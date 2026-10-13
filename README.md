# Market Inventory System

Sistema de gestão de estoque de mercado — **Django + React + PostgreSQL**.

Cadastro de produtos e fornecedores, vínculos entre eles, controle de validade
(produtos vencidos e a vencer), alertas de estoque baixo, dashboard com gráficos
e exportação em CSV. Substitui o protótipo legado em Tkinter/SQLite presente em
`legacy/`.

## Funcionalidades

- **Dashboard** — resumo (produtos, fornecedores, unidades, valor do estoque),
  gráficos de valor imobilizado, situação das validades, estoque por categoria e
  produtos por fornecedor.
- **Produtos** — cadastro, edição, exclusão, busca por nome, filtro por situação
  (no prazo / a vencer / vencido) e por estoque baixo.
- **Fornecedores** — cadastro, edição, exclusão e lista de produtos vinculados.
- **Vínculos** — vincular/desvincular fornecedores a produtos.
- **Alertas** — produtos vencidos, a vencer (30 dias) e estoque baixo (mínimo
  configurável, padrão 25).
- **Exportação CSV** — produtos e fornecedores (delimitador `;`, compatível
  com Excel pt-BR).

## Stack

| Camada   | Tecnologias                                |
| -------- | ------------------------------------------ |
| Backend  | Python 3.10+, Django 5, PostgreSQL 16, WhiteNoise, Gunicorn |
| Frontend | React 18, Vite 5, Recharts                 |
| Tooling  | Docker Compose, uv (Python), npm (frontend)|

## Estrutura do projeto

```
.
├── backend/
│   ├── config/                  # settings, urls, wsgi/asgi
│   ├── inventory/               # app Django (models, views, urls, testes)
│   │   └── management/commands/ # seed_demo, wait_for_db
│   └── cli.py                   # entry point `market-inventory`
├── frontend/
│   └── src/
│       ├── components/          # Dashboard, Products, Suppliers, Alerts, Modal
│       ├── api.js
│       └── App.jsx
├── legacy/                      # protótipo original (Tkinter + SQLite)
├── Dockerfile                   # imagem única: API + frontend buildado
├── docker-compose.yml           # web + PostgreSQL 16
├── docker-entrypoint.sh         # wait_for_db → migrate → seed → gunicorn
├── start.ps1                    # inicialização local completa no Windows
├── manage.py
└── pyproject.toml
```

## Requisitos

- **Com Docker**: apenas [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  (inclui o Docker Compose).
- **Sem Docker (local)**: Python 3.10+, Node.js 18+ e npm, e um PostgreSQL 14+
  (serviço do Windows ou via Docker). Opcional: [uv](https://docs.astral.sh/uv/).

## Execução com Docker (recomendado)

Um único comando sobe PostgreSQL + backend + frontend (buildado na imagem):

```bash
docker compose up --build
```

Acesse <http://localhost:8000>. Na primeira execução o banco é criado, as
migrações aplicadas e dados de demonstração carregados automaticamente
(entrypoint `docker-entrypoint.sh`). Os dados persistem no volume `pgdata`.

Comandos úteis:

```bash
docker compose up -d          # sobe em segundo plano
docker compose down           # para (o volume com dados é mantido)
docker compose down -v        # para e apaga o banco
docker compose logs -f web    # acompanha os logs
docker compose exec web python manage.py test   # roda os testes no container
```

## Execução local no Windows (sem Docker)

Com o PostgreSQL instalado e rodando (ou o Docker Desktop disponível para o
script subir só o banco), tudo é feito por um script:

```powershell
.\start.ps1
```

O script, de forma automática e idempotente:

1. Carrega o `.env`, se existir (senão usa os padrões).
2. Cria/atualiza o ambiente Python com `uv sync` ou `venv + pip`.
3. Detecta o PostgreSQL (tenta a porta 5432 → serviço do Windows →
   `docker compose up -d db` como fallback).
4. **Cria o banco de dados, se ainda não existir**.
5. Roda as migrações e popula dados de demonstração.
6. Gera o build do frontend com npm, se `frontend/dist` não existir.
7. Sobe o servidor em <http://localhost:8000>.

Opções:

```powershell
.\start.ps1 -Port 8080           # outra porta
.\start.ps1 -RebuildFrontend     # força novo build do frontend
.\start.ps1 -SkipFrontend        # não mexe no frontend
.\start.ps1 -NoSeed              # pula o dados de demonstração
```

> Política de execução do PowerShell: se aparecer erro de script bloqueado,
> rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### Execução manual (Linux/macOS ou passo a passo)

Backend (porta 8000):

```bash
uv sync                                   # ou pip install .
uv run python manage.py wait_for_db
uv run python manage.py migrate
uv run python manage.py seed_demo        # dados de demonstração (opcional)
uv run python manage.py runserver
```

Frontend em modo de desenvolvimento (porta 5173, com proxy para `/api`):

```bash
cd frontend
npm install
npm run dev
```

Para servir tudo pelo Django, build o frontend (`cd frontend && npm run build`)
e acesse <http://localhost:8000>.

### CLI empacotado

Após `uv sync` (ou `pip install .`), o comando abaixo aguarda o banco, migra,
popula e sobe o servidor:

```bash
uv run market-inventory
```

Qualquer comando do Django também funciona: `uv run market-inventory test`.

## Testes

É necessário um PostgreSQL acessível (suba com `docker compose up -d db` ou
use o serviço local):

```bash
uv run python manage.py test
# ou dentro do container:
docker compose exec web python manage.py test
```

## API

Base: `/api/`

| Método     | Rota                                   | Descrição                         |
| ---------- | -------------------------------------- | --------------------------------- |
| GET/POST   | `/api/products/`                       | Lista (com `q`, `status`, `threshold`) / cria produtos |
| GET/PATCH/DELETE | `/api/products/<id>/`           | Detalha, atualiza ou exclui       |
| POST       | `/api/products/<id>/link/`             | Vincula fornecedor (`supplier_id`) |
| DELETE     | `/api/products/<id>/link/<fid>/`       | Desvincula fornecedor             |
| GET/POST   | `/api/suppliers/`                      | Lista / cria fornecedores         |
| GET/PATCH/DELETE | `/api/suppliers/<id>/`          | Detalha, atualiza ou exclui       |
| GET        | `/api/dashboard/`                      | Métricas e séries para os gráficos |
| GET        | `/api/products/export/`                | Exporta produtos em CSV           |
| GET        | `/api/suppliers/export/`               | Exporta fornecedores em CSV       |

Regras de situação: **vencido** (validade < hoje), **a vencer** (validade até
hoje + 30 dias), **no prazo** (demais).

## Configuração (.env)

Copie `.env.example` para `.env` e ajuste (usado pelo `docker compose` e pelo
`start.ps1`):

| Variável              | Padrão                     | Descrição                     |
| --------------------- | -------------------------- | ----------------------------- |
| `POSTGRES_DB`         | `market_inventory`         | Nome do banco                 |
| `POSTGRES_USER`       | `postgres`                 | Usuário do banco              |
| `POSTGRES_PASSWORD`   | `postgres`                 | Senha do banco                |
| `POSTGRES_HOST`       | `127.0.0.1` (`db` no Docker)| Host do banco                |
| `POSTGRES_PORT`       | `5432`                     | Porta do banco                |
| `DJANGO_SECRET_KEY`   | chave de desenvolvimento   | Chave secreta do Django       |
| `DJANGO_DEBUG`        | `1` (`0` na imagem Docker)| `0` desativa o modo debug     |
| `DJANGO_ALLOWED_HOSTS`| `*`                        | Hosts permitidos (separados por vírgula) |
| `WEB_PORT`            | `8000`                     | Porta exposta pelo servidor   |
| `GUNICORN_WORKERS`    | `2`                        | Workers do Gunicorn (Docker)  |

## Licença

MIT — veja [LICENSE](LICENSE).
