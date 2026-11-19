"""Keep request pins aligned with the native donor export and final handoff."""
from pathlib import Path
import sys,subprocess,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';R=D/'rehearsal3';ns=Path('/tmp/q_22c714e1')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
if '--inside' not in sys.argv:
    args=J.load(R/'VIEW.json');py=sys.executable
    env={**os.environ,'S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24f_fresh'}
    for cmd in ([py,'-I','-s','-B',str(Path(__file__).resolve()),'--inside'],
       [py,'-B',str(D/'rehearsal_handoff.py'),str(ns/'p2'),str(ns/'v.json')],
       [py,'-B',str(D/'rehearsal_gates.py')]):subprocess.run(args+cmd,env=env,check=True)
    p=J.load(R/'PREPARED.json');p['canary']=J.sha(R/'p2/q/RESULT.json');J.write(R/'PREPARED.json',p)
    raise SystemExit(0)
import torch
torch.set_num_threads(2)
from student_pilot import r1_handover as H,r1_persisted as P
gen=J.load(R/'GENERATION.json');receipt=J.load(gen['receipt']['path'])
paths={p['sha256']:p['path'] for p in receipt['pins'].values()}
with P.scope(J.load(R/'r2.json')['_paths']),P.scope(paths):
    for name in ('seed','input','n'):
        c=J.load(R/(name+'.json'));c['init_artifact']['artifact']=gen['artifact']
        c['r1_training'].update(handover_receipt=gen['receipt'],persisted_files=paths)
        c=H.bind_target(c,R/'rebind'/(name+'_mapping.json'))
        pin=J.write(R/(name+'.json'),c)
        if name=='input':input_pin=pin
    for name in ('r','r2'):
        r=J.load(R/(name+'.json'));r['config']=input_pin;r['staged_pins']=[input_pin]
        J.write(R/(name+'.json'),r)
    result=J.load(ns/'p2/q/RESULT.json');result['staged']=[input_pin]
    J.write(ns/'p2/q/RESULT.json',result)
print('PASS: request, seed, and input pins bind the native export.')
