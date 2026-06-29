# Database

## Engine

Configured via `DATABASE_URL` in `backend/.env`:

- **Development:** `sqlite:///./credenceai.db`
- **Production:** `postgresql://user:pass@host:5432/credenceai`

## Migrations (Alembic)

Location: `backend/migrations/versions/`

```bash
cd backend
set PYTHONPATH=src
alembic upgrade head
alembic current
alembic history
```

Config: `backend/alembic.ini` (`script_location = migrations`, `prepend_sys_path = src`)

## Migration chain

```
392713c6803a_initial_migration
  → 3e01201308cd_add_version_2_tables
    → 4a01_add_agent_budget_table
      → 4a02_add_agent_decisions_table
        → fda5d7dfffb3_add_api_keys_table
          → ad9bb0cbfcdb_add_user_id_to_jobs
```

The `ad9bb0cbfcdb` migration adds `user_id` to the `jobs` table for per-user job scoping.

## Core tables

| Table | Purpose |
|-------|---------|
| `jobs` | Search/job records |
| `normalized_results` | Structured crawl results |
| `users` | OAuth / session users |
| `api_keys` | Programmatic API access |
| `monitors` | Topic monitors |
| `collections` | Saved collections |

ORM models: `backend/src/app/models.py`

## Backup (Postgres)

```bash
pg_dump -U user -d credenceai > backup.sql
psql -U user -d credenceai < backup.sql
```

## SQLite (dev)

Copy `backend/credenceai.db` for backup. File is gitignored.

## Startup DDL

`main.py` lifespan calls `Base.metadata.create_all()` for idempotent table creation. Prefer Alembic for schema changes in shared environments.
