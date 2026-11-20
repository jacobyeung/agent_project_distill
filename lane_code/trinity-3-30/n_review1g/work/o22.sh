X=/project/community/jjyeung/okh7/x_22c714e1; J=${J:-173912}; O=$X/o/$J; TZ=UTC date +%TZ; df -h /project/community | tail -1
ls -la $O | head -80; ls -la $O/live 2>&1 | head -40; ls $O/rd0 2>&1 | head
sha256sum $O/k_* $O/live/* $O/*.json 2>/dev/null | cut -c1-200
J=$J nice -n 10 python3 -I -s -B - <<'PY'
import json,os,glob,hashlib
X='/project/community/jjyeung/okh7/x_22c714e1'; O=X+'/o/'+os.environ['J']
P=json.load(open(X+'/u/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))['sources']
for f in sorted(glob.glob(O+'/k_*receipt*.json')):
    h=hashlib.sha256(open(f,'rb').read()).hexdigest()
    if not h.startswith('655b953d'): continue
    v=json.load(open(f)); s=v.get('sources'); print('SELECTION',os.path.basename(f),h,'keys',list(v)[:20])
    if s is None: print('  no sources key'); continue
    for k in sorted(set(P)|set(s)):
        a=P.get(k,{}); b=s.get(k,{})
        print('  %-16s P %-9s %-24s %6s | N %-9s %-24s %6s %s'%(k,a.get('status'),a.get('reason'),a.get('retained',a.get('declared_rows')),b.get('status'),b.get('reason'),b.get('retained',b.get('declared_rows')),'' if a.get('declared_rows')==b.get('declared_rows') else 'DECLARED_DIFF'))
for n in ('chain.json',):
    p=O+'/'+n
    if os.path.isfile(p):
        c=json.load(open(p)); print('chain population',json.dumps(c.get('population'))[:800]); r=c['streams'].get('routing',{}); print('routing chain',{k:r.get(k) for k in ('status','rows_checked','refused_rows','database_rows','complete','database_key_set_sha256','checked_key_set_sha256')})
def grep(x,keys,p=''):
    if isinstance(x,dict):
        for k,y in x.items():
            if any(t in k for t in keys): print('   ',p+'/'+k,json.dumps(y)[:600])
            elif isinstance(y,(dict,list)): grep(y,keys,p+'/'+k)
    elif isinstance(x,list):
        for i,y in enumerate(x[:50]): grep(y,keys,p+'[%d]'%i)
for f in sorted(glob.glob(O+'/*.json'))+sorted(glob.glob(O+'/live/*.json')):
    try: v=json.load(open(f))
    except Exception as e: print('@@',f,'unreadable',type(e).__name__); continue
    print('@@',f[len(O)+1:],list(v)[:25] if isinstance(v,dict) else type(v).__name__)
    grep(v,('reader_filter','population','first_batch','protected','unresolved'))
PY
