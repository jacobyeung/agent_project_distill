"""Package the validated E-A CPU implementation and GPU hand-off."""
import ast,json,re,subprocess,tarfile
from pathlib import Path
from types import SimpleNamespace as NS
from provenance import sha256,write_json
from probe_common import ROOT,ARMS,gate,rules,RULES_PATH
from card import run as card

def main():
    out=ROOT/'out';rules()
    log=(out/'CPU_R3_FINAL.log').read_text()
    if not log.rstrip().endswith('OK'):raise ValueError('Final CPU suite did not pass')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    mutants=json.loads((out/'MUTATIONS_R3.json').read_text())
    if len(mutants)!=27 or not all(m['caught'] for m in mutants):raise ValueError('Reviewer fault set is incomplete')
    if not json.loads((out/'M13_CONTROL_R3.json').read_text())['passed']:raise ValueError('Benign M13 control failed')
    card(NS(results=str(out/'gpu_pending_r3'),availability=str(out/'AVAILABILITY.json'),out=str(out)))
    write_json(out/'SMOKE_STATUS.json',dict(status='PENDING_GPU',measurements={a:dict(status='pending',size_hw=size,peak_bytes=None,spatial_gate='PENDING',bf16_autocast='PENDING') for a,(_,size) in ARMS.items()},frames_per_arm=8,physical_gpu=7,host='trinity-1-18'))
    names=['DECISION_CARD.md','ARMS.md','DOWNLOADS.md','GPU_COMMAND.md','API.md','ONLINE_SCHEMA.md','RECORD.md','MEMORY_AUDIT.md','STAGING_INVENTORY.md','STAGING_INVENTORY.json','SAM_SOURCE_CHECK.json','run_EA_arm.sh','run_EA_phase.sh','WEIGHTS.example.json','WEIGHTS.gpu.json','room_gate.py','EVAL_ROOMS.json','EVAL_ROOMS.sha256','b2_manifest.jsonl','tuning_manifest.jsonl','MANIFEST_REPORT.json','g3t_taps.py','provenance.py','g3t_sparse.patch','PLAN.json','AVAILABILITY.json','SMOKE_STATUS.json','P0_CARD.json','P0_CARD.md','CPU_R3_FINAL.log','MUTATIONS_R3.json','M13_CONTROL_R3.json','M13_CONTROL_R3.log','MUTANTS_R3/M13.log','AREA_POOL_AUDIT.json','QWEN_PREFIX_PARITY_R2.json','SAM_REFERENCE_R2.json']
    excluded=('update_','revise_','fix_','run_mutants_r2')
    code=[p for p in (ROOT/'work').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.sha256') and not p.name.startswith(excluded) and '__pycache__' not in p.parts]
    for p in code:
        if p.suffix=='.py':ast.parse(p.read_text())
    files=sorted(set(code+[out/n for n in names]+list((out/'MUTANTS_R3').glob('*.json'))))
    listing={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in files}
    write_json(out/'FILES.json',dict(schema='own-probe-r3',files=listing,rules_sha256=sha256(RULES_PATH)))
    files.append(out/'FILES.json');archive=out/'own_probe_delivery_r3.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
        for p in files:tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    footprint=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    if footprint>300_000_000:raise ValueError('Folder exceeds 300 MB')
    stamp=subprocess.check_output(['date','-u','+%Y%m%dT%H%MZ'],text=True).strip()
    event=ROOT/'events'/f'{stamp}_RESULT_own_probe_r3.md'
    lines=[
      '`bash /scratch/jjyeung/orch_cd/own_probe/out/run_EA_phase.sh 7 1`',
      'Run in the allocated tmux session on trinity-1-18 after staging; phase 1 is A1, A7, A2.',
      'Phase 1 runs smoke, calibration/extraction, T1/T4 and all three readouts, then prints its provisional choice.',
      'The shared 240-minute ledger reserves 165 minutes for phase 1, including calibration and the third readout.',
      'The card prints every paired T1 interval; PENDING R2/R3 never suppress the provisional T1 choice.',
      'R1 compares each arm with A7; only an upper bound below −3 points fails parity. INCONCLUSIVE permits the pilot.',
      'T1/R3 choose selection and presence; R2 chooses masks. No point estimate can switch either route.',
      'Training-only channel statistics precede token LN; another LN follows channel averaging for every arm.',
      'The card shows standardized four taps, standardized final layer, and unstandardized four-tap control.',
      'Per-arm/tap native and head energy shares are instrumented; real-encoder measurements remain PENDING GPU.',
      'The real-frame CPU descriptor test rejects shifted, transposed and noise grids; every GPU provider must pass its own gate.',
      'Phase 2 requires phase-1 completion; outside extraction requires a pinned successful real-frame smoke.',
      'SAM smoke records actual bf16 autocast; launchers accept only the assigned physical GPU 7.',
      'Staging includes all three environments and G3T at source jjyeung_mdg_next/g3t and target jjyeung_evalx/g3t.',
      f'CPU suite: {count}/{count} PASS. Reviewer faults: 27/27 caught, 0 missed, 0 harness errors; serial targeted replay. Benign M13 stays green.',
      'Evidence: out/CPU_R3_FINAL.log, out/MUTATIONS_R3.json, out/DECISION_CARD.md, out/STAGING_INVENTORY.json.',
      'Hand-off: out/GPU_COMMAND.md; archive: out/own_probe_delivery_r3.tar.gz; pins: out/FILES.json.',
      'This lane ran no GPU, SSH, Git, network download, deletion or feature-cache write.',
    ]
    if len(lines)>20:raise ValueError('RESULT exceeds 20 lines')
    event.write_text('\n'.join(lines)+'\n')
    write_json(out/'DELIVERY.json',dict(schema='own-probe-r3',status='CPU_READY_GPU_PENDING',timestamp_utc=stamp,archive=dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha256(archive)),event=str(event),files_sha256=sha256(out/'FILES.json'),rules_sha256=sha256(RULES_PATH),authority_sha256=gate.authority_sha256(),tests=count,review_mutants_caught=27,review_mutants_missed=0,folder_bytes=footprint,unresolved=['Real-provider spatial gates and bf16 smoke pending GPU','Real per-arm channel energy shares pending GPU','Outside weights and O5 labels require staging','Phase-1 time estimate is unmeasured']))
    print(json.dumps(dict(event=str(event),archive_bytes=archive.stat().st_size,folder_bytes=footprint)))
if __name__=='__main__':main()
