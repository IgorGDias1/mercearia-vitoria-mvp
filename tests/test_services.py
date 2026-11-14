import pytest

from app import services
from app.services import ValidationError


@pytest.mark.parametrize("text,cents", [
    ("12,50", 1250), ("12.50", 1250), ("R$ 3,00", 300), ("0", 0),
    ("1.234,56", 123456), ("7", 700),
])
def test_parse_price_ok(text, cents):
    assert services.parse_price_to_cents(text) == cents


@pytest.mark.parametrize("text", ["", "abc", "-1", "1,234", "nan", "inf"])
def test_parse_price_invalid(text):
    with pytest.raises(ValidationError):
        services.parse_price_to_cents(text)


def test_format_brl():
    assert services.format_brl(0) == "R$ 0,00"
    assert services.format_brl(1250) == "R$ 12,50"
    assert services.format_brl(123456) == "R$ 1.234,56"


PRODUCTS = {
    1: {"id": 1, "name": "Pão", "price_cents": 150, "active": 1},
    2: {"id": 2, "name": "Leite", "price_cents": 599, "active": 1},
    3: {"id": 3, "name": "Velho", "price_cents": 100, "active": 0},
}


def test_subtotal_and_total():
    items, total = services.build_sale_items({1: "4", 2: "2", 3: ""}, PRODUCTS)
    assert [i["subtotal_cents"] for i in items] == [600, 1198]   # qtd × preço
    assert total == 1798                                          # soma dos subtotais


def test_zero_and_blank_are_ignored():
    items, total = services.build_sale_items({1: "0", 2: "1"}, PRODUCTS)
    assert len(items) == 1 and total == 599


@pytest.mark.parametrize("qtys", [{1: "-1"}, {1: "abc"}, {1: "1.5"}, {1: "0", 2: ""}, {}])
def test_invalid_quantity_message(qtys):
    with pytest.raises(ValidationError) as exc:
        services.build_sale_items(qtys, PRODUCTS)
    assert str(exc.value) == "Informe uma quantidade maior que zero"


def test_inactive_product_rejected():
    with pytest.raises(ValidationError):
        services.build_sale_items({3: "1"}, PRODUCTS)


def test_product_form_validation():
    with pytest.raises(ValidationError):
        services.validate_product_form({"name": " ", "price": "1"})
    name, cents, stock, active = services.validate_product_form(
        {"name": " Café ", "price": "9,90", "stock": "3", "active": "on"})
    assert (name, cents, stock, active) == ("Café", 990, 3, True)
    with pytest.raises(ValidationError):
        services.validate_product_form({"name": "x", "price": "1", "stock": "-2"})


@pytest.mark.parametrize("text,cents", [
    ("  9,90  ", 990), ("0,05", 5), ("1000", 100000), ("2.5", 250), ("R$12,5", 1250),
])
def test_parse_price_edge_cases_ok(text, cents):
    assert services.parse_price_to_cents(text) == cents


@pytest.mark.parametrize("text", ["12,345", "1,2,3", "--5", "R$", "12abc", None])
def test_parse_price_edge_cases_invalid(text):
    with pytest.raises(ValidationError):
        services.parse_price_to_cents(text)


@pytest.mark.parametrize("cents,expected", [
    (0, "R$ 0,00"), (5, "R$ 0,05"), (123456, "R$ 1.234,56"), (100000000, "R$ 1.000.000,00"),
])
def test_format_brl_edge_cases(cents, expected):
    assert services.format_brl(cents) == expected


def test_low_stock_rules():
    ativo_baixo = {"active": 1, "stock": 5}
    ativo_ok = {"active": 1, "stock": 6}
    inativo_baixo = {"active": 0, "stock": 0}
    assert services.is_low_stock(ativo_baixo, 5)
    assert not services.is_low_stock(ativo_ok, 5)
    assert not services.is_low_stock(inativo_baixo, 5)
    assert services.low_stock_products([ativo_baixo, ativo_ok, inativo_baixo], 5) == [ativo_baixo]
