GO (M4 is fixed; I found no MUST or SHOULD items)

Scope: `donor3/out/PATCH_DONOR3.patch` and `PATCH_DONOR3_DELTA.patch` on base seal 57a1f14d and live seal 189df6ac. I staged every tree myself under `work/` and wrote or reran every check there. Paths below are relative to the patched tree unless they start with `work/`.

## Verified

1. The new recipe loads an export in the real runtime, and the old order still refuses (`work/RUNTIME_{new,live}_{real,train_config}.json`, all PASS).
   - Method: I ran the unmodified `mdg_runtime.load_runtime` function object, with no source rewrite. At its own `torch.load` of `heads.pt` (`student_pilot/mdg_runtime.py:212`), my hook ran the `READER_REQUEST.md:49-64` block verbatim, extracted from the file, and then the runtime's own strict load at `:213` ran.
   - Substitutes: only `_bundle`, `processor_for_receipt` and `r2_policy.unsupported_entry`. Real code: `CarrierC1` (`:195-198`), routing init, the bf16 cast and `full_ft.load_export` (`:206-208`). The `real` runs also used the real `_empty_base` (`:153-166`) on a native fixture's `config.json`.
   - Entry state: on entry the model was a `CarrierC1` with no donor and a trainable private visual.
   - Result: after loading, all 268 head tensors match `heads.pt` byte for byte. The visual matches `visual_sha256`, donor metadata equals `artifact['scale_donor']`, nothing is trainable, and `depth_init` is skipped.
   - Refusals:
     - Donor2's old block (attach first) and loading without freezing raise "already frozen".
     - A tampered visual raises "shared visual pin differs".
     - Freezing alone and a non-strict visual load also refuse at attach. On the real `_empty_base` they fail through the nonfinite check (`student_pilot/scale_donor.py:28-29`), because `no_init_weights` leaves uninitialized bytes.
     - A missing visual key raises "Missing key". A tampered donor tensor raises "changed since initialization". The unmodified runtime with no adapter raises "Unexpected key" on `scale_donor.*`.
   - Fixture: the export is a native step-3 donor export from my own rerun of the resume chain on each tree.
2. The new runtime test builds the real `CarrierC1` and fails without the fix (`work/TEST_MUTANTS.json`, PASS).
   - The test asserts the real type and the absence of a pre-attached donor (`tests/test_scale_donor.py:287-288`). It runs the real `load_export` once (`:333`) inside the runtime body (`:320`).
   - Its `reader_steps` (`:268`) equals the documented block minus the import and `torch.load` lines.
   - Three mutants each fail the test: donor2's order fails with "already frozen", dropping the freeze with "already frozen", and dropping the visual load with "shared visual pin differs".
3. The delta changes no donor training code (`work/SETUP.json`). My `new` tree differs from donor2's patched tree only in `tests/test_scale_donor.py`. The delta patch touches only that file, and base + `PATCH_DONOR2` + delta equals `new`.
4. Donor2's results still hold on both seals.
   - Tests and resume: the 11 donor tests pass on `new` and `live` (`work/unit_{new,live}.log`). The resume check passes on both trees: step 3 equals the uninterrupted reference on 175 trainable and 525 optimizer tensors, and all four pre-donor refusals fire (`work/RESUME_{new,live}.json`).
   - Field-absent parity: base equals new and live base equals live on 25 of 25 fields (`work/PARITY_COMPARE.txt`). The 22 tensor and decode fields also equal donor2rev's outputs. The other three fields are identity hashes that embed this review's run paths.
   - Live application: all four applications have zero fuzz and zero offset, and live + `PATCH_DONOR3` equals the expected file set (`work/SETUP.json`).
   - Package: the tar's SHA256 matches `fbp_donor3.tar.sha256`, and `bash -n out/REAL_WEIGHT_COMMAND.sh` passes. Only its usage comment changed.

## Notes (non-blocking)

- The test's empty-base substitute (`tests/test_scale_donor.py:283-285`) uses the fixture's fp32 training config, whose `vision.dtype` is `None`. `feature_contract` hashes `vision_config.to_dict()` (`student_pilot/scale_donor.py:42`), and the real `_empty_base` sets that field to bfloat16. So the real `_empty_base` refuses the test's fixture binding with "preprocessing/architecture pin differs" (`work/RUNTIME_*` first run, `work/CONTRACT_new.json`).
- That refusal is a fixture limit, not a production defect. Production training loads the base with `dtype=bfloat16` and `attn_implementation='sdpa'` (`student_pilot/carrier_c1_run.py:817-819`), and that contract digest equals the runtime's. A fixture whose training config uses bf16 passes the real `_empty_base` path (`work/RUNTIME_*_real.json`).
- An MDG bundle cannot carry the donor source checkpoint, because `_bundle` requires exact file coverage (`student_pilot/mdg_runtime.py:142-146`). `attach` rehashes that checkpoint from its pinned path (`student_pilot/scale_donor.py:182,191`), so the production reader adapter must stage it separately. `READER_REQUEST.md:70` already defers that adapter.
- donor2rev's notes still apply. Followers rely on rank zero's hash of the source heads, and the real step-400 and step-544 heads and the V1/V2 decision remain MISSING.
