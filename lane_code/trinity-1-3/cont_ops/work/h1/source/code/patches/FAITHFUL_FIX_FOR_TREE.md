# Faithful own-value camera rows

The sealed `student_pilot/carrier_c1_routing.py:443-447` masks every suffix token
following the first own-value response. Its GT-authored explanation and answer
therefore receive no supervision when the head supplies its own camera values.

`faithful_own_rows.patch` adds S1 only. It parses the existing renderer's printed
camera responses, uses the faithful materializer to re-derive the explanation
and answer, and supervises every non-tool suffix token. Refusals retain the GT
batch and record their reason. Ground/gap rows retain GT supervision.

Set `h1.faithful_own_camera_rows=true`; keep the existing sampling gates at
`max_own_probability=0.5` and `force_from_step=1`. The absent/false switch keeps
the sealed path. This patch adds no routing pose loss, stop control or R0 filter.

Run from `/scratch/jjyeung/orch_n30/h1_headsft/kit`:

```sh
bash cpu.sh tests/patch_composition.py
bash cpu.sh tests/faithful_patch_proof.py
bash cpu.sh -m unittest tests.test_trainer tests.test_own_forward -v
bash cpu.sh tests/compare_off.py --b logs/off_faithful.json --out logs/off_faithful_identity.json
```

The composition proof applies S1 and `h1_rest.patch` in both orders with zero
fuzz and compares all six affected files with `tree/`: 3/3 compositions pass.
The standalone S1 proof passes 12 faithful-row checks and one native own-head
forward. The OFF proof compares four full rank plans, including labels, losses
and post-update parameters, against the sealed result. See `BUILD_REPORT.md`.
