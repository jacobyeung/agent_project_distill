The configured production inputs remain MISSING. Paths below come from the retained reviewer evidence and the reviewed config; no path or owner has been invented.

| Input or evidence | Exact path or config location | Owner | Status |
|---|---|---|---|
| preparation | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json` | tree_rebuild (W) | MISSING |
| code | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/7.json` | orchestrator | MISSING |
| admission | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/review.json` | independent reviewer | MISSING |
| depth_init | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/97a6a3eb/runs/b19c1200/train/step_400/heads.json` | P x_ee227714, staged by W | MISSING |
| config:r2_sampling | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r2_sampling` | W production binding; host audit; independent review | MISSING |
| config:preparation | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:preparation` | W production binding; host audit; independent review | MISSING |
| config:r1_training.row_plan_sha256 | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.row_plan_sha256` | W production binding; host audit; independent review | MISSING |
| config:r1_training.host_receipt | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.host_receipt` | W production binding; host audit; independent review | MISSING |
| config:r1_training.review | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.review` | W production binding; host audit; independent review | MISSING |
| config:r1_training.store_hashes.pose | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.store_hashes.pose` | W production binding; host audit; independent review | MISSING |
| config:r1_training.store_hashes.routing | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.store_hashes.routing` | W production binding; host audit; independent review | MISSING |
| config:r1_training.store_hashes.pointing | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/configs/r1_config_f64.json:r1_training.store_hashes.pointing` | W production binding; host audit; independent review | MISSING |
| student_manifest | `/scratch/jjyeung/orch_n30/sb_f64fix2/kit/read/READ_CONFIG_F64.json:settings_add.student_manifest` | reader lane | MISSING |
| POOL.jsonl | `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl` | MISSING producer identity; orchestrator must assign the producer | MISSING |
| Four-rank GPU pilot | MISSING output directory; `kit/scripts/mem_pilot.py --out DIR` writes `DIR/PILOT.json` | Orchestrator authorizes allocation; pilot operator is MISSING | MISSING; unmeasured |
| Actual all-rank CPU first batches | MISSING evidence output path | W production binding; execution owner must be assigned by orchestrator | MISSING |
| Complete production token audit | MISSING shard and summary output paths; `kit/scripts/token_audit.py --out` selects them | Production owner must be assigned by orchestrator | MISSING |
| Reader memory evidence | MISSING evidence output path | Reader lane | MISSING |

The GPU and closure entries in `sb_f64fix2/out/FIX2_REPORT.md` do not meet an exact-path handoff requirement. The pool entry names its path but explicitly lacks its producer. The orchestrator must assign those fields; this review cannot infer them.

The config omits `r2_sampling`, `preparation`, and `r1_training.store_hashes.{pose,routing,pointing}`. It sets `r1_training.{row_plan_sha256,host_receipt,review}` to null. The report’s phrase “all null” should read “absent or null.”
