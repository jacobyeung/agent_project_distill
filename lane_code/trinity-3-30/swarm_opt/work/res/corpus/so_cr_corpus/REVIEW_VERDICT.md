VERDICT: GO AFTER FIXES

The patch is safe to merge now. Its default path is byte-identical on read and orphan files, and each of the three fixes is correct for the defect it targets. I agree with the report that no published read needs re-ingest. Before anyone turns on `--review2-checks` for production ingests, fix finding 1, and have the owner wire the switch for new reads (finding 2). Findings 3–6 predate this patch, and the switch still does not catch them.

Paths: `T=/scratch/jjyeung/orch_n30/so_corpus_fix/work/tool` (the fixed tool, byte-identical to the patch applied to the input), `I=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin`.

## What I verified (measured here)

- **Tests fail before the fix and pass after.** I ran 19 in-memory review-two tests, which write no files.
  - On the input tool: `test_kit_alias_rejects_actual_id` fails because `{'answer': 0.25} is not None`; `test_native_requires_exact_arm_populations` and `test_native_rejects_full_task_identity_conflict` both fail with "Refusal not raised".
  - On `$T`: 19 of 19 pass.
- **`test_synthetic.py` passes 20 of 20** in three configurations: the input tool, `$T` in default mode, and `$T` with `--review2-checks` forced on. The four review-two CLI tests pass on `$T` in default mode. These runs used a private user-namespace tmpfs, so no fixture files persist anywhere.
- **The default path is unchanged.** Every behavioural change is gated on `review2_checks`, which defaults to False (`$T/ingest_read.py:170,231,430,658,687,960`). With the switch off, the alias lookup returns the same first row as the old `fetchone()` (`:428-431`).
  - The read gzip contains no `tool_version`, so read and orphan bytes are identical. Only the index's `tool_version` changes.
  - The 17 other tool files are byte-identical to the input. `corpus_score.py` and `pub.py` do not use the changed classes.
- **The native identity audit's candidate pool is complete.** The report did not show this; I did.
  - The 9 hash-verified input files yield exactly 6,967 records, which equals the published `orphan_count` of 6,967.
  - The remaining 9,511 − 6,967 = 2,544 = 4 × 636 return rows are all attached to `devrows:` items (`$T/ingest_read.py:813-822`). None of them can be a candidate for a bare task id.
  - Every one of the 636 keys has exactly 2 candidates, with 0 conflicting fields. So the identity check would not refuse the published native read. The identity half of basis D is now shown, not just inferred.

## Findings

1. **MEDIUM. With the switch on, a merely partial native return becomes a hard refusal, even with `--archive-partial`.**
   - `validate_populations` raises `Refusal` for a missing arm and for an arm whose keys are a strict subset of the declared set (`$T/ingest_read.py:715-717,728-730`). `main` maps `Refusal` to exit 2 before the `--archive-partial` check (`:980,992-994`).
   - This contradicts the documented contract: native short counts exit 2 only "unless `--archive-partial`" (`$T/SCHEMA.md:37-38`, `$T/HOWTO.md:11`). It also breaks the kit precedent, where population mismatches are issues, not refusals (`:468-475`).
   - Probe: 1 of 2 declared keys in `scripted`. Default mode records the issue `scripted: 1 != expected 2`, which `--archive-partial` can archive. Switch mode raises `Mismatched native keys for arm scripted`.
   - The test codifies the refusal (`$T/tests/test_review2.py:235-243`). Risk: a final partial native return becomes un-archivable with the switch on. That pushes operators to rerun without the switch, which re-enables all three defects.
   - **Smallest fix:** in `validate_populations`, when a required arm is missing or its keys are a strict subset of the expected set, append to `self.issues` instead of raising. Keep `Refusal` for undeclared arms, keys outside the declared set, invalid or contradictory declarations, and label mismatches. Change the test to expect exit 2 without `--archive-partial`, and exit 0 with `partial=true` when it is passed.

2. **MEDIUM. The fixes are inert for new reads unless someone passes the flag.**
   - `add_read.sh` calls `ingest` without `--review2-checks` (`$T/add_read.sh:10`), and neither `SCHEMA.md` nor `HOWTO.md` mentions the switch.
   - `LEFTOVER.md:9` routes every new read (D@544 and every step-400/600 read) through `add_read.sh`, so all three defects stay live for those reads.
   - Default-off was mandated by the dispatch, so this is not a patch defect, but it needs an owner action.
   - **Smallest fix:** document the switch in `SCHEMA.md` (the native completion paragraph and the kit alias row). Then either have the caller append `--review2-checks` (`add_read.sh` forwards `"$@"`) or add it at `add_read.sh:10`. New read_ids only; published reads are unaffected.

3. **LOW. Duplicate eligible report rows with different scores resolve silently to the first row, in both modes.**
   - `$T/ingest_read.py:425-433`. Probe: two key-only `devrows:q` rows scoring 0.25 and 0.75 give scores of 0.25, exit 0, with no issue.
   - The same applies to duplicate exact-id rows. Fix 1 already iterates the candidates, so detecting this is a one-line change.
   - **Smallest fix (under the switch):** collect every eligible row (exact matches, otherwise key-only aliases) and refuse or add an issue if their `scores` differ.

4. **LOW. Native report rows with no `arm` field are skipped without any check.**
   - Rows under `arms.X` that have no `arm` are skipped by `prepare` (`$T/ingest_read.py:641`) and are exempt from the new label check (`:705`). So the duplicate/contradiction check at `:646-649` never runs on them.
   - Probe: journal `scripted` score 1.0 and report `arms.scripted` score 0.0 give exit 0, complete, in both modes.
   - **Smallest fix (under the switch):** compare each such row, as `dict(row, arm=X)`, against the normalized (key, X) row and refuse if they differ.

5. **LOW. Native row fields override the joined task without comparison.**
   - `room`, `question_type` and `stratum` come from the row (`$T/ingest_read.py:676-678`). Fix 3 compares task candidates only, not the row against the task.
   - Probe: task room `r1` and row room `r2` give a normalized `room` of `r2`, exit 0. The raw input keeps `r1`.
   - **Smallest fix (under the switch):** refuse when the row and the selected task both supply `room` (and `question`, `options`, `scene` or `video` if rows carry them) with different values.

6. **LOW. With `--inputs`, a declared native key that has no task is emitted with null question and truth, and the status is complete.**
   - `$T/ingest_read.py:654`. The routed adapter fails in this case (`:529-530`, `SCHEMA.md:38`), and `SCHEMA.md:89-90` only documents nulls for runs without inputs.
   - Probe P7 confirms this in both modes. The published native read is not affected: all 636 keys have candidates.
   - **Smallest fix (under the switch):** if any `inputs/` path was loaded, refuse or add an issue for keys with zero candidates.

7. **INFO. The no-re-ingest argument holds, with these qualifications.**
   - **Kit reads without report sources (4 reads, basis B):** each has 0 report sources in the index, so the alias code is unreachable.
   - **Routed and offread reads (7 reads, basis A):** their code paths are unchanged. The offread `prepare` does no report lookup.
   - **Kit reads with report sources (6 reads, basis C):** the inference is valid.
     - An actual-ID `devrows:X` report row can attach only to an item whose id is exactly `devrows:X` in the same family (`$T/ingest_read.py:819-821`). Zero orphans therefore excludes the review's case unless such items exist.
     - Cheap proof on Trinity: scan those 6 published read files for any `item_id` starting with `devrows:`. If there are none, zero orphans proves the defect never fired.
   - **Native read (basis D):** two parts are still inferred.
     - Whether the arm key sets equal the declared set. INDEX has counts only.
     - Whether the `R1.json` arm-array names match the row labels. `R1.json` is not on this node.
     - To certify both, run `$T` with and without `--review2-checks` on the native source into a scratch root on trinity-3-30, and compare the read sha256 values.
   - **Tool version:** all 18 published entries record `tool_version` `ebd8c6d0…`, not the input's `97bb63d8…`. "Unchanged" means the patch adds no difference relative to the input script, not that a re-ingest reproduces the published bytes. The report says this (`out/REPORT.md:28`).

8. **INFO. Additive task evidence is accepted for native reads but never attached to the read.**
   - For all 636 native keys, the selected candidate (`TASKS.jsonl` for 186 keys, `CAMERA_TASKS.jsonl` for 450) lacks `room_key`. The `devs1_routed.json` candidate that carries it lands in the orphan sidecar, because emit never matches bare task ids for `devrows:` items (`$T/ingest_read.py:813-822`).
   - This complies with the sidecar contract (`SCHEMA.md:57-62`). But the report's "preserves the valid additive room_key evidence" (`out/REPORT.md:24`) only means the check does not refuse. Analyses that read only `reads/` will not see native `room_key`.
   - Changing this alters bytes, so it would need new read_ids.
