from app import db
from tests.conftest import get_csrf


def test_login_required_redirects(client):
    resp = client.get("/")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_login_wrong_password(client):
    token = get_csrf(client)
    resp = client.post("/login", data={"username": "caixa", "password": "errada", "_csrf": token})
    assert "Usuário ou senha incorretos" in resp.get_data(as_text=True)


def test_post_without_csrf_is_rejected(client):
    resp = client.post("/login", data={"username": "caixa", "password": "senha123"})
    assert resp.status_code == 400


def test_open_redirect_blocked(client):
    token = get_csrf(client)
    resp = client.post("/login?next=//evil.com",
                       data={"username": "caixa", "password": "senha123", "_csrf": token})
    assert resp.status_code == 302 and "evil.com" not in resp.headers["Location"]


def test_menu_after_login(logged):
    html = logged.get("/").get_data(as_text=True)
    assert "Registrar vendas" in html and "Consultar produtos" in html


def test_sale_flow_updates_stock(app, logged, seed_products):
    page = logged.get("/vendas/nova").get_data(as_text=True)
    assert "Produto inativo" not in page            # só produtos ativos
    token = get_csrf(logged, "/vendas/nova")
    resp = logged.post("/vendas/nova", data={
        "_csrf": token,
        f"qty_{seed_products['pao']}": "4",
        f"qty_{seed_products['leite']}": "2",
    })
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Venda registrada com sucesso" in html
    assert "R$ 17,98" in html
    with app.app_context():
        assert db.get_product(seed_products["pao"])["stock"] == 96
        assert db.get_product(seed_products["leite"])["stock"] == 8
        assert db.sales_summary()["n"] == 1


def test_sale_without_quantity_shows_validation_message(app, logged, seed_products):
    token = get_csrf(logged, "/vendas/nova")
    resp = logged.post("/vendas/nova", data={"_csrf": token})
    assert resp.status_code == 400
    assert "Informe uma quantidade maior que zero" in resp.get_data(as_text=True)
    with app.app_context():
        assert db.sales_summary()["n"] == 0


def test_insufficient_stock_rolls_back(app, logged, seed_products):
    token = get_csrf(logged, "/vendas/nova")
    resp = logged.post("/vendas/nova", data={
        "_csrf": token,
        f"qty_{seed_products['pao']}": "1",
        f"qty_{seed_products['leite']}": "11",      # estoque é 10
    })
    assert resp.status_code == 400
    assert "Estoque insuficiente para Leite 1L" in resp.get_data(as_text=True)
    with app.app_context():
        assert db.sales_summary()["n"] == 0
        assert db.get_product(seed_products["pao"])["stock"] == 100   # nada foi baixado


def test_stock_not_deducted_when_option_off(app, logged, seed_products):
    app.config["STOCK_DEDUCT_ON_SALE"] = False
    token = get_csrf(logged, "/vendas/nova")
    logged.post("/vendas/nova", data={"_csrf": token, f"qty_{seed_products['pao']}": "5"})
    with app.app_context():
        assert db.get_product(seed_products["pao"])["stock"] == 100


def test_client_cannot_override_price(app, logged, seed_products):
    token = get_csrf(logged, "/vendas/nova")
    resp = logged.post("/vendas/nova", data={
        "_csrf": token, f"qty_{seed_products['pao']}": "2", "price_1": "0,01"})
    assert "R$ 3,00" in resp.get_data(as_text=True)


def test_product_create_and_edit_price(app, logged):
    token = get_csrf(logged, "/produtos/novo")
    resp = logged.post("/produtos/novo", data={
        "_csrf": token, "name": "Bolo", "price": "25,00", "stock": "3", "active": "on"})
    assert resp.status_code == 302
    with app.app_context():
        p = db.list_products(search="Bolo")[0]
        assert p["price_cents"] == 2500
    token = get_csrf(logged, f"/produtos/{p['id']}/editar")
    logged.post(f"/produtos/{p['id']}/editar", data={
        "_csrf": token, "name": "Bolo", "price": "27,50", "stock": "3"})
    with app.app_context():
        updated = db.get_product(p["id"])
        assert updated["price_cents"] == 2750 and updated["active"] == 0


def test_invalid_product_shows_error(logged):
    token = get_csrf(logged, "/produtos/novo")
    resp = logged.post("/produtos/novo", data={"_csrf": token, "name": "", "price": "1"})
    assert resp.status_code == 400
    assert "Informe o nome do produto" in resp.get_data(as_text=True)


def test_sql_injection_in_search_is_harmless(app, logged, seed_products):
    resp = logged.get("/produtos?q=' OR 1=1; DROP TABLE product;--")
    assert resp.status_code == 200
    with app.app_context():
        assert len(db.list_products()) == 3


def test_reports_page(logged, seed_products):
    assert logged.get("/relatorios").status_code == 200


def test_inactive_product_cannot_be_sold_even_if_posted(app, logged, seed_products):
    """Mesmo forjando o campo no formulário, o produto inativo nunca é vendido nem baixado."""
    token = get_csrf(logged, "/vendas/nova")
    resp = logged.post("/vendas/nova", data={
        "_csrf": token,
        f"qty_{seed_products['velho']}": "1",
    })
    assert resp.status_code == 400
    assert "Venda registrada com sucesso" not in resp.get_data(as_text=True)
    with app.app_context():
        assert db.sales_summary()["n"] == 0
        assert db.get_product(seed_products["velho"])["stock"] == 5


def test_missing_secret_key_gets_random_temporary_key(tmp_path):
    from app import create_app
    a = create_app({"TESTING": True, "DATABASE": str(tmp_path / "a.db"), "SECRET_KEY": None})
    b = create_app({"TESTING": True, "DATABASE": str(tmp_path / "b.db"), "SECRET_KEY": None})
    assert a.config["SECRET_KEY"] and len(a.config["SECRET_KEY"]) >= 32
    assert a.config["SECRET_KEY"] != "troque-esta-chave-em-producao"
    assert a.config["SECRET_KEY"] != b.config["SECRET_KEY"]


def test_session_cookie_flags(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_health_endpoint_is_public_and_ok(client):
    resp = client.get("/saude")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
