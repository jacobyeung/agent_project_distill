import pytest
from trace_format.contracts import contract_epoch

def test_generator_register_exception_and_missing_cache_alias():
    from generator.derivgen_v7.derivgen.calculator import PrintedPointRegistry,CalculatorError
    from student_pilot.phrases import cache_view
    with contract_epoch(True):
        with pytest.raises(CalculatorError):
            PrintedPointRegistry().register(camera=[0,0,1],f1=[0,0,1],spread=0,requested_frame=99)
        cache=dict(phrases=['table'],frames={})
        view,name=cache_view(cache,'chair')
        assert view==cache and view is not cache and name=='chair'

def test_private_metric_anchor_skips_invalid_pose_and_handles_vertical_anchor():
    import numpy as np
    from student_pilot.carrier_c1_routing import OwnGeometry
    pose=np.zeros((32,9));pose[:,6]=1;pose[:,7:9]=1
    pose[1,3:7]=0
    with contract_epoch(True):
        geometry=OwnGeometry(pose,np.array([0.,0.,1.]),lambda k,pts:np.ones(len(pts)))
        assert np.isfinite(geometry.to_l1).all()
        assert np.allclose(geometry.to_l1@geometry.to_l1.T,np.eye(3))
        from trace_format.contracts import private_metric_basis
        for invalid in (np.zeros((1,)),np.full((3,3),np.nan),np.zeros((3,3))):
            assert private_metric_basis(lambda k:invalid,np.array([0.,0.,1.])) is None
        pose[1:,3:7]=0
        geometry=OwnGeometry(pose,np.array([0.,0.,1.]),lambda k,pts:np.ones(len(pts)))
        assert np.isfinite(geometry.to_l1).all()
