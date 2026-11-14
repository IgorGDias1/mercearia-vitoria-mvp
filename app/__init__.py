"""Mercearia Vitória — MVP de gerenciamento comercial (monolito em camadas).

Camadas:
  routes.py / templates  -> interface
  services.py            -> regras de negócio
  db.py / schema.sql     -> acesso e persistência de dados
"""
import secrets

from flask import Flask, render_template

from . import auth, db, routes, services
from .config import Config


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        # Chave temporária: as sessões deixam de valer quando o servidor reinicia.
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning(
            "SECRET_KEY não definida: usando chave aleatória temporária. "
            "Defina a variável de ambiente SECRET_KEY para manter os logins entre reinícios."
        )

    db.init_app(app)
    auth.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)
    app.jinja_env.filters["brl"] = services.format_brl

    @app.context_processor
    def _stock_alert_helpers():
        threshold = app.config["LOW_STOCK_THRESHOLD"]
        return {
            "low_stock_threshold": threshold,
            "is_low_stock": lambda p: services.is_low_stock(p, threshold),
        }

    @app.errorhandler(400)
    @app.errorhandler(404)
    def _error(err):
        return render_template("error.html", error=err), err.code

    with app.app_context():
        db.init_db()  # cria as tabelas se ainda não existirem
    return app
