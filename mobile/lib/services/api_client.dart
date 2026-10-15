import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../models.dart';

enum TipoError { sinConexion, servidor, sesion, negocio }

/// Error ya "traducido" para mostrar al usuario. Distingue falta de internet, servidor caído y errores de negocio.
class ApiException implements Exception {
  final TipoError tipo;
  final String mensaje;
  final String codigo;
  final int? status;

  const ApiException(this.tipo, this.mensaje, {this.codigo = '', this.status});

  const ApiException.sinConexion()
      : this(TipoError.sinConexion, 'Sin conexión a internet. Verificá tu conexión e intentá nuevamente.');

  const ApiException.servidor()
      : this(TipoError.servidor, 'No pudimos comunicarnos con el servidor. Intentá nuevamente en unos minutos.');

  const ApiException.sesion()
      : this(TipoError.sesion, 'Tu sesión expiró. Iniciá sesión nuevamente.', codigo: 'NO_AUTENTICADO', status: 401);

  @override
  String toString() => mensaje;
}

/// Cliente de la API REST. Cada request lleva el ID Token de Firebase del usuario autenticado.
class ApiClient {
  static const _timeout = Duration(seconds: 60); // el plan gratuito de Render puede tardar en "despertar"

  Future<dynamic> _enviar(String metodo, String ruta, {Map<String, String>? query, Object? body}) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) throw const ApiException.sesion();

    String? token;
    try {
      token = await user.getIdToken();
    } on FirebaseAuthException catch (e) {
      if (e.code == 'network-request-failed') throw const ApiException.sinConexion();
      throw const ApiException.sesion();
    }

    final uri = Uri.parse('$apiBaseUrl$ruta').replace(queryParameters: query);
    final headers = {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'};
    final cuerpo = body == null ? null : jsonEncode(body);

    http.Response resp;
    try {
      switch (metodo) {
        case 'POST':
          resp = await http.post(uri, headers: headers, body: cuerpo).timeout(_timeout);
        case 'PUT':
          resp = await http.put(uri, headers: headers, body: cuerpo).timeout(_timeout);
        case 'DELETE':
          resp = await http.delete(uri, headers: headers).timeout(_timeout);
        default:
          resp = await http.get(uri, headers: headers).timeout(_timeout);
      }
    } on SocketException {
      throw const ApiException.sinConexion();
    } on http.ClientException {
      throw const ApiException.sinConexion();
    } on TimeoutException {
      throw const ApiException.servidor();
    }

    final texto = utf8.decode(resp.bodyBytes);
    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      return texto.isEmpty ? null : jsonDecode(texto);
    }
    if (resp.statusCode >= 500) throw const ApiException.servidor();
    if (resp.statusCode == 401) throw const ApiException.sesion();

    var codigo = '', mensaje = 'Ocurrió un error inesperado.';
    try {
      final e = jsonDecode(texto)['error'];
      codigo = e['codigo'];
      mensaje = e['mensaje'];
    } catch (_) {}
    throw ApiException(TipoError.negocio, mensaje, codigo: codigo, status: resp.statusCode);
  }

  List<T> _lista<T>(dynamic json, T Function(Map<String, dynamic>) f) =>
      (json as List).map((e) => f(e as Map<String, dynamic>)).toList();

  // ---- Usuarios ----
  Future<Usuario> registrarPerfil({
    required String nombre,
    required String apellido,
    required String dni,
    required String fechaNacimiento,
  }) async {
    final j = await _enviar('POST', '/api/v1/usuarios',
        body: {'nombre': nombre, 'apellido': apellido, 'dni': dni, 'fecha_nacimiento': fechaNacimiento});
    return Usuario.fromJson(j);
  }

  Future<Usuario> perfil() async => Usuario.fromJson(await _enviar('GET', '/api/v1/usuarios/me'));

  Future<Usuario> editarPerfil({
    required String nombre,
    required String apellido,
    required String fechaNacimiento,
  }) async {
    final j = await _enviar('PUT', '/api/v1/usuarios/me',
        body: {'nombre': nombre, 'apellido': apellido, 'fecha_nacimiento': fechaNacimiento});
    return Usuario.fromJson(j);
  }

  Future<void> guardarFcmToken(String token) => _enviar('PUT', '/api/v1/usuarios/me/fcm-token', body: {'token': token});

  // ---- Catálogo ----
  Future<List<Sede>> sedes() async => _lista(await _enviar('GET', '/api/v1/sedes'), Sede.fromJson);

  Future<List<Deporte>> deportes() async => _lista(await _enviar('GET', '/api/v1/deportes'), Deporte.fromJson);

  Future<List<Espacio>> espacios({int? sedeId, int? deporteId}) async {
    final query = <String, String>{
      if (sedeId != null) 'sede_id': '$sedeId',
      if (deporteId != null) 'deporte_id': '$deporteId',
    };
    return _lista(await _enviar('GET', '/api/v1/espacios', query: query), Espacio.fromJson);
  }

  Future<List<Franja>> disponibilidad(int espacioId, DateTime fecha, int duracion) async => _lista(
        await _enviar('GET', '/api/v1/espacios/$espacioId/disponibilidad',
            query: {'fecha': fechaIso(fecha), 'duracion': '$duracion'}),
        Franja.fromJson,
      );

  // ---- Reservas ----
  Future<Reserva> reservar({
    required int espacioId,
    required DateTime fecha,
    required String horaInicio,
    required String horaFin,
  }) async {
    final j = await _enviar('POST', '/api/v1/reservas', body: {
      'espacio_id': espacioId,
      'fecha': fechaIso(fecha),
      'hora_inicio': horaInicio,
      'hora_fin': horaFin,
    });
    return Reserva.fromJson(j);
  }

  Future<List<Reserva>> misReservas({required bool historial}) async => _lista(
        await _enviar('GET', '/api/v1/reservas/mis-reservas', query: {'tipo': historial ? 'historial' : 'proximas'}),
        Reserva.fromJson,
      );

  Future<Reserva> cancelarReserva(int id) async => Reserva.fromJson(await _enviar('DELETE', '/api/v1/reservas/$id'));
}

final api = ApiClient();
