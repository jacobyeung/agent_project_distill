from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];O=L/'work/build19/proofs/native/600'
for name in ('export/artifact.json','h.json','config.json'):
    v=json.loads((O/name).read_text());print(name,{k:v.get(k) for k in ('job_id','r2_identity','init_artifact','output')})
