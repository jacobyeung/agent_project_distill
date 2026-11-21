echo "@@ATT"; timeout 25 nice -n 19 python3 -B - "$Q" "/project/community/jjyeung/okh7/x_22c714e1/o/$J/live" <<'PY' 2>&1 | head -40 | cut -c1-400
import os,sys,json,re
seen=set()
for root in sys.argv[1:]:
  if not os.path.isdir(root):continue
  base=root.rstrip('/').count('/')
  for d,ds,fs in os.walk(root):
    if d.count('/')-base>=3:ds[:]=[]
    for f in fs:
      p=os.path.join(d,f)
      try:
        sz=os.path.getsize(p)
        if sz==0 or sz>60e6 or f.endswith(('.tar','.tgz')):continue
        h=open(p,'rb').read(4096)
      except Exception:continue
      if b'"http"' not in h or b'"name"' not in h:continue
      ob={};n=0
      for l in open(p,errors='replace'):
        try:r=json.loads(l)
        except Exception:continue
        nm=r.get('name');t=r.get('time')
        if not isinstance(nm,str) or not isinstance(t,(int,float)):continue
        n+=1;m=re.match(r'^(.*?)\.j(\d+)\.part(\d\d)-of-\d\d$',nm)
        if not m:continue
        o=ob.setdefault(m.group(1),{'p':{},'att':0,'err':0})
        q=o['p'].setdefault(m.group(3),[t,None]);o['att']+=1;o['err']+=bool(r.get('error'))
        if r.get('http') in (200,201):q[1]=t
      key=(sz,n)
      if key in seen:continue
      seen.add(key);print('@@ATTF',p.replace(sys.argv[1],'$Q'),sz,n)
      for k,o in sorted(ob.items()):
        ps=o['p'];dn={a:b for a,b in ps.items() if b[1]}
        print('@@ATTO',json.dumps({'f':f,'obj':k,'parts':len(ps),'done':len(dn),'first':min(v[0] for v in ps.values()),'last_done':max([v[1] for v in dn.values()] or [None]) if dn else None,'att':o['att'],'err':o['err'],'part_walls':{a:round(b[1]-b[0],2) for a,b in dn.items()}}))
PY
