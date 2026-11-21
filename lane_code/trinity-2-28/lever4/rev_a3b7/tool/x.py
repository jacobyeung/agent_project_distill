import sys,os,tarfile,json,re,io
OLD,NEW='a4282fee306d6','a3b73b53d92a7'
def norm(b,tok):
    return b.replace(tok.encode(),b'TOKEN')
def walk(root,tok,out):
    # returns dict path->bytes (normalized), recursing
    pass
def expand(name,data,tok,res,depth=0):
    if depth>6: res[name]=norm(data,tok);return
    isz=data[:2]==b'\x1f\x8b' 
    if isz or (len(data)>512 and data[257:262]==b'ustar'):
        try:
            tf=tarfile.open(fileobj=io.BytesIO(data));mem=tf.getmembers()
            for m in mem:
                if m.isfile():
                    expand(name.replace(tok,'TOKEN')+'!'+m.name.replace(tok,'TOKEN'),tf.extractfile(m).read(),tok,res,depth+1)
                else: res[name.replace(tok,'TOKEN')+'!'+m.name.replace(tok,'TOKEN')+'#'+m.type.decode() if isinstance(m.type,bytes) else 'd']=b''
            return
        except Exception as e: pass
    # JSON a0 envelope
    try:
        j=json.loads(data)
        def dec(o):
            if isinstance(o,dict):
                if set(o)=={'a0'} and isinstance(o['a0'],str):
                    try:return {'a0dec':bytes.fromhex(o['a0']).decode()}
                    except Exception:return o
                return {k:dec(v) for k,v in o.items()}
            if isinstance(o,list):return [dec(v) for v in o]
            return o
        d=dec(j)
        if d!=j:
            res[name.replace(tok,'TOKEN')]=norm(json.dumps(d,sort_keys=True,indent=1).encode(),tok);return
    except Exception:pass
    # hex blobs in text
    try:
        t=data.decode()
        def h(m):
            try:return '<HEX:'+bytes.fromhex(m.group(0)).decode()+'>'
            except Exception:return m.group(0)
        t2=re.sub(r'[0-9a-f]{200,}',h,t)
        res[name.replace(tok,'TOKEN')]=norm(t2.encode(),tok);return
    except Exception:pass
    res[name.replace(tok,'TOKEN')]=norm(data,tok)
def load(p,tok):
    r={};expand('ROOT',open(p,'rb').read(),tok,r);return r
a=load(sys.argv[1],OLD);b=load(sys.argv[2],NEW)
print(len(a),len(b))
import difflib
for k in sorted(set(a)|set(b)):
    if k not in a:print('ONLY_NEW',k);continue
    if k not in b:print('ONLY_OLD',k);continue
    if a[k]!=b[k]:
        print('DIFF',k,len(a[k]),len(b[k]))
        for l in list(difflib.unified_diff(a[k].decode('latin1').splitlines(),b[k].decode('latin1').splitlines(),lineterm='',n=0))[:12]:print('   ',l[:300])
