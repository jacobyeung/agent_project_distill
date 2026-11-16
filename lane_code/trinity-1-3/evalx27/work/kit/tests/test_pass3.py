import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace as NS
import pytest
from conftest import ROOT
from test_kit import fresh
import orchard_results as R
import orchard_launcher as L
import orchard_job as J
import return_io
import phase_b


def local_source():
    p=fresh('return3');p.mkdir();src=p/'source';src.mkdir()
    (src/'COMPLETE.json').write_text(json.dumps(dict(plan_sha256='0'*64,synthetic=False)))
    return p,src


def test_write_test_and_unique_token():
    p=fresh('wtest');p.mkdir();pool=p/'pool';token='p0123456789'
    r=R.write_test(pool,token)
    assert r['bytes']==4*1024**2 and len(r['sha256'])==64
    assert not (pool/token/'.wtest').exists()
    with pytest.raises(subprocess.CalledProcessError):R.write_test(pool,token)


def test_pool_limit_prevents_test(monkeypatch):
    p=fresh('poolcap');p.mkdir()
    monkeypatch.setattr(return_io,'usage',lambda p:96_000_000)
    with pytest.raises(ValueError,match='100 MB'):return_io.operate('test',p,'p0123456789')
    assert not (p/'p0123456789').exists()


def test_write_test_subprocess_timeout(monkeypatch):
    seen=[]
    class Child:
        def __init__(self,argv,**kw):self.args=argv;self.stdout=io.StringIO();self.stderr=io.StringIO()
        def communicate(self,timeout):
            assert timeout==60 and self.args[4]=='test'
            raise subprocess.TimeoutExpired(self.args,timeout)
        def kill(self):seen.append('kill')
        def wait(self,*a,**kw):raise AssertionError('Must not wait on an NFS-blocked child')
    monkeypatch.setattr(R.subprocess,'Popen',Child)
    with pytest.raises(TimeoutError):R.write_test('/does/not/matter','p0123456789')
    assert seen==['kill']



@pytest.mark.parametrize('pool_ok,gcs_ok',[(True,False),(False,True),(True,True),(False,False)])
def test_independent_returns(monkeypatch,pool_ok,gcs_ok):
    p,src=local_source();calls=[]
    def pool(action,*a,**k):
        calls.append(action)
        if not pool_ok:raise OSError('unwritable')
        return dict(verified=True)
    def upload(*a):
        calls.append('gcs')
        if not gcs_ok:raise TimeoutError('upload timed out')
        return dict(verified=True,objects={})
    monkeypatch.setattr(R,'pool_operation',pool);monkeypatch.setattr(R,'upload',upload)
    r=R.publish(src,p/'pool','p0123456789','0'*64,0,mode='proof')
    assert r['returned']==(pool_ok or gcs_ok)
    assert r['status']==('COMPLETE' if pool_ok or gcs_ok else 'INCOMPLETE')
    assert calls==['publish','gcs','receipt']
    receipt=json.loads((src/'RETURN_RECEIPT.json').read_text())
    assert receipt['verified_channels']==(["pool"] if pool_ok else [])+(["gcs"] if gcs_ok else [])


def test_real_pool_publish_and_receipt(monkeypatch):
    p,src=local_source();pool=p/'pool';token='p0123456789';R.write_test(pool,token)
    monkeypatch.setattr(R,'upload',lambda *a:dict(verified=False,error='offline fixture'))
    r=R.publish(src,pool,token,'0'*64,0,mode='proof')
    assert r['returned'] and r['verified_channels']==['pool']
    R.verify(json.loads((pool/token/'EXIT.json').read_text()),pool/token/'result.tar.gz','0'*64)
    assert json.loads((pool/token/'RETURN_RECEIPT.json').read_text())['returned']
    assert R.usage(pool)<100_000_000 and R.usage(pool/token)<20_000_000


@pytest.mark.parametrize('mode,expected',[('proof',18_999_999),('production',89_899_999)])
def test_packet_cap_applied_before_writing(monkeypatch,mode,expected):
    p,src=local_source()
    def writer(raw,limit):
        assert limit==expected
        raise R.S.BudgetError('test cap')
    monkeypatch.setattr(R.S,'LimitedWriter',writer)
    with pytest.raises(R.S.BudgetError):R.publish(src,p/'pool','p0123456789','0'*64,0,mode=mode)


@pytest.mark.parametrize('corrupt',[False,True])
def test_upload_generation_and_readback_sha(monkeypatch,corrupt):
    p=fresh('cloud3');p.mkdir();(p/'result.tar.gz').write_bytes(b'archive');(p/'EXIT.json').write_bytes(b'{}')
    objects={};calls=[]
    def cloud(argv,**kw):
        calls.append(argv);assert kw['env']['CLOUDSDK_CONFIG']==R.CLOUD_CONFIG and kw['timeout']<=180
        if argv[2]=='cp':objects[argv[4]]=Path(argv[3]).read_bytes();return NS(returncode=0)
        if argv[2]=='objects':return NS(stdout=json.dumps(dict(generation='1234',size=len(objects[argv[4]]))))
        assert argv[2]=='cat' and argv[3].endswith('#1234')
        kw['stdout'].write(b'bad' if corrupt else objects[argv[3].split('#')[0]])
        return NS(returncode=0)
    monkeypatch.setattr(R.subprocess,'run',cloud)
    if corrupt:
        with pytest.raises(ValueError,match='SHA256'):R.upload(p,'p0123456789')
    else:
        r=R.upload(p,'p0123456789');assert r['verified'] and len(r['objects'])==2
        assert all(v['generation']=='1234' for v in r['objects'].values())
        assert all(v['sha256']==hashlib.sha256(objects[v['uri']]).hexdigest() for v in r['objects'].values())
        assert [json.loads(l)['upload']['generation'] for l in (p/'JOB.log').read_text().splitlines()]==['1234','1234']


def fetch_fixture(size=10):
    p=fresh('fetch3');p.mkdir()
    cfg=dict(token='p0123456789',pool='/unwritable/pool',mode='production',plan_sha256='0'*64)
    (p/'CONFIG.json').write_text(json.dumps(cfg));(p/'SUBMISSION.json').write_text(json.dumps(dict(status='SUBMITTED',job=123)))
    receipt=dict(token=cfg['token'],job=123,plan_sha256='0'*64,synthetic=False,status='FAILED',
                 archive=dict(name='result.tar.gz',bytes=size,sha256='1'*64))
    return p,receipt


def test_large_fetch_prints_command_without_stream(monkeypatch):
    p,receipt=fetch_fixture(20_000_000);calls=[]
    def remote(argv):calls.append(argv);return NS(returncode=0,stdout=json.dumps(receipt).encode())
    monkeypatch.setattr(L,'remote',remote)
    with pytest.raises(L.TransferRegistrationRequired,match='Register a governor stream') as e:L.fetch(p)
    assert len(calls)==1 and 'ossh.sh' in str(e.value) and 'result.tar.gz' in str(e.value)


def test_fetch_streams_gcs_stdout_without_pool_write(monkeypatch):
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w:gz') as tf:
        data=b'{}';m=tarfile.TarInfo('FAILED.json');m.size=len(data);tf.addfile(m,io.BytesIO(data))
    archive=raw.getvalue();p,receipt=fetch_fixture(len(archive));receipt['archive']['sha256']=hashlib.sha256(archive).hexdigest()
    calls=[]
    def remote(argv):
        calls.append(argv)
        return NS(returncode=1,stdout=b'') if argv[0]=='python3' else NS(returncode=0,stdout=json.dumps(receipt).encode())
    def stream(argv,**kw):
        assert 'gcloud storage cat' in argv[-1] and 'gs://' in argv[-1]
        assert '>' not in argv[-1] and '/unwritable/pool' not in argv[-1]
        kw['stdout'].write(archive);return NS(returncode=0)
    monkeypatch.setattr(L,'remote',remote);monkeypatch.setattr(L.subprocess,'run',stream)
    r=L.fetch(p);assert r['channel']=='gcs' and len(calls)==2
    assert (p/'fetched/result.tar.gz').read_bytes()==archive


def test_accepted_receipt_hashes_and_need_list():
    r=json.loads((ROOT/'parity/DEV20.json').read_text());need=set()
    assert len(r['ids'])==20 and r['ids']==sorted(r['ids'])
    for value in r['receipts'].values():
        raw=(json.dumps(value['receipt'],sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
        assert hashlib.sha256(raw).hexdigest()==value['pin']['sha256']
        need.update(p['sha256'] for p in value['receipt']['frames'])
    assert sorted(need)==r['need'] and len(need)==576
    assert not any('prompt_token_ids' in row for row in r['arms']['ON16k'])


def test_failed_phase_a_cannot_start_phase_b(monkeypatch):
    import chain
    p=fresh('gate3');p.mkdir();package=p/'p';(package/'cohort').mkdir(parents=True)
    (package/'cohort/MEDIA_MANIFEST.json').write_text('[]');(package/'TRANSPORT.json').write_text('{}')
    calls=[]
    def utility(spec,script,*args,**kw):calls.append(Path(script).name);raise ValueError('Phase A failed')
    monkeypatch.setattr(chain,'utility',utility)
    cfg=dict(mode='proof',phase_b=True,proof_only=True,release={},plan_sha256='0'*64,
             spec=dict(run=str(p/'r'),package=str(package),inputs=dict(video_root='unused')))
    with pytest.raises(ValueError,match='Phase A failed'):chain.run(cfg)
    assert calls==['runtime_checks.py']


def test_write_test_failure_precedes_all_staging(monkeypatch):
    p=fresh('firststep3');p.mkdir();logical=J.SJ/'ap0123456789';events=[]
    cfg=dict(token='p0123456789',pool=str(p/'pool'),plan_sha256='0'*64,output=str(logical/'o'),
             spec=dict(run=str(logical/'r'),artifact=dict(path=str(logical/'artifact'))))
    monkeypatch.setattr(J.signal,'signal',lambda *a:None)
    def fail(*a):events.append('pool');raise TimeoutError('NFS test deadline')
    def forbidden(*a,**k):raise AssertionError('Staging started after pool refusal')
    monkeypatch.setattr(R,'write_test',fail);monkeypatch.setattr(J.S,'stage',forbidden)
    monkeypatch.setattr(J,'storage_proof',forbidden);monkeypatch.setattr(J,'card',lambda **k:{})
    monkeypatch.setattr(R,'publish',lambda *a,**k:dict(status='FAILED'))
    assert J.run(p,cfg)!=0 and events==['pool']
    failed=json.loads((J.physical(p,cfg['spec']['run'])/'FAILED.json').read_text())
    assert failed['error']=='NFS test deadline'


def test_comparison_reports_generation_disagreement(monkeypatch):
    p=fresh('compare3');p.mkdir();dest=p/'d0';out=dest/'results';ids=[f'q{i:02}' for i in range(20)]
    ref=dict(ids=ids,arms={},prompt_probes=[])
    checks=[]
    for i,id in enumerate(ids[:16]):
        row=dict(example_id=id,prompt_equal=True,observed_ids_sha256='1'*64)
        if i<2:row['pixels']=dict(pass_=True)
        checks.append(row);ref['prompt_probes'].append(row)
    for arm,rel in [('ON16k','0/items_b0.jsonl'),('B2048','budget_2048/0/items_b0.jsonl'),('B4096','budget_4096/0/items_b0.jsonl')]:
        rows=[dict(example_id=id,prompt_text='p',raw_generation='a',token_ids=[1],extracted_answer='a',score=1) for id in ids]
        ref['arms'][arm]=copy.deepcopy(rows)
        rows[0].update(raw_generation='b',token_ids=[2],extracted_answer='b',score=0)
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (out/'0/summary_b0.json').write_text(json.dumps(dict(parity_pass=True,parity_checks=checks)))
    report=phase_b.compare(ref,dest,'b0')
    assert report['accepted_prompt_ids']['exact']==16
    for arm in report['arms'].values():
        assert arm['exact']['raw_generation']==19 and arm['actual_score']==.95 and arm['accepted_score']==1


def test_final_trace_returns_generation_receipts(monkeypatch):
    p=fresh('trace3');p.mkdir();local=p/'return';local.mkdir()
    (p/'RETURN.json').write_text(json.dumps(dict(local_return=str(local))))
    (local/'RETURN_RECEIPT.json').write_text(json.dumps(dict(returned=True)))
    import trace_runtime
    monkeypatch.setattr(trace_runtime,'collect',lambda root,target:target.write_bytes(b'fixture-trace'))
    calls=[]
    def pool(action,*args,**kw):calls.append(action);return dict(verified=True)
    def upload(local,token,names):
        assert names==('TRACE.json.gz','TRACE.pin.json')
        return dict(verified=True,objects={n:dict(generation='1',sha256=R.sha(local/n)) for n in names})
    monkeypatch.setattr(R,'pool_operation',pool);monkeypatch.setattr(R,'upload',upload)
    r=R.final_trace(p,dict(token='p0123456789',pool=str(p/'pool'),plan_sha256='0'*64))
    assert calls==['trace','receipt'] and r['gcs']['verified']
    receipt=json.loads((local/'RETURN_RECEIPT.json').read_text())
    assert receipt['final_trace']['gcs']['objects']['TRACE.json.gz']['generation']=='1'


def test_failed_second_upload_preserves_first_generation(monkeypatch):
    p=fresh('partialcloud3');p.mkdir();(p/'result.tar.gz').write_bytes(b'a');(p/'EXIT.json').write_bytes(b'{}')
    def cloud(argv,**kw):
        if argv[2]=='cp':
            if argv[3].endswith('EXIT.json'):raise subprocess.TimeoutExpired(argv,180)
            return NS(returncode=0)
        if argv[2]=='objects':return NS(stdout=json.dumps(dict(generation='17',size=1)))
        kw['stdout'].write(b'a');return NS(returncode=0)
    monkeypatch.setattr(R.subprocess,'run',cloud)
    with pytest.raises(R.UploadError) as caught:R.upload(p,'p0123456789')
    first=caught.value.objects['result.tar.gz']
    assert first['generation']=='17' and first['verified']
    assert caught.value.objects['EXIT.json']['generation'] is None


def test_pool_helper_runs_under_job_trace(monkeypatch):
    import gzip
    p=fresh('tracedpool3');p.mkdir();config=p/'CONFIG.json'
    config.write_text(json.dumps(dict(mode='proof',spec=dict(package=str(ROOT),run=str(p/'r')))))
    monkeypatch.setenv('A_TRACE_RUNNER',str(ROOT/'launcher/trace_runtime.py'))
    monkeypatch.setenv('A_JOB_ROOT',str(p));monkeypatch.setenv('A_JOB_CONFIG',str(config))
    assert R.write_test(p/'pool','p0123456789')['bytes']==4*1024**2
    files=[row for path in (p/'t').glob('*.json.gz') for row in json.loads(gzip.decompress(path.read_bytes()))['files']]
    assert any(r['file']=='launcher/return_io.py' and r['lines'] for r in files)
