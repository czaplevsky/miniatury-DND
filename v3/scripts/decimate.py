"""Decimate the high-res voxel mesh (quadric, fast-simplification; Blender's decimate OOMs at ~13M tris / 15 GB).
usage: decimate.py IN.stl OUT.stl [TARGET_TRIS=1900000]"""
import sys, time, numpy as np, trimesh, fast_simplification
t = time.time()
src, dst = sys.argv[1], sys.argv[2]
T = int(sys.argv[3]) if len(sys.argv) > 3 else 1900000
m = trimesh.load(src)                     # merges vertices
V, F = m.vertices.astype(np.float32), m.faces.astype(np.int32)
del m
print('loaded', len(F), round(time.time() - t), flush=True)
V2, F2 = fast_simplification.simplify(V, F, target_reduction=1 - T / len(F), agg=5)
out = trimesh.Trimesh(V2, F2, process=True)
out.export(dst)
print('decimated', len(F), '->', len(F2), 'watertight', out.is_watertight, round(time.time() - t), 's')
