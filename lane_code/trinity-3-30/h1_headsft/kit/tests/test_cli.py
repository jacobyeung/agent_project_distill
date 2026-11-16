import copy
import json
from pathlib import Path
import pytest
from h1eval import items
from h1eval.cli import code_hash, pair, curve, write_curve, main
from h1eval.statistics import bootstrap, paired
from tests.fixtures import K


def test_revsi_manifest(tmp_path):
    result=items.build(tmp_path,sets=['revsi999'])['revsi999']
    assert result['status']=='ready',result
    m=items.load_manifest(tmp_path/'revsi999.json')
    assert m['count']==999 and m['per_type']['object_abs_distance']==283
    assert sum(v for k,v in m['per_type'].items() if k.startswith('room_size'))==37
    assert m['r0_check']['checked']==999 and m['r0_check']['found']==0
    assert items.build(tmp_path,sets=['revsi999'])['revsi999']==result


def test_reserve_refusal_and_stub(tmp_path):
    pin=dict(path=str(items.R0),sha256=items.R0_SHA256)
    reserve=items.Reserve(pin);room=sorted(reserve.rooms)[0]
    row=dict(id='x',room=room,question_type='object_counting',question='How many?')
    source=tmp_path/'source.json';source.write_text(json.dumps([row]))
    with pytest.raises(ValueError,match='overlap R0'):items.manifest('test',[row],source)
    items.build(tmp_path,sets=['r0dev'])
    with pytest.raises(ValueError,match='Supply'):items.load_manifest(tmp_path/'r0dev.json')
    assert main(['items','build','--sets','r0dev','--out',str(tmp_path)])==1


def test_routed_count_contract_and_missing_direct(tmp_path):
    source=tmp_path/'routed.json';source.write_text('[]')
    result=items.build(tmp_path,routed=source,sets=['devs1_routed','devs1_direct'])
    assert result['devs1_routed']['status']=='unavailable'
    assert '636' in result['devs1_routed']['reason']
    assert result['devs1_direct']['status']=='unavailable'
    assert '300' in result['devs1_direct']['reason']


def test_code_hash_tracks_scorer(tmp_path):
    p=tmp_path/'scorers.py';p.write_text('score=1\n');a=code_hash(tmp_path)
    p.write_text('score=2\n');assert code_hash(tmp_path)!=a


def test_pair_refuses_and_curve_order(tmp_path):
    roots=[]
    for i,(lineage,step) in enumerate([('RL',2),('SFT',200),('RL',1),('SFT',100)]):
        root=tmp_path/str(i);root.mkdir();roots.append(root)
        c=dict(lineage=lineage,step=step,export_sha256=str(i),item_set_sha256='same',evaluator_code_sha256='code',frames=32)
        (root/'curve.json').write_text(json.dumps(c));(root/'items.jsonl').write_text('')
    text=curve(roots);assert text.index('| SFT | 100')<text.index('| SFT | 200')<text.index('| RL | 1')<text.index('| RL | 2')
    assert pair(roots[0],roots[1])['per_type']==[]
    c['item_set_sha256']='different';(roots[0]/'curve.json').write_text(json.dumps(c))
    with pytest.raises(ValueError,match='item-set'):pair(roots[0],roots[1])


def test_bootstrap_and_pair_eligibility():
    result=bootstrap([('roomA',0),('roomA',1),('roomB',1)])
    assert result['value']==pytest.approx(2/3) and result['ci95']==[.5,1.]
    assert result==bootstrap([('roomA',0),('roomA',1),('roomB',1)])
    row=dict(id='1',type='camera_rotation',room_key='roomA',arm='own',mode='negate_turn',
             measurements=dict(M1=dict(call_rate=1),M3=dict(eligible=True,follow=1,stick=0)))
    other=copy.deepcopy(row);other['measurements']['M3']=dict(eligible=False)
    out=paired([row],[other])[0]
    assert out['shared_items']==1 and 'M3.follow' not in out['differences']
    assert out['differences']['M1.call_rate']['value']==0


def test_usage_thresholds():
    from h1eval.scorers import usage
    item=dict(question_type='camera_displacement',question='How far in centimeters?')
    def output(number,answer):return dict(calls=[dict(call='<move from=1 to=2>',response=f'dx = 0 m, dy = 0 m, dz = {number} m, distance = {number} m')],text=f'<answer>{answer}</answer>')
    base=output(1,100)
    assert not usage(base,output(1.19,119),item)['eligible']
    assert usage(base,output(1.2,120),item)['follow']==1
    assert usage(base,output(2,104),item)['stick']==1
    assert usage(base,output(2,106),item)['stick']==0
    assert usage(base,output(2,2),item)['follow']==0

# The unchanged reader fixture creates a real local tiny checkpoint.
from tests.test_eval import kit

def test_tiny_cli_curve(kit,tmp_path):
    import torch
    torch.set_num_threads(2)
    root=kit['root']
    loader=K/'tests/eval_fixture.py'
    (root/'h1eval.json').write_text(json.dumps(dict(lineage='RL',step=7,fixture=True,
        loader='tests.eval_fixture:load',loader_sha256=items.sha(loader))))
    item=dict(id='tiny-camera',dataset='scannet',scene='scene9999_00',
              question_type='camera_displacement',question='Approximately how far in meters between frame 1 and frame 9 of 32?')
    src=tmp_path/'source.json';src.write_text(json.dumps([item]))
    manifest=items.manifest('fixture',[item],src)
    file=tmp_path/'items.json';file.write_text(json.dumps(manifest))
    out=tmp_path/'run'
    assert main(['run','--export',str(root),'--items',str(file),'--arms','own','--modes','scale_translation:2','--out',str(out)])==0
    record=json.loads((out/'curve.json').read_text())
    assert record['lineage']=='RL' and record['step']==7 and record['fixture']
    assert record['bootstrap']['draws']==10000
    assert len(record['export_sha256'])==len(record['evaluator_code_sha256'])==64
    m=record['per_type']['camera_displacement']['own']['scale_translation:2']['M3']
    assert m['follow']['value']==1 and m['follow']['ci95']==[1,1]
    assert m['passes_bars']
    (K/'logs/tiny_curve_build2.json').write_text(json.dumps(record,indent=2)+'\n')
    assert main(['pair','--a',str(out),'--b',str(out)])==0
    assert main(['curve',str(out)])==0


def test_native_inventory_counts():
    inventory=json.loads((K/'items_sources/c8r_inventory.json').read_text())
    assert len(inventory['keys'])==len(set(inventory['keys']))==636
    assert inventory['per_type']==dict(camera_displacement=150,camera_movement_direction=150,
        camera_rotation=150,object_abs_distance=150,room_size_estimation=36)


def test_gt_hash_and_arrays(tmp_path):
    import numpy as np
    from h1eval.cli import gt_pins
    from h1eval.native import gt_arrays
    item={'id':'x'};path=tmp_path/(items.digest('x')+'.npz')
    np.savez(path,gt_depth=np.ones((32,2,2)),grid_uv=np.array([0.,1000.]),gt_up=np.array([0.,-1.,0.]))
    a=gt_pins(tmp_path,[item]);data=gt_arrays(tmp_path,item)
    assert data['depth'](1,np.array([[300.,400.]])).tolist()==pytest.approx([1.])
    np.savez(path,gt_depth=np.full((32,2,2),2.))
    assert gt_pins(tmp_path,[item])!=a
