# One Service, Four Ways: Password Strength Checker

CET322 Cloud Computing, Elsewedy University of Technology.

One Flask application, deployed four ways: **VM**, **Docker**, **Kubernetes (Minikube)** and **Hybrid**.
This repository currently contains the **application** (frontend, backend, database schema, tests, docs) and the Docker deployment.
The VM, Kubernetes and Hybrid deployment stages are still being completed by teammates (see [Status](#status-and-known-limitations)).

> **Runbook note.** The project Runbook was not available when this application was written. Everything here follows
> the project brief (endpoints, env var names, table/column names, ports, hostnames). Anything the brief did not
> specify is marked **[decision]**. Please compare against the Runbook and report any mismatch (see [Open points](#open-points-to-confirm-against-the-runbook)).

## Features

- Password analysis with a 0-100 score and a label: **Weak, Medium, Strong, Very Strong**
- Dynamic recommendations and a 7-point checklist produced by the backend for the actual password
- Responsive dark "cybersecurity" UI: animated meter, glassmorphism, show/hide control, loading and error states, reduced-motion support, keyboard accessible, no external fonts/CDNs
- Footer shows the deployment environment (`ENV_NAME`)
- Anonymous statistics saved to PostgreSQL when configured; works without any database for local development
- `/health` and `/ready` endpoints for Kubernetes probes

## Technology stack

Python 3 · Flask · SQLAlchemy 2 · PostgreSQL (psycopg2) · Gunicorn (Linux production) · HTML/CSS/vanilla JavaScript · Pytest

## Architecture

```
Browser ──HTTP──> [Nginx on VM only] ──> Gunicorn/Flask :8000 ──SQLAlchemy──> PostgreSQL :5432
                                              │
                                  scoring.py (pure logic, no I/O)
```

| File | Responsibility |
|---|---|
| `app/app.py` | Flask app factory `create_app()`, routes, error handling, security headers. Entry point `app:app` |
| `app/scoring.py` | Password scoring and recommendations. Pure Python, independently testable |
| `app/models.py` | `Stat` model and a lazy `Database` helper (record, ping, count) |
| `app/config.py` | Reads configuration from environment variables |
| `app/templates/index.html`, `app/static/` | Single-page UI (HTML, CSS, JS, favicon) |
| `app/tests/` | The 18 unit tests |
| `tests/` | PostgreSQL integration tests (skipped unless `DB_HOST` is set) |
| `db/init.sql` | Creates the `stats` table |

The app is **stateless**: nothing is written to local disk, so replicas and replacement pods are interchangeable.

## Folder structure

```
one-service-four-ways/
├── app/                  ← APPLICATION (owned by the application developer)
│   ├── app.py  scoring.py  models.py  config.py
│   ├── requirements.txt  requirements-dev.txt  pytest.ini
│   ├── templates/index.html
│   ├── static/{css,js,assets}/
│   └── tests/            (18 unit tests)
├── db/init.sql           ← DATABASE schema
├── tests/                ← PostgreSQL integration tests
├── vm/                   ← VM deployment files
├── docker/               ← Docker deployment files (completed)
├── k8s/                  ← Kubernetes deployment files
├── hybrid/               ← Hybrid deployment files
├── .env.example  .gitignore
├── README.md  WINDOWS_SETUP_GUIDE.md  TEAMMATE_HANDOFF.md
```

## Quick start (Linux / macOS)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements-dev.txt
cd app
python -m flask --app app run --port 8000      # http://127.0.0.1:8000  (no database needed)
python -m pytest -q                            # 18 unit tests
```

Production (Linux): `cd app && gunicorn -b 0.0.0.0:8000 app:app`
Windows beginners: follow **[WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)**.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ENV_NAME` | recommended | `local` | `vm`, `docker`, `kubernetes` or `hybrid`. Shown in the footer and stored with every statistic |
| `DB_HOST` | for DB use | *(empty)* | PostgreSQL host. **Empty = no database** (local mode). `localhost` (vm), `db` (docker), `vm-db` (hybrid) |
| `DB_PORT` | no | `5432` | PostgreSQL port |
| `DB_NAME` | no | `passcheck` | Database name |
| `DB_USER` | no | `passcheck` | Database user |
| `DB_PASSWORD` | for DB use | *(empty)* | Chosen privately by the team. Never commit it |
| `DATABASE_URL` | no, optional | *(empty)* | **[decision]** Full SQLAlchemy URL override, used by the unit tests (SQLite). Not needed in any stage |
| `FLASK_DEBUG` | no | off | Only honoured by `python app.py`; keep unset in production |

A `.env` file (copy of `.env.example`) is loaded automatically **for local development only**; real environment variables always take precedence. `.env` is git-ignored.

## API

### `POST /api/check`

Request (`Content-Type: application/json`):
```json
{ "password": "Hello#Pass9" }
```
Response `200`:
```json
{
  "score": 73,
  "label": "Strong",
  "length_bucket": "8-11",
  "checks": [{"id": "length", "label": "12+ characters", "passed": false}, "..."],
  "recommendations": ["Make it 12 or more characters long."],
  "recorded": true
}
```
`recorded` is `true` only when a statistics row was written (`false` with no database or on a database error; the check still succeeds).
The password is never echoed back. Errors return `{"error": "<generic message>"}`:
`400` (invalid JSON, missing/empty/non-string password, longer than 128 characters), `413` (body > 4 KB), `405`.

### `GET /health`: liveness
`200` `{"status": "ok", "host": "<hostname>", "env": "<ENV_NAME>"}`. Never touches the database. `host` is the container/pod hostname, used to demonstrate load balancing.

### `GET /ready`: readiness
- No database configured → `200` `{"status": "ready", "database": "not_configured", "host": "..."}`
- Database reachable → `200` `{"status": "ready", "database": "ok", "host": "..."}`
- Database configured but unreachable → `503` `{"status": "not_ready", "database": "unavailable", "host": "..."}`

### `GET /`
The single-page UI.

## Scoring rules **[decision, not an official requirement]**

| Rule | Effect |
|---|---|
| Length | 2 points per character, up to 20 characters (max 40) |
| Character variety | 10 points each: lowercase, uppercase, digit, other/symbol (max 40) |
| Uniqueness | distinct characters, up to 16, scaled to max 20 |
| 3+ identical characters in a row | −15 |
| 3-character sequences (`abc`, `321`, `qwe`) | −10 each, max −20 |
| Common password (small built-in list, also with trailing digits/symbols) | score capped at 10 |
| Shorter than 8 characters | capped at 39 |
| Only one character class | capped at 59 |

Labels: **0-39 Weak · 40-59 Medium · 60-79 Strong · 80-100 Very Strong.**
Required examples: `abc` → Weak (10), `Hello#Pass9` → Strong (73), `Xq7!mPz2#Lw9vTr4` → Very Strong (92).
Length buckets stored in the database **[decision]**: `1-7`, `8-11`, `12-15`, `16+`.

## Database schema

`db/init.sql` creates one table (no password column exists):

| Column | Type | Meaning |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | |
| `env` | VARCHAR(32) | `ENV_NAME` at the time of the check |
| `label` | VARCHAR(16) | Weak / Medium / Strong / Very Strong |
| `length_bucket` | VARCHAR(16) | `1-7`, `8-11`, `12-15`, `16+` |
| `ts` | TIMESTAMPTZ default `now()` | time of the check |

Apply it (database `passcheck` and user `passcheck` must already exist; creating them with the team's private password is a deployment step):
```bash
psql -h <host> -U passcheck -d passcheck -f db/init.sql
```
If run as the `postgres` superuser, the script also grants `SELECT, INSERT` to the `passcheck` role when it exists.

## Privacy and security design

- The password is used only inside `analyze_password()` and is dropped immediately; it is never stored, logged, printed or returned.
- Only `env`, `label`, `length_bucket`, `ts` are persisted. On database errors only the exception **class name** is logged.
- The browser sends the password only in a POST body. The UI is intentionally **not** an HTML `<form>`, so it can never end up in a URL; nothing is put in localStorage, sessionStorage or cookies.
- No credentials in code or the frontend; `.env` is git-ignored; `.env.example` has placeholders only.
- Generic error messages; Flask debug is off by default; `Cache-Control: no-store` on API responses.
- Security headers: strict `Content-Security-Policy` (same-origin only), `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`.
- Request size limit (4 KB) and password length limit (128).
- **Note:** transport encryption (HTTPS) is not provided by the app. The planned stages use plain HTTP; a real deployment should add TLS at the proxy.

Automated evidence: `test_password_is_never_logged_printed_stored_or_leaked` checks logs, stdout/stderr, responses, DB rows and the raw database file (including failure paths). I verified it fails if a log line leaks the password.
Manual verification: after using the app, run `SELECT * FROM stats;` (no password anywhere) and `grep` your server logs for a test password (no matches).

## Testing

**Unit tests (18, no database or network needed):**
```bash
cd app
python -m pytest -q          # expected: 18 passed
```
**PostgreSQL integration tests (2 tests, skipped without `DB_HOST`):** create the DB, apply `db/init.sql`, set `DB_HOST`, `DB_USER`, `DB_NAME`, `DB_PASSWORD`, then from the repo root:
```bash
python -m pytest tests -q -v
```
**Smoke tests for the team's script:** against any running stage (`BASE` = `http://localhost:8080` for the VM, etc.):
```bash
curl -s $BASE/health                          # 200, contains "host"
curl -s $BASE/ready                           # 200 once DB is reachable
for p in abc 'Hello#Pass9' 'Xq7!mPz2#Lw9vTr4'; do
  curl -s -X POST $BASE/api/check -H 'Content-Type: application/json' -d "{\"password\":\"$p\"}"; echo; done
# expected labels: Weak, Strong, Very Strong
```

## Compatibility with the four stages

| Stage | What the app provides | Typical settings |
|---|---|---|
| 1 VM | Gunicorn entry `app:app` on port 8000 behind Nginx (proxy headers honoured); env-based config | `ENV_NAME=vm`, `DB_HOST=localhost` |
| 2 Docker | Stateless app; separate PostgreSQL container with persistent named volume. Image: `passcheck:1.0` (built and verified) | `ENV_NAME=docker`, `DB_HOST=db` |
| 3 Kubernetes | Stateless replicas, `/health` liveness, `/ready` readiness, `host` field for load-balancing demo; NodePort 30080 | `ENV_NAME=kubernetes` |
| 4 Hybrid | Same image in Kubernetes; DB on the VM via env only (IP never in code) | `ENV_NAME=hybrid`, `DB_HOST=vm-db` (→ `192.168.56.10`) |

### For teammates

1. Add your files only inside your folder: `vm/`, `docker/`, `k8s/`, `hybrid/`.
2. **Do not modify `app/`** without telling the application owner. If something in the app blocks you, open an issue/PR.
3. Run the app from the `app/` directory: `gunicorn -b 0.0.0.0:8000 app:app` (Gunicorn is in `requirements.txt` for Linux).
4. Supply configuration as environment variables or Kubernetes Secrets. Never commit real passwords. Exclude `.env` from Docker contexts (`.dockerignore`).
5. Create the database/user, then apply `db/init.sql`.
6. Probes: liveness `GET /health`, readiness `GET /ready` (both port 8000).
7. Under Docker/Kubernetes, `python:3.x-slim` works with `requirements.txt` (psycopg2-binary needs no compiler).
8. Update the status table below when your stage is *actually verified*.

## Status and known limitations

| Item | Status |
|---|---|
| Application, UI, API, scoring | Implemented |
| 18 unit tests | **18 passed on Windows 11 and Kali Linux** |
| PostgreSQL 17 | Manual connection, API and statistics tests passed on Kali Linux |
| PostgreSQL integration test script | Not independently verified yet |
| Gunicorn + PostgreSQL | Not independently verified yet |
| UI testing | Manually tested on Windows 11 |
| Windows 11 setup steps | **Executed successfully (Python 3.13)** |
| API health and readiness | Passed |
| Database privacy and application logs | Manually verified |
| Stage 1 VM (Nginx, host port 8080→80) | Not implemented / not verified |
| Stage 2 Docker (`passcheck:1.0`) | Implemented and verified |
| Stage 3 Kubernetes (replicas, probes, NodePort 30080) | Not implemented / not verified |
| Stage 4 Hybrid (`vm-db` → 192.168.56.10) | Not implemented / not verified |

Known limitations: password rules are heuristic, not a full entropy estimator (no large breach dictionary); each button press records one statistic; no HTTPS in the app itself; no rate limiting (add at Nginx/Ingress if needed); the schema is applied by `init.sql`, not auto-migrated.

### Open points to confirm against the Runbook
1. Exact classification names/thresholds and length buckets (chosen here: see above).
2. Whether the Runbook expects a different app entry point than `app/app.py` (`app:app`) or a fixed Python version.
3. Exact JSON field names expected by the smoke-test script (this app returns `label`, `score`, `recommendations`, `host`).
4. The "18 unit tests" in the Runbook may be specific tests; these 18 are newly written.
5. `ENV_NAME` default `local` when unset.
---

## Docker Deployment – Stage 2 

This stage deploys the Password Strength Checker application using Docker. The application and PostgreSQL database run in two separate containers connected through a custom Docker bridge network.

### Docker Components

- **Dockerfile:** Defines how the Flask application image is built.
- **Docker Image:** `passcheck:1.0`.
- **Application Container:** Runs Flask using Gunicorn on port `8000`.
- **Database Container:** Runs PostgreSQL 16.
- **Docker Network:** `docker_passnet`, allowing the application and database to communicate using the service name `db`.
- **Persistent Volume:** `passcheck_pgdata`, keeping database records when containers are stopped or recreated.
- **Docker Compose:** Manages the application and database services.

### Requirements

Install the following before running this stage:

- Docker Engine
- Docker Compose V2

### How to Run the Docker Deployment

**1. Open the project directory**

```bash
cd one-service-four-ways
```

**2. Create the environment file**

Copy the example configuration:

```bash
cp docker/.env.example docker/.env
```

Open `docker/.env` and replace the `DB_PASSWORD` placeholder with the database password provided privately by the team.

**Important:** The actual `.env` file contains private configuration and must not be shared or uploaded. Only `.env.example` should be included in the project files.

**3. Build and start the containers**

Run from the project root:

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build
```

This command builds the application image and starts both the application and database containers.

**4. Verify the containers**

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
```

The application should be running, and the database should report a healthy status.

**5. Open the application**

Visit the following address in your browser:

```text
http://localhost:8000
```

The application footer should display `Environment: docker`.

### Stopping the Deployment

To stop the containers without removing them:

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml stop
```

To remove the containers and network while keeping database data:

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml down
```

**Important:** Do not use `docker compose down -v` if you want to preserve the database records, because this command removes the associated volume.

### Docker Verification

The following features were successfully tested:

- Application image built successfully.
- Both containers started successfully.
- Database health check passed.
- Application and database communicated through `docker_passnet`.
- Database service-name resolution using `db` worked.
- PostgreSQL `stats` table was created successfully.
- Password analysis API returned valid results.
- Database records remained after container recreation.
- Test passwords did not appear in application logs.
- The database schema contained no password column.

Docker evidence screenshots are available in `evidence/docker/`.

### Docker Configuration Files

| File | Purpose |
|---|---|
| `docker/Dockerfile` | Builds the Flask application image |
| `docker/docker-compose.yml` | Defines and manages both containers |
| `docker/.env.example` | Provides example environment variables |
| `.dockerignore` | Excludes unnecessary and sensitive files from the build context |
| `db/init.sql` | Initializes the PostgreSQL stats table |

