import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';
import 'confirmar_reserva_page.dart';

class HorariosPage extends StatefulWidget {
  final Espacio espacio;
  const HorariosPage({super.key, required this.espacio});
  @override
  State<HorariosPage> createState() => _HorariosPageState();
}

class _HorariosPageState extends State<HorariosPage> {
  late final DateTime _hoy = DateUtils.dateOnly(DateTime.now());
  late DateTime _fecha = _hoy;
  int _duracion = 1;
  Franja? _seleccion;
  late Future<List<Franja>> _franjas = _cargar();

  Future<List<Franja>> _cargar() => api.disponibilidad(widget.espacio.id, _fecha, _duracion);

  void _recargar() => setState(() {
        _seleccion = null;
        _franjas = _cargar();
      });

  Future<void> _reservar() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ConfirmarReservaPage(espacio: widget.espacio, fecha: _fecha, franja: _seleccion!),
      ),
    );
    if (mounted) _recargar(); // al volver (ej. horario ocupado) se actualiza la grilla
  }

  @override
  Widget build(BuildContext context) {
    final e = widget.espacio;
    return Scaffold(
      appBar: AppBar(title: Text('HORARIOS', style: titulo(24))),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(e.nombre,
                  style: const TextStyle(color: kNeon, fontFamily: 'monospace', fontWeight: FontWeight.w600)),
              Text('${e.tipo} · ${dinero(e.precioHora)}/h', style: TextStyle(color: blanco(0.7))),
            ]),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 74,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: 14,
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (context, i) {
              final d = _hoy.add(Duration(days: i));
              final activo = d == _fecha;
              return InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: () {
                  _fecha = d;
                  _recargar();
                },
                child: Container(
                  width: 58,
                  decoration: BoxDecoration(
                    color: activo ? kNeon : kCard,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: activo ? kNeon : blanco(0.1)),
                  ),
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    Text(diaCorto(d).toUpperCase(),
                        style: TextStyle(fontSize: 12, color: activo ? Colors.black : blanco(0.6))),
                    Text('${d.day}',
                        style: TextStyle(
                            fontSize: 22, fontWeight: FontWeight.w800, color: activo ? Colors.black : Colors.white)),
                  ]),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 14),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(children: [
            Text('Duración', style: TextStyle(color: blanco(0.7))),
            const Spacer(),
            SegmentedButton<int>(
              segments: const [ButtonSegment(value: 1, label: Text('1 hora')), ButtonSegment(value: 2, label: Text('2 horas'))],
              selected: {_duracion},
              showSelectedIcon: false,
              onSelectionChanged: (s) {
                _duracion = s.first;
                _recargar();
              },
            ),
          ]),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: FutureBuilder<List<Franja>>(
            future: _franjas,
            builder: (context, snap) {
              if (snap.connectionState != ConnectionState.done) return const Cargando();
              if (snap.hasError) return ErrorView(error: snap.error!, onRetry: _recargar);
              final franjas = snap.data!;
              final libres = franjas.where((f) => f.disponible).length;
              if (libres == 0) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Icon(Icons.event_busy, size: 52, color: blanco(0.5)),
                      const SizedBox(height: 12),
                      Text('No hay horarios disponibles', style: titulo(22)),
                      const SizedBox(height: 6),
                      Text('Probá con otra fecha o con otra duración.',
                          textAlign: TextAlign.center, style: TextStyle(color: blanco(0.6))),
                    ]),
                  ),
                );
              }
              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  if (libres < franjas.length)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Text('Algunos horarios están ocupados · ${franjas.length - libres} no disponibles',
                          style: TextStyle(color: blanco(0.5), fontSize: 13)),
                    ),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    for (final f in franjas)
                      ChoiceChip(
                        label: Text(f.horaInicio),
                        selected: _seleccion?.horaInicio == f.horaInicio,
                        onSelected: f.disponible ? (_) => setState(() => _seleccion = f) : null,
                        selectedColor: kNeon,
                        showCheckmark: false,
                        labelStyle: TextStyle(
                          color: _seleccion?.horaInicio == f.horaInicio
                              ? Colors.black
                              : (f.disponible ? Colors.white : blanco(0.25)),
                          decoration: f.disponible ? null : TextDecoration.lineThrough,
                        ),
                      ),
                  ]),
                ]),
              );
            },
          ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
          decoration: BoxDecoration(color: kCard, border: Border(top: BorderSide(color: blanco(0.08)))),
          child: SafeArea(
            top: false,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              if (_seleccion != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(children: [
                    Expanded(
                      child: Text('${fechaLegible(_fecha)} · ${_seleccion!.horaInicio} a ${_seleccion!.horaFin}',
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    Text(dinero(e.precioHora * _duracion),
                        style: const TextStyle(color: kNeon, fontWeight: FontWeight.w800, fontSize: 18)),
                  ]),
                ),
              FilledButton(
                onPressed: _seleccion == null ? null : _reservar,
                child: Text(_seleccion == null ? 'ELEGÍ UN HORARIO' : 'RESERVAR'),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}
