"""Builds a PSA 10 slab image from Grayson's own OP-11 Luffy slab photo:
swaps in the given Pokemon card and rewrites the label text; keeps his barcode, PSA logo and cert number (his OK, Nov 25)."""
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

SRC = "/home/claude/newreels/slab/src.png"
CROP = (0, 275, 1170, 2256)              # slab in the screenshot
CARD = (122, 825 - 275, 1034, 2100 - 275)  # card window inside the crop
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
INK = (38, 38, 44)

_base = None
def base():
    global _base
    if _base is None: _base = Image.open(SRC).convert("RGB").crop(CROP)
    return _base

def _label_font():
    # match the original label: "2025 ONE PIECE OP11 EN" spans ~565px
    for sz in range(30, 70):
        if ImageFont.truetype(FONT, sz).getlength("2025 ONE PIECE OP11 EN") >= 565: return sz
    return 46

def build(card_img, line1, line2, line3, num, seed=0):
    im = base().copy()
    # --- card ---
    x0, y0, x1, y1 = CARD; w, h = x1 - x0, y1 - y0
    card = card_img.convert("RGB").resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.7))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=255)
    im.paste(card, (x0, y0), m)
    # --- label ---
    d = ImageDraw.Draw(im)
    ly = 399 - 275  # label top inside crop
    a = np.array(im); bg = tuple(int(v) for v in np.median(a[ly + 5:ly + 15, 600:700].reshape(-1, 3), axis=0))
    lx0, lx1, ly1 = 116, 1057, 622 - 275                           # whole white label except the PSA logo tab
    d.rectangle((lx0, ly + 1, lx1, 566 - 275), fill=bg)            # text lines only: barcode, PSA logo and cert stay original
    sz = _label_font(); f = ImageFont.truetype(FONT, sz)
    L, R = 142, 1040; ys = [ly + 22, ly + 72, ly + 122]
    def left(t, y, maxw=None):
        maxw = maxw or int(R - f.getlength("#" + num) - 40 - L)
        if not t: return
        tw = f.getlength(t)
        if tw <= maxw: d.text((L, y), t, font=f, fill=INK); return
        tmp = Image.new("RGBA", (int(tw) + 4, sz + 16), bg + (0,)); ImageDraw.Draw(tmp).text((0, 0), t, font=f, fill=INK + (255,))
        tmp = tmp.resize((maxw, tmp.height), Image.LANCZOS); im.paste(tmp, (L, y), tmp)
    def right(t, y): d.text((R - f.getlength(t), y), t, font=f, fill=INK)
    left(line1, ys[0]); left(line2, ys[1]); left(line3, ys[2])
    right("#" + num, ys[0]); right("GEM MT", ys[1]); right("10", ys[2])
    # soften the redrawn label to match the photo's softness
    lab = im.crop((120, ly, 1060, 566 - 275)).filter(ImageFilter.GaussianBlur(0.8)); im.paste(lab, (120, ly))
    out = im.convert("RGBA")
    mk = Image.new("L", im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 26, fill=255); out.putalpha(mk)
    return out

if __name__ == "__main__":
    c = Image.open("/home/claude/newreels/cards/94683_hi.jpg")
    s = build(c, "2014 POKEMON XY PHANTOM FORCES", "FA/GENGAR EX", "", "114", 1)
    s.save("/tmp/gengar_slab.png"); s.convert("RGB").resize((585, 990)).save("/tmp/gs.jpg")
