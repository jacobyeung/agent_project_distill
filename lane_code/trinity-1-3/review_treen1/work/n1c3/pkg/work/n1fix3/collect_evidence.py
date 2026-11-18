from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
R=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c2')
O=B/'proofs/review_inputs';O.mkdir(parents=True,exist_ok=True)
files=[R/n for n in ('N1.json','N1X.json','MUTANTS.json','N3_VARIANTS.json','F1_prod.json')]
files+=list(R.glob('N5*.json'))+list(R.glob('F6*.json'))
records=[]
for p in files:
    raw=p.read_bytes();value=json.loads(raw)
    (O/p.name).write_bytes(raw)
    records.append(dict(source=str(p),sha256=hashlib.sha256(raw).hexdigest(),keys=list(value) if isinstance(value,dict) else len(value)))
print(json.dumps(records,indent=2))
(O/'RECEIPT.json').write_text(json.dumps(records,indent=2))
G=L.parent/'wn2/work/n1fix2'
for name in ('CHANGED_COVERAGE.json','SUITE_COMPARISON.json','STATUS.md','DECISIONS.md'):
    (B/'inherited'/('N1FIX2_'+name)).write_bytes((G/name).read_bytes())
(B/'inherited/CHANGED_COVERAGE.json').write_bytes((G/'CHANGED_COVERAGE.json').read_bytes())
p=B/'proof_text.py';s=p.read_text().replace("Rows({'streams':{},'extent_receipt':extent_pin},TinyProcessor())", "Rows({'streams':{},'extent_receipt':extent_pin,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor())")
p.write_text(s)
P=B/'proofs/checkpoint_limit';P.mkdir(exist_ok=True)
source=L/'work/base/tree_b01ce449/student_pilot/carrier_c1_run.py'
(P/'RESULT.json').write_text(json.dumps(dict(status='BLOCKED',source=str(source.relative_to(L)),
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    reason='The sealed export authenticates the config identity but that identity excludes preparation. Neither the export nor its weight manifests pins complete.json or checkpoint shards. Shard hashes listed only inside an operator-supplied complete.json cannot authenticate that file.',
    required_producer_file='P must write a handover.json containing export artifact SHA256, complete.json SHA256, shard SHA256 values, config SHA256 and preparation SHA256, then publish its SHA256 through the trusted run record; alternatively P must include the complete.json pin in its authenticated export artifact.',
    reviewer_forgery='work/n1fix3/proofs/review_inputs/N1.json',
    unchanged_semantics=True),indent=2))
