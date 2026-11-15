"""KF 4Fortken Holdings Ltd: public website and admin panel."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent.parent


def _secret_key(instance_dir: Path) -> str:
    """Use SECRET_KEY from the environment, or create one and keep it in instance/."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    key_file = instance_dir / "secret_key"
    if not key_file.exists():
        key_file.write_text(secrets.token_hex(32))
    return key_file.read_text().strip()


def create_app(test_config=None):
    load_dotenv(BASE_DIR / ".env")
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    production = os.environ.get("APP_ENV") == "production"

    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        static_url_path="",
        template_folder=str(BASE_DIR / "templates"),
        instance_path=str(instance_dir),
    )
    app.config.update(
        SECRET_KEY=_secret_key(instance_dir),
        DATABASE=os.environ.get("DATABASE_PATH", str(instance_dir / "fortken.db")),
        UPLOAD_FOLDER=str(BASE_DIR / "static" / "uploads"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        PRODUCTION=production,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SMTP_HOST=os.environ.get("SMTP_HOST", ""),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USER=os.environ.get("SMTP_USER", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        MAIL_FROM=os.environ.get("MAIL_FROM", ""),
    )
    if test_config:
        app.config.update(test_config)

    if os.environ.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from . import admin, cli, db, security, site, templating

    db.init_app(app)
    security.init_app(app)
    templating.init_app(app)
    cli.init_app(app)
    app.register_blueprint(site.bp)
    app.register_blueprint(admin.bp)
    return app
