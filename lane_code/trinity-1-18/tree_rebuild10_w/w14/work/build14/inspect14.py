from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
paths={'A':'/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json','C':'/scratch/jjyeung/orch_n30/r1_ops/work/snap_6a5c7d00/out/config.json','N':str(L/'work/build13/inputs/kit_config.json')}
for name,path in paths.items():
    v=json.loads(Path(path).read_text())
    print(name,json.dumps({k:v.get(k) for k in ('recipe','h1','routing_opener_init','init_artifact','pose','camera','continuation','r1_training')},indent=2))
print('bytes',sum(p.stat().st_size for p in L.rglob('*') if p.is_file()))
