X=/project/community/jjyeung/okh7/x_22c714e1; J=${J:-173964}; O=$X/o/$J; TZ=UTC date +%TZ; df -h /project/community < /dev/null | tail -1
ls -la $O < /dev/null | head -40; find $O -type f < /dev/null | sort | head -200 | while read f; do echo "$(stat -c %s "$f") ${f#$O/}"; done
nice -n 10 python3 -I -s -B - <<'PY'
import json,gzip,hashlib,os,glob
X='/project/community/jjyeung/okh7/x_22c714e1'; O=X+'/o/173964'
def raw(p):
    b=open(p,'rb').read()
    return gzip.decompress(b) if p.endswith('.gz') else b
def shape(v,d=0,maxd=3):
    if isinstance(v,dict):
        if d>=maxd: return '{%d keys}'%len(v)
        items=list(v.items())
        s='{'+', '.join('%s: %s'%(k,shape(x,d+1,maxd)) for k,x in items[:25])
        return s+(', ...+%d'%(len(items)-25) if len(items)>25 else '')+'}'
    if isinstance(v,list):
        return '[%d x %s]'%(len(v),shape(v[0],d+1,maxd) if v else '')
    s=json.dumps(v); return s if len(s)<80 else s[:77]+'...'
jp=O+'/j7.json'
if os.path.exists(jp):
    j=json.load(open(jp)); print('j7.json rc',j.get('returncode'),'kit',j.get('kit_sha256'),'missing',j.get('missing'),'bytes',j.get('bytes'))
    bad=0
    for r in j['files']:
        p=O+'/'+r['name']
        if not os.path.exists(p): print('  ABSENT',r['name']); bad+=1; continue
        b=open(p,'rb').read(); ok=hashlib.sha256(b).hexdigest()==r['stored_sha256'] and hashlib.sha256(raw(p)).hexdigest()==r['sha256']
        if not ok: bad+=1; print('  HASH_DIFF',r['name'])
        print('  %-22s %-40s %9d %s'%(r['name'],r['source'],r['bytes'],r['sha256'][:8]))
    print('j7 files',len(j['files']),'bad',bad)
for p in sorted(glob.glob(O+'/**/*',recursive=True)):
    if not os.path.isfile(p) or p.endswith(('j2.log','j2.err','.part','j7.json')): continue
    try: v=json.loads(raw(p))
    except Exception as e: print('@@',p[len(O)+1:],'not json',type(e).__name__,os.path.getsize(p)); continue
    print('@@',p[len(O)+1:],shape(v)[:2500])
PY
