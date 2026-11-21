X=/project/community/jjyeung/okh7/x_22c714e1
ls $X/o | tr '\n' ' '; echo
ls -la $X/o/173964 2>&1 | head -30
python3 -I - <<'PY'
import json,hashlib,tarfile,os,base64
X='/project/community/jjyeung/okh7/x_22c714e1'
def rd(p):
    v=json.load(open(p))
    if isinstance(v,dict) and v.get('encoding')=='base64-json': v=json.loads(base64.b64decode(v['payload']))
    return v
for j in ('173964','174085'):
    for n in ('q0.json','RESULT.json','r0.json'):
        p=f'{X}/o/{j}/{n}'
        if os.path.isfile(p):
            try:
                d=rd(p); print(j,n,{k:(str(v)[:400] if k not in ('staged','room_certification','augmented_room_audit') else '...') for k,v in d.items()})
            except Exception as e: print(j,n,'ERR',e)
        else: print(j,n,'absent')
want='cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7'
m=None
for cand in (f'{X}/u/{want}','/project/community/jjyeung/okh7/h_6ed2c7aa/m400/'+want):
    if os.path.isfile(cand): m=open(cand,'rb').read(); print('manifest at',cand)
if m is None:
    t='/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar'
    print('s.tar bytes',os.path.getsize(t))
    with tarfile.open(t) as tf:
        for mem in tf:
            if mem.isfile() and mem.size<2_000_000:
                raw=tf.extractfile(mem).read()
                if hashlib.sha256(raw).hexdigest()==want: m=raw; print('manifest member',mem.name); break
if m is not None:
    d=json.loads(m); print('MANIFEST keys',sorted(d)); print('root',d['root']); print('kind',d.get('kind'),'base_identity',d.get('base_identity'),'schema',d.get('schema'))
    print('MANIFEST_JSON_BEGIN'); print(json.dumps({k:v for k,v in d.items()},sort_keys=True)); print('MANIFEST_JSON_END')
    pool='/project/community/jjyeung/okh7'
    for name,h in sorted(d['files'].items()):
        loc=[c for c in (f'{X}/u/{h}',) if os.path.isfile(c)]
        print(' ',name,h[:16],(os.path.getsize(loc[0]) if loc else 'not in X/u'))
PY
