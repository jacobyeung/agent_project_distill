Run the four new cells after the two main pass-3 cells. Keep separate destinations and attempt names for each family and checkpoint. Every new cell has 150 tasks, 50 per kind. Both checkpoints use greedy decoding, thinking ON and a 16,384-token cap; CP1 uses 32 duplicate anchors and f17 uses 32 spread anchors.

The payload directories are `DEV_BACKDIR` and `DEV_FORWARD_TWINS`. Their cell names are `devS1_v3_backdir_real_timing_{cp1m200,f17}` and `devS1_v3_forward_twins_real_timing_{cp1m200,f17}`. `PAIRS.jsonl` joins exact away/forward items. Their strata are `facing_away_no_released_label` and `forward_twin_gt_control`; use the own-GT scores for these cells. No released label exists for the away wording. The forward controls copy the stored dev source wording and GT answers.

Set local paths and verify the delivery:

```bash
set -euo pipefail
L=/scratch/jjyeung/orch_cd/devs1_direct
P=$L/out/r4
CPU=/scratch/jjyeung/envs/p1cpu/bin/python
CPKIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt
F17KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps
FRAMES=/scratch/jjyeung/devs1_frames
(cd "$P" && sha256sum -c SHA256SUMS)
"$CPU" -I -s "$P/test_r4.py"
```

The adapter accepts `--payload-root` (alias `--payload`). Its default is the adjacent pass-3 `out/r3` directory. The existing main-cell commands therefore continue to work through the new entrypoint; the r3 adapter and payload must remain staged beside r4. The new families use their own pins and the copied pass-3 timing authorities. Do not pass the old back_dir payload directly.

For CPU dry binds, choose unused destinations:

```bash
"$CPU" -I -s "$P/adapter.py" bind --dry --payload-root "$P/DEV_BACKDIR" --cell cp1m200 --kit "$CPKIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r4/operator_dry_backdir_cp1"
"$CPU" -I -s "$P/adapter.py" bind --dry --payload-root "$P/DEV_BACKDIR" --cell f17 --kit "$F17KIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r4/operator_dry_backdir_f17"
"$CPU" -I -s "$P/adapter.py" bind --dry --payload-root "$P/DEV_FORWARD_TWINS" --cell cp1m200 --kit "$CPKIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r4/operator_dry_forward_cp1"
"$CPU" -I -s "$P/adapter.py" bind --dry --payload-root "$P/DEV_FORWARD_TWINS" --cell f17 --kit "$F17KIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r4/operator_dry_forward_f17"
```

Each must report 150 tasks and zero missing labels. Each BIND_STATUS must report 150 unused/unavailable released labels. The delivered CPU binds are `work/r4/dry_backdir_{cp1m200,f17}` and `dry_forward_twins_{cp1m200,f17}`. Dry binds cannot launch.

On the separately assigned run host, stage the pinned frame tree, model assets, payload and reviewed kits. Set FRAMES and kit paths for that host. Write `work/r4/MODELS.runhost.json` by changing only paths in MODELS.reference.json. Preserve the CP1 artifact SHA256 `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`, f17 archive SHA256 `47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae`, and base snapshot pin. Live binding verifies production PNG hashes, RGB dimensions and pixels and creates same-filesystem hard links:

```bash
"$CPU" -I -s "$P/adapter.py" bind --payload-root "$P/DEV_BACKDIR" --cell cp1m200 --kit "$CPKIT" --models "$L/work/r4/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r4/run_backdir_cp1"
"$CPU" -I -s "$P/adapter.py" bind --payload-root "$P/DEV_BACKDIR" --cell f17 --kit "$F17KIT" --models "$L/work/r4/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r4/run_backdir_f17"
"$CPU" -I -s "$P/adapter.py" bind --payload-root "$P/DEV_FORWARD_TWINS" --cell cp1m200 --kit "$CPKIT" --models "$L/work/r4/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r4/run_forward_cp1"
"$CPU" -I -s "$P/adapter.py" bind --payload-root "$P/DEV_FORWARD_TWINS" --cell f17 --kit "$F17KIT" --models "$L/work/r4/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r4/run_forward_f17"
```

After both main cells finish, the operator sets RUN_PY to the reviewed kit-compatible interpreter with vLLM 0.32.0 and CUDA_VISIBLE_DEVICES to one assigned card. Launch sequentially:

```bash
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r4/run_backdir_cp1" --attempt devS1_v3_backdir_cp1_a1
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r4/run_backdir_f17" --attempt devS1_v3_backdir_f17_a1
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r4/run_forward_cp1" --attempt devS1_v3_forward_cp1_a1
"$RUN_PY" -I -s "$P/adapter.py" launch --dest "$L/work/r4/run_forward_f17" --attempt devS1_v3_forward_f17_a1
```

The unchanged CP1 worker derives B2048 and B4096 from the ON16k run, including authenticated continuation journals; the adapter then calls the kit’s budget merger. Preserve those journals and parity records. Do not rerun a killed job automatically. This delivery ran no inference.

Use each kit’s merged summary for its cell and retain the per-kind scores. Compare away medium with 18/50 always-back (36%) and 20/50 majority-right (40%); easy majority-right is 27/50 (54%), and hard majority-back-right is 18/50 (36%). Forward medium always-back is 2/50 (4%) and majority-left is 29/50 (58%). Keep the main-cell report separate: its fixed 1,525-item membership and strata do not describe these controls. Join family results by PAIRS.jsonl to compare the exact 150 twins.
