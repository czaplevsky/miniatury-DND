"""Step 3: background removal (rembg isnet-general-use, CPU). usage: cutout.py IN OUT_RGBA"""
import sys, numpy as np
from PIL import Image
from rembg import remove, new_session
from scipy import ndimage
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
r = np.asarray(remove(im, session=new_session('isnet-general-use'))).copy()
a = r[..., 3]
lab, n = ndimage.label(a > 40)
if n > 1:
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.where(sizes > 0.002 * sizes.max())[0])
    a[~ndimage.binary_dilation(keep, iterations=3)] = 0
r[..., 3] = a
Image.fromarray(r).save(out); print(out, n, Image.fromarray(a).getbbox())
