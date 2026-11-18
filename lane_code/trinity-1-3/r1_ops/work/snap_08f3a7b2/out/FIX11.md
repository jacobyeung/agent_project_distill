BUILT_PENDING_FULL_LOCAL_CHECKS. Packet A has S2 on. The proof initializes its own shell environment before the loader audit.

Config identity: `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f` (unchanged; zero config-field changes).
Run key: `673bc60f`. Archive: `p_a5dc8f30.tar`.
Archive SHA256: `a5dc8f306b6867c24fc80aa1215697cb178337252ec912f61ff575b8ec1e9169`.

The generated `out/proof/p.py` embeds the post-admission shell in `program()`. `tools/make_proof.py` compresses this program into `p_673bc60f.sh`; `tools/package_operator.py` includes that script in the archive. The bundle's `p.py` is the unchanged `tools/seal_proof.py`, which binds the script bytes in the authority's `bundle_files`.

The proof runs `r.sh p 0` in a child shell, then sources `c.sh` in its caller. Child exports cannot initialize the caller. The caller explicitly exports `TK_JOBDIR` and reconstructs `R1_RUNTIME_RECORD` from the pinned staged record. It also exports `TK_RUNS_DIR=$NR` for consistency with the training entry.

`TK_JOBDIR` is `/tmp/jjyeung/a_673bc60f/jobs/${SLURM_JOB_ID}.proof` inside the proof namespace. The existing `/tmp` bind maps it to `/tmp/jjyeung/p_673bc60f_${SLURM_JOB_ID}/tmp/jjyeung/a_673bc60f/jobs/${SLURM_JOB_ID}.proof` on the host. The proof sets umask 077 and creates the leaf with `mkdir -m 700` before `tk_bwrap`. A pre-existing directory or symlink fails. No writable mount is added.

`tk_current record` supplies the runtime-record SHA. The caller verifies `$S/c7d31ddd/anyhost/<sha>.json` with `sha_is` and exports its namespace path `$P/anyhost/<sha>.json`. `tk_env` then exports the same path as `ANYHOST_NEUTRAL_RUNTIME`. The staged bytes remain read-only; caches and temporary files use the private proof job directory.

| Shell dependency | Source and use |
|---|---|
| `TK_KIT_HOME`, `ROOT` | The proof sets `TK_KIT_HOME=$ROOT` before sourcing; `ROOT` is the validated kit path from the generated job prefix. |
| `SLURM_JOB_ID` | Proof `main()` requires a positive numeric allocation ID; shell expansion uses `${SLURM_JOB_ID:?}`. |
| `TK_JOBDIR` | The proof creates a fresh 0700 `.proof` directory before `tk_bwrap` or `tk_env`. |
| `R1_RUNTIME_RECORD` | The proof resolves and verifies the record already staged by admission. It does not depend on a child export. |
| `TK_RUNS_DIR` | The proof exports `$NR`; `r.sh` obtains the same run parent from the pinned launch record. No current `c.sh` expansion requires this variable. |
| `AS AL K X R HX IN REV P RR EPOCHS S U HM NX NR CUR COMMIT CLOSURE_DIR` | Sourcing the sealed `c.sh` initializes all of them before functions run. `COMMIT` and `CLOSURE_DIR` come from pinned `k/0.json`. |
| `BW` | `tk_bwrap` initializes the array before the loader command expands it. Its `bw`, `sha` and `entry` locals are assigned by `read` and iteration. |
| `ANYHOST_JOBS PILOT_VENV PYTHONPATH TMPDIR` | `tk_env` initializes these before `tk_pythonpath p` and the loader call. All other runtime exports are constants or derived from the initialized paths. |
| `TK_LIGHT` | Staging reads it only through `${TK_LIGHT:-}`; `r.sh` explicitly sets or unsets it for its own stage. |
| `TK_JOB_START`, `TK_STAGE_ROOT` | The wrapper/job prefix sets `TK_JOB_START`; preflight exports `TK_STAGE_ROOT=$S` in its child. Neither is read by the post-admission `c.sh` functions or the loader-audit entry. |

The audit covers all 28 uppercase shell-variable reads in the entire staged `c.sh`, including staging and persistence. `ENVIRONMENT_AUDIT11.json` assigns each read an owner. Function parameters use guarded arguments or are supplied by their caller; staging locals receive their values before use from assignments, `read`, or loop bindings. `r.sh` and `p0.sh` already initialize `TK_JOBDIR` before their staging calls. `tk_stage` initializes `R1_RUNTIME_RECORD` before their `tk_env` calls. The proof does not repeat staging after admission.

The mount/path audit covers `$U` at both AWS prefixes, `$NX` at `$X`, `$NR` at `$X/runs`, units, frame roots, models, the closure, epochs and the new job-directory bind. The admission child stages all existing sources before the post-admission block. The runtime-record read uses the staged physical path; the loader receives the namespace path. `tk_pythonpath p` uses `$X/b`, the closure, its site alias and the optional NumPy overlay. The `c`, `t` and `u`-only FLA branch is outside this CPU proof. Both NumPy branches pass the fixture.

The loader command receives `$PILOT_VENV/bin/python` and `$X`. Its Python entry reads the pinned launch/config and admission outputs, then writes `inputs/l.json` and `inputs/a.json` through the existing run mount. After shell success, `verify_prepared` validates `data_receipt.json` through the physical run path. Proof `main()` checks the loader receipt's identity, hash and required predicates, then writes the already reserved job receipt under `kh/o`. No later shell expansion depends on a child export. These predicates and trainer bytes retain their existing definitions.

All 7 focused regressions pass. The full suite and `tools/run_local_checks.py` await explicit heavy-I/O approval under the supplied Trinity rule; they have not been run for this fix.

`proof/POST_ADMISSION_SHELL.json` records two successful nounset executions. Each runs the generated suffix, sources the exact production `c.sh` (SHA256 `900d05353901d661474ffa12562d17bebafc4af1f95e03743e348d5ebefb9598`), executes its real helpers, reaches a stub loader import/call and writes a fixture receipt through the proof's real `execute()` function. The fixture supplies a fake allocation, stub admission, stub bwrap and stub loader body. It remaps path constants after sourcing instead of creating a real namespace. Mutation cases remove each required export, precreate or symlink the job directory, and alter runtime bytes; every case refuses before the loader.

`proof/RESEAL11.json` records a successful seal against a local production-form deployment fixture. The archive test checks every member hash and decodes the embedded script to verify exact equality with the generated proof program. It does not issue production authority. The archive name derives from its payload SHA256 so a proof-only change retains config and deployment paths while producing a distinct archive.

Reviewer checks: inspect the environment initialization and namespace mapping; verify the unchanged config, trainer, `c.sh`, `r.sh`, `p0.sh`, job entry and `jb.sh`; verify the new archive SHA and embedded proof; deploy the corrected script and reseal the authority against its new `bundle_files` hash before any approved CPU proof. Bundle and kit names remain `i_69d2930d` and `x_69d2930d`; the archive filename is independent of those names. The failed job receipt remains failed. A complete production loader audit and proof receipt remain unverified locally. No Orchard, SSH, Git or GPU action was performed.

`FIX11.diff` compares packet tools, tests, configs, current bundle, proof evidence and reports with `snap_fac07052`. It omits unchanged archives and transient work fixtures; binary additions carry hashes. Existing `out/p_*.tar` hashes are checked against `FIX11_PROTECTED_ARCHIVES.json`. Snapshot and packet B bytes were not edited. The snapshot comparison is retained because the brief explicitly requires it.
