"""Clean product cutouts for white-background product photos.
1. background = near-white connected to the image border (flood fill)
2. AI matte (rembg isnet) restores any light artwork the flood fill ate (e.g. pale lid art)
3. union -> largest object -> holes filled
4. edges: 1px trim of the white fringe, then the mask is smoothed and re-thresholded at 4x
   and area-downsampled, giving clean anti-aliased edges instead of stair-steps
5. edge colour decontamination: semi-transparent edge pixels have the white bleed removed
Results are cached as PNG next to the source."""
import os, numpy as np, cv2
from PIL import Image

_sess = None
def _ai_alpha(im):
    global _sess
    from rembg import new_session, remove
    if _sess is None: _sess = new_session("isnet-general-use")
    return np.array(remove(im, session=_sess, only_mask=True).convert("L"))

def repair_lid(m):
    """Open booster boxes: the raised lid is a straight-sided panel. Pale lid art touching the white
    background can get eaten; rebuild the lid from its straight left/right/top edges."""
    ys, xs = np.nonzero(m); y0, y1 = ys.min(), ys.max(); H = y1 - y0
    rows = range(y0, y0 + int(H * 0.5))
    L = {}; R = {}
    for y in rows:
        r = np.nonzero(m[y])[0]
        if len(r): L[y] = r.min(); R[y] = r.max()
    top = [y for y in L][: max(5, int(H * 0.25))]
    lid_w = np.median([R[y] - L[y] for y in top[len(top)//3:]])
    lid_rows = [y for y in L if (R[y] - L[y]) <= lid_w * 1.08]
    if len(lid_rows) < H * 0.15: return m
    ycut = max(lid_rows)
    fit_rows = [y for y in lid_rows if y > y0 + (ycut - y0) * 0.55]
    if len(fit_rows) < 10: return m
    fy = np.array(fit_rows)
    pl = np.polyfit(fy, [L[y] for y in fy], 1); pr = np.polyfit(fy, [R[y] for y in fy], 1)
    # top edge from the columns in the right half of the lid (the left corner is the one that gets eaten)
    xm = (np.polyval(pl, ycut) + np.polyval(pr, ycut)) / 2
    cols = [x for x in range(int(xm), int(np.polyval(pr, y0 + 5)) - 10) if m[:, x].any()]
    tops = [np.nonzero(m[:, x])[0].min() for x in cols]
    if len(cols) < 10: return m
    pt = np.polyfit(cols, tops, 1)
    poly = np.array([[np.polyval(pl, np.polyval(pt, np.polyval(pl, y0))), np.polyval(pt, np.polyval(pl, y0))],
                     [np.polyval(pr, np.polyval(pt, np.polyval(pr, y0))), np.polyval(pt, np.polyval(pr, y0))],
                     [np.polyval(pr, ycut), ycut], [np.polyval(pl, ycut), ycut]], np.float32)
    lid = np.zeros_like(m); cv2.fillPoly(lid, [poly.round().astype(np.int32)], 255)
    # stay 2px inside the fitted edges (the real edge wins wherever it survived) and round the corners
    r = max(6, int(lid_w * 0.03))
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    lid = cv2.morphologyEx(lid, cv2.MORPH_OPEN, disk)
    lid = cv2.erode(lid, np.ones((5, 5), np.uint8))
    return m | lid

REPAIR = set()

def cutout(path, thr=238, chroma=14, ss=4):
    cache = os.path.splitext(path)[0] + "_cut.png"
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(__file__): return Image.open(cache)
    im0 = Image.open(path).convert("RGB"); P0 = 12  # pad so the background is one connected region
    im = Image.new("RGB", (im0.width + 2 * P0, im0.height + 2 * P0), (255, 255, 255)); im.paste(im0, (P0, P0))
    a = np.array(im).astype(np.int16); h, w = a.shape[:2]
    white = ((a.min(2) >= thr) & ((a.max(2) - a.min(2)) <= chroma)).astype(np.uint8)
    n, lab = cv2.connectedComponents(white, connectivity=4)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    fg = ~np.isin(lab, list(border))
    ai = _ai_alpha(im) > 160
    m = (fg | ai).astype(np.uint8) * 255
    k3 = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k3, iterations=2)
    nn, ll, st, _ = cv2.connectedComponentsWithStats(m)
    m = np.where(ll == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    if os.path.basename(path).split(".")[0] in REPAIR: m = repair_lid(m)
    ff = m.copy(); cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255); m = m | (255 - ff)  # fill holes
    m = cv2.erode(m, k3, iterations=1)  # drop the light JPEG fringe
    # smooth edges: blur, upsample, threshold, area-downsample -> anti-aliased straight edges
    f = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.3)
    big = cv2.resize(f, (w * ss, h * ss), interpolation=cv2.INTER_CUBIC)
    big = (big > 0.5).astype(np.float32)
    alpha = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
    # decontaminate: un-mix white from partially transparent edge pixels
    rgb = a.astype(np.float32); al = alpha[..., None]
    edge = (alpha > 0.02) & (alpha < 0.98)
    dec = np.clip((rgb - 255 * (1 - al)) / np.maximum(al, 0.05), 0, 255)
    rgb[edge] = dec[edge]
    out = np.dstack([rgb.astype(np.uint8), (alpha * 255).astype(np.uint8)])
    res = Image.fromarray(out, "RGBA"); res = res.crop(res.getbbox()); res.save(cache)
    return res
