import 'package:flutter/material.dart';

import '../models.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import '../widgets.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});
  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _form = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _apellido = TextEditingController();
  final _dni = TextEditingController();
  final _fecha = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  DateTime? _nacimiento;
  bool _ocultar = true, _cargando = false, _exito = false;
  String? _error;

  @override
  void dispose() {
    for (final c in [_nombre, _apellido, _dni, _fecha, _email, _password]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _elegirFecha() async {
    final hoy = DateTime.now();
    final f = await showDatePicker(
      context: context,
      initialDate: _nacimiento ?? DateTime(hoy.year - 25),
      firstDate: DateTime(1920),
      lastDate: hoy,
      helpText: 'Fecha de nacimiento',
    );
    if (f != null) {
      setState(() => _nacimiento = f);
      _fecha.text = fechaIso(f);
    }
  }

  Future<void> _crearCuenta() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      await AuthService.registrar(
        email: _email.text,
        password: _password.text,
        nombre: _nombre.text.trim(),
        apellido: _apellido.text.trim(),
        dni: _dni.text.trim(),
        fechaNacimiento: fechaIso(_nacimiento!),
      );
      if (mounted) setState(() => _exito = true);
    } catch (e) {
      // Usuario ya registrado, DNI repetido, sin conexión, servidor caído...: se queda en el formulario.
      if (mounted) setState(() => _error = mensajeDe(e));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _volverAlLogin() async {
    await AuthService.finalizarRegistro();
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: !_exito,
        child: Scaffold(
          appBar: AppBar(
            automaticallyImplyLeading: !_exito,
            title: Text('CREAR CUENTA', style: titulo(22)),
          ),
          body: _exito ? _exitoView() : _formulario(),
        ),
      );

  Widget _exitoView() => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.check_circle_outline, size: 72, color: kNeon),
          const SizedBox(height: 16),
          Text('¡CUENTA CREADA!', style: titulo(30).copyWith(color: kNeon)),
          const SizedBox(height: 8),
          Text('Tu cuenta fue registrada con éxito. Ya podés iniciar sesión.',
              textAlign: TextAlign.center, style: TextStyle(color: blanco(0.7))),
          const SizedBox(height: 28),
          FilledButton(onPressed: _volverAlLogin, child: const Text('VOLVER AL LOGIN')),
        ]),
      );

  Widget _formulario() => SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _form,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (_error != null) ...[BannerError(_error!), const SizedBox(height: 16)],
            TextFormField(
              controller: _nombre,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Nombre'),
              validator: (v) => requerido(v, 'El nombre'),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _apellido,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Apellido'),
              validator: (v) => requerido(v, 'El apellido'),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _dni,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'DNI'),
              validator: (v) {
                final r = requerido(v, 'El DNI');
                if (r != null) return r;
                return RegExp(r'^\d{7,9}$').hasMatch(v!.trim()) ? null : 'El DNI debe tener entre 7 y 9 números';
              },
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _fecha,
              readOnly: true,
              onTap: _elegirFecha,
              decoration: const InputDecoration(
                labelText: 'Fecha de nacimiento',
                suffixIcon: Icon(Icons.calendar_today_outlined),
              ),
              validator: (v) => requerido(v, 'La fecha de nacimiento'),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'Email'),
              validator: (v) {
                final r = requerido(v, 'El email');
                if (r != null) return r;
                return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v!.trim()) ? null : 'El email no es válido';
              },
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _password,
              obscureText: _ocultar,
              decoration: InputDecoration(
                labelText: 'Contraseña',
                helperText: 'Mínimo 6 caracteres',
                suffixIcon: IconButton(
                  icon: Icon(_ocultar ? Icons.visibility_off : Icons.visibility),
                  onPressed: () => setState(() => _ocultar = !_ocultar),
                ),
              ),
              validator: (v) {
                final r = requerido(v, 'La contraseña');
                if (r != null) return r;
                return v!.length >= 6 ? null : 'Mínimo 6 caracteres';
              },
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _cargando ? null : _crearCuenta,
              child: _cargando
                  ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('CREAR CUENTA'),
            ),
          ]),
        ),
      );
}
