"""Subprocess receipt protocol fixture; no backend/model execution."""
from pathlib import Path
import argparse
import sys,time
K=Path(__file__).resolve().parents[1]/'guard_kit';sys.path.insert(0,str(K))
from guard_core import read,write,sha
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--role',required=True);p.add_argument('--fail',action='store_true');a=p.parse_args()
d=Path(a.out);label='PROOF' if a.role=='proof' else 'CANARY'
write(d/(label+'.json'),dict(status='FAIL' if a.fail else 'PASS',fixture=True))
write(d/(label+'.ready.json'),dict(path=str(d/(label+'.json'))))
end=time.monotonic()+10
while not (d/(label+'.ack.json')).exists():
 if time.monotonic()>end:raise TimeoutError('No acknowledgement')
 time.sleep(.05)
if read(d/(label+'.ack.json'))!=dict(status='PASS',sha256=sha(d/(label+'.json'))):raise ValueError('Wrong acknowledgement')
if a.fail:sys.exit(1)
if a.role=='candidate':write(d/'TAIL_STARTED.json',dict(after_ack=True))
