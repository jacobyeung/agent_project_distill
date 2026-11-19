from pathlib import Path
import json
W=Path(__file__).resolve().parents[1];O=W/'out';t=json.loads((O/'TESTS.json').read_text());f=json.loads((O/'FILES_TOUCHED.json').read_text());s=t['suites'];assert t['status']=='PASS'
summary=lambda x:f"{x['tests_run']} tests, {x['failures']} failures, {x['errors']} errors and {x['skips']} skips"
lines=[
'# PATCH_DONOR2',
'',
'M1–M3, S2 and S3 pass CPU fixture validation. S1 remains documented because the requested native resume needs a change to resume legality. Real weights and the production FoV/source decision remain MISSING.',
'',
f"The replacement patch changes {len(f['files'])} files against seal `57a1f14d`; the delta changes {len(f['delta_files'])} files against base+PATCH_DONOR. `code/build_patch2.py` produces both patches and `FILES_TOUCHED.json`.",
'`code/verify_patches.py` verifies full, delta and live applications with zero fuzz and zero offset, including every unchanged file. The live copy matches `189df6ac` across 940 files (`code/stage_live.py`, using `tree_rebuild15_w24l/out24j/TREE24J_SEAL.json` and `work/tree_r1_base`). The mapped live directory and literal TREE_SEAL.json were missing; the named live workspace supplied the verified seal.',
'',
'M1: The unit and K1 fixtures set nonzero `fov_film[-1]` weights before saving the source. The correct V1 donor ignores live FoV changes; the injected live-FoV donor fails the same invariance assertion on both K1 captures. V1 and V2 scales differ in both K1_INVARIANCE.json and EXPORT_CHECK_V1/V2.json.',
'M2: `code/reader_docs.py` writes READER_REQUEST.md with all nine feature-contract source files with base/patched SHA256 values and requires byte-identical reader sources. A later edit locks out existing exports. Repinning only the reader hash still fails; retaining the original reader or a reviewed matching binding migration is required. Verification stays fail-closed.',
'M3: The reader recipe pops `_scale_donor`, checks equality with artifact metadata, verifies the export and then strict-loads. The actual mdg_runtime strict-load call passes with this preprocessing and fails without it; metadata and tensor corruption also fail. The test isolates the legacy R2 entry guard and bundle/model-loading boundaries. Production still needs an authenticated reader adapter.',
'',
'S1: No preparation or resume-legality change is made. N needs a fresh preparation containing its donor. `identity(cfg)` includes the donor, `train` binds that identity, and `restore` rejects the pre-donor checkpoint under a changed binding. The native regression restores with the attached donor under the unchanged binding, proving that trainable-shard layout is compatible; it refuses the new binding. Extending the rebind policy would change resume legality, which this task excludes. S1_STATUS.json records the unchanged protected functions and test command.',
'S2: `load_model` forwards verify_assets. Rank zero hashes heads; followers reuse that verification after the existing startup agreement. Both paths memory-map heads and enforce tensor, visual and feature identities. The fixture observes one heads hash on the verifier and none on the follower, including relocated storage. Each rank still constructs frozen modules; production memory and throughput are unmeasured.',
'S3: REAL_WEIGHT_COMMAND.sh requires JSON shaped as `{"scale_donor": {...}}` and takes its interpreter from PYTHON. `bash -n out/REAL_WEIGHT_COMMAND.sh` passes.',
'',
f"`code/run_unit.py` passes {t['unit_tests']['unit_final.log']} donor tests on base+donor2 and {t['unit_tests']['unit_live.log']} on the live overlay (DONOR_TREE=live). The inherited seven tests and four new regressions all pass.",
'`code/k1_fixture.py` authenticates 64 anchor-frame hashes across two K1 training captures and runs two native optimizer steps per variant. Donor tensors, grids, float64 scales and shared visual stay byte-identical while the live head and grids change. It uses tiny native weights, 4×4 RGB fixtures and synthetic fixed G3T depth/confidence; it does not establish real-weight accuracy.',
'`code/run_export_check.py` produces both passing export checks; `code/adversarial_checks.py` refuses all five inherited export attacks.',
'`code/parity_full.py base` and `new` prove field-absent byte parity for both decode arms before training, after two steps and after reload, optimizer groups, handover table, 275 state tensors, 525 optimizer-state tensors and 202 exported head tensors. `code/absent_parity.py base/new` also passes the inherited parity check.',
'',
f"Full suite (`code/run_suite_final.py base/new`): base has {summary(s['SUITE_BASE_FINAL'])}; new has {summary(s['SUITE_NEW_FINAL'])}.",
f"Focused suite (`code/run_focused.py base/new`): base has {summary(s['FOCUSED_BASE'])}; new has {summary(s['FOCUSED_NEW'])}.",
f"Live focused suite (`code/run_focused.py live_base/live`): base has {summary(s['FOCUSED_LIVE_BASE'])}; patched has {summary(s['FOCUSED_LIVE'])}.",
'All three comparisons have no new failure signature. PREEXISTING_FAILURES.md lists every observed baseline failure/error and its cause; TESTS.json retains full tracebacks. These suites do not fully pass: unavailable archived fixtures/dependencies and forbidden process/socket/NFS operations remain explicit failures, errors or skips.',
'',
'Overlap (`code/build_patch2.py`): none with the available patchA2, camform or prior2 file inventories. pointD is MISSING at `/scratch/jjyeung/orch_n30/fb_pack/pointD/out/FILES_TOUCHED.json`; its overlap is unknown.',
'Real step-400 heads are MISSING at `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt`, expected SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. Step-544 heads have no supplied location. No production donor binding, admission or benchmark gain is claimed.',
'',
'Run real-weight validation from the patched tree with `PYTHON=/path/to/python bash out/REAL_WEIGHT_COMMAND.sh` and its required pinned variables. READER_REQUEST.md gives the complete integration contract.',
'Every model/test Python command above uses `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`. JSON receipts record input hashes and exact commands. `code/assemble_final.py` computes the counts/comparisons above; `code/package2.py` builds and verifies fbp_donor2.tar and its SHA256.',
'The package retains the overlay, both patches, harnesses, fixture source/export tensors and validation evidence. CPU only; no Git, network, SSH, GPU, signals or tmux operations. Borderline prose retained: the pre-donor checkpoint comparison is a required boundary test, not a revision narrative.'
]
assert len(lines)<=70
(O/'REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('The donor2 replacement and delta patches, reader instructions and all CPU evidence are complete. M1–M3/S2/S3 pass; S1 remains documented at the resume-legality boundary. Full and focused comparisons introduce no new failure, field-absent parity is exact, and both tree seals verify. The package is being assembled; pointD inventory and production donor weights/selection remain missing.\n')
print(len(lines),'report lines')
