"""Step 1: exaggerate bandages on the (already branch-swapped) front view.
usage: python edit_front.py {qwen|kontext} SEED SRC OUT"""
import os, shutil, sys, time
from gradio_client import Client, handle_file
mode, seed, src, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
PROMPTS = {"a": ("Make every bandage on the man thick, chunky and clearly layered like a sculpted tabletop miniature: "
          "wide overlapping cloth strips with deep dark gaps between strips on his head, face, arms, abdomen, thighs and shins; "
          "eyes still visible through a gap in the head wrappings. Keep exactly the same pose, the same plain thick broken "
          "tree branch held diagonally in both hands, the fur mantle, leather armor with crossed straps, belt pouches, "
          "long tattered cloak and wrapped boots. Full body head to feet, plain light grey background."),
 "b": ("Sculpt the bandage wrappings like a tabletop miniature: the head, face, forearms, belly and legs are wrapped in "
       "thick distinct cloth strips, each strip raised with a dark deep groove between neighbouring strips, strips crossing "
       "diagonally around the head with a narrow gap for the eyes. Do not change anything else: same pose, same broken "
       "branch held in both hands, same armor, fur mantle and cloak, plain light grey background.")}
PROMPT = PROMPTS[os.environ.get('PV', 'b')]
g_scale = float(os.environ.get('GS', '2.5'))
t = time.time()
if mode == 'qwen':
    c = Client('linoyts/Qwen-Image-Edit-2511-Fast', token=os.environ['HF_TOKEN'], verbose=False)
    r = c.predict(images=[{"image": handle_file(src)}], prompt=PROMPT, seed=seed, randomize_seed=False,
                  true_guidance_scale=1.0, num_inference_steps=4, height=1248, width=832, rewrite_prompt=False, api_name='/infer')
    g = r[0]; p = g[0]['image'] if isinstance(g, list) else g
else:
    c = Client('black-forest-labs/FLUX.1-Kontext-Dev', token=os.environ['HF_TOKEN'], verbose=False)
    r = c.predict(input_image=handle_file(src), prompt=PROMPT, seed=seed, randomize_seed=False, guidance_scale=g_scale, steps=28, api_name='/infer')
    p = r[0]
p = p.get('path') if isinstance(p, dict) else p
shutil.copy(p, out); print('secs', round(time.time() - t), 'saved', out)
