"""Run with the specified production interpreter and numpy overlay."""
import dataclasses
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

B=Path(__file__).resolve().parents[2]
W=Path('/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/work')
ROOT=Path('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build/out/guard_kit/sj/orch_cd/evalx/work/milestone')
sys.path[:0]=[str(W/'tree'),str(ROOT/'native/out2'),str(ROOT/'orchard_native')]
import numpy as np
from student_pilot import geometry_profiles as GP
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
import native_worker as worker

MANIFEST=json.loads((W/'p9/native/geometry/GEOMETRY_MANIFEST.json').read_text())
RECORDS={r['native']:r for r in MANIFEST['records']}

def fresh_guard():
    spec=importlib.util.spec_from_file_location('gravity_guard',ROOT/'native/out2/gravity_guard.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def geometry(name):
    p=W/'p9/native/geometry'/(RECORDS[name]['clip']+'.npz')
    with np.load(p,allow_pickle=False) as z:
        frames=FrameMap(tuple(int(x) for x in z['anchor_frame_indices']))
    return load_geometry(p,frames,'tower_scaled')

class Guard(unittest.TestCase):
    def setUp(self):
        self.original=GP.GeometryContract.validate
        self.guard=fresh_guard()

    def tearDown(self):
        GP.GeometryContract.validate=self.original

    def install(self):
        self.guard.install(GP,self.guard.Recorder())

    def test_sealed_inspect_identity(self):
        self.assertEqual(hashlib.sha256(inspect.getsource(self.original).encode()).hexdigest(),
                         self.guard.SEALED_VALIDATE_SHA256)

    def test_install_success(self):
        self.install()
        with self.guard.capture('dev-S1','d1/scene0155_00'):
            value=geometry('d1/scene0155_00')
        self.assertIs(value.contract.validate(),value.contract)
        self.assertEqual(self.guard.report()['dev-S1']['capture_count'],1)

    def test_source_refusal(self):
        with patch.object(self.guard.inspect,'getsource',return_value=inspect.getsource(self.original)+'\n'):
            with self.assertRaisesRegex(RuntimeError,'sealed_validate_mismatch'):self.install()
        self.assertIs(GP.GeometryContract.validate,self.original)

    def test_terminal_ast_refusal(self):
        source=inspect.getsource(self.original).replace('return self','return None')
        self.guard.SEALED_VALIDATE_SHA256=hashlib.sha256(source.encode()).hexdigest()
        with patch.object(self.guard.inspect,'getsource',return_value=source):
            with self.assertRaisesRegex(RuntimeError,'sealed_validate_terminal_mismatch'):self.install()

    def test_second_install(self):
        self.install()
        with self.assertRaisesRegex(RuntimeError,'gravity_guard_already_installed'):self.install()

    def test_foreign_exception(self):
        foreign=types.SimpleNamespace(GeometryError=type('GeometryError',(ValueError,),{}),
                                      GeometryContract=GP.GeometryContract)
        with self.assertRaisesRegex(RuntimeError,'gravity_guard_exception_class_mismatch'):
            self.guard.install(foreign,self.guard.Recorder())

    def test_earlier_failure(self):
        contract=geometry('d1/scene0155_00').contract
        bad=np.array(contract.camera_to_world,copy=True)
        bad[0,0,0]+=0.5
        contract=dataclasses.replace(contract,camera_to_world=bad)
        self.install()
        with self.guard.capture('fixture','bad_rotation'):
            with self.assertRaisesRegex(GP.GeometryError,'^camera_rotation_not_proper$'):contract.validate()
        self.assertEqual(self.guard.report(),{})

    def test_inverted_conventions(self):
        contract=geometry('d1/scene0155_00').contract
        base=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
        fixtures={'OpenGL':base@np.diag([1.,-1,-1]),
                  'z_down_world':np.diag([1.,-1,-1])@base,
                  'upside_down':base@np.diag([-1.,-1,1])}
        self.install()
        for name,rotation in fixtures.items():
            with self.subTest(name=name):
                c=np.repeat(np.eye(4)[None],32,axis=0);c[:,:3,:3]=rotation
                fixture=dataclasses.replace(contract,camera_to_world=c)
                with self.guard.capture('inverted',name):
                    with self.assertRaisesRegex(GP.GeometryError,'^reference_camera_up_opposes_gravity$'):
                        fixture.validate()

    def test_five_geometries_unchanged(self):
        names=['d1/scene0155_00','d1/scene0155_01','d1/scene0155_02','d1/scene0166_00','d2/ca3b651c23']
        before={name:geometry(name) for name in names}
        self.install()
        for name in names:
            with self.subTest(native=name),self.guard.capture('dev-S1',name):
                after=geometry(name)
                self.assertEqual(after.identity,before[name].identity)
                for field in ('K','A','C','depth_grid','grid_uv'):
                    self.assertEqual(getattr(after,field).tobytes(),getattr(before[name],field).tobytes())

    def test_near_nadir_passes(self):
        self.install()
        with self.guard.capture('dev-S1','d3/41069053'):
            geometry('d3/41069053')
        value=self.guard.report()['dev-S1']
        self.assertEqual(value['sealed_refused'],['d3/41069053'])
        self.assertEqual(value['reviewed_refused'],[])

    def test_unbound_context_refusal(self):
        self.install()
        with self.assertRaisesRegex(RuntimeError,'gravity_guard_capture_context_missing'):
            geometry('d1/scene0155_00')

    def test_invalid_context(self):
        with self.assertRaisesRegex(RuntimeError,'gravity_guard_capture_identity_missing'):
            with self.guard.capture('', 'x'):pass

    def test_worker_install_refusal_receipt(self):
        import uuid
        dest=B/'work/guard_install_refusal'/uuid.uuid4().hex
        dest.mkdir(parents=True,exist_ok=True)
        source=inspect.getsource(self.original)+'\n'
        with patch.dict(sys.modules,{'gravity_guard':self.guard}),patch.object(self.guard.inspect,'getsource',return_value=source):
            with self.assertRaisesRegex(RuntimeError,'sealed_validate_mismatch'):
                worker.install_gravity_guard(dest)
        self.assertEqual(json.loads((dest/'GUARD_INSTALL_REFUSAL.json').read_text())['error'],'sealed_validate_mismatch')

    def test_all_real_capture_decisions(self):
        self.install()
        outcomes=[]
        for name in sorted(RECORDS):
            with self.guard.capture('dev-S1',name):
                try:
                    geometry(name);status='PASS';error=None
                except GP.GeometryError as exc:
                    self.assertEqual(str(exc),'reference_camera_up_opposes_gravity')
                    status='REFUSED';error={'code':str(exc)}
            outcomes.append(dict(native=name,status=status,error=error))
        import native_metrics as M
        M.validate_gravity_guard(self.guard.report(),{'dev-S1':outcomes})
        (B/'out/GUARD_EXECUTED_CENSUS.json').write_text(json.dumps(dict(
            runtime=sys.version,numpy=np.__version__,identity=self.guard.identity(),
            report=self.guard.report(),dispositions=outcomes),indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
