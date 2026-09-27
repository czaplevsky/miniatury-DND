"""Generate a 3D shape from the prepared concept views via Hugging Face Spaces.

Usage (from dnd-mini/):  python scripts/gen.py <job> [image]
  job = mv    -> tencent/Hunyuan3D-2mv, front+back+side views
        h21   -> tencent/Hunyuan3D-2.1, single image (default: front view)
Needs network access to huggingface.co, *.hf.space; HF_TOKEN env var raises the ZeroGPU quota.
"""
import os
import shutil
import sys
import time

from gradio_client import Client, handle_file

P = os.environ.get("PREP", "prepped/")
job = sys.argv[1]
img = sys.argv[2] if len(sys.argv) > 2 else P + "view_front_rgba.png"
token = os.environ.get("HF_TOKEN")
os.makedirs("ai", exist_ok=True)
t = time.time()
if job == "mv":
    c = Client("tencent/Hunyuan3D-2mv", token=token, verbose=False)
    r = c.predict(caption=None, image=None, mv_image_front=handle_file(P + "view_front_rgba.png"),
                  mv_image_back=handle_file(P + "view_back_rgba.png"), mv_image_left=handle_file(P + "view_side_rgba.png"),
                  mv_image_right=None, steps=30, guidance_scale=5.0, seed=1234, octree_resolution=512,
                  check_box_rembg=True, num_chunks=200000, randomize_seed=False, api_name="/shape_generation")
elif job == "h21":
    c = Client("tencent/Hunyuan3D-2.1", token=token, verbose=False)
    r = c.predict(image=handle_file(img), mv_image_front=None, mv_image_back=None, mv_image_left=None,
                  mv_image_right=None, steps=30, guidance_scale=5.0, seed=1234, octree_resolution=512,
                  check_box_rembg=True, num_chunks=200000, randomize_seed=False, api_name="/shape_generation")
else:
    raise SystemExit(f"unknown job {job}")
print(job, "secs", round(time.time() - t))
print(str(r[2])[:300])
f0 = r[0]
f0 = (f0.get("value") or f0.get("path")) if isinstance(f0, dict) else f0
out = f"ai/{job}_{int(time.time())}.glb"
shutil.copy(f0, out)
print("saved", out)
