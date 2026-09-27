import sys
from PIL import Image
d=sys.argv[1]; names=sys.argv[2:] or ['front','front34','side','back']
ims=[Image.open(f'{d}/{n}.png').convert('RGB') for n in names]
c=Image.new('RGB',(sum(i.width for i in ims),ims[0].height))
x=0
for i in ims: c.paste(i,(x,0)); x+=i.width
c.save(f'{d}/sheet.png')
