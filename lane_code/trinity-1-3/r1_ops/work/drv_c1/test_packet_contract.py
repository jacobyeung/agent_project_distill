"""Run the sealed CPU-proof binder against the local unit-bound READY fixture."""
import json,subprocess,sys,tempfile
from pathlib import Path
from packet_config import PINS,fixture
W=Path(__file__).resolve().parent;K=Path(sys.argv[1]).resolve();B=fixture();T=Path(tempfile.mkdtemp(prefix='contract_p5_',dir=W))
assert K.is_relative_to(W) and K.name=='derived_ready'
args=[sys.executable,'-B',str(B/'p.py'),'--kit',str(K),'--bundle',str(B),'--binding',str(B/'BINDING.json')]
for part in ('general','bootstrap'):
 out=T/(part+'.json')
 r=subprocess.run(args+['--partition',part,'--out',str(out)],capture_output=True,text=True)
 assert r.returncode==0,r.stderr
 record=json.loads(out.read_text())
 assert record['partition']==part and record['identity']==PINS['identity'] and record['run_key']==PINS['run']
r=subprocess.run(args+['--partition','advanced','--out',str(T/'advanced_refused.json')],capture_output=True,text=True)
assert r.returncode and 'Proof partition is not authorized' in r.stderr
assert not (T/'advanced_refused.json').exists()
print('PASS C proof refuses advanced')
p=K/'k/selection_equality.json';raw=p.read_bytes()
try:
 value=json.loads(raw);value['native_unit_regeneration_executed']=False;p.write_text(json.dumps(value))
 r=subprocess.run(args+['--partition','general','--out',str(T/'refused.json')],capture_output=True,text=True)
 assert r.returncode!=0 and 'Native unit selection regeneration required' in r.stderr
 assert not (T/'refused.json').exists()
finally:p.write_bytes(raw)
print('PASS sealed p.py binds both partitions to packet C and refuses absent native unit regeneration')
