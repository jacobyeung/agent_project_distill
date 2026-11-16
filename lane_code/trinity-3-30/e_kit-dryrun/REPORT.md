# kit-dryrun: report

Branch `eff/kit-dryrun` in `/scratch/jjyeung/orch_n30/e_kit-dryrun/clone`: commit 5756b91 (the build), then 2b1a289 (`--path`). Both heads are listed in `PUSH_QUEUE.txt`. Every file sits under `tools/orchkit/`.

## What I built

- `dryrun.py run`: runs a kit's batch entry inside bwrap. `/home` and every `/data*` show up as empty directories, `/tmp` is private, there is no network, and the only parts of `/scratch` the entry can see are the kit copy, OUTDIR, its interpreter tree, `--ro`/`--path` and the `--map` sources.
  - The kit runs from a fresh copy in OUTDIR, bound at its own path (`--kit-at`). The source kit is never touched.
  - Config identity: the production CONFIG is bound unchanged at `--config-at` (or at the path of the config pin). Its sha256 must match the config pin or `--expect-config-sha256`. No option edits the config. A `--map` that covers the config path fails the run.
  - Shims: `gcloud`, `gsutil`, `sbatch`, `squeue`, `sacct`, `scontrol`, `nvidia-smi`, `ssh` and `curl` go first on PATH. They are also bound over the absolute system paths, because K1 calls `/usr/bin/gcloud`. A shim serves pinned objects with URI and generation honoured, or replays exact-argv fixtures from `--calls`. It logs each call to `shim_calls.jsonl` and fails any call it has no fixture for.
  - The tracer (a port of `trace_runtime.py` and `rh_coverage.statements`) reaches child processes in three ways: by rewriting `Popen`, through `sitecustomize`, and through `--wrap-python` for children started with `-I`. On Python 3.8+ its audit hooks also log reads under hidden roots and every `mkdir`.
  - It writes `DRYRUN_REPORT.json` in the orchkit-dryrun-v1 format, plus `fail_reasons` and `checks`.
  - Checks:
    - Pins: identity and pin sha256.
    - `config_lint`.
    - Calls: an unplanned call fails the run.
    - Paths: any access to a hidden path fails it.
    - Entry: rc and timeout.
    - Stage markers (`--stage NAME=REGEX`) and the item count (`--item-regex` against `n_items`).
    - `dir_collision`: one directory created by two processes, the 169477 class.
    - Staging closure, required by the verdict and checked inside the namespace after the run: every pin of role code, config, input, weights, record or env exists at its logical path and matches its sha256; every absolute path in CONFIG exists, mapped through `--alias` for kits that translate paths; every `gs://` URI in CONFIG is pinned.
    - `tar_member_type`, from VSTI 170209: an archive may hold only files and directories unless `--tar-links` names it.
    - `row_schema`, with `--rows`/`--row-profile`.
    - `hardcoded_cap`, required by the verdict.
    - `unclassified_lines`: classification file `orchkit-dryrun-classify-v1`.
- `lint_config.py` (built by Codex Astra from my brief; I ran its tests): the schema subset, the prose rule plus the field rules ported from K1 `audit_config.py`, the budget rule, `host_path` plus the opacity words, and the pins check. `--code FILE.py` adds `cap_default`: an AST check for numeric defaults on cap, limit, bytes and timeout names.
- `rowschema.py check` (Codex): `orchkit-rowprofile-v1` profiles (required, when, vocab, forbid_substrings, forbid_values(_files), groups, unique), streamed over `.jsonl` or `.jsonl.gz`. `tests/fixtures/dryrun/rows/d0_rows.profile.json` holds the D0 rules.
- `shims/`: `shim.py`, `trace.py`, `sitecustomize.py`, `runner.py` (runs inside the namespace and does the closure check) and `pywrap.py`. The toy kit is in `tests/fixtures/dryrun/toykit/`.

## Tests (56 in total)
```
cd clone/tools/orchkit && TMPDIR=W/tmp /usr/bin/python3 -m unittest discover -s tests
Ran 56 tests in 5.500s
OK
bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc env HOME=/tmp TMPDIR=W/tmp /scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider tests
56 passed in 4.66s
```
- Toy kit: PASS, 5 items, 1 shim call, every stage reached, and the only never-run range is the classified error path.
- Mutants, each failing with its named reason:
  - `config_mismatch`
  - `unplanned_call` (gsutil cat)
  - `hidden_path` (a `/data2` read)
  - `dir_collision`
  - `unclassified_lines`
  - `closure_missing`: a pinned weights object that is never staged, the 170206 class
  - `tar_member_type`: a hard link
  - `config_lint`: the members prose
- Regressions in `test_lint_config.py` and `test_rowschema.py`:
  - the `anchors.members` prose fails;
  - 1.5 GB against 300 items × 10 MB fails;
  - `total_num_frames: null` under the duplicate layout fails;
  - `/scratch/jjyeung/orch_n30/` in row metadata fails.
- Caveat: `discover -t .` cannot import `tests/` because the folder has no `__init__.py`, and I own no such file. Run discovery with `-s tests` only.

## Replay on REF copies (outputs in `W/replay/`)

- **K1 Part B config**:
  - REF does not hold the `a.json` submitted with 170193. Instead, `lint_config` ran on `INPUTS_PLAN.json`, the descriptor that the config's anchors item was built from. It failed with 4 findings: `anchors.members` is prose, `anchors.generation` is null, `base.archive_sha256` is null, and `anchors.logical_root` holds `/scratch/jjyeung/`. The acceptance check therefore holds: this K1 config fails.
  - `cap_default` flags `max_bytes=1_500_000_000` at `k1_phases.py:115`, which is the tower_sam stop. It also flags `timeout` in `job_support.py:72`.
- **D0 read kit** (`ae3be05b81a`):
  - Config sha `0d77bdbd…` equals `BATCH.pin.json`. This family embeds its CONFIG in `BATCH.sh`, so the dry run can prove identity by sha only.
  - Lint: 14 findings: two null sha256 pins, plus Trinity paths (`/home/jjyeung/okit/...`, `/scratch/jjyeung/...`) in a config bound for the batch host.
  - The entry ran through bootstrap, extraction and `orchard_job.py` under `--path` p1cpu. It stopped at the kit's storage proof: "Storage is not the assigned job-private /tmp mount". The kit then made its return: the shim captured `result.tar.gz` holding FAILED.json.
  - Unplanned calls: `nvidia-smi --query-compute-apps` and `gcloud storage objects describe` on the return object. 27 config paths were missing, mostly pool files that REF lacks.
  - The tracer did not see the kit, because the bootstrap execs a `-I` interpreter that `--wrap-python` cannot relocate for a uv build.
- **K1 package** (`k1_build`): it cannot run, because REF lacks `a.json` (`FileNotFoundError` at `batch_entry.py:16`). Even so, the run traced 3 files and flagged 5 unpinned `gs://` URIs and the `job_support.py` timeout cap.
- **Tree kit** (`launch_s1`): `--wrap-python /usr/bin/python3` traced both `-I` children under Python 3.6. The entry stopped because REF lacks `ANON_OK.json` and the sealed `k/` directory.

## Saving (restated as the verdict requires)
The config and row lints catch 2 of the 5 session failures: D0 170050 and K1 170193. They also catch about 5 of the 9 pilots. On top of that:
- **Staging closure** catches the 170206 class. I proved this on a toy mutant only, not on 170206's inputs.
- **`cap_default`** flags the tower_sam default cap in replay. Nothing proves that this flag would have stopped the GPU run.
- **The tar check** catches the 170209 class, again proven on a toy mutant only.

## What a CPU dry run cannot prove
- GPU-only lines, which belong to the GPU canary.
- Batch-host mounts and storage proofs. D0's job-private `/tmp` check fails by design on this host.
- Real GCS and Orchard transport, and real Slurm.
- Bytes behind stand-ins.
- Hidden-path reads and directory collisions in Python below 3.8, which has no audit hooks; there the kit's own error is the only signal.
- Shell-level `mkdir`.
- `-I` children of uv interpreters.
- Rules in the D0 records that are not mechanical. `W/work/LINTS_REPLY.md` lists them: provenance of frame counts, store identity, pair keys, semantic validators, withheld-scene ids, and review decisions.

## Adoption steps (orchestrator)
1. Get a cross-family review of `dryrun.py`, `shims/` and the two lints. The tool admits nothing; it only adds failures.
2. Fast-forward `eff/kit-dryrun` into `main` at an epoch boundary. orchkit-core's `launch.py prepare` reads `DRYRUN_REPORT.json`.
3. For each new kit, run the following before review: `lint_config.py CONFIG --schema FAMILY --pins PINS --code <kit modules>`, then `rowschema.py check` when a row store is built, then `dryrun.py run` with the production CONFIG and a classification file.
4. Old-format kits need a pins manifest and `--alias` mappings before the closure check means much.
