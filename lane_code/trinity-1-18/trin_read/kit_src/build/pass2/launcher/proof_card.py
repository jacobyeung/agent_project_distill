"""Card boundary for a CPU Slurm proof; retain the actual command evidence."""
import os
import subprocess
import time


def card(require_empty=False):
    observations=[]
    for query in ('--query-gpu=index,uuid,name,memory.used,utilization.gpu',
                  '--query-compute-apps=gpu_uuid,pid,used_memory'):
        argv=['nvidia-smi',query,'--format=csv,noheader,nounits']
        try:
            result=subprocess.run(argv,capture_output=True,text=True,timeout=30)
            observations.append(dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        except (OSError,subprocess.TimeoutExpired) as error:
            observations.append(dict(argv=argv,error_type=type(error).__name__,error=str(error),
                stdout=str(getattr(error,'stdout','') or ''),stderr=str(getattr(error,'stderr','') or '')))
    return dict(mode='proof',substitution='H100 query/check only',require_empty=require_empty,
        utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),job=os.environ.get('SLURM_JOB_ID'),
        hostname=os.uname().nodename,observations=observations,
        nvidia_smi='\n'.join(o.get('stdout','')+o.get('stderr','')+o.get('error','') for o in observations))
