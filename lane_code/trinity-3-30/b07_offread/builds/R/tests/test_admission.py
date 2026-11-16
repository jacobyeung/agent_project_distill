"""Exercise the unchanged four-part stager and full checker on tiny exports."""
from contextlib import contextmanager
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/vsi/launcher'))
sys.path.insert(0,str(ROOT/'kit/vsi/proof'))
import export_stage as E
import orchard_stage as S
import orchard_job as J
import gate
import fixtures as F


def test_four_parts_full_checker_and_bound_hash(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();(root/'archives').mkdir();(root/'bootstrap').mkdir()
    logical=str(J.FSW/'ap/8865619b/runs/359fcc3c/m200/artifact.json')
    artifact=J.physical(root,logical)
    fixture=tmp_path/'fixture';fixture.mkdir()
    base,bm,export,ap=F.models(fixture,artifact)
    a=json.loads(ap.read_text());a['step']=200;F.js(ap,a)
    (export/'heads.pt').write_bytes(b'fixture')
    archive=F.archive(fixture/'export.tar',{'m200/'+str(p.relative_to(export)):p.read_bytes() for p in export.rglob('*') if p.is_file()})
    done=fixture/'input.done';done.write_text('q8/8865619b/359fcc3c_m200.tar '+str(archive['bytes'])+' '+archive['sha256']+'\n')
    cloud=fixture/'cloud';cloud.mkdir()
    c=dict(x0='a'*64,x1=archive['sha256'],x2=1,x3=archive['bytes'],spec=dict(step=200,artifact=dict(path=logical,kind='c1_export',sha256=None),
        models={'base':{'path':str(base)}},interpreters={'p1cpu':sys.executable}),assets={'gcloud_config':str(cloud)})
    F.js(root/'bootstrap/CONFIG.json',c)
    for name in E.CHECKER_PINS:
        target=J.physical(root,E.CHECKER.parent/name);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/'kit/vsi/reader/out'/name).read_bytes())
    raw=Path(archive['path']).read_bytes();size=len(raw)//4
    parts=[raw[i*size:(i+1)*size] if i<3 else raw[i*size:] for i in range(4)]
    requests=[]
    @contextmanager
    def process(argv,env,log):
        requests.append(argv[-1]);idx=int(argv[-1].split('.part')[1][:2])
        yield io.BytesIO(parts[idx])
    original=E.Path
    def path(value):
        if str(value).startswith('/project/community/jjyeung/okh7/x_f5c353f7/o'):
            # fetch_and_stage creates the receipt path using /, so map the parent.
            return fixture/'receipt'
        return original(value)
    receipts=fixture/'receipt';receipts.mkdir()
    (receipts/'gcs_359fcc3c_m200.done').write_bytes(done.read_bytes())
    monkeypatch.setattr(E,'Path',path)
    monkeypatch.setattr(gate,'Path',path)
    monkeypatch.setattr(E.T,'writable',lambda p:original(p).resolve())
    monkeypatch.setattr(E,'writable',lambda p:original(p).resolve())
    monkeypatch.setattr(S,'MIN_FREE',0)
    monkeypatch.setattr(S,'process_stream',process)
    monkeypatch.setattr(J,'namespace',lambda *a:[])
    original_run=subprocess.run
    def run(argv,**kw):
        argv=list(argv);argv[2]=str(J.physical(root,E.CHECKER))
        argv[argv.index('--export')+1]=str(artifact)
        # The full checker itself runs unchanged in a separate CPU interpreter.
        return original_run(argv,**kw)
    monkeypatch.setattr(E.subprocess,'run',run)
    monkeypatch.setattr(J,'environment',lambda r:dict(__import__('os').environ,PYTHONDONTWRITEBYTECODE='1'))
    gate.before(root,c)
    result=E.fetch_and_stage(root,c)
    assert len(requests)==4 and result['status']=='complete'
    assert result['checker']['status']=='VERIFIED' and result['checker']['step']==200
    assert result['checker_mode']=='full'
    assert result['tar_sha256']==c['x1']
    gate.after(root,c,{'export':result})
    bad=copy.deepcopy(c);bad['x1']='b'*64
    with pytest.raises(ValueError,match='X1 receipt'):gate.before(root,bad)
    with pytest.raises(ValueError,match='X1 admission'):gate.after(root,bad,{'export':result})


def test_tampered_tar_is_refused_before_extraction(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir()
    source=tmp_path/'a.tar';source.write_bytes(b'not a tar')
    done=tmp_path/'a.json';done.write_text(json.dumps(dict(object='x',bytes=9,sha256='a'*64)))
    monkeypatch.setattr(E.T,'writable',lambda p:Path(p).resolve())
    monkeypatch.setattr(E,'writable',lambda p:Path(p).resolve())
    args=NS(root=str(root),run='359fcc3c',step=200,tar=str(source),done=str(done),full=True,bwrap='/unused')
    with pytest.raises(ValueError,match='Tar SHA256'):E.stage_export(args)
    assert not (root/'exports').exists()
