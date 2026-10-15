import 'package:flutter/material.dart';

import '../models.dart';
import '../services/api_client.dart';
import '../theme.dart';
import '../widgets.dart';
import 'horarios_page.dart';

class SedePage extends StatefulWidget {
  final Sede sede;
  const SedePage({super.key, required this.sede});
  @override
  State<SedePage> createState() => _SedePageState();
}

class _SedePageState extends State<SedePage> {
  late Future<List<Espacio>> _espacios = api.espacios(sedeId: widget.sede.id);
  String? _deporte; // null = todos

  void _recargar() => setState(() => _espacios = api.espacios(sedeId: widget.sede.id));

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('SEDE ${widget.sede.nombre.toUpperCase()}', style: titulo(24))),
        body: FutureBuilder<List<Espacio>>(
          future: _espacios,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const Cargando();
            if (snap.hasError) return ErrorView(error: snap.error!, onRetry: _recargar);
            final todos = snap.data!;
            final deportes = todos.map((e) => e.deporte).toSet().toList()..sort();
            final visibles = _deporte == null ? todos : todos.where((e) => e.deporte == _deporte).toList();
            return Column(children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 4),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text('${widget.sede.direccion} · ${widget.sede.horario}',
                      style: TextStyle(color: blanco(0.6), fontSize: 13)),
                ),
              ),
              SizedBox(
                height: 52,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  children: [
                    for (final d in [null, ...deportes])
                      Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(d ?? 'Todos'),
                          selected: _deporte == d,
                          onSelected: (_) => setState(() => _deporte = d),
                          selectedColor: kNeon,
                          labelStyle: TextStyle(color: _deporte == d ? Colors.black : Colors.white),
                          showCheckmark: false,
                        ),
                      ),
                  ],
                ),
              ),
              Expanded(
                child: visibles.isEmpty
                    ? Center(child: Text('No hay espacios para mostrar.', style: TextStyle(color: blanco(0.6))))
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                        itemCount: visibles.length,
                        separatorBuilder: (_, _) => const SizedBox(height: 10),
                        itemBuilder: (context, i) {
                          final e = visibles[i];
                          return Tarjeta(
                            onTap: () =>
                                Navigator.push(context, MaterialPageRoute(builder: (_) => HorariosPage(espacio: e))),
                            child: Row(children: [
                              Expanded(
                                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Text(e.nombre,
                                      style: const TextStyle(
                                          color: kNeon, fontFamily: 'monospace', fontSize: 13, fontWeight: FontWeight.w600)),
                                  const SizedBox(height: 4),
                                  Text('${e.tipo} · ${e.techado ? 'Techado' : 'Aire libre'}',
                                      style: TextStyle(color: blanco(0.7))),
                                  Text('${dinero(e.precioHora)}/h', style: TextStyle(color: blanco(0.7))),
                                ]),
                              ),
                              const Icon(Icons.chevron_right),
                            ]),
                          );
                        },
                      ),
              ),
            ]);
          },
        ),
      );
}
