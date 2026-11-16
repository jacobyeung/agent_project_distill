Use only `devS1_v2_real_timing_cp1m200` and `devS1_v2_real_timing_f17`. **The old attempt’s 844 journaled rows are void and must not be resumed, copied, merged, or scored with these cells.** Start fresh bind directories and fresh attempt names. Keep the old files as evidence; do not delete them.

Both cells contain 1,525 items: 1,375 primary and 150 unavailable routes. CP1 reads 32 duplicate anchors (64 RGB frames); f17 reads 32 spread anchors. Both use greedy decoding, thinking ON and a 16,384-token cap. S1-FPS1 rates are 24/60/10 fps. `TIMING.md` records training and processor formulas. The separate training release-text gate remains NO, as documented in `LABEL_AGREEMENT.md`; this timing repair does not change that finding.

Set the local paths:

```bash
set -euo pipefail
L=/scratch/jjyeung/orch_cd/devs1_direct
P=$L/out/r3
CPU=/scratch/jjyeung/envs/p1cpu/bin/python
CPKIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt
F17KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps
FRAMES=/scratch/jjyeung/devs1_frames
```

Verify the delivery and repeat CPU checks:

```bash
(cd "$P" && sha256sum -c SHA256SUMS)
$CPU -I -s "$P/test_adapter.py"
$CPU -I -s "$P/test_timing.py"
$CPU -I -s "$P/prove_timing.py" --model cp1m200
$CPU -I -s "$P/prove_timing.py" --model f17
```

The proof files are deterministic. Tests retain their synthetic fixtures in `work/r3`. The delivered reviewed dry binds are `work/r3/final_cp1` and `work/r3/final_f17`; they cannot launch. `DRY_BIND_*.json` pins their requests, receipts, prompt inventories, source archives and code inventories. The copied evaluator code is unchanged from the reviewed kits.

For a new operator dry bind, use unused destinations:

```bash
$CPU -I -s "$P/adapter.py" bind --dry --cell cp1m200 --kit "$CPKIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r3/operator_v2_cp1"
$CPU -I -s "$P/adapter.py" bind --dry --cell f17 --kit "$F17KIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r3/operator_v2_f17"
```

Each must report 1,525 tasks, zero blocking canonical labels and 150 unavailable released labels. Prompt-context inventories must match. Existing destinations are refused.

For the separately scheduled run, stage the already pinned PNG tree and model assets on the run host. Prepare `work/r3/MODELS.runhost.json` by changing only paths in `MODELS.reference.json`. Preserve every model hash: CP1 artifact `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`, f17 archive `47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae`. Stage the pinned payload and reviewed kit closure together; do not alter their files.

Live binding reads the staged PNGs, verifies their byte hashes, RGB dimensions and pixel hashes, then hard-links them on the same filesystem:

```bash
$CPU -I -s "$P/adapter.py" bind --cell cp1m200 --kit "$CPKIT" --models "$L/work/r3/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r3/run_v2_cp1"
$CPU -I -s "$P/adapter.py" bind --cell f17 --kit "$F17KIT" --models "$L/work/r3/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r3/run_v2_f17"
```

No inference was launched in this CPU task. On the separately assigned run host, the operator supplies `RUN_PY`, the kit-compatible interpreter with vLLM 0.32.0, and sets `CUDA_VISIBLE_DEVICES` to exactly one assigned card. Run sequentially:

```bash
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r3/run_v2_cp1" --attempt devS1_v2_real_timing_cp1_a1
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r3/run_v2_f17" --attempt devS1_v2_real_timing_f17_a1
```

Preserve ON and CP1 B2048/B4096 continuation journals. The kits own model authentication, processor parity, continuations and merging. A killed job must not be automatically retried. The r3 adapter rejects an old binding, and the report rejects old timing metadata even when frame order matches.

After both complete, produce the paired report:

```bash
$CPU -I -s "$P/report.py" report --cp1 "$L/work/r3/run_v2_cp1" --f17 "$L/work/r3/run_v2_f17" --cp1-attempt devS1_v2_real_timing_cp1_a1 --f17-attempt devS1_v2_real_timing_f17_a1 --output "$L/work/r3/report_devS1_v2" --replicates 10000
```

The report keeps primary, disagreement and unavailable views. It compares CP1 B2048 and ON16k with f17 using paired physical-room bootstrap intervals. Incomplete journals, conflicting rows, altered bindings, wrong timing and failed parity are refused.

The read-only facing-away payload in `back_dir/out/r2/DEV_BACKDIR` also has fps=1 in all 152 frame records and all 150 task rows. Its owner must rebuild timing, pins and versioned cells before using this adapter. `PLACEHOLDER_AUDIT.md` and `.json` list every affected file and location. Do not feed its current manifest or task timing to a v2 run.
