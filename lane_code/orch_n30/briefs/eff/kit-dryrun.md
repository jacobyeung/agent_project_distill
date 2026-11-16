# Build brief 2 of 8: kit-dryrun (lane `eff_kit_dryrun`, branch `eff/kit-dryrun`, Claude Opus, effort high, size M: 6 to 8 agent-hours)

Build the one check that runs a kit's real batch entry with its production config on CPU before anyone reviews or submits it, plus two lints for the config and the row store.

## Why

Every first-launch failure of this session, and five of nine pilots the day before, died on a path that no CPU run had executed with the production config.

- D0 job 170050 failed after 1 h 29 min: "a row's student_input.total_num_frames is null ... rows_rebuild2's CPU proof did not run layout_inputs with frame_layout duplicate" (`B/events/cont_ops/20261115T2355Z_BLOCKER_job_a_mode_p_rows_total_num_frames.md`). The chain to a passing proof took about 4 h more.
- K1 job 170193 failed in staging after 3 min: "In CONFIG.json, anchors.members is a descriptive string ... The rehearsals missed it because their fixture configs replaced the anchors item" (`B/events/k1_ops3/20261116T0942Z_BLOCKER_170193_failed_in_staging.md`).
- tower_sam stopped at a default 1.5 GB output cap after 152 of 300 captures: the cap "could never hold the pilot" (`B/events/k1_ops3/20261116T0032Z_BLOCKER_tower_sam_output_cap.md`).
- Pilot 169477 collided on a directory: "The CPU rehearsal passed because its synthetic inputs did not reproduce the real paths"; pilot 8: "This is the fourth pilot lost to a line that no CPU run had executed" (`/scratch/jjyeung/orch_n30/seal_plan/recovered/evalx/written/20261114T083608_*` and `20261115T024906_*`).
- Detail: `AUD/incidents/INCIDENTS.md` rows 6, 7, 8, 11; `AUD/process/NOTES.md` table "Review rounds per kit".

## Rules (these win over everything else in this brief)

Paths. B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. W = `/scratch/jjyeung/orch_n30/eff_kit_dryrun` on trinity-3-30, your lane folder (create it; under 5 GB). REF = `/scratch/jjyeung/distill_sync/stage`, a read-only copy of every lane's code (text files up to 512 KB, refreshed hourly; copy what you need into `W/ref` once). AUD = `/scratch/jjyeung/orch_n30/eff_audit`, the audit notes and these briefs (read-only). SK = `AUD/briefs/skeleton`. RECORD = `/data2/jjyeung/agent_project_data/distill_design/EXPERIMENT_EFFICIENCY_20261116.md`.

1. **Read first**, as named files: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md` (it wins over this brief), `B/tools/CLAUDE_LANE_RULES.md`, `B/tools/LANE_RULES.md`, then RECORD (your change is number 2; `AUD/briefs/INTERFACES.md` holds the formats shared with the other builds).
2. **Host.** You run on trinity-3-30. If `hostname -s` prints `trinity`, stop and tell the orchestrator.
3. **Never touch running work.** You change nothing outside W. Running work is: Orchard jobs 170111 (D0 training), 170209 (VSTI native read) and the K1 own-phase job; the sealed kits and inputs they use (trainer tree b01ce449, row store v5 4af43b40, the confirmed D0 read kit, VSTI kit V1c dc40cf60, the K1 package and manifest v2, every object on an Orchard pool or in GCS); every other lane's folder under `/scratch/jjyeung/orch_n30/` on any node and its tmux sessions; the IO governor under `/data3/jjyeung/orch_n13_20261026/io_governor/`; the scripts in `B/tools/`; other lanes' event folders; the `/home/jjyeung/agent_project_distill` working tree; `/scratch/jjyeung/distill_sync/`. Your code replaces nothing in place: a new version of a live script is a new file on your branch, and the orchestrator adopts it at the next epoch.
4. **Forbidden.** No ssh of any kind (Trinity, Orchard, GitHub), no Slurm command, no GPU, no governed or ungoverned copy to or from `/home` or `/data*`, no stream registered with the governor, no Gemini, OpenRouter or NV call, no package install or download. No recursive grep/find/du/ls -R and no built-in Grep or Glob on `/home` or `/data*`. Tests reach the outside world only through fakes you write.
5. **NFS reads.** From `/home` and `/data*` read only the files this brief names, each once, in bounded parts, never in a loop. You write there only the event files and the one result block named under rule 9.
6. **Git, one narrow exception.** The deliverable is a branch, so the orchestrator allows Git inside `W/clone` only, on local disk: one `git clone --branch main --single-branch /scratch/jjyeung/distill_sync/repo W/clone`, then `git -C W/clone` with `checkout -b eff/kit-dryrun`, `config user.name` / `user.email` (copy the values from the `[user]` section of `/scratch/jjyeung/distill_sync/repo/.git/config`), `add <named paths>`, `commit`, and the read-only `status`, `diff`, `log`, `show`, `rev-parse`. Forbidden: any Git command whose repository or working directory lies under `/home` or `/data*`; `push`, `fetch`, `pull`, `remote`; `add -A` or `add .`; force, rebase, reset or amend of a commit already queued; worktrees. Commit messages are plain: no attribution or co-author lines. If the orchestrator withholds this exception, deliver `W/clone` as a plain directory with `W/COMMITS.md` (one message per intended commit), and the Git owner commits it.
7. **Commit and push often (USER 2026-11-16).** Commit at every passing test milestone and at least once per hour of work. After each commit append one line `<UTC> eff/kit-dryrun <full sha>` to `W/PUSH_QUEUE.txt`. The Git owner (lane code_sync) publishes each queued head to origin as `eff/kit-dryrun`. You never push, and nothing of yours goes to `main`.
8. **Code rules.**
   - Shared helpers: copy `SK/tools/orchkit/__init__.py`, `util.py` and `tests/test_util.py` byte for byte into `W/clone/tools/orchkit/` (sha256 in INTERFACES.md). Import from `util.py`, never edit it (lane eff_orchkit_core owns its changes), and never write your own sha, canonical-JSON, atomic-write, process-identity or locked-append helper.
   - Python 3.6: every module that the batch host or `/usr/bin/python3` (3.6.8) runs uses the standard library only, with no `dataclasses`, no walrus, no `subprocess.run(capture_output=, text=)`, no `Path.is_relative_to`, no `from __future__ import annotations`.
   - No deletion: code and commands never remove a file (no `rm`, `unlink`, `os.remove`, `shutil.rmtree`, `git rm`, `git clean`). Write into fresh paths and leave temporary files in place. The rm_guard hook blocks any shell command that contains a deletion call, including a heredoc that writes one, and queues it for the user: create source files with the Write tool.
   - Opacity: nothing that reaches the batch host (job name, comment, script, file name, argument, environment variable, log line, packed byte) names the project or its work, a benchmark, dataset, model or method, a lane, or a Trinity path. Job names are `a15_cot_ap` plus opaque hex.
   - Tests are `unittest.TestCase` classes in the folder this brief names, with `TMPDIR=W/tmp`. Both runs must pass: `/usr/bin/python3 -m unittest discover` for 3.6-safe modules, and `/scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider` under `bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc` with `HOME=/tmp`, which proves the code needs neither `/home` nor `/data*`.
9. **Reporting.** Keep `W/STATUS.md` current after every step and copy it to `B/events/eff_kit_dryrun/STATUS.md`; a successor resumes from it alone. Write an event (`B/events/eff_kit_dryrun/<UTC>_<RESULT|QUESTION|BLOCKER>_<slug>.md`, at most 20 lines, stamp from `date -u +%Y%m%dT%H%MZ` in the writing command) only for a question, a blocker or the final result. A question states its default, and you continue on that default. Finish with `W/REPORT.md` (what you built, each test command with the tail of its output, what is not proven, the adoption steps for the orchestrator), one RESULT event, and one block of at most 12 lines appended once to RECORD under "## Build results" (slug, branch, head sha, tests and counts, what is not proven, adoption steps). Report failures with their output and never report a check you did not run. You never review your own work for a launch gate. Near 300K tokens finish the step, update STATUS.md and write a RESULT event `rotate`. Your final message to the orchestrator has at most 15 lines.

## Scope

**`tools/orchkit/dryrun.py`.** `dryrun.py run --kit KITDIR --config CONFIG.json --pins PINS.json --map SRC=DST [--map ...] --out OUTDIR -- <argv of the batch entry>` runs the entry exactly as the job would, with four differences and no others:
1. *Sandbox.* bwrap hides `/home`, `/data`, `/data2`, `/data3`, gives a private `/tmp`, and unshares the network. A dry run therefore cannot read NFS or cross the head node, whatever the kit does. `--map` binds staged files from `/scratch` at the job's real logical paths (pool paths, job `/tmp` paths), so the layout equals production.
2. *Config identity.* The dry run takes the production CONFIG file itself and records its sha256. It has no option that edits, overlays or replaces a config field. Substitution happens only behind paths: an `input` or `weights` pin entry with a `standin` may be served by that stand-in, and the report lists every stand-in used.
3. *Transport shims.* A `shims/` directory heads `PATH` with `gcloud`, `gsutil`, `sbatch`, `squeue`, `sacct`, `scontrol`, `nvidia-smi`, `ssh` and `curl`. Each serves from local files named by the pin manifest (URI and generation honoured), appends every call to `OUTDIR/shim_calls.jsonl`, and exits non-zero on a call it has no fixture for, which fails the run with `fail_reason: unplanned_call`.
4. *No GPU.* `CUDA_VISIBLE_DEVICES` is empty. Lines that only a GPU can execute are not proven here; the report lists them under `not_proven`, and they go to the GPU canary (the first steps of the real job).

The stages are the kit's own: stage, admit, prepare over every row or item, first batch, return. Read how three kit families name them before you fix the interface: `REF/trinity-1-3/cont_ops/work/d0/readk/kit/launcher/` (`orchard_job.py`, `orchard_stage.py`, `trace_runtime.py`), `REF/trinity-3-30/k1_ops6/src118/build/` (`batch_entry.py`, `stage_job.py`, `rehearse_v2.py`, `audit_config.py`), and the tree kit `AUD/repo/sealed_tree_b01ce449/launch_s1/` (`job.sh`, `b/`). The dry run must work on a kit of each family without changing the kit.

*Coverage.* The entry runs under a line tracer limited to the kit's own files (port `trace_runtime.py`; no third-party package). The report lists, per file, the line ranges never run. A classification file maps each range to `unit_test` (naming the test), `gpu_only`, or `error_path` with a reason; an unclassified range in a module the entry imported fails the run.

*Output.* `OUTDIR/DRYRUN_REPORT.json` in the `orchkit-dryrun-v1` format of INTERFACES.md, verdict PASS or FAIL.

**`tools/orchkit/lint_config.py`.** `lint_config.py CONFIG.json --schema FAMILY.schema.json [--pins PINS.json]` fails on:
- a schema violation (implement the subset you need with the standard library: type, required, enum, pattern, properties, additionalProperties, items, minimum);
- prose in a field a verifier reads: any string under a key matching `sha|digest|members|inventory|path|uri|object|generation|pin` that is not a 64-hex digest, a clean path, a `gs://` URI or an integer, or that holds a space, `<`, `>`, `...`, `TODO` or `plus`;
- a budget below need: `budgets.<name>.max_bytes < n_items * per_item_bytes`, or `job.time_limit_s < n_items * budgets.time.per_item_s + budgets.time.fixed_s`; a budget with no `per_item` figure fails too, because a constant default caused the tower_sam stop;
- a Trinity or lane path (`/scratch/jjyeung/`, `/home/`, `/data`) or a host name in a config bound for the batch host.

**`tools/orchkit/rowschema.py`.** `rowschema.py check --rows FILE.jsonl[.gz] --profile PROFILE.json --config CONFIG.json` streams the rows once and prints violations per family. A profile states required non-null fields, conditional on config values (with `frame_layout == "duplicate"`, `student_input.fps` and `student_input.total_num_frames` are positive integers), the answer-unit vocabulary, and substrings no row may hold (lane paths, Trinity host names, the opacity word list). Encode the rules of `distill_design/D0_V5_NULL_FRAME_COUNT_20261116.md` and `D0_ROWS_ADMISSION_20261115.md` (read each once); list in REPORT.md any rule those records state that you could not make mechanical. This is a lint that runs when a row store is built and inside the dry run. It is wired into no admission function: changing admission needs an independent review and a new epoch.

## Files you own

`tools/orchkit/dryrun.py`, `lint_config.py`, `rowschema.py`, `shims/`, `tests/test_dryrun.py`, `tests/test_lint_config.py`, `tests/test_rowschema.py`, `tests/fixtures/dryrun/`.

## Tests (folder `tools/orchkit/tests/`)

1. Toy kit end to end (`fixtures/dryrun/toykit/`: an entry that fetches one object through `gsutil`, reads CONFIG, prepares five items, writes a return): verdict PASS, five items prepared, one shim call logged.
2. Five mutants, each FAIL with the named reason: a fixture config whose sha differs from the production config; an unplanned `gsutil cat`; a read of a `/data2` path; two stages that create one directory (the 169477 class); an imported module with an unclassified never-run line.
3. Regressions from the real failures: a config with `anchors.members: "xx/<sha>.png plus ANCHORS_MANIFEST.json"` fails the prose check; `max_bytes` 1.5 GB with 300 items at 10 MB each fails the budget check; a row with `total_num_frames: null` under `frame_layout: duplicate` fails `rowschema`; a row whose metadata holds `/scratch/jjyeung/orch_n30/` fails it.
4. Replay on real kits, from REF copies in `W/ref` only: run `lint_config` over the K1 Part B CONFIG as submitted in 170193 if REF holds it (`REF/trinity-1-18/k1_ops3/work/partb/`), and run the dry run on the D0 read kit and on the K1 package as far as REF's files allow. Report what each run flags and what could not run because REF lacks a file. Fetch nothing.
5. The whole suite passes on `/usr/bin/python3` and under the bwrap run of rule 8.

## Deliverables

Branch `eff/kit-dryrun`; `W/REPORT.md` with the replay results and the list of what a CPU dry run cannot prove; the RESULT event; the result block in RECORD.

## Out of scope

Wiring the report into `launch.py` (orchkit-core reads `DRYRUN_REPORT.json`); any admission function; the GPU canary; changing a live or sealed kit; fetching inputs from another node, Orchard or GCS.

## Review

None required for the tool: it is stricter than admission and admits nothing. Its acceptance check is test 4: the K1 config and the null-frame row must fail.
