BUILT FOR REVIEW; production admission remains blocked by missing local RGB and source streams. Both packets remove exactly 601 out-of-division VQA rows through one appended pinned REMOVE list. The sealed trainer and its admission predicates, store, division, and inherited filter files retain their bytes.

| Packet | S2 | Config identity | Run key | Archive | Archive SHA256 |
|---|---|---|---|---|---|
| A | True | `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f` | `673bc60f` | `p_69d2930d.tar` | `a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589` |
| B | False | `0647a0df37862199ea4a766875969d28e7fbfc66821ea5f5a0d00f0607452f92` | `13daf33c` | `p_27bfcd1d.tar` | `4343e9a08c7b54c745cd5c20b0393d5d222fb5f929b182fe1a3228ae066b5a1a` |

The new list is `records/n.json`, SHA256 `02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411`. Its opaque deployment name follows the existing extra-file staging path: each bundle contains the list, its manifest pins the bytes, the deriver stages it read-only at the new packet path, and the config appends that exact pin to `remove_files`. The file uses the sealed one-`row_key`-per-line format. `FIX10_OFFENDERS.json` records every QID, type, pool, and dataset/scene after both exclusions and all six inherited lists. No duplicate QIDs remain.

| Pool and question type | Removed |
|---|---:|
| b12_cntapp_gt_v1::first_seen_frame | 91 |
| b12_cntapp_gt_v1::obj_appearance_order | 204 |
| b12_cntapp_gt_v1::object_counting | 173 |
| r1_room_traced::room_size_estimation | 6 |
| vsti_rel_v4::camera_obj_rel_dist_v1 | 21 |
| vsti_rel_v4::camera_obj_rel_dist_v2 | 26 |
| vsti_rel_v4::camera_obj_rel_dist_v3 | 20 |
| vsti_rel_v4::obj_obj_relative_pos_lr | 20 |
| vsti_rel_v4::obj_obj_relative_pos_nf | 18 |
| vsti_rel_v4::obj_obj_relative_pos_ud | 22 |

The full census contains 204,413 rows and admits 203,812. The 173 removed counting questions split into 71 counting-cell rows and 102 totals-cell rows. All affected populations and cells follow; ceilings use floor(4 × eligible / 1000 × 1000) / 1000, and sampler cells use the hundredths floor.

| Family | Old eligible | New eligible | Old cell | New cell | New ceiling |
|---|---:|---:|---:|---:|---:|
| appearance | 27791 | 27587 | 14.42 | 14.42 | 110.348 |
| camera_obj_rel_dist_v1 | 1951 | 1930 | 2.00 | 2.00 | 7.720 |
| camera_obj_rel_dist_v2 | 1983 | 1957 | 2.00 | 2.00 | 7.828 |
| camera_obj_rel_dist_v3 | 1998 | 1978 | 2.00 | 2.00 | 7.912 |
| counting | 11366 | 11295 | 10.87 | 10.87 | 45.180 |
| direction | 49901 | 49901 | 31.17 | 31.19 | 199.604 |
| first_seen | 7076 | 6985 | 2.00 | 2.00 | 27.940 |
| obj_obj_relative_pos_lr | 1998 | 1978 | 2.00 | 2.00 | 7.912 |
| obj_obj_relative_pos_nf | 2000 | 1982 | 2.00 | 2.00 | 7.928 |
| obj_obj_relative_pos_ud | 1996 | 1974 | 2.00 | 2.00 | 7.896 |
| room | 431 | 425 | 1.72 | 1.70 | 1.700 |
| totals | 9303 | 9201 | 3.39 | 3.39 | 36.804 |

Room uses 1.70 at 425 eligible rows. The sealed ordered refill assigns its two-cent reduction to direction, giving 31.19. VQA remains 128.00 per step. Routing requests remain displacement 18.25, movement direction 15.88, rotation 12.53, absolute distance 16.34, feet 1.00, recovery 0; full production routing populations remain unmeasured. Native unit regeneration retains 747 rows (683 feet and 64 inches), with only feet sampled. `FIX10_UNIT_REMOVE_CHECK.json` verifies that the new list matches none of those 747 rows.

The unmodified full-store VQA call fails locally before reaching the division violation because a pinned RGB file is absent: `[Errno 2] No such file or directory: '/data2/k6tk/67/677d27bc9bbb17948540be9f28a76b3bb600401cece15768b93c2b6b628b655c.png'`. This is a local-data limitation, not a production PASS. The supplementary full-store structural regression executes the sealed build with only `common.binding` RGB-byte reads mocked. It raises the exact reported ValueError without the list and builds 203812 rows with it. Every output QID and scene is checked. The test does not read or certify RGB bytes.

| Production prepare entry point | Local result |
|---|---|
| native_prepare | BLOCKED_LOCAL_INPUT: `ValueError: Missing or changed pinned input: /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/7c9f2d84/receipt.json` |
| parent_grounding | BLOCKED_LOCAL_INPUT: `ValueError: Missing or changed pinned input: /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/receipt.json` |
| pointing | BLOCKED_LOCAL_INPUT: `ValueError: Missing or changed pinned input: /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/7c9f2d84/receipt.json` |
| routing_outputs | BLOCKED_LOCAL_INPUT: `ValueError: Missing or changed pinned input: /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/receipt.json` |
| routing_selection_relocation | BLOCKED_LOCAL_INPUT: `ValueError: Missing or changed pinned input: /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/u/eb3429c5/a67a3f6f489031d4.jsonl.gz` |

Local validation reaches native unit regeneration, the full VQA row census, native capped sampler preparation, the 1,000-step/128,000-draw loader audit, and four-rank first-batch forward/loss checks. All 46 tests and `tools/run_local_checks.py` pass for A and B. Each run checks deterministic packaging, two equal fixture deployments, production-form evidence validation, wrong-evidence refusal, and exact D0 optimizer states. First batches use real selected VQA targets with synthetic pixels and auxiliary-stream fixtures. A supervises camera routing poses; B masks every routing pose. The deployment helpers enforce S2=true for A and S2=false for B; both require S1=false and zero own-sampling probability in both schedule copies. No Slurm or Orchard call occurred.

Reviewer checks: verify the REMOVE list against the pinned division and v7 bytes; inspect the 601-row scope, staging pin, room cap and refill; confirm A requires S2 on and B requires S2 off; run complete production preparation with RGB, pointing, pose/model metadata and routing archives. Inspect actual routing populations/caps and first-batch labels there. Independent review and production CPU proof remain required.

`FIX10A.diff` compares current packet tools, tests, configs and evidence against `snap_8246a4dd`; `FIX10B.diff` compares the fallback against `snap_2c67f1f2`. Binary deltas carry SHA256 values. Historical reports/archives absent from the fresh fallback workspace are not treated as deletions. Trainer inventory equality is tested. Existing root archives and frozen snapshot files were not modified. The exact config diffs below are the required reviewer comparisons; retaining them follows the explicit brief.

Packet A: exact config diff.

```json
[
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/v.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/v.json",
    "field": "admission.path"
  },
  {
    "after": "3b3cc53285d5a92449e6b133c2f47dd4ea6b9df1eb83dd8ac60353f859f079fb",
    "before": "45fc274b9f80d77e80b838dfba75878d2551e58454ef04a78362a32baf535fa3",
    "field": "admission.sha256"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/c.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/c.json",
    "field": "code.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/673bc60f",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/07297df8",
    "field": "output"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/673bc60f",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/07297df8",
    "field": "preparation_output"
  },
  {
    "after": [
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl",
        "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl",
        "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl",
        "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"
      },
      {
        "defects": [
          "identity",
          "absent",
          "merged"
        ],
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl",
        "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json",
        "sha256": "02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411"
      }
    ],
    "before": [
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl",
        "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl",
        "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl",
        "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"
      },
      {
        "defects": [
          "identity",
          "absent",
          "merged"
        ],
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl",
        "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "field": "remove_files"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/r.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/r.json",
    "field": "s1_route_policy.table.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/s.json",
    "field": "s1_routing.catalog.5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/s.json",
    "field": "s1_routing.selection.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/d.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/082d2d90/d.json",
    "field": "streams.vqa.path"
  },
  {
    "after": "aaecc9c42cd549ebdf4da6483ffa6de6f580dc1039a2b53457e975cfe5082ebb",
    "before": "ed469fbbc13f31e29cb7d95e276516f69c97aa3f6cae8dc36c02ac7fb1bc5a18",
    "field": "streams.vqa.sha256"
  },
  {
    "after": 3119,
    "before": 3117,
    "field": "type_mix.streams.vqa.cells.direction.cents"
  },
  {
    "after": 170,
    "before": 172,
    "field": "type_mix.streams.vqa.cells.room.cents"
  }
]
```

Packet B: exact config diff.

```json
[
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/v.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/v.json",
    "field": "admission.path"
  },
  {
    "after": "e0692552473ef72e6b48648d04a8426f5cf4cfdf570cb053e3245dd54f827bb8",
    "before": "a42237c5c21d5adb5f8176057810f672c7bbb075f4e15d973ab6d5c5e323d98a",
    "field": "admission.sha256"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/c.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/c.json",
    "field": "code.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/13daf33c",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/78d0a06c",
    "field": "output"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/13daf33c",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/78d0a06c",
    "field": "preparation_output"
  },
  {
    "after": [
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl",
        "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl",
        "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl",
        "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"
      },
      {
        "defects": [
          "identity",
          "absent",
          "merged"
        ],
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl",
        "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/n.json",
        "sha256": "02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411"
      }
    ],
    "before": [
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl",
        "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl",
        "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl",
        "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"
      },
      {
        "defects": [
          "identity",
          "absent",
          "merged"
        ],
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl",
        "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      {
        "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "field": "remove_files"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/r.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/r.json",
    "field": "s1_route_policy.table.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/s.json",
    "field": "s1_routing.catalog.5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/s.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/s.json",
    "field": "s1_routing.selection.path"
  },
  {
    "after": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/27bfcd1d/d.json",
    "before": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/6f8ed106/d.json",
    "field": "streams.vqa.path"
  },
  {
    "after": "294a936b44ff7af8aaa9c1f1d7fbe2fb66a8f59c6fab7f19bcb823ab524c3d5b",
    "before": "93e920e25fff5397deae1c9b72a7ab1423e3e70960e789a06c66fbdd9ce8d140",
    "field": "streams.vqa.sha256"
  },
  {
    "after": 3119,
    "before": 3117,
    "field": "type_mix.streams.vqa.cells.direction.cents"
  },
  {
    "after": 170,
    "before": 172,
    "field": "type_mix.streams.vqa.cells.room.cents"
  }
]
```
