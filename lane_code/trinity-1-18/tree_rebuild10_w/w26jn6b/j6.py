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
        lim=job_vals.get('memory.max') or job_vals.get('memory.limit_in_bytes') or 'max'
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
        for name in ('v.json','WAITING_REVIEW.json','f1.json'):
            p=live/name
            if p.is_file():s=p.stat();g.append('%s bytes=%d mtime=%s'%(name,s.st_size,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(s.st_mtime))))
            else:g.append(name+' absent')
        rv=xr/'n_r'/'review.json';g.append('review.json '+('present' if rv.is_file() else 'absent'))
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
            try:pr.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(pr.pid,signal.SIGKILL);notes.append('df timeout')
        put('df.txt',('utc '+now+'\n').encode()+out.read_bytes()[-16384:])
    except Exception as e:notes.append('df '+type(e).__name__)
    state['last']=now;state['phase']=phase;state['notes']=notes[-20:]
    put('live.json',(json.dumps(state,sort_keys=True)+'\n').encode())
    sp.write_text(json.dumps(state))
    os.close(lock)
if mode=='once':
    try:snapshot()
    except Exception:raise SystemExit(1)
    raise SystemExit(0)
me=[sys.executable,'-B','-I','-s',__file__,*sys.argv[1:7],'once']
while True:
    try:subprocess.run(['timeout','-k','2','30',*me,'live'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)
    except Exception:pass
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    except Exception:pass
    time.sleep(float(interval))
