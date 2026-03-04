# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Thinking Platform is a multi-service application with three independently running services:

- **Python Backend (FastAPI)** on port 8001 — handles auth (login/register/JWT)
- **Java Backend (Spring Boot)** on port 8002 — handles modules and permissions
- **Vue 3 Frontend (Vite)** on port 3000 — proxies `/api/auth` → :8001, `/api/modules` → :8002

### Key Gotchas

- **bcrypt compatibility**: Must use `bcrypt==4.0.1` (not 5.x) due to passlib incompatibility with newer bcrypt.
- **Database**: External PostgreSQL at `111.231.145.50:2345`, database name `thinking`. Schema is in `sql/init.sql`.
- **Maven**: Not pre-installed in the environment; install with `sudo apt-get install -y maven` if missing.
- **Vite proxy**: The Vue frontend dev server proxies API calls via `vite.config.ts` — no Nginx needed in dev mode.
- **Java build**: Run `mvn package -DskipTests` in `backend-java/` before starting the Java service.

### Running Services

See `README.md` Quick Start section for commands. All three services must be running for the full application to work.

### Experiment Module

The experiment module provides drug dose-response assay (孔板) management:
- 96-well plate editor with batch fill support
- Statistics: grouped by compound+concentration, computes mean/max/min/std
- 4-Parameter Logistic (4PL) curve fitting via scipy for IC50 calculation
- ECharts dose-response charts with fitted curves

The curve fitting API is at `/api/experiment/curve-fit/{plate_id}` and requires at least 4 concentration data points per compound.

### Linting / Testing

- Frontend: `cd frontend && npx vue-tsc --noEmit` (type check), `cd frontend && npx vite build` (build check)
- Python: `cd backend-python && python -m py_compile main.py experiment.py` (syntax check)
- Java: `cd backend-java && mvn compile` (compile check)
