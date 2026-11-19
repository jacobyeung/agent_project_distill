"""Same-process admission and pinned N-side room-removal boundaries."""
from pathlib import Path
import os, unittest, json, sqlite3
from copy import deepcopy
from tests.test_r2_build_n1 import write
from student_pilot.p3_provenance import load,pinned,file_pin

class Admission18(unittest.TestCase):
    def test_repeated_admission_thread_setup(self):
        from student_pilot.s1_admission import admit
        root=Path(os.environ['R2_PROOFS'])/'threads18';root.mkdir(parents=True,exist_ok=True)
        pin=write(root/'config.json',{})
        for _ in range(2):
            with self.assertRaisesRegex(ValueError,'four- or eight-rank'):
                admit(pin,root,[str(root)],threads=1,memory_gib=16,prepare_only=True)

class Rooms18(unittest.TestCase):
    def setUp(self):
        from student_pilot import r1_rooms
        self.R=r1_rooms
        lane=Path(os.environ['R2_LANE_ROOT'])
        self.cfg=load(lane/'work/build18/inputs/config.json')
        self.audit=load(pinned(self.cfg['r1_training']['room_audit']))
        self.root=Path(os.environ['R2_PROOFS'])/'rooms18';self.root.mkdir(parents=True,exist_ok=True)

    def check(self,cfg,audit):
        return self.R.verify_audit(cfg,write(self.root/'audit.json',audit))

    def test_exact_bound_list_and_unknown_scope(self):
        result=self.check(self.cfg,self.audit)
        pin=self.cfg['r1_training']['v7_k1_removal']
        rows=[json.loads(line) for line in pinned(pin).read_text().splitlines()]
        self.assertEqual(pin['sha256'],self.R.V7_K1_LIST)
        self.assertEqual(len(rows),2637);self.assertEqual(len({r['row_key'] for r in rows}),2637)
        rooms=self.R.Rooms(self.cfg['r1_training']['room_authority'])
        self.assertTrue(all(set(r)=={'row_key','canonical','reason'} and r['reason']=='k1_heldout_v7'
            and rooms.status(r)[0]=='k1_heldout' for r in rows))
        self.assertEqual(result['store']['unremoved_hits'],0)
        self.assertEqual(result['store']['unresolved'],119375)
        self.assertIn('admitted by P',result['certifies'])
        self.assertIn('not declared overlap-free',result['certifies'])

    def test_missing_v7_list_refuses(self):
        cfg=deepcopy(self.cfg);audit=deepcopy(self.audit)
        cfg['r1_training'].pop('v7_k1_removal')
        with self.assertRaisesRegex(ValueError,'V7_K1_REMOVAL_REQUIRED'):self.check(cfg,audit)
        cfg=deepcopy(self.cfg)
        cfg['remove_files']=[p for p in cfg['remove_files'] if p['sha256']!=self.R.V7_K1_LIST]
        audit['remove_files']=cfg['remove_files']
        with self.assertRaisesRegex(ValueError,'V7_K1_REMOVAL_REQUIRED'):self.check(cfg,audit)

    def test_order_and_duplicate_refuse(self):
        for duplicate in (False,True):
            cfg=deepcopy(self.cfg);audit=deepcopy(self.audit)
            pin=cfg['r1_training']['v7_k1_removal']
            if not duplicate:cfg['remove_files']=[p for p in cfg['remove_files'] if p['sha256']!=pin['sha256']]
            cfg['remove_files'].append(pin);audit['remove_files']=cfg['remove_files']
            with self.assertRaisesRegex(ValueError,'V7_K1_REMOVAL_REQUIRED'):self.check(cfg,audit)

    def test_repin_or_omitted_audit_binding_refuses(self):
        cfg=deepcopy(self.cfg);audit=deepcopy(self.audit)
        pin=cfg['r1_training']['v7_k1_removal'];rows=pinned(pin).read_text().splitlines()
        path=self.root/'changed.json';path.write_text('\n'.join(rows[:-1])+'\n');bad=file_pin(path)
        cfg['r1_training']['v7_k1_removal']=bad
        cfg['remove_files']=[bad if p['sha256']==pin['sha256'] else p for p in cfg['remove_files']]
        audit['remove_files']=cfg['remove_files'];audit['store']['k1_removal']=bad
        with self.assertRaisesRegex(ValueError,'V7_K1_REMOVAL_REQUIRED'):self.check(cfg,audit)
        audit=deepcopy(self.audit);audit['store'].pop('k1_removal')
        with self.assertRaisesRegex(ValueError,'V7_K1_REMOVAL_REQUIRED'):self.check(self.cfg,audit)

    def test_unremoved_v7_refuses(self):
        for value in (1,None):
            audit=deepcopy(self.audit);audit['store']['unremoved_hits']=value
            with self.assertRaisesRegex(ValueError,'V7_K1_UNREMOVED'):self.check(self.cfg,audit)

    def test_census_collects_keys_and_retains_unresolved(self):
        cfg=deepcopy(self.cfg)
        empty=self.root/'empty.jsonl';empty.write_text('')
        cfg['r1_training']['row_sources']=write(self.root/'sources.json',{k:dict(source=file_pin(empty)) for k in ('recovery','units','absolute_distance')})
        rows=[dict(qid='fixture_hit',canonical='arkitscenes/41069175'),dict(qid='fixture_unknown',dataset='d1',scene='unknown')]
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
        db.executemany('INSERT INTO rows VALUES(?,?)',[(i,json.dumps(row)) for i,row in enumerate(rows)]);db.commit()
        path=self.root/'store.sqlite';path.write_bytes(db.serialize());db.close()
        cfg['streams']['vqa']=write(self.root/'vqa.json',dict(database=file_pin(path)))
        hits=[];audit,_=self.R.census(cfg,store_hits=hits)
        self.assertEqual(hits,[dict(row_key='fixture_hit',canonical='arkitscenes/41069175',reason='k1_heldout_v7')])
        self.assertEqual(audit['store']['unremoved_hits'],1);self.assertEqual(audit['store']['unresolved'],1)
