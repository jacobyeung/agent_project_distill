#!/bin/bash
#SBATCH -p advanced
#SBATCH --job-name=a15_cot_apb2edfac4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/tmp/q_22c714e1_%j.log
#SBATCH --error=/tmp/q_22c714e1_%j.err
set -euo pipefail
X="/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7/work/build27/x/s"
ROOT="$X/n"
# jn7 node hold: a failure before training keeps the job (and its node directory) for at most 180 min.
J7_HOLD_S=10800
J7_POLL_S=15
J7_SIG=''
hold() {
    local status=$1 now deadline reason='' pid rc job=${SLURM_JOB_ID:-0}
    # Never after a TERM/USR1 reached the work (stop path), never on success, never without the helper.
    [[ $status != 0 && -z ${J7_SIG:-} && -f ${N:-/nonexistent}/j7.py ]] || return 0
    # Training has started once rv.py installed the review pin (p/rv.json) or j.sh opened t.log for t.py.
    if [[ -e $N/t.log || -L $N/t.log || -e $N/p/rv.json || -L $N/p/rv.json ]]; then return 0; fi
    now=$(date +%s); deadline=$((now + J7_HOLD_S))
    # Leave Slurm's TERM warning (600 s) and the publication after it untouched.
    if [[ ${SLURM_JOB_END_TIME:-} =~ ^[0-9]+$ ]] && (( SLURM_JOB_END_TIME - 660 < deadline )); then deadline=$((SLURM_JOB_END_TIME - 660)); fi
    (( deadline > now + 60 )) || return 0
    # No published HOLD.txt, no hold: nobody would know the node is held.
    if ! timeout --signal=KILL 30s python3 -B -I -s "$N/j7.py" hold "$N" "$X" "$job" "$status" "${step:-setup}" "$now" "$deadline" </dev/null >/dev/null 2>&1; then
        echo "$(date -u +%FT%TZ) HOLD record not written; no hold"; return 0
    fi
    echo "$(date -u +%FT%TZ) HOLD status=$status until $(date -u -d "@$deadline" +%FT%TZ) or $X/o/$job/RELEASE"
    # TERM/USR1 (scancel, time limit) end the hold at once.
    trap 'reason=signal' TERM USR1
    while [[ -z $reason ]]; do
        if (( $(date +%s) >= deadline )); then reason=timeout; break; fi
        timeout --signal=KILL 10s python3 -B -I -s "$N/j7.py" poll "$X" "$job" </dev/null >/dev/null 2>&1 &
        pid=$!; wait "$pid"; rc=$?
        if [[ -n $reason ]]; then kill -KILL "$pid" 2>/dev/null; break; fi
        if [[ $rc == 0 ]]; then reason=release; break; fi
        sleep "$J7_POLL_S" </dev/null >/dev/null 2>&1 &
        pid=$!; wait "$pid"
        if [[ -n $reason ]]; then kill -KILL "$pid" 2>/dev/null; fi
    done
    trap '' TERM USR1
    echo "$(date -u +%FT%TZ) HOLD end reason=$reason status=$status"
    timeout --signal=KILL 15s python3 -B -I -s "$N/j7.py" end "$X" "$job" "$status" "$reason" "$now" </dev/null >/dev/null 2>&1 || true
}
# One final attempt: 120 s, then at most 15 s for fixed-text fallback.
# KILL deadlines also cover children that inherit ignored TERM/USR1.
finish() {
    local status=$1 left=${2:-0} right=${3:-0} message
    trap - EXIT
    trap '' TERM USR1
    set +e
    # Stop the separate periodic session on every exit; never wait on its IO.
    if [[ -n ${J2_PID:-} ]]; then kill -KILL -- "-$J2_PID" 2>/dev/null || true; fi
    # Stop the live mirror now; its one final snapshot comes after the final publish.
    if [[ -n ${J6_PID:-} ]]; then kill -KILL -- "-$J6_PID" 2>/dev/null || true; fi
    if timeout --signal=KILL 120s python3 -B -I -s "${N:-}/j2.py" "$ROOT" "${N:-}" "$X" "${SLURM_JOB_ID:-0}" "$$" 600 once; then
        :
    else
        # Never copy raw logs here. Only these fixed labels and shell statuses
        # may reach X without the kit's screen(), including setup failures.
        case ${step:-setup} in
            node) message='node directory failed' ;;
            log) message='j2.log redirect failed' ;;
            publisher) message='j2.py creation failed' ;;
            gpu) message='fewer than 4 H100; stop before staging' ;;
            seal) message='v.py refusal' ;;
            resolve)
                if [[ $right != 0 ]]; then message='l.py refusal'
                elif [[ $left != 0 ]]; then message='resolve.py refusal'
                else message='resolve.py/l.py refusal'; fi ;;
            child) message='job.sh exit' ;;
            *) message='wrapper setup failed' ;;
        esac
        timeout --signal=KILL 15s bash -c '
            umask 077
            mkdir -p -- "$1/o/$2" &&
            printf "%s; status=%s\n" "$3" "$4" >> "$1/o/$2/j2.fallback.log"
        ' bash "$X" "${SLURM_JOB_ID:-0}" "$message" "$status" || true
    fi
    # The kit's raw traceback file, at most 200 KB, on every failure (jn7).
    if [[ $status != 0 && -f ${N:-/nonexistent}/j7.py ]]; then
        timeout --signal=KILL 30s python3 -B -I -s "$N/j7.py" tb "$N" "$X" "${SLURM_JOB_ID:-0}" "$status" </dev/null >/dev/null 2>&1 || true
    fi
    # One bounded final live snapshot, after the publish so it can never delay the failure text.
    if [[ -f ${N:-/nonexistent}/j6.py ]]; then
        timeout --signal=KILL 30s python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "${SLURM_JOB_ID:-0}" "$$" 120 once final </dev/null >/dev/null 2>&1 || true
    fi
    hold "$status"
    exit "$status"
}
trap 'finish "$?" "${PIPESTATUS[@]}"' EXIT
umask 077
export PYTHONDONTWRITEBYTECODE=1
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
step=node
mkdir -p "$N"
step=log
exec >>"$N/j2.log" 2>>"$N/j2.err"
step=publisher
cat > "$N/j2.py" <<'PYJ2'
import os,sys,time
from pathlib import Path
kit,node,target,job,parent=sys.argv[1:6]
node=Path(node);target=Path(target)/'o'/job
sys.path.insert(0,str(Path(kit)/'b'))
from z import load,screen
words=load(Path(kit)/'k/g.json');hashes=load(Path(kit)/'b/wh.json')
interval=float(sys.argv[6]) if len(sys.argv)>6 else 600
# This process owns no training pipe; failed publication cannot close one.
def publish():
    try:
        target.mkdir(parents=True,exist_ok=True,mode=0o700)
        for name in ('j2.log','j2.err'):
            with (node/name).open('rb') as f:
                f.seek(max(0,os.fstat(f.fileno()).st_size-300000))
                raw=screen(f.read().decode('utf-8','replace'),words,hashes).encode()[-300000:]
            temp=target/(name+'.part')
            with temp.open('wb') as f:f.write(raw)
            os.replace(temp,target/name)
        return True
    except Exception as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' '+type(e).__name__+' '+__import__('re').sub(r'https?://[^\s]+','[URL]',str(e))+'\n')
        return False
if len(sys.argv)>7 and sys.argv[7]=='once':raise SystemExit(0 if publish() else 1)
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
J2_PID=$!
# Live mirror every 120 s into $X/o/<job>_live (memory, disk, screened tails, gate state), plus one copy
# of the six gate files into $X/o/<job>_gate once WAITING_REVIEW.json is on X; never fatal.
step=mirror
if cat > "$N/j6.py" <<'PYJ6'
import json,os,stat,subprocess,sys,time
from pathlib import Path
# Live mirror for the batch shell: memory, disk, screened log tails, gate state.
# Never raises into the wrapper; every snapshot runs in a child bounded by timeout.
kit,node,xr,job,parent,interval,mode=sys.argv[1:8]
phase=sys.argv[8] if len(sys.argv)>8 else 'live'
kit,node,xr=Path(kit),Path(node),Path(xr)
target=xr/'o'/(job+'_live')
LIMIT=2_000_000
CG=Path(os.environ.get('J6_CG','/sys/fs/cgroup'));PC=Path(os.environ.get('J6_PC','/proc/self/cgroup'))
def snapshot():
    import fcntl
    lock=os.open(node/'j6.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX)
    if any(p.is_symlink() for p in (target,*target.parents)):raise ValueError('E01')
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    sp=node/'j6.state.json'
    try:state=json.loads(sp.read_text())
    except Exception:state={}
    state.setdefault('alarm',False);state.setdefault('events',{});state['n']=state.get('n',0)+1
    notes=[]
    def size(skip):
        return sum(p.stat().st_size for p in target.iterdir() if p.is_file() and p.name!=skip and not p.name.endswith('.part'))
    def put(name,raw,append=False):
        dest=target/name;temp=target/(name+'.part')
        if dest.is_symlink() or temp.is_symlink():raise ValueError('E02')
        if append and dest.is_file():raw=dest.read_bytes()+raw
        if size(name)+len(raw)>LIMIT:notes.append('skip %s %d budget'%(name,len(raw)));return False
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
        os.replace(temp,dest);return True
    now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    # Memory of the job cgroup (v2, else v1), the step and the leaf.
    mem=['utc '+now,'phase '+phase,'snapshot '+str(state['n'])];job_vals={}
    def rd(p,cap=16384):
        with open(p,'rb') as f:return f.read(cap).decode('ascii','replace')
    try:
        lines=rd(PC).splitlines()
        v2=next((s.split(':',2)[2] for s in lines if s.startswith('0::')),None)
        v1=next((s.split(':',2)[2] for s in lines if ':memory:' in s),None)
        if v1 is not None:base=CG/'memory';entry=v1
        else:base=CG;entry=v2 or '/'
        leaf=base/entry.lstrip('/');chain=[leaf,*leaf.parents]
        jobd=next((p for p in chain if p.name=='job_'+job),None)
        stepd=next((p for p in chain if p.name.startswith('step_')),leaf)
        # Orchard names the job level by a hash (slurmstepd.scope/<id>/step_batch): use the step's parent.
        if jobd is None and stepd.name.startswith('step_'):jobd=stepd.parent
        lim_from=None
        for p in ([jobd,*jobd.parents] if jobd else []):
            if p==base:break
            try:
                v=rd(p/'memory.max').split()[0] if (p/'memory.max').exists() else rd(p/'memory.limit_in_bytes').split()[0]
                if v.isdigit():lim_from=(int(v),p);break
            except OSError:pass
        mem.append('limit %s from %s'%((lim_from[0],lim_from[1]) if lim_from else ('none','none')))
        if lim_from:job_vals['limit']=str(lim_from[0])
        keep=('anon','file','shmem','file_dirty','file_writeback','kernel','rss','cache','dirty','writeback','total_rss','total_cache','total_shmem','total_dirty','total_writeback')
        names=('memory.current','memory.max','memory.peak','memory.events','memory.usage_in_bytes','memory.limit_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control','memory.stat')
        for label,d in (('job',jobd),('step',stepd),('leaf',leaf)):
            mem.append('%s %s'%(label,d if d else 'missing'))
            if d is None:continue
            for name in names:
                p=d/name
                if not p.exists():continue
                try:
                    raw=rd(p)
                    if name=='memory.stat':raw='\n'.join(s for s in raw.splitlines() if s.split() and s.split()[0] in keep)
                    mem.append(name+'\n'+raw.rstrip())
                    if label=='job':job_vals[name]=raw
                except OSError as e:mem.append(name+' E%s'%e.errno)
    except Exception as e:mem.append('E03 '+type(e).__name__)
    put('mem.txt',('\n'.join(mem)+'\n').encode())
    # Alarm: anon+shmem over 80% of the limit (page cache is expected to fill it), or new oom events.
    try:
        st={s.split()[0]:int(s.split()[1]) for s in job_vals.get('memory.stat','').splitlines() if len(s.split())==2}
        lim=job_vals.get('limit') or 'max'
        lim=int(lim.split()[0]) if lim.split()[0].isdigit() else 0
        cur=job_vals.get('memory.current') or job_vals.get('memory.usage_in_bytes') or '0'
        anon=st.get('anon',st.get('total_rss',0));shm=st.get('shmem',st.get('total_shmem',0));fil=st.get('file',st.get('total_cache',0))
        line=None
        if lim and anon+shm>0.8*lim and not state['alarm']:
            state['alarm']=True;line='MEM_ALARM %s %s %d anon=%d shmem=%d file=%d'%(now,cur.split()[0],lim,anon,shm,fil)
        elif lim and anon+shm<0.75*lim and state['alarm']:
            state['alarm']=False;line='MEM_CLEAR %s %s %d anon=%d shmem=%d file=%d'%(now,cur.split()[0],lim,anon,shm,fil)
        if line:put('alarm.txt',(line+'\n').encode(),append=True)
        ev={s.split()[0]:int(s.split()[1]) for s in job_vals.get('memory.events','').splitlines() if len(s.split())==2}
        for k in ('oom','oom_kill'):
            if k not in ev:continue
            if ev[k]>state['events'].get(k,0):
                put('alarm.txt',('OOM_EVENT %s %s=%d (was %d) anon=%d shmem=%d\n'%(now,k,ev[k],state['events'].get(k,0),anon,shm)).encode(),append=True)
            state['events'][k]=ev[k]
    except Exception as e:notes.append('alarm E04 '+type(e).__name__)
    # Screened tails (never raw): the kit's own screen, as j2.py uses.
    try:
        sys.path.insert(0,str(kit/'b'))
        from z import load,screen
        words=load(kit/'k/g.json');hashes=load(kit/'b/wh.json')
        tails=(('q.log',node/'q.log'),('q.steps',node/(job+'.steps')),('j2.err',node/'j2.err'),('j2.log',node/'j2.log'),
               ('s.err',Path(os.environ.get('SLURM_TMPDIR','/tmp'))/('q_22c714e1_%s.err'%job)))
        for name,p in tails:
            try:
                if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode):continue
                with p.open('rb') as f:
                    f.seek(max(0,os.fstat(f.fileno()).st_size-65536));raw=f.read(65536)
                put('t_'+name,screen(raw.decode('utf-8','replace'),words,hashes).encode()[-65536:])
            except OSError as e:notes.append('%s E%s'%(name,e.errno))
    except Exception as e:notes.append('tails E05 '+type(e).__name__)
    # Gate state: the kit publishes v.json and WAITING_REVIEW.json on X itself; record presence only.
    try:
        live=xr/'o'/job/'live';g=['utc '+now]
        for name in ('v.json','WAITING_REVIEW.json'):
            p=live/name
            if p.is_file():s=p.stat();g.append('%s bytes=%d mtime=%s'%(name,s.st_size,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(s.st_mtime))))
            else:g.append(name+' absent')
        rv=xr/'n_r'/'review.json';g.append('review.json '+('present' if rv.is_file() else 'absent'))
        g.append('gate_copy '+('done' if (xr/'o'/(job+'_gate')/'SHA256SUMS').is_file() else 'not yet'))
        w=live/'WAITING_REVIEW.json'
        if w.is_file():
            try:
                from z import load
                b=load(kit/'k/a.json')['review_wait_seconds'];age=int(time.time()-w.stat().st_mtime)
                g.append('gate waiting_since=%s waited_s=%d bound_s=%s left_s=%s'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(w.stat().st_mtime)),age,b,(b-age) if type(b) is int else '?'))
            except Exception as e:g.append('gate bound E06 '+type(e).__name__)
        put('gate.txt',('\n'.join(g)+'\n').encode())
    except Exception as e:notes.append('gate '+type(e).__name__)
    # Disk: node directory, /tmp, /dev/shm. Own session and a file, so a hung df cannot hold a pipe.
    try:
        import signal
        out=node/'j6.df.out'
        with open(out,'wb') as f:
            pr=subprocess.Popen(['df','-Pk',str(node),'/tmp','/dev/shm'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:pr.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(pr.pid,signal.SIGKILL);notes.append('df timeout')
        put('df.txt',('utc '+now+'\n').encode()+out.read_bytes()[-16384:])
    except Exception as e:notes.append('df '+type(e).__name__)
    state['last']=now;state['phase']=phase;state['notes']=notes[-20:]
    put('live.json',(json.dumps(state,sort_keys=True)+'\n').encode())
    sp.write_text(json.dumps(state))
    os.close(lock)
GATE=xr/'o'/(job+'_gate');WAIT=xr/'o'/job/'live'/'WAITING_REVIEW.json'
GFILES=(('population.json','p/q/b/population.json'),('indices.json','p/q/b/indices.json'),('reader_filters.json','p/q/b/reader_filters.json'),
        ('binding.json','p/q/b/binding.json'),('receipt.json','p/q/b/receipt.json'),('f.json','p/q/f.json'))
def gate_copy():
    # Once, when WAITING_REVIEW.json is on X: gzip -9 the six node-local gate files into X/o/<job>_gate,
    # SHA256SUMS of the raw bytes written last, at most 10 MB in total; separate from the live mirror.
    import gzip,hashlib,io
    if (GATE/'SHA256SUMS').is_file() or not WAIT.is_file():return
    if any(p.is_symlink() for p in (GATE,*GATE.parents)):raise ValueError('E07')
    GATE.mkdir(parents=True,exist_ok=True,mode=0o700)
    def put(name,raw):
        dest=GATE/name;temp=GATE/(name+'.part')
        if dest.is_symlink() or temp.is_symlink():raise ValueError('E08')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
        os.replace(temp,dest)
    total=0;sums=[];notes=[]
    for name,rel in GFILES:
        p=node/rel
        try:
            if not p.exists():notes.append('%s absent'%rel);continue
            if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode):notes.append('%s not a regular file'%rel);continue
            raw=p.read_bytes();b=io.BytesIO()
            with gzip.GzipFile(fileobj=b,mode='wb',compresslevel=9,mtime=0) as z:z.write(raw)
            z=b.getvalue()
            if total+len(z)>10_000_000:notes.append('%s skipped: %d raw bytes, %d gz bytes over the 10 MB total'%(rel,len(raw),len(z)));continue
            put(name+'.gz',z);total+=len(z);sums.append('%s  %s'%(hashlib.sha256(raw).hexdigest(),name))
        except OSError as e:notes.append('%s E%s'%(rel,e.errno))
    put('NOTES.txt',('utc %s\ngz_bytes %d\n'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),total)+''.join(n+'\n' for n in notes)).encode())
    put('SHA256SUMS',''.join(x+'\n' for x in sums).encode())
if mode=='once':
    try:gate_copy() if phase=='gate' else snapshot()
    except Exception:raise SystemExit(1)
    raise SystemExit(0)
me=[sys.executable,'-B','-I','-s',__file__,*sys.argv[1:7],'once']
tries=0
while True:
    try:subprocess.run(['timeout','-k','2','30',*me,'live'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)
    except Exception:pass
    try:
        if tries<3 and WAIT.is_file() and not (GATE/'SHA256SUMS').is_file():
            tries+=1;subprocess.run(['timeout','-k','2','300',*me,'gate'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=310)
    except Exception:pass
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    except Exception:pass
    time.sleep(float(interval))
PYJ6
then
    setsid python3 -B -I -s "$N/j6.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" 120 loop </dev/null >>"$N/j6.err" 2>&1 &
    J6_PID=$!
else
    echo "$(date -u +%FT%TZ) live mirror not written"
fi
step=holdkit
if cat > "$N/j7.part" <<'PYJ7'
import os,re,socket,stat,sys,time
from pathlib import Path
# jn7 helper for the batch shell: traceback copy (tb), node hold record (hold), release poll (poll), hold end (end).
# Every call runs under a KILL timeout in the wrapper; failures return non-zero and never raise into it.
TB_CAP=204800
mode=sys.argv[1]
def utc(t=None):return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(t))
def target(xr,job):
    t=Path(xr)/'o'/job
    if not re.fullmatch('[0-9]+',job):raise ValueError('E71')
    if any(p.is_symlink() for p in (t,*t.parents)):raise ValueError('E72')
    return t
def put(t,name,raw):
    t.mkdir(parents=True,exist_ok=True,mode=0o700)
    dest=t/name;temp=t/(name+'.part')
    if dest.is_symlink() or temp.is_symlink():raise ValueError('E73')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)
    os.replace(temp,dest)
def regular(p):
    try:s=os.lstat(p)
    except OSError:return None
    return s.st_size if stat.S_ISREG(s.st_mode) else -1
def tb(node,xr,job,status):
    # The kit's raw traceback file (fix4 contract: $Q_ROOT/tb.txt), unscreened, bounded at 200 KB; URLs replaced.
    src=Path(node)/'tb.txt';t=target(xr,job);size=regular(src)
    if size is None:raw=('no traceback file at %s; status=%s; utc %s\n'%(src,status,utc())).encode()
    elif size<0:raw=('%s is not a regular file; status=%s\n'%(src,status)).encode()
    else:
        fd=os.open(src,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as f:
            if size<=TB_CAP:raw=f.read(TB_CAP)
            else:
                head=f.read(TB_CAP//2-200);f.seek(size-(TB_CAP//2-200));tail=f.read()
                raw=head+('\n[jn7: %d bytes of %d omitted]\n'%(size-len(head)-len(tail),size)).encode()+tail
        raw=re.sub(rb'https?://[^\s\'"]+',b'[URL]',raw)[:TB_CAP]
    put(t,'tb.txt',raw)
def hold(node,xr,job,status,step,start,deadline):
    node=Path(node);t=target(xr,job);start=int(start);deadline=int(deadline)
    def row(label,p):
        size=regular(p)
        return '%-22s %s  %s\n'%(label,p,'absent' if size is None else ('dir' if p.is_dir() else ('not regular' if size<0 else '%d bytes'%size)))
    slog=Path('/tmp')/('q_22c714e1_%s'%job)
    text=('HOLD job=%s node=%s status=%s step=%s\n'%(job,socket.gethostname(),status,step)+
        'start_utc %s deadline_utc %s hold_seconds %d\n'%(utc(start),utc(deadline),deadline-start)+
        'The job failed before training; the wrapper keeps the node and the node directory until the deadline,\n'
        'until %s exists, or until TERM/USR1 (scancel). It then exits with status %s.\n'%(t/'RELEASE',status)+
        'release: touch %s (seen within about 25 s)\n'%(t/'RELEASE')+
        'enter:   srun --overlap --jobid %s --pty bash\n'%job+
        'sandbox: /tmp/q_22c714e1 inside the job sandbox is the node directory below\n'
        'node-local paths:\n'+
        row('node directory',node)+row('prepared root p',node/'p')+row('prepared q p/q',node/'p'/'q')+
        row('proof result',node/'p'/'q'/'RESULT.json')+row('traceback tb.txt',node/'tb.txt')+
        row('kit shell j.sh',node/'j.sh')+row('request r.json',node/'r.json')+
        ''.join(row('log '+n,node/n) for n in ('j2.log','j2.err','q.log','rooms.log','h.log','rv.log',job+'.steps'))+
        row('slurm log',Path(str(slog)+'.log'))+row('slurm err',Path(str(slog)+'.err'))+
        'training markers (absent, else no hold): %s %s\n'%(node/'t.log',node/'p'/'rv.json'))
    raw=text.encode()
    try:put(node,'HOLD.txt',raw)
    except OSError:pass
    put(t,'HOLD.txt',raw)
def poll(xr,job):
    return 0 if os.path.lexists(target(xr,job)/'RELEASE') else 1
def end(xr,job,status,reason,start):
    put(target(xr,job),'HOLD_END.txt',('HOLD_END job=%s reason=%s status=%s start_utc %s end_utc %s held_seconds %d\n'%(
        job,reason,status,utc(int(start)),utc(),int(time.time())-int(start))).encode())
try:
    if mode=='tb':tb(*sys.argv[2:6])
    elif mode=='hold':hold(*sys.argv[2:9])
    elif mode=='poll':raise SystemExit(poll(*sys.argv[2:4]))
    elif mode=='end':end(*sys.argv[2:7])
    else:raise SystemExit(2)
except SystemExit:raise
except Exception:raise SystemExit(3)
PYJ7
then
    mv -f -- "$N/j7.part" "$N/j7.py" || echo "$(date -u +%FT%TZ) hold helper not installed"
else
    echo "$(date -u +%FT%TZ) hold helper not written"
fi
step=setup
printf '%s SLURM_TMPDIR=%s free_bytes=' "$(date -u +%FT%TZ)" "${SLURM_TMPDIR:-/tmp}"
python3 -B -I -s -c 'import shutil,sys;print(shutil.disk_usage(sys.argv[1]).free)' "${SLURM_TMPDIR:-/tmp}"
child=''
forward() { if [[ -n "$child" ]]; then kill -"$1" "$child" 2>/dev/null || true; fi; }
trap 'J7_SIG=TERM; forward TERM' TERM
trap 'J7_SIG=USR1; forward USR1' USR1
step=gpu
g=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>&1 | head -4 || true); echo "$(date -u +%FT%TZ) gpus: $g" | tr '\n' ';'; echo
[ "$(nvidia-smi -L 2>/dev/null | grep -c H100)" -ge 4 ] || { echo "$(date -u +%FT%TZ) fewer than 4 H100; stop before staging"; exit 3; }
echo "$(date -u +%FT%TZ) resolve start"
step=seal
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
step=resolve
OMP_NUM_THREADS=8 python3 -B -I -s "$ROOT/b/resolve.py" --pool "/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7/work/build27/pool" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT"
echo "$(date -u +%FT%TZ) resolve done; start job.sh"
step=child
bash "$ROOT/job.sh" "$N/r0.json" &
child=$!
set +e
while true; do
    wait "$child"
    status=$?
    kill -0 "$child" 2>/dev/null || break
done
trap '' TERM USR1
# Retrieve the final child status even if the signal interrupted the first wait.
wait "$child"
status=$?
exit "$status"
