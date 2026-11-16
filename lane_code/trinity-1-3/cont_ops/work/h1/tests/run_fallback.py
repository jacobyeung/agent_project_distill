import json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parents[1];base=H/'evidence/cpu'/sys.argv[1];base.mkdir(exist_ok=False)
kh=base/'kit';run=base/'run';slots=base/'slots'
for p in [kh/'o',run,slots,base/'tmp']:p.mkdir(parents=True,exist_ok=True)
(kh/'job.sh').write_text(f'#!/bin/bash\nexec /scratch/jjyeung/envs/p1cpu/bin/python -B {H}/tests/cpu_fallback.py\n')
s=(H/'runtime/jb.sh').read_text();newest=s[s.index('newest()'):s.index('# BEGIN directory preflight')];suffix=s[s.index('( [[ -f $RS/binding.json ]'):]
wrapper=f'''#!/bin/bash
set -uo pipefail
export TK_JOB_START="$(date +%s)"
KH={kh}; RUN={run}; RS={slots}; LOG=$KH/o/${{SLURM_JOB_ID}}.w.steps
step() {{ printf '%s | %s\\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }}
'''+newest+suffix
(base/'jb.sh').write_text(wrapper)
env=dict(os.environ,H1_PACKET=str(H),CPU_RUN=str(run),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',SLURM_JOB_ID='993',TMPDIR=str(base/'tmp'),S1_CPU_REHEARSAL='1',S1_REHEARSAL_ATTEMPT='993',STUDENT_PRESERVE_CHECKPOINTS='1')
with (base/'chain.log').open('w') as log:r=subprocess.run(['/bin/bash',str(base/'jb.sh')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
assert r.returncode==0,'see chain.log and w.steps'
record=dict(exit=r.returncode,run=json.loads((run/'result.json').read_text()),slot=json.loads((slots/'A.json').read_text()))
assert record['slot']['verified'] and record['slot']['step']==200
(base/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
