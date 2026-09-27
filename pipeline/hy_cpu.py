"""Step 4: Hunyuan3D-2 shape on CPU (0 GPU quota).
usage: python hy_cpu.py {mv|mini} OUT.glb OCTREE STEPS SEED view=path [view=path ...]
  mv  : tencent/Hunyuan3D-2mv hunyuan3d-dit-v2-mv-turbo (views: front/back/left/right, any subset)
  mini: tencent/Hunyuan3D-2mini hunyuan3d-dit-v2-mini-turbo (single image; pass front=path)
Images should be RGBA cutouts. Env HY3DGEN_MODELS must point to research/models.
DiT+conditioner are moved to 'meta' before volume decoding (otherwise OOM at octree 512 on 15 GB)."""
import sys, os, time, gc, torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'research', 'Hunyuan3D-2'))
os.environ.setdefault('HY3DGEN_MODELS', os.path.join(HERE, '..', 'research', 'models'))
torch.set_num_threads(4)
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
mode, out, octree, steps, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
views = dict(a.split('=', 1) for a in sys.argv[6:])
repo, sub = {'mv': ('tencent/Hunyuan3D-2mv', os.environ.get('HY_SUB', 'hunyuan3d-dit-v2-mv-turbo')),
             'mini': ('tencent/Hunyuan3D-2mini', 'hunyuan3d-dit-v2-mini-turbo')}[mode]
t = time.time()
p = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(repo, subfolder=sub, use_safetensors=True, device='cpu', dtype=torch.float32)
if 'turbo' in sub:
    p.enable_flashvdm(mc_algo='mc')
p.vae.to(torch.float32)
_orig = p._export
def _exp(*a, **k):
    p.model.to('meta'); p.conditioner.to('meta'); gc.collect(); return _orig(*a, **k)
p._export = _exp
print('load', round(time.time() - t), flush=True)
imgs = {}
for k, f in views.items():
    im = Image.open(f).convert('RGBA'); im.thumbnail((1024, 1024)); imgs[k] = im
img = imgs if mode == 'mv' else imgs['front']
t = time.time()
m = p(image=img, num_inference_steps=steps, octree_resolution=octree, num_chunks=20000,
      generator=torch.manual_seed(seed), output_type='trimesh')[0]
print('gen', octree, steps, round(time.time() - t), len(m.faces), flush=True)
m.export(out); print('saved', out)
