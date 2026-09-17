---
name: migrate
description: Generate and apply an Alembic migration for model schema updates
---
1. Check if `alembic/` exists; if missing, run `alembic init -t async alembic`.
2. Ensure `alembic/env.py` imports `Base` from `app.database` and sets `target_metadata = Base.metadata`.
3. Generate a migration script: `alembic revision --autogenerate -m "$ARG1"`.
4. Apply the migration: `alembic upgrade head`.