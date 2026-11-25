"""Visuals for TCG Quant daily X/Threads text posts.
  chart(points, out, title, sub, money_fmt=True, marks=True)  -> 1200x675 price chart (dark, brand green)
  photo_card(img_path, out, headline, stat, sub="")           -> 1080x1350 product/card photo with one stat
Fonts: Anton (downloaded on first use) + Inter (system). Logo: assets/logo.png next to this file."""
import os, math, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ANTON = os.path.join(HERE, "assets", "Anton.ttf")
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
BG = (11, 15, 23); PANEL = (20, 25, 36); GREEN = (46, 230, 166); BRAND = (22, 184, 138)
WHITE = (255, 255, 255); MUTED = (148, 160, 182); RED = (248, 92, 92)

def _anton(size):
    if not os.path.exists(ANTON):
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf", ANTON)
    return ImageFont.truetype(ANTON, size)
def _inter(w, size): return ImageFont.truetype(INTER.format(w), size)

def _logo(h):
    im = Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGB"); a = np.array(im).astype(int)
    alpha = np.clip((a.max(2) - 30) * 4, 0, 255).astype(np.uint8)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(alpha)); out = out.crop(out.getbbox())
    return out.resize((int(out.width * h / out.height), h), Image.LANCZOS)

def lockup(h=44):
    ic = _logo(h); f = _inter("ExtraBold", int(h * 0.8)); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = int(d0.textlength("TCG QUANT", font=f))
    im = Image.new("RGBA", (ic.width + 12 + tw + 4, h + 8), (0, 0, 0, 0)); im.alpha_composite(ic, (0, 4))
    ImageDraw.Draw(im).text((ic.width + 12, 4 + (h - f.size) // 2 - 4), "TCG QUANT", font=f, fill=GREEN); return im

def _money(v): return f"${v:,.0f}" if v >= 100 else f"${v:,.2f}"

def chart(points, out, title, sub="", marks=True):
    """points: [(YYYY-MM-DD, price), ...] oldest first."""
    import datetime as dt
    W, H = 1200, 675
    img = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(img, "RGBA")
    d.text((48, 34), title, font=_anton(54), fill=WHITE)
    if sub: d.text((50, 104), sub, font=_inter("SemiBold", 24), fill=MUTED)
    lk = lockup(34); img.alpha_composite(lk, (W - lk.width - 40, 44))
    x0, y0, x1, y1 = 120, 160, W - 60, H - 70
    vals = [p for _, p in points]; lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.18 or hi * 0.1; vmin = max(0, lo - pad); vmax = hi + pad
    ts = [dt.date.fromisoformat(a) for a, _ in points]; t0, t1 = ts[0], ts[-1]; span = max(1, (t1 - t0).days)
    X = lambda t: x0 + (t - t0).days / span * (x1 - x0); Y = lambda v: y1 - (v - vmin) / (vmax - vmin) * (y1 - y0)
    fa = _inter("Medium", 20)
    raw = (vmax - vmin) / 4; mag = 10 ** math.floor(math.log10(raw)); step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw))
    v = math.ceil(vmin / step) * step
    while v <= vmax:
        y = Y(v); d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 22), width=1)
        t = _money(v); d.text((x0 - 14 - d.textlength(t, font=fa), y - 12), t, font=fa, fill=MUTED); v += step
    months = sorted({(a.year, a.month) for a in ts}); every = max(1, round(len(months) / 6))
    for i, (yy, mm) in enumerate(months[1:], 1):
        if i % every: continue
        t = dt.date(yy, mm, 1)
        if t < t0 or t > t1: continue
        lab = t.strftime("%b %Y") if mm == 1 else t.strftime("%b")
        d.text((X(t) - d.textlength(lab, font=fa) / 2, y1 + 14), lab, font=fa, fill=MUTED)
    pts = [(X(t), Y(v)) for t, v in zip(ts, vals)]
    area = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], y1), (pts[0][0], y1)], fill=GREEN + (44,))
    img.alpha_composite(area); d = ImageDraw.Draw(img, "RGBA")
    d.line(pts, fill=GREEN, width=5, joint="curve")
    if marks:
        fm = _anton(34)
        hi_i = int(np.argmax(vals)); items = [(len(vals) - 1, "now")]
        if hi_i != len(vals) - 1: items.append((hi_i, "peak"))
        for i, kind in items:
            x, y = pts[i]; d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=WHITE, outline=GREEN, width=4)
            t = _money(vals[i]) if kind == "now" else "PEAK " + _money(vals[i])
            tw = d.textlength(t, font=fm)
            if kind == 'now': tx, ty = x - tw - 18, y + 12
            else: tx = min(max(x - tw / 2, x0), x1 - tw); ty = y - 58 if y - 58 > y0 - 10 else y + 16
            d.text((tx, ty), t, font=fm, fill=WHITE)
    img.convert("RGB").save(out, quality=92); return out

def photo_card(img_path, out, headline, stat, sub=""):
    W, H = 1080, 1350
    ph = Image.open(img_path).convert("RGB")
    bg = ph.copy(); s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * s) + 2, int(bg.height * s) + 2), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(28))
    img = ImageEnhance.Brightness(bg).enhance(0.55).convert("RGBA")
    # photo: rounded, shadowed, centered upper area (white backgrounds of product shots are kept: product photos are framed as a card)
    mw, mh = 820, 820; r = min(mw / ph.width, mh / ph.height); p = ph.resize((int(ph.width * r), int(ph.height * r)), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", p.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, p.width - 1, p.height - 1), 28, fill=255); p.putalpha(m)
    sh = Image.new("RGBA", (p.width + 120, p.height + 120), (0, 0, 0, 0)); sm = Image.new("L", sh.size, 0)
    ImageDraw.Draw(sm).rounded_rectangle((60, 70, 60 + p.width, 70 + p.height), 28, fill=190); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(26)))
    px = (W - p.width) // 2; py = 90 + (mh - p.height) // 2
    img.alpha_composite(sh, (px - 60, py - 60)); img.alpha_composite(p, (px, py))
    d = ImageDraw.Draw(img, "RGBA")
    def fit(text, font_fn, size, maxw):
        while size > 20 and d.textlength(text, font=font_fn(size)) > maxw: size -= 2
        return font_fn(size)
    fh = fit(headline, _anton, 76, W - 100); d.text(((W - d.textlength(headline, font=fh)) / 2, 960), headline, font=fh, fill=WHITE)
    fs = fit(stat, _anton, 120, W - 100); d.text(((W - d.textlength(stat, font=fs)) / 2, 1055), stat, font=fs, fill=GREEN)
    if sub:
        fsub = fit(sub, lambda z: _inter("SemiBold", z), 30, W - 120); d.text(((W - d.textlength(sub, font=fsub)) / 2, 1210), sub, font=fsub, fill=MUTED)
    lk = lockup(34); img.alpha_composite(lk, ((W - lk.width) // 2, 1270))
    img.convert("RGB").save(out, quality=92); return out
