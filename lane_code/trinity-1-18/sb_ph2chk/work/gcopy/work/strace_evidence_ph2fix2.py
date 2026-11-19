"""Record denied fresh ptrace honestly; audit supplied reviewer evidence and run actual imports."""
import json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];KIT=ROOT/'sb_mask_phrase';sys.path.insert(0,str(KIT/'part2'))
import launch_gpu as L
out=ROOT/'work/ph2rev_probes/strace_fixed'
env=L.environment(KIT,out,'',4320,'pass',False)
commands={
'imports':[str(ROOT/'payload/environment/bin/python'),'-B','-c','import ssl,hashlib,torch; torch.set_num_threads(8); print(ssl.OPENSSL_VERSION, hashlib.sha256(b"probe").hexdigest(), torch.__version__)'],
'launcher_bootstrap':['bash',str(KIT/'part2/launch_gpu.sh'),'--help']}
runs={}
for name,command in commands.items():
    r=subprocess.run(command,cwd=KIT,env=env,capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    runs[name]=dict(command=command,returncode=r.returncode,stdout=r.stdout)
trace=ROOT/'work/ph2rev_probes/strace_opensslfix.txt'
lines=trace.read_text().splitlines()
# Reviewer trace uses ordinary strace without -yy; count file paths in quoted arguments.
nfs=[l for l in lines if re.search(r'"/(?:home(?:/|")|data[^/\"]*(?:/|"))',l)]
assert not nfs,nfs[:10]
paths=[Path(__file__),ROOT/'work/strace_ph2fix2.py',ROOT/'out/strace_ph2fix2.log',trace,KIT/'part2/launch_gpu.py',KIT/'part2/launch_gpu.sh',ROOT/'payload/environment/bin/python',ROOT/'payload/environment/ssl/openssl.cnf']
record=dict(status='MISSING_FRESH_STRACE',fresh_trace=dict(status='MISSING',expected=str(out/'imports.strace'),reason='Sandbox denies PTRACE_TRACEME: Operation not permitted',attempt_log=str(ROOT/'out/strace_ph2fix2.log')),
            reviewer_trace=dict(status='PASS',path=str(trace),nfs_touches=len(nfs),scope='Supplied reviewer evidence, not a fresh trace of this build'),
            untraced_runs=runs,environment={k:env[k] for k in ('OPENSSL_CONF','PATH','CUDA_VISIBLE_DEVICES')},input_sha256={str(p):L.sha(p) for p in paths})
(ROOT/'out/STRACE_PH2FIX2.json').write_text(json.dumps(record,indent=1)+'\n')
print('Fresh strace MISSING (sandbox ptrace denial); reviewer fixed trace NFS touches 0; actual untraced imports and bootstrap PASS')
