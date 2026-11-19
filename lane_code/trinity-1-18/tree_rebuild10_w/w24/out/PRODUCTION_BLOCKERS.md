Build 24h does not authorize N's production launch.

The sealed mode-q path does not produce a `frame_host()` receipt. Kit `b/a.py` calls `launch_r1.production_proof.run()` for mode q. That function calls native preparation, population binding, loader audit and handover binding, but never calls `launch_r1.entry.frame_host()`. The direct `frame_host()` call in `a.py` belongs to mode p. Decoded `k/h.json` also has null `staging`, `routing_selection` and `routing_base` pins. The kit now captures an actual `frame_host()` return at `Q_NS/p/host.json` when that function runs. It never promotes the canary audit into a synthetic production host PASS. Consequently the current production q path still reaches `R1_HOST_RECEIPT_MISSING` in `h.py` after a successful canary.

The final production identity cannot be computed from the input capsule alone. `identity()` excludes the two receipt pins and four top-level authorization/preparation fields; it retains ordinary paths and the following values that preparation creates:

- `r1_direction_twins.augment()` changes `streams.vqa` and adds `r1_training.direction_augmented`.
- `production_proof._run()` adds the room-audit pin and `routing_vocabulary`.
- `r1_population.bind_prepared()` produces `r2_sampling` and its `r1_training.row_plan_sha256`.
- `production_proof.bind_handover()` binds `store_hashes`, `continuation_identity` and `handover_mapping` to the prepared stores and row plan.

The hidden-view look-ahead reaches the production-store boundary before any final `RESULT.json.config` exists. `N_PRODUCTION_CONFIG.json` therefore holds the decoded, localised input only. `N_IDENTITY.txt` is its authentic sealed-tree identity, computed with `/scratch/jjyeung`, `/home` and `/data*` hidden. `IDENTITY_COMPARISON.json` enumerates every localisation difference from the hidden canary's input config. These differences and the generated fields are not safe to ignore for review: `h.py` refuses any mismatch with the final config.

Completing production admission requires a host-proof producer that certifies the exact final configuration, and the independent review of that final identity. The builder cannot manufacture either receipt or change the sealed admission contract under the kit-only rule. The fixture tests exercise receipt attachment and native `admit()` without supplying production evidence.

The copier signal budget uses at most 420 seconds for the trainer, 10 seconds for copier shutdown, and 155 seconds for final publication. It leaves 15 seconds before the 600-second Slurm warning expires and assumes no KillWait grace; the cluster's KillWait setting was not queried. A trainer timeout yields status 124 and copies only small evidence, avoiding an archive of an active writer. The final-copy timeout can leave large production exports or checkpoints incomplete; only small fake exports were timed in this build.
