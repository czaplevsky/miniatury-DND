"""Image-space maps for detail.py (front view, 832x1248 px, same framing as img/front_s7_rgba.png).
Outputs maps/front_maps.npz: relief (Marigold height high-pass, ~[-1,1]), groove (0..1 V-profile on bandage seams),
band (soft bandage-region mask), alpha."""
import numpy as np, os
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_erosion
from skimage.filters import sato
from skimage.morphology import skeletonize, remove_small_objects
os.makedirs('maps', exist_ok=True)
col = np.asarray(Image.open('img/front_s7_rgba.png')).astype(float)
scu = np.asarray(Image.open('img/front_k21b.png').convert('L')).astype(float) / 255
alpha = col[..., 3] > 128
H, W = alpha.shape
# --- bandage regions (hand-placed on the front concept, px) ---
reg = Image.new('L', (W, H), 0); d = ImageDraw.Draw(reg)
for e in [(360, 95, 470, 245)]:                      # head (also handled procedurally in detail.py)
    d.ellipse(e, fill=255)
for b in [(378, 222, 452, 275),                      # neck
          (318, 365, 548, 460),                      # abdomen band
          (210, 355, 292, 425), (522, 350, 585, 425), # upper arms
          (565, 415, 642, 505), (222, 555, 305, 645), # hands / forearm wraps
          (282, 595, 392, 790), (438, 595, 545, 790), # thighs
          (250, 1030, 335, 1135), (470, 1020, 605, 1105)]:  # boot wraps
    d.rectangle(b, fill=255)
# zone labels (for procedural wraps around the limbs in detail.py)
ZONES = [('head', 'e', (360, 95, 470, 245)), ('neck', 'r', (378, 222, 452, 275)), ('belly', 'r', (318, 365, 548, 460)),
         ('uarmR', 'r', (210, 355, 292, 425)), ('uarmL', 'r', (522, 350, 585, 425)),
         ('handL', 'r', (565, 415, 642, 505)), ('handR', 'r', (222, 555, 305, 645)),
         ('thighR', 'r', (282, 595, 392, 790)), ('thighL', 'r', (438, 595, 545, 790)),
         ('bootR', 'r', (250, 1030, 335, 1135)), ('bootL', 'r', (470, 1020, 605, 1105))]
lab = Image.new('L', (W, H), 0); dl = ImageDraw.Draw(lab)
for i, (nm, kind, bb) in enumerate(ZONES):
    (dl.ellipse if kind == 'e' else dl.rectangle)(bb, fill=i + 1)
# branch centreline (px) through both fists
BR = [(150, 775), (205, 695), (262, 605), (330, 563), (420, 520), (500, 477), (585, 436), (650, 352), (710, 285), (760, 242)]
brm = Image.new('L', (W, H), 0); db = ImageDraw.Draw(brm)
db.line(BR, fill=255, width=50, joint='curve')
for p in (BR[0], BR[-1]): db.ellipse((p[0] - 30, p[1] - 30, p[0] + 30, p[1] + 30), fill=255)
branch = (np.asarray(brm) > 0) & alpha
band = gaussian_filter(np.asarray(reg).astype(float) / 255, 4) * binary_erosion(alpha, iterations=6)
band *= 1 - gaussian_filter(branch.astype(float), 3)
# --- relief from AI normals (avg of sculpt + colour estimates), high-pass ~6 px ---
hp = 0
for k in ('k21', 's7'):
    h = np.load(f'nrm/{k}_h.npy'); x = h - gaussian_filter(h, 6)
    hp = hp + x / np.percentile(np.abs(x[alpha]), 98)
hp = np.clip(hp / 2, -1, 1)
edge = distance_transform_edt(alpha)                  # fade out 8 px from the silhouette (halo)
hp *= np.clip((edge - 3) / 8, 0, 1)
# --- seams: dark ridges in the sculpt (k21) luminance and in the colour image, only in bandage regions ---
lum = col[..., :3].mean(-1) / 255
r = 0.6 * sato(scu, sigmas=[1.5, 2.5], black_ridges=True) / 0.05 + 0.4 * sato(lum, sigmas=[1.5, 2.5], black_ridges=True) / 0.05
r *= band > 0.3
lines = r > np.percentile(r[band > 0.3], 78)
lines = remove_small_objects(lines, max_size=25)
sk = skeletonize(lines)
sk = remove_small_objects(sk, max_size=10, connectivity=2)
dist = distance_transform_edt(~sk)
groove = np.clip(1 - dist / 3.2, 0, 1)                # V profile, half-width 3.2 px (~0.11 mm @ 28.8 px/mm)
np.savez_compressed('maps/front_maps.npz', relief=hp.astype(np.float32), groove=groove.astype(np.float32),
                    band=band.astype(np.float32), alpha=alpha,
                    zones=np.asarray(lab), branch=branch, branch_line=np.array(BR, float))
# previews
o = (col[..., :3] * 0.5).astype(np.uint8)
o[..., 0] = np.maximum(o[..., 0], (band * 90).astype(np.uint8))
o[groove > 0.5] = [255, 255, 0]
o[branch, 2] = 200
Image.fromarray(o).crop((180, 80, 680, 820)).save('maps/_grooves.png')
Image.fromarray(np.clip(128 + hp * 127, 0, 255).astype(np.uint8)).save('maps/_relief.png')
print('seam px', sk.sum())
