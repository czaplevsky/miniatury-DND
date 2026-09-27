import sys, trimesh, numpy as np, matplotlib
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
m = trimesh.load(src)
st=0.08
xs=np.arange(-12,12,st); zs=np.arange(39.5,2.5,-st)
X,Z=np.meshgrid(xs,zs)
O=np.stack([X.ravel(),np.full(X.size,-30.0),Z.ravel()],1); D=np.tile([0,1,0],(X.size,1))
loc,ri,ti=m.ray.intersects_location(O,D,multiple_hits=False)
dep=np.full(X.size,np.nan); dep[ri]=loc[:,1]; dep=dep.reshape(X.shape)
np.save(out.replace('.png','.npy'),dep)
v=np.clip((4-dep)/12,0,1); v[np.isnan(dep)]=0
rgb=(matplotlib.colormaps['turbo'](v)[:,:,:3]*255).astype(np.uint8); rgb[np.isnan(dep)]=40
im=Image.fromarray(rgb).resize((X.shape[1]*3,X.shape[0]*3),Image.NEAREST); d=ImageDraw.Draw(im)
k=3/st
for mm in range(-12,13,1):
    x=(mm+12)*k; d.line([(x,0),(x,im.height)],fill=(255,255,255) if mm%5==0 else (70,70,70)); 
    if mm%2==0: d.text((x+2,2),str(mm),fill=(255,255,255))
for z in range(4,40,1):
    y=(39.5-z)*k; d.line([(0,y),(im.width,y)],fill=(255,255,255) if z%5==0 else (70,70,70))
    if z%2==0: d.text((2,y+1),str(z),fill=(255,255,255))
im.save(out); print(im.size)
