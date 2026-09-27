"""Hybrid AI body: crisp front from the single-view mesh (mini_k21) + back from the multi-view mesh (fur collar,
cloak drape): FRONT ∪ (BACK ∩ {y > Y0}) with a soft boolean via manifold3d. Both meshes are in the same mm frame
(prep.py normalises by bbox, both come from the same front image).  usage: hybrid.py FRONT.stl BACK.stl OUT.stl [Y0]"""
import sys, numpy as np, trimesh, manifold3d as mf
F, B, out = sys.argv[1], sys.argv[2], sys.argv[3]
Y0 = float(sys.argv[4]) if len(sys.argv) > 4 else 1.5


def to_mf(t):
    t = trimesh.Trimesh(t.vertices, t.faces, process=True)
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


f = trimesh.load(F); b = trimesh.load(B)
ZT = float(sys.argv[5]) if len(sys.argv) > 5 else 34.3
XH = float(sys.argv[6]) if len(sys.argv) > 6 else 9.8
box = trimesh.creation.box(extents=[2 * XH, 20, ZT - 2]); box.apply_translation([0, Y0 + 10, 2 + (ZT - 2) / 2])
# keep the MV back only below the head (head comes from the front mesh) and away from the branch/hands region in front
# exclude the MV head: vertical capsule around the front mesh's head
hv = f.vertices[f.vertices[:, 2] > 36.5]
hc = hv[:, :2].mean(0); hrad = np.percentile(np.linalg.norm(hv[:, :2] - hc, axis=1), 98) + 0.35
cyl = trimesh.creation.cylinder(radius=hrad, height=10, sections=64); cyl.apply_translation([hc[0], hc[1], 34.0 + 5])
sph = trimesh.creation.icosphere(subdivisions=4, radius=hrad); sph.apply_translation([hc[0], hc[1], 34.0])
print('head capsule centre', np.round(hc, 2), 'r', round(hrad, 2))
# no collar fin behind the head: rounded (ellipsoidal) dip instead of a box cut (box left flat walls in d19)
nape = trimesh.creation.icosphere(subdivisions=4, radius=1.0); nape.apply_scale([hrad * 0.95, 3.2, 1.9])
nape.apply_translation([hc[0], hc[1] + 1.6, 36.6])
Bk = (to_mf(b) ^ to_mf(box)) - to_mf(cyl) - to_mf(sph) - to_mf(nape)
# cloak sides: behind the cut plane only the MV cloak is kept, so the front mesh's cloak edge cannot poke through it
Fm = to_mf(f)
for sx in (-1, 1):
    cb = trimesh.creation.box(extents=[6, 12, 29.5]); cb.apply_translation([sx * (7.3 + 3), Y0 + 0.2 + 6, 3.5 + 29.5 / 2])
    Fm = Fm - to_mf(cb)
M = Fm + Bk
o = M.to_mesh()
r = trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts), process=True)
parts = r.split(only_watertight=False)
r = max(parts, key=lambda p: len(p.faces))
print('faces', len(r.faces), 'watertight', r.is_watertight, 'bounds', np.round(r.bounds, 2).tolist())
r.export(out)
