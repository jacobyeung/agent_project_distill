import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
IN=Path('/scratch/jjyeung/orch_n30/b07_offread/in')
sys.path.insert(0,str(ROOT/'kit'))
import rebind as B


def cli(*args,ok=True):
    p=subprocess.run([PY,'-B',str(ROOT/'kit/rebind.py'),*map(str,args)],capture_output=True,text=True,
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'))
    if ok: assert p.returncode==0,p.stderr
    else: assert p.returncode!=0,p.stdout
    return p


def prep(tmp,bench='vsibench5130',export='step544',extra=()):
    d=tmp/'packet'
    cli('prepare','--benchmark',bench,'--export',export,'--token','a00123456','--destination',d,
        '--ledger',tmp/'official.jsonl',*extra)
    return d


@pytest.mark.parametrize('bench,key,count,headline',[
 ('vsibench5130','vsi',4008,'six_task_mean'),('revsi999t32','revsi',679,'five_category_mean')])
def test_accepted_report(tmp_path,bench,key,count,headline):
    d=prep(tmp_path,bench)
    binding=json.loads((d/'BINDING.json').read_text())
    assert binding['frames']['count']==32 and binding['frames']['layout']=='duplicate'
    changed=json.loads(json.dumps(binding));changed['frames']['count']=64
    with pytest.raises(ValueError,match='binding_sha256'):B.verify_binding(changed)
    cli('report','--destination',d,'--return-dir',IN/('ret_'+key),'--accepted-return')
    for arm in ('B2048','ON16k','B4096'):
        actual=json.loads((d/'reports'/f'{arm}.json').read_text())
        accepted=json.loads((IN/('ret_'+key)/'report'/f'{arm}.json').read_text())
        assert actual['items']==count
        if arm=='B2048':
            target=(68.77,[66.5,71.0]) if key=='vsi' else (64.94,[61.3,68.4])
            assert round(100*actual['headline']['score'],2)==target[0]
            assert [round(100*x,1) for x in actual['headline']['percentile_95']]==target[1]
        assert actual['headline']['score']==accepted[headline]['score']
        assert actual['headline']['percentile_95']==accepted[headline]['percentile_95']
        for g in accepted['groups']:
            assert actual['groups'][g]['score']==accepted['groups'][g]['score']
            assert actual['groups'][g]['percentile_95']==accepted['groups'][g]['percentile_95']
        assert (d/'reports'/f'{arm}.txt').read_text().splitlines()[0]==actual['first_line']
        assert actual['arm']=='primary'
        assert actual['not_read']==['object_abs_distance','room_size_estimation']
        assert actual['binding_sha256']==binding['binding_sha256']
        assert actual['frames']==binding['frames'] and actual['mode']=='production'


@pytest.mark.parametrize('bench,key', [('vsibench5130','vsi'),('revsi999t32','revsi')])
def test_payload_and_membership(tmp_path,bench,key):
    d=prep(tmp_path,bench)
    accepted=ROOT/'work/accepted_vsi' if key=='vsi' else IN/'kit_revsi'
    script="""import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/launcher')
import orchard_launcher as L
kw={'media_root':'/project/community/jjyeung/okh7/313db5a47f11ff0c/'} if sys.argv[3]=='revsi' else {}
L.prepare('a00123456',sys.argv[2],**kw)
"""
    p=subprocess.run([PY,'-B','-c',script,str(accepted),str(tmp_path/'accepted'),key],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    got=B.boot_files(d/'BATCH.sh'); old=B.boot_files(tmp_path/'accepted/BATCH.sh')
    # Path-only repacking changes tar bytes; accepted reader/scorer/item bytes stay exact.
    assert B.X.scan_members(got['bootstrap/payload.tar.gz'])>0
    assert b'logical_path(item.name)' in got['bootstrap/orchard_stage.py']
    payload=B.unpack(got['bootstrap/payload.tar.gz'])
    assert all('BINDING.json' not in n for n in payload)
    assert 'BINDING.json' not in str(got.keys())
    a=json.loads((tmp_path/'accepted/CONFIG.json').read_text());c=json.loads((d/'CONFIG.json').read_text())
    for name in ('spec','assets','release'):
        assert a[name]==c[name]
    for n,data in payload.items():
        if '/reader/' in n or '/cohort/' in n or '/inputs/' in n or '/parity/' in n:
            accepted_bytes=B.unpack(old['bootstrap/payload.tar.gz'])[n]
            if key=='vsi' and n.endswith('/cohort/MEDIA_MANIFEST.json'):
                strip=lambda value:[{k:v for k,v in row.items() if k not in ('bytes','status')} for row in json.loads(value)]
                assert strip(data)==strip(accepted_bytes)
                assert all(row['bytes']>0 for row in json.loads(data))
            else:assert data==accepted_bytes
    # Invoke the accepted production loader and its membership guard without a model.
    script="""import sys,json
from pathlib import Path
p=Path(sys.argv[1]);sys.path.insert(0,str(p/'reader'))
import official_adapter as A
if sys.argv[2]=='vsi':
 cfg={'datasets':[dict(benchmark='official5130',rows=dict(path=str(p/'cohort/meta_5130.jsonl'),sha256=A.ROWS_SHA),question_types=sorted(A.COUNTS))], 'roots':{'video_root':'/unused'},'mode':'production'}
 cohort=p/'cohort/COHORT_OFFICIAL6.jsonl'
else:
 cfg={'datasets':[A.dataset(p/'inputs/i1.json')],'roots':{'revsi_video_root':'/unused'},'mode':'production'}
 cohort=p/'cohort/c5.jsonl'
ts=A.membership(cfg); rows=A.load_rows(cohort)
assert {t['example_id'] for t in ts}=={str(r['id']) for r in rows}
assert not any(t['question_type'] in ('object_abs_distance','room_size_estimation') for t in ts)
print(json.dumps({'items':len(ts),'scenes':len({(r['dataset'],r['scene_name']) for r in rows})}))
"""
    p=subprocess.run([PY,'-B','-c',script,str(ROOT/'kit'/key),key],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert json.loads(p.stdout)==dict(items=4008 if key=='vsi' else 679,scenes=288 if key=='vsi' else 261)


def done_files(tmp,sha='a'*64,step=200):
    from offkit.bind import INIT_RULE_SHA
    done=tmp/f'm{step}.done';done.write_text(f'q8/8865619b/359fcc3c_m{step}.tar 10240 '+sha+'\n')
    sel=tmp/'selection.json';sel.write_text(json.dumps(dict(selected_sha256=sha,selected_step=step,
        init_rule_sha256=INIT_RULE_SHA,d0_ended=dict(reason='completed_step_1000',event='fixture:D0-ended'))))
    return done,sel


@pytest.mark.parametrize('case',['missing_selection','mismatch','second','malformed','spacing','lineage'])
def test_binding_refusals(tmp_path,case):
    done,sel=done_files(tmp_path)
    ledger=tmp_path/'ledger.jsonl'
    extra=['--init-selection',str(sel),'--ledger',str(ledger)]
    if case=='missing_selection':extra=[]
    if case=='mismatch':
        selection=json.loads(sel.read_text());selection['selected_sha256']='b'*64
        sel.write_text(json.dumps(selection))
    if case=='second':ledger.write_text(json.dumps({'export_kind':'done','export_sha256':'b'*64})+'\n')
    if case=='malformed':done.write_text('broken\n')
    if case=='spacing':done.write_text(done.read_text().replace(' 10240','\t10240'))
    if case=='lineage':done.write_text(done.read_text().replace('359fcc3c','11111111'))
    cli('prepare','--benchmark','vsibench5130','--export','done:'+str(done),'--token','a00123456',
        '--destination',tmp_path/'refused',*extra,ok=False)
    assert not (tmp_path/'refused').exists()


@pytest.mark.parametrize('bench,key',[('vsibench5130','vsi'),('revsi999t32','revsi')])
def test_done_prepare_and_tamper(tmp_path,bench,key):
    done,sel=done_files(tmp_path)
    d=prep(tmp_path,bench,'done:'+str(done),('--init-selection',str(sel),'--ledger',str(tmp_path/'l.jsonl')))
    c=json.loads((d/'CONFIG.json').read_text());assert c['spec']['step']==200
    assert c['x1']=='a'*64
    assert not (tmp_path/'l.jsonl').exists()
    assert (ROOT/'kit'/key/'launcher/export_stage.py').read_bytes()==(IN/'readk/kit/launcher/export_stage.py').read_bytes()
    b=json.loads((d/'BINDING.json').read_text());b['export']['sha256']='b'*64
    (d/'BINDING.json').write_text(json.dumps(b))
    cli('submit-command','--destination',d,ok=False)


def test_m100_refused_with_matching_selection(tmp_path):
    done,sel=done_files(tmp_path,step=100)
    p=cli('prepare','--benchmark','vsibench5130','--export','done:'+str(done),
        '--init-selection',sel,'--ledger',tmp_path/'ledger.jsonl','--token','a00123456',
        '--destination',tmp_path/'refused',ok=False)
    assert 'rule candidate' in p.stderr
    assert not (tmp_path/'refused').exists()


def test_launcher_independently_refuses_m100(monkeypatch,tmp_path):
    from types import SimpleNamespace as NS
    monkeypatch.setattr(B,'bind',lambda *a,**kw:dict(export=dict(kind='done',
        object='q8/8865619b/359fcc3c_m100.tar')))
    a=NS(token='a00123456',benchmark='vsibench5130',export='done:fixture',mode='production',
         init_selection='fixture',ledger=tmp_path/'ledger.jsonl')
    with pytest.raises(ValueError,match='unregistered lineage or step'):B.prepare(a)


def offkit_copy(tmp_path):
    source=Path(B.reports.__file__).parent
    target=tmp_path/'offkit';target.mkdir()
    for name in B.OFFKIT_MODULES:(target/name).write_bytes((source/name).read_bytes())
    return target


@pytest.mark.parametrize('name',B.OFFKIT_MODULES)
def test_mutated_offkit_refused_before_import(tmp_path,name):
    target=offkit_copy(tmp_path)
    # Executing the changed module would produce a distinct error.
    (target/name).write_text("raise RuntimeError('UNVERIFIED_MODULE_EXECUTED')\n"+(target/name).read_text())
    p=subprocess.run([PY,'-B','-c',
        'import sys;sys.path[:0]=sys.argv[1:];import rebind',str(tmp_path),str(ROOT/'kit')],
        capture_output=True,text=True)
    assert p.returncode!=0 and 'offkit content pin mismatch: '+name in p.stderr
    assert 'UNVERIFIED_MODULE_EXECUTED' not in p.stderr


@pytest.mark.parametrize('action',['prepare','submit-command','record-submission','fetch','report'])
def test_offkit_rechecked_before_each_action(tmp_path,action):
    target=offkit_copy(tmp_path)
    script="""import sys
from pathlib import Path
sys.path[:0]=sys.argv[1:3]
import rebind
p=Path(sys.argv[1])/'offkit/frames.py'
p.write_text(p.read_text()+'\\n# changed after import\\n')
sys.argv=['rebind',sys.argv[3],'--destination',sys.argv[1]+'/unused']
rebind.main()
"""
    p=subprocess.run([PY,'-B','-c',script,str(tmp_path),str(ROOT/'kit'),action],capture_output=True,text=True)
    assert p.returncode!=0 and 'offkit content pin mismatch: frames.py' in p.stderr
    assert not (tmp_path/'unused').exists()


def test_identical_offkit_copy_is_accepted(tmp_path):
    target=offkit_copy(tmp_path)
    p=subprocess.run([PY,'-B','-c',
        'import sys;sys.path[:0]=sys.argv[1:];import rebind;print(rebind.reports.__file__)',
        str(tmp_path),str(ROOT/'kit')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert str(target/'report.py') in p.stdout


def test_submission_is_only_ledger_writer(tmp_path):
    d=prep(tmp_path)
    ledger=tmp_path/'official.jsonl'
    assert not ledger.exists()
    (d/'SUBMIT.out').write_text('123456;cluster\n')
    cli('record-submission','--destination',d,'--ledger',ledger)
    assert len(ledger.read_text().splitlines())==1
    cli('record-submission','--destination',d,'--ledger',ledger,ok=False)
    assert len(ledger.read_text().splitlines())==1


def test_submit_shape(tmp_path):
    d=prep(tmp_path)
    command=cli('submit-command','--destination',d,'--ledger',tmp_path/'l').stdout
    for s in ('--gres=gpu:1','--cpus-per-task=16','--mem=200G','--partition=general','a15_cot_ap'):
        assert s in command
    assert re.search(r'--job-name=a15_cot_ap[0-9a-f]{16}',command)
    assert json.loads((d/'CONFIG.json').read_text())['job_name'] in command
    assert '#SBATCH' not in (d/'BATCH.sh').read_text()
    assert all(x not in command for x in ('vsibench','revsi','D0','BINDING'))


def test_gate_refuses_before_chain(tmp_path,monkeypatch):
    sys.path.insert(0,str(ROOT/'kit/vsi/launcher'))
    import gate
    c=dict(x0='a'*64,x1='b'*64,x2=0,spec={'package':str(ROOT/'kit/vsi'),'run':str(tmp_path/'run'),
        'interpreters':{'vllm':PY},'models':{'base':{'path':'/unused'}}})
    def run(argv,**kwargs):
        target=Path(argv[argv.index('--output')+1]);target.mkdir(parents=True)
        (target/'PARITY.json').write_text(json.dumps(dict(processor_checked=True,all_prompt_bytes_equal=False,prompt_pins_equal=True)))
        return subprocess.CompletedProcess(argv,0,b'',b'')
    monkeypatch.setattr(gate.subprocess,'run',run)
    with pytest.raises(ValueError,match='P9 failed'):gate.run(c,tmp_path)
    assert json.loads((tmp_path/'run/metadata/P9.json').read_text())['passed'] is False
    c['x2']=1
    with pytest.raises(ValueError,match='X1 admission'):
        gate.after(tmp_path,c,{'export':{'tar_sha256':'c'*64,'status':'complete','checker':{'status':'VERIFIED'}}})


def test_governed_transfer_registers_only_stopped_source(monkeypatch):
    calls=[]
    class Proc:
        def __init__(self,pid):
            self.pid=pid;self.stdout=io.BytesIO();self.code=None
        def poll(self):return self.code
        def wait(self,**kw):self.code=0;return 0
        def terminate(self):raise AssertionError('A completed fixture must not be stopped')
    processes=[Proc(101),Proc(102)]
    def popen(argv,**kw):
        calls.append(('popen',argv,kw))
        return processes[len([r for r in calls if r[0]=='popen'])-1]
    class P:
        def __init__(self,v):self.v=str(v)
        def __truediv__(self,n):return P(self.v+'/'+str(n))
        def __str__(self):return self.v
        def is_file(self):return True
        def exists(self):return any(r[0]=='register' for r in calls)
        def read_text(self):return '101 (python) T 1' if self.v.endswith('/stat') else 'ratelimit\n'
        def with_name(self,n):return P('/record/'+n)
        def rename(self,p):calls.append(('rename',str(p)))
    def register(argv,**kw):
        assert len([r for r in calls if r[0]=='popen'])==2
        assert '--allow-resume' in argv and '--rl-pid' in argv
        calls.append(('register',argv))
    monkeypatch.setattr(B,'Path',P)
    monkeypatch.setattr(B.subprocess,'Popen',popen)
    monkeypatch.setattr(B.subprocess,'run',register)
    B.governed_transfer(['approved-fixture-source'],io.BytesIO(),io.BytesIO(),123,'a00123456')
    assert calls[-1][0]=='rename'
    assert 'SIGSTOP' in calls[0][1][3]
