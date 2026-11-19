"""Use pinned fixture metadata to locate the next unchanged native boundary."""
from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
view=J.load(D/'VIEW.json');v=view['variables'];node=Path(v['Q_ROOT']);ns=v['Q_NS']
args=J.load(D/'proofs/view/after.json')
paths={x['sha256']:x['local_path'] for x in J.load(B/'UPLOADS.json')['files'] if Path(x['local_path']).is_relative_to(L)}
seen=set();unavailable=[]
def collect(value):
    if isinstance(value,dict):
        h=value.get('sha256');raw=value.get('path')
        if isinstance(h,str) and isinstance(raw,str) and h not in seen:
            seen.add(h);p=Path(paths.get(h,raw))
            if not p.is_relative_to(L) and '/work/' in raw:p=L/'work'/raw.split('/work/',1)[1]
            if p.is_relative_to(L) and p.is_file():
                paths[h]=str(p)
                if p.suffix=='.json' and p.stat().st_size<4_000_000:
                    try:collect(J.load(p))
                    except (ValueError,UnicodeDecodeError):pass
            else:unavailable.append(dict(path=raw,sha256=h))
        for item in value.values():collect(item)
    elif isinstance(value,list):
        for item in value:collect(item)
request=J.load(B/'proofs/capacity/400/request.json');collect(request)
request['_paths']=paths;request['memory_gib']=16
J.write(node/'native.json',request)
command=args+[sys.executable,'-s','-B',str(K/'b/a.py'),'q',ns+'/p2',ns+'/native.json']
p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
result=J.load(node/'p2/q/RESULT.json') if (node/'p2/q/RESULT.json').exists() else None
record=dict(command=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,result=result,
    request='work/build21/proofs/capacity/400/request.json',stand_ins='Existing pinned synthetic fixture metadata; production GPU guard checked independently in VIEW.json.',
    aliases=len(paths),unavailable=unavailable,tree_changes=False)
J.write(D/'NATIVE_VIEW.json',record)
print(json.dumps(dict(returncode=p.returncode,result=result,stderr=p.stderr,unavailable=len(unavailable)),indent=2))
assert result and result.get('refusal')=='ValueError:R1_PROOF_FRAME_HOST_REQUIRED'
