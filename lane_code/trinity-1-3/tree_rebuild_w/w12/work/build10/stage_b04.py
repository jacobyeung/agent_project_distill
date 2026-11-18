from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10'
src=N/'work/design/b04_v7/b04_e2ehook';stage=B/'b04_stage'
records=[]
for name in ('e2e_reader','eat1_adapter','heads/scale','heads/selector'):
    for p in (src/name).rglob('*.py'):
        if 'work' in p.relative_to(src/name).parts:continue
        target=stage/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(p.read_bytes())
        records.append(dict(source=str(p),target=str(target),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
path=stage/'eat1_adapter/b04_tiny.py';old=path.read_text()
data=N/'work/design/b04_inputs/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook'
new=old.replace("DATA = Path('/scratch/jjyeung/orch_n30/b04_e2ehook')",f'DATA = Path({str(data)!r})')
new=new.replace("TREE = '/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/wm/work/base/tree_b01ce449'",f'TREE = {str(L/"work/tree_r1")!r}')
new=new.replace("K1 = Path('/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2/3912542710353e09')",f'K1 = Path({str(N/"work/design/b04_inputs/scratch/jjyeung/k1/run_tower_sam_2/3912542710353e09")!r})')
path.write_text(new)
changed=[dict(file=str(path.relative_to(L)),line=i,before=a,after=b) for i,(a,b) in enumerate(zip(old.splitlines(),new.splitlines()),1) if a!=b]
inputs=[]
for line in (N/'work/design/b04_inputs/SHA256SUMS.txt').read_text().splitlines():
    sha,name=line.split(None,1);p=N/'work/design/b04_inputs'/name
    if p.name in ('SHA256SUMS.txt','fetch.err'):continue
    inputs.append(dict(path=str(p),expected_sha256=sha,bytes=p.stat().st_size))
(B/'B04_STAGING.json').write_text(json.dumps(dict(code=records,changed_lines=changed,inputs=inputs,
    adapter='b04 eat1_adapter/b04_tiny.py; harness adapter differs and is not used'),indent=2)+'\n')
print(json.dumps(dict(files=len(records),changed_lines=changed,input_bytes=sum(v['bytes'] for v in inputs))))
