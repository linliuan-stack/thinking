# Thinking Platform

统一模块管理平台 — A modular platform with Vue 3 frontend, Python (FastAPI) and Java (Spring Boot) backends, PostgreSQL database, and Nginx HA reverse proxy.

## Architecture

```
┌──────────────┐
│  Vue 3 (3000)│
└──────┬───────┘
       │
┌──────▼───────┐
│  Nginx (80)  │  ← HA reverse proxy with upstream failover
├──────┬───────┤
│      │       │
▼      ▼       ▼
┌──────┐ ┌──────┐
│Python│ │ Java │
│:8001 │ │:8002 │  ← Primary instances
│:8011 │ │:8012 │  ← Backup instances
└──┬───┘ └──┬───┘
   │        │
   ▼        ▼
┌──────────────┐
│  PostgreSQL  │
│  :2345       │
└──────────────┘
```

## Services

| Service | Port | Technology | Responsibility |
|---------|------|------------|----------------|
| Frontend | 3000 | Vue 3 + Vite + Element Plus | UI (login, dashboard) |
| Auth Service | 8001 | Python FastAPI | Authentication, user management |
| Module Service | 8002 | Java Spring Boot | Module management, permissions |
| Nginx | 80 | Nginx | Reverse proxy, HA load balancing |
| Database | 2345 | PostgreSQL | Data persistence |

## Quick Start (Dev)

```bash
# Install Python deps
cd backend-python && pip install -r requirements.txt

# Build Java service
cd backend-java && mvn package -DskipTests

# Install frontend deps
cd frontend && npm install

# Start services
cd backend-python && python main.py          # :8001
cd backend-java && java -jar target/module-service-1.0.0.jar  # :8002
cd frontend && npx vite --port 3000          # :3000
```

## Docker Compose (Production-like)

```bash
docker-compose up -d
```
