import copy
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pytest
import torch
from torch import nn
from h1eval.perception import Heads,OwnPerception,perturb,own_profile
from h1eval import scorers as S
from tests.fixtures import K,camera_fixtures
from student_pilot.carrier_c1_routing import OwnGeometry
from e2e_reader.grounding import StageOneSocket


def sample_heads():
    rows,clip,_=camera_fixtures()
    return Heads(np.array(clip['gt_pose9']),np.array(clip['gt_up']),lambda f,uv:2.+np.asarray(uv)[:,0]*.001,'capture-A')


def socket(frames,geometry):
    def propose(name):
        m=np.zeros((16,16),bool)
        m[3:12,1:6 if name=='chair' else 2]=True if name=='chair' else False
        if name!='chair':m[3:12,10:15]=True
        return [dict(candidate_id=name,masks={3:m,8:m})],torch.tensor([[1.]])
    return StageOneSocket(propose,lambda x:0,(16,16))


FRAMES=dict(capture_id='capture-A',source_hw=(16,16),anchor_indices=list(range(32)))


def call_outputs(mode=None):
    h=sample_heads();p=OwnPerception(socket,mode=mode)
    servers,built=p.lazy(FRAMES,NS(heads=h),{})
    calls=['<move from=1 to=9>','<turn from=2 to=17>','<pose frame=3>',
           '<depth_at frame=3 pts=[[500,500]]>','<ground obj="chair" mode="box">',
           '<ground obj="table" mode="box">','<gap a="chair" b="table" rule="box_grid_5cm">']
    out=[]
    for call in calls:
        name=S.signature(call)[0];text,info=servers[name](call)
        out.append(dict(call=call,response=text,served=True,**info))
    return dict(calls=out),built


def test_own_serves_all_and_profile():
    out,b=call_outputs()
    assert all(not r['response'].startswith('error:') for r in out['calls'])
    assert out['calls'][-1]['response'].startswith('distance ')
    assert b['scale']==1 and b['geometry'].contract.depth_source=='vc'
    assert b['geometry'].contract.profile=='legacy_v3122'
    assert all(r['perception']=='own' for r in out['calls'])


def test_perturb_fields():
    h=sample_heads();uv=np.array([[200,300],[800,500]])
    scaled,a=perturb(h,{'name':'scale_translation','k':2})
    np.testing.assert_array_equal(scaled.pose9[:,3:],h.pose9[:,3:]);np.testing.assert_allclose(scaled.pose9[:,:3],h.pose9[:,:3]*2)
    np.testing.assert_equal(scaled.depth(2,uv),h.depth(2,uv))
    scene,a=perturb(h,{'name':'scale_scene','k':2})
    np.testing.assert_equal(scene.depth(2,uv),h.depth(2,uv)*2)
    turn,a=perturb(h,{'name':'negate_turn'})
    own,new=OwnGeometry(h.pose9,h.gravity,h.depth),OwnGeometry(turn.turn_pose9,turn.gravity,turn.depth)
    assert float(new.turn_text(2,17).split()[2]) == -float(own.turn_text(2,17).split()[2])
    for k in (2,9,17):np.testing.assert_allclose(new.camera(k)[1],own.camera(k)[1],atol=1e-7)
    np.testing.assert_array_equal(turn.pose9,h.pose9)
    rotated,a=perturb(h,{'name':'rotate_translation','deg':90})
    r=OwnGeometry(rotated.pose9,rotated.gravity,rotated.depth)
    assert r.move_text(1,9)!=own.move_text(1,9)
    assert r.turn_text(2,17)==own.turn_text(2,17)
    np.testing.assert_allclose(np.linalg.norm(rotated.pose9[:,:3],axis=1),np.linalg.norm(h.pose9[:,:3],axis=1))
    donor=Heads(h.pose9*1,h.gravity,lambda f,uv:np.ones(len(uv))*7,'capture-B')
    d,a=perturb(h,{'name':'donor'},donor=donor);assert a['donor_capture']=='capture-B'
    assert d.depth(1,uv)[0]==7
    g,a=perturb(scene,{'name':'gt'},gt={'gt_pose9':h.pose9,'gt_up':h.gravity,'depth':h.depth})
    np.testing.assert_array_equal(g.pose9,h.pose9)
    with pytest.raises(ValueError):perturb(h,{'name':'donor'},donor=h)
    base,_=call_outputs();scaled,_=call_outputs({'name':'scale_scene','k':2})
    v,w=S.printed(base['calls'][6]),S.printed(scaled['calls'][6])
    assert abs(w['distance']-v['distance'])>=.20*abs(v['distance'])
    item=dict(question='Distance between chair and table (in meters)?',question_type='object_abs_distance')
    base['text']='<answer>'+str(v['distance'])+'</answer>'
    scaled['text']='<answer>'+str(w['distance'])+'</answer>'
    assert S.usage(base,scaled,item)['follow']==1.0


def record(call,start=4,response='distance 1.00 m'):
    return dict(call=call,response=response,start_token=start,at_token=start+10)


def test_placement_cases():
    item=dict(question='Approximately how far in meters between frame 1 and frame 9 of 32?',question_type='camera_displacement')
    call='<move from=1 to=9>';out=dict(text='Think '+call+' done',calls=[record(call)])
    assert S.placement(out,item)['exact']
    assert S.placement(out,item)['first_call_token_offset']==4
    bad={**out,'calls':[record('<move from=1 to=8>')]};assert S.placement(bad,item)['argument_agreement']==0
    assert S.placement({**out,'text':'<answer>2</answer>'+call},item)['answer_before_first_call']
    direct={**item,'question_type':'object_counting'};assert S.placement(out,direct)['call_rate']==1
    assert S.placement(out,direct)['exact'] is None
    item=dict(question='What is the distance between the chair and the table (in meters)?',question_type='object_abs_distance')
    calls=['<ground obj="chair" mode="box">','<ground obj="table" mode="box">']
    p=S.placement(dict(text=''.join(calls),calls=[record(c) for c in calls]),item)
    assert p['missing_calls']==1 and not p['exact']
    p=S.placement(dict(text=call+call,calls=[record(call),record(call)]),direct)
    assert p['repeated_calls']==1 and p['extra_calls'] is None


def test_scores_units_frames_and_m4():
    item=dict(question='Distance between the chair and the table (in centimeters)?',question_type='object_abs_distance',gt_answer=100)
    c='<gap a="chair" b="table" rule="box_grid_5cm">'
    base=dict(text='<think>x</think><answer>100</answer>',calls=[record(c)])
    changed=dict(text='<think>x</think><answer>200</answer>',calls=[record(c,response='distance 2.00 m')])
    assert S.usage(base,changed,item)['follow']==1
    assert S.usage(base,{**changed,'text':base['text']},item)['stick']==1
    assert S.accuracy(base,item)['calls'][0]['absolute_error_m']==0
    assert not S.answer_equals('2 meters',200)
    h=sample_heads();scores=S.per_frame({'pose9':h.pose9,'gravity':h.gravity,'depth_grid':np.ones((32,2,2))*2},
                                      {'gt_pose9':h.pose9,'gt_up':h.gravity,'gt_depth':np.ones((32,2,2))})
    assert scores['gravity_angle_deg']==0 and scores['depth_absrel']==1
    assert max(x['rotation_error_deg'] for x in scores['frames'])<1e-5
    result=S.benchmark({**base,'finish':'eos'},{'ground_truth':'100','answer_type':'numeric','question_type':'object_abs_distance','options':[]})
    assert result['score']==1

# Use the reader's unchanged real-tokenizer fixture and script processor pattern.
spec=importlib.util.spec_from_file_location('reader_tiny_fixture',Path('/scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
reader.OUT=K/'tmp/b4/h1_reader_proofs';reader.CODE_ROOTS={'reader':K/'h1eval/reader_core/e2e_reader','tree':K/'tree'}
@pytest.fixture(scope='session')
def kit(tmp_path_factory):
    import os
    reuse=os.environ.get('H1_TINY_FIXTURE')
    if not reuse:return reader.kit.__wrapped__(tmp_path_factory)
    from transformers import AutoTokenizer
    from student_pilot.carrier_c1_routing import OPENERS
    from h1eval.items import sha
    root=Path(reuse);tok=AutoTokenizer.from_pretrained(root/'tokenizer',local_files_only=True)
    return dict(root=root,digest=sha(root/'E2E_MANIFEST.json'),tok=tok,
                openers={name:tok.convert_tokens_to_ids(name) for name in OPENERS})


class TinyOwnHeads(nn.Module):
    """Test-only head parameters stored inside the tiny LM; read on each prefill."""
    def __init__(self):
        super().__init__();h=sample_heads()
        self.pose=nn.Parameter(torch.tensor(h.pose9));self.gravity=nn.Parameter(torch.tensor(h.gravity))
        self.depth_bias=nn.Parameter(torch.tensor(2.));self.reads=0
    def forward(self,prefill):
        self.reads+=1
        # A small prefill-dependent translation perturbation exercises in-forward ownership.
        p=self.pose.detach().numpy().copy();p[:,0]+=float(prefill.logits[0,-1,:32].mean())*.001
        return Heads(p,self.gravity.detach().numpy(),lambda f,uv:float(self.depth_bias.detach())+np.asarray(uv)[:,0]*.001,'capture-A')


def generated(kit,mode,kind='all',policy='copier',unchanged=None,perception_factory=None):
    from e2e_reader.generate import generate
    art,model,hook=reader.load(kit);model.add_module('own_heads',TinyOwnHeads())
    class Bound(OwnPerception):
        def lazy(self,frames,prefill,timings):
            return super().lazy(frames,NS(heads=model.own_heads(prefill)),timings)
    if perception_factory is None:
        perception=Bound(socket,mode=mode)
    else:
        model.h10_stage1_socket=socket
        own=perception_factory(art,model,'cpu')
        class Adapt:
            def lazy(self,frames,prefill,timings):
                return own.lazy(frames,NS(heads=model.own_heads(prefill)),timings)
        perception=Adapt()
    tok=kit['tok'];call='<move from=1 to=9>'
    script=(reader.SCRIPT.replace(' and the room <ground mode="room"> so the answer is 1.2','') if kind=='all' else call)
    prefix=tok.encode(script,add_special_tokens=False);queue=list(prefix);last=[]
    item=dict(question='Approximately how far in meters between frame 1 and frame 9 of 32?',question_type='camera_displacement')
    def process(ids,logits):
        if not queue and not last:
            expected=S.program_decision({'calls':hook.report()},item)
            answer=unchanged if policy=='ignorer' else str(expected)
            queue.extend(tok.encode('\n</think>\n<answer>'+str(answer)+'</answer>',add_special_tokens=False)+[tok.eos_token_id]);last.append(True)
        t=queue.pop(0);out=torch.full_like(logits,-1e9);out[...,t]=0;return out
    prompt=tok.encode('<|im_start|>assistant\n<think>\n',add_special_tokens=False)
    out=generate(model,hook,perception,FRAMES,prompt,artifact=art,eos_ids=[tok.eos_token_id],max_new_tokens=2048,logits_processor=process)
    assert model.own_heads.reads==1
    assert not out['audit']['violations']
    return out,item


def test_tiny_own_and_scripted_usage(kit):
    torch.set_num_threads(2)
    all_calls,item=generated(kit,{'name':'none'})
    assert all_calls['finish']=='eos'
    assert len(all_calls['hook']['records'])==6
    assert all(r['served'] and not r['response'].startswith('error:') for r in all_calls['hook']['records'])
    base,item=generated(kit,{'name':'none'},kind='move')
    copier,_=generated(kit,{'name':'scale_translation','k':2},kind='move')
    ignorer,_=generated(kit,{'name':'scale_translation','k':2},kind='move',policy='ignorer',unchanged=S.answer_text(base))
    assert S.usage(base,copier,item)['follow']==1
    assert S.usage(base,ignorer,item)['stick']==1
    (Path(os.environ.get('LANE_TEST_OUTPUT', K/'logs'))/'tiny_usage.json').write_text(json.dumps(dict(copier=S.usage(base,copier,item),ignorer=S.usage(base,ignorer,item)),indent=2)+'\n')
    from h1eval.runner import measure,table
    runs=[]
    for mode,value in [('none',base),('copier_scale_translation',copier),('ignorer_scale_translation',ignorer)]:
        value['seconds']=value['timings']['total_s']
        runs.append(dict(id='tiny-camera',type=item['question_type'],arm='own',mode=mode,output=value,measurements=measure(value,item,None if mode=='none' else base)))
    (Path(os.environ.get('LANE_TEST_OUTPUT', K/'logs'))/'tiny_eval_items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in runs))
    report=table(runs)
    assert 'Head distance MAE' in report and 'copier_scale_translation' in report
    (Path(os.environ.get('LANE_TEST_OUTPUT', K/'logs'))/'tiny_eval_report.md').write_text(report)
