"""Wall-thickness check that ignores relief flanks: a sample counts as a thin WALL only if the inward ray exits
through a face roughly opposite to the start face (dot < -0.7), i.e. a real sheet. usage: thick2.py MESH.stl"""
import sys, trimesh, numpy as np
m = trimesh.load(sys.argv[1])
rng = np.random.default_rng(0)
idx = rng.choice(len(m.faces), 300000, replace=False)
c = m.triangles_center[idx]; n = m.face_normals[idx]
o = c - n * 0.003
loc, ri, ti = m.ray.intersects_location(o, -n, multiple_hits=False)
d = np.full(len(idx), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
opp = np.zeros(len(idx), bool); opp[ri] = (m.face_normals[ti] * n[ri]).sum(1) < -0.7
mask = c[:, 2] > 3.2
for thr in (0.3, 0.4, 0.5):
    sel = mask & (d < thr) & opp
    print(f'wall < {thr} mm: {sel.sum() / mask.sum() * 100:.2f}% of surface samples')
thin = mask & (d < 0.4) & opp
H, xe, ze = np.histogram2d(c[thin, 0], c[thin, 2], bins=[6, 8], range=[[-12, 12], [3, 39]])
for j in range(H.shape[1] - 1, -1, -1): print(f'z {ze[j]:4.1f}-{ze[j+1]:4.1f}', H[:, j].astype(int))
