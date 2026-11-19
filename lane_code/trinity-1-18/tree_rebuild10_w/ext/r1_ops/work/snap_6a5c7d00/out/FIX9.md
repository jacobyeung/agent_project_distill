BUILT. S2 is on; S1 is off; both scheduled-sampling copies keep max_own_probability at zero. The packet remains subject to production admission and independent review.

Config identity: `8246a4dd34bcfb7de1770b62ae7f0f331849714397d66fe68dfda8f8aa676573`.
Run key: `07297df8`.
Archive: `p_082d2d90.tar`.
Archive SHA256: `3401c318e552cf0ba23f691d197b8f022550639693632abeeaa3bf3b08658384`.

All 43 packet tests pass. The five guard copies pass 180 cases (36 per copy). Each accepts only S2=true, S1=false, and both max_own_probability=0. S1 alone, S1+S2, either nonzero sampling copy, S2 off, missing fields and malformed scalar values refuse. The deployed deriver, sealer and embedded proof contain the checked guards. `tools/run_local_checks.py` verifies deterministic packaging and two equal deployment derivations, production-form evidence, every packet test, four-rank D0 identity, and the final S2-on first batch.

All 288 first-batch microsteps pass the native forward/loss path on CPU. The test calls the inherited `Rows.get`, `h1.pose_targets` and `CarrierC1.forward`; the trainer bytes remain unchanged. `h1.py` and `carrier_c1.py` are byte-identical to the H1 kit; `Rows.get` has the identical syntax tree. Each camera fixture retains its own ordered 32-frame labels through the sealed `c1_row` converter. The tests compare every emitted pose label with its source row. Every rank covers all three camera types, absolute distance, bound feet, VQA, pointing and the ordinary pose stream.

| Rank | Microsteps | Camera routing rows | Other routing rows | Camera pose loss range | Other routing pose loss |
|---|---:|---:|---:|---:|---:|
| 0 | 72 | 10 | 6 | 1.281822–1.825822 | 0 |
| 1 | 72 | 10 | 6 | 1.360238–1.904238 | 0 |
| 2 | 72 | 10 | 6 | 1.970815–2.514815 | 0 |
| 3 | 72 | 10 | 6 | 1.242371–1.786371 | 0 |

S2 supervises 40 camera routing rows and masks all 24 other routing rows. The inherited trainer exposes a `pose` component on every row; absent supervision means that component is exactly zero, not that its dictionary key disappears. VQA and pointing also have zero pose loss. The ordinary pose stream retains its existing supervision. Missing camera GT masks supervision; malformed camera GT refuses.

The CPU test uses synthetic pixels, camera GT, pose and pointing fixtures, 128 real VQA targets, and bound feet payloads. It replaces RGB/token encoding at the existing tiny-model boundary. It does not certify production RGB, complete routing membership, or actual production camera GT coverage. These remain production-proof checks.

The OFF identity test uses unchanged D0 bytes, with S1 off, S2 off and both max_own_probability values zero. All four optimizer-state hashes and rank reports match the sealed D0 tree exactly and match the frozen proof-2 evidence. D0 config identity is `3d5040d54094395af16f516ce0ba5d6dd4ebe694d8ffe5feee6ba80bd8285e57`. The local OFF test does not pass through the S2-only deployment gate.

The config delta against `2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d` has 11 leaves: the S2 boolean and ten derived paths/pins. `CONFIG_DIFF9.json` records the exact before/after values below. The run key changes from `78d0a06c` to `07297df8`. The store content hash, Orchard store, mix, cells, 747 bound unit rows, feet dose, frame authorities, trainer tree and routing-selection bytes remain exact. The sampler census is inherited from the frozen packet with explicit provenance; its input policy is unchanged and its first-step plan is executed again by the CPU test.

```json
[
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/v.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/v.json",
    "field": "admission.path"
  },
  {
    "after": "45fc274b9f80d77e80b838dfba75878d2551e58454ef04a78362a32baf535fa3",
    "before": "a42237c5c21d5adb5f8176057810f672c7bbb075f4e15d973ab6d5c5e323d98a",
    "field": "admission.sha256"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/c.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/c.json",
    "field": "code.path"
  },
  {
    "after": true,
    "before": false,
    "field": "h1.routing_pose_targets"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/07297df8",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/78d0a06c",
    "field": "output"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/07297df8",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/78d0a06c",
    "field": "preparation_output"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/r.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/r.json",
    "field": "s1_route_policy.table.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/s.json",
    "field": "s1_routing.catalog.5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/s.json",
    "field": "s1_routing.selection.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/d.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/d.json",
    "field": "streams.vqa.path"
  },
  {
    "after": "ed469fbbc13f31e29cb7d95e276516f69c97aa3f6cae8dc36c02ac7fb1bc5a18",
    "before": "93e920e25fff5397deae1c9b72a7ab1423e3e70960e789a06c66fbdd9ce8d140",
    "field": "streams.vqa.sha256"
  }
]
```

`FIX9.diff` compares tools, tests, configs, current out files, STATUS.md, the trainer tree and proof parent against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_2c67f1f2`. It shows each guard change, including the deployed copies and generated proof. Binary deltas carry SHA256 values. The diff excludes this report, itself and SHA256SUMS to avoid recursion; the final checksum manifest authenticates both FIX9 files. `FROZEN9.local.json` authenticates all 1845 frozen snapshot files. The protected local proof-2 archive retains SHA256 `def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f`. No frozen bytes changed.

Reviewer focus: verify the exact switch conjunction in every deployment boundary, the unchanged H1 target path, the non-camera zero-loss convention, and the local fixture scope. Production preparation, actual RGB/GT coverage, native full selection regeneration and independent review remain pending. This build does not authorize production. All writes stay inside this lane; execution uses CPU only.

The report follows the no-archaeology and summary skills. The frozen comparison is retained because the brief expressly requires it.
