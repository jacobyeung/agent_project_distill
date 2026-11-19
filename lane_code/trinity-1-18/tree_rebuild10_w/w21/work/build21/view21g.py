"""Execute the generated tk_bwrap function with node-local stand-ins."""
from pathlib import Path
import base64,datetime,hashlib,json,os,shlex,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g';K=B/'kits/q';R=D/'proofs/view'
R.mkdir(parents=True,exist_ok=True);node=R/'node';dest=R/'dest'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
spec=J.load(K/'k/p.json');ns=spec['namespace']
as_real='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
al_real=as_real.replace('/scratch/','/lustre/')
p_real='/project/community/jjyeung/c7d31ddd'
v=dict(Q_ROOT=str(node),Q_NS=ns,Q_KIT=str(K),S=str(node/'s'),U=str(node/'s/aws/u'),NX=str(node/'x'),NR=str(node/'rp'),
       AS=str(dest/as_real[1:]),AL=str(dest/al_real[1:]),P=str(dest/p_real[1:]),EPOCHS='/home/jjyeung/6d00e578',
       TK_JOBDIR=str(node/'j'),K='8865619b',RR='runs/aws128p_20261025')
v['X']=v['AS']+'/ap/'+v['K']
# Only AS, AL and P receive a host prefix: their production destinations were
# accepted before Orchard's final Q_NS failure. We cannot inspect that host here.
for p in (node/'s/aws/u/ap/8865619b/u',node/'x/runs',node/'x/u',node/'x/data2root',node/'x/models',node/'rp',node/'j',
          node/'s/c7d31ddd/data2root',node/'s/c7d31ddd/runs/aws128p_20261025/models',node/'s/epochs',
          Path(v['AS']),Path(v['AL']),Path(v['P'])):
    p.mkdir(parents=True,exist_ok=True)
for label,path in [('root',node),('job',node/'j'),('x',node/'x'),('runs',node/'rp'),('u',node/'s/aws/u/ap/8865619b/u')]:
    (path/'marker').write_text(label)
def function(kit):
    shell=base64.b64decode(J.load_raw(kit/'k/j.json')['payload']).decode()
    return shell[shell.index('tk_bwrap() {'):shell.index('\ntk_env() {')]
def arguments(label,kit):
    script=R/(label+'.sh');target=R/(label+'.json')
    source='set -euo pipefail\n'+''.join(k+'='+shlex.quote(x)+'\n' for k,x in v.items())
    source+='tk_current() { printf "%s %s\\n" /usr/bin/bwrap '+J.sha(Path('/usr/bin/bwrap'))+'; }\n'
    source+='sha_is() { [[ "$(sha256sum < "$1" | cut -d\' \' -f1)" == "$2" ]]; }\n'
    source+=function(kit)+'\ntk_bwrap\nBW+=(--bind "$Q_ROOT" "$Q_NS")\n'
    source+=shlex.quote(sys.executable)+' -I -s -B '+shlex.quote(str(K/'b/w.py'))+' '+shlex.quote(str(target))+' "${BW[@]}"\n'
    script.write_text(source)
    subprocess.run(['/bin/bash',str(script)],check=True)
    return json.loads(target.read_text())
old=arguments('before',L/'attic/build21g/q');new=arguments('after',K)
records=[]
def run(label,args):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    record=dict(stage=label,args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    records.append(record);print(json.dumps(record),flush=True)
    return record
before=run('full_view_before',old+['/usr/bin/true'])
after=run('full_view_after',new+['/usr/bin/true'])
assert before['returncode'] and "Can't mkdir /tmp/q_22c714e1: Read-only file system" in before['stderr']
assert after['returncode']==0
probe=R/'visible.py'
probe.write_text('from pathlib import Path\nimport json,sys\nexpected=json.loads(sys.argv[1])\nfor path,value in expected.items():\n assert Path(path).read_text()==value,path\nprint("All bound markers visible")\n')
markers={str(node/'marker'):'root',ns+'/marker':'root',str(node/'j/marker'):'job',v['X']+'/marker':'x',v['X']+'/runs/marker':'runs',v['X']+'/u/marker':'u'}
visible=run('bind_visibility',new+[sys.executable,'-I','-s','-B',str(probe),json.dumps(markers)])
assert visible['returncode']==0
# The production entry order stops at the real GPU guard. Run the independent
# CPU-capable q entry as an additional diagnostic, without altering that guard.
guard=run('real_gpu_guard',new+[sys.executable,'-s','-B',str(K/'b/g.py')])
assert guard['returncode'] and 'E42' in guard['stderr']
J.write(node/'r.json',dict(staged_pins=[]))
entry=run('real_q_entry_missing_inputs',new+[sys.executable,'-s','-B',str(K/'b/a.py'),'q',ns+'/p',ns+'/r.json'])
result_path=node/'p/q/RESULT.json'
result=J.load(result_path) if result_path.exists() else None
J.write(D/'VIEW.json',dict(host=os.uname().nodename,GO=False,variables=v,
    destination_prefix=str(dest),production_destinations=dict(AS=as_real,AL=al_real,P=p_real),
    source='Exact tk_bwrap function from each decoded kit; same top-level ro binds, private home, UID/GID and namespace bind.',
    stand_ins=['Empty staged source directories and content markers; AS/AL/P destinations prefixed under L.',
               'Scratch Python 3.12 CPU environment replaces the absent staged CUDA environment.',
               'Empty staged_pins request locates the native input boundary; no production store or weights.'],
    runs=records,native_result=result))
assert result and result['refusal']=='ValueError:R1_PROOF_STAGED_PINS_REQUIRED'
assert entry['returncode']==1
