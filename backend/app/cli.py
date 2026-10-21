import click
from sqlalchemy import inspect, text

from .extensions import db
from .models import Espacio, generar_nombre_espacio
from .seed import cargar_datos_ejemplo


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas si no existen (es seguro ejecutarlo en cada arranque)."""
        db.create_all()
        # Migración mínima: el booleano `recordatorio_enviado` se reemplazó por la tabla `notificaciones`.
        if "recordatorio_enviado" in [c["name"] for c in inspect(db.engine).get_columns("reservas")]:
            db.session.execute(text("ALTER TABLE reservas DROP COLUMN recordatorio_enviado"))
            db.session.commit()
            click.echo("Columna reservas.recordatorio_enviado eliminada.")
        # Los nombres de espacios siguen el formato del enunciado (Sede_Calle_Altura_Tipo_Numero).
        renombrados = 0
        for espacio in db.session.query(Espacio).all():
            nombre = generar_nombre_espacio(espacio.sede, espacio.tipo, espacio.numero)
            if espacio.nombre != nombre:
                espacio.nombre = nombre
                renombrados += 1
        db.session.commit()
        if renombrados:
            click.echo(f"{renombrados} espacios renombrados al formato del enunciado.")
        click.echo("Tablas creadas / verificadas.")

    @app.cli.command("seed")
    def seed():
        """Carga sedes, deportes y espacios de ejemplo solo si la base está vacía."""
        click.echo("Datos de ejemplo cargados." if cargar_datos_ejemplo() else "La base ya tiene datos; no se carga nada.")
