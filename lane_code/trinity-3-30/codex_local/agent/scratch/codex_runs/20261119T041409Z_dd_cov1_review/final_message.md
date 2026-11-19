The current rows pass all requested preservation, arithmetic, and kit-validation checks. The generator has three verified acceptance gaps. No files were written.

| Check | Verified result |
|---|---|
| Source matching and unchanged field values | 6,000/6,000 pass |
| Exact template substitution, object names, unit wording, recomputed identity, provenance edit | 6,000/6,000 pass |
| Nested units-row question/qid consistency | 4,500/4,500 pass |
| Unique output qids | 6,000; zero duplicates |
| Source reuse | 6,000 distinct sources; maximum reuse **1** |
| Non-metre gap, conversion factor, HALF_UP rounding, answers and unit agreement | 4,500/4,500 pass |
| Metre gap/answer agreement and absence of conversion | 1,500/1,500 pass |
| Kit `pack` → `validate`, outputs | 4,500 units + 1,500 distance pass; **0 failures** |
| Same validation, sources | 4,500 units + 1,500 distance pass; **0 failures** |
| Output counts | All **60 cells contain 100 rows**; 1,500 per unit |
| Artifact hashes | Both decompressed output hashes and generator hash match `SUMMARY.json` |
| Wording review | Read **60 questions**, one per template/unit cell; no verified grammatical or referent ambiguity |
| Whole-output wording scans | **0** object names containing standalone “and”; **0** repeated unit words |
| Available dev-S1 exclusion check | 6,000 sources checked against 150 local dev-S1 IDs, including lineage aliases; **0 overlaps** |

Verified problems:

1. **The generator accepts incomplete output and excessive source reuse.** Two executions with inputs and outputs intercepted entirely in memory returned normally:
   - Four eligible sources produced **4 rows**, despite the configured 6,000-row target.
   - One source repeated four times produced **4 rewordings of that source**, exceeding three.

   Failed rows are skipped without replenishment or a final count assertion at [coverage_rows.py:103](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/pub/coverage_rows.py:103). The generator reports maximum reuse without enforcing it at [coverage_rows.py:145](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/pub/coverage_rows.py:145). Neither defect occurs in the supplied output.

2. **A missing ground-record unit can pass both generator checks.** In memory, removing `ground_record.unit` from units-file line **3**, `a0_units_vsi590k_251501_dd02`, still passed `check_units(..., 'feet')` and `validate_units`. Its answer is `9.84`; its GT value is `9.844477628738037`.

   [coverage_rows.py:46](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/pub/coverage_rows.py:46) substitutes the expected unit when the field is missing. [ground_rows.py:102](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/tree/work/tree_r1/student_pilot/ground_rows.py:102) then defaults to metres, whose numerical check happens to pass. All **4,500 actual rows** contain the correct unit.

3. **Retained candidate IDs conflate rendered variants.** The 6,000 outputs contain **5,121 distinct candidate IDs**, with **879 duplicate excess entries**. Those duplicates already exist among the sources, but every output also shares its candidate ID with its source. For **1,145 metre rows**, the source matches the kit’s candidate-ID formula and the reworded row no longer does.

   The formula includes qid and question at [ground_v312_quality.py:99](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/tree/work/tree_r1/generator/derivgen_v7/derivgen/ground_v312_quality.py:99). The aggregation code uses candidate-ID membership to assign `balanced` at [ground_v312_production.py:145](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/tree/work/tree_r1/generator/derivgen_v7/derivgen/ground_v312_production.py:145), so variants cannot be distinguished there. This is a verified identity ambiguity; `pack`/`validate` does **not** reject it.

4. **The coverage table omits three required counts.** N’s feet, inches and centimetres counts are `None` at [COVERAGE.md:33](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/COVERAGE.md:33), also repeated in the routed-template row. [SUMMARY.json:2](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/pub/SUMMARY.json:2) reports **2,634 / 2,583 / 2,588**, respectively.

Rebuilding distance events is faithful **for the supplied `pack`/`validate` interface**: all 1,500 outputs reconstruct exactly three ordered calls—ground, ground, gap—and preserve the suffix as the packed target. [validate_evidence](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/tree/work/tree_r1/trace_format/ground_v312.py:265) checks ordered call/response attachment and unrecorded responses. This does not reconstruct historical audit metadata or constitute geometry replay.

No new qid-pattern or question-identity rejection was found. All **6,000 output question identities are unique**. The **4,500 `source_qid` and `metric_twin_id` values** preserve their source lineage. However, regeneration through [shuffled_item](/scratch/jjyeung/orch_n30/dist_diag/review_cov1/tree/work/tree_r1/generator/derivgen_v7/derivgen/ground_v312_quality.py:117) replaces all **1,500 metre paraphrases** with the original wording while leaving their sources’ wording intact. Native packing does not invoke that function.

Selection order matches the hash ordering and template rotation for all four supplied 1,500-row groups. An in-memory reversal test produced identical rows; exact-qid exclusions rejected **4 non-bound and 4 K1 test records**. Actual membership/K1 manifests and full candidate pools are absent, so actual exclusion membership and globally lowest-hash selection remain unverified. The primary wording parser is also absent; the supplied paraphrase fallback has no absolute-distance branch.

Finally, **100 rows per cell meets the 6,000 cap**, but falls below ORDER.md’s 400-per-cell target in all 60 cells; satisfying both literally would require 24,000 rows.

**Verdict: GO AFTER FIXES.**