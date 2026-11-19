import sys, json, re, statistics as st
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
def mra(p,g):
    if g==0: return 0.0
    e=abs(p-g)/abs(g); return sum(e<=1-t/100+1e-12 for t in range(50,100,5))/10
R=K.routed(544, types=['camera_displacement','camera_rotation','camera_movement_direction'])
print(len(R)); r=R[0]; print(r['question'][:300]); print(r['calls'][:2]); print(r['gt'], r['answer'], r['score'])
for t in ('camera_displacement','camera_rotation'):
    rows=[]
    for r in R:
        if r['type']!=t or not r['calls']: continue
        c=r['calls'][-1]; m=re.search(r'from=(\d+) to=(\d+)', c['call'] or '')
        v=re.search(r'(-?[\d.]+)', (c['response'] or '').split(':')[-1]) if c['response'] else None
        try: g=float(r['gt']); a=float(r['answer'])
        except Exception: continue
        if not m: continue
        rows.append(dict(i=int(m.group(1)), j=int(m.group(2)), g=g, a=a, s=r['score'], resp=c['response']))
    print('==', t, len(rows), 'score %.1f' % (100*sum(x['s'] for x in rows)/len(rows)))
    print('  example response:', rows[0]['resp'][:200].replace('\n',' | '))
    def tab(key,label):
        b={}
        for x in rows: b.setdefault(key(x),[]).append(x)
        print(' --',label)
        for k in sorted(b):
            v=b[k]; print('   %-10s n=%3d MRA=%5.1f med|err|=%.3f med ratio=%.2f over=%d' % (k,len(v),100*sum(x['s'] for x in v)/len(v), st.median(abs(x['a']-x['g']) for x in v), st.median((x['a']/x['g']) if x['g'] else 9 for x in v), sum(x['a']>x['g'] for x in v)))
    tab(lambda x: '%02d-%02d'%((0,1) if abs(x['j']-x['i'])<=1 else (2,3) if abs(x['j']-x['i'])<=3 else (4,7) if abs(x['j']-x['i'])<=7 else (8,15) if abs(x['j']-x['i'])<=15 else (16,31)), 'frame gap |j-i|')
    if t=='camera_displacement':
        tab(lambda x: 'a<=0.25' if x['g']<=.25 else 'b<=0.5' if x['g']<=.5 else 'c<=1' if x['g']<=1 else 'd<=2' if x['g']<=2 else 'e>2', 'truth band (m)')
    else:
        tab(lambda x: 'a<=10' if x['g']<=10 else 'b<=20' if x['g']<=20 else 'c<=45' if x['g']<=45 else 'd<=90' if x['g']<=90 else 'e>90', 'truth band (deg)')
    ae=[abs(x['a']-x['g']) for x in rows]; print('  abs error median %.3f p75 %.3f p90 %.3f' % (st.median(ae), sorted(ae)[int(.75*len(ae))], sorted(ae)[int(.9*len(ae))]))
    json.dump(rows, open('camdiag_%s.json'%t,'w'))
