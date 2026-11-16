# Build brief 5 of 8: reader-harness (lane `eff_reader_harness`, branch `eff/reader-harness`, Claude Opus, effort high, size L: 10 to 14 agent-hours)

Build one reader that every read of every export uses, so that a new read is a config with inputs and a plan of several reads runs in one job.

## Why

- Each read today is a new kit: the D0 read kit is a fork of the evalx27 package with a line-range `DIFF.md`, two fix rounds and two reader lanes (`REF/trinity-1-3/cont_ops/work/d0/readk/`); `trinity_read.py` exists in 14 distinct versions with 3 live builds (`AUD/kits/INVENTORY.md` section 2). A new read kit costs an estimated 3 to 6 h before submission.
- The general partition runs one of our jobs at a time, so D0 reads, K1 and VSTI queue one behind another (`B/events/k1_ops3/20261116T1102Z_ORCH_RULING_general_order.md`); the record on packed jobs estimates 1 to 4 h of queue per read (`distill_design/ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md`, line 5). A plan that runs its reads in order inside one job pays that queue once and needs none of the isolation the packed design lacked.
- A read with the wrong frame layout costs 3 to 13 points and looks like a model result.

## Rules (these win over everything else in this brief)

Paths. B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. W = `/scratch/jjyeung/orch_n30/eff_reader_harness` on trinity-3-30, your lane folder (create it; under 5 GB). REF = `/scratch/jjyeung/distill_sync/stage`, a read-only copy of every lane's code (text files up to 512 KB, refreshed hourly; copy what you need into `W/ref` once). AUD = `/scratch/jjyeung/orch_n30/eff_audit`, the audit notes and these briefs (read-only). SK = `AUD/briefs/skeleton`. RECORD = `/data2/jjyeung/agent_project_data/distill_design/EXPERIMENT_EFFICIENCY_20261116.md`.

1. **Read first**, as named files: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md` (it wins over this brief), `B/tools/CLAUDE_LANE_RULES.md`, `B/tools/LANE_RULES.md`, then RECORD (your change is number 5; `AUD/briefs/INTERFACES.md` holds the formats shared with the other builds).
2. **Host.** You run on trinity-3-30. If `hostname -s` prints `trinity`, stop and tell the orchestrator.
3. **Never touch running work.** You change nothing outside W. Running work is: Orchard jobs 170111 (D0 training), 170209 (VSTI native read) and the K1 own-phase job; the sealed kits and inputs they use (trainer tree b01ce449, row store v5 4af43b40, the confirmed D0 read kit, VSTI kit V1c dc40cf60, the K1 package and manifest v2, every object on an Orchard pool or in GCS); every other lane's folder under `/scratch/jjyeung/orch_n30/` on any node and its tmux sessions; the IO governor under `/data3/jjyeung/orch_n13_20261026/io_governor/`; the scripts in `B/tools/`; other lanes' event folders; the `/home/jjyeung/agent_project_distill` working tree; `/scratch/jjyeung/distill_sync/`. Your code replaces nothing in place: a new version of a live script is a new file on your branch, and the orchestrator adopts it at the next epoch.
4. **Forbidden.** No ssh of any kind (Trinity, Orchard, GitHub), no Slurm command, no GPU, no governed or ungoverned copy to or from `/home` or `/data*`, no stream registered with the governor, no Gemini, OpenRouter or NV call, no package install or download. No recursive grep/find/du/ls -R and no built-in Grep or Glob on `/home` or `/data*`. Tests reach the outside world only through fakes you write.
5. **NFS reads.** From `/home` and `/data*` read only the files this brief names, each once, in bounded parts, never in a loop. You write there only the event files and the one result block named under rule 9.
6. **Git, one narrow exception.** The deliverable is a branch, so the orchestrator allows Git inside `W/clone` only, on local disk: one `git clone --branch main --single-branch /scratch/jjyeung/distill_sync/repo W/clone`, then `git -C W/clone` with `checkout -b eff/reader-harness`, `config user.name` / `user.email` (copy the values from the `[user]` section of `/scratch/jjyeung/distill_sync/repo/.git/config`), `add <named paths>`, `commit`, and the read-only `status`, `diff`, `log`, `show`, `rev-parse`. Forbidden: any Git command whose repository or working directory lies under `/home` or `/data*`; `push`, `fetch`, `pull`, `remote`; `add -A` or `add .`; force, rebase, reset or amend of a commit already queued; worktrees. Commit messages are plain: no attribution or co-author lines. If the orchestrator withholds this exception, deliver `W/clone` as a plain directory with `W/COMMITS.md` (one message per intended commit), and the Git owner commits it.
7. **Commit and push often (USER 2026-11-16).** Commit at every passing test milestone and at least once per hour of work. After each commit append one line `<UTC> eff/reader-harness <full sha>` to `W/PUSH_QUEUE.txt`. The Git owner (lane code_sync) publishes each queued head to origin as `eff/reader-harness`. You never push, and nothing of yours goes to `main`.
8. **Code rules.**
   - Shared helpers: copy `SK/tools/orchkit/__init__.py`, `util.py` and `tests/test_util.py` byte for byte into `W/clone/tools/orchkit/` (sha256 in INTERFACES.md). Import from `util.py`, never edit it (lane eff_orchkit_core owns its changes), and never write your own sha, canonical-JSON, atomic-write, process-identity or locked-append helper.
   - Python 3.6: every module that the batch host or `/usr/bin/python3` (3.6.8) runs uses the standard library only, with no `dataclasses`, no walrus, no `subprocess.run(capture_output=, text=)`, no `Path.is_relative_to`, no `from __future__ import annotations`.
   - No deletion: code and commands never remove a file (no `rm`, `unlink`, `os.remove`, `shutil.rmtree`, `git rm`, `git clean`). Write into fresh paths and leave temporary files in place. The rm_guard hook blocks any shell command that contains a deletion call, including a heredoc that writes one, and queues it for the user: create source files with the Write tool.
   - Opacity: nothing that reaches the batch host (job name, comment, script, file name, argument, environment variable, log line, packed byte) names the project or its work, a benchmark, dataset, model or method, a lane, or a Trinity path. Job names are `a15_cot_ap` plus opaque hex.
   - Tests are `unittest.TestCase` classes in the folder this brief names, with `TMPDIR=W/tmp`. Both runs must pass: `/usr/bin/python3 -m unittest discover` for 3.6-safe modules, and `/scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider` under `bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc` with `HOME=/tmp`, which proves the code needs neither `/home` nor `/data*`.
9. **Reporting.** Keep `W/STATUS.md` current after every step and copy it to `B/events/eff_reader_harness/STATUS.md`; a successor resumes from it alone. Write an event (`B/events/eff_reader_harness/<UTC>_<RESULT|QUESTION|BLOCKER>_<slug>.md`, at most 20 lines, stamp from `date -u +%Y%m%dT%H%MZ` in the writing command) only for a question, a blocker or the final result. A question states its default, and you continue on that default. Finish with `W/REPORT.md` (what you built, each test command with the tail of its output, what is not proven, the adoption steps for the orchestrator), one RESULT event, and one block of at most 12 lines appended once to RECORD under "## Build results" (slug, branch, head sha, tests and counts, what is not proven, adoption steps). Report failures with their output and never report a check you did not run. You never review your own work for a launch gate. Near 300K tokens finish the step, update STATUS.md and write a RESULT event `rotate`. Your final message to the orchestrator has at most 15 lines.

## Scope: `tools/orchkit/reader/`

**`read.py`, the driver.** `read.py run --plan PLAN.json --pins PINS.json --out OUT/` executes a list of `orchkit-read-v1` configs in order. For each read it loads the export, builds prompts from the frozen item list, generates, scores, and writes predictions and one receipt (`{read_id, export sha, items sha, scorer digests, frames, counts, metrics, state}`). A read that fails is recorded with its traceback and the plan continues; a rerun skips every read whose receipt exists. The generator sits behind one small interface, so tests drive the whole plan with a deterministic stub and no model.

**Frame guard.** The driver compares the read's `frames.layout` and `frames.count` with the layout the export recorded at training and refuses a mismatch unless `layout_override_reason` is set; the receipt then carries the reason.

**`score/`, the scorers.** Port, without changing their arithmetic, the reviewed scorers of the D0 read kit: `REF/trinity-1-3/cont_ops/work/d0/readk/kit/reader/` (`chain.py`, `paired_read.py`, `official_adapter.py`, `official_score.py`, `records.py`, `worker.py`) and the native reader of `REF/trinity-1-18/trin_read/build_t6/trinity_read.py`. Keep the kit's rule that the official scorer source is a pinned member checked by digest before use: the main repository stays the authority for benchmark scoring, and this harness calls that source and never rewrites it. State in REPORT.md, per ported function, the source file and lines.

**`verdict.py`, the registered rules.** Port `stop_rule()` and the F1/F2 functions of `REF/trinity-1-3/cont_ops/work/d0/readk/f1f2.py`. Each rule function names the registered record it implements and that record's sha256, loads the record as the pinned member with role `record`, and refuses to return a verdict when the member's sha256 differs (use `cite.check_member` if lane eff_review_gate has delivered it; otherwise compare with `util.sha256_file` and say so). A record amendment then forces a code change and its review, which is the intent. Read `distill_design/D0_STOP_RULE_20261116.md` and `NEXT_LEG_INIT_RULE_20261116.md` once each; implement the stop rule as amended, and implement the init rule only if it is mechanical as written (list what is not).

**`plan.schema.json`** and `examples/plan_two_reads.json`.

**Runtime.** Modules under `reader/` run inside the model environment and may use its Python; anything the batch bootstrap runs before that environment is active stays 3.6-safe. The packed reader passes the opacity check: item identifiers, family names and scorer names bound for the batch host are opaque tokens whose meanings stay in a Trinity-side map, as in the existing kit.

## Files you own

`tools/orchkit/reader/` (all of it) and `tools/orchkit/tests/test_reader_*.py`, `tests/fixtures/reader/`.

## Tests (folder `tools/orchkit/tests/`)

1. The D0 read kit's own tests (`REF/trinity-1-3/cont_ops/work/d0/readk/tests/`), ported, all passing.
2. Parity: for every saved prediction file you can find on this node (in REF, in `/scratch/jjyeung/orch_n30/review_a0d/`, `/scratch/jjyeung/orch_n30/a0_design/`, or named by a design record as stored on trinity-3-30), the new scorer reproduces the banked number exactly. Targets: VSTI f17 66.95 and P1 m200 68.71; official VSI-Bench direct at step 544, six tasks 68.77; ReVSI direct, five categories 64.94; dev-S1 parent 71.64. List which targets had a prediction file here and which did not. Fetch nothing from another node, Orchard or GCS; a missing file is a line in REPORT.md and an input the orchestrator can order through the governor.
3. Plan runner with the stub generator: three reads, the second raises; reads one and three complete with receipts; a rerun executes only the second.
4. Frame guard: a mismatch refuses; an override passes and is recorded.
5. Rule guard: a changed record member refuses; the amended stop rule gives the registered verdict on each worked example the record contains.
6. The packed reader holds no word of the opacity list.

## Deliverables

Branch `eff/reader-harness`; `W/REPORT.md` with the parity table and the port map; the RESULT event; the result block in RECORD.

## Out of scope

Launch, staging and return (orchkit-core); any new scoring rule, routing rule or change to a registered rule; the D0 milestone reads in flight, which keep the confirmed read kit; concurrent steps in one job; running a model.

## Review

One independent review before any number from this harness is reported, because it scores. The reviewer starts from the parity table. Ask for it in the RESULT event.
