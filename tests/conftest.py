import re

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "SECRET_KEY": "test",
        "STOCK_DEDUCT_ON_SALE": True,
    })
    with app.app_context():
        db.insert_user("caixa", generate_password_hash("senha123"))
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def get_csrf(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


@pytest.fixture
def logged(client):
    token = get_csrf(client)
    client.post("/login", data={"username": "caixa", "password": "senha123", "_csrf": token})
    return client


@pytest.fixture
def seed_products(app):
    with app.app_context():
        pao = db.insert_product("Pão francês", 150, 100, True)
        leite = db.insert_product("Leite 1L", 599, 10, True)
        velho = db.insert_product("Produto inativo", 1000, 5, False)
    return {"pao": pao, "leite": leite, "velho": velho}
