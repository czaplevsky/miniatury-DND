"""Cut stray thin thorns/twigs off the AI body (shoulder/collar thorns, forearm vine spikes, knee/shin twigs).
Detect thin-in-2-directions clusters (pegs.py), keep only those in the listed regions, and subtract an enlarged
convex hull of each (manifold3d). Collapsing them by smoothing (d12-d19) left rounded knobs.
usage: depeg.py IN.stl OUT.stl"""
import sys, numpy as np, trimesh, manifold3d as mf
from pegs import peg_mask
m = trimesh.load(sys.argv[1])
pm, _ = peg_mask(m, TH=0.8, CH=0.9)
sub = m.submesh([np.where(pm[m.faces].all(1))[0]], append=True)


def wanted(c, e, n):
    if n < 25 or n > 2500 or e[2] > 3.0 or e[0] < 0.05:
        return None
    x, y, z = c
    if -12 < x < -8.3 and 13.3 < z < 17.5:      # lower branch end
        return None
    if x > 9.5 and z > 32:                       # upper branch end
        return None
    if z > 33 and abs(x) < 8 and e[1] < 1.0:
        return 'shoulder'
    if z > 21 and z < 33 and (x < -7.3 or (x < -4.5 and y < -1)) and e[1] < 1.4 and y < 0.5:
        return 'forearm'
    if 8 < z < 16.5 and abs(x) > 4.2 and y < 2.6 and e[1] < 1.6:
        return 'leg'
    return None


cuts = []; centres = []
for p in sub.split(only_watertight=False):
    c = p.vertices.mean(0); e = np.sort(p.extents)
    k = wanted(c, e, len(p.faces))
    if k:
        h = p.convex_hull
        h.apply_translation(-c); h.apply_scale(1.35); h.apply_translation(c)
        cuts.append(h); centres.append(c)
        print(k, len(p.faces), np.round(c, 1), np.round(e, 2))


def to_mf(t):
    t = trimesh.Trimesh(t.vertices, t.faces, process=True)
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


A = to_mf(m)
for h in cuts:
    A = A - to_mf(h)
o = A.to_mesh()
r = trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts), process=True)
parts = r.split(only_watertight=False)
r = max(parts, key=lambda p: len(p.faces))
print('cuts', len(cuts), 'dropped parts', len(parts) - 1, 'faces', len(r.faces), 'watertight', r.is_watertight)
r.export(sys.argv[2])
np.save(sys.argv[2].replace('.stl', '_cuts.npy'), np.array(centres))
