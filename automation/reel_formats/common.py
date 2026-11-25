"""Shared pieces for the new reel formats. Reuses the race reel's brand helpers and hook motion unchanged."""
import sys, math, subprocess, os
sys.path.insert(0, "/home/claude/sp")
from race import (W, H, FPS, font, ease, money, rounded, cover_crop, skew_text, shadow_paste, lockup, fit_text,
                  GREEN, BRAND, WHITE, MUTED, RED, PANEL)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

CARDS = "/home/claude/newreels/cards/"

def card_img(pid, hi=False):
    f = CARDS + f"{pid}_hi.jpg"
    return Image.open(f if hi and os.path.exists(f) else CARDS + f"{pid}.jpg").convert("RGB")

def hook_bg(hero, box=(0.14, 0.07, 0.86, 0.40), focus=(0.5, 0.4), contrast=1.0, color=1.15):
    hb = cover_crop(hero.crop((int(hero.width * box[0]), int(hero.height * box[1]), int(hero.width * box[2]), int(hero.height * box[3]))), W, H, focus).filter(ImageFilter.GaussianBlur(5))
    hb = ImageEnhance.Color(hb).enhance(color)
    if contrast != 1.0: hb = ImageEnhance.Contrast(hb).enhance(contrast)
    return ImageEnhance.Brightness(hb).enhance(1.1).convert("RGBA")

def dark_bg(hero, bright=0.42):
    bg = cover_crop(hero.crop((40 * hero.width // 1000, 90 * hero.width // 1000, hero.width - 40 * hero.width // 1000, int(hero.height * 0.55))), W, H, (0.5, 0.35)).filter(ImageFilter.GaussianBlur(26))
    return ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.15)).enhance(bright).convert("RGBA")

_fade = None
def bottom_fade():
    global _fade
    if _fade is None:
        _fade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(_fade)
        for yy in range(1180, H):
            u = min(1, (yy - 1180) / 330); fd.line([(0, yy), (W, yy)], fill=(8, 12, 20, int(185 * u * u * (3 - 2 * u))))
    return _fade

def hook_frame(hero, bgimg, t, title, parts, sub, heroes2=None):
    """Same motion and layout as the race reel hook. parts = list of (text, colour, slanted)."""
    u = min(1.0, t / 1.5); bs = 1 + 0.02 * u
    bw, bh = int(W * bs), int(H * bs)
    bgz = bgimg.resize((bw, bh), Image.BICUBIC); ox = (bw - W) // 2; oy = int((bh - H) / 2 + 18 * u)
    img = bgz.crop((ox, oy, ox + W, oy + H))
    ph = 2 * math.pi * t / 2.4
    sc = 1 + 0.04 * (1 - (1 - min(1.0, t / 2.0)) ** 2)
    ang = 1.0 * math.sin(ph); dx = -4.3 * math.sin(ph); dy = -12 * (1 - math.cos(ph))
    if heroes2:
        # two cards: same zoom / tilt / sway / float, fanned out (left card behind, right card in front)
        for k, (hc, base_ang, bx) in enumerate(((heroes2[0], 6.0, 325), (heroes2[1], -6.0, 755))):
            cw = int(560 * sc); ch = int(cw * hc.height / hc.width)
            card = rounded(hc.resize((cw, ch), Image.LANCZOS), int(26 * sc)).rotate(base_ang + ang * (1 if k else -1), resample=Image.BICUBIC, expand=True)
            cx = bx + dx * (1 if k else -1); cy = 270 + int(560 * hc.height / hc.width) / 2 + dy * (1 if k else 0.7) + (0 if k else 30)
            shadow_paste(img, card, cx - card.width / 2, cy - card.height / 2, blur=24, dy=14, alpha=170)
    else:
        cw = int(900 * sc); ch = int(cw * hero.height / hero.width)
        card = rounded(hero.resize((cw, ch), Image.LANCZOS), int(40 * sc)).rotate(ang, resample=Image.BICUBIC, expand=True)
        cx = W / 2 + dx; cy = 250 + int(900 * hero.height / hero.width) / 2 + dy
        shadow_paste(img, card, cx - card.width / 2, cy - card.height / 2, blur=26, dy=14, alpha=170)
    img.alpha_composite(bottom_fade())
    ttl = fit_text(title, "anton", 1000, 150, WHITE, stroke=2)
    shadow_paste(img, ttl, (W - ttl.width) // 2, 1225, blur=12, dy=6, alpha=230)
    ims = [skew_text(txt, font("anton", 150), col, slant=0.12 if sl else 0, stroke=2) for txt, col, sl in parts]
    tw = sum(i.width for i in ims) + 34 * (len(ims) - 1)
    if tw > 1020: ims = [i.resize((int(i.width * 1020 / tw), int(i.height * 1020 / tw)), Image.LANCZOS) for i in ims]; tw = 1020
    x = (W - tw) / 2; y = 1395; mh = max(i.height for i in ims)
    for im in ims: shadow_paste(img, im, x, y + (mh - im.height) // 2, blur=12, dy=6); x += im.width + 34
    s = fit_text(sub, "anton", 980, 50, GREEN, slant=0.15)
    shadow_paste(img, s, (W - s.width) // 2, 1560, blur=8, dy=3)
    lk = lockup(34); img.alpha_composite(lk, ((W - lk.width) // 2, 1640))
    return img

def pill(d, text, cy, size=27, fill=(6, 60, 44, 235), col=GREEN):
    fpl = font("Bold", size); tw = d.textlength(text, font=fpl); cx = W / 2; h = size + 14
    d.rounded_rectangle((cx - tw / 2 - 22, cy - h / 2, cx + tw / 2 + 22, cy + h / 2), h / 2, fill=fill, outline=col + (255,), width=2)
    d.text((cx - tw / 2, cy - h / 2 + 4 + (size - 27) * 0.1), text, font=fpl, fill=col)

def ctext(d, text, f, y, fill, cx=W / 2):
    d.text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)

def glow(im, col, r=22, strength=2):
    """coloured glow behind an RGBA image"""
    pad = r * 3; g = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    solid = Image.new("RGBA", im.size, col + (255,)); solid.putalpha(im.getchannel("A")); g.alpha_composite(solid, (pad, pad))
    g = g.filter(ImageFilter.GaussianBlur(r))
    if strength > 1:
        a = np.array(g.getchannel("A")).astype(float) * strength; g.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return g, pad

def dim(im, k):
    """darken RGBA image by factor k (1 = unchanged)"""
    a = im.getchannel("A"); rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(k); rgb = ImageEnhance.Color(rgb).enhance(0.4 + 0.6 * k)
    out = rgb.convert("RGBA"); out.putalpha(a); return out

def encode(frames, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for im in frames: p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close(); p.wait(); print("wrote", out)

def clamp01(x): return max(0.0, min(1.0, x))
def eout(x): x = clamp01(x); return 1 - (1 - x) ** 3
