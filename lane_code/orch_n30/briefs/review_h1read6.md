# Lane review_h1read6 (Devin, runs on trinity-1-3): one short independent refute review of h1read kit fix round 6 (admission of leg R1's exports)
Lane folder: /scratch/jjyeung/orch_n30/review_h1read6 on trinity-1-3. Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_h1read6/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are a reviewer: you write only in your lane folder and your events folder, and you test in copies under your lane folder. No GPU, no Orchard call, no ssh, no copy above 20 MB, no Git, no deletion. You fix nothing and you do not talk to the builder. Time budget 45 minutes.

## What and why
The h1read kit (/scratch/jjyeung/orch_n30/cont_ops/work/h1read/, read only; fix 5 reviewed GO in events/review_h1read5/) reads exports directly. Leg R1 trains run 673bc60f (launch packet /scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052, KH okh7/x_69d2930d, m100/m200) and continues as run 05b8ac69 (/scratch/jjyeung/orch_n30/r1_ops/work/snap_c60b9015, KH x_7f1589c1, m400/m600). The registered pooled harm rule (events/pooled_rule/REGISTERED_POOLED_RULE_R1.md, POOLED_RULE_REGISTRATION_v3.md) decides R1's boundaries from this kit's direct reads of families main and a7, and requires that the files under kit/reader/ stay unchanged except chain.py, paired_read.py, worker.py, x7.py and read_filter.py. Codex (GPT family; you are the cross-family reviewer) built fix 6. Builder brief: FIX_BRIEF_R6.md; report: FIX6.md.

## Do
Try to refute each of the following, with file:line evidence and a test in a copy where possible:
1. binding.py and orchard_launcher.py admit exactly the R1 identities: run, namespace, KH, generations, steps, object names, .done receipts, stop claims and artifact path. Each matches what the packets' b/c.sh and configs really write (check yourself, e.g. snap_fac07052/work/tree/launch_s1/b/c.sh:404-430). Everything else still refuses.
2. No kit/reader file and no evaluator, scorer or adapter byte changed against fix 5 (evidence/FINAL_PINS.json at fix 5 = f8911c19; compare).
3. The fix-5 prepares (469ddece a7 direct and unfiltered, D0/H1 runs) stay byte-identical in plan bytes and plan_sha256.
4. For fixture R1 prepares of main and a7 with --types direct, build_manifest.py (events/pooled_rule/, run a copy) gives a config block equal to the registered baseline manifest's, apart from the registered dev-S1 type-filter allowance. pooled_harm_rule_v3.py --calibration accepts the manifests, or the refusal is explained.
5. All suites pass in a copy, and SHA256SUMS / FINAL_PINS cover every changed file.

## Deliver
REVIEW_VERDICT_H1READ6.md in the events folder: GO, GO AFTER FIXES (numbered, each with file:line and a failing test), or NO-GO; at most 30 lines. Also write a RESULT event (at most 15 lines). Then exit. Message the orchestrator only for blockers.
