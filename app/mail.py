"""Email notifications. Sent on a background thread so the visitor isn't kept waiting.
Without SMTP settings in .env, messages are written to the log instead."""
import logging
import smtplib
import threading
from email.message import EmailMessage

from flask import current_app, url_for

log = logging.getLogger(__name__)


def _deliver(cfg, msg):
    try:
        if cfg["SMTP_PORT"] == 465:
            server = smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20)
        else:
            server = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20)
            server.starttls()
        with server:
            if cfg["SMTP_USER"]:
                server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.send_message(msg)
    except Exception:
        log.exception("Could not send email %r to %s", msg["Subject"], msg["To"])


def send(to, subject, body, reply_to=None):
    cfg = current_app.config
    if not cfg["SMTP_HOST"]:
        log.warning("Email not configured. Would have sent %r to %s", subject, to)
        return
    msg = EmailMessage()
    msg["From"] = cfg["MAIL_FROM"] or cfg["SMTP_USER"]
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    smtp = {k: cfg[k] for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD")}
    threading.Thread(target=_deliver, args=(smtp, msg), daemon=True).start()


def new_enquiry(enquiry, settings):
    """Alert the company, and confirm receipt to the visitor if they left an email."""
    link = url_for("admin.enquiry_detail", enquiry_id=enquiry["id"], _external=True)
    send(
        settings.get("notify_email") or settings.get("email"),
        f"New service request: {enquiry['service'] or 'General'} from {enquiry['name']}",
        f"Name: {enquiry['name']}\nPhone: {enquiry['phone']}\nEmail: {enquiry['email'] or '-'}\n"
        f"Service: {enquiry['service'] or '-'}\n\n{enquiry['message']}\n\nOpen in admin: {link}\n",
        reply_to=enquiry["email"] or None,
    )
    if enquiry["email"]:
        send(
            enquiry["email"],
            "We've received your request - KF 4Fortken Holdings Ltd",
            f"Hello {enquiry['name']},\n\nThank you for contacting KF 4Fortken Holdings Ltd. "
            f"We have received your request{' for ' + enquiry['service'] if enquiry['service'] else ''} "
            f"and will get back to you shortly.\n\nIf it's urgent, call us on {settings.get('phone1', '')}.\n\n"
            "KF 4Fortken Holdings Ltd\n",
        )
