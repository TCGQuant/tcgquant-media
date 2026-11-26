import numpy as np, cv2
from PIL import Image, ImageFilter
def cutout(path, thr=236, chroma=14):
    im = Image.open(path).convert("RGB"); a = np.array(im).astype(int)
    white = ((a.min(2) >= thr) & ((a.max(2) - a.min(2)) <= chroma)).astype(np.uint8)
    h, w = white.shape
    n, lab = cv2.connectedComponents(white, connectivity=4)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    m = (~bg).astype(np.uint8) * 255
    # drop specks, fill small holes, trim the light fringe by 1px, feather
    k = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    nn, ll, st, _ = cv2.connectedComponentsWithStats(m)
    keep = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(ll == keep, 255, 0).astype(np.uint8)
    m = cv2.erode(m, k, iterations=1)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(m).filter(ImageFilter.GaussianBlur(0.7)))
    return out.crop(out.getbbox())
