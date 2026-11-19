"""Cont_ops handoff: preflight, OFF prefix read, archive, and original unpack validation."""
from pathlib import Path
import argparse
import json
import secrets
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package');parser.add_argument('card')
    parser.add_argument('--items',type=int,default=50)
    a=parser.parse_args(argv)
    if not 1<=a.items<=636:raise Refusal('--items must be in 1..636')
    target_host();root=package_root(a.package);card=a.card
    out=root.parent/'runs'/('a'+secrets.token_hex(8))
    command=['bash',str(HERE/'run228.sh'),str(root),card,str(out),'--items',str(a.items)]
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
