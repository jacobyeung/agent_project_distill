from pathlib import Path
import json
import sys
import pytest
from offnative.source import bind_source,CLIP_LABEL
from offnative.io import dump,load,sha,tar_bytes
from offnative.transport import packet,inventory


def test_dense_source_freeze_and_mapping(tmp_path):
    with pytest.raises(ValueError,match='g3t-source'):bind_source(None)
    with pytest.raises(ValueError,match='P8'):bind_source('clip32',production=True)
    assert bind_source('clip32',freeze={'g3t_source':'clip32'},production=True)['label']==CLIP_LABEL
    with pytest.raises(ValueError,match='mapping'):bind_source('original')
    p=tmp_path/'mapping.json'
    dump(p,{'schema':'clip-original-v1','registration':'signed freeze','clips':{'x':{
        'clip_sha256':'a'*64,'original_sha256':'b'*64,'anchor_indices':list(range(0,64,2)),
        'dense_indices':list(range(64)),'anchor_slots':list(range(0,64,2))}}})
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
    root=Path(__file__).resolve().parents[2]/'work/n2_native_harness_03'
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
