# Agenda Village Pet 🐾

MVP de **agendamento online de banho e tosa** para a unidade Village Pet – BR-116 (Taboão da Serra/SP),
desenvolvido na disciplina **Projeto de Software** (ADS – Cruzeiro do Sul), Experiências Práticas I a III.

O agendamento hoje depende do WhatsApp da loja, o mesmo canal do Disk Ração. O MVP permite que o tutor
marque sozinho em um horário realmente livre, que a equipe acompanhe a agenda do dia com a ficha do pet e
que a gerência meça faltas, ocupação e recorrência. ODS relacionado: **ODS 8 – Trabalho decente e crescimento
econômico** (metas 8.2 e 8.3).

> Projeto acadêmico. Todos os dados de exemplo (tutores, pets, e-mails) são **fictícios**.

## Funcionalidades

| Requisito | Descrição | Onde |
|---|---|---|
| RF01 | Cadastro de tutor (com aceite LGPD) e de pets | `routers/auth.py`, `routers/tutor.py`, `cadastro.html`, `pets.html` |
| RF02 | Horários livres por serviço, data e porte do pet | `services/agendamento_service.py` |
| RF03 | Agendamento online sem sobreposição; conflito retorna 3 alternativas | `services/agendamento_service.py`, `agendar.html` |
| RF04 | Agenda do dia da equipe com ficha do pet e status | `routers/equipe.py`, `equipe.html` |
| RF05 | Agendamento pelo balcão/telefone na mesma agenda | `routers/equipe.py` |
| RF06 | Lembrete da véspera com link de WhatsApp pré-preenchido | `services/lembrete_service.py` |
| RF07/RF08 | Pets sem retorno e painel de indicadores da gerência | `services/indicador_service.py` |

## Arquitetura

Monolito em camadas (cliente-servidor):

```
Front-end PWA (HTML/CSS/JS)  →  API FastAPI (rotas + Pydantic + JWT)
        →  Serviços (regras de negócio)  →  Repositórios (SQLAlchemy)  →  PostgreSQL / SQLite
```

- **Python 3.12**, FastAPI, SQLAlchemy 2, Pydantic 2
- Senhas com **Argon2id** (argon2-cffi), sessão com **JWT** (PyJWT), bloqueio após 5 tentativas
- Restrição única `(id_profissional, data_hora_inicio)` + verificação de sobreposição no serviço
- Cabeçalhos de segurança (CSP, nosniff) e mensagens de erro genéricas

## Como rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m app.seed            # cria dados fictícios em SQLite (agenda.db)
uvicorn app.main:app --reload # http://localhost:8000
```

Logins de demonstração (fictícios): `carla@exemplo.com` (tutor), `atendente@exemplo.com`,
`gerente@exemplo.com` — senha `senha-de-teste-123`. Documentação interativa da API: `/docs`.

Com PostgreSQL: `docker compose up --build`.

## Testes e integração contínua

```bash
pytest --cov=app --cov-report=term-missing
```

- `tests/unit/` – regras puras: cálculo de horários livres, sobreposição, transições de status,
  hash de senha, bloqueio de login, indicadores.
- `tests/integration/` – API + serviço + banco: cadastro/login, IDOR, XSS, injeção SQL, conflito de horário,
  agenda da equipe, permissões por perfil, lembretes.
- O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda **ruff**, **pytest com cobertura
  mínima de 80%** e **pip-audit** em todo push e pull request para `main`.

## Fluxo de trabalho com Git

- `main` protegida; cada funcionalidade em uma branch `feat/…`, `test/…`, `ci/…` ou `docs/…`.
- Commits no padrão **Conventional Commits** (`feat:`, `fix:`, `test:`, `ci:`, `docs:`, `refactor:`).
- Toda mudança entra por **Pull Request** com o checklist de revisão do template e CI verde.

## Variáveis de ambiente

Veja [`.env.example`](.env.example). Nenhum segredo fica no código.
