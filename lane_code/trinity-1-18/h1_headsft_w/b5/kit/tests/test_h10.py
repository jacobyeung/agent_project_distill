import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace as NS
import pytest
import torch
from h1eval.h10.launch import run, selected, reader_factory, read_records
from h1eval.h10.merge import merge
from h1eval.h10.perception_own import perception_factory
from h1eval.items import manifest, K
from tests.test_eval import sample_heads, socket, FRAMES, kit


class FakeMaker:
    pass


def fake_make_real(export_dir, artifact_manifest, items, *, perception_factory=None, device):
    """Tiny in-memory model, build-1 heads/socket, unchanged reader-shaped outputs."""
    model=torch.nn.Linear(2,2).eval()
    model.h10_stage1_socket=socket
    perception=None if perception_factory is None else perception_factory(NS(),model,device)
    def generate(item):
        model(torch.zeros(1,2))
        if perception is None:
            return dict(text='<answer>tower untouched</answer>',finish='eos',calls=[],timings={'total_s':.001})
        routes,built=perception.lazy(FRAMES,NS(heads=sample_heads()),{})
        calls=[]
        from rows.expected_calls import expected_calls
        from h1eval.scorers import signature
        for call in expected_calls(item['question'],item['question_type']):
            response,info=routes[signature(call)[0]](call)
            calls.append(dict(call=call,response=response,served=True,**info))
        return dict(text='<answer>1.0</answer>',finish='eos',calls=calls,timings={'total_s':.001})
    return generate


@pytest.fixture
def setup(tmp_path):
    items=[]
    for i,(kind,q) in enumerate([
        ('camera_displacement','How far in meters between frame 1 and frame 9?'),
        ('camera_rotation','How much between frame 2 and frame 17?'),
        ('object_abs_distance','Distance between chair and table (in meters)?'),
        ('object_counting','How many chairs?'),
    ]):
        items.append(dict(id=str(i),dataset='scannet',scene='scene9999_00',question_type=kind,question=q))
    src=tmp_path/'source.json';src.write_text(json.dumps(items))
    m=manifest('fixture',items,src);mp=tmp_path/'items.json';mp.write_text(json.dumps(m))
    export=tmp_path/'export';export.mkdir();(export/'tiny.txt').write_text('fixture')
    artifact=tmp_path/'artifact.json';artifact.write_text('{}')
    return NS(items=str(mp),export=str(export),artifact_manifest=str(artifact),reader_root=str(K/'h1eval/reader_core'),
              shard='0/1',arms='own,tower',modes='scale_translation:2',device='cpu',out=str(tmp_path/'out'),
              reader_entry='e2e_reader.real:make_real')


def test_shards_resume_merge(setup,tmp_path):
    a=setup;roots=[];ids=[]
    for i in range(3):
        a.shard=f'{i}/3';a.out=str(tmp_path/f'shard{i}');roots.append(a.out)
        result=run(a,make_real=fake_make_real)
        before=Path(a.out,'items.jsonl').read_bytes()
        assert run(a,make_real=fake_make_real)['added']==0
        assert Path(a.out,'items.jsonl').read_bytes()==before
        rs=read_records(Path(a.out,'items.jsonl'))
        ids.extend(r['id'] for r in rs if r['arm']=='own' and r['mode']=='none')
        towers=[r['output'] for r in rs if r['arm']=='tower']
        assert all(o==dict(text='<answer>tower untouched</answer>',finish='eos',calls=[],timings={'total_s':.001}) for o in towers)
    assert sorted(ids)==['0','1','2','3']
    result=merge(roots,tmp_path/'merged')
    assert result['records']==9 and result['items']==4
    curve=json.loads((tmp_path/'merged/curve.json').read_text())
    assert curve['fixture'] and curve['step']==544
    with pytest.raises(ValueError,match='Missing or duplicate'):merge(roots[:2],tmp_path/'bad')
    a.modes='scale_translation:3'
    with pytest.raises(ValueError,match='binding differs'):run(a,make_real=fake_make_real)


def test_own_all_routes():
    model=torch.nn.Linear(2,2);model.h10_stage1_socket=socket
    p=perception_factory(NS(),model,'cpu',mode={'name':'scale_scene','k':2})
    routes,built=p.lazy(FRAMES,NS(heads=sample_heads()),{})
    for call in ['<move from=1 to=9>','<turn from=2 to=17>','<pose frame=3>',
                 '<depth_at frame=3 pts=[[500,500]]>','<ground obj="chair" mode="box">',
                 '<ground obj="table" mode="box">','<gap a="chair" b="table" rule="box_grid_5cm">']:
        response,info=routes[call.split()[0][1:]](call)
        assert not response.startswith('error:') and info['perception']=='own'
    assert built['scale']==1 and built['geometry'].contract.depth_source=='vc'
    assert set(built['intervention']['changed_fields'])=={'translation','depth'}


def test_busy_card(tmp_path):
    binary=tmp_path/'nvidia-smi';binary.write_text('#!/bin/bash\necho 1025\n');binary.chmod(0o755)
    env={**os.environ,'PATH':str(tmp_path)+os.pathsep+os.environ['PATH']}
    result=subprocess.run(['bash',str(K/'h1eval/h10/run_card.sh'),'0','0/1',str(tmp_path/'out')],env=env,text=True,capture_output=True)
    assert result.returncode==3 and 'busy' in result.stderr and '1025 MiB' in result.stderr
    assert not (tmp_path/'out').exists()


def test_absent_make_real(tmp_path):
    root=tmp_path/'reader';(root/'e2e_reader').mkdir(parents=True)
    (root/'e2e_reader/__init__.py').write_text('')
    (root/'e2e_reader/real.py').write_text('')
    code='from h1eval.h10.launch import reader_factory; reader_factory('+repr(str(root))+')'
    result=subprocess.run(['bash',str(K/'cpu.sh'),'-c',code],capture_output=True,text=True)
    assert result.returncode!=0 and 'make_real is unavailable' in result.stderr


def test_import_from_reader_root(tmp_path):
    root=tmp_path/'reader';(root/'e2e_reader').mkdir(parents=True)
    (root/'e2e_reader/__init__.py').write_text('')
    (root/'e2e_reader/real.py').write_text('def make_real(export_dir, artifact_manifest, items, *, perception_factory=None, device):\n    return lambda item: {"text":"unchanged", "finish":"eos"}\n')
    code='from h1eval.h10.launch import reader_factory; f=reader_factory('+repr(str(root))+'); assert f(None,None,[],device="cpu")({})["text"]=="unchanged"'
    result=subprocess.run(['bash',str(K/'cpu.sh'),'-c',code],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_real_tiny_decode(kit):
    # The build-1 tiny checkpoint runs the real hook/cache loop once through make_real.
    from tests.test_eval import generated
    def make_real(export_dir, artifact_manifest, items, *, perception_factory=None, device):
        assert device=='cpu' and perception_factory is not None
        return lambda item:generated(kit,{'name':'scale_scene','k':2},kind='all',perception_factory=perception_factory)[0]
    generator=make_real(kit['root'],kit['root']/'E2E_MANIFEST.json',[],
                        perception_factory=perception_factory,device='cpu')
    output=generator({})
    assert output['finish']=='eos'
    assert all(r['served'] for r in output['hook']['records'])


def test_resume_after_partial_failure(setup):
    args=setup;args.arms='own'
    state={'fail':True,'calls':0}
    def maker(export_dir,artifact_manifest,items,*,perception_factory=None,device):
        generate=fake_make_real(export_dir,artifact_manifest,items,perception_factory=perception_factory,device=device)
        def read(item):
            state['calls']+=1
            if state['fail'] and state['calls']==2:raise RuntimeError('simulated reader failure')
            return generate(item)
        return read
    with pytest.raises(RuntimeError,match='simulated reader failure'):run(args,make_real=maker)
    completed=read_records(Path(args.out)/'items.jsonl')
    assert len(completed)==1
    state['fail']=False
    result=run(args,make_real=maker)
    assert result==dict(added=4,skipped=1,completed=5,expected=5)
    assert read_records(Path(args.out)/'items.jsonl')[0]==completed[0]
