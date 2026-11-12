# Decisões pendentes da Mercearia Vitória

O documento do projeto marca os pontos abaixo como **NÃO DEFINIDO**. Onde o código precisou de um
comportamento mínimo para funcionar, ele foi isolado para ser fácil de mudar. Cada item deve ser
confirmado com a mercearia antes de virar regra.

| Ponto | O que o código faz hoje | Onde mudar | Decisão da mercearia |
|---|---|---|---|
| Baixa de estoque após a venda | Baixa automática; bloqueia venda acima do estoque | `STOCK_DEDUCT_ON_SALE` em `app/config.py` | _pendente_ |
| Quantidades | Apenas números inteiros (venda por peso não definida) | `services.build_sale_items` | _pendente_ |
| Arredondamento | Valores em centavos inteiros; preço com no máximo 2 casas | `services.parse_price_to_cents` | _pendente_ |
| Expiração de sessão | 8 horas (provisório) | `PERMANENT_SESSION_LIFETIME` | _pendente_ |
| Relatórios | Lista de vendas e estoque, sem filtros nem exportação | `routes.reports`, `templates/reports.html` | _pendente_ |
| Perfis e permissões | Todo usuário logado acessa tudo | `app/auth.py` | _pendente_ |
| Backup | Cópia manual de `instance/mercearia.db` | — | _pendente_ |

## Fora do escopo até que sejam confirmados

Fiado, clientes, fornecedores, formas de pagamento, descontos, custo e margem, validade,
cancelamento de venda, comprovante, abertura e fechamento de caixa, Pix, nota fiscal, balança e
leitor de código de barras.
