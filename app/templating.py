"""Template filters and globals shared by the site and the admin."""
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from flask import g
from markupsafe import Markup, escape

from .content import ICONS
from .enquiries import STATUSES
from .security import csrf_token

NAIROBI = timezone(timedelta(hours=3))  # East Africa Time, no daylight saving


def icon(name, cls=""):
    paths = ICONS.get(name, ICONS["cleaning"])[1]
    cls_attr = f' class="{escape(cls)}"' if cls else ""
    return Markup(
        f'<svg{cls_attr} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>'
    )


# Contact and social icons (24x24, filled with currentColor).
SOCIAL_ICONS = {
    "whatsapp": '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9'
                '-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1'
                '-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2'
                ' 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/>',
    "instagram_url": '<path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zM17.3 5.5a1.2'
                     ' 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM16.5 2h-9A5.5 5.5 0 0 0 2 7.5v9A5.5 5.5 0 0 0 7.5 22h9a5.5 5.5 0 0'
                     ' 0 5.5-5.5v-9A5.5 5.5 0 0 0 16.5 2zm3.7 14.5a3.7 3.7 0 0 1-3.7 3.7h-9a3.7 3.7 0 0 1-3.7-3.7v-9a3.7 3.7'
                     ' 0 0 1 3.7-3.7h9a3.7 3.7 0 0 1 3.7 3.7z"/>',
    "tiktok_url": '<path d="M16.6 2h-3.3v13.4a2.9 2.9 0 1 1-2.9-2.9c.3 0 .6 0 .9.1V9.2a6.2 6.2 0 1 0 5.3 6.2V8.6a7.6 7.6 0 0 0'
                  ' 4.4 1.4V6.7A4.4 4.4 0 0 1 16.6 2z"/>',
    "x_url": '<path d="M17.8 3h3.1l-6.8 7.8L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.3-8.3L2 3h6.4l4.4 5.8zm-1.1 16.2h1.7L7.4 4.7H5.6z"/>',
}
SOCIAL_LABELS = {"instagram_url": "Instagram", "tiktok_url": "TikTok", "x_url": "X (Twitter)"}


def social_icon(name):
    return Markup(f'<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{SOCIAL_ICONS[name]}</svg>')


def tel(number):
    return re.sub(r"[^\d+]", "", number or "")


def whatsapp(number):
    """wa.me needs the international number without +, e.g. 0712... -> 254712..."""
    digits = re.sub(r"\D", "", number or "")
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif len(digits) == 9:
        digits = "254" + digits
    return digits


def local_time(value, fmt="%d %b %Y, %H:%M"):
    if not value:
        return ""
    stamp = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return stamp.astimezone(NAIROBI).strftime(fmt)


def maps_url(address):
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address or "")


def maps_embed(address):
    return "https://www.google.com/maps?output=embed&q=" + quote_plus(address or "")


def paragraphs(value):
    """Text with blank lines between paragraphs -> list of paragraphs."""
    return [p.strip() for p in re.split(r"\n\s*\n", value or "") if p.strip()]


def lines(value):
    """One item per line -> list, ignoring blank lines and leading bullet characters."""
    return [ln.strip().lstrip("-*• ").strip() for ln in (value or "").splitlines() if ln.strip().lstrip("-*• ").strip()]


def split_tags(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def init_app(app):
    app.jinja_env.filters.update(tel=tel, whatsapp=whatsapp, local_time=local_time, maps_url=maps_url, maps_embed=maps_embed, paragraphs=paragraphs, lines=lines,
                                 tags=split_tags)
    app.jinja_env.globals.update(icon=icon, social_icon=social_icon, csrf_token=csrf_token, STATUSES=STATUSES,
                                 ICONS=ICONS, SOCIAL_LABELS=SOCIAL_LABELS)

    @app.context_processor
    def inject():
        return {"csp_nonce": getattr(g, "csp_nonce", ""), "year": datetime.now(NAIROBI).year}
