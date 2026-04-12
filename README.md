# VAGVIN

`VAGVIN` is a Django application for VIN-based vehicle reports, payment handling, and operational monitoring.

The project combines report generation, user accounts, payment providers, and a Docker-based local stack with Prometheus and Grafana. It is closer to a product-shaped web application than a toy demo.

## Highlights

- multi-provider vehicle report workflow
- payment integrations for Robokassa, YooKassa, and Heleket
- user accounts, reviews, and admin-side moderation flows
- PostgreSQL-backed Django application
- Docker-based local stack
- Prometheus and Grafana monitoring included in the repository

## Stack

- Python
- Django 5
- PostgreSQL
- Gunicorn
- Docker Compose
- Prometheus
- Grafana

## Quick start

Clone the repository:

```bash
git clone https://github.com/chupakobra6/vagvin.git
cd vagvin
```

Create local configuration:

```bash
cp .env.example .env
```

Start the Docker stack:

```bash
docker compose up -d --build
docker compose ps
```

The main application is exposed on `http://localhost:9999`.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

If you need admin access:

```bash
python manage.py createsuperuser
```

## Testing and quality checks

Run the full test suite:

```bash
pytest
```

Run targeted checks:

```bash
pytest apps/accounts/tests.py
pytest --cov=apps --cov-report=html
flake8
black .
```

Generate sample data:

```bash
python manage.py generate_test_payments 100
python manage.py generate_test_reviews 50
```

## Monitoring

The Docker stack includes:

- application: `http://localhost:9999`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Default Grafana credentials in the local stack:

- username: `admin`
- password: `admin`

## Project layout

- `apps/`
  Django applications for accounts, payments, reports, reviews, and site pages.

- `vagvin/`
  Django settings, URLs, and WSGI configuration.

- `grafana/`
  Local Grafana provisioning.

- `prometheus/`
  Prometheus configuration for local monitoring.

- `docker-compose.yml`
  Local multi-service stack.

## Configuration

Important environment groups in `.env.example`:

- Django core settings
- PostgreSQL connection
- payment provider credentials
- external report provider credentials
- cache configuration

For production-style deployment you should, at minimum:

1. replace development secrets and payment credentials;
2. update `ALLOWED_HOSTS`;
3. run behind HTTPS;
4. use a managed or otherwise properly backed-up PostgreSQL instance;
5. keep static/media serving and reverse proxy concerns outside of debug defaults.
