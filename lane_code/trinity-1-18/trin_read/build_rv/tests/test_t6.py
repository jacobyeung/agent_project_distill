import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest
import trinity_read as T
import milestone as M
import done_record as D
import items_export as I
import model_links as L
import launch_gcs as G
from test_t5b import archive_fixture, fake_stage


def done_fixture(tmp_path, text=None):
    p = tmp_path/'record.done'
    p.write_text(text or ('q8/8865619b/359fcc3c_m100.tar 12 '+'a'*64+'\n'))
    return p


@pytest.mark.parametrize('json_form', [False, True])
def test_done_and_stage_both_forms(tmp_path, monkeypatch, json_form):
    a = archive_fixture(tmp_path); fake_stage(monkeypatch)
    value = T.load(a.done)
    if not json_form:
        Path(a.done).write_text('{object} {bytes} {sha256}\n'.format(**value))
    assert D.parse_done(a.done, '359fcc3c', 100) == value
    assert M.stage_export(a)['status'] == 'complete'


@pytest.mark.parametrize('text', [
    'q8/8865619b/359fcc3c_m100.tar 0 {sha}', 'q8/8865619b/359fcc3c_m100.tar -1 {sha}',
    'q8/8865619b/359fcc3c_m100.tar 1.0 {sha}', 'q8/8865619b/359fcc3c_m100.tar 1 BAD',
    'q8/8865619b/359fcc3c_m100.tar 1 {sha} extra', 'q8/8865619b/359fcc3c_m100.tar 1 {sha}\n\n',
    'q8/8865619b/359fcc3c_m100.tar 1 {sha}\nsecond', 'gs://bucket/q8/8865619b/359fcc3c_m100.tar 1 {sha}',
    'q8/8865619b/359fcc3c_m200.tar 1 {sha}', 'q8/8865619b/469ddece_m100.tar 1 {sha}',
    'q8/other/359fcc3c_m100.tar 1 {sha}', 'q8/8865619b/359fcc3c_m0100.tar 1 {sha}',
    '{{"object":"q8/8865619b/359fcc3c_m100.tar","bytes":1,"sha256":"{sha}","extra":1}}',
    '{{"object":"q8/8865619b/359fcc3c_m100.tar","bytes":true,"sha256":"{sha}"}}',
    '{{"object":"q8/8865619b/359fcc3c_m100.tar","bytes":1,"bytes":2,"sha256":"{sha}"}}',
])
def test_done_refusals(tmp_path, text):
    with pytest.raises(ValueError): D.parse_done(done_fixture(tmp_path, text.format(sha='a'*64)), '359fcc3c', 100)


def packet_fixture(tmp_path, camera=False):
    # Extend the inherited packet-journal fixture with accepted membership and metadata.
    template = json.loads((T.BUILD/'tests/t5b_full_02/test_full_comparison_report0/actual/results/budget_2048/0/items_test.jsonl').read_text())
    accepted = [json.loads(s) for s in I.A544.read_text().splitlines()]
    if camera:
        accepted += [dict(id=k, family='camera', task_type=v, level=None, room='room', scene='scene',
                         score=1, scoring_basis='answer', prediction='A', pair_id=None)
                     for k,v in M.inventory()['camera']['items'].items()]
    root = tmp_path/'read'; families = {}
    for family in T.FAMILIES:
        rows = [r for r in accepted if r['family'] == family]
        if not rows: continue
        packet = root/family; report_rows = []; journal = []
        for row in rows:
            key = 'devrows:'+row['id']
            report_rows.append(dict(key=key, question_type=row['task_type'], room=row['room'],
                stratum='primary' if row['scoring_basis']=='released_answer' else 'own',
                scores=dict(answer=row['score'], released_answer=row['score'])))
            journal.append(dict(template, key=key, id=row['id'], example_id=row['id'],
                question_type=row['task_type'], room=row['room'], scene=row['scene'], status='complete',
                label_provenance=dict(paired_away_qid=row['pair_id']), extracted_answer=row['prediction']))
        report = packet/'report/B2048.json'; path = packet/'direct'/family/'results/budget_2048/0/items_a0.jsonl'
        T.dump(report, dict(arm='B2048', rows=report_rows)); path.parent.mkdir(parents=True)
        path.write_text(''.join(json.dumps(r)+'\n' for r in journal))
        T.dump(packet/'COMPLETE.json', dict(family=family, ids=[r['id'] for r in rows],
            input_sha256={str(p.relative_to(packet)):T.sha(p) for p in (report, path)}))
        T.dump(packet/'EXIT.json', dict(returncode=0, yielded=False, sampler_errors=[]))
        families[family] = dict(status='complete', report_sha256=T.sha(report))
    T.dump(root/'MILESTONE_SUMMARY.json', dict(status='complete', step=100, families=families))
    return NS(read=str(root), step=100, out=str(tmp_path/'ITEMS.jsonl'), a=None)


@pytest.mark.parametrize('camera', [False, True])
def test_items_full_membership_and_receipt(tmp_path, camera):
    args = packet_fixture(tmp_path, camera)
    receipt = I.export_items(args)
    assert receipt['counts'] == dict(main=1525, away=150, forward=150, **({'camera':450} if camera else {}))
    assert receipt['sha256'] == T.sha(args.out)
    assert receipt['records']['sha256'] == T.sha(I.RECORDS)
    assert receipt['f1f2']['sha256'] == T.sha(I.F1F2)
    assert T.load(tmp_path/'ITEMS.RECEIPT.json') == receipt
    with pytest.raises(ValueError, match='exists'): I.export_items(args)


@pytest.mark.parametrize('failure', ['report', 'journal', 'step', 'failed', 'missing_family', 'metadata', 'membership', 'a'])
def test_items_refusals(tmp_path, failure):
    args = packet_fixture(tmp_path); root = Path(args.read); packet=root/'main'
    report=packet/'report/B2048.json'; journal=packet/'direct/main/results/budget_2048/0/items_a0.jsonl'
    if failure in ('report','journal'):
        with (report if failure=='report' else journal).open('a') as f: f.write(' ')
    elif failure == 'step': args.step = 200
    elif failure in ('failed','missing_family'):
        value=T.load(root/'MILESTONE_SUMMARY.json')
        if failure=='failed': value['status']='failed'
        else: value['families'].pop('away')
        T.dump(root/'MILESTONE_SUMMARY.json',value)
    elif failure == 'a':
        a=tmp_path/'A.jsonl'; rows=[json.loads(l) for l in I.A544.read_text().splitlines()]
        rows[0]['scene']='changed'; a.write_text(''.join(json.dumps(r)+'\n' for r in rows)); args.a=str(a)
    else:
        rows=[json.loads(l) for l in journal.read_text().splitlines()]
        if failure=='metadata': rows[0]['scene']='changed'
        else: rows[0]['id']='unknown'
        journal.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        value=T.load(packet/'COMPLETE.json');value['input_sha256'][str(journal.relative_to(packet))]=T.sha(journal)
        T.dump(packet/'COMPLETE.json',value)
    with pytest.raises(ValueError): I.export_items(args)
    assert not Path(args.out).exists()


@pytest.mark.parametrize('name', ['RECORDS_SHA', 'F1F2_SHA'])
def test_scorer_pin_refusal(tmp_path, monkeypatch, name):
    args=packet_fixture(tmp_path);monkeypatch.setattr(I,name,'0'*64)
    with pytest.raises(ValueError,match='SHA256'):I.export_items(args)


def model_fixture(tmp_path):
    root=tmp_path; base=T.AP/'base'; art=T.FSW/'ap/8865619b/runs/359fcc3c/m100/artifact.json'
    files=[]
    for name, raw in [('config.json',b'{"model_type":"qwen3_5"}'), ('tokenizer_config.json',b'{}'), ('model.safetensors',b'base')]:
        path=T.physical(root,base/name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        files.append(dict(path=name,bytes=len(raw),sha256=T.sha(path)))
    bm=T.physical(root,base/'manifest.json');T.dump(bm,dict(files=files))
    weights=T.physical(root,art).parent/'full_weights';weights.mkdir(parents=True)
    shard=weights/'model-1.safetensors';shard.write_bytes(b'export')
    index=weights/'model.safetensors.index.json';T.dump(index,dict(weight_map={'tensor':shard.name}))
    wm=weights/'full_weights.json';T.dump(wm,dict(files=[dict(name=shard.name,bytes=6,sha256=T.sha(shard))],index=dict(name=index.name,sha256=T.sha(index))))
    T.dump(T.physical(root,art),dict(full_weights=dict(path=str(art.parent/'full_weights/full_weights.json'),sha256=T.sha(wm))))
    pin=dict(kind='c1_export',path=str(art),sha256=T.sha(T.physical(root,art)))
    cfg=dict(spec=dict(link_models=True,artifact=pin,models=dict(base=dict(kind='snapshot',path=str(base),manifest=dict(path=str(base/'manifest.json'),sha256=T.sha(bm))),cp1m200=pin)))
    packet=root/'packet';(packet/'direct/main').mkdir(parents=True)
    return cfg, packet


def test_links_native_receipts_and_readonly_binds(tmp_path, monkeypatch):
    cfg,packet=model_fixture(tmp_path);receipt=L.create(tmp_path,cfg,packet,'main')
    assert receipt['models_linked'] and receipt['before_verified']
    for row in receipt['files']: assert os.stat(row['source']).st_ino == os.stat(row['target']).st_ino
    argv=receipt['bwrap_args']; assert all(argv[i]=='--ro-bind' for i in range(0,len(argv),3))
    assert ['--ro-bind',str(packet/'direct/main/models'),str(packet/'direct/main/models')] in [argv[i:i+3] for i in range(0,len(argv),3)]
    # The unchanged preparer must reuse both identity receipts, without copying any file.
    stage=I.pinned_import(T.DEFAULT_ROOT/'sj/orch_cd/rv_merge_fix/work/r3/aws_vl64rt/evaluator/stage.py',
        T.sha(T.DEFAULT_ROOT/'sj/orch_cd/rv_merge_fix/work/r3/aws_vl64rt/evaluator/stage.py'),'t6_stage')
    monkeypatch.setattr(stage.shutil,'copyfile',lambda *a,**k:pytest.fail('Unexpected model copy'))
    models=packet/'direct/main/models'
    for slot in ('base','cp1m200'):assert stage.prepare(cfg['spec']['models'][slot],models/'base',models/slot)==models/slot
    L.finish(packet,tmp_path,receipt);assert T.load(packet/'MODELS_LINKED.json')['after_verified']
    monkeypatch.setattr(T,'kit_stage',lambda:NS(room=lambda *a:None))
    assert T.read_space(tmp_path,cfg,dict(estimated_frame_bytes={'x':11}))==22+2*1024**3


def test_links_postrun_corruption_fails(tmp_path):
    cfg,packet=model_fixture(tmp_path);receipt=L.create(tmp_path,cfg,packet,'main')
    path=Path(receipt['files'][0]['target']); raw=path.read_bytes(); path.write_bytes(bytes([raw[0]^1])+raw[1:])
    with pytest.raises(ValueError,match='size/hash'):L.finish(packet,tmp_path,receipt)
    assert not T.load(packet/'MODELS_LINKED.json')['after_verified']


def test_links_cross_filesystem_refuses(tmp_path,monkeypatch):
    cfg,packet=model_fixture(tmp_path);stat=Path.stat
    def device(path,*a,**k):
        result=stat(path,*a,**k)
        return NS(st_dev=result.st_dev+1) if path==packet/'direct/main' else result
    monkeypatch.setattr(Path,'stat',device)
    with pytest.raises(ValueError,match='same filesystem'):L.create(tmp_path,cfg,packet,'main')
    assert not (packet/'direct/main/models').exists()


def gcs_fixture(tmp_path, monkeypatch, failure=None):
    gov=tmp_path/'governor';gov.mkdir();streams=tmp_path/'streams';streams.mkdir()
    payload=b'part0part1part2part3';done=done_fixture(tmp_path,'q8/8865619b/359fcc3c_m100.tar %d %s\n'%(len(payload),hashlib.sha256(payload).hexdigest()))
    gcloud=tmp_path/'gcloud'
    gcloud.write_text('#!/usr/bin/python3\nimport sys\nassert sys.argv[1:3]==["storage","cat"]\n'
        'assert sys.argv[3:]==["gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m100.tar.part%02d-of-04"%i for i in range(4)]\n'+
        ('sys.exit(7)\n' if failure=='stream' else 'sys.stdout.write("'+('bad' if failure=='hash' else 'xxxx0xxxx1xxxx2xxxx3' if failure=='sha' else payload.decode())+'")\n'))
    gcloud.chmod(0o700)
    (gov/'ratelimit.py').write_text('import sys,shutil\nshutil.copyfileobj(sys.stdin.buffer,sys.stdout.buffer)\n')
    (gov/'register.py').write_text('import json,os,signal,sys\nfrom pathlib import Path\na=sys.argv[1:];get=lambda k:a[a.index(k)+1]\npid=int(get("--pid"))\n'
        'assert Path("/proc/%d/stat"%pid).read_text().split()[2]=="T"\n'
        'assert Path("/proc/%d/comm"%pid).read_text().strip()=="bash"\n'
        'assert get("--member-pid")==get("--rl-pid")\n'
        'assert get("--expected-bytes")=="20" and get("--priority")=="37"\n'
        'Path('+repr(str(streams/'fixture.json'))+').write_text(json.dumps(a))\n'
        'os.kill(pid,signal.SIGCONT)\n')
    monkeypatch.setenv('PRIO','37')
    def identity(pid):
        return dict(state=Path('/proc/%d/stat'%pid).read_text().split()[2],comm='fixture-rate')
    return dict(lane='fixture',done_file=done,output=tmp_path/'out.tar',gcloud=gcloud,governor=gov,streams=streams,
                identity_fn=identity,ratelimit_comm='fixture-rate')


def test_gcs_gate_stream_verify_receipt(tmp_path,monkeypatch):
    args=gcs_fixture(tmp_path,monkeypatch);r=G.launch(**args)
    assert r['verified'] and Path(args['output']).read_bytes()==b'part0part1part2part3'
    assert len(list(args['streams'].glob('fixture.done.*')))==1
    assert not (args['streams']/'fixture.json').exists()
    assert r['register_argv'][-1]=='37'
    with pytest.raises(ValueError,match='exists'):G.launch(**args)


@pytest.mark.parametrize('failure',['hash','sha','stream'])
def test_gcs_failure_retains_partial_no_retry(tmp_path,monkeypatch,failure):
    args=gcs_fixture(tmp_path,monkeypatch,failure)
    with pytest.raises((ValueError,RuntimeError)):G.launch(**args)
    assert not Path(args['output']).exists() and Path(str(args['output'])+'.part').exists()
    with pytest.raises(ValueError,match='exists'):G.launch(**args)


@pytest.mark.parametrize('corrupt', [False, True])
def test_linked_launch_records_mounts_and_postcheck(tmp_path, monkeypatch, corrupt):
    source=tmp_path/'staged';source.mkdir();cfg,_=model_fixture(source)
    cfg['spec'].update(package=str(T.SJ/'pkg'),interpreters=dict(vllm='fixture-vllm',p1cpu='fixture-cpu'))
    # Use the same root for the model plan and the production launch boundary.
    root=source;out=root/'launched'
    monkeypatch.setattr(T,'require_stage',lambda r:copy.deepcopy(cfg))
    monkeypatch.setattr(T,'cpu_need',lambda *a:dict(ids=['one'],need=[],estimated_frame_bytes={}))
    monkeypatch.setattr(M,'inventory',lambda:{'main':{'items':{'one':'fixture'}}})
    monkeypatch.setattr(T,'kit_stage',lambda:NS(room=lambda *a:None,MIN_FREE=0))
    monkeypatch.setattr(T,'check_card',lambda *a:dict(index='0'))
    monkeypatch.setattr(T,'probe',lambda *a:dict(passed=True))
    monkeypatch.setattr(T,'capture_command',lambda *a:dict(stdout='',returncode=0))
    monkeypatch.setattr(T,'bwrap_evidence',lambda *a:dict(path='/usr/bin/bwrap'))
    monkeypatch.setattr(T,'host_shm_ours',lambda:[])
    monkeypatch.setattr(T,'ns_command',lambda *a,**k:['/usr/bin/bwrap','--bind',str(root),str(root),
        'fixture-vllm' if k['gpu'] else 'fixture-cpu'])
    def bind(cmd,**kwargs):
        assert 'fixture-cpu' in cmd
        T.dump(out/'direct/main/request.json',{'binding':'fixture'})
    monkeypatch.setattr(T.subprocess,'run',bind)
    class Sampler:
        def __init__(self,*a):
            self.thread=NS(start=lambda:None,join=lambda **kw:None);self.stop=NS(set=lambda:None);self.errors=[]
    monkeypatch.setattr(T,'Sampler',Sampler)
    def reader(argv,env,*a):
        Path(env['LLG_STUB_LOG']).write_text('{"event":"import","module":"llguidance","pid":2}\n')
        links=T.load(out/'MODELS_LINKED.json')
        if corrupt:
            path=Path(links['files'][0]['source']);raw=path.read_bytes();path.write_bytes(bytes([raw[0]^1])+raw[1:])
        return 0,None
    monkeypatch.setattr(T,'run_reader',reader)
    pin=cfg['spec']['artifact']
    args=NS(root=str(root),command='read',token='d12345678',gpu='0',family='main',first=1,ids=None,
        out=str(out),artifact=pin['path'],sha256=pin['sha256'],step=100,link_models=True)
    if corrupt:
        with pytest.raises(RuntimeError,match='Post-run linked model'):T.launch(args)
    else:T.launch(args)
    assert T.load(out/'CARD.json')['models_linked']
    assert T.load(out/'EXIT.json')['models_linked']
    assert bool(T.load(out/'EXIT.json')['model_link_error']) == corrupt
    receipt=T.load(out/'MODELS_LINKED.json');assert receipt['after_verified'] != corrupt
    sandbox=T.load(out/'SANDBOX.json')['namespace_argv']
    for i in range(0,len(receipt['bwrap_args']),3):
        triple=receipt['bwrap_args'][i:i+3]
        assert any(sandbox[j:j+3]==triple for j in range(len(sandbox)-2))
    assert T.load(out/'INPUT.json')['attempt']=='a0'


@pytest.mark.parametrize('family', T.FAMILIES)
def test_prepared_binding_reuse_cpu(tmp_path, family):
    script = '''import sys
from pathlib import Path
import fixture_need as F
import trinity_read as T
import namespace_worker as W
import paired_read as P
family, work = sys.argv[1], Path(sys.argv[2])
first = F.bind_fixture(dict(family=family, work=str(work)))
config = T.load(T.REFERENCE/'CONFIG.json')
config['spec'] = T.load(work/'SPEC.json')
pin = T.sha(work/'direct'/family/'request.json')
second = W.bind_plan(config, family, work, reader=F.RUNTIME/'legs1_reads',
    kit=F.RUNTIME/'rv_merge_fix/work/r3/aws_vl64rt', camera=T.physical(T.DEFAULT_ROOT, P.CAMERA), binding_sha256=pin)
assert first[-1] == second[-1]
try:
    W.bind_plan(config, family, work, reader=F.RUNTIME/'legs1_reads',
        kit=F.RUNTIME/'rv_merge_fix/work/r3/aws_vl64rt', camera=T.physical(T.DEFAULT_ROOT, P.CAMERA), binding_sha256='0'*64)
except ValueError as error:
    assert 'Prepared binding changed' in str(error)
else: raise AssertionError('Changed binding accepted')
'''
    subprocess.run([sys.executable,'-B','-c',script,family,str(tmp_path/'packet')],check=True,cwd=str(T.BUILD))


@pytest.mark.parametrize('target', ['base/config.json','cp1m200/model-1.safetensors'])
def test_link_source_pin_refusal(tmp_path,target):
    cfg,packet=model_fixture(tmp_path)
    row=next(r for r in L.plan(tmp_path,cfg) if r['target']==target)
    path=Path(row['source']);raw=path.read_bytes();path.write_bytes(bytes([raw[0]^1])+raw[1:])
    with pytest.raises(ValueError,match='size/hash'):L.create(tmp_path,cfg,packet,'main')
    assert not (packet/'direct/main/models').exists()
