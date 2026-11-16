"""Replay real recorded generations; reject policy, task, and tier mismatches."""
import json,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from routing import *
from scoring import score_item
from native_routed import validate_record

def table():return dict(schema='dev-route-table-v1',dev_sha256=DEV_SHA,checkpoint_sha256=CP1_SHA,
    protocol=PROTOCOL,default='direct',selection='scene-bootstrap-lower95-positive',direct_pin={'path':'/fixture/direct','sha256':'a'*64},routed_pin={'path':'/fixture/routed','sha256':'b'*64},routes={t:dict(action='direct',ci95=[0.,0.]) for t in DEV_TYPES})

class Routing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(s) for s in (ROOT/'inputs/replay_generations.jsonl').read_text().splitlines()]
        cls.tasks=[{k:r[k] for k in ('benchmark','example_id','question_type','ground_truth','options','question','scene_name')} for r in cls.rows]

    def test_real_recorded_generations_replay_scores(self):
        policy=table();typ=self.tasks[0]['question_type'];policy['routes'][typ]=dict(action='routed',ci95=[.01,.1])
        result=replay(self.tasks,self.rows,self.rows,policy,'a'*64)
        self.assertEqual(len(result),len(self.tasks))
        for t,r,source in zip(self.tasks,result,self.rows):
            expected=score_item(t,source['raw_generation'],source['output_tokens'],finish=source['finish_reason'])
            self.assertEqual(r['score'],expected['score']);self.assertEqual(r['response_text'],expected['response_text'])
            self.assertEqual(r['route_action'],'routed' if t['question_type']==typ else 'direct')
        # The chosen branch comes from the table, even if the unchosen score is better.
        bad=[dict(r,raw_generation='</think>\ninvalid',score=100) for r in self.rows]
        forced=replay(self.tasks,bad,self.rows,table(),'a'*64)
        self.assertTrue(all(r['score']==0 for r in forced))

    def test_policy_missing_duplicate_and_tier_rejected(self):
        for change in ({'dev_sha256':'0'*64},{'checkpoint_sha256':'0'*64},{'review_only':True}, {'default':'routed'}):
            with self.assertRaises(ValueError):validate_table({**table(),**change})
        with self.assertRaises(ValueError):replay(self.tasks,[],self.rows,table(),'a'*64)
        with self.assertRaises(ValueError):replay(self.tasks,self.rows+self.rows[:1],self.rows,table(),'a'*64)
        bad=[dict(r,revsi_tier=64) for r in self.rows]
        with self.assertRaises(ValueError):replay(self.tasks,bad,self.rows,table(),'a'*64)
        bad=[dict(r,ground_truth='tampered') for r in self.rows]
        with self.assertRaises(ValueError):replay(self.tasks,bad,self.rows,table(),'a'*64)

    def test_resume_rescores_and_checks_table(self):
        t=self.tasks[0];r=replay([t],self.rows,self.rows,table(),'a'*64)[0];r['binding']='b'
        validate_record(r,t,'b','a'*64,'direct')
        for change in ({'score':999},{'route_table_sha256':'c'*64},{'checkpoint_sha256':'c'*64},{'frames':64}):
            with self.assertRaises(ValueError):validate_record({**r,**change},t,'b','a'*64,'direct')

    def test_freeze_rejects_test_set_and_incomplete_dev(self):
        pin=dict(path=str(ROOT/'inputs/replay_generations.jsonl'),sha256=sha256(ROOT/'inputs/replay_generations.jsonl'))
        with self.assertRaisesRegex(ValueError,'development'):freeze(pin,pin,pin)
        dev=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl'
        with self.assertRaisesRegex(ValueError,'exactly dev noReVSI 741'):freeze(dict(path=str(dev),sha256=sha256(dev)),pin,pin)

    def test_freeze_complete_dev_bootstrap_and_provenance(self):
        dev=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl';rows=[json.loads(s) for s in dev.read_text().splitlines()]
        pins=[]
        for selected in ('direct','routed'):
            path=ROOT/'checks'/f'freeze_fixture_{selected}.jsonl'
            rs=[]
            for t in rows:
                answer='invalid' if selected=='direct' else str(t['ground_truth'])
                rs.append(dict(t,example_id=str(t['id']),benchmark='devrows',status='complete',
                    checkpoint_sha256=CP1_SHA,protocol=PROTOCOL,route_action=selected,
                    raw_generation='</think>\n'+answer,output_tokens=8,finish_reason='stop'))
            path.write_text(''.join(json.dumps(r)+'\n' for r in rs))
            pins.append(dict(path=str(path),sha256=sha256(path)))
        policy=freeze(dict(path=str(dev),sha256=sha256(dev)),*pins)
        self.assertEqual(len(policy['routes']),4)
        self.assertTrue(all(r['action']=='routed' and r['ci95']==[1.,1.] for r in policy['routes'].values()))
        self.assertEqual(policy['direct_pin'],pins[0])

if __name__=='__main__':unittest.main()
