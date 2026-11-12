"""Camada de regras de negócio. Não depende de Flask (exceto pela leitura do banco via db.py)."""
from decimal import Decimal, InvalidOperation

from . import db

MSG_SALE_OK = "Venda registrada com sucesso"
MSG_QTY_INVALID = "Informe uma quantidade maior que zero"


class ValidationError(Exception):
    """Erro de validação com mensagem pronta para o usuário."""


# ---------- dinheiro ----------
def parse_price_to_cents(text):
    """Converte '12,50' ou '12.50' em 1250. Levanta ValidationError se inválido."""
    raw = (text or "").strip().replace("R$", "").replace(" ", "")
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValidationError("Informe um preço válido, por exemplo 12,50")
    if not value.is_finite() or value < 0:
        raise ValidationError("Informe um preço válido, por exemplo 12,50")
    cents = value * 100
    if cents != cents.to_integral_value():
        raise ValidationError("O preço deve ter no máximo duas casas decimais")
    return int(cents)


def format_brl(cents):
    reais, centavos = divmod(int(cents), 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"


# ---------- produtos ----------
def parse_int(text, field_label, minimum=0):
    try:
        value = int((text or "").strip())
    except ValueError:
        raise ValidationError(f"Informe um número inteiro válido em {field_label}")
    if value < minimum:
        raise ValidationError(f"{field_label} não pode ser menor que {minimum}")
    return value


def validate_product_form(form):
    name = (form.get("name") or "").strip()
    if not name:
        raise ValidationError("Informe o nome do produto")
    if len(name) > 120:
        raise ValidationError("O nome do produto deve ter no máximo 120 caracteres")
    price_cents = parse_price_to_cents(form.get("price"))
    stock = parse_int(form.get("stock") or "0", "Quantidade em estoque", minimum=0)
    active = form.get("active") == "on"
    return name, price_cents, stock, active


def create_product(form):
    name, price_cents, stock, active = validate_product_form(form)
    return db.insert_product(name, price_cents, stock, active)


def edit_product(product_id, form):
    name, price_cents, stock, active = validate_product_form(form)
    db.update_product(product_id, name, price_cents, stock, active)


# ---------- vendas ----------
def build_sale_items(quantities, products_by_id):
    """quantities: dict {product_id: texto_digitado}. Linhas vazias ou 0 são ignoradas.

    Retorna (itens, total_cents). Levanta ValidationError com a mensagem definida
    no planejamento quando a quantidade é inválida ou nenhuma foi informada.
    """
    items = []
    for pid, text in quantities.items():
        text = (text or "").strip()
        if text == "":
            continue
        try:
            qty = int(text)
        except ValueError:
            raise ValidationError(MSG_QTY_INVALID)
        if qty < 0:
            raise ValidationError(MSG_QTY_INVALID)
        if qty == 0:
            continue
        product = products_by_id.get(pid)
        if product is None or not product["active"]:
            raise ValidationError("Produto indisponível para venda")
        unit = product["price_cents"]
        items.append({
            "product_id": pid,
            "name": product["name"],
            "quantity": qty,
            "unit_price_cents": unit,
            "subtotal_cents": qty * unit,          # Subtotal = Quantidade × Preço unitário
        })
    if not items:
        raise ValidationError(MSG_QTY_INVALID)
    total = sum(i["subtotal_cents"] for i in items)  # Total = Σ Subtotais
    return items, total


def register_sale(quantities, deduct_stock):
    """Valida usando os preços do banco (nunca os enviados pelo navegador) e grava."""
    products = {p["id"]: p for p in db.list_products(only_active=False)}
    items, total = build_sale_items(quantities, products)
    try:
        sale_id = db.insert_sale(items, total, deduct_stock)
    except ValueError as exc:
        name = products[exc.args[0]]["name"]
        raise ValidationError(f"Estoque insuficiente para {name}")
    return sale_id, total
