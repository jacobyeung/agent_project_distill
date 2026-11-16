from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
import uuid
from unittest.mock import patch
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine
engine.initialize(dict(tree=str(R/'from113/work/tree')))

class TowerBoundary(unittest.TestCase):
    def test_real_tower_loop_with_pinned_provider_fixture(self):
        import geometry as G
        import numpy as np
        from student_pilot import tower_read as T
        root=B/'work'/('tb_'+uuid.uuid4().hex);root.mkdir()
        prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root/'i',True)
        weights=root/'w';config=root/'c';weights.write_bytes(b'fixture weights');config.write_bytes(b'fixture config')
        # The provider alone is replaced; capture validation, PNG checks and archive serialization are real.
        class Provider:
            def __init__(self,settings):self.dense_frames=settings['dense_frames']
            def run(self,batch):
                T.g3t_to_c1_pose9(None,None,None)
                pose=np.zeros((32,9));pose[:,0]=np.arange(32)*.03;pose[:,6]=1;pose[:,7:]=1
                return T.TowerState(pose,np.ones((32,51,51)),np.broadcast_to(np.linspace(1,2,51*51).reshape(1,51,51),(32,51,51)),
                                    np.array(batch['frame_indices']),np.arange(32))
        with patch.object(T,'FrozenG3TTower',Provider),patch.object(T,'WEIGHTS_SHA256',sha(weights)),patch.object(T,'CONFIG_SHA256',sha(config)),patch.object(T,'g3t_to_c1_pose9',return_value=dict(gravity_up=np.array([0.,-1.,0.]))):
            G.tower(NS(device='cpu',weights=weights,config=config,frames=root/'i/FRAMES.json',dense_manifest=root/'i/DENSE.json',dest=root/'r',output_name='RAW.json'))
        raw=load(root/'r/RAW.json');self.assertEqual(len(raw['captures']),2)
        for entry in raw['captures'].values():
            with np.load(checked(entry),allow_pickle=False) as z:
                self.assertEqual(z['raw_pose'].shape,(32,9));self.assertEqual(z['gravity_up'].tolist(),[0.,-1.,0.])
if __name__=='__main__':unittest.main(verbosity=2)
