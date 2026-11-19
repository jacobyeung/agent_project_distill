from pathlib import Path
import sys,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24';sys.path[:0]=[str(D),str(Path(os.environ.get('R2_TREE',L/'work/tree_r1')))]
import joblib as J
from student_pilot.r1_persisted import verify
cfg=J.load(D/'proofs/capacity/final/600/h/config.json');v=cfg['r1_training']
r=verify(v['handover_receipt'],v['p_run'],cfg['init_artifact']['artifact'],v['persisted_files'],weights=True,proof_mode='train')
assert r['receipt']['step']==600
J.write(D/'LAUNCH_MODE.json',dict(status='PASS',GO=False,proof_mode='train',checkpoint_step=600,without_proof_scope=True,
    template=J.load(D/'kits/n/k/n.json')['r1_training']['proof_mode'],world_size=4,partition='advanced'))
print('PASS: native step600 checkpoint admission accepts training mode without a proof-scope override')
