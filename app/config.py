"""Configuração da aplicação.

Itens marcados como PENDENTE no documento do projeto ficam aqui como
chaves configuráveis, para que a decisão da Mercearia Vitória possa ser
aplicada sem mexer na lógica de negócio.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "mercearia.db"))

    # PENDENTE (não definido pela mercearia): a venda dá baixa automática no estoque?
    # Mantido como opção. Altere para False se a mercearia decidir que não.
    STOCK_DEDUCT_ON_SALE = os.environ.get("STOCK_DEDUCT_ON_SALE", "1") == "1"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Expiração de sessão: NÃO DEFINIDO. Valor técnico provisório de 8 horas.
    PERMANENT_SESSION_LIFETIME = 8 * 60 * 60
