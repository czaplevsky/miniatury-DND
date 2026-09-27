import os, shutil, sys, time
from gradio_client import Client, handle_file
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
src = sys.argv[2] if len(sys.argv) > 2 else 'imgprep/out/view_front.png'
c = Client('black-forest-labs/FLUX.1-Kontext-Dev', token=os.environ['HF_TOKEN'], verbose=False)
prompt = ("Replace the ornate forked staff with a plain thick broken tree branch: a simple straight log, slightly bent, "
          "rough grey-brown bark, one short broken side stub, blunt broken ends, no forks, no twigs, no carvings, no mushrooms. "
          "He still grips it diagonally across his body with both hands, its lower end reaching down near his right foot. "
          "Keep the bandaged man, fur mantle, leather armor, cloak, pose and framing exactly the same, plain grey background.")
t = time.time()
r = c.predict(input_image=handle_file(src), prompt=prompt, seed=seed, randomize_seed=False, guidance_scale=2.5, steps=28, api_name='/infer')
print('secs', round(time.time() - t))
p = r[0]; p = p.get('path') if isinstance(p, dict) else p
out = f'edit/kontext_s{seed}.png'; shutil.copy(p, out); print('saved', out)
