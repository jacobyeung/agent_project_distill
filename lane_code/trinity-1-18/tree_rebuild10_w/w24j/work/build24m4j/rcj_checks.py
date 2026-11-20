from common import *
import subprocess,ast
p=L/'out/rcj/rcj.sh';s=p.read_text();assert '#SBATCH -p preempt' in s and '--gres' not in s
for t in ('--cpus-per-task=16','--mem=128G','--time=02:00:00','--no-requeue','--job-name=JOBNAME_PLACEHOLDER','/j/%j.log','/j/%j.err'):assert t in s,t
subprocess.run(['/bin/bash','-n',str(p)],check=True)
compile((L/'out/rcj/x.py').read_text(),str(L/'out/rcj/x.py'),'exec')
assert J.sha(D/'p_tree/launch_s1/b/s.py')==J.load(kit('qd')/'k/p.json')['p_files']['b/s.py']
assert sum(p.stat().st_size for p in (L/'out/rcj').iterdir())<2_000_000
p=L/'out/rcj/x.py';s=p.read_text().replace("        for name, h in model['files'].items():", "        self.revision = model['base_identity']\n        for name, h in model['files'].items():")
s=s.replace("if m.isfile() and '/snapshots/' in m.name and m.name.endswith('/'+name)","if m.isfile() and '/snapshots/'+self.revision+'/' in m.name and m.name.endswith('/'+name)")
s=s.replace("    cmd = ['bwrap', '--ro-bind', '/', '/',", "    pin = z.load(Path(kit)/'k/l.json')['bwrap']\n    binary = z.checked(pin['file'], pin['sha256'])\n    cmd = [str(binary), '--ro-bind', '/', '/',")
replace(p,s)
J.write(D/'RCJ_STATIC.json',dict(status='PASS',scheduler_syntax=True,required_directives=True,no_gpu=True,helper_bytes=sum(p.stat().st_size for p in (L/'out/rcj').iterdir()),staging_code_matches_kit_pin=True))
print('RCJ shell and staging code pins PASS')
