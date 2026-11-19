from pathlib import Path
import json
E=Path(__file__).resolve().parents[3]
for name in ('inputs/p_configs/RUNTIME_CONFIG_171377_673bc60f.json',
 'ext/r1_ops/work/adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/vqa/receipt.json',
 'ext/r1_ops/work/adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json'):
    x=json.loads((E/name).read_text());print(name)
    for k in ('output','preparation_output','model','source','source_receipt','database','streams'):
        if k in x:print(k,json.dumps(x[k])[:2800])
for d in ('ext/r1_ops/work/snap_fac07052/work/kit','ext/r1_ops/work/snap_fac07052/out'):
    p=E/d
    print(d,[x.name for x in p.iterdir() if x.is_file()][:60])
