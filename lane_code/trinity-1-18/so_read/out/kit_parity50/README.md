This kit has **not run on a GPU**. It compares the same pinned 50 items with every new cache OFF and with selected caches ON. The existing G3T memo setting stays as supplied. The sample contains ten items per type and twelve native captures; it stresses reuse and is not a representative speed sample.

Apply both diffs from `out/patches/` to a fresh copy of the staged payload's `src` directory with `patch --batch --fuzz=0 -p1`. Rebuild and authenticate the payload before production use. The patches change source hashes even when their switches are OFF. The rebinding-only `build_r10.py` does not automatically incorporate source patches.

Copy `config.example.json` to a new configuration and fill its paths to the approved staged checkpoint, export pin, artifact binding, reader source, settings, native task manifests, and frames. Use the production torch 2.11/CUDA 12.9 environment on an assigned Orchard GPU. Keep the checkpoint, source, precision, attention backends, and hardware fixed across passes. Do not run this kit on the shared Trinity GPUs.

The acceptance command, **not executed here**, is:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B /path/to/kit_parity50/run.py /path/to/config.json \
  --out /scratch/NEW_PARITY_OUTPUT --enable-gpu --repeat-baseline --shards 4
```

`CUDA_VISIBLE_DEVICES` must already identify the assigned GPU. Each pass starts a fresh process. `OFF_REPEAT` checks the baseline's repeatability. The four optional shards run sequentially on that GPU to check shard equivalence; this does not measure parallel speed. Change `enable_caches` to a subset of `processor`, `vision`, and `sam` to isolate a failing or slow cache. Never overwrite a completed parity output.

The kit writes complete reader journals, per-type seconds/item, cache counters, model-load timings, host/GPU memory peaks, and kernel/version receipts. The comparison requires exactly the expected 50 IDs. It checks the full generated text, token IDs, calls, responses, heads, scale, finish, scores, decode budget, and all remaining semantic fields without numeric tolerance. It detects a changed answer even if the official score is unchanged. All enabled caches should show useful hits before adoption; an all-miss run establishes no speed benefit.

The comparator excludes only `seconds`, `timings`, `audit`, `perception_memo`, `read_cache`, and `read_profile` from the output payload; audit violations still fail. JSON object order is canonicalized. Runtime paths, timings, and cache counters cannot be identical between passes. The original journals retain that evidence. `MERGE_PARITY.json` additionally requires identical bytes in the canonical single-shard and multi-shard answer/trace tarballs.

For a preempt array, fill `array_config.example.json` and adapt `array_preempt.template.sh`. The worker is OFF unless `--enable-array` is supplied. The template has no submission action. The orchestrator must stage the approved inputs, provide the actual policy wrapper and memory allocation, preserve the same logical input paths, and choose a journal directory that survives node loss. Do not use allocation-local `/tmp` or `/scratch` as the only journal copy. Keep shard count, manifest, source, checkpoint, and settings fixed across requeues.

Each shard owns whole physical rooms and preserves manifest order within its assigned set. Every item becomes durable in `committed/` before entering `items.jsonl`. A requeue preserves a torn JSONL file, rebuilds it from complete commits, and reruns only uncommitted items. It can repeat an interrupted computation but cannot duplicate its committed answer. The store requires Linux/POSIX rename, file/directory fsync, and advisory-lock support; the actual persistent filesystem has not been tested here.

After all tasks finish, invoke `h1eval.h10.merge_read` with the full manifest and the explicit journal directories (`journal_root/<type>/<shard>`). The module rejects missing, duplicate, foreign, or differently bound records and writes `answer_trace_return.tgz` plus separate `PROVENANCE.json`. It does not publish an Orchard return token. A normal deadline exit with incomplete work returns status 75; only scheduler preemption with the configured REQUEUE policy supplies automatic requeue. There is no retry loop.

The CPU comparator test is:

```bash
READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts \
  bash /scratch/jjyeung/orch_n30/so_read/work/cpu.sh \
  /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_compare.py
```
