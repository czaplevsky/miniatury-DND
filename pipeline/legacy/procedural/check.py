import sys, trimesh, numpy as np
m = trimesh.load(sys.argv[1])
print("tris", len(m.faces), "watertight", m.is_watertight, "winding", m.is_winding_consistent)
print("bounds mm", np.round(m.bounds, 2).tolist(), "extent", np.round(m.extents, 2).tolist())
parts = m.split(only_watertight=False)
print("bodies", len(parts), "sizes", sorted([len(p.faces) for p in parts], reverse=True)[:6])
print("volume mm3", round(m.volume, 1), "resin ml ~", round(m.volume / 1000, 2))
