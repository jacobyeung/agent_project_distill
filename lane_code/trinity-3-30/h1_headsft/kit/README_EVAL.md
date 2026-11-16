# H1 evaluator for b09_rlkit

Run from `/scratch/jjyeung/orch_n30/h1_headsft/kit` in b09's checkpoint-read environment.
`cpu.sh` supplies the CPU-only build-test environment with a 32 GiB/16-thread cap.

```sh
K=$PWD
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B -m h1eval.cli items build --sets revsi999,devs1_routed,devs1_direct_main
"$PY" -B -m h1eval.cli run --export "$RL_EXPORT" --items items/revsi999.json --arms own --modes scale_translation:0.5,scale_translation:2,rotate_translation:180,negate_turn,scale_scene:0.5,scale_scene:2 --out "$K/runs/rl_step100" --frames 32
"$PY" -B -m h1eval.cli pair --a "$K/runs/sft_step200" --b "$K/runs/rl_step100"
"$PY" -B -m h1eval.cli curve "$K/runs/rl_step100" "$K/runs/sft_step200"
```

`items build` writes immutable ready manifests; unavailable sets exit nonzero.
RevSI has 999 items (283 meter-distance, 37 room), with zero R0 overlaps.
The native C8r routed set has 636 items, including 450 camera tasks.
The ready e193 direct set has 1,825 items: 1,525 main and 150 each forward/away.
To rebuild it, supply both pinned twin files with `--forward-tasks FILE --away-tasks FILE`.
The builder checks fixed membership, type counts, room keys and the R0 pin.
`r0dev` refuses without `--r0dev-items FILE`; supplied rooms must belong to R0-dev.

Each export needs `h1eval.json`; use `configs/h1eval_native.example.json`.
Set `lineage`, the actual checkpoint `step`, and the lane's read `device`.
The native loader pins config, receipt, model manifest, checkpoint, reader artifact
and media bindings. `NATIVE_EXPORT_CONTRACT.md` defines these inputs.
It uses `H1Generator` over the reader core; no caller-written factory is required.
Real 9B loading and RGB/SAM/selector integration remain unverified on this CPU build.
The CPU fixture uses a real tiny LM with scripted sampled tokens and is marked `fixture`.

Add `tower` to `--arms own,tower`; its baseline uses the reader's tower factory.
Modes also include `donor` and `gt`; `gt` requires `--gt NPZ_DIRECTORY`.
GT filenames are SHA256(canonical JSON item ID) plus `.npz`; arrays are documented
in the export contract. Donors come from a different capture in the pinned set.
M3 uses each intervention's own printed decision and a 20% numeric-change gate.
It converts expected values only; it never rewrites the model's answer.
Each run writes `items.jsonl`, `report.md` and `curve.json`, including all hashes.
Intervals resample rooms 10,000 times with seed 20261115. Pair reports B minus A
on shared items (M3 uses shared eligible items) and refuses incompatible bindings.
Curve prints per-type metrics and hashes, ordered by SFT step, then RL step.

Each perturbation applies only to its registered type. Parameter-bearing keys such
as `scale_translation:0.5` and `scale_translation:2` remain distinct in records,
paired statistics and curves. The tower arm decodes each item only once.
M1 reports explicit pass flags: routed call rate >=98%, exact sequence >=95%,
answer-before-call <=1%; direct false calls <=2% overall and <=5% per type.
ReVSI distance uses the registered >=95% call-rate threshold.
M2 reports per-item own-minus-tower task accuracy in percentage points, with the
room bootstrap. A type passes when its lower 95% bound is strictly above -5.

S1 preparation checks camera materialization on the config-bound routing receipt.
A rate below 95%, missing receipt or empty camera denominator refuses launch.
An operator can run `bash cpu.sh rows/faithful_gate.py ROWS_OR_SQLITE_RECEIPT`;
the JSON report includes the identity rate, per-type counts and refusal histogram.
The real receipt bound by these configs is not staged on this node.
