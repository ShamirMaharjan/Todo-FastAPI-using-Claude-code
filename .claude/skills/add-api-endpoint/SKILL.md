---
name: add-api-endpoint
description: Guided workflow to implement a new FastAPI REST endpoint using TDD
---
Follow these exact steps to add a new API endpoint:
1. Define request and response schemas in `app/schemas.py` using Pydantic v2.
2. Write a failing async test in `tests/test_api.py` targeting the new route.
3. Add the router path and database logic in `app/routers/`.
4. Verify response models match `CLAUDE.md` guidelines and pass all tests.