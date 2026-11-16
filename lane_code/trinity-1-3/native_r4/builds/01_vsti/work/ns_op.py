import json,subprocess,uuid,os
B='/scratch/jjyeung/orch_n30/native_r4/builds/01_vsti'
n=json.load(open(B+'/out/rehearsal/NAMESPACE.json'))
cmd=n['command']; old=cmd[cmd.index('--dest')+1].split('/run/job')[0]
new=B+'/work/ns_op_'+uuid.uuid4().hex[:8]
for d in ('shm','tmp','cache','run'): os.makedirs(new+'/'+d)
cmd=[c.replace(old,new) for c in cmd]+['--fixture-tower']
open(B+'/work/ns_op_cmd.json','w').write(json.dumps(cmd))
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=1800)
open(B+'/work/ns_op.log','w').write(json.dumps(dict(rc=r.returncode,stdout=r.stdout[-3000:],stderr=r.stderr[-5000:],root=new)))
print(r.returncode, r.stderr[-1500:])
p=new+'/run/job/RESULT.json'
print(open(p).read()[:1500] if os.path.exists(p) else 'no result')
