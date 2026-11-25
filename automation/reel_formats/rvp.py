"""Raw vs PSA 10 reel: python3 rvp.py out.mp4 [--preview]"""
import sys, math
from common import *

CARDS_ = [
    dict(pid=642553, name="Volcarona", tag="Black Bolt · 100/086", era="SV", year="2025", sl1="POKEMON SV BLACK BOLT", sl2="VOLCARONA #100", raw=47.57, psa=2125.00, g10=21, tot=551),
    dict(pid=157675, name="Giratina Prism Star", tag="Ultra Prism · 58/156", era="SM", year="2018", sl1="POKEMON SM ULTRA PRISM", sl2="GIRATINA PRISM STAR #58", raw=88.55, psa=4124.99, g10=103, tot=615),
    dict(pid=124026, name="Charizard", tag="Evolutions · 11/108", era="XY", year="2016", sl1="POKEMON XY EVOLUTIONS", sl2="CHARIZARD HOLO #11", raw=91.30, psa=6856.00, g10=600, tot=54233),
    dict(pid=91238, name="Charizard EX (Full Art)", tag="Flashfire · 100/106", era="XY", year="2014", sl1="POKEMON XY FLASHFIRE", sl2="CHARIZARD EX FULL ART #100", raw=298.20, psa=25650.00, g10=184, tot=4343),
    dict(pid=94683, name="Gengar EX (Full Art)", tag="Phantom Forces · 114/119", era="XY", year="2014", sl1="POKEMON XY PHANTOM FORCES", sl2="GENGAR EX FULL ART #114", raw=828.92, psa=73857.78, g10=86, tot=6134),
]
HOOK, XF, SEG, FIN, END = 2.6, 0.35, 4.4, 6.4, 3.8
CWID, CHT = 404, 564
SW = 460; LAB = 112; STOP = 420
SH = 16 + LAB + 14 + CHT + 20
RX, SX = 275, 805
CARD_TOP = STOP + 16 + LAB + 14

def big(v): return f"${v:,.0f}" if v >= 1000 else f"${v:,.2f}"

def make_slab(c, card):
    im = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, SW - 1, SH - 1), 14, fill=(228, 233, 240, 185), outline=(250, 252, 255, 235), width=4)
    d.rounded_rectangle((7, 7, SW - 8, SH - 8), 10, outline=(255, 255, 255, 80), width=2)
    # PSA-style label: white label, red frame, black text (plain "PSA" text, not their logo artwork)
    RED_ = (200, 30, 42); INK = (18, 18, 20)
    d.rectangle((14, 14, SW - 15, 16 + LAB), fill=(246, 246, 246, 255))
    d.rectangle((20, 20, SW - 21, 10 + LAB), outline=RED_ + (255,), width=5)
    def fit(txt, kind, sz, maxw):
        while d.textlength(txt, font=font(kind, sz)) > maxw and sz > 11: sz -= 1
        return font(kind, sz)
    L = 34; R_ = SW - 34
    l1 = f"{c['year']} {c['sl1']}"; f1 = fit(l1, "Bold", 18, SW - 170); d.text((L, 30), l1, font=f1, fill=INK)
    nm, num = c["sl2"].rsplit(" #", 1)
    f2 = fit(nm, "Bold", 18, SW - 200); d.text((L, 54), nm, font=f2, fill=INK)
    fn = font("Bold", 18); t = "#" + num; d.text((R_ - d.textlength(t, font=fn), 30), t, font=fn, fill=INK)
    fg = font("ExtraBold", 21); t = "GEM MT 10"; d.text((R_ - d.textlength(t, font=fg), 54), t, font=fg, fill=INK)
    fp = font("ExtraBold", 22); d.text((R_ - d.textlength("PSA", font=fp), 82), "PSA", font=fp, fill=RED_)
    # barcode-style stripes (no cert number)
    import random; rnd = random.Random(c["pid"]); x = L
    while x < L + 190:
        w_ = rnd.choice((1, 1, 2, 3)); d.rectangle((x, 84, x + w_ - 1, 102), fill=INK); x += w_ + rnd.choice((1, 2, 2, 3))
    # card well
    wx, wy = (SW - CWID) // 2, 16 + LAB + 14
    d.rounded_rectangle((wx - 7, wy - 7, wx + CWID + 6, wy + CHT + 6), 8, fill=(240, 243, 248, 200), outline=(255, 255, 255, 160), width=2)
    im.alpha_composite(card, (wx, wy))
    # glare stripe
    gl = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.polygon([(SW * 0.55, 0), (SW * 0.78, 0), (SW * 0.30, SH), (SW * 0.07, SH)], fill=(255, 255, 255, 34))
    gl = gl.filter(ImageFilter.GaussianBlur(14))
    m = Image.new("L", (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, SW - 1, SH - 1), 22, fill=255)
    gl.putalpha(Image.fromarray(np.minimum(np.array(gl.getchannel("A")), np.array(m))))
    im.alpha_composite(gl)
    return im

class RVP:
    def __init__(s):
        s.hero = card_img(94683, hi=True); s.hbg = hook_bg(s.hero)
        s.card = {c["pid"]: rounded(card_img(c["pid"]).resize((CWID, CHT), Image.LANCZOS), 18) for c in CARDS_}
        s.slab = {c["pid"]: make_slab(c, s.card[c["pid"]]) for c in CARDS_}
        s.bg = {c["pid"]: dark_bg(card_img(c["pid"]), 0.5) for c in CARDS_}
        s.lock = lockup(60)

    def seg_frame(s, i, t):
        c = CARDS_[i]; fin = i == len(CARDS_) - 1; p = c["pid"]
        sl0, sl1, cn0, cn1, mx, st = (1.0, 1.5, 1.6, 3.6, 3.8, 4.15) if fin else (0.7, 1.15, 1.2, 2.3, 2.4, 2.7)
        img = s.bg[p].copy(); d = ImageDraw.Draw(img, "RGBA")
        img.alpha_composite(s.lock, ((W - s.lock.width) // 2, 66))
        pill(d, "THE BIG REVEAL" if fin else f"CARD {i + 1} / {len(CARDS_)}", 176, 30,
             fill=(70, 14, 14, 235) if fin else (6, 60, 44, 235), col=(255, 120, 120) if fin else GREEN)
        ttl = skew_text("RAW vs PSA 10", font("anton", 100), WHITE, stroke=2)
        shadow_paste(img, ttl, (W - ttl.width) // 2, 216, blur=8, dy=4)
        ph = 2 * math.pi * t / 2.4
        # raw card
        e = eout(t / 0.4); dx = -4 * math.sin(ph) - (1 - e) * 600; dy = -9 * (1 - math.cos(ph))
        rc = s.card[p].rotate(0.8 * math.sin(ph), resample=Image.BICUBIC, expand=True)
        shadow_paste(img, rc, RX + dx - rc.width / 2, CARD_TOP + CHT / 2 + dy - rc.height / 2, blur=20, dy=12, alpha=170)
        fb = font("ExtraBold", 28); tw = d.textlength("RAW", font=fb)
        d.rounded_rectangle((RX - tw / 2 - 20, CARD_TOP - 64, RX + tw / 2 + 20, CARD_TOP - 22), 21, fill=(235, 240, 248, 255))
        d.text((RX - tw / 2, CARD_TOP - 60), "RAW", font=fb, fill=(14, 20, 32))
        # slab
        k = eout((t - sl0) / (sl1 - sl0))
        if k > 0:
            sx = SX + 4 * math.sin(ph + math.pi) + (1 - k) * 650; sy = STOP - 9 * (1 - math.cos(ph + math.pi))
            sim = s.slab[p]
            if t > cn1:
                g, pad = glow(sim, GREEN, 22, 1.6); a = eout((t - cn1) / 0.4)
                g.putalpha(g.getchannel("A").point(lambda v: int(v * a))); img.alpha_composite(g, (int(sx - SW / 2 - pad), int(sy - pad)))
            rs = sim.rotate(0.8 * math.sin(ph + math.pi), resample=Image.BICUBIC, expand=True)
            shadow_paste(img, rs, sx - rs.width / 2, sy + SH / 2 - rs.height / 2, blur=22, dy=14, alpha=170)
        else:
            d.rounded_rectangle((SX - SW / 2, STOP, SX + SW / 2, STOP + SH), 22, outline=(255, 255, 255, 255), width=3)
            q = skew_text("?", font("anton", 220), (235, 240, 248)); shadow_paste(img, q, SX - q.width / 2, STOP + SH / 2 - q.height / 2, blur=10)
        # name
        nm = fit_text(c["name"], "Bold", 1000, 46, WHITE); shadow_paste(img, nm, (W - nm.width) // 2, 1180, blur=6, dy=3)
        ctext(d, c["tag"], font("Medium", 29), 1240, (200, 208, 222))
        # prices
        y = 1292
        rp = fit_text(money(c["raw"]), "anton", 470, 84, WHITE, stroke=2); ra = int(255 * eout((t - 0.3) / 0.3))
        rp.putalpha(rp.getchannel("A").point(lambda v: v * ra // 255)); shadow_paste(img, rp, RX - rp.width / 2, y, blur=10, dy=5, alpha=ra * 200 // 255)
        ar = skew_text("→", font("anton", 80), GREEN); img.alpha_composite(ar, (W // 2 - ar.width // 2, y + 8))
        kk = clamp01((t - cn0) / (cn1 - cn0)); kk = 1 - (1 - kk) ** (4 if fin else 3)
        ptxt = "$???" if t < cn0 else big(c["psa"] * kk)
        pp = fit_text(ptxt, "anton", 470, 84, GREEN if t >= cn0 else (200, 208, 222), slant=0.1, stroke=2)
        shadow_paste(img, pp, SX - pp.width / 2, y, blur=10, dy=5)
        # multiplier
        if t >= mx:
            u = eout((t - mx) / 0.3); sc = 1.25 - 0.25 * u
            mult = c["psa"] / c["raw"]
            parts = [skew_text("PSA 10 = ", font("anton", 104), WHITE, stroke=2), skew_text(f"{mult:.0f}x", font("anton", 104), GREEN, slant=0.15, stroke=2),
                     skew_text(" RAW", font("anton", 104), WHITE, stroke=2)]
            tw = sum(q.width for q in parts) + 12; hh = max(q.height for q in parts)
            row = Image.new("RGBA", (tw, hh), (0, 0, 0, 0)); x = 0
            for q in parts: row.alpha_composite(q, (x, hh - q.height)); x += q.width + 6
            row = row.resize((int(row.width * sc), int(row.height * sc)), Image.LANCZOS)
            if row.width > 1000: row = row.resize((1000, int(row.height * 1000 / row.width)), Image.LANCZOS)
            row.putalpha(row.getchannel("A").point(lambda v: int(v * u)))
            shadow_paste(img, row, (W - row.width) // 2, 1450 - (row.height - hh) // 2, blur=10, dy=5, alpha=int(200 * u))
        if t >= st:
            a = int(255 * eout((t - st) / 0.3))
            line = f"Only {c['g10']:,} PSA 10s out of {c['tot']:,} graded ({c['g10'] / c['tot'] * 100:.1f}%)"
            ctext(d, line, font("SemiBold", 32), 1610, (225, 231, 242, a))
        ctext(d, "TCGQuant.com", font("Bold", 38), 1760, GREEN)
        return img

    def end_frame(s, t):
        img = s.bg[94683].copy(); d = ImageDraw.Draw(img, "RGBA")
        img.alpha_composite(s.lock, ((W - s.lock.width) // 2, 66))
        ttl = fit_text("RAW vs PSA 10", "anton", 1000, 100, WHITE, stroke=2); shadow_paste(img, ttl, (W - ttl.width) // 2, 176, blur=8, dy=4)
        y0, rh = 350, 250
        for i, c in enumerate(CARDS_):
            k = eout((t - 0.12 * i) / 0.4); y = y0 + i * rh + (1 - k) * 40; al = int(255 * k)
            d.rounded_rectangle((50, y, W - 50, y + rh - 22), 26, fill=(20, 25, 36, int(225 * k)), outline=(255, 255, 255, int(26 * k)), width=2)
            th = rounded(card_img(c["pid"]).resize((140, 196), Image.LANCZOS), 10); th.putalpha(th.getchannel("A").point(lambda v: v * al // 255))
            img.alpha_composite(th, (80, int(y + 16)))
            d.text((250, y + 30), c["name"], font=font("Bold", 36), fill=WHITE + (al,))
            d.text((250, y + 78), f"{c['era']} · {c['tag']}", font=font("Medium", 24), fill=MUTED + (al,))
            d.text((250, y + 124), f"{money(c['raw'])}  →  {big(c['psa'])}", font=font("SemiBold", 32), fill=GREEN + (al,))
            mt = f"{c['psa'] / c['raw']:.0f}x"; fm = font("anton", 72)
            d.text((W - 80 - d.textlength(mt, font=fm), y + 60), mt, font=fm, fill=GREEN + (al,))
        if t > 1.0: pill(d, "Would you grade any of these?", 1648, 34)
        ctext(d, "TCGQuant.com", font("Bold", 38), 1760, GREEN)
        return img

    def hook(s, t):
        return hook_frame(s.hero, s.hbg, t, "RAW vs PSA 10", [(f"${round(CARDS_[-1]['raw']):,}", WHITE, False), ("→", GREEN, False), (big(CARDS_[-1]["psa"]), GREEN, True)], "Wait for the last one...")

    def frames(s):
        durs = [SEG] * (len(CARDS_) - 1) + [FIN]; starts = np.cumsum([0] + durs)
        total = HOOK + starts[-1] + END
        def at(u):
            if u >= starts[-1]: return s.end_frame(u - starts[-1])
            i = int(np.searchsorted(starts, u, side="right") - 1); return s.seg_frame(i, u - starts[i])
        for fi in range(int(total * FPS)):
            t = fi / FPS
            if t < HOOK: im = s.hook(t)
            else:
                u = t - HOOK; im = at(u)
                if u < XF: im = Image.blend(s.hook(t).convert("RGB"), im.convert("RGB"), u / XF)
                else:
                    for b in starts[1:]:
                        if b <= u < b + 0.25:
                            im = Image.blend(at(b - 1e-3).convert("RGB"), im.convert("RGB"), (u - b) / 0.25)
            yield im

if __name__ == "__main__":
    out = sys.argv[1]; R = RVP()
    if "--preview" in sys.argv:
        b = out.rsplit(".", 1)[0]
        R.hook(2.5).convert("RGB").save(b + "_hook.jpg", quality=88)
        R.seg_frame(2, 0.9).convert("RGB").save(b + "_s0.9.jpg", quality=88)
        R.seg_frame(2, 4.0).convert("RGB").save(b + "_s4.jpg", quality=88)
        R.seg_frame(4, 6.0).convert("RGB").save(b + "_fin.jpg", quality=88)
        R.end_frame(3).convert("RGB").save(b + "_end.jpg", quality=88)
    else: encode(R.frames(), out)
