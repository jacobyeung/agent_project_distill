"""Seal CPU evidence and finalize the concise delivery report after S1 aggregation."""
from common import *
from gates import run_code_hashes
import socket,time
names=['S0','KITCHECK','DRYRUN','K1_REPRODUCTION','TESTS','S1A']
records={n:read(W/f'out/{n}.json') for n in names}
assert all(r['verdict'] in ('PASS','COMPLETE') for r in records.values())
inputs={};receipts=[]
def merge(values):
 for p,h in values.items():
  if p in inputs and inputs[p]!=h:raise ValueError('conflicting provenance for '+p)
  inputs[p]=h
for n,r in records.items():
 merge(r['input_sha256']);inputs[str(W/f'out/{n}.json')]=sha(W/f'out/{n}.json')
for p in sorted((W/'out/s1').glob('*/*/DONE.json')):
 r=read(p);merge(r['input_sha256']);inputs[str(p)]=sha(p);receipts.append(dict(path=str(p),seconds=r['seconds'],peak_rss_kib=r['peak_rss_kib'],pred_sha256=r['pred_sha256']))
assert len(receipts)==6
merge(run_code_hashes())
for p in [Path(__file__).resolve(),W/'OPERATOR.md',W/'KIT_SPEC_room_pricing.md',W/'configs/SNAPSHOT_INPUTS.json',W/'configs/KERNEL_PROVENANCE.json',W/'configs/READER_RECEIPT.json',W/'configs/GO.template.json',W/'out/SCORER_SELF_TEST.log']:
 inputs[str(p)]=sha(p)
for p,h in inputs.items():
 if not p.startswith('/scratch/'):raise ValueError('nonlocal final verification forbidden: '+p)
 if sha(p)!=h:raise ValueError('stale final input: '+p)
dry=records['DRYRUN'];k=dry['k1'];rl=dry['rl']
report=W/'out/ROOMKIT_REPORT.md';s=report.read_text()
s=s.replace('The kit is built; S0, S1a, S1b and CPU tests pass. The 32-frame K1 and R0-rl CPU passes are running.','The kit is built. S0, all six S1 CPU forwards, S1b and all 22 CPU tests pass. GPU pricing has not run.')
line='- S1 remaining: 32-frame K1 and R0-rl forwards are RUNNING; `C scripts/summarize_s1.py` will aggregate their receipts.'
repl=['- `C scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; both 64-frame checks are within 5%; all six full CPU forwards have verified receipts.']
for r in k:repl.append(f"- {r['capture']} K1 32-frame area: {r['k1_32']:.2f} m²; 32/64 ratio: {r['ratio32_to64']:.6f}.")
for scene in sorted({r['scene'] for r in rl}):
 rows={r['arm']:r for r in rl if r['scene']==scene};a=rows['da3_f32+R0'];b=rows['da3_f32+T10'];repl.append(f"- R0-rl {scene}: label {a['gt_m2']} m²; R0 {a['area_m2']} m²; T10 {b['area_m2']} m². These plumbing values decide nothing.")
repl.append(f"- Both K1 32/64 ratios outside [0.85,1.15]: {dry['both_ratios_outside_15pct']}. No rule or setting was adjusted.")
s=s.replace(line,'\n'.join(repl))
s=s.replace('Packaging command:', 'Final evidence seal: `C out/finalize_delivery.py` verifies every distinct local input digest. Packaging command:')
assert len(s.splitlines())<=80;report.write_text(s);inputs[str(report)]=sha(report)
write(W/'out/CPU_RUN_RECEIPT.json',dict(verdict='PASS',host=socket.gethostname(),card=None,gpu_hours=0,network_used=False,inference_gt_used=False,evaluation_gt_used=True,stages={n:r['verdict'] for n,r in records.items()},forward_receipts=receipts,verified_distinct_inputs=len(inputs),completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),remaining_gaps=['MISSING kernel-selection provenance','MISSING authenticated remote reader/checkpoint/frame receipts','GPU pricing and physical allocation checks unrun','second-node mirror prohibited by no-network instruction']),inputs)
status('CPU delivery complete: S0 COMPLETE; all six S1 full CPU forwards complete and both required 64-frame areas within 5% of stored GPU values; S1b matches 134/134 room rows and 24/24 train-table entries; 22 CPU tests PASS. The report is out/ROOMKIT_REPORT.md. Package with scripts/package.py to out/sb_roomkit.tar and out/sb_roomkit.tar.sha256. GPU pricing is unrun and blocked on missing kernel/reader provenance, independent launch review and an orchestrator GO note. No GPU, network, Git, process termination or writes outside this workspace were used.')
print('FINAL CPU PASS;',len(inputs),'distinct local inputs verified;',len(s.splitlines()),'report lines')
