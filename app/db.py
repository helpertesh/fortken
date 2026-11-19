"""SQLite connection, schema and first-run content."""
import re
import secrets
import shutil
import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'staff')),
    session_version INTEGER NOT NULL DEFAULT 1,
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    service TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'contacted', 'quoted', 'won', 'lost')),
    ip TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_enquiries_status ON enquiries (status);
CREATE TABLE IF NOT EXISTS enquiry_notes (
    id INTEGER PRIMARY KEY,
    enquiry_id INTEGER NOT NULL REFERENCES enquiries (id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS slides (
    id INTEGER PRIMARY KEY,
    caption TEXT NOT NULL,
    image TEXT NOT NULL,
    image_small TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT 'cleaning',
    accent TEXT NOT NULL DEFAULT 'gold',
    image TEXT NOT NULL DEFAULT '',
    image_alt TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS service_sections (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL REFERENCES services (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    points_title TEXT NOT NULL DEFAULT '',
    points TEXT NOT NULL DEFAULT '',
    image TEXT NOT NULL DEFAULT '',
    image_alt TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS testimonials (
    id INTEGER PRIMARY KEY,
    quote TEXT NOT NULL,
    author TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# The content the site launched with, so a fresh database shows the same page.
SEED_SETTINGS = {
    "phone1": "+254 703 178 323",
    "phone2": "+254 783 474 570",
    "email": "4fortken@gmail.com",
    "address": "Moli Center, Links Road, Mombasa",
    "notify_email": "4fortken@gmail.com",
    "whatsapp": "010 0106340",
    "instagram_url": "",
    "tiktok_url": "",
    "x_url": "",
}
SEED_SLIDES = [
    ("Professional Cleaning", "/assets/img/hero-cleaning.jpg", "/assets/img/hero-cleaning-960.jpg"),
    ("Fumigation & Pest Control", "/assets/img/service-fumigation.jpg", ""),
    ("Garbage Collection", "/assets/img/hero-waste.jpg", "/assets/img/hero-waste-960.jpg"),
    ("General Supplies", "/assets/img/hero-supplies.jpg", "/assets/img/hero-supplies-960.jpg"),
    ("Facility Support", "/assets/img/hero-facility.jpg", "/assets/img/hero-facility-960.jpg"),
]
SEED_SERVICES = [
    ("Cleaning Services", "Comprehensive cleaning for every kind of space.",
     "Office, Institutional, Industrial, Residential", "cleaning", "purple",
     "/assets/img/service-cleaning.jpg", "A gloved hand wiping down a surface with spray cleaner"),
    ("Fumigation & Pest Control", "Safe and effective pest management solutions.",
     "Safe, Effective", "fumigation", "blue",
     "/assets/img/service-fumigation.jpg", "A technician in protective gear spraying treatment"),
    ("Garbage Collection & Waste Disposal", "Structured and sustainable waste management systems.",
     "Structured, Sustainable", "waste", "green",
     "/assets/img/service-waste.jpg", "A row of colour-coded waste bins"),
    ("General Supplies", "Provision of essential goods and consumables for corporate and institutional clients.",
     "Corporate, Institutional", "supplies", "gold",
     "/assets/img/service-supplies.jpg", "Warehouse shelves stocked with supplies"),
    ("Facility Support Services", "Customized solutions to improve operational efficiency and workplace hygiene.",
     "Operational efficiency, Workplace hygiene", "facility", "purple",
     "/assets/img/service-facility.jpg", "A cleaner mopping the floor of an office lobby"),
]
SEED_TESTIMONIALS = [
    ("KF 4Fortken Holdings Ltd has consistently provided reliable cleaning and garbage collection services. "
     "Their team is professional, punctual, and thorough, ensuring our commercial cum residential environment "
     "remains clean and well-maintained.", "Valletta Homes, Shanzu"),
    ("We are impressed by the efficiency and dedication of KF 4Fortken Holdings Ltd. Their waste management "
     "services have greatly improved the hygiene standards of our estate, making it a healthier and more "
     "pleasant place to live.", "Links Garden, Nyali"),
    ("KF 4Fortken Holdings Ltd has proven to be a dependable partner in maintaining cleanliness and waste "
     "disposal for our commercial premises. Their structured approach and commitment to service excellence "
     "have enhanced the overall appeal of our property.", "Links Arcade Plaza"),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _seed(db):
    # Runs every start so settings added in later versions appear; existing values are kept.
    db.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", SEED_SETTINGS.items())
    if db.execute("SELECT 1 FROM settings WHERE key = 'seeded'").fetchone():
        return
    db.executemany(
        "INSERT INTO slides (caption, image, image_small, position) VALUES (?, ?, ?, ?)",
        [(*row, i) for i, row in enumerate(SEED_SLIDES, 1)],
    )
    db.executemany(
        "INSERT INTO services (title, description, tags, icon, accent, image, image_alt, position)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(*row, i) for i, row in enumerate(SEED_SERVICES, 1)],
    )
    db.executemany(
        "INSERT INTO testimonials (quote, author, position) VALUES (?, ?, ?)",
        [(*row, i) for i, row in enumerate(SEED_TESTIMONIALS, 1)],
    )
    db.execute("INSERT INTO settings (key, value) VALUES ('seeded', '1')")


# Columns added after the first release. Added to existing databases on start-up.
SERVICE_COLUMNS = {
    "slug": "TEXT NOT NULL DEFAULT ''",
    "category": "TEXT NOT NULL DEFAULT 'environmental'",
    "details": "TEXT NOT NULL DEFAULT ''",
    "includes": "TEXT NOT NULL DEFAULT ''",
}


def slugify(title, taken=()):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower().replace("&", "and")).strip("-") or "service"
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug


def _add_columns(db):
    existing = {row["name"] for row in db.execute("PRAGMA table_info(services)")}
    for name, spec in SERVICE_COLUMNS.items():
        if name not in existing:
            db.execute(f"ALTER TABLE services ADD COLUMN {name} {spec}")


def _service_pages_update(db):
    """One-time move to service pages and the real estate division (client brief, Nov 2026).
    Only services still carrying their original titles are changed, so owner edits are kept."""
    if db.execute("SELECT 1 FROM settings WHERE key = 'content_v2'").fetchone():
        return
    from . import seed_content

    rows = {row["title"]: row for row in db.execute("SELECT * FROM services")}
    fields = ("category", "description", "tags", "icon", "accent", "image", "image_alt", "details", "includes")
    for spec in seed_content.SERVICES:
        values = {k: spec[k] for k in fields if k in spec}
        title = spec.get("rename", spec["match"])
        row = rows.get(spec["match"])
        if row is None and not spec.get("new"):
            continue
        if row is None:
            if title in rows:
                continue
            cur = db.execute("INSERT INTO services (title, description) VALUES (?, ?)", (title, values.pop("description")))
            service_id = cur.lastrowid
        else:
            service_id = row["id"]
            values["title"] = title
        if values:
            db.execute(f"UPDATE services SET {', '.join(f'{k} = ?' for k in values)} WHERE id = ?",
                       [*values.values(), service_id])
        for pos, section in enumerate(spec.get("sections", []), 1):
            db.execute("INSERT INTO service_sections (service_id, title, body, points_title, points, image, image_alt, position)"
                       " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (service_id, section["title"], section["body"], section["points_title"], section["points"],
                        section["image"], section["image_alt"], pos))

    # If the owner already uploaded a post-construction photo for a service of their own,
    # use a copy of it on the new Post-Construction Cleaning section instead of the stock photo.
    own = db.execute("SELECT image FROM services WHERE title LIKE '%post%construction%' AND image LIKE '/uploads/%'"
                     " ORDER BY id LIMIT 1").fetchone()
    section = db.execute("SELECT id FROM service_sections WHERE title = 'Post-Construction Cleaning'").fetchone()
    if own and section:
        folder = Path(current_app.config["UPLOAD_FOLDER"])
        source = folder / own["image"].removeprefix("/uploads/")
        if source.is_file():
            copy_name = f"{secrets.token_hex(8)}-section.jpg"
            shutil.copyfile(source, folder / copy_name)
            db.execute("UPDATE service_sections SET image = ?, image_alt = ? WHERE id = ?",
                       (f"/uploads/{copy_name}", "Before and after post-construction cleaning of a kitchen", section["id"]))

    # Put the known services in order; anything the owner added stays after them.
    order = {title: i for i, title in enumerate(seed_content.ORDER, 1)}
    for row in db.execute("SELECT id, title, position FROM services").fetchall():
        db.execute("UPDATE services SET position = ? WHERE id = ?", (order.get(row["title"], 100 + row["position"]), row["id"]))

    caption, image, small = seed_content.NEW_SLIDE
    if not db.execute("SELECT 1 FROM slides WHERE image = ?", (image,)).fetchone():
        position = db.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM slides").fetchone()[0]
        db.execute("INSERT INTO slides (caption, image, image_small, position) VALUES (?, ?, ?, ?)",
                   (caption, image, small, position))
    db.execute("INSERT INTO settings (key, value) VALUES ('content_v2', '1')")


def _fill_slugs(db):
    rows = db.execute("SELECT id, title, slug FROM services ORDER BY position, id").fetchall()
    taken = {row["slug"] for row in rows if row["slug"]}
    for row in rows:
        if not row["slug"]:
            slug = slugify(row["title"], taken)
            taken.add(slug)
            db.execute("UPDATE services SET slug = ? WHERE id = ?", (slug, row["id"]))


def _hibiscus_project(db):
    """One-time: add the Hibiscus Homes project to the top of the Property Management page."""
    if db.execute("SELECT 1 FROM settings WHERE key = 'content_v3'").fetchone():
        return
    from .seed_content import HIBISCUS_SECTION as sec

    service = db.execute("SELECT id FROM services WHERE slug = ?", (sec["service_slug"],)).fetchone()
    if service:
        top = db.execute("SELECT COALESCE(MIN(position), 1) - 1 FROM service_sections WHERE service_id = ?",
                         (service["id"],)).fetchone()[0]
        db.execute("INSERT INTO service_sections (service_id, title, body, points_title, points, image, image_alt, position)"
                   " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (service["id"], sec["title"], sec["body"], sec["points_title"], sec["points"], sec["image"],
                    sec["image_alt"], top))
    db.execute("INSERT INTO settings (key, value) VALUES ('content_v3', '1')")


def _hide_general_supplies(db):
    """One-time (client request, Nov 2026): take General Supplies off the website.
    Hidden rather than deleted, so an owner can show it again from the admin."""
    if db.execute("SELECT 1 FROM settings WHERE key = 'content_v4'").fetchone():
        return
    db.execute("UPDATE services SET active = 0 WHERE title = 'General Supplies'")
    db.execute("UPDATE slides SET active = 0 WHERE caption = 'General Supplies'")
    db.execute("INSERT INTO settings (key, value) VALUES ('content_v4', '1')")


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(SCHEMA)
        _add_columns(db)
        _seed(db)
        _service_pages_update(db)
        _fill_slugs(db)
        _hibiscus_project(db)
        _hide_general_supplies(db)
        db.commit()
