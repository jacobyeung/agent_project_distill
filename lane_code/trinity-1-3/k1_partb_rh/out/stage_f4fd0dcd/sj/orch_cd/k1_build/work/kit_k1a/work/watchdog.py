"""Watch one own child; never retry a failed or stalled worker."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stall_state import publish
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--stall',type=int,default=900);p.add_argument('--seconds',type=int,default=21600);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if (out/'HALTED.json').exists():raise ValueError('HALTED worker requires operator review and a fresh root')
 cmd=a.command[1:] if a.command[:1]==['--'] else a.command
 start=time.monotonic();last=start;stamp=None
 started=time.time();publish(out,started)
 with (out/'worker.log').open('a') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while child.poll() is None:
   publish(out,started)
   progress=out/'PROGRESS.jsonl'
   current=progress.stat().st_mtime_ns if progress.exists() else None
   if current!=stamp:stamp=current;last=time.monotonic()
   reason='wall_time_cap' if time.monotonic()-start>a.seconds else 'stall' if time.monotonic()-last>a.stall else None
   if reason:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    (out/'HALTED.json').write_text(json.dumps(dict(reason=reason,automatic_retry=False,operator_review_required=True))+'\n');publish(out,started,finished=True);return 3
   time.sleep(1)
  if child.returncode not in (0,4) and not (out/'HALTED.json').exists():
   (out/'HALTED.json').write_text(json.dumps(dict(reason='worker_failed',returncode=child.returncode,automatic_retry=False,operator_review_required=True))+'\n')
  publish(out,started,finished=True)
  return child.returncode
if __name__=='__main__':raise SystemExit(main())
