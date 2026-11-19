import os
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
from common import *
from e2e_reader.geometry import from_npz
from replay import price,load_selector
c=manifest()['captures'][0]
g=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz')
cache=read_json(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json')
print('selector loading',flush=True);head=load_selector();print('replay start',flush=True)
r=price(c,g,cache,32,head=head)
write_json(ROOT/'out/REPLAY_SMOKE.json',dict(status='PASS',rows=r));print([(x['row_id'],x['response']) for x in r],flush=True)
