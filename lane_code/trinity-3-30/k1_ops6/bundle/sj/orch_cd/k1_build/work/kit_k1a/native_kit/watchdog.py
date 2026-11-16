"""One worker, no retries. Stop only this kit's own process group after a stall."""
import argparse,subprocess,os,signal,time,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(__doc__)
 for name in ['python','manifest','out']:p.add_argument('--'+name,required=True)
 p.add_argument('--max-seconds',default='14400');p.add_argument('--max-bytes',default='10000000000');p.add_argument('--stall-seconds',type=float,default=1800)
 a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if (out/'HALTED.json').exists():raise ValueError('HALTED: no automatic restart')
 cmd=[a.python,'-I','-s','-B',str(Path(__file__).with_name('run.py')),'run','--manifest',a.manifest,'--out',a.out,'--max-seconds',a.max_seconds,'--max-bytes',a.max_bytes]
 with (out/'worker.log').open('a') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True);last=time.monotonic();size=0
  while child.poll() is None:
   progress=out/'PROGRESS.jsonl';current=progress.stat().st_size if progress.exists() else 0
   if current!=size:size=current;last=time.monotonic()
   if time.monotonic()-last>a.stall_seconds:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=30)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    (out/'HALTED.json').write_text(json.dumps(dict(reason='worker stall',automatic_retry=False,pid=child.pid))+'\n');return 3
   time.sleep(5)
  if child.returncode not in (0,4) and not (out/'HALTED.json').exists():(out/'HALTED.json').write_text(json.dumps(dict(reason='worker nonzero',returncode=child.returncode,automatic_retry=False))+'\n')
  return child.returncode
if __name__=='__main__':raise SystemExit(main())
