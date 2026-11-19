from pathlib import Path
import hashlib,json,sys,importlib.util
sys.path.insert(0,'kit/files');import count_guard as G
root=Path('/scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd')
files=[root/n for n in ('teacher.py','common.py','stub_tower.py','vendor/SAM3_RECEIPT.json','vendor/sam3_tower.py','vendor/sam_backend.py')]
G.write('kit/files/BACKEND_PINS.json',dict(inputs_sha256={str(p):G.sha(p) for p in files}))
p=Path('kit/files/count_guard.py');s=p.read_text()
s=s.replace("ITEM_SHA=", "AUTH_SHA='"+G.sha('kit/files/DEV_AUTHORIZATION.json')+"'\nMRA_SHA='"+G.sha('kit/files/official_vsi_mra.py')+"'\nITEM_SHA=",1)
s=s.replace("def pins():return", "def pins():\n for p,h in read(HERE/'BACKEND_PINS.json')['inputs_sha256'].items():\n  if sha(p)!=h:raise ValueError('backend source pin differs: '+p)\n return")
s=s.replace("('FROZEN_CONFIG.json','DEV_AUTHORIZATION.json','MRA_SOURCE.json')", "('FROZEN_CONFIG.json','DEV_AUTHORIZATION.json','MRA_SOURCE.json','BACKEND_PINS.json','MRA_BOUNDARIES.json')")
s=s.replace("p=scratch(p);m=read(p);auth=read(HERE/'DEV_AUTHORIZATION.json')", "p=scratch(p)\n if sha(HERE/'DEV_AUTHORIZATION.json')!=AUTH_SHA:raise ValueError('allowlist pin changed')\n m=read(p);auth=read(HERE/'DEV_AUTHORIZATION.json')")
s=s.replace("c=read(HERE/'FROZEN_CONFIG.json')", "if sha(HERE/'official_vsi_mra.py')!=MRA_SHA:raise ValueError('official metric source changed')\n c=read(HERE/'FROZEN_CONFIG.json')")
p.write_text(s)
# Golden boundary expectations use the original pinned source, not the kit wrapper.
source=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1/evalpath/official.py')
sp=importlib.util.spec_from_file_location('pinned_original',source);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
import numpy as np
rows=[]
for threshold in [.5+i*(.95-.5)/9 for i in range(10)]:
 for sign in (-1,1):
  p=1+sign*(1-threshold)
  for x in (np.nextafter(p,-np.inf),p,np.nextafter(p,np.inf)):
   rows.append(dict(pred=float(x),truth=1,expected=mod.official_mra(float(x),1),threshold_hex=threshold.hex()))
G.write('kit/files/MRA_BOUNDARIES.json',dict(cases=rows,inputs_sha256={str(source):G.sha(source),'finish_pins.py':G.sha('finish_pins.py')}))
p=Path('kit/files/score_count_pricing.py');s=p.read_text();start=s.index('    # Independent numpy');end=s.index('    rows=[*G.items',start)
s=s[:start]+'''    # Golden values come from N's pinned source, including adjacent floating-point values.
    comparisons=0
    for case in G.read(G.HERE/'MRA_BOUNDARIES.json')['cases']:
        assert mra(case['pred'],case['truth'])==case['expected'],case
        comparisons+=1
'''+s[end:];p.write_text(s)
p=Path('kit/files/run_count_teacher.py');s=p.read_text().replace("Checked().check()\n   d=out", "Checked().check()\n   result['inputs_sha256']={str(a.manifest):G.sha(a.manifest),**G.pins()}\n   d=out");p.write_text(s)
