NO-GO

Eight original defects are fixed. Defect 4 retains a wrong-score join, and native has two additional validation defects.

**Blocking findings**

1. **Kit can assign another ID’s scores.** [ingest_read.py:420](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:420) retries report lookup using `devrows:<id>` without requiring a key-only record. Reproduction: item `q`, report `{"id":"devrows:q","scores":{"answer":0.25}}`. Ingestion exits **0** and assigns those scores to `q`, while correctly putting the report row in orphans. Restrict this alias to key-only records.

2. **Native accepts missing or incompatible arm populations.** [ingest_read.py:661](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:661) checks counts only for observed arms. With expected count 1:
   - Empty `scripted` plus one `unflagged` row exits **0**, complete.
   - `scripted=devrows:other`, `unflagged=devrows:q` exits **0**, complete, with two incomplete items.
   
   Validate required arms and their exact key sets against the request/report declarations.

3. **Native silently chooses between contradictory task identities.** [ingest_read.py:643](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:643) compares only question and scored answer. Two candidates with ID `q`, question `Which?`, answer `A`, but reversed options and different scenes exit **0**, complete. The first filename determines the selected options/scene. Validate the full task identity before joining.

**Original nine defects**

| # | Result and reproduction | Implementation |
|---|---|---|
| 1 | **Fixed.** Unmatched report rows, including scalar `42`, survive in orphans. Joined `room_key` survives; all 636 real A4 items retain manifest `room_key` evidence. | [ingest_read.py:760](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:760), [orphan emission:804](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:804) |
| 2 | **Fixed.** Contradictory task hash exits **2**, with and without `--archive-partial`. | [ingest_read.py:517](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:517) |
| 3 | **Fixed.** Different arm IDs, contradictory question/truth, and counts above the expected count each exit **2**. | [ingest_read.py:437](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:437), [arm validation:452](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:452) |
| 4 | **Partially fixed.** Exact `namespace:q` retains its report and scores. The alias counterexample above still joins distinct actual IDs. | [ingest_read.py:194](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:194), [report lookup:418](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:418) |
| 5 | **Fixed.** Arm `input` preserves both `raw.input` and `raw.arms.input`. | [ingest_read.py:744](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:744), [arm storage:767](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:767) |
| 6 | **Fixed.** Failed supplementary ITEMS and unmatched report rows each exit **2**. | [ingest_read.py:200](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:200) |
| 7 | **Fixed.** Zero generations exit **2**, including with `--archive-partial`. | [ingest_read.py:913](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:913) |
| 8 | **Fixed.** Manifest at `a/4.json` produces set `room134`. Real B5 also preserves that set. | [ingest_read.py:481](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:481) |
| 9 | **Fixed by the authorized policy change.** `/scratch/` and `/dev/shm/` pass; `/tmp/` fails. Documentation agrees. | [ingest_read.py:41](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:41), [SCHEMA.md:4](/scratch/jjyeung/orch_n30/corpus/tool/SCHEMA.md:4) |

**Real-output verification**

Source-to-output row comparisons found no missing or extra consumed rows:

| Output | Items | Preserved consumed rows | Additional verification |
|---|---:|---:|---|
| offread VSI | 4,008 | 32,352 | Mean **68.771337%**; count **63.026549%**, size **72.025184%** |
| offread ReVSI | 679 | 5,693 | Mean **64.944614%**; count **58.573802%**, direction **51.185897%** |
| native | 636 | 9,511 | Both arms contain 636 items; all **1,857 calls**, responses, and traces match source records |

Reproductions used the current parser, adapters, and emitter with in-memory SQLite and mocked filesystem writes. Real checks audited stored artifacts; their recorded `tool_version` differs from the current script. Peak measured RSS was **287 MiB**. No files changed.