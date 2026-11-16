from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import uuid
import pytest
from conftest import ROOT
import official_adapter as A
import official_score as O
import orchard_launcher as L
import orchard_stage as S
import fixtures as F
import frame_plan


def fresh(name):
    p=ROOT/'tests/runs'/(name+uuid.uuid4().hex[:8]);p.parent.mkdir(parents=True,exist_ok=True);return p


def spec():return dict(benchmark='official5130',rows=dict(path=str(ROOT/'cohort/meta_5130.jsonl'),sha256=A.ROWS_SHA),question_types=sorted(A.COUNTS))


def cohort():return O.read_rows(ROOT/'cohort/COHORT_OFFICIAL6.jsonl')


def test_counts_and_media():
    rows=cohort();assert len(rows)==len({r['id'] for r in rows})==4008
    assert Counter(r['question_type'] for r in rows)==A.COUNTS
    media=json.loads((ROOT/'cohort/MEDIA_MANIFEST.json').read_text());assert len(media)==288
    assert Counter(r['relative_path'].split('/')[0] for r in media)==dict(arkitscenes=150,scannet=88,scannetpp=50)
    for r in rows:
        matches=[m for m in media if m['alias_path']==r['video_alias_path']]
        assert len(matches)==1 and matches[0]['sha256']==r['video_sha256']
    assert {(r['dataset'],r['scene_name']) for r in rows}=={tuple(m['relative_path'][:-4].split('/')) for m in media}


def test_identical_evaluator_and_sources():
    origins=json.loads((ROOT/'build/ORIGINS.json').read_text());changed=[]
    for dest,source in origins.items():
        if not dest.startswith('reader/'):continue
        if (ROOT/dest).read_bytes()!=(ROOT.parent/'pull'/source).read_bytes():changed.append(dest)
    assert changed==['reader/evaluator/evalpath/kit_inputs.py']
    pins=json.loads((ROOT.parent/'pull/x27/res/e193/CODE_PINS.json').read_text())
    assert hashlib.sha256((ROOT/'reader/out/direct.py').read_bytes()).hexdigest()=='d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a'


def test_filter_and_absent_key():
    from data import tasks_for
    s=spec();root=dict(video_root='/tmp/v')
    filtered=tasks_for(s,root);assert len(filtered)==4008
    assert {t['example_id'] for t in filtered}=={r['id'] for r in cohort()}
    s.pop('question_types');assert len(tasks_for(s,root))==5130


@pytest.mark.parametrize('value',[[],['route_planning','object_counting'],['route_planning','route_planning'],['unknown'],'route_planning',[3]])
def test_bad_filter(value):
    from data import tasks_for
    with pytest.raises(ValueError):tasks_for(dict(spec(),question_types=value),dict(video_root='/tmp/v'))


def test_filter_refuses_slice():
    from data import tasks_for
    with pytest.raises(ValueError):tasks_for(dict(spec(),slice=12),dict(video_root='/tmp/v'))


def test_filter_keeps_5130_guard():
    from data import tasks_for
    p=fresh('bad').with_suffix('.jsonl');p.write_text(json.dumps(O.read_rows(ROOT/'cohort/meta_5130.jsonl')[0])+'\n')
    s=spec();s['rows']=dict(path=str(p),sha256=F.sha(p))
    with pytest.raises(ValueError,match='5130'):tasks_for(s,dict(video_root='/tmp/v'))


def test_all_callers_share_filter(monkeypatch):
    import data,worker,frame_stage,merge,budget_merge,parity,budget
    cfg=dict(datasets=[spec()],roots=dict(video_root='/tmp/v'),cells=[A.CELL],binding='a',source_sha256='b',smoke_items=0)
    wanted={r['id'] for r in cohort()}
    for module in (worker,frame_stage,merge,budget_merge):
        assert module.tasks_for is data.tasks_for
        assert {r['example_id'] for r in module.tasks_for(spec(),cfg['roots'])}==wanted
    ts=sorted(data.tasks_for(spec(),cfg['roots']),key=lambda t:t['example_id'])
    assert {t['example_id'] for t,_ in parity.probe_tasks(cfg,ts)}=={t['example_id'] for t in ts[:16]}
    p=fresh('frame');p.mkdir();F.js(p/'q.json',cfg)
    seen=[]
    def staged(t,*args):seen.append(t['example_id']);return dict(path='fixture',sha256='x'),False
    monkeypatch.setattr(frame_stage,'stage_one',staged)
    ix=frame_stage.stage(p/'q.json',p/'cache',16)
    assert len(ix['items'])==4008 and ix['decodes']==288
    assert all(k in wanted for k in seen)
    # Derivation has no independent dataset loader: its immutable source keys are
    # checked against these worker task keys, then checked again by budget_merge.
    assert 'Budget source shard is incomplete' in Path(worker.__file__).read_text()
    assert 'Budget derivation count mismatch' in Path(budget.__file__).read_text()


def test_protocol():
    accepted=json.loads((ROOT.parent/'pull/x27/res/e193/direct/main/request.json').read_text())
    assert {k:v for k,v in A.CELL.items() if k not in ('benchmarks','name')}=={k:v for k,v in accepted['cells'][0].items() if k not in ('benchmarks','name')}
    models=json.loads((ROOT/'launcher/MODELS.json').read_text());A.model_specs(models)
    bad=json.loads(json.dumps(models));bad['cp1m200']['sha256']='0'*64
    with pytest.raises(ValueError):A.model_specs(bad)


def test_scorer_accepted():
    r=O.self_check(ROOT.parent/'pull/x27/res/e193');assert r['passed'] and r['items']==1525 and r['types']==11


def test_bootstrap_grouping_errors_and_caps():
    ts=cohort();rows=[dict(t,status='complete',score=float(t['question_type']=='object_rel_direction_easy'),parse_failed=False) for t in ts]
    a=O.aggregate(ts,rows,rows);b=O.aggregate(ts,rows,rows)
    assert a==b and a['scenes']==288 and a['bootstrap']['repetitions']==10000
    assert a['groups']['object_rel_direction']['score']==pytest.approx(1/3)
    assert a['six_task_mean']['score']==pytest.approx(1/18)
    assert all(v['status']=='not read' for v in a['excluded'].values())
    rows[0].update(status='error',score=1,error='test',output_tokens=16384)
    rows[1].update(max_new_tokens=64,output_tokens=64,parse_failed=True)
    c=O.aggregate(ts,rows,rows)
    group=next(v for k,v in c['groups'].items() if ts[0]['question_type'] in O.GROUPS[k])
    assert group['errors'] and group['source_capped']>=1
    assert sum(g['continuation_capped'] for g in c['groups'].values())==1
    with pytest.raises(ValueError):O.aggregate(ts,rows+[rows[0]],rows)


def test_frame_plan_and_receipt(monkeypatch):
    import frame_stage
    p=fresh('mp4');p.mkdir();v=F.video(p/'v.mp4');r=frame_plan.one(v)
    assert r['total_frames']==40 and r['fps']==24 and r['packet_equals_decode'] is True
    assert r['anchor_indices']==[i*39//31 for i in range(32)]
    assert r['duplicate_indices']==[i for i in r['anchor_indices'] for _ in range(2)]
    assert r['timestamps']==[i/24 for i in r['duplicate_indices']]
    assert frame_plan.one(v,True)['packet_equals_decode'] is None
    t=dict(benchmark='official5130',example_id='0',dataset='a',scene_name='b',video_path=str(v))
    monkeypatch.setattr(frame_stage,'tasks_for',lambda s,r:[t])
    F.js(p/'q.json',dict(datasets=[dict(benchmark='official5130')],roots={},cells=[A.CELL],binding='x',source_sha256='y'))
    frame_stage.stage(p/'q.json',p/'c',16)
    F.js(p/'plan.json',dict(mode='decode',videos={'a/b.mp4':r}))
    assert frame_plan.check([t],p/'c',p/'plan.json',F.sha(p/'c/0.json'))['items']==1
    r['anchor_indices'][1]+=1;F.js(p/'plan.json',dict(mode='decode',videos={'a/b.mp4':r}))
    with pytest.raises(ValueError):frame_plan.check([t],p/'c',p/'plan.json',F.sha(p/'c/0.json'))


def test_batch_prepare_render_extract():
    p=fresh('batch');p.mkdir();manifest=json.loads((ROOT/'cohort/MEDIA_MANIFEST.json').read_text())
    F.js(p/'plan.json',dict(mode='decode',videos={r['relative_path']:dict(sha256=r['sha256'],total_frames=32,fps=24,anchor_indices=list(range(32)),duplicate_indices=[i for i in range(32) for _ in range(2)],timestamps=[i/24 for i in range(32) for _ in range(2)]) for r in manifest}))
    cfg=L.prepare('a0123456789',p/'o',p/'plan.json');script=(p/'o/BATCH.sh').read_text();L.validate_batch(script,cfg)
    assert len(script)<3*1024**2+8192
    subprocess.run(['bash','-n',str(p/'o/BATCH.sh')],check=True)
    assert '--cpus-per-task=16' in L.submit_argv(None,cfg['token']) and '--time=06:00:00' in L.submit_argv(None,cfg['token'])
    assert L.SSH[0]=='bash' and L.SSH[1].endswith('/ossh.sh')
    assert '/data3/' not in Path(L.__file__).read_text()
    with pytest.raises(ValueError):L.validate_batch(script+'# altered\n',cfg)
    with pytest.raises(ValueError):L.valid_token('benchmark')
    with pytest.raises(ValueError):L.render_batch(b'x'*(3*1024**2),'a0123456789')
    with pytest.raises(ValueError):L.validate_request(dict(cfg,proof_only=True))


def test_transport():
    t=json.loads((ROOT/'launcher/TRANSPORT.json').read_text());assert len(t['parts'])==4
    assert sum(p['bytes'] for p in t['parts'])==t['archive_bytes']==21583032320
    assert t['archive_sha256']=='3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7'
    assert t['artifact_sha256']==A.EXPORT_SHA
    assert all(p['generation'] and len(p['sha256'])==64 for p in t['parts'])


def test_stage_copy_and_reject():
    p=fresh('copy');p.mkdir();src=p/'a';src.write_bytes(b'abc')
    part=dict(bytes=3,sha256=F.sha(src))
    assert S.copy_parts([part],p/'b',lambda _:src.open('rb'),check_space=False)['bytes']==3
    with pytest.raises(FileExistsError):S.copy_parts([part],p/'b',lambda _:src.open('rb'),check_space=False)
    with pytest.raises(ValueError):S.copy_parts([dict(part,sha256='0'*64)],p/'c',lambda _:src.open('rb'),check_space=False)
    for name in ('../a','/a','a/../../b'):
        with pytest.raises(ValueError):S.relative(name)


def test_full_cpu_proof():
    p=fresh('proof')
    env=dict(__import__('os').environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1')
    result=subprocess.run([sys.executable,str(ROOT/'proof/run.py'),'--work',str(p)],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads((p/'RESULT.json').read_text());assert receipt['passed'] and receipt['items']==14 and receipt['phase_b_items']==20 and len(receipt['datasets'])==3
    root=Path(receipt['job_root']);run=next((root/'sj').glob('*/r'))
    scores=json.loads((run/'report/B2048.json').read_text())
    assert sum(len(g['errors']) for g in scores['groups'].values())==1
    secondary=json.loads((run/'report/B4096.json').read_text())
    assert sum(g['continuation_capped'] for g in secondary['groups'].values())==1
    assert sum(g['unparsed'] for g in scores['groups'].values())>=1
    assert receipt['archive_bytes']<19000000
    b=json.loads((run/'b0/PHASE_B.json').read_text())
    assert b['fixture'] and b['items']==20 and b['parity']==dict(id_checks=16,pixel_checks=2,passed=True,skipped=False)
    assert b['accepted_prompt_ids']['recorded']==16
    assert set(b['arms'])=={'ON16k','B2048','B4096'}


def test_prompt_bind_before_processor():
    p=fresh('parity')
    r=subprocess.run([sys.executable,str(ROOT/'parity/prove_prompts.py'),'--output',str(p)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    report=json.loads((p/'PARITY.json').read_text());assert report['prompt_pins_equal'] and not report['processor_checked']


def test_process_stream_and_runtime_links():
    p=fresh('stream');p.mkdir()
    with S.process_stream([sys.executable,'-I','-c','print("fixture")'],dict(__import__('os').environ),p/'log') as stream:
        assert stream.read(1024)==b'fixture\n'
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w') as tf:
        m=tarfile.TarInfo('a');m.size=1;tf.addfile(m,io.BytesIO(b'x'))
        m=tarfile.TarInfo('b');m.type=tarfile.SYMTYPE;m.linkname='a';tf.addfile(m)
        m=tarfile.TarInfo('c');m.type=tarfile.LNKTYPE;m.linkname='a';tf.addfile(m)
    raw.seek(0);S.extract_stream(raw,p/'out',None,10240,links=True)
    assert (p/'out/b').read_bytes()==(p/'out/c').read_bytes()==b'x'


def test_namespace_and_card_policy(monkeypatch):
    import orchard_job as J
    p=fresh('ns');p.mkdir()
    cmd=J.namespace(p)
    assert cmd[0]==str(p/'bwrap') and '--die-with-parent' in cmd
    monkeypatch.setenv('USER','fixture');monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0');monkeypatch.setenv('SLURM_JOB_ID','123')
    def gpu(argv,**kw):
        text='0, GPU-x, NVIDIA H100 80GB HBM3, 0, 0\n' if argv[0]=='nvidia-smi' and argv[1].startswith('--query-gpu=') else ''
        return subprocess.CompletedProcess(argv,0,text,'')
    monkeypatch.setattr(J.subprocess,'run',gpu)
    assert J.card(True)['gpu_type']=='NVIDIA H100 80GB HBM3'
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0,1')
    with pytest.raises(ValueError):J.card(True)


def test_failed_packet_keeps_source_journal():
    import chain_save
    p=fresh('failed');p.mkdir()
    F.js(p/'FAILED.json',dict(error='source failure'))
    journal=p/'a0/results/0/g0.jsonl';journal.parent.mkdir(parents=True);journal.write_text('{"status":"error"}\n')
    assert 'a0/results/0/g0.jsonl' in chain_save.members(p)
