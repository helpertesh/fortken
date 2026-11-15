"""Service requests sent from the website's contact form."""
from .db import get_db

STATUSES = {
    "new": "New",
    "contacted": "Contacted",
    "quoted": "Quoted",
    "won": "Won",
    "lost": "Lost",
}
PAGE_SIZE = 25


def create(name, phone, email, service, message, ip):
    db = get_db()
    cur = db.execute(
        "INSERT INTO enquiries (name, phone, email, service, message, ip) VALUES (?, ?, ?, ?, ?, ?)",
        (name, phone, email, service, message, ip),
    )
    db.commit()
    return get(cur.lastrowid)


def _filters(status="", service="", q=""):
    where, args = [], []
    if status in STATUSES:
        where.append("status = ?")
        args.append(status)
    if service:
        where.append("service = ?")
        args.append(service)
    if q:
        where.append("(name LIKE ? OR phone LIKE ? OR email LIKE ? OR message LIKE ?)")
        args.extend([f"%{q}%"] * 4)
    return ("WHERE " + " AND ".join(where)) if where else "", args


def search(status="", service="", q="", page=1, limit=PAGE_SIZE):
    """Return (rows, total) for one page, newest first. limit=None returns everything."""
    where, args = _filters(status, service, q)
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM enquiries {where}", args).fetchone()[0]
    sql = f"SELECT * FROM enquiries {where} ORDER BY created_at DESC, id DESC"
    if limit:
        sql += " LIMIT ? OFFSET ?"
        args = args + [limit, (page - 1) * limit]
    return db.execute(sql, args).fetchall(), total


def get(enquiry_id):
    return get_db().execute("SELECT * FROM enquiries WHERE id = ?", (enquiry_id,)).fetchone()


def set_status(enquiry_id, status):
    if status not in STATUSES:
        return
    db = get_db()
    db.execute("UPDATE enquiries SET status = ?, updated_at = datetime('now') WHERE id = ?", (status, enquiry_id))
    db.commit()


def notes(enquiry_id):
    return get_db().execute(
        "SELECT * FROM enquiry_notes WHERE enquiry_id = ? ORDER BY created_at, id", (enquiry_id,)
    ).fetchall()


def add_note(enquiry_id, author, body):
    db = get_db()
    db.execute("INSERT INTO enquiry_notes (enquiry_id, author, body) VALUES (?, ?, ?)", (enquiry_id, author, body))
    db.execute("UPDATE enquiries SET updated_at = datetime('now') WHERE id = ?", (enquiry_id,))
    db.commit()


def delete(enquiry_id):
    db = get_db()
    db.execute("DELETE FROM enquiries WHERE id = ?", (enquiry_id,))
    db.commit()


def count_new():
    return get_db().execute("SELECT COUNT(*) FROM enquiries WHERE status = 'new'").fetchone()[0]


def stats():
    db = get_db()
    one = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    return {
        "total": one("SELECT COUNT(*) FROM enquiries"),
        "new": one("SELECT COUNT(*) FROM enquiries WHERE status = 'new'"),
        "this_month": one("SELECT COUNT(*) FROM enquiries WHERE created_at >= date('now', 'start of month')"),
        "won": one("SELECT COUNT(*) FROM enquiries WHERE status = 'won'"),
        "by_service": db.execute(
            "SELECT COALESCE(NULLIF(service, ''), 'Not specified') AS service, COUNT(*) AS n "
            "FROM enquiries GROUP BY 1 ORDER BY n DESC"
        ).fetchall(),
        "by_status": {row["status"]: row["n"] for row in db.execute(
            "SELECT status, COUNT(*) AS n FROM enquiries GROUP BY status")},
        "recent": db.execute("SELECT * FROM enquiries ORDER BY created_at DESC, id DESC LIMIT 5").fetchall(),
    }
