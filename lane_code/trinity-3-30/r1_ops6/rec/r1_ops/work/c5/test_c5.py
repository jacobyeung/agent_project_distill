"""Local, CPU-only scheduler and input fixtures; no external commands."""
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile

W = Path(__file__).resolve().parent
D = W.parent/'drv_c1'
E = W.parent/'ex_08f3a7b2'
S = W.parent/'snap_08f3a7b2'
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
assert sys.executable == PY
os.umask(0o077)
T = Path(tempfile.mkdtemp(prefix='tests_', dir=W))
BIN = T/'bin'; BIN.mkdir()
(BIN/'python3').symlink_to(PY)
def exe(name, text):
    p = BIN/name; p.write_text('#!/bin/bash\n'+text+'\n'); p.chmod(0o700)
exe('squeue', '[[ ${QUEUE_FAIL:-0} == 0 ]] || exit 9\nprintf "%s" "$QUEUE"')
exe('sacct', '[[ ${HISTORY_FAIL:-0} == 0 ]] || exit 9\nif [[ " $* " == *" -j 171377 "* ]]; then printf "%s" "$DONOR"; else printf "%s" "$HISTORY"; fi')
exe('sbatch', 'printf "%s\\n" "$*" >> "$CALLED"\n[[ ${SBATCH_FAIL:-0} == 0 ]] || exit 8\nprintf "%s\\n" "$ANSWER"')
sha = lambda raw: hashlib.sha256(raw).hexdigest()
dump = lambda p, obj: p.write_text(json.dumps(obj, sort_keys=True))
PIN = '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd'
IDENTITY = '6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74'
RESULTS = []

def passed(name):
    RESULTS.append(name); print('PASS', name, flush=True)

def fixture(label):
    root = T/label; root.mkdir(mode=0o700)
    b=root/'i_7f1589c1';k=root/'x_7f1589c1'
    for p in (b,k,k/'o',k/'b',k/'k',b/'d0'):
        p.mkdir(mode=0o700)
    # Small certified runtime fixture exercises all driver-side predicates.
    ready=D/'tests_c2_cszuhpu9/derived_ready'
    auth=json.loads((ready/'k/4.json').read_text())
    dump(k/'k/4.json',auth)
    (k/'b/a.py').write_text('def main(k):\n return None\n')
    names=['k/4.json','b/a.py']
    (k/'SHA256SUMS.txt').write_text(''.join(sha((k/n).read_bytes())+'  '+n+'\n' for n in names))
    cert=dict(status='CLEAN',hits=0,reviewer='fixture',config_identity=IDENTITY,
              operator_archive_sha256=PIN,scan_record_sha256='1'*64,
              exemption_sha256='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720',
              manifest_sha256=sha((k/'SHA256SUMS.txt').read_bytes()),external=[])
    dump(k/'ANON_OK.json',cert)
    # Archive verification uses a tiny substitute only in relocated test scripts.
    (b/'p.tar').write_bytes(b'local packet fixture')
    (b/'sums.txt').write_text(sha(b'local packet fixture')+'  p.tar\n')
    (b/'BINDING.json').write_text('{}')
    (b/'p.py').write_text('import json,sys\nfrom pathlib import Path\np=Path(sys.argv[sys.argv.index("--out")+1])\nwith p.open("x") as f:json.dump(dict(partition="general",fixture=True),f)\n')
    (b/'d0/rc').write_text('0\n');dump(b/'compare.json',dict(status='READY'))
    keys=['entry'+str(i) for i in range(20)]
    (b/'e.txt').write_text('\n'.join(keys)+'\n')
    dump(k/'sess.json',{v:'https://storage.googleapis.com/upload/'+v for v in keys})
    (k/'sess.json').chmod(0o600)
    old=root/'i_7f1589c1.f172180';old.mkdir()
    (old/'job.id').write_text('172180\n')
    for name in ('sbatch.out.a1_bootstrap','submission.started.a1_bootstrap','a.json.a1_bootstrap'):
        (old/name).write_text('' if name.startswith('sbatch') else '{}')
    receipt=dict(status='REHEARSAL_FAIL',rc=1,job='172467',rehearsal=True,
                 admission_executed=False,error='ValueError: Staged root unavailable',steps={'preflight':'FAIL'})
    dump(k/'o/172467.rehearsal.json',receipt)
    (b/'rehearsal.started').write_text('fixture\n')
    (b/'rehearsal.job.id').write_text('172467\n')
    (b/'rehearsal.sbatch.out').write_text('Submitted batch job 172467\n')
    dump(b/'rehearsal.json',dict(job='172467',kind='REHEARSAL',partition='general',proof=False))
    dump(b/'a4.json',dict(partition='general',fixture=True))
    waiver=root/'event.txt';waiver.write_text('Operator permits this held CPU proof with the rehearsal waived.\n')
    env=dict(os.environ,PATH=str(BIN)+':/usr/bin:/bin',QUEUE='',USER='fixture',
             HISTORY='172180|a15_cot_ap05b8ac69|FAILED|1:0\n',DONOR='171377|a15_cot_ap673bc60f|COMPLETED|0:0\n',
             CALLED=str(root/'called'),ANSWER='172999;fixture')
    return root,b,k,waiver,env

def relocated(name,root):
    text=(W/name).read_text().replace('/project/community/jjyeung/okh7',str(root))
    text=text.replace('/usr/bin/python3',PY)
    # Change the expected archive pin only; all other driver predicates execute.
    text=text.replace(PIN,sha(b'local packet fixture'))
    # Certificate fixture must match this expected pin too.
    k=root/'x_7f1589c1';cert=json.loads((k/'ANON_OK.json').read_text())
    cert['operator_archive_sha256']=sha(b'local packet fixture');dump(k/'ANON_OK.json',cert)
    p=root/name;p.write_text(text);return p

def run(script,args,env):
    r=subprocess.run(['/bin/bash',str(script),*args],env=env,capture_output=True,text=True,timeout=20)
    return r

proof_success=None
for label in ('success','no_hold','wrong_sha','missing_event','linked_event','missing_receipt','bad_receipt',
              'bad_cert','bad_auth','bad_sessions','bad_compare','bad_history','queue_fail','queued',
              'top_shadow','uncertain','sbatch_fail','existing_marker'):
    root,b,k,event,env=fixture('proof_'+label)
    script=relocated('pr4.sh',root)
    args=['general','--hold','--waive-rehearsal',sha(event.read_bytes()),str(event)]
    if label=='no_hold':args.remove('--hold')
    if label=='wrong_sha':args[-2]='0'*64
    if label=='missing_event':args[-1]=str(root/'missing')
    if label=='linked_event':
        link=root/'link';link.symlink_to(event);args[-1]=str(link)
    if label=='missing_receipt':(k/'o/172467.rehearsal.json').rename(k/'o/retained.json')
    if label=='bad_receipt':dump(k/'o/172467.rehearsal.json',dict(status='REHEARSAL_OK',rc=0,job='172467'))
    if label=='bad_cert':
        v=json.loads((k/'ANON_OK.json').read_text());v['hits']=1;dump(k/'ANON_OK.json',v)
    if label=='bad_auth':(k/'k/4.json').write_text('{}')
    if label=='bad_sessions':dump(k/'sess.json',{})
    if label=='bad_compare':dump(b/'compare.json',dict(status='BLOCKED'))
    if label=='bad_history':env['HISTORY']+='172111|a15_cot_ap05b8ac69|FAILED|1:0\n'
    if label=='queue_fail':env['QUEUE_FAIL']='1'
    if label=='queued':env['QUEUE']='172222|a15_cot_ap05b8ac69|general|PENDING\n'
    if label=='top_shadow':(k/'json.py').write_text('')
    if label=='uncertain':env['ANSWER']='uncertain'
    if label=='sbatch_fail':env['SBATCH_FAIL']='1'
    if label=='existing_marker':(k/'o/pr4.waiver.json').write_text('{}')
    r=run(script,args,env)
    assert (r.returncode==0)==(label=='success'),(label,r.stdout,r.stderr)
    called=root/'called'
    assert called.exists()==(label in ('success','uncertain','sbatch_fail')),(label,r.stdout,r.stderr)
    if called.exists():
        command=called.read_text();assert '--hold' in command and '-p general' in command
        assert len(command.strip().splitlines())==1
        again=run(script,args,env);assert again.returncode and called.read_text()==command
        assert json.loads((k/'o/pr4.waiver.json').read_text())['failing_receipt_sha256']==sha((k/'o/172467.rehearsal.json').read_bytes())
    if label=='success':
        assert (b/'job.id').read_text().strip()=='172999'
        ledger=json.loads((k/'o/172999.waiver.json').read_text())
        assert ledger['held'] is True and ledger['waiver_sha256']==sha(event.read_bytes())
        proof_success=(root,b,k,env)
    passed('pr4 '+label)

for label in ('success','stale_authority','malformed_authority','absent_authority','collision','linked_collision',
              'wrong_id','bad_receipt','top_shadow','queued','queue_fail','uncertain','sbatch_fail','proof_exists'):
    root,b,k,event,env=fixture('rehearsal_'+label)
    script=relocated('rh2.sh',root);env['ANSWER']='Submitted batch job 172998'
    original=(b/'a4.json').read_bytes()
    if label=='stale_authority':dump(b/'a4.json',dict(partition='bootstrap'))
    if label=='malformed_authority':(b/'a4.json').write_text('{')
    if label=='absent_authority':(b/'a4.json').rename(b/'held_authority.json')
    if label=='collision':(b/'rehearsal.started.r172467').write_text('retained')
    if label=='linked_collision':(b/'rehearsal.started.r172467').symlink_to(root/'missing')
    if label=='wrong_id':(b/'rehearsal.job.id').write_text('172468\n')
    if label=='bad_receipt':dump(k/'o/172467.rehearsal.json',dict(status='PASS'))
    if label=='top_shadow':(k/'json.py').write_text('')
    if label=='queued':env['QUEUE']='172222|a15_cot_ap05b8ac6a|general|RUNNING\n'
    if label=='queue_fail':env['QUEUE_FAIL']='1'
    if label=='uncertain':env['ANSWER']='uncertain'
    if label=='sbatch_fail':env['SBATCH_FAIL']='1'
    if label=='proof_exists':(b/'submission.started').write_text('held')
    inode=(b/'rehearsal.started').stat().st_ino
    r=run(script,[],env)
    okay=label in ('success','stale_authority','malformed_authority','absent_authority')
    assert (r.returncode==0)==okay,(label,r.stdout,r.stderr)
    called=root/'called';assert called.exists()==(okay or label in ('uncertain','sbatch_fail'))
    assert not (b/'job.id').exists()
    if called.exists():
        assert (b/'rehearsal.started.r172467').stat().st_ino==inode
        command=called.read_text()
        for token in ('--account=mt01','--partition=general','--nodelist=orchard-community-0','--gres=gpu:0','--time=00:45:00','/o/rh2_08f3a7b2.sh'):
            assert token in command
        again=run(script,[],env);assert again.returncode and called.read_text()==command
    if okay:
        assert (b/'rehearsal.job.id').read_text().strip()=='172998'
        assert json.loads((b/'a4.json').read_text())==dict(partition='general',fixture=True)
    if label=='success':assert (b/'a4.json').read_bytes()==original
    if label in ('stale_authority','malformed_authority'):assert (b/'a4.json.r172467').exists()
    passed('rh2 '+label)

# Verify the existing canary wrapper consumes the actual pr4 marker layout.
root,b,k,env=proof_success
for name in ('jb.sh','s.sh','ids.json'):
    (b/name).write_bytes((E/name).read_bytes())
(b/'sums.txt').write_text(''.join(sha((b/n).read_bytes())+'  '+n+'\n' for n in ('jb.sh','s.sh','ids.json')))
donor=root/'r/673bc60f';donor.mkdir(parents=True)
dump(donor/'A.json',dict(verified=True,step=200))
env.update(QUEUE='172999|a15_cot_ap05b8ac69|general|PENDING|JobHeldUser\n',
           HISTORY='172180|a15_cot_ap05b8ac69|FAILED|1:0\n172999|a15_cot_ap05b8ac69|PENDING|0:0\n')
exe('bash', '''[[ "$1" == s.sh ]] || exit 9
python3 -I -B - "$PROOF_JOB" <<'P'
import json,os,sys
from pathlib import Path
job=sys.argv[1];b=Path.cwd();k=b.parent/'x_7f1589c1'
with (k/'o'/(job+'.canary.json')).open('x') as f:json.dump(dict(canary=True,proof_job=job,admission_job='172180',submission='GATE_ACCEPTED'),f)
P
printf 'Submitted batch job 173000\\n' ''')
body=(D/'go_submit_canary_08f3a7b2.sh').read_text().replace('/project/community/jjyeung/okh7',str(root))
body=body.replace(PIN,sha(b'local packet fixture'))
body=body.replace('1d2270924ef7a7397d8fcf9ecd61811b8bfce954929acb5288d4119a4f5e97ae',sha((b/'sums.txt').read_bytes()))
script=root/'canary.sh';script.write_text(body)
r=run(script,['172999','31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89'],env)
assert r.returncode==0,(r.stdout,r.stderr)
assert (b/'training.job.id').read_text().strip()=='173000'
passed('canary wrapper accepts pr4 held proof markers (sealed gate stubbed)')

# The complete retained guard block must be byte-identical to pr1.
old=(D/'pr1.sh').read_text();new=(W/'pr4.sh').read_text()
for start,end in [("python3 -I -B - <<'HISTORY'",'HISTORY\n'),('def fields():',"rjid=b/'rehearsal.job.id'"),
                  ("assert (b/'d0/rc')","print('PASS sealed kit, independent scan, evidence, and 20 private sessions')")]:
    a=old.index(start);z=old.index(end,a)+len(end)
    block=old[a:z]
    if start=='def fields():':block=block[:block.index("rjid=")]
    assert block.replace('.split(', '.rsplit(') in new,start
for line in old.splitlines():
    if line.startswith('TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch'):
        assert line in new
passed('all retained pr1 guards identical apart from neutral tokenizer spelling')

# Verify sealed p.py source bytes, and the child-entry acceptance conditions.
sealed=(E/'p_05b8ac69.sh').read_text()
import base64,zlib
raw=zlib.decompress(base64.b64decode(re.search("b64decode\\('([^']+)'",sealed)[1]))
assert sha(raw)=='90f968228b4130f5d65f33e3fce7604a582f8c80fd7b5bd56fd070625c647e47'
scope={};exec(compile(raw,'sealed-p.py','exec'),scope)
assert raw==(S/'out/proof/p.py').read_bytes()
previous=os.environ.copy()
os.environ.update(SLURM_JOB_PARTITION='general',CUDA_VISIBLE_DEVICES='',SLURM_GPUS_ON_NODE='0')
assert scope['proof_allocation'](dict(partition='general',allowed_partitions=['general']))['partition']=='general'
os.environ.clear();os.environ.update(previous)
passed('sealed source SHA and CPU child allocation check')

dump(T/'results.json',dict(status='PASS',checks=RESULTS))
print('ARTIFACTS',T)
