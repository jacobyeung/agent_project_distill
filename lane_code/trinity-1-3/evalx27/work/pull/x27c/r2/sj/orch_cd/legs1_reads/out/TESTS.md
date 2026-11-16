The delivery passes 112 CPU unit tests, 14 retained synthetic decision scenarios, 8 full-journal integration cases, 20 parent-metadata dry binds, and three real parent journal merges. No GPU inference, real LEG export load, network transfer or parent weight staging ran here.

| Evidence | Result and scope |
|---|---|
| `TEST_RUN_DELIVERY_FINAL.log` | 112 tests; export inventory/hash/shape/step refusals, room bootstrap, all decision rules, trained-group admission, dense-frame/geometry checks, request controls, native scoring, safe archive receive, and native random-model decoding. |
| `SYNTHETIC_TESTS_FINAL.log`, `work/synthetic_journals_final/RESULTS.json` | 14 persisted normalized-journal scenarios trip m100 primary/route reversal, R3 caps/dev-858 regression, R1 score/call/version failures, R1b path/score failures, R2 positive/negative/zero intervals and persistent m200 R1. Synthetic evidence cannot enter empirical merge admission. |
| `REVIEWED_INTEGRATION.log` | Eight full raw-journal cases exercise both reviewed kits, main and control families, CP1 budget derivation and f17 ON16k. Three paired reports, the room-bootstrap oracle and admission negatives also pass. Toy tokenizer/parity fixtures are explicitly synthetic. |
| `DRY_BIND_FINAL.log`, `CELLS.json` | Six direct requests (three families × two steps), eight supported-600 routed requests, six main-1525 free-generation requests. All are dry, parent stand-ins. No export bytes or real PNG pixels were checked. |
| `PARENT_MERGE.log`, `PARENT_AWAY_MERGE.log`, `PARENT_FORWARD_MERGE.log` | Byte-preserving copies of real parent requests/journals merged through the copied r5 adapter and reviewed kit. All three arms ON16k/B2048/B4096 pass. |
| `PARENT_REPORT.log`, `PARENT_STANDIN.json`, `PARENT_STANDIN.md` | Exact zero paired differences and zero-width intervals against the parent; prints “no difference from the parent.” Missing f17, dev-858 and routed evidence remains incomplete. |
| `NATIVE_CPU_SMOKE.json` | Tiny random Qwen3.5 runs its actual pose/depth heads and tool-response/replay loop with controlled token choices. No model function replacement, learned-accuracy claim or full MDG/G3T loader claim. |

The geometry test feeds synthetic raw G3T-shaped arrays through the frozen scale estimator and camera conversion, then the native explicit-geometry loader. It verifies that scale 2 changes depth 2 to depth 4 exactly once. It is not a G3T neural-forward test. Native request tests reject GT masks, changed fusion/prompt/layout, small generation caps, zero artifact hashes, changed bindings, fallback geometry, dry launches and unsupported full scripted scope. The test suite is focused; it does not claim exhaustive testing of every transitive trainer failure.

Reproduce with fresh output directories. The unit fixtures use unique retained directories and never clean up:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/test_reads.py
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/synthetic.py --dest work/synthetic_recheck
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/dry_bind.py --dest work/bind_recheck
/scratch/jjyeung/envs/p1cpu/bin/python -I -s work/vendor/r5/test_merge.py suite --dest work/integration_recheck
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/decision.py \
  --leg work/parent_main_merge --parent work/parent_main_merge \
  --away work/parent_away_merge --forward work/parent_forward_merge \
  --step 100 --parent-standin --output work/parent_recheck.json
```

The unit runner hides CUDA, enables offline mode, limits CPU threads and directs caches/temp files into the lane. It retains fixtures. Rechecks consume additional local space; the delivered lane is below 2 GB.

Production checks still required: real export/base staging, every native trained-group load, true PNG/dense-frame byte admission, real tokenizer prompts, GPU parity, full native MDG/G3T inference, behavior of matched trained flags, complete scripted type coverage, f17 comparisons, dev-858 source scoring and official full-set results. These are not converted to passing CPU fixtures.
