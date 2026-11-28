# Cutout library

Approved, transparent product cutouts. Reuse these before cutting a product again.

- `sealed/{tcgplayer_product_id}.png` - transparent PNG, already checked.
- `sealed/index.json` - name, game, source photo, date approved.

Workflow for a new product:
1. Get the cleanest full-product photo (no frame cropping; prefer transparent or non-white backgrounds).
2. Cut with `automation/cutout.py` (cut5: white print kept, pale-art PATCH polygons per image).
3. Check at full size on a dark background against the source photo: no missing corners, no white rims, white print kept.
4. Only then add it here and use it in a post.
