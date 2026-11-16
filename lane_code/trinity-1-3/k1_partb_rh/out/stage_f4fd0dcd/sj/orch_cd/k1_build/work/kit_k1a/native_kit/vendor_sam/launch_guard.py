"""Hard watchdog around one cache worker; no restart loop."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import argparse,subprocess,time,signal,selectors

def supervise(command,out,stall=900,poll=.5):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=False,start_new_session=True)
 sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);last=time.monotonic()
 with (out/'worker.log').open('ab') as log:
  while p.poll() is None:
   for key,_ in sel.select(poll):
    data=os.read(key.fileobj.fileno(),65536)
    if data:log.write(data);log.flush();sys.stdout.buffer.write(data);sys.stdout.buffer.flush();last=time.monotonic()
   if time.monotonic()-last>stall:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    sel.close();p.stdout.close()
    dump(out/'HALTED.json',dict(reason='watchdog: no worker progress',automatic_retry=False));return 3
  tail=p.stdout.read()
  if tail:log.write(tail)
 sel.close();p.stdout.close()
 if p.returncode not in (0,4):dump(out/'HALTED.json',dict(reason='worker failed',returncode=p.returncode,automatic_retry=False))
 return p.returncode

def main():
 p=argparse.ArgumentParser(__doc__);p.add_argument('--python',required=True);p.add_argument('--out',required=True);p.add_argument('--stall-seconds',type=float,default=900);p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
 out=scratch(a.out)
 if (out/'HALTED.json').exists() and '--review-halt' not in a.args:raise SystemExit('HALTED: explicit operator review required')
 args=a.args[1:] if a.args[:1]==['--'] else a.args
 return supervise([a.python,'-I','-s',str(HERE/'cache_masks.py'),'--out',str(out),*args],out,a.stall_seconds)
if __name__=='__main__':sys.exit(main())
