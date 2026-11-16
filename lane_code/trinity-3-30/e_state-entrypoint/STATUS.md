# STATUS e_state-entrypoint (updated 20261116T1158Z); ~35% done
Goal: build brief /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/eff/state-entrypoint.md (change 8 "state-entrypoint"); refute verdict briefs/eff/state-entrypoint.verdict.md is binding (restate savings: ~30-45K tokens per orch start, 1-3/day; ~3K per Claude subagent from the MEMORY trim; ~12 asks/16h; CLAUDE.md edit + budget table are no-build steps; keep "NOT clean / never compare" caveats in auto-loaded memory).
W = /scratch/jjyeung/orch_n30/e_state-entrypoint (trinity-3-30). Lane name in the build brief is eff_state_entrypoint; the orchestrator's lane brief uses e_state-entrypoint, so W and the events folder use that name.

## Done (paths)
- Clone W/clone (git clone of /scratch/jjyeung/distill_sync/repo main a38bc5b), branch eff/state-entrypoint, user jacobyeung. Head 6c15b2b3dc0758bcd4ae0a9229e918c280bda533 (queued in W/PUSH_QUEUE.txt).
- Skeleton copied byte for byte: tools/orchkit/{__init__.py 10e50fc5, util.py 0da3aaf1, tests/test_util.py e25aaf36}.
- Built (tools/docs/): indexfmt.py (parser), index_lint.py, index_add.py (flock on <index>.lock + util.atomic_write), state_lint.py, mkbrief.py; templates agent/templates/briefs/{_header,operator,reviewer,builder,successor}.md; tests test_index_lint.py, test_index_add.py (5/5 OK on py3.6); fixtures tools/docs/tests/fixtures/ (INDEX_20261116.md = saved index, design_ls_20261116.txt, cont_ops6_brief.md, cont_ops_STATUS.md).
- Lint of the saved index: duplicate 4, unlisted 27, outside_folder 4, no_verdict 196, long_row 145, empty_row 0 (audit's "~45 empty rows" not found).
- NFS reads complete (never repeat): W/ref/{design_ls.txt, INDEX.md, SNAP_1123Z.md, SNAP_1054Z.md, SNAP_0930Z.md, SNAP_1811Z_tail.md, RECOVERY_MAP_full.md, MEMORY.md, memory_ls.txt, succ/*}, W/ref/heads/ (188 record heads, 30 lines each). Digest W/work/digest.txt (per file: legacy topic/status, H1, status line).

## In flight
Nothing running (no tmux, no background process, no stream, no Orchard job).

## Next steps
1. W/work/build_index.py -> W/out/INDEX_PROPOSED.md (grouped table, <=110 lines above "## Archive", every listing entry once; LOST-2-18/PARTIAL from heads + recovery map); copy to tools/docs/tests/fixtures/INDEX_PROPOSED.md; run test_index_lint.
2. W/out/CURRENT_STATE.md (<=150 lines; sections in state_lint.REQUIRED) + fixture copy + tests/test_state_lint.py; tests/test_mkbrief.py with golden files in tests/golden/.
3. W/out/PROPOSED_MEMORY.md, W/out/PROPOSED_CLAUDE_MD.diff (+ orch cwd /scratch/jjyeung/orch_home_distill/CLAUDE.md diff), clone/docs/README.md, tools/docs/measure_reads.py token measurement.
4. Both test runs (py3.6 unittest; p1cpu pytest under bwrap with /home,/data* hidden), commit, PUSH_QUEUE line, W/REPORT.md, RESULT event, 12-line block under "## Build results" in /data2/jjyeung/agent_project_data/distill_design/EXPERIMENT_EFFICIENCY_20261116.md.

## Open questions (defaults in force)
- 1157Z QUESTION registered_record_hashes: default from 12:35Z = one sha256sum over the five registered records (D0_STOP_RULE, REFREEZE_AMENDMENT_1/2/3, NEXT_LEG_INIT_RULE); prereg md sha ca4a4fbe849be0aa8089b706a7d6b98d629bb008482624eafc1d62608736fa6a (from amendment 3), json 6375d400 (prefix).

## Successor must read
This file; the build brief + verdict; W/work/digest.txt; W/ref/SNAP_1123Z.md, SNAP_1054Z.md; W/ref/MEMORY.md; INTERFACES.md. Rules: no edit of INDEX.md/MEMORY.md/CLAUDE.md (proposals under W/out only); Git only in W/clone; no deletion.
