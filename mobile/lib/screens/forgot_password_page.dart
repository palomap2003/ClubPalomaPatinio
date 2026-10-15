import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../theme.dart';
import '../widgets.dart';

class ForgotPasswordPage extends StatefulWidget {
  final String email;
  const ForgotPasswordPage({super.key, this.email = ''});
  @override
  State<ForgotPasswordPage> createState() => _ForgotPasswordPageState();
}

class _ForgotPasswordPageState extends State<ForgotPasswordPage> {
  final _form = GlobalKey<FormState>();
  late final _email = TextEditingController(text: widget.email);
  bool _cargando = false, _enviado = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      await AuthService.recuperarPassword(_email.text);
      if (mounted) setState(() => _enviado = true);
    } catch (e) {
      if (mounted) setState(() => _error = mensajeDe(e));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('RECUPERAR CONTRASEÑA', style: titulo(22))),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: _enviado
              ? Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  const Icon(Icons.mark_email_read_outlined, size: 64, color: kNeon),
                  const SizedBox(height: 16),
                  Text('Revisá tu correo', style: titulo(26)),
                  const SizedBox(height: 8),
                  Text(
                    'Si el email está registrado, te enviamos un enlace para crear una nueva contraseña.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: blanco(0.7)),
                  ),
                  const SizedBox(height: 28),
                  FilledButton(onPressed: () => Navigator.pop(context), child: const Text('VOLVER AL LOGIN')),
                ])
              : Form(
                  key: _form,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    Text('Ingresá el email de tu cuenta y te enviaremos un enlace para restablecer la contraseña.',
                        style: TextStyle(color: blanco(0.7))),
                    const SizedBox(height: 20),
                    if (_error != null) ...[BannerError(_error!), const SizedBox(height: 16)],
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(labelText: 'Email'),
                      validator: (v) => requerido(v, 'El email'),
                    ),
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _cargando ? null : _enviar,
                      child: _cargando
                          ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('ENVIAR ENLACE'),
                    ),
                  ]),
                ),
        ),
      );
}
