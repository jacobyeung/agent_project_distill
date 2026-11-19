import json; from collections import Counter, defaultdict
D=json.load(open('/tmp/san_dircls.json'))
FLIP={'front':'back','back':'front','left':'right','right':'left'}
def tparts(t):
    if t and '-' in t: a,b=t.split('-'); return a,b
    if t=='back': return 'back',None
    return None,t
def mode(x):
    if x['right']: return 'right'
    if x['turn'] in ('turn','mixed') and not x['away']: return 'spurious_turn'
    if x['away'] and x['turn'] in ('keep','mixed'): return 'turn_omitted'
    if x['final'] is None: return 'unparsed'
    tf,tl=tparts(x['truth']); ff,fl=tparts(x['final'])
    if x['type']=='hard':
        if ff!=tf and fl!=tl: return 'both_wrong'
        return 'fb_wrong' if ff!=tf else 'lr_wrong'
    if x['type']=='medium':
        if x['truth']=='back': return 'missed_back'
        if x['final']=='back': return 'spurious_back'
        return 'lr_wrong'
    return 'lr_wrong'
rows=[]
for k,v in D.items():
    run,st,s=k.split('|')
    for x in v:
        rows.append((s,int(st),'away' if x['away'] else 'toward',x['type'],x,mode(x)))
def show(sets,cls,title):
    print('==',title)
    for s in sets:
      for ty in ('easy','medium','hard'):
        line=[]
        for st in (544,100,200,400):
            R=[r for r in rows if r[0]==s and r[1]==st and r[2]==cls and r[3]==ty]
            if not R: continue
            m=Counter(r[5] for r in R); n=len(R)
            back_ans=sum(1 for r in R if (r[4]['final'] or '').startswith('back')); back_true=sum(1 for r in R if str(r[4]['truth']).startswith('back'))
            line.append('%d: n%d wrong %d [%s] back-ans %d/true %d'%(st,n,n-m['right'],', '.join('%s %d'%(a,b) for a,b in sorted(m.items()) if a!='right'),back_ans,back_true))
        if line: print(' %s %s %s\n    '%(s,cls,ty)+'\n    '.join(line))
show(['forward'],'toward','forward (toward) twins')
show(['dev-S1','R0-dev'],'toward','direct sets, toward questions')
show(['R0-dev','away'],'away','away questions')
# openings on toward wrong vs right
print('== opening x outcome, toward questions')
for s in ('forward','dev-S1','R0-dev'):
    for st in (544,100,200,400):
        R=[r for r in rows if r[0]==s and r[1]==st and r[2]=='toward']
        if not R: continue
        c=defaultdict(lambda:[0,0])
        for r in R: c[(r[3],r[4]['open'])][0]+=1; c[(r[3],r[4]['open'])][1]+=int(not r[4]['right'])
        print(' ',s,st,'; '.join('%s/%s n%d wr%d'%(a,b,v[0],v[1]) for (a,b),v in sorted(c.items())))
