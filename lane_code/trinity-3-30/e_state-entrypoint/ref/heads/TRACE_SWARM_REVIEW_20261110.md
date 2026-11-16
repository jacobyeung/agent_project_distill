# Trace review swarm (swarm_ops, 2026-11-10)

## Question
Can a swarm of independent model readers, one per training row or model output, find the defects in our trace sets fast and cheaply enough to run before every training job? And which defects do the sets read tonight carry? Those sets were:
- the CP1-Rv routing rows r4, r5 and r6;
- the vxm object rows, original and m4;
- the ground formats 3.12.2 (fixtures v1, v3 and v4) and 3.13 (r1 and r2);
- the routed dev-858 outputs.

## Answer
Yes. A row costs about $0.05-0.07 and 0.6 minutes with one Codex gpt-6.1-sol (high) session. Of roughly 5,900 sessions, none failed after its one retry.
- The readers recompute numbers reliably. Across the 520 set-1 routing rows they found no arithmetic, sign, angle-wrap, option-letter or label error.
- They miss rules that a question leaves unstated. Category summaries (one gpt-6-astra high session per category) catch those, so they are the stage that finds template defects. A deterministic scan of every row then gives each template defect's exact prevalence.
- Defects found and fixed tonight (owning lane, then the re-read that confirmed the fix):
  - r5 medium direction: 6,721 of 15,162 questions omitted the 135-degree sentence, yet the target claimed the question stated it. 974 answers depended on that rule. Fixed in r6, where all 15,162 state the rule once.
  - vxm medium direction: 2,538 of 18,327 rows said "behind" with a left/right answer. 0 remain in m4.
  - 101 misspelt object names, found by one session over the 2,302 distinct names. The name map v2 removed nearly all of them.
  - Ground 3.12.2: the shuffle broke medium phrases, and simulated-miss rows sat inside the selection files. Both are fixed in fixtures v3 and v4.
  - Spec 3.13: the printed gap disagreed with the printed witness points. Fixed in r2.
- Dev-858 with GT masks (geometry logged by mdg_next):
  - The single-frame surface-median centre explains 79-83% of the direction errors. Merged centres raise hard direction by 11.3 points and medium by 8.9.
  - Depth underestimates explain 52% of the absolute-distance errors, all in shared frames.
  - Frame refusals explain 67% of the relative-distance errors.
- Benchmark wording (VSI-Bench 5,130, local question file): medium questions always carry the single exact sentence "An object is to my back if I would have to turn at least 135 degrees in order to face it." and the option "back". The verb is always "is", even for plurals ("is the shoes"). Our rows should copy these quirks.

## Evidence
- Runs live in /scratch/jjyeung/orch_cd/swarm_ops/work/runs/<set>/: run.json, units/, reports/<id>/{report.md, verdict.json}, summary/<category>.md and SUMMARY.md, status.json. The events are in /scratch/jjyeung/orch_cd/swarm_ops/events/, and every finding was also sent to the owning lane's inbox.
- The exact population counts come from deterministic scans:
  - runs/set1b/POPULATION_COUNTS.md (vxm);
  - runs/set5/POPULATION_COUNTS.json (r6);
