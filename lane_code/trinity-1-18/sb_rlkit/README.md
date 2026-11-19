# RL stage kit for N

This overlay adds GRPO to N's native routed decoder. It imports the sealed N tree without changing it. The production pool and export bindings are MISSING: the supplied N report stops at missing `init_m544` evidence. The kit does not authorize or launch a GPU job.

Run the CPU checks from this workspace:

```bash
bash scripts/run_tests.sh
bash scripts/run_cpu.sh
PYTHONPATH="$PWD/overlay" /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/make_configs.py
```

`out/RL_ON_N_SURVEY.md` describes the interfaces. `out/RL_ON_N_REPORT.md` states measured results and remaining limits. The tar contains code, configs, tests, and documentation, with no data or weights.

## Reward and optimization

The reward is `1.0 * correctness + 0.1 * short + 0.1 * routing`. Correctness imports N's official MRA or exact-choice scorer. A complete thought gets length credit that falls linearly from one at 128 own thought tokens to zero at 1,024. Printed responses are free. Incomplete/budget-cut thoughts get no length credit. These bounds keep an exact answer above a zero-correctness answer; partial MRA scores can trade against auxiliary terms.

Routing earns one only for the question type's required native call sequence inside the thought, with matching decoder-injected responses. Direct types earn it for making no call. Object absolute distance needs two grounds and a gap; camera displacement/direction needs move; rotation needs turn. The route table comes from the authenticated N config. Room size stays direct.

Four draws share a prompt; advantages use the group's population standard deviation. Ties produce zero policy signal. GRPO clips at 0.2 and uses k3 KL with beta 0.04. Temperature is 0.7 and top-p is 1.0, so rollout and loss use the same distribution. Only sampled tokens receive gradients; injected responses, test-forced prefixes, and budget EOS do not. Each sequence has equal weight.

The production memory plan trains rank-16, alpha-32 adapters on each LM MLP's gate/up/down projections. Base weights, heads, and towers stay frozen. Disabling adapters supplies the immutable starting reference on the same response-conditioned trajectory; no second 9B model is resident. `LowRank` uses FP32 adapter parameters and BF16 base compute. The CPU proof trains this same adapter family.

## Production bindings

`configs/h100_4.json` and `configs/h100_8.json` keep the same batch: eight prompts × four draws = 32 sequences. Each rank rolls out one sequence at a time and accumulates eight/four sequence losses, respectively. The runner is `python -m rl_on_n.train --config CONFIG` inside an externally assigned distributed environment. No launch script is included.

Before that runner can proceed, the operator must supply exact path/SHA256 pins for the native configuration, admitted-pool configuration, starting C1 artifact, prompt pool, and frozen G3T weights/config. Native frame paths must already resolve locally. The runner verifies these inputs and revalidates the pool against N's native admitted population.

- `start_mode=n_export` reloads an export matching its own authenticated preparation and config.
- `start_mode=p_handover` uses N's admitted continuation config and its exact P export pin. N's persisted handover and native initialization checks must pass; no P metadata is fabricated.
- `pool_config` always names N's prepared training population. `python -m rl_on_n.pool --tree N_TREE --config PREPARED_N_CONFIG --out POOL.json` builds the pool. It refuses unknown rooms, R0, K1, the separate 80-room withheld set, dev-S1, benchmark scenes, removal-list hits, and unadmitted rows. No source slice can be relabeled as admitted.
- The native decoder handles camera carriers, call parsing, in-call head execution, forced responses, and v3.14 sessions. Native RGB frames feed frozen G3T; the checkpoint supplies depth and grounding. A fresh grounding backend belongs to each draw; a prompt's immutable tower result is shared across its draws.

The native training component gate remains active. Its program-choice evidence belongs to the separate native-evaluation phase; this kit does not bypass or enable a benchmark reader.

The runner saves `RL_EXPORT.json` plus `rl_adapters.pt`, bound to the starting export. `rl_on_n.restore.load` restores them. This is an RL adapter artifact, not a native N/P SFT export. Export loading, distributed collectives, real grounding, and GPU memory fit require validation on qualified inputs; CPU proof does not establish those properties.

## Memory and time estimates

The per-rank planning envelope is approximately 16.8 GiB of BF16 base weights, 1 GiB for adapters/optimizer, 14 GiB for heads/towers, 24 GiB for activations/cache, and 8 GiB for workspaces. These are budgets, not measured allocations. Native model loading temporarily uses FP32 masters, and visual-prefix length can exceed the activation budget. No memory-fit claim is made.

`out/GPU_ESTIMATE.json` exposes every token/rate assumption and the formula. It uses 200 steps, 6,400 rollouts, 4,096 prompt tokens, 512 sampled tokens, and 128 response tokens per rollout. No measured b09 H100 step time exists in the supplied deliverables. Production timing must replace these estimates before reserving compute.
