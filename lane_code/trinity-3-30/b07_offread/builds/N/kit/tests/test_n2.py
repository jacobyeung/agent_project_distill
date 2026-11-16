from pathlib import Path
import json
import sys
import pytest
from offnative.source import bind_source,CLIP_LABEL
from offnative.io import dump,load,sha,tar_bytes
from offnative.transport import packet,inventory


def test_dense_source_freeze_and_mapping(tmp_path):
    with pytest.raises(ValueError,match='g3t-source'):bind_source(None)
    with pytest.raises(ValueError,match='diagnostic'):bind_source('clip32',production=True)
    assert bind_source('clip32')['label']==CLIP_LABEL
    with pytest.raises(ValueError,match='mapping'):bind_source('original',mapping=tmp_path/'missing')
    p=tmp_path/'mapping.json'
    dump(p,{'schema':'revsi-dense64-v1','registration':'signed freeze','clips':{'x':{
        'path':'x.mp4','clip_sha256':'a'*64,'original_sha256':'b'*64,'anchor_indices':list(range(0,64,2)),
        'dense_indices':list(range(64)),'dense_decode_indices':list(range(64)),'anchor_slots':list(range(0,64,2))}}})
    assert bind_source('original',mapping=p)['mapping_sha256']==sha(p)
    v=load(p);v['clips']['x']['anchor_indices'][1]=3;dump(p,v)
    with pytest.raises(ValueError,match='correspondence'):bind_source('original',mapping=p)


def test_packet_scans_actual_bytes_and_can_be_unpacked(tmp_path):
    import tarfile,io,zlib
    files={'0.py':b'print("revsi sam3 trinity")','a/b':b'model'}
    p=tmp_path/'packet.tar';receipt=packet(files,p,'a'*24)
    assert receipt['passed'] and inventory(p.read_bytes())['sha256']==sha(p)
    with tarfile.open(p) as outer:
        raw=zlib.decompress(bytes.fromhex(outer.extractfile('0').read().decode()))
    with tarfile.open(fileobj=io.BytesIO(raw)) as inner:
        assert {m.name:inner.extractfile(m).read() for m in inner}==files
    with pytest.raises(ValueError,match='leaked'):inventory(b'job-revsi')


def test_watchdog_reserves_return_window(tmp_path):
    from offnative.watchdog import run
    from datetime import datetime,timezone
    import time
    deadline=datetime.fromtimestamp(time.time()+601,timezone.utc).isoformat()
    r=run([sys.executable,'-B','-c','import time;time.sleep(10)'],tmp_path,tmp_path/'deadline.json',
          deadline_utc=deadline)
    assert r['timed_out'] and r['seconds']<4 and r['return_seconds']==600


def test_query_digest_detects_mutation():
    from copy import deepcopy
    from offnative.proof import verify_served
    r={'decode':{'text':'x','tokens':[], 'calls':[{'response':'2 m'}],
                 'heads':{'ground_queries':[{'name':'chair','points':[1,2]}]}}}
    assert verify_served(r,r)['passed']
    other=deepcopy(r);other['decode']['heads']['ground_queries'][0]['points'][0]=7
    assert not verify_served(r,other)['passed']


def test_native_decoder_rehearsal_evidence():
    root=Path(__file__).resolve().parents[2]/'work/n2_rehearsal_harness_release'
    assert load(root/'RESULT.json')['passed']
    from offnative.io import rows
    calls=[c for row in rows(root/'return/decode.jsonl') for c in row['decode']['calls']]
    assert any(c.get('spec_version')=='3.14' for c in calls)
    assert any(c['call'].startswith('<ground') for c in calls)


def test_frozen_proposal_pipeline(tmp_path):
    import hashlib,io
    import numpy as np
    from PIL import Image
    from offnative.proposals import build
    frames=tmp_path/'frames';frames.mkdir()
    captures=[];items=[]
    for video in range(2):
        entries=[]
        for i in range(32):
            data=io.BytesIO();Image.fromarray(np.full((16,16,3),i+video*32,dtype=np.uint8)).save(data,format='PNG')
            raw=data.getvalue();h=hashlib.sha256(raw).hexdigest();name=h[:2]+'/'+h+'.png'
            p=frames/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
            entries.append({'path':name,'sha256':h,'index':i})
        scene='fixture/'+str(video)
        captures.append(dict(native=scene,scene=scene,anchor_indices=list(range(32)),frames=entries,
                             hw=[16,16],names={'chair':'chair'},phrases=['chair']))
        items.append(dict(scene=scene,question='Where is the chair?',operands=['chair'],options=[]))
    p=build(captures,items,frames,tmp_path/'proposals',checkpoint=None,source=None,stub=True)
    assert load(p)['synthetic'] is True
    from offnative.c8 import install
    P=install()
    m=load(load(p)['manifest']['path'])
    with pytest.raises(ValueError,match='stub'):
        P.validate_cache_header(m,load(p)['manifest']['sha256'],
            load(p.parent/'dense_aliases/candidates/BINDING.json'),
            load(p.parent/'dense_aliases/candidates/COMPLETE.json'))


def test_return_authentication_rejects_changed_job(tmp_path):
    from offnative.transport import authenticate
    d=tmp_path/'d';d.mkdir()
    dump(d/'CONFIG.json',{'token':'a'*24,'x0':'b'*64})
    (d/'packet.tar').write_bytes(b'opaque')
    dump(d/'SUBMISSION.json',{'status':'SUBMITTED','job':123,'config_sha256':sha(d/'CONFIG.json'),
                              'packet_sha256':sha(d/'packet.tar')})
    complete={'plan_sha256':sha(d/'CONFIG.json'),'synthetic':False}
    archive=d/'return.tar';archive.write_bytes(tar_bytes({'COMPLETE.json':json.dumps(complete).encode()}))
    receipt={'status':'COMPLETE','synthetic':False,'token':'a'*24,'job':123,
             'config_sha256':sha(d/'CONFIG.json'),'packet_sha256':sha(d/'packet.tar'),
             'binding_sha256':'b'*64,'archive':{'bytes':archive.stat().st_size,'sha256':sha(archive)}}
    assert authenticate(d,receipt,archive)['job']==123
    with pytest.raises(ValueError,match='identity'):authenticate(d,dict(receipt,job=124),archive)
    with pytest.raises(ValueError,match='synthetic'):authenticate(d,dict(receipt,synthetic=True),archive)


def test_r_stage_plan_covers_full_manifest(tmp_path):
    from offnative.stage_plan import prepare
    from offnative.cohort import cohort,media302
    from offnative.paths import r_launcher
    from offkit.bind import STEP544_SHA
    b={'benchmark':'revsi999t32','binding_sha256':'b'*64,'export':{'kind':'step544','sha256':STEP544_SHA}}
    inputs={'uploaded_media_root':'/project/community/jjyeung/okh7/12345678/','media':media302(cohort('revsi999t32'))}
    c,boot=prepare(b,inputs,tmp_path/'r','a'*24,'/project/community/jjyeung/okh7/12345678')
    files=r_launcher().unpack(boot['bootstrap/payload.tar.gz'])
    name=next(n for n in files if n.endswith('/cohort/MEDIA_MANIFEST.json'))
    assert len(json.loads(files[name]))==302
    assert c['x0']==b['binding_sha256'] and c['x1']==STEP544_SHA
    from offnative.staging import reviewed_modules
    for mod in reviewed_modules():
        assert Path(mod.__file__).is_file()


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_portable_worker_sources(tmp_path,kind):
    import subprocess,os
    from offnative.portable import sources,ROOTS
    from offnative.paths import OFFKIT
    from offnative.io import extract
    files,pins=sources()
    files['r.json']=json.dumps(ROOTS).encode()
    p=tmp_path/'sources.tar';p.write_bytes(tar_bytes(files))
    dest=tmp_path/'staged';extract(p,dest,max_bytes=64*1024**2)
    env=dict(os.environ,OFFNATIVE_ROOTS=str(dest/'r.json'),PYTHONPATH=str(OFFKIT),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
             HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    with (tmp_path/'execution.log').open('wb') as log:
        subprocess.run([sys.executable,'-B','-m','offnative.rehearse',str(dest/'work/result'),kind],
                       env=env,cwd=dest,stdout=log,stderr=log,check=True,timeout=120)
    assert load(dest/'work/result/RESULT.json')['passed']
    assert all(not Path(x).is_absolute() for x in ROOTS.values())


def test_named_admission_reports_each_missing_asset():
    from offnative.admission import check
    b={'mode':'production','benchmark':'revsi999t32','reader':{'kind':'harness','freeze_values':{}},
       'read_config':{'frames':{'count':32},'g3t':{'source':'clip32'}}}
    reasons=check(b,None)
    for name in ('sam3_weights','g3t_weights','selector','proof_original_export'):
        assert any('missing input: '+name==r for r in reasons)
    assert any('P8 freeze_values.g3t_source' in r for r in reasons)
    assert not any('not implemented or rehearsed' in r for r in reasons)


def test_original_indices_are_not_repeated(tmp_path):
    from offnative.frames import selected
    from offnative.paths import ROOT
    video=ROOT/'work/n2_rehearsal_harness_release/assets/0.mp4'
    assert len(selected(video,[0,12,31]))==3
    with pytest.raises(ValueError,match='increase'):selected(video,[0,0,1])
    with pytest.raises(ValueError,match='lacks'):selected(video,[0,12,99])


def test_reviewed_stage_rejects_runtime_hardlinks(tmp_path):
    import tarfile,io
    from offnative.staging import reject_hardlinks
    p=tmp_path/'linked.tar'
    with tarfile.open(p,'w') as archive:
        first=tarfile.TarInfo('a');first.size=1;archive.addfile(first,io.BytesIO(b'x'))
        link=tarfile.TarInfo('b');link.type=tarfile.LNKTYPE;link.linkname='a';archive.addfile(link)
    with pytest.raises(ValueError,match='hard link'):reject_hardlinks(p)
