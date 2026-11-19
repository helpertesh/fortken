"""Build the KF 4Fortken services showcase video (1280x720, H.264) from the website's photos.

usage: python make_video.py <site static dir> <output dir> [--timeline timeline.json]

With --timeline, scene lengths are read from the file's "lengths" (seconds, one per scene:
intro, photo scenes and title card in order, outro), and the scene start times are written back
as "starts" plus the total "duration". tools/build_showcase.py uses this to fit the narration.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

STATIC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
TIMELINE = Path(sys.argv[sys.argv.index("--timeline") + 1]) if "--timeline" in sys.argv else None
HERE = Path(__file__).parent
W, H, FPS = 1280, 720, 25
FADE = 0.6  # crossfade between scenes, seconds

PURPLE_950 = (41, 19, 57)
PURPLE_700 = (115, 68, 151)
GOLD = (212, 175, 90)
GOLD_LIGHT = (238, 218, 168)
CREAM = (252, 248, 239)

serif = lambda size: ImageFont.truetype(str(HERE / "DMSerif.ttf"), size)  # noqa: E731


def sans(size, weight="Bold"):
    font = ImageFont.truetype(str(HERE / "Manrope.ttf"), size)
    try:
        font.set_variation_by_name(weight)
    except Exception:
        pass
    return font


LOGO = Image.open(HERE / "logo-light.png").convert("RGBA")
LOGO = LOGO.crop(LOGO.getbbox())

IMG = STATIC / "assets" / "img"
# (division, title, subtitle, photo) — photos show African workers or no people.
SCENES = [
    ("Cleaning & Environmental", "Cleaning Services", "Post-construction, move-in, office, residential & commercial", IMG / "hero-cleaning.jpg"),
    ("Cleaning & Environmental", "Post-Construction Cleaning", "From construction mess to a spotless, ready space", STATIC / "uploads" / "f336519e4f16a440-1920.jpg", "bottom"),
    ("Cleaning & Environmental", "Fumigation & Pest Control", "Safe, effective pest management", IMG / "service-fumigation.jpg"),
    ("Cleaning & Environmental", "Garbage Collection", "Scheduled collection and sustainable waste management", IMG / "hero-waste.jpg"),
    ("Cleaning & Environmental", "Landscaping & Gardening", "Gardens, lawns and grounds kept green and tidy", IMG / "services" / "landscaping-gardening.jpg"),
    None,  # division title card
    ("Real Estate", "Property Management", "Now managing Hibiscus Homes, Shanzu", IMG / "services" / "property-management.jpg"),
    ("Real Estate", "Facilities Management", "Maintenance and building services under one plan", IMG / "services" / "facilities-management.jpg"),
    ("Real Estate", "Rent Collection", "On-time collection with clear landlord statements", IMG / "services" / "rent-collection.jpg"),
    ("Real Estate", "Land & Valuation", "Buying, selling and valuing land and property", IMG / "services" / "land.jpg"),
]
SCENE_LEN, CARD_LEN, INTRO_LEN, OUTRO_LEN = 3.2, 2.4, 4.0, 5.5


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def cover(img, w, h):
    """Scale an image to cover w x h."""
    scale = max(w / img.width, h / img.height)
    return img.resize((math.ceil(img.width * scale), math.ceil(img.height * scale)), Image.LANCZOS)


def text_w(draw, text, font):
    return draw.textlength(text, font=font)


def crenels(draw, y, color, up=True):
    """The battlement edge from the logo, across the frame."""
    x = 0
    while x < W:
        draw.rectangle([x, y - 12 if up else y, x + 30, y if up else y + 12], fill=color)
        x += 54


def gradient_overlay():
    """Purple shade over the left/bottom of photos so the white text stays readable."""
    ov = Image.new("RGBA", (W, H))
    px = ov.load()
    for x in range(W):
        a_left = int(235 * max(0.0, 1 - x / (W * 0.72)) ** 1.3)
        for y in range(H):
            a_bottom = int(200 * max(0.0, (y - H * 0.45) / (H * 0.55)) ** 1.5)
            px[x, y] = (*PURPLE_950, min(245, max(a_left, a_bottom)))
    return ov


OVERLAY = gradient_overlay()


def photo_scene(division, title, subtitle, photo, n_frames, index, anchor="center"):
    src = Image.open(photo).convert("RGB")
    base = cover(src, int(W * 1.12), int(H * 1.12))
    pan_dir = 1 if index % 2 == 0 else -1
    f_div, f_title, f_sub = sans(22, "ExtraBold"), serif(64), sans(28, "SemiBold")
    for i in range(n_frames):
        t = i / max(1, n_frames - 1)
        zoom = 1.0 + 0.08 * t  # slow Ken Burns push-in
        cw, ch = W * 1.12 / zoom, H * 1.12 / zoom
        cx = base.width / 2 + pan_dir * (base.width - cw) / 2 * (t - 0.5) * 0.8
        cy = base.height - ch / 2 if anchor == "bottom" else base.height / 2
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        frame = base.crop(tuple(int(v) for v in box)).resize((W, H), Image.BILINEAR).convert("RGBA")
        frame.alpha_composite(OVERLAY)
        d = ImageDraw.Draw(frame)
        show = ease((t * n_frames / FPS - 0.25) / 0.6)
        dy = int(24 * (1 - show))
        alpha = int(255 * show)
        layer = Image.new("RGBA", (W, H))
        ld = ImageDraw.Draw(layer)
        y0 = H - 250 + dy
        # gold battlement mark + division label
        for k in range(3):
            ld.rectangle([80 + k * 9, y0 + 6, 84 + k * 9, y0 + 20], fill=(*GOLD_LIGHT, alpha))
        ld.text((116, y0), division.upper(), font=f_div, fill=(*GOLD_LIGHT, alpha))
        ld.text((78, y0 + 34), title, font=f_title, fill=(255, 255, 255, alpha))
        ld.text((80, y0 + 120), subtitle, font=f_sub, fill=(255, 255, 255, int(alpha * 0.92)))
        frame.alpha_composite(layer)
        # small logo in the corner and a gold progress bar
        small = LOGO.resize((int(LOGO.width * 48 / LOGO.height), 48), Image.LANCZOS)
        badge = Image.new("RGBA", (small.width + 36, small.height + 24))
        ImageDraw.Draw(badge).rounded_rectangle([0, 0, badge.width - 1, badge.height - 1], radius=14, fill=(*PURPLE_950, 215))
        badge.alpha_composite(small, (18, 12))
        frame.alpha_composite(badge, (W - badge.width - 36, 32))
        d.rectangle([0, H - 6, int(W * t), H], fill=(*GOLD, 255))
        yield frame.convert("RGB")


def plain_card(n_frames, draw_fn):
    for i in range(n_frames):
        t = i / max(1, n_frames - 1)
        frame = Image.new("RGB", (W, H), PURPLE_950)
        d = ImageDraw.Draw(frame)
        crenels(d, H - 40, GOLD)
        d.rectangle([0, H - 40, W, H], fill=GOLD)
        draw_fn(frame, d, t)
        yield frame


def centered(d, y, text, font, fill):
    d.text(((W - text_w(d, text, font)) / 2, y), text, font=font, fill=fill)


def intro(n):
    f_tag, f_small = serif(58), sans(24, "SemiBold")

    def draw(frame, d, t):
        a = ease(t / 0.35)
        logo_h = int(150 + 12 * ease(t))
        logo = LOGO.resize((int(LOGO.width * logo_h / LOGO.height), logo_h), Image.LANCZOS)
        logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
        frame.paste(logo, ((W - logo.width) // 2, 150 - (logo_h - 150) // 2), logo)
        b = ease((t - 0.35) / 0.35)
        if b > 0:
            col = tuple(int(PURPLE_950[k] + (GOLD_LIGHT[k] - PURPLE_950[k]) * b) for k in range(3))
            centered(d, 380, "Cleaner, safer, better-kept properties.", f_tag, col)
            col2 = tuple(int(PURPLE_950[k] + (255 - PURPLE_950[k]) * b * 0.85) for k in range(3))
            centered(d, 470, "Cleaning  •  Fumigation  •  Waste  •  Landscaping  •  Real Estate", f_small, col2)
    return plain_card(n, draw)


def division_card(n):
    f_div, f_title, f_sub = sans(24, "ExtraBold"), serif(84), sans(28, "SemiBold")

    def draw(frame, d, t):
        a = ease(t / 0.4)
        col = tuple(int(PURPLE_950[k] + (GOLD_LIGHT[k] - PURPLE_950[k]) * a) for k in range(3))
        white = tuple(int(PURPLE_950[k] + (255 - PURPLE_950[k]) * a) for k in range(3))
        centered(d, 220, "OUR SECOND DIVISION", f_div, col)
        centered(d, 262, "Real Estate Services", f_title, white)
        centered(d, 390, "Property and facilities management, rent collection,", f_sub, white)
        centered(d, 430, "commercial leasing, land sales and valuation.", f_sub, white)
    return plain_card(n, draw)


def outro(n, contacts):
    f_title, f_line, f_cta = serif(66), sans(30, "Bold"), sans(26, "ExtraBold")

    def draw(frame, d, t):
        a = ease(t / 0.3)
        logo = LOGO.resize((int(LOGO.width * 92 / LOGO.height), 92), Image.LANCZOS)
        logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
        frame.paste(logo, ((W - logo.width) // 2, 70), logo)
        white = tuple(int(PURPLE_950[k] + (255 - PURPLE_950[k]) * a) for k in range(3))
        gold = tuple(int(PURPLE_950[k] + (GOLD_LIGHT[k] - PURPLE_950[k]) * a) for k in range(3))
        centered(d, 196, "Request a service today", f_title, white)
        for k, line in enumerate(contacts):
            b = ease((t - 0.2 - k * 0.08) / 0.25)
            col = tuple(int(PURPLE_950[c] + (gold[c] - PURPLE_950[c]) * b) for c in range(3))
            centered(d, 310 + k * 52, line, f_line, col)
        # gold call-to-action pill
        b = ease((t - 0.5) / 0.25)
        if b > 0:
            label = "Visit our website to send an enquiry"
            tw = text_w(d, label, f_cta)
            x0, y0 = (W - tw) / 2 - 34, 560
            fill = tuple(int(PURPLE_950[c] + (GOLD[c] - PURPLE_950[c]) * b) for c in range(3))
            d.rounded_rectangle([x0, y0, x0 + tw + 68, y0 + 62], radius=31, fill=fill)
            d.text((x0 + 34, y0 + 14), label, font=f_cta, fill=PURPLE_950)
    return plain_card(n, draw)


def default_lengths():
    return [INTRO_LEN] + [CARD_LEN if s is None else SCENE_LEN for s in SCENES] + [OUTRO_LEN]


def frames(contacts, lengths):
    """All scenes in order, each a frame generator plus its length in frames."""
    seq = [intro]
    idx = 0
    for scene in SCENES:
        if scene is None:
            seq.append(division_card)
        else:
            seq.append(lambda n, s=scene, k=idx: photo_scene(*s[:4], n, k, *s[4:]))
            idx += 1
    seq.append(lambda n: outro(n, contacts))
    return [(make, round(sec * FPS)) for make, sec in zip(seq, lengths)]


def render(contacts, mp4, poster, lengths):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE)
    fade = int(FADE * FPS)
    tail = []  # last frames of the previous scene, blended into the next
    total = 0
    starts = []
    plan = frames(contacts, lengths)
    for k, (make, n) in enumerate(plan):
        starts.append(total / FPS)
        scene = list(make(n))
        if k == 0:
            scene[int(len(scene) * 0.8)].save(poster, quality=85)
        if tail:
            for j in range(min(fade, len(tail))):
                scene[j] = Image.blend(tail[j], scene[j], (j + 1) / (fade + 1))
        body = scene[: len(scene) - fade] if k < len(plan) - 1 else scene
        for frame in body:
            proc.stdin.write(frame.tobytes())
            total += 1
        tail = scene[len(scene) - fade:]
    proc.stdin.close()
    proc.wait()
    print(f"wrote {mp4} ({total} frames, {total / FPS:.1f}s)")
    return starts, total / FPS


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    contacts = [a for a in sys.argv[3:] if not a.startswith("--") and not a.endswith(".json")] or ["+254 703 178 323   |   +254 783 474 570", "WhatsApp 010 0106340   |   4fortken@gmail.com",
                                "Moli Center, Links Road, Mombasa"]
    timeline = json.loads(TIMELINE.read_text()) if TIMELINE and TIMELINE.exists() else {}
    lengths = timeline.get("lengths") or default_lengths()
    starts, duration = render(contacts, OUT / "kf-services.mp4", OUT / "kf-services-poster.jpg", lengths)
    if TIMELINE:
        timeline.update(starts=starts, duration=duration)
        TIMELINE.write_text(json.dumps(timeline, indent=1))
