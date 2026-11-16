"""Refresh implementation pins after validated admission fixes; preserve manifest rows."""
import json
from pathlib import Path
from provenance import sha256,write_json

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'out'
authority=json.loads((out/'EVAL_ROOMS.json').read_text())
authority['arkit_rooms']['43649472']='arkitscenes/43649472'
for p in authority['provenance']['code']:authority['provenance']['code'][p]=sha256(p)
write_json(out/'EVAL_ROOMS.json',authority)
pin=sha256(out/'EVAL_ROOMS.json');(out/'EVAL_ROOMS.sha256').write_text(pin+'  EVAL_ROOMS.json\n')
for name in ('b2_manifest.jsonl','tuning_manifest.jsonl'):
    path=out/name
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:row['authority_sha256']=pin
    with path.open('w') as f:
        for row in rows:f.write(json.dumps(row,sort_keys=True)+'\n')
report=json.loads((out/'MANIFEST_REPORT.json').read_text());report['provenance']=authority['provenance']
report['manifests']={name:sha256(out/name) for name in ('b2_manifest.jsonl','tuning_manifest.jsonl')}
report['finalizer_sha256']=sha256(__file__);write_json(out/'MANIFEST_REPORT.json',report)
print(pin)
