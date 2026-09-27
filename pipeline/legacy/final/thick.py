import sys, trimesh, numpy as np
m = trimesh.load(sys.argv[1])
rng = np.random.default_rng(0)
idx = rng.choice(len(m.faces), 150000, replace=False)
c = m.triangles_center[idx]; n = m.face_normals[idx]
o = c - n * 0.005
loc, ri, ti = m.ray.intersects_location(o, -n, multiple_hits=False)
d = np.full(len(idx), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
z = c[:, 2]
mask = z > 3.2
for thr in (0.3, 0.4, 0.5, 0.6):
    sel = mask & (d < thr)
    print(f'< {thr} mm: {sel.sum()/mask.sum()*100:.2f}% of surface samples')
thin = mask & (d < 0.4)
if thin.any():
    H, xe, ze = np.histogram2d(c[thin, 0], c[thin, 2], bins=[6, 8], range=[[-12, 12], [3, 39]])
    print('thin (<0.4) sample counts, rows = z bins (top first), cols = x from -12 to 12:')
    for j in range(H.shape[1] - 1, -1, -1): print(f'z {ze[j]:4.1f}-{ze[j+1]:4.1f}', H[:, j].astype(int))
