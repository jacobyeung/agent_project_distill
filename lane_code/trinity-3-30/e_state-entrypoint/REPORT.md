# REPORT: state-entrypoint (branch eff/state-entrypoint, head cbed590d3e489d7225b1f8a16d38eebc41b1c72b)

## What is built
- Branch (clone W/clone, commits 6c15b2b, fe399b9, 3d185bb, cbed590; all in W/PUSH_QUEUE.txt): tools/docs/{indexfmt,index_lint,index_add,state_lint,mkbrief,measure_reads}.py, tests in tools/docs/tests (fixtures, golden briefs), agent/templates/briefs/{_header,operator,reviewer,builder,successor}.md, docs/README.md, tools/orchkit skeleton copied byte for byte.
- W/out/INDEX_PROPOSED.md: one grouped table, 109 lines above "## Archive", 73 main rows, 124 archive rows; every one of the 213 folder entries once; index_lint clean with --max-main-lines 110. Built by W/work/build_index.py from W/ref only.
- W/out/CURRENT_STATE.md: 84 lines, all eight sections, state as of the 11:23Z snapshot; state_lint clean on this host (every registered record cited with its sha256).
- W/out/PROPOSED_MEMORY.md: 24 lines, 8,954 bytes (from 103 lines, 18,578 bytes); all 121 linked files kept, none added; READ FIRST on 4 lines; first line points at CURRENT_STATE.md; no MB/s rate; "NOT clean" and "never compare" caveats kept on the Results line.
- W/out/PROPOSED_CLAUDE_MD.diff: repo CLAUDE.md (read CURRENT_STATE.md first, newest snapshot only where newer; handoff and pending-PKG lines removed) and the orchestrator cwd CLAUDE.md; patch --dry-run applies to the bytes read at 12:49Z (repo CLAUDE.md sha256 802a2829).

## Tests (commands and output tails; logs W/work/test_py36.txt, W/work/test_p1cpu_bwrap.txt)
- `cd W/clone && TMPDIR=W/tmp /usr/bin/python3 -m unittest discover -s tools/docs/tests` -> Ran 36 tests ... OK
- `... /usr/bin/python3 -m unittest discover -s tools/orchkit/tests` -> Ran 10 tests ... OK
- `bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc --chdir W/clone --setenv HOME /tmp /scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider tools/docs/tests tools/orchkit/tests` -> 46 passed in 0.68s
- Saved index (fixture INDEX_20261116.md): duplicate 4 (the audit's four files), unlisted 25, missing 1 (FINAL_VERDICTS.tsv), outside_folder 4, no_verdict 196, long_row 145, empty_row 0. The audit's "~45 empty rows" do not exist in the saved copy; its unlisted count was not stated, my predecessor's 27 came from an earlier parser.

## Token measurement (tools/docs/measure_reads.py, bytes/4; W/work/measure_reads.txt)
- Today, orchestrator start without INDEX: 72,527 B, ~18.1K tokens (global CLAUDE.md truncated at 16,384 B, AGENTS.md, two CLAUDE.md, MEMORY.md, snapshots 1123Z + 1054Z, 0930Z goal/rulings/do-not-redo sections, newest handoff).
- Today with INDEX.md read: 164,135 B, ~41.0K tokens.
- Proposed: 61,248 B, ~15.3K tokens (CURRENT_STATE + trimmed memory + index above the archive + the 1123Z delta).
- Saving per orchestrator start: ~2.8K tokens when today's start skips INDEX, ~25.7K when it reads INDEX. The verdict's ~30-45K per start is NOT supported by this measurement; the 1811Z tail search and any lane-turn re-reads were not measured. MEMORY trim: ~2.4K tokens per Claude session or subagent that loads memory (verdict said ~3K). The ~12 asks/16h claim is not measured here; budgets in mkbrief are a no-build step for the orchestrator to adopt.

## Archived rows (124; check that no binding record is hidden): W/work/archived_rows.md
- Only one archived row has verdict REGISTERED or GO: LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md (LEG-S1 ended at step 544).
- Archived as SUPERSEDED_BY NEXT_QUEUE_20261116.md: the AWS, SOTA, improvement and model-improvement plans and NEXT_QUEUE_20261115.md. Archived NO-GO: MDG line, T2, C1 sweeps, packed Orchard job. Evidence archives whose owning record no head names (four 11-14 tgz) are archived as CLOSED evidence rows.

## Not proven
- Verdict, evidence and status cells come from each record's first 30 lines, the saved index, the snapshots and the recovery map, not from full records; evidence tags (PARTIAL vs LOST-2-18) are my reading of where cited outputs lived. Rows written by other lanes after 06:50Z are absent: lint the live listing before the swap.
- CURRENT_STATE.md reflects 11:23Z; live-run lines (VSTI 170209, K1, D0 milestones) must be refreshed by the orchestrator at adoption.
- Golden briefs prove the generator is stable, not that the templates suit every lane.

## Reads beyond the plan
- One sha256sum over the five registered records plus the pre-registration md and json (ORCH answer 1224Z): W/work/registered_sha256.txt.
- One read of /home/jjyeung/agent_project_distill/CLAUDE.md (1,582 B) and /scratch/jjyeung/orch_home_distill/CLAUDE.md, the two diff targets; stat sizes of the global CLAUDE.md and AGENTS.md.

## Adoption steps (orchestrator)
1. At a quiet moment: save a fresh ls of distill_design, rerun W/work/build_index.py against it (add rows for new files), lint with `index_lint.py --index INDEX_PROPOSED.md --listing <ls> --max-main-lines 110`, then swap INDEX.md.
2. Refresh W/out/CURRENT_STATE.md's live runs and queue, lint with `state_lint.py --state CURRENT_STATE.md --listing <ls> --index INDEX.md`, write it to distill_design/, and rewrite it at every ruling as part of the snapshot step.
3. Apply W/out/PROPOSED_CLAUDE_MD.diff (patch -p1 in the repo; the second hunk to /scratch/jjyeung/orch_home_distill) and replace MEMORY.md with W/out/PROPOSED_MEMORY.md.
4. New records: `index_add.py --index INDEX.md --topic T --file F --status S --verdict V --evidence E --folder <distill_design>`. New briefs: `mkbrief.py <role> ...`, successor briefs with `mkbrief.py successor --predecessor ... --status ...`.
