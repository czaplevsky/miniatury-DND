"""Wall-thickness check at the scale of sheets, not relief: the inward ray uses the surface normal averaged over a
0.45 mm neighbourhood, so the flanks of raised relief (fur locks, strips, bark) shoot into the body instead of across
the ridge (thick2.py counts those ridges as 'walls'). A sample is a thin WALL if the ray exits through an opposite
face within the threshold. usage: thick3.py MESH.stl"""
import sys, trimesh, numpy as np
from scipy.spatial import cKDTree
m = trimesh.load(sys.argv[1])
rng = np.random.default_rng(0)
pool = rng.choice(len(m.faces), min(500000, len(m.faces)), replace=False)
P = m.triangles_center[pool]; PN = m.face_normals[pool] * m.area_faces[pool, None]
test = rng.choice(len(m.faces), 150000, replace=False)
C = m.triangles_center[test]
tree = cKDTree(P)
nb = tree.query_ball_point(C, 0.45)
SN = np.array([PN[i].sum(0) for i in nb])
SN /= np.maximum(np.linalg.norm(SN, axis=1, keepdims=True), 1e-9)
o = C - SN * 0.003
loc, ri, ti = m.ray.intersects_location(o, -SN, multiple_hits=False)
d = np.full(len(test), np.inf); d[ri] = np.linalg.norm(loc - o[ri], axis=1)
opp = np.zeros(len(test), bool); opp[ri] = (m.face_normals[ti] * SN[ri]).sum(1) < -0.5
mask = (C[:, 2] > 3.2) & np.isfinite(SN).all(1)
art = opp & (d < 0.08)          # < 2.5 voxels: decimation slivers in creases, not walls
print(f'crease slivers (<0.08 mm, ignored): {(mask & art).sum() / mask.sum() * 100:.2f}%')
opp &= ~art
for thr in (0.3, 0.4, 0.5):
    print(f'sheet wall < {thr} mm: {(mask & opp & (d < thr)).sum() / mask.sum() * 100:.2f}% of surface samples')
thin = mask & opp & (d < 0.4)
H, xe, ze = np.histogram2d(C[thin, 0], C[thin, 2], bins=[6, 8], range=[[-12, 12], [3, 39]])
for j in range(H.shape[1] - 1, -1, -1):
    print(f'z {ze[j]:4.1f}-{ze[j+1]:4.1f}', H[:, j].astype(int))
