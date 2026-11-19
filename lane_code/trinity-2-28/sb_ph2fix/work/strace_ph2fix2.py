"""Trace the actual payload imports and launcher bootstrap; no GPU or network."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; KIT=ROOT/'sb_mask_phrase'
sys.path.insert(0,str(KIT/'part2'))
import launch_gpu as L
out=ROOT/'work/ph2rev_probes/strace_fixed';out.mkdir(exist_ok=True)
env=L.environment(KIT,out,'',4320,'pass',False)
for key in ('HOME','TMPDIR'): Path(env[key]).mkdir(parents=True,exist_ok=True)
code='import ssl, hashlib, torch; torch.set_num_threads(8); print(ssl.OPENSSL_VERSION, hashlib.sha256(b"probe").hexdigest(), torch.__version__)'
commands={
    'imports':[str(ROOT/'payload/environment/bin/python'),'-B','-c',code],
    'launcher_bootstrap':['bash',str(KIT/'part2/launch_gpu.sh'),'--help']}
records={}
for name,cmd in commands.items():
    log=out/(name+'.strace')
    command=['strace','-f','-yy','-s','4096','-e','trace=%file','-o',str(log),*cmd]
    result=subprocess.run(command,env=env,cwd=KIT,text=True,capture_output=True)
    text=log.read_text()
    bad=[line for line in text.splitlines() if re.search(r'(?:"|<)/(?:home(?:/|[">])|data[^/">]*(?:/|[">]))',line)]
    assert result.returncode==0,(name,result.stderr)
    assert not bad,bad[:10]
    records[name]=dict(command=command,returncode=result.returncode,nfs_touches=len(bad),stdout=result.stdout,trace=str(log))
paths=[Path(__file__),KIT/'part2/launch_gpu.py',KIT/'part2/launch_gpu.sh',ROOT/'payload/environment/ssl/openssl.cnf',ROOT/'payload/environment/bin/python',*out.glob('*.strace')]
record=dict(status='PASS',records=records,environment={k:env[k] for k in ('OPENSSL_CONF','PATH','HOME','CUDA_VISIBLE_DEVICES')},input_sha256={str(p):L.sha(p) for p in paths})
(ROOT/'out/STRACE_PH2FIX2.json').write_text(json.dumps(record,indent=1)+'\n')
print('PASS: payload ssl/hashlib/torch and launch_gpu.sh --help; /home and /data* touches = 0')
