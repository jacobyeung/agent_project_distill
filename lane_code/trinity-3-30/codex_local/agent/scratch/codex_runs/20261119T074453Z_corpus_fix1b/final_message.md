Implemented A1–A8 and both adapters. **39 synthetic tests and 6 real-return checks passed on Python 3.6.8.**

- **A1:** Every consumed row survives in item raw data or a counted, hashed orphan sidecar. Joined tasks retain all keys.
- **A2:** Contradictory task hashes return exit 2. B5’s 98 R0 joins use its documented `answer=ground_truth` transformation and verify the resulting hash.
- **A3:** Kit validates identical populations, consistent question/truth, and exact per-arm counts.
- **A4:** IDs retain colons exactly.
- **A5:** Original arm rows now live under `raw.arms`.
- **A6:** Status checks cover every consumed row type.
- **A7:** Zero generation rows return exit 2, including with `--archive-partial`.
- **A8:** Routed manifests are identified by content.

`writable()` remains unchanged; [SCHEMA.md](/scratch/jjyeung/orch_n30/corpus/tool/SCHEMA.md) documents `/scratch/` and `/dev/shm/` output roots.

| Adapter | Field mapping |
|---|---|
| kit/offread | Question/truth from direct rows; `extracted_answer`, `raw_generation`, token fields and `score` supply arms. Offread adds report categories and budget-file layouts. |
| routed | Hash-bound task supplies question/truth; `output.text`, `calls.records`, and `scores.answer` supply generations. |
| native | Preserves `scripted` and `unflagged`; maps `decode.text/calls/finish`, token counts and row scores. Verified **all 1,857 calls**, including responses and audit fields. |

Native used A4’s task inputs because its return lacks question text. Unrecorded export identifiers and direct-call fields remain null.

The real outputs are under [t/real/validated](/scratch/jjyeung/orch_n30/corpus/tool/t/real/validated). Full SHA256 values are printed in [metrics.json](/scratch/jjyeung/orch_n30/corpus/tool/t/real/validated/metrics.json); prefixes appear below.

| Return | Items | Bytes | Seconds | Max RSS MiB | SHA256 prefix |
|---|---:|---:|---:|---:|---|
| a8102c3207b tar | 3,120 | 9,012,464 | 24.012 | 156.8 | `b0cc401b9cf1` |
| a8102c3207b x/ | 3,120 | 8,878,544 | 23.487 | 157.0 | `6f0f938f3319` |
| A4 | 636 | 3,951,421 | 4.856 | 38.7 | `4102ef63f755` |
| B5 | 134 | 552,274 | 1.707 | 57.1 | `601fb5aa9276` |
| ret_vsi | 4,008 | 2,873,814 | 17.013 | 113.2 | `c99a230446c4` |
| ret_revsi | 679 | 766,124 | 3.267 | 49.4 | `70d7b5a1c5eb` |
| full_c8r | 636 | 96,610,159 | 38.761 | 406.7 | `98ff3196eac8` |
| a4cadd8934b | 1,825 | 4,147,193 | 15.640 | 110.2 | `7fd7fb682a5a` |

`corpus_score.py --arm B2048 --by category --mean-of-types` reproduces:

| Headline | Corpus | Reported |
|---|---:|---:|
| VSI six-task mean | 68.77 | 68.77 |
| VSI count / size | 63.03 / 72.03 | 63.03 / 72.03 |
| ReVSI five-category mean | 64.94 | 64.94 |
| ReVSI count / direction | 58.57 / 51.19 | 58.57 / 51.19 |
| A4 tower | 75.267296 | 75.267296 |

Three source details matter:

- The kit tar and `x/` contain different supplementary `ITEMS` rows. Their 3,120 generation records match, but lossless output hashes differ; both outputs are retained.
- Kit primary stored scores match the report’s **released-answer** column, 77.342304%, rather than its separate own-answer column.
- Two native items have scored geometry refusals in both arms. Their zero scores survive; absent traces remain null.

[Final real-test log](/scratch/jjyeung/orch_n30/corpus/tool/t/real-verification.log) · [Synthetic-test log](/scratch/jjyeung/orch_n30/corpus/tool/t/default-tests.log)