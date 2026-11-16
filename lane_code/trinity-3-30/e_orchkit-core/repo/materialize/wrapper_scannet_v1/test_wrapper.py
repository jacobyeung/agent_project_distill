import ast, copy, json, os, unittest
from pathlib import Path
import common as b
import run_batch as run

class WrapperTests(unittest.TestCase):
    def test_plan_counts(self):
        rows=b.load_plan();self.assertEqual(len(rows),234)
        supported=[r for r in rows if r['blocking_class'] is None]
        self.assertEqual(len(supported),233);self.assertEqual(sum(r['question_count'] for r in rows),12662)
    def test_known_refusal_not_retried(self):
        rows=b.load_plan();blocked=[r for r in rows if r['blocking_class']]
        self.assertEqual([r['scene'] for r in blocked],['scene0001_00'])
        self.assertEqual(blocked[0]['blocking_class'],'all_32_sensor_ordinals')
    def test_blocked_execution_refused(self):
        for row in b.load_plan():
            if row['blocking_class']:
                with self.assertRaisesRegex(ValueError,'blocked scene'):b.scene_plan(row['scene'])
    def test_bad_scene_refused(self):
        for scene in ('../scene','/scene','abc;foo',''):
            with self.assertRaises(ValueError):b.work_id(scene)
    def test_lease_id(self):
        self.assertEqual(b.work_id('01ce24e652'),'preprocess__req232_gt_scene_01ce24e652__train50k__s17__b9a4226662')
    def test_plan_duplicate_refused(self):
        p=b.read_json(b.CONFIG['plan']['path']);p['scenes'][1]=p['scenes'][0]
        with self.assertRaises(ValueError):b.parse_plan(p,b.read_json(b.CONFIG['duplicate_census']['path']))
    def test_bad_qid_count(self):
        p=b.read_json(b.CONFIG['plan']['path']);p['scenes'][0]['qids']=[]
        with self.assertRaises(ValueError):b.parse_plan(p,b.read_json(b.CONFIG['duplicate_census']['path']))
    def test_registry_schema_exact(self):
        reference=b.read_json(b.ROOT.parent.parent/'additional_top10_v1/ready/REGISTRY_05.json')
        self.assertEqual(b.registry(reference['receipts'])['receipts'],reference['receipts']); self.assertEqual(b.registry([])['preparer']['version'],'scannet_v1')
        self.assertEqual(set(reference['receipts'][0]),{'path','sha256','size_bytes'})
    def test_registry_reviewed_parser(self):
        from collect import registry_rows
        path=b.ROOT.parent.parent/'additional_top10_v1/ready/REGISTRY_05.json'
        self.assertEqual(len(registry_rows({'assets_registry':str(path)})),5)
    def test_source_contract(self):
        self.assertEqual(b.verify_sources()['count'],46)
    def test_wrapper_contract(self):
        b.verify_scripts()
    def test_live_coord_readonly(self):
        import coordination as c
        store=c.Coord(str(b.COORD))
        records=list(Path(store.completed).glob('*.lock/lease.json'))
        self.assertTrue(records)
        record=b.read_json(records[0]);self.assertIn('work_id',record);self.assertEqual(record['status'],'completed')
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
