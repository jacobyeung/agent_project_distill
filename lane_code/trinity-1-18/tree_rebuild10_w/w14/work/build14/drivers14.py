from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build14'
for name in ('census13.py','native_builder13.py','recompose13.py','encode13.py','edges13.py','mutations13.py','storage13.py'):
    s=(L/'work/build13'/name).read_text().replace('work/build13','work/build14').replace('B13_PROOF','B14_PROOF').replace('test13.py','test14.py')
    (B/name.replace('13','14')).write_text(s)
for name,target in [('proof_text.py','text14.py'),('proof_row_delta.py','row_delta14.py')]:
    s=(L/'work/n1fix2'/name).read_text().replace('work/build12/proofs/n1','work/build14/proofs')
    (B/target).write_text(s)
s=(L/'work/build12/preservation.py').read_text().replace("B=L/'work/build12'","B=L/'work/build14'")
(B/'preservation14.py').write_text(s)
(B/'inputs/config.json').write_bytes((B/'inputs/kit_config.json').read_bytes())
tasks=[('focused',['test14.py','tests.test_r1_build14','tests.test_r2_build12.Build12.test_trainer_hook_y5']),
       ('census',['census14.py']),('builder',['native_builder14.py']),('composition',['recompose14.py']),
       ('plans',['census14.py','--resume']),('encode',['encode14.py']),('edges',['edges14.py']),
       ('mutations',['mutations14.py']),('text',['text14.py']),('row_delta',['row_delta14.py']),('preservation',['preservation14.py'])]
(B/'TASKS.json').write_text(json.dumps(tasks))
