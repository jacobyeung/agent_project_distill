import json, sys, time
from pathlib import Path
W = Path(sys.argv[1])
sys.path.insert(0, str(W/'tree'))
from student_pilot.p3_provenance import write, file_pin
from student_pilot import carrier_c1_run as run
seal = json.loads((W/'dec/7.json').read_text())
seal['archive']['path'] = str(W/'kit_orig/n_go'/seal['archive']['path']) if not Path(seal['archive']['path']).is_absolute() else seal['archive']['path']
p = W/'fx/code.json'
if not p.exists(): write(p, seal)
t = time.time()
print(seal['schema'], seal['archive'])
print('commit', run.authenticate(dict(code=file_pin(p))), round(time.time()-t, 2), 's')
