from datetime import datetime, time, timedelta, timezone

from .extensions import db
from .utils import slug

ESTADO_CONFIRMADA = "confirmada"
ESTADO_CANCELADA = "cancelada"


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Usuario(db.Model):
    """Perfil del usuario. La contraseña NO se guarda acá: la administra Firebase Authentication."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    dni = db.Column(db.String(12), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    fcm_token = db.Column(db.String(512))  # token del dispositivo para notificaciones push
    creado_en = db.Column(db.DateTime, nullable=False, default=utcnow)

    reservas = db.relationship("Reserva", back_populates="usuario")


class Deporte(db.Model):
    __tablename__ = "deportes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)  # Fútbol, Tenis, Paddle...

    tipos = db.relationship("TipoEspacio", back_populates="deporte", order_by="TipoEspacio.id")


class TipoEspacio(db.Model):
    """Variante dentro de un deporte (Fútbol -> Fútbol 5, Fútbol 7...). Los tipos dependen del deporte."""

    __tablename__ = "tipos_espacio"
    __table_args__ = (db.UniqueConstraint("deporte_id", "codigo", name="uq_tipo_deporte_codigo"),)

    id = db.Column(db.Integer, primary_key=True)
    deporte_id = db.Column(db.Integer, db.ForeignKey("deportes.id"), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)  # "Fútbol 5"
    codigo = db.Column(db.String(20), nullable=False)  # "F5" (se usa en el nombre compuesto del espacio)

    deporte = db.relationship("Deporte", back_populates="tipos")


class Sede(db.Model):
    __tablename__ = "sedes"
    __table_args__ = (
        db.CheckConstraint(
            "hora_apertura >= 0 AND hora_apertura < hora_cierre AND hora_cierre <= 24",
            name="ck_sede_horario",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    calle = db.Column(db.String(120), nullable=False)
    altura = db.Column(db.String(10), nullable=False)
    hora_apertura = db.Column(db.SmallInteger, nullable=False)  # hora completa 0-23
    hora_cierre = db.Column(db.SmallInteger, nullable=False)  # hora completa 1-24
    activa = db.Column(db.Boolean, nullable=False, default=True)

    espacios = db.relationship("Espacio", back_populates="sede")

    @property
    def direccion(self):
        return f"{self.calle} {self.altura}"


class Espacio(db.Model):
    __tablename__ = "espacios"
    __table_args__ = (
        db.UniqueConstraint("sede_id", "tipo_espacio_id", "numero", name="uq_espacio_sede_tipo_numero"),
    )

    id = db.Column(db.Integer, primary_key=True)
    sede_id = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=False)
    tipo_espacio_id = db.Column(db.Integer, db.ForeignKey("tipos_espacio.id"), nullable=False)
    numero = db.Column(db.Integer, nullable=False)  # correlativo por sede y tipo
    nombre = db.Column(db.String(200), unique=True, nullable=False)  # Sede_Calle_Deporte_Tipo_Numero
    precio_hora = db.Column(db.Numeric(10, 2), nullable=False)
    techado = db.Column(db.Boolean, nullable=False, default=False)  # indoor / outdoor
    iluminacion = db.Column(db.Boolean, nullable=False, default=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    sede = db.relationship("Sede", back_populates="espacios")
    tipo = db.relationship("TipoEspacio")
    reservas = db.relationship("Reserva", back_populates="espacio")


def generar_nombre_espacio(sede, tipo, numero):
    """Ej.: Moron_Rivadavia_Futbol_F5_1  (sede, calle, deporte, tipo, número)."""
    calle = " ".join(p for p in sede.calle.split() if p.lower().strip(".") not in ("av", "avenida", "calle"))
    return "_".join([slug(sede.nombre), slug(calle), slug(tipo.deporte.nombre), slug(tipo.codigo), str(numero)])


class Reserva(db.Model):
    """Reserva de un espacio para una fecha y un rango de horas completas [hora_inicio, hora_fin)."""

    __tablename__ = "reservas"
    __table_args__ = (
        db.CheckConstraint(
            "hora_inicio >= 0 AND hora_inicio < hora_fin AND hora_fin <= 24", name="ck_reserva_horas"
        ),
        db.Index("ix_reserva_espacio_fecha", "espacio_id", "fecha"),
        db.Index("ix_reserva_usuario", "usuario_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    espacio_id = db.Column(db.Integer, db.ForeignKey("espacios.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.SmallInteger, nullable=False)
    hora_fin = db.Column(db.SmallInteger, nullable=False)
    estado = db.Column(db.String(12), nullable=False, default=ESTADO_CONFIRMADA)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)  # se congela al reservar
    creada_en = db.Column(db.DateTime, nullable=False, default=utcnow)
    cancelada_en = db.Column(db.DateTime)
    recordatorio_enviado = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship("Usuario", back_populates="reservas")
    espacio = db.relationship("Espacio", back_populates="reservas")

    @property
    def inicio(self):
        return datetime.combine(self.fecha, time.min) + timedelta(hours=self.hora_inicio)

    @property
    def fin(self):
        return datetime.combine(self.fecha, time.min) + timedelta(hours=self.hora_fin)
