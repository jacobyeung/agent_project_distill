from pathlib import Path
import contextlib,importlib.util,io,json,os,stat,sys,subprocess
from unittest.mock import patch
from types import SimpleNamespace
L=Path(__file__).resolve().parents[2];D=L/'work/build24g'
sys.path.insert(0,str(D))
from live_tests import WRITER

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def case(C,version,label,mutation=None,override=False,envhome=False):
    root=D/'copier_tests'/version/label;root.mkdir(parents=True)
    kit=root/'kit';(kit/'k').mkdir(parents=True);(kit/'b').mkdir()
    node=root/'node';node.mkdir();project=root/'project';project.mkdir()
    sd=project/'n_s';sd.mkdir(mode=0o700);sessions=sd/'sess.json'
    # The synthetic value is generated in memory and never written to evidence.
    token='https://'+'example.invalid/'+'session-'+os.urandom(16).hex()
    values={'q9/test/m100.tar.part00-of-04':token}
    sessions.write_text(json.dumps(values));sessions.chmod(0o600)
    C.put(kit/'k/p.json',dict(n_root=str(project)))
    C.put(kit/'k/n.json',dict(output='/run/469ddece'))
    C.put(kit/'k/y.json',dict(objects={'m100':'q9/test/m100.tar'}))
    writer=kit/'b/gc.py'
    writer.write_text(WRITER+"\nprint(next(iter(__import__('json').loads(Path(s).read_text()).values())))\n")
    (kit/'b/pc.py').write_bytes(Path(C.__file__).read_bytes())
    target=root/'live_target';target.mkdir()
    kw=dict(target=target)
    if override:
        alternate=root/'alternate';alternate.mkdir(mode=0o700)
        sessions.rename(alternate/'chosen.json');sessions=alternate/'chosen.json';sd=alternate
        kw['sessions']=sessions
    if mutation=='file mode':sessions.chmod(0o644)
    elif mutation=='directory mode':sd.chmod(0o755)
    elif mutation=='file missing':sessions.rename(sd/'saved.json')
    elif mutation=='file symlink':
        sessions.rename(sd/'saved.json');sessions.symlink_to(sd/'saved.json')
    elif mutation=='file not regular':sessions.rename(sd/'saved.json');sessions.mkdir()
    elif mutation=='not an object':sessions.write_text(json.dumps([token]))
    elif mutation=='invalid JSON':sessions.write_text('{'+token)
    elif mutation=='invalid mapping':sessions.write_text(json.dumps({'part':17}))
    elif mutation=='invalid URL':sessions.write_text(json.dumps({'part':'not a URL'}))
    output=io.StringIO()
    with patch.dict(os.environ,{},clear=True):
        if envhome:os.environ['TK_KIT_HOME']=str(root/'unused')
        c=C.Copier(kit,node,'41',**kw)
        export=c.train/'m100';export.mkdir(parents=True)
        (export/'w.bin').write_bytes(b'fixture weights')
        C.put(export/'artifact.json',dict(step=100))
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            if mutation=='directory owner':
                get=C.os.getuid
                with patch.object(C.os,'getuid',return_value=get()+1):c.exports()
            else:c.exports()
    done=(c.live/'gcs_m100.done').exists()
    status=C.read(c.live/'gcs_m100.json')['status'] if (c.live/'gcs_m100.json').exists() else None
    expected=('export not uploaded: sessions unusable ('+mutation+')') if mutation else None
    passed=(not done and status==expected) if mutation else done
    assert token not in output.getvalue()
    for p in c.live.rglob('*'):
        if p.is_file():assert token.encode() not in p.read_bytes()
    objects=list((c.spool/'private/objects').glob('*'))
    if mutation:assert not objects
    if done:
        private=c.spool/'private/sess.json'
        assert stat.S_IMODE(private.stat().st_mode)==0o600
        assert stat.S_IMODE(private.parent.stat().st_mode)==0o700
        assert json.loads(private.read_text())==values
        assert len(objects)==4
        stamp=(c.live/'gcs_m100.done').stat().st_mtime_ns;c.exports()
        assert (c.live/'gcs_m100.done').stat().st_mtime_ns==stamp
    # Check every runtime file except the required source/private capability files.
    for p in root.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        if p.parent==sd or p==c.spool/'private/sess.json':continue
        assert token.encode() not in p.read_bytes()
    return dict(case=label,expected_pass=passed,done=done,status=status,uploaded_parts=len(objects),session_value_leaks=0)

old=load(L/'attic/build24g/work/build24/kits/n/b/pc.py','before')
new=load(L/'work/build24/kits/n/b/pc.py','after')
records={}
cases=[('default',None),('mode','file mode'),('symlink','file symlink'),('missing','file missing'),('object','not an object')]
records['before']=[case(old,'before',label,mutation) for label,mutation in cases]
assert all(not r['expected_pass'] for r in records['before'])
records['after']=[case(new,'after',label,mutation) for label,mutation in cases]
for label,mutation in [('dir_mode','directory mode'),('dir_owner','directory owner'),('regular','file not regular'),('json','invalid JSON'),('mapping','invalid mapping'),('url','invalid URL')]:
    records['after'].append(case(new,'after',label,mutation))
records['after'].append(case(new,'after','explicit',override=True))
records['after'].append(case(new,'after','env_ignored',envhome=True))
assert all(r['expected_pass'] for r in records['after'])
# Exercise the public CLI in a fresh stand-in, including its explicit filename option.
root=D/'copier_tests/after/explicit';kit=root/'kit';node=root/'cli_node';node.mkdir()
export=node/'r/m100';export.mkdir(parents=True);(export/'w.bin').write_bytes(b'cli weights')
new.put(export/'artifact.json',dict(step=100,case='cli'))
result=subprocess.run([sys.executable,'-I','-s','-B',str(kit/'b/pc.py'),str(kit),str(node),'42','--sessions',str(root/'alternate/chosen.json')],capture_output=True)
assert result.returncode==0 and not result.stdout and not result.stderr
assert (root/'project/o/42/live/gcs_m100.done').is_file()
records['cli_explicit']='PASS';records['status']='PASS'
(D/'COPIER_TESTS.json').write_text(json.dumps(records,indent=2)+'\n')
print('Copier: 5 failing-before controls; 13 passing-after cases; explicit CLI PASS; no session-value leaks')
