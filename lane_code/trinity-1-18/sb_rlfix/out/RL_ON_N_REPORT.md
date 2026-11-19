# RL on N: delivery and CPU proof

The overlay and CPU proof are complete. **Production remains MISSING, and no GPU job was launched.** N's native component check refuses `Missing component evidence: init_m544`; the supplied package does not provide a qualified production pool/export binding.

## Delivered kit

- `overlay/rl_on_n/` contains reward, native rollout, prompt-pool builder, GRPO loss, adapters, trainer, and adapter restore code. N stays read-only; there are no package patches.
- `configs/h100_4.json` and `configs/h100_8.json` are unbound templates. Both use eight prompts × four draws = 32 sequences per step, with eight/four sequence microbatches per rank and one sequence resident at a time.
- The sampler imports N's routed decoder. Native code detects calls, executes heads, inserts responses, and binds v3.14 grounding sessions. Frozen G3T reads pinned native RGB; the checkpoint supplies metric depth and grounding. Each draw gets a fresh grounding session.
- The pool builder uses N's prepared reader and authenticated membership, then applies `Rooms`, `Reserve`, `Withheld`, dev-S1/benchmark exclusions, and removal lists. Unknown room identity refuses. Pool ordering depends only on seed and prompt ID; duplicate IDs refuse.
- `start_mode=n_export` requires an export matching its own native preparation/config. `start_mode=p_handover` uses N's authenticated P continuation and native initializer. Neither path fabricates a manifest or skips component evidence.
- Training updates rank-16, alpha-32 adapters on LM MLP gate/up/down projections. The base model, vision, heads, and towers are frozen. Disabling adapters gives the immutable reference without another 9B copy.
- The separate RL artifact binds its adapter weights to the starting C1 export and initialization seed. It is not a native N/P SFT export. Production reload and distributed execution remain untested because qualified inputs are missing.

## Reward and loss

`R = 1.0 × correctness + 0.1 × short + 0.1 × routed-placement`.
N's official scorer supplies numeric MRA, including its zero-target rule, or exact choice credit. Length credit decreases linearly from one at 128 own thought tokens to zero at 1,024; responses are excluded. Incomplete/budget-cut thoughts get no length credit. The two small auxiliary weights keep an exact answer above a zero-correctness answer; they can reorder partial-MRA answers.

Routing credit requires successful calls inside the thought, in decoder order, with matching injected responses. Camera displacement/direction needs move; rotation needs turn; object distance needs two grounds followed by gap. Direct types, including room size, must make no call. The route table comes from the pinned N config.

GRPO uses group-centered, standard-deviation-normalized advantages, clip 0.2, k3 KL beta 0.04, and sequence means. Temperature is 0.7 and top-p is 1.0. Only sampled tokens receive policy gradients; prompt, response, forced-test-prefix and budget-EOS tokens are excluded. Defaults and rationale are in `README.md`; configs were produced by `PYTHONPATH=overlay /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/make_configs.py`.

## CPU proof

Command: `bash scripts/run_cpu.sh > out/cpu_proof_validated.log 2>&1`. Measurements below come from `out/CPU_PROOF.json`.

| Check | Observed result |
|---|---|
| Architecture | Supplied Qwen3.5-9B config, random initialization; four text layers, three vision layers |
| Preserved dimensions | Hidden size 4,096; vocabulary 248,320; original head, MLP, vision-width and rotary dimensions |
| Hybrid layers | Three linear-attention layers and one full-attention layer |
| Depth feature taps | Native depth head reads retained vision layers 1, 2, 3 instead of 9, 17, 25 |
| Parameters | 3,315,508,280 total; 3,145,728 trainable adapter parameters |
| Batch | One synthetic 32-frame prompt, two rollouts; real tokenizer; two free sampled tokens per rollout |
| Native execution | One successful camera move call; 37 injected response tokens; zero calls in the other rollout |
| Reward | 0.1 and 0.0; correctness and length terms both zero because these random suffixes are budget-cut |
| Backward | Finite nonzero gradients; gradient absolute sum 8,372.219833 |
| Optimizer update | Nonzero adapter change; measured absolute sum 1.966038 |
| Reference KL | Zero at adapter initialization |
| Cached/replayed probabilities | Maximum absolute deviation of the mean probability ratio from one: 0.0227635 |
| Runtime and memory | 107.065 seconds; peak RSS 14.627 GiB; eight CPU threads; CUDA hidden |

The sole substituted head input is frozen G3T's output, supplied through native `TowerState` using synthetic poses, depth and nonconstant confidence. Native pose/gravity and private depth heads execute. RGB patches are synthetic. Forced test prefixes exercise call-present/call-absent cases; suffix tokens are sampled from the real model and carry gradients. This proves integration, not learned routing or answer quality.

SAM3/MDG object grounding, an actual export reload, the full 32-text/27-vision-layer model, realistic image resolution, and distributed GPU behavior are unexercised. The observed BF16 cached-versus-full-prefix probability difference is disclosed; GPU numerical parity is not established. No socket or GPU stand-in was used.

## Tests and admission

Command: `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONPATH=overlay /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/check.py`.
`out/TEST_RESULTS.json` records **20 passed, zero failures, zero errors**. Tests cover correct/incorrect numeric and choice answers, zero-target MRA, long/short and unclosed thoughts, required/missing/spurious/late/failed calls, ground-gap order, masks, clipping/KL/backward, frozen reference behavior, held-out/K1/R0 refusal, unknown rooms, deterministic pool ordering, and duplicate refusal.

`out/PROMPT_POOL.json` is explicitly **MISSING** with no prompts. Its recorded command invokes N's `r1_training.training_components` on the sealed local registry and config; it reproduces the missing `init_m544` refusal. This is a component check, not a full preparation run.
The registry is `/scratch/jjyeung/orch_n30/sb_f64/pkg/work/n1fix2/inputs/registry.json`. Qualified evidence for its `init_m544` slot is MISSING; other empty slots must also be resolved. Source: `pkg/out/BUILD18_REPORT.md:1`.
N's declared source files below are MISSING from this task's delivered admitted population; their source metadata explicitly requires full scene admission:

- `/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl`
- `/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl`
- `/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl`
- `/scratch/jjyeung/orch_n30/rows_r1/out/room_v2/rows.jsonl`

Their exact pins and preparation binding are preserved in `out/INPUT_AUDIT.json`; these external paths were not opened. `in/b09_out/RUN.md`, `in/b09_out/STATUS.md`, and `in/b09_out/HASHES.txt` are also MISSING; `in/b09_code/RUN.md` is present. No production pool, scene mapping, or export qualification was invented.

## Estimate for 200 steps

Command: `PYTHONPATH=overlay /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/make_configs.py`. `out/GPU_ESTIMATE.json` records every assumption and formula. b09 supplies a proposed dry-run card, not measured H100 step times (`in/b09_out/CARD_DRAFT_RL_DRYRUN.md:2`; `in/b09_out/RL_KIT_READY.md:1`).

The estimate assumes 6,400 rollouts, each with 4,096 prompt, 512 sampled, and 128 injected tokens. Those are planning lengths, not measurements of an admitted pool. The formula counts cached decoding, prefill, reference replay, policy/backward replay, head execution and overhead.

| Hardware | Planning GPU-hours | Planning wall hours | Assumption range, GPU-hours |
|---|---:|---:|---:|
| 4 H100 | 102.10 | 25.53 | 58.65–218.46 |
| 8 H100 | 110.98 | 13.87 | 63.75–237.45 |

The planning rates are 25 decoded tokens/s/GPU, 1,200 prefill tokens/s/GPU, 450 effective replay tokens/s/GPU, and five head seconds per rollout. Four/eight-rank overhead factors are 1.15/1.25. These ranges are scenarios, not confidence intervals. Long visual prefixes or slow heads can exceed them.
The per-rank memory envelope is about 64 GiB, including base weights, adapters, heads/towers, cache/activations and workspace. It is an unmeasured budget; native loading temporarily uses FP32 masters. A qualified GPU check must establish memory fit and timing.

## Archive and provenance

`out/sb_rlkit.tar` contains 21 code/config/test/documentation files and is 102,400 bytes; it contains no data or weights. Command: `PYTHONPATH=overlay /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/package.py`.
SHA256: `eafa9841a2d235e4427bd0069fc541398cb4a30cb95abcdc499fcf002d69fcde`.
The supplied N tar hashes to `caa09d0c6aa79f55ee7ddf0dbe4580145a1e483a164226678539f554e8af6a36`; `out/INPUT_AUDIT.json` records the file and hash. `out/SHA256SUMS`, `out/PACKAGE.json`, and `out/PORT_ORIGINS.json` record delivery and copied-source provenance. Every output JSON includes input SHA256 values.
The survey retains the requested b09/N comparison because those differences determine the port; it does not narrate discarded implementation attempts.
