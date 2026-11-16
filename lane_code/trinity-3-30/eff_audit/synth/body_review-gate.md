# Build brief 4 of 8: review-gate (lane `eff_review_gate`, branch `eff/review-gate`, Claude Opus, effort high, size M: 4 to 5 agent-hours)

Make "one review suffices" executable: a reviewer writes a machine-readable verdict with reproduction commands, a script confirms a fix that stays inside the verdict, and every kit cites its registered rule by hash instead of restating it.

## Why

- The project rule is one review: "Only a change that touches admission, legality or scoring needs an independent review, and one review suffices" (`/home/jjyeung/agent_project_distill/AGENTS.md`, section Provenance). The GO text turned it into a loop: "If it demands fixes, apply them and get one more confirmation first" (`B/events/cont_ops/20261115T2109Z_ORCH_GO_d0_job_a.md`, line 2). The D0 derive kit then went through rounds r1 to r12, and seven second-reader lanes (vsti2, d0r2, k1b3, k1b4, rows2, contracts2, an2) confirmed without finding a new blocker.
- Measured wait on critical paths in 18 h: 19 min (VSTI), 25 min (D0 read kit), about 45 min (k1b3) and about 50 min (k1b4). A reviewer lane exits after its verdict, so the K1 confirmation had no reader: "review_k1b2 has not confirmed batch fc9ed8a8 and looks idle, so the conditional GO cannot fire" (`B/events/k1_ops3/20261116T0854Z_BLOCKER_reader_silent_on_fixes.md`).
- One registered stop rule was paraphrased four times (a GO, a ruling, two briefs), and the read kit implemented a paraphrase (`AUD/process/NOTES.md`, "Rule restatement drift").
- First reviews that reproduce find the blockers; confirmations confirm (`AUD/process/NOTES.md`, "Pattern").

{{COMMON}}

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
