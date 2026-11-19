from pathlib import Path
import base64,collections,datetime,hashlib,json,shutil,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d';A=L/'attic/build21d'
D.mkdir(exist_ok=True);A.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from launch_r2.build import bad_string
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
for n in ('naming21.py','joblib.py','OPERATOR.md','PACKAGE_MANIFEST.json','DELIVERY.json'):
    if not (A/n).exists():shutil.copyfile(B/n,A/n)
kit=B/'kits/q';files={str(p.relative_to(kit)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in kit.rglob('*') if p.is_file()}
base=L/'out/tree_rebuild_b21c_6f5e6cc2.tar'
start=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()),
    base=dict(path=str(base.relative_to(L)),bytes=base.stat().st_size,sha256=sha(base)),kit_files=files,
    kit_seal=sha(kit/'SHA256SUMS.txt'),tree=json.loads((L/'out/TREE_SEAL.json').read_text()))
assert start['base']['sha256']=='8c5634344f81355f93bbed8ee3ba981c79ef3cf5b8a10c53adc03190d777d9e8'
write(D/'START.json',start)
wh=json.loads((kit/'b/wh.json').read_text());bad=[];docs={}
def visit(v,doc,parts=()):
    if isinstance(v,dict):
        if 'payload' in v and 'sha256' in v and set(v)<= {'payload','sha256','encoding'}:
            raw=base64.b64decode(v['payload']);assert hashlib.sha256(raw).hexdigest()==v['sha256']
            if doc=='k/j.json':return
            return visit(json.loads(raw),doc,parts+('@content',))
        for k,x in v.items():
            if bad_string(k,wh):bad.append(dict(doc=doc,path=list(parts+(k,)),kind='key',value=k))
            visit(x,doc,parts+(k,))
    elif isinstance(v,list):
        for i,x in enumerate(v):visit(x,doc,parts+(str(i),))
    elif isinstance(v,str) and bad_string(v,wh):bad.append(dict(doc=doc,path=list(parts),kind='value',value=v))
for p in sorted(kit.rglob('*.json')):
    doc=str(p.relative_to(kit));v=json.loads(p.read_text());visit(v,doc)
    if isinstance(v,dict) and 'payload' in v and doc!='k/j.json':v=json.loads(base64.b64decode(v['payload']))
    docs[doc]=list(v) if isinstance(v,dict) else type(v).__name__
write(D/'IDENTIFIERS.json',dict(documents=docs,identifiers=bad))
summary=collections.Counter((x['doc'],x['path'][1] if len(x['path'])>1 else '',x['kind']) for x in bad)
print(json.dumps(dict(kit_seal=start['kit_seal'],workspace_bytes=start['workspace_bytes'],documents=docs,counts=[dict(doc=k[0],field=k[1],kind=k[2],count=v) for k,v in summary.items()]),indent=2))
