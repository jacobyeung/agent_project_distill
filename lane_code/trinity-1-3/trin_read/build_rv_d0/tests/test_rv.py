"""CPU fixtures for ReVSI admission, unchanged scorer, and packet failures."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import pytest
import rv_read as R


def js(p, value):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(value)+'\n')


def media(tmp_path, entries=None):
    data = b'fixture video bytes'
    need = tmp_path/'NEED.json'
    js(need, [dict(relative_path='one.mp4', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())])
    archive = tmp_path/'media.tar'
    with tarfile.open(archive, 'w') as tf:
        for name, content, kind in entries or [('one.mp4', data, tarfile.REGTYPE)]:
            m = tarfile.TarInfo(name); m.type = kind; m.size = len(content) if kind == tarfile.REGTYPE else 0
            if kind in (tarfile.SYMTYPE,tarfile.LNKTYPE): m.linkname = '/tmp/outside'
            tf.addfile(m, io.BytesIO(content) if m.size else None)
    return archive, need


def test_stage_and_receipt(tmp_path):
    archive, need = media(tmp_path); out=tmp_path/'videos'
    r = R.extract_media(archive,out,need)
    assert r['complete'] and r['files']['one.mp4']['sha256'] == R.T.sha(out/'one.mp4')
    assert r['namespace_target'] == R.LOGICAL_MEDIA
    with pytest.raises(ValueError,match='exists'): R.extract_media(archive,out,need)


@pytest.mark.parametrize('entries', [
    [('../escape.mp4',b'fixture video bytes',tarfile.REGTYPE)],
    [('/escape.mp4',b'fixture video bytes',tarfile.REGTYPE)],
    [('one.mp4',b'',tarfile.SYMTYPE)], [('one.mp4',b'',tarfile.LNKTYPE)],
    [('one.mp4',b'',tarfile.FIFOTYPE)], [('one.mp4',b'x',tarfile.REGTYPE)],
    [('one.mp4',b'fixture video bytes',tarfile.REGTYPE)]*2,
    [('two.mp4',b'fixture video bytes',tarfile.REGTYPE)],
])
def test_stage_rejects_headers(tmp_path,entries):
    archive, need=media(tmp_path,entries)
    with pytest.raises(ValueError): R.extract_media(archive,tmp_path/'videos',need)
    assert not (tmp_path/'videos').exists()


def test_stage_hash_failure_retains_partial(tmp_path):
    archive, need=media(tmp_path,[('one.mp4',b'Fixture video bytes',tarfile.REGTYPE)])
    with pytest.raises(ValueError,match='SHA256'):R.extract_media(archive,tmp_path/'videos',need)
    assert (tmp_path/'videos/one.mp4').exists()
    assert not (tmp_path/'videos/RECEIPT.json').exists()
    with pytest.raises(ValueError,match='exists'):R.extract_media(archive,tmp_path/'videos',need)


def test_stage_missing_and_symlink(tmp_path):
    archive,need=media(tmp_path)
    rows=R.T.load(need);rows.append(dict(rows[0],relative_path='two.mp4'));js(need,rows)
    with pytest.raises(ValueError,match='inventory'):R.extract_media(archive,tmp_path/'videos',need)
    link=tmp_path/'link';link.symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):R.extract_media(archive,link/'videos',need)


def test_runtime_pins_equal_and_changed(tmp_path,monkeypatch):
    root=tmp_path/'root';js(root/'bootstrap/CONFIG.json',dict(assets=R.T.load(R.KIT/'launcher/ORCHARD_ASSETS.json')))
    js(root/'STAGING.json',dict(pieces={n:dict(status='complete') for n in ('runtime_0','runtime_1','runtime_2','base','export')}))
    assert R.runtime_check(root)['assets_identical']
    value=R.T.load(root/'bootstrap/CONFIG.json');value['assets']['groups'][0][0][2]='0'*64;js(root/'bootstrap/CONFIG.json',value)
    with pytest.raises(ValueError,match='Runtime pins differ'):R.runtime_check(root)


def test_reviewed_payload():
    assert R.pins_check()
    assert len(R.need_rows(R.KIT/'media/NEED_261.json'))==261
    assert len(R.journal(R.KIT/'cohort/c5.jsonl'))==679


def test_artifact_paths_and_refusals(tmp_path,monkeypatch):
    monkeypatch.setattr(R,'local',lambda p:Path(p))
    root=tmp_path
    p=root/'fsw/ap/8865619b/runs/359fcc3c/m100/artifact.json';js(p,dict(step=100))
    with pytest.raises(ValueError,match='regular file'):R.select_artifact(root,p,R.T.sha(p))
    with pytest.raises(ValueError,match='64 frames'):R.select_artifact(root,p,R.T.sha(p),64)
    with pytest.raises(ValueError,match='SHA256'):R.select_artifact(root,p,'0'*64)
    foreign=root/'fsw/ap/8865619b/runs/foreign/m100/artifact.json';js(foreign,dict(step=100))
    with pytest.raises(ValueError,match='allowed run'):R.select_artifact(root,foreign,R.T.sha(foreign))


def test_two_card_readings(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(R.T,'check_card',lambda n: calls.append(n) or dict(uuid='GPU-1',index=n))
    pauses=[];p=tmp_path/'CARD.json'
    assert R.card_admission('0',p,pause=pauses.append)['passed']
    assert calls==['0','0'] and pauses==[60]
    assert len(R.T.load(p)['readings'])==2


@pytest.mark.parametrize('failure',['busy','uuid'])
def test_second_card_failure(tmp_path,monkeypatch,failure):
    n=[0]
    def check(index):
        n[0]+=1
        if n[0]==2 and failure=='busy':raise ValueError('busy')
        return dict(uuid=str(n[0]) if failure=='uuid' else 'gpu')
    monkeypatch.setattr(R.T,'check_card',check)
    with pytest.raises(ValueError):R.card_admission('0',tmp_path/'CARD.json',pause=lambda n:None)
    assert not R.T.load(tmp_path/'CARD.json')['passed']


def test_namespace_binds(tmp_path,monkeypatch):
    root=tmp_path; (root/'rv_media').mkdir()
    monkeypatch.setattr(R.T,'namespace',lambda *a,**k:['bwrap','--unshare-net','--ro-bind',str(root/'trinity_runner_t6'),'/trinity-build'])
    args=R.namespace(root)
    assert ['--ro-bind',str(R.BUILD),'/trinity-build']==args[2:5]
    assert args[-3:]==['--ro-bind',str(root/'rv_media'),R.LOGICAL_MEDIA]
    assert str(R.KIT) in args and '--unshare-net' in args


def test_config_keeps_engine_contract(tmp_path):
    cfg=R.make_config(tmp_path,tmp_path/'out','proof',R.T.load(R.KIT/'launcher/MODELS.json')['cp1m200'])
    assert cfg['phase_b'] is False and cfg['mode']=='proof'
    assert cfg['spec']['inputs']['video_root']==R.LOGICAL_MEDIA
    text=(R.KIT/'reader/official_adapter.py').read_text()
    assert 'max_seqs=32,inflight=16' in text and "engine_version='0.32.0'" in text


def synthetic_packet(tmp_path):
    """Run the kit's real scorer on all 679 fixture answers; no model imports."""
    p=tmp_path/'packet';cohort=R.journal(R.KIT/'cohort/c5.jsonl')
    rows=[dict(r,example_id=k,status='complete',score=(int(k)%3)/2,token_ids=[1,int(k)],raw_generation='unmodified fixture') for k,r in cohort.items()]
    for f in R.ARMS.values():
        q=p/'a0/results/0'/f;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    js(p/'a0/request.json',dict(mode='production'))
    subprocess.run([sys.executable,'-B',str(R.KIT/'reader/official_score.py'),'--dest',str(p/'a0'),'--cohort',str(R.KIT/'cohort/c5.jsonl'),'--output',str(p/'report')],check=True,stdout=subprocess.PIPE)
    js(p/'COMPLETE.json',dict(mode='production',items=679,generation_synthetic=False))
    js(p/'EXIT.json',dict(status='COMPLETE',fixture=True))
    js(p/'SPEC.json',dict(step=544,artifact=R.T.load(R.KIT/'launcher/MODELS.json')['cp1m200']))
    return p


@pytest.fixture
def packet_fixture(tmp_path):return synthetic_packet(tmp_path)


def test_compare_real_scorer(packet_fixture):
    r=R.compare(packet_fixture,packet_fixture)
    for arm in R.ARMS:
        assert r['arms'][arm]['token_id_equality_share']==1
        assert all(g['score_equality_share']==1 for g in r['arms'][arm]['categories'].values())


def test_compare_token_divergences(packet_fixture,tmp_path):
    b=tmp_path/'second';shutil_copy_packet(packet_fixture,b)
    p=b/'a0/results/0/items_a0.jsonl';lines=p.read_text().splitlines();r=json.loads(lines[0]);r['token_ids'].append(99);lines[0]=json.dumps(r);p.write_text('\n'.join(lines)+'\n')
    result=R.compare(packet_fixture,b)['arms']['ON16k']
    assert result['tokens_equal']==678
    d=next(x for x in result['per_item'] if not x['tokens_equal'])
    assert d['first_divergence']==dict(index=2,a=None,b=99)


def shutil_copy_packet(a,b):
    import shutil
    shutil.copytree(a,b)


@pytest.mark.parametrize('change',['missing','duplicate','tokens','score','mean','failed','synthetic'])
def test_compare_rejects_bad_packet(packet_fixture,change):
    p=packet_fixture
    if change in ('missing','duplicate','tokens'):
        path=p/'a0/results/0/items_a0.jsonl';lines=path.read_text().splitlines()
        if change=='missing':lines=lines[1:]
        elif change=='duplicate':lines.append(lines[0])
        else:
            row=json.loads(lines[0]);row.pop('token_ids');lines[0]=json.dumps(row)
        path.write_text('\n'.join(lines)+'\n')
    elif change in ('score','mean'):
        path=p/'report/ON16k.json';r=R.T.load(path)
        if change=='score':r['rows'][0]['score']=0.1234
        else:r['five_category_mean']['score']=0.1234
        js(path,r)
    elif change=='failed':js(p/'EXIT.json',dict(status='FAILED'))
    else:js(p/'COMPLETE.json',dict(mode='production',items=679,generation_synthetic=True))
    with pytest.raises(ValueError):R.compare(p,p)


@pytest.mark.parametrize('mode,fail', [('proof',None),('production',None),('production','exit'),('production','stub'),('production','sampler'),('proof','parity')])
def test_launch_packet(tmp_path,monkeypatch,mode,fail):
    root=tmp_path/'root';root.mkdir();out=root/'packet';(root/'rv_media').mkdir();js(root/'rv_media/RECEIPT.json',{})
    artifact=R.T.load(R.KIT/'launcher/MODELS.json')['cp1m200']
    monkeypatch.setattr(R,'local',lambda p:Path(p))
    monkeypatch.setattr(R,'select_artifact',lambda *a:artifact)
    monkeypatch.setattr(R,'pins_check',lambda:'pin')
    monkeypatch.setattr(R,'runtime_check',lambda r:{})
    monkeypatch.setattr(R,'media_check',lambda r:{})
    monkeypatch.setattr(R,'proof_check',lambda *a:{})
    monkeypatch.setattr(R.shutil,'disk_usage',lambda r:SimpleNamespace(free=1000*1024**3))
    monkeypatch.setattr(R.T,'environment',lambda *a,**k:{})
    monkeypatch.setattr(R.T,'bwrap_evidence',lambda *a:{'path':'/usr/bin/bwrap'})
    monkeypatch.setattr(R.T,'llguidance_evidence',lambda *a:{'enabled':True})
    monkeypatch.setattr(R.T,'probe',lambda *a,**k:dict(versions=dict(vllm='0.32.0'),passed=True))
    monkeypatch.setattr(R,'namespace',lambda *a,**k:['bwrap','--unshare-net'])
    monkeypatch.setattr(R.T,'sandbox_receipt',lambda cmd,*a:dict(namespace_argv=cmd,namespace_executed=False))
    def card(index,p):js(p,dict(passed=True,readings=[{},{}]))
    monkeypatch.setattr(R,'card_admission',card)
    class Sampler:
        def __init__(self,*a):self.errors=['fixture'] if fail=='sampler' else [];self.stop=SimpleNamespace(set=lambda:None);self.thread=SimpleNamespace(start=lambda:None,join=lambda **k:None)
    monkeypatch.setattr(R.T,'Sampler',Sampler)
    calls=[]
    def run(argv,**kwargs):
        calls.append(argv)
        assert argv[0]==R.T.VNICE and len(argv)==2 and '-I -B' in argv[1]
        assert kwargs['env']['LLG_STUB_LOG']==str(out/'llg_stub_calls.jsonl')
        (out/'llg_stub_calls.jsonl').write_text(json.dumps(dict(event='import',pid=1,module='llguidance'))+'\n'+(json.dumps(dict(event='call',name='blocked'))+'\n' if fail=='stub' else ''))
        if fail=='exit':return 7
        n=10 if mode=='proof' else 679
        js(out/'COMPLETE.json',dict(items=n,mode=mode))
        for arm,f in R.ARMS.items():
            js(out/'report'/(arm+'.json'),dict(items=n,groups={g:{} for g in R.GROUPS}))
            js(out/'a0/results/0'/f,{})
        if mode=='proof':js(out/'PARITY.json',dict(items=20,processor_checked=fail!='parity',all_prompt_bytes_equal=True,prompt_pins_equal=True))
        return 0
    monkeypatch.setattr(R.subprocess,'call',run)
    args=SimpleNamespace(root=str(root),out=str(out),artifact='unused',sha256='unused',frames=32,command='rv-proof' if mode=='proof' else 'rv-read',proof='fixture',gpu=0,token='a12345678',bwrap='/usr/bin/bwrap')
    if fail:
        with pytest.raises((RuntimeError,ValueError)):R.launch(args)
        assert R.T.load(out/'EXIT.json')['status']=='FAILED'
    else:
        assert R.launch(args)['status']=='COMPLETE'
        done=R.T.load(out/'EXIT.json');R.verify_outputs(out,done)
        assert R.T.load(out/'CARD.json')['passed']
        assert R.T.load(out/'SANDBOX.json')['namespace_executed']
    assert len(calls)==1
    with pytest.raises(ValueError,match='exists'):R.launch(args)
