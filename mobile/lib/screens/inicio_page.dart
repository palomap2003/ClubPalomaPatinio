import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';
import 'home_page.dart';
import 'sede_page.dart';

class InicioPage extends StatefulWidget {
  final Usuario usuario;
  const InicioPage({super.key, required this.usuario});
  @override
  State<InicioPage> createState() => _InicioPageState();
}

typedef _Datos = ({List<Sede> sedes, List<Reserva> proximas});

class _InicioPageState extends State<InicioPage> {
  late Future<_Datos> _datos = _cargar();

  Future<_Datos> _cargar() async {
    final r = await Future.wait([api.sedes(), api.misReservas(historial: false)]);
    return (sedes: r[0] as List<Sede>, proximas: r[1] as List<Reserva>);
  }

  void _recargar() => setState(() => _datos = _cargar());

  @override
  Widget build(BuildContext context) => FutureBuilder<_Datos>(
        future: _datos,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Cargando();
          if (snap.hasError) return ErrorView(error: snap.error!, onRetry: _recargar);
          final d = snap.data!;
          final proxima = d.proximas.isEmpty ? null : d.proximas.first;
          return RefreshIndicator(
            color: kNeon,
            onRefresh: () async => _recargar(),
            child: ListView(padding: const EdgeInsets.all(20), children: [
              Text('HOLA, ${widget.usuario.nombre.toUpperCase()}', style: titulo(34)),
              Text('¿Qué querés reservar hoy?', style: TextStyle(color: blanco(0.6))),
              const SizedBox(height: 24),
              Text('TU PRÓXIMA RESERVA', style: titulo(20).copyWith(color: kNeon)),
              const SizedBox(height: 10),
              if (proxima == null)
                Tarjeta(
                  child: Text('Todavía no tenés reservas próximas. Elegí una sede para reservar.',
                      style: TextStyle(color: blanco(0.7))),
                )
              else
                Tarjeta(
                  onTap: () => tabActual.value = 1,
                  child: Row(children: [
                    const Icon(Icons.event_available, color: kNeon),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(proxima.espacioNombre, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text(
                          '${fechaLegible(proxima.fechaDate)} · ${proxima.horaInicio} a ${proxima.horaFin}',
                          style: TextStyle(color: blanco(0.7)),
                        ),
                      ]),
                    ),
                    const Icon(Icons.chevron_right),
                  ]),
                ),
              const SizedBox(height: 24),
              Text('SEDES', style: titulo(20).copyWith(color: kNeon)),
              const SizedBox(height: 10),
              for (final s in d.sedes) ...[
                Tarjeta(
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SedePage(sede: s))),
                  child: Row(children: [
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(s.nombre.toUpperCase(), style: titulo(22)),
                        const SizedBox(height: 2),
                        Text(s.direccion, style: TextStyle(color: blanco(0.7))),
                        const SizedBox(height: 6),
                        Row(children: [
                          Icon(Icons.schedule, size: 16, color: blanco(0.6)),
                          const SizedBox(width: 6),
                          Text('Abierto de ${s.horario}', style: TextStyle(color: blanco(0.6), fontSize: 13)),
                        ]),
                      ]),
                    ),
                    const Icon(Icons.chevron_right),
                  ]),
                ),
                const SizedBox(height: 10),
              ],
            ]),
          );
        },
      );
}
