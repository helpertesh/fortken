"""Editable site content: slides, services, testimonials and contact settings."""
from .db import get_db, slugify

# Service icons offered in the admin. Each value is the inner SVG (24x24 stroke icon).
ICONS = {
    "cleaning": ("Sparkle (cleaning)",
                 '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/>'
                 '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>'),
    "fumigation": ("Shield (fumigation)",
                   '<path d="M12 3l8 3v6c0 4.5-3.2 7.7-8 9-4.8-1.3-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>'),
    "waste": ("Bin (waste)", '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>'),
    "supplies": ("Box (supplies)",
                 '<path d="M12 3l8.5 4.5v9L12 21l-8.5-4.5v-9z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>'),
    "facility": ("Building (facility)",
                 '<path d="M4 21V5l8-2v18M12 9l8 2v10M2 21h20M7.5 8.5h1.5M7.5 12.5h1.5M7.5 16.5h1.5'
                 'M15.5 13.5H17M15.5 17H17"/>'),
    "leaf": ("Leaf (eco)", '<path d="M5 19c0-8 5-14 15-14 0 10-6 15-14 15"/><path d="M5 19l8-8"/>'),
    "drop": ("Drop (water)", '<path d="M12 3s-6 7-6 11a6 6 0 0 0 12 0c0-4-6-11-6-11z"/>'),
    "truck": ("Truck (transport)",
              '<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>'),
    "home": ("House (property)", '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>'),
    "tools": ("Spanner (maintenance)",
              '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>'),
    "receipt": ("Receipt (rent)", '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>'),
    "store": ("Shopfront (leasing)",
              '<path d="M3 9l1.5-5h15L21 9"/><path d="M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/>'
              '<path d="M5 12v9h14v-9"/><path d="M10 21v-5h4v5"/>'),
    "map": ("Map (land)", '<path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>'),
    "scale": ("Scales (valuation)",
              '<path d="M12 3v18M7 21h10M5 7h14"/><path d="M5 7l-3 6a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0z"/>'),
    "key": ("Key", '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M14 9l2 2"/>'),
}

# The two divisions services are grouped into on the website.
CATEGORIES = {
    "environmental": {
        "label": "Cleaning & Environmental",
        "title": "Cleaning & Environmental Services",
        "intro": "Professional cleaning, pest control, waste management and landscaping for homes, businesses and institutions.",
    },
    "real_estate": {
        "label": "Real Estate",
        "title": "Real Estate Services",
        "intro": "Property management, leasing, land and valuation services that protect and grow the value of your property.",
    },
}
ACCENTS = {"gold": "Gold", "purple": "Purple", "green": "Green", "blue": "Blue"}

SETTING_FIELDS = [
    ("phone1", "Main phone", "tel"),
    ("phone2", "Second phone (optional)", "tel"),
    ("whatsapp", "WhatsApp number", "tel"),
    ("email", "Public email", "email"),
    ("address", "Office address", "text"),
    ("notify_email", "Send new enquiry alerts to", "email"),
    ("instagram_url", "Instagram link (optional)", "url"),
    ("tiktok_url", "TikTok link (optional)", "url"),
    ("x_url", "X (Twitter) link (optional)", "url"),
]
SOCIAL_FIELDS = ("instagram_url", "tiktok_url", "x_url")


class Collection:
    """An ordered list of rows the admin can add to, edit, reorder, hide and delete."""

    def __init__(self, table, fields, scope=None):
        self.table = table
        self.fields = fields
        self.scope = scope  # rows are reordered only among rows with the same value in this column

    def all(self, active_only=False, **where):
        clauses = ["active = 1"] if active_only else []
        clauses += [f"{col} = ?" for col in where]
        sql = f"SELECT * FROM {self.table} {'WHERE ' + ' AND '.join(clauses) if clauses else ''} ORDER BY position, id"
        return get_db().execute(sql, list(where.values())).fetchall()

    def get(self, item_id):
        return get_db().execute(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,)).fetchone()

    def create(self, **data):
        db = get_db()
        cols = [f for f in self.fields if f in data]
        position = db.execute(f"SELECT COALESCE(MAX(position), 0) + 1 FROM {self.table}").fetchone()[0]
        cur = db.execute(
            f"INSERT INTO {self.table} ({', '.join(cols)}, position) VALUES ({', '.join('?' * len(cols))}, ?)",
            [data[c] for c in cols] + [position],
        )
        db.commit()
        return cur.lastrowid

    def update(self, item_id, **data):
        cols = [f for f in self.fields if f in data]
        if not cols:
            return
        db = get_db()
        db.execute(
            f"UPDATE {self.table} SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?",
            [data[c] for c in cols] + [item_id],
        )
        db.commit()

    def move(self, item_id, direction):
        item = self.get(item_id)
        if item is None:
            return
        rows = self.all(**({self.scope: item[self.scope]} if self.scope else {}))
        items = [row["id"] for row in rows]
        positions = sorted(row["position"] for row in rows)
        i = items.index(item_id)
        j = i - 1 if direction == "up" else i + 1
        if 0 <= j < len(items):
            items[i], items[j] = items[j], items[i]
        # Reuse this group's own position numbers so other groups keep their order.
        if len(set(positions)) < len(positions):
            positions = list(range(positions[0], positions[0] + len(positions)))
        db = get_db()
        db.executemany(f"UPDATE {self.table} SET position = ? WHERE id = ?", list(zip(positions, items)))
        db.commit()

    def toggle(self, item_id):
        db = get_db()
        db.execute(f"UPDATE {self.table} SET active = 1 - active WHERE id = ?", (item_id,))
        db.commit()

    def delete(self, item_id):
        db = get_db()
        db.execute(f"DELETE FROM {self.table} WHERE id = ?", (item_id,))
        db.commit()


slides = Collection("slides", ["caption", "image", "image_small", "active"])
services = Collection("services", ["title", "slug", "category", "description", "tags", "icon", "accent", "image",
                                   "image_alt", "details", "includes", "active"], scope="category")
sections = Collection("service_sections", ["service_id", "title", "body", "points_title", "points", "image", "image_alt"],
                      scope="service_id")
testimonials = Collection("testimonials", ["quote", "author", "active"])


def services_by_category(active_only=True):
    """[(key, info, [services])] in division order, skipping empty divisions."""
    rows = services.all(active_only=active_only)
    groups = []
    for key, info in CATEGORIES.items():
        items = [row for row in rows if row["category"] == key]
        if items:
            groups.append((key, info, items))
    return groups


def service_by_slug(slug):
    return get_db().execute("SELECT * FROM services WHERE slug = ?", (slug,)).fetchone()


def new_slug(title):
    taken = {row["slug"] for row in get_db().execute("SELECT slug FROM services")}
    return slugify(title, taken)


def get_settings():
    rows = get_db().execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def save_settings(values):
    db = get_db()
    db.executemany("INSERT INTO settings (key, value) VALUES (?, ?) "
                   "ON CONFLICT (key) DO UPDATE SET value = excluded.value", values.items())
    db.commit()
