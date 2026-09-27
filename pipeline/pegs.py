"""Find thin peg/twig protrusions (thin in >=2 directions) on a mesh. Returns bool mask per vertex.
A vertex is 'peg' if the inward normal ray exits within TH mm AND at least 5 of 8 inward-tilted tangent rays exit
within CH mm (a sheet like the cloak is thin only along its normal)."""
import numpy as np


def peg_mask(mesh, V=None, N=None, TH=0.62, CH=0.75):
    V = mesh.vertices if V is None else V
    N = mesh.vertex_normals if N is None else N
    o = V - N * 0.004

    def hitdist(d):
        out = np.full(len(V), 99.0)
        for a in range(0, len(V), 500000):
            b = min(len(V), a + 500000)
            loc, ri, ti = mesh.ray.intersects_location(o[a:b], d[a:b], multiple_hits=False)
            out[a + ri] = np.linalg.norm(loc - o[a:b][ri], axis=1)
        return out
    t = hitdist(-N)
    cand = t < TH
    idx = np.where(cand)[0]
    Vc, Nc, oc = V[idx], N[idx], o[idx]
    ref = np.where(np.abs(Nc[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
    T1 = np.cross(Nc, ref); T1 /= np.linalg.norm(T1, axis=1, keepdims=True)
    T2 = np.cross(Nc, T1)
    cnt = np.zeros(len(idx), int)
    for k in range(8):
        a = k * np.pi / 4
        d = np.cos(a) * T1 + np.sin(a) * T2 - 0.35 * Nc
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        loc, ri, ti = mesh.ray.intersects_location(oc, d, multiple_hits=False)
        dd = np.full(len(idx), 99.0); dd[ri] = np.linalg.norm(loc - oc[ri], axis=1)
        cnt += dd < CH
    peg = np.zeros(len(V), bool); peg[idx[cnt >= 5]] = True
    return peg, t


if __name__ == '__main__':
    import sys, trimesh
    from scipy import ndimage
    m = trimesh.load(sys.argv[1])
    peg, t = peg_mask(m)
    print('peg verts', peg.sum(), 'of', len(peg))
    # clusters
    sub = m.submesh([np.where(peg[m.faces].all(1))[0]], append=True)
    parts = sub.split(only_watertight=False)
    for p in sorted(parts, key=lambda p: -len(p.faces))[:40]:
        c = p.vertices.mean(0); e = p.extents
        print('cluster faces %5d  centre %s  extent %s' % (len(p.faces), np.round(c, 1), np.round(e, 2)))
    sub.export('out/pegs_dbg.stl')
