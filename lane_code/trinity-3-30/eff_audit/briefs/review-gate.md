# Build brief 4 of 8: review-gate (lane `eff_review_gate`, branch `eff/review-gate`, Claude Opus, effort high, size M: 4 to 5 agent-hours)

Make "one review suffices" executable: a reviewer writes a machine-readable verdict with reproduction commands, a script confirms a fix that stays inside the verdict, and every kit cites its registered rule by hash instead of restating it.

## Why

- The project rule is one review: "Only a change that touches admission, legality or scoring needs an independent review, and one review suffices" (`/home/jjyeung/agent_project_distill/AGENTS.md`, section Provenance). The GO text turned it into a loop: "If it demands fixes, apply them and get one more confirmation first" (`B/events/cont_ops/20261115T2109Z_ORCH_GO_d0_job_a.md`, line 2). The D0 derive kit then went through rounds r1 to r12, and seven second-reader lanes (vsti2, d0r2, k1b3, k1b4, rows2, contracts2, an2) confirmed without finding a new blocker.
- Measured wait on critical paths in 18 h: 19 min (VSTI), 25 min (D0 read kit), about 45 min (k1b3) and about 50 min (k1b4). A reviewer lane exits after its verdict, so the K1 confirmation had no reader: "review_k1b2 has not confirmed batch fc9ed8a8 and looks idle, so the conditional GO cannot fire" (`B/events/k1_ops3/20261116T0854Z_BLOCKER_reader_silent_on_fixes.md`).
- One registered stop rule was paraphrased four times (a GO, a ruling, two briefs), and the read kit implemented a paraphrase (`AUD/process/NOTES.md`, "Rule restatement drift").
- First reviews that reproduce find the blockers; confirmations confirm (`AUD/process/NOTES.md`, "Pattern").

## Rules (these win over everything else in this brief)

Paths. B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. W = `/scratch/jjyeung/orch_n30/eff_review_gate` on trinity-3-30, your lane folder (create it; under 5 GB). REF = `/scratch/jjyeung/distill_sync/stage`, a read-only copy of every lane's code (text files up to 512 KB, refreshed hourly; copy what you need into `W/ref` once). AUD = `/scratch/jjyeung/orch_n30/eff_audit`, the audit notes and these briefs (read-only). SK = `AUD/briefs/skeleton`. RECORD = `/data2/jjyeung/agent_project_data/distill_design/EXPERIMENT_EFFICIENCY_20261116.md`.

1. **Read first**, as named files: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md` (it wins over this brief), `B/tools/CLAUDE_LANE_RULES.md`, `B/tools/LANE_RULES.md`, then RECORD (your change is number 4; `AUD/briefs/INTERFACES.md` holds the formats shared with the other builds).
2. **Host.** You run on trinity-3-30. If `hostname -s` prints `trinity`, stop and tell the orchestrator.
3. **Never touch running work.** You change nothing outside W. Running work is: Orchard jobs 170111 (D0 training), 170209 (VSTI native read) and the K1 own-phase job; the sealed kits and inputs they use (trainer tree b01ce449, row store v5 4af43b40, the confirmed D0 read kit, VSTI kit V1c dc40cf60, the K1 package and manifest v2, every object on an Orchard pool or in GCS); every other lane's folder under `/scratch/jjyeung/orch_n30/` on any node and its tmux sessions; the IO governor under `/data3/jjyeung/orch_n13_20261026/io_governor/`; the scripts in `B/tools/`; other lanes' event folders; the `/home/jjyeung/agent_project_distill` working tree; `/scratch/jjyeung/distill_sync/`. Your code replaces nothing in place: a new version of a live script is a new file on your branch, and the orchestrator adopts it at the next epoch.
4. **Forbidden.** No ssh of any kind (Trinity, Orchard, GitHub), no Slurm command, no GPU, no governed or ungoverned copy to or from `/home` or `/data*`, no stream registered with the governor, no Gemini, OpenRouter or NV call, no package install or download. No recursive grep/find/du/ls -R and no built-in Grep or Glob on `/home` or `/data*`. Tests reach the outside world only through fakes you write.
5. **NFS reads.** From `/home` and `/data*` read only the files this brief names, each once, in bounded parts, never in a loop. You write there only the event files and the one result block named under rule 9.
6. **Git, one narrow exception.** The deliverable is a branch, so the orchestrator allows Git inside `W/clone` only, on local disk: one `git clone --branch main --single-branch /scratch/jjyeung/distill_sync/repo W/clone`, then `git -C W/clone` with `checkout -b eff/review-gate`, `config user.name` / `user.email` (copy the values from the `[user]` section of `/scratch/jjyeung/distill_sync/repo/.git/config`), `add <named paths>`, `commit`, and the read-only `status`, `diff`, `log`, `show`, `rev-parse`. Forbidden: any Git command whose repository or working directory lies under `/home` or `/data*`; `push`, `fetch`, `pull`, `remote`; `add -A` or `add .`; force, rebase, reset or amend of a commit already queued; worktrees. Commit messages are plain: no attribution or co-author lines. If the orchestrator withholds this exception, deliver `W/clone` as a plain directory with `W/COMMITS.md` (one message per intended commit), and the Git owner commits it.
7. **Commit and push often (USER 2026-11-16).** Commit at every passing test milestone and at least once per hour of work. After each commit append one line `<UTC> eff/review-gate <full sha>` to `W/PUSH_QUEUE.txt`. The Git owner (lane code_sync) publishes each queued head to origin as `eff/review-gate`. You never push, and nothing of yours goes to `main`.
8. **Code rules.**
   - Shared helpers: copy `SK/tools/orchkit/__init__.py`, `util.py` and `tests/test_util.py` byte for byte into `W/clone/tools/orchkit/` (sha256 in INTERFACES.md). Import from `util.py`, never edit it (lane eff_orchkit_core owns its changes), and never write your own sha, canonical-JSON, atomic-write, process-identity or locked-append helper.
   - Python 3.6: every module that the batch host or `/usr/bin/python3` (3.6.8) runs uses the standard library only, with no `dataclasses`, no walrus, no `subprocess.run(capture_output=, text=)`, no `Path.is_relative_to`, no `from __future__ import annotations`.
   - No deletion: code and commands never remove a file (no `rm`, `unlink`, `os.remove`, `shutil.rmtree`, `git rm`, `git clean`). Write into fresh paths and leave temporary files in place. The rm_guard hook blocks any shell command that contains a deletion call, including a heredoc that writes one, and queues it for the user: create source files with the Write tool.
   - Opacity: nothing that reaches the batch host (job name, comment, script, file name, argument, environment variable, log line, packed byte) names the project or its work, a benchmark, dataset, model or method, a lane, or a Trinity path. Job names are `a15_cot_ap` plus opaque hex.
   - Tests are `unittest.TestCase` classes in the folder this brief names, with `TMPDIR=W/tmp`. Both runs must pass: `/usr/bin/python3 -m unittest discover` for 3.6-safe modules, and `/scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider` under `bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc` with `HOME=/tmp`, which proves the code needs neither `/home` nor `/data*`.
9. **Reporting.** Keep `W/STATUS.md` current after every step and copy it to `B/events/eff_review_gate/STATUS.md`; a successor resumes from it alone. Write an event (`B/events/eff_review_gate/<UTC>_<RESULT|QUESTION|BLOCKER>_<slug>.md`, at most 20 lines, stamp from `date -u +%Y%m%dT%H%MZ` in the writing command) only for a question, a blocker or the final result. A question states its default, and you continue on that default. Finish with `W/REPORT.md` (what you built, each test command with the tail of its output, what is not proven, the adoption steps for the orchestrator), one RESULT event, and one block of at most 12 lines appended once to RECORD under "## Build results" (slug, branch, head sha, tests and counts, what is not proven, adoption steps). Report failures with their output and never report a check you did not run. You never review your own work for a launch gate. Near 300K tokens finish the step, update STATUS.md and write a RESULT event `rotate`. Your final message to the orchestrator has at most 15 lines.

## Scope

**`tools/orchkit/fixcheck.py`.** `fixcheck.py --old KIT_OLD --new KIT_NEW --verdict VERDICT.json --protected PROTECTED.json --out FIXCHECK.json` decides whether a fix needs a reader. The verdict format is `orchkit-verdict-v1` in INTERFACES.md. The script:
1. diffs the two kits file by file and hunk by hunk (`difflib`);
2. requires every changed hunk to overlap a finding's file and line range (three lines of context allowed) or to be a regenerated manifest that verifies against the new kit;
3. escalates any changed hunk in a protected file, even inside a finding. `PROTECTED.json` lists, per kit family, the path patterns of admission, legality and scoring code and of answer or label sources; a kit family with no list is protected as a whole;
4. requires at least one changed hunk for every `blocker` and `fix` finding;
5. runs each finding's `repro` and the verdict's `repro_suite` against the new kit inside the bwrap sandbox of rule 8 with the network unshared, and compares each result with `expect`.
The outcome is one of `CONFIRMED_MECHANICAL`, `NEEDS_READER` (naming the hunks), `UNADDRESSED` (naming the findings) or `REPRO_FAILED` (with output), bound to the sha256 of the old kit, the new kit and the verdict. The script confirms; it never reviews: anything it cannot bound goes to a reader.

**`tools/orchkit/cite.py`.** `cite.py stamp RECORD.md` prints `{path, sha256}` for a registered record. `cite.py verify --config CONFIG.json --pins PINS.json` checks that every `records[]` entry of a config equals the pin entry with role `record`. `cite.check_member(path, sha256)` is the job-side call a verdict function makes before it applies a rule, and it refuses on mismatch (3.6-safe, relative import of `util`). `cite.py lint-text FILE.md` flags a GO, ruling or brief that names a registered record without its sha256, so the text points at the rule instead of restating it.

**`docs/REVIEW_CHECKLIST.md`.** At most 40 lines, one check per line: what to check, the command that checks it, the event that taught it. Build it from the findings of this week's reviews and failures: `AUD/incidents/INCIDENTS.md` rows 4, 5, 8, 11, 13 and 25; `B/events/review_rows2/20261115T2235Z_RESULT_d0_v3_verdict.md`; the four verdict files `B/events/review_vsti/REVIEW_VERDICT_VSTI_KIT.md`, `B/events/review_d0r/REVIEW_VERDICT_D0_READ_KIT.md`, `B/events/review_k1b2/REVIEW_VERDICT_K1_PART_B.md` and `B/events/review_contracts2/REVIEW_VERDICT_CONTRACTS_R4.md` (each read once); `distill_design/ROUTED_READ_PIN_GRAPH_AUDIT_20261114.md` (first 60 lines). Where a command of kit-dryrun or orchkit-core checks the item (`dryrun.py`, `lint_config.py`, `rowschema.py`, `pins.py verify`), name that command, so the reviewer runs the check and does not re-derive it.

**`agent/templates/`.**
- `REVIEW_BRIEF.md`: the reviewer reproduces before it reads (runs the dry run and the kit's tests), reviews the full diff once against the checklist, writes `VERDICT.json` beside its verdict text, and stays alive for up to 3 h after the verdict to confirm fixes to its own kit, waking on the operator's fix event.
- `GO.md`: the job token, `kit_pins_sha256`, `config_sha256`, the records cited by sha256, and conditions written as file predicates a script can test (a reviewer's `CONFIRMED_<sha>.md`, or `FIXCHECK.json` with `CONFIRMED_MECHANICAL` for that sha; inputs verified; slot free; deadline). It holds no sentence that asks for another confirmation after a fix.
- `VERDICT.schema.json`.

**`W/PROPOSED_RULE_one_review.md`.** The rule text for the orchestrator to adopt in `B/tools/LANE_RULES.md` and its GO messages, at most 15 lines: one independent review per kit that changes admission, legality or scoring; a fix is confirmed by `fixcheck.py`; a reader confirms only when `fixcheck.py` says `NEEDS_READER`; texts cite records by path and sha256. You edit neither `LANE_RULES.md` nor `AGENTS.md`.

## Files you own

`tools/orchkit/fixcheck.py`, `cite.py`, `tests/test_fixcheck.py`, `tests/test_cite.py`, `tests/fixtures/fixcheck/`, `docs/REVIEW_CHECKLIST.md`, `agent/templates/GO.md`, `agent/templates/REVIEW_BRIEF.md`, `agent/templates/VERDICT.schema.json`.

## Tests (folder `tools/orchkit/tests/`)

1. Synthetic kit pairs: a fix inside a finding gives `CONFIRMED_MECHANICAL`; an extra hunk elsewhere gives `NEEDS_READER` naming it; a hunk in a protected file gives `NEEDS_READER`; an untouched blocker gives `UNADDRESSED`; a failing reproduction gives `REPRO_FAILED`; a regenerated manifest passes only when it verifies.
2. Replay on this week's fix rounds, from REF copies in `W/ref` only: the K1 Part B rounds (`REF/trinity-1-18/review_k1b2/batch` against `REF/trinity-1-18/review_k1b3/newbatch`) and the D0 read kit's two fix rounds (`REF/trinity-1-3/cont_ops/work/d0/readk/` with `FIX1.md`, `DIFF_FIX1.patch`, `FIX2.md`, `DIFF_FIX2.patch`). Write each `VERDICT.json` by hand from the reviewer's verdict text (the two verdict files named above), run `fixcheck.py`, and report per round what it rules and what the second reader ruled. This table is the evidence for adopting the rule: it shows how many of the confirmation lanes the script would have replaced, and whether it ever confirms what a reader refused.
3. `cite.py`: stamp, verify, a changed record refuses, `lint-text` flags a brief that names `D0_STOP_RULE_20261116.md` without a sha256 and passes one that carries it.
4. The suite passes on `/usr/bin/python3` and under the bwrap run of rule 8.

## Deliverables

Branch `eff/review-gate`; `W/PROPOSED_RULE_one_review.md`; `W/REPORT.md` with the replay table; the RESULT event; the result block in RECORD.

## Out of scope

Who reviews admission, legality or scoring changes (always an independent reader); editing `LANE_RULES.md`, `AGENTS.md`, `CLAUDE.md` or any live GO; the lease that keeps a reviewer alive (orch-watch builds it; your template only states the 3 h window).

## Review

One independent review of `fixcheck.py` before the orchestrator adopts the rule, because the script decides when a second reader is skipped. Ask for it in the RESULT event and attach the replay table.
