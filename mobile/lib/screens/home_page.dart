import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/notificaciones_service.dart';
import '../widgets.dart';
import 'inicio_page.dart';
import 'mis_reservas_page.dart';
import 'perfil_page.dart';

/// Permite que otras pantallas (ej. la reserva confirmada) cambien de pestaña.
final ValueNotifier<int> tabActual = ValueNotifier(0);

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  Usuario? _usuario;
  Object? _error;

  @override
  void initState() {
    super.initState();
    tabActual.value = 0;
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _error = null);
    try {
      final u = await api.perfil();
      if (mounted) {
        setState(() => _usuario = u);
        // Ya hay sesión y perfil: se piden permisos y se registra el teléfono para los recordatorios.
        WidgetsBinding.instance.addPostFrameCallback((_) => NotificacionesService.iniciar());
      }
    } catch (e) {
      if (mounted) setState(() => _error = e);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        body: SafeArea(
          child: Column(children: [
            Expanded(child: ErrorView(error: _error!, onRetry: _cargar)),
            TextButton(onPressed: AuthService.cerrarSesion, child: const Text('Cerrar sesión')),
            const SizedBox(height: 16),
          ]),
        ),
      );
    }
    final usuario = _usuario;
    if (usuario == null) return const Scaffold(body: Cargando());

    return ValueListenableBuilder<int>(
      valueListenable: tabActual,
      builder: (context, indice, _) => Scaffold(
        body: SafeArea(
          child: switch (indice) {
            0 => InicioPage(usuario: usuario),
            1 => const MisReservasPage(),
            _ => PerfilPage(usuario: usuario, onActualizado: (u) => setState(() => _usuario = u)),
          },
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: indice,
          onDestinationSelected: (i) => tabActual.value = i,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Inicio'),
            NavigationDestination(
                icon: Icon(Icons.event_note_outlined), selectedIcon: Icon(Icons.event_note), label: 'Mis reservas'),
            NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}
