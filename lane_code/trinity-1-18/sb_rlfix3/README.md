# RL kit with the deployed A4 reader

Rollouts call the sealed out3/A4 `e2e_reader.real.generate_real` with the adapter-installed model. `serving.py` pins A4's package, settings, arm descriptor, export identity and `INPUTS.json`. The kit checks every staged payload file against `A4/package/0.tgz`. During loading, prompting and decoding, an isolated module scope supplies A4's native helpers; N's admission and training modules remain available outside that scope.

Training loads the policy with A4's `e2e_reader.parity.load_native` inside that scope (`train.load_export`) and builds each prompt with A4's `evalpath.runtime.prompt_batch` from the loader's `info['config']` (`train.prompt_inputs`). The greedy replay calls the same two functions, so it certifies the loader training uses. A4's loader refuses N exports, whose stored config identity differs from A4's (`out/N_EXPORT_CHECK.json`); RL from an N export needs an A4-reader journal of that export, named by the orchestrator.

The claimed arm uses frozen G3T for camera geometry and depth-based lifting, SAM 3 with the learned `candidates_argmax` selector, and the deployed K1 proposal retention rule. **Own gravity and own depth for scale are part of the claimed arm.** Scale uses the deployed positive-depth median ratio. Gravity and depth heads are frozen, but their outputs come from the current model's prefill.

`SamplingProcessor` samples after the unchanged A4 `ThinkingBudget`. The deployed budget forces the think-close after 2,048 callbacks, defers an open call by at most 96 callbacks, and allows 64 answer callbacks after the forced close. A natural think-close retains the deployed direct-answer behavior. The overall cap is 16,384 tokens. Budget-forced IDs have kind `b`; injected responses have kind `r`. Neither receives policy gradients. Distance stops at its sixth call and room at its second, without serving the cap-reaching call; both receive zero reward when capped.

Correctness uses N's official scorer. Reward is correctness + 0.1 × short + 0.1 × route, with both auxiliaries multiplied by correctness. Auxiliary credit requires one valid think-close. Length credit decreases between 128 and 1,024 thought tokens. Routing requires the expected calls and matching responses inside the thought; distance requires two grounds before a gap.

The runner freezes base weights, heads and towers and trains rank-16, alpha-32 LM MLP adapters. Four draws share each prompt; advantages subtract the group mean without standard-deviation scaling. The sequence objective clips at 0.2, uses k3 KL with beta 0.04, and samples at temperature 0.7 with top-p 1. A4's typed refusals and the ValueErrors `generate_real` raises receive zero reward and skip backward; alignment errors still raise. Every rank reduces its gradients and refusal count, and all ranks stop when refusals exceed 25% of a step's draws. Checkpoints retain adapters, optimizer, step, prompt cursor, order and rng every 25 steps and at completion; `python -m rl_on_n.train --config C --resume checkpoint_NNNNNN.json` continues the same config.

The pool uses N's native admission, room exclusions and REMOVE checks. It excludes the entire pinned R0 reserve. Model inputs use explicit allow-lists; labels stay outside the model-visible row. Every admitted row must satisfy equality of raw and cleaned `prompt_batch(...)["input_ids"]`; a dropped prompt-relevant field causes a refusal.

Run the CPU checks from this workspace:

```bash
bash scripts/run_tests.sh
bash scripts/run_cpu.sh
```

The CPU proof uses random real-width Qwen3.5 layers, synthetic visual inputs and synthetic G3T/gravity/scale values through A4's real decoder. Its two-token suffix cap is a declared test fixture. Wrong answers earn zero reward; separate synthetic advantages exercise backward and an adapter update. It does not establish production quality, SAM 3 parity or GPU memory fit. The step-loop tests run `train.run` on four sequential CPU rank fixtures, covering a refusing rank, the refusal limit and resume; CUDA and collective communication are mocked because sockets are unavailable.

Before training, run the GPU replay on one idle assigned H100 from a `/scratch` environment:

```bash
RL_PYTHON=/scratch/path/to/gpu/python bash scripts/run_greedy_replay.sh <card> \
  --export-dir /scratch/path/to/authenticated/m200/restore \
  --config /scratch/path/to/m200/prepared/config.json \
  --artifact-binding /scratch/path/to/admitted/binding.json \
  --artifact-binding-sha256 ACTUAL_SHA256
```

The launcher takes a numeric physical card index, refuses a card with more than 1,024 MiB used, and runs under `timeout 2h` at nice 10, through vnice on Trinity. The script requires NVIDIA H100 80GB HBM3, A4's recorded card, and `/scratch` paths for the interpreter, inputs and artifact roots. It authenticates the export against A4's `EXPORT_PIN.json`, installs zero-initialized adapters and compares tokens, finish, call families and budget firing on 26 A4 journal items: four per type, four whose calls include a gap and two whose budget fired. Each item is appended to `out/GREEDY_REPLAY.items.jsonl`, so a rerun skips matched items. Training requires the pinned PASS receipt for all 26 items, the same N tree and code, and the export identity it loads. The script has not run on GPU.

The artifact binding must be an existing, verified artifact manifest admitting the current immutable export, tokenizer, G3T, SAM 3, selector, sealed A4 code and RL overlay. Bind its `reader`, `tree`, `heads` and `runner` code roots to the corresponding paths under `in/claimed_reader`. Do not bind the staged `/scratch/jjyeung/b01ec87a6f29b/p` reader. After `Artifact.verify()`, `serving.build_reader` requires the G3T, SAM 3 and selector files to carry the sha256 A4's `INPUTS.json` records, then calls A4's `_head`, `Sam3Tower` and `real_perception`. CPU tests bind those calls' signatures; real perception loading has not run.

`configs/h100_{4,8}.json` leave every production binding unset and list each under `missing_bindings` with its expected path and hash source: the m200 restore and config, the admitted pool and its config, the artifact manifest, the GPU replay receipt and an A4-reader journal for any N export. A4's settings name `/scratch/jjyeung/b01ec87a6f29b/d/e`, but its local `RESTORE.json` identifies m544 rather than the required m200. No export, scene mapping or artifact manifest is inferred.

`scripts/run_gpu_dry_run.sh` supplies a two-step, one-GPU timing run after bindings and replay pass. GPU replay, timing and real NCCL remain unrun. `out/REPORT.md` states measured CPU results; output JSON receipts record input SHA256 hashes. `scripts/package.py` packages the kit and sealed reader payload into `out/sb_rlfix3.tar`.
