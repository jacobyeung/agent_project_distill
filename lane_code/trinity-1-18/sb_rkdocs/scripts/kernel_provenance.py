"""Bind independent K1-train selection and disclose the benchmark-selected antecedent."""
from common import *
def main():
 result_path=W/'out/S1K_RESULTS.json';reg_path=W/'out/S1K_REGISTRATION.json';frozen_path=W/'configs/KERNEL_FROZEN.json'
 result=read(result_path);reg=read(reg_path);frozen=read(frozen_path)
 assert result['status']=='COMPLETE' and len(reg['captures'])==110
 assert len(set(reg['captures']))==110 and result['grid']==reg['grid']
 assert frozen['constants']==result['winner']==reg['grid'][result['winner_index']]
 ins={str(p):sha(p) for p in [Path(__file__).resolve(),result_path,reg_path,frozen_path,W/'vendor/room_kernel.py']}
 # Snapshot paths preserve the exact execution inputs even after launch code is finalized.
 snapshots={}
 for p,h in result['input_sha256'].items():
  path=Path(p)
  if path.parent in (W/'scripts',W/'vendor'):
   snap=W/'evidence/s1k_execution_code'/path.relative_to(W)
   assert sha(snap)==h,(snap,h)
   snapshots[p]=dict(file=str(snap),sha256=h);ins[str(snap)]=h
  else:
   assert sha(path)==h,path
   ins[p]=h
 for name in ['ROOM_HEAD_DESIGN_SOURCE.md','A0_AFTER_NATIVE_READ_DESIGN_20261116.md','COMPOSED_TRACES_COUNT_SIZE_ROOM_20261108.md','DESIGN_SOURCE_HASHES.json','room_v314.original.py']:
  p=W/'evidence'/name;ins[str(p)]=sha(p)
 old=reg['old_values'];same=old==frozen['constants']
 relation=dict(old_values=old,winner_equals_old=same,
  disclosure='ROOM_HEAD_DESIGN_20261119.md cites A0_AFTER_NATIVE_READ_DESIGN_20261116.md, which states that the room rule was chosen among five rules on 88 official VSI-Bench ScanNet items. These records do not establish clean independent selection of each of the four constants. The legacy values are not certified as benchmark-independent. S1k selects the deployed constants anew using only K1 training scores.',
  label_caveat='K1 ground-truth room labels were generated with the legacy room rule; independent K1 selection does not remove that label-definition inheritance.',
  grid_caveat='The preregistered grid includes the legacy tuple as requested; the grid is not claimed to be historically independent of the benchmark-derived rule family.')
 table=[dict(index=i,constants=r['constants'],mra=r['mra'],n=r['n']) for i,r in enumerate(result['result_table'])]
 write(W/'configs/KERNEL_PROVENANCE.json',dict(status='VERIFIED',selection_scope='K1 train only',benchmark_selected=False,
  authorized_by='pending orchestrator',kernel_sha256=sha(W/'vendor/room_kernel.py'),frozen_sha256=sha(frozen_path),constants=frozen['constants'],grid=reg['grid'],result_table=table,
  relation_to_benchmark_rule=relation,execution_code_snapshots=snapshots,command='bash scripts/cpu.sh scripts/s1k.py; bash scripts/cpu.sh scripts/kernel_provenance.py'),ins)
 report=['# Kernel provenance','',
  'Status: VERIFIED for the new K1-train selection. Authorization: pending orchestrator.',
  'The design record cites a five-rule selection on 88 official VSI-Bench ScanNet items; it does not prove a clean origin for each constant.',
  'S1k uses only the 110 K1 TRAINING room captures and stored dense-64 DA3 predictions, sampled at their 32 anchors through adapter.convert.',
  'The preregistered Cartesian grid is margin {0.05, 0.10} m × cell {0.05, 0.10} m × votes {1, 2} × closing {0.10, 0.20} m.',
  'The objective is mean per-item K1-train MRA; refusals score zero. Ties choose the first listed tuple.',
  f"Winner: {frozen['constants']}; K1-train MRA {table[result['winner_index']]['mra']:.6f}.",
  f'Legacy tuple: {old}. Winner equals legacy: {same}.',
  'K1 labels inherit the legacy kernel; this selection does not establish benchmark-independent labels or a new rule family.',
  f"Measured: {result['cpu_seconds']:.2f} CPU-seconds, {result['wall_seconds']:.2f} elapsed seconds; eight-thread limit; no new inference.",
  'Command: bash scripts/cpu.sh scripts/s1k.py > out/S1K.log 2>&1',
  'Receipt command: bash scripts/cpu.sh scripts/kernel_provenance.py',
  'Evidence: out/S1K_REGISTRATION.json, out/S1K_RESULTS.json, configs/KERNEL_FROZEN.json; every input has a SHA256.',
  'evidence/s1k_execution_code preserves the exact source hashes used during selection; execution_code_snapshots maps the recorded paths.',
  'The frozen kernel serves selection.py and price.py. reproduce.py checks the legacy kernel against its stored reference.',
  'The benchmark-origin disclosure is retained because the task explicitly requires it. No benchmark item or score was read for S1k.']
 assert len(report)<=30
 (W/'out/KERNEL_PROVENANCE_REPORT.md').write_text('\n'.join(report)+'\n')
 status('The reader receipt and new K1-train kernel provenance are VERIFIED. The kernel authorization remains pending orchestrator. S1c and R0-dev inference are unrun; all launch gates remain closed until an authorized immutable GO note and kernel approval exist.')
 print('KERNEL_PROVENANCE VERIFIED; authorization pending orchestrator')
if __name__=='__main__':main()
