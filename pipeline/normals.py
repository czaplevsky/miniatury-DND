"""Step 5: Marigold-e2e normals on CPU + Frankot-Chellappa integration.
usage: python normals.py IMG_RGBA OUTPREFIX [res=1248]
writes OUTPREFIX_n.npy (HxWx3, camera space, +x right, +y up, +z towards viewer), _n.png, _h.npy (integrated height, px units)"""
import sys, time, torch, numpy as np
from PIL import Image
from diffusers import MarigoldNormalsPipeline, DDIMScheduler
torch.set_num_threads(4)
src, pref = sys.argv[1], sys.argv[2]
res = int(sys.argv[3]) if len(sys.argv) > 3 else 1248
im = Image.open(src).convert('RGBA')
rgb = Image.new('RGB', im.size, (200, 200, 200)); rgb.paste(im, mask=im.split()[3])
t = time.time()
p = MarigoldNormalsPipeline.from_pretrained('GonzaloMartinGarcia/marigold-e2e-ft-normals', torch_dtype=torch.float32)
p.scheduler = DDIMScheduler.from_config(p.scheduler.config, timestep_spacing='trailing')
out = p(rgb, num_inference_steps=1, ensemble_size=1, processing_resolution=res, match_input_resolution=True)
print('normals', round(time.time() - t), flush=True)
n = out.prediction[0]
p.image_processor.visualize_normals(out.prediction)[0].save(pref + '_n.png')
np.save(pref + '_n.npy', n.astype(np.float32))
# Frankot-Chellappa: gradients p = -nx/nz, q = ny/nz (image rows go down -> flip)
a = np.asarray(im)[..., 3] > 128
nz = np.clip(n[..., 2], 0.15, 1)
gx = np.where(a, -n[..., 0] / nz, 0); gy = np.where(a, n[..., 1] / nz, 0)
H, W = gx.shape
wx = np.fft.fftfreq(W) * 2 * np.pi; wy = np.fft.fftfreq(H) * 2 * np.pi
WX, WY = np.meshgrid(wx, wy)
den = WX ** 2 + WY ** 2; den[0, 0] = 1
Z = (-1j * WX * np.fft.fft2(gx) - 1j * WY * np.fft.fft2(gy)) / den; Z[0, 0] = 0
h = np.real(np.fft.ifft2(Z)).astype(np.float32)
np.save(pref + '_h.npy', h); print('saved', pref)
