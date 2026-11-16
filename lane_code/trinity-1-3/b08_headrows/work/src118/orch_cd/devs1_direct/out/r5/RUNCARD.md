Run the CPU merge against the existing request and journals. No rebind or generation is needed. The command writes a new destination and preserves the original request binding, source code pin, task pins, and journal bytes.

```bash
L=/scratch/jjyeung/orch_cd/devs1_direct
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="$L/work/r5/hf_cache" XDG_CACHE_HOME="$L/work/r5/cache"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s "$L/out/r5/adapter.py" merge \
  --source /scratch/jjyeung/orch_cd/evalx/work/res_devS1v2_cp1 \
  --kit /scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt \
  --dest "$L/work/r5/operator_cp1_merge" \
  --attempt devS1_v2_real_timing_cp1_a1 \
  --tokenizer-dir "$L/work/r5/tokenizer" \
  --tokenizer-manifest "$L/work/r5/tokenizer/base_manifest.json"
```

`operator_cp1_merge` must not already exist. The delivered merge is in `work/r5/real_cp1_final`; its compact results and receipts are also in `out/r5`. `work/r5/tokenizer` contains the exact manifest-pinned tokenizer files copied from local `p1_build/ref/qwen35_tok`; no weights or network are needed. Its tokenizer SHA256 is `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`.

The source directory must contain `request.json`, `results/0/g0.jsonl`, and the matching `p0_<attempt>.json`. CP1 also requires both `budget_{2048,4096}.g0.jsonl` and their `.meta.jsonl` receipts in `results/0`. Use the attempt named in the parity filename. The adapter verifies the original request formula and reconstructs the exact bound code archive from `--kit` before importing it. Only the output path changes, and output is excluded from the binding hash. Dataset paths must still resolve to the original pinned payload.

The merge writes authenticated items and summaries for ON16k, B2048 and B4096, three `report/<arm>.json` exports, `MERGE_INPUTS.json`, and `MERGE_COMPLETE.json`. The report includes primary per-type and overall scores, capped/unanswered/unparsed counts, and own-GT views. It refuses incomplete membership or failed parity. Frame/timing metadata is checked against the payload; existing parity receipts are validated by the kit. This CPU merge does not regenerate pixels or GPU parity.

For f17, use the same command with its source directory, its attempt, an unused destination, and `--kit /scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps`. Omit both tokenizer arguments: that kit's merge interface does not use a tokenizer. It produces ON16k only. For either pass-4 family, use that family's existing source directory and attempt. The request selects its pinned payload and own-GT stratum automatically; CP1 still merges both budgets.

After both checkpoint merges, compare their completed exports:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s "$L/out/r5/report.py" \
  --cp1 "$L/work/r5/operator_cp1_merge" \
  --f17 "$L/work/r5/operator_f17_merge" \
  --output "$L/work/r5/operator_paired.json" --replicates 10000
```

The comparator checks export digests, checkpoint identities, strata pins, and exact paired membership. It reports all three CP1 arms minus f17 with a physical-room bootstrap, seed 17. Compare matching families only. An empirical f17 comparison awaits its journals; the delivered paired reports use synthetic answers.

For future binds and launches, substitute `out/r5/adapter.py` in the existing pass-3/pass-4 commands. Its `bind` delegates to the pinned original adapter, so the kit copy and binding scheme stay unchanged. Its `launch` installs the summary wrapper around the original launch. Existing r3/r4 launch entrypoints do not acquire this wrapper automatically. This pass ran only CPU commands.

Run the complete synthetic integration suite in a fresh directory:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s "$L/out/r5/test_merge.py" suite \
  --dest "$L/work/r5/operator_tests"
```
