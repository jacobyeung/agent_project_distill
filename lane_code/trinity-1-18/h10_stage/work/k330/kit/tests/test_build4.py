"""Registered H1 stop, refusal, gate, metric, and decode-plan contracts."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import sqlite3
import pytest
import torch
from student_pilot import h1, h1_faithful as F, carrier_c1_routing as R, carrier_c1_run as run
from student_pilot.p3_provenance import file_pin
from tests.fixtures import camera_fixtures, packed, tiny, routing_batch, Processor, K
from h1eval.modes import DEFAULT_MODES, mode_key, plan, read_counts, applies, TARGETS
from h1eval.cli import modes
from h1eval.statistics import aggregate, paired
from tests.test_h10 import setup, fake_make_real
from h1eval.h10.launch import run as launch, read_records

@pytest.mark.parametrize('kind,own,gt,expected',[
 ('camera_displacement','1.01','1',False),('camera_displacement','1.1','1',False),
 ('camera_displacement','1.1001','1',True),('camera_displacement','0','0',False),
 ('camera_displacement','.01','0',True),('camera_rotation','-179','179',False),
 ('camera_rotation','-170','180',False),('camera_rotation','-169','180',True),
 ('camera_rotation','-180','180',False),('camera_movement_direction','A','A',False),
 ('camera_movement_direction','B','A',True)])
def test_stop_tolerances(kind,own,gt,expected):
    assert F.answer_differs(kind,own,gt)==expected


def test_faithful_training_keeps_own_printed_answer():
    raw,clip,_=camera_fixtures();raw=next(r for r in raw if r['question_type']=='camera_displacement')
    p=torch.tensor(raw['gt_pose9']).numpy();p[:,:3]*=1.01
    out,target,*_=F.faithful(packed(raw,clip),R.OwnGeometry(p,raw['gt_up'],None))
    assert out['answer']!=raw['answer']  # Do not snap the faithful training answer to GT.
    assert not F.answer_differs(raw['question_type'],out['answer'],raw['answer'])
    assert str(out['answer']) in target


def test_counts_reduce_across_ranks():
    shapes=[{'h1':dict(type='camera_rotation',values='own',answer_differs=True)},
            {'h1':dict(type='camera_rotation',values='gt',answer_differs=True)},
            {'h1':dict(type='room_size',values='own',answer_differs=True)}]
    def remote(tensor):tensor.add_(torch.tensor([1,4]))
    with patch.object(torch.distributed,'all_reduce',side_effect=remote) as reduce:
        value=h1.global_answer_counts(shapes,torch.device('cpu'),True)
    reduce.assert_called_once();assert value==dict(answer_differs=2,own=5,share=.4)


def test_stop_window_resume_and_threshold(tmp_path):
    state=h1.AnswerStop();records=[]
    for step in range(1,101):
        counts=dict(answer_differs=8 if step<=50 else 0,own=20,share=.4 if step<=50 else 0.)
        value=state.update(step,counts)
        assert value['triggered']==(step>=50)
        records.append(dict(step=step,ranks=[dict(h1_answer_counts=counts)]*4))
    (tmp_path/'metrics_cpu.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    resumed=h1.AnswerStop();assert resumed.replay(tmp_path,80)['window_share']==.4
    with pytest.raises(ValueError,match='Missing'):h1.AnswerStop().replay(tmp_path,101)
    boundary=h1.AnswerStop()
    for step in range(1,51):value=boundary.update(step,dict(answer_differs=7,own=20))
    assert not value['triggered']


def test_native_registered_stop_exports_100_and_never_requeues(tmp_path):
    cfg=json.loads((K/'configs/h1_1.json').read_text());cfg['output']=str(tmp_path);cfg['first_step_admission']=None
    model=NS(depth_stage1=False);calls=[]
    def optimize(*args):
        step=args[6];calls.append(step)
        return dict(wall_seconds=.001,head_metrics={},h1_answer_counts=dict(answer_differs=1,own=2,share=.5)),None
    def export(directory,*args,**kw):directory.mkdir();(directory/'artifact.json').write_text('{}')
    counts=dict(pose=8,vqa=8,routing=8,pointing=8)
    with patch.object(run,'optimize_step',side_effect=optimize),patch.object(run,'checkpoint'), \
         patch.object(run,'export',side_effect=export),patch.object(run,'existing_export',return_value=False):
        report=run.run_steps(model,model,None,NS(),counts,tmp_path,cfg,{},torch.device('cpu'),distributed=False)
    assert calls==list(range(1,101))
    assert report['last_step']==100 and report['status']=='H1_STOP' and not report['stopped_for_resume']
    assert report['stop_reason']==h1.STOP_RULE
    stop=json.loads((tmp_path/'h1_stop_000100.json').read_text())
    assert stop['stop_state']['window_share']==.5 and stop['lr_horizon']==1000
    assert (tmp_path/'m100/artifact.json').exists() and not (tmp_path/'m200').exists()
    with patch.object(run,'optimize_step') as opt,patch.object(run,'export') as exp, \
         patch.object(run,'existing_export',return_value=True):
        report=run.run_steps(model,model,None,NS(),counts,tmp_path,cfg,{},torch.device('cpu'),start_step=100,distributed=False)
    opt.assert_not_called();exp.assert_not_called();assert report['status']=='H1_STOP'


@pytest.mark.parametrize('error',[F.MaterializeRefusal('fixture'),R.RenderError('fixture'),ValueError('fixture'),
                                  KeyError('fixture'),StopIteration(),IndexError('fixture')])
def test_every_row_failure_trains_gt_and_joins_flag(error):
    raw,clip,_=camera_fixtures();row=packed(raw[0],clip);model,base,_=tiny();batch,audit=routing_batch(base,row)
    class Rows:
        h1={'faithful_own_camera_rows':True};processor=Processor()
        def row(self,*args):return row,None
    with patch.object(R,'encode_own',side_effect=error),patch.object(torch.distributed,'is_initialized',return_value=True), \
         patch.object(torch.distributed,'all_reduce') as reduce:
        result,audit=run.own_values(model,Rows(),batch,audit,0,(True,True),torch.device('cpu'))
    reduce.assert_called_once();assert result is batch
    assert audit['h1']['values']=='gt' and audit['h1']['refused'] and audit['h1']['any_rank_refused']
    model(result,None,stream='routing')['loss'].backward()
    assert model.lm_head.weight.grad is not None


def test_row_lookup_refusal_still_reads_and_reduces():
    model,base,_=tiny();raw,clip,_=camera_fixtures();row=packed(raw[0],clip);batch,audit=routing_batch(base,row)
    class Rows:
        h1={'faithful_own_camera_rows':True};processor=Processor()
        def row(self,*args):raise IndexError('missing local row')
    with patch.object(torch.distributed,'is_initialized',return_value=True),patch.object(torch.distributed,'all_reduce') as reduce:
        result,audit=run.own_values(model,Rows(),batch,audit,0,(True,True),torch.device('cpu'))
    assert result is batch and audit['h1']['refused'];reduce.assert_called_once()


def test_step2_own_draw():
    cfg=json.loads((K/'configs/h1_1.json').read_text());g=R.Gates(cfg['recipe']['scheduled_sampling'],False)
    factor=cfg['recipe']['reference_world_size']//cfg['recipe']['world_size']
    groups={i//factor for i,s in enumerate(cfg['recipe']['mix']) if s=='routing'}
    assert not any(g.decide(1,i)[1] for i in groups)
    assert any(g.decide(2,i)[1] for i in groups)


def test_identity_gate_rows_sqlite_and_preparation(tmp_path):
    raw,clip,_=camera_fixtures();rows=[packed(r,clip) for r in raw]
    db=tmp_path/'rows.sqlite'
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
        con.executemany('INSERT INTO rows VALUES(?,?)',[(i,json.dumps(r)) for i,r in enumerate(rows)])
    src=tmp_path/'routing.json';src.write_text(json.dumps(dict(database=file_pin(db))))
    cfg=dict(h1=dict(faithful_own_camera_rows=True),streams=dict(routing=file_pin(src)),preparation_output=str(tmp_path))
    prepared=F.prepare_identity({},cfg)
    assert prepared['h1_faithful_identity']['identity_rate']==1.
    assert prepared['h1_faithful_identity']['rows']==12
    F.require_identity(prepared,cfg)
    bad=copy.deepcopy(cfg);bad['streams']['routing']['sha256']='0'*64
    with pytest.raises(ValueError):F.require_identity(prepared,bad)
    with sqlite3.connect(db) as con:
        broken=rows[0];broken['routing']['trace_revision']='unsupported'
        con.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(broken),))
    src.write_text(json.dumps(dict(database=file_pin(db))));cfg['streams']['routing']=file_pin(src)
    with pytest.raises(ValueError,match='95%'):F.prepare_identity({},cfg)
    report=json.loads((tmp_path/'receipt.json').read_text())['h1_faithful_identity']
    assert report['refused']==1 and report['identity_rate']==11/12
    assert F.prepare_identity({},dict(h1={}))=={}


def test_registered_mapping_counts_and_keys():
    ms=[{'name':'none'},*modes(DEFAULT_MODES)]
    for name,target in TARGETS.items():
        mode=next(m for m in ms if m['name']==name)
        for kind in [*TARGETS.values(),'object_counting','room_size']:
            assert applies(mode,dict(question_type=kind))==(kind==target)
    dev=json.loads((K/'items/devs1_routed.json').read_text())['items']
    rev=json.loads((K/'items/revsi999.json').read_text())['items']
    assert read_counts(dev,ms)==dict(own_baseline=636,own_perturbed=900,tower=636,tower_reused=0,reads=2172)
    assert read_counts(rev,ms)==dict(own_baseline=999,own_perturbed=566,tower=999,tower_reused=0,reads=2564)
    assert read_counts(dev,ms,tower_reused=True)['reads']==1536
    assert len(plan(dev,['own','tower'],ms))==2172
    assert {mode_key(m) for m in modes('scale_translation:0.5,scale_translation:2')}=={'scale_translation:0.5','scale_translation:2'}
    with pytest.raises(ValueError,match='Duplicate'):modes('scale_translation:2,scale_translation:2.0')


def metric_row(id='a',kind='camera_displacement',arm='own',score=1.,calls=1.,exact=True,before=False,set_name='fixture'):
    return dict(id=id,room_key='room'+id,type=kind,arm=arm,mode='none',item_set=set_name,
        measurements=dict(M1=dict(call_rate=calls,exact=exact,answer_before_first_call=before,
                                  false_call_rate=calls if kind=='object_counting' else None),
                          M2=dict(task_accuracy=score,calls=[]),M4=dict(score=score)))


def test_m1_and_m2_bars_and_paired_modes():
    own=metric_row(score=.94);tower=metric_row(arm='tower',score=1.)
    record=aggregate([own,tower])['camera_displacement']['own']['none']
    assert record['M1']['passes_bars'] and not record['M2']['passes_bars']
    assert record['M2']['own_minus_tower']['value']==pytest.approx(-6)
    own['measurements']['M2']['task_accuracy']=.96
    assert aggregate([own,tower])['camera_displacement']['own']['none']['M2']['passes_bars']
    own['measurements']['M1']['answer_before_first_call']=True
    assert not aggregate([own,tower])['camera_displacement']['own']['none']['M1']['passes_bars']
    direct=[metric_row(str(i),kind='object_counting',calls=float(i==0)) for i in range(40)]
    m=aggregate(direct)['object_counting']['own']['none']['M1']
    assert m['pass_flags']['per_type'] and not m['pass_flags']['overall']
    rev=[metric_row(str(i),kind='object_abs_distance',calls=float(i<96),set_name='revsi999') for i in range(100)]
    assert aggregate(rev)['object_abs_distance']['own']['none']['M1']['passes_bars']
    for r in rev:r['item_set']='devs1_routed'
    assert not aggregate(rev)['object_abs_distance']['own']['none']['M1']['passes_bars']
    rows=[{**metric_row(),'mode':key} for key in ('scale_translation:0.5','scale_translation:2')]
    assert len(paired(rows,rows))==2


@pytest.mark.parametrize('mismatch',[None,'export_sha256','item_set_sha256','items_sha256','reader_sha256','artifact_manifest_sha256'])
def test_tower_reuse_and_hash_refusal(setup,tmp_path,mismatch):
    args=setup;args.arms='tower';args.out=str(tmp_path/'parity')
    launch(args,make_real=fake_make_real)
    parity=Path(args.out);env=json.loads((parity/'environment.json').read_text())
    if mismatch:env['binding'][mismatch]='0'*64;(parity/'environment.json').write_text(json.dumps(env))
    args.out=str(tmp_path/'own');args.arms='own,tower';args.tower_from=str(parity)
    if mismatch:
        with pytest.raises(ValueError,match='hash mismatch'):launch(args,make_real=fake_make_real)
    else:
        def own_only(*a,**kw):
            assert kw['perception_factory'] is not None
            return fake_make_real(*a,**kw)
        assert launch(args,make_real=own_only)['expected']==9
        rows=read_records(Path(args.out)/'items.jsonl')
        assert len([r for r in rows if r.get('reused')])==4
        assert launch(args,make_real=own_only)['added']==0


def test_r0_rejects_unregistered_digest(tmp_path):
    from student_pilot.h1_r0 import Reserve
    p=tmp_path/'rooms';p.write_text('scannet/scene0001\n')
    with pytest.raises(ValueError,match='R0_SHA256'):Reserve(file_pin(p))


def test_first_ten_projection_and_resume(setup,tmp_path):
    from h1eval.items import manifest
    args=setup;original=json.loads(Path(args.items).read_text())['items'][0]
    items=[{**original,'id':str(i)} for i in range(12)]
    src=tmp_path/'twelve_source.json';src.write_text(json.dumps(items))
    Path(args.items).write_text(json.dumps(manifest('fixture',items,src)))
    args.arms='own';args.modes='none'
    result=launch(args,make_real=fake_make_real)
    report=json.loads((Path(args.out)/'projection.json').read_text())
    assert result['added']==12 and report['sample_items']==10
    assert report['read_plan']['reads']==12
    assert report['expected_card_hours']==pytest.approx(12*report['seconds_per_read']/3600)
    assert launch(args,make_real=fake_make_real)['added']==0
    assert json.loads((Path(args.out)/'projection.json').read_text())==report


def test_unserved_call_preserves_answer_accuracy():
    from h1eval.scorers import accuracy
    item=dict(question_type='camera_displacement',question='How far in meters from frame 1 to frame 9?',ground_truth='1')
    output=dict(text='</think><answer>1</answer>',finish='eos',calls=[])
    assert accuracy(output,item)['task_accuracy']==1.
    output['calls']=[dict(call='<move from=1 to=9>',response='distance unavailable',served=False)]
    assert accuracy(output,item)['task_accuracy']==1.


def test_remote_refusal_flag_keeps_local_collective_path():
    raw,clip,_=camera_fixtures();row=packed(raw[0],clip);model,base,_=tiny();batch,audit=routing_batch(base,row)
    class Rows:
        h1={'faithful_own_camera_rows':True};processor=Processor()
        def row(self,*args):return row,None
    def remote_failure(flag,op):
        assert op==torch.distributed.ReduceOp.MAX
        flag.fill_(1)
    with patch.object(torch.distributed,'is_initialized',return_value=True), \
         patch.object(torch.distributed,'all_reduce',side_effect=remote_failure):
        result,audit=run.own_values(model,Rows(),batch,audit,0,(False,False),torch.device('cpu'))
    assert result is batch and audit['h1']['any_rank_refused'] and audit['h1']['refused'] is None
    model(result,None,stream='routing')['loss'].backward()
