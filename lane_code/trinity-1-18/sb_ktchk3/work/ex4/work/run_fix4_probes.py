"""Run the reviewer probes with workspace-only receipts and input hashes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
name=sys.argv[1]
assert name in ('plant','plant2')
p=ROOT/'work/ktchk2_probes'/(name+'.py')
sha(__file__);sha(p);code_pins()
s=p.read_text()
if name=='plant':
    old="Path('/scratch/jjyeung/orch_n30/sb_ktchk/work/plant_results.json').write_text(json.dumps(RES, indent=1))"
else:
    old='OUTFILE.write_text(json.dumps(RES, indent=1))'
assert s.count(old)==1
s=s.replace(old,'pass # The wrapper writes the receipt inside this workspace.')
s=s.replace('hashlib.sha256(p.read_bytes()).hexdigest()', 'sha(p)')
ns=dict(__name__='__main__',__file__=str(p))
exec(compile(s,str(p),'exec'),ns)
results=ns['RES'];code_pins()
if name=='plant':
    checks=[r for r in results if 'returncode' in r]
    assert all(r['returncode']!=0 and not r['written'] for r in checks)
    forge=results[-1]
    assert all(forge[k]['returncode']!=0 and forge[k]['refused'] for k in ('before_plant','after_plant'))
    summary=dict(planted_files_refused=len(checks)+1,synthetic_gain_comparisons=results[-2]['verdicts'],bound_B_checks='out/FIX4_plant2.json')
else:
    checks=[r for r in results if r.get('expect')=='refuse']
    assert all(r['ok'] and r['returncode']!=0 and not r['written'] for r in checks)
    assert next(r for r in results if r['attempt']=='duplicate_rows_appended')['ok']
    assert next(r for r in results if r['attempt']=='A_rows_roundtrip_real_price_rows')['ok']
    assert next(r for r in results if r.get('expect')=='proceed')['returncode']==0
    summary=dict(planted_files_refused=len(checks),duplicate_rows_refused=True,roundtrip=True,informational_controls=[r['attempt'] for r in results if r.get('expect')=='info'])
write_json(ROOT/'out'/('FIX4_'+name+'.json'),dict(status='PASS',command='bash scripts/cpu.sh work/run_fix4_probes.py '+name,adaptation='Only the result destination and input-hash recording change; every probe executes.',summary=summary,results=results))
print(json.dumps(summary))
