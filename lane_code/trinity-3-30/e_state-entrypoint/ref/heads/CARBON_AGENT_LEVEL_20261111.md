# Gemini 4 Carbon as a Devin coding agent: medium against high thinking, on tonight's fixed bugs
Paths are on trinity-2-18. Lane: carbon_agent_ab (Devin, Opus 5.5 high), 2026-11-11.

## Question
Should Devin lanes that run gemini-4-carbon use the medium or the high variant for coding?

## Answer
Use **gemini-4-carbon-medium**. Medium and high solved the same tasks. Medium completed every session, while one high session aborted. High cost about 22% more per completed session and was not faster. The task set is too easy to separate the two variants: every completed session passed, so this result shows that high adds nothing on bounded bug fixes with a located traceback. It does not show that the variants are equal on open-ended diagnosis.

## Evidence
Five tasks, two sessions per variant, 20 sessions in total. Each session ran through `orch_tools/devin_bg.sh` semantics (wrapper `carbon_agent_ab/devin_bg_ab.sh`) in a fresh copy under `/dev/shm/jjyeung_carbon_ab/<task>/<variant>_<run>/`, with a 30-minute timeout and at most four sessions at once. The agent saw the brief and the copy, never the hidden test.

| | medium | high |
|---|---|---|
| Hidden test, strict | 8/10 | 7/10 |
| Hidden test, t2 conflict-list order ignored | 10/10 | 9/10 |
| Copy's own suite after the run | 10/10 pass | 10/10 pass |
| Median minutes (all runs / completed runs) | 21.2 / 21.2 | 19.4 / 19.9 |
| Timeouts | 0 | 0 |
| Aborted sessions | 0 | 1 (t1 run 2: `empty_response` after 14.4 min, no edits) |
| ACU per completed session | 0.96 | 1.18 |
| Out-of-scope actions | read-only reads of own_teach and own_probe files that the copy's tests and card_run.py name (t2 runs 1 and 2); no write outside the copy, no deletion, git, ssh or GPU | same pattern (t2 runs 1 and 2) |

Per-task minutes, medium (r1/r2) against high (r1/r2): t1 22.0/21.2 vs 22.3/14.4 (abort); t2 23.9/21.2 vs 24.1/22.5; t3 17.5/23.6 vs 14.3/19.0; t4 10.3/11.3 vs 8.0/13.6; t5 19.8/22.5 vs 19.9/22.3.

All four t2 sessions failed the same strict assertion. They fixed the join, but the report listed the two conflicting spellings as `['book', 'books']`, while the lane's test expects file order (`['books', 'book']`). The brief never fixes that order, so `hidden_orderfree_t2.sh` also scores t2 with the order ignored; that variant still fails on the pre-fix copy and passes all four sessions. Every session also added its own regression tests. Edits to existing test files only added tests, apart from one helper refactor in a t2 medium session.

Records: `carbon_agent_ab/results/runs.jsonl` (one line per session), `results/SUMMARY.json`. Transcripts, diffs and test logs: `/dev/shm/jjyeung_carbon_ab/logs/`.

## Task set
