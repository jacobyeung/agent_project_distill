from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for path in [L/'work/build13/inputs/kit_config.json',Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json'),Path('/scratch/jjyeung/orch_n30/r1_ops/work/adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json')]:
 v=json.loads(path.read_text());print(str(path),json.dumps({k:v.get(k) for k in ['preparation','camera','streams']},indent=2)[:8000])
