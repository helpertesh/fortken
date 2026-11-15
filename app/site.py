"""Public website."""
import re
from urllib.parse import quote

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from . import content, enquiries, mail
from .security import RateLimiter
from .templating import SOCIAL_LABELS, whatsapp

bp = Blueprint("site", __name__)
enquiry_limiter = RateLimiter(limit=5, window=15 * 60)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s()-]{7,20}$")


WA_GREETING = "Hello KF 4Fortken, I'd like to request a service."


def _page_data():
    settings = content.get_settings()
    wa = ""
    if settings.get("whatsapp"):
        wa = f"https://wa.me/{whatsapp(settings['whatsapp'])}?text={quote(WA_GREETING)}"
    return {
        "settings": settings,
        "wa": wa,
        "socials": [key for key in SOCIAL_LABELS if settings.get(key)],
        "slides": content.slides.all(active_only=True),
        "services": content.services.all(active_only=True),
        "categories": content.services_by_category(),
        "testimonials": content.testimonials.all(active_only=True),
        "sent": request.args.get("sent") == "1",
        "failed": request.args.get("error") == "1",
    }


@bp.get("/")
def index():
    return render_template("site/index.html", **_page_data())


@bp.get("/contact")
def contact():
    return render_template("site/contact.html", **_page_data())


@bp.get("/services/")
def services():
    return redirect(url_for("site.index", _anchor="services"))


@bp.get("/services/<slug>")
def service(slug):
    item = content.service_by_slug(slug)
    if item is None or not item["active"]:
        abort(404)
    data = _page_data()
    related = [s for s in data["services"] if s["category"] == item["category"] and s["id"] != item["id"]]
    return render_template("site/service.html", service=item, category=content.CATEGORIES.get(item["category"]),
                           sections=content.sections.all(service_id=item["id"]), related=related, **data)


@bp.get("/letterhead")
def letterhead():
    return render_template("site/letterhead.html", settings=content.get_settings())


def _validate(form):
    data = {k: (form.get(k) or "").strip() for k in ("name", "phone", "email", "service", "message")}
    errors = {}
    if not 2 <= len(data["name"]) <= 100:
        errors["name"] = "Enter your name."
    if not PHONE_RE.match(data["phone"]):
        errors["phone"] = "Enter a valid phone number."
    if data["email"] and (len(data["email"]) > 200 or not EMAIL_RE.match(data["email"])):
        errors["email"] = "Enter a valid email address, or leave it empty."
    if not 5 <= len(data["message"]) <= 3000:
        errors["message"] = "Tell us a little about what you need (up to 3000 characters)."
    titles = {s["title"] for s in content.services.all()}
    if data["service"] not in titles:
        data["service"] = ""
    return data, errors


@bp.post("/enquiry")
def enquiry():
    wants_json = request.accept_mimetypes.best == "application/json"
    form = request.get_json(silent=True) or request.form

    def respond(ok, status=200, errors=None, message=""):
        if wants_json:
            return jsonify(ok=ok, errors=errors or {}, message=message), status
        args = {"sent": 1} if ok else {"error": 1}
        source = form.get("from_page", "")
        if source == "contact":
            return redirect(url_for("site.contact", **args, _anchor="contact"))
        if source.startswith("service:") and content.service_by_slug(source[8:]):
            return redirect(url_for("site.service", slug=source[8:], **args, _anchor="contact"))
        return redirect(url_for("site.index", **args, _anchor="contact"))

    # Bots fill in the hidden "website" field; pretend it worked and store nothing.
    if form.get("website"):
        return respond(True)
    if not enquiry_limiter.allow(request.remote_addr or "unknown"):
        return respond(False, 429, message="Too many requests. Please call us instead, or try again later.")
    data, errors = _validate(form)
    if errors:
        return respond(False, 400, errors, "Please check the highlighted fields.")
    saved = enquiries.create(ip=request.remote_addr or "", **data)
    mail.new_enquiry(saved, content.get_settings())
    return respond(True, message="Thank you. We have received your request and will contact you shortly.")
