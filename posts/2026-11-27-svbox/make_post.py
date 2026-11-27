"""Nov 27: every Scarlet & Violet booster box, 1 year later (same layout as Nov 26; gains green, losses red).
Data: TCGplayer weekly market price history (week of Dec 1 2025 vs week of Nov 23 2026), pulled Nov 26, 2026."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1, "/home/claude/daily/2026-11-25/carousel")
import importlib.util as _u
_sp = _u.spec_from_file_location("nov25", "/home/claude/daily/2026-11-25/carousel/make_post.py"); P = _u.module_from_spec(_sp); _sp.loader.exec_module(P)  # helpers: rays, shadow_text, line_parts, logo, anton
from cut3 import cutout as cut
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, "out"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1350; GREEN = P.GREEN; WHITE = P.WHITE

BOXES = [  # name, pid, week of Dec 1 2025, week of Nov 23 2026 (TCGplayer market)
    ("SCARLET & VIOLET", 476452, 218.29, 291.19),
    ("PALDEA EVOLVED", 493975, 351.04, 471.03),
    ("OBSIDIAN FLAMES", 501257, 297.37, 378.94),
    ("PARADOX RIFT", 512821, 237.62, 277.46),
    ("TEMPORAL FORCES", 536225, 270.53, 323.68),
    ("TWILIGHT MASQUERADE", 543846, 293.65, 324.93),
    ("STELLAR CROWN", 557354, 250.54, 308.24),
    ("SURGING SPARKS", 565606, 253.33, 294.26),
    ("JOURNEY TOGETHER", 610931, 221.33, 198.76),
    ("DESTINED RIVALS", 624679, 405.23, 386.40),
]
RED = (255, 92, 92)
BOXES.sort(key=lambda b: -(b[3] / b[2]))
img_path = lambda pid: os.path.join(D, "hi", f"{pid}.jpg")

def box_bg(pid, bright=0.62):
    c = cut(img_path(pid)); im = c.convert("RGB")
    art = im.crop((int(im.width * 0.15), int(im.height * 0.38), int(im.width * 0.85), int(im.height * 0.82)))
    s = max(W / art.width, H / art.height) * 1.1
    big = art.resize((int(art.width * s) + 2, int(art.height * s) + 2), Image.LANCZOS)
    x = (big.width - W) // 2; y = int((big.height - H) * 0.3)
    bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(16))
    return ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.1)).enhance(bright).convert("RGBA")

def fade(img, y0=640, amt=235):
    f = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(f)
    for yy in range(y0, H): u = min(1, (yy - y0) / 380); fd.line([(0, yy), (W, yy)], fill=(8, 10, 16, int(amt * u * u * (3 - 2 * u))))
    img.alpha_composite(f)

def place(img, p, x, y):
    sh = Image.new("RGBA", (p.width + 140, p.height + 140), (0, 0, 0, 0)); k = Image.new("RGBA", p.size, (0, 0, 0, 255))
    k.putalpha(p.getchannel("A").point(lambda v: v * 200 // 255)); sh.alpha_composite(k, (70, 80)); sh = sh.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(sh, (int(x) - 70, int(y) - 70)); img.alpha_composite(p, (int(x), int(y)))

def fit(p, mw, mh):
    r = min(mw / p.width, mh / p.height); return p.resize((int(p.width * r), int(p.height * r)), Image.LANCZOS)

def money(v): return f"${v:,.2f}"

def slide(rank, b):
    name, pid, old, new = b
    img = box_bg(pid); fade(img)
    p = fit(cut(img_path(pid)), 820, 640); place(img, p, (W - p.width) / 2, 680 - p.height)
    pct = (new / old - 1) * 100; COL = GREEN if pct >= 0 else RED
    P.shadow_text(img, (52, 44), f"#{rank}", P.anton(150), COL, slant=0.18, stroke=2)
    P.line_parts(img, 712, [(name, False)], 100)
    tsz = 100
    P.shadow_text(img, (None, 812), "BOOSTER BOX", P.anton(92), COL, stroke=2)
    ptxt = f"{pct:+.1f}%".replace("-", "−")
    pf = P.anton(240)
    while pf.getlength(ptxt) > 980: pf = P.anton(pf.size - 8)
    P.shadow_text(img, (None, 905), ptxt, pf, COL, stroke=2, blur=10, dy=6)
    # price line: white prices, green arrow, green slanted tail
    f = P.anton(84); parts = [(money(old), WHITE, 0), ("→", COL, 0), (money(new), WHITE, 0), ("SINCE DEC 2025", COL, 0.18)]
    while True:
        ws = [f.getlength(t) + (f.size * 0.18 if sl else 0) for t, _, sl in parts]; tot = sum(ws) + 26 * 3
        if tot <= W - 70: break
        f = P.anton(f.size - 4)
    x = (W - tot) / 2
    for (t, col, sl), w in zip(parts, ws):
        P.shadow_text(img, (x, 1140 + (14 if t == "→" else 0)), t, f, col, slant=sl, stroke=2); x += w + 26
    P.logo(img, H - 96)
    return img.convert("RGB")

def cover():
    a, b = BOXES[0], BOXES[1]
    img = box_bg(a[1], 0.85); P.rays(img, W / 2, 380, 34)
    pa = cut(img_path(a[1])); pb = cut(img_path(b[1]))
    sz = (520, 560)  # identical box: same width and height for both
    pa = fit(pa, *sz); pb = fit(pb, *sz)
    gap = -40  # slight overlap
    tot = pa.width + pb.width + gap; x0 = (W - tot) / 2; bottom = 660
    place(img, pb, x0 + pa.width + gap, bottom - pb.height)
    place(img, pa, x0, bottom - pa.height)
    fade(img, 600, 225)
    y = 690
    y = P.line_parts(img, y, [("EVERY", False), ("SCARLET & VIOLET", True)], 140) + 4
    y = P.line_parts(img, y, [("BOOSTER BOX,", False)], 140) + 4
    y = P.line_parts(img, y, [("1 YEAR LATER", False)], 140) + 16
    w, h = P.shadow_text(img, (None, y), "TCGPLAYER MARKET PRICE, DEC 2025 TO NOV 2026", P.anton(44), GREEN, slant=0.15, blur=6, dy=3)
    d = ImageDraw.Draw(img); ay = y + h + 26; x0, x1 = (W - w) / 2 + 70, (W + w) / 2 - 98
    d.line([(x0, ay), (x1, ay)], fill=GREEN, width=5); d.polygon([(x1 + 28, ay), (x1 - 2, ay - 15), (x1 - 2, ay + 15)], fill=GREEN)
    P.logo(img, H - 98)
    return img.convert("RGB")

if __name__ == "__main__":
    slides = [cover()] + [slide(r, b) for r, b in zip(range(10, 0, -1), BOXES[::-1])]
    cta = Image.open("/home/claude/tcgquant-media/posts/2026-11-23-drops/06-data.jpg").convert("RGB")
    slides.append(cta)
    names = [f"{i:02d}.jpg" for i in range(len(slides) - 1)] + [f"{len(slides) - 1:02d}-data.jpg"]
    for s, n in zip(slides, names): s.save(os.path.join(OUT, n), quality=93)
    bgs = [BOXES[0][1]] + [b[1] for b in BOXES[::-1]] + [BOXES[0][1]]
    for i, (s, pid) in enumerate(zip(slides, bgs)):
        im = cut(img_path(pid)).convert("RGB"); art = im.crop((int(im.width * 0.15), int(im.height * 0.38), int(im.width * 0.85), int(im.height * 0.82)))
        sc = max(W / art.width, 1920 / art.height); art = art.resize((int(art.width * sc) + 2, int(art.height * sc) + 2), Image.LANCZOS)
        art = art.crop(((art.width - W) // 2, (art.height - 1920) // 2, (art.width - W) // 2 + W, (art.height - 1920) // 2 + 1920)).filter(ImageFilter.GaussianBlur(14))
        art = ImageEnhance.Brightness(art).enhance(0.6)
        m = Image.new("L", (W, H), 255); md = ImageDraw.Draw(m)
        for k in range(70): md.line([(0, k), (W, k)], fill=int(255 * k / 70)); md.line([(0, H - 1 - k), (W, H - 1 - k)], fill=int(255 * k / 70))
        art.paste(s, (0, (1920 - H) // 2), m); art.save(os.path.join(OUT, f"tt-{i:02d}.jpg"), quality=92)
    sh = Image.new("RGB", (6 * 360 + 50, 2 * 450 + 10), (24, 24, 24))
    for i, s in enumerate(slides): sh.paste(s.resize((360, 450)), ((i % 6) * 370, (i // 6) * 460))
    sh.save(os.path.join(D, "overview.jpg"), quality=88)
    json.dump([dict(name=b[0], pid=b[1], dec2025=b[2], nov2026=b[3], pct=round((b[3] / b[2] - 1) * 100, 1)) for b in BOXES], open(os.path.join(D, "data.json"), "w"), indent=1)
