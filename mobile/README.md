# ClubPalomaPatinio – App móvil (Flutter)

App Android para reservar espacios deportivos de las sedes del club. Se conecta a la API REST del
backend (ver [`../backend/README.md`](../backend/README.md)) y usa **Firebase Authentication** para el
inicio de sesión y **Firebase Cloud Messaging** para los recordatorios.

- API en producción: `https://clubpalomapatinio.onrender.com` (Swagger en `/apidocs/`)
- Modelo de datos: [`../docs/modelo-datos.md`](../docs/modelo-datos.md)

## Funcionalidades

- Registro (nombre, apellido, DNI, fecha de nacimiento, email, contraseña), inicio de sesión,
  recuperación de contraseña por email y cierre de sesión.
- Sedes y espacios deportivos, con filtro por deporte.
- Horarios disponibles por fecha y duración (1 o 2 horas), confirmación y reserva.
- Mis reservas: próximas e historial, detalle y cancelación con confirmación.
- Perfil editable (el email y el DNI no se modifican).
- Recordatorios push 24 h y 1 h antes del turno; al tocarlos se abre el detalle de la reserva.

## Manejo de errores

| Situación | Qué ve el usuario |
|---|---|
| Sin internet | "Sin conexión" con botón Reintentar |
| Servidor caído, error 5xx o timeout (60 s) | "Servidor no disponible" con botón Reintentar |
| Contraseña o email incorrectos | Mensaje en el formulario de login |
| Email ya registrado | Mensaje en el formulario de registro |
| DNI ya registrado | Mensaje en el formulario de registro |
| Sesión vencida (401) | Pantalla que lleva al login |
| Horario ocupado por otro usuario | Aviso y la grilla de horarios se recarga |

> El backend corre en el plan gratuito de Render: si estuvo inactivo, la primera respuesta puede tardar
> hasta 1 minuto mientras el servicio "se despierta".

## Requisitos

- Flutter 3.x con Dart 3.x (`flutter doctor` sin errores para Android)
- Android Studio con un emulador o un celular Android con depuración USB
- El archivo `android/app/google-services.json` del proyecto Firebase `club-paloma-patinio`
  (no se sube a GitHub; viene incluido en el ZIP de entrega)

## Ejecutar

```bash
cd mobile
flutter pub get
flutter run
```

Por defecto usa la API de Render. Para apuntar a otra (por ejemplo el backend local, que desde el
emulador Android se ve como `10.0.2.2`):

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000
```

APK de prueba: `flutter build apk --debug` (queda en `build/app/outputs/flutter-apk/`).

### Si es la primera vez que compilás Android

Gradle descarga el NDK y CMake la primera vez; puede tardar bastante. Si falla con
"Package ndk not found", instalalo desde Android Studio (**SDK Manager → SDK Tools → NDK (Side by side)**).

## Estructura

```
lib/
  main.dart                  Inicio de Firebase y AuthGate (¿hay sesión? Home : Login)
  config.dart                URL de la API (override con --dart-define)
  theme.dart                 Tema oscuro con acento lima
  models.dart                Usuario, Sede, Espacio, Franja, Reserva
  services/
    api_client.dart          Cliente HTTP: agrega el token, traduce errores a ApiException
    auth_service.dart        Login, registro, recuperación, cierre de sesión (Firebase)
    notificaciones_service.dart  Permiso, token FCM y apertura de la reserva desde el aviso
  screens/                   Login, registro, recuperar contraseña, inicio, sede, horarios,
                             confirmar reserva, mis reservas, detalle de reserva y perfil
```

## Cómo funciona la autenticación

1. La app inicia sesión (o crea la cuenta) en **Firebase**; la contraseña nunca pasa por nuestro backend.
2. En cada llamada a la API envía `Authorization: Bearer <ID Token de Firebase>`.
3. El backend verifica el token con Firebase Admin y usa el `uid` para saber quién es el usuario:
   el usuario nunca viaja en el cuerpo de las peticiones.
4. Al registrarse, si falla el guardado del perfil en la API se elimina la cuenta de Firebase recién
   creada, para no dejar una cuenta sin perfil.

## Notificaciones push

Al entrar a la app se explica el beneficio y se pide el permiso del sistema; el token FCM se guarda en la
API (`PUT /usuarios/me/fcm-token`) y se borra al cerrar sesión. Si el permiso está denegado se avisa una
sola vez y los turnos próximos se siguen viendo en la tarjeta "Tu próxima reserva" de la pantalla de inicio.
Con la app abierta el aviso aparece como un banner dentro de la app. El envío lo dispara el backend (ver
"Recordatorios push" en el README del backend).

## Tests y análisis

```bash
flutter analyze
flutter test
```
