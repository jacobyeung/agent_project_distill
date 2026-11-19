"""Run each sealed bootstrap in a fresh interpreter without a model replacement."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

L=Path(__file__).resolve().parents[2]
records=[]
size=lambda p:sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
shim=Path(tempfile.mkdtemp(prefix='ee',dir=L/'work/tmp'))
adapter=shim/'python3'
adapter.write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B "$@"\n')
adapter.chmod(0o700)
for item in json.loads((L/'out/B3_KITS.json').read_text()):
    original=L/item['kit_path']
    root=L/'work/build3/entry_proofs'/original.name
    if root.exists():
        raise ValueError('Fresh-entry proof folder already exists')
    root.mkdir(parents=True)
    # Copy only the small sealed code/configuration kit; no data or weights.
    for source in original.rglob('*'):
        target=root/source.relative_to(original)
        if source.is_dir():
            target.mkdir(exist_ok=True)
        elif source.is_file():
            target.write_bytes(source.read_bytes())
            target.chmod(source.stat().st_mode & 0o777)
    target=root/'o/ee000001'
    if target.exists():
        raise ValueError('Fresh-entry proof requires a newly sealed kit')
    before=size(L/'work/tmp')
    if before>200000000 or size(L)>2000000000:raise ValueError('Proof storage guard')
    command=['bash','job.sh']
    result=subprocess.run(command,cwd=root,env={**os.environ,'PATH':str(shim)+':/usr/bin:/bin'},capture_output=True,text=True,timeout=180)
    log=L/'work/build3'/('entry_'+item['connector']+'.log')
    log.write_text(result.stdout+result.stderr)
    reason='Missing component evidence: init_m544'
    refusal=json.loads((root/'o/ee000007.json').read_text())
    if result.returncode==0 or refusal['reason']!=reason:
        raise ValueError('Unexpected production entry boundary: '+str(log))
    after=size(L/'work/tmp')
    if after>200000000 or size(L)>2000000000:raise ValueError('Proof storage guard')
    records.append(dict(connector=item['connector'],kit=item['kit_path'],proof_folder=str(root.relative_to(L)),command=command,
        exit_code=result.returncode,reason=reason,source_staged=True,stand_ins=[],
        model_loader_reached=False,log=str(log.relative_to(L)),tmp_before=before,tmp_after=after,
        runtime_adapter='python3 resolves to the mandated p1cpu interpreter with -I -s -B; no model stand-in is reached',
        refusal=refusal))
(L/'out/B3_FRESH_ENTRY_PROOF.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
