import math
from PIL import Image, ImageDraw, ImageFont
def png(panels, path, title=''):
    W, PH, L, R = 1000, 170, 210, 25
    H = PH*len(panels)+80
    x0, x1 = -3.0, 3.0
    X = lambda v: L + (min(max(v,x0),x1)-x0)/(x1-x0)*(W-L-R)
    col = {'cm':(31,119,180),'m':(44,160,44),'in':(255,127,14),'ft':(214,39,40)}
    im = Image.new('RGB',(W,H),'white'); d = ImageDraw.Draw(im)
    try: f = ImageFont.load_default(size=13)
    except TypeError: f = ImageFont.load_default()
    d.text((10,8), title, fill='black', font=f)
    for i,(t,pts) in enumerate(panels):
        y0 = 40+i*PH; base = y0+PH-25
        d.text((8,y0+PH//2-10), t, fill='black', font=f)
        d.line([(L,base),(W-R,base)], fill=(150,150,150))
        for v,lab in ((0,'1x'),(math.log2(0.3048),'0.30x m-for-ft'),(math.log2(2.54),'2.54x cm-for-in'),(1,'2x'),(-1,'0.5x')):
            for yy in range(y0+5, base, 6): d.line([(X(v),yy),(X(v),yy+3)], fill=(190,190,190))
            if i==0: d.text((X(v)+2,y0-14), lab, fill=(100,100,100), font=f)
        stack = {}
        for v,u,s in sorted(pts):
            b = round(X(v)/7); stack[b] = stack.get(b,0)+1
            y = base-5-(stack[b]-1)*6; x = X(v); c = col.get(u,(0,0,0))
            if s: d.ellipse([x-4,y-4,x+4,y+4], outline=c, width=2)
            else: d.ellipse([x-2.5,y-2.5,x+2.5,y+2.5], fill=c)
    for t in range(-3,4): d.text((X(t)-10,H-38), '%gx'%(2**t), fill='black', font=f)
    d.text((L,H-20), 'prediction / truth (log2 axis); colour = asked unit: cm blue, m green, in orange, ft red; ring = unit slip', fill='black', font=f)
    im.save(path)
