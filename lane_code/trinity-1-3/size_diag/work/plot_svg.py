import json, math, sys
# panels: list of (title, [(log2ratio, unit, slip)])
def svg(panels, path):
    W, PH, L, R = 900, 150, 170, 20
    H = PH*len(panels)+60
    x0, x1 = -3.0, 3.0
    X = lambda v: L + (min(max(v,x0),x1)-x0)/(x1-x0)*(W-L-R)
    col = {'cm':'#1f77b4','m':'#2ca02c','in':'#ff7f0e','ft':'#d62728'}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">', f'<rect width="{W}" height="{H}" fill="white"/>']
    for i,(title,pts) in enumerate(panels):
        y0 = 30+i*PH
        o.append(f'<text x="5" y="{y0+PH/2}" >{title}</text>')
        o.append(f'<line x1="{L}" y1="{y0+PH-20}" x2="{W-R}" y2="{y0+PH-20}" stroke="#999"/>')
        for v,lab in ((0,'1x'),(math.log2(0.3048),'0.30x (m for ft)'),(math.log2(2.54),'2.54x (cm for in)'),(1,'2x'),(-1,'0.5x')):
            o.append(f'<line x1="{X(v):.1f}" y1="{y0+5}" x2="{X(v):.1f}" y2="{y0+PH-20}" stroke="#bbb" stroke-dasharray="3,3"/>')
            if i==0: o.append(f'<text x="{X(v)+2:.1f}" y="{y0-5}" font-size="10" fill="#666">{lab}</text>')
        stack = {}
        for v,u,s in sorted(pts):
            b = round(X(v)/6); stack[b] = stack.get(b,0)+1
            y = y0+PH-24-(stack[b]-1)*5
            c = col.get(u,'#000')
            if s: o.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{c}" stroke-width="1.5"/>')
            else: o.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="2.2" fill="{c}"/>')
    for t in range(-3,4):
        o.append(f'<text x="{X(t)-8:.1f}" y="{H-12}" font-size="11">{2**t:g}x</text>')
    o.append(f'<text x="{L}" y="{H-0}" font-size="11">prediction / truth (log scale); colour = asked unit (cm blue, m green, in orange, ft red); ring = unit slip</text>')
    o.append('</svg>'); open(path,'w').write('\n'.join(o))
