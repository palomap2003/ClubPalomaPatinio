import 'package:club_paloma_patinio/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('formatea fechas para la API', () {
    expect(fechaIso(DateTime(2026, 3, 5)), '2026-03-05');
  });

  test('formatea importes con separador de miles', () {
    expect(dinero(3800), r'$3.800');
    expect(dinero(1234567), r'$1.234.567');
    expect(dinero(900), r'$900');
  });

  test('interpreta una reserva devuelta por la API', () {
    final r = Reserva.fromJson({
      'id': 7,
      'estado': 'confirmada',
      'fecha': '2026-11-12',
      'hora_inicio': '18:00',
      'hora_fin': '19:00',
      'precio_total': 3800.0,
      'puede_cancelar': true,
      'espacio': {'id': 1, 'nombre': 'Moron_Rivadavia_19850_Futbol5_1', 'deporte': 'Fútbol', 'tipo': 'Fútbol 5'},
      'sede': {'id': 1, 'nombre': 'Morón', 'direccion': 'Av. Rivadavia 19850'},
    });
    expect(r.sedeNombre, 'Morón');
    expect(r.puedeCancelar, isTrue);
    expect(r.fechaDate, DateTime(2026, 11, 12));
  });
}
