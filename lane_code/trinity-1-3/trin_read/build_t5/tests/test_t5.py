import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS
import pytest
import trinity_read as T
import paired_read as P


@pytest.fixture(scope='module')
def all_bindings(tmp_path_factory):
    root=tmp_path_factory.mktemp('e193_binds'); result={}
    for family in ('main','camera'):
        for slot in ('step544','cp1m200','f17'):
            work=root/(family+'_'+slot)
            subprocess.run([sys.executable,'-B',str(T.BUILD/'validate_t5_bind.py'),family,slot,str(work)],check=True)
            result[family,slot]=work
    return result


@pytest.mark.parametrize('family', ['main', 'camera'])
@pytest.mark.parametrize('slot', ['step544', 'cp1m200', 'f17'])
def test_e193_cpu_binding(all_bindings, family, slot):
    report = T.load(all_bindings[family,slot]/'BIND_PARITY.json')
    assert report['items'] == (186 if family=='main' else 450)
    assert report['cell_used']['layout']=='duplicate'
    assert report['request_normalized_byte_equal'] and report['prompts_byte_equal'] and report['frames_normalized_byte_equal']
    assert not report['actual_pixels_verified'] and not report['namespace_executed']
    if slot=='f17': assert report['model']['kind']=='archive'


@pytest.mark.parametrize('family', ['main','camera'])
def test_model_identity_only_differences(all_bindings, family):
    from validate_t5_bind import differences
    allowed={'binding','models.cp1m200.path','models.cp1m200.sha256','models.cp1m200.kind',
             'legs1.artifact.path','legs1.artifact.sha256','legs1.step','legs1.name'}
    requests={}
    for slot in ('step544','cp1m200','f17'):
        work=all_bindings[family,slot]
        raw=(work/'direct'/family/'request.json').read_text()
        requests[slot]=json.loads(raw.replace(str(work),'/fixture'))
    observed={}
    for slot in ('cp1m200','f17'):
        changed=differences(requests['step544'],requests[slot])
        assert set(changed)<=allowed
        observed[slot]=changed
        a=all_bindings[family,'step544'];b=all_bindings[family,slot]
        assert (a/'comparison/frames/0.json').read_bytes()==(b/'comparison/frames/0.json').read_bytes()
        assert (a/'direct'/family/'PROMPT_PINS.json').read_bytes()==(b/'direct'/family/'PROMPT_PINS.json').read_bytes()
    T.dump(all_bindings[family,'step544']/'MODEL_PAIRING.json', observed)


@pytest.mark.parametrize('slot,kind,step', [('cp1m200','c1_export',200), ('f17','archive',None)])
def test_registry_selection(tmp_path, slot, kind, step):
    registry = T.physical(tmp_path, P.CAMERA/'models.json')
    registry.parent.mkdir(parents=True)
    registry.write_bytes(T.physical(T.DEFAULT_ROOT, P.CAMERA/'models.json').read_bytes())
    cfg = T.load(T.REFERENCE/'CONFIG.json')
    P.select_model(tmp_path, cfg, slot)
    assert cfg['spec']['artifact']['kind']==kind
    assert cfg['spec']['step']==step
    assert cfg['spec']['models']['cp1m200']==cfg['spec']['artifact']
    assert T.inside(T.physical(tmp_path, cfg['spec']['artifact']['path']), tmp_path)
    registry.write_bytes(registry.read_bytes()+b' ')
    with pytest.raises(ValueError,match='registry changed'): P.select_model(tmp_path,cfg,slot)


@pytest.mark.parametrize('key,value', [('layout','spread'), ('frames',16), ('max_tokens',8192), ('thinking',False), ('model','f17')])
def test_refuse_protocol_change(key,value):
    cfg=P.contract('camera');cfg['cells'][0][key]=value
    with pytest.raises(ValueError,match='protocol differs'): P.validate_protocol(cfg,'camera')


def test_parent_lineage(tmp_path):
    logical=T.FSW/'ap/f2ad01ad/runs/49becb79/m200/artifact.json'
    assert T.logical_artifact(tmp_path,str(T.physical(tmp_path,logical)),200)==str(logical)
    with pytest.raises(ValueError): T.logical_artifact(tmp_path,str(logical),544)


def test_archive_reserve_and_pin(tmp_path,monkeypatch):
    base=T.AP/'base_manifest.json'; archive=T.AP/'f17.tar'
    T.dump(T.physical(tmp_path,base),dict(files=[dict(path='weights.safetensors',bytes=100),dict(path='config.json',bytes=10)]))
    target=T.physical(tmp_path,archive);target.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(target,'w') as tf:
        member=tarfile.TarInfo('weights/model.safetensors');member.size=200
        tf.addfile(member,io.BytesIO(b'x'*200))
    cfg=dict(spec=dict(models=dict(base=dict(manifest=dict(path=str(base),sha256=T.sha(T.physical(tmp_path,base))))),
                       artifact=dict(kind='archive',path=str(archive),sha256=T.sha(target))))
    calls=[];monkeypatch.setattr(T.kit_stage(),'room',lambda root,reserve:calls.append(reserve))
    reserve=T.read_space(tmp_path,cfg,dict(estimated_frame_bytes={'f':50}))
    assert reserve==110+400+10+100+2*1024**3
    assert calls==[reserve]
    cfg['spec']['artifact']['sha256']='0'*64
    with pytest.raises(ValueError,match='pin differs'): T.read_space(tmp_path,cfg,dict(estimated_frame_bytes={}))


def test_archive_checker_does_not_call_export_checker(tmp_path):
    b=P.Bridge.__new__(P.Bridge);b.spec={'artifact':{'kind':'archive'}}
    p=tmp_path/'archive.tar';p.write_bytes(b'fixture')
    assert b.check_export(p,T.sha(p),None,None)['kind']=='archive'
    with pytest.raises(ValueError,match='full-file SHA256'):b.check_export(p,'0'*64,None,None)


def test_export_checker_unchanged():
    b=P.Bridge.__new__(P.Bridge);b.spec={'artifact':{'kind':'c1_export'}}
    calls=[];b.leg=NS(check_export=lambda *a:calls.append(a) or 'verified')
    assert b.check_export('artifact','pin','base',200)=='verified'
    assert calls==[('artifact','pin','base',200)]


def test_keys_and_frame_needs():
    main=T.read_ids(T.BUILD/'KEYS636_main.ids');camera=T.read_ids(T.BUILD/'KEYS636_camera.ids')
    assert len(set(main))==186 and len(set(camera))==450
    assert not set(main)&set(camera)
    ordered=set((T.AREA/'work/NEED_X27.txt').read_text().splitlines())
    assert set(T.read_ids(T.BUILD/'NEED636_camera.txt'))<=ordered
    assert set(T.read_ids(T.BUILD/'NEED636_main.txt'))<=ordered


@pytest.mark.parametrize('extra', [[], ['--model-slot','f17','--artifact','x'], ['--artifact','x','--step','200']])
def test_cli_requires_unambiguous_model(extra):
    cmd=[sys.executable,'-B',str(T.BUILD/'trinity_read.py'),'read','--family','main','--first','1','--gpu','0','--token','a12345678','--out','unused']+extra
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert result.returncode==2 and b'error:' in result.stderr


def test_exact_e193_key_selection():
    from collections import Counter
    from validate_t5_bind import E193
    for family in ('main','camera'):
        selected=[]
        with (E193/'direct'/family/'results/0/budget_2048.jsonl').open() as stream:
            for line in stream:
                row=json.loads(line)
                if family=='camera' or row['question_type'] in ('object_abs_distance','room_size_estimation'):
                    selected.append(row)
        assert sorted(r['example_id'] for r in selected)==T.read_ids(T.BUILD/('KEYS636_'+family+'.ids'))
        if family=='main':
            assert Counter(r['question_type'] for r in selected)==dict(object_abs_distance=150,room_size_estimation=36)


def test_unchanged_kit_archive_prepare_keeps_both_copies(tmp_path):
    import importlib.util
    from fixture_need import RUNTIME
    path=RUNTIME/'rv_merge_fix/work/r3/aws_vl64rt/evaluator/stage.py'
    spec=importlib.util.spec_from_file_location('t5_kit_stage_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    base=tmp_path/'base';base.mkdir()
    (base/'config.json').write_text('{"model_type":"qwen3_5"}')
    (base/'tokenizer_config.json').write_text('{}')
    archive=tmp_path/'f17.tar'
    with tarfile.open(archive,'w') as tf:
        info=tarfile.TarInfo('full_weights/model.safetensors');info.size=7
        tf.addfile(info,io.BytesIO(b'fixture'))
    dest=module.prepare(dict(kind='archive',path=str(archive),sha256=T.sha(archive)),base,tmp_path/'packet/model')
    assert (dest/'a/full_weights/model.safetensors').read_bytes()==b'fixture'
    assert (dest/'model.safetensors').read_bytes()==b'fixture'
    assert (dest/'config.json').read_bytes()==(base/'config.json').read_bytes()
    assert archive.exists()
