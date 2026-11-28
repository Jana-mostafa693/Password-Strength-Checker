# Handoff note for deployment teammates

Application is ready in `app/`. Please read the README sections *API*, *Environment variables* and *For teammates*.

**Run it:** `cd app && gunicorn -b 0.0.0.0:8000 app:app` (Python 3, `pip install -r requirements.txt`).

**Config (environment variables only):** `ENV_NAME` (`vm|docker|kubernetes|hybrid`), `DB_HOST`, `DB_PORT` (5432), `DB_NAME` (passcheck), `DB_USER` (passcheck), `DB_PASSWORD` (team secret). Empty `DB_HOST` = runs without database.

**Database:** create DB `passcheck` + user `passcheck`, then `psql -h <host> -U passcheck -d passcheck -f db/init.sql` (table `stats`).

**Endpoints:** `GET /` · `POST /api/check` (`{"password": "..."}`) · `GET /health` (liveness, includes `host`) · `GET /ready` (200 ready / 503 DB down).

**Expected smoke results:** `abc` → Weak · `Hello#Pass9` → Strong · `Xq7!mPz2#Lw9vTr4` → Very Strong. Footer shows `Environment: <ENV_NAME>`.

**Stage values:** VM `DB_HOST=localhost`; Docker `DB_HOST=db`, image `passcheck:1.0`; K8s NodePort 30080, probes `/health` + `/ready`; Hybrid `ENV_NAME=hybrid`, `DB_HOST=vm-db` (→ 192.168.56.10 via your hosts/Service config, never in code).

**Rules:** put files only in your own folder (`vm/ docker/ k8s/ hybrid/`); never commit real passwords or `.env`; don't change `app/` without asking; tell the app owner if the app blocks you.
