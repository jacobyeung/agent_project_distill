GO AFTER FIXES (MUST M4 only: a documentation and test fix for the separate runtime reader; the donor code passed every check I ran)

Scope: `donor2/out/PATCH_DONOR2.patch` on base seal 57a1f14d and live seal 189df6ac. I staged both trees under `work/` and wrote every check myself. Scripts and JSON outputs are in `work/`; the paths below are relative to the patched tree.

## MUST

- M4. Following `READER_REQUEST.md` in the separate runtime loader fails closed at `attach`. Lines 17 and 47 say to construct and warm-start the model, call `scale_donor.attach`, and then run the pop/verify/strict-load sequence. But `mdg_runtime.load_runtime` builds `CarrierC1` on an empty base (`student_pilot/mdg_runtime.py:194-198`), and the private visual starts as a trainable deep copy (`student_pilot/carrier_c1.py:47`). `full_ft.load_export` replaces only base tensors (`mdg_runtime.py:208`). The standalone runtime never reads `depth_init` (`:220-222`), so the private visual gets its weights only from the strict head load (`:212-213`) and is frozen only at `:217`. `attach` therefore raises at `student_pilot/scale_donor.py:69-70` or `:74-76`.
  - Reproduction: I followed the recipe on a real step-3 donor export, on a model built the way `load_runtime` builds it (`work/READER_new.json`, `work/READER_live.json`). The literal recipe raises "requires an already frozen private visual copy". Freezing alone raises "shared visual pin differs". Loading the visual without freezing it raises "already frozen" again.
  - What works: load `depth.model.visual.*` from `heads.pt` (strict), call `requires_grad_(False)`, then follow the documented sequence. All 268 head tensors then match. `attach` still checks that visual against `visual_sha256`, so this order stays authenticated.
  - Overclaimed coverage: `READER_REQUEST.md:58` says the fixture runs the actual `load_runtime`. The test replaces `CarrierC1` with an already attached fixture (`tests/test_scale_donor.py:254,268`), so it never builds the model the way `load_runtime` does.
  - Fix: add the load-and-freeze step to the recipe, and make the runtime test build the real `CarrierC1`.

## Verified

1. M1 to M3 are fixed.
   - M1, the fixture: it now sets nonzero `fov_film[-1]` (`tests/test_scale_donor.py:23-31`). The new negative control (`:199-214`) fails on a V1 donor that reads live FoV.
   - M1, my unit mutants: I planted three leaks, each caught by a named test (`work/MUTANTS_UNIT.json`). A V1 donor reading live `depth.fov` fails at `:118` and `:207`. A donor fed the pose-head FoV fails at `:168`. A donor reading the live frame queries fails at `:118`.
   - M1, my K1 check: it uses independent FiLM seeds and the full `HeadState` tower decode on the authenticated K1 captures. The patch passes it and all three mutants fail it (`work/K1_*.json`). With FiLM zeroed, both FoV mutants pass the unit tests undetected (`work/MUTANTS_FILM0.json`), so the nonzero path is what lets the test see the leak.
   - M2: the nine-file table matches `FEATURE_FILES` (`student_pilot/scale_donor.py:18-20`) in membership and order. Every SHA256 matches the base, new and live bytes; `scale_donor.py` is correctly MISSING at base.
   - M3: the pop/compare/`verify_export`/strict-load order matches `carrier_c1_run.load_artifact` (`student_pilot/carrier_c1_run.py:3264-3269`) and fits before `mdg_runtime.py:212-213`. Only the precondition in M4 is missing.
2. A donor leg resumes under its own binding (`work/RESUME_new.json` and `work/RESUME_live.json`, both PASS).
   - Chain: native `prepare`, then `prepared`, then `load_model`, which attaches the donor from the receipt (`carrier_c1_run.py:888-890`). Then two optimizer steps, a checkpoint, a fresh `load_model` and `restore`, which returns 2.
   - Step 3 equals the uninterrupted reference on all 175 trainable and 525 optimizer tensors.
   - The donor still equals its source on all 66 pins, the source bytes are unchanged, and the checkpoint holds no donor tensors. The step-3 export binds the same donor, and `load_artifact` accepts it.
   - A pre-donor leg under the donor binding refuses with named errors: `restore` "C1 resume binding differs", `prepared` "frame layout/LM lever differs", `latest_resume` "No complete C1 resume state", `bind_output` "belongs to another run". The old leg still restores under its own binding.
   - Mocks covered only validation, authentication, the database, exclusions, the student snapshot, a tiny base and `dist`.
3. With the donor field absent, base and new are byte-identical, and so are live base and live (`work/PARITY_COMPARE.txt`, 25 of 25 fields each).
   - The fields cover identity, receipt bytes, groups, and all 275 state and 525 optimizer tensors at initialization and at steps 2 and 3.
   - They also cover own and tower decode before, after and on reload, checkpoint file hashes, the `heads.pt` hash and the artifact JSON.
4. S2 holds (`work/S2_new.json`, PASS).
   - Rank zero hashes the artifact and the heads. Followers hash only the artifact and memory-map the same relocated path.
   - Both refuse a wrong feature-contract pin, a wrong visual pin, a changed live visual, a tampered heads visual or a wrong artifact pin.
   - Followers attach only after rank zero verifies and `agree` runs (`carrier_c1_run.py:2921-2931`). No other path loads donor heads without `pinned()`.
5. `REAL_WEIGHT_COMMAND.sh` works when run verbatim on donor2's fixtures (`work/REALCMD*.json`).
   - V1 and V2 pass.
   - A flat binding stops with `KeyError 'scale_donor'`, and a missing `N_STEP2_ARTIFACT_SHA` stops at line 11.
   - `bash -n` exits 0, and the CLI flags match `scale_donor_check.py:110-196`.
6. The patch applies on 189df6ac with no fuzz (`work/SETUP.json`).
   - Live differs from base only in `launch_r1/entry.py`, `launch_r1/production_proof.py` and `tests/test_host24j.py`, none of which the patch touches.
   - The 11 donor tests, the resume check and the reader check give the same results on live as on new.

## Notes (non-blocking)

- Followers do not authenticate the donor's point-depth, query or FoV tensors themselves. A follower given changed point-depth bytes attached them (`work/S2_new.json`, `heads_point_depth_tampered`).
  - They rely on rank zero's hash of the same file (`scale_donor.py:191`). That is safe while every rank resolves the same immutable node-local path, as in N's single-node, world-size-4 launch.
  - A multi-node launch with per-node replicas would load unhashed bytes on the other nodes.
  - `scale_donor.py:177` and `READER_REQUEST.md:68` call tensor checks "mandatory on every rank". That holds for the check against the tensors' state at attach time, not for authenticating the source.
- `READER_REQUEST.md:25` says to run `out/REAL_WEIGHT_COMMAND.sh` "from the patched tree", but `out/` sits in the donor2 package. The script works when invoked by its absolute path from the tree root.
- Real step-400 and step-544 heads and the V1/V2 decision remain MISSING, as the lane reports.
