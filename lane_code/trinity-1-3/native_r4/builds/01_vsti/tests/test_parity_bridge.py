"""Exercise the inherited parity gate with CPU control-flow fixtures."""
from pathlib import Path
import sys,unittest,uuid
from unittest.mock import patch
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
import engine
engine.initialize(dict(tree=str(R/'from113/work/tree')))

class ParityBridge(unittest.TestCase):
    def test_inherited_gate_and_failure(self):
        import nomdg as N,perception as P,routed
        from evalpath import parity,items,runtime
        root=B/'work'/('parity_fixture_'+uuid.uuid4().hex);root.mkdir()
        boundary=engine.NativeBoundary.__new__(engine.NativeBoundary)
        boundary.model=object();boundary.processor=object();boundary.info={};boundary.cfg={};boundary.spec=dict(device='cpu')
        task=dict(native='c0',id='q0');capture={};row={'fixture':True}
        decoded=dict(heads={},calls=[dict(kind='head',call='<move from=1 to=2>')],errors=0)
        p1=dict(checked=1,mismatches=[],sequence=dict(exact=True),cached_positions_complete=True)
        with patch.object(routed,'trainer_row',return_value=row),patch.object(items,'assert_prompt_equal'),patch.object(runtime,'prompt_batch',return_value={}),patch.object(N,'move_batch',side_effect=lambda b,d:b),patch.object(P,'generate',return_value=decoded),patch.object(parity,'LogitTap',return_value=object()),patch.object(parity,'p1',return_value=p1),patch.object(parity,'p2',return_value=dict(pass_=True,**{'pass':True,'independent_calls':1})),patch.object(parity,'p3',return_value={'pass':True}):
            result=boundary.parity(task,capture,'fixture',root)
            self.assertTrue(result['pass']);self.assertTrue(result['p1_gate']['pass'])
            p1['cached_positions_complete']=False
            with self.assertRaisesRegex(ValueError,'parity failed'):
                boundary.parity(task,capture,'fixture',root)
if __name__=='__main__':unittest.main()
