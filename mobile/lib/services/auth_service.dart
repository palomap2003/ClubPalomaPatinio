import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'notificaciones_service.dart';

/// Acceso a Firebase Authentication. La contraseña vive solo en Firebase; nuestra base guarda el perfil.
class AuthService {
  /// Mientras es true, el AuthGate no entra al Home aunque Firebase ya haya creado la cuenta:
  /// el registro termina recién cuando se guarda el perfil en la API y el usuario vuelve al login.
  static final ValueNotifier<bool> registrando = ValueNotifier(false);

  static ApiException _traducir(FirebaseAuthException e) {
    switch (e.code) {
      case 'network-request-failed':
        return const ApiException.sinConexion();
      case 'invalid-credential':
      case 'wrong-password':
      case 'user-not-found':
        return const ApiException(TipoError.negocio, 'Email o contraseña incorrectos.');
      case 'invalid-email':
        return const ApiException(TipoError.negocio, 'El email no es válido.');
      case 'user-disabled':
        return const ApiException(TipoError.negocio, 'Esta cuenta fue deshabilitada.');
      case 'too-many-requests':
        return const ApiException(TipoError.negocio, 'Demasiados intentos. Esperá unos minutos e intentá de nuevo.');
      case 'email-already-in-use':
        return const ApiException(
            TipoError.negocio, 'El usuario ya está registrado. Iniciá sesión o usá otro email.',
            codigo: 'USUARIO_YA_REGISTRADO');
      case 'weak-password':
        return const ApiException(TipoError.negocio, 'La contraseña es muy débil (mínimo 6 caracteres).');
      default:
        return ApiException(TipoError.negocio, 'No se pudo completar la operación (${e.code}).');
    }
  }

  static Future<void> iniciarSesion(String email, String password) async {
    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(email: email.trim(), password: password);
    } on FirebaseAuthException catch (e) {
      throw _traducir(e);
    }
  }

  static Future<void> registrar({
    required String email,
    required String password,
    required String nombre,
    required String apellido,
    required String dni,
    required String fechaNacimiento,
  }) async {
    registrando.value = true;
    UserCredential? cred;
    try {
      cred = await FirebaseAuth.instance.createUserWithEmailAndPassword(email: email.trim(), password: password);
      await api.registrarPerfil(nombre: nombre, apellido: apellido, dni: dni, fechaNacimiento: fechaNacimiento);
    } on FirebaseAuthException catch (e) {
      registrando.value = false;
      throw _traducir(e);
    } on ApiException {
      // El perfil no se pudo guardar (DNI repetido, sin conexión...): se elimina la cuenta recién creada
      // para no dejar un usuario de Firebase "a medias".
      try {
        await cred?.user?.delete();
      } catch (_) {
        await FirebaseAuth.instance.signOut();
      }
      registrando.value = false;
      rethrow;
    }
  }

  /// Registro terminado: se cierra la sesión que Firebase abrió al crear la cuenta y se vuelve al login.
  static Future<void> finalizarRegistro() async {
    await FirebaseAuth.instance.signOut();
    registrando.value = false;
  }

  static Future<void> recuperarPassword(String email) async {
    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(email: email.trim());
    } on FirebaseAuthException catch (e) {
      // Por seguridad no se informa si el email existe o no.
      if (e.code == 'user-not-found') return;
      throw _traducir(e);
    }
  }

  static Future<void> cerrarSesion() async {
    await NotificacionesService.detener(); // antes del signOut: borrar el token requiere sesión
    await FirebaseAuth.instance.signOut();
  }
}
