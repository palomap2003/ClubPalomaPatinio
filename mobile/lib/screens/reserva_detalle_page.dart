import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';

/// Detalle de una reserva. Es el destino al tocar una notificación push de recordatorio.
class ReservaDetallePage extends StatefulWidget {
  final int reservaId;
  const ReservaDetallePage({super.key, required this.reservaId});
  @override
  State<ReservaDetallePage> createState() => _ReservaDetallePageState();
}

class _ReservaDetallePageState extends State<ReservaDetallePage> {
  late Future<Reserva> _reserva = api.reserva(widget.reservaId);
  bool _cancelando = false;

  void _recargar() => setState(() => _reserva = api.reserva(widget.reservaId));

  Future<void> _cancelar(Reserva r) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: kCard,
        title: const Text('¿Querés cancelar la reserva?'),
        content: Text('${r.sedeNombre} · ${r.espacioNombre}\n${fechaLegible(r.fechaDate)} · ${r.horaInicio} a ${r.horaFin}'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Volver')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Cancelar reserva', style: TextStyle(color: kError)),
          ),
        ],
      ),
    );
    if (confirmar != true || !mounted) return;
    setState(() => _cancelando = true);
    try {
      await api.cancelarReserva(r.id);
      if (!mounted) return;
      mostrarSnack(context, 'Reserva cancelada con éxito');
    } on ApiException catch (e) {
      if (!mounted) return;
      mostrarSnack(context, e.mensaje, error: true);
    }
    if (mounted) {
      setState(() => _cancelando = false);
      _recargar();
    }
  }

  Widget _fila(String etiqueta, String valor) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(children: [
          Text(etiqueta, style: TextStyle(color: blanco(0.6))),
          const SizedBox(width: 16),
          Expanded(child: Text(valor, textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w700))),
        ]),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('DETALLE DE LA RESERVA', style: titulo(24))),
        body: FutureBuilder<Reserva>(
          future: _reserva,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const Cargando();
            if (snap.hasError) return ErrorView(error: snap.error!, onRetry: _recargar);
            final r = snap.data!;
            final cancelada = r.estado == 'cancelada';
            final etiqueta = cancelada ? 'Cancelada' : (r.puedeCancelar ? 'Confirmada' : 'Finalizada');
            return ListView(padding: const EdgeInsets.all(20), children: [
              Tarjeta(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Column(children: [
                  _fila('Estado', etiqueta),
                  const Divider(height: 1),
                  _fila('Sede', r.sedeNombre),
                  const Divider(height: 1),
                  _fila('Espacio', r.espacioNombre),
                  const Divider(height: 1),
                  _fila('Deporte', '${r.deporte} · ${r.tipo}'),
                  const Divider(height: 1),
                  _fila('Fecha', fechaLegible(r.fechaDate)),
                  const Divider(height: 1),
                  _fila('Horario', '${r.horaInicio} a ${r.horaFin}'),
                  const Divider(height: 1),
                  _fila('Total', dinero(r.precioTotal)),
                ]),
              ),
              if (r.puedeCancelar) ...[
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: _cancelando ? null : () => _cancelar(r),
                  style: OutlinedButton.styleFrom(
                      foregroundColor: kError, side: const BorderSide(color: kError), minimumSize: const Size.fromHeight(48)),
                  child: const Text('Cancelar reserva'),
                ),
              ],
            ]);
          },
        ),
      );
}
