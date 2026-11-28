"""Password Strength Checker: Flask application (entry point: app:app).

Production (Linux):  gunicorn -b 0.0.0.0:8000 app:app
Local development:   python -m flask --app app run --port 8000
"""
from __future__ import annotations

import logging
import os
import socket
from typing import Mapping, Optional

from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from models import Database
from scoring import MAX_PASSWORD_LENGTH, analyze_password

log = logging.getLogger("passcheck")


def create_app(env: Optional[Mapping[str, str]] = None) -> Flask:
    config = Config.from_env(os.environ if env is None else env)
    db = Database(config.database_url)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024  # a password request is tiny
    app.json.sort_keys = False
    app.extensions["passcheck_config"] = config
    app.extensions["passcheck_db"] = db
    # Trust X-Forwarded-* headers from the Nginx reverse proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    @app.get("/")
    def index():
        return render_template("index.html", env_name=config.env_name)

    @app.post("/api/check")
    def check():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "password" not in data:
            return error("Request body must be JSON with a 'password' field.", 400)
        password = data["password"]
        if not isinstance(password, str):
            return error("'password' must be a string.", 400)
        if password == "":
            return error("Password must not be empty.", 400)
        if len(password) > MAX_PASSWORD_LENGTH:
            return error(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.", 400)

        result = analyze_password(password)
        del password, data  # only the derived result is used from here on

        recorded = False
        if db.configured:
            try:
                db.record(config.env_name, result.label, result.length_bucket)
                recorded = True
            except Exception as exc:  # never include exception text or request data
                log.warning("Statistics could not be recorded (%s).", type(exc).__name__)

        body = result.to_dict()
        body["recorded"] = recorded
        return jsonify(body)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "host": socket.gethostname(), "env": config.env_name})

    @app.get("/ready")
    def ready():
        host = socket.gethostname()
        if not db.configured:
            return jsonify({"status": "ready", "database": "not_configured", "host": host})
        if db.ping():
            return jsonify({"status": "ready", "database": "ok", "host": host})
        return jsonify({"status": "not_ready", "database": "unavailable", "host": host}), 503

    @app.errorhandler(404)
    def not_found(_):
        return error("Not found.", 404)

    @app.errorhandler(405)
    def bad_method(_):
        return error("Method not allowed.", 405)

    @app.errorhandler(413)
    def too_large(_):
        return error("Request too large.", 413)

    @app.errorhandler(Exception)
    def unexpected(exc):
        # Generic message only; details could contain sensitive data.
        if hasattr(exc, "code") and isinstance(exc.code, int):
            return error(getattr(exc, "name", "Error"), exc.code)
        log.error("Unhandled error (%s).", type(exc).__name__)
        return error("Internal server error.", 500)

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    return app


# Load an optional local .env for development. Real environment variables
# (VM / Docker / Kubernetes) always win because override=False.
load_dotenv(find_dotenv(usecwd=True), override=False)
app = create_app()

if __name__ == "__main__":
    # Local development only. Debug stays OFF unless FLASK_DEBUG=1 is set.
    app.run(host="127.0.0.1", port=8000, debug=os.environ.get("FLASK_DEBUG") == "1")
