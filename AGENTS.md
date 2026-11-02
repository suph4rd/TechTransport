# Repository Guidelines

## Project Structure & Module Organization

Tech Transport is a local equipment-search MVP for Belarus, using FastAPI, Vue 3 with TypeScript, and PostgreSQL.

- `backend/app/`: API setup, configuration, database sessions, error handling, and routers.
- `backend/migrations/`: Alembic environment and versioned schema migrations.
- `backend/tests/`: health endpoint, error contract, and lifecycle tests.
- `frontend/src/`: Vue components and TypeScript entry point; styles currently live in `App.vue`.
- `compose.yaml`: local services and persistent database/photo volumes.
- `README.md`: operational instructions; `start_project_plan.md` and `project_plan.md`: planned functionality.

## Build, Test, and Development Commands

Run from the repository root with Docker Compose v2 installed:

- `cp .env.example .env`: initialize local settings.
- `docker compose up --build -d`: build and start services; backend startup applies migrations.
- `docker compose logs -f backend frontend db`: inspect logs.
- `docker compose exec backend python -m pytest -q`: run backend tests.
- `docker compose exec frontend npm run build`: check TypeScript and build frontend assets.
- `docker compose exec backend alembic upgrade head`: apply migrations.
- `docker compose down`: stop services while retaining data.

The UI runs at `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`. Rebuild after code, dependency, or environment changes.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case functions/modules, and PascalCase classes in Python. Follow existing Vue components with `<script setup lang="ts">`, two-space indentation, and camelCase variables/functions. TypeScript strict mode is enabled. No formatter or linter is configured; follow surrounding code. Keep dependencies pinned and update corresponding lockfiles.

## Testing Guidelines

Name Python files `test_*.py` and functions `test_*`. Use pytest and FastAPI TestClient; clear dependency overrides after tests. Cover changed behavior, failure responses, and sensitive-data handling. No coverage threshold or frontend test framework is configured; run the frontend build and manually check UI changes.

## Commit & Pull Request Guidelines

History contains only `init`, so no established commit convention exists. Use concise, imperative subjects. PRs should explain changes, list validation commands/results, link relevant issues, and include screenshots for UI changes. Document configuration or migration changes.

## Security & Configuration

Keep `.env` and credentials out of Git. Preserve sanitized API errors and logs. Database writes require explicit `commit()`; import new models in `backend/migrations/env.py` for migration discovery. Avoid `docker compose down -v`: it deletes database and photo volumes.
