from pathlib import Path
import sqlite3,json
p=Path('/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
c=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
print('BYTES',p.stat().st_size)
print('SCHEMA',c.execute('SELECT name,sql FROM sqlite_master').fetchall())
c.close()
L=Path(__file__).resolve().parents[2]
cfg=json.loads((L/'work/n1fix2/inputs/config.json').read_text())
print('STREAMS',cfg['streams'])
for name in ('vehN_pool_abs_distance','vehN_units'):
    root=Path('/scratch/jjyeung/orch_n30/rows_r1/out')/name
    print(name,[(p.name,p.stat().st_size) for p in root.iterdir() if p.is_file()])
