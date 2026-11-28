"""Product cutouts v4 (white-background product photos).
- background = near-white connected to the image border (flood fill)
- AI matte (rembg isnet) restores pale artwork the flood fill ate, but AI pixels that are pale/grey
  (floor shadows and reflections under the box) are rejected
- largest object kept, holes filled, optional manual patch polygons per image
- edge: hard mask smoothed at 4x, then a colour-based alpha on the outer 3px band removes the white halo,
  and edge colours are un-mixed from white."""
import os, numpy as np, cv2
from PIL import Image

_sess = None
def _ai_alpha(im):
    global _sess
    from rembg import new_session, remove
    if _sess is None: _sess = new_session("isnet-general-use")
    return np.array(remove(im, session=_sess, only_mask=True).convert("L"))

LAST = {}
KEEP = {"493975": [[(900, 841), (1043, 841), (1043, 1000), (900, 1000)]]}   # protect from the white-pocket drop (tray rim is white print)
PATCH = {
    "501257": [[(262, 229), (1100, 227), (1100, 470), (262, 470)],          # lid rectangle (pale lightning art)
               [(990, 440), (1099, 440), (1082, 1325), (990, 1325)],      # right side panel (pale art)
               [(17, 1300), (72, 1300), (72, 1363), (17, 1355)]],         # tray bottom-left corner (glare)
    "476452": [[(1060, 940), (1101, 940), (1099, 1040), (1060, 1040)]],    # right side panel (pale art)
    "610931": [[(1000, 690), (1078, 690), (1073, 812), (1000, 812)]],      # right pack edge (pale art)
    "512821": [[(505, 324), (662, 324), (662, 420), (505, 420)]],          # lid top-left corner (pale art)
}
BOX = False
STRAIGHT = False   # display boxes: body and lid panel are convex, so fill pale-art bites along their straight edges

def straighten_sides(m, mn, tol=3):
    """Box body sides are straight lines. Fit each side on the rows where it sits at its outer edge and
    fill rows where pale art next to the background was bitten out."""
    ys = np.nonzero(m.any(1))[0]
    L = np.full(m.shape[0], -1); R = np.full(m.shape[0], -1)
    for y in ys:
        xs = np.nonzero(m[y])[0]; L[y] = xs.min(); R[y] = xs.max()
    width = R - L
    full = width[ys].max()
    body = ys[width[ys] >= 0.85 * full]
    if len(body) < 50: return m
    body = body[(body >= body.min()) & (body <= body.max())]
    out = m.copy()
    for side, sign in ((L, 1), (R, -1)):
        yb = body; xb = side[yb].astype(float)
        # robust line fit: iterate, keeping rows on the outer side of the current fit
        keep = np.ones(len(yb), bool)
        for _ in range(4):
            a, b = np.polyfit(yb[keep], xb[keep], 1)
            resid = (xb - (a * yb + b)) * sign   # >0 means bitten inward
            keep = resid <= np.percentile(resid, 60)
        fit = a * yb + b
        resid = (xb - fit) * sign
        bit = (resid > tol) & (resid < 0.25 * full)
        # only fill bites enclosed above and below by straight edge (corners at the body ends are real shape)
        i = 0; n = len(yb); margin = max(3, int(0.04 * n))
        while i < n:
            if not bit[i]: i += 1; continue
            j = i
            while j < n and bit[j]: j += 1
            if i > margin and j < n - margin and (j - i) < 0.2 * n:
                for k in range(i, j):
                    y = yb[k]; x0, x1 = sorted((int(round(fit[k])), int(xb[k])))
                    seg = mn[y, x0:x1 + 1] <= 250
                    out[y, x0:x1 + 1][seg] = 255
            i = j
    return out

def box_hulls(m):
    ys, xs = np.nonzero(m); y0, y1 = ys.min(), ys.max(); H = y1 - y0 + 1
    rows = np.arange(y0, y1 + 1)
    width = np.array([(np.nonzero(m[y])[0].max() - np.nonzero(m[y])[0].min()) if m[y].any() else 0 for y in rows])
    full = width.max()
    # body starts where the silhouette reaches (nearly) its full width
    body_top = rows[np.argmax(width >= 0.9 * full)]
    out = m.copy()
    pts = np.column_stack(np.nonzero(m[body_top:]))[:, ::-1] + [0, body_top]
    cv2.fillConvexPoly(out, cv2.convexHull(pts.astype(np.int32)), 255)
    # lid panel: rows above the body whose width is close to the lid's typical width
    upper = width[: body_top - y0]
    if len(upper) > 20:
        lid_w = np.median(upper[len(upper) // 2:])
        lid_rows = rows[: body_top - y0][upper >= 0.85 * lid_w]
        if len(lid_rows) > 10:
            lt = lid_rows.min()
            pts = np.column_stack(np.nonzero(m[lt:body_top]))[:, ::-1] + [0, lt]
            cv2.fillConvexPoly(out, cv2.convexHull(pts.astype(np.int32)), 255)
    return out   # name -> list of polygons (image coords, before padding) to force into the product

def cutout(path, thr=236, chroma=14, ss=4, cache=True):
    name = os.path.basename(path).split(".")[0]
    out_path = os.path.splitext(path)[0] + "_cut4.png"
    if cache and os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(__file__): return Image.open(out_path)
    im0 = Image.open(path).convert("RGB"); P0 = 12
    im = Image.new("RGB", (im0.width + 2 * P0, im0.height + 2 * P0), (255, 255, 255)); im.paste(im0, (P0, P0))
    a = np.array(im).astype(np.int16); h, w = a.shape[:2]
    mn = a.min(2); ch = a.max(2) - mn
    white = ((mn >= thr) & (ch <= chroma)).astype(np.uint8)
    n, lab = cv2.connectedComponents(white, connectivity=4)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    fg = ~bg
    ai = _ai_alpha(im) > 160
    pale = (mn >= 200) & (ch <= 22)
    m = (fg | (ai & ~pale)).astype(np.uint8) * 255
    for poly in PATCH.get(name, []):
        cv2.fillPoly(m, [np.array(poly, np.int32) + P0], 255)
    # drop near-white pockets that sit on the silhouette edge behind a faint line (e.g. the wedge where the body meets the tray)
    keep = np.zeros_like(m)
    for poly in PATCH.get(name, []) + KEEP.get(name, []):
        cv2.fillPoly(keep, [np.array(poly, np.int32) + P0], 255)
    wht = ((mn >= 244) & (ch <= 12) & (m > 0) & (keep == 0)).astype(np.uint8)
    ext = cv2.dilate((m == 0).astype(np.uint8), np.ones((7, 7), np.uint8))
    nw, lw, sw, _ = cv2.connectedComponentsWithStats(wht, connectivity=8)
    touch = np.unique(lw[(ext > 0) & (wht > 0)])
    drop = np.isin(lw, [t for t in touch if t and sw[t, 4] >= 15])
    LAST["drop"] = drop[P0:-P0, P0:-P0]
    m[drop] = 0
    k3 = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k3, iterations=2)
    nn, ll, st, _ = cv2.connectedComponentsWithStats(m)
    m = np.where(ll == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    ff = m.copy(); cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255); m = m | (255 - ff)
    if BOX: m = box_hulls(m)
    if STRAIGHT: m = straighten_sides(m, mn)
    # smooth the silhouette: blur, upsample, threshold, area-downsample
    f = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2)
    big = (cv2.resize(f, (w * ss, h * ss), interpolation=cv2.INTER_CUBIC) > 0.5).astype(np.float32)
    alpha = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
    # colour alpha on the outer band: pale pixels next to the background are mostly background
    inside = (alpha > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(inside, cv2.DIST_L2, 3)
    band = (dist > 0) & (dist <= 3.0)
    ca = np.clip((255 - mn.astype(np.float32)) / 45.0, 0, 1)
    alpha = np.where(band, np.minimum(alpha, np.maximum(ca, (dist - 1) / 2.0)), alpha)
    rgb = a.astype(np.float32); al = alpha[..., None]
    edge = (alpha > 0.02) & (alpha < 0.98)
    dec = np.clip((rgb - 255 * (1 - al)) / np.maximum(al, 0.05), 0, 255)
    rgb[edge] = dec[edge]
    out = np.dstack([rgb.astype(np.uint8), (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
    LAST["alpha"] = alpha[P0:-P0, P0:-P0]
    res = Image.fromarray(out, "RGBA"); res = res.crop(res.getbbox())
    if cache: res.save(out_path)
    return res
