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
    except Exception as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' '+type(e).__name__+' '+__import__('re').sub(r'https?://[^\s]+','[URL]',str(e))+'\n')
if len(sys.argv)>7 and sys.argv[7]=='once':publish();raise SystemExit(0)
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)