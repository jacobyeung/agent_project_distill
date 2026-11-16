# Repository efficiency audit (angle: repository), trinity-3-30, 2026-11-16
Clone: /scratch/jjyeung/orch_n30/eff_audit/repo/clone (HEAD a38bc5b = origin/main, last commit 2026-11-09 20:11 -0500).
Branch eff-audit-pkg-configurable (ee5604c) holds the PKG change; patch: 0001-Supervisor-DISTILL_COLLECTOR_PKG-selects-the-collect.patch.
Sealed trainer tree extracted read-only for inspection: sealed_tree_b01ce449/ (from tree_rebuild/work/t_b01ce449beffe35b.tar).
Test logs: tests/*.txt; runner tests/run.sh (bwrap hides /home, /data*, /tmp).

## 1. The live code is not in the repository (largest loss)
- Repo code commits stop 10-29 (tools/rung1_build); since then only handoff docs, CLAUDE/AGENTS edits, codex_dispatch.sh.
  Per-area last commit: collector 09-19, gt_adapters/preparers/materialize/student/* 09-18..09-25, tools/rung1_build 10-29, docs 11-09.
- The trainer tree in use (792 files, student_pilot/ + launch_s1/ + generator/ + verifykit/ ...) lives only as
  /data3/jjyeung/distill_src_archive/t_*.tar (3 tars, ~9.9 MB each) and lane folders. Its own AGENTS.md: "Work only in this tiny repository";
  it is versioned by student_pilot/source_seal.py (file-inventory sha256), not Git.
- tree_rebuild lane reinvents VCS: out/ holds tree_r1_build1_fab2eea8.tar, ..._build2_cd82c5c4.tar, tree_rebuild_b3_a1f559e2.tar,
  tree_rebuild_b3b_ba0c6ebf.tar, DIFF_3b_vs_a1f559e2.diff, TREE.diff, TREE_FILES.sha256 (5 builds, 4 full-tree tars, hand diffs).
- Cost of the 2-18 loss (NEXT_LEG_REBUILD_PLAN_20261115.md l.11,15): "The code itself does not survive, except one file (r1_contract.py).
  Every change can be re-specified from text; none can be copied." "Rebuild to A0 launch: about 30 to 40 agent-hours ... about 1.5 to 2 days of wall clock".
  Lanes spawned for it (LANES.txt): tree_rebuild x3, rows_rebuild x3, contracts_rebuild x2, recover_k1, recover_map2, seal_plan + reviews.
- Sealed tree pins dead-node lane paths: 70 files reference /scratch/jjyeung/orch_cd/* (stageb_merge 27, evalx 12, derivgen 12, ground_rows 10,
  leg_s1_tree 9, ttower 8, mdg_next 8 ...), incl. production modules: student_pilot/mdg_eval.py:20 EVAL=Path('/scratch/jjyeung/orch_cd/evalx/work'),
  mask_grounding_head.py:17 STEM_WEIGHTS='/scratch/jjyeung/orch_cd/mdg_build/work/weights/resnet18-f37072fd.pth', mdg_rasters.py:14 GT=... toolprog.
  Cross-lane code is imported by path (mdg_eval.py:31 puts evalx/ttower/ghead parents on sys.path). 58 tree .py files hack sys.path.
- Proposal: put the trainer tree in the repo as trainer/ (or a second small repo with origin on GitHub); one Git owner (orchestrator)
  imports each accepted build as a commit on a lane branch from a /scratch clone (Git on local disk, not NFS; push to GitHub origin).
  Keep source_seal digest as the launch identity and record the commit beside it. Mirror is then free (push), diffs are git diff.
  Replace /scratch/jjyeung/orch_cd literals with one config root (env DISTILL_LANE_ROOT / kit manifest).

## 2. /home working tree is dirty and stale
- Uncommitted: CLAUDE.md differs from HEAD (lines 9 and 11, the Codex-default and operating-rules text). Untracked, not ignored:
  T3_ATTEMPT10_STATE.md, monitor.out, names.fifo, out.txt (check-ignore run in clone). tools/provenance.py refuses on any
  `git status --porcelain --untracked-files=all` output, so every git-provenance gate fails today.
- Root clutter is failed-command output from agents whose cwd is the repo root (LANE_RULES: "Your working directory is the repository root
  on /home only because Devin needs a trusted folder"): monitor.out "bash: monitor.sh: No such file or directory"; out.txt "can't open file
  'count.py'"; serve1.log, submit_e3.log, verify_watch.log same; HEARTBEAT.log (09-25), out/heartbeat.pid, scratch/ (887 KB jpg), _quarantine/.
- Proposal: commit CLAUDE.md; move the four non-ignored files to REMOVAL_CANDIDATES (user deletes); add `*.out`, `*.fifo`, `/*_STATE.md`
  to .gitignore; give Devin a trusted empty dir on /scratch (like /scratch/jjyeung/orch_home_distill) instead of the repo root.
- docs/: 61 DISTILLATION_HANDOFF files (largest 202 KB); newest 20261110_0110Z, but orchestrator state moved to
  ORCH_STATE_SNAPSHOT_* on /data2 (12 files, newest 20261116T1054Z). Repo CLAUDE.md still says "read the newest docs/DISTILLATION_HANDOFF_*".
- Git admin load: 225 entries in .git/worktrees (111 on /data2, 50 nested in the /home tree, 4 on dead orch_cd); 51 epoch checkouts in
  /home/jjyeung/agent_project_distill_epochs; 1785 Codex receipt dirs + 597 devin_lanes dirs under agent/scratch on /home NFS.

## 3. Dead or superseded modules (tracked)
- Teacher collector stack (collector/, gt_adapters/*, preparers/scannet_v3, materialize/*): last commit 09-18/19; run root
  collection_gt_r1313 last written 2026-09-22. tools/{recover_boundary,watchdog_v5,monitor_v5}_remediation.py supervise only it.
- tools/rung1_build (65 files): AWS code-aws closures; AWS ended 11-09 (memory aws-down-until-user-says). Candidate for archive/ or removal.
- student/{landing,eval-harness,shakedown}: three forks of student_pilot (24/13/12 modules); superseded by the 792-file tree off-repo.
- agent/scratch (53 tracked Devin lane briefs), agent/reports (14) are history.

## 4. Duplication
- 158 byte-identical extra copies, 1.69 MB of 8.56 MB tracked bytes (20%). Whole collector copied into gt_adapters/arkit and
  preparers/scannet_v3 (spatial_agent_r1313.py 307 KB x3, run_experiment_r1313.py x3, pool_harness x3); collector tests copied 6x;
  student_pilot split/runner/lease/cli/checks/batches/admission/adapters x3. Diverged forks: collect.py, trace_archive.py,
  donor_grounding.py, pool_harness/{pool,state,atomicfs}.py differ between collector and the adapters.
- Proposal: no action on frozen sealed packages; for new work, one package imported, not copied.

## 5. Test suite health (CPU, /home and /data* hidden by bwrap, ~1 min total)
No root test config, no single env: p1cpu lacks shapely/cv2/google.genai/av/peft; allospatial_1111_v1 lacks av/peft/google.genai.
Tests need undeclared env vars (H5_TEST_OUTPUT, COMPACT_TEST_OUTPUT, STUDENT_DATASET_TEST_OUTPUT, STUDENT_PILOT_TEST_OUTPUT,
CLEAN_VSI590K_WORKSPACE) and repo root on PYTHONPATH. Best result per directory:
| dir | result | blocker |
| tools/test_provenance.py | 7 pass | - |
| tools/tests (+ new PKG test) | 3 pass; test_numeric_tolerance_tiers collection error | hard path /home/jjyeung/agent_project_distill/collector/census.py |
| tools/paper_tables | 77 pass, 9 skip | needs PYTHONPATH=repo root |
| tools/gtmeasure | 113 pass, 1 skip | needs shapely env + H5_TEST_OUTPUT + PYTHONPATH |
| orchard/stages/qwen36_27b_answeronly | 23 pass, 12 skip | - |
| student/compact_targets | 140 pass, 63 fail | git rev-parse on a /data2 checkout (70), /home and /data2 fixture paths |
| student/landing | 71 pass, 71 fail, 115 err (p1cpu) | env vars, /home/jjyeung/agent_project/agent/scripts/cohort_guard.py (main repo), av/peft |
| student/eval-harness | 20 pass, 1 fail, 35 err | cohort_guard.py in main repo; HF cache on /data2 |
| student/shakedown | 13 pass, 1 fail | HF cache path on /data2 |
| materialize/* (3) | 3-4 pass, 11-12 fail each | /data2 PLAN.json, CONTRACT.json not in tree |
| collector, gt_adapters/*, preparers | collection errors | google.genai, cv2; adapters import collector modules by sibling path |
Totals of the best runs: ~470 pass, ~160 fail, ~170 error/collection error. Tests are not hermetic; they read /home and /data2.
Import-path hacks: 41 tracked .py files, 61 sys.path.insert/append sites; 124 py/sh files hard-code /home|/data2|/data3/jjyeung.

## 6. Pending change: PKG configurable (done on clone branch)
- tools/recover_boundary_remediation.py: PKG = DISTILL_COLLECTOR_PKG (default unchanged), resolved, refuses a path without collect.py.
  tools/monitor_v5_remediation.py PKGS uses the same variable. watchdog imports PKG, so it follows. New tools/tests/test_collector_pkg_env.py (3 pass).
- The line has been pending since 09-19 (DISTILLATION_HANDOFF_20260919.md l.8) for a collector idle since 09-22; after landing,
  drop the CLAUDE.md "Pending code change" line (commit it together with the uncommitted CLAUDE.md edit to avoid a conflict).
- Land: `git -C /home/jjyeung/agent_project_distill fetch /scratch/jjyeung/orch_n30/eff_audit/repo/clone eff-audit-pkg-configurable && git merge --ff-only FETCH_HEAD`
  (only when no collector runs from the tree; none has since 09-22), then push origin main.

## Not done (task limits writes to this folder)
No events, STATUS.md mirror or design record written; no Git on /home; no push.
