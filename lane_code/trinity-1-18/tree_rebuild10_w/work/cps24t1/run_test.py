import os,sys,json,hashlib,base64,resource,subprocess,time,struct,tarfile
from pathlib import Path
T=Path(__file__).resolve().parent
KIT=T/'kit'
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
NROOT='/project/community/jjyeung/okh7/x_22c714e1'
resource.setrlimit(resource.RLIMIT_AS,(7*1024**3,7*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
records=[]
def record(v):
    records.append(v)
    (T/'run_records.json').write_text(json.dumps(records,indent=2)+'\n')
def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True)+'\n')
def textfile(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for d in ('bin','project','tmp','cases','traces'):
    (T/d).mkdir(exist_ok=True)
textfile(T/'bin/python3', '#!/bin/bash\nexec '+PY+' -I -s -B "$@"\n')
(T/'bin/python3').chmod(0o755)
# x86_64 classic BPF: refuse sockets and deletion calls after bwrap setup.
instructions=[(0x20,0,0,0)]
for nr in (41,42,87,84,263):
    instructions.extend([(0x15,0,1,nr),(0x06,0,0,0x00050000|1)])
instructions.append((0x06,0,0,0x7fff0000))
(T/'seccomp.bpf').write_bytes(b''.join(struct.pack('HBBI',*i) for i in instructions))
shell="""set -eu
umask 077
ROOT="$TEST_KIT"
N="$TEST_ROOT"
export ROOT N
exec 9>"$N/shell.xtrace"
BASH_XTRACEFD=9
PS4='+ pid=$BASHPID line=$LINENO '
set -x
source "$ROOT/b/pc.sh"
# These PIDs belong only to this disposable test.
printf '%s %s\\n' "$TK_COPY_PID" "$TK_LOG_PID" > "$N/copier_pids"
sleep 0.2
case "$TEST_VARIANT" in
 EXIT) exit "$TEST_STATUS" ;;
 TERM) kill -TERM "$$" ;;
 USR1) kill -USR1 "$$" ;;
 TERM_WORKER|USR1_WORKER)
   (sleep 0.3; exit "$TEST_STATUS") &
   TK_WORK_PID=$!
   if [[ "$TEST_VARIANT" == TERM_WORKER ]]; then kill -TERM "$$"; else kill -USR1 "$$"; fi ;;
esac
exit 99
"""
textfile(T/'trap_driver.sh',shell)
def setup(name,job):
    root=T/'cases'/name/'Q_ROOT'
    train=root/'p/q/r'
    export=train/'m100'
    checkpoint=train/'checkpoint_100'
    export.mkdir(parents=True);checkpoint.mkdir(parents=True)
    textfile(export/'payload.txt','synthetic copier data only\n'*100)
    put(export/'config.json',{'synthetic':True,'step':100})
    put(export/'artifact.json',{'step':100,'files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in export.iterdir() if p.is_file()},'synthetic':True})
    textfile(checkpoint/'state.txt','synthetic checkpoint marker payload\n'*20)
    put(checkpoint/'complete.json',{'step':100,'synthetic':True,'files':['state.txt']})
    textfile(train/'metrics_0.jsonl','{"step":100,"loss":1.25}\n')
    put(train/'attempt_0.json',{'attempt':0,'step':100,'synthetic':True})
    put(train/'run_0.json',{'step':100,'status':'stopped','synthetic':True})
    for name2 in ('q.log','rooms.log','h.log','rv.log','t.log','dr/q.log'):
        textfile(root/name2,'synthetic log at step 100\n')
    textfile(root/'h/o'/f'{job}.steps','100\n')
    textfile(root/f'{job}.steps','100\n')
    for name2 in ('p/q/RESULT.json','p/q/host.json','p/q/f.json','p/r0.json','dr/p/r0.json','rooms.json','routing_selection.json','p/q/selection/receipt.json','p/q/selection/materialization.json'):
        put(root/name2,{'step':100,'synthetic':True})
    return root
def command(label,root,job,args,extra=None):
    with (T/'seccomp.bpf').open('rb') as sec:
        env={'PATH':str(T/'bin')+':/usr/bin:/bin','SLURM_JOB_ID':job,'TEST_KIT':str(KIT),'TEST_ROOT':str(root),'TMPDIR':str(T/'tmp'),'XDG_CACHE_HOME':str(T/'tmp/cache'),'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}
        env.update(extra or {})
        cmd=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(T),str(T),'--ro-bind',str(KIT),str(KIT),'--tmpfs','/project','--bind',str(T/'project'),NROOT,'--bind',str(T/'tmp'),'/tmp','--unshare-user','--unshare-pid','--proc','/proc','--die-with-parent','--clearenv','--chdir',str(root),'--seccomp',str(sec.fileno())]
        for k,v in env.items():cmd+=['--setenv',k,v]
        cmd+=['--']+args
        traced=['/usr/bin/strace','-f','-qq','-s','256','-yy','-e','trace=%file,%process,%network,write,pwrite64,writev,ftruncate','-o',str(T/'traces'/f'{label}.strace')]+cmd
        start=time.monotonic()
        result=subprocess.run(traced,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,pass_fds=(sec.fileno(),))
    textfile(T/'traces'/f'{label}.stdout',result.stdout)
    textfile(T/'traces'/f'{label}.stderr',result.stderr)
    value={'label':label,'command_argv':traced,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'stdout':result.stdout,'stderr':result.stderr,'environment':env,'nice':os.getpriority(os.PRIO_PROCESS,0),'affinity':sorted(os.sched_getaffinity(0))}
    record(value);print(json.dumps({'label':label,'exit_code':result.returncode,'seconds':value['seconds']}),flush=True)
    return value
def checks(root,job):
    target=T/'project/o'/job
    live=target/'live'
    expected=['markers.json','metrics_0.jsonl','attempt_0.json','run_0.json',job+'.steps','q.log','h.log','t.log','rooms.log','copy.json','gcs_m100.json','ckstop.json']
    values={'expected_live_files':{n:(live/n).is_file() for n in expected},'export_marker':json.loads((live/'gcs_m100.json').read_text()) if (live/'gcs_m100.json').exists() else None,'checkpoint_marker':json.loads((live/'ckstop.json').read_text()) if (live/'ckstop.json').exists() else None,'upload_done':(live/'gcs_m100.done').exists(),'archive_at_trap_exit':(target/'o.tar').exists(),'result_at_trap_exit':(target/'RESULT.json').exists(),'r1':json.loads((target/'r1.json').read_text()) if (target/'r1.json').exists() else None}
    values['live_copies_match']=all((live/n).read_bytes()==(root/n).read_bytes() for n in ('q.log','h.log','t.log','rooms.log',job+'.steps') if (live/n).exists())
    ck=T/'project/n_ck'/job
    values['checkpoint_done']=(ck/'complete.json').is_file()
    values['checkpoint_tar_members']=tarfile.open(ck/'checkpoint_100.tar').getnames() if (ck/'checkpoint_100.tar').exists() else []
    values['export_archive_members']=[{'name':p.name,'members':tarfile.open(p).getnames()} for p in (root/'live_spool').glob('*.tar')]
    return values
cases=[]
for i,(name,variant,status,expected) in enumerate([('exit','EXIT',0,0),('term','TERM',0,143),('usr1','USR1',0,138),('term_worker','TERM_WORKER',7,7),('usr1_worker','USR1_WORKER',0,0)],start=2401):
    job=str(i);root=setup(name,job)
    r=command(name,root,job,['/bin/bash',str(T/'trap_driver.sh')],{'TEST_VARIANT':variant,'TEST_STATUS':str(status)})
    c=checks(root,job)
    cases.append({'name':name,'job':job,'root':str(root),'exit_code':r['exit_code'],'expected_exit_code':expected,'checks':c})
    (T/'case_results.json').write_text(json.dumps(cases,indent=2)+'\n')
# o.py is a distinct worker epilogue, never a child of tk_live_finish.
root=Path(cases[0]['root']);job=cases[0]['job']
command('o_standalone',root,job,[PY,'-I','-s','-B',str(KIT/'b/o.py'),str(root),'0','0'])
command('ep_after_o',root,job,[PY,'-I','-s','-B',str(KIT/'b/ep.py'),str(KIT),str(root),job,'0'])
# A user-named synthetic endpoint file exercises the sessions-unusable path
# without opening or creating any file named sess.json.
sessions=T/'project/n_s/fake-endpoint.json'
put(sessions,{'q9/22c714e1/469ddece_m100.tar.part00-of-04':'https://127.0.0.1:1/refused'})
sessions.parent.chmod(0o700);sessions.chmod(0o644)
command('fake_endpoint_bad_mode',root,job,[PY,'-I','-s','-B',str(KIT/'b/pc.py'),str(KIT),str(root),job,'--final','--sessions',NROOT+'/n_s/fake-endpoint.json'])
record({'label':'fake_endpoint_marker','value':json.loads((T/'project/o'/job/'live/gcs_m100.json').read_text()),'note':'Mode 0644 is deliberately unusable; endpoint is never opened and no sess.json is read or copied.'})
print('COMPLETE',flush=True)
