# Build brief 1 of 8: code-in-git (lane `eff_code_in_git`, branch `eff/code-in-git`, Claude Opus, effort high, size L: 10 to 14 agent-hours)

Put the trainer tree and the Git owner's publishing step under version control, so that a node loss costs a `git clone` and every accepted build is one commit pushed to GitHub within the hour.

## Why

- The live trainer (792 files) exists only as tars and lane folders. When trinity-2-18 died, the rebuild plan priced the loss: "The code itself does not survive, except one file (`r1_contract.py`)" and "Rebuild to A0 launch: about 30 to 40 agent-hours of builds and reviews, in three parallel lanes, about 1.5 to 2 days of wall clock" (`distill_design/NEXT_LEG_REBUILD_PLAN_20261115.md`, section Answer).
- The tree's history is four full-tree tars and hand-made diffs (`/scratch/jjyeung/orch_n30/tree_rebuild/out/`: `tree_r1_build1_fab2eea8.tar`, `tree_r1_build2_cd82c5c4.tar`, `tree_rebuild_b3_a1f559e2.tar`, `tree_rebuild_b3b_ba0c6ebf.tar`, `DIFF_3b_vs_a1f559e2.diff`).
- The user asked on 2026-11-16: "You should be committing and pushing code frequently so we don't lose history." The hourly sync publishes a filtered snapshot on branch `lane-code`; it carries no build history, and it cannot reproduce a seal because it drops files above 512 KB.
- Detail: `AUD/repo/NOTES.md` sections 1, 2 and 5.

{{COMMON}}

## Scope: five commits, in this order, each one landable alone

**C1. Publishing queue for the Git owner.** `main` does not hold the sync script yet (it lives in `B/tools/` and on branch `lane-code`). Copy `B/tools/lane_code_sync.sh`, `lane_code_filter.py` and `lane_code_scan.py` (three small files, each read once) into `tools/` and commit them unchanged, so that the next commit shows only your step. Then add a step to `tools/lane_code_sync.sh` on your branch (the live copy in `B/tools/` stays untouched; the orchestrator adopts yours). After the `lane-code` push, the step reads every `/scratch/jjyeung/orch_n30/eff_*/PUSH_QUEUE.txt` and, for each line `<UTC> <branch> <sha>` not yet listed in `$S/PUSH_DONE.txt`:
- accepts only a branch matching `^eff/[a-z0-9-]+$` and a clone at `<that lane folder>/clone`; refuses `main` and anything else with one log line;
- fetches the branch from the clone (local disk) into the Git owner's clone, and checks that the fetched head equals the queued sha or descends from it;
- runs the existing secret scan (`lane_code_scan.py`) over the files the branch changes against `main`; a flagged file blocks that branch and is named in the log and in one BLOCKER event;
- pushes `origin <sha>:refs/heads/<branch>` with a 300 s timeout and no force (a non-fast-forward fails and is reported), verifies with `ls-remote`, and appends the line to `PUSH_DONE.txt`.
The step never checks out a branch, never touches `/home`, and never writes `main`.

**C2. `tools/treegit/tree_commit.py`: accepting a build is one command.** `tree_commit.py --repo CLONE --branch BR --tree DIR|--tar FILE --build NAME --expect-seal HEX [--prefix trainer]`:
- computes the tree's seal with the tree's own code, never a reimplementation: `tree_sha256 = digest(inventory(root))` from `student_pilot/source_seal.py` and `student_pilot/p3_provenance.py` (read them in `AUD/repo/sealed_tree_b01ce449/student_pilot/`; the inventory maps each relative path to its sha256, skips `.git`, `__pycache__` and `artifacts`, and refuses links and files above 16 MB), run under `/scratch/jjyeung/envs/p1cpu/bin/python`, and refuses when the digest does not start with `--expect-seal`;
- builds the commit with Git plumbing and no working tree: a private index (`GIT_INDEX_FILE` under `W/tmp`), `add -f` of the build directory so no ignore pattern drops a member (`.gitignore` ignores `*.png`, `*.npz`, `out/`, `data/`, `*.log`, `scratch/`), `write-tree`, then the parent's root tree with the `trainer` entry replaced (`ls-tree`, `mktree`), `commit-tree`, and `update-ref` with the old value given, so a concurrent move of the branch fails;
- appends `{utc, build, seal, tar_sha256, parent, commit}` to `tools/treegit/SEALS.jsonl` in the same commit (the file sits outside `trainer/`, so it never changes a seal);
- writes the message `trainer: <build> seal <digest> tar <sha256>`;
- verifies before it returns: `git archive <commit> trainer` extracted into a fresh directory reproduces the seal. A tree member that Git cannot hold exactly (a mode the seal reads, a symlink, an empty directory the seal counts) makes the command refuse and name the member.
The plumbing commands are allowed for you inside `W/clone` and inside throwaway repositories under `W/tmp`.

**C3. Import the history with that command.** Base: `/scratch/jjyeung/orch_n30/tree_rebuild/work/t_b01ce449beffe35b.tar` (9,881,600 bytes; the sealed tree that job 170111 runs; read it, never change it). First establish what `b01ce449beffe35b` is (the leading hex of `tree_sha256`, or of the tar's sha256) and state it in REPORT.md; `--expect-seal` always takes the computed `tree_sha256`. Then the four build tars listed under Why, in build order, each as one commit with its own seal. Those tars hold more than a tree (`tree_r1/` plus, from build 3 on, `build3/kits` and the like; 88 MB against 9.9 MB for the base): commit the `tree_r1/` subtree only, and list in REPORT.md every member left out. A member the seal skips (`artifacts/`, `__pycache__/`) stays out of Git. Builds 4 to 6 live on trinity-1-3 under the running lane tree_rebuild3: do not import them from REF (REF is filtered and cannot reproduce a seal); the Git owner commits them with `tree_commit.py` when that lane next delivers a build.

**C4. Lane-path ratchet.** 70 files of the sealed tree hold literal `/scratch/jjyeung/orch_cd/...` paths on the dead node (`student_pilot/mdg_eval.py:20`, `mask_grounding_head.py:17`). Add `tools/tests/test_no_lane_paths.py`: it scans `trainer/**/*.py` for the literals `/scratch/jjyeung/orch_`, `/home/jjyeung/` and `/data2/jjyeung/`, compares the per-file counts with `tools/treegit/LANE_PATH_BASELINE.json` (generated at the head of C3), and fails when a file's count rises or a new file appears. Write `tools/treegit/PATH_ROOTS.md` (at most 40 lines): the resolver the next epoch's tree uses (one root from the kit manifest or the environment variable `DISTILL_LANE_ROOT`, no `sys.path` edits across lanes). You change no file under `trainer/`: the conversion belongs to the tree owner lane at its next build, and the ratchet makes it measurable.

**C5. Hermetic CPU tests without changing any gate.** Add `tools/test_cpu.sh`, `tools/pytest_cpu.ini`, `tools/pytest_cpu_plugin.py` and `requirements-cpu.txt`. The script runs pytest under the bwrap line of rule 8 with `-c tools/pytest_cpu.ini -p pytest_cpu_plugin`; the plugin puts the repository root on `sys.path`, points `H5_TEST_OUTPUT`, `COMPACT_TEST_OUTPUT`, `STUDENT_DATASET_TEST_OUTPUT` and `STUDENT_PILOT_TEST_OUTPUT` at a temporary directory, and skips (with the reason printed) tests in directories listed as reading `/home` or `/data*`. Plain `pytest` anywhere in the repository behaves exactly as before, because nothing is added at the root: no `conftest.py`, no `pytest.ini`. `requirements-cpu.txt` lists the packages the audit found missing (`AUD/repo/NOTES.md` section 5); you write the list and the build command, and you install nothing. Add `*.out`, `*.fifo` and `/*_STATE.md` to `.gitignore`.

## Files you own

`tools/lane_code_sync.sh`, `tools/lane_code_filter.py`, `tools/lane_code_scan.py` (copied unchanged; you add the queue step only), `tools/treegit/`, `trainer/` (through `tree_commit.py` only), `tools/tests/test_push_queue.py`, `tools/tests/test_tree_commit.py`, `tools/tests/test_no_lane_paths.py`, `tools/test_cpu.sh`, `tools/pytest_cpu.ini`, `tools/pytest_cpu_plugin.py`, `requirements-cpu.txt`, `.gitignore`. You touch nothing under `collector/`, `gt_adapters/`, `preparers/`, `materialize/`, `student/`, and neither `CLAUDE.md` nor `AGENTS.md`.

## Tests (folder `tools/tests/`)

1. Queue step, against throwaway repositories under `W/tmp` standing in for origin, the Git owner's clone and a builder clone. For this test only, `git init`, `fetch` and `push` are allowed between those throwaway repositories; no path or remote outside `W/tmp` is ever named, and GitHub is never contacted. Cases: refuses `main`; refuses a branch outside `^eff/`; refuses a clone path outside the pattern; publishes a fast-forward; reports a non-fast-forward without forcing; treats a repeated line as done; a planted fake secret blocks the branch and names the file.
2. `tree_commit.py` on a throwaway repository: an added, a changed and a removed file, a mode change, and members named `x.png` and `out/y.json` all land; every path outside the prefix keeps its blob id; a wrong `--expect-seal` refuses; a branch that moved between read and `update-ref` refuses.
3. Import: for the base and each of the four builds, `tree_sha256` of the `git archive` export equals `tree_sha256` of the tar's tree. State in REPORT.md the five commit ids, the five digests and how each relates to the hex in its tar name.
4. Ratchet: passes at the head of C3; fails when a test fixture adds one literal.
5. `tools/test_cpu.sh tools/orchkit/tests tools/tests` passes with `/home` and `/data*` hidden; `pytest tools/test_provenance.py` run the plain way still reports 7 passed.

## Deliverables

Branch `eff/code-in-git` in `W/clone` with commits C1 to C5 queued for the Git owner; `W/REPORT.md` with the restore procedure ("clone origin, check out the commit, `git archive`, verify the seal") measured in minutes on this node; the RESULT event; the result block in RECORD.

## Out of scope

Editing tree files or converting lane paths; importing builds 4 to 6; moving or archiving old modules; any Git command on `/home`; pushing; landing on `main`; cleaning the `/home` working tree (the orchestrator and the user handle its four untracked files); installing an environment.

## Review

None required: nothing here touches admission, legality or scoring. The seal-equality test in 3 is the acceptance check, and the orchestrator reads it in REPORT.md before adopting C1.
