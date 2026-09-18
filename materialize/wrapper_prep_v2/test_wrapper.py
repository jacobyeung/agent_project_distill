import ast, copy, json, os, unittest
from pathlib import Path
import common as b
import run_batch as run

class WrapperTests(unittest.TestCase):
    def test_plan_counts(self):
        rows=b.load_plan();self.assertEqual(len(rows),b.CONFIG['expected_count'])
        self.assertTrue(all(r['blocking_class'] is None for r in rows))
        self.assertEqual(sum(r['question_count'] for r in rows),b.CONFIG['expected_questions'])
        self.assertIn('992cd74f2c',{r['scene'] for r in rows})
    def test_unauthorized_scene_refused(self):
        p=b.read_json(b.CONFIG['plan']['path']);p['scenes'][0]['scene']='01ce24e652';p['scenes'][0]['work_id']=b.work_id('01ce24e652')
        with self.assertRaisesRegex(ValueError,'outside authorized'):b.parse_plan(p,b.read_json(b.CONFIG['duplicate_census']['path']))
    def test_bad_scene_refused(self):
        for scene in ('../scene','/scene','abc;foo',''):
            with self.assertRaises(ValueError):b.work_id(scene)
    def test_lease_id(self):
        self.assertEqual(b.work_id('01ce24e652'),'preprocess__req232_gt_scene_01ce24e652__train50k__s17__41ade5e4a9')
    def test_plan_duplicate_refused(self):
        p=b.read_json(b.CONFIG['plan']['path']);p['scenes'][1]=p['scenes'][0]
        with self.assertRaises(ValueError):b.parse_plan(p,b.read_json(b.CONFIG['duplicate_census']['path']))
    def test_bad_qid_count(self):
        p=b.read_json(b.CONFIG['plan']['path']);p['scenes'][0]['qids']=[]
        with self.assertRaises(ValueError):b.parse_plan(p,b.read_json(b.CONFIG['duplicate_census']['path']))
    def test_registry_schema_exact(self):
        reference=b.read_json(b.ROOT.parent.parent/'additional_top10_v1/ready/REGISTRY_05.json')
        actual=b.registry(reference['receipts']);self.assertEqual(actual.pop('preparer'),b.CONFIG['preparer']);self.assertEqual(actual,reference)
        self.assertEqual(set(reference['receipts'][0]),{'path','sha256','size_bytes'})
    def test_registry_reviewed_parser(self):
        from collect import registry_rows
        path=b.ROOT.parent.parent/'additional_top10_v1/ready/REGISTRY_05.json'
        self.assertEqual(len(registry_rows({'assets_registry':str(path)})),5)
    def test_validator_membership_arrays(self):
        from mesh_membership import build_memberships,instance_faces
        import numpy as np
        faces=np.array([[0,1,2],[2,3,0]])
        groups=[{'id':1,'segments':[5]},{'id':2,'segments':[5,6]}]
        mesh=build_memberships(faces,np.array([5,6]),groups,True)
        np.testing.assert_array_equal(instance_faces(mesh,1),[0])
        np.testing.assert_array_equal(instance_faces(mesh,2),[0,1])
    def test_source_contract(self):
        self.assertEqual(b.verify_sources()['count'],b.CONFIG['source_file_count'])
    def test_wrapper_contract(self):
        b.verify_scripts()
    def test_live_coord_readonly(self):
        import coordination as c
        store=c.Coord(str(b.COORD))
        wid='preprocess__req232_gt_scene_7efa3f6b1b__train50k__s17__76e67ed6e8'
        record=b.read_json(Path(store.completed_dir(wid))/'lease.json')
        self.assertEqual(record['work_id'],wid);self.assertEqual(record['status'],'completed')
    def test_real_coord_lifecycle(self):
        import coordination as c
        from types import SimpleNamespace
        fixture=b.ROOT/'tests'/f'coord_{os.getpid()}'
        store=c.Coord(str(fixture));store.ensure()
        old=os.environ.get('AGENT_ID');os.environ['AGENT_ID']=b.OWNER
        try:
            wid=b.work_id('fixture')
            won,reason=c.do_claim(store,wid,{'pid':os.getpid()});self.assertTrue(won,reason)
            c.cmd_heartbeat(store,SimpleNamespace(work_id=wid,status=None,note='CPU fixture'))
            c.cmd_complete(store,SimpleNamespace(work_id=wid,result='fixture'))
            self.assertFalse(c.do_claim(store,wid,{'pid':os.getpid()})[0])
            failed=b.work_id('fixturefailed');self.assertTrue(c.do_claim(store,failed,{})[0])
            c.move_lease(store,failed,store.failed,status='failed',ended_at=b.utc())
            self.assertTrue(store.is_failed(failed))
        finally:
            if old is not None:os.environ['AGENT_ID']=old
            else:os.environ.pop('AGENT_ID',None)
    def test_no_deleting_calls(self):
        forbidden={'unlink','rmdir','remove','rmtree','truncate'}
        for file in ('common.py','run_batch.py','validate_scene.py'):
            tree=ast.parse((b.ROOT/file).read_text())
            self.assertFalse([n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in forbidden])

if __name__=='__main__':unittest.main(verbosity=2)
