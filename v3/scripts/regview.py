"""Overlay: mesh front shading (from registration json) blended with the front image. usage: regview.py MESH REG.json OUT.png"""
import sys, json, numpy as np, trimesh
from PIL import Image
m = trimesh.load(sys.argv[1]); R = json.load(open(sys.argv[2]))
m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(R['yaw']), [0, 0, 1]))
img = np.asarray(Image.open('img/front_s7_rgba.png').convert('RGB')).astype(float)
H, W = img.shape[:2]
w, u = np.mgrid[:H, :W]
x = R['x0'] + (u - R['u0']) / R['sx']; z = R['z0'] - (w - R['w0']) / R['sz']
o = np.stack([x.ravel(), np.full(x.size, -100.0), z.ravel()], 1)
loc, ri, ti = m.ray.intersects_location(o, np.tile([0, 1.0, 0], (x.size, 1)), multiple_hits=False)
sh = np.zeros(x.size); n = m.face_normals[ti]
sh[ri] = np.clip(n @ np.array([-0.4, -0.8, 0.45]), 0, 1) * 255
sh = sh.reshape(H, W)
out = img.copy(); out[..., 1] = sh; out[..., 2] = sh * 0.5 + img[..., 2] * 0.5
Image.fromarray(out.astype(np.uint8)).save(sys.argv[3])
