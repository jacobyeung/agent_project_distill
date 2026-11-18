"""Resume a successful proof phase only when its exact inputs still match."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';name=sys.argv[1]
assert name in ('targeted','packet')
pending=B/'REQUALIFICATION.json'
if pending.exists() and json.loads(pending.read_text()).get('pending'):
    raise SystemExit('Source repair remains pending')
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def inputs():
    files={p for p in (B/'inputs').glob('*.json')}
    files.update(B/n for n in ('phase.py','test_runner.py','compact_tmp.py','PACKET_TEST.sh','packet_final.py','packet_support.py','packet_recovery.py','PACKET_INPUTS.json','requalification_gate.py'))
    for row in json.loads((B/'PACKET_INPUTS.json').read_text()):
        path=(L/row['source']).resolve();assert path.is_relative_to(L);files.add(path)
    return dict(source=inventory(L/'work/tree_r1'),fixtures=inventory(L/'fixtures'),
                contracts=inventory(L/'work/contracts_r6/tests_r6'),
                files={str(p.relative_to(L)):sha(p) for p in sorted(files)},
                python=sys.version,environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','CUDA_VISIBLE_DEVICES','R2_FAST_CENSUS')})
root=B/'proofs'/name;receipt=root/'PHASE_RECEIPT.json';result=root/'results.json'
key=inputs()
prior=json.loads(receipt.read_text()) if receipt.exists() else {}
if prior.get('complete') is True and prior.get('inputs')==key and result.exists() and prior.get('results_sha256')==sha(result):
    print('Resumed completed phase '+name);raise SystemExit(0)
command=([sys.executable,'-I','-s','-B',str(B/'test_runner.py'),str(root),'tests.test_r2_build_n1']
         if name=='targeted' else ['bash',str(B/'PACKET_TEST.sh')])
code=subprocess.run(command,cwd=L).returncode
if code<0:raise SystemExit('Proof process was killed; stop without retry')
if code:raise SystemExit(code)
value=json.loads(result.read_text())
if name=='targeted':
    assert value['complete'] and not value['failures'] and not value['errors'] and not value['fatal']
else:assert value and all(row['outcome']=='passed' for row in value.values())
assert inputs()==key,'Phase inputs changed during proof'
receipt.write_text(json.dumps(dict(inputs=key,results_sha256=sha(result),complete=True,command=command),indent=2)+'\n')
