from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((B/'proofs/final/packet/results.json').read_text())
failed={k:v for k,v in rows.items() if v['outcome']!='passed'}
assert len(failed)==2
missing='/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py'
assert not Path(missing).exists()
old=json.loads((B/'BASE14_SEAL.json').read_text())['files']
generator={n:sha(T/n) for n in old if n.startswith(('generator/','trace_format/'))}
assert all(h==old[n] for n,h in generator.items())
tests=L/'work/contracts_r6/packet_root/work/tests_r6'
baseline=L/'work/build15/proofs/final/packet/work/generator_baseline_r5.json'
pins=json.loads((L/'work/build14/PACKET_INPUTS.json').read_text())
expected=next(r['sha256'] for r in pins if r['target'].endswith('generator_baseline_r5.json'))
assert sha(baseline)==expected
value=dict(passed=sum(v['outcome']=='passed' for v in rows.values()),failed=failed,
    missing_input='not rerun: input absent ('+missing+')',
    comparison='Exact JSON float serialization differs at a trailing digit; unchanged source and baseline. No tolerance changed and no pass claimed.',
    generator_source_hashes=generator,baseline_sha256=expected,
    test_source={p.name:sha(p) for p in (tests/'test_generator_r4.py',tests/'test_review_r4.py')})
(B/'PACKET_QUALIFICATION.json').write_text(json.dumps(value,indent=2));print('Packet qualification recorded.')
