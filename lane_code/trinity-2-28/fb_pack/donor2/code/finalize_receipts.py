from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Keep direct execution dependencies, not unrelated report helpers discovered by glob.
keep={
'EVIDENCE_RUNS.json':{'run_evidence.py','run_unit.py','k1_fixture.py','run_export_check.py','adversarial_checks.py','absent_parity.py','parity_full.py'},
'SHORT_CHECK_RUNS.json':{'run_short_checks.py','environment.py','base_negative.py','run_focused.py'}}
for name,names in keep.items():
 p=O/name;value=json.loads(p.read_text());pins=value['input_sha256'];selected={}
 for key,h in pins.items():
  q=Path(key)
  if q.is_relative_to(W/'code') and q.name not in names:continue
  assert sha(q)==h,key
  selected[key]=h
 selected[str(Path(__file__).resolve())]=sha(__file__)
 value['input_sha256']=selected;value['receipt_command']='python code/finalize_receipts.py'
 p.write_text(json.dumps(value,indent=2)+'\n')
