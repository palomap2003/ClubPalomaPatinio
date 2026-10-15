import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';
import 'home_page.dart';

class ConfirmarReservaPage extends StatefulWidget {
  final Espacio espacio;
  final DateTime fecha;
  final Franja franja;
  const ConfirmarReservaPage({super.key, required this.espacio, required this.fecha, required this.franja});
  @override
  State<ConfirmarReservaPage> createState() => _ConfirmarReservaPageState();
}

class _ConfirmarReservaPageState extends State<ConfirmarReservaPage> {
  bool _cargando = false;
  String? _error;
  Reserva? _reserva;

  int get _horas => int.parse(widget.franja.horaFin.substring(0, 2)) - int.parse(widget.franja.horaInicio.substring(0, 2));

  Future<void> _confirmar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final r = await api.reservar(
        espacioId: widget.espacio.id,
        fecha: widget.fecha,
        horaInicio: widget.franja.horaInicio,
        horaFin: widget.franja.horaFin,
      );
      if (mounted) setState(() => _reserva = r);
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.codigo == 'HORARIO_NO_DISPONIBLE') {
        // Otro usuario reservó primero: se vuelve a la grilla, que se recarga sola.
        mostrarSnack(context, 'El horario seleccionado ya no está disponible. Por favor elegí otro turno.', error: true);
        Navigator.pop(context);
      } else {
        setState(() => _error = e.mensaje);
      }
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Widget _fila(String etiqueta, String valor, {bool destacado = false}) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(children: [
          Text(etiqueta, style: TextStyle(color: blanco(0.6))),
          const SizedBox(width: 16),
          Expanded(
            child: Text(valor,
                textAlign: TextAlign.right,
                style: TextStyle(
                    fontWeight: FontWeight.w700, fontSize: destacado ? 20 : 15, color: destacado ? kNeon : Colors.white)),
          ),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final e = widget.espacio;
    if (_reserva != null) return _exito();
    return Scaffold(
      appBar: AppBar(title: Text('CONFIRMÁ TU RESERVA', style: titulo(24))),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        Tarjeta(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Column(children: [
            _fila('Sede', e.sedeNombre),
            const Divider(height: 1),
            _fila('Espacio', e.nombre),
            const Divider(height: 1),
            _fila('Deporte', '${e.deporte} · ${e.tipo}'),
            const Divider(height: 1),
            _fila('Fecha', fechaLegible(widget.fecha)),
            const Divider(height: 1),
            _fila('Horario', '${widget.franja.horaInicio} a ${widget.franja.horaFin}'),
            const Divider(height: 1),
            _fila('Total', dinero(e.precioHora * _horas), destacado: true),
          ]),
        ),
        const SizedBox(height: 20),
        if (_error != null) ...[BannerError(_error!), const SizedBox(height: 16)],
        FilledButton(
          onPressed: _cargando ? null : _confirmar,
          child: _cargando
              ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2))
              : Text(_error == null ? 'CONFIRMAR RESERVA' : 'REINTENTAR'),
        ),
        const SizedBox(height: 12),
        OutlinedButton(
          onPressed: _cargando ? null : () => Navigator.pop(context),
          style: OutlinedButton.styleFrom(foregroundColor: kError, side: const BorderSide(color: kError)),
          child: const Text('Cancelar'),
        ),
      ]),
    );
  }

  Widget _exito() {
    final r = _reserva!;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            const Icon(Icons.check_circle_outline, size: 80, color: kNeon),
            const SizedBox(height: 16),
            Text('¡RESERVA CONFIRMADA!', style: titulo(32).copyWith(color: kNeon)),
            const SizedBox(height: 12),
            Text(r.espacioNombre, style: const TextStyle(fontWeight: FontWeight.w600)),
            Text('${fechaLegible(r.fechaDate)} · ${r.horaInicio} a ${r.horaFin}', style: TextStyle(color: blanco(0.7))),
            Text(dinero(r.precioTotal), style: const TextStyle(color: kNeon, fontWeight: FontWeight.w800, fontSize: 20)),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: () {
                tabActual.value = 1;
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: const Text('VER MIS RESERVAS'),
            ),
          ]),
        ),
      ),
    );
  }
}
