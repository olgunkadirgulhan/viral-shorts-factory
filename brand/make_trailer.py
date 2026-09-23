#!/usr/bin/env python3
"""make_trailer.py — kanal karşılama videosu (16:9, ~25 sn), bugünün gerçek verisiyle.
Çıktı: brand/trailer.mp4     Çalıştır:  python brand/make_trailer.py
"""
import json, pathlib, shutil, subprocess, sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "brand"))
import renderer as R          # noqa: E402  (font, tts, fmt, grafik yardımcıları)
import make_brand as B        # noqa: E402  (ikon, palet)

W, H, FPS = 1920, 1080, 30
OUT = ROOT / "brand" / "trailer.mp4"
BIG_TECH = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "META"]

BEATS = [
    {"say": "Stocks move every single day. Most people never find out why.", "scene": "hook"},
    {"say": "On Why Stocks Moved, you get one real market move, explained in under forty seconds.", "scene": "phone"},
    {"say": "Nvidia, Apple, Tesla, the Fed, gold and oil. Real numbers from today's data. No hype, and no price predictions.", "scene": "tiles"},
    {"say": "Six new Shorts every single day. Subscribe, so you always know why.", "scene": "end"},
]


def bg():
    img = B.gradient(W, H).convert("RGBA")

    def grid(d):
        for x in range(0, W, 60):
            d.line([(x, 0), (x, H)], fill=(255, 255, 255, 10))
        for y in range(0, H, 60):
            d.line([(0, y), (W, y)], fill=(255, 255, 255, 10))
    B.overlay(img, grid)
    return img


def centered(d, y, text, f, fill):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def scene_hook(img, p, m):
    s = m["^GSPC"]["series"]
    pts = B.to_pts(s, 120, 330, W - 120, 900)
    k = max(2, int(len(pts) * R.ease(p / 0.8)))
    up = m["^GSPC"]["change_pct"] >= 0
    col = R.UP if up else R.DOWN
    B.overlay(img, lambda d: d.polygon(pts[:k] + [(pts[k - 1][0], 900), (pts[0][0], 900)], fill=col + (30,)))
    B.glow_line(img, pts[:k], col, 8, 10)
    d = ImageDraw.Draw(img)
    f = R.font(110)
    a, b = "STOCKS MOVE ", "EVERY DAY"
    x = (W - d.textlength(a + b, font=f)) / 2
    d.text((x, 110), a, font=f, fill=R.FG)
    d.text((x + d.textlength(a, font=f), 110), b, font=f, fill=R.ACC)
    if p > 0.55:
        centered(d, 940, "Most people never find out why.", R.font(56, bold=False), (226, 232, 240))


def scene_phone(img, p, m, phone_frame):
    d = ImageDraw.Draw(img)
    f = R.font(92)
    d.text((140, 300), "ONE MOVE.", font=f, fill=R.FG)
    d.text((140, 410), "UNDER 40 SEC.", font=f, fill=R.ACC)
    d.text((140, 560), "Chart first. The cause in plain English.", font=R.font(46, bold=False), fill=(226, 232, 240))
    # telefon: gerçek bir Short karesi, aşağıdan kayarak gelir
    ph_w, ph_h = 470, 836
    y = 122 + (1 - R.ease(p / 0.35)) * 700
    x = W - 180 - ph_w
    B.overlay(img, lambda d: d.rounded_rectangle([x - 18, y - 18, x + ph_w + 18, y + ph_h + 18], 56,
                                                 fill=(0, 0, 0, 120)), blur=18)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 14, y - 14, x + ph_w + 14, y + ph_h + 14], 52, fill=(30, 41, 59))
    shot = phone_frame.resize((ph_w, ph_h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (ph_w, ph_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, ph_w, ph_h], 40, fill=255)
    img.paste(shot, (int(x), int(y)), mask)


def scene_tiles(img, p, m):
    d = ImageDraw.Draw(img)
    centered(d, 90, "REAL NUMBERS. NO HYPE.", R.font(84), R.FG)
    keys = [k for k in BIG_TECH if k in m][:6]
    cols, tw, th, gap = 3, 520, 250, 40
    x0 = (W - cols * tw - (cols - 1) * gap) / 2
    for i, k in enumerate(keys):
        q = R.ease((p - i * 0.07) / 0.3)
        if q <= 0:
            continue
        cx = x0 + (i % cols) * (tw + gap)
        cy = 260 + (i // cols) * (th + gap) + (1 - q) * 60
        v = m[k]
        col = R.UP if v["change_pct"] >= 0 else R.DOWN
        B.overlay(img, lambda d, cx=cx, cy=cy, q=q: d.rounded_rectangle([cx, cy, cx + tw, cy + th], 30,
                                                                         fill=(30, 41, 59, int(235 * q))))
        d = ImageDraw.Draw(img)
        d.text((cx + 36, cy + 34), v["name"], font=R.font(54), fill=R.FG)
        d.text((cx + 36, cy + 126), R.pct_str(v["change_pct"], 2), font=R.font(70), fill=col)
        sp = B.to_pts(v["series"][-15:], cx + tw - 170, cy + 140, cx + tw - 36, cy + 200)
        d.line(sp, fill=col, width=5, joint="curve")
    d = ImageDraw.Draw(img)
    if p > 0.5:
        centered(d, 880, "Stocks · Big tech · The Fed · Gold · Oil · The dollar", R.font(48, bold=False), (226, 232, 240))
    centered(d, 960, "Today's closing data. Not financial advice.", R.font(34, bold=False), R.MUTED)


def scene_end(img, p, m, icon):
    s = 1 + 0.04 * R.ease(p / 0.3)
    ic = icon.resize((int(300 * s), int(300 * s)), Image.LANCZOS)
    img.alpha_composite(ic, ((W - ic.width) // 2, 120))
    d = ImageDraw.Draw(img)
    f = R.font(104)
    a, b = "WHY ", "STOCKS MOVED"
    x = (W - d.textlength(a + b, font=f)) / 2
    d.text((x, 470), a, font=f, fill=R.ACC)
    d.text((x + d.textlength(a, font=f), 470), b, font=f, fill=R.FG)
    centered(d, 610, "6 new Shorts every day", R.font(50), (226, 232, 240))
    if p > 0.35:                                                  # abone ol butonu
        pulse = 1 + 0.06 * abs(((p * 3) % 1) - 0.5)
        bw, bh = 520 * pulse, 120 * pulse
        bx, by = (W - bw) / 2, 790 - bh / 2
        d.rounded_rectangle([bx, by, bx + bw, by + bh], bh / 2, fill=(204, 0, 0))
        by = 730
        centered(d, by + 28, "SUBSCRIBE", R.font(62), R.FG)


def main():
    m = json.loads(subprocess.run([sys.executable, str(ROOT / "market_snapshot.py")], capture_output=True,
                                  text=True, encoding="utf-8", check=True).stdout)["tickers"]
    # telefondaki örnek Short karesi: günün en çok hareket eden Big Tech hissesi
    star = max((k for k in BIG_TECH if k in m), key=lambda k: abs(m[k]["change_pct"]))
    v = m[star]
    beat = {"say": f"{v['name']} moved {R.pct_str(v['change_pct'], 2)} today. Here's why.",
            "osd": f"Why {v['name']} moved", "emphasis": v["name"], "visual": "chart", "ticker": star}
    phone = R.frame(R._background(), beat, m, star, 3.0, 5.0, 3.0, 30.0)
    icon = B.icon(300, transparent=True)

    tmp = ROOT / "out" / "trailer_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        auds, durs = [], []
        for i, b in enumerate(BEATS):
            a = tmp / f"a{i}.mp3"
            R.tts(b["say"], a)
            auds.append(a)
            durs.append(R.duration(a) + 0.45)
        durs[-1] += 1.5                                           # son kareyi biraz tut
        total = sum(durs)
        fc = ";".join(f"[{i + 1}:a]apad=whole_dur={dd:.3f}[a{i}]" for i, dd in enumerate(durs))
        fc += ";" + "".join(f"[a{i}]" for i in range(len(durs))) + f"concat=n={len(durs)}:v=0:a=1[aout]"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-"] + sum((["-i", str(a)] for a in auds), []) + [
               "-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
               "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
               "-movflags", "+faststart", str(OUT)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        base = bg()
        starts = [sum(durs[:i]) for i in range(len(durs))]
        bi = 0
        for fi in range(int(total * FPS) + 1):
            t = fi / FPS
            while bi + 1 < len(BEATS) and t >= starts[bi + 1]:
                bi += 1
            prog = (t - starts[bi]) / durs[bi]
            img = base.copy()
            sc = BEATS[bi]["scene"]
            if sc == "hook":
                scene_hook(img, prog, m)
            elif sc == "phone":
                scene_phone(img, prog, m, phone)
            elif sc == "tiles":
                scene_tiles(img, prog, m)
            else:
                scene_end(img, prog, m, icon)
            fade = min(1.0, (t - starts[bi]) / 0.25)                # sahne girişinde kısa kararma geçişi
            if fade < 1 and bi > 0:
                B.overlay(img, lambda d, a=int(255 * (1 - fade)): d.rectangle([0, 0, W, H], fill=(8, 12, 26, a)))
            ImageDraw.Draw(img).rectangle([0, H - 8, W * t / total, H], fill=R.ACC)
            p.stdin.write(img.convert("RGB").tobytes())
        p.stdin.close()
        if p.wait():
            raise RuntimeError("ffmpeg failed")
        print(f"ok {OUT} ({total:.1f}s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
