# RL stage kit for N

This overlay adds GRPO to N's native routed decoder. The CPU tests and synthetic proof are runnable. Production remains blocked on an admitted pool, qualified export, frozen assets, and the claimed-arm serving bindings. See `out/REPORT.md` for measured evidence and missing inputs.

```bash
bash scripts/run_tests.sh
bash scripts/run_cpu.sh
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONPATH=overlay nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/make_configs.py
```

Correctness calls N's `evalpath.run.score_item`, including its question-type inference and final-answer extraction. Reward is correctness plus 0.1 × short plus 0.1 × route. Zero correctness gives zero auxiliary reward. Auxiliary credit requires exactly one `</think>`; malformed or duplicate close tags get no auxiliary credit. Length credit decreases linearly between 128 and 1,024 thought tokens, excluding injected responses.

Routing requires exactly the question type's call kinds and matching decoder responses inside the thought. Distance requires ground and gap, with two grounds before the gap. Direct types require no calls. This checks call placement, not whether the answer causally uses a response.

Advantages are reward minus group mean, with standard-deviation scaling disabled. Four draws share each prompt. The objective accepts only `grpo.norm=seq`, clips at 0.2, and uses k3 KL with beta 0.04. Sampling uses temperature 0.7 and top-p 1. Only sampled tokens receive gradients; responses, forced fixture tokens, and budget EOS do not. Each scheduled sequence has equal weight, including refused slots in the denominator.

The default training arm explicitly uses `pose_source='tower'`: frozen G3T for camera and lifting, SAM 3 with the deployed selector for grounding, and fixed math for scale and gap. Own heads may be printed only through `rollout.diagnostic_own`; `reward.score` rejects that diagnostic arm. The native tower path remains active.

The supplied generic `evalpath/run.py` uses own pose and MDG. Its defaults do not verify the claimed arm. `grounding.serving_table` and `grounding.evaluator_adapter` are therefore MISSING pins, and `serving.load_binding` refuses production until they are supplied. The adapter must come from the deployed evaluator, validate the actual table, and expose `validate_claimed_arm(table_pin, **requirements)` and `build_backend(model=..., row=..., batch=..., artifact_pin=..., audit_dir=..., settings=...)`. The batch includes the prepared TowerState. A backend whose mask source differs from `svp_sam3` is refused. No deployed adapter or serving table is fabricated in this kit; this interface remains unverified against the missing source.

The runner freezes base weights, heads, and towers and trains rank-16, alpha-32 adapters on the LM MLP projections. Disabling adapters supplies the immutable reference. Each rank initializes gradients to zero and participates in every parameter's all-reduce, even when local draws fail. There is no DDP `no_sync` path.

`RowRefusal` and tower failures receive reward zero and skip backward. Progress files record each rank's refusal count, reasons, timing, and peak CUDA allocation. If every rank has no usable draw, the optimizer does not step. Rank zero saves adapters and optimizer state every 25 steps and at the final step. `RL_EXPORT.json` pins the final checkpoint; `rl_on_n.restore.load` restores its adapters.

`pool.RoomGate` checks native room authorities, withheld rooms, reserve rooms, scene exclusions, and REMOVE lists before rows enter the pool. The kit deliberately excludes the entire pinned R0 reserve, including R0-rl. This conservative restriction stays in force; it is broader than heldout-only exclusion. The row and nested model inputs use explicit allow-lists. Ground truth remains only in the scoring envelope, outside the row passed to the model.

Production configurations preserve eight prompts × four draws across four or eight ranks. Bind source_config, pool_config, artifact, pool, frozen_tower weights/config, and the deployed serving inputs. N's component gate and native admission checks remain active. No pool or export qualification is invented.

The CPU proof uses random weights, four real-width text layers, three vision layers, synthetic RGB, and synthetic frozen TowerState inputs. Its wrong outputs earn zero reward and zero production advantages. A separately labeled synthetic reward pair tests nonzero backward propagation on the sampled tokens. This is not evidence of learned routing, answer quality, production grounding, or GPU memory fit.

`scripts/run_gpu_dry_run.sh --config BOUND_CONFIG --out OUTPUT` runs two timed steps on exactly one assigned GPU, preserving the 32-sequence batch. It records per-step time, refusals, peak memory, and total time. It requires a suitable GPU environment through `RL_PYTHON`. This script is supplied but not executed in the CPU-only task.

`out/GPU_ESTIMATE.json` contains arithmetic scenarios, not measured throughput. It assumes 4,800 prompt tokens; decode is serial within each rank, and policy replay rates include backward only as an unmeasured effective-rate assumption. Obtain the timed dry run before reserving GPUs. Multi-GPU collective behavior, deployed grounding, and export reload remain untested.
