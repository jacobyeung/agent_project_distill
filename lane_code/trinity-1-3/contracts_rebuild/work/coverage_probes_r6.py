import builtins
import pytest
from trace_format.contracts import contract_epoch


def test_standalone_construction_fallback(monkeypatch):
    from generator.derivgen_v7.derivgen.calculator import PrintedPointRegistry
    original=builtins.__import__
    def importing(name,*args,**kwargs):
        if name=='trace_format':raise ImportError('standalone generator')
        return original(name,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(builtins,'__import__',importing)
        registry=PrintedPointRegistry()
    point=registry.register(camera=[1,2,3],f1=[4,5,6],spread=0,requested_frame=2)
    assert point['line']=='P1: cam2 (1.00, 2.00, 3.00) m; f1 (4.00, 5.00, 6.00) m; spread 0.00'


def test_partial_basis_fallback():
    import numpy as np
    from student_pilot.carrier_c1_routing import OwnGeometry
    pose=np.zeros((32,9));pose[:,6]=1;pose[:,7:9]=1
    pose[1:,3:7]=0
    with contract_epoch(True):
        geometry=OwnGeometry(pose,np.array([0.,0.,1.]),lambda k,pts:np.ones(len(pts)))
        assert np.isfinite(geometry.to_l1).all()
