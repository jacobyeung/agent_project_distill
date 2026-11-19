# Frozen tower-scale donor

The overlay implements a frozen donor for tower-arm scale against seal `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`.

`PATCH_DONOR.patch` changes eight files. `FILES_TOUCHED.json` records their before/after hashes. The patch passes `patch --dry-run -p1 -d work/base`; no named fbp_patchA component overlaps.

The pinned `scale_donor` configuration requires a checkpoint, explicit `V1` or `V2`, shared-visual hash and feature-contract hash. The source may be step 400 or 544. No FoV variant is selected implicitly. The donor copies point-depth weights and private frame queries; V1 also copies `depth.fov`, while V2 reads frozen G3T intrinsics. The donor shares the already frozen private visual module by reference.

Donor parameters require no gradients, stay in eval mode, and never enter an optimizer group or weight decay. The trainer carries the binding through preparation and initialization. Handover checks preserve the inherited student optimizer topology. C1 exports include donor tensors, individual tensor hashes, shared-visual identity, source checkpoint pins, FoV-source identity and frozen scale-rule hashes. The reader verifies these against the pinned initialization.

The tower arm uses the unchanged median estimator on the donor's `[32,51,51]` grids. It applies the resulting scale once to raw G3T translations and raw G3T depth, then lifts the scaled depth. The own arm keeps its live heads. Tower reads add a private-ViT forward; GPU and distributed performance are unmeasured.

CPU evidence:

- Seven donor unit tests pass. Optimizer exclusion, both FoV variants, export/reload, handover binding and frozen dependencies are covered.
- Both K1 training captures, `arkitscenes/41048124` and `arkitscenes/41069076`, have 32 authenticated anchors each. All 64 frame hashes are in `K1_SELECTION.json`.
- After two native `optimize_step` calls per variant, every donor tensor and the shared visual retain their hashes. Donor grids and float64 scale values remain bit-identical on both captures; live grids change.
- The tiny fixture has 63 point-depth tensors, all of which change. Its donor has 66 tensors for V1 and 64 for V2. These are fixture counts; the record's production requirements are 91 point-depth and 333 shared-visual tensors.
- With the donor field absent, own/tower outputs, optimizer groups and all 275 fixture state tensors match base byte-for-byte.
- Five corruption checks refuse changed point-depth, FoV, private-query or shared-visual tensors, including forged internal hashes. The export checker passes on both fixture variants.
- The guarded full CPU suite ran 1,921 tests on base and 1,928 on new. Both have the same 18 failures, 485 errors and 145 skips; no new failure or changed cause appears after normalizing temporary paths. `TESTS.json` preserves the comparison and tracebacks; `PREEXISTING_FAILURES.md` lists all 503 base failures/errors and their causes. Missing dependencies/fixtures and forbidden integration operations prevent a fully passing suite.

The K1 proof uses native tiny weights, explicit 4×4 RGB fixtures, the duplicate/32-frame layout, and synthetic fixed G3T depth/confidence/translations. V2 FoV values come from the authenticated pricing-kit input. This proves invariance, not K1 scale accuracy. The retained GO rehearsal reports zero optimizer steps because loopback sockets were denied; this delivery uses the native optimizer locally and mocks only export transport. The GO fixture model manifest is MISSING at the mapped `tree_rebuild10_w/w24/work/build24/proofs/capacity/model.json`; the sealed tree's `tests.test_carrier_c1_final.final_fixture` supplies the tiny native model.

Real step-400 heads are MISSING at the staging plan's `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt`, expected SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. Step-544 `heads.pt` is MISSING, with no location supplied. The frozen FoV/source pricing decision for the N kit is also MISSING. No production donor binding or benchmark improvement is claimed.

`READER_REQUEST.md` specifies the cont_ops21 binding and scaling contract. Every tower-arm baseline must be read again under the selected donor before any N export is read under it. `bash out/REAL_WEIGHT_COMMAND.sh` is the exact real-export check entrypoint; its required variables identify pinned N inputs and the native step-2 export. It authenticates RGB and checks real exported tensors at an explicit fixture resolution without loading the LM.

Commands producing the evidence (run from this workspace; each JSON also retains its input hashes):

- `code/build_patch.py` verifies the 939 base file hashes and canonical seal, then produces the eight-file patch and file inventory.
- `code/stage_inputs.py` authenticates the two captures and 64 RGB frames.
- `code/run_unit.py` produces the seven-test donor result in `unit_final.log`.
- `code/k1_fixture.py` produces all tensor counts, changed-tensor lists, grid hashes, scales and two-step evidence in `K1_INVARIANCE.json`.
- `code/absent_parity.py base` and `code/absent_parity.py new` produce the absent-field byte comparisons.
- `code/adversarial_checks.py` produces the five refusal cases; `code/run_export_check.py` checks both fixture export variants.
- `code/run_suite_final.py base` and `code/run_suite_final.py new` produce the full CPU-suite results under identical sandbox guards.
- `code/assemble_reports.py` compares suite results and writes `TESTS.json` and the failure ledger.
- `code/package.py` builds and verifies every archive member, then writes `fbp_donor.tar.sha256`.

Each Python command above uses `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`.

The package is `fbp_donor.tar`; its checksum is `fbp_donor.tar.sha256`. `PACKAGE_CONTENTS.json` lists every member hash. The archive also retains the tiny fixture initialization and step-2 heads used by the export checker. `RUN_SUITE_EXECUTED.py` retains the exact execution runner; its raw source flag includes an extra runner hash, so `TESTS.json` independently rechecks the recorded tree-input hashes after testing.
