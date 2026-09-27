"""Fit the image->mesh mapping (yaw, per-axis scale, offset) by correlating the mesh's front normal map with the
AI (Marigold) normal map of the front image. usage: regfit.py MESH.stl NORMALS.npy ALPHA_RGBA.png OUT.json"""
import sys, json, numpy as np, trimesh
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import minimize
mesh0 = trimesh.load(sys.argv[1]); N = np.load(sys.argv[2]); alpha = np.asarray(Image.open(sys.argv[3]))[..., 3] > 128
H, W = alpha.shape
ys, xs = np.where(alpha)
u0, u1, w0, w1 = xs.min(), xs.max(), ys.min(), ys.max()
nimg = [gaussian_filter(N[..., k], 1.5) for k in (0, 1)]


def mesh_normals(mesh, res=0.04):
    b = mesh.bounds
    gx = np.arange(b[0][0], b[1][0], res); gz = np.arange(b[0][2], b[1][2], res)
    X, Z = np.meshgrid(gx, gz)
    o = np.stack([X.ravel(), np.full(X.size, -100.0), Z.ravel()], 1)
    loc, ri, ti = mesh.ray.intersects_location(o, np.tile([0, 1.0, 0], (X.size, 1)), multiple_hits=False)
    nx = np.full(X.size, np.nan); nz = np.full(X.size, np.nan)
    fn = mesh.face_normals[ti]
    nx[ri] = fn[:, 0]; nz[ri] = fn[:, 2]
    return gx, gz, nx.reshape(X.shape), nz.reshape(X.shape)


best = None
step = 3
wg, ug = np.mgrid[w0:w1:step, u0:u1:step]
am = alpha[wg, ug]
for yaw in (-6, -3, 0, 3, 6, 9, 12):
    m = mesh0.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1]))
    gx, gz, mnx, mnz = mesh_normals(m)
    b = m.bounds
    valid = ~np.isnan(mnx)
    mnx0 = np.nan_to_num(mnx); mnz0 = np.nan_to_num(mnz)

    def score(p):
        sx, sz, ox, oz = p
        x = b[0][0] + ox + (ug - u0) / sx; z = b[1][2] + oz - (wg - w0) / sz
        ci = (x - gx[0]) / (gx[1] - gx[0]); ri = (z - gz[0]) / (gz[1] - gz[0])
        v = map_coordinates(valid.astype(float), [ri, ci], order=0) > 0.5
        sel = v & am
        a1 = map_coordinates(mnx0, [ri, ci], order=1)[sel]; a2 = map_coordinates(mnz0, [ri, ci], order=1)[sel]
        b1 = nimg[0][wg, ug][sel]; b2 = nimg[1][wg, ug][sel]
        c = (np.corrcoef(a1, b1)[0, 1] + np.corrcoef(a2, b2)[0, 1]) / 2
        iou = sel.sum() / (v | am).sum()
        return -(c + 0.5 * iou)
    p0 = [(u1 - u0) / (b[1][0] - b[0][0]), (w1 - w0) / (b[1][2] - b[0][2]), 0.0, 0.0]
    r = minimize(score, p0, method='Nelder-Mead', options=dict(xatol=1e-3, fatol=1e-4, maxiter=300,
                 initial_simplex=[p0, [p0[0] * 1.04, p0[1], 0, 0], [p0[0], p0[1] * 1.03, 0, 0], [p0[0], p0[1], 0.4, 0], [p0[0], p0[1], 0, 0.4]]))
    print(yaw, round(-r.fun, 4), np.round(r.x, 3), round(-score(p0), 4), flush=True)
    if best is None or r.fun < best[0]:
        best = (r.fun, yaw, r.x.tolist(), [float(b[0][0]), float(b[1][2])])
f, yaw, (sx, sz, ox, oz), (xmin, zmax) = best
json.dump(dict(yaw=yaw, sx=sx, sz=sz, x0=xmin + ox, z0=zmax + oz, u0=int(u0), w0=int(w0), score=-f), open(sys.argv[4], 'w'), indent=1)
print('best', yaw, -f)
