"""Packet salt, secret exclusion, and salted runtime lookup contracts."""
import hashlib,hmac,importlib.util,io,json,os,subprocess,sys,tarfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'offnative/opacity.py'
if not SOURCE.is_file():
    ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'kit/xnames.py'

def module():
    spec=importlib.util.spec_from_file_location('salt_contract',SOURCE)
    x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
    return x

def archive(files):
    import gzip
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w') as tf:
        for n,v in sorted(files.items()):
            t=tarfile.TarInfo(n);t.size=len(v);tf.addfile(t,io.BytesIO(v))
    return gzip.compress(b.getvalue(),mtime=0)

def test_salt_matches_pins_rebuild_and_payload_changes():
    x=module();files={'vsi/data.py':b'value=1\n'}
    a,_=x.pack(files);b,_=x.pack(files);c,_=x.pack(dict(files,extra=b'2'))
    ta=json.loads(a['x0.json']);tc=json.loads(c['x0.json'])
    assert ta['salt']==json.loads(b['x0.json'])['salt']!=tc['salt']
    assert hashlib.sha256(archive(a)).digest()==hashlib.sha256(archive(b)).digest()
    secret=bytes.fromhex(Path(os.environ['A0_BUILD_SECRET_FILE']).read_text().strip())
    assert ta['salt']==hmac.new(secret,x.payload_digest(a),hashlib.sha256).hexdigest()
    names=set(x.WORDS)|set(x._NAMES)
    assert not ({hashlib.sha256(n.encode()).hexdigest() for n in names}&(set(ta['tokens'])|set(ta['aliases'])))
    assert all(secret not in v and secret.hex().encode() not in v for v in a.values())

def test_missing_secret_refuses_pack(tmp_path,monkeypatch):
    x=module();monkeypatch.setenv('A0_BUILD_SECRET_FILE',str(tmp_path/'absent'))
    with pytest.raises(ValueError,match='secret unavailable'):x.pack({'a':b'b'})

@pytest.mark.parametrize('salt',[None,'','bad'])
def test_install_refuses_unsalted_or_malformed_table(tmp_path,salt):
    table={'tokens':{},'aliases':{}}
    if salt is not None:table['salt']=salt
    (tmp_path/'x0.json').write_text(json.dumps(table))
    code="import runpy;v=runpy.run_path("+repr(str(SOURCE))+");v['install']("+repr(str(tmp_path))+")"
    r=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True)
    assert r.returncode!=0 and 'salted table required' in r.stderr

def test_salted_alias_learn_component_and_child(tmp_path):
    x=module();x.media_alias('vsi/clip.mp4','v/clip.mp4')
    raw=b"from pathlib import Path\ndef run(): return Path('vsi/clip.mp4').read_bytes()\n"
    files,_=x.pack({'student_pilot/__init__.py':raw,'v/clip.mp4':b'fixture', 'xnames.py':SOURCE.read_bytes()})
    for n,v in files.items():
        p=tmp_path/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
    code="""import xnames as X,hashlib,json,subprocess,sys
X.install('.')
import student_pilot
assert student_pilot.run()==b'fixture'
assert X._key('student_pilot')==hashlib.sha256(X._SALT+b'student_pilot').hexdigest()
token=X.component('revsi_new')
assert X._TABLE[X._key('revsi_new')]==token
X.media_alias('revsi/next.mp4','v/clip.mp4')
subprocess.run([sys.executable,'-B','-c',"from pathlib import Path;import student_pilot;assert student_pilot.run()==b'fixture';assert Path('revsi/next.mp4').read_bytes()==b'fixture'"],check=True)
"""
    r=subprocess.run([sys.executable,'-B','-c',code],cwd=tmp_path,capture_output=True,text=True)
    assert r.returncode==0,r.stderr
