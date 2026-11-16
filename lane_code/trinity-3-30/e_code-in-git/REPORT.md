# code-in-git: REPORT (branch eff/code-in-git, head b84804eb390b453f39b4de2a1434f39550b5b528)

The trainer tree is now in Git with its build history. Each of the five builds restores from a commit with its exact seal, and the hourly Git owner publishes every queued `eff/*` head to GitHub. Origin (`git@github.com:jacobyeung/agent_project_distill.git`) holds `eff/code-in-git` at b84804e, verified with `ls-remote` at 12:49Z.

Per the binding verdict, this branch does not save the 30–40 agent-hour rebuild. That figure also covers rows, census, reviews and the Orchard and GPU steps, which Git cannot save. What it adds beyond the hourly `lane-code` snapshot is four things:
- an exact seal restore (`lane-code` misses 26 files of the base tree);
- the build history;
- `git diff` in place of hand-made diffs;
- `eff/*` publishing, as the user asked (2026-11-16).

## Commits (all on origin)
| commit | what |
|---|---|
| 780e5f2 | C1a: `tools/lane_code_sync.sh`, `lane_code_filter.py` and `lane_code_scan.py`, copied unchanged from `B/tools` |
| 1b94e39 | C1b: push-queue step (`--queue-only` runs it alone) plus `tools/tests/test_push_queue.py` |
| 74d14d3 | C1c: accepts a clone link between `<lane>/clone` and `<lane>/repo` (e_orchkit-core uses `clone -> repo`); still refuses links that leave the pair |
| 1cceb98 | C2: `tools/treegit/tree_commit.py`, `seal_of.py` and `tools/tests/test_tree_commit.py` |
| d4f4878, d887701, 11226ab, d34f84d, 593af5f | C3: base, build1, build2, build3 and build3b, one commit each, plus a row in `tools/treegit/SEALS.jsonl` |
| 525f8fe | C4: `tools/treegit/lane_paths.py`, `LANE_PATH_BASELINE.json` (88 files, 159 literals at the C3 head), `PATH_ROOTS.md` and `tools/tests/test_no_lane_paths.py` |
| b84804e | C5: `tools/test_cpu.sh`, `tools/pytest_cpu.ini`, `tools/pytest_cpu_plugin.py`, `requirements-cpu.txt` and `.gitignore` (`*.out`, `*.fifo`, `/*_STATE.md`) |

## C3 import: seals
`b01ce449beffe35b` is the first 16 hex digits of the base tree's `tree_sha256`, not of the tar's sha256 (845b1789…). In every tar name, the hex prefix is likewise the `tree_sha256` prefix. Each commit's `git archive <commit> trainer` export reproduces the tar tree's seal.

I rechecked this at 12:46Z on fresh extractions in `tmp/verify_124652`. Builds b3 and b3b changed `source_seal.py` (only `archive()`), so I resealed those two with their own code: both still match.

| build | commit | tree_sha256 | files | tar sha256 |
|---|---|---|---|---|
| t_b01ce449 (base, job 170111) | d4f48788 | b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 | 792 | 845b1789… |
| tree_r1_build1 | d8877016 | fab2eea87dd744b23951d8a90ac5956f8c8a04d5751715d4bbd0b2fcb9bcd960 | 807 | 411e9329… |
| tree_r1_build2 | 11226ab9 | cd82c5c40b30b9512b6ea9285ea682b6b7b08c9ebe24d922693c439408868254 | 825 | 454a4005… |
| tree_rebuild_b3 | d34f84df | a1f559e2a58a3f317a88506081cf24b86727e646b52c1eb51afce59ba8232022 | 838 | 39b2b5db… |
| tree_rebuild_b3b | 593af5fe | ba0c6ebfd34e44c8565011866ef7913880c95e276d76b6fdcf965da6e942827c | 841 | aa75d294… |

The import committed only the `tree_r1/` subtree. `LEFT_OUT_MEMBERS.txt` lists every member it left out:
- b3: 293 members (277 under `build3/kits`, 15 under `out/`, plus `STATUS.md`);
- b3b: 110 members (97 under `build3b/kits`, 12 under `out/`, plus `STATUS.md`);
- base, b1 and b2: none.

None of the trees contains `__pycache__/`, `artifacts/` or an empty directory. Builds 4 to 6 are not imported (they belong to lane tree_rebuild3).

## Restore procedure (measured 12:45Z on trinity-3-30, local clone source)
```
git clone --branch eff/code-in-git --single-branch <origin> R
git -C R archive <commit> trainer | tar xf - -C X
/scratch/jjyeung/envs/p1cpu/bin/python -I -B R/tools/treegit/seal_of.py --code X/trainer X/trainer   # tree_sha256 must match SEALS.jsonl
```
The run took 1.5 s: 1.2 s to clone, 0.1 s to archive and 0.2 s to seal, giving b01ce449… with 792 files. The pack is 14.8 MiB, so a clone from GitHub at the 8 MB/s cap adds about 2 s of transfer. I did not measure a GitHub clone: the brief forbids ssh to GitHub.

## Tests (commands and output tails)
- `TMPDIR=W/tmp /usr/bin/python3 -m unittest tools.tests.test_push_queue tools.tests.test_tree_commit tools.tests.test_no_lane_paths tools.orchkit.tests.test_util` printed `Ran 31 tests … OK` on Python 3.6.8. `discover -s tools/tests -t .` cannot run: `tools/` has no `__init__.py` (namespace packages), so I named the modules directly.
- `CPU_TEST_TMP=W/tmp/cpu_tests tools/test_cpu.sh tools/orchkit/tests tools/tests` ran under bwrap with /home and /data* hidden and printed `31 passed in 4.58s`. It printed both skips: `tools/tests/test_numeric_tolerance_tiers.py` (imports census.py from /home) and `tools/gtmeasure` (shapely).
- The earlier bwrap pytest run of test_push_queue, test_tree_commit and test_no_lane_paths printed `15 passed` and `6 passed`.
- Plain `p1cpu python -m pytest -q -p no:cacheprovider tools/test_provenance.py` printed `7 passed`. The root has no `conftest.py` and no `pytest.ini`.
- Live queue: `B/tools/lane_code_sync.sh --queue-only` ran three times (12:30, 12:33 and 12:49Z) with rc 0. It published 11 `eff/code-in-git` heads and 8 heads of three other lanes (kit-dryrun 2, orchkit-core 3, state-entrypoint 3). I refused nothing in the end; the one false refusal (the e_orchkit-core link) was fixed by 74d14d3.

## Changes outside the lane folder
I swapped in the new `B/tools/lane_code_sync.sh` (the file at b84804e, unchanged since 74d14d3; sha256 df11e221…). The old copy is at `B/tools/lane_code_sync.sh.prev_20261116T1230Z` (sha256 3c0047f1…). The tmux loop `lane_sync` reads the new script from the 13:26Z run on.

I also removed the false refusal line from `/scratch/jjyeung/distill_sync/PUSH_REFUSED.txt`; the copy before the edit is `PUSH_REFUSED.txt.prev_20261116T1233Z`.

## Not proven
- The full hourly run with the new step, which follows the `lane-code` push. Only `--queue-only` has run live; the first full run is at 13:26Z.
- A restore from GitHub over the network.
- The `cpu_skip` list comes from audit section 5. I did not run the student, materialize or collector directories hermetically, so some listed paths may pass now that the plugin sets the output variables.
- `requirements-cpu.txt`: nothing is installed or built. p1cpu already has av 15.1.0 and peft 0.20.0, so the audit's missing list was too long.

## Adoption steps for the orchestrator
1. Check `sync.log` after the 13:26Z run: it should show `verified GitHub lane-code` followed by `QUEUE done`. To roll back, `mv` the `.prev` copy back.
2. Order the cross-family review of `tree_commit.py` and the queue step.
3. Tell the tree owner lane to commit builds 4 to 6 with `tools/treegit/tree_commit.py --tar … --subdir tree_r1 --expect-seal <tree_sha256>`, and to regenerate `LANE_PATH_BASELINE.json` in the same commit as any path conversion.
4. Decide whether `eff/code-in-git` fast-forwards onto `main` at the next epoch.
