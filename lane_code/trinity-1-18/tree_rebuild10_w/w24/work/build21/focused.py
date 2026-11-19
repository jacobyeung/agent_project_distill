"""Serialize the remaining frozen-source checks."""
from pathlib import Path
import os,sys,subprocess,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
if (L/'work/build24').is_dir():
    import hashlib
    fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(Path(os.environ.get('R2_TREE',L/'work/tree_r1')).rglob('*.py')))).hexdigest()
    lock=L/'work/build24'/('focused_'+fingerprint+'.lock')
    try:
        with lock.open('x') as f:f.write(str(os.getpid()))
    except FileExistsError:
        print('This source already has a focused-suite owner.',flush=True)
        raise SystemExit(0)
steps=[
 ('final_focused',B/'test21.py',['tests.test_r1_build20','tests.test_r1_build19','tests.test_r1_build18','tests.test_r1_build17','tests.test_r1_export17',
  'tests.test_r1_build16','tests.test_r1_build15','tests.test_r1_build14','tests.test_r2_build_n1',
  'tests.test_r2_n1fix','tests.test_r2_n1fix3','tests.test_r2_build12','tests.test_r1_build13',
  'tests.test_r2_build3.Build3.test_opener_export_keep_and_reset','export_mutation17.HashTwin.test_same_size_shard_refuses']),
 ('edges',B/'test21.py',['edge_test16.Edges','stage_test16.Staging']),
 ('producer_edges',B/'test21.py',['export_edges17.ProducerEdges']),
]
records=[]
for name,script,args in steps:
    with (B/(name+'.log')).open('w') as f:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(script),*args],
            env={**os.environ,'B21_PROOF':name},stdout=f,stderr=subprocess.STDOUT)
    records.append(dict(name=name,returncode=result.returncode))
    (B/'FINAL_CHECKS.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit('Check failed; inspect retained log: '+name)
