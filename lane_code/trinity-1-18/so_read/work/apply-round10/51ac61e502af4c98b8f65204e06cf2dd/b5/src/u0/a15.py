"""Generate a reviewable array command and script; never invoke the scheduler."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys


def validate_policy(policy,shards,seconds):
    # An owner must approve the exact partition and lifetime budget. No policy
    # is assumed from the availability of a partition or a scheduler flag.
    if not isinstance(policy,dict) or policy.get('approved') is not True:
        raise ValueError('Array policy requires explicit owner approval')
    if policy.get('partition')!='preempt':raise ValueError('Unsupported array partition')
    attempts=policy.get('max_attempts')
    if type(attempts) is not int or not 1<=attempts<=4:raise ValueError('Invalid attempt bound')
    if type(shards) is not int or not 1<=shards<=4:raise ValueError('Invalid shard count')
    if type(seconds) is not int or seconds<2400:raise ValueError('Require at least 40 minutes')
    budget=policy.get('gpu_seconds')
    if type(budget) is not int or not 0<budget<=18000 or shards*seconds*attempts>budget:
        raise ValueError('Array exceeds approved lifetime GPU-hour budget')
    return attempts


def submission(token,config,python,source,config_path,*,enabled=False):
    if enabled is not True:raise ValueError('Array generation is OFF')
    from orchard_h10.common import submit_argv,opaque
    from a9 import validate_config,opaque_path
    validate_config(config)
    if not all(opaque_path(p) for p in (python,source,config_path)):
        raise ValueError('Array requires approved neutral staged paths')
    pin=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    count=config['shards'];seconds=config['attempt_seconds']
    attempts=validate_policy(config.get('policy'),count,seconds)
    wall=f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}'
    argv=submit_argv(token,1,wall)
    argv=[v.replace('--partition=general','--partition=preempt')
          .replace('--no-requeue','--requeue').replace('--signal=B:USR1@1800','--signal=B:USR1@900')
          for v in argv]
    argv+=['--array=0-'+str(count-1)+'%'+str(count)]
    # exec-style forwarding lets the reader drain at its existing deadlines.
    # Exit 75 requests a bounded retry; all other failures remain failures.
    script='''#!/bin/bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
if (( ${SLURM_RESTART_COUNT:-0} >= LIMIT )); then exit 75; fi
trap 'kill -USR1 "$pid" 2>/dev/null || true' USR1 TERM INT
rc=0
COMMAND &
pid=$!
while true; do
    wait "$pid" && rc=0 || rc=$?
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
done
if (( rc == 75 && ${SLURM_RESTART_COUNT:-0} + 1 < LIMIT )); then
    scontrol requeue "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
    exit 0
fi
exit "$rc"
'''.replace('LIMIT',str(attempts)).replace('COMMAND',shlex.join([
        'nice','-n','10',python,'-I','-s','-B',str(Path(source)/'u0/a14.py'),config_path,'--enable-array','--config-sha256',pin]))
    opaque(argv);opaque([script])
    return dict(argv=argv,script=script,config_sha256=pin)


def main():
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--out',required=True)
    p.add_argument('--token',required=True);p.add_argument('--python',required=True)
    p.add_argument('--source',required=True);p.add_argument('--staged-config',required=True)
    p.add_argument('--enable-array',action='store_true');a=p.parse_args()
    source=Path(__file__).resolve().parent.parent
    sys.path[:0]=[str(source/'u0'),str(source)]
    from a9 import read_wire
    result=submission(a.token,read_wire(json.loads(Path(a.config).read_bytes())),a.python,a.source,
                      a.staged_config,enabled=a.enable_array)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    (out/'0.sh').write_text(result.pop('script'))
    (out/'0.json').write_text(json.dumps(result,sort_keys=True)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
