"""Refresh only locally generated tiny artifacts, then judge the final sealed source."""
from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
import torch
from eat1.artifact import write_manifest
from eat1.adapters.c8r_tiny import ProgramPolicy
from eat1.adapters.build10_manifest import entries
sizes=[]
def temporary_size():
    size=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    assert size<=200_000_000,'Temporary storage cap reached'
    return size
def record_size(name,before):
    sizes.append(dict(reader=name,before=before,after=temporary_size()))
    (B/'proofs/eat1/TEMP_SIZES.json').write_text(json.dumps(sizes,indent=2)+'\n')
for name in ('gf1','c8r'):
    before=temporary_size()
    if name=='gf1':
        from tests.test_gf1 import fixture
        from eat1.adapters.gf1_tiny import MODULES
        model,_,_=fixture();model.trace_program_version=None
        g=torch.Generator().manual_seed(5)
        with torch.no_grad():
            for p in model.auxiliary_heads.gf1.parameters():
                if p.is_floating_point():p.add_(.05*torch.randn(p.shape,generator=g))
    else:
        from tests.test_batched_routed_decode import fixture
        from eat1.adapters.c8r_tiny import MODULES
        model,_,_=fixture()
    model.eat1_program_policy=ProgramPolicy()
    art=B/'proofs/eat1'/name/'reader/artifact';art.mkdir(parents=True,exist_ok=True)
    torch.save(model.state_dict(),art/'weights.pt')
    files,modules=entries(model,T,art,MODULES)
    write_manifest(art/'ARTIFACT.json',art,files,modules)
    with (B/'proofs'/name/'console.log').open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'monitor_eat10.py'),name],stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise SystemExit(result.returncode)
    record_size(name,before)
    print(name+' final EAT-1 complete',flush=True)
before=temporary_size()
result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'launch_b04_local10.py')])
if result.returncode:raise SystemExit(result.returncode)
record_size('b04',before)
print('b04 final EAT-1 complete',flush=True)
