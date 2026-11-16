import json,os,signal,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parents[1];PY='/scratch/jjyeung/envs/p1cpu/bin/python';case=sys.argv[1]
base=H/'evidence/cpu'/case;base.mkdir(exist_ok=False)
kh=base/'kit';run=base/'run';slots=base/'slots'
for p in [kh/'b',kh/'k',kh/'o',run,slots,base/'tmp']:p.mkdir(parents=True,exist_ok=True)
for n in ['r.sh','h.py','v.py','q0.py','sg.py']:(kh/'b'/n).write_bytes((H/'build/fx/b'/n).read_bytes())
for n in ['a.py','g.py']:(kh/'b'/n).write_text('pass\n')
(kh/'b/p0.sh').write_text('exit 0\n');(kh/'b/r8.py').write_text('print("t")\n')
(kh/'b/r.sh').write_text((kh/'b/r.sh').read_text().replace('export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}', 'export TK_JOBDIR="$H1_PACKET/evidence/cpu/signal/tmp/job"'))
(kh/'job.sh').write_bytes((H/'build/fx/job.sh').read_bytes())
(kh/'b/i.py').write_bytes((H/'rv/rv_supervisor.py').read_bytes());(kh/'b/w.py').write_bytes((H/'rv/rv_cpu_rank.py').read_bytes())
(kh/'k/launch.json').write_text(json.dumps(dict(run_directory=str(run))))
# Actual bwrap user namespace, no PID namespace; the run inode is writable inside it.
(kh/'b/c.sh').write_text(f'''K=8865619b
HM="$HX"; X="$HX"; PILOT_VENV=/scratch/jjyeung/envs/p1cpu
function tk_stage {{ :; }}
function tk_env {{ export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1; }}
function tk_pythonpath {{ :; }}
function tk_step {{ printf '%s\\n' "$*"; }}
function tk_persist_small {{ :; }}
function tk_persist_exports {{ :; }}
function tk_bwrap {{ BW=(/usr/bin/bwrap --ro-bind / / --dev-bind /dev /dev --proc /proc --bind "{H}" "{H}" --unshare-user --uid "$(id -u)" --gid "$(id -g)"); }}
''')
# Keep the shipped wrapper's launch/trap/wait and complete slot-copy suffix exactly.
s=(H/'runtime/jb.sh').read_text();newest=s[s.index('newest()'):s.index('mkdir -p /tmp')]
suffix=s[s.index('( [[ -f $RS/binding.json ]'):]
wrapper=f'''#!/bin/bash
set -uo pipefail
export TK_JOB_START="$(date +%s)"
KH={kh}; RUN={run}; RS={slots}; LOG=$KH/o/${{SLURM_JOB_ID}}.w.steps
step() {{ printf '%s | %s\\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }}
'''+newest+suffix
(base/'jb.sh').write_text(wrapper)
env=dict(os.environ,H1_PACKET=str(H),CPU_RUN=str(run),CPU_CASE=case,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',SLURM_JOB_ID='991' if case in ('signal','fileonly') else '992',SLURM_JOB_NUM_NODES='1',SLURM_GPUS_ON_NODE='0',TMPDIR=str(base/'tmp'),STUDENT_PRESERVE_CHECKPOINTS='1')
with (base/'chain.log').open('w') as log:
 p=subprocess.Popen(['/bin/bash',str(base/'jb.sh')],env=env,stdout=log,stderr=subprocess.STDOUT)
 if case in ('signal','fileonly'):
  end=time.monotonic()+150
  while not all((run/f'ready{i}').exists() for i in range(4)):
   if p.poll() is not None:raise RuntimeError('chain exited: see '+str(base/'chain.log'))
   if time.monotonic()>end:raise RuntimeError('chain readiness timeout; inspect live job; no relaunch')
   time.sleep(.25)
  os.kill(p.pid,signal.SIGUSR1)
  end=time.monotonic()+10
  while not (run/'stop.991.request').exists():
   if time.monotonic()>end:raise RuntimeError('stop marker missing')
   time.sleep(.05)
  (run/'release').write_text('go\n')
 rc=p.wait(timeout=500)
record=dict(case=case,exit=rc,bwrap=True,signal_target='batch shell only' if case in ('signal','fileonly') else None,relay_suppressed=(run/'relay_suppressed').exists(),ranks=[json.loads((run/f'rank{i}.json').read_text()) for i in range(4)],slot=json.loads((slots/'A.json').read_text()))
assert rc==0 and record['slot']['verified'] is True
assert (run/('m3' if case in ('signal','fileonly') else 'm200')/'artifact.json').is_file()
if case not in ('signal','fileonly'):assert (run/'m100/artifact.json').is_file()
(base/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
