"""Validate the diagnosed repairs, stage empty kits, and run a fresh final pass."""
import json,os,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
py=[sys.executable,'-I','-s','-B']
state=json.loads((B/'FINAL_PASS.json').read_text())
if any(r['status']=='running' for r in state):raise SystemExit('The prior frozen pass must finish first')
for name in ('SUITE_COMPARISON.json','CHANGED_COVERAGE.json','GAPS.json'):
 p=B/name
 if p.exists():(B/('DIAGNOSTIC_'+name)).write_bytes(p.read_bytes())
env={**os.environ,'R2_TREE':str(L/'work/tree_r1'),'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'0','R2_SUITE_GROUP':'','R2_PACKAGE_MEMBERS':''}
names=['tests.test_r2_build8_frames','tests.test_carrier_c1_single_image.SingleImageTests.test_single_image_marker_does_not_relax_video_or_mask_guards']
with (B/'final_repairs.log').open('w') as f:
 result=subprocess.run(py+[str(B/'test_runner.py'),str(B/'proofs/final_repairs'),*names],env=env,cwd=L,stdout=f,stderr=subprocess.STDOUT)
if result.returncode<0:raise SystemExit('Repair proof was killed; stop without retry')
if result.returncode:raise SystemExit('Repair proof failed; inspect final_repairs.log')
current=B/'kits';prior=B/'kits_before_gap_closure'
if prior.exists():raise SystemExit('Repair staging already began; inspect its receipts')
if current.exists():current.rename(prior)
for name in ('build_kits','review_evidence','frame_review','resolve_resize','inference_inventory'):
 result=subprocess.run(py+[str(B/(name+'.py'))],env=env,cwd=L)
 if result.returncode<0:raise SystemExit('A preparation process was killed; stop without retry')
 if result.returncode:raise SystemExit('Preparation failed: '+name)
env['B8_KEEP_FINAL_KITS']='1'
with (B/'STATUS.md').open('a') as f:f.write('\nThe single-image message repair and native malformed-frame/pose/FoV cases passed (`proofs/final_repairs/results.json`). Both kits were rebuilt from empty, A2 first. A fresh frozen pass follows.\n')
result=subprocess.run(py+[str(B/'final_pass.py')],env=env,cwd=L)
if result.returncode<0:raise SystemExit('The final-pass process was killed; stop without retry')
raise SystemExit(result.returncode)
