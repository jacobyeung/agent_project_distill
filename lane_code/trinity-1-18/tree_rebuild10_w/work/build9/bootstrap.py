"""Prepare the bounded build harness and summarize inherited evidence."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
B=L/'work/build9'
for p in (L/'work/build7').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh'):
        text=p.read_text()
        if p.name!='test_runner.py':
            text=text.replace('build7','build8').replace('package7_', 'package9_').replace('tree_rebuild_b7_', 'tree_rebuild_b8_')
        (B/p.name).write_text(text)
for group in ('generator','legacy','r2'):
    src=L/'work/build7/proofs/suite_base'/group
    dst=B/'proofs/suite_base'/group
    dst.mkdir(parents=True,exist_ok=True)
    for p in src.iterdir():
        if p.is_file() and p.suffix=='.json': (dst/p.name).write_bytes(p.read_bytes())
(B/'STATUS.md').write_text('# Build 8 status\n\nInput evidence read. Step 1: regressions under investigation. No remote action or GPU use.\n')
(B/'DECISIONS.md').write_text('# Build 8 decisions\n\n- Retain input-hash-bound base receipts; rerun only groups whose inputs change. The copied test runner retains its bytes.\n- Fix BF16 parity only if the computation has a defect. Otherwise retain the original failing assertion and the kit refusal.\n- Skills stored outside this lane are not read: this build restricts external reads to its named files. Apply the supplied prose rules directly.\n')
for name in ('FINAL_PASS','SUITE_COMPARISON','GAPS','CHANGED_COVERAGE'):
    v=json.loads((L/'work/build7'/f'{name}.json').read_text())
    if name=='SUITE_COMPARISON':
        print(name, list(v) if isinstance(v,dict) else type(v).__name__)
        for k,value in v.items():
            if k in ('regressions','r2_failures','counts'):print(k,json.dumps(value))
    elif name=='GAPS':print(name,json.dumps(v))
    elif name=='CHANGED_COVERAGE':print(name,[(k,value) for k,value in v.items() if k in ('counts','classes','summary')])
    else:print(name,json.dumps(v))
print('TMP_BYTES',sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
