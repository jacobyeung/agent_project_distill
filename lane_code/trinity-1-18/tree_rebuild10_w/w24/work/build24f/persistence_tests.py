from pathlib import Path
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import sys
import unittest
from unittest.mock import patch

L = Path(__file__).resolve().parents[2]
D = L/'work/build24f'
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2 import persistence as P
from student_pilot.checkpoint_space import plan
from student_pilot.p3_provenance import write, file_pin

spec=importlib.util.spec_from_file_location('old_persistence', L/'attic/build24f/persistence.py')
OLD=importlib.util.module_from_spec(spec);spec.loader.exec_module(OLD)
EVIDENCE={}


def fixture(name, kind='export'):
    root=D/'persistence_tests'/name
    state=root/('m1' if kind=='export' else 'checkpoint_000001')
    state.mkdir(parents=True,exist_ok=False)
    recipe=dict(wall_seconds=120,stop_before_seconds=10,resume_every_seconds=30,milestones=[1],export_at_stop=True)
    cfg=dict(output=str(root),recipe=recipe,checkpoint_disk_guard=plan(recipe,0,1),r2_identity={},r1_training={})
    if kind=='export':(state/'w.bin').write_bytes(b'unchanged native export bytes\0'*17)
    if kind=='export':write(state/'artifact.json',dict(step=1,files={'w.bin':file_pin(state/'w.bin')}))
    else:
        bound=dict(synthetic=True);write(root/'binding.json',bound)
        (state/'rng000.pt').write_bytes(b'rng state')
        (state/'shards').mkdir();(state/'shards/rank000.pt').write_bytes(b'native shard boundary')
        files={name:{**file_pin(state/name),'bytes':(state/name).stat().st_size} for name in ('rng000.pt','shards/rank000.pt')}
        write(state/'complete.json',dict(schema='c1-checkpoint-v1',binding=bound,layouts=[{}],step=1,files=files))
    return cfg,state


def records(path,key):
    raw=path.read_bytes();width=(len(raw)+3)//4
    return [dict(name=key+f'.part{i:02d}-of-04',generation=str(i+1),offset=i*width,bytes=len(raw[i*width:(i+1)*width]),sha256=hashlib.sha256(raw[i*width:(i+1)*width]).hexdigest()) for i in range(4)]


class Persistence24F(unittest.TestCase):
    def test_local_checkpoint_and_export_before_after(self):
        for kind in ('checkpoint','export'):
            cfg,state=fixture('local_'+kind,kind)
            with self.assertRaisesRegex(ValueError,'Missing durable state persistence binding'):
                OLD.milestone(cfg,state,kind,distributed=False)
            P.milestone(cfg,state,kind,distributed=False)
            value=P.upload(cfg,state,kind,uploader=lambda *_:self.fail('local path uploaded'))
            self.assertFalse(value['durable']);self.assertEqual(value['parts'],[])
            self.assertEqual(value['source'],file_pin(state/('complete.json' if kind=='checkpoint' else 'artifact.json')))
            EVIDENCE[kind]=value

    def test_explicit_upload_and_identical_export_pins(self):
        cfg,state=fixture('equality')
        local=P.upload(cfg,state,'export')
        original={str(p.relative_to(state)):file_pin(p)['sha256'] for p in state.rglob('*') if p.is_file()}
        cfg['r2_persistence']={'synthetic':True}
        remote=P.upload(cfg,state,'export',records)
        self.assertTrue(remote['durable']);self.assertEqual(local['archive'],remote['archive']);self.assertEqual(local['source'],remote['source'])
        self.assertEqual(original,{str(p.relative_to(state)):file_pin(p)['sha256'] for p in state.rglob('*') if p.is_file()})
        self.assertEqual(OLD.upload(cfg,state,'export',records),remote)
        EVIDENCE['identical_export']=dict(export_files=original,local=local,upload=remote,archive_sha256=local['archive']['sha256'])

    def test_other_combinations_refuse(self):
        cfg,state=fixture('refusals')
        for changes in ({'r2_persistence':None},{'r2_persistence':{}},{'r2_persistence':False}):
            with self.assertRaisesRegex(ValueError,'Missing durable state persistence binding'):
                P.milestone({**cfg,**changes},state,'export',distributed=False)
        cfg.pop('r1_training')
        with self.assertRaisesRegex(ValueError,'Missing durable state persistence binding'):
            P.milestone(cfg,state,'export',distributed=False)
        cfg['r2_persistence']={'synthetic':True}
        self.assertTrue(P.upload(cfg,state,'export',records)['durable'])

    def test_local_native_predicate_and_archive_refusals(self):
        cfg,state=fixture('bad_checkpoint','checkpoint')
        (state/'rng000.pt').write_bytes(b'Rng state')
        with self.assertRaisesRegex(ValueError,'member digest'):P.upload(cfg,state,'checkpoint')
        cfg,state=fixture('no_space')
        with patch.object(P.shutil,'disk_usage',return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError,'reserve'):P.upload(cfg,state,'export')
        cfg,state=fixture('outside')
        cfg['output']=str(state/'elsewhere')
        with self.assertRaisesRegex(ValueError,'outside'):P.upload(cfg,state,'export')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Persistence24F))
    (D/'PERSISTENCE_TESTS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,evidence=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
