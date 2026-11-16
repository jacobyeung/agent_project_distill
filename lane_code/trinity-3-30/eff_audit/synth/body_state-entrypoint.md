# Build brief 8 of 8: state-entrypoint (lane `eff_state_entrypoint`, branch `eff/state-entrypoint`, Claude Opus, effort high, size M: 4 to 6 agent-hours)

Give every fresh agent one short page of current state, an index it can read in one call, and briefs generated from templates, and draft the instruction changes for the orchestrator and the user to apply.

## Why

- `distill_design/INDEX.md` has 197 lines and 89 KB: a table, then a bullet list with no status, about 45 empty rows and four files listed twice. One read costs about 40K tokens, and briefs tell every design and debug lane to read it first (`AUD/docs/PROPOSAL.md`, "Measured state").
- The repository's `CLAUDE.md` sends an orchestrator to "the newest `docs/DISTILLATION_HANDOFF_*.md`", which is dated 2026-11-10. The real state is `ORCH_STATE_SNAPSHOT_20261116T1054Z.md`, which points on to two older snapshots for the rulings and the do-not-redo list.
- 64 briefs in 18.5 h were written by hand; "No Git" is restated in 29 of them, "no deletion" in 31, the rotate text in 22 (`AUD/process/NOTES.md`, "Counts"). Lanes asked about their disk cap, scratch floor or IO class about 12 times, each an orchestrator turn.
- `MEMORY.md` carries about 25 lines marked READ FIRST and IO rates (10, 18, 20 MB/s) that differ from the admins' current rules.

{{COMMON}}

## Extra rule for this build: instruction files are proposals

You edit none of `CLAUDE.md`, `AGENTS.md`, `MEMORY.md`, `B/tools/LANE_RULES.md`, `distill_design/INDEX.md` or any file under `/home/jjyeung/.claude/`. Each change to them is a file under `W/out/` that the orchestrator or the user applies. Other lanes append to `INDEX.md` while you work, so a swap is the orchestrator's step at a quiet moment.

## NFS reading plan (the only reads on `/data2` and `/home` you make)

1. `ls` of `/data2/jjyeung/agent_project_data/distill_design/` once, saved to `W/ref/design_ls.txt`.
2. `INDEX.md` once, copied to `W/ref/INDEX.md`.
3. The first 30 lines of each record, one file at a time, at most 30 files a minute, saved under `W/ref/heads/`; never a second read of a file.
4. `ORCH_STATE_SNAPSHOT_20261116T1054Z.md` (or the newest), `ORCH_STATE_SNAPSHOT_20261115T0930Z.md`, and the tail of `ORCH_STATE_SNAPSHOT_20261115T1811Z.md` by bounded search, each once, under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
5. `RECOVERY_MAP_2_18_OUTAGE_20261115.md` once.
6. The memory index `/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/MEMORY.md` once, and one `ls` of that folder. You open no linked memory file.

## Scope

**`W/out/INDEX_PROPOSED.md`.** One table, at most about 110 lines above the archive: `Topic | File | Status | Verdict (GO, NO-GO, OPEN, DESIGN, REGISTERED, RESULT) | Evidence (OK, PARTIAL, LOST-2-18)`, grouped as `AUD/docs/PROPOSAL.md` section "Proposed structure" lists (results that bind; active and next leg; rulings; grounding; pose and geometry; traces and pools; Orchard, infrastructure and tools; VLA; archive). Status has at most 160 characters. Every file of the folder appears exactly once. A superseded row moves to the archive section with `SUPERSEDED_BY`; no file moves and none is removed. A record whose evidence sits under `/scratch/jjyeung/orch_cd/` or `orch_n28` gets `LOST-2-18` or `PARTIAL` from the record's own text and the recovery map, with a link to the map; you probe no node.

**`tools/docs/index_lint.py` and `tools/docs/index_add.py`.** The lint reads an index file and one saved directory listing and fails on a file listed twice, a listed file that does not exist, a file of the folder that is not listed, a row without status or verdict, a row above 300 characters, and an empty row. `index_add.py --index FILE --topic T --file F --status S --verdict V --evidence E` appends one row in the table's format under a lock and refuses a file already listed.

**`W/out/CURRENT_STATE.md` and `tools/docs/state_lint.py`.** The draft of the single entry page, at most 150 lines, written as the current state only: goal in two lines; live runs with job ids, owner lane and the record that rules them; nodes up, down and forbidden; the standing rulings, one line each with the record's path; the results that bind, one line each; the do-not-redo list; the ranked ready-to-launch queue; pointers to the index groups. After adoption the orchestrator is its only writer and rewrites it at each ruling, as part of its snapshot step. The lint checks the length, the required sections, that every cited file exists, and that a registered record is cited with its sha256.

**`agent/templates/briefs/` and `tools/docs/mkbrief.py`.** Templates for an operator, a reviewer, a builder and a successor. A template states the role once and points at `LANE_RULES.md` instead of restating it. `mkbrief.py <role> --lane L --node N --events E --cap-gb G --scratch-floor-gb F --io-class C --limit T [--predecessor P]` fills the header and a table of default budgets (lane cap, scratch floor, IO class, each with the rule "inside this budget act without asking"), and leaves `Why` and `Do` for the orchestrator. `mkbrief.py successor` builds the brief from the predecessor's brief, its `STATUS.md` and its rotate event. A free-text `Limits` field keeps lane-specific limits visible.

**`W/out/PROPOSED_MEMORY.md`.** The memory index cut to about 40 lines, following `AUD/docs/PROPOSAL.md` section "MEMORY.md consolidation": one line per merged group, each still linking its files; READ FIRST on at most five lines; the first line points at `CURRENT_STATE.md`; result lines and run state move to `CURRENT_STATE.md`. The IO line names the governor and the admins' rules in the global `CLAUDE.md` and carries no rate of its own. Where two user rulings pull in different directions, keep both links and say in one clause which governs; drop none.

**`W/out/PROPOSED_CLAUDE_MD.diff`.** A diff of the repository's `CLAUDE.md`, "Orchestrator only" section: read `CURRENT_STATE.md` first, then the newest snapshot only where it differs; remove the handoff instruction and the pending supervisor line (its change exists as a branch). Plus `docs/README.md` on your branch: the handoffs and the September result files are history, and the entry page is `CURRENT_STATE.md`.

## Files you own

On the branch: `tools/docs/` (with `tools/docs/tests/`), `agent/templates/briefs/`, `docs/README.md`. Under `W/out/`: the four proposal files.

## Tests (folder `tools/docs/tests/`)

1. `index_lint.py` on the saved current index reports the defects the audit counted (four files listed twice, the empty rows, the unlisted files); on `INDEX_PROPOSED.md` with the saved listing it passes.
2. `index_add.py`: appends one row; refuses a duplicate; two parallel adds both land.
3. `mkbrief.py`: a golden file per role; the successor brief of `cont_ops6` (inputs copied from `B/briefs/cont_ops6.md` and `B/events/cont_ops/STATUS.md`, each read once) names the folders and the next step of the predecessor.
4. `state_lint.py` passes on the draft and fails on a draft of 151 lines, on a missing section and on a registered record cited without a sha256.
5. Measure and report: bytes and estimated tokens a fresh orchestrator reads today (instruction chain, memory index, index, snapshot) and with the proposals.

## Deliverables

Branch `eff/state-entrypoint`; the four files under `W/out/`; `W/REPORT.md` with the token measurement and the list of rows you archived, so the orchestrator can check that no binding record is hidden; the RESULT event; the result block in RECORD.

## Out of scope

Applying any proposal; moving handoff files; pruning worktrees or receipts (deletions go to the user); changing a record's content; reading the linked memory files or the records beyond their first 30 lines.

## Review

None required. The orchestrator reads the archived-row list before it swaps the index.
