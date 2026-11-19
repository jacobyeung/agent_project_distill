This GPU kit is delivered unrun. Run `bash run.sh` in a separately admitted four-H100 production allocation with `TREE`, `CONFIG`, fresh scratch `OUT`, production `PYTHON`, and an optional explicit `RESUME_PIN`. It runs exactly ten optimizer steps per arm: all OFF, prefetch only, decoded cache only, batched metrics only. The baseline emits ten native sampler plans; every ON arm reloads those exact plans and the same checkpoint/base initialization in a fresh process. The launcher preserves the real trainer's admission, model, optimizer, learning rates, gate replay and FSDP wrapper. It does not checkpoint, export, or evaluate these disposable updates.

The shared `kit_profile/disposable.py` adapter permits checkpoint restoration with the bounded smoke loop and redirects native smoke receipts and locks to each arm's `OUT/trainer` directory. It preserves the configuration and admission checks and refuses a changed source pattern. `RESUME_PIN` names a JSON checkpoint pin; its loaded content is retained in each manifest and compared across arms.

`summarize.py OUT` prints slowest-rank wall time, data time, all ten step times and first-measured-step loss parity for every microstep and rank. It also checks plan hashes, trainable names/counts, configuration, checkpoint and binding. The tolerance for these scheduling/cache patches is zero; any nonzero difference fails and is printed as `max_abs_loss_error`. GPU nondeterminism can also fail this check; investigate with an explicitly authorized repeated OFF arm rather than silently relaxing the tolerance. CPU tests check every gradient and optimizer update; this GPU kit checks losses and timing, not full GPU gradient parity.

The report includes the median across all ten steps and steps 2–10. Neither is automatically steady state: run A's fresh-process wall time settles over about 20 steps. Compilation caches, filesystem warmth, allocator initialization and thermal variation can bias an OFF-first comparison. Use the same known kernel-cache state in each arm and record it. A cache hit is part of the decoded-cache feature; unrelated kernel cache warming is not. The first native update and its RNG/optimizer state remain matched. These gains are individual, not additive. The combined arm is supported by `launch.py --arm all` for a separately authorized follow-up.

The real model need not fit a single 48 GB GPU to test the data path. `data_only.py` reads the actual prepared receipt and processor, replays one rank of all ten plans, and optionally transfers one encoded microbatch at a time:

```bash
nice -n 10 "$PYTHON" data_only.py --tree "$TREE" --config "$CONFIG" \
  --receipt "$PREPARED_RECEIPT" --manifest "$BASE_MANIFEST" \
  --plan "$OUT/off/rank0/plan.json" --out "$SMALL_OUT" --arm prefetch
```

Use a fresh output and `--arm off`, `prefetch` or `cache` for each data comparison. Add `--gpu-copy` for actual copies on an explicitly allocated single GPU, and `--pin` for pinning plus nonblocking copies. The copy timer includes pinning and the final wait. The default performs no GPU work. `--consumer-ms 1400` simulates a consumer to test queue overlap; report that delay as simulated, never as a measured training speedup. Without a consumer, prefetch has little work to overlap.

This smaller variant measures real decoding, encoding, cache reuse and copy latency. It also checks Python, NumPy and torch CPU RNG state with the actual production processor and rejects an RNG-consuming path. It cannot show full-model loss/gradient parity, H100 compute speed, FSDP communication, activation-memory fit, or four-rank stragglers. All frames, caches and outputs must be on scratch. Preserve the host's CPU/IO limits and obtain the required approval before a substantial dataset replay.
