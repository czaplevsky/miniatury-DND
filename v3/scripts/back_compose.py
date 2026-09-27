"""CPU fallback for step 2 (quota gone): build a back view consistent with the new front from the concept sheet's back view.
- remove the old forked staff (outside the hand) from the sheet back view
- paste the two ends of the new branch from the front view, mirrored, where they stick out past the back silhouette"""
import numpy as np
from PIL import Image
from scipy import ndimage
B = np.asarray(Image.open('/home/user/DASHBOARD/dnd-mini/prepped/view_back_rgba.png')).copy()
F = np.asarray(Image.open('v3/img/front_s7_rgba.png'))
# 1. remove staff: pixels right of / below the hand
yy, xx = np.mgrid[:B.shape[0], :B.shape[1]]
staff = (xx > 1530) & (yy > 1440) & (yy < 1900)
B[staff, 3] = 0
a = B[..., 3] > 40
lab, n = ndimage.label(a); sz = ndimage.sum(a, lab, range(1, n + 1))
B[~np.isin(lab, 1 + np.argmax(sz)), 3] = 0
# 2. mirrored branch ends from the front
s = (2802 - 250) / (1136 - 99)
for (x0, x1, y0, y1) in ((560, 775, 205, 340), (128, 262, 560, 815)):
    for y in range(y0, y1):
        for x in range(x0, x1):
            if F[y, x, 3] < 128: continue
            xb = 1040 - (x - 415) * s; yb = 250 + (y - 99) * s
            X0, X1, Y0, Y1 = int(xb - s / 2), int(xb + s / 2) + 1, int(yb), int(yb + s) + 1
            reg = B[Y0:Y1, X0:X1]
            m = reg[..., 3] < 40
            reg[m] = F[y, x]
Image.fromarray(B).save('v3/img/back_composed_rgba.png')
bg = Image.new('RGB', (2048, 3072), (200, 200, 200)); im = Image.fromarray(B); bg.paste(im, mask=im.split()[3])
bg.resize((512, 768)).save('v3/img/_back_composed_prev.png')
