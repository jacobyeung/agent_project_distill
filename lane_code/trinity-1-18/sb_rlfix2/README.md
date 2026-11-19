# RL kit with the deployed A4 reader

Rollouts call the sealed out3/A4 `e2e_reader.real.generate_real` with the adapter-installed model. `serving.py` pins A4's package, settings, arm descriptor and export identity. The kit checks every staged payload file against `A4/package/0.tgz`. During decoding, an isolated module scope supplies A4's native helpers; N's admission and training modules remain available outside that scope.

The claimed arm uses frozen G3T for camera geometry and depth-based lifting, SAM 3 with the learned `candidates_argmax` selector, and the deployed K1 proposal retention rule. **Own gravity and own depth for scale are part of the claimed arm.** Scale uses the deployed positive-depth median ratio. Gravity and depth heads are frozen, but their outputs come from the current model's prefill.

`SamplingProcessor` samples after the unchanged A4 `ThinkingBudget`. The deployed budget forces the think-close after 2,048 callbacks, defers an open call by at most 96 callbacks, and allows 64 answer callbacks after the forced close. A natural think-close retains the deployed direct-answer behavior. The overall cap is 16,384 tokens. Budget-forced IDs have kind `b`; injected responses have kind `r`. Neither receives policy gradients. Distance stops at its sixth call and room at its second, without serving the cap-reaching call; both receive zero reward when capped.

Correctness uses N's official scorer. Reward is correctness + 0.1 × short + 0.1 × route, with both auxiliaries multiplied by correctness. Auxiliary credit requires one valid think-close. Length credit decreases between 128 and 1,024 thought tokens. Routing requires the expected calls and matching responses inside the thought; distance requires two grounds before a gap.

The runner freezes base weights, heads and towers and trains rank-16, alpha-32 LM MLP adapters. Four draws share each prompt; advantages subtract the group mean without standard-deviation scaling. The sequence objective clips at 0.2, uses k3 KL with beta 0.04, and samples at temperature 0.7 with top-p 1. Refusals receive zero reward and skip backward. Every rank reduces its gradients, including zero gradients from a refusing rank. Checkpoints retain adapters and optimizer state every 25 steps and at completion.

The pool uses N's native admission, room exclusions and REMOVE checks. It excludes the entire pinned R0 reserve. Model inputs use explicit allow-lists; labels stay outside the model-visible row. Every admitted row must satisfy equality of raw and cleaned `prompt_batch(...)["input_ids"]`; a dropped prompt-relevant field causes a refusal.

Run the CPU checks from this workspace:

```bash
bash scripts/run_tests.sh
bash scripts/run_cpu.sh
```

The CPU proof uses random real-width Qwen3.5 layers, synthetic visual inputs and synthetic G3T/gravity/scale values through A4's real decoder. Its two-token suffix cap is a declared test fixture. Wrong answers earn zero reward; separate synthetic advantages exercise backward and an adapter update. It does not establish production quality, SAM 3 parity or GPU memory fit. The step-loop test runs `train.run` on four sequential CPU rank fixtures with one refusing rank; CUDA and collective communication are mocked because sockets are unavailable.

Before training, run the supplied GPU replay script on an assigned GPU:

```bash
RL_PYTHON=/path/to/gpu/python bash scripts/run_greedy_replay.sh \
  --export-dir /path/to/authenticated/m200/restore \
  --config /path/to/m200/prepared/config.json \
  --artifact-binding /path/to/admitted/binding.json \
  --artifact-binding-sha256 ACTUAL_SHA256
```

The script authenticates the export against A4's `EXPORT_PIN.json`, installs zero-initialized adapters, and exercises the training rollout and frame bridge greedily. It compares every token and finish reason with four A4 journal items per type. Training requires a pinned PASS receipt for all 20 items and checks its source hashes and N tree. The script is supplied but has not run on GPU.

The artifact binding must be an existing, verified artifact manifest admitting the current immutable export, tokenizer, G3T, SAM 3, selector, sealed A4 code and RL overlay. Bind its `reader`, `tree`, `heads` and `runner` code roots to the corresponding paths under `in/claimed_reader`. Do not bind the staged `/scratch/jjyeung/b01ec87a6f29b/p` reader. `serving.build_reader` uses the actual A4 APIs; no custom evaluator interface is required.

MISSING production inputs remain explicit in `configs/h100_{4,8}.json`: source and pool configs, qualified training export, admitted pool, artifact manifest and GPU replay receipt. A4's settings name `/scratch/jjyeung/b01ec87a6f29b/d/e`, but its local `RESTORE.json` identifies m544 rather than the required m200. Supply the authenticated m200 restore to the replay script. No export, scene mapping or artifact manifest is inferred.

`scripts/run_gpu_dry_run.sh` supplies a two-step, one-GPU timing run after bindings and replay pass. GPU replay, timing and real NCCL remain unrun. `out/REPORT.md` states measured CPU results; output JSON receipts record input SHA256 hashes. `scripts/package.py` packages the kit and sealed reader payload into `out/sb_rlfix2.tar`.
