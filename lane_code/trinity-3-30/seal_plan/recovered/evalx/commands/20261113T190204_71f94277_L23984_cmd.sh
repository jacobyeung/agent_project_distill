<!-- recovered by seal_plan: transcript=71f94277 line=23984 utc=2026-11-13T19:02:04.185Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_decision_logic_verdict_and_three_rulings.md <<'EOF'
# ORCH ruling: decision-logic verdict is ACCEPT AFTER FIXES; three rulings, made before any leg read

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_DECISION_LOGIC.md` (read it in full). Admission, scoring, item pairing and the room-level bootstrap are correct and reproduce (71.6436% on 1,375 items, all ten per-type values, an independent bootstrap). The rule layer is not. Fork `legs1_reads/out/decision.py` (sha 2874d0a7, left unchanged) into your lane, fix it there with tests, pin the fork, and send me the pin for a short confirmation review.

## Ruling 1: scope of the stop rule (reviewer's blocker 1)

The registered text is the plan's line 152. The stop rule tests exactly seven types against f17: route planning, counting, relative direction easy, medium and hard, relative distance, object size. Relative count and relative size are reported beside them and never stop the leg. Absolute distance and room size are routed types and belong to R1, not to this rule. Implement a frozen list; every other type is printed as "reported, not tested", on dev-S1 and on dev 858. Keep the reviewer's synthetic test: an f17 better only on an untested type must not stop the leg.

## Ruling 2: what "hits the cap" means in R3 (blocker 2)

The plan's R3 reads: no direct task below f17 with its interval below zero, "and at most 1 answer per 100 hits the cap. A failure raises the direct share or shortens the thinking budget at the next boundary." Under the bounded budget an answer cannot reach the output cap, so counting output-cap rows in the B2048 export tests nothing. The parent itself has 34 budget-forced closes at B2048 (2.23 per 100) and 29 output-cap hits at ON16k (1.90 per 100).

- Count, per arm and per type, both quantities: budget-forced closes at B2048, and output-cap hits at ON16k. Print both for the leg, the parent and f17 where the arm exists.
- The clause is evaluated on the forced closes at B2048, the leg's own policy, in two forms that are both printed: against the registered absolute limit of 1 per 100, and as the paired difference leg minus parent on the same items with its interval.
- Consequence, unchanged from the plan: a failure of this clause never stops the leg; it raises the direct share or shortens the thinking budget at the next boundary. Because the parent already exceeds the absolute limit, the adjustment is triggered only when the leg is worse than the parent with the interval wholly above zero. Say in the report that the absolute limit is exceeded by the parent before any leg training.

## Ruling 3: which thinking arms decide (reviewer's major finding)

The plan's registered baseline (f17 73.50 against the parent 71.64, route planning +35.3, counting +10.5) compares each model under its own policy: f17 thinking on with the 16k cap, the parent under the bounded 2,048 budget. The leg's direct rows are trained under the bounded budget, so that is its own policy.

- **The deciding pair for the stop rule and for R3 is: leg at B2048 against f17 at ON16k**, as registered. The deciding pair for leg minus parent is B2048 against B2048.
- Print the same-budget pair beside each (leg ON16k against f17 ON16k; leg ON16k against parent ON16k) as a sensitivity table, with every table's arms named. If the two pairs disagree on whether a tested type's interval is wholly below zero, say so at the top of the report; I rule on that case when I see it. The launch card's phrase "same thinking budget" is loose wording of mine and is superseded by this ruling.

## Also fix (reviewer's findings 4 to 6)

- The report names the GPU type, the token policy and the arm of every table, and marks untested types.
- Assert the task file's registered sha256 (a2f3fdbd...) for all three merges.
- **The 47-scene cut needs a list that does not exist yet.** `init_audit/F17_EXPOSURE.md` holds counts only, inferred from a division with 183 unresolved keys. Write the 47 native scene identifiers as a file with its derivation and sha256 (from the audit's working files under `/scratch/jjyeung/orch_cd/init_audit/`); say plainly how the 183 unresolved keys bound it (the cut may be "at least these scenes"). Map scenes to physical rooms through the journal's scene-to-room field, count a room as seen if any of its captures is listed, list mixed rooms, and run the same paired machinery on the two strata for both comparisons. The registered decision stays on all items; the cut is printed beside it as a diagnostic.

These rulings are recorded in `/data2/jjyeung/agent_project_data/distill_design/LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md`.
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import datetime
d = "/data2/jjyeung/agent_project_data/distill_design/"
t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
body = f"""# LEG-S1 step-100 decision rules: three clarifications made before any leg read ({t})

**Question.** An independent review of the decision code (`/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_DECISION_LOGIC.md`) found that the rule layer differed from the registered text in `/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md` (lines 152 and 156) and that one clause could not fail. What exactly do the rules test?

**Answer (orchestrator, before any leg checkpoint was read; job 169097 was at about step 15).**
1. Stop rule scope: exactly seven types against f17 on dev-S1 (route planning, counting, relative direction easy/medium/hard, relative distance, object size). Relative count and relative size are reported and never stop the leg. Absolute distance and room size are routed types and belong to R1.
2. R3's cap clause: "hits the cap" is evaluated on budget-forced closes under the leg's own bounded 2,048-token thinking budget, printed both against the registered limit of 1 per 100 and as the paired difference leg minus parent. Output-cap hits with thinking on (16k) are printed beside it. The clause never stops the leg; its registered consequence (raise the direct share or shorten the budget at the next boundary) is triggered only when the leg is worse than the parent with the interval wholly above zero.
3. Deciding arms: each model under its own policy, as in the registered baseline: leg at the bounded budget against f17 with thinking on; leg against parent both at the bounded budget. The same-budget pairs are printed as a sensitivity table; a disagreement between the pairs on a tested type is reported at the top and ruled on then.

**Reasons and evidence.**
- The plan's line 152 names the seven tested types and says the two dev-only types "do not stop the leg"; the code stopped on every primary type. At step 0, f17 leads the parent on relative count by +15.1 [+4.4, +26.9], so a leg equal to its parent would have been stopped falsely.
- Under the bounded budget no answer can reach the output cap, so the code's count was zero by construction. The parent has 34 forced closes in 1,525 answers at the bounded budget (2.23 per 100) and 29 output-cap hits with thinking on (1.90 per 100): the absolute limit is exceeded before any leg training, so only a comparison with the parent carries information about the leg.
- The registered baseline (f17 73.50 against the parent 71.64) already compares own-policy arms; the parent's two arms differ by -0.36 [-0.85, 0.00] on dev-S1 primary.

**Options rejected.** Keeping the code as written (false stops; a vacuous clause). Deciding on same-budget arms only (changes the registered baseline after the fact). Dropping the absolute limit from the report (hides that the parent exceeds it).

**What might not work and how we would notice.** The two arm pairings could disagree on a tested type; the report's first lines say so. The list of the 47 scenes f17 saw is not yet a file; the exposure cut is a diagnostic until that list is hashed.

**Tests that settle it.** The reviewer's synthetic-f17 scope test; a forced-close count test on the parent's journals (34 of 1,525); the confirmation review of the forked decision code.

**Status.** Ruled; fixes ordered from the eval lane (`/scratch/jjyeung/orch_cd/evalx/inbox/`, file ending `ORCH_RULING_decision_logic_verdict_and_three_rulings.md`); confirmation review pending.
"""
open(d + "LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md", "w").write(body)
with open(d + "INDEX.md", "a") as f:
    f.write("- [LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md](LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md): LEG-S1 step-100 rules clarified before any leg read: seven tested types, forced closes for the cap clause (parent already at 2.23 per 100), own-policy arms decide.\n")
print("record written", t)
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: DECISION-LOGIC REVIEW (Claude Opus high; leg_s1_review/REVIEW_VERDICT_DECISION_LOGIC.md): ACCEPT AFTER FIXES. Admission, scoring, pairing, room bootstrap correct and reproduced (71.6436% on 1,375; independent bootstrap matches). BLOCKER 1: stop rule fired on every primary type instead of the plan's seven (a leg equal to its parent would be stopped by f17's +15.1 on relative count). BLOCKER 2: R3 cap test vacuous at B2048 (parent: 34 forced closes = 2.23/100 at B2048, 29 output-cap hits = 1.90/100 at ON16k). MAJOR: leg B2048 vs f17 ON16k arms; report lacks GPU type/policy; 47-scene cut missing and its scene list does not exist as a file. RULINGS ($N, before any leg read): (1) seven tested types; (2) cap clause on forced closes at B2048, absolute and paired vs parent, never a stop, adjustment only if worse than the parent; (3) own-policy arms decide (leg B2048 vs f17 ON16k; leg vs parent at B2048), same-budget pairs as sensitivity. evalx forks decision.py with fixes + tests; confirmation review to follow. Design record: distill_design/LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md (+ INDEX)." >> $C/ORCH_HANDOFF.md; echo done $N