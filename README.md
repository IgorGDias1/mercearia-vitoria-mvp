# Mercearia Vitória — MVP de gerenciamento comercial

Projeto de Otimização dos Processos da Mercearia Vitória (Moreira César, Pindamonhangaba–SP).
Problema que originou o projeto: lentidão do software de caixa. Funcionalidade central: **registro de vendas**.

Stack: Python, Flask, Bootstrap 5, SQLite. Arquitetura monolítica em camadas:

| Camada | Arquivos |
|---|---|
| Interface | `app/routes.py`, `app/templates/`, `app/static/` |
| Regras de negócio | `app/services.py` |
| Dados | `app/db.py`, `app/schema.sql` |
| Autenticação/segurança | `app/auth.py` |

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

flask --app run create-user caixa    # pede a senha; cria o primeiro usuário
export SECRET_KEY="uma-chave-longa-e-aleatoria"
python run.py                        # http://127.0.0.1:5000
```

### No Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # se bloquear: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
pip install -r requirements-dev.txt

flask --app run create-user caixa       # pede a senha; cria o primeiro usuário
$env:SECRET_KEY = "uma-chave-longa-e-aleatoria"
python run.py                           # http://127.0.0.1:5000
```

No Prompt de Comando (cmd), ative com `.venv\Scripts\activate.bat` e defina a chave com `set SECRET_KEY=...`.

Testes: `python -m pytest -v`

## Funcionalidades (escopo do MVP)

- Login (autenticação por sessão, senha com hash, proteção CSRF, consultas parametrizadas)
- Cadastro, consulta e edição de produtos (nome, preço, estoque, ativo/inativo) — a edição do preço cobre o "gerenciamento de preços"
- Registro de vendas: produtos ativos, quantidades, subtotal (`quantidade × preço`) e total (`soma dos subtotais`); o servidor sempre recalcula usando os preços do banco
- Relatórios iniciais: lista das últimas vendas e estoque atual
- Mensagens: "Venda registrada com sucesso" e "Informe uma quantidade maior que zero"
- Acessibilidade: contraste, rótulos, navegação por teclado, foco visível, botões com no mínimo 44×44 px, mensagens com ícone + texto (não só cor)

## Decisões que ainda dependem da mercearia

O documento do projeto marca estes pontos como NÃO DEFINIDO. Onde o código precisou de um comportamento mínimo, ele foi isolado para ser fácil de mudar:

| Ponto | O que o código faz hoje | Como mudar |
|---|---|---|
| Baixa de estoque após a venda | Dá baixa automática e **bloqueia** venda acima do estoque | `STOCK_DEDUCT_ON_SALE=0` desliga a baixa (`app/config.py`) |
| Quantidades | Apenas números inteiros (venda por peso não definida) | `services.build_sale_items` |
| Arredondamento | Valores em centavos inteiros; preço com no máximo 2 casas | `services.parse_price_to_cents` |
| Expiração de sessão | 8 horas (provisório) | `PERMANENT_SESSION_LIFETIME` |
| Relatórios | Sem filtros nem exportação | `routes.reports`, `templates/reports.html` |
| Perfis/permissões | Todo usuário logado acessa tudo | `app/auth.py` |

Não implementados de propósito (não confirmados): fiado, clientes, fornecedores, formas de pagamento, descontos, custo/margem, validade, cancelamento de venda, comprovante, abertura/fechamento de caixa, Pix, nota fiscal, balança, leitor de código de barras, backup automático.

## Backup

Estratégia não definida. Enquanto isso, o banco é o arquivo `instance/mercearia.db`; copiar esse arquivo faz um backup completo.
