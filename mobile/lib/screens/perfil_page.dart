import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import '../widgets.dart';

class PerfilPage extends StatefulWidget {
  final Usuario usuario;
  final ValueChanged<Usuario> onActualizado;
  const PerfilPage({super.key, required this.usuario, required this.onActualizado});
  @override
  State<PerfilPage> createState() => _PerfilPageState();
}

class _PerfilPageState extends State<PerfilPage> {
  final _form = GlobalKey<FormState>();
  late final _nombre = TextEditingController(text: widget.usuario.nombre);
  late final _apellido = TextEditingController(text: widget.usuario.apellido);
  late final _fecha = TextEditingController(text: widget.usuario.fechaNacimiento);
  bool _editando = false, _guardando = false;
  String? _error;

  @override
  void dispose() {
    _nombre.dispose();
    _apellido.dispose();
    _fecha.dispose();
    super.dispose();
  }

  Future<void> _elegirFecha() async {
    final actual = DateTime.tryParse(_fecha.text) ?? DateTime(DateTime.now().year - 25);
    final f = await showDatePicker(
        context: context, initialDate: actual, firstDate: DateTime(1920), lastDate: DateTime.now());
    if (f != null) _fecha.text = fechaIso(f);
  }

  void _cancelarEdicion() => setState(() {
        _editando = false;
        _error = null;
        _nombre.text = widget.usuario.nombre;
        _apellido.text = widget.usuario.apellido;
        _fecha.text = widget.usuario.fechaNacimiento;
      });

  Future<void> _guardar() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _guardando = true;
      _error = null;
    });
    try {
      final u = await api.editarPerfil(
          nombre: _nombre.text.trim(), apellido: _apellido.text.trim(), fechaNacimiento: _fecha.text);
      widget.onActualizado(u);
      if (mounted) {
        setState(() => _editando = false);
        mostrarSnack(context, 'Perfil actualizado');
      }
    } catch (e) {
      if (mounted) setState(() => _error = mensajeDe(e));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final u = widget.usuario;
    return ListView(padding: const EdgeInsets.all(20), children: [
      Text('MI PERFIL', style: titulo(34)),
      const SizedBox(height: 16),
      Form(
        key: _form,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          if (_error != null) ...[BannerError(_error!), const SizedBox(height: 14)],
          TextFormField(
            initialValue: u.email,
            enabled: false,
            decoration: const InputDecoration(labelText: 'Email (no se puede modificar)'),
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _nombre,
            enabled: _editando,
            decoration: const InputDecoration(labelText: 'Nombre'),
            validator: (v) => requerido(v, 'El nombre'),
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _apellido,
            enabled: _editando,
            decoration: const InputDecoration(labelText: 'Apellido'),
            validator: (v) => requerido(v, 'El apellido'),
          ),
          const SizedBox(height: 14),
          TextFormField(
            initialValue: u.dni,
            enabled: false,
            decoration: const InputDecoration(labelText: 'DNI'),
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _fecha,
            enabled: _editando,
            readOnly: true,
            onTap: _editando ? _elegirFecha : null,
            decoration: const InputDecoration(labelText: 'Fecha de nacimiento', suffixIcon: Icon(Icons.calendar_today_outlined)),
            validator: (v) => requerido(v, 'La fecha de nacimiento'),
          ),
        ]),
      ),
      const SizedBox(height: 20),
      if (_editando) ...[
        FilledButton(
          onPressed: _guardando ? null : _guardar,
          child: _guardando
              ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('GUARDAR CAMBIOS'),
        ),
        const SizedBox(height: 10),
        OutlinedButton(onPressed: _guardando ? null : _cancelarEdicion, child: const Text('Cancelar')),
      ] else
        FilledButton(onPressed: () => setState(() => _editando = true), child: const Text('EDITAR PERFIL')),
      const SizedBox(height: 28),
      OutlinedButton.icon(
        onPressed: () async {
          Navigator.of(context).popUntil((r) => r.isFirst);
          await AuthService.cerrarSesion();
        },
        icon: const Icon(Icons.logout, color: kError),
        label: const Text('Cerrar sesión', style: TextStyle(color: kError)),
        style: OutlinedButton.styleFrom(side: const BorderSide(color: kError)),
      ),
    ]);
  }
}
