"""Exercise bwrap without creating any host file outside the workspace."""
from pathlib import Path
import datetime,json,os,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g';R=D/'proofs/mount'
R.mkdir(parents=True,exist_ok=True);source=R/'source';source.mkdir(exist_ok=True)
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
destination='/tmp/q_22c714e1'
assert not Path(destination).exists(),'The reduction requires an absent host destination'
def run(label,args):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    result=dict(label=label,args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    print(json.dumps(result),flush=True);return result
before=run('read_only_parent',['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(source),destination,'/usr/bin/true'])
after=run('writable_parent',['/usr/bin/bwrap','--ro-bind','/','/','--tmpfs','/tmp','--bind',str(source),destination,'/usr/bin/true'])
(D/'MOUNT_REDUCTION.json').write_text(json.dumps(dict(before=before,after=after),indent=2)+'\n')
assert before['returncode'] and 'Read-only file system' in before['stderr']
assert after['returncode']==0
