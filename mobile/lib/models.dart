String fechaIso(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

const _dias = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];
const _meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

String diaCorto(DateTime d) => _dias[d.weekday - 1];
String fechaLegible(DateTime d) => '${diaCorto(d)} ${d.day} ${_meses[d.month - 1]}';
String dinero(num n) {
  final s = n.round().toString();
  final conPuntos = s.replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => '.');
  return '\$$conPuntos';
}

class Usuario {
  final String email, nombre, apellido, dni, fechaNacimiento;
  Usuario.fromJson(Map<String, dynamic> j)
      : email = j['email'],
        nombre = j['nombre'],
        apellido = j['apellido'],
        dni = j['dni'],
        fechaNacimiento = j['fecha_nacimiento'];
}

class Sede {
  final int id;
  final String nombre, direccion, horaApertura, horaCierre;
  Sede.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        nombre = j['nombre'],
        direccion = j['direccion'],
        horaApertura = j['hora_apertura'],
        horaCierre = j['hora_cierre'];
  String get horario => '$horaApertura a $horaCierre';
}

class Deporte {
  final int id;
  final String nombre;
  Deporte.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        nombre = j['nombre'];
}

class Espacio {
  final int id;
  final String nombre, deporte, tipo, sedeNombre;
  final double precioHora;
  final bool techado, iluminacion;
  Espacio.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        nombre = j['nombre'],
        deporte = j['deporte'],
        tipo = j['tipo']['nombre'],
        sedeNombre = j['sede']['nombre'],
        precioHora = (j['precio_hora'] as num).toDouble(),
        techado = j['techado'],
        iluminacion = j['iluminacion'];
}

class Franja {
  final String horaInicio, horaFin;
  final bool disponible;
  Franja.fromJson(Map<String, dynamic> j)
      : horaInicio = j['hora_inicio'],
        horaFin = j['hora_fin'],
        disponible = j['disponible'];
}

class Reserva {
  final int id;
  final String estado, fecha, horaInicio, horaFin, espacioNombre, deporte, tipo, sedeNombre, sedeDireccion;
  final double precioTotal;
  final bool puedeCancelar;
  Reserva.fromJson(Map<String, dynamic> j)
      : id = j['id'],
        estado = j['estado'],
        fecha = j['fecha'],
        horaInicio = j['hora_inicio'],
        horaFin = j['hora_fin'],
        precioTotal = (j['precio_total'] as num).toDouble(),
        puedeCancelar = j['puede_cancelar'],
        espacioNombre = j['espacio']['nombre'],
        deporte = j['espacio']['deporte'],
        tipo = j['espacio']['tipo'],
        sedeNombre = j['sede']['nombre'],
        sedeDireccion = j['sede']['direccion'];
  DateTime get fechaDate => DateTime.parse(fecha);
}
