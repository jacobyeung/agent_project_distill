from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];E=L.parent
for name in ('ext/r1_ops/work/snap_fac07052/out/config.json','ext/r1_ops/work/snap_6a5c7d00/out/config.json','inputs/p_configs/cprime_31abe087.json'):
    cfg=json.loads((E/name).read_text()); print(name)
    print(json.dumps({k:cfg.get(k) for k in ('output','preparation_output','streams','s1_routing','continuation','code','init_artifact','preparation','base_identity')},indent=2))
