"""AI glb (Y-up, with floor slab) -> Z-up mm mesh, soles at z=3 (base top), head top at z=39."""
import sys, trimesh, numpy as np
src, dst = sys.argv[1], sys.argv[2]
m = trimesh.load(src, force='mesh')
keep = m.vertices[m.faces][:, :, 1].min(axis=1) > -0.605
m.update_faces(keep); m.remove_unreferenced_vertices()
parts = m.split(only_watertight=False)
m = max(parts, key=lambda p: len(p.faces))
R = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
m.apply_transform(R)                       # y-up -> z-up, front (+z) -> -y
b = m.bounds
H = b[1][2] - b[0][2]
s = 36.0 / H
m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
m.apply_scale(s)
m.apply_translation([0, 0, 3.0])
trimesh.repair.fill_holes(m); print('watertight', m.is_watertight)
print('faces', len(m.faces), 'bounds', np.round(m.bounds, 2).tolist())
m.export(dst)
