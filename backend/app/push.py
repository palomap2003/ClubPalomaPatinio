"""Envío de notificaciones push con Firebase Cloud Messaging."""

from datetime import timedelta

from firebase_admin import exceptions as fb_exceptions
from firebase_admin import messaging


class TokenInvalido(Exception):
    """FCM informa que el token no está registrado (app desinstalada, otro dispositivo, sesión cerrada)."""


class ErrorTemporal(Exception):
    """Falla transitoria de FCM o de red: se puede reintentar."""


def enviar_push(token, titulo, cuerpo, data, ttl_segundos):
    mensaje = messaging.Message(
        token=token,
        notification=messaging.Notification(title=titulo, body=cuerpo),
        data={k: str(v) for k, v in data.items()},
        # El TTL es el tiempo que falta para la reserva: si el celular reconecta tarde, el aviso se descarta.
        android=messaging.AndroidConfig(priority="high", ttl=timedelta(seconds=max(int(ttl_segundos), 1))),
    )
    try:
        messaging.send(mensaje)
    except (messaging.UnregisteredError, messaging.SenderIdMismatchError, fb_exceptions.InvalidArgumentError) as e:
        raise TokenInvalido(str(e)) from e
    except (fb_exceptions.FirebaseError, OSError) as e:
        raise ErrorTemporal(str(e)) from e
