-- Esquema provisório (o documento do projeto NÃO define um modelo aprovado).
-- Contém apenas o necessário para: produtos, vendas, itens de venda e usuários.
-- Valores monetários são guardados em centavos (inteiro) para evitar erros de ponto flutuante.

CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    stock       INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_product_active_name ON product (active, name);

CREATE TABLE IF NOT EXISTS sale (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0)
);

CREATE TABLE IF NOT EXISTS sale_item (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id          INTEGER NOT NULL REFERENCES sale (id) ON DELETE CASCADE,
    product_id       INTEGER NOT NULL REFERENCES product (id),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    subtotal_cents   INTEGER NOT NULL CHECK (subtotal_cents >= 0)
);
CREATE INDEX IF NOT EXISTS idx_sale_item_sale ON sale_item (sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_created ON sale (created_at);
