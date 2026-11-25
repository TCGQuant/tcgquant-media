"""Higher or Lower reel: python3 hol.py out.mp4 [--preview]"""
import sys, math
from common import *

ROUNDS = [
    (dict(pid=517045, name="Charizard ex", tag="151 · SIR", price=279.99), dict(pid=610511, name="Sylveon ex", tag="Prismatic Evolutions · SIR", price=374.91)),
    (dict(pid=253266, name="Gengar VMAX", tag="Fusion Strike · Alt Art", price=997.53), dict(pid=284137, name="Giratina V", tag="Lost Origin · Alt Art", price=799.95)),
    (dict(pid=541660, name="Roronoa Zoro", tag="OP-06 · Manga", price=2500.00), dict(pid=246723, name="Umbreon VMAX", tag="Evolving Skies · Alt Art", price=2149.10)),
    (dict(pid=662184, name="Mega Charizard X ex", tag="Phantasmal Flames · SIR", price=510.68), dict(pid=451834, name="Lugia V", tag="Silver Tempest · Alt Art", price=432.62)),
    (dict(pid=587966, name="Nami", tag="PRB-01 · Manga", price=2043.68), dict(pid=610516, name="Umbreon ex", tag="Prismatic Evolutions · SIR", price=1130.37)),
]
HOOK, XF, RD, END = 2.6, 0.35, 4.8, 3.6
CW, CH = 470, 656
CX = (270, 810); CTOP = 430
T_CD0, T_CD1, T_REV, T_WIN = 0.35, 2.6, 2.7, 3.4

class HoL:
    def __init__(s):
        s.hero = card_img(662184, hi=True); s.hbg = hook_bg(s.hero, box=(0.33, 0.20, 0.87, 0.85), focus=(0.5, 0.5), contrast=1.3, color=1.3); s.hero2 = [card_img(517045, hi=True), s.hero]
        s.bg = [dark_bg(card_img(a["pid"]), 0.5) for a, b in ROUNDS]
        s.card = {}
        for a, b in ROUNDS:
            for c in (a, b): s.card[c["pid"]] = rounded(card_img(c["pid"]).resize((CW, CH), Image.LANCZOS), 22)
        s.lock = lockup(60)
        s.endbg = dark_bg(card_img(541660), 0.45)

    def round_frame(s, ri, t):
        a, b = ROUNDS[ri]; img = s.bg[ri].copy(); d = ImageDraw.Draw(img, "RGBA")
        img.alpha_composite(s.lock, ((W - s.lock.width) // 2, 66))
        pill(d, f"ROUND {ri + 1} / {len(ROUNDS)}", 176, 30)
        ttl = skew_text("WHICH IS WORTH MORE?", font("anton", 92), WHITE, stroke=2)
        shadow_paste(img, ttl, (W - ttl.width) // 2, 222, blur=8, dy=4)
        win = 0 if a["price"] >= b["price"] else 1
        enter = eout(t / 0.4)
        for k, c in enumerate((a, b)):
            ph = 2 * math.pi * t / 2.4 + k * math.pi
            dx = -4 * math.sin(ph) + (1 - enter) * (-1 if k == 0 else 1) * 600
            dy = -10 * (1 - math.cos(ph))
            im = s.card[c["pid"]]
            wk = eout((t - T_WIN) / 0.35)
            if k == win and wk > 0:
                g, pad = glow(im, GREEN, 20, 2); g.putalpha(g.getchannel("A").point(lambda v: int(v * wk)))
                img.alpha_composite(g, (int(CX[k] - CW / 2 + dx - pad), int(CTOP + dy - pad)))
            if k != win and wk > 0: im = dim(im, 1 - 0.55 * wk)
            ang = 0.8 * math.sin(ph)
            rim = im.rotate(ang, resample=Image.BICUBIC, expand=True)
            shadow_paste(img, rim, CX[k] + dx - rim.width / 2, CTOP + CH / 2 + dy - rim.height / 2, blur=20, dy=12, alpha=170)
            if k == win and wk > 0:
                bt = "WORTH MORE"; fb = font("ExtraBold", 28); tw = d.textlength(bt, font=fb)
                y0 = CTOP - 26 + (1 - wk) * 20
                d.rounded_rectangle((CX[k] - tw / 2 - 20, y0, CX[k] + tw / 2 + 20, y0 + 44), 22, fill=GREEN + (int(255 * wk),))
                d.text((CX[k] - tw / 2, y0 + 5), bt, font=fb, fill=(6, 30, 22, int(255 * wk)))
            # name + tag
            nm = fit_text(c["name"], "Bold", 500, 38, WHITE)
            shadow_paste(img, nm, CX[k] - nm.width / 2, CTOP + CH + 34, blur=6, dy=3)
            ctext(d, c["tag"], font("Medium", 25), CTOP + CH + 84, MUTED, CX[k])
            # price
            rk = eout((t - T_REV) / 0.7)
            if rk <= 0: txt, col = "$???", (200, 208, 222)
            else:
                txt = money(c["price"] * rk)
                col = WHITE if wk <= 0 else (GREEN if k == win else (150, 156, 170))
            pim = fit_text(txt, "anton", 500, 86, col, slant=0.1 if (k == win and wk > 0) else 0, stroke=2)
            shadow_paste(img, pim, CX[k] - pim.width / 2, CTOP + CH + 130, blur=10, dy=5)
        # centre VS / countdown
        cy = CTOP + CH / 2; r = 64
        d.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), fill=(10, 14, 22, 235), outline=GREEN + (255,), width=4)
        if T_CD0 <= t < T_CD1:
            n = 3 - int((t - T_CD0) / ((T_CD1 - T_CD0) / 3)); lab, f = str(n), font("anton", 76)
        else:
            lab, f = "VS", font("anton", 60)
        bb = d.textbbox((0, 0), lab, font=f); d.text((W / 2 - (bb[2] + bb[0]) / 2, cy - (bb[3] + bb[1]) / 2), lab, font=f, fill=WHITE)
        # timer bar
        y = 1395; k = 1 - clamp01((t - T_CD0) / (T_CD1 - T_CD0))
        d.rounded_rectangle((120, y, W - 120, y + 12), 6, fill=(255, 255, 255, 40))
        if k > 0: d.rounded_rectangle((120, y, 120 + (W - 240) * k, y + 12), 6, fill=BRAND)
        # result line
        if t >= T_WIN:
            wc, lc = (a, b) if win == 0 else (b, a)
            line = f"{wc['name']} wins by {money(wc['price'] - lc['price'])}"
            al = int(255 * eout((t - T_WIN) / 0.3))
            li = fit_text(line, "anton", 960, 62, GREEN, slant=0.15); li.putalpha(li.getchannel("A").point(lambda v: v * al // 255))
            shadow_paste(img, li, (W - li.width) // 2, 1450, blur=8, dy=3, alpha=al * 200 // 255)
        else:
            ctext(d, "Keep score in your head...", font("SemiBold", 32), 1460, (215, 222, 235))
        ctext(d, "TCGQuant.com", font("Bold", 38), 1760, GREEN)
        return img

    def end_frame(s, t):
        img = s.endbg.copy(); d = ImageDraw.Draw(img, "RGBA")
        img.alpha_composite(s.lock, ((W - s.lock.width) // 2, 66))
        ttl = fit_text("HOW MANY DID YOU GET RIGHT?", "anton", 1000, 96, WHITE, stroke=2)
        shadow_paste(img, ttl, (W - ttl.width) // 2, 180, blur=8, dy=4)
        y0 = 360; rh = 250
        for i, (a, b) in enumerate(ROUNDS):
            k = eout((t - 0.12 * i) / 0.4); y = y0 + i * rh + (1 - k) * 40
            al = int(255 * k)
            d.rounded_rectangle((50, y, W - 50, y + rh - 22), 26, fill=(20, 25, 36, int(225 * k)), outline=(255, 255, 255, int(26 * k)), width=2)
            win = a if a["price"] >= b["price"] else b; lose = b if win is a else a
            for j, c in enumerate((win, lose)):
                th = rounded(card_img(c["pid"]).resize((140, 196), Image.LANCZOS), 10)
                if j == 1: th = dim(th, 0.5)
                th.putalpha(th.getchannel("A").point(lambda v: v * al // 255))
                img.alpha_composite(th, (80 + j * 156, int(y + 16)))
            d.text((400, y + 34), f"ROUND {i + 1}", font=font("Bold", 26), fill=MUTED + (al,))
            d.text((400, y + 70), win["name"], font=font("Bold", 40), fill=WHITE + (al,))
            d.text((400, y + 126), f"{money(win['price'])}  vs  {money(lose['price'])}", font=font("SemiBold", 32), fill=GREEN + (al,))
        if t > 1.0: pill(d, "Comment your score below!", 1648, 34)
        ctext(d, "TCGQuant.com", font("Bold", 38), 1760, GREEN)
        return img

    def hook(s, t):
        return hook_frame(s.hero, s.hbg, t, "HIGHER OR LOWER?", [("CAN YOU GO", WHITE, False), ("5 FOR 5?", GREEN, True)], "Guess which card is worth more", heroes2=s.hero2)

    def frames(s):
        total = HOOK + RD * len(ROUNDS) + END
        for fi in range(int(total * FPS)):
            t = fi / FPS
            if t < HOOK: im = s.hook(t)
            else:
                u = t - HOOK; ri = int(u // RD)
                im = s.round_frame(ri, u - ri * RD) if ri < len(ROUNDS) else s.end_frame(u - RD * len(ROUNDS))
                if u < XF: im = Image.blend(s.hook(t).convert("RGB"), im.convert("RGB"), u / XF)
                elif ri >= 1 and (u - ri * RD) < 0.25:
                    prev = s.round_frame(ri - 1, RD) if ri - 1 < len(ROUNDS) else None
                    im = Image.blend(prev.convert("RGB"), im.convert("RGB"), (u - ri * RD) / 0.25)
            yield im

if __name__ == "__main__":
    out = sys.argv[1]; R = HoL()
    if "--preview" in sys.argv:
        b = out.rsplit(".", 1)[0]
        R.hook(2.5).convert("RGB").save(b + "_hook.jpg", quality=88)
        for t in (1.2, 3.0, 4.5): R.round_frame(2, t).convert("RGB").save(b + f"_r{t}.jpg", quality=88)
        R.end_frame(3).convert("RGB").save(b + "_end.jpg", quality=88)
    else: encode(R.frames(), out)
