"""Emboss painted surface detail (bandage strips, fur, straps) from the concept art onto the mesh.
Front image projected along +Y onto front-facing surfaces, back image along -Y onto back-facing ones."""
import sys, trimesh, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
src, dst = sys.argv[1], sys.argv[2]
AMP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.09
m = trimesh.load(src)
V = m.vertices.copy(); N = m.vertex_normals


def signal(path, s_px):
    a = np.asarray(Image.open(path).convert('L')).astype(float)
    fine = a - gaussian_filter(a, s_px * 0.07)      # ~0.07 mm features
    mid = a - gaussian_filter(a, s_px * 0.18)       # bandage strips ~0.4-0.6 mm
    sig = 0.45 * fine + 0.55 * mid
    return np.clip(sig / (3 * sig.std()), -1, 1)


# registration: (image top px, bottom px) <-> z 39 / 3 ; head centre px <-> x=-0.64
F = dict(path='edit/kontext_s7.png', top=102, bot=1133, cx=415.5, mirror=False)
B = dict(path='imgprep/out/view_back.png', top=254, bot=2785, cx=1039.0, mirror=True)
disp = np.zeros(len(V))
wsum = np.zeros(len(V))
for cfg, w in ((F, np.clip(-N[:, 1], 0, 1)), (B, np.clip(N[:, 1], 0, 1))):
    s = (cfg['bot'] - cfg['top']) / 36.0
    sig = signal(cfg['path'], s)
    px = cfg['cx'] + (-(V[:, 0] + 0.64) if cfg['mirror'] else (V[:, 0] + 0.64)) * s
    py = cfg['top'] + (39.0 - V[:, 2]) * s
    val = map_coordinates(sig, [py, px], order=1, mode='nearest')
    w = w ** 1.5
    disp += val * w; wsum += w
disp = np.where(wsum > 1e-3, disp / np.maximum(wsum, 1e-3), 0) * np.clip(wsum * 2, 0, 1)
d = disp * AMP
d = np.where(d < 0, d * 0.35, d) + 0.08   # mostly raised detail + 0.08 mm skin so thin cloth never gets thinner
m.vertices = V + N * d[:, None]
print('disp range mm', np.round(np.percentile(d, [1, 50, 99]), 3))
m.export(dst)
