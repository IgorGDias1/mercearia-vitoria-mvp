"""Camada de interface (rotas). Sem regra de negócio: delega para services."""
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for, abort)

from . import db, services
from .auth import login_required

bp = Blueprint("main", __name__)


@bp.route("/saude")
def health():
    """Verificação de saúde para monitoramento (sem login e sem expor dados)."""
    try:
        db.get_db().execute("SELECT 1").fetchone()
    except Exception:
        return {"status": "erro"}, 503
    return {"status": "ok"}


@bp.route("/")
@login_required
def menu():
    return render_template("menu.html")


# ---------- produtos ----------
@bp.route("/produtos")
@login_required
def products():
    search = (request.args.get("q") or "").strip()
    return render_template("products.html", products=db.list_products(search=search or None),
                           search=search)


@bp.route("/produtos/novo", methods=["GET", "POST"])
@login_required
def product_new():
    if request.method == "POST":
        try:
            services.create_product(request.form)
        except services.ValidationError as exc:
            flash(str(exc), "error")
            return render_template("product_form.html", product=None, form=request.form), 400
        flash("Produto cadastrado com sucesso", "success")
        return redirect(url_for("main.products"))
    return render_template("product_form.html", product=None, form={})


@bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    product = db.get_product(product_id)
    if product is None:
        abort(404)
    if request.method == "POST":
        try:
            services.edit_product(product_id, request.form)
        except services.ValidationError as exc:
            flash(str(exc), "error")
            return render_template("product_form.html", product=product, form=request.form), 400
        flash("Produto atualizado com sucesso", "success")
        return redirect(url_for("main.products"))
    return render_template("product_form.html", product=product, form={})


# ---------- vendas (funcionalidade central) ----------
@bp.route("/vendas/nova", methods=["GET", "POST"])
@login_required
def sale_new():
    products = db.list_products(only_active=True)
    if request.method == "POST":
        quantities = {}
        for p in products:
            quantities[p["id"]] = request.form.get(f"qty_{p['id']}", "")
        try:
            sale_id, total = services.register_sale(
                quantities, current_app.config["STOCK_DEDUCT_ON_SALE"]
            )
        except services.ValidationError as exc:
            flash(str(exc), "error")
            return render_template("sale_form.html", products=products, entered=quantities), 400
        return render_template("sale_result.html", sale_id=sale_id, total=total,
                               message=services.MSG_SALE_OK)
    return render_template("sale_form.html", products=products, entered={})


# ---------- relatórios (conteúdo ainda não definido pela mercearia) ----------
@bp.route("/relatorios")
@login_required
def reports():
    return render_template("reports.html", sales=db.list_sales(),
                           summary=db.sales_summary(),
                           products=db.list_products())
