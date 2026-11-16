import json, random, re
from collections import defaultdict, Counter
P='scratch/jjyeung/orch_n30/native_r2/work/parent'
b=json.load(open(P+'/r5/merge_results/B2048.json'))
par={r['key']:r for r in b['rows']}
assert len(par)==len(b['rows'])
R=json.load(open('R1_distroom.json'))
nat={a:{r['key']:r for r in R['arms'][a]} for a in ('unflagged','scripted')}
tasks={('devrows:'+x['id']):x for x in map(json.loads,open(P+'/r3/TASKS.jsonl'))}
keys=sorted(nat['unflagged'])
assert set(keys)==set(nat['scripted']) and len(keys)==186
def lab(t): return 'released_answer' if t['stratum']=='primary' else 'answer'
def unit(q):
    m=re.findall(r'\b(square\s+)?(millimeters?|millimetres?|centimeters?|centimetres?|meters?|metres?|inches|inch|feet|foot)\b',q,re.I)
    if not m: return 'unknown'
    s,v=m[-1]; v=v.lower().replace('metre','meter')
    u='mm' if v.startswith('milli') else 'cm' if v.startswith('centi') else 'm' if v.startswith('meter') else 'in' if v.startswith('inch') else 'ft'
    return ('sq ' if s else '')+u
rows=[]
for k in keys:
    t=tasks[k]; p=par[k]; n=nat['unflagged'][k]; s=nat['scripted'][k]
    assert p['question_type']==n['question_type']==t['question_type']==s['question_type'], k
    assert p['room']==n['room']==t['room']==s['room'], k
    assert p['stratum']==n['stratum']==t['stratum'], k
    L=lab(t)
    rows.append(dict(k=k,qt=t['question_type'],room=t['room'],u=unit(t['question']),stratum=t['stratum'],
      p=p['scores'][L],n=n['scores'][L],s=s['scores'][L],pcap=p['capped'],pun=p['unanswered'],ppa=p['unparsed'],
      geo=bool(n.get('geometry_refusal')), nqu=n['question_unit']['unit']))
print('strata',Counter(r['stratum'] for r in rows))
print('parent flags', sum(r['pcap'] for r in rows), sum(r['pun'] for r in rows), sum(r['ppa'] for r in rows))
def boot(rs,draws=50000,seed=20261115):
    by=defaultdict(lambda:[0,0.,0.])
    for r in rs:
        a=by[r['room']]; a[0]+=1; a[1]+=r['n']-r['p']; a[2]+=r['s']-r['p']
    cl=[by[x] for x in sorted(by)]; rnd=random.Random(seed); v=[[],[]]
    for _ in range(draws):
        ch=rnd.choices(cl,k=len(cl)); d=sum(c[0] for c in ch)
        for j in (0,1): v[j].append(100*sum(c[j+1] for c in ch)/d)
    def q(xs,p):
        xs.sort(); pos=(len(xs)-1)*p; lo=int(pos); return xs[lo]+(xs[min(lo+1,len(xs)-1)]-xs[lo])*(pos-lo)
    return [[q(v[j],.025),q(v[j],.975)] for j in (0,1)]
def m(rs,f): return 100*sum(r[f] for r in rs)/len(rs)
out={}
for qt in ('object_abs_distance','room_size_estimation'):
    T=[r for r in rows if r['qt']==qt]
    groups={'all':T}
    for u in sorted({r['u'] for r in T}): groups[u]=[r for r in T if r['u']==u]
    groups['non_metre']=[r for r in T if r['u'] not in ('m','sq m')]
    for g,rs in groups.items():
        bi=boot(rs)
        line=dict(n=len(rs),rooms=len({r['room'] for r in rs}),parent=m(rs,'p'),native=m(rs,'n'),scripted=m(rs,'s'),
          nat_minus_par=m(rs,'n')-m(rs,'p'),scr_minus_par=m(rs,'s')-m(rs,'p'),ci_nat=bi[0],ci_scr=bi[1],
          geo=sum(r['geo'] for r in rs))
        out[qt+'/'+g]=line
        print(qt[:12],g.ljust(10),' '.join(f'{k}={v:.4f}' if isinstance(v,float) else f'{k}={v}' for k,v in line.items() if not k.startswith('ci')),
              'CInat=[%.2f,%.2f] CIscr=[%.2f,%.2f]'%(*bi[0],*bi[1]))
json.dump(dict(out=out,rows=rows),open('../RECOMPUTE.json','w'),indent=1)
