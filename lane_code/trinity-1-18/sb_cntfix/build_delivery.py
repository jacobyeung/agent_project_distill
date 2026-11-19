"""Write the concise report and GPU decision from verified CPU artifacts."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'kit/files');import count_guard as G
R=Path.cwd();O=R/'out'
cfg=G.read(G.HERE/'FROZEN_CONFIG.json');metric=G.read(O/'METRIC_TEST.json');audit=G.read(O/'CPU_AUDIT.json');control=G.read(O/'CONTROL_TESTS.json');runtime=G.read(O/'RUNTIME_TESTS.json');deadline=G.read(O/'DEADLINE_TEST.json');stub=G.read(O/'STUB_SCORE.json');missing=G.read(O/'MISSING_INPUTS.json')
code=(G.HERE/'official_vsi_mra.py').read_text();fn=code[code.index('def official_mra'):].strip();got=hashlib.sha256(fn.encode()).hexdigest();expected=G.read(G.HERE/'MRA_UPSTREAM_PINS.json')['score_and_aggregate.py']['functions']['official_mra'];assert got==expected
G.write(O/'MRA_PIN_VERIFICATION.json',dict(matched=True,canonicalization='stripped function source text',expected_sha256=expected,actual_sha256=got,inputs_sha256={str(G.HERE/n):G.sha(G.HERE/n) for n in ('official_vsi_mra.py','MRA_UPSTREAM_PINS.json','MRA_SOURCE.json')}))
assert metric['stored_scores']==1605 and not metric['mismatches']
assert not audit['stored_metric_check']['mismatches']
assert stub['coverage']['with_teacher']==stub['coverage']['items']==385 and stub['stub']
assert control['passed']==34 and runtime['passed']==6 and deadline['status']=='time_cap'
assert cfg['training_decision']=='REJECT_ON_TRAINING'
assert not (G.LEDGER/'R0-dev-counting.json').exists() and not (G.LEDGER/'R0-dev-counting.consumed.json').exists()
ca=G.read(O/'CONTROL_AUDIT.json');assert ca['returncode']!=0 and ca['teacher_outputs']==0
rp=G.read(O/'STUB_REPLAY_TEST.json');assert rp['rejected'] and not rp['second_output_exists']
inputs={str(p):G.sha(p) for p in [G.HERE/'FROZEN_CONFIG.json',O/'METRIC_TEST.json',O/'CPU_AUDIT.json',O/'CONTROL_TESTS.json',O/'RUNTIME_TESTS.json',O/'DEADLINE_TEST.json',O/'STUB_SCORE.json',O/'MISSING_INPUTS.json',O/'CONTROL_AUDIT.json',O/'STUB_REPLAY_TEST.json',R/'build_delivery.py']}
G.write(O/'GPU_NEED.json',dict(gpu_needed=False,requested_gpu_hours=0,decision=cfg['training_decision'],reason='The K1-training-selected rule loses to the K1-training-frozen constant; the protocol prohibits a real dev registration.',selected_training_MRA=cfg['selected_train_MRA'],frozen_constant=cfg['best_const'],constant_training_MRA=cfg['constant_train_MRA'][str(cfg['best_const'])],paired_training_difference_CI=cfg['selected_minus_constant_CI'],real_R0_dev_registered=False,real_R0_dev_look_consumed=False,CPU_only=True,official_item_files_read=0,pilot_status='MISSING',limitations=['Five pilot artifacts and 64 fixture frames are unavailable; exact paths are in MISSING_INPUTS.json.','dev-S1 frame authority is MISSING and diagnostic only.','GPU availability and vnice executable were not checked.','A native GPU call can delay Python alarm delivery; no external GPU watchdog is claimed.'],inputs_sha256=inputs))
report='''# Counting kit: CPU controls pass; GPU launch rejected on training
The frozen K1-training decision is `REJECT_ON_TRAINING`; requested GPU time is zero.
No real R0-dev registration or look was consumed. No official item file was opened.

- `bash cpu.sh kit/files/freeze_training.py`: 24 rules, 202 train captures, 1,960 pairs, 196 large pairs.
- Training selects raw per-frame maximum, joint ≥0.35, and constant 6. MRA is 45.0 versus 53.877551; paired difference CI is [−15.674157, −2.425743]. The same command produces these values.
- Rules, thresholds, the decision, response, and row filter are frozen in `kit/files/FROZEN_CONFIG.json`. Training rejection disables the response and rows.
- `bash cpu.sh kit/files/score_count_pricing.py --selftest --items kit/files/COUNT_ITEMS_535.jsonl`: all 1,605 stored scores and 60 boundary cases pass. N's upstream function pin matches exactly (`MRA_PIN_VERIFICATION.json`).
- `bash cpu.sh audit_cpu.py`: zero stored-score mismatches; constant6=55.236220 and identity oracle=80.748031 on the 254-pair diagnostic overlap; GT frame maximum=48.300654 on all 306 large pairs. These diagnostics do not affect selection.
- `bash cpu.sh recompute_k1_references.py`: `K1_REFERENCE_RECOMPUTE.json` gives the corrected per-bin reference table and verifies that the training freeze did not change.
- The manifest command in `COMMANDS.md` verifies 3,136 frame hashes, 98 captures, and 464 prompts against the pinned allowlist.
- The full stub command in `COMMANDS.md` completes all 98 captures. `bash cpu.sh run_stub_score.py` verifies 385/385 items and rejects a second output path; scores remain `STUB_ONLY`.
- `STUB_SCORE_CATEGORY_ERRORS.json` reports category zero counts and item under/over errors. Multi-category items do not provide category-specific truth.
- `bash cpu.sh test_controls.py`: 34 checks pass, including atomic one-look races, unauthorized captures/paths, stale DONE fields, payload coverage, stub/real separation, and unrounded decisions.
- `bash cpu.sh test_runtime.py`: six checks pass for expired deadlines, cumulative budgets, abnormal restarts, changed bindings, and clean resumes.
- `bash cpu.sh test_deadline.py`: the in-flight CPU deadline exits with `time_cap`; no other process receives a signal.
- `bash cpu.sh audit_controls.py`: 98 invalid DONE markers produce a nonzero exit and zero teacher payloads. Both reviewer audits were rerun; their originals are retained under `review/`.

The ledger uses a fixed absolute path keyed by evaluation category, binds IDs/config/code/settings/manifest hashes before inference, and consumes the look before teacher results are opened. The real namespace is independent of output directories and synthetic namespaces.
The runner validates checksums, contract/settings hashes, full frame/category coverage, and non-stub provenance. It retains vnice launch requirements, nice 10, scratch caches, eight threads, a fixed deadline, cumulative accounting, and explicit clean resumes. It prohibits automatic relaunch after abnormal termination.
GPU availability and vnice were not checked. A native GPU call can delay Python's alarm; this kit does not claim an external GPU watchdog.

`bash cpu.sh inspect_missing.py` finds no matching fixture frames in the local K1 archive. `MISSING_INPUTS.json` lists all 64 exact paths and the five absent pilot files: `K1_PAIRS.json.gz`, `K1_LIFT.npz`, `K1_NMS.npz`, `K1_LMERGE.json`, and `K1_LEARN_EST.json`, expected under `kit/work/`. The full learned/geometry pilot table remains MISSING. Raw K1 labels and teacher outputs are packaged.
The active spec and design permit one preregistered R0-dev comparison only; dev-S1 remains diagnostic and its frame authority is MISSING. No count-form, floor, or future-head gate can select a release on dev.
Every generated evidence JSON records its input hashes. `COMMANDS.md` gives exact commands; `PACKAGE_PROVENANCE.json` hashes packaged files. The delivery is `sb_cntfix.tar` with `sb_cntfix.tar.sha256`.
No borderline prose-history sentence was retained; the explicit source/audit disclosures identify provenance.
'''
assert len(report.splitlines())<=50
(O/'FIX_REPORT.md').write_text(report)
(R/'STATUS.md').write_text('Stage 3: The full CPU stub covers all 385 authorized R0-dev items. The metric self-test, reviewer audits, 34 control checks, six resume checks, and the in-flight deadline check pass. The training gate rejects a GPU launch at MRA 45.0 versus constant-6 MRA 53.877551, so no real dev look is consumed. The delivery includes the pinned scorer, training freeze, corrected spec/design, raw K1 inputs, exact missing-input list, and hashed evidence. Packaging and final integrity checks are in progress.\n')
print('report lines',len(report.splitlines()))
