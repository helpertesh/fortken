"""Resize uploaded photos so the site stays fast on mobile data."""
import secrets
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageError(ValueError):
    pass


def _open(file_storage):
    if not file_storage or not file_storage.filename:
        raise ImageError("Choose a photo to upload.")
    try:
        img = Image.open(BytesIO(file_storage.read()))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ImageError("That file isn't a photo we can read. Upload a JPG, PNG or WebP image.")
    if img.format not in ALLOWED_FORMATS:
        raise ImageError("Upload a JPG, PNG or WebP image.")
    return ImageOps.exif_transpose(img).convert("RGB")


def _save(img, suffix):
    name = f"{secrets.token_hex(8)}-{suffix}.jpg"
    img.save(Path(current_app.config["UPLOAD_FOLDER"]) / name, "JPEG", quality=78, optimize=True, progressive=True)
    return f"/uploads/{name}"


def _width(img, width):
    if img.width <= width:
        return img.copy()
    return img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)


def save_slide(file_storage):
    """Full-screen slide: a 1920px version for large screens and 960px for phones."""
    img = _open(file_storage)
    if img.width < 1200:
        raise ImageError("Slide photos need to be at least 1200 pixels wide so they stay sharp full-screen.")
    return _save(_width(img, 1920), "1920"), _save(_width(img, 960), "960")


def save_service(file_storage):
    """Service card photo, cropped to 3:2."""
    img = _open(file_storage)
    return _save(ImageOps.fit(img, (900, 600), Image.LANCZOS), "card")


def delete_upload(url):
    """Delete a file this app uploaded. Built-in images under /assets are never touched."""
    if not url or not url.startswith("/uploads/"):
        return
    name = url.removeprefix("/uploads/")
    if "/" in name or "\\" in name or name.startswith("."):
        return
    (Path(current_app.config["UPLOAD_FOLDER"]) / name).unlink(missing_ok=True)
