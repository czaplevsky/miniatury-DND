"""Torn cloak hem: subtract random V-notches / rips from the back of the cloak hem (manifold3d boolean).
usage: notch.py IN.stl OUT.stl"""
import sys, numpy as np, trimesh, manifold3d as mf
m = trimesh.load(sys.argv[1])
V = m.vertices
rng = np.random.default_rng(21)
# cloak = everything behind the legs (y > 2.7) below z 12; hem height per x
cl = V[(V[:, 1] > 2.7) & (V[:, 2] < 12) & (V[:, 2] > 3.3)]
cuts = []
xs = np.sort(rng.uniform(cl[:, 0].min() + 0.6, cl[:, 0].max() - 0.6, 30))
xs = xs[np.concatenate([[True], np.diff(xs) > 0.7])]
for x0 in xs:
    col = cl[np.abs(cl[:, 0] - x0) < 0.25]
    if len(col) < 20:
        continue
    zh = col[:, 2].min()
    if zh < 3.4:          # hem touches the base here: do not cut (keeps it supported)
        continue
    h = rng.uniform(0.9, 2.3); wb = rng.uniform(0.45, 1.0); lean = rng.uniform(-0.35, 0.35)
    y0, y1 = col[:, 1].min() - 0.3, col[:, 1].max() + 0.6
    y0 = max(y0, 2.7)
    # triangular prism along y: base below the hem, apex h above it
    P = np.array([[x0 - wb / 2, zh - 0.6], [x0 + wb / 2, zh - 0.6], [x0 + lean, zh + h]])
    verts = np.array([[p[0], y, p[1]] for y in (y0, y1) for p in P])
    faces = np.array([[0, 2, 1], [3, 4, 5], [0, 1, 4], [0, 4, 3], [1, 2, 5], [1, 5, 4], [2, 0, 3], [2, 3, 5]])
    pr = trimesh.Trimesh(verts, faces, process=True); pr.fix_normals()
    cuts.append(pr)
print('notches', len(cuts))


def to_mf(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


A = to_mf(m)
for c in cuts:
    A = A - to_mf(c)
out = A.to_mesh()
r = trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts), process=True)
print('faces', len(r.faces), 'watertight', r.is_watertight, 'volume', round(r.volume, 1))
r.export(sys.argv[2])
