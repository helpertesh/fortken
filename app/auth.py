"""Admin accounts, sign-in and role checks."""
import functools
import time

from flask import flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

ROLES = {"owner": "Owner (full access)", "staff": "Staff (enquiries only)"}
MIN_PASSWORD = 10
MAX_FAILED = 5
LOCK_SECONDS = 15 * 60
# Compared against when the email is unknown, so both cases take the same time.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def password_problem(password):
    if len(password) < MIN_PASSWORD:
        return f"Passwords must be at least {MIN_PASSWORD} characters."
    return None


def get_user(user_id):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def all_users():
    return get_db().execute("SELECT * FROM users ORDER BY role, name").fetchall()


def owner_count():
    return get_db().execute("SELECT COUNT(*) FROM users WHERE role = 'owner'").fetchone()[0]


def create_user(name, email, password, role):
    db = get_db()
    db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
               (name, email.strip().lower(), generate_password_hash(password), role))
    db.commit()


def set_password(user_id, password):
    """Changing a password also signs that user out everywhere else."""
    db = get_db()
    db.execute("UPDATE users SET password_hash = ?, session_version = session_version + 1, "
               "failed_logins = 0, locked_until = 0 WHERE id = ?", (generate_password_hash(password), user_id))
    db.commit()


def set_role(user_id, role):
    db = get_db()
    db.execute("UPDATE users SET role = ?, session_version = session_version + 1 WHERE id = ?", (role, user_id))
    db.commit()


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()


def authenticate(email, password):
    """Return (user, error). Locks the account for 15 minutes after 5 wrong passwords."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
    now = int(time.time())
    if user is None:
        check_password_hash(_DUMMY_HASH, password or "")
        return None, "Wrong email or password."
    if user["locked_until"] > now:
        minutes = (user["locked_until"] - now) // 60 + 1
        return None, f"Too many failed attempts. Try again in {minutes} minutes."
    if not check_password_hash(user["password_hash"], password or ""):
        failed = user["failed_logins"] + 1
        locked = now + LOCK_SECONDS if failed >= MAX_FAILED else 0
        db.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
                   (0 if locked else failed, locked, user["id"]))
        db.commit()
        if locked:
            return None, "Too many failed attempts. This account is locked for 15 minutes."
        return None, "Wrong email or password."
    db.execute("UPDATE users SET failed_logins = 0, locked_until = 0 WHERE id = ?", (user["id"],))
    db.commit()
    return user, None


def log_in(user):
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    session["session_version"] = user["session_version"]


def load_user():
    """Run before every admin request. Signs out removed users and changed passwords."""
    g.user = None
    user_id = session.get("user_id")
    if user_id is None:
        return
    user = get_user(user_id)
    if user is None or user["session_version"] != session.get("session_version"):
        session.clear()
        return
    g.user = user


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def owner_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "owner":
            flash("Only an owner can do that.", "error")
            return redirect(url_for("admin.dashboard"))
        return view(*args, **kwargs)
    return wrapped
