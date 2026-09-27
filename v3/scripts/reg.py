"""Front-image <-> mesh registration helpers (mesh: mm, Z up, front faces -Y)."""
import numpy as np


class Reg:
    def __init__(self, mesh, alpha, fit=True):
        self.alpha = alpha
        ys, xs = np.where(alpha)
        self.u0, self.u1, self.w0, self.w1 = xs.min(), xs.max(), ys.min(), ys.max()
        b = mesh.bounds
        self.xmin, self.xmax, self.zmin, self.zmax = b[0][0], b[1][0], b[0][2], b[1][2]
        self.sx = (self.u1 - self.u0) / (self.xmax - self.xmin)
        self.sz = (self.w1 - self.w0) / (self.zmax - self.zmin)
        self.mesh = mesh
        self.depth()

    def pix(self, x, z):
        return self.u0 + (x - self.xmin) * self.sx, self.w0 + (self.zmax - z) * self.sz

    def world(self, u, w):
        return self.xmin + (u - self.u0) / self.sx, self.zmax - (w - self.w0) / self.sz

    def depth(self):
        """first-hit y (front) and last-hit y (back) per image pixel via embree."""
        H, W = self.alpha.shape
        w, u = np.mgrid[:H, :W]
        x, z = self.world(u + 0.5, w + 0.5)
        o = np.stack([x.ravel(), np.full(x.size, -100.0), z.ravel()], 1)
        d = np.tile([0, 1.0, 0], (x.size, 1))
        loc, ri, ti = self.mesh.ray.intersects_location(o, d, multiple_hits=False)
        yf = np.full(x.size, np.nan); yf[ri] = loc[:, 1]
        self.yfront = yf.reshape(H, W)
        o[:, 1] = 100.0
        loc, ri, ti = self.mesh.ray.intersects_location(o, -d, multiple_hits=False)
        yb = np.full(x.size, np.nan); yb[ri] = loc[:, 1]
        self.yback = yb.reshape(H, W)

    def sample(self, img, x, z, order=1):
        from scipy.ndimage import map_coordinates
        u, w = self.pix(x, z)
        return map_coordinates(img, [w - 0.5, u - 0.5], order=order, mode='nearest')
