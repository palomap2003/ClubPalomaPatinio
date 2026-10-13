import click

from .extensions import db
from .seed import cargar_datos_ejemplo


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas si no existen (es seguro ejecutarlo en cada arranque)."""
        db.create_all()
        click.echo("Tablas creadas / verificadas.")

    @app.cli.command("seed")
    def seed():
        """Carga sedes, deportes y espacios de ejemplo solo si la base está vacía."""
        click.echo("Datos de ejemplo cargados." if cargar_datos_ejemplo() else "La base ya tiene datos; no se carga nada.")
