## ERP POS (FastAPI + React)

Stack: FastAPI, SQLAlchemy, Alembic, PostgreSQL, React (Vite + TS), TailwindCSS, Docker, JWT Auth (access/refresh), multi-tenant (header `X-Tenant-ID`).

### Quick start (Docker)

1. Copy env examples and adjust if needed:
   - Backend: `cp backend/.env.example backend/.env`
   - Frontend: `cp frontend/.env.example frontend/.env`
2. Start: `docker-compose up --build`
3. Open:
   - API: http://localhost:8000/docs
   - Frontend: http://localhost:5173

Default seed: no default users. Register via `POST /auth/register` sending `X-Tenant-ID` header.

Tenant scoping: send header `X-Tenant-ID: <tenant_slug>` on all requests.

### Iteration 1 scope (included)
Backend auth (register/login/refresh), product CRUD (tenant-scoped), basic health endpoint, Alembic, tests skeleton. Frontend with login and product list pages.



