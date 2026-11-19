from common import *
import os,subprocess,shlex,time,signal,base64,json
F=D/'discovery';node=F/'node';kit=F/'kit';project=F/'project';target=project/'n';boundary=F/'boundary.py'
outer=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--ro-bind','/scratch','/scratch','--tmpfs','/tmp','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(F),str(F),'--bind',str(project),'/project']
inner=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(node),str(node),'--bind',str(node),'/tmp/q_22c714e1','--bind','/project/n/o/94/live','/project/n/o/94/live','--chdir','/tmp/q_22c714e1']
# Prove that the old destination fails, while the live child remains writable.
probe=F/'probe.py';probe.write_text("from pathlib import Path\nPath('/project/n/o/94/live/probe').write_text('ok')\ntry:Path('/project/n/o/94/routing_selection.json').write_text('{}')\nexcept OSError as e:assert e.errno==30\nelse:raise AssertionError('project is writable')\n")
subprocess.run(outer+inner+[sys.executable,'-B',str(probe)],check=True)
decoded=base64.b64decode(json.loads((L/'work/build24/kits/n/k/j.json').read_text())['payload']).decode()
start=decoded.index('set +e\n"${BW[@]}"');end=decoded.index('\n"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/d.py"',start)
tail=decoded[start:end].replace('/usr/bin/python3',shlex.quote(sys.executable)).replace('"$Q_KIT/b/a.py"',shlex.quote(str(boundary))+' "$Q_KIT/b/a.py"')
prefix='set -uo pipefail\nBW=('+shlex.join(inner)+')\nPILOT_VENV='+shlex.quote(str(Path(sys.executable).parent.parent))+'\nQ_KIT='+shlex.quote(str(kit))+'\nQ_ROOT='+shlex.quote(str(node))+'\nQ_NS=/tmp/q_22c714e1\nexport Q_MODE=r SLURM_JOB_ID=94\n'
script=F/'run.sh';script.write_text(prefix+tail.replace('exit \"$rc\"', '/usr/bin/python3 -B -I -s \"$Q_KIT/b/ep.py\" \"$Q_KIT\" \"$Q_ROOT\" 94 \"$rc\"; exit \"$rc\"')+'\n')
with (F/'shell.log').open('w') as log:
    p=subprocess.Popen(outer+['/bin/bash',str(script)],env={**os.environ,'TMPDIR':str(node/'tmp')},stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    while p.poll() is None:
        allocated=sum(x.stat().st_blocks*512 for x in D.rglob('*') if x.is_file() and not x.is_symlink() and x.stat().st_nlink==1)
        if allocated>175_000_000:
            os.killpg(p.pid,signal.SIGTERM);p.wait();raise RuntimeError('TEST_SPACE_GUARD:'+str(allocated))
        time.sleep(.5)
assert p.returncode==0,(p.returncode,(node/'q.log').read_text()[-4000:],(F/'shell.log').read_text())
value=J.load(node/'p/routing_selection.json');assert value==J.load(target/'o/94/routing_selection.json')
assert (target/'o/94/q.log').read_bytes()==(node/'q.log').read_bytes()
J.write(D/'MODE_R_TEST.json',dict(status='PASS',rows=value['rows'],regenerated_sha256=value['regenerated_sha256'],project_read_only=True,live_writable=True,publication_outside=True,returncode=p.returncode,scope='Native planner, staging validation, host checks and routing build; retained synthetic stores; tiny processor; hardlinked authenticated staging; P production equality requires Orchard.'))
print('mode r read-only project PASS',value['rows'],flush=True)
