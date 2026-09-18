# Design review — REQ-20260917-232

## A. Rubric and admission

**Adopt a tiered rubric, but admit none of the reviewed targets unchanged.** The three review submissions contain four completed targets: v3/1600, v3/2544, v5.2/1582 and v6/1569; v3/3919 produced incomplete JSON, not a target. Correct answer bytes alone do not establish correct supervision. [V3, lines 5–23][r3]; [V5.2, lines 26–32][r52]; [V6, lines 82–88][r6].

**Tier I blocks admission:** a wrong answer, invented observation or measurement, wrong identity/frame/direction, unsupported numerical precision, native-final explanatory leakage, actual tool/planner artifacts, or a changed qualification that teaches a false scope, certainty or condition. **Tier II records incomplete auditing or explanation:** a correct fact whose citation omits its local binding, a meaning-preserving paraphrase, or an incomplete explanation of a supported calculation.

The seven checks should remain, with severity assigned to the defect: checks 1 and 7 are hard gates; checks 2–4 distinguish false content from incomplete citation or explanation; check 5 distinguishes actual tool/process artifacts from thin prose; check 6 blocks inventions. Coordinate formatting and literal wording are not independent scientific truths. The specifications currently require every check to pass, and v6 additionally requires verbatim qualifications. [V5.2 specification, lines 12, 35–39][p52]; [V6 specification, lines 5, 29–33][p6].

| Target / failed check | Classification under the proposed rubric |
|---|---|
| v3/1600 — 4 | **II:** omitted array-index correction and unsuccessful optional frame-24 search; the review establishes no resulting wrong measurement, and API-index debugging itself is not perceptual knowledge. |
| v3/1600 — 5 | **I:** variable/data-shape debugging and future planner narration; **II:** missing explanation of the completed closest-point method. |
| v3/2544 — 2 | **I:** ordinal names switch identities 24/25/15 to 15/24/25, and a static summary becomes a persistence assertion. |
| v3/2544 — 3 | **I:** image-relative truncation becomes an unscoped vertical-extent statement. |
| v3/2544 — 4 | **I:** warnings lose their affected objects, frames and image direction; retaining “likely” does not preserve these referents. |
| v3/2544 — 5 | **I:** expert-persona/thought-summary and feature-analysis artifacts; **II:** vague, incomplete explanation. |
| v3/2544 — 6 | **I:** the identity reassignment and unsupported persistence above. |
| v5.2/1582 — 2 | **I:** “exactly −1.8171” overstates source precision; **II:** missing operand and re-check-instruction citations, whose support exists elsewhere in the bound evidence. |
| v5.2/1582 — 3 | **I:** unsupported exactness; **II:** missing explanation connecting the signed angle to right. |
| v5.2/1582 — 4 | **I:** the same precision inflation; **II:** omitted re-check citation and explanatory convention, plus omitted unused-Z discard advice and explicit horizontal-unaffected wording where the retained warning already specifies vertical/Z scope. |
| v5.2/1582 — 5 | **I:** “archived measurement,” plan verification, unavailable verifier and execution-summary references; **II:** missing geometric explanation. |
| v6/1569 — 2 | **I:** R2 broadens door-only horizontal-unaffected wording to door and toilet; **II:** missing local frame/operation citations, although the archive contains the asserted records. |
| v6/1569 — 3 | **II:** missing ordered-vector explanation; numbers and rounding pass; the omitted condition on the sign rule also raises the Tier-I issue under check 4 below. |
| v6/1569 — 4 | **I:** R2 changes warning scope, and the sign rule drops its Z-up condition; dropping the qualified cross-frame comparison also removes useful uncertainty; **II:** equivalent paraphrasing and omitted discard advice about unused Z extent. |
| v6/1569 — 5 | **II:** “centroid was derived,” undefined comparisons, omitted back-threshold application and missing left-to-B mapping are thin explanations; the review explicitly finds no literal tool names, paths or coordinate triples. |

The table covers every failed check; overlapping findings are one defect, not several independent errors. Evidence: [V3, lines 25–62][r3], [V5.2, lines 27–57][r52], and [V6, lines 34–88][r6]. I disagree with treating every procedural correction or omitted unused-axis instruction as scientifically blocking; consequential visual corrections still block if lost.

**None would be admitted under Tier-I-only blocking.** The targets would respectively supervise unavailable debugging/planning behavior (1600), wrong object identities and persistence (2544), false numerical exactness and verifier behavior (1582), and an overgeneralized reliability qualification/sign rule (1569). The last target’s R2 error alone suffices; this conclusion does not depend on calling incomplete explanations unsafe. The incomplete 3919 response remains unusable. These are proposed reclassifications, not changes to existing admission decisions.

## B. Smallest substantive redesign

The pipeline confuses **finding a token with binding a fact**, then mistakes deterministic formatting for semantic preservation. The v5.2 audit found 20/24 recorded first-failure findings were false positives, not that 83% of all checks or rejected sheets were wrong; the sample cannot estimate population precision. Its definition allowed nearby evidence, whereas the admission review required the claim’s own citations. [Audit, lines 3–7, 52][audit]; [V5.2 specification, lines 33–39][p52].

Bind each observation to its **own measurement record**, carrying value, identity, frame and reference together: fan O2 needs E27.L20 plus E27.L8–L11; door O3 needs E28.L20 plus E28.L8–L11; toilet O4 needs E29.L20 plus E29.L8–L11; O5/O6 analogously need E38/E44.L8–L11 and L20. Bind door warnings separately to E21/E35.L7–L8, L20 and L30–L32. The frame lists E14.L17 and E15.L17 establish availability, not which measurement belongs to a frame. A deterministic join through the archived call/return and instance identity can attach these citations without asking a model to repair them. [Canonical rendering, E21/E27–29/E35/E38/E44][e].

Preserve each qualification’s exact source text in the sheet’s audit fields, normalize tool terminology once into student-facing wording with the same scope and meaning, and copy that wording **verbatim from sheet to target**. Keep object, frame, image/world reference, affected quantity and exceptions attached; never combine qualifications across objects in the reasoning. Crucially, v6 already copies its sheet’s wording: the omission of “consider dropping it” exists in the sheet itself, so changing only the renderer cannot restore it. [Sheet, lines 3306, 3374][sheet]; [Target, lines 4, 6, 17][target]. Retain the toilet comparison’s uncertainty and any consequential correction; discard actual planning chatter, not whole mixed-content groups.

Give each calculation a typed operation and **one explanatory sentence stating geometric meaning and the applicable sign/direction convention**. For this archive, describe the signed turn from fan→door to fan→toilet, and describe the ordered facing-vector × target-vector cross product with the recorded Z-up/positive-means-left convention; retain each operand’s own frame and the archived result. Then connect the recorded angles to the question’s 135-degree threshold and map left to B using the options. These explanations translate recorded operations; they do not infer new geometry. [Rendering, E31.L11–L22, E33.L33, E46.L11–L22, E48.L24–L27, E3.L4–L5][e].

Replace “was derived” with supported spatial content, and use operation-specific templates for the short reasoning chain; unknown operations remain deferred. Allow numbers from referenced observations and the question as well as calculations: v6’s calculations-only vocabulary otherwise excludes O1’s 135-degree threshold. Replace blanket bans on words such as “assume” or “conventions” with checks for actual tool/process references. [V6 brief, lines 19–22][b6]; [V6 review, lines 70–76][r6].

**Drop Stage C from the production path.** Its 199/405 disputed overrules are finding-level disagreements across repeated attempts, not a 49.1% target-error estimate; nevertheless, its decisions neither repair citations nor establish independent support. All seven v6 overrules pass literal containment yet fail the intended binding check. Keep deterministic record joins, scoped rendering and one independent review of the admission changes and pilot; use sampled independent audits during bulk conversion, not another model’s per-target permission to overrule. [V5.2 review, lines 59, 434–466][r52]; [V6 review, lines 50–70][r6].

The design premise “every remaining failure enters through stage B” is too strong: the sheet already contains incomplete qualifications, generic operations and a blanket disposition of substantive uncertainty. Passing 476 CPU tests does not establish semantic quality. Add only fixtures reproducing those observed failures, including positive controls for correct nearby-record bindings. [V6 brief, line 10][b6]; [Sheet, lines 838, 2001–2105, 3306][sheet]; [V6 report, lines 6–8][report6].

## C. Conversion cost and first training size

The five archived qid-1569 calls took 151.841, 59.289, 93.806, 48.036 and 53.311 seconds: **81.3 seconds/call on this one example**, excluding queue/barrier delays. Their visible outputs ranged from 150 to 4,897 tokens, with additional thinking tokens; 32,768 is a ceiling, not actual output consumption. [Call records, attempts 001–005, each provider.json line 4][calls].

For planning, assume **2 minutes/call, 75% effective utilization**, and 3–5 calls per accepted source trace; these are explicit capacity assumptions, not measured fleet throughput. Wall hours = N × calls/trace × minutes/call ÷ (60 × concurrent calls × utilization). Reserve September 21–23 for a 48-hour conversion window, September 23–24 for the stated one-day training/evaluation budget, and September 24–25 for paper completion; stream earlier-ready traces immediately.

| Accepted source traces attempted | Calls at 3–5 each | Maximum output-budget tokens | Wall time at 32 concurrent calls | Concurrency needed for 48 hours |
|---:|---:|---:|---:|---:|
| 5,000 | 15,000–25,000 | 0.492–0.819 billion | 20.8–34.7 hours | 14–24 |
| 10,000 | 30,000–50,000 | 0.983–1.638 billion | 41.7–69.4 hours | 28–47 |
| 20,000 | 60,000–100,000 | 1.966–3.277 billion | 83.3–138.9 hours | 56–93 |

At the recorded two-worker concurrency, even 5,000 take approximately 14–23 days under these assumptions. Doubling mean latency doubles the table’s time or required concurrency. Input-token limits, shared collector demand, retries and output throughput can prevent linear scaling; the documented shared input ceiling is 8M tokens/minute, not a reservation for conversion. [V6 report, line 9][report6]; [Dispatch, line 239][dispatch].

One extraction call plus deterministic binding/rendering/reasoning needs **5k/10k/20k calls**, approximately **6.9/13.9/27.8 hours at concurrency 32**, or **5/10/19 concurrent calls for 48 hours**, under the same assumptions. Remove Stage C, deterministic-repairable citation retries, and the separate Stage-B prose call; retain at most one targeted extraction repair for an actual unresolved defect. Keep the output ceiling and shorten redundant requested content instead of inducing truncation with a smaller cap.

These are source-processing budgets, not guarantees of admitted-target yield: the reviewed designs admitted zero targets. If admission yield is y and repairs add fraction r of a call per source, producing M targets needs approximately M(1+r)/y calls with the proposed pipeline; 20,000 sources cannot produce 20,000 admitted targets when y<1. Measure latency, tokens, retries and yield on the clean pilot before committing spend.

**Start the first informative LoRA run at 1,000 admitted, diverse targets; aim for 5,000 for the main comparison.** This is a practical starting threshold, not an empirically established minimum: it permits hundreds of examples across several spatial families and many scenes while leaving time for an end-to-end result. Sixteen examples test the converter, not transfer; waiting for 20,000 postpones the first learning signal unnecessarily.

Use the same training subset for both backbones, keep training scenes disjoint from all three benchmarks, and compare each base/distilled pair with identical RGB inputs and inference settings. Report paired benchmark changes with uncertainty; training count alone cannot determine statistical power or guarantee gains. Base-versus-distilled results test transfer from this training recipe, but an answer-only matched control—or a narrower claim—is needed to attribute gains specifically to observation reasoning.

## D. Recommended path and decision rule

**Recommend a one-call converter, a Tier-I admission gate, a 16-trace clean-pool pilot, and training as soon as 1,000 admitted targets are available.** Keep Tier-II findings visible and measured; do not turn their wording preferences into hidden admission gates.

Pipeline changes, each scoped to an observed failure:

1. Build typed measurement records from existing call/return pairs and attach each observation’s own value, instance, frame and qualification citations deterministically.
2. Have Stage A select substantive spatial facts, calculations, uncertainty and corrections into a compact sheet, preserving source qualifications and one complete student-facing version.
3. Render that version verbatim with its scope, and render calculation/reasoning templates with operand order, geometric meaning, recorded conventions, question thresholds and option mapping.
4. Remove production Stage B and Stage C calls, retain byte-exact answers and evidence isolation, and allow one targeted extraction repair before deferring an unresolved trace.
5. Fix the strict clean adapter’s separate source/output-root handling without weakening acceptance or split checks, then keep benchmark fallback examples out of student training.

Pilot protocol: freeze the converter and rubric, select **16 accepted clean-pool traces before conversion**, and stratify across four spatial task families, multiple scenes and trace lengths, including existing warning/correction cases; record the sampling rule and never replace failures with easier examples. Verify the actual clean snapshot first: v6 used benchmark fallback after the strict adapter refused the source/output roots, so its eight examples do not establish clean-pool readiness. [V6 report, lines 2, 8][report6]; [V6 specification, line 25][p6].

Run reproducing fixtures and the pilot, then give **one independent reviewer** the admission/legality/scoring changes and all 16 outcomes, including rejects and both versions of repaired targets. Review each final candidate against its canonical source, independently of converter self-assessments, and record Tier-I defects, first-pass and repaired yield, Tier-II record-binding/qualification/explanation rates, actual tokens, call latency and total wall time.

**Start bounded bulk conversion when at least 14/16 sources yield independently Tier-I-clean targets, no target proposed for admission contains a Tier-I defect, the remaining cases are explicitly deferred, and measured throughput fits the reserved window.** Keep all 16 in the yield denominator; reject/deferred cases must not disappear. Tier-II scores are reported, not an additional pass threshold. If the rule fails, reproduce the specific defect and return it for a bounded decision rather than automatically commissioning another converter round.

Freeze the reviewed version for bulk conversion and audit a random 16 admitted targets per 1,000; any Tier-I defect pauses the affected template and quarantines its affected batch for correction. Even ideal independent sampling with 0 failures in 16 leaves a one-sided 95% upper defect-rate bound of **17.1%**; the pilot is a release diagnostic, not proof of near-perfect reliability.

**Only the user can adopt the tiered rubric as the admission definition, authorize replacing per-target independent admission with a reviewed pipeline plus sampling, and choose the data/spend target and acceptable paper claim.** This report changes no verdict and launches no provider work.

Delivery limitation: the session’s higher-priority read-only filesystem rejected `out/HEARTBEAT.log` with EROFS, so neither the heartbeat nor `out/DESIGN_REVIEW.md` could be persisted; the complete report is returned here for the orchestrator to save. The requested ≤120-line A–D report overrides the boilerplate’s ≤20-line final format; version comparisons are retained because this review explicitly requires them, and the lane-only scope precludes writing the external experiment queue.

[r3]: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_review_converter_v3/out/REVIEW.md:5
[r52]: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_review_converter_v5_2/out/REVIEW.md:26
[r6]: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_review_converter_v6/out/REVIEW.md:34
[p52]: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_review_converter_v5_2/PROMPT.md:35
[p6]: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_review_converter_v6/PROMPT.md:5
[audit]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v5_2_20260918/out/VALIDATOR_AUDIT.md:3
[e]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/out/eight_v6/revalidated/1569/evidence_rendering.txt:547
[sheet]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/out/eight_v6/revalidated/1569/fact_sheet.json:3306
[target]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/out/eight_v6/revalidated/1569/rendered_target.txt:1
[b6]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/BRIEF.md:19
[report6]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/out/REPORT.md:2
[calls]: /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_20260918/out/eight_v6_preparation_retry/run/1569/attempts/001/provider.json:4
[dispatch]: /home/jjyeung/agent_project_distill/agent/scripts/DISPATCH_BOILERPLATE.md:239

LANE_DONE