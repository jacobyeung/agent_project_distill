"""n_ops9: sustained upload rate per object from a per-attempt upload log (jsonl: time, name, http, range, error).
Usage: rate.py ATTEMPT_LOG SIZES   (SIZES: lines 'name bytes ...', e.g. a receipts list). Prints per part and per object
(object = name without .jNNN.partNN-of-04): bytes, first attempt, final 200/201, MB/s (10^6 B/s); WARN <84, QUESTION <55 (ORCH 0104Z)."""
import json,re,sys,collections
first={};fin={};att=collections.Counter();err=collections.Counter()
for l in open(sys.argv[1],errors='replace'):
  try: d=json.loads(l)
  except Exception: continue
  n=d.get('name'); t=d.get('time')
  if not n or t is None: continue
  first.setdefault(n,t); att[n]+=1
  if d.get('error'): err[n]+=1
  if d.get('http') in (200,201): fin[n]=t
size={}
for l in open(sys.argv[2]):
  p=l.split()
  if len(p)>=2 and p[0].startswith('q9/') and p[1].isdigit(): size[p[0]]=int(p[1])
obj=collections.defaultdict(list)
for n in sorted(first):
  o=re.sub(r'\.j\d+\.part\d\d-of-\d\d$','',n); obj[o].append(n)
  b=size.get(n); dt=(fin[n]-first[n]) if n in fin else None
  r=(b/dt/1e6) if (b and dt) else None
  print('part %s bytes=%s attempts=%d errors=%d wall=%s MBps=%s'%(n,b,att[n],err[n],None if dt is None else round(dt,2),None if r is None else round(r,1)))
for o,ns in sorted(obj.items()):
  done=[n for n in ns if n in fin]; b=sum(size.get(n,0) for n in done)
  if not done: print('object %s parts=%d done=0 (no final 200/201)'%(o,len(ns))); continue
  dt=max(fin[n] for n in done)-min(first[n] for n in ns); r=b/dt/1e6 if dt>0 else None
  flag='' if r is None or b<1e9 else (' QUESTION<55' if r<55 else (' WARN<84' if r<84 else ''))
  print('object %s parts=%d done=%d bytes=%d wall=%.2f MBps=%s%s'%(o,len(ns),len(done),b,dt,None if r is None else round(r,1),flag))
