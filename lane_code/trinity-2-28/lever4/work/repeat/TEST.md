# compare.py test (2026-11-21, trinity-2-28, CPU, threads 1, nice 10)

## Kit
`kit/r1/` holds a snapshot of lever1_c/r1 `relift.py`, `runtime/`, `returned/` (job 174135) and
`depth_format.py`; `kit/r3/devpose.py` is a copy of lever1_c/r3. compare.py loads `kit/r1/relift.py`
and calls its `dependencies()`, so it uses relift's Records reader, `restore`, `fit_lift`, `gap_value`,
`round_gap`, `printed_gap`, `read_records` and `depth_free_parity`. The gbuild modules load from
cont_ops24_c, as in relift.

## Definitions
- Camera and scale fields (K, camera_to_world_metric, camera_to_world_unscaled, canvas_to_source,
  scale) use the capture worker's `compare` (runtime/w.py:20), which takes max |a-b| over all anchors.
- Each run is compared with T1 per item, against the item's T1 pass-0 geometry; a capture's value is
  the max over its items. T1 has geometry for 149 of the 150 items (`vsi590k_045785` lacks it), as in 5.json.
- Bounds are twice the max T1 repeat deviation, recomputed from the 10 repeats in t1.gz exactly
  as build_depth.reference does.
- Translation is the metric camera-centre distance per anchor. Rotation is the geodesic angle per anchor.
- Gap classes compare the 2-decimal gaps: 0.00, 0.01, beyond, or missing (one side None). Objects
  inherit their item's class, which is relift's rule.

## Test 1: run2 = run1 (job 174135 dump against itself)
Command (56 s):
```
cd /scratch/jjyeung/orch_n30/lever4/work/repeat; K=kit/r1/returned
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python compare.py \
  --run1 $K/0.gz --receipt1 $K/4.json --run2 $K/0.gz --receipt2 $K/4.json --out test/self.json --md test/self.md
```
- run2 vs run1: every field, translation, rotation, depth and object box is 0 in all 60 captures.
  Agreement within T1 bounds is True, and the gaps agree for 150/150 items at 0.00.
- run vs T1: the per-item w.py deviations equal returned/5.json's per-item `max_deviations` and its
  maxima bit-for-bit (K 0.3224, c2w_metric 0.1174, c2w_unscaled 0.0318, canvas 0, scale 2.27e-4). They
  also equal the parity embedded in each row. The recomputed bounds equal 5.json `bounds`. The
  47 captures over the bounds are exactly the captures 5.json marks untrusted.
- Gaps: run vs printed gives 141 at 0.00 and 9 at 0.01, with none beyond. All 150 relift values and the
  9-item list match RELIFT_GAPDIAG.json exactly. relift's depth-free gate passes 142/142.
- Worst vs T1: arkitscenes/41126645 (0.141 m, 1.44 deg), scannet/scene0320_01 (0.0075 m, 0.088 deg)
  and scannetppv2/7e7cd69a59 (0.0102 m).

## Test 2: synthetic run2 (test/make_perturbed.py, test/perturbed/)
The synthetic run2 scales the depth of scannet/scene0515_00 by 1.01 and rotates anchor 5 of
arkitscenes/42446097 by 0.3 deg.
- compare.py recovers the rotation as 0.300 deg and the depth change as 0.0471 m max (1.00% relative).
- The rotated capture's c2w deviation is 0.0049, which exceeds the 0.00372 bound, so agreement is False.
- Of the 7 scene0515_00 items, 1 gap moves by 0.01 and 6 move beyond it. 18 object boxes change.
  Every other capture stays at zero.

## Run on the second dump
```
... compare.py --run1 kit/r1/returned/0.gz --receipt1 kit/r1/returned/4.json \
  --run2 RUN2/0.gz --receipt2 RUN2/4.json [--parity2 RUN2/5.json] --out OUT.json --md OUT.md
```
Requirements for run2:
- The receipt is JSON, plain or a0-hex. It holds `sha256` (or `capture_sha256`) of the raw .gz,
  `verified: true`, and optionally `bytes`, which must then equal the file size.
- The dump holds the same 60 captures, one row each, and must not be salvaged. Each row holds
  `metadata.capture`, `metadata.frame_binding_sha256` (equal to the manifest's) and
  `metadata.geometry.{K, canvas_to_source, camera_to_world_metric, camera_to_world_unscaled, scale,
  source_indices}`, with source_indices equal to the manifest's.
- The rows carry depth arrays that depth_format.decode can read (schema 1, 32x51x51).
- The parity receipt (5.json beside the dump, or `--parity2`) is optional and used only for
  cross-checks. The row-level `parity` is also optional.
