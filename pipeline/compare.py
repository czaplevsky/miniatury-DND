"""v2 vs v3 comparison image. usage: compare.py V3_FULL_SHEET V3_CLOSE_SHEET OUT.png"""
import sys
from PIL import Image, ImageDraw
v2a = Image.open('/home/user/DASHBOARD/dnd-mini/renders/v2_widoki.png').convert('RGB')
v2b = Image.open('/home/user/DASHBOARD/dnd-mini/renders/v2_zblizenie.png').convert('RGB')
v3a = Image.open(sys.argv[1]).convert('RGB'); v3b = Image.open(sys.argv[2]).convert('RGB')
W = 2000
rows = []
for lab, im in (('v2', v2a), ('v3', v3a), ('v2 close-up', v2b), ('v3 close-up', v3b)):
    im = im.resize((W, int(im.height * W / im.width)))
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 190, 44), fill=(20, 20, 20)); d.text((10, 10), lab, fill=(255, 220, 90), font_size=30)
    rows.append(im)
out = Image.new('RGB', (W, sum(r.height for r in rows)))
y = 0
for r in rows:
    out.paste(r, (0, y)); y += r.height
out.save(sys.argv[3]); print(out.size)
