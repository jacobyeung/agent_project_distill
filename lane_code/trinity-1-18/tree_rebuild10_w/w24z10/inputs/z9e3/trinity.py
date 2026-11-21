"""Drive the sealed E3 fixture inside a private root on the designated CPU node."""
import importlib.util,json,os,shutil,socket,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
X=Path("/project/community/jjyeung/okh7/x_22c714e1")

def module():
    spec=importlib.util.spec_from_file_location("e3_driver",D/"e3.py")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def inside():
    n=Path(os.environ["E3_N"]);job=os.environ["SLURM_JOB_ID"];m=module();rc=1
    try:
        (X/"n_s").mkdir(mode=0o700)
        p=X/"n_s"/("sess_"+job+".json")
        shutil.copyfile(n/"input.json",p);p.chmod(0o600)
        m.stage(D,n,X,job)
        rc=m.run(n,X,job)
    except Exception as e:
        code=str(e) if isinstance(e,ValueError) and str(e).startswith("E") and str(e)[1:].isdigit() else "E99"
        m.fail(n,code);print("E3_FAIL "+code+" "+type(e).__name__,flush=True)
    finally:
        try:m.finish(n,X,job,rc)
        except Exception as e:
            m.fail(n,"E90");print("E3_FAIL E90 "+type(e).__name__,flush=True);rc=1
    return rc

def outer():
    if socket.gethostname().split(".")[0]!="trinity-1-18":
        print("E3_FAIL E_HOST");return 2
    job,source,target=sys.argv[1:]
    if not job.isascii() or not job.isdigit():return 2
    n=Path(target).resolve()
    if not str(n).startswith("/scratch/"):
        print("E3_FAIL E_OUTPUT");return 2
    n.mkdir(mode=0o700,parents=True,exist_ok=True)
    if any(n.iterdir()):
        print("E3_FAIL E_USED_OUTPUT");return 2
    n.chmod(0o700)
    for name in ("tmp","probe","logs","obs","bin","root"):(n/name).mkdir(mode=0o700)
    m=module()
    # Copy capabilities only into the private output; never render their values.
    try:
        source=Path(source).resolve()
        if not source.is_file() or source.stat().st_size>2_000_000:raise ValueError("E11")
        raw=source.read_bytes();values=json.loads(raw)
        if not isinstance(values,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in values.items()):raise ValueError("E11")
        (n/"input.json").write_bytes(raw);(n/"input.json").chmod(0o600)
    except Exception as e:
        m.fail(n,"E11");print("E3_FAIL E11 "+type(e).__name__);return 1
    env={**os.environ,"E3_N":str(n),"E3_PY":sys.executable,"SLURM_JOB_ID":job,
         "E3_LOCAL_BYTES":str(1<<20),"TMPDIR":str(n/"tmp"),"SLURM_TMPDIR":str(n/"tmp"),
         "TK_JOB_START":str(int(time.time())),"TK_TIME_LIMIT_SECONDS":"1800"}
    for key in ("TK_COPY_DEADLINE","SLURM_JOB_END_TIME","TK_FINALIZING"):env.pop(key,None)
    with (n/"logs/e3.log").open("w") as out,(n/"logs/e3.err").open("w") as err:
        out.write("SLURM_TMPDIR="+env["SLURM_TMPDIR"]+"\n");out.flush()
        subprocess.run(["df","-B1",env["SLURM_TMPDIR"]],stdout=out,stderr=err,env=env)
        p=subprocess.run(["unshare","-Urm","bash",str(D/"trinity.sh"),"--namespace",str(n)],env=env,stdout=out,stderr=err)
    if p.returncode or not (n/"E3.json").exists():
        if not (n/"E3.json").exists():m.fail(n,"E01")
        print("E3_FAIL; local logs retained");return p.returncode or 1
    report=m.load(n/"E3.json")
    print("E3_"+report["status"])
    return 0 if report["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(inside() if sys.argv[1:]==["--inside"] else outer())
