"""Whether A4's load_native can read an N-tree export: compare both trees' config identity on N's configs."""
from pathlib import Path
from rl_on_n import provenance as P
from rl_on_n.serving import load_binding,reader_runtime,PAYLOAD,ROOT
P.sha(__file__)
N=Path('/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1');P.tree(N)
load_binding()
configs=[N.parents[1]/'work/build18/inputs/config.json',N.parents[1]/'work/n1fix2/inputs/config.json']
from student_pilot.carrier_c1_run import identity as n_identity
rows=[dict(config=P.pin(path),n_identity=n_identity(P.load(path))) for path in configs]
with reader_runtime():
    from student_pilot.carrier_c1_run import identity as a4_identity
    for row in rows:row['a4_identity']=a4_identity(P.load(row['config']['path']))
for row in rows:row['equal']=row['a4_identity']==row['n_identity']
loader=PAYLOAD/'b/e2e_reader/parity.py';P.sha(loader)
line=next(i for i,text in enumerate(loader.read_text().splitlines(),1) if 'loaded export identity differs' in text)
readable=any(row['equal'] for row in rows)
finding=(f"A4 identity() differs from N's on {sum(not r['equal'] for r in rows)} of {len(rows)} N configs; "
         f"load_native raises 'loaded export identity differs' at b/e2e_reader/parity.py:{line}")
P.write(ROOT/'out/N_EXPORT_CHECK.json',dict(status='READABLE' if readable else 'MISSING',finding=finding,configs=rows,
    loader=dict(path=str(loader),line=line),
    scope='Identity check only: an N export stores N identity(cfg) as artifact.config_sha256, which A4 recomputes with its own identity(cfg).',
    command='PYTHONPATH=overlay python -B scripts/n_export_check.py'))
print(finding)
