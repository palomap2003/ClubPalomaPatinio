import 'package:flutter/material.dart';

import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'theme.dart';

class Cargando extends StatelessWidget {
  const Cargando({super.key});
  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator(color: kNeon));
}

/// Pantalla/estado de error con el mensaje adecuado (sin internet, servidor caído, sesión vencida...).
class ErrorView extends StatelessWidget {
  final Object error;
  final VoidCallback? onRetry;
  const ErrorView({super.key, required this.error, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final e = error is ApiException ? error as ApiException : null;
    final tipo = e?.tipo;
    final icono = switch (tipo) {
      TipoError.sinConexion => Icons.wifi_off_rounded,
      TipoError.servidor => Icons.cloud_off_rounded,
      TipoError.sesion => Icons.lock_outline_rounded,
      _ => Icons.error_outline_rounded,
    };
    final encabezado = switch (tipo) {
      TipoError.sinConexion => 'Sin conexión',
      TipoError.servidor => 'Servidor no disponible',
      TipoError.sesion => 'Sesión vencida',
      _ => 'Ocurrió un error',
    };
    final mensaje = e?.mensaje ?? 'Ocurrió un error inesperado.';
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icono, size: 56, color: kError),
          const SizedBox(height: 16),
          Text(encabezado, style: titulo(20)),
          const SizedBox(height: 8),
          Text(mensaje, textAlign: TextAlign.center, style: TextStyle(color: blanco(0.7))),
          const SizedBox(height: 24),
          if (tipo == TipoError.sesion)
            FilledButton(onPressed: AuthService.cerrarSesion, child: const Text('INICIAR SESIÓN'))
          else if (onRetry != null)
            FilledButton(onPressed: onRetry, child: const Text('REINTENTAR')),
        ]),
      ),
    );
  }

}

/// Mensaje de error en línea (formularios).
class BannerError extends StatelessWidget {
  final String mensaje;
  const BannerError(this.mensaje, {super.key});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: kError.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: kError.withValues(alpha: 0.6)),
        ),
        child: Row(children: [
          const Icon(Icons.error_outline, color: kError, size: 20),
          const SizedBox(width: 10),
          Expanded(child: Text(mensaje, style: const TextStyle(color: kError))),
        ]),
      );
}

void mostrarSnack(BuildContext context, String mensaje, {bool error = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(
      content: Text(mensaje, style: TextStyle(color: error ? Colors.white : Colors.black)),
      backgroundColor: error ? kError : kNeon,
      behavior: SnackBarBehavior.floating,
    ));
}

String mensajeDe(Object e) => e is ApiException ? e.mensaje : 'Ocurrió un error inesperado.';

/// Tarjeta oscura reutilizable.
class Tarjeta extends StatelessWidget {
  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;
  const Tarjeta({super.key, required this.child, this.onTap, this.padding = const EdgeInsets.all(14)});

  @override
  Widget build(BuildContext context) => Material(
        color: kCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: BorderSide(color: blanco(0.08))),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Padding(padding: padding, child: child),
        ),
      );
}

String? requerido(String? v, [String campo = 'Este campo']) =>
    (v == null || v.trim().isEmpty) ? '$campo es obligatorio' : null;
