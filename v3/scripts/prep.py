"""Hunyuan glb (Y-up, front +Z) -> Z-up mm, front facing -Y, soles z=3, head top z=39 (36 mm figure).
usage: prep.py IN.glb OUT.stl"""
import sys, trimesh, numpy as np
m = trimesh.load(sys.argv[1], force='mesh')
parts = m.split(only_watertight=False)
big = max(len(p.faces) for p in parts)
parts = [p for p in parts if len(p.faces) > 0.01 * big]
print('parts kept', len(parts), [len(p.faces) for p in parts])
m = trimesh.util.concatenate(parts)
m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
b = m.bounds
s = 36.0 / (b[1][2] - b[0][2])
m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
m.apply_scale(s); m.apply_translation([0, 0, 3.0])
print('faces', len(m.faces), 'bounds', np.round(m.bounds, 2).tolist(), 'watertight', m.is_watertight)
m.export(sys.argv[2])
