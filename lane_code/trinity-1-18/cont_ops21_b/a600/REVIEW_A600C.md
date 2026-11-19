GO AFTER FIXES

1. **Add export-archive validation before scoring, with a rejection test.** The unchanged scorer checks export labels but ignores `archive_sha256` ([score_r5_look.py:47](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/in/out4s/score_r5_look.py:47)). I replaced only the synthetic return’s archive hash with the step-400 hash `dcd49569…`; `load(...,600,...)` still accepted all 450 rows. The plan correctly pins `673c147c…` ([READ_PLAN_C600.json:26](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/READ_PLAN_C600.json:26)). Preserve the original scorer; add a validation wrapper that checks the return’s archive hash and declared bytes against the plan. Existing negative tests mutate only `IDENTITY.json` ([test_score_c600.py:125](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/test_score_c600.py:125)).

Other checks passed:

- **Build equivalence:** Independently compared all 15 delivery, 927 payload and three bundle members. Only the eight reported delivery members, payload `9.json`, and bundle `0.json`/`7.py` changed. The operator changes exactly match [build_r11.py:119](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/build_r11.py:119). All 450 camera IDs are unique; items, settings, serving pins, memo/tower code, USR1 shell and return code remain unchanged.
- **Production binding:** Fill checks reject step 400, `m400`, the old object/hash and incorrect byte totals. The done-marker checks and four downloads target step 600 ([o_place_pull_fill_c600.sh:19](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/o_place_pull_fill_c600.sh:19)). Generated READ_PLAN matches the package.
- **Execution and duplication:** Five generated scripts match their generator exactly. Python 3.6.8 compiled 28 distinct sources; seven shell syntax checks passed. Fresh-stage, no-retry, empty-general and return-pool guards remain intact ([o_sub_c600.sh:54](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/o_sub_c600.sh:54)).
- **Walltime:** Recomputed `1.25 × (3579.215 + 76.592) + 1800 + 1200 + 3000 = 10569.759 < 10800` seconds. Three hours satisfies the requested margin ([TIMING.json:2](/scratch/jjyeung/orch_n30/cont_ops21_b/a600/rehearsal/TIMING.json:2)); inferred step-400 startup was approximately 375 seconds.
- **Scoring arithmetic:** Recomputed full-400 versus camera-only-600 results. Camera dictionaries, intervals, calls and H3 decisions match at **99.82%**; scores are 81.600%, 76.133% and 94.667%. Missing noncamera types remain incomplete. These are synthetic compatibility results.

Commands/checks ran: `diff -u` on builders, generators and dry checks; `bash -n`; `/usr/bin/python3 -B -c` for archive/seal comparisons, compilation, regeneration, dry checks and guards; p1cpu Python with one-thread limits for scorer and operator tests. All test writes were replaced by in-memory capture or comparison.

`dryres2` passed; `dry2` reproduced only the two documented missing-policy-body failures. Operator full/partial/stop cases passed. Live archives, Orchard execution and signal delivery remain untested.

`REVIEW_A600C.md` was not written because this session’s filesystem permissions prohibit writes.