VERDICT: GO

Yes. The corpus owner can apply patches 01–03 and run every new read through `add_read.sh` with `--review2-checks` on.

- **Default path:** with the switch off, read and orphan bytes are identical to the input tool. The index differs only in `tool_version`, which is unavoidable.
- **Earlier findings:** all six are fixed, and a partial native return can now be archived with `--archive-partial`.
- **Tests:** every new regression fails on the unfixed tool and passes on the fixed one. Each also fails again when its own fix is reverted.
- **Proof script:** it opens only the six named read files and writes nothing.

The findings below are LOW or INFO. None blocks applying the patches. Finding 1 is a remaining way for a native read to be silently mislabelled. It predates the patches and is present in both modes; the switch does not close it. Fix it in the next round.

Paths:
- `T=/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool` is the fixed tool.
- `I=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin` is the input tool.
- `F=/scratch/jjyeung/orch_n30/so_corpus_fix` is the fix workspace.

Every probe ran in a private user-namespace tmpfs (`unshare -rm` with a tmpfs over `/dev/shm`), so nothing persisted outside this file.

## What I verified (measured here)

**Patches**
- `01→02→03` apply cleanly to a copy of `I`, and the result is byte-identical to `T` (`diff -r` is empty).
- With only patch 01 applied, `add_read.sh` is still the input version.
- The ingest SHA256 values match the report: `eb0b207c…` fixed, `97bb63d8…` input. All 42 hash entries in `MANIFEST.json` verify.
- Round 4 did not change `ingest_read.py`; it has the same SHA as round 3. The round adds the docs, wrapper patch 02, the proof script and tests.

**Suites** (my runner, fixtures on tmpfs; `test_no_leftovers` excluded because it needs a real return)

| Tree | Suite | Result |
|---|---|---:|
| Full patch stack | five modules | 69/69 pass |
| Full stack, checks forced on | `test_synthetic` | 20/20 pass |
| Patch 01 only | three modules | 60/60 pass |
| Input tool | `test_synthetic` | 20/20 pass |
| `work/pre_round3` (unfixed) with the new tests | `test_review3` | 17 tests, 27 failures |
| Saved pre-round-4 wrapper | wrapper test | fails `0 != 1` |

The 27 `test_review3` failures match `out/REPORT.md` exactly.

**Mutation check for question 3.** I reverted each fix separately and reran `test_review2` and `test_review3` (40 tests):
- Missing arm or subset raises a refusal again: the F1 tests and the review-two CLI partial test fail.
- No score-conflict check: the three F3 refusal tests fail.
- No arm inference: all three F4 tests fail.
- `raw=row` instead of `raw=original`: the F4 raw-preservation test fails.
- No row/task check: 16 F5 cases fail.
- No missing-task refusal, or `inputs_loaded` not set: the F6 tests fail.
- Alias actual-ID filter, label check and unexpected-arm check removed one at a time: each review-two test fails.

Two guards have no test (finding 3).

**Question 1, default byte identity.** I added 11 new edge fixtures on top of the report's 13:
- duplicate exact report rows mixed with alias and actual-ID rows;
- an actual-ID row placed before a key-only row;
- unlabeled, keyless and top-level `rows` R1 rows;
- row/task conflicts with additive candidates;
- a journal row without `arm`;
- no request and no report;
- a realistic partial (torn ends, no R1, no paired COMPLETE) run with `--archive-partial`;
- kit inline scores against report scores;
- duplicate unlabeled report rows.

Results:
- Exit codes and stderr match the input tool on all 11.
- `reads/p.jsonl.gz` and `index/p.orphans.jsonl.gz` are byte-identical.
- `index/p.json` is identical once `tool_version` is removed.
- `tool_version` hashes the executing script (`T/ingest_read.py:893`), so a changed tool can never write an identical index. A rerun into a root that already has the read does not rewrite its index on `SAME` (`:912`), so published index files keep their bytes.

**Question 2, enabled mode.**
- **Realistic partial native return:** request declares 2 keys, the journal has 3 of 4 rows, R1 and paired COMPLETE are absent.
  - Without `--archive-partial`: exit 2.
  - With it: exit 0, `status=partial`, and reasons `Missing native keys for arm unflagged: 1 != expected 2` and `Missing native/paired/results/COMPLETE.json`.
- **Conflicts:** score, row/task and keyless report-row conflicts refuse with exit 2, even with `--archive-partial`.
- **Duplicate unlabeled report rows:** accepted (exit 0).

**Question 4, the proof script.** `out/scripts/prove_kit_alias_ids.py` is identical to `T/prove_kit_alias_ids.py`.
- On a synthetic corpus that also held `INDEX.jsonl` and an unrelated read, a Python audit hook logged exactly six opens. They were the six named `reads/<id>.jsonl.gz` files (`:57`), all read-only, with no write opens.
- It runs under `/usr/bin/python3` 3.6.8, the interpreter in `OWNER_REPLAY.md:17`, and exits 0.
- Pacing: two scans of 11.66 MB each took 26 s, consistent with the 1 MiB/s cap (`:29,47`).
- Its six IDs and counts (`:21-28`) are exactly the INDEX kit reads with report sources.

## Findings

1. **LOW. A native journal row without `arm` skips the journal/report comparison, in both modes.**
   - With checks on, arm inference covers only R1 `arms.X` rows (`T/ingest_read.py:651-655`). Any journal row lacking `arm` is skipped by `:656-657`.
   - Probe: journal row `{key: devrows:q, scores: 0.0}` with no `arm`, and R1 `arms.unflagged` row with `arm: unflagged` and score 1.0.
     - With `--review2-checks`: exit 0, `status=complete`, no issue, and `unflagged` score 1.0.
     - The journal's 0.0 survives only in `raw.records`.
   - This predates the patches: the input tool behaves the same way. But it means the bar "nothing can silently mislabel" is not fully met.
   - Real paired journals are expected to carry `arm`, so the risk is low.
   - **Smallest fix (under the switch):** in `prepare`, refuse a journal row that is a dict with `key` but no `arm` (`Refusal('Unlabeled native journal row: ' + key)`), and add a test.

2. **LOW. With no arm declaration at all, a partial native return still hard-refuses with the switch on.**
   - "No declaration" means `request.json` has no `arm` and R1 has no arm arrays. Then `required` is empty, and `:736-738` raises `Contradictory or missing native arm declarations`, even with `--archive-partial`. Default mode archives the same return.
   - `SCHEMA.md:47-50` says missing arms become partial issues. It does not list missing declarations among the refusals.
   - Rare in practice, since native returns ship `native/paired/request.json`. But patch 02 leaves no switch-off route through the wrapper.
   - **Smallest fix:** when `not required` and `report_arms - required` is empty, append the issue `Missing native arm declarations` and use the observed arms. Keep the refusal for `report_arms - required`. Alternatively, document the refusal in SCHEMA and HOWTO.

3. **LOW. Two enabled-mode guards have no regression test.**
   - The guards are the `Invalid native report row` refusal (`:652-653`) and the duplicate-row arm augmentation (`:663-664`).
   - Removing either one leaves all 40 review tests passing.
   - Current behaviour is correct by probe:
     - A keyless object in `arms.scripted` refuses, even with `--archive-partial`.
     - Two identical unlabeled `arms.scripted` rows give exit 0, complete.
   - **Smallest fix:** add those two cases to `tests/test_review3.py`.

4. **INFO. Kit inline `scores` silently win over a disagreeing exact report row, in both modes.**
   - The code is `:440-441`.
   - Probe: inline `{answer: 1.0}` against report `{answer: 0.0}` gives exit 0, complete. The report row is kept in `raw.records` (0 orphans).
   - This is outside findings 1–6 and preserves the evidence.
   - **Optional fix (under the switch):** refuse, or add an issue, when both are present and differ.

5. **INFO. Published reads stay valid. No re-ingest is needed unless an owner replay refuses.**
   - **Native read** (`469ddece_s544_devS1_native_b07a20b364`): enabled mode can only reproduce the published bytes or refuse.
     - INDEX shows 636 items in each arm, complete, with request `arm: paired` and 636 keys declared in both request and R1.
     - So every (key, arm) pair already comes from labeled rows. Unlabeled R1 rows can only duplicate them, which is accepted, or contradict them, which refuses. They cannot add rows.
     - The missing-task, row/task and label checks only refuse.
   - **Six kit reads with report sources:** only the alias filter can change bytes, and proof exit 0 rules that out. The duplicate-score check only refuses.
     - My arithmetic on `work/evidence/INDEX_round3.jsonl` gives `consumed_row_count − 5×items` equal to one report row per family item per report for all six. For example, `17c4ffa4…` gives 5475 = 3×(1525+150+150). That fits no duplicate report rows. It is an inference from counts, not from IDs.
   - **Proof premise:** the proof assumes the publishing tool (`ebd8c6d0…`) attaches records the same way as the input. The published SCHEMA (`F/work/evidence/PUBLISHED_SCHEMA.md`) is byte-identical to the input's and states "an actual `id` is never stripped". That supports the assumption but does not prove it.
   - **Who runs what:** the corpus owner on trinity-3-30 runs the proof (`F/out/OWNER_REPLAY.md:13-18`) and any replays (into scratch only, new `.review4` IDs). None of it ran here.
   - **Smallest fix:** none required. Optionally state in the report that the seven "unverified" IDs can only reproduce or refuse once the proof exits 0.

6. **INFO. Wrapper and docs are consistent.**
   - `add_read.sh:11` adds `--review2-checks` before `"$@"`; argparse `store_true` makes a repeated flag harmless.
   - Patch 02 without patch 01 fails loudly, because the input argparse rejects the flag and the wrapper prints `nothing published`.
   - HOWTO forbids republishing an existing ID with checks on (`HOWTO.md:10`). `SAME` on a rerun (`HOWTO.md:18`) holds only for IDs first staged with the checks on.
