"""review_offnative3 refute tests. Run inside sbx.sh (b07_offread -> review copy) from builds/R."""
import base64,hashlib,io,json,os,re,secrets,subprocess,sys,tarfile
from pathlib import Path
import pytest
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
R=Path('/scratch/jjyeung/orch_n30/b07_offread/builds/R')
HERE=Path(__file__).parent
WORDS=None
import tempfile
_fx=Path(tempfile.mkdtemp(prefix='a',dir='/dev/shm/b07_n7'))/'secret';_fx.write_text('5a'*32);_fx.chmod(0o600)
os.environ['A0_BUILD_SECRET_FILE']=str(_fx)
def words():
    sys.path.insert(0,str(R/'kit'));import xnames;return xnames.WORDS

def batch_root(tmp,bench,named):
    tok='a'+secrets.token_hex(6)[:11]
    d=tmp/'packet'
    p=subprocess.run([PY,'-B',str(R/'kit/rebind.py'),'prepare','--benchmark',bench,'--export','step544','--token',tok,
        '--destination',str(d),'--ledger',str(tmp/'l.jsonl')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    text=(d/'BATCH.sh').read_text()
    body=text.split("<<'P0'\n",1)[1].split('\nP0\n',1)[0]
    body=body.split('os.chdir(root)',1)[0]+'print(root)\n'
    parent='/tmp'
    if named:
        parent='/tmp/a_900000_'+secrets.token_hex(6)+'/orch_n30/b07_offread';os.makedirs(parent)
        assert "root=Path('/tmp')/" in body;body=body.replace("root=Path('/tmp')/","root=Path(%r)/"%parent)
    q=subprocess.run(['python3','-I','-s','-B','-'],input=body,capture_output=True,text=True,env=dict(os.environ,SLURM_JOB_ID='900000'))
    assert q.returncode==0,q.stderr
    root=q.stdout.strip()
    if not named:assert re.fullmatch(r'/tmp/a_900000_[0-9a-f]{12}',root),root
    return root,text

@pytest.mark.parametrize('named',[False,True])
@pytest.mark.parametrize('bench,key',[('vsibench5130','vsi'),('revsi999t32','revsi')])
def test_F1_F2_real_bwrap(tmp_path,bench,key,named):
    root,batch=batch_root(tmp_path,bench,named)
    r=subprocess.run([PY,'-B',str(HERE/'drv_bwrap.py'),str(R/'kit'/key/'launcher'),root,'x'],capture_output=True,text=True,
        env=dict(os.environ,USER=os.environ.get('USER','jjyeung'),SLURM_JOB_ID='900000'),timeout=300)
    assert r.returncode==0,r.stderr[-3000:]
    v=json.loads(r.stdout.strip().splitlines()[-1])
    (tmp_path/'V.json').write_text(json.dumps(v,indent=1))
    W=words()
    if named and v['rc']!=0:
        pytest.fail('named-ancestor root: real bwrap refuses the /proc fd spelling: '+v['log'].strip()[:200])
    assert v['rc']==0 and v['probe'] is not None,v['log']
    # F1: the interpreter vllm_isolated.sh execs lies under the AP bind destination and actually ran.
    target=re.search(r"exec (\S+) -I",v['vllm_sh'])[1].strip("'")
    assert target.startswith(v['ap']+'/'),(target,v['ap'])
    assert v['probe']['executable']==target or v['probe']['executable'].endswith('python3.12'),v['probe']
    assert v['probe']['media_ok'],v['probe']
    # F2: ps-visible argv of bwrap and of the in-namespace interpreter carry no forbidden word.
    for argv in (v['outer_cmdline'] or [],v['probe']['parent_cmdline'],v['probe']['self_cmdline'],[v['vllm_sh']]):
        bad=sorted({w for a in argv for w in W if w in a.lower()})
        assert not bad,(bad,[a for a in argv if any(w in a.lower() for w in bad)][:3])
    assert v['outer_cmdline'] and sum(a.endswith('.mp4') for a in v['outer_cmdline'])==2*v['media']
    ns=v['outer_cmdline'][:v['outer_cmdline'].index('--chdir')]
    assert not any('/project/' in a for a in ns)
    # Staging reads the registered aliases before namespace(): no build-time alias may redirect them.
    assert v['aliases_before_namespace']==0
