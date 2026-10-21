# Hub Pessoal

Pequeno projeto que reúne notícias e informações financeiras num resumo matinal: um dashboard
somente leitura dos dados do [Banco](../Banco) e digests de notícias (AI e Finanças) gerados
pelo Gemini a partir de feeds RSS.

- **Backend:** FastAPI em `backend/` (porta 8000)
- **Frontend:** React + Vite em `frontend/` (porta 5173)

## Pré-requisitos

- Python 3.12+
- Node.js 20+ (o `start.sh` carrega o `nvm` automaticamente, se existir)
- O código de domínio do Banco vive em `backend/banco/`. O banco de dados fica em
  `~/.local/share/banco/banco.db` (criado com contas e categorias padrão se não existir; cópia
  diária em `backups/`, últimas 14). O `hub.db` fica em `~/.local/share/hubpessoal/`.
- Uma chave da API do Gemini (camada gratuita) para gerar os digests de notícias

## Instalação (uma vez)

Backend:

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Frontend:

```bash
cd frontend && npm install
```

Crie o arquivo `backend/.env` com a chave do Gemini:

```
GEMINI_API_KEY=sua-chave-aqui
# Opcional: outro caminho para o banco do Banco (padrão: ~/.local/share/banco/banco.db)
# BANCO_DB_PATH=/caminho/para/banco.db
```

## Rodando

Na raiz do projeto, um comando sobe os dois servidores. Ctrl+C para os dois:

```bash
./start.sh
```

Depois abra http://localhost:5173. A documentação da API fica em http://localhost:8000/docs.

Para subir só uma parte, use `./start.sh backend` ou `./start.sh frontend`.

O Vite encaminha as chamadas `/api` para `localhost:8000` (`frontend/vite.config.js`). Se outro
projeto estiver usando as portas 8000 ou 5173, encerre-o antes, porque o Hub não sobe em outras
portas sem mudar essa configuração.

## Testes

```bash
cd backend && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/python -m pytest
```

Os testes usam um banco SQLite temporário e nunca tocam no `banco.db` real.

## Documentação

- [`PLAN.md`](PLAN.md): arquitetura e marcos
- [`PRD.md`](PRD.md): requisitos do overhaul de UI
- [`DESIGN.md`](DESIGN.md): sistema visual (paleta, tipografia, componentes)
- [`CONTEXT.md`](CONTEXT.md): estado atual do projeto e onde a última sessão parou
