"""Run the standalone proofs serially after frozen-package qualification."""
from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';out=L/'work/build12/proofs/final_chain';out.mkdir(exist_ok=True)
assert (L/'work/build12/proofs/fixture_requalification/RESUME_RECEIPT.json').is_file()
temp=L/'work/tmp/g8_available';prior=L/'work/tmp/g8_available_compacted'
if temp.exists():
    assert not prior.exists();temp.rename(prior)
py=[sys.executable,'-I','-s','-B'];steps=[]
def temp_size():
    size=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
    assert size<=200_000_000,'Temporary storage cap reached'
    return size
def run(name,script,*args):
    print('Starting '+name,flush=True)
    row=dict(name=name,status='running',tmp_before=temp_size());steps.append(row)
    (B/'FINAL_PROOFS.json').write_text(json.dumps(steps,indent=2)+'\n')
    status=json.loads((B/'STEPS.json').read_text())
    status['FINAL']=dict(status='RUNNING',detail='Final serial proof: '+name+'. Source: FINAL_PROOFS.json. GO=false.')
    (B/'STEPS.json').write_text(json.dumps(status,indent=2)+'\n')
    (B/'STATUS.md').write_text('# Build 10 status\n\nGO=false. Source: STEPS.json.\n\n'+''.join(f'- {k}: {v["status"]}. {v["detail"]}\n' for k,v in status.items()))
    with (out/(name+'.log')).open('w') as log:
        result=subprocess.run(py+[str(B/script),*args],stdout=log,stderr=subprocess.STDOUT)
    row.update(status='complete' if result.returncode==0 else 'failed',returncode=result.returncode,tmp_after=temp_size())
    (B/'FINAL_PROOFS.json').write_text(json.dumps(steps,indent=2)+'\n')
    if result.returncode<0:raise SystemExit('A process was killed; stop without retry.')
    if result.returncode:raise SystemExit(result.returncode)
run('g8_available','proof_runner10.py','g8_available',*['eat1.tests.test_eat1.'+n for n in ('Adversarial','FixedMathContract','Instruments','StaticScanner','ToyEndToEnd')])
result=json.loads((L/'work/build12/proofs/g8_available/RESULT.json').read_text());assert result['run']==29 and not result['failures'] and not result['errors']
run('adapter_manifest','proof_runner10.py','adapter_manifest','test_adapter_manifest10.AdapterManifest')
run('final_eat','final_eat10.py')
run('parity_build7','parity_build7_10.py')
run('eat_summary','eat_summary10.py');run('eat_groups','eat_evidence10.py')
run('source_preservation','source_preservation10.py')
run('bindings','finish_audit9.py');run('pins','pin_audit.py');run('legacy_guards','legacy_guard_proof.py')
run('comparison','compare.py');run('coverage','coverage10.py');run('incremental_coverage','incremental_coverage10.py')
run('harness_coverage','harness_coverage10.py');run('inference_inventory','inference_inventory.py')
run('b04_source','check_stage10.py');run('b04_inventory','b04_inventory10.py');run('b04_pin','b04_pin10.py')
run('storage','storage_check.py')
print('Final proof sequence completed.',flush=True)
