"""Box cutout v5: background = near-pure white connected to the border (box white print kept).
Per-image PATCH polygons force product in, CLIP polygons force background (shadows)."""
import os, numpy as np, cv2
from PIL import Image
TH = {}        # per-image bg threshold override
PATCH = {      # source-coord polygons forced into product (pale art that touches the white background)
    "501257": [[(262, 229), (1100, 227), (1100, 470), (262, 470)],          # lid rectangle
               [(990, 440), (1099, 440), (1082, 1325), (990, 1325)]],     # right side panel
    "476452": [[(1060, 940), (1101, 940), (1099, 1040), (1060, 1040)]],    # right side panel
    "610931": [[(1000, 690), (1078, 690), (1073, 812), (1000, 812)]],      # right pack edge
    "512821": [[(505, 324), (662, 324), (662, 420), (505, 420)]],          # lid top-left corner
}
CLIP = {}      # source-coord polygons forced to background
LAST = {}
KS = 5
TIGHT = 238
WIDE = 9      # white areas narrower than this are edge halo, wider ones are real white print
WIN = 25      # median window (px) for straightening the bottom and side outlines
BAND = 30
def mask(path, th=250, chroma=14):
    name = os.path.splitext(os.path.basename(path))[0]; th = TH.get(name, th)
    im0 = Image.open(path).convert("RGB"); P = 12
    im = Image.new("RGB", (im0.width + 2 * P, im0.height + 2 * P), (255, 255, 255)); im.paste(im0, (P, P))
    a = np.array(im).astype(np.int16); h, w = a.shape[:2]
    mn = a.min(2); ch = a.max(2) - mn
    def flood(t):
        white = ((mn >= t) & (ch <= chroma)).astype(np.uint8)
        n, lab = cv2.connectedComponents(white, connectivity=4)
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
        return (~np.isin(lab, list(border))).astype(np.uint8) * 255
    tight = flood(TIGHT)            # coloured print, edge halo excluded
    loose = flood(th)               # also takes the box's white print (base strip, gussets, rims)
    extra = loose & ~cv2.dilate(tight, np.ones((7, 7), np.uint8))
    extra = cv2.morphologyEx(extra, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (WIDE, WIDE)))
    extra = cv2.dilate(extra, np.ones((9, 9), np.uint8)) & loose   # reconnect wide white areas to the print
    m = tight | extra
    for poly in PATCH.get(name, []): cv2.fillPoly(m, [np.array(poly, np.int32) + P], 255)
    for poly in CLIP.get(name, []): cv2.fillPoly(m, [np.array(poly, np.int32) + P], 0)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (KS, KS))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)      # knock off JPEG-noise spikes along white edges
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)     # and fill the notches between them
    nn, ll, st, _ = cv2.connectedComponentsWithStats(m)
    m = np.where(ll == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    ff = m.copy(); cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255); m = m | (255 - ff)
    m = straighten(m)
    return a, m, P
def _med(v, win):
    from scipy.ndimage import median_filter
    return median_filter(v, size=win, mode="nearest")
def _fit(v):
    """Piecewise-straight version of a profile: split at steps, fit 1 or 2 lines per run,
    keep the median value wherever the fit strays > 5px (not actually straight there)."""
    v = np.asarray(v, float); out = v.copy(); n = len(v)
    cuts = [0] + [i + 1 for i in range(n - 1) if abs(v[i + 1] - v[i]) > 6] + [n]
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b - a < 15: continue
        t = np.arange(a, b); y = v[a:b]
        def line(tt, yy):
            k = np.polyfit(tt, yy, 1); return np.polyval(k, tt)
        f1 = line(t, y); e1 = np.abs(f1 - y).mean(); best = f1
        if e1 > 0.8 and b - a >= 40:
            be = None
            for j in range(a + 15, b - 15, 3):
                f = np.r_[line(t[:j - a], y[:j - a]), line(t[j - a:], y[j - a:])]
                e = np.abs(f - y).mean()
                if be is None or e < be: be, bf = e, f
            if be is not None and be < 0.6 * e1: best = bf
        good = np.abs(best - y) <= 5
        out[a:b] = np.where(good, best, y)
    return out
def straighten(m):
    """The box's bottom and side outlines are straight; the white base strip makes them noisy.
    Median-filter the outline profiles (keeps steps and long edges, drops JPEG-noise spikes)."""
    h, w = m.shape; on = m > 0
    rows = np.where(on.any(1))[0]; cols = np.where(on.any(0))[0]
    y0, y1 = rows[0], rows[-1]; ybody = int(y0 + 0.35 * (y1 - y0))
    out = m.copy()
    # bottom profile
    yb = np.full(w, -1); idx = np.arange(h)[:, None]
    yb_raw = np.where(on.any(0), (on * idx).max(0), -1)
    c0, c1 = cols[0], cols[-1]
    prof = _fit(_med(yb_raw[c0:c1 + 1].astype(float), WIN))
    for i, x in enumerate(range(c0, c1 + 1)):
        yb = int(round(prof[i]))
        if yb < ybody: continue
        out[yb + 1:, x] = 0; out[max(ybody, yb - BAND):yb + 1, x] = 255
    # side profiles, body rows only
    for side in (0, 1):
        xs = np.array([ (np.where(out[y] > 0)[0][0] if side == 0 else np.where(out[y] > 0)[0][-1]) if out[y].any() else -1 for y in range(h)])
        ys = np.arange(ybody, y1 + 1); ys = ys[xs[ys] >= 0]
        if not len(ys): continue
        pr = _fit(_med(xs[ys].astype(float), WIN))
        for y, xv in zip(ys, pr):
            xv = int(round(xv))
            if side == 0: out[y, :xv] = 0; out[y, xv:xv + BAND] = 255
            else: out[y, xv + 1:] = 0; out[y, max(0, xv - BAND):xv + 1] = 255
    return out
def cutout(path, ss=4, cache=True):
    name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(os.path.dirname(path), f"{name}_cut5.png")
    if cache and os.path.exists(out_path) and os.path.getmtime(out_path) > max(os.path.getmtime(path), os.path.getmtime(__file__)):
        return Image.open(out_path).convert("RGBA")
    a, m, P = mask(path); h, w = m.shape
    f = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.0)
    big = (cv2.resize(f, (w * ss, h * ss), interpolation=cv2.INTER_CUBIC) > 0.5).astype(np.float32)
    alpha = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
    LAST["alpha"] = alpha[P:-P, P:-P]
    out = np.dstack([a.astype(np.uint8), (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
    res = Image.fromarray(out, "RGBA"); res = res.crop(res.getbbox())
    if cache: res.save(out_path)
    return res
