import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent/'kc_guard/k1_build/work/kit_k1a/work'
sys.path.insert(0,str(WORK))
import k1_pipeline as K
K._native()
B=K.B
import k1_guard as guard
import k1_phases as F
guard.install()
before=B.load(ROOT/'identity_before.json')
after={p:B.sha(p) for p in before}
assert before==after
bound_before=B.load(ROOT/'bound_identity_before.json')
bound_after=B.source_identity();bound_after[str(WORK/'k1_phases.py')]=B.sha(WORK/'k1_phases.py')
assert bound_before==bound_after
base=ROOT.parent.parent/'kc'
private=ROOT.parent/'kc_guard'
paired={}
for path,sha in before.items():
 p=Path(path)
 if p.is_relative_to(private):
  q=base/p.relative_to(private)
  assert B.sha(q)==sha,(p,q)
  paired[path]=dict(original=str(q),sha256=sha)
m=B.load(ROOT.parent/'manifest_v2/a40fbc19.json')
assert B.sha(ROOT.parent/'manifest_v2/a40fbc19.json')=='e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146'
assert len(m['captures'])==300
for c in m['captures']:F.checked_phase(c,'/scratch/jjyeung/k1/run_tower_sam_2','tower_sam')
for c in m['captures'][:3]:F.checked_phase(c,str(ROOT.parent/'own7/canary/native/probe'),'own')
canary=ROOT/'canary'
receipts=[]
for c in m['captures'][:3]:
 raw,geo,r=K.cached(c,canary/B.digest(c['canonical'])[:16])
 assert geo is not None and not r.get('geometry_refusal')
 receipts.append(dict(canonical=c['canonical'],gravity_verdict=r['gravity_verdict'],geometry=r['geometry']))
assert receipts[2]['gravity_verdict']==dict(sealed_refused=True,reviewed_refused=False)
assert guard.GG.report()==B.load(canary/'GUARD_REPORT.json')
events=[json.loads(line) for line in (canary/'PROGRESS.jsonl').read_text().splitlines()]
assert [e['canonical'] for e in events if e['event']=='capture_start'][-1]==m['captures'][3]['canonical']
assert B.digest(m['captures'][3]['canonical'])[:16] in (ROOT/'canary.log').read_text()
assert B.load(canary/'HALTED.json')['error'].startswith('FileNotFoundError')
proof=dict(private_before=before,private_after=after,bound_before=bound_before,bound_after=bound_after,baseline_pairs=paired,
 tower_checked=300,own_checked=3,canary=receipts,guard_report=guard.GG.report(),expected_halt=B.load(canary/'HALTED.json'))
(ROOT/'identity_proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(identity_files=len(before),private_equal=True,bound_equal=True,baseline_equal=True,tower_checked=300,own_checked=3,canary_receipts=3,expected_halt_capture=4)))
