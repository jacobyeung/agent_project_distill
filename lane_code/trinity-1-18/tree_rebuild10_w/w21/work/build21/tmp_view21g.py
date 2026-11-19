"""Exercise the default /tmp job path without writing there on the host."""
from pathlib import Path
import datetime,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
view=J.load(D/'VIEW.json');node=view['variables']['Q_ROOT'];dest='/tmp/q_22c714e1_173051'
args=J.load(D/'proofs/view/after.json');replacement=[];i=0
while i<len(args):
    option=args[i]
    if option in ('--bind','--ro-bind','--dev-bind','--symlink'):
        source,target=args[i+1:i+3]
        if target==node or target.startswith(node+'/'):target=dest+target[len(node):]
        replacement.extend([option,source,target]);i+=3
    else:replacement.append(option);i+=1
probe=D/'proofs/view/visible.py';expected={dest+'/marker':'root',dest+'/j/marker':'job','/tmp/q_22c714e1/marker':'root'}
command=replacement+[sys.executable,'-I','-s','-B',str(probe),json.dumps(expected)]
p=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
J.write(D/'TMP_VIEW.json',dict(command=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,
    stand_in='Host sources stay under L; only the destination of the job-root/jobdir bind uses the production default /tmp layout.'))
assert p.returncode==0,p.stderr
print('PASS: namespace and default /tmp job-root aliases remain visible')
