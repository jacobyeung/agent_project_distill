The direct kit can stage a LEG-S1 export only if its language-model weights retain the native Qwen3.5 base inventory. The routed evaluator additionally needs the trained heads and the authenticated training configuration. A direct read does not test the heads.

Required files beside `artifact.json`:

```text
mN/
  artifact.json
  heads.pt                         # required for routed reads
  full_weights/
    full_weights.json
    model.safetensors.index.json
    <every shard named in the manifest>
```

`artifact.json` must have schema `carrier-c1-artifact-v1`, the requested optimizer `step`, and an absolute, SHA256-pinned `full_weights` reference to this milestone's `full_weights/full_weights.json`. The input hash is the hash of the artifact JSON, not the tar archive or a tensor shard. The archive has a separate hash.

The full-weight manifest must have schema `full-ft-export-v1`, dtype `bfloat16`, tensor count, a pinned `model.safetensors.index.json`, and a nonempty, unique shard list. Every shard entry supplies `name`, `bytes`, `sha256`, and `tensors`. Shard bytes, digests, header counts, names and index assignments must agree. Absolute shard names, traversal and escaped symlinks refuse.

The reviewed stager compares every tensor name and shape with the authenticated native base snapshot. Export tensors must be BF16; matching native tensors may be BF16 or FP32. Only missing native `mtp.*` tensors are allowed. Extra tensors, other missing tensors, shape changes or unsupported dtypes refuse. An adapter-only or heads-only checkpoint cannot stage.

The base is a separate prerequisite. Its snapshot manifest SHA256 is `ae9247f7c316e7661bfbe4301c28d75b6871db7427d675b8e1cc4c0c41b4b252`. `models.json` must give its real local snapshot path and the pinned manifest path. The reviewed `stage.snapshot` verifies the base; `c1_export.py` copies its tokenizer/configuration metadata to the staged language model. Export-side tokenizer files and `heads.pt` do not enter that direct stage. The runtime must provide the reviewed vLLM version, 0.32.0.

The parent was staged as `c1_export` from artifact SHA256 `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`, at `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f2ad01ad/runs/49becb79/m200/artifact.json`. The operator's namespace exposed this published path through local mounts. Preserve absolute nested paths when receiving another export. Rewriting artifact paths changes its hash and is not an authenticated transfer. Use the producer's published layout or an operator-managed mount that exposes the same paths.

Run the read-only check before binding:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s out/export_check.py \
  --export "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --step "$STEP" \
  --base "$BASE" --output "$RUN/export_check.json"
```

The default hashes all export shards and compares native headers. `--header-only` produces `HEADER_ONLY_NOT_VERIFIED`; it cannot make a cell launchable. A live bind and launch repeat the complete check. The kit independently verifies its staging. Do not put full weights in this CPU lane: its budget is 2 GB.

Routed admission also requires:

- The exact training config, preparation receipt, source seal, base snapshot manifest and all assets those files pin. The frozen loader calls `trainer.prepared(..., admission=True)`; it is not a standalone weights-only loader.
- A pinned `heads.pt`, compatible `base_identity`, `config_sha256`, final-mode carrier/depth settings and trace version 3.14.
- `trained_groups` with pose, depth, camera connector and grounding, plus fusion when enabled. Its tensor inventory, fingerprints, nonzero state, changed-from-initial state and gradient-step evidence must pass the native loader. Frozen MDG threshold `tau` must be in [0,1].
- The external frozen geometry encoder assets named by `geometry_online`, and native MDG assets/configuration. The loader must restore every trained group; partial grafts are not evaluation exports.

`export_check.py --scope routed --receipt RECEIPT` checks the artifact's init contract and heads digest. It does not substitute for `runtime.load_model`: actual tensor restoration, source/config identity and accelerator compatibility are first-item checks.

Evidence: copied reviewed `evaluator/c1_export.py` and `stage.py` in each direct bind; frozen `evalpath/runtime.py`, `student_pilot/carrier_c1_run.py`, `source_seal.py`, and `trained_groups.py` in `work/tree_final`. The real parent export bytes are unavailable in this lane. Parent dry binds authenticate metadata and payloads only; tiny synthetic exports test byte-level refusals.
