NO-GO — the Orchard job stops during staging, and its export layout blocks native initialization.

Paths below are relative to `w20`.

1. **Blocking: staging omits `ANON_OK.json`.** Decoding `work/build20/kits/q/k/p.json` shows no such entry in `p_files`. `b/z.py:207` copies only those entries. Decoded `k/j.json:400` then requires `$HX/ANON_OK.json` in an `rsync` command under `set -e`. The missing source aborts staging. The fixture explicitly supplies this file, masking the omission (`work/build20/jobtest.py`, `test_shell_stage_and_namespace`).

2. **Blocking: staged weights cannot load through the native initializer.** `work/build20/kits/q/b/z.py:164` stores the manifest as `u/<sha256>`; lines 193–197 preserve hash-named replicas. `work/tree_r1/student_pilot/carrier_c1_run.py:962` passes that manifest’s parent directory to the native export reader, which expects `full_weights.json`. Read-only reproduction using `work/tmp/q20/node/e.json` and its verified replica: `full_ft.read_export(pinned(pin).parent)` raised `FileNotFoundError: .../node/u/full_weights.json`.

3. **The executable kit violates the job-visible naming rule.** Base64-decoding `work/build20/kits/q/k/j.json` reveals `/project/community/jjyeung/distill/okit` at decoded line 11, `models--Qwen--Qwen3.5-9B` in an executed argument at line 107, and `STUDENT_MODEL_ROOT` at line 375. `b/z.py:211` decodes this shell and line 216 executes it; these strings become job-visible.

4. **The required production proof remains incomplete.** Reading `work/build20/proofs/native/{400,600}/q/RESULT.json` shows `REFUSE`, `R1_POST_FILTER_CAPACITY_SHORTFALL:pose`, and `forward: "not requested"`. Neither result reaches production audit, final handover, initialization, or every-rank forward/loss.

Review-19 checks: the pose schema/hash repair passed an extra-field refusal and a valid-hash-change identity probe. Official selection refused a DEFERRED artifact even with `banks=[]`. The component guard refused an edited record with a recomputed status digest. Both `f7eaf7a7` and `43853165` are present in the delivery archive with matching sizes and hashes.

**DEFERRED boundary answer:** I found no verified bypass in the reviewed paths. Read-only calls to the existing sealed VSI-Bench, VSTI and ReVSI fixtures refused at `official-item-read`; official selection and export also refused. This does not establish exhaustive coverage of unchanged readers.

The shipped execution path showed no writes into P’s kit or run. The room census remains separate from admission and cannot turn a failed proof into success.

Not checked: live Orchard files, actual bwrap isolation, GPU execution, scheduler behavior, complete real input closure, or the unreached production stages. I ran no confirmation commands and changed no files.