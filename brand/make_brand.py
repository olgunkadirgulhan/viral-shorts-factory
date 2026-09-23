#!/usr/bin/env python3
"""make_brand.py — Why Stocks Moved kanal görselleri: banner, profil resmi, filigran.
Videolarla aynı palet (renderer.py). Çalıştır:  python brand/make_brand.py
"""
import math, os, pathlib, random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
NAME_A, NAME_B = "WHY", "STOCKS MOVED"
TAGLINE = "One real market move. Explained in 40 seconds."
SCHEDULE = "NEW SHORTS DAILY  ·  12:30 PM & 7 PM ET"

BG_TOP, BG_BOT = (8, 12, 26), (22, 32, 62)
FG, ACC, UP, DOWN, MUTED = (255, 255, 255), (255, 196, 0), (34, 197, 94), (239, 68, 68), (148, 163, 184)
BLACK = "C:/Windows/Fonts/ariblk.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"


def font(path, size):
    return ImageFont.truetype(path if os.path.exists(path) else BOLD, size)


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOT)))
    return img


def walk(n, seed, drift=0.35):
    """Deterministik 'hisse grafiği' serisi: yukarı eğilimli rastgele yürüyüş."""
    rnd = random.Random(seed)
    v, out = 0.0, []
    for _ in range(n):
        v += rnd.gauss(drift, 1.0)
        out.append(v)
    return out


def overlay(base, draw_fn, blur=0):
    """Yarı saydam çizimleri ayrı katmanda yapıp alfa ile karıştır (RGBA üstüne doğrudan çizim karıştırmaz)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def glow_line(base, pts, color, width, blur):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=color + (170,), width=width * 3, joint="curve")
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).line(pts, fill=color + (255,), width=width, joint="curve")


def to_pts(series, x0, y0, x1, y1):
    lo, hi = min(series), max(series)
    n = len(series)
    return [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * (v - lo) / ((hi - lo) or 1)) for i, v in enumerate(series)]


# ---------------- banner 2560x1440 (güvenli alan orta 1546x423) ----------------
def banner():
    W, H = 2560, 1440
    img = gradient(W, H).convert("RGBA")

    def grid(d):                                                  # ince ızgara
        for x in range(0, W, 80):
            d.line([(x, 0), (x, H)], fill=(255, 255, 255, 12))
        for y in range(0, H, 80):
            d.line([(0, y), (W, y)], fill=(255, 255, 255, 12))
    overlay(img, grid)
    # arka planda iki soluk grafik (TV'de ve masaüstünde görünen geniş alan)
    s1 = to_pts(walk(90, 7), -20, 180, W + 20, 640)
    s2 = to_pts(walk(90, 11, -0.2), -20, 860, W + 20, 1280)
    overlay(img, lambda d: d.polygon(s1 + [(W + 20, H), (-20, H)], fill=UP + (26,)))
    overlay(img, lambda d: d.line(s1, fill=UP + (90,), width=6, joint="curve"))
    overlay(img, lambda d: d.line(s2, fill=DOWN + (60,), width=5, joint="curve"))

    # güvenli alan (her cihazda görünen): 1546x423, merkez
    SW, SH = 1546, 423
    sx0, sy0 = (W - SW) // 2, (H - SH) // 2
    overlay(img, lambda d: d.rounded_rectangle([sx0 - 30, sy0 - 20, sx0 + SW + 30, sy0 + SH + 20], 40,
                                               fill=(8, 12, 26, 215)))
    d = ImageDraw.Draw(img)

    size = 150
    while True:                                                   # başlık güvenli alana sığana kadar küçült
        f_big = font(BLACK, size)
        wa = d.textlength(NAME_A + " ", font=f_big)
        wb = d.textlength(NAME_B, font=f_big)
        if wa + wb <= SW - 120:
            break
        size -= 4
    x = (W - wa - wb) / 2
    ty = sy0 + 45
    d.text((x, ty), NAME_A, font=f_big, fill=ACC)
    d.text((x + wa, ty), NAME_B, font=f_big, fill=FG)

    # başlığın altında yükselen mini grafik + nokta (videolardaki imza)
    mini = to_pts(walk(40, 5, 0.6), x, ty + size + 40, x + wa + wb - 30, ty + size + 95)
    glow_line(img, mini, UP, 7, 8)
    cx, cy = mini[-1]
    for r, a in ((26, 60), (16, 110)):
        overlay(img, lambda d, r=r, a=a: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=UP + (a,)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=UP)

    f_tag = font(BOLD, 52)
    d.text(((W - d.textlength(TAGLINE, font=f_tag)) / 2, sy0 + 300), TAGLINE, font=f_tag, fill=(226, 232, 240))
    f_sch = font(BOLD, 34)
    d.text(((W - d.textlength(SCHEDULE, font=f_sch)) / 2, sy0 + 378), SCHEDULE, font=f_sch, fill=ACC)
    img.convert("RGB").save(HERE / "banner_2560x1440.png", optimize=True)
    return img


# ---------------- ikon: yükselen grafik + sarı "?" ----------------
def icon(size=800, transparent=False):
    S = size * 2                                                  # 2x çizip küçült (yumuşak kenar)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0)) if transparent else gradient(S, S).convert("RGBA")
    if transparent:
        overlay(img, lambda d: d.ellipse([0, 0, S, S], fill=BG_TOP + (215,)))
    # daire içinde kalacak alan: merkez %70. Grafik solda yükselir, "?" sağda ayrı durur.
    pts = [(0.16, 0.68), (0.27, 0.55), (0.36, 0.62), (0.47, 0.42)]
    pts = [(x * S, y * S) for x, y in pts]
    glow_line(img, pts, UP, int(S * 0.045), int(S * 0.02))
    d = ImageDraw.Draw(img)
    cx, cy = pts[-1]
    r = S * 0.042
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=UP)
    f = font(BLACK, int(S * 0.50))
    q = "?"
    bb = d.textbbox((0, 0), q, font=f)
    qx = S * 0.69 - (bb[0] + bb[2]) / 2
    qy = S * 0.50 - (bb[1] + bb[3]) / 2
    overlay(img, lambda d: d.text((qx + S * 0.012, qy + S * 0.016), q, font=f, fill=(0, 0, 0, 150)), blur=S * 0.006)
    ImageDraw.Draw(img).text((qx, qy), q, font=f, fill=ACC)
    return img.resize((size, size), Image.LANCZOS)


def main():
    banner()
    icon(800).convert("RGB").save(HERE / "profile_800x800.png", optimize=True)
    icon(150, transparent=True).save(HERE / "watermark_150x150.png", optimize=True)
    # önizleme: telefonda profil resmi daire olarak görünür
    p = icon(800)
    mask = Image.new("L", p.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 800, 800], fill=255)
    circ = Image.new("RGBA", p.size, (255, 255, 255, 0))
    circ.paste(p, mask=mask)
    circ.save(HERE / "_preview_profile_circle.png")
    print("ok:", ", ".join(sorted(f.name for f in HERE.glob("*.png"))))


if __name__ == "__main__":
    main()
