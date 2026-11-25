"""Nov 25: Prismatic Evolutions booster bundle listings down 74% (Oct 22 -> Nov 5), price check style (matches Nov 24 151 UPC slides).
Data: TCG Quant ALL_DATASETS/METRICS_HISTORY 'Specialty Set Bundles::Prismatic Evolutions', pulled Nov 25, 2026."""
import os, sys, math, datetime as dt
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
sys.path.insert(0, "/home/claude/tcgquant-media/automation"); import visuals as V
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, "out"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1350
WHITE = (255, 255, 255); GREEN = (46, 230, 166); INK = (11, 15, 23); MUTED = (150, 163, 184)
anton = V._anton; inter = lambda w, s: V._inter(w, s)

SUP = [("2026-04-23",1731),("2026-05-07",1842),("2026-05-21",1875),("2026-06-04",1979),("2026-06-18",2080),("2026-07-02",1805),("2026-07-16",1867),
       ("2026-07-30",1951),("2026-08-13",2043),("2026-08-27",2164),("2026-09-10",1662),("2026-09-24",2123),("2026-10-08",2189),("2026-10-22",2432),
       ("2026-11-05",631),("2026-11-19",877)]
PRICE = [("2025-11-25",None)]  # filled below
HIST = [("2025-12-09",None)]

def cutout(path):
    im = Image.open(path).convert("RGB"); a = np.array(im).astype(int)
    nw = a.min(2) < 236; nw[:12] = 0; nw[-12:] = 0; nw[:, :12] = 0; nw[:, -12:] = 0
    ys, xs = np.nonzero(nw); hull = cv2.convexHull(np.c_[xs, ys].astype(np.int32))
    m = np.zeros(a.shape[:2], np.uint8); cv2.fillPoly(m, [hull], 255); m = cv2.erode(m, np.ones((3, 3), np.uint8))
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(m).filter(ImageFilter.GaussianBlur(0.8))); return out.crop(out.getbbox())

def art_bg(bright=0.8, zoom=2.4, focus=(0.5, 0.36)):
    card = Image.open(os.path.join(D, "610516.jpg")).convert("RGB")
    art = card.crop((int(card.width * 0.08), int(card.height * 0.16), int(card.width * 0.92), int(card.height * 0.56)))
    s = max(W / art.width, H / art.height) * zoom / 2.4 * 1.0
    big = art.resize((int(art.width * s) + 2, int(art.height * s) + 2), Image.LANCZOS)
    x = int((big.width - W) * focus[0]); y = int((big.height - H) * focus[1])
    bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(6))
    return ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.1)).enhance(bright).convert("RGBA")

def rays(img, cx, cy, alpha=40):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(18):
        a0 = k * 20 * math.pi / 180; a1 = a0 + 8 * math.pi / 180; R = 2000
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=(255, 255, 255, alpha))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))

def shadow_text(img, xy, text, font, fill, slant=0.0, stroke=0, blur=8, dy=4):
    bb = font.getbbox(text, stroke_width=stroke); w, h = bb[2] - bb[0] + 40, bb[3] + 30
    t = Image.new("RGBA", (w + int(h * slant), h), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((20 - bb[0] + int(h * slant), 10), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    if slant: t = t.transform(t.size, Image.AFFINE, (1, slant, 0, 0, 1, 0), Image.BICUBIC)
    t = t.crop(t.getbbox()); sh = Image.new("RGBA", (t.width + 6 * blur, t.height + 6 * blur), (0, 0, 0, 0))
    k = Image.new("RGBA", t.size, (0, 0, 0, 255)); k.putalpha(t.getchannel("A").point(lambda v: v * 230 // 255)); sh.alpha_composite(k, (3 * blur, 3 * blur))
    sh = sh.filter(ImageFilter.GaussianBlur(blur)); x, y = xy
    if x is None: x = (W - t.width) / 2
    img.alpha_composite(sh, (int(x - 3 * blur), int(y - 3 * blur + dy))); img.alpha_composite(t, (int(x), int(y))); return t.width, t.height

def line_parts(img, y, parts, size, maxw=W - 90):
    """parts: [(text, green?)]; green words slanted. centred."""
    while True:
        f = anton(size); widths = [f.getlength(t) + (size * 0.18 if g else 0) for t, g in parts]
        tot = sum(widths) + size * 0.22 * (len(parts) - 1)
        if tot <= maxw or size < 40: break
        size -= 4
    x = (W - tot) / 2; hmax = 0
    for (t, g), w in zip(parts, widths):
        _, h = shadow_text(img, (x, y), t, f, GREEN if g else WHITE, slant=0.18 if g else 0, stroke=2); x += w + size * 0.22; hmax = max(hmax, h)
    return y + hmax

def logo(img, y=H - 62):
    lk = V.lockup(34); img.alpha_composite(lk, ((W - lk.width) // 2, y))

def cover():
    img = art_bg(1.0); rays(img, W / 2, 400, 40)
    p = cutout(os.path.join(D, "600518.jpg")); r = min(800 / p.width, 680 / p.height); p = p.resize((int(p.width * r), int(p.height * r)), Image.LANCZOS)
    sh = Image.new("RGBA", (p.width + 140, p.height + 140), (0, 0, 0, 0)); k = Image.new("RGBA", p.size, (0, 0, 0, 255)); k.putalpha(p.getchannel("A").point(lambda v: v * 200 // 255))
    sh.alpha_composite(k, (70, 80)); sh = sh.filter(ImageFilter.GaussianBlur(30)); x = (W - p.width) // 2; y = 50
    img.alpha_composite(sh, (x - 70, y - 70)); img.alpha_composite(p, (x, y))
    fade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fade)
    for yy in range(700, H): u = min(1, (yy - 700) / 300); fd.line([(0, yy), (W, yy)], fill=(8, 10, 16, int(200 * u * u * (3 - 2 * u))))
    img.alpha_composite(fade)
    y = 770
    y = line_parts(img, y, [("PRISMATIC", False), ("BUNDLE", False)], 140) + 6
    y = line_parts(img, y, [("LISTINGS", False), ("DOWN", True)], 140) + 6
    y = line_parts(img, y, [("74%", True), ("IN", False), ("2", False), ("WEEKS", False)], 140) + 14
    shadow_text(img, (None, y), "EBAY LISTINGS NEAR MARKET, OCT 22 TO NOV 5", anton(40), GREEN, slant=0.15, blur=6, dy=3)
    logo(img); return img.convert("RGB")

def chart_slide(title_parts, sub, points, kind, stats, marks):
    img = art_bg(0.8, focus=(0.5, 0.5))
    y = line_parts(img, 46, title_parts, 104) + 2
    shadow_text(img, (None, y), sub, anton(38), GREEN, slant=0.15, blur=6, dy=3)
    px0, py0, px1, py1 = 40, 250, W - 40, 1010
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((px0, py0, px1, py1), 34, fill=(16, 20, 30, 222), outline=(255, 255, 255, 30), width=2)
    img.alpha_composite(g); d = ImageDraw.Draw(img, "RGBA")
    cx0, cy0, cx1, cy1 = px0 + 120, py0 + 80, px1 - 50, py1 - 80
    vals = [v for _, v in points]; vmax = max(vals) * 1.15
    raw = vmax / 4; mag = 10 ** math.floor(math.log10(raw)); step = min(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    Y = lambda v: cy1 - v / vmax * (cy1 - cy0)
    t0 = dt.date.fromisoformat(points[0][0]); t1 = dt.date.fromisoformat(points[-1][0]); span = (t1 - t0).days
    X = lambda s: cx0 + (dt.date.fromisoformat(s) - t0).days / span * (cx1 - cx0)
    fa = inter("SemiBold", 26)
    v = 0
    while v <= vmax:
        yy = Y(v); d.line([(cx0, yy), (cx1, yy)], fill=(255, 255, 255, 60 if v == 0 else 26), width=1)
        lab = (f"${v:,.0f}" if kind == "price" else f"{v:,.0f}"); d.text((cx0 - 18 - d.textlength(lab, font=fa), yy - 15), lab, font=fa, fill=MUTED); v += step
    months = sorted({s[:7] for s, _ in points}); every = max(1, round(len(months) / 4))
    for i, mth in enumerate(months):
        if i % every: continue
        s = mth + "-01"
        if not (points[0][0] <= s <= points[-1][0]): s = points[0][0] if i == 0 else s
        if s > points[-1][0]: continue
        lab = dt.date.fromisoformat(s).strftime("%b %Y"); d.text((X(s) - d.textlength(lab, font=fa) / 2, cy1 + 16), lab, font=fa, fill=MUTED)
    if kind == "price":
        yy = Y(26.94); x = cx0
        while x < cx1: d.line([(x, yy), (min(x + 18, cx1), yy)], fill=(255, 255, 255, 200), width=3); x += 30
        fl = inter("Bold", 28); t = "MSRP $26.94"; d.text((cx1 - d.textlength(t, font=fl), yy - 44), t, font=fl, fill=WHITE)
    pts = [(X(s), Y(v)) for s, v in points]
    area = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], Y(0)), (pts[0][0], Y(0))], fill=GREEN + (52,))
    img.alpha_composite(area); d = ImageDraw.Draw(img, "RGBA"); d.line(pts, fill=GREEN, width=7, joint="curve")
    fm = anton(46)
    for s, txt, dx, dy in marks:
        v = dict(points)[s]; x, y = X(s), Y(v)
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=WHITE, outline=GREEN, width=5)
        tw = d.textlength(txt, font=fm); tx = min(max(x + dx - tw / 2, cx0 - 60), cx1 - tw + 30); d.text((tx, y + dy), txt, font=fm, fill=WHITE)
    colw = (W - 80) / 3
    for i, (v, l) in enumerate(stats):
        f1 = anton(84)
        while f1.getlength(v) > colw - 30: f1 = anton(f1.size - 4)
        cx = 40 + i * colw + colw / 2
        w1, h1 = shadow_text(img, (cx - (f1.getlength(v) + f1.size * 0.16) / 2, 1040), v, f1, GREEN if i == 0 else WHITE, slant=0.16, blur=8)
        f2 = anton(34); shadow_text(img, (cx - (f2.getlength(l) + 6) / 2, 1040 + h1 + 10), l, f2, GREEN, slant=0.15, blur=6, dy=3)
    logo(img); return img.convert("RGB")

PRICE = [("2025-11-25",72.24),("2025-12-09",71.06),("2026-01-06",73.5),("2026-02-03",76.43),("2026-03-03",77.92),("2026-03-31",79.86),
         ("2026-04-28",82.03),("2026-05-26",89.36),("2026-06-23",97.08),("2026-07-21",86.48),("2026-08-18",86.17),("2026-09-15",86.9),
         ("2026-10-13",84.55),("2026-10-22",83.35),("2026-11-05",66.71),("2026-11-19",70.39),("2026-11-25",75.11)]
if __name__ == "__main__":
    import json
    PRICE = [tuple(x) for x in json.load(open(os.path.join(D, "price.json")))]
    s0 = cover()
    s1 = chart_slide([("PRISMATIC", False), ("BUNDLE", False), ("LISTINGS", True)], "EBAY LISTINGS NEAR MARKET, APR TO NOV 2026", SUP, "supply",
                     [("-74%", "OCT 22 → NOV 5"), ("631", "LOW ON NOV 5"), ("877", "LISTED NOW")],
                     [("2026-10-22", "2,432", -40, -78), ("2026-11-05", "631", 0, 22), ("2026-11-19", "877", 10, -78)])
    s2 = chart_slide([("PRISMATIC", False), ("BUNDLE", False), ("PRICE", True)], "TCGPLAYER MARKET PRICE, APR TO NOV 2026", PRICE, "price",
                     [(f"+{(75.11/66.71-1)*100:.0f}%", "SINCE NOV 5 LOW"), ("$75.11", "TODAY"), (f"{75.11/26.94:.1f}X", "MSRP ($26.94)")],
                     [(PRICE[-1][0], "$75", -30, -80), ("2026-11-05", "$67", 0, 22), (max(PRICE, key=lambda x: x[1])[0], "PEAK $" + f"{max(v for _, v in PRICE):.0f}", 0, -80)])
    cta = Image.open("/home/claude/tcgquant-media/posts/2026-11-23-drops/06-data.jpg").convert("RGB")
    slides = [s0, s1, s2, cta]
    for i, s in enumerate(slides): s.save(os.path.join(OUT, f"{i:02d}.jpg" if i < 3 else "03-data.jpg"), quality=93)
    # TikTok 9:16 versions: blurred art extension behind the 4:5 slide
    for i, s in enumerate(slides):
        bg = art_bg(0.55).resize((W, int(H * 1920 / H)), Image.LANCZOS) if False else None
        base = Image.open(os.path.join(D, "610516.jpg")).convert("RGB")
        art = base.crop((int(base.width * 0.08), int(base.height * 0.16), int(base.width * 0.92), int(base.height * 0.56)))
        sc = max(W / art.width, 1920 / art.height); art = art.resize((int(art.width * sc) + 2, int(art.height * sc) + 2), Image.LANCZOS)
        art = art.crop(((art.width - W) // 2, (art.height - 1920) // 2, (art.width - W) // 2 + W, (art.height - 1920) // 2 + 1920)).filter(ImageFilter.GaussianBlur(14))
        art = ImageEnhance.Brightness(art).enhance(0.6)
        m = Image.new("L", (W, H), 255); md = ImageDraw.Draw(m)
        for k in range(70): md.line([(0, k), (W, k)], fill=int(255 * k / 70)); md.line([(0, H - 1 - k), (W, H - 1 - k)], fill=int(255 * k / 70))
        art.paste(s, (0, (1920 - H) // 2), m); art.save(os.path.join(OUT, f"tt-{i:02d}.jpg"), quality=92)
    sh = Image.new("RGB", (4 * 540 + 30, 675), (24, 24, 24))
    for i, s in enumerate(slides): sh.paste(s.resize((540, 675)), (i * 550, 0))
    sh.save(os.path.join(D, "overview.jpg"), quality=88)
