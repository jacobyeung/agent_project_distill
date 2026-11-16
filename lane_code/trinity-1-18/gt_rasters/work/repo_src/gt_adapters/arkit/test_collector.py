"""Focused local tests for teacher admission and offline keeper semantics."""
import copy,json,unittest
from census import grade,select_attempt,recorded_cap,mechanically_complete,perceptual_evidence
from training_assets import bind_runtime_row,teacher_rows


def record(answer,finish='STOP'):
    usage={'input_tokens':10,'output_tokens':20,'total_tokens':30}
    raw={'id':'a1','content':f'<ANSWER>{answer}</ANSWER>','tool_calls':[],
        'response_metadata':{'finish_reason':finish},'usage_metadata':usage}
    ai={'role':'ai','provenance':'provider',**copy.deepcopy(raw),'raw_response':copy.deepcopy(raw)}
    initial=[{'role':'system','content':'fixture'},{'role':'human','content':'fixture'}]
    call={'status':'ok','family':'planner','call_index':1,'attempt_index':1,'finish_reason':finish,
        'usage':usage,'raw_response':copy.deepcopy(raw),'served_model':'gemini-3.1-pro-preview',
        'request_controls':{'model':'gemini-3.1-pro-preview'}}
    return {'trace':initial+[ai],'pred_source':'answer_tag','budget_terminal':finish=='MAX_TOKENS',
        'error':None,'orphan_tool_drop':False,'discarded_message_history':{'schema':'r1308-discarded-message-history-v1','recoveries':[]},
        'tool_telemetry':[],'native_google_provider_calls':[],'native_google_tool_responses':[],'tool_vlm_responses':[],'llm_usage':{'planner':{'calls_detail':[call]}}}


def attempt(trace,budget):return {'trace':trace,'budget':budget,'trace_path':'fixture','trace_sha256':'fixture','archive_complete':True}


class Tests(unittest.TestCase):
    def test_units_and_choices(self):
        row={'question_type':'object_abs_distance','question':'How far in meters?'}
        self.assertTrue(grade(row,'4','4.2')[0]);self.assertFalse(grade(row,'4','4 feet')[0])
        self.assertFalse(grade(row,'4','4.3')[0])
        area={'question_type':'room_size_estimation','question':'What is the area in square feet?'}
        self.assertTrue(grade(area,'100','100 ft2')[0]);self.assertFalse(grade(area,'100','100 m2')[0])
        count={'question_type':'object_counting','question':'How many?'}
        self.assertFalse(grade(count,'7','6')[0]);self.assertTrue(grade(count,'7','7')[0])
        mc={'question_type':'object_rel_distance','question':'Which?','options':['left','right'],'option_letters':['A','B']}
        self.assertTrue(grade(mc,'B','B')[0]);self.assertFalse(grade(mc,'B','D')[0])
    def test_budget_selection(self):
        row={'question_type':'object_counting','question':'How many?'}
        wrong=record('6','MAX_TOKENS');right=record('7')
        self.assertTrue(select_attempt(row,'7',[attempt(wrong,16384)])['needs_topup'])
        self.assertFalse(select_attempt(row,'7',[attempt(record('7','MAX_TOKENS'),16384)])['needs_topup'])
        self.assertFalse(select_attempt(row,'7',[attempt(record('6'),16384)])['needs_topup'])
        chosen=select_attempt(row,'7',[attempt(wrong,16384),attempt(right,32768)])
        self.assertEqual(chosen['chosen_budget'],32768);self.assertFalse(chosen['needs_topup']);self.assertFalse(chosen['accepted']);self.assertTrue(chosen['answer_correct'])
        self.assertTrue(mechanically_complete(right))
        with self.assertRaises(ValueError):select_attempt(row,'7',[attempt(wrong,16384),attempt(wrong,16384)])
        inconsistent=record('6');inconsistent['budget_terminal']=True
        self.assertFalse(select_attempt(row,'7',[attempt(inconsistent,16384)])['needs_topup'])
    def test_bad_native_binding_refused(self):
        trace=record('7');trace['trace'][-1]['content']='<ANSWER>6</ANSWER>'
        self.assertFalse(mechanically_complete(trace))
        trace=record('7');trace['trace'][-1]['tool_calls']=[{'id':'orphan','name':'fixture','args':{}}]
        self.assertFalse(mechanically_complete(trace))
    def test_perceptual_eligibility(self):
        trace=record('7');self.assertEqual(perceptual_evidence(trace),[])
        evidence=[{'role':'ai','provenance':'provider','tool_calls':[{'id':'t1','name':'get_world_3d_point_from_2d','args':{}}]},
            {'role':'tool','tool_call_id':'t1','content':'[1.0, 2.0, 3.0]'}]
        trace['trace'][2:2]=evidence
        self.assertEqual(len(perceptual_evidence(trace)),1)
        trace['trace'][3]['content']='["Error: no valid pixels"]';self.assertEqual(perceptual_evidence(trace),[])
        trace['trace'][3]['content']='[1,2,3]';trace['trace'][2]['tool_calls'][0]['name']='execute_python_code'
        self.assertEqual(perceptual_evidence(trace),[])
        trace['trace'][2]['tool_calls'][0]['name']='get_frame_image';trace['trace'][3]['content']='/data2/frame.png'
        self.assertEqual(perceptual_evidence(trace),[])
    def test_runtime_worker_delta_controls_actual_claims(self):
        import time
        from pathlib import Path
        from collect import resize_workers,initialize
        from training_assets import DATA_ROOT
        from pool_harness.state import TargetStore,PoolConfig,EpisodeQueue,EpisodeCatalog,Episode,ClaimOutcome
        root=DATA_ROOT/'capacity_fixtures'/str(time.time_ns())
        target=TargetStore(root,PoolConfig('fixture',8));initialize(target,0)
        queue=EpisodeQueue(root,EpisodeCatalog([Episode('first','scene',{}),Episode('second','scene',{})]),target,lambda item:False)
        self.assertEqual(queue.claim_next('worker0',0).outcome,ClaimOutcome.RETIRE)
        self.assertEqual(resize_workers(target,delta=1),1)
        self.assertEqual(queue.claim_next('worker0',0).outcome,ClaimOutcome.CLAIMED)
        self.assertEqual(resize_workers(target,delta=1),2)
        self.assertEqual(queue.claim_next('worker1',1).outcome,ClaimOutcome.CLAIMED)
        self.assertEqual(resize_workers(target,delta=-1),1)
        self.assertEqual(queue.claim_next('worker1',1).outcome,ClaimOutcome.RETIRE)
    def test_teacher_input(self):
        rows=teacher_rows();self.assertEqual(len(rows),50000)
        source=rows[0];bound=bind_runtime_row(source,{'dataset':source['dataset'],'scene_name':source['scene_name']})
        self.assertEqual(bound['question'],source['question']);self.assertEqual(bound.get('options'),source.get('options'))
        with self.assertRaises(ValueError):bind_runtime_row(source,{'dataset':'wrong','scene_name':source['scene_name']})

if __name__=='__main__':unittest.main()
