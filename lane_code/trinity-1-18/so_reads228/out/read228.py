"""Cont_ops handoff: preflight, full OFF read, archive, and original unpack validation."""
from pathlib import Path
import json
import secrets
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def main():
    if len(sys.argv)!=3:raise Refusal('Usage: read228.sh <package> <card>')
    target_host();root=package_root(sys.argv[1]);card=sys.argv[2]
    out=root.parent/'runs'/('a'+secrets.token_hex(8))
    command=['bash',str(HERE/'run228.sh'),str(root),card,str(out)]
    rc=subprocess.run(command).returncode
    # Even an OOM/partial return can be inspected by the original unpacker, if it has a started journal.
    result=out/'RESULT.json'
    if result.is_file():
        proof=read(result)
        unpack=subprocess.run([sys.executable,'-I','-s','-B',str(HERE/'unpack228.py'),'--operator',str(root),
            '--archive',proof['archive'],'--exit',proof['exit'],'--out',str(out/'accepted')],capture_output=True,text=True)
        write(out/'UNPACK.json',dict(returncode=unpack.returncode,stdout=unpack.stdout,stderr=unpack.stderr))
        if unpack.returncode:
            print(unpack.stderr,file=sys.stderr);return rc or 2
        handoff=json.loads(unpack.stdout.strip().splitlines()[-1])
        print(json.dumps(dict(**handoff,run_returncode=rc,result=str(result)),sort_keys=True))
    return rc

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError) as e:print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
