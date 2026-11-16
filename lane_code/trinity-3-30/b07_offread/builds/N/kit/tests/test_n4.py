from copy import deepcopy
import io,json,os,subprocess,sys,tarfile
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from test_n3 import clips
from offnative.io import dump,load,sha,digest,rows
from offnative.paths import ROOT

@pytest.fixture
def real_frames(tmp_path,clips):
    from offnative.production import Runtime
    from offnative.source import bind_source
    from offkit.frames import bind_frames
    root,mapping,_=clips;p=tmp_path/'mapping.json';dump(p,mapping)
    target=tmp_path/'runtime';(target/'revsi_media/b').mkdir(parents=True)
    (target/'bootstrap').mkdir();dump(target/'STAGE_READY.json',{})
    (target/'revsi_media/b/x.mp4').write_bytes((root/'b/x.mp4').read_bytes())
    media=tmp_path/'media';media.mkdir();h=sha(root/'a/x.mp4')
    (media/(h+'.mp4')).write_bytes((root/'a/x.mp4').read_bytes())
    item=dict(id='1',dataset='fixture',scene_name='x',scene='fixture:x',native='fixture:x',
              question_type='object_counting_single',question='How many chairs?',options=[])
    binding={'benchmark':'revsi999t32','reader':{'kind':'harness'},'read_config':{
        'g3t':bind_source(mapping=p,reader='harness'),'frames':bind_frames()}}
    rt=Runtime(target,[item],binding,{'media':[{'relative_path':'x.mp4','sha256':h}],
        'media_root':str(media),'original_mapping':str(p)})
    rt.frames(bind_frames())
    return rt,item,media/(h+'.mp4')


def test_model_prompt_bytes_equal_direct_kit(real_frames):
    from offnative.c8 import install
    from offnative.frames import sample
    from offkit.frames import bind_frames
    from offnative.paths import R,module
    install()
    from routed import trainer_row
    from student_pilot.carrier_c1_data import layout_inputs
    from student_pilot.batches import training_text
    rt,item,video=real_frames
    _,direct=sample(video,bind_frames());cap=rt.captures['fixture:x']
    row=trainer_row(item,cap,rt.store)
    model=layout_inputs(row,'duplicate')
    want=dict(frame_indices=[i for i in direct['indices'] for _ in (0,1)],
              timestamps=[i/direct['fps'] for i in direct['indices'] for _ in (0,1)],
              fps=direct['fps'],total_num_frames=direct['total'])
    assert json.dumps({k:model[k] for k in want},sort_keys=True).encode()==json.dumps(want,sort_keys=True).encode()
    direct_core=module('_n4_direct_prompt',R/'kit/revsi/reader/evaluator/evalpath/official.py')
    direct_text=direct_core.build_prompt_context(item,'ours')
    class Processor:
        tokenizer=NS(eos_token='<|im_end|>',eos_token_id=248046,encode=lambda *a,**k:[248044])
        def apply_chat_template(self,messages,**kw):
            base=messages[0]['content'][1]['text']+'<think>\n'
            return base if len(messages)==1 else base+messages[1]['content']+'<|im_end|>\n'
    got,_=training_text(Processor(),item['question'],item['options'],'2\n')
    assert got.encode()==(direct_text+'<think>\n').encode()
    payload=rt.frames_for(item)
    assert payload['anchor_indices']==direct['indices']
    assert payload['fps']==direct['fps'] and payload['total_num_frames']==direct['total']
    assert payload['geometry_anchor_indices']!=payload['anchor_indices']


def test_loaded_entry_prompt_guard(real_frames):
    from offnative.prompt import expected
    from offnative.readers import E2EReader
    rt,item,_=real_frames;payload=rt.frames_for(item)
    called=[]
    entry=NS(prompt_inputs=lambda f,q:expected(f,q),generate=lambda f,q:(called.append(1) or {'text':'x'}))
    reader=E2EReader(entry,lambda d:True);reader.generate(payload,item)
    assert called==[1]
    entry.prompt_inputs=lambda f,q:dict(expected(f,q),anchor_indices=f['geometry_anchor_indices'])
    with pytest.raises(ValueError,match='prompt differs'):reader.generate(payload,item)
    assert called==[1]


def test_three_shards_cutoff_preserves_finished_items(tmp_path):
    from offnative.worker import Worker,merge
    from offnative.shards import plan
    from offkit.report import key
    items=[dict(id=str(i),dataset='fixture',scene_name=str(i%3),question_type='object_abs_distance') for i in range(12)]
    partition=plan(items,count=3)
    by_id={key(i):i for i in items};returned=[];missing=[]
    class Scorer:
        def score(self,i,d,arm):return dict(id=key(i),score=1,refusal=False,arm=arm)
    for shard in partition['shards']:
        w=Worker.__new__(Worker);w.config={'shard':shard};w.items=[by_id[k] for k in shard['ids']]
        w.binding={'reader':{'kind':'harness'},'binding_sha256':'a'*64}
        w.decoded={};w.unserved={};w.cutoff=False;w.fixture=True;w.scorer=Scorer();w.out=tmp_path/str(shard['index'])
        w.budget=NS(record=lambda:{'return_seconds':600});calls=[]
        def generate(item,served=True):
            if shard['index']==1 and len(calls)==3:raise TimeoutError('cutoff')
            calls.append((key(item),served));return {'text':'done'}
        w.generate=generate;w.read();w.score()
        marker=load(w.out/'COMPLETE.json');records=rows(w.out/'primary.jsonl');returned.append(records)
        if shard['index']==1:
            assert len(records)==2 and len(rows(w.out/'secondary_fallback.jsonl'))==1
            assert not marker['complete'] and (w.out/'PARTIAL.json').exists()
            assert len(marker['missing_ids']['primary'])==len(shard['ids'])-2
            missing=marker['missing_ids']['primary']
        else:assert marker['complete']
    with pytest.raises(ValueError,match='union'):merge([key(i) for i in items],returned)
    assert len(merge([key(i) for i in items],returned+[[{'id':k} for k in missing]]))==12


def test_packet_scans_decoded_paths_env_and_submission(tmp_path):
    from offnative.transport import packet,submission_argv,inventory
    from offnative.opacity import path_name,scan,pack,scan_members
    from offnative.io import tar_bytes
    with pytest.raises(ValueError):packet({'offnative/a.py':b'x'},tmp_path/'bad.tar','a'*24)
    with pytest.raises(ValueError):packet({'a.tar':tar_bytes({'kit/revsi/a.py':b'x'})},tmp_path/'bad2.tar','a'*24)
    files,_=pack({'offnative/a.py':b'x','a.tar':tar_bytes({'kit/revsi/a.py':b'x'})})
    assert packet(files,tmp_path/'ok.tar','a'*24)['decoded_members']==4
    with pytest.raises(ValueError):scan('OFFNATIVE_ROOTS=r.json')
    with pytest.raises(ValueError):scan('A0_ROOTS=/tmp/revsi')
    c={'job_name':'a15_cot_ap'+'0'*16,'job':{'time_limit_s':21600}}
    assert inventory(' '.join(submission_argv(c,'/p/1.sh',packet_sha256='0'*64)).encode())['passed']


def test_opaque_runtime_keeps_source_bytes(tmp_path):
    from offnative.opacity import path_name,scan
    d=tmp_path/'packed';d.mkdir()
    (d/'xnames.py').write_bytes((ROOT/'offnative/opacity.py').read_bytes())
    source=b"from pathlib import Path\ndef run():\n p=Path('out/REVSI_x.json');p.parent.mkdir(exist_ok=True);p.write_text('exact');return p.read_text()\n"
    p=d/path_name('student_pilot');p.mkdir();(p/'__init__.py').write_bytes(source)
    from offnative.opacity import runtime_table,seed
    seed({'student_pilot/__init__.py':source})
    (d/'x0.json').write_bytes(runtime_table())
    code="import xnames;xnames.install('.');import student_pilot,os,subprocess,sys;assert student_pilot.run()=='exact';os.environ['LEGS1_TREE']='work/runtime/revsi_media';assert os.getenv('LEGS1_TREE')=='work/runtime/revsi_media';subprocess.run([sys.executable,'-B','-c',\"import student_pilot;assert student_pilot.run()=='exact'\"],check=True);print('revsi')"
    r=subprocess.run([sys.executable,'-B','-c',code],cwd=d,capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    scan(r.stdout);scan(r.stderr)
    for path in d.rglob('*'):scan(str(path.relative_to(d)))
    assert (p/'__init__.py').read_bytes()==source
    assert (d/path_name('out/REVSI_x.json')).read_text()=='exact'


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_opaque_whole_worker_sources(tmp_path,kind):
    from offnative.portable import sources,ROOTS
    from offnative.opacity import pack,path_name,scan
    from offnative.paths import OFFKIT
    files,_=sources();files['r.json']=json.dumps(ROOTS).encode()
    files['xnames.py']=(ROOT/'offnative/opacity.py').read_bytes()
    files,pins=pack(files);files['out/ARCHIVE_TRANSPORT.json']=json.dumps(pins).encode()
    d=tmp_path/'p';d.mkdir()
    for name,raw in files.items():
        p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    code="import xnames;xnames.install('.');from offnative.rehearse import run;run('work/result',"+repr(kind)+")"
    env=dict(os.environ,A0_ROOTS='r.json',PYTHONPATH=str(OFFKIT),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    r=subprocess.run([sys.executable,'-B','-c',code],cwd=d,env=env,capture_output=True,text=True,timeout=120)
    (tmp_path/'execution.log').write_text(r.stdout+r.stderr)
    assert r.returncode==0,r.stderr
    assert load(d/'work/result/RESULT.json')['passed']
    for p in d.rglob('*'):scan(str(p.relative_to(d)))
