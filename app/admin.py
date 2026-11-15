"""Admin panel. Owners can edit everything; staff can only work on enquiries."""
import csv
import io
import sqlite3
from datetime import datetime

from flask import (Blueprint, Response, abort, flash, g, redirect, render_template, request, session,
                   url_for)
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash

from . import auth, content, enquiries, images
from .auth import login_required, owner_required
from .security import RateLimiter, check_csrf
from .templating import local_time

bp = Blueprint("admin", __name__, url_prefix="/admin")
# Failed sign-ins per IP address. Only failures count, so staff sharing an
# office connection aren't locked out by each other's normal logins.
failed_login_limiter = RateLimiter(limit=20, window=15 * 60)

COLLECTIONS = {
    "slides": content.slides,
    "services": content.services,
    "testimonials": content.testimonials,
}


@bp.before_request
def before():
    auth.load_user()
    if request.method == "POST":
        check_csrf()


@bp.context_processor
def admin_globals():
    return {"new_count": enquiries.count_new() if g.get("user") else 0, "ROLES": auth.ROLES}


@bp.app_errorhandler(RequestEntityTooLarge)
def too_large(_err):
    flash("That file is too big. Upload a photo under 10 MB.", "error")
    return redirect(request.referrer or url_for("admin.dashboard"))


def _text(name, max_len, required=True):
    value = (request.form.get(name) or "").strip()
    if required and not value:
        raise ValueError(f"Fill in {name.replace('_', ' ')}.")
    if len(value) > max_len:
        raise ValueError(f"{name.replace('_', ' ').capitalize()} must be {max_len} characters or fewer.")
    return value


def _back(endpoint, **kwargs):
    return redirect(url_for(endpoint, **kwargs))


# Sign in / out -------------------------------------------------------------

@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return _back("admin.dashboard")
    error = None
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if failed_login_limiter.blocked(ip):
            error = "Too many failed sign-in attempts from this connection. Wait 15 minutes and try again."
        else:
            user, error = auth.authenticate(request.form.get("email"), request.form.get("password"))
            if not user:
                failed_login_limiter.record(ip)
            else:
                auth.log_in(user)
                target = request.args.get("next", "")
                if not target.startswith("/admin") or target.startswith("//"):
                    target = url_for("admin.dashboard")
                return redirect(target)
    return render_template("admin/login.html", error=error, email=request.form.get("email", ""))


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return _back("admin.login")


# Dashboard -------------------------------------------------------------------

@bp.get("/")
@login_required
def dashboard():
    settings = content.get_settings()
    missing_social = [k for k in content.SOCIAL_FIELDS if not settings.get(k)]
    return render_template("admin/dashboard.html", stats=enquiries.stats(), missing_social=missing_social)


# Enquiries -------------------------------------------------------------------

def _enquiry_filters():
    return {
        "status": request.args.get("status", ""),
        "service": request.args.get("service", ""),
        "q": request.args.get("q", "").strip()[:100],
    }


@bp.get("/enquiries")
@login_required
def enquiry_list():
    filters = _enquiry_filters()
    page = max(request.args.get("page", 1, type=int), 1)
    rows, total = enquiries.search(page=page, **filters)
    pages = max((total + enquiries.PAGE_SIZE - 1) // enquiries.PAGE_SIZE, 1)
    services = sorted({s["title"] for s in content.services.all()})
    return render_template("admin/enquiries.html", rows=rows, total=total, page=page, pages=pages,
                           filters=filters, services=services)


@bp.get("/enquiries/export.csv")
@login_required
def enquiry_export():
    rows, _total = enquiries.search(limit=None, **_enquiry_filters())

    def cell(value):
        # Stop spreadsheet apps treating text such as "=cmd" as a formula.
        value = str(value or "")
        return "'" + value if value[:1] in ("=", "+", "-", "@") else value

    out = io.StringIO()
    out.write("﻿")  # lets Excel detect UTF-8
    writer = csv.writer(out)
    writer.writerow(["Date", "Name", "Phone", "Email", "Service", "Status", "Message"])
    for r in rows:
        writer.writerow([local_time(r["created_at"]), cell(r["name"]), cell(r["phone"]), cell(r["email"]),
                         cell(r["service"]), enquiries.STATUSES[r["status"]], cell(r["message"])])
    filename = f"enquiries-{datetime.now():%Y-%m-%d}.csv"
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _enquiry_or_404(enquiry_id):
    enquiry = enquiries.get(enquiry_id)
    if enquiry is None:
        abort(404)
    return enquiry


@bp.get("/enquiries/<int:enquiry_id>")
@login_required
def enquiry_detail(enquiry_id):
    enquiry = _enquiry_or_404(enquiry_id)
    return render_template("admin/enquiry.html", e=enquiry, notes=enquiries.notes(enquiry_id))


@bp.post("/enquiries/<int:enquiry_id>/status")
@login_required
def enquiry_status(enquiry_id):
    _enquiry_or_404(enquiry_id)
    enquiries.set_status(enquiry_id, request.form.get("status", ""))
    flash("Status updated.", "success")
    return _back("admin.enquiry_detail", enquiry_id=enquiry_id)


@bp.post("/enquiries/<int:enquiry_id>/notes")
@login_required
def enquiry_note(enquiry_id):
    _enquiry_or_404(enquiry_id)
    body = (request.form.get("body") or "").strip()
    if body:
        enquiries.add_note(enquiry_id, g.user["name"], body[:2000])
        flash("Note added.", "success")
    return _back("admin.enquiry_detail", enquiry_id=enquiry_id)


@bp.post("/enquiries/<int:enquiry_id>/delete")
@owner_required
def enquiry_delete(enquiry_id):
    _enquiry_or_404(enquiry_id)
    enquiries.delete(enquiry_id)
    flash("Enquiry deleted.", "success")
    return _back("admin.enquiry_list")


# Shared actions for slides, services and testimonials ------------------------

def _collection(kind):
    if kind not in COLLECTIONS:
        abort(404)
    return COLLECTIONS[kind]


@bp.post("/<kind>/<int:item_id>/move/<direction>")
@owner_required
def item_move(kind, item_id, direction):
    _collection(kind).move(item_id, "up" if direction == "up" else "down")
    return redirect(url_for(f"admin.{kind}") + f"#item-{item_id}")


@bp.post("/<kind>/<int:item_id>/toggle")
@owner_required
def item_toggle(kind, item_id):
    _collection(kind).toggle(item_id)
    flash("Visibility updated.", "success")
    return redirect(url_for(f"admin.{kind}") + f"#item-{item_id}")


@bp.post("/<kind>/<int:item_id>/delete")
@owner_required
def item_delete(kind, item_id):
    coll = _collection(kind)
    item = coll.get(item_id)
    if item is None:
        abort(404)
    if kind == "services":
        for section in content.sections.all(service_id=item_id):
            images.delete_upload(section["image"])
    coll.delete(item_id)
    for key in ("image", "image_small"):
        if key in item.keys():
            images.delete_upload(item[key])
    flash("Deleted.", "success")
    return _back(f"admin.{kind}")


# Hero slides -------------------------------------------------------------------

@bp.get("/slides")
@owner_required
def slides():
    return render_template("admin/slides.html", items=content.slides.all())


@bp.post("/slides/new")
@owner_required
def slide_create():
    try:
        caption = _text("caption", 60)
        large, small = images.save_slide(request.files.get("image"))
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.slides")
    content.slides.create(caption=caption, image=large, image_small=small)
    flash("Slide added. It now shows on the website.", "success")
    return _back("admin.slides")


@bp.post("/slides/<int:item_id>")
@owner_required
def slide_update(item_id):
    item = content.slides.get(item_id) or abort(404)
    try:
        data = {"caption": _text("caption", 60)}
        upload = request.files.get("image")
        if upload and upload.filename:
            data["image"], data["image_small"] = images.save_slide(upload)
    except ValueError as err:
        flash(str(err), "error")
        return redirect(url_for("admin.slides") + f"#item-{item_id}")
    content.slides.update(item_id, **data)
    if "image" in data:
        images.delete_upload(item["image"])
        images.delete_upload(item["image_small"])
    flash("Slide saved.", "success")
    return redirect(url_for("admin.slides") + f"#item-{item_id}")


# Services ----------------------------------------------------------------------

def _choice(name, options, default):
    value = request.form.get(name, "")
    return value if value in options else default


def _service_form():
    return {
        "title": _text("title", 80),
        "category": _choice("category", content.CATEGORIES, "environmental"),
        "description": _text("description", 300),
        "tags": _text("tags", 150, required=False),
        "icon": _choice("icon", content.ICONS, "cleaning"),
        "accent": _choice("accent", content.ACCENTS, "gold"),
        "image_alt": _text("image_alt", 150, required=False),
        "details": _text("details", 4000, required=False),
        "includes": _text("includes", 2000, required=False),
    }


def _service_or_404(item_id):
    item = content.services.get(item_id)
    if item is None:
        abort(404)
    return item


@bp.get("/services")
@owner_required
def services():
    return render_template("admin/services.html", groups=content.services_by_category(active_only=False),
                           CATEGORIES=content.CATEGORIES)


@bp.post("/services/new")
@owner_required
def service_create():
    try:
        data = {
            "title": _text("title", 80),
            "category": _choice("category", content.CATEGORIES, "environmental"),
            "description": _text("description", 300),
            "icon": _choice("icon", content.ICONS, "cleaning"),
        }
        data["image"] = images.save_service(request.files.get("image"))
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.services")
    data["slug"] = content.new_slug(data["title"])
    service_id = content.services.create(**data)
    flash("Service added and showing on the website. Now add its page details below.", "success")
    return _back("admin.service_edit", item_id=service_id)


@bp.get("/services/<int:item_id>")
@owner_required
def service_edit(item_id):
    return render_template("admin/service_edit.html", s=_service_or_404(item_id),
                           sections=content.sections.all(service_id=item_id),
                           CATEGORIES=content.CATEGORIES, ACCENTS=content.ACCENTS)


@bp.post("/services/<int:item_id>")
@owner_required
def service_update(item_id):
    item = _service_or_404(item_id)
    try:
        data = _service_form()
        upload = request.files.get("image")
        if upload and upload.filename:
            data["image"] = images.save_service(upload)
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.service_edit", item_id=item_id)
    content.services.update(item_id, **data)
    if "image" in data:
        images.delete_upload(item["image"])
    flash("Service saved.", "success")
    return _back("admin.service_edit", item_id=item_id)


# Sub-sections of a service page ------------------------------------------------------

def _section_form():
    return {
        "title": _text("title", 100),
        "body": _text("body", 4000, required=False),
        "points_title": _text("points_title", 60, required=False),
        "points": _text("points", 2000, required=False),
        "image_alt": _text("image_alt", 150, required=False),
    }


def _section_or_404(section_id):
    section = content.sections.get(section_id)
    if section is None:
        abort(404)
    return section


def _to_section(section):
    return redirect(url_for("admin.service_edit", item_id=section["service_id"]) + f"#section-{section['id']}")


@bp.post("/services/<int:item_id>/sections/new")
@owner_required
def section_create(item_id):
    _service_or_404(item_id)
    try:
        data = _section_form()
        upload = request.files.get("image")
        if upload and upload.filename:
            data["image"] = images.save_service(upload)
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.service_edit", item_id=item_id)
    section_id = content.sections.create(service_id=item_id, **data)
    flash("Section added to the service page.", "success")
    return _to_section(content.sections.get(section_id))


@bp.post("/sections/<int:section_id>")
@owner_required
def section_update(section_id):
    section = _section_or_404(section_id)
    try:
        data = _section_form()
        upload = request.files.get("image")
        if upload and upload.filename:
            data["image"] = images.save_service(upload)
        elif request.form.get("remove_image"):
            data["image"] = ""
    except ValueError as err:
        flash(str(err), "error")
        return _to_section(section)
    content.sections.update(section_id, **data)
    if "image" in data:
        images.delete_upload(section["image"])
    flash("Section saved.", "success")
    return _to_section(section)


@bp.post("/sections/<int:section_id>/move/<direction>")
@owner_required
def section_move(section_id, direction):
    section = _section_or_404(section_id)
    content.sections.move(section_id, "up" if direction == "up" else "down")
    return _to_section(section)


@bp.post("/sections/<int:section_id>/delete")
@owner_required
def section_delete(section_id):
    section = _section_or_404(section_id)
    content.sections.delete(section_id)
    images.delete_upload(section["image"])
    flash("Section deleted.", "success")
    return _back("admin.service_edit", item_id=section["service_id"])


# Testimonials ------------------------------------------------------------------

@bp.get("/testimonials")
@owner_required
def testimonials():
    return render_template("admin/testimonials.html", items=content.testimonials.all())


@bp.post("/testimonials/new")
@owner_required
def testimonial_create():
    try:
        content.testimonials.create(quote=_text("quote", 1000), author=_text("author", 100))
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.testimonials")
    flash("Testimonial added.", "success")
    return _back("admin.testimonials")


@bp.post("/testimonials/<int:item_id>")
@owner_required
def testimonial_update(item_id):
    content.testimonials.get(item_id) or abort(404)
    try:
        content.testimonials.update(item_id, quote=_text("quote", 1000), author=_text("author", 100))
    except ValueError as err:
        flash(str(err), "error")
    else:
        flash("Testimonial saved.", "success")
    return redirect(url_for("admin.testimonials") + f"#item-{item_id}")


# Contact details ---------------------------------------------------------------

@bp.route("/settings", methods=["GET", "POST"])
@owner_required
def settings():
    if request.method == "POST":
        values = {key: (request.form.get(key) or "").strip()[:200] for key, _label, _type in content.SETTING_FIELDS}
        bad_links = []
        for key in content.SOCIAL_FIELDS:
            link = values[key]
            if link and not link.startswith(("https://", "http://")):
                link = values[key] = "https://" + link.lstrip("/")
            if link and ("." not in link or " " in link):
                bad_links.append(key.removesuffix("_url").replace("x", "X").capitalize())
        if not values["phone1"] or not values["email"]:
            flash("The main phone and public email are required.", "error")
        elif bad_links:
            flash(f"Check the {', '.join(bad_links)} link. Paste the full address of your profile page.", "error")
        else:
            content.save_settings(values)
            flash("Contact details saved. The website header, footer and contact section now use them.", "success")
            return _back("admin.settings")
    return render_template("admin/settings.html", settings=content.get_settings(), fields=content.SETTING_FIELDS)


# Users -------------------------------------------------------------------------

@bp.get("/users")
@owner_required
def users():
    return render_template("admin/users.html", users=auth.all_users())


@bp.post("/users/new")
@owner_required
def user_create():
    role = request.form.get("role", "staff")
    password = request.form.get("password", "")
    try:
        name, email = _text("name", 100), _text("email", 200)
    except ValueError as err:
        flash(str(err), "error")
        return _back("admin.users")
    problem = auth.password_problem(password) or (None if role in auth.ROLES else "Choose a role.")
    if problem:
        flash(problem, "error")
        return _back("admin.users")
    try:
        auth.create_user(name, email, password, role)
    except sqlite3.IntegrityError:
        flash(f"An account for {email} already exists.", "error")
        return _back("admin.users")
    flash(f"Account created for {name}. Share the password with them privately.", "success")
    return _back("admin.users")


def _other_user(user_id):
    user = auth.get_user(user_id) or abort(404)
    return user


@bp.post("/users/<int:user_id>/role")
@owner_required
def user_role(user_id):
    user = _other_user(user_id)
    role = request.form.get("role", "")
    if role not in auth.ROLES:
        abort(400)
    if user["role"] == "owner" and role != "owner" and auth.owner_count() == 1:
        flash("There must always be at least one owner.", "error")
    else:
        auth.set_role(user_id, role)
        if user_id == g.user["id"]:
            session["session_version"] = auth.get_user(user_id)["session_version"]
        flash(f"{user['name']} is now {auth.ROLES[role].split(' (')[0].lower()}.", "success")
    return _back("admin.users")


@bp.post("/users/<int:user_id>/password")
@owner_required
def user_password(user_id):
    user = _other_user(user_id)
    password = request.form.get("password", "")
    problem = auth.password_problem(password)
    if problem:
        flash(problem, "error")
    else:
        auth.set_password(user_id, password)
        if user_id == g.user["id"]:
            session["session_version"] = auth.get_user(user_id)["session_version"]
        flash(f"Password reset for {user['name']}. They have been signed out of other devices.", "success")
    return _back("admin.users")


@bp.post("/users/<int:user_id>/delete")
@owner_required
def user_delete(user_id):
    user = _other_user(user_id)
    if user_id == g.user["id"]:
        flash("You can't delete your own account.", "error")
    elif user["role"] == "owner" and auth.owner_count() == 1:
        flash("There must always be at least one owner.", "error")
    else:
        auth.delete_user(user_id)
        flash(f"{user['name']}'s account was deleted.", "success")
    return _back("admin.users")


# Own account -------------------------------------------------------------------

@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        if not check_password_hash(g.user["password_hash"], current):
            flash("Your current password is wrong.", "error")
        elif new != request.form.get("confirm_password", ""):
            flash("The new passwords don't match.", "error")
        elif problem := auth.password_problem(new):
            flash(problem, "error")
        else:
            auth.set_password(g.user["id"], new)
            session["session_version"] = auth.get_user(g.user["id"])["session_version"]
            flash("Password changed. Any other devices have been signed out.", "success")
            return _back("admin.account")
    return render_template("admin/account.html")
