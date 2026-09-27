"""Optional quota spend: Stable-X/Hi3DGen single-view (normal-bridged TRELLIS). usage: hi3dgen.py IMG OUTPREFIX [seed]"""
import os, sys, shutil, time
from gradio_client import Client, handle_file
img, pref = sys.argv[1], sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
c = Client('Stable-X/Hi3DGen', token=os.environ['HF_TOKEN'], verbose=False)
t = time.time()
pre = c.predict(image=handle_file(img), api_name='/preprocess_image')
pp = pre.get('path') if isinstance(pre, dict) else pre
print('pre', round(time.time() - t), flush=True)
r = c.predict(image=handle_file(pp), seed=seed, ss_guidance_strength=3, ss_sampling_steps=50, slat_guidance_strength=3,
              slat_sampling_steps=6, api_name='/generate_3d')
print('gen', round(time.time() - t), flush=True)
nb = r[1].get('path') if isinstance(r[1], dict) else r[1]
if nb: shutil.copy(nb, pref + '_normal.png')
for f in (r[3], r[2]):
    f = f.get('path') if isinstance(f, dict) else f
    if f:
        ext = os.path.splitext(f)[1]; shutil.copy(f, pref + ext); print('saved', pref + ext); break
