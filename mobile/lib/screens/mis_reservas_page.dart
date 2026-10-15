import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';

class MisReservasPage extends StatelessWidget {
  const MisReservasPage({super.key});

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 2,
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
            child: Align(alignment: Alignment.centerLeft, child: Text('MIS RESERVAS', style: titulo(34))),
          ),
          const TabBar(
            indicatorColor: kNeon,
            labelColor: kNeon,
            tabs: [Tab(text: 'Próximas'), Tab(text: 'Historial')],
          ),
          const Expanded(
            child: TabBarView(children: [_ListaReservas(historial: false), _ListaReservas(historial: true)]),
          ),
        ]),
      );
}

class _ListaReservas extends StatefulWidget {
  final bool historial;
  const _ListaReservas({required this.historial});
  @override
  State<_ListaReservas> createState() => _ListaReservasState();
}

class _ListaReservasState extends State<_ListaReservas> with AutomaticKeepAliveClientMixin {
  late Future<List<Reserva>> _reservas = api.misReservas(historial: widget.historial);

  @override
  bool get wantKeepAlive => true;

  void _recargar() => setState(() => _reservas = api.misReservas(historial: widget.historial));

  Future<void> _cancelar(Reserva r) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: kCard,
        title: const Text('¿Querés cancelar la reserva?'),
        content: Text('${r.sedeNombre} · ${r.espacioNombre}\n${fechaLegible(r.fechaDate)} · ${r.horaInicio} a ${r.horaFin}\n${dinero(r.precioTotal)}'),
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
    try {
      await api.cancelarReserva(r.id);
      if (!mounted) return;
      mostrarSnack(context, 'Reserva cancelada con éxito');
    } on ApiException catch (e) {
      if (!mounted) return;
      mostrarSnack(context, e.tipo == TipoError.servidor ? 'No se pudo cancelar la reserva en este momento. Intente más tarde.' : e.mensaje, error: true);
    }
    if (mounted) _recargar();
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return FutureBuilder<List<Reserva>>(
      future: _reservas,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) return const Cargando();
        if (snap.hasError) return ErrorView(error: snap.error!, onRetry: _recargar);
        final lista = snap.data!;
        return RefreshIndicator(
          color: kNeon,
          onRefresh: () async => _recargar(),
          child: lista.isEmpty
              ? ListView(children: [
                  const SizedBox(height: 80),
                  Icon(Icons.event_busy, size: 52, color: blanco(0.4)),
                  const SizedBox(height: 12),
                  Center(
                    child: Text(widget.historial ? 'Todavía no tenés historial.' : 'No tenés reservas próximas.',
                        style: TextStyle(color: blanco(0.6))),
                  ),
                ])
              : ListView.separated(
                  padding: const EdgeInsets.all(20),
                  itemCount: lista.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) => _TarjetaReserva(reserva: lista[i], onCancelar: () => _cancelar(lista[i])),
                ),
        );
      },
    );
  }
}

class _TarjetaReserva extends StatelessWidget {
  final Reserva reserva;
  final VoidCallback onCancelar;
  const _TarjetaReserva({required this.reserva, required this.onCancelar});

  @override
  Widget build(BuildContext context) {
    final r = reserva;
    final cancelada = r.estado == 'cancelada';
    final (etiqueta, color) = cancelada
        ? ('CANCELADA', kError)
        : (r.puedeCancelar ? ('CONFIRMADA', kNeon) : ('FINALIZADA', blanco(0.5)));
    return Tarjeta(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(r.sedeNombre.toUpperCase(), style: titulo(20))),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: color),
            ),
            child: Text(etiqueta, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w800)),
          ),
        ]),
        const SizedBox(height: 4),
        Text(r.espacioNombre, style: const TextStyle(color: kNeon, fontFamily: 'monospace', fontSize: 12)),
        const SizedBox(height: 8),
        Row(children: [
          Icon(Icons.calendar_today, size: 15, color: blanco(0.6)),
          const SizedBox(width: 6),
          Text('${fechaLegible(r.fechaDate)} · ${r.horaInicio} a ${r.horaFin}'),
          const Spacer(),
          Text(dinero(r.precioTotal), style: const TextStyle(fontWeight: FontWeight.w800)),
        ]),
        if (r.puedeCancelar) ...[
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onCancelar,
            style: OutlinedButton.styleFrom(
                foregroundColor: kError, side: const BorderSide(color: kError), minimumSize: const Size.fromHeight(40)),
            child: const Text('Cancelar reserva'),
          ),
        ],
      ]),
    );
  }
}
