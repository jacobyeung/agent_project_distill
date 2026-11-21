import fcntl,json,os,stat,subprocess,sys,time
from pathlib import Path
node,target,job,err,phase=sys.argv[1:]
node,target=Path(node),Path(target)
lock=None
try:
    lock=os.open(node/"j8.lock",os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX)
    if any(p.is_symlink() for p in (target,*target.parents)):raise ValueError("E01")
    target.mkdir(parents=True,exist_ok=True,mode=0o700);target.chmod(0o700)
    status=target/"live.json"
    state=json.loads(status.read_bytes()) if status.is_file() else {"once":{}}
    state.update(phase=phase,time_ns=time.time_ns(),notes=[])
    def size():
        return sum(p.stat().st_size for p in target.rglob("*") if p.is_file())
    def put(name,raw,limit=3_980_000):
        dest=target/name;temp=target/(name+".part")
        if dest.is_symlink() or temp.is_symlink():raise ValueError("E02")
        # Count both the old destination and the full .part during replacement.
        if size()+len(raw)>=limit:
            state["notes"].append({"name":name,"bytes":len(raw),"reason":"budget"});return False
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,"wb") as f:f.write(raw)
        subprocess.run(["timeout","-k","1","30","mv","-f","--",str(temp),str(dest)],check=True)
        return True
    def read(path,cap=65536):
        with Path(path).open("rb") as f:return f.read(cap)
    def tail(path):
        with Path(path).open("rb") as f:
            f.seek(max(0,os.fstat(f.fileno()).st_size-65536));return f.read(65536)
    mem=["time_ns "+str(state["time_ns"]),"phase "+phase]
    try:
        entry=next(s.split(":",2)[2] for s in Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z15/work/build24m4z15/live/cgroup').read_text().splitlines() if s.startswith("0::"))
        leaf=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z15/work/build24m4z15/live/cg')/entry.lstrip("/")
        chain=[leaf,*leaf.parents]
        parent=next((p for p in chain if p.name=="job_"+job),None)
        step=next((p for p in chain if p.name.startswith("step_")),leaf)
        for label,path in (("job",parent),("step",step),("leaf",leaf)):
            mem.append(label+" "+(str(path) if path else "missing"))
            if path is None:continue
            for name in ("memory.current","memory.max","memory.peak","memory.events","memory.stat"):
                try:
                    raw=read(path/name,8192).decode("ascii","replace")
                    if name=="memory.stat":raw="\n".join(s for s in raw.splitlines() if s.split()[0] in ("anon","file","shmem","file_dirty","file_writeback","kernel"))+"\n"
                    mem.append(name+"\n"+raw.rstrip())
                except OSError as e:mem.append(name+" E"+str(e.errno))
    except (OSError,StopIteration,ValueError) as e:mem.append("E03 "+type(e).__name__)
    put("mem.txt",("\n".join(mem)+"\n").encode())
    result=subprocess.run(["timeout","-k","1","30","df","-Pk",str(node),"/dev/shm"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    put("df.txt",result.stdout[-65536:])
    for name,path in (("q.log",node/"ev/q.log"),("q.steps",node/"ev/q.steps"),("s.err",Path(err))):
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):continue
            put(name,tail(path))
        except OSError as e:state["notes"].append({"name":name,"errno":e.errno})
    for name in ("v.json","WAITING_REVIEW.json","f1.json"):
        if name in state["once"]:continue
        path=node/"ev/live"/name
        try:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):continue
            n=path.stat().st_size
            if n>=1_500_000:state["once"][name]={"bytes":n,"copied":False,"reason":"size"};continue
            raw=read(path,1_500_000)
            if len(raw)>=1_500_000:state["once"][name]={"bytes":path.stat().st_size,"copied":False,"reason":"size"};continue
            state["once"][name]={"bytes":len(raw),"copied":put(name,raw)}
            if not state["once"][name]["copied"]:state["once"][name]["reason"]="budget"
        except OSError as e:state["notes"].append({"name":name,"errno":e.errno})
    put("live.json",(json.dumps(state,sort_keys=True)+"\n").encode(),4_000_000)
except Exception:
    pass
finally:
    if lock is not None:os.close(lock)
