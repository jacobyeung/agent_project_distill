from pathlib import Path
import hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build12';F=L/'work/n1fix2'
rows=json.loads((F/'PACKET_INPUTS.json').read_text())
for row in rows:
    src=L/row['source']
    if not src.exists():src=L/row['target']
    assert src.is_file(),src
    assert hashlib.sha256(src.read_bytes()).hexdigest()==row['sha256'],src
    row['source']=str(src.relative_to(L))
    row['target']=row['target'].replace('work/merge11','work/build12')
    dst=L/row['target'];dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():dst.symlink_to(src)
(F/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2))
old=L/'work/build9fix/test_runner.py';new=F/'test_runner.py'
(B/'RUNNER_EQUIVALENCE.json').write_text(json.dumps(dict(
    equivalent=old.read_text().replace('work/build9fix','work/n1fix2')==new.read_text(),
    original_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),current_sha256=hashlib.sha256(new.read_bytes()).hexdigest()),indent=2))
with (B/'DECISIONS.md').open('a') as f:
    f.write('''

The exact handover allow-list is defined in student_pilot/r1_handover.py:
- streams and mix may differ because the authenticated donor row plan and explicit mapping bind source and target stores and sampler positions.
- preparation and r2_sampling may differ because the authenticated donor preparation and target sampler bind their respective populations.
- r1_training carries the N continuation contract, receipt pin, host attestations and mapping; donor-side extensions still refuse.
- init_artifact changes from P's initializer to P's export. Separate exact depth pins and authenticated inherited-head membership checks gate initialization.
- output and preparation_output are output destinations and do not select optimizer groups.
- admission, authorization and milestone_gate are allocation/review attestations, not optimizer settings.
- code changes from P's sealed trainer to N's sealed trainer. The P receipt records P's trainer commit and N's kit seals N's code.
- r2_identity and routing_vocabulary bind N's initializer lineage and token inventory; the native initializer and opener admission validate them. routing_opener_init itself must match.
Only recipe.mix is exempt inside recipe. All other nested recipe values, topology fields, loss settings, unknown keys and initializer settings compare exactly.

Fixture retention overrides exclusive creation only inside each owned CPU proof folder. This changes output-file lifecycle, not producer calculations, serialized tensors, receipt contents or reader checks. Tiny native models replace pretrained weights; local collectives replace distributed GPU collectives. No production P weights or full stores were copied.
''')
print('Packet inputs staged; frozen-runner equivalence recorded.')
