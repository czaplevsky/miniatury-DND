import os, shutil, sys, time
from gradio_client import Client, handle_file
img = sys.argv[1]; res = sys.argv[2] if len(sys.argv) > 2 else '1024'; tag = sys.argv[3] if len(sys.argv) > 3 else 't2'
c = Client('microsoft/TRELLIS.2', token=os.environ['HF_TOKEN'], verbose=False)
t = time.time()
try:
    c.predict(api_name='/start_session')
except Exception as e:
    print('start_session', e)
pre = c.predict(input=handle_file(img), api_name='/preprocess_image')
pp = pre.get('path') if isinstance(pre, dict) else pre
print('pre', round(time.time() - t)); shutil.copy(pp, f'ai/{tag}_pre.png')
c.predict(image=handle_file(pp), seed=7, resolution=res, api_name='/image_to_3d')
print('gen', round(time.time() - t))
r = c.predict(decimation_target=500000, texture_size=1024, api_name='/extract_glb')
print('glb', round(time.time() - t))
f = r[1] if r[1] else r[0]
f = f.get('path') if isinstance(f, dict) else f
shutil.copy(f, f'ai/{tag}.glb'); print('saved', f'ai/{tag}.glb')
