# syncmove_filter_fix1: review round 1 fixes (gpt-6-astra)

Workspace `L=/scratch/jjyeung/orch_n30/sm_filter` (yours to write). `$L/PROMPT.md` binds you (standing rules included). Review verdict (Cursor Opus, GO AFTER FIXES): `/scratch/jjyeung/orch_n30/sm_cr_filter/REVIEW_VERDICT.md`, read it in full first; its probes are under `$L/work/tmp_review/`. Copy `$L/out/` to `$L/out_round1/` before changing anything.

Fix as the review proposes, each with a regression test that fails before and passes after (reuse the reviewer's probes):
1. Finding 1 (HIGH): the word-plus-number exemption on the generic suffix rule, plus an explicit exemption so every directory directly under a `codex_runs/` directory is kept (run records). Fixture cases: `lane/out/kit_parity50/run.py`, `lane/agent/scratch/codex_runs/20261119T152211Z_so_reads228/prompt.md`, `.../20261119T134431Z_sb_ph2gate3/meta.json` (all keep).
2. Finding 2 (MEDIUM): protect root children only when the label is a node label (`trinity-<n>-<n>`), so dry_count and land_kit regain the old behaviour at their roots.
3. Finding 4: `/lib/python` becomes a directory-only PATHRE rule (`/lib/python[0-9][^/]*/`), not SUBSTR.
4. Findings 6 and 7: restore the `$` anchor for the pre-existing DIRRE alternatives (new alternatives may use `\Z`); record the dry_count default-mode change in REPORT.
5. Finding 5: add only rules that are clearly by-products: `pytest_*` directories under `work/` or `out/` that hold test outputs, and the nested lane copies `work/{fcopy,scopy,lcopy,pcopy}`; leave `work/base` and `replay*` kept. Decide from the data and record.
Rerun the simulation (`in/commits`) and the real trinity-2-28 dry run (old vs new, same command as before), rerun every test, regenerate patches, PREIMAGE/POSTIMAGE, SHA256SUMS; REPORT.md first line `VERDICT: ...`, plus a section "Review round 1: finding -> fix -> test". Due 25 minutes after you start.
