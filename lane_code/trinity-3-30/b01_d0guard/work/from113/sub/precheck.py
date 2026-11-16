import sys,json
from pathlib import Path
sys.path[:0]=['/scratch/jjyeung/orch_cd/evalx/work/milestone/orchard_native','/scratch/jjyeung/orch_cd/evalx/work/milestone']
import native_common as C, native_launcher as N, native_local_check as I
d=Path(sys.argv[1])
config=C.load(d/'CONFIG.json');family=C.load(d/'FAMILY.json');review=C.load(d/'REVIEW.json');order=(d/'ORDER.md').read_bytes()
C.admit(config,family,review);C.validate_order(order.decode(),config)
for field,name in (('family','FAMILY.json'),('review','REVIEW.json')):
    assert C.sha(d/name)==config[field]['sha256']
assert C.sha(d/'ORDER.md')==config['authorization']['orch_order']['sha256']
frozen=dict(family,bytes=(d/'FAMILY.json').read_bytes())
N.validate_batch((d/'BATCH.sh').read_text(),config,frozen,(d/'REVIEW.json').read_bytes(),order)
print('admit/order/batch OK; argv',N.submit_argv(config))
try:
    I.admit(d,config,family,N.batch_files(config,frozen,(d/'REVIEW.json').read_bytes(),order)); print('local_check admit OK')
except Exception as e: print('local_check admit FAILED:',type(e).__name__,str(e)[:600])
