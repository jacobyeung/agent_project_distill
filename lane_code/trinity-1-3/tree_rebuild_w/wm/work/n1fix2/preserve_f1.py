from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';P=L/'work/merge11/proofs/n1/text'
values={}
for name in ('a0_recovery','a0_units'):
    p=P/name/'RESULT.json'
    if p.exists():values[name]=json.loads(p.read_text())
(P/'BEFORE_EXTENT_GATE.json').write_text(json.dumps(dict(scope='F1-only reader and intake, before the mandatory extent admission gate; partial baseline census.',families=values),indent=2)+'\n')
with (B/'DECISIONS.md').open('a') as f:
    f.write('\n- F1 baseline count discrepancy: the pinned original units slice admits 1915 at intake, while the prompt requests 1895 for that family. Preserve the bytes and existing exclusions; do not tune admission to the requested count. BEFORE_EXTENT_GATE.json records the partial F1-only census. The final reader additionally applies the required F5 receipt.\n')
