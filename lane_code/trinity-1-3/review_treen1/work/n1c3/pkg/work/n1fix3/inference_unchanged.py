from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
old=json.loads((B/'inherited/proofs/audit/INFERENCE_COMPONENTS.json').read_text())
current=json.loads((B/'proofs/audit/INFERENCE_COMPONENTS.json').read_text())
records=[]
for row in current['known_outside_forward']:
    name=row['file'];sha=hashlib.sha256((L/'work/tree_r1'/name).read_bytes()).hexdigest()
    assert old['source_hashes'][name]==sha
    records.append(dict(file=name,line=row['line'],component=row['component'],sha256=sha,unchanged=True))
(B/'proofs/audit/INFERENCE_UNCHANGED.json').write_text(json.dumps(dict(source='work/n1fix3/inherited/proofs/audit/INFERENCE_COMPONENTS.json',records=records),indent=2))
print('Known inference components retain their exact source bytes.')
