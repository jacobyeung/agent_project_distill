import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS

import pytest
import trinity_read as T
import compare_tokens as C


def archive(path, entries):
    with tarfile.open(path, 'w') as tf:
        for name, raw in entries:
            item = tarfile.TarInfo(name); item.size = len(raw)
            tf.addfile(item, io.BytesIO(raw))


def png(color):
    from PIL import Image
    out = io.BytesIO(); Image.new('RGB',(8,8),color).save(out,format='PNG')
    raw = out.getvalue(); h = hashlib.sha256(raw).hexdigest()
    return h, raw


def test_bootstrap_matches_accepted():
    cfg, files = T.reference_bundle()
    assert cfg['token'] == 'pb59bef09f3'
    assert hashlib.sha256(files['bootstrap/payload.tar.gz']).hexdigest() == cfg['payload_sha256']
    assert files['bootstrap/trace_runtime.py'] == (T.KIT/'launcher/trace_runtime.py').read_bytes()


def test_partial_stage_refused(tmp_path):
    T.dump(tmp_path/'STAGING.json', {'pieces':{'runtime_0':{'status':'partial'}}})
    with pytest.raises(ValueError, match='Partial stage refused'):
        T.stage(tmp_path,tmp_path/'dl')


def test_piece_idempotent_and_failure_retained(tmp_path):
    state = {'pieces':{}}; calls = []
    T.piece(tmp_path,state,'ok',lambda:calls.append(1))
    T.piece(tmp_path,state,'ok',lambda:calls.append(2))
    assert calls == [1]
    def fail(): raise ValueError('bad payload')
    with pytest.raises(ValueError): T.piece(tmp_path,state,'bad',fail)
    with pytest.raises(ValueError,match='Partial'): T.piece(tmp_path,state,'bad',lambda:None)
    assert T.load(tmp_path/'STAGING.json')['pieces']['bad']['status'] == 'partial'


def test_runtime_part_hashes(tmp_path):
    p = tmp_path/'rt.tar'; p.write_bytes(b'abcdef')
    rows = [('a',3,hashlib.sha256(b'abc').hexdigest()),('b',3,hashlib.sha256(b'def').hexdigest())]
    assert T.authenticate_parts(p,rows) == hashlib.sha256(b'abcdef').hexdigest()
    rows[1] = ('b',3,'0'*64)
    with pytest.raises(ValueError,match='SHA256'): T.authenticate_parts(p,rows)


def test_receipt_required(tmp_path):
    p = tmp_path/'a.tar'; p.write_bytes(b'abc')
    assert not T.receipt_ready(p)
    T.dump(str(p)+'.RECEIPT.json',dict(bytes=3,sha256=hashlib.sha256(b'abc').hexdigest()))
    assert T.receipt_ready(p)


def test_store_append_and_unchanged_pull(tmp_path,monkeypatch):
    monkeypatch.setattr(T.kit_stage(),'room',lambda *a:None)
    a,ar = png('red'); b,br = png('blue')
    archive(tmp_path/'a.tar',[(a[:2]+'/'+a+'.png',ar)])
    archive(tmp_path/'b.tar',[(a[:2]+'/'+a+'.png',ar),(b[:2]+'/'+b+'.png',br)])
    assert T.frames(tmp_path,[tmp_path/'a.tar'])['added'] == 1
    original = (tmp_path/'k6tk/MEMBERS.tsv.gz').read_bytes()
    original_index = T.store_index(tmp_path)
    assert T.frames(tmp_path,[tmp_path/'b.tar'])['added'] == 1
    assert (tmp_path/'k6tk/MEMBERS.tsv.gz').read_bytes().startswith(original)
    assert T.store_index(tmp_path)[a] == original_index[a]
    assert T.frames(tmp_path,[tmp_path/'b.tar'])['added'] == 0
    listing = tmp_path/'NEED.txt'; listing.write_text(a+'\n'+b+'\n')
    raw = subprocess.check_output([sys.executable,'-B',str(T.KIT/'proof/pull.py'),str(listing),str(tmp_path/'k6tk')])
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
        assert {hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf} == {a,b}


@pytest.mark.parametrize('bad_name,bad_bytes', [(True,False),(False,True)])
def test_store_sha_refusal(tmp_path, monkeypatch, bad_name, bad_bytes):
    monkeypatch.setattr(T.kit_stage(),'room',lambda *a:None)
    h,raw = png('red')
    archive(tmp_path/'bad.tar',[(('../' if bad_name else '')+h[:2]+'/'+h+'.png',raw+b'x' if bad_bytes else raw)])
    with pytest.raises(ValueError): T.frames(tmp_path,[tmp_path/'bad.tar'])
    assert not (tmp_path/'k6tk/MEMBERS.tsv.gz').exists()


def test_system_python_store(tmp_path):
    h,raw = png('red'); archive(tmp_path/'p.tar',[(h[:2]+'/'+h+'.png',raw)])
    script = 'import trinity_read as T; T.kit_stage().room=lambda *a:None; print(T.frames(T.Path(%r),[T.Path(%r)]))' % (str(tmp_path),str(tmp_path/'p.tar'))
    subprocess.run(['/usr/bin/python3','-B','-c',script],cwd=T.BUILD,check=True)


def test_selection_and_need():
    tasks = [dict(benchmark='devrows',example_id=i,native=n) for i,n in [('b','x'),('a','y'),('c','x')]]
    captures = {'x':{'frames':[{'sha256':'1'*64}]},'y':{'frames':[{'sha256':'2'*64}]}}
    assert [t['example_id'] for t in T.selected_tasks(tasks,ids=['c','a'])] == ['a','c']
    assert T.needed(captures,T.selected_tasks(tasks,first=1)) == ['2'*64]
    with pytest.raises(ValueError,match='outside'): T.selected_tasks(tasks,ids=['not-dev'])
    with pytest.raises(ValueError,match='unique'): T.selected_tasks(tasks,ids=['a','a'])
    with pytest.raises(ValueError): T.selected_tasks(tasks,first=4)
    with pytest.raises(ValueError): T.selected_tasks([dict(benchmark='official5130',example_id='1')])


@pytest.mark.parametrize('family', T.FAMILIES)
@pytest.mark.parametrize('prefix', [20, None])
def test_need_real_payload_with_kit_fakes(tmp_path,family,prefix):
    # A fresh process is required by origin.kit_import; fake only tensor/processor imports.
    script = '''
import sys
from pathlib import Path
import trinity_read as T
sys.path.insert(0,str(T.KIT/'proof'))
import fakes
fakes.install()
import namespace_worker as W
cfg=T.load(T.REFERENCE/'CONFIG.json')
runtime=Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd')
reader=runtime/'legs1_reads'
assert T.sha(reader/'out/direct.py') == 'd16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a'
W.bind_plan(cfg,sys.argv[1],Path(sys.argv[2]),first=int(sys.argv[3]) if sys.argv[3]!='all' else None,reader=reader,kit=runtime/'rv_merge_fix/work/r3/aws_vl64rt')
'''
    subprocess.run([sys.executable,'-B','-c',script,family,str(tmp_path),str(prefix) if prefix else 'all'],cwd=T.BUILD,check=True)
    result = T.load(tmp_path/'NEED.json')
    assert result['items'] == (20 if prefix else result['family_items'])
    assert len(result['need']) == len(set(result['need']))
    assert sum(result['estimated_frame_bytes'].values()) > 0
    if family == 'main' and prefix == 20:
        reference = T.load(T.KIT/'parity/DEV20.json')
        assert result['ids'] == reference['ids']
        expected = (T.BUILD/'NEED20.fixture.txt').read_text().splitlines()
        assert result['need'] == sorted(expected)
        assert len(result['need']) == 576


def test_filter_updates_existing_and_future_imports(monkeypatch):
    import namespace_worker as W
    import types
    data = types.ModuleType('test_data'); consumer = types.ModuleType('test_consumer')
    data.tasks_for = lambda *a:[dict(benchmark='devrows',example_id=k) for k in ['b','a','c']]
    consumer.tasks_for = data.tasks_for
    monkeypatch.setitem(sys.modules,'test_data',data); monkeypatch.setitem(sys.modules,'test_consumer',consumer)
    W.install_filter(data,['c','a'])
    assert consumer.tasks_for is data.tasks_for
    assert [r['example_id'] for r in consumer.tasks_for({'benchmark':'devrows'}, {})] == ['a','c']
    with pytest.raises(ValueError): consumer.tasks_for({'benchmark':'revsi'}, {})


def record(tokens=(1,2,3)):
    return dict(example_id='item',token_ids=list(tokens),raw_generation='answer',extracted_answer='A',score=1.0)


@pytest.mark.parametrize('actual,k,equal', [([1,2,3],None,True),([1,9,3],1,False),([1,2],2,False),([1,2,3,4],3,False)])
def test_token_comparison(actual,k,equal):
    report = C.compare_row(record(),record(actual))
    assert report['token_ids_identical'] is equal
    assert report['first_divergence_index'] == k
    assert report['accepted_length'] == 3 and report['actual_length'] == len(actual)


def test_comparison_missing_and_duplicates():
    reference = dict(ids=['item'],arms={arm:[record()] for arm in C.ARMS})
    good = {arm:[record()] for arm in C.ARMS}
    assert C.compare(reference,good)['passed']
    bad = copy.deepcopy(good); bad['ON16k'] = []
    result = C.compare(reference,bad)
    assert not result['passed'] and result['arms']['ON16k']['mean_score_actual'] is None
    bad['ON16k'] = [record(),record()]
    with pytest.raises(ValueError,match='Duplicate'): C.compare(reference,bad)


def test_budget_reuse_not_counted_as_new_generation(tmp_path):
    d = tmp_path/'results/0'; d.mkdir(parents=True)
    row = dict(record(),seconds=2.0)
    (d/'g0.jsonl').write_text(json.dumps(row)+'\n')
    (d/'budget_2048.g0.jsonl').write_text(json.dumps(row)+'\n')
    (d/'budget_2048.g0.meta.jsonl').write_text(json.dumps(dict(source_key='devrows:item',answer_cap_policy='reuse_full_on_answer'))+'\n')
    assert C.timing(tmp_path,'ON16k',['item'])['items'][0]['generated_tokens_per_second'] == 1.5
    assert C.timing(tmp_path,'B2048',['item'])['items'][0]['seconds'] is None
    # A stopped-unclosed source also generates a continuation; forced_close alone is insufficient.
    (d/'budget_2048.g0.meta.jsonl').write_text(json.dumps(dict(source_key='devrows:item',
        answer_cap_policy='continuation_64',stopped_unclosed=True,forced_close=False))+'\n')
    assert C.timing(tmp_path,'B2048',['item'])['items'][0]['seconds'] == 2.0


def test_card_checks_are_mocked(monkeypatch):
    def smi(args):
        return '0, GPU-a, RTX 6000 Ada, 49140, 99\n' if 'index,uuid,name,memory.total,memory.used' in ' '.join(args) else ''
    monkeypatch.setattr(T,'smi',smi)
    assert T.check_card('0')['total_mib'] == 49140
    monkeypatch.setattr(T,'smi',lambda args:smi(args).replace(', 99',', 100'))
    with pytest.raises(ValueError): T.check_card('0')


def test_namespace_is_local_and_cpu_has_no_gpu_devices(tmp_path):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    command = T.namespace(tmp_path)
    assert '--unshare-net' in command and '--dev-bind' not in command
    assert command[command.index(T.STORE)-1] == str(tmp_path/'k6tk')
    assert not any('MEDIA_MANIFEST' in x for x in command)
    assert T.environment(tmp_path)['CUDA_VISIBLE_DEVICES'] == ''


def test_missing_frames_stop_before_card(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(T,'require_stage',lambda root:{})
    monkeypatch.setattr(T,'cpu_need',lambda *a:dict(need=['a'*64],ids=['item']))
    monkeypatch.setattr(T,'check_card',lambda *a:pytest.fail('GPU boundary reached'))
    with pytest.raises(ValueError,match='Missing frames'):
        T.launch(NS(root=str(tmp_path),command='proof',token='p12345678'))
    assert 'NEED\n' in capsys.readouterr().out


def test_lineage_and_write_boundary(tmp_path):
    logical = str(T.LINEAGE/'m544/artifact.json')
    assert T.logical_artifact(tmp_path,str(T.physical(tmp_path,logical)),544) == logical
    with pytest.raises(ValueError): T.logical_artifact(tmp_path,logical,545)
    with pytest.raises(ValueError): T.writable(T.KIT/'forbidden')


def test_stage_piecewise_and_complete(tmp_path,monkeypatch):
    root = tmp_path/'root'; dl = tmp_path/'dl'; dl.mkdir()
    assets = dict(groups=[],camera_archive={},bwrap_pin={},base_manifest={})
    manifest = json.dumps(dict(files=[dict(path='config.json',bytes=2,sha256=hashlib.sha256(b'{}').hexdigest())])).encode()
    for i in range(3):
        entries = [('sj/runtime'+str(i),b'fixture')]
        if i == 2: entries.append(('m/ap/90da7ac2/m/base_manifest.json',manifest))
        archive(dl/('runtime_'+str(i)+'.tar'),entries)
        p = dl/('runtime_'+str(i)+'.tar')
        assets['groups'].append([['unused',p.stat().st_size,T.sha(p)]])
    archive(dl/'camera.tar',[('sj/camera',b'fixture')])
    (dl/'bwrap').write_bytes(b'fixture')
    for key,filename in [('camera_archive','camera.tar'),('bwrap_pin','bwrap')]:
        p = dl/filename; assets[key] = dict(bytes=p.stat().st_size,sha256=T.sha(p))
    archive(dl/'base.tar',[('a/b/c/config.json',b'{}')])
    assets['base_archive_bytes'] = (dl/'base.tar').stat().st_size
    assets['base_manifest'] = dict(path=str(T.AP/'90da7ac2/m/base_manifest.json'),sha256=hashlib.sha256(manifest).hexdigest())
    p = tmp_path/'payload.tar'; archive(p,[('sj/fixture/p/code.py',b'pass\n')])
    config = dict(assets=assets,payload_sha256=T.sha(p))
    bootstrap = {'bootstrap/CONFIG.json':json.dumps(config).encode(),'bootstrap/payload.tar.gz':p.read_bytes()}
    monkeypatch.setattr(T,'reference_bundle',lambda:(config,bootstrap))
    monkeypatch.setattr(T,'verify_export_local',lambda *a:dict(fixture=True))
    monkeypatch.setattr(T.kit_stage(),'room',lambda *a:None)
    T.dump(str(dl/'runtime_2.tar')+'.RECEIPT.json',{})
    initial = T.stage(root,dl)
    assert not initial['complete'] and initial['pieces']['runtime_2']['status'] == 'complete'
    for p in dl.iterdir():
        if p.name.endswith('.RECEIPT.json'): continue
        T.dump(str(p)+'.RECEIPT.json',{})
    complete = T.stage(root,dl)
    assert complete['complete']
    assert (root/'m/ap/85fc3486/config.json').read_bytes() == b'{}'
    assert T.stage(root,dl)['pieces'] == complete['pieces']


def test_unregistered_stage_destination_refused(tmp_path,monkeypatch):
    monkeypatch.setattr(T.kit_stage(),'room',lambda *a:None)
    (tmp_path/'bootstrap').mkdir()
    with pytest.raises(ValueError,match='Unrecorded bootstrap'):
        T.stage(tmp_path,tmp_path/'dl')
    assert T.load(tmp_path/'STAGING.json')['pieces']['bootstrap']['status'] == 'partial'


def test_runtime_absolute_link_policy(tmp_path):
    raw = io.BytesIO()
    link = 'm/ap/19252904/e/bin/python'
    target = T.kit_stage().RUNTIME_ABSOLUTE_LINKS[link]
    with tarfile.open(fileobj=raw,mode='w') as tf:
        m = tarfile.TarInfo(link); m.type = tarfile.SYMTYPE; m.linkname = target; tf.addfile(m)
    T.kit_stage().extract_stream(io.BytesIO(raw.getvalue()),tmp_path,None,len(raw.getvalue()),links=True)
    assert os.readlink(tmp_path/link) == target


def test_full_comparison_report(tmp_path):
    reference = dict(ids=['item'],arms={arm:[record()] for arm in C.ARMS})
    T.dump(tmp_path/'reference.json',reference)
    for arm,rel in C.ARMS.items():
        directory = tmp_path/'actual/results'/rel; directory.mkdir(parents=True)
        (directory/'items_test.jsonl').write_text(json.dumps(record())+'\n')
    (tmp_path/'memory.jsonl').write_text(json.dumps(dict(memory_used_mib=123.0))+'\n')
    T.dump(tmp_path/'exit.json',dict(returncode=0,sampler_errors=[]))
    report = C.write_report(tmp_path/'reference.json',tmp_path/'actual','test',tmp_path/'report',tmp_path/'memory.jsonl',tmp_path/'exit.json')
    assert report['passed'] and report['peak_card_memory_mib'] == 123.0
    assert (tmp_path/'report/PROOF.md').is_file()


def test_corrupt_result_still_writes_failed_report(tmp_path):
    reference = dict(ids=['item'],arms={arm:[record()] for arm in C.ARMS})
    T.dump(tmp_path/'reference.json',reference)
    directory = tmp_path/'actual/results/0'; directory.mkdir(parents=True)
    (directory/'items_test.jsonl').write_text('{broken\n')
    report = C.write_report(tmp_path/'reference.json',tmp_path/'actual','test',tmp_path/'report')
    assert not report['passed'] and report['errors']
    assert (tmp_path/'report/PROOF.json').exists()


def test_read_space_reserves_model_copies(tmp_path,monkeypatch):
    base_path = T.AP/'manifest.json'; artifact_path = T.LINEAGE/'m544/artifact.json'
    weight_path = T.LINEAGE/'m544/full_weights/full_weights.json'
    T.dump(T.physical(tmp_path,base_path),dict(files=[dict(bytes=100)]))
    T.dump(T.physical(tmp_path,weight_path),dict(files=[dict(bytes=200)]))
    T.dump(T.physical(tmp_path,artifact_path),dict(full_weights=dict(path=str(weight_path),sha256=T.sha(T.physical(tmp_path,weight_path)))))
    cfg = dict(spec=dict(models=dict(base=dict(manifest=dict(path=str(base_path),sha256=T.sha(T.physical(tmp_path,base_path))))),
                         artifact=dict(path=str(artifact_path),sha256=T.sha(T.physical(tmp_path,artifact_path)))))
    observed = []
    monkeypatch.setattr(T.kit_stage(),'room',lambda root,extra:observed.append(extra))
    reserve = T.read_space(tmp_path,cfg,dict(estimated_frame_bytes={'frame':50}))
    assert reserve == 400+2*1024**3 and observed == [reserve]
