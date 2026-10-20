# Backend – ClubPalomaPatinio

API REST (Flask + PostgreSQL) para la gestión de reservas de espacios deportivos. La autenticación la resuelve
Firebase Authentication: la app inicia sesión en Firebase y envía el *ID Token* en cada request
(`Authorization: Bearer <token>`); la API lo verifica con Firebase Admin y obtiene el `uid` del usuario.

- Documentación interactiva (Swagger UI): `/apidocs/` · especificación OpenAPI: `/apispec.json`
- Modelo de datos: ver [`../docs/modelo-datos.md`](../docs/modelo-datos.md)

## Endpoints (`/api/v1`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/usuarios` | Completa el perfil tras crear la cuenta en Firebase |
| GET / PUT | `/usuarios/me` | Ver / editar perfil (el email no se modifica) |
| PUT / DELETE | `/usuarios/me/fcm-token` | Guarda / quita el token del dispositivo (push) |
| GET | `/sedes`, `/sedes/{id}` | Sedes con horarios de funcionamiento |
| GET | `/deportes` | Deportes y sus tipos (para el filtro) |
| GET | `/espacios?sede_id=&deporte_id=&tipo_id=` | Espacios con su sede, filtrables |
| GET | `/espacios/{id}/disponibilidad?fecha=&duracion=` | Franjas libres/ocupadas |
| POST | `/reservas` | Reservar (valida horarios y superposición) |
| GET | `/reservas/mis-reservas?tipo=proximas\|historial` | Reservas del usuario |
| GET | `/reservas/{id}` | Detalle de una reserva propia |
| DELETE | `/reservas/{id}` | Cancelar (libera el horario) |
| POST | `/notificaciones/recordatorios` | Envía los recordatorios push (lo invoca un cron; header `X-Cron-Secret`) |

Errores: siempre JSON `{"error": {"codigo": "...", "mensaje": "..."}}` con el código HTTP correspondiente
(400 datos inválidos, 401 sin sesión, 404 no existe, 409 conflicto, 500 error interno).

## Ejecutar en tu PC

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env             # y completar los valores
flask --app app init-db            # crea las tablas
flask --app app seed               # carga sedes/espacios de ejemplo (solo si la base está vacía)
flask --app app run               # http://127.0.0.1:5000/apidocs/
```

Tests (no necesitan Firebase ni PostgreSQL; usan SQLite y un verificador de tokens simulado):

```bash
python -m pytest
# Contra PostgreSQL real:  set TEST_DATABASE_URL=postgresql://usuario:clave@host:5432/base_de_test
```

## 1. Crear el proyecto de Firebase

1. https://console.firebase.google.com → **Agregar proyecto** (ej. `club-paloma-patino`). Analytics no hace falta.
2. **Authentication → Comenzar → Método de acceso → Correo electrónico/contraseña → Habilitar**.
3. **Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada**. Se descarga un JSON.
   **Es un secreto: no se sube a GitHub ni se pone en la app.**
4. (Más adelante, para la app) registrar la app Android en el mismo proyecto.

## 2. Desplegar en Render

1. **New → PostgreSQL** (plan Free). Copiar la **Internal Database URL**.
2. **New → Web Service** → conectar el repositorio de GitHub. Configurar:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3 · **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `flask --app app init-db && flask --app app seed && gunicorn "app:create_app()"`
3. **Environment** del servicio:
   - `DATABASE_URL` = Internal Database URL del paso 1
   - `FIREBASE_CREDENTIALS_JSON` = contenido completo del JSON de la cuenta de servicio (en una línea)
   - `CRON_SECRET` = un valor largo y aleatorio
   - `PYTHON_VERSION` = `3.13.5`
4. Deploy. Verificar `https://<tu-servicio>.onrender.com/health` y `https://<tu-servicio>.onrender.com/apidocs/`.

> En el plan gratuito el servicio se "duerme" tras un rato sin uso: la primera request puede tardar ~1 minuto.

## 3. Recordatorios push (CU-24)

`POST /api/v1/notificaciones/recordatorios` revisa las reservas confirmadas y envía por Firebase Cloud Messaging
el aviso **"Tenés una reserva mañana"** (entre 22 h y 24 h antes) y **"Tu reserva comienza en 1 hora"**
(en la última hora). Cada envío queda en la tabla `notificaciones`, que impide repetirlo.

Alguien tiene que llamar a ese endpoint cada pocos minutos. Opción gratuita: [cron-job.org](https://cron-job.org)
con una tarea **cada 5 minutos**, método `POST`, URL `https://<tu-servicio>.onrender.com/api/v1/notificaciones/recordatorios`
y el header `X-Cron-Secret: <el valor de CRON_SECRET>`. (Render también ofrece *Cron Jobs*, pero son de pago.)

Casos contemplados: reserva cancelada (no se avisa), usuario sin token o sin permiso (queda el aviso dentro de la
app), token inválido (se borra de la cuenta y no se reintenta), falla temporal de FCM (hasta 3 intentos con espera
creciente) y TTL del mensaje igual al tiempo que falta para la reserva.

Para probarlo a mano, con el secreto en una variable de entorno:

```bash
curl -X POST "$URL/api/v1/notificaciones/recordatorios" -H "X-Cron-Secret: $CRON_SECRET"
```

## Decisiones de diseño (para la defensa)

- **Contraseñas fuera de nuestra base:** las administra Firebase; la tabla `usuarios` solo guarda el `firebase_uid` y los datos de perfil.
- **El usuario nunca viaja en el body:** se obtiene del token verificado, así nadie puede reservar o cancelar en nombre de otro.
- **Horas como enteros:** `hora_inicio`/`hora_fin` se guardan como hora completa (0–24); "minuto 00" queda garantizado por el tipo de dato y la API rechaza cualquier otro minuto.
- **Superposición:** dos rangos `[a,b)` y `[c,d)` chocan si `a < d` y `b > c`; 19–20 y 20–21 no chocan. Antes de validar se bloquea la fila del espacio (`SELECT … FOR UPDATE`) para que dos reservas simultáneas no se pisen.
- **Un usuario, una reserva por horario:** no puede tener dos reservas confirmadas que se superpongan, aunque sean en canchas distintas (409 `RESERVA_SUPERPUESTA_USUARIO`). Se bloquean las filas del usuario y del espacio durante la validación, así dos pedidos simultáneos tampoco se pisan.
- **Cancelación lógica:** la reserva queda `cancelada` (se ve en el historial) y el horario se libera porque la validación solo mira las `confirmada`.
- **Zona horaria:** "horario futuro" se evalúa en hora de Argentina (Render corre en UTC).
