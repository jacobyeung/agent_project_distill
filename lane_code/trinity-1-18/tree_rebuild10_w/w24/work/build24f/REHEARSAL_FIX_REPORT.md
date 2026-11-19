Fixture-only cause: the tiny model ties the input embedding to `lm_head`; native FULL_SHARD wraps them separately.
Evidence: `work/build21/native_assets21.py:68,75` sets both tie flags true; `work/tree_r1/student_pilot/full_ft.py:332–343` wraps embedding/head with `use_orig_params=True`.
PyTorch `_get_orig_params` excludes parameters already owned by nested FSDP; `_use_sharded_views` restores flat original-parameter shards after embedding lookup.
The later pose touch (`carrier_c1.py:562`) therefore sees a 248064-element shard: 248064 vocabulary × 4 width / 4 ranks, exactly the error in `rehearsal/train_fresh.log`.
Production verdict: this cause is not a launch blocker for the pinned 9B base and four-GPU NCCL FSDP; its head and embedding are independent parameters, and native warm-start uses `parameter.copy_` without tying them.
The staged `/scratch/jjyeung/devs1c_models/cp1/base/config.json` hashes to the kit-pinned `d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05`; top-level tie=false and the text default=false.
`rehearsal2/PRODUCTION_EVIDENCE.json` records the receipt→preparation→model-manifest pins; `SINGLE_PROCESS.json` confirms separate production parameters using only meta tensors.
The fixture clones `lm_head.weight` after native authenticated warm-start loading, sets both effective tie flags false, and recomputes native parameter accounting before optimizer/FSDP creation.
This placement preserves the tied donor's exact inventory checks; all initial tensor values remain unchanged. Native code, production configs, kits and packages are unchanged.
`rehearsal2/model_override.json` describes the constructor boundary; `FIXTURE_DIFF.json.build24fr` lists every changed input field and effective model field.
Single-process validation passes alias separation, exact forward equality, finite backward, and production metadata construction (`rehearsal2/SINGLE_PROCESS.json`).
Regenerated inputs pass the native canary (ADMIT), room audit, v.json handoff and fixture gate refusal tests; `rehearsal2/FIX_VALIDATION.json` records these checks and 79 changed input fields.
The current handoff receives the existing synthetic host/review evidence before native h.py runs; only its control-review pin is substituted in memory (`rehearsal_handoff.py`), never in the kit or production approval.
The minimal reproduction uses the actual tiny Qwen modules and `carrier_c1_run.wrap_model`: tied must reproduce the flat-weight error on every rank; untied must pass forward/backward.
The lane runs the reproduction followed by the prepared native fresh/budget/resume paths; results go to `rehearsal2/repro_*.json` and `rehearsal2/CHECK.json`.
Distributed reproduction and four-rank training have NOT been run by this agent; their success remains pending the external run.
Exact command: `cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24 && nice -n 10 bash work/build24f/go_rehearsal.sh`
