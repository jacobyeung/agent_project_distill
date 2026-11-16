The adapter passes CPU checks, but this payload is **not launch-ready**. The fixed list contains 1,536 scored items, not 1,486. It also contains 150 routes without released labels and 11 room placeholders without either label. `MISSING_LABELS.jsonl` identifies all 161 items. The current ruling requires both labels, so a live bind refuses them.

These commands run locally on the operator's compute host; they perform no transfer. The operator must stage the delivery there, assign an available card, and use a GPU environment with the kit's pinned vLLM 0.32.0 and Qwen3.5 dependencies. This lane used only the isolated CPU interpreter and ran no GPU command.

Set the paths once:

```bash
L=/scratch/jjyeung/orch_cd/devs1_direct
CPU=/scratch/jjyeung/envs/p1cpu/bin/python
P=$L/out
CPKIT=/scratch/jjyeung/orch_cd/evalx/work/aws_vl64rt
F17KIT=/scratch/jjyeung/orch_cd/evalx/work/aws_eval_gaps
FRAMES=/scratch/jjyeung/devs1_frames
```

Before inference, replace `CPKIT` and `F17KIT` with the reviewed consolidated kit directories when the merge-fix lane delivers them. This delivery tested the two paths above. It does not certify the pending revision.

Reproduce the CPU bind checks in fresh directories:

```bash
$CPU -I -s "$P/adapter.py" bind --dry --cell cp1m200 --kit "$CPKIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/operator_dry_cp1"
$CPU -I -s "$P/adapter.py" bind --dry --cell f17 --kit "$F17KIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/operator_dry_f17"
$CPU -I -s "$P/test_adapter.py"
```

The test suite uses the supplied `work/dry_release_cp1` and `work/dry_release_f17` copies. Keep them with the lane when running the full suite. The two commands above independently test a newly adopted kit. Choose a new destination for another authorized bind; existing destinations are never deleted or overwritten by the binder.

To close the label gaps under the current ruling, provide `work/LABEL_SUPPLEMENT.jsonl` with exactly the 161 missing-label qids. For each missing field, supply its value and `<field>_source: {path, sha256, locator}`. Sources must be staged under `/scratch`; `locator` identifies the source row and field. Values must use the question's units. The operator must verify that a released label is an independent released value; the resolver checks pins and completeness, not that semantic claim. It refuses changes to existing labels.

```bash
$CPU -I -s "$P/resolve_labels.py" --source "$P" --labels "$L/work/LABEL_SUPPLEMENT.jsonl" --dest "$L/work/payload_resolved"
P=$L/work/payload_resolved
```

The resolver writes new tasks, strata, counts, and hashes before any model runs. It preserves the original payload. If the orchestrator instead allows a missing-release stratum, the launch gate needs that explicit policy change; the present resolver does not fabricate 150 released route answers. Six of the eleven missing room canonical labels have local GT candidates; five do not. The requested CPU GT pass was not authorized or run.

Create `work/MODELS.runhost.json` with the same checkpoint identities as `MODELS.reference.json`, updating paths to the staged, authenticated assets. The reference CP1 artifact hash is `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`; the f17 archive hash is `47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae`. The kit validates model manifests and weights at launch. This lane did not read them.

Bind both cells after labels, reviewed kits, and model paths are ready:

```bash
$CPU -I -s "$P/adapter.py" bind --cell cp1m200 --kit "$CPKIT" --models "$L/work/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/run_cp1"
$CPU -I -s "$P/adapter.py" bind --cell f17 --kit "$F17KIT" --models "$L/work/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/run_f17"
```

These commands finish the PNG receipts and byte checks. They read roughly 142 captures of PNGs sequentially; hard links avoid duplicating PNG bytes. Check free scratch space for the model stage before launching: the kit may copy full weights. Do not run a model stage or other heavy I/O without the operator's authorization.

Use the assigned card and the already-staged GPU interpreter. Run these sequentially in the operator's persistent session:

```bash
: "${GPU_PY:?Set the path to the kit-compatible GPU Python}"
: "${CARD:?Set one assigned GPU index}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$L/work/cache" HF_HOME="$L/work/hf" TRITON_CACHE_DIR="$L/work/triton"
CUDA_VISIBLE_DEVICES="$CARD" "$GPU_PY" -I -s "$P/adapter.py" launch --dest "$L/work/run_cp1" --attempt devs1_cp1_a1
CUDA_VISIBLE_DEVICES="$CARD" "$GPU_PY" -I -s "$P/adapter.py" launch --dest "$L/work/run_f17" --attempt devs1_f17_a1
```

The wrapper calls the copied kit's worker, merge, and CP1 budget merge. It bypasses the kit's video-decoding launch stage because the PNG receipts already exist. CP1 uses 32 duplicate anchors, greedy thinking, cap 16,384, and derives B2048 plus the kit's ancillary B4096 arm with its 64-token continuation rule. f17 uses 32 spread anchors, greedy thinking, and the VSI kit's 16,384 cap. No weights, prompts, scorer functions, or budget derivation code are patched.

Plan roughly one hour per cell from the operator's earlier ReVSI throughput estimate, plus staging and CP1 budget continuations. This is unmeasured for dev-S1; long thinking outputs can take longer. Read the first completed timing records before assigning a tighter estimate. No timeout kills or automatic relaunch loop are supplied.

Outputs are `work/run_*/request.json`, `kit/CODE_PINS.json`, `PROMPT_PINS.json`, `frames/0.json`, and `results/0/{g0.jsonl,p0_ATTEMPT.json,items_ATTEMPT.jsonl,summary_ATTEMPT.json}`. CP1 also writes source-bound budget journals and `results/budget_2048/0/` and `results/budget_4096/0/` summaries. Preserve the ON journal and budget receipts.

After both runs finish, produce the paired report on CPU:

```bash
$CPU -I -s "$P/report.py" report --cp1 "$L/work/run_cp1" --f17 "$L/work/run_f17" --cp1-attempt devs1_cp1_a1 --f17-attempt devs1_f17_a1 --output "$L/work/report_devS1" --replicates 10000
```

`REPORT.json` reports each of the 11 types and an item-weighted overall. Primary items score against `released_answer`. Disagreements report `released_answer` and `answer` separately, with per-type disagreement counts. Each view includes item/scored counts, score percent, capped, unanswered (empty extracted answer), and unparsed counts. It reports ON16k and B2048 independently. The primary comparison is CP1 B2048 minus f17; ON16k minus f17 is supplementary. These mixed 11-type means are not the official VSI benchmark aggregate.

The paired 95% percentile interval uses 10,000 bootstrap draws with seed 17. Each draw samples physical rooms with replacement and retains every paired item in each sampled room. ScanNet rescans share `d1/sceneNNNN`; ARKit videos share a venue. Both checkpoints use the same draw. The point estimate and bootstrap use item-weighted means. Per-type intervals resample the rooms represented in that type. Empty strata return null metrics. A report refuses mismatched keys, conflicting complete records, changed bindings, wrong frame order, incomplete rows, or failed kit parity. It never fills missing predictions with successful rows from another run.
