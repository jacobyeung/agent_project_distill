import json,os,shutil,subprocess,sys,tempfile,importlib
from pathlib import Path
batch=Path(sys.argv[1]); label=sys.argv[2]
sys.path.insert(0,str(batch))
import job_support as H, stage_job as S
_,_,NS,J=H.native(str(batch/'reference/sj/orch_cd/evalx/work/milestone'))
config=json.loads((batch/'a.json').read_text())
root=Path(tempfile.mkdtemp(prefix='k1b3_',dir='/tmp'))
for n in ('sj','fsw','m/ap','project','cache','temp','home'): (root/n).mkdir(parents=True)
NS.physical(root,config['logical_run']).mkdir(parents=True)
shutil.copy('/usr/bin/bwrap',root/'bwrap')
hostpool=Path(tempfile.mkdtemp(prefix='k1b3pool_',dir='/tmp')); hostcfg=Path(tempfile.mkdtemp(prefix='k1b3cfg_',dir='/tmp'))
argv=S.namespace(root,config)
pool_root=str(Path(config['pointer']).parent); g=config['assets']['gcloud_config']
out=[]; i=0
while i<len(argv):
    if argv[i] in('--bind','--ro-bind') and i+2<len(argv) and argv[i+1]==argv[i+2] and argv[i+1] in(pool_root,g):
        out+=[argv[i], str(hostpool if argv[i+1]==pool_root else hostcfg), argv[i+2]]; i+=3
    else: out.append(argv[i]); i+=1
test=f"""set -e; touch {pool_root}/w && echo pool_writable; touch {g}/w && echo gcloud_writable; if touch /project/community/jjyeung/x 2>/dev/null; then echo project_WRITABLE; else echo project_read_only; fi; touch {config['logical_run']}/w && echo run_writable"""
r=subprocess.run(out+['/bin/sh','-c',test],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
print(label,'pool/gcloud bind kinds:',[out[k] for k in range(len(out)) if k+2<len(out) and out[k+2] in(pool_root,g)])
print(r.stdout.strip()); print('rc=%d'%r.returncode)
print('host files:',sorted(os.listdir(hostpool)),sorted(os.listdir(hostcfg)))
