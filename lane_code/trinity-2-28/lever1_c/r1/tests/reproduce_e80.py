"""Replay the placed full-closure boot with a safe 30-second policy watcher."""
import json,os,sys,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'runtime'))
import e,j
exec((HERE/'out/E80_OLD_CAPTURE.py').read_text(),e.__dict__)
proof=json.loads((HERE/'out/E80_REPRO.json').read_text())
root=Path(proof['argv'][-2]).parent.parent;base=root.parent
helper=base/'watch_e80.sh';pidfile=root/'a/watch_e80.pid'
helper.write_text('#!/bin/bash\necho $$ > '+str(pidfile)+'\nexec sleep 30\n');helper.chmod(0o700)
argv=proof['argv']
env=dict(PATH='/usr/bin:/bin',USER='jjyeung',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
start=time.monotonic();evidence=dict(argv=argv,source_delivery_sha256=proof['source_delivery_sha256'])
try:
    with e.capture(base/'e80.json') as stream:
        pipe=os.readlink('/proc/self/fd/'+str(stream.fileno()))
        result=subprocess.run(argv,env=env,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
        evidence['returncode']=result.returncode
        pid=int(pidfile.read_text())
        evidence.update(returncode=result.returncode,pipe=pipe,watcher_pid=pid,
                        watcher_stdout=os.readlink('/proc/'+str(pid)+'/fd/1'),watcher_stderr=os.readlink('/proc/'+str(pid)+'/fd/2'),
                        watcher_command=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\0',b' ').decode())
except RuntimeError as error:evidence['error']=str(error)
evidence['seconds']=time.monotonic()-start
evidence['boot']=j.loads((root/'sj/b01ec87a6f29b/r/metadata/25.json').read_bytes())
(HERE/'out/E80_REPRO.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence,indent=2))
assert evidence['error']=='E80' and evidence['returncode']==0 and evidence['boot']['modules']==411
assert evidence['pipe']==evidence['watcher_stdout']==evidence['watcher_stderr']
