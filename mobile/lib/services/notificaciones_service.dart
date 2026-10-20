import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../screens/reserva_detalle_page.dart';
import '../theme.dart';
import 'api_client.dart';

final navigatorKey = GlobalKey<NavigatorState>();
final messengerKey = GlobalKey<ScaffoldMessengerState>();

/// Notificaciones push (CU-24): permiso, token FCM y apertura del detalle de la reserva al tocar el aviso.
class NotificacionesService {
  static final _fcm = FirebaseMessaging.instance;
  static final List<StreamSubscription> _subs = [];
  static bool _iniciado = false;

  /// Se llama una vez que hay sesión iniciada y perfil cargado.
  static Future<void> iniciar() async {
    if (_iniciado) return;
    _iniciado = true;
    try {
      await _pedirPermiso();
      await _registrarToken();
      // ignore: deprecated_member_use
      _subs.add(_fcm.onTokenRefresh.listen((t) => _guardar(t)));
      // Con la app abierta FCM no muestra nada solo: se avisa con un banner dentro de la app.
      _subs.add(FirebaseMessaging.onMessage.listen(_enPrimerPlano));
      // Toque sobre la notificación con la app en segundo plano o cerrada.
      _subs.add(FirebaseMessaging.onMessageOpenedApp.listen(_abrirDetalle));
      final inicial = await _fcm.getInitialMessage();
      if (inicial != null) _abrirDetalle(inicial);
    } catch (_) {
      // Las notificaciones nunca deben impedir usar la app: sin ellas queda la tarjeta "Tu próxima reserva".
    }
  }

  /// Al cerrar sesión: se desvincula el teléfono de la cuenta para no avisarle a quien no tiene sesión.
  static Future<void> detener() async {
    for (final s in _subs) {
      await s.cancel();
    }
    _subs.clear();
    _iniciado = false;
    try {
      await api.borrarFcmToken();
      // ignore: deprecated_member_use
      await _fcm.deleteToken();
    } catch (_) {}
  }

  static Future<void> _pedirPermiso() async {
    final estado = (await _fcm.getNotificationSettings()).authorizationStatus;
    final contexto = navigatorKey.currentState?.overlay?.context;
    if (contexto == null || !contexto.mounted) return;
    if (estado == AuthorizationStatus.notDetermined) {
      final acepta = await showDialog<bool>(
        // ignore: use_build_context_synchronously
        context: contexto,
        builder: (ctx) => AlertDialog(
          backgroundColor: kCard,
          icon: const Icon(Icons.notifications_active_outlined, color: kNeon, size: 40),
          title: const Text('Recordatorios de tus reservas'),
          content: const Text('Te avisamos 24 horas y 1 hora antes de cada turno para que no te lo pierdas.'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Ahora no')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Habilitar notificaciones')),
          ],
        ),
      );
      if (acepta == true) await _fcm.requestPermission();
      return;
    } else if (estado == AuthorizationStatus.denied) {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool('aviso_notificaciones_mostrado') == true) return;
      await prefs.setBool('aviso_notificaciones_mostrado', true); // se muestra por única vez
      final ctx2 = navigatorKey.currentState?.overlay?.context;
      if (ctx2 == null || !ctx2.mounted) return;
      await showDialog<void>(
        context: ctx2,
        builder: (ctx) => AlertDialog(
          backgroundColor: kCard,
          icon: const Icon(Icons.notifications_off_outlined, color: kError, size: 40),
          title: const Text('Notificaciones desactivadas'),
          content: const Text(
              'No vas a recibir recordatorios en el teléfono. Podés activarlas desde Ajustes > Aplicaciones > '
              'ClubPalomaPatinio > Notificaciones. Mientras tanto, tus próximas reservas se ven en la pantalla de inicio.'),
          actions: [FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Entendido'))],
        ),
      );
    }
  }

  static Future<void> _registrarToken() async {
    // ignore: deprecated_member_use
    final token = await _fcm.getToken();
    if (token != null) await _guardar(token);
  }

  static Future<void> _guardar(String token) async {
    try {
      await api.guardarFcmToken(token);
    } catch (_) {}
  }

  static int? _reservaId(RemoteMessage m) => int.tryParse('${m.data['reserva_id']}');

  static void _abrirDetalle(RemoteMessage m) {
    final id = _reservaId(m);
    if (id == null) return;
    navigatorKey.currentState?.push(MaterialPageRoute(builder: (_) => ReservaDetallePage(reservaId: id)));
  }

  static void _enPrimerPlano(RemoteMessage m) {
    final n = m.notification;
    if (n == null) return;
    messengerKey.currentState
      ?..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(
        duration: const Duration(seconds: 8),
        content: Text('${n.title ?? ''}\n${n.body ?? ''}'.trim()),
        action: SnackBarAction(label: 'VER', textColor: kNeon, onPressed: () => _abrirDetalle(m)),
      ));
  }
}
