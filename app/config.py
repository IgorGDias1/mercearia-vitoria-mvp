"""Configuração da aplicação.

Itens marcados como PENDENTE no documento do projeto ficam aqui como
chaves configuráveis, para que a decisão da Mercearia Vitória possa ser
aplicada sem mexer na lógica de negócio.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # Sem valor padrão fixo: uma chave pública no código permitiria forjar sessões.
    # Se a variável SECRET_KEY não existir, create_app() gera uma chave aleatória temporária.
    SECRET_KEY = os.environ.get("SECRET_KEY") or None
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "mercearia.db"))

    # PENDENTE (não definido pela mercearia): a venda dá baixa automática no estoque?
    # Mantido como opção. Altere para False se a mercearia decidir que não.
    STOCK_DEDUCT_ON_SALE = os.environ.get("STOCK_DEDUCT_ON_SALE", "1") == "1"

    # Alerta de estoque baixo (sugerido pelo representante da mercearia na validação).
    # O limite exato NÃO foi definido pela mercearia: valor provisório, ajustável por variável de ambiente.
    LOW_STOCK_THRESHOLD = int(os.environ.get("LOW_STOCK_THRESHOLD", "5"))

    # Defina SESSION_COOKIE_SECURE=1 quando o sistema for servido por HTTPS.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Expiração de sessão: NÃO DEFINIDO. Valor técnico provisório de 8 horas.
    PERMANENT_SESSION_LIFETIME = 8 * 60 * 60
