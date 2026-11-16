# Operator instructions

This package performs one own-arm read of 636 dev-S1 items: 636 baselines and 900 registered perturbations. It uses one general allocation, one process per GPU, and a barrier between displacement, rotation, movement direction, absolute distance, and room. The model writes every answer and numeric conversion. Room receives baseline only.

Nothing has been submitted, uploaded, or accessed on Orchard. Do not submit until ORCH releases GPUs and every OPEN input is resolved. A killed allocation requires the user's answer before any resubmission. No automatic retry, requeue, terminator restart, or GPU keeper exists.

## Stage

The package token is `b01ec87a6f29b`. Its Orchard directory must be `/project/community/jjyeung/b01ec87a6f29b`. Its stable in-job root is `/scratch/jjyeung/b01ec87a6f29b`. Slurm receives the batch on stdin, with `/tmp` as workdir and `/dev/null` for logs. The submission helper explicitly exports only `A_N`, `A_T`, `A_I`, and `A_C`; it does not export the operator's environment. Internal source and item contents are exempt from naming restrictions. No internal reader command is submitted as an `srun` task.

1. Give `STAGING.md`, `OPEN_INPUTS.md`, `INPUT_CATALOG.json`, and `package/PACKAGE.json` to the operator. Keep `TOKENS.json` on Trinity. Resolve existing Orchard archives by their full hashes before transferring anything. The template's generic runtime archives do not prove that H1-0's frames, environment versions, SAM files, G3T, or export are present.
2. Package the six small operator files and the code tar as one archive on a host with approved space. Do not copy a tree or folder through Trinity. After storage approval, the local packaging command is:

   ```bash
   K=/scratch/jjyeung/orch_n30/h1_headsft/kit
   tar -cf "$K/tmp/b8/b01ec87a6f29b.tar" -C "$K/orchard_h10/package" \
     0.tgz 0.json 3.py BATCH.sh CONFIG.json SUBMIT.cmd PACKAGE.json INPUTS.example.json
   ```

   This optional transport archive was not created by the builder because the node is below its disk floor. Transfer it once through the operator's existing governed Orchard bridge, at no more than 8 MB/s through Trinity. The bridge and its staging authority are not available in this builder session; no direct SSH command is prescribed as a substitute.
3. On Orchard, after the governed bridge deposits `/tmp/b01ec87a6f29b.tar`, run:

   ```bash
   mkdir -p /project/community/jjyeung/b01ec87a6f29b
   tar -xf /tmp/b01ec87a6f29b.tar -C /project/community/jjyeung/b01ec87a6f29b
   cd /project/community/jjyeung/b01ec87a6f29b
   ```

4. Fill `1.json` using the schema below. All added archives live at opaque paths under `/project/community/jjyeung/`. Use the template's governed transport, not independent downloads. Never extract a tree into Trinity `/home` or `/data*`. Archive bytes, expanded sizes, full SHA256s and provenance must be known before admission. For more than about 30 GB through Trinity, arrange the transfer with an admin. The 21,583,032,320-byte export already has generation-pinned GCS objects in `TRANSPORT.json`; use that cloud source if authorized, rather than sending weights through Trinity.

The job always stages the three pinned template runtime groups and bwrap. Added archives extract into `sj/b01ec87a6f29b/d` on the job-private disk, which bwrap exposes at `/scratch/jjyeung/b01ec87a6f29b/d`. Archives must use relative members, with no `d/` outer directory. Multiple archives must have disjoint members. Relative internal links are allowed by the template; arbitrary absolute links are refused.

The required input layout under that data root is:

- An export directory containing `artifact.json`, `heads.pt` and `full_weights/` with all five tensors, the index, and `full_weights.json`. The original artifact, head and weight-manifest pins are fixed. `stage_restore` verifies every weight against the manifest and restores via local links, without a second weight copy.
- A G3T directory containing `model.safetensors` and `config.json`.
- A selector directory containing `selector_head.json` and `selector_head.safetensors` from run_iso.
- SAM source, checkpoint and receipt, preserving the source tree's vocabulary assets and file pins.
- A frame directory with the exact relative paths in the pinned FRAMES/DENSE manifests: 32 anchors and the registered 32/64 dense frames. Each generation checks RGB hashes. Do not replace dense frames with repeated anchors.
- Original processor assets and `model_8005668fc14ce5ee.tar`. The restored base must use the original tokenizer/config/processor bytes; the template's unrelated base manifest is insufficient evidence.
- A compatible environment or overlay, an exact imported-versions receipt, and the authorized vnice/terminator scripts or their staged runtime locations. The environment needs torch, torchvision, transformers >=5.12, scipy, and SAM dependencies. No installation or download runs in the job. The template's UV interpreter paths must remain valid inside its namespace.

`1.json` has this structure; replace every placeholder before checking:

```json
{
  "schema": 1,
  "archives": [{
    "parts": [{"path": "/project/community/jjyeung/<opaque>/0.tar", "bytes": 1, "sha256": "<64 hex>"}],
    "sha256": "<whole archive 64 hex>",
    "expanded_bytes": 1,
    "destination": "sj/b01ec87a6f29b/d"
  }],
  "files": {
    "artifact": {"path": "/scratch/jjyeung/b01ec87a6f29b/d/x/artifact.json", "bytes": 11474, "sha256": "<registered full pin>"},
    "heads": {"path": "/scratch/jjyeung/b01ec87a6f29b/d/x/heads.pt", "bytes": 2763214343, "sha256": "<registered full pin>"},
    "full_weights": {"path": "/scratch/jjyeung/b01ec87a6f29b/d/x/full_weights/full_weights.json", "bytes": 1794, "sha256": "<registered full pin>"},
    "g3t_weights": {"path": "<logical path>", "bytes": 1, "sha256": "<64 hex>"},
    "g3t_config": {"path": "<logical path>", "bytes": 1, "sha256": "<64 hex>"},
    "sam_checkpoint": {"path": "<logical path>", "bytes": 1, "sha256": "<registered full pin>"},
    "sam_receipt": {"path": "<logical path>", "bytes": 1, "sha256": "<64 hex>"},
    "selector_weights": {"path": "<logical path>", "bytes": 207328, "sha256": "<registered full pin>"},
    "selector_config": {"path": "<logical path>", "bytes": 6541, "sha256": "<registered full pin>"},
    "base_config": {"path": "<logical processor directory>/config.json", "bytes": 3126, "sha256": "<64 hex>"},
    "original_model": {"path": "<logical path to original manifest tar>", "bytes": 10240, "sha256": "<64 hex>"},
    "env": {"path": "<logical versions receipt>", "bytes": 1, "sha256": "<64 hex>"},
    "policy": {"path": "<logical policy receipt>", "bytes": 1, "sha256": "<64 hex>"}
  },
  "frames_root": "/scratch/jjyeung/b01ec87a6f29b/d/f",
  "sam_source": "/scratch/jjyeung/b01ec87a6f29b/d/s",
  "python": "/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python",
  "env_roots": [],
  "environment_receipt": "env",
  "policy_receipt": "policy",
  "policy": {"vnice": "<staged logical path>", "terminator": "<staged logical path>"},
  "resume": null
}
```

The environment receipt contains `{"versions":{"torch":"...","torchvision":"...","transformers":"...","scipy":"..."}}` with the actual imported versions. The policy receipt contains the exact `vnice` and `terminator` paths and `"authorized": true`; it attests that `bash <vnice> <command...>` is the approved invocation. The job checks both script hashes against the template registry. It never launches a terminator or disables one. Runtime groups are reused by pinned copy; `orchard_stage.copy_parts`, `extract_stream`, `orchard_job.namespace`, `orchard_results.publish` and `return_io` retain their template code.

## CPU check on the Orchard login node

After staging, run only the metadata check on login. It hashes the small code package, checks the complete input contract and staged archive sizes, and validates every Slurm submission string. It does not open model tensors, run nvidia-smi, or decode on login.

```bash
cd /project/community/jjyeung/b01ec87a6f29b
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 4 --time 01:15:00
```

`2.json` must report `passed: true`. On the allocated node, the job rechecks all archive/file hashes, imports the required libraries, checks their versions, and calls b04's reviewed CPU restore before any GPU decode. A real step-544 decode has not been rehearsed here.

## Submit after ORCH releases GPUs

The operator chooses `A_T`; 01:15:00 is an example for four GPUs. The helper refuses more than four GPUs, less than 40 minutes, or more than five allocated GPU-hours. Staging and return consume part of that allocation. Run the Slurm test and actual submission as separate, explicit commands:

```bash
cd /project/community/jjyeung/b01ec87a6f29b
A_N=4 A_T=01:15:00 bash SUBMIT.cmd --test-only
A_N=4 A_T=01:15:00 bash SUBMIT.cmd
```

The job name is `a15_cot_apb01ec87a6f29b`. `LEDGER.jsonl` retains the exact argv and Slurm response. A nonzero return is a stop, never a relaunch trigger. Change the time/card count only after rerunning the CPU check. Keep the same GPU count on resume because shard identity is immutable.

The runner admits no new records during the last 1,800 seconds. Each worker has a Python timer for 1,200 seconds before allocation end; it abandons an unfinished read and exits 75. This conservative return reserve covers the template's pool/GCS timeout chain (up to about 1,020 seconds plus archive work). The commit section defers that timer until a full JSONL line is fsynced. A Slurm warning creates a shared stop marker. Python timers cannot interrupt an indefinitely blocked kernel or filesystem call; no successful wall-time guarantee is claimed for that failure mode.

## Fetch and resume

The template returns `result.tar.gz`, `EXIT.json`, `JOB.log`, and `RETURN_RECEIPT.json` to `/project/community/jjyeung/okh7/ae71c903/<return-token>` and attempts its independent GCS return. The return token is the package token followed by the Slurm job ID encoded as eight hex digits. The template enforces its 100 MB shared pool and 90 MB result cap; a full pool blocks the job before staging.

For example, after setting the actual numeric Slurm ID:

```bash
cd /project/community/jjyeung/b01ec87a6f29b
J=170999
R=$(/usr/bin/python3 -I -s -B -c 'import sys; print("b01ec87a6f29b"+format(int(sys.argv[1]),"08x"))' "$J")
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$R" --out "/tmp/$R"
```

This fetch runs locally on Orchard and reuses the template's framed `stdout_transfer.emit/receive`. Return `/tmp/$R/0.tgz` and receipts through the operator's existing governed bridge at <=8 MB/s. The exact bridge connection is OPEN; this builder has no Orchard connection authority. Never send result folders or relay node data through a laptop.

The result tar contains `metadata/journals/<type-index>/<gpu-index>/{items.jsonl,environment.json,item_mapping.json,projection.json,...}`, aggregate `metadata/projection.json`, `SUMMARY.json`, `STEPS.jsonl`, and logs. A shard gets its projection after ten reads; the aggregate projection exists even for a shorter stop. Caches, weights and RGB are excluded. A clean partial return is incomplete under the template's `EXIT.json` contract; `SUMMARY.json` distinguishes a deadline stop from a worker failure. Do not treat a partial return as a completed read.

To resume a clean stop, pin its returned archive path, bytes and SHA256 in `1.json` under `resume`. Leave the package, input bytes, logical paths, and GPU count unchanged. Rerun the CPU check and explicitly submit again. The job imports only the journal subtree and stable identity, omitting allocation stop/terminal markers. It refuses changed bindings, duplicate records, and torn tails. A killed or failed allocation requires the user's answer first; this package never retries it automatically.
