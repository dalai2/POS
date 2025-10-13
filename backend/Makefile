PY=python
PIP=pip

.PHONY: setup dev test lint fmt migrate upgrade

setup:
	$(PY) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check . || true

fmt:
	$(PY) -m ruff check --fix . || true

migrate:
	alembic revision --autogenerate -m "auto"

upgrade:
	alembic upgrade head





