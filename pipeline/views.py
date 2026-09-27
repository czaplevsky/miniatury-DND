"""Step 2: consistent back/left/right views from the edited front.
usage: python views.py SRC OUTPREFIX SEED [az1 az2 ...]   (az: 180=back, 90, 270)
Primary: multimodalart/qwen-image-multiple-angles-3d-camera (Qwen-Image-Edit-2511 + multiple-angles LoRA).
Fallback (env FALLBACK=kontext): FLUX.1-Kontext-Dev with a 'viewed from behind/side' prompt."""
import os, shutil, sys, time
from gradio_client import Client, handle_file
src, pref, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
azs = [float(a) for a in sys.argv[4:]] or [180, 90, 270]
KPROMPT = {180: "same character, same pose, viewed from directly behind, orthographic, full body, plain light grey background",
           90: "same character, same pose, viewed from his left side (profile), orthographic, full body, plain light grey background",
           270: "same character, same pose, viewed from his right side (profile), orthographic, full body, plain light grey background"}
if os.environ.get('FALLBACK') == 'kontext':
    c = Client('black-forest-labs/FLUX.1-Kontext-Dev', token=os.environ['HF_TOKEN'], verbose=False)
else:
    c = Client('multimodalart/qwen-image-multiple-angles-3d-camera', token=os.environ['HF_TOKEN'], verbose=False)
for az in azs:
    t = time.time(); out = f'{pref}_az{int(az)}_s{seed}.png'
    try:
        if os.environ.get('FALLBACK') == 'kontext':
            r = c.predict(input_image=handle_file(src), prompt=KPROMPT[int(az)], seed=seed, randomize_seed=False,
                          guidance_scale=2.5, steps=28, api_name='/infer'); p = r[0]
        else:
            r = c.predict(image=handle_file(src), azimuth=az, elevation=0, distance=1.0, seed=seed, randomize_seed=False,
                          guidance_scale=1.0, num_inference_steps=4, height=1248, width=832, api_name='/infer_camera_edit')
            p = r[0]; print('prompt:', r[2])
        p = p.get('path') if isinstance(p, dict) else p
        shutil.copy(p, out); print('az', az, 'secs', round(time.time() - t), 'saved', out, flush=True)
    except Exception as e:
        print('az', az, 'FAILED', round(time.time() - t), repr(e)[:400], flush=True)
        if 'quota' in repr(e).lower(): sys.exit(3)
