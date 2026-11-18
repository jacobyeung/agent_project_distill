import json, sqlite3, hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix3'
H=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/payload')
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
dst=B/'inputs';dst.mkdir(exist_ok=True)
def read(path,name):
    raw=path.read_bytes();(dst/name).write_bytes(raw)
    return json.loads(raw)
over=read(H/'over.json','h1_over.json')
print('OVER KEYS',list(over))
for key,val in over.items():
    if key not in ('config',):
        print(key,str(val)[:700])
artifact=read(H/'d_1d6eeb28f51688c4.json','init_artifact.json')
print('ARTIFACT', {k:v for k,v in artifact.items() if k not in ('trained_groups','source_seal','training_source_seal')})
for name in ('receipt.json','MANIFEST.json','JOB_PATHS.json'):
    value=read(R/'a2_vqa_v7/vqa'/name,'v7_'+name)
    print('V7',name,str(value)[:1800])
read(R/'a2_vqa_v7/CHECK_MERGE.json','v7_validator.json')
read(R/'a2_vqa_v7/BUILD_MANIFEST.json','v7_build.json')
for family in ('room_v2','recovery_v2'):
    for name in ('CHECK.json','COUNTS.json'):
        value=read(R/family/name,family+'_'+name)
        print(family,name,str(value)[:1300])
    with (R/family/'rows.jsonl').open() as f:
        row=json.loads(next(f));print(family,'ROW',str(row)[:2000])
con=sqlite3.connect('file:'+str(R/'a2_vqa_v7/vqa/rows.sqlite')+'?mode=ro&immutable=1',uri=True)
print('SCHEMA',con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall())
print('FIRST',str(con.execute('SELECT * FROM rows LIMIT 1').fetchone())[:3500])
con.close()
for p in (L/'work/kit07ca49df_meta/m/k/b02e4385.json', L/'work/kit07ca49df_meta/m/k/0.json'):
    value=json.loads(p.read_text()); print(p.name,'keys',list(value))
    if p.name=='b02e4385.json':
        print('CFG', {k:v for k,v in value.items() if k in ('recipe','max_pixels','min_pixels','camera_overrides','model','processor','streams','training_mode')})
