"""Autenticação por sessão e proteção CSRF."""
import functools
import hmac
import secrets

import click
from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db

bp = Blueprint("auth", __name__)


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def init_security(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def _load_user_and_check_csrf():
        user_id = session.get("user_id")
        g.user = db.get_user(user_id) if user_id else None
        if request.method == "POST":
            sent = request.form.get("_csrf", "")
            expected = session.get("_csrf", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, "Requisição inválida. Recarregue a página e tente de novo.")

    @app.after_request
    def _security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _safe_next(target):
    # só aceita caminhos internos, evitando redirecionamento para sites externos
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("main.menu")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = db.get_user_by_username(username)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Usuário ou senha incorretos", "error")
        else:
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            return redirect(_safe_next(request.args.get("next")))
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@click.command("create-user")
@click.argument("username")
@click.password_option()
def create_user_command(username, password):
    """Cria um usuário de acesso ao sistema."""
    db.init_db()
    if db.get_user_by_username(username):
        raise click.ClickException("Esse usuário já existe.")
    db.insert_user(username, generate_password_hash(password))
    click.echo(f"Usuário '{username}' criado.")


def init_app(app):
    init_security(app)
    app.cli.add_command(create_user_command)
