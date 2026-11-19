Thirty complete generated records: all 24 large rows and six controls.

## sb_rowLR_54bcfbc102c1f453_q0

```json
{
  "answer": "41.41",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-816fae8c46dde57967738489c828275507287e8dfc4e21da2b916254d8e8ac9e",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d1",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v5d4c9aff2621",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        66,
        132,
        198,
        265,
        331,
        397,
        464,
        530,
        596,
        662,
        729,
        795,
        861,
        928,
        994,
        1060,
        1126,
        1193,
        1259,
        1325,
        1392,
        1458,
        1524,
        1590,
        1657,
        1723,
        1789,
        1856,
        1922,
        1988,
        2055
      ],
      "options": [],
      "qid": "sb_rowLR_54bcfbc102c1f453_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannet/scene0694_01",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0694_01",
    "details": {
      "cell": "scannet|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      66,
      132,
      198,
      265,
      331,
      397,
      464,
      530,
      596,
      662,
      729,
      795,
      861,
      928,
      994,
      1060,
      1126,
      1193,
      1259,
      1325,
      1392,
      1458,
      1524,
      1590,
      1657,
      1723,
      1789,
      1856,
      1922,
      1988,
      2055
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0694_01.npz": "961f97d4bc4364c2522d841a80fee96143038d1e033a997508b0a63f792177a3",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0694",
    "room_measurement": {
      "area_m2": 41.410000000000004,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 16564,
      "floor_height_m": -0.012751661154961097,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 14188
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 25,
          "centroid": [
            4.386447727680206,
            0.8434118181467056,
            1.1283576861023903
          ],
          "footprint": 9.411033972745786,
          "instance_id": 1,
          "label": "mailboxes",
          "pixel_share": 0.5860416666666667
        },
        {
          "best_view": 18,
          "centroid": [
            2.036268949508667,
            2.9984352588653564,
            0.8425085544586182
          ],
          "footprint": 1.9435169812013555,
          "instance_id": 14,
          "label": "table",
          "pixel_share": 0.2766015625
        },
        {
          "best_view": 16,
          "centroid": [
            0.22992461454123259,
            3.2794947624206543,
            1.4512982368469238
          ],
          "footprint": 1.924452331959401,
          "instance_id": 20,
          "label": "whiteboard",
          "pixel_share": 0.0461328125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0694_01.npz",
      "raster_sha256": "961f97d4bc4364c2522d841a80fee96143038d1e033a997508b0a63f792177a3",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.386447727680206,
            0.8434118181467056
          ],
          [
            2.036268949508667,
            2.9984352588653564
          ],
          [
            0.22992461454123259,
            3.2794947624206543
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 0.6708819714976993,
        "projection": 0.6470323933270898,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.817798719481848,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12ct_32e12c27a0e7f5eb08d8a58e",
    "source_row_sha256": "9f3d3be6f4fb9d0f806cc673827f3645c23b903e9e4ccab365306df17c50041c",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_54bcfbc102c1f453_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v5d4c9aff2621",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      66,
      132,
      198,
      265,
      331,
      397,
      464,
      530,
      596,
      662,
      729,
      795,
      861,
      928,
      994,
      1060,
      1126,
      1193,
      1259,
      1325,
      1392,
      1458,
      1524,
      1590,
      1657,
      1723,
      1789,
      1856,
      1922,
      1988,
      2055
    ],
    "frames": [
      {
        "path": "/data2/k6tk/69/693a823f37b0a0d693d53086ecd3ceeb590e73ed8571f5ff2377c250ebcc5959.png",
        "sha256": "693a823f37b0a0d693d53086ecd3ceeb590e73ed8571f5ff2377c250ebcc5959"
      },
      {
        "path": "/data2/k6tk/a6/a6ca04b89bf8f2709e304fb55339ef93eecf79c2fc637ea1607d14e96243babb.png",
        "sha256": "a6ca04b89bf8f2709e304fb55339ef93eecf79c2fc637ea1607d14e96243babb"
      },
      {
        "path": "/data2/k6tk/1e/1e93ecff351e5adf3c7721333fe210cb9e7cd91350cf0bf550c3248029f94065.png",
        "sha256": "1e93ecff351e5adf3c7721333fe210cb9e7cd91350cf0bf550c3248029f94065"
      },
      {
        "path": "/data2/k6tk/21/2104af1b762f501ec2a136ec3c350182de55065c2fe18622d41fb1406f154deb.png",
        "sha256": "2104af1b762f501ec2a136ec3c350182de55065c2fe18622d41fb1406f154deb"
      },
      {
        "path": "/data2/k6tk/69/6999d07535467ea227ca888bed0d9b12ff15a3857574a8ad29cd2113dbe970c7.png",
        "sha256": "6999d07535467ea227ca888bed0d9b12ff15a3857574a8ad29cd2113dbe970c7"
      },
      {
        "path": "/data2/k6tk/77/7722f2aa1870bb6f5771a47419429d812c964cc6329b67cc4239de3327c8cb2d.png",
        "sha256": "7722f2aa1870bb6f5771a47419429d812c964cc6329b67cc4239de3327c8cb2d"
      },
      {
        "path": "/data2/k6tk/2b/2b3ee30ce0669ed71384b16cf9d0f40cb7e45eb21180c7b41150ccc3ea1d58f1.png",
        "sha256": "2b3ee30ce0669ed71384b16cf9d0f40cb7e45eb21180c7b41150ccc3ea1d58f1"
      },
      {
        "path": "/data2/k6tk/d3/d3af6661492b579e19801e36d903a6d857ecf3c251b65b71212755f75fff35b9.png",
        "sha256": "d3af6661492b579e19801e36d903a6d857ecf3c251b65b71212755f75fff35b9"
      },
      {
        "path": "/data2/k6tk/0e/0ecc38542b896838d8e87411bc068942175ade11bdf44511a7faf3c59d4a4c0d.png",
        "sha256": "0ecc38542b896838d8e87411bc068942175ade11bdf44511a7faf3c59d4a4c0d"
      },
      {
        "path": "/data2/k6tk/5b/5bd4877b98aa94bf664a4df9e3e5ecde90cbe3159388373597c7c34f1487df2a.png",
        "sha256": "5bd4877b98aa94bf664a4df9e3e5ecde90cbe3159388373597c7c34f1487df2a"
      },
      {
        "path": "/data2/k6tk/e3/e3867b3e38722e9199acbcdd7719846195aae4dbb8199668f53293b79c8d35f7.png",
        "sha256": "e3867b3e38722e9199acbcdd7719846195aae4dbb8199668f53293b79c8d35f7"
      },
      {
        "path": "/data2/k6tk/5c/5ceb8ea7d6e182475132d2b0e9a9a0b0a8bc298a110236ce6c03bd26d83ce2ca.png",
        "sha256": "5ceb8ea7d6e182475132d2b0e9a9a0b0a8bc298a110236ce6c03bd26d83ce2ca"
      },
      {
        "path": "/data2/k6tk/5b/5b619927f1e05b3f823715833a039738b5b2e76fe373d75e4a9c5acbb0961a91.png",
        "sha256": "5b619927f1e05b3f823715833a039738b5b2e76fe373d75e4a9c5acbb0961a91"
      },
      {
        "path": "/data2/k6tk/cf/cfa84e1b184fd56de79bfc7ea7c109d00dc68cc12cde3ebf8d13e3b2be6a5e56.png",
        "sha256": "cfa84e1b184fd56de79bfc7ea7c109d00dc68cc12cde3ebf8d13e3b2be6a5e56"
      },
      {
        "path": "/data2/k6tk/82/824fcb7fe2a61e100eef1bb86495f3211a3d5b989dfd512dd3118d3b7da14110.png",
        "sha256": "824fcb7fe2a61e100eef1bb86495f3211a3d5b989dfd512dd3118d3b7da14110"
      },
      {
        "path": "/data2/k6tk/43/43e2e9b03a8be5f378dc9836b105209f84bd479dfc8d2c0bd76a634de75d4f47.png",
        "sha256": "43e2e9b03a8be5f378dc9836b105209f84bd479dfc8d2c0bd76a634de75d4f47"
      },
      {
        "path": "/data2/k6tk/c6/c6beb3e95b4f58eb0c21468108bd546ae17bf2a2ed7169a930ba04714dfe5190.png",
        "sha256": "c6beb3e95b4f58eb0c21468108bd546ae17bf2a2ed7169a930ba04714dfe5190"
      },
      {
        "path": "/data2/k6tk/70/70ba1d21f87c1eb59bd57b7ae0cf9105408a2951580c09ff805deefbe2f05664.png",
        "sha256": "70ba1d21f87c1eb59bd57b7ae0cf9105408a2951580c09ff805deefbe2f05664"
      },
      {
        "path": "/data2/k6tk/3b/3bb7a440417fd58a739eead7eade774dfd87b0ce2f911908b08fc7b3655d47d4.png",
        "sha256": "3bb7a440417fd58a739eead7eade774dfd87b0ce2f911908b08fc7b3655d47d4"
      },
      {
        "path": "/data2/k6tk/11/117be6af18423a2c1965e8161de082bd91a3e9d66521c1dc6b7b826eebe32419.png",
        "sha256": "117be6af18423a2c1965e8161de082bd91a3e9d66521c1dc6b7b826eebe32419"
      },
      {
        "path": "/data2/k6tk/79/79f8301ebccbec60fcc7678c9c6ae07698cfd7eff29e98d36b75c51f52614579.png",
        "sha256": "79f8301ebccbec60fcc7678c9c6ae07698cfd7eff29e98d36b75c51f52614579"
      },
      {
        "path": "/data2/k6tk/65/65e78c012269d7d915f4eaf4a1507cebda114899f58d659e7a943b7449dbca1d.png",
        "sha256": "65e78c012269d7d915f4eaf4a1507cebda114899f58d659e7a943b7449dbca1d"
      },
      {
        "path": "/data2/k6tk/6a/6a529c30b57bf4398360607114647be8f8032e3dab021bfcdaf9d43feeb89cfe.png",
        "sha256": "6a529c30b57bf4398360607114647be8f8032e3dab021bfcdaf9d43feeb89cfe"
      },
      {
        "path": "/data2/k6tk/09/0906bcfc1a9d98797bd3ea7ab5778cbbd9e886dd679534646b3b2fce59218a83.png",
        "sha256": "0906bcfc1a9d98797bd3ea7ab5778cbbd9e886dd679534646b3b2fce59218a83"
      },
      {
        "path": "/data2/k6tk/43/439840fa5fcaa118ba2fd0fca917a7789e9925c48194cad01f346bb34af0bc1b.png",
        "sha256": "439840fa5fcaa118ba2fd0fca917a7789e9925c48194cad01f346bb34af0bc1b"
      },
      {
        "path": "/data2/k6tk/ce/ce7849dcccb58d83b8b0a07a38343ea1f1c8fdbbacede21e2d7f09f1a471809a.png",
        "sha256": "ce7849dcccb58d83b8b0a07a38343ea1f1c8fdbbacede21e2d7f09f1a471809a"
      },
      {
        "path": "/data2/k6tk/73/7327fa0228d325dd88ecd17b185f667ad288f1b563115affe759ff3a8a9f4630.png",
        "sha256": "7327fa0228d325dd88ecd17b185f667ad288f1b563115affe759ff3a8a9f4630"
      },
      {
        "path": "/data2/k6tk/e9/e9ad31e264fc01e98b3f2a20c7f57d845c36f6d5bc182e7f182174e621c681b9.png",
        "sha256": "e9ad31e264fc01e98b3f2a20c7f57d845c36f6d5bc182e7f182174e621c681b9"
      },
      {
        "path": "/data2/k6tk/30/300aec5f3008a36be49daf1c2c499527c06236c797695fe1f05994acdcd6bf4c.png",
        "sha256": "300aec5f3008a36be49daf1c2c499527c06236c797695fe1f05994acdcd6bf4c"
      },
      {
        "path": "/data2/k6tk/7a/7a503af1a6ae69c9bde6fc30d4e4f619c56afe6bacd37501e9795e704c26d004.png",
        "sha256": "7a503af1a6ae69c9bde6fc30d4e4f619c56afe6bacd37501e9795e704c26d004"
      },
      {
        "path": "/data2/k6tk/88/882be187203f841414b4d6fb35cd9358fb546854e678490cdd8a172b9bbfcd4a.png",
        "sha256": "882be187203f841414b4d6fb35cd9358fb546854e678490cdd8a172b9bbfcd4a"
      },
      {
        "path": "/data2/k6tk/87/877a9b8cef026f0d8cda0ec064d395f0966bd40ffb5be7a6ad5e154afd8e3d25.png",
        "sha256": "877a9b8cef026f0d8cda0ec064d395f0966bd40ffb5be7a6ad5e154afd8e3d25"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      2.75,
      5.5,
      8.25,
      11.041666666666666,
      13.791666666666666,
      16.541666666666668,
      19.333333333333332,
      22.083333333333332,
      24.833333333333332,
      27.583333333333332,
      30.375,
      33.125,
      35.875,
      38.666666666666664,
      41.416666666666664,
      44.166666666666664,
      46.916666666666664,
      49.708333333333336,
      52.458333333333336,
      55.208333333333336,
      58.0,
      60.75,
      63.5,
      66.25,
      69.04166666666667,
      71.79166666666667,
      74.54166666666667,
      77.33333333333333,
      80.08333333333333,
      82.83333333333333,
      85.625
    ],
    "total_num_frames": 2056
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: mailboxes in frame 25; table in frame 18; whiteboard in frame 16.\nThe mailboxes and the whiteboard are the farthest apart among these landmarks, with the table between them.\n</think>\n\n41.41",
  "validation_commit": ""
}
```

## sb_rowLR_54bcfbc102c1f453_q1

```json
{
  "answer": "41.41",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-36273297cc526721e2f898e1809eadf20aaef64a25736863b295620b07a1bb50",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d1",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v5d4c9aff2621",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        66,
        132,
        198,
        265,
        331,
        397,
        464,
        530,
        596,
        662,
        729,
        795,
        861,
        928,
        994,
        1060,
        1126,
        1193,
        1259,
        1325,
        1392,
        1458,
        1524,
        1590,
        1657,
        1723,
        1789,
        1856,
        1922,
        1988,
        2055
      ],
      "options": [],
      "qid": "sb_rowLR_54bcfbc102c1f453_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannet/scene0694_01",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0694_01",
    "details": {
      "cell": "scannet|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      66,
      132,
      198,
      265,
      331,
      397,
      464,
      530,
      596,
      662,
      729,
      795,
      861,
      928,
      994,
      1060,
      1126,
      1193,
      1259,
      1325,
      1392,
      1458,
      1524,
      1590,
      1657,
      1723,
      1789,
      1856,
      1922,
      1988,
      2055
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0694_01.npz": "961f97d4bc4364c2522d841a80fee96143038d1e033a997508b0a63f792177a3",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0694",
    "room_measurement": {
      "area_m2": 41.410000000000004,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 16564,
      "floor_height_m": -0.012751661154961097,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 14188
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 25,
          "centroid": [
            4.386447727680206,
            0.8434118181467056,
            1.1283576861023903
          ],
          "footprint": 9.411033972745786,
          "instance_id": 1,
          "label": "mailboxes",
          "pixel_share": 0.5860416666666667
        },
        {
          "best_view": 18,
          "centroid": [
            2.036268949508667,
            2.9984352588653564,
            0.8425085544586182
          ],
          "footprint": 1.9435169812013555,
          "instance_id": 14,
          "label": "table",
          "pixel_share": 0.2766015625
        },
        {
          "best_view": 16,
          "centroid": [
            0.22992461454123259,
            3.2794947624206543,
            1.4512982368469238
          ],
          "footprint": 1.924452331959401,
          "instance_id": 20,
          "label": "whiteboard",
          "pixel_share": 0.0461328125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0694_01.npz",
      "raster_sha256": "961f97d4bc4364c2522d841a80fee96143038d1e033a997508b0a63f792177a3",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.386447727680206,
            0.8434118181467056
          ],
          [
            2.036268949508667,
            2.9984352588653564
          ],
          [
            0.22992461454123259,
            3.2794947624206543
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 0.6708819714976993,
        "projection": 0.6470323933270898,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.817798719481848,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_32e12c27a0e7f5eb08d8a58e",
    "source_row_sha256": "9f3d3be6f4fb9d0f806cc673827f3645c23b903e9e4ccab365306df17c50041c",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_54bcfbc102c1f453_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v5d4c9aff2621",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      66,
      132,
      198,
      265,
      331,
      397,
      464,
      530,
      596,
      662,
      729,
      795,
      861,
      928,
      994,
      1060,
      1126,
      1193,
      1259,
      1325,
      1392,
      1458,
      1524,
      1590,
      1657,
      1723,
      1789,
      1856,
      1922,
      1988,
      2055
    ],
    "frames": [
      {
        "path": "/data2/k6tk/69/693a823f37b0a0d693d53086ecd3ceeb590e73ed8571f5ff2377c250ebcc5959.png",
        "sha256": "693a823f37b0a0d693d53086ecd3ceeb590e73ed8571f5ff2377c250ebcc5959"
      },
      {
        "path": "/data2/k6tk/a6/a6ca04b89bf8f2709e304fb55339ef93eecf79c2fc637ea1607d14e96243babb.png",
        "sha256": "a6ca04b89bf8f2709e304fb55339ef93eecf79c2fc637ea1607d14e96243babb"
      },
      {
        "path": "/data2/k6tk/1e/1e93ecff351e5adf3c7721333fe210cb9e7cd91350cf0bf550c3248029f94065.png",
        "sha256": "1e93ecff351e5adf3c7721333fe210cb9e7cd91350cf0bf550c3248029f94065"
      },
      {
        "path": "/data2/k6tk/21/2104af1b762f501ec2a136ec3c350182de55065c2fe18622d41fb1406f154deb.png",
        "sha256": "2104af1b762f501ec2a136ec3c350182de55065c2fe18622d41fb1406f154deb"
      },
      {
        "path": "/data2/k6tk/69/6999d07535467ea227ca888bed0d9b12ff15a3857574a8ad29cd2113dbe970c7.png",
        "sha256": "6999d07535467ea227ca888bed0d9b12ff15a3857574a8ad29cd2113dbe970c7"
      },
      {
        "path": "/data2/k6tk/77/7722f2aa1870bb6f5771a47419429d812c964cc6329b67cc4239de3327c8cb2d.png",
        "sha256": "7722f2aa1870bb6f5771a47419429d812c964cc6329b67cc4239de3327c8cb2d"
      },
      {
        "path": "/data2/k6tk/2b/2b3ee30ce0669ed71384b16cf9d0f40cb7e45eb21180c7b41150ccc3ea1d58f1.png",
        "sha256": "2b3ee30ce0669ed71384b16cf9d0f40cb7e45eb21180c7b41150ccc3ea1d58f1"
      },
      {
        "path": "/data2/k6tk/d3/d3af6661492b579e19801e36d903a6d857ecf3c251b65b71212755f75fff35b9.png",
        "sha256": "d3af6661492b579e19801e36d903a6d857ecf3c251b65b71212755f75fff35b9"
      },
      {
        "path": "/data2/k6tk/0e/0ecc38542b896838d8e87411bc068942175ade11bdf44511a7faf3c59d4a4c0d.png",
        "sha256": "0ecc38542b896838d8e87411bc068942175ade11bdf44511a7faf3c59d4a4c0d"
      },
      {
        "path": "/data2/k6tk/5b/5bd4877b98aa94bf664a4df9e3e5ecde90cbe3159388373597c7c34f1487df2a.png",
        "sha256": "5bd4877b98aa94bf664a4df9e3e5ecde90cbe3159388373597c7c34f1487df2a"
      },
      {
        "path": "/data2/k6tk/e3/e3867b3e38722e9199acbcdd7719846195aae4dbb8199668f53293b79c8d35f7.png",
        "sha256": "e3867b3e38722e9199acbcdd7719846195aae4dbb8199668f53293b79c8d35f7"
      },
      {
        "path": "/data2/k6tk/5c/5ceb8ea7d6e182475132d2b0e9a9a0b0a8bc298a110236ce6c03bd26d83ce2ca.png",
        "sha256": "5ceb8ea7d6e182475132d2b0e9a9a0b0a8bc298a110236ce6c03bd26d83ce2ca"
      },
      {
        "path": "/data2/k6tk/5b/5b619927f1e05b3f823715833a039738b5b2e76fe373d75e4a9c5acbb0961a91.png",
        "sha256": "5b619927f1e05b3f823715833a039738b5b2e76fe373d75e4a9c5acbb0961a91"
      },
      {
        "path": "/data2/k6tk/cf/cfa84e1b184fd56de79bfc7ea7c109d00dc68cc12cde3ebf8d13e3b2be6a5e56.png",
        "sha256": "cfa84e1b184fd56de79bfc7ea7c109d00dc68cc12cde3ebf8d13e3b2be6a5e56"
      },
      {
        "path": "/data2/k6tk/82/824fcb7fe2a61e100eef1bb86495f3211a3d5b989dfd512dd3118d3b7da14110.png",
        "sha256": "824fcb7fe2a61e100eef1bb86495f3211a3d5b989dfd512dd3118d3b7da14110"
      },
      {
        "path": "/data2/k6tk/43/43e2e9b03a8be5f378dc9836b105209f84bd479dfc8d2c0bd76a634de75d4f47.png",
        "sha256": "43e2e9b03a8be5f378dc9836b105209f84bd479dfc8d2c0bd76a634de75d4f47"
      },
      {
        "path": "/data2/k6tk/c6/c6beb3e95b4f58eb0c21468108bd546ae17bf2a2ed7169a930ba04714dfe5190.png",
        "sha256": "c6beb3e95b4f58eb0c21468108bd546ae17bf2a2ed7169a930ba04714dfe5190"
      },
      {
        "path": "/data2/k6tk/70/70ba1d21f87c1eb59bd57b7ae0cf9105408a2951580c09ff805deefbe2f05664.png",
        "sha256": "70ba1d21f87c1eb59bd57b7ae0cf9105408a2951580c09ff805deefbe2f05664"
      },
      {
        "path": "/data2/k6tk/3b/3bb7a440417fd58a739eead7eade774dfd87b0ce2f911908b08fc7b3655d47d4.png",
        "sha256": "3bb7a440417fd58a739eead7eade774dfd87b0ce2f911908b08fc7b3655d47d4"
      },
      {
        "path": "/data2/k6tk/11/117be6af18423a2c1965e8161de082bd91a3e9d66521c1dc6b7b826eebe32419.png",
        "sha256": "117be6af18423a2c1965e8161de082bd91a3e9d66521c1dc6b7b826eebe32419"
      },
      {
        "path": "/data2/k6tk/79/79f8301ebccbec60fcc7678c9c6ae07698cfd7eff29e98d36b75c51f52614579.png",
        "sha256": "79f8301ebccbec60fcc7678c9c6ae07698cfd7eff29e98d36b75c51f52614579"
      },
      {
        "path": "/data2/k6tk/65/65e78c012269d7d915f4eaf4a1507cebda114899f58d659e7a943b7449dbca1d.png",
        "sha256": "65e78c012269d7d915f4eaf4a1507cebda114899f58d659e7a943b7449dbca1d"
      },
      {
        "path": "/data2/k6tk/6a/6a529c30b57bf4398360607114647be8f8032e3dab021bfcdaf9d43feeb89cfe.png",
        "sha256": "6a529c30b57bf4398360607114647be8f8032e3dab021bfcdaf9d43feeb89cfe"
      },
      {
        "path": "/data2/k6tk/09/0906bcfc1a9d98797bd3ea7ab5778cbbd9e886dd679534646b3b2fce59218a83.png",
        "sha256": "0906bcfc1a9d98797bd3ea7ab5778cbbd9e886dd679534646b3b2fce59218a83"
      },
      {
        "path": "/data2/k6tk/43/439840fa5fcaa118ba2fd0fca917a7789e9925c48194cad01f346bb34af0bc1b.png",
        "sha256": "439840fa5fcaa118ba2fd0fca917a7789e9925c48194cad01f346bb34af0bc1b"
      },
      {
        "path": "/data2/k6tk/ce/ce7849dcccb58d83b8b0a07a38343ea1f1c8fdbbacede21e2d7f09f1a471809a.png",
        "sha256": "ce7849dcccb58d83b8b0a07a38343ea1f1c8fdbbacede21e2d7f09f1a471809a"
      },
      {
        "path": "/data2/k6tk/73/7327fa0228d325dd88ecd17b185f667ad288f1b563115affe759ff3a8a9f4630.png",
        "sha256": "7327fa0228d325dd88ecd17b185f667ad288f1b563115affe759ff3a8a9f4630"
      },
      {
        "path": "/data2/k6tk/e9/e9ad31e264fc01e98b3f2a20c7f57d845c36f6d5bc182e7f182174e621c681b9.png",
        "sha256": "e9ad31e264fc01e98b3f2a20c7f57d845c36f6d5bc182e7f182174e621c681b9"
      },
      {
        "path": "/data2/k6tk/30/300aec5f3008a36be49daf1c2c499527c06236c797695fe1f05994acdcd6bf4c.png",
        "sha256": "300aec5f3008a36be49daf1c2c499527c06236c797695fe1f05994acdcd6bf4c"
      },
      {
        "path": "/data2/k6tk/7a/7a503af1a6ae69c9bde6fc30d4e4f619c56afe6bacd37501e9795e704c26d004.png",
        "sha256": "7a503af1a6ae69c9bde6fc30d4e4f619c56afe6bacd37501e9795e704c26d004"
      },
      {
        "path": "/data2/k6tk/88/882be187203f841414b4d6fb35cd9358fb546854e678490cdd8a172b9bbfcd4a.png",
        "sha256": "882be187203f841414b4d6fb35cd9358fb546854e678490cdd8a172b9bbfcd4a"
      },
      {
        "path": "/data2/k6tk/87/877a9b8cef026f0d8cda0ec064d395f0966bd40ffb5be7a6ad5e154afd8e3d25.png",
        "sha256": "877a9b8cef026f0d8cda0ec064d395f0966bd40ffb5be7a6ad5e154afd8e3d25"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      2.75,
      5.5,
      8.25,
      11.041666666666666,
      13.791666666666666,
      16.541666666666668,
      19.333333333333332,
      22.083333333333332,
      24.833333333333332,
      27.583333333333332,
      30.375,
      33.125,
      35.875,
      38.666666666666664,
      41.416666666666664,
      44.166666666666664,
      46.916666666666664,
      49.708333333333336,
      52.458333333333336,
      55.208333333333336,
      58.0,
      60.75,
      63.5,
      66.25,
      69.04166666666667,
      71.79166666666667,
      74.54166666666667,
      77.33333333333333,
      80.08333333333333,
      82.83333333333333,
      85.625
    ],
    "total_num_frames": 2056
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: mailboxes in frame 25; table in frame 18; whiteboard in frame 16.\nOf these, the mailboxes and the whiteboard are farthest apart, with the table between them.\n</think>\n\n41.41",
  "validation_commit": ""
}
```

## sb_rowLR_894e6bce458cf4f8_q0

```json
{
  "answer": "47.95",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-3ee2ee6085bda4d7a8bb8b21f128ec59c23c2fd7c72deec0ec2620c0c5148420",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vb578540859dd",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        324,
        649,
        973,
        1298,
        1622,
        1947,
        2271,
        2596,
        2920,
        3245,
        3569,
        3894,
        4218,
        4543,
        4867,
        5192,
        5516,
        5841,
        6165,
        6490,
        6814,
        7139,
        7463,
        7788,
        8112,
        8437,
        8761,
        9086,
        9410,
        9735,
        10060
      ],
      "options": [],
      "qid": "sb_rowLR_894e6bce458cf4f8_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/469f112e38",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/469f112e38",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      324,
      649,
      973,
      1298,
      1622,
      1947,
      2271,
      2596,
      2920,
      3245,
      3569,
      3894,
      4218,
      4543,
      4867,
      5192,
      5516,
      5841,
      6165,
      6490,
      6814,
      7139,
      7463,
      7788,
      8112,
      8437,
      8761,
      9086,
      9410,
      9735,
      10060
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__469f112e38.npz": "8d86fddf8ec244431f9ca6ac2079587b09a49902a6d3e7f3266d5782d7df4d34",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/469f112e38",
    "room_measurement": {
      "area_m2": 47.95,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 19180,
      "floor_height_m": 0.06917706465212373,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 10550
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 19,
          "centroid": [
            4.266610229525998,
            5.444207362030484,
            1.1658108948984587
          ],
          "footprint": 0.49111145857293376,
          "instance_id": 102,
          "label": "bed frame",
          "pixel_share": 0.12765625
        },
        {
          "best_view": 13,
          "centroid": [
            1.3249835179558485,
            6.050217127305748,
            0.5742144286632539
          ],
          "footprint": 0.34992748720818295,
          "instance_id": 104,
          "label": "table",
          "pixel_share": 0.027890625
        },
        {
          "best_view": 23,
          "centroid": [
            5.760232532006663,
            3.611519824276369,
            1.3547698563001476
          ],
          "footprint": 0.18254354439034004,
          "instance_id": 202,
          "label": "curtain",
          "pixel_share": 0.2023828125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__469f112e38.npz",
      "raster_sha256": "8d86fddf8ec244431f9ca6ac2079587b09a49902a6d3e7f3266d5782d7df4d34",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.266610229525998,
            5.444207362030484
          ],
          [
            1.3249835179558485,
            6.050217127305748
          ],
          [
            5.760232532006663,
            3.611519824276369
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.8862870711276422,
        "projection": 0.5669582619588601,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.0614897364749725,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12cs_5346a97e13d7d8186b181278",
    "source_row_sha256": "d0e33b88ad36c2c0698d68ef09dfa8f4e8b876940aac49f3c867cbe606aa5450",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_894e6bce458cf4f8_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vb578540859dd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      324,
      649,
      973,
      1298,
      1622,
      1947,
      2271,
      2596,
      2920,
      3245,
      3569,
      3894,
      4218,
      4543,
      4867,
      5192,
      5516,
      5841,
      6165,
      6490,
      6814,
      7139,
      7463,
      7788,
      8112,
      8437,
      8761,
      9086,
      9410,
      9735,
      10060
    ],
    "frames": [
      {
        "path": "/data2/k6tk/90/9036aec663a042887eac8eae640053dcee0db0636211ca0f1d88a3e089103d19.png",
        "sha256": "9036aec663a042887eac8eae640053dcee0db0636211ca0f1d88a3e089103d19"
      },
      {
        "path": "/data2/k6tk/32/3210f60b9f78b148f8fb31d2958f48bc0f59e276bdab3a0fe313dc4ce347ec99.png",
        "sha256": "3210f60b9f78b148f8fb31d2958f48bc0f59e276bdab3a0fe313dc4ce347ec99"
      },
      {
        "path": "/data2/k6tk/08/087646a1f29980bec221ca981ee8c1c661341dd7347a0c672d39ea21cdc03e7f.png",
        "sha256": "087646a1f29980bec221ca981ee8c1c661341dd7347a0c672d39ea21cdc03e7f"
      },
      {
        "path": "/data2/k6tk/57/57f55db6270fdf830cd590596f6758dd776faef1cf5a8a38786f33cbdf0f4a28.png",
        "sha256": "57f55db6270fdf830cd590596f6758dd776faef1cf5a8a38786f33cbdf0f4a28"
      },
      {
        "path": "/data2/k6tk/e7/e73e74c21aa10f0865364c71e508818054ec1b00242e3c5487b6bc57de42425d.png",
        "sha256": "e73e74c21aa10f0865364c71e508818054ec1b00242e3c5487b6bc57de42425d"
      },
      {
        "path": "/data2/k6tk/f4/f45d2eb8b0241166371f5739e4c8ec43f6fd4683d78a49fcb06aefc2a6dc9a68.png",
        "sha256": "f45d2eb8b0241166371f5739e4c8ec43f6fd4683d78a49fcb06aefc2a6dc9a68"
      },
      {
        "path": "/data2/k6tk/3d/3db565272ff785e3411aaa58d69ad3d8175c29223cb426b6c3b616113371270d.png",
        "sha256": "3db565272ff785e3411aaa58d69ad3d8175c29223cb426b6c3b616113371270d"
      },
      {
        "path": "/data2/k6tk/00/005ef92f071b2ed49a88b876fd06c08c2c8cfb68737cedada3bc83649333f567.png",
        "sha256": "005ef92f071b2ed49a88b876fd06c08c2c8cfb68737cedada3bc83649333f567"
      },
      {
        "path": "/data2/k6tk/e0/e00d2229dd2757c379265009f8bd15f79e92b1143d5e2d2ef5f9ab779a281c79.png",
        "sha256": "e00d2229dd2757c379265009f8bd15f79e92b1143d5e2d2ef5f9ab779a281c79"
      },
      {
        "path": "/data2/k6tk/b3/b34de490056f31d16480f48ed3a04d91328ef977fe8d12d207dc50b512d614af.png",
        "sha256": "b34de490056f31d16480f48ed3a04d91328ef977fe8d12d207dc50b512d614af"
      },
      {
        "path": "/data2/k6tk/34/349d34e8eda00ca0cac3d66b0847919ccb9d3a04629b6786ca2196f86ba8ece9.png",
        "sha256": "349d34e8eda00ca0cac3d66b0847919ccb9d3a04629b6786ca2196f86ba8ece9"
      },
      {
        "path": "/data2/k6tk/b8/b8a225cab00e3eb30ddf87efb0a086e45b885c960a8ab4495f5019b8e8ed865d.png",
        "sha256": "b8a225cab00e3eb30ddf87efb0a086e45b885c960a8ab4495f5019b8e8ed865d"
      },
      {
        "path": "/data2/k6tk/fa/fa8b440ca849d918f6a7bd530acab2ccbeaddc4193737533638b0a754091aee8.png",
        "sha256": "fa8b440ca849d918f6a7bd530acab2ccbeaddc4193737533638b0a754091aee8"
      },
      {
        "path": "/data2/k6tk/2d/2d0580a86b31dcd6ac949040fedf9811bd684399128eb8b1aaf514e5dc403c9e.png",
        "sha256": "2d0580a86b31dcd6ac949040fedf9811bd684399128eb8b1aaf514e5dc403c9e"
      },
      {
        "path": "/data2/k6tk/09/09096cb0d694f8a509d9714aa010adbf080a143145cb19bf2b575aa917cd1ca2.png",
        "sha256": "09096cb0d694f8a509d9714aa010adbf080a143145cb19bf2b575aa917cd1ca2"
      },
      {
        "path": "/data2/k6tk/b1/b1b6eed0267b057d592a3024eb466439290b6fb1ec395fa6adaa9b45edf1680c.png",
        "sha256": "b1b6eed0267b057d592a3024eb466439290b6fb1ec395fa6adaa9b45edf1680c"
      },
      {
        "path": "/data2/k6tk/1b/1bbcff4e9fc4fc38c74342590a323bdd62924ecad40ffa9cf26b9b09f37187a0.png",
        "sha256": "1bbcff4e9fc4fc38c74342590a323bdd62924ecad40ffa9cf26b9b09f37187a0"
      },
      {
        "path": "/data2/k6tk/72/725a3444d7649d6116b43317bd2bdb21690fd61f26ac8b317e82f838a8737d18.png",
        "sha256": "725a3444d7649d6116b43317bd2bdb21690fd61f26ac8b317e82f838a8737d18"
      },
      {
        "path": "/data2/k6tk/4b/4baefa4e53e6fee8a0b3ba51014512b84a694d6f5520a9cb2d626fccf8531400.png",
        "sha256": "4baefa4e53e6fee8a0b3ba51014512b84a694d6f5520a9cb2d626fccf8531400"
      },
      {
        "path": "/data2/k6tk/d0/d0f1d19eca4b7694579b585166ebfbab4b91063f656e7c77389a65c93b3aeb9c.png",
        "sha256": "d0f1d19eca4b7694579b585166ebfbab4b91063f656e7c77389a65c93b3aeb9c"
      },
      {
        "path": "/data2/k6tk/88/8850044214f6f6e60375101adc3e44990cab119fc8ded3e09d7581062223b0d0.png",
        "sha256": "8850044214f6f6e60375101adc3e44990cab119fc8ded3e09d7581062223b0d0"
      },
      {
        "path": "/data2/k6tk/62/6281b285e1d4462cc079c24a3dd5b5375956488b5aa190d736ad871044508e25.png",
        "sha256": "6281b285e1d4462cc079c24a3dd5b5375956488b5aa190d736ad871044508e25"
      },
      {
        "path": "/data2/k6tk/a5/a5a3e8276268dd678bbba67fddcdeddf9b69a9253668b9af1d605959d8d68ce3.png",
        "sha256": "a5a3e8276268dd678bbba67fddcdeddf9b69a9253668b9af1d605959d8d68ce3"
      },
      {
        "path": "/data2/k6tk/22/22872b08d737d4f94415132297ea9adc7096cbe1cf45ccacdefec57fcc781a90.png",
        "sha256": "22872b08d737d4f94415132297ea9adc7096cbe1cf45ccacdefec57fcc781a90"
      },
      {
        "path": "/data2/k6tk/1f/1f86d5d6c70de138e748f6d0dfa2f7c436947ad8a056c29e4185cda18c9841e7.png",
        "sha256": "1f86d5d6c70de138e748f6d0dfa2f7c436947ad8a056c29e4185cda18c9841e7"
      },
      {
        "path": "/data2/k6tk/5c/5cbf9e3d16f5c95d7fadd96a68db48803c3fa0d401cff0cb613b287ee38ba28e.png",
        "sha256": "5cbf9e3d16f5c95d7fadd96a68db48803c3fa0d401cff0cb613b287ee38ba28e"
      },
      {
        "path": "/data2/k6tk/10/10883403ae4f987db3f53784c57fd00cd7b278487a3548d1f03d40ca02e22f1b.png",
        "sha256": "10883403ae4f987db3f53784c57fd00cd7b278487a3548d1f03d40ca02e22f1b"
      },
      {
        "path": "/data2/k6tk/fb/fb32d2257e9e7eba3387c1ef19865e99de70da7e1bbc23a51d7d4459960c0072.png",
        "sha256": "fb32d2257e9e7eba3387c1ef19865e99de70da7e1bbc23a51d7d4459960c0072"
      },
      {
        "path": "/data2/k6tk/89/8953eeb56a9b81bb41a12ebaf9006a54ee9d00254be0a49a7a0e2d172ae191ec.png",
        "sha256": "8953eeb56a9b81bb41a12ebaf9006a54ee9d00254be0a49a7a0e2d172ae191ec"
      },
      {
        "path": "/data2/k6tk/49/49bd8fdcc0e2bd4cae40df646ba9f342b31d1dd9ba3031edd44aa98462301804.png",
        "sha256": "49bd8fdcc0e2bd4cae40df646ba9f342b31d1dd9ba3031edd44aa98462301804"
      },
      {
        "path": "/data2/k6tk/07/07e6134ecdeb3fe1e07313b73ebcf55bd2702b2e07bcc9d24057af238d3ad434.png",
        "sha256": "07e6134ecdeb3fe1e07313b73ebcf55bd2702b2e07bcc9d24057af238d3ad434"
      },
      {
        "path": "/data2/k6tk/f6/f6f4154420e986b0a593d36e96103b7ae6389949f88a27d7ba00c90671b36056.png",
        "sha256": "f6f4154420e986b0a593d36e96103b7ae6389949f88a27d7ba00c90671b36056"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.4,
      10.816666666666666,
      16.216666666666665,
      21.633333333333333,
      27.033333333333335,
      32.45,
      37.85,
      43.266666666666666,
      48.666666666666664,
      54.083333333333336,
      59.483333333333334,
      64.9,
      70.3,
      75.71666666666667,
      81.11666666666666,
      86.53333333333333,
      91.93333333333334,
      97.35,
      102.75,
      108.16666666666667,
      113.56666666666666,
      118.98333333333333,
      124.38333333333334,
      129.8,
      135.2,
      140.61666666666667,
      146.01666666666668,
      151.43333333333334,
      156.83333333333334,
      162.25,
      167.66666666666666
    ],
    "total_num_frames": 10061
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: bed frame in frame 19; table in frame 13; curtain in frame 23.\nOf these, the table and the curtain are farthest apart, with the bed frame between them.\n</think>\n\n47.95",
  "validation_commit": ""
}
```

## sb_rowLR_894e6bce458cf4f8_q1

```json
{
  "answer": "47.95",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-b82ad3fc9ea5e59fc0a91ac703687e51f60846c0432e8649091d73e4fbe43713",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vb578540859dd",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        324,
        649,
        973,
        1298,
        1622,
        1947,
        2271,
        2596,
        2920,
        3245,
        3569,
        3894,
        4218,
        4543,
        4867,
        5192,
        5516,
        5841,
        6165,
        6490,
        6814,
        7139,
        7463,
        7788,
        8112,
        8437,
        8761,
        9086,
        9410,
        9735,
        10060
      ],
      "options": [],
      "qid": "sb_rowLR_894e6bce458cf4f8_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/469f112e38",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/469f112e38",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      324,
      649,
      973,
      1298,
      1622,
      1947,
      2271,
      2596,
      2920,
      3245,
      3569,
      3894,
      4218,
      4543,
      4867,
      5192,
      5516,
      5841,
      6165,
      6490,
      6814,
      7139,
      7463,
      7788,
      8112,
      8437,
      8761,
      9086,
      9410,
      9735,
      10060
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__469f112e38.npz": "8d86fddf8ec244431f9ca6ac2079587b09a49902a6d3e7f3266d5782d7df4d34",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/469f112e38",
    "room_measurement": {
      "area_m2": 47.95,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 19180,
      "floor_height_m": 0.06917706465212373,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 10550
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 19,
          "centroid": [
            4.266610229525998,
            5.444207362030484,
            1.1658108948984587
          ],
          "footprint": 0.49111145857293376,
          "instance_id": 102,
          "label": "bed frame",
          "pixel_share": 0.12765625
        },
        {
          "best_view": 13,
          "centroid": [
            1.3249835179558485,
            6.050217127305748,
            0.5742144286632539
          ],
          "footprint": 0.34992748720818295,
          "instance_id": 104,
          "label": "table",
          "pixel_share": 0.027890625
        },
        {
          "best_view": 23,
          "centroid": [
            5.760232532006663,
            3.611519824276369,
            1.3547698563001476
          ],
          "footprint": 0.18254354439034004,
          "instance_id": 202,
          "label": "curtain",
          "pixel_share": 0.2023828125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__469f112e38.npz",
      "raster_sha256": "8d86fddf8ec244431f9ca6ac2079587b09a49902a6d3e7f3266d5782d7df4d34",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.266610229525998,
            5.444207362030484
          ],
          [
            1.3249835179558485,
            6.050217127305748
          ],
          [
            5.760232532006663,
            3.611519824276369
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.8862870711276422,
        "projection": 0.5669582619588601,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.0614897364749725,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12cs_5346a97e13d7d8186b181278",
    "source_row_sha256": "d0e33b88ad36c2c0698d68ef09dfa8f4e8b876940aac49f3c867cbe606aa5450",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_894e6bce458cf4f8_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vb578540859dd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      324,
      649,
      973,
      1298,
      1622,
      1947,
      2271,
      2596,
      2920,
      3245,
      3569,
      3894,
      4218,
      4543,
      4867,
      5192,
      5516,
      5841,
      6165,
      6490,
      6814,
      7139,
      7463,
      7788,
      8112,
      8437,
      8761,
      9086,
      9410,
      9735,
      10060
    ],
    "frames": [
      {
        "path": "/data2/k6tk/90/9036aec663a042887eac8eae640053dcee0db0636211ca0f1d88a3e089103d19.png",
        "sha256": "9036aec663a042887eac8eae640053dcee0db0636211ca0f1d88a3e089103d19"
      },
      {
        "path": "/data2/k6tk/32/3210f60b9f78b148f8fb31d2958f48bc0f59e276bdab3a0fe313dc4ce347ec99.png",
        "sha256": "3210f60b9f78b148f8fb31d2958f48bc0f59e276bdab3a0fe313dc4ce347ec99"
      },
      {
        "path": "/data2/k6tk/08/087646a1f29980bec221ca981ee8c1c661341dd7347a0c672d39ea21cdc03e7f.png",
        "sha256": "087646a1f29980bec221ca981ee8c1c661341dd7347a0c672d39ea21cdc03e7f"
      },
      {
        "path": "/data2/k6tk/57/57f55db6270fdf830cd590596f6758dd776faef1cf5a8a38786f33cbdf0f4a28.png",
        "sha256": "57f55db6270fdf830cd590596f6758dd776faef1cf5a8a38786f33cbdf0f4a28"
      },
      {
        "path": "/data2/k6tk/e7/e73e74c21aa10f0865364c71e508818054ec1b00242e3c5487b6bc57de42425d.png",
        "sha256": "e73e74c21aa10f0865364c71e508818054ec1b00242e3c5487b6bc57de42425d"
      },
      {
        "path": "/data2/k6tk/f4/f45d2eb8b0241166371f5739e4c8ec43f6fd4683d78a49fcb06aefc2a6dc9a68.png",
        "sha256": "f45d2eb8b0241166371f5739e4c8ec43f6fd4683d78a49fcb06aefc2a6dc9a68"
      },
      {
        "path": "/data2/k6tk/3d/3db565272ff785e3411aaa58d69ad3d8175c29223cb426b6c3b616113371270d.png",
        "sha256": "3db565272ff785e3411aaa58d69ad3d8175c29223cb426b6c3b616113371270d"
      },
      {
        "path": "/data2/k6tk/00/005ef92f071b2ed49a88b876fd06c08c2c8cfb68737cedada3bc83649333f567.png",
        "sha256": "005ef92f071b2ed49a88b876fd06c08c2c8cfb68737cedada3bc83649333f567"
      },
      {
        "path": "/data2/k6tk/e0/e00d2229dd2757c379265009f8bd15f79e92b1143d5e2d2ef5f9ab779a281c79.png",
        "sha256": "e00d2229dd2757c379265009f8bd15f79e92b1143d5e2d2ef5f9ab779a281c79"
      },
      {
        "path": "/data2/k6tk/b3/b34de490056f31d16480f48ed3a04d91328ef977fe8d12d207dc50b512d614af.png",
        "sha256": "b34de490056f31d16480f48ed3a04d91328ef977fe8d12d207dc50b512d614af"
      },
      {
        "path": "/data2/k6tk/34/349d34e8eda00ca0cac3d66b0847919ccb9d3a04629b6786ca2196f86ba8ece9.png",
        "sha256": "349d34e8eda00ca0cac3d66b0847919ccb9d3a04629b6786ca2196f86ba8ece9"
      },
      {
        "path": "/data2/k6tk/b8/b8a225cab00e3eb30ddf87efb0a086e45b885c960a8ab4495f5019b8e8ed865d.png",
        "sha256": "b8a225cab00e3eb30ddf87efb0a086e45b885c960a8ab4495f5019b8e8ed865d"
      },
      {
        "path": "/data2/k6tk/fa/fa8b440ca849d918f6a7bd530acab2ccbeaddc4193737533638b0a754091aee8.png",
        "sha256": "fa8b440ca849d918f6a7bd530acab2ccbeaddc4193737533638b0a754091aee8"
      },
      {
        "path": "/data2/k6tk/2d/2d0580a86b31dcd6ac949040fedf9811bd684399128eb8b1aaf514e5dc403c9e.png",
        "sha256": "2d0580a86b31dcd6ac949040fedf9811bd684399128eb8b1aaf514e5dc403c9e"
      },
      {
        "path": "/data2/k6tk/09/09096cb0d694f8a509d9714aa010adbf080a143145cb19bf2b575aa917cd1ca2.png",
        "sha256": "09096cb0d694f8a509d9714aa010adbf080a143145cb19bf2b575aa917cd1ca2"
      },
      {
        "path": "/data2/k6tk/b1/b1b6eed0267b057d592a3024eb466439290b6fb1ec395fa6adaa9b45edf1680c.png",
        "sha256": "b1b6eed0267b057d592a3024eb466439290b6fb1ec395fa6adaa9b45edf1680c"
      },
      {
        "path": "/data2/k6tk/1b/1bbcff4e9fc4fc38c74342590a323bdd62924ecad40ffa9cf26b9b09f37187a0.png",
        "sha256": "1bbcff4e9fc4fc38c74342590a323bdd62924ecad40ffa9cf26b9b09f37187a0"
      },
      {
        "path": "/data2/k6tk/72/725a3444d7649d6116b43317bd2bdb21690fd61f26ac8b317e82f838a8737d18.png",
        "sha256": "725a3444d7649d6116b43317bd2bdb21690fd61f26ac8b317e82f838a8737d18"
      },
      {
        "path": "/data2/k6tk/4b/4baefa4e53e6fee8a0b3ba51014512b84a694d6f5520a9cb2d626fccf8531400.png",
        "sha256": "4baefa4e53e6fee8a0b3ba51014512b84a694d6f5520a9cb2d626fccf8531400"
      },
      {
        "path": "/data2/k6tk/d0/d0f1d19eca4b7694579b585166ebfbab4b91063f656e7c77389a65c93b3aeb9c.png",
        "sha256": "d0f1d19eca4b7694579b585166ebfbab4b91063f656e7c77389a65c93b3aeb9c"
      },
      {
        "path": "/data2/k6tk/88/8850044214f6f6e60375101adc3e44990cab119fc8ded3e09d7581062223b0d0.png",
        "sha256": "8850044214f6f6e60375101adc3e44990cab119fc8ded3e09d7581062223b0d0"
      },
      {
        "path": "/data2/k6tk/62/6281b285e1d4462cc079c24a3dd5b5375956488b5aa190d736ad871044508e25.png",
        "sha256": "6281b285e1d4462cc079c24a3dd5b5375956488b5aa190d736ad871044508e25"
      },
      {
        "path": "/data2/k6tk/a5/a5a3e8276268dd678bbba67fddcdeddf9b69a9253668b9af1d605959d8d68ce3.png",
        "sha256": "a5a3e8276268dd678bbba67fddcdeddf9b69a9253668b9af1d605959d8d68ce3"
      },
      {
        "path": "/data2/k6tk/22/22872b08d737d4f94415132297ea9adc7096cbe1cf45ccacdefec57fcc781a90.png",
        "sha256": "22872b08d737d4f94415132297ea9adc7096cbe1cf45ccacdefec57fcc781a90"
      },
      {
        "path": "/data2/k6tk/1f/1f86d5d6c70de138e748f6d0dfa2f7c436947ad8a056c29e4185cda18c9841e7.png",
        "sha256": "1f86d5d6c70de138e748f6d0dfa2f7c436947ad8a056c29e4185cda18c9841e7"
      },
      {
        "path": "/data2/k6tk/5c/5cbf9e3d16f5c95d7fadd96a68db48803c3fa0d401cff0cb613b287ee38ba28e.png",
        "sha256": "5cbf9e3d16f5c95d7fadd96a68db48803c3fa0d401cff0cb613b287ee38ba28e"
      },
      {
        "path": "/data2/k6tk/10/10883403ae4f987db3f53784c57fd00cd7b278487a3548d1f03d40ca02e22f1b.png",
        "sha256": "10883403ae4f987db3f53784c57fd00cd7b278487a3548d1f03d40ca02e22f1b"
      },
      {
        "path": "/data2/k6tk/fb/fb32d2257e9e7eba3387c1ef19865e99de70da7e1bbc23a51d7d4459960c0072.png",
        "sha256": "fb32d2257e9e7eba3387c1ef19865e99de70da7e1bbc23a51d7d4459960c0072"
      },
      {
        "path": "/data2/k6tk/89/8953eeb56a9b81bb41a12ebaf9006a54ee9d00254be0a49a7a0e2d172ae191ec.png",
        "sha256": "8953eeb56a9b81bb41a12ebaf9006a54ee9d00254be0a49a7a0e2d172ae191ec"
      },
      {
        "path": "/data2/k6tk/49/49bd8fdcc0e2bd4cae40df646ba9f342b31d1dd9ba3031edd44aa98462301804.png",
        "sha256": "49bd8fdcc0e2bd4cae40df646ba9f342b31d1dd9ba3031edd44aa98462301804"
      },
      {
        "path": "/data2/k6tk/07/07e6134ecdeb3fe1e07313b73ebcf55bd2702b2e07bcc9d24057af238d3ad434.png",
        "sha256": "07e6134ecdeb3fe1e07313b73ebcf55bd2702b2e07bcc9d24057af238d3ad434"
      },
      {
        "path": "/data2/k6tk/f6/f6f4154420e986b0a593d36e96103b7ae6389949f88a27d7ba00c90671b36056.png",
        "sha256": "f6f4154420e986b0a593d36e96103b7ae6389949f88a27d7ba00c90671b36056"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      5.4,
      10.816666666666666,
      16.216666666666665,
      21.633333333333333,
      27.033333333333335,
      32.45,
      37.85,
      43.266666666666666,
      48.666666666666664,
      54.083333333333336,
      59.483333333333334,
      64.9,
      70.3,
      75.71666666666667,
      81.11666666666666,
      86.53333333333333,
      91.93333333333334,
      97.35,
      102.75,
      108.16666666666667,
      113.56666666666666,
      118.98333333333333,
      124.38333333333334,
      129.8,
      135.2,
      140.61666666666667,
      146.01666666666668,
      151.43333333333334,
      156.83333333333334,
      162.25,
      167.66666666666666
    ],
    "total_num_frames": 10061
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: bed frame in frame 19; table in frame 13; curtain in frame 23.\nThe table and the curtain are the farthest apart among these landmarks, with the bed frame between them.\n</think>\n\n47.95",
  "validation_commit": ""
}
```

## sb_rowLR_4d432628e44ff231_q0

```json
{
  "answer": "45.66",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-a66f4a0abaa47a2f591ba2a7113944ddaf19cbc89bd6d7eaa9b4658a69142671",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v75b40392ada3",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        266,
        533,
        800,
        1067,
        1334,
        1601,
        1868,
        2135,
        2402,
        2669,
        2936,
        3203,
        3470,
        3737,
        4004,
        4270,
        4537,
        4804,
        5071,
        5338,
        5605,
        5872,
        6139,
        6406,
        6673,
        6940,
        7207,
        7474,
        7741,
        8008,
        8275
      ],
      "options": [],
      "qid": "sb_rowLR_4d432628e44ff231_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/036bce3393",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/036bce3393",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      266,
      533,
      800,
      1067,
      1334,
      1601,
      1868,
      2135,
      2402,
      2669,
      2936,
      3203,
      3470,
      3737,
      4004,
      4270,
      4537,
      4804,
      5071,
      5338,
      5605,
      5872,
      6139,
      6406,
      6673,
      6940,
      7207,
      7474,
      7741,
      8008,
      8275
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__036bce3393.npz": "ea4c864e410b72e7163ecaeb4ed47246c82b561ef157bab6d00bc941fb4f2cfc",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/036bce3393",
    "room_measurement": {
      "area_m2": 45.657500000000006,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 18263,
      "floor_height_m": 0.02103545676881753,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 15078
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            4.4839597450143325,
            3.850429213211479,
            2.9076585769653325
          ],
          "footprint": 9.276261655271414,
          "instance_id": 18,
          "label": "pipe",
          "pixel_share": 0.06338541666666667
        },
        {
          "best_view": 4,
          "centroid": [
            2.8053230019378432,
            2.726579234325177,
            0.579362452030182
          ],
          "footprint": 1.2248963528125711,
          "instance_id": 3,
          "label": "sofa",
          "pixel_share": 0.29359375
        },
        {
          "best_view": 1,
          "centroid": [
            7.569598187968429,
            2.6467943581458213,
            1.2623789943754675
          ],
          "footprint": 1.182764142976193,
          "instance_id": 45,
          "label": "cabinet",
          "pixel_share": 0.23458333333333334
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__036bce3393.npz",
      "raster_sha256": "ea4c864e410b72e7163ecaeb4ed47246c82b561ef157bab6d00bc941fb4f2cfc",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.4839597450143325,
            3.850429213211479
          ],
          [
            2.8053230019378432,
            2.726579234325177
          ],
          [
            7.569598187968429,
            2.6467943581458213
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 1.1517997517558076,
        "projection": 0.348290302709781,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.764943197425729,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12cs_209b69b0dfac46731f873720",
    "source_row_sha256": "64e7faf1dc6d778ee0a5613130274028686e5e316b916db87774928197845433",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_4d432628e44ff231_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v75b40392ada3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      266,
      533,
      800,
      1067,
      1334,
      1601,
      1868,
      2135,
      2402,
      2669,
      2936,
      3203,
      3470,
      3737,
      4004,
      4270,
      4537,
      4804,
      5071,
      5338,
      5605,
      5872,
      6139,
      6406,
      6673,
      6940,
      7207,
      7474,
      7741,
      8008,
      8275
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ff/ffea902cfebef130f1beccfa5c7d0b2ed56f06fdcd04c55ffc76bcef99479794.png",
        "sha256": "ffea902cfebef130f1beccfa5c7d0b2ed56f06fdcd04c55ffc76bcef99479794"
      },
      {
        "path": "/data2/k6tk/d3/d3b3e721a04b7e6b2bef3edd0675b2d8f8076227497a1b11d19bdde91c707f77.png",
        "sha256": "d3b3e721a04b7e6b2bef3edd0675b2d8f8076227497a1b11d19bdde91c707f77"
      },
      {
        "path": "/data2/k6tk/11/11b896fce202da0b427fe814a30a3dcfa58ac55533466508ca9a407e465d7079.png",
        "sha256": "11b896fce202da0b427fe814a30a3dcfa58ac55533466508ca9a407e465d7079"
      },
      {
        "path": "/data2/k6tk/93/93cbf079976776151f25c41c0c260d58dda1f63dfda4dfbbb2d475832bddf8bf.png",
        "sha256": "93cbf079976776151f25c41c0c260d58dda1f63dfda4dfbbb2d475832bddf8bf"
      },
      {
        "path": "/data2/k6tk/51/510ebbb4e11fe7b33d7189b8594c384f9848ac8ef334df3583dda6cd19445110.png",
        "sha256": "510ebbb4e11fe7b33d7189b8594c384f9848ac8ef334df3583dda6cd19445110"
      },
      {
        "path": "/data2/k6tk/cd/cd348a526b8a2ee50da196810363e8a20f345cebd3b0b9bd62dcb21d8d63318e.png",
        "sha256": "cd348a526b8a2ee50da196810363e8a20f345cebd3b0b9bd62dcb21d8d63318e"
      },
      {
        "path": "/data2/k6tk/ee/ee248edfe71364ed6c0888be2f90c19e57814b5f47051e3f3bd22276182b7bd1.png",
        "sha256": "ee248edfe71364ed6c0888be2f90c19e57814b5f47051e3f3bd22276182b7bd1"
      },
      {
        "path": "/data2/k6tk/df/dfc4bdd1067c70d9c86d4cabc9cf58622cf34af62ee14d5fec7ec72f4ae7b534.png",
        "sha256": "dfc4bdd1067c70d9c86d4cabc9cf58622cf34af62ee14d5fec7ec72f4ae7b534"
      },
      {
        "path": "/data2/k6tk/d6/d6cffc26c6158e0788fe46fc6d077f87fd7a3ad00756b84a6a43c7c2ff2ab80a.png",
        "sha256": "d6cffc26c6158e0788fe46fc6d077f87fd7a3ad00756b84a6a43c7c2ff2ab80a"
      },
      {
        "path": "/data2/k6tk/23/23c6c96060c9faeca1678f36397dc181912946bacb88e0d8f4ffd4c92137b3e6.png",
        "sha256": "23c6c96060c9faeca1678f36397dc181912946bacb88e0d8f4ffd4c92137b3e6"
      },
      {
        "path": "/data2/k6tk/72/7248d6b2bed6a03b850abd6f35143d22da6b73f1139d806922f67099b82abc03.png",
        "sha256": "7248d6b2bed6a03b850abd6f35143d22da6b73f1139d806922f67099b82abc03"
      },
      {
        "path": "/data2/k6tk/59/59644418d9ee53745cfaf177829526171d6b3bf8cab22797fd7c67740cd5b9a9.png",
        "sha256": "59644418d9ee53745cfaf177829526171d6b3bf8cab22797fd7c67740cd5b9a9"
      },
      {
        "path": "/data2/k6tk/27/271aa57a28e057b72ec0300273e11b20e00a6e01af4a8bda1c1b3a3ba8584a6c.png",
        "sha256": "271aa57a28e057b72ec0300273e11b20e00a6e01af4a8bda1c1b3a3ba8584a6c"
      },
      {
        "path": "/data2/k6tk/98/9869281b8a354aa3c808e052fe79c72f90194c61249b7664b0e0e59c4aa7eb26.png",
        "sha256": "9869281b8a354aa3c808e052fe79c72f90194c61249b7664b0e0e59c4aa7eb26"
      },
      {
        "path": "/data2/k6tk/1e/1e8e1f559d6a45be98f3b8ae46aaabad11c0ab11aee067c0b87a36b454139b03.png",
        "sha256": "1e8e1f559d6a45be98f3b8ae46aaabad11c0ab11aee067c0b87a36b454139b03"
      },
      {
        "path": "/data2/k6tk/65/652c659b21cae51cc4fd839c5f121787dbb0d712b1fa8326f6acef74ae856983.png",
        "sha256": "652c659b21cae51cc4fd839c5f121787dbb0d712b1fa8326f6acef74ae856983"
      },
      {
        "path": "/data2/k6tk/f4/f48e8480ffcaa383549b396e9fc473a1e124cdac8c65e8278802ead89fc89a57.png",
        "sha256": "f48e8480ffcaa383549b396e9fc473a1e124cdac8c65e8278802ead89fc89a57"
      },
      {
        "path": "/data2/k6tk/90/9032d4890ac7f5025ad8a90d7175a2018bb9bfea1de2f7d110f78d5f2715c7ba.png",
        "sha256": "9032d4890ac7f5025ad8a90d7175a2018bb9bfea1de2f7d110f78d5f2715c7ba"
      },
      {
        "path": "/data2/k6tk/ba/ba46e2d7ca4155bcbf5d23f660580d937f162f53d2e3702b17a0cf6fe34a7482.png",
        "sha256": "ba46e2d7ca4155bcbf5d23f660580d937f162f53d2e3702b17a0cf6fe34a7482"
      },
      {
        "path": "/data2/k6tk/0b/0b3f1daceefb3b00c7c89a66c315bfe2256c76b449f571f917a169046201ffc6.png",
        "sha256": "0b3f1daceefb3b00c7c89a66c315bfe2256c76b449f571f917a169046201ffc6"
      },
      {
        "path": "/data2/k6tk/a9/a98810434d78a06ce8b1085ab448ab558e02af9089852c7ed103e714d4afe708.png",
        "sha256": "a98810434d78a06ce8b1085ab448ab558e02af9089852c7ed103e714d4afe708"
      },
      {
        "path": "/data2/k6tk/7e/7e5bee1cfe069f7df33a1561934e3582a707228eeb77c779372c99549268a5b9.png",
        "sha256": "7e5bee1cfe069f7df33a1561934e3582a707228eeb77c779372c99549268a5b9"
      },
      {
        "path": "/data2/k6tk/ec/ec9ddd319326950276c9a85135b856539086d7ed6a8651bc23c0d813c9b5396d.png",
        "sha256": "ec9ddd319326950276c9a85135b856539086d7ed6a8651bc23c0d813c9b5396d"
      },
      {
        "path": "/data2/k6tk/6b/6b5ea39d7005172e88e95f8430fdaaa958a1c12a3eccf7701b575beb98b81a38.png",
        "sha256": "6b5ea39d7005172e88e95f8430fdaaa958a1c12a3eccf7701b575beb98b81a38"
      },
      {
        "path": "/data2/k6tk/0b/0b7d77c1d2d1a0f3d679d16aad99566155e0dc723447d8526e08e2f871309cee.png",
        "sha256": "0b7d77c1d2d1a0f3d679d16aad99566155e0dc723447d8526e08e2f871309cee"
      },
      {
        "path": "/data2/k6tk/af/af4ee9933529e58b3d36ca200f979c09299e727e47dbee5b727f5c48aede345e.png",
        "sha256": "af4ee9933529e58b3d36ca200f979c09299e727e47dbee5b727f5c48aede345e"
      },
      {
        "path": "/data2/k6tk/0a/0a235a7e3cb7e401604a70aacb19fccd407ddfb24f599936f7a8dcfcb6757f87.png",
        "sha256": "0a235a7e3cb7e401604a70aacb19fccd407ddfb24f599936f7a8dcfcb6757f87"
      },
      {
        "path": "/data2/k6tk/94/940f23104e7918d4b4e5e4e2487d27649a72c7fe4cbc9493dc834b64b1836da1.png",
        "sha256": "940f23104e7918d4b4e5e4e2487d27649a72c7fe4cbc9493dc834b64b1836da1"
      },
      {
        "path": "/data2/k6tk/a2/a20e577dd2112288035784ae901524f9cb0aa401b058eb166f70ca6932810402.png",
        "sha256": "a20e577dd2112288035784ae901524f9cb0aa401b058eb166f70ca6932810402"
      },
      {
        "path": "/data2/k6tk/14/1419e4f3bdfb6c59875340396c8d3e604efcf338285fd3379b20110114ec342c.png",
        "sha256": "1419e4f3bdfb6c59875340396c8d3e604efcf338285fd3379b20110114ec342c"
      },
      {
        "path": "/data2/k6tk/74/749cead719adcdb8bd400eddfdf09bb19f9184cf6646bf364408b224c51d3891.png",
        "sha256": "749cead719adcdb8bd400eddfdf09bb19f9184cf6646bf364408b224c51d3891"
      },
      {
        "path": "/data2/k6tk/96/9668fb9c2d8bcf70f65d4c284fcc7201e4465bb2baeea8bf63b8779b9644ae8f.png",
        "sha256": "9668fb9c2d8bcf70f65d4c284fcc7201e4465bb2baeea8bf63b8779b9644ae8f"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      4.433333333333334,
      8.883333333333333,
      13.333333333333334,
      17.783333333333335,
      22.233333333333334,
      26.683333333333334,
      31.133333333333333,
      35.583333333333336,
      40.03333333333333,
      44.483333333333334,
      48.93333333333333,
      53.38333333333333,
      57.833333333333336,
      62.28333333333333,
      66.73333333333333,
      71.16666666666667,
      75.61666666666666,
      80.06666666666666,
      84.51666666666667,
      88.96666666666667,
      93.41666666666667,
      97.86666666666666,
      102.31666666666666,
      106.76666666666667,
      111.21666666666667,
      115.66666666666667,
      120.11666666666666,
      124.56666666666666,
      129.01666666666668,
      133.46666666666667,
      137.91666666666666
    ],
    "total_num_frames": 8276
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: pipe in frame 5; sofa in frame 4; cabinet in frame 1.\nOf these, the sofa and the cabinet are farthest apart, with the pipe between them.\n</think>\n\n45.66",
  "validation_commit": ""
}
```

## sb_rowLR_4d432628e44ff231_q1

```json
{
  "answer": "45.66",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-da66029b1ed0696aebb780bbd8de081d0ba684697e64b01f4d768e9fe944bcd6",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v75b40392ada3",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        266,
        533,
        800,
        1067,
        1334,
        1601,
        1868,
        2135,
        2402,
        2669,
        2936,
        3203,
        3470,
        3737,
        4004,
        4270,
        4537,
        4804,
        5071,
        5338,
        5605,
        5872,
        6139,
        6406,
        6673,
        6940,
        7207,
        7474,
        7741,
        8008,
        8275
      ],
      "options": [],
      "qid": "sb_rowLR_4d432628e44ff231_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/036bce3393",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/036bce3393",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      266,
      533,
      800,
      1067,
      1334,
      1601,
      1868,
      2135,
      2402,
      2669,
      2936,
      3203,
      3470,
      3737,
      4004,
      4270,
      4537,
      4804,
      5071,
      5338,
      5605,
      5872,
      6139,
      6406,
      6673,
      6940,
      7207,
      7474,
      7741,
      8008,
      8275
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__036bce3393.npz": "ea4c864e410b72e7163ecaeb4ed47246c82b561ef157bab6d00bc941fb4f2cfc",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/036bce3393",
    "room_measurement": {
      "area_m2": 45.657500000000006,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 18263,
      "floor_height_m": 0.02103545676881753,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 15078
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            4.4839597450143325,
            3.850429213211479,
            2.9076585769653325
          ],
          "footprint": 9.276261655271414,
          "instance_id": 18,
          "label": "pipe",
          "pixel_share": 0.06338541666666667
        },
        {
          "best_view": 4,
          "centroid": [
            2.8053230019378432,
            2.726579234325177,
            0.579362452030182
          ],
          "footprint": 1.2248963528125711,
          "instance_id": 3,
          "label": "sofa",
          "pixel_share": 0.29359375
        },
        {
          "best_view": 1,
          "centroid": [
            7.569598187968429,
            2.6467943581458213,
            1.2623789943754675
          ],
          "footprint": 1.182764142976193,
          "instance_id": 45,
          "label": "cabinet",
          "pixel_share": 0.23458333333333334
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__036bce3393.npz",
      "raster_sha256": "ea4c864e410b72e7163ecaeb4ed47246c82b561ef157bab6d00bc941fb4f2cfc",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.4839597450143325,
            3.850429213211479
          ],
          [
            2.8053230019378432,
            2.726579234325177
          ],
          [
            7.569598187968429,
            2.6467943581458213
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 1.1517997517558076,
        "projection": 0.348290302709781,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.764943197425729,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12cs_209b69b0dfac46731f873720",
    "source_row_sha256": "64e7faf1dc6d778ee0a5613130274028686e5e316b916db87774928197845433",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_4d432628e44ff231_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v75b40392ada3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      266,
      533,
      800,
      1067,
      1334,
      1601,
      1868,
      2135,
      2402,
      2669,
      2936,
      3203,
      3470,
      3737,
      4004,
      4270,
      4537,
      4804,
      5071,
      5338,
      5605,
      5872,
      6139,
      6406,
      6673,
      6940,
      7207,
      7474,
      7741,
      8008,
      8275
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ff/ffea902cfebef130f1beccfa5c7d0b2ed56f06fdcd04c55ffc76bcef99479794.png",
        "sha256": "ffea902cfebef130f1beccfa5c7d0b2ed56f06fdcd04c55ffc76bcef99479794"
      },
      {
        "path": "/data2/k6tk/d3/d3b3e721a04b7e6b2bef3edd0675b2d8f8076227497a1b11d19bdde91c707f77.png",
        "sha256": "d3b3e721a04b7e6b2bef3edd0675b2d8f8076227497a1b11d19bdde91c707f77"
      },
      {
        "path": "/data2/k6tk/11/11b896fce202da0b427fe814a30a3dcfa58ac55533466508ca9a407e465d7079.png",
        "sha256": "11b896fce202da0b427fe814a30a3dcfa58ac55533466508ca9a407e465d7079"
      },
      {
        "path": "/data2/k6tk/93/93cbf079976776151f25c41c0c260d58dda1f63dfda4dfbbb2d475832bddf8bf.png",
        "sha256": "93cbf079976776151f25c41c0c260d58dda1f63dfda4dfbbb2d475832bddf8bf"
      },
      {
        "path": "/data2/k6tk/51/510ebbb4e11fe7b33d7189b8594c384f9848ac8ef334df3583dda6cd19445110.png",
        "sha256": "510ebbb4e11fe7b33d7189b8594c384f9848ac8ef334df3583dda6cd19445110"
      },
      {
        "path": "/data2/k6tk/cd/cd348a526b8a2ee50da196810363e8a20f345cebd3b0b9bd62dcb21d8d63318e.png",
        "sha256": "cd348a526b8a2ee50da196810363e8a20f345cebd3b0b9bd62dcb21d8d63318e"
      },
      {
        "path": "/data2/k6tk/ee/ee248edfe71364ed6c0888be2f90c19e57814b5f47051e3f3bd22276182b7bd1.png",
        "sha256": "ee248edfe71364ed6c0888be2f90c19e57814b5f47051e3f3bd22276182b7bd1"
      },
      {
        "path": "/data2/k6tk/df/dfc4bdd1067c70d9c86d4cabc9cf58622cf34af62ee14d5fec7ec72f4ae7b534.png",
        "sha256": "dfc4bdd1067c70d9c86d4cabc9cf58622cf34af62ee14d5fec7ec72f4ae7b534"
      },
      {
        "path": "/data2/k6tk/d6/d6cffc26c6158e0788fe46fc6d077f87fd7a3ad00756b84a6a43c7c2ff2ab80a.png",
        "sha256": "d6cffc26c6158e0788fe46fc6d077f87fd7a3ad00756b84a6a43c7c2ff2ab80a"
      },
      {
        "path": "/data2/k6tk/23/23c6c96060c9faeca1678f36397dc181912946bacb88e0d8f4ffd4c92137b3e6.png",
        "sha256": "23c6c96060c9faeca1678f36397dc181912946bacb88e0d8f4ffd4c92137b3e6"
      },
      {
        "path": "/data2/k6tk/72/7248d6b2bed6a03b850abd6f35143d22da6b73f1139d806922f67099b82abc03.png",
        "sha256": "7248d6b2bed6a03b850abd6f35143d22da6b73f1139d806922f67099b82abc03"
      },
      {
        "path": "/data2/k6tk/59/59644418d9ee53745cfaf177829526171d6b3bf8cab22797fd7c67740cd5b9a9.png",
        "sha256": "59644418d9ee53745cfaf177829526171d6b3bf8cab22797fd7c67740cd5b9a9"
      },
      {
        "path": "/data2/k6tk/27/271aa57a28e057b72ec0300273e11b20e00a6e01af4a8bda1c1b3a3ba8584a6c.png",
        "sha256": "271aa57a28e057b72ec0300273e11b20e00a6e01af4a8bda1c1b3a3ba8584a6c"
      },
      {
        "path": "/data2/k6tk/98/9869281b8a354aa3c808e052fe79c72f90194c61249b7664b0e0e59c4aa7eb26.png",
        "sha256": "9869281b8a354aa3c808e052fe79c72f90194c61249b7664b0e0e59c4aa7eb26"
      },
      {
        "path": "/data2/k6tk/1e/1e8e1f559d6a45be98f3b8ae46aaabad11c0ab11aee067c0b87a36b454139b03.png",
        "sha256": "1e8e1f559d6a45be98f3b8ae46aaabad11c0ab11aee067c0b87a36b454139b03"
      },
      {
        "path": "/data2/k6tk/65/652c659b21cae51cc4fd839c5f121787dbb0d712b1fa8326f6acef74ae856983.png",
        "sha256": "652c659b21cae51cc4fd839c5f121787dbb0d712b1fa8326f6acef74ae856983"
      },
      {
        "path": "/data2/k6tk/f4/f48e8480ffcaa383549b396e9fc473a1e124cdac8c65e8278802ead89fc89a57.png",
        "sha256": "f48e8480ffcaa383549b396e9fc473a1e124cdac8c65e8278802ead89fc89a57"
      },
      {
        "path": "/data2/k6tk/90/9032d4890ac7f5025ad8a90d7175a2018bb9bfea1de2f7d110f78d5f2715c7ba.png",
        "sha256": "9032d4890ac7f5025ad8a90d7175a2018bb9bfea1de2f7d110f78d5f2715c7ba"
      },
      {
        "path": "/data2/k6tk/ba/ba46e2d7ca4155bcbf5d23f660580d937f162f53d2e3702b17a0cf6fe34a7482.png",
        "sha256": "ba46e2d7ca4155bcbf5d23f660580d937f162f53d2e3702b17a0cf6fe34a7482"
      },
      {
        "path": "/data2/k6tk/0b/0b3f1daceefb3b00c7c89a66c315bfe2256c76b449f571f917a169046201ffc6.png",
        "sha256": "0b3f1daceefb3b00c7c89a66c315bfe2256c76b449f571f917a169046201ffc6"
      },
      {
        "path": "/data2/k6tk/a9/a98810434d78a06ce8b1085ab448ab558e02af9089852c7ed103e714d4afe708.png",
        "sha256": "a98810434d78a06ce8b1085ab448ab558e02af9089852c7ed103e714d4afe708"
      },
      {
        "path": "/data2/k6tk/7e/7e5bee1cfe069f7df33a1561934e3582a707228eeb77c779372c99549268a5b9.png",
        "sha256": "7e5bee1cfe069f7df33a1561934e3582a707228eeb77c779372c99549268a5b9"
      },
      {
        "path": "/data2/k6tk/ec/ec9ddd319326950276c9a85135b856539086d7ed6a8651bc23c0d813c9b5396d.png",
        "sha256": "ec9ddd319326950276c9a85135b856539086d7ed6a8651bc23c0d813c9b5396d"
      },
      {
        "path": "/data2/k6tk/6b/6b5ea39d7005172e88e95f8430fdaaa958a1c12a3eccf7701b575beb98b81a38.png",
        "sha256": "6b5ea39d7005172e88e95f8430fdaaa958a1c12a3eccf7701b575beb98b81a38"
      },
      {
        "path": "/data2/k6tk/0b/0b7d77c1d2d1a0f3d679d16aad99566155e0dc723447d8526e08e2f871309cee.png",
        "sha256": "0b7d77c1d2d1a0f3d679d16aad99566155e0dc723447d8526e08e2f871309cee"
      },
      {
        "path": "/data2/k6tk/af/af4ee9933529e58b3d36ca200f979c09299e727e47dbee5b727f5c48aede345e.png",
        "sha256": "af4ee9933529e58b3d36ca200f979c09299e727e47dbee5b727f5c48aede345e"
      },
      {
        "path": "/data2/k6tk/0a/0a235a7e3cb7e401604a70aacb19fccd407ddfb24f599936f7a8dcfcb6757f87.png",
        "sha256": "0a235a7e3cb7e401604a70aacb19fccd407ddfb24f599936f7a8dcfcb6757f87"
      },
      {
        "path": "/data2/k6tk/94/940f23104e7918d4b4e5e4e2487d27649a72c7fe4cbc9493dc834b64b1836da1.png",
        "sha256": "940f23104e7918d4b4e5e4e2487d27649a72c7fe4cbc9493dc834b64b1836da1"
      },
      {
        "path": "/data2/k6tk/a2/a20e577dd2112288035784ae901524f9cb0aa401b058eb166f70ca6932810402.png",
        "sha256": "a20e577dd2112288035784ae901524f9cb0aa401b058eb166f70ca6932810402"
      },
      {
        "path": "/data2/k6tk/14/1419e4f3bdfb6c59875340396c8d3e604efcf338285fd3379b20110114ec342c.png",
        "sha256": "1419e4f3bdfb6c59875340396c8d3e604efcf338285fd3379b20110114ec342c"
      },
      {
        "path": "/data2/k6tk/74/749cead719adcdb8bd400eddfdf09bb19f9184cf6646bf364408b224c51d3891.png",
        "sha256": "749cead719adcdb8bd400eddfdf09bb19f9184cf6646bf364408b224c51d3891"
      },
      {
        "path": "/data2/k6tk/96/9668fb9c2d8bcf70f65d4c284fcc7201e4465bb2baeea8bf63b8779b9644ae8f.png",
        "sha256": "9668fb9c2d8bcf70f65d4c284fcc7201e4465bb2baeea8bf63b8779b9644ae8f"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      4.433333333333334,
      8.883333333333333,
      13.333333333333334,
      17.783333333333335,
      22.233333333333334,
      26.683333333333334,
      31.133333333333333,
      35.583333333333336,
      40.03333333333333,
      44.483333333333334,
      48.93333333333333,
      53.38333333333333,
      57.833333333333336,
      62.28333333333333,
      66.73333333333333,
      71.16666666666667,
      75.61666666666666,
      80.06666666666666,
      84.51666666666667,
      88.96666666666667,
      93.41666666666667,
      97.86666666666666,
      102.31666666666666,
      106.76666666666667,
      111.21666666666667,
      115.66666666666667,
      120.11666666666666,
      124.56666666666666,
      129.01666666666668,
      133.46666666666667,
      137.91666666666666
    ],
    "total_num_frames": 8276
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: pipe in frame 5; sofa in frame 4; cabinet in frame 1.\nThe sofa and the cabinet are the farthest apart among these landmarks, with the pipe between them.\n</think>\n\n45.66",
  "validation_commit": ""
}
```

## sb_rowLR_238522c9ff597fc6_q0

```json
{
  "answer": "44.85",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-a28d9d57710c31dc603e2de9acedffb045c44c328aef6ced2ea9f4cf185dac03",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v83d66e858b6f",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        349,
        699,
        1049,
        1399,
        1749,
        2099,
        2448,
        2798,
        3148,
        3498,
        3848,
        4198,
        4547,
        4897,
        5247,
        5597,
        5947,
        6297,
        6646,
        6996,
        7346,
        7696,
        8046,
        8396,
        8745,
        9095,
        9445,
        9795,
        10145,
        10495,
        10845
      ],
      "options": [],
      "qid": "sb_rowLR_238522c9ff597fc6_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/98b4ec142f",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/98b4ec142f",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      349,
      699,
      1049,
      1399,
      1749,
      2099,
      2448,
      2798,
      3148,
      3498,
      3848,
      4198,
      4547,
      4897,
      5247,
      5597,
      5947,
      6297,
      6646,
      6996,
      7346,
      7696,
      8046,
      8396,
      8745,
      9095,
      9445,
      9795,
      10145,
      10495,
      10845
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__98b4ec142f.npz": "5e587f3ff00ac040df3fd91f15f5891591abb9909f5c651d2ee29f5bbef8ae96",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/98b4ec142f",
    "room_measurement": {
      "area_m2": 44.852500000000006,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 17941,
      "floor_height_m": -0.054053765552842074,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 12771
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            4.678618070229798,
            5.0142891485278716,
            0.9133260250091553
          ],
          "footprint": 1.044556513719557,
          "instance_id": 75,
          "label": "window sill",
          "pixel_share": 0.14678385416666667
        },
        {
          "best_view": 6,
          "centroid": [
            4.753835505840006,
            0.5230678759694811,
            1.1559315398335457
          ],
          "footprint": 0.5855122780369304,
          "instance_id": 40,
          "label": "storage cabinet",
          "pixel_share": 0.190078125
        },
        {
          "best_view": 27,
          "centroid": [
            2.9221945652434966,
            0.34484490116246835,
            1.1689881905913353
          ],
          "footprint": 0.564424762918808,
          "instance_id": 3,
          "label": "bookshelf",
          "pixel_share": 0.47553385416666666
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__98b4ec142f.npz",
      "raster_sha256": "5e587f3ff00ac040df3fd91f15f5891591abb9909f5c651d2ee29f5bbef8ae96",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.678618070229798,
            5.0142891485278716
          ],
          [
            4.753835505840006,
            0.5230678759694811
          ],
          [
            2.9221945652434966,
            0.34484490116246835
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 1.6516215608452673,
        "projection": 0.837302307528927,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.9888609028637205,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12cs_212e022e2c508a4d3b71514a",
    "source_row_sha256": "99d46ffe2588226fa6602e9a39b8de0d6377d3f2209f2eb7f6d3d421f4d62fde",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_238522c9ff597fc6_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v83d66e858b6f",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      349,
      699,
      1049,
      1399,
      1749,
      2099,
      2448,
      2798,
      3148,
      3498,
      3848,
      4198,
      4547,
      4897,
      5247,
      5597,
      5947,
      6297,
      6646,
      6996,
      7346,
      7696,
      8046,
      8396,
      8745,
      9095,
      9445,
      9795,
      10145,
      10495,
      10845
    ],
    "frames": [
      {
        "path": "/data2/k6tk/47/47857dd1ee52b76f826c99474625592c3ff8bd68c4e7efe48f1299253e6f5eac.png",
        "sha256": "47857dd1ee52b76f826c99474625592c3ff8bd68c4e7efe48f1299253e6f5eac"
      },
      {
        "path": "/data2/k6tk/9f/9fe9a206b7e3f910fa9e4753e5aa56dd0f0f5266f8cfdbcd03bb634be6c0a1ab.png",
        "sha256": "9fe9a206b7e3f910fa9e4753e5aa56dd0f0f5266f8cfdbcd03bb634be6c0a1ab"
      },
      {
        "path": "/data2/k6tk/f9/f94553f9ced36438707e03f721b1e06e9324e5608d73898c1398e7166c29f1d2.png",
        "sha256": "f94553f9ced36438707e03f721b1e06e9324e5608d73898c1398e7166c29f1d2"
      },
      {
        "path": "/data2/k6tk/e6/e671163843165532c580b3ffd842035eedaffa6a5861efdc9b2f44bf69dab005.png",
        "sha256": "e671163843165532c580b3ffd842035eedaffa6a5861efdc9b2f44bf69dab005"
      },
      {
        "path": "/data2/k6tk/c3/c3bbb42a1e980da6ac39c5437d0703b1990b88075727d3a0ba0a81c0cdfc75fb.png",
        "sha256": "c3bbb42a1e980da6ac39c5437d0703b1990b88075727d3a0ba0a81c0cdfc75fb"
      },
      {
        "path": "/data2/k6tk/8d/8d0d81dbe0f4f71971d05f0298b71b2a12b241619ae865de8bea6a0a45c3374f.png",
        "sha256": "8d0d81dbe0f4f71971d05f0298b71b2a12b241619ae865de8bea6a0a45c3374f"
      },
      {
        "path": "/data2/k6tk/a8/a8972dcf66d68c6e2e25d4e0d9af7eeaf296d25d75922234e18192c437b4b05b.png",
        "sha256": "a8972dcf66d68c6e2e25d4e0d9af7eeaf296d25d75922234e18192c437b4b05b"
      },
      {
        "path": "/data2/k6tk/3b/3ba883960f850f368ed300d137526d7801408fd1653e25ca731d0d95c6333baf.png",
        "sha256": "3ba883960f850f368ed300d137526d7801408fd1653e25ca731d0d95c6333baf"
      },
      {
        "path": "/data2/k6tk/d2/d25430a70d46f1b1186e0daf774a7dcd2f8b48cd1f27b501cd144d521db40cd4.png",
        "sha256": "d25430a70d46f1b1186e0daf774a7dcd2f8b48cd1f27b501cd144d521db40cd4"
      },
      {
        "path": "/data2/k6tk/6c/6cf910fc1b5f4b401094b55d58b47d9741938297c77815816e55e90f276a936e.png",
        "sha256": "6cf910fc1b5f4b401094b55d58b47d9741938297c77815816e55e90f276a936e"
      },
      {
        "path": "/data2/k6tk/3a/3a4d116a0a6534cdddb318e3c493c28efbf110392fc42ed342ba1e81c6943322.png",
        "sha256": "3a4d116a0a6534cdddb318e3c493c28efbf110392fc42ed342ba1e81c6943322"
      },
      {
        "path": "/data2/k6tk/51/512549bc7803b93fe4ef896722083611f4b2a61f7e62611e9a6c487f78d8d5dd.png",
        "sha256": "512549bc7803b93fe4ef896722083611f4b2a61f7e62611e9a6c487f78d8d5dd"
      },
      {
        "path": "/data2/k6tk/e5/e5b420cc464785257f705388cdc94dcd8f8b3d5de11aef9d828a0b27d0c11750.png",
        "sha256": "e5b420cc464785257f705388cdc94dcd8f8b3d5de11aef9d828a0b27d0c11750"
      },
      {
        "path": "/data2/k6tk/96/9668c6ecc58cfc93c3058676c61ebbed183db76765d2d51cfe843fb3b3bb0328.png",
        "sha256": "9668c6ecc58cfc93c3058676c61ebbed183db76765d2d51cfe843fb3b3bb0328"
      },
      {
        "path": "/data2/k6tk/1b/1be9a8e871ec423cd6a617107cda9e4d23e39de0b35c0f47295b553b304a831a.png",
        "sha256": "1be9a8e871ec423cd6a617107cda9e4d23e39de0b35c0f47295b553b304a831a"
      },
      {
        "path": "/data2/k6tk/7e/7e959ba6c698fd49b8c10e601e5cfcf98abadebb4d09800595d9e42cfa84a5d6.png",
        "sha256": "7e959ba6c698fd49b8c10e601e5cfcf98abadebb4d09800595d9e42cfa84a5d6"
      },
      {
        "path": "/data2/k6tk/25/25a3389c399cf5357bcd5a6106827a144e738e297c8d3519889814079c2f9ca9.png",
        "sha256": "25a3389c399cf5357bcd5a6106827a144e738e297c8d3519889814079c2f9ca9"
      },
      {
        "path": "/data2/k6tk/cc/cce20cfe675b36b562dde2300de21fc2391dbe660c67aa30b9c2d1f7d76584dd.png",
        "sha256": "cce20cfe675b36b562dde2300de21fc2391dbe660c67aa30b9c2d1f7d76584dd"
      },
      {
        "path": "/data2/k6tk/db/db801fd29539f95d83ed7eb1640893ec3489c35d2fc531144afe2804b0174f85.png",
        "sha256": "db801fd29539f95d83ed7eb1640893ec3489c35d2fc531144afe2804b0174f85"
      },
      {
        "path": "/data2/k6tk/5d/5df5599678b242f7898fde88b884610dec73732e9d837dad5367a3fc652e5de4.png",
        "sha256": "5df5599678b242f7898fde88b884610dec73732e9d837dad5367a3fc652e5de4"
      },
      {
        "path": "/data2/k6tk/ad/ad5d68891f48ad6446ff2e07359b1b5957ae2b17767e5ba80252e38c61729c35.png",
        "sha256": "ad5d68891f48ad6446ff2e07359b1b5957ae2b17767e5ba80252e38c61729c35"
      },
      {
        "path": "/data2/k6tk/6f/6fdf1484d037fda35bbfedbc34899efcea6391dc76a08b371842c61de473c4b1.png",
        "sha256": "6fdf1484d037fda35bbfedbc34899efcea6391dc76a08b371842c61de473c4b1"
      },
      {
        "path": "/data2/k6tk/0a/0a51a18f8dd2d995b4a72ad8b602fc2f0514c94e2614e8a9b53a52e31517ec8c.png",
        "sha256": "0a51a18f8dd2d995b4a72ad8b602fc2f0514c94e2614e8a9b53a52e31517ec8c"
      },
      {
        "path": "/data2/k6tk/6e/6ed651234ef0f84ba877dbbd1d8be88da7e0d87297b03bd9cac3bfbcaf520cf9.png",
        "sha256": "6ed651234ef0f84ba877dbbd1d8be88da7e0d87297b03bd9cac3bfbcaf520cf9"
      },
      {
        "path": "/data2/k6tk/63/63c464e59a017eadbe30e5d56181a216fc84b3d11658ec765aa07b5d0741e7e6.png",
        "sha256": "63c464e59a017eadbe30e5d56181a216fc84b3d11658ec765aa07b5d0741e7e6"
      },
      {
        "path": "/data2/k6tk/54/54865ad37c0f083daca2b724e6227c3272f88df41831ab538835e3e4875dc4b6.png",
        "sha256": "54865ad37c0f083daca2b724e6227c3272f88df41831ab538835e3e4875dc4b6"
      },
      {
        "path": "/data2/k6tk/4d/4d74f8f6d18ea2f3cf75ede62c56197eab6d25fb11b1cf925b8497e71f016815.png",
        "sha256": "4d74f8f6d18ea2f3cf75ede62c56197eab6d25fb11b1cf925b8497e71f016815"
      },
      {
        "path": "/data2/k6tk/d7/d7b5e98e6fea20dfdac05da91cf342d82d133d6444e357680b28f938255a15aa.png",
        "sha256": "d7b5e98e6fea20dfdac05da91cf342d82d133d6444e357680b28f938255a15aa"
      },
      {
        "path": "/data2/k6tk/a8/a8419cc8462467dbbfef9a3efd453562e5e5e3fed954d6ec0897bf02d31c1e86.png",
        "sha256": "a8419cc8462467dbbfef9a3efd453562e5e5e3fed954d6ec0897bf02d31c1e86"
      },
      {
        "path": "/data2/k6tk/76/76dff12365dd9ea0d3ebe00d3764c31f8e588b654e2252ba90e32c4327e0778c.png",
        "sha256": "76dff12365dd9ea0d3ebe00d3764c31f8e588b654e2252ba90e32c4327e0778c"
      },
      {
        "path": "/data2/k6tk/4a/4a1944f824021105c62983b1db6f2605bcd2f64433deea86c6d59b27c33b5c61.png",
        "sha256": "4a1944f824021105c62983b1db6f2605bcd2f64433deea86c6d59b27c33b5c61"
      },
      {
        "path": "/data2/k6tk/2e/2e2820c7dde59a353b99876f368731ab8fa4c97b98543a87dbf6a4c3eeb35299.png",
        "sha256": "2e2820c7dde59a353b99876f368731ab8fa4c97b98543a87dbf6a4c3eeb35299"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.816666666666666,
      11.65,
      17.483333333333334,
      23.316666666666666,
      29.15,
      34.983333333333334,
      40.8,
      46.63333333333333,
      52.46666666666667,
      58.3,
      64.13333333333334,
      69.96666666666667,
      75.78333333333333,
      81.61666666666666,
      87.45,
      93.28333333333333,
      99.11666666666666,
      104.95,
      110.76666666666667,
      116.6,
      122.43333333333334,
      128.26666666666668,
      134.1,
      139.93333333333334,
      145.75,
      151.58333333333334,
      157.41666666666666,
      163.25,
      169.08333333333334,
      174.91666666666666,
      180.75
    ],
    "total_num_frames": 10846
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: window sill in frame 5; storage cabinet in frame 6; bookshelf in frame 27.\nThe window sill and the bookshelf are the farthest apart among these landmarks, with the storage cabinet to the side of that pair.\n</think>\n\n44.85",
  "validation_commit": ""
}
```

## sb_rowLR_238522c9ff597fc6_q1

```json
{
  "answer": "44.85",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-e99d35210d032ced4b58345ca847f3f91d6c45bb633e28b6a47e68f7c2490149",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v83d66e858b6f",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        349,
        699,
        1049,
        1399,
        1749,
        2099,
        2448,
        2798,
        3148,
        3498,
        3848,
        4198,
        4547,
        4897,
        5247,
        5597,
        5947,
        6297,
        6646,
        6996,
        7346,
        7696,
        8046,
        8396,
        8745,
        9095,
        9445,
        9795,
        10145,
        10495,
        10845
      ],
      "options": [],
      "qid": "sb_rowLR_238522c9ff597fc6_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/98b4ec142f",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/98b4ec142f",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      349,
      699,
      1049,
      1399,
      1749,
      2099,
      2448,
      2798,
      3148,
      3498,
      3848,
      4198,
      4547,
      4897,
      5247,
      5597,
      5947,
      6297,
      6646,
      6996,
      7346,
      7696,
      8046,
      8396,
      8745,
      9095,
      9445,
      9795,
      10145,
      10495,
      10845
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__98b4ec142f.npz": "5e587f3ff00ac040df3fd91f15f5891591abb9909f5c651d2ee29f5bbef8ae96",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/98b4ec142f",
    "room_measurement": {
      "area_m2": 44.852500000000006,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 17941,
      "floor_height_m": -0.054053765552842074,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 12771
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            4.678618070229798,
            5.0142891485278716,
            0.9133260250091553
          ],
          "footprint": 1.044556513719557,
          "instance_id": 75,
          "label": "window sill",
          "pixel_share": 0.14678385416666667
        },
        {
          "best_view": 6,
          "centroid": [
            4.753835505840006,
            0.5230678759694811,
            1.1559315398335457
          ],
          "footprint": 0.5855122780369304,
          "instance_id": 40,
          "label": "storage cabinet",
          "pixel_share": 0.190078125
        },
        {
          "best_view": 27,
          "centroid": [
            2.9221945652434966,
            0.34484490116246835,
            1.1689881905913353
          ],
          "footprint": 0.564424762918808,
          "instance_id": 3,
          "label": "bookshelf",
          "pixel_share": 0.47553385416666666
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__98b4ec142f.npz",
      "raster_sha256": "5e587f3ff00ac040df3fd91f15f5891591abb9909f5c651d2ee29f5bbef8ae96",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.678618070229798,
            5.0142891485278716
          ],
          [
            4.753835505840006,
            0.5230678759694811
          ],
          [
            2.9221945652434966,
            0.34484490116246835
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 1.6516215608452673,
        "projection": 0.837302307528927,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.9888609028637205,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12cs_212e022e2c508a4d3b71514a",
    "source_row_sha256": "99d46ffe2588226fa6602e9a39b8de0d6377d3f2209f2eb7f6d3d421f4d62fde",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_238522c9ff597fc6_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v83d66e858b6f",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      349,
      699,
      1049,
      1399,
      1749,
      2099,
      2448,
      2798,
      3148,
      3498,
      3848,
      4198,
      4547,
      4897,
      5247,
      5597,
      5947,
      6297,
      6646,
      6996,
      7346,
      7696,
      8046,
      8396,
      8745,
      9095,
      9445,
      9795,
      10145,
      10495,
      10845
    ],
    "frames": [
      {
        "path": "/data2/k6tk/47/47857dd1ee52b76f826c99474625592c3ff8bd68c4e7efe48f1299253e6f5eac.png",
        "sha256": "47857dd1ee52b76f826c99474625592c3ff8bd68c4e7efe48f1299253e6f5eac"
      },
      {
        "path": "/data2/k6tk/9f/9fe9a206b7e3f910fa9e4753e5aa56dd0f0f5266f8cfdbcd03bb634be6c0a1ab.png",
        "sha256": "9fe9a206b7e3f910fa9e4753e5aa56dd0f0f5266f8cfdbcd03bb634be6c0a1ab"
      },
      {
        "path": "/data2/k6tk/f9/f94553f9ced36438707e03f721b1e06e9324e5608d73898c1398e7166c29f1d2.png",
        "sha256": "f94553f9ced36438707e03f721b1e06e9324e5608d73898c1398e7166c29f1d2"
      },
      {
        "path": "/data2/k6tk/e6/e671163843165532c580b3ffd842035eedaffa6a5861efdc9b2f44bf69dab005.png",
        "sha256": "e671163843165532c580b3ffd842035eedaffa6a5861efdc9b2f44bf69dab005"
      },
      {
        "path": "/data2/k6tk/c3/c3bbb42a1e980da6ac39c5437d0703b1990b88075727d3a0ba0a81c0cdfc75fb.png",
        "sha256": "c3bbb42a1e980da6ac39c5437d0703b1990b88075727d3a0ba0a81c0cdfc75fb"
      },
      {
        "path": "/data2/k6tk/8d/8d0d81dbe0f4f71971d05f0298b71b2a12b241619ae865de8bea6a0a45c3374f.png",
        "sha256": "8d0d81dbe0f4f71971d05f0298b71b2a12b241619ae865de8bea6a0a45c3374f"
      },
      {
        "path": "/data2/k6tk/a8/a8972dcf66d68c6e2e25d4e0d9af7eeaf296d25d75922234e18192c437b4b05b.png",
        "sha256": "a8972dcf66d68c6e2e25d4e0d9af7eeaf296d25d75922234e18192c437b4b05b"
      },
      {
        "path": "/data2/k6tk/3b/3ba883960f850f368ed300d137526d7801408fd1653e25ca731d0d95c6333baf.png",
        "sha256": "3ba883960f850f368ed300d137526d7801408fd1653e25ca731d0d95c6333baf"
      },
      {
        "path": "/data2/k6tk/d2/d25430a70d46f1b1186e0daf774a7dcd2f8b48cd1f27b501cd144d521db40cd4.png",
        "sha256": "d25430a70d46f1b1186e0daf774a7dcd2f8b48cd1f27b501cd144d521db40cd4"
      },
      {
        "path": "/data2/k6tk/6c/6cf910fc1b5f4b401094b55d58b47d9741938297c77815816e55e90f276a936e.png",
        "sha256": "6cf910fc1b5f4b401094b55d58b47d9741938297c77815816e55e90f276a936e"
      },
      {
        "path": "/data2/k6tk/3a/3a4d116a0a6534cdddb318e3c493c28efbf110392fc42ed342ba1e81c6943322.png",
        "sha256": "3a4d116a0a6534cdddb318e3c493c28efbf110392fc42ed342ba1e81c6943322"
      },
      {
        "path": "/data2/k6tk/51/512549bc7803b93fe4ef896722083611f4b2a61f7e62611e9a6c487f78d8d5dd.png",
        "sha256": "512549bc7803b93fe4ef896722083611f4b2a61f7e62611e9a6c487f78d8d5dd"
      },
      {
        "path": "/data2/k6tk/e5/e5b420cc464785257f705388cdc94dcd8f8b3d5de11aef9d828a0b27d0c11750.png",
        "sha256": "e5b420cc464785257f705388cdc94dcd8f8b3d5de11aef9d828a0b27d0c11750"
      },
      {
        "path": "/data2/k6tk/96/9668c6ecc58cfc93c3058676c61ebbed183db76765d2d51cfe843fb3b3bb0328.png",
        "sha256": "9668c6ecc58cfc93c3058676c61ebbed183db76765d2d51cfe843fb3b3bb0328"
      },
      {
        "path": "/data2/k6tk/1b/1be9a8e871ec423cd6a617107cda9e4d23e39de0b35c0f47295b553b304a831a.png",
        "sha256": "1be9a8e871ec423cd6a617107cda9e4d23e39de0b35c0f47295b553b304a831a"
      },
      {
        "path": "/data2/k6tk/7e/7e959ba6c698fd49b8c10e601e5cfcf98abadebb4d09800595d9e42cfa84a5d6.png",
        "sha256": "7e959ba6c698fd49b8c10e601e5cfcf98abadebb4d09800595d9e42cfa84a5d6"
      },
      {
        "path": "/data2/k6tk/25/25a3389c399cf5357bcd5a6106827a144e738e297c8d3519889814079c2f9ca9.png",
        "sha256": "25a3389c399cf5357bcd5a6106827a144e738e297c8d3519889814079c2f9ca9"
      },
      {
        "path": "/data2/k6tk/cc/cce20cfe675b36b562dde2300de21fc2391dbe660c67aa30b9c2d1f7d76584dd.png",
        "sha256": "cce20cfe675b36b562dde2300de21fc2391dbe660c67aa30b9c2d1f7d76584dd"
      },
      {
        "path": "/data2/k6tk/db/db801fd29539f95d83ed7eb1640893ec3489c35d2fc531144afe2804b0174f85.png",
        "sha256": "db801fd29539f95d83ed7eb1640893ec3489c35d2fc531144afe2804b0174f85"
      },
      {
        "path": "/data2/k6tk/5d/5df5599678b242f7898fde88b884610dec73732e9d837dad5367a3fc652e5de4.png",
        "sha256": "5df5599678b242f7898fde88b884610dec73732e9d837dad5367a3fc652e5de4"
      },
      {
        "path": "/data2/k6tk/ad/ad5d68891f48ad6446ff2e07359b1b5957ae2b17767e5ba80252e38c61729c35.png",
        "sha256": "ad5d68891f48ad6446ff2e07359b1b5957ae2b17767e5ba80252e38c61729c35"
      },
      {
        "path": "/data2/k6tk/6f/6fdf1484d037fda35bbfedbc34899efcea6391dc76a08b371842c61de473c4b1.png",
        "sha256": "6fdf1484d037fda35bbfedbc34899efcea6391dc76a08b371842c61de473c4b1"
      },
      {
        "path": "/data2/k6tk/0a/0a51a18f8dd2d995b4a72ad8b602fc2f0514c94e2614e8a9b53a52e31517ec8c.png",
        "sha256": "0a51a18f8dd2d995b4a72ad8b602fc2f0514c94e2614e8a9b53a52e31517ec8c"
      },
      {
        "path": "/data2/k6tk/6e/6ed651234ef0f84ba877dbbd1d8be88da7e0d87297b03bd9cac3bfbcaf520cf9.png",
        "sha256": "6ed651234ef0f84ba877dbbd1d8be88da7e0d87297b03bd9cac3bfbcaf520cf9"
      },
      {
        "path": "/data2/k6tk/63/63c464e59a017eadbe30e5d56181a216fc84b3d11658ec765aa07b5d0741e7e6.png",
        "sha256": "63c464e59a017eadbe30e5d56181a216fc84b3d11658ec765aa07b5d0741e7e6"
      },
      {
        "path": "/data2/k6tk/54/54865ad37c0f083daca2b724e6227c3272f88df41831ab538835e3e4875dc4b6.png",
        "sha256": "54865ad37c0f083daca2b724e6227c3272f88df41831ab538835e3e4875dc4b6"
      },
      {
        "path": "/data2/k6tk/4d/4d74f8f6d18ea2f3cf75ede62c56197eab6d25fb11b1cf925b8497e71f016815.png",
        "sha256": "4d74f8f6d18ea2f3cf75ede62c56197eab6d25fb11b1cf925b8497e71f016815"
      },
      {
        "path": "/data2/k6tk/d7/d7b5e98e6fea20dfdac05da91cf342d82d133d6444e357680b28f938255a15aa.png",
        "sha256": "d7b5e98e6fea20dfdac05da91cf342d82d133d6444e357680b28f938255a15aa"
      },
      {
        "path": "/data2/k6tk/a8/a8419cc8462467dbbfef9a3efd453562e5e5e3fed954d6ec0897bf02d31c1e86.png",
        "sha256": "a8419cc8462467dbbfef9a3efd453562e5e5e3fed954d6ec0897bf02d31c1e86"
      },
      {
        "path": "/data2/k6tk/76/76dff12365dd9ea0d3ebe00d3764c31f8e588b654e2252ba90e32c4327e0778c.png",
        "sha256": "76dff12365dd9ea0d3ebe00d3764c31f8e588b654e2252ba90e32c4327e0778c"
      },
      {
        "path": "/data2/k6tk/4a/4a1944f824021105c62983b1db6f2605bcd2f64433deea86c6d59b27c33b5c61.png",
        "sha256": "4a1944f824021105c62983b1db6f2605bcd2f64433deea86c6d59b27c33b5c61"
      },
      {
        "path": "/data2/k6tk/2e/2e2820c7dde59a353b99876f368731ab8fa4c97b98543a87dbf6a4c3eeb35299.png",
        "sha256": "2e2820c7dde59a353b99876f368731ab8fa4c97b98543a87dbf6a4c3eeb35299"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      5.816666666666666,
      11.65,
      17.483333333333334,
      23.316666666666666,
      29.15,
      34.983333333333334,
      40.8,
      46.63333333333333,
      52.46666666666667,
      58.3,
      64.13333333333334,
      69.96666666666667,
      75.78333333333333,
      81.61666666666666,
      87.45,
      93.28333333333333,
      99.11666666666666,
      104.95,
      110.76666666666667,
      116.6,
      122.43333333333334,
      128.26666666666668,
      134.1,
      139.93333333333334,
      145.75,
      151.58333333333334,
      157.41666666666666,
      163.25,
      169.08333333333334,
      174.91666666666666,
      180.75
    ],
    "total_num_frames": 10846
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: window sill in frame 5; storage cabinet in frame 6; bookshelf in frame 27.\nThe window sill and the bookshelf are the farthest apart among these landmarks, with the storage cabinet to the side of that pair.\n</think>\n\n44.85",
  "validation_commit": ""
}
```

## sb_rowLR_9a1ea173fe2cb99c_q0

```json
{
  "answer": "42.85",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-5ae52ca92d380647e72254bd630d9d6d44e64c34b0f0e3289ee71252b9756c17",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vddece0ae5dce",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        322,
        644,
        966,
        1288,
        1610,
        1932,
        2254,
        2576,
        2898,
        3220,
        3543,
        3865,
        4187,
        4509,
        4831,
        5153,
        5475,
        5797,
        6119,
        6441,
        6764,
        7086,
        7408,
        7730,
        8052,
        8374,
        8696,
        9018,
        9340,
        9662,
        9985
      ],
      "options": [],
      "qid": "sb_rowLR_9a1ea173fe2cb99c_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/1b75758486",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/1b75758486",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      322,
      644,
      966,
      1288,
      1610,
      1932,
      2254,
      2576,
      2898,
      3220,
      3543,
      3865,
      4187,
      4509,
      4831,
      5153,
      5475,
      5797,
      6119,
      6441,
      6764,
      7086,
      7408,
      7730,
      8052,
      8374,
      8696,
      9018,
      9340,
      9662,
      9985
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__1b75758486.npz": "19e06b35182cd53beeac3462a23b4864a5c380256f870618807855765beb612a",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/1b75758486",
    "room_measurement": {
      "area_m2": 42.847500000000004,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 17139,
      "floor_height_m": 0.13526197507202786,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 11886
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 20,
          "centroid": [
            0.732183104317611,
            2.660998608384493,
            1.0672707185149193
          ],
          "footprint": 1.3267199492662134,
          "instance_id": 40,
          "label": "bookshelf",
          "pixel_share": 0.2996744791666667
        },
        {
          "best_view": 30,
          "centroid": [
            4.9528279500236945,
            6.480217881104727,
            1.2600806951522827
          ],
          "footprint": 1.1042100608606777,
          "instance_id": 39,
          "label": "door",
          "pixel_share": 0.61609375
        },
        {
          "best_view": 29,
          "centroid": [
            3.062121489808708,
            5.964908702109188,
            1.2207441329956057
          ],
          "footprint": 0.511315180907539,
          "instance_id": 9,
          "label": "storage cabinet",
          "pixel_share": 0.31580729166666666
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__1b75758486.npz",
      "raster_sha256": "19e06b35182cd53beeac3462a23b4864a5c380256f870618807855765beb612a",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            0.732183104317611,
            2.660998608384493
          ],
          [
            4.9528279500236945,
            6.480217881104727
          ],
          [
            3.062121489808708,
            5.964908702109188
          ]
        ],
        "pair": [
          0,
          1
        ],
        "perpendicular_distance": 0.8865030483324068,
        "projection": 0.6929631594990354,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.692124275409225,
        "third": 2
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_0ea1ac22c6ad574131c08fd0",
    "source_row_sha256": "c2db4c8a215ac1166bf45529c03b8a9e154c4d8a39c314fee1cea50e95d1640e",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_9a1ea173fe2cb99c_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vddece0ae5dce",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      322,
      644,
      966,
      1288,
      1610,
      1932,
      2254,
      2576,
      2898,
      3220,
      3543,
      3865,
      4187,
      4509,
      4831,
      5153,
      5475,
      5797,
      6119,
      6441,
      6764,
      7086,
      7408,
      7730,
      8052,
      8374,
      8696,
      9018,
      9340,
      9662,
      9985
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f7/f704b78dead3cee906bb95c1f03f1a869d30c000df800257dd46b53422a74457.png",
        "sha256": "f704b78dead3cee906bb95c1f03f1a869d30c000df800257dd46b53422a74457"
      },
      {
        "path": "/data2/k6tk/c9/c9c0c64de069adc5d28bb560580aa30928364d3af76cdf73df99e295f97a63f1.png",
        "sha256": "c9c0c64de069adc5d28bb560580aa30928364d3af76cdf73df99e295f97a63f1"
      },
      {
        "path": "/data2/k6tk/29/2901dcb646714753d57aa18a1155afe1497d247ce9bc81de1813e74f564d585b.png",
        "sha256": "2901dcb646714753d57aa18a1155afe1497d247ce9bc81de1813e74f564d585b"
      },
      {
        "path": "/data2/k6tk/73/731c07493d673f3cdb7b3ebc9719ffa98e6f2e53089a58c7727c8431270b0c15.png",
        "sha256": "731c07493d673f3cdb7b3ebc9719ffa98e6f2e53089a58c7727c8431270b0c15"
      },
      {
        "path": "/data2/k6tk/49/49a79d6ff3cf3f904e98086e2362633671761545c7ce7f9f441ce19c7c632c96.png",
        "sha256": "49a79d6ff3cf3f904e98086e2362633671761545c7ce7f9f441ce19c7c632c96"
      },
      {
        "path": "/data2/k6tk/2f/2fb7be8620053b27af6ea2076487587cb4b89f873951d6349c6d156067b8487d.png",
        "sha256": "2fb7be8620053b27af6ea2076487587cb4b89f873951d6349c6d156067b8487d"
      },
      {
        "path": "/data2/k6tk/1b/1b778ea73fa02accd7bdda8cfb584190753469d11a7fa0fa9f584f70b3cffe0e.png",
        "sha256": "1b778ea73fa02accd7bdda8cfb584190753469d11a7fa0fa9f584f70b3cffe0e"
      },
      {
        "path": "/data2/k6tk/d8/d8bac00d850f2a7546fa6bfeda99ee0cc9614ff1191bcbdd47d428df50d93cde.png",
        "sha256": "d8bac00d850f2a7546fa6bfeda99ee0cc9614ff1191bcbdd47d428df50d93cde"
      },
      {
        "path": "/data2/k6tk/78/78a3f7dc1db15aaad9a571c47a850c74d5ae1c826b9ea847d6cbe491c0421b7e.png",
        "sha256": "78a3f7dc1db15aaad9a571c47a850c74d5ae1c826b9ea847d6cbe491c0421b7e"
      },
      {
        "path": "/data2/k6tk/9e/9e8c053154dc76a915c411c5f74d82d14290817e598434fc08e3778190fa3217.png",
        "sha256": "9e8c053154dc76a915c411c5f74d82d14290817e598434fc08e3778190fa3217"
      },
      {
        "path": "/data2/k6tk/84/84c76593588d388aa5334007cf39605f418f84ceec38eeed9f6b207ee1adb28e.png",
        "sha256": "84c76593588d388aa5334007cf39605f418f84ceec38eeed9f6b207ee1adb28e"
      },
      {
        "path": "/data2/k6tk/9a/9ab3e1171e18133e7d69a3811d7dc28204e2e685486ac00dcb2abb7ca8e402a5.png",
        "sha256": "9ab3e1171e18133e7d69a3811d7dc28204e2e685486ac00dcb2abb7ca8e402a5"
      },
      {
        "path": "/data2/k6tk/c4/c43cba607688c30609b77eb1999c743cceef064ff4b9eda83d865f1b76d47f3a.png",
        "sha256": "c43cba607688c30609b77eb1999c743cceef064ff4b9eda83d865f1b76d47f3a"
      },
      {
        "path": "/data2/k6tk/16/169f2356ed583a0b65852d39e7f31ff954fa19601daa4e5852559aef0f96a1e3.png",
        "sha256": "169f2356ed583a0b65852d39e7f31ff954fa19601daa4e5852559aef0f96a1e3"
      },
      {
        "path": "/data2/k6tk/d5/d5d00be0d2da46b80d51b41f81f8e06de39cda4e8d847bc7a7adfa22dc8d8226.png",
        "sha256": "d5d00be0d2da46b80d51b41f81f8e06de39cda4e8d847bc7a7adfa22dc8d8226"
      },
      {
        "path": "/data2/k6tk/b9/b9b395787b9533fa35a0eb9857cf163eacf3732c8ee734e0927c3c4f17f04be9.png",
        "sha256": "b9b395787b9533fa35a0eb9857cf163eacf3732c8ee734e0927c3c4f17f04be9"
      },
      {
        "path": "/data2/k6tk/cc/ccbb5f1eecd267b0647aa233e0f96322d2a9d1b6d463227df2afb58dcb26b3ed.png",
        "sha256": "ccbb5f1eecd267b0647aa233e0f96322d2a9d1b6d463227df2afb58dcb26b3ed"
      },
      {
        "path": "/data2/k6tk/bc/bc2536a03b45b6274c1c8cbf932e83114849c31d4fdde7a7d4410d15b4bd9307.png",
        "sha256": "bc2536a03b45b6274c1c8cbf932e83114849c31d4fdde7a7d4410d15b4bd9307"
      },
      {
        "path": "/data2/k6tk/0e/0ef0eebc044d77f4d52467e2aa859872e8605cf09944262f8d08ef2088397a7c.png",
        "sha256": "0ef0eebc044d77f4d52467e2aa859872e8605cf09944262f8d08ef2088397a7c"
      },
      {
        "path": "/data2/k6tk/5a/5ab5c6e7e918707bae3e08e06b66752c61f1a53b6afe20246f9256c216a75845.png",
        "sha256": "5ab5c6e7e918707bae3e08e06b66752c61f1a53b6afe20246f9256c216a75845"
      },
      {
        "path": "/data2/k6tk/b4/b428468d826d45413973e222c7a93c44cedad1dd9e8ef58e35083ca182cbf5ce.png",
        "sha256": "b428468d826d45413973e222c7a93c44cedad1dd9e8ef58e35083ca182cbf5ce"
      },
      {
        "path": "/data2/k6tk/4b/4be0d478a339f66b4988f469c027f021316c0b634b373f64aa79eb0f6bd331f1.png",
        "sha256": "4be0d478a339f66b4988f469c027f021316c0b634b373f64aa79eb0f6bd331f1"
      },
      {
        "path": "/data2/k6tk/c1/c1a3e3c6b7a4eeb5aca58cd4777547b6947fd26411ce85e394426792d51e6369.png",
        "sha256": "c1a3e3c6b7a4eeb5aca58cd4777547b6947fd26411ce85e394426792d51e6369"
      },
      {
        "path": "/data2/k6tk/61/613804a896b53576d555c86db8be1d3be17ff5d16ce9923ccb65e5947264806f.png",
        "sha256": "613804a896b53576d555c86db8be1d3be17ff5d16ce9923ccb65e5947264806f"
      },
      {
        "path": "/data2/k6tk/62/62f02d1ab994b94ecb74cc011ea96a46502a31844ca2c0aa75a4aa5ce2168312.png",
        "sha256": "62f02d1ab994b94ecb74cc011ea96a46502a31844ca2c0aa75a4aa5ce2168312"
      },
      {
        "path": "/data2/k6tk/5a/5ae60c526a3f5e6032a5712857d17c6318e560114616bfed4bb5aac4594a21b4.png",
        "sha256": "5ae60c526a3f5e6032a5712857d17c6318e560114616bfed4bb5aac4594a21b4"
      },
      {
        "path": "/data2/k6tk/62/626d34dc4edcc0210f9e4e48fa05a199caf0b7d966d1e8404abad1e6ea8be829.png",
        "sha256": "626d34dc4edcc0210f9e4e48fa05a199caf0b7d966d1e8404abad1e6ea8be829"
      },
      {
        "path": "/data2/k6tk/c3/c314c547606c7f6cef98ac3a9b82dd6e3feb4f7500d2166aa0e35307cf709e6e.png",
        "sha256": "c314c547606c7f6cef98ac3a9b82dd6e3feb4f7500d2166aa0e35307cf709e6e"
      },
      {
        "path": "/data2/k6tk/85/854ee4a70501acac168653327a7996c3b15dcf785e9e122f320630f4064dd857.png",
        "sha256": "854ee4a70501acac168653327a7996c3b15dcf785e9e122f320630f4064dd857"
      },
      {
        "path": "/data2/k6tk/fc/fc128563e578dc0a4beab1073a018542aa224c0d00cc26f269d4b38db23a9fea.png",
        "sha256": "fc128563e578dc0a4beab1073a018542aa224c0d00cc26f269d4b38db23a9fea"
      },
      {
        "path": "/data2/k6tk/d5/d572bb24d22b9c02bcb5a860a5e3c916d565bce15bf4c42879af2e74c942af6c.png",
        "sha256": "d572bb24d22b9c02bcb5a860a5e3c916d565bce15bf4c42879af2e74c942af6c"
      },
      {
        "path": "/data2/k6tk/5d/5d5ed84d236a713ba17a3706b240acbe39bd6a646959df395b156117cd581774.png",
        "sha256": "5d5ed84d236a713ba17a3706b240acbe39bd6a646959df395b156117cd581774"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.366666666666666,
      10.733333333333333,
      16.1,
      21.466666666666665,
      26.833333333333332,
      32.2,
      37.56666666666667,
      42.93333333333333,
      48.3,
      53.666666666666664,
      59.05,
      64.41666666666667,
      69.78333333333333,
      75.15,
      80.51666666666667,
      85.88333333333334,
      91.25,
      96.61666666666666,
      101.98333333333333,
      107.35,
      112.73333333333333,
      118.1,
      123.46666666666667,
      128.83333333333334,
      134.2,
      139.56666666666666,
      144.93333333333334,
      150.3,
      155.66666666666666,
      161.03333333333333,
      166.41666666666666
    ],
    "total_num_frames": 9986
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: bookshelf in frame 20; door in frame 30; storage cabinet in frame 29.\nOf these, the bookshelf and the door are farthest apart, with the storage cabinet between them.\n</think>\n\n42.85",
  "validation_commit": ""
}
```

## sb_rowLR_9a1ea173fe2cb99c_q1

```json
{
  "answer": "42.85",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-10b7e7fb8aeaa9de441d44f2e3193e9a459d811bbe0c14b80d4af3477ba6a043",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vddece0ae5dce",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        322,
        644,
        966,
        1288,
        1610,
        1932,
        2254,
        2576,
        2898,
        3220,
        3543,
        3865,
        4187,
        4509,
        4831,
        5153,
        5475,
        5797,
        6119,
        6441,
        6764,
        7086,
        7408,
        7730,
        8052,
        8374,
        8696,
        9018,
        9340,
        9662,
        9985
      ],
      "options": [],
      "qid": "sb_rowLR_9a1ea173fe2cb99c_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/1b75758486",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/1b75758486",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      322,
      644,
      966,
      1288,
      1610,
      1932,
      2254,
      2576,
      2898,
      3220,
      3543,
      3865,
      4187,
      4509,
      4831,
      5153,
      5475,
      5797,
      6119,
      6441,
      6764,
      7086,
      7408,
      7730,
      8052,
      8374,
      8696,
      9018,
      9340,
      9662,
      9985
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__1b75758486.npz": "19e06b35182cd53beeac3462a23b4864a5c380256f870618807855765beb612a",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/1b75758486",
    "room_measurement": {
      "area_m2": 42.847500000000004,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 17139,
      "floor_height_m": 0.13526197507202786,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 11886
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 20,
          "centroid": [
            0.732183104317611,
            2.660998608384493,
            1.0672707185149193
          ],
          "footprint": 1.3267199492662134,
          "instance_id": 40,
          "label": "bookshelf",
          "pixel_share": 0.2996744791666667
        },
        {
          "best_view": 30,
          "centroid": [
            4.9528279500236945,
            6.480217881104727,
            1.2600806951522827
          ],
          "footprint": 1.1042100608606777,
          "instance_id": 39,
          "label": "door",
          "pixel_share": 0.61609375
        },
        {
          "best_view": 29,
          "centroid": [
            3.062121489808708,
            5.964908702109188,
            1.2207441329956057
          ],
          "footprint": 0.511315180907539,
          "instance_id": 9,
          "label": "storage cabinet",
          "pixel_share": 0.31580729166666666
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__1b75758486.npz",
      "raster_sha256": "19e06b35182cd53beeac3462a23b4864a5c380256f870618807855765beb612a",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            0.732183104317611,
            2.660998608384493
          ],
          [
            4.9528279500236945,
            6.480217881104727
          ],
          [
            3.062121489808708,
            5.964908702109188
          ]
        ],
        "pair": [
          0,
          1
        ],
        "perpendicular_distance": 0.8865030483324068,
        "projection": 0.6929631594990354,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.692124275409225,
        "third": 2
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "vstirel_0ea1ac22c6ad574131c08fd0",
    "source_row_sha256": "c2db4c8a215ac1166bf45529c03b8a9e154c4d8a39c314fee1cea50e95d1640e",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_9a1ea173fe2cb99c_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vddece0ae5dce",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      322,
      644,
      966,
      1288,
      1610,
      1932,
      2254,
      2576,
      2898,
      3220,
      3543,
      3865,
      4187,
      4509,
      4831,
      5153,
      5475,
      5797,
      6119,
      6441,
      6764,
      7086,
      7408,
      7730,
      8052,
      8374,
      8696,
      9018,
      9340,
      9662,
      9985
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f7/f704b78dead3cee906bb95c1f03f1a869d30c000df800257dd46b53422a74457.png",
        "sha256": "f704b78dead3cee906bb95c1f03f1a869d30c000df800257dd46b53422a74457"
      },
      {
        "path": "/data2/k6tk/c9/c9c0c64de069adc5d28bb560580aa30928364d3af76cdf73df99e295f97a63f1.png",
        "sha256": "c9c0c64de069adc5d28bb560580aa30928364d3af76cdf73df99e295f97a63f1"
      },
      {
        "path": "/data2/k6tk/29/2901dcb646714753d57aa18a1155afe1497d247ce9bc81de1813e74f564d585b.png",
        "sha256": "2901dcb646714753d57aa18a1155afe1497d247ce9bc81de1813e74f564d585b"
      },
      {
        "path": "/data2/k6tk/73/731c07493d673f3cdb7b3ebc9719ffa98e6f2e53089a58c7727c8431270b0c15.png",
        "sha256": "731c07493d673f3cdb7b3ebc9719ffa98e6f2e53089a58c7727c8431270b0c15"
      },
      {
        "path": "/data2/k6tk/49/49a79d6ff3cf3f904e98086e2362633671761545c7ce7f9f441ce19c7c632c96.png",
        "sha256": "49a79d6ff3cf3f904e98086e2362633671761545c7ce7f9f441ce19c7c632c96"
      },
      {
        "path": "/data2/k6tk/2f/2fb7be8620053b27af6ea2076487587cb4b89f873951d6349c6d156067b8487d.png",
        "sha256": "2fb7be8620053b27af6ea2076487587cb4b89f873951d6349c6d156067b8487d"
      },
      {
        "path": "/data2/k6tk/1b/1b778ea73fa02accd7bdda8cfb584190753469d11a7fa0fa9f584f70b3cffe0e.png",
        "sha256": "1b778ea73fa02accd7bdda8cfb584190753469d11a7fa0fa9f584f70b3cffe0e"
      },
      {
        "path": "/data2/k6tk/d8/d8bac00d850f2a7546fa6bfeda99ee0cc9614ff1191bcbdd47d428df50d93cde.png",
        "sha256": "d8bac00d850f2a7546fa6bfeda99ee0cc9614ff1191bcbdd47d428df50d93cde"
      },
      {
        "path": "/data2/k6tk/78/78a3f7dc1db15aaad9a571c47a850c74d5ae1c826b9ea847d6cbe491c0421b7e.png",
        "sha256": "78a3f7dc1db15aaad9a571c47a850c74d5ae1c826b9ea847d6cbe491c0421b7e"
      },
      {
        "path": "/data2/k6tk/9e/9e8c053154dc76a915c411c5f74d82d14290817e598434fc08e3778190fa3217.png",
        "sha256": "9e8c053154dc76a915c411c5f74d82d14290817e598434fc08e3778190fa3217"
      },
      {
        "path": "/data2/k6tk/84/84c76593588d388aa5334007cf39605f418f84ceec38eeed9f6b207ee1adb28e.png",
        "sha256": "84c76593588d388aa5334007cf39605f418f84ceec38eeed9f6b207ee1adb28e"
      },
      {
        "path": "/data2/k6tk/9a/9ab3e1171e18133e7d69a3811d7dc28204e2e685486ac00dcb2abb7ca8e402a5.png",
        "sha256": "9ab3e1171e18133e7d69a3811d7dc28204e2e685486ac00dcb2abb7ca8e402a5"
      },
      {
        "path": "/data2/k6tk/c4/c43cba607688c30609b77eb1999c743cceef064ff4b9eda83d865f1b76d47f3a.png",
        "sha256": "c43cba607688c30609b77eb1999c743cceef064ff4b9eda83d865f1b76d47f3a"
      },
      {
        "path": "/data2/k6tk/16/169f2356ed583a0b65852d39e7f31ff954fa19601daa4e5852559aef0f96a1e3.png",
        "sha256": "169f2356ed583a0b65852d39e7f31ff954fa19601daa4e5852559aef0f96a1e3"
      },
      {
        "path": "/data2/k6tk/d5/d5d00be0d2da46b80d51b41f81f8e06de39cda4e8d847bc7a7adfa22dc8d8226.png",
        "sha256": "d5d00be0d2da46b80d51b41f81f8e06de39cda4e8d847bc7a7adfa22dc8d8226"
      },
      {
        "path": "/data2/k6tk/b9/b9b395787b9533fa35a0eb9857cf163eacf3732c8ee734e0927c3c4f17f04be9.png",
        "sha256": "b9b395787b9533fa35a0eb9857cf163eacf3732c8ee734e0927c3c4f17f04be9"
      },
      {
        "path": "/data2/k6tk/cc/ccbb5f1eecd267b0647aa233e0f96322d2a9d1b6d463227df2afb58dcb26b3ed.png",
        "sha256": "ccbb5f1eecd267b0647aa233e0f96322d2a9d1b6d463227df2afb58dcb26b3ed"
      },
      {
        "path": "/data2/k6tk/bc/bc2536a03b45b6274c1c8cbf932e83114849c31d4fdde7a7d4410d15b4bd9307.png",
        "sha256": "bc2536a03b45b6274c1c8cbf932e83114849c31d4fdde7a7d4410d15b4bd9307"
      },
      {
        "path": "/data2/k6tk/0e/0ef0eebc044d77f4d52467e2aa859872e8605cf09944262f8d08ef2088397a7c.png",
        "sha256": "0ef0eebc044d77f4d52467e2aa859872e8605cf09944262f8d08ef2088397a7c"
      },
      {
        "path": "/data2/k6tk/5a/5ab5c6e7e918707bae3e08e06b66752c61f1a53b6afe20246f9256c216a75845.png",
        "sha256": "5ab5c6e7e918707bae3e08e06b66752c61f1a53b6afe20246f9256c216a75845"
      },
      {
        "path": "/data2/k6tk/b4/b428468d826d45413973e222c7a93c44cedad1dd9e8ef58e35083ca182cbf5ce.png",
        "sha256": "b428468d826d45413973e222c7a93c44cedad1dd9e8ef58e35083ca182cbf5ce"
      },
      {
        "path": "/data2/k6tk/4b/4be0d478a339f66b4988f469c027f021316c0b634b373f64aa79eb0f6bd331f1.png",
        "sha256": "4be0d478a339f66b4988f469c027f021316c0b634b373f64aa79eb0f6bd331f1"
      },
      {
        "path": "/data2/k6tk/c1/c1a3e3c6b7a4eeb5aca58cd4777547b6947fd26411ce85e394426792d51e6369.png",
        "sha256": "c1a3e3c6b7a4eeb5aca58cd4777547b6947fd26411ce85e394426792d51e6369"
      },
      {
        "path": "/data2/k6tk/61/613804a896b53576d555c86db8be1d3be17ff5d16ce9923ccb65e5947264806f.png",
        "sha256": "613804a896b53576d555c86db8be1d3be17ff5d16ce9923ccb65e5947264806f"
      },
      {
        "path": "/data2/k6tk/62/62f02d1ab994b94ecb74cc011ea96a46502a31844ca2c0aa75a4aa5ce2168312.png",
        "sha256": "62f02d1ab994b94ecb74cc011ea96a46502a31844ca2c0aa75a4aa5ce2168312"
      },
      {
        "path": "/data2/k6tk/5a/5ae60c526a3f5e6032a5712857d17c6318e560114616bfed4bb5aac4594a21b4.png",
        "sha256": "5ae60c526a3f5e6032a5712857d17c6318e560114616bfed4bb5aac4594a21b4"
      },
      {
        "path": "/data2/k6tk/62/626d34dc4edcc0210f9e4e48fa05a199caf0b7d966d1e8404abad1e6ea8be829.png",
        "sha256": "626d34dc4edcc0210f9e4e48fa05a199caf0b7d966d1e8404abad1e6ea8be829"
      },
      {
        "path": "/data2/k6tk/c3/c314c547606c7f6cef98ac3a9b82dd6e3feb4f7500d2166aa0e35307cf709e6e.png",
        "sha256": "c314c547606c7f6cef98ac3a9b82dd6e3feb4f7500d2166aa0e35307cf709e6e"
      },
      {
        "path": "/data2/k6tk/85/854ee4a70501acac168653327a7996c3b15dcf785e9e122f320630f4064dd857.png",
        "sha256": "854ee4a70501acac168653327a7996c3b15dcf785e9e122f320630f4064dd857"
      },
      {
        "path": "/data2/k6tk/fc/fc128563e578dc0a4beab1073a018542aa224c0d00cc26f269d4b38db23a9fea.png",
        "sha256": "fc128563e578dc0a4beab1073a018542aa224c0d00cc26f269d4b38db23a9fea"
      },
      {
        "path": "/data2/k6tk/d5/d572bb24d22b9c02bcb5a860a5e3c916d565bce15bf4c42879af2e74c942af6c.png",
        "sha256": "d572bb24d22b9c02bcb5a860a5e3c916d565bce15bf4c42879af2e74c942af6c"
      },
      {
        "path": "/data2/k6tk/5d/5d5ed84d236a713ba17a3706b240acbe39bd6a646959df395b156117cd581774.png",
        "sha256": "5d5ed84d236a713ba17a3706b240acbe39bd6a646959df395b156117cd581774"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      5.366666666666666,
      10.733333333333333,
      16.1,
      21.466666666666665,
      26.833333333333332,
      32.2,
      37.56666666666667,
      42.93333333333333,
      48.3,
      53.666666666666664,
      59.05,
      64.41666666666667,
      69.78333333333333,
      75.15,
      80.51666666666667,
      85.88333333333334,
      91.25,
      96.61666666666666,
      101.98333333333333,
      107.35,
      112.73333333333333,
      118.1,
      123.46666666666667,
      128.83333333333334,
      134.2,
      139.56666666666666,
      144.93333333333334,
      150.3,
      155.66666666666666,
      161.03333333333333,
      166.41666666666666
    ],
    "total_num_frames": 9986
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: bookshelf in frame 20; door in frame 30; storage cabinet in frame 29.\nThe bookshelf and the door are the farthest apart among these landmarks, with the storage cabinet between them.\n</think>\n\n42.85",
  "validation_commit": ""
}
```

## sb_rowLR_0cf456a768ae1748_q0

```json
{
  "answer": "52.88",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-5d6d863ac8eefce604fef83702a9e3dd16f8cfa6d6c82ac6671424ba0166d79c",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v2c05c423edce",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        418,
        836,
        1254,
        1672,
        2090,
        2509,
        2927,
        3345,
        3763,
        4181,
        4600,
        5018,
        5436,
        5854,
        6272,
        6691,
        7109,
        7527,
        7945,
        8363,
        8782,
        9200,
        9618,
        10036,
        10454,
        10873,
        11291,
        11709,
        12127,
        12545,
        12964
      ],
      "options": [],
      "qid": "sb_rowLR_0cf456a768ae1748_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/3aa115e55e",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3aa115e55e",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      418,
      836,
      1254,
      1672,
      2090,
      2509,
      2927,
      3345,
      3763,
      4181,
      4600,
      5018,
      5436,
      5854,
      6272,
      6691,
      7109,
      7527,
      7945,
      8363,
      8782,
      9200,
      9618,
      10036,
      10454,
      10873,
      11291,
      11709,
      12127,
      12545,
      12964
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3aa115e55e.npz": "e5a5f6cca6368151d3515695fb627be46b3437b1dacfe59b9e58580d47adeea3",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3aa115e55e",
    "room_measurement": {
      "area_m2": 52.88250000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 21153,
      "floor_height_m": 0.1486045029787181,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 17837
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 6,
          "centroid": [
            0.5805466009622808,
            5.104415812076509,
            2.339073926210404
          ],
          "footprint": 2.6176645676693244,
          "instance_id": 42,
          "label": "projector screen",
          "pixel_share": 0.42173177083333335
        },
        {
          "best_view": 2,
          "centroid": [
            3.5300209992502536,
            0.7322784869876515,
            0.5740740522742271
          ],
          "footprint": 1.1326406970690361,
          "instance_id": 116,
          "label": "heater",
          "pixel_share": 0.049375
        },
        {
          "best_view": 20,
          "centroid": [
            3.528888246344536,
            0.6641584759935961,
            1.1001657843589783
          ],
          "footprint": 0.7533283679258483,
          "instance_id": 8,
          "label": "windowsill",
          "pixel_share": 0.020989583333333332
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3aa115e55e.npz",
      "raster_sha256": "e5a5f6cca6368151d3515695fb627be46b3437b1dacfe59b9e58580d47adeea3",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            0.5805466009622808,
            5.104415812076509
          ],
          [
            3.5300209992502536,
            0.7322784869876515
          ],
          [
            3.528888246344536,
            0.6641584759935961
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 0.03862511321168694,
        "projection": 0.9894704210219288,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.3299722014784905,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "vstirel_22b2efdca49969d8ceb06e1b",
    "source_row_sha256": "a0577f09c308ea02f75effd6b2276a697fe5418c159b8b32b9221b88271e94d7",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_0cf456a768ae1748_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v2c05c423edce",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      418,
      836,
      1254,
      1672,
      2090,
      2509,
      2927,
      3345,
      3763,
      4181,
      4600,
      5018,
      5436,
      5854,
      6272,
      6691,
      7109,
      7527,
      7945,
      8363,
      8782,
      9200,
      9618,
      10036,
      10454,
      10873,
      11291,
      11709,
      12127,
      12545,
      12964
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e2/e26204f2d495e3d864f93455333a76d36400f73c938ac4eb818ffe07eb9fc26a.png",
        "sha256": "e26204f2d495e3d864f93455333a76d36400f73c938ac4eb818ffe07eb9fc26a"
      },
      {
        "path": "/data2/k6tk/09/0920537b6a524d5a9d64d78337ac45f5f7684dfa7948d2dbe0aba1535b20d456.png",
        "sha256": "0920537b6a524d5a9d64d78337ac45f5f7684dfa7948d2dbe0aba1535b20d456"
      },
      {
        "path": "/data2/k6tk/a9/a978dd043a3fd02ed020bd568aaa22a8d1a674eebd6e3416e0e8a355073d421d.png",
        "sha256": "a978dd043a3fd02ed020bd568aaa22a8d1a674eebd6e3416e0e8a355073d421d"
      },
      {
        "path": "/data2/k6tk/ac/ac9678f75b3ebd5dc57f39f45caf07f8bd6b865a9b3cfdd62a96e9695826fa0f.png",
        "sha256": "ac9678f75b3ebd5dc57f39f45caf07f8bd6b865a9b3cfdd62a96e9695826fa0f"
      },
      {
        "path": "/data2/k6tk/fe/fe2ab289094e1e9f885ed2a84586026a523484a8aeaa58b1a9f7b8c59218f8b4.png",
        "sha256": "fe2ab289094e1e9f885ed2a84586026a523484a8aeaa58b1a9f7b8c59218f8b4"
      },
      {
        "path": "/data2/k6tk/44/4489a997a9fb671cc1d0921e2c24d2ef4f959f23269bf3a586bc32f7523cac34.png",
        "sha256": "4489a997a9fb671cc1d0921e2c24d2ef4f959f23269bf3a586bc32f7523cac34"
      },
      {
        "path": "/data2/k6tk/b9/b9d8c5548802b7583c989aef6b0391c2c364f96c36ee4f66b08399424a2b10bc.png",
        "sha256": "b9d8c5548802b7583c989aef6b0391c2c364f96c36ee4f66b08399424a2b10bc"
      },
      {
        "path": "/data2/k6tk/ac/ace624c7b0732436ba0f41f79a6937d0ccad51ea64ac60ffbcf7623d4259c138.png",
        "sha256": "ace624c7b0732436ba0f41f79a6937d0ccad51ea64ac60ffbcf7623d4259c138"
      },
      {
        "path": "/data2/k6tk/35/35f8ae7d464187056737c4b45bbf48dc8c6d2688075a75e9ea23cf74a840cc29.png",
        "sha256": "35f8ae7d464187056737c4b45bbf48dc8c6d2688075a75e9ea23cf74a840cc29"
      },
      {
        "path": "/data2/k6tk/a2/a27791f6c0b8460ba17d80b7ef1ad689b7e3d66af4ed867ed647a268649c3b0a.png",
        "sha256": "a27791f6c0b8460ba17d80b7ef1ad689b7e3d66af4ed867ed647a268649c3b0a"
      },
      {
        "path": "/data2/k6tk/42/424f326481b87e47259bf88fd8f925f176d04c8e0c7ccc7ae5d59fe4de5e7d98.png",
        "sha256": "424f326481b87e47259bf88fd8f925f176d04c8e0c7ccc7ae5d59fe4de5e7d98"
      },
      {
        "path": "/data2/k6tk/04/04dab9a958071d86213b83aa56a9eb2b1eaa6ff74500b55bda7d1c5f6e9ffa90.png",
        "sha256": "04dab9a958071d86213b83aa56a9eb2b1eaa6ff74500b55bda7d1c5f6e9ffa90"
      },
      {
        "path": "/data2/k6tk/7c/7cacc6448d373d9b832e6b5c99f1b569ab1579c0270b49c5eca19b6a62534255.png",
        "sha256": "7cacc6448d373d9b832e6b5c99f1b569ab1579c0270b49c5eca19b6a62534255"
      },
      {
        "path": "/data2/k6tk/c3/c3de6a6c146db503be3c4d31c493a301b40178d1c6a57a84b26bb567a93a0a97.png",
        "sha256": "c3de6a6c146db503be3c4d31c493a301b40178d1c6a57a84b26bb567a93a0a97"
      },
      {
        "path": "/data2/k6tk/7e/7e42dc7577b354a2eaa4648de91ad72bd79a232c4db2fb073c0381b59616901b.png",
        "sha256": "7e42dc7577b354a2eaa4648de91ad72bd79a232c4db2fb073c0381b59616901b"
      },
      {
        "path": "/data2/k6tk/9a/9a3cffc5bffa742e6562ec9eca1428a1a304da2251cdc58d1984abf5a0e33b8f.png",
        "sha256": "9a3cffc5bffa742e6562ec9eca1428a1a304da2251cdc58d1984abf5a0e33b8f"
      },
      {
        "path": "/data2/k6tk/b5/b55165872ddd1cd78b19670ccadf8b0059da2aed1ca2c9d4dfdb52b2e2fe67ce.png",
        "sha256": "b55165872ddd1cd78b19670ccadf8b0059da2aed1ca2c9d4dfdb52b2e2fe67ce"
      },
      {
        "path": "/data2/k6tk/d2/d2516bd1bf139b41b9254c9e3b2d40a89e511b2fb3afd489e3a488793dc27782.png",
        "sha256": "d2516bd1bf139b41b9254c9e3b2d40a89e511b2fb3afd489e3a488793dc27782"
      },
      {
        "path": "/data2/k6tk/9f/9f0e05aa6a9aba2c3c4aa48f4db81e7a58520e96acb305f51ff4e239a9559753.png",
        "sha256": "9f0e05aa6a9aba2c3c4aa48f4db81e7a58520e96acb305f51ff4e239a9559753"
      },
      {
        "path": "/data2/k6tk/97/97b73261862ebe133a4138400ce9376dfaa4913c5beaf3be3f30dfbd704117dc.png",
        "sha256": "97b73261862ebe133a4138400ce9376dfaa4913c5beaf3be3f30dfbd704117dc"
      },
      {
        "path": "/data2/k6tk/44/44312d6f20cecf027af8a4089c8f373afbdf6873ded34627420d3283e426a583.png",
        "sha256": "44312d6f20cecf027af8a4089c8f373afbdf6873ded34627420d3283e426a583"
      },
      {
        "path": "/data2/k6tk/99/99615720bb8c4184b672166ea329ebb4b2ef3632e175ead0f776f1111958be1c.png",
        "sha256": "99615720bb8c4184b672166ea329ebb4b2ef3632e175ead0f776f1111958be1c"
      },
      {
        "path": "/data2/k6tk/be/beadefe588125092df2f17e3d33d4246843d19f033900adb66c558a26c0d1346.png",
        "sha256": "beadefe588125092df2f17e3d33d4246843d19f033900adb66c558a26c0d1346"
      },
      {
        "path": "/data2/k6tk/dd/ddf2c927c51924e809fc48b291cae64e9d382b055ba82d4690d5648d06d322b0.png",
        "sha256": "ddf2c927c51924e809fc48b291cae64e9d382b055ba82d4690d5648d06d322b0"
      },
      {
        "path": "/data2/k6tk/e8/e81c6644735b3dbbf351d71729f4cb0c9cc5bb939ac2d758a3029c43f38ddccd.png",
        "sha256": "e81c6644735b3dbbf351d71729f4cb0c9cc5bb939ac2d758a3029c43f38ddccd"
      },
      {
        "path": "/data2/k6tk/5b/5b9cb25810b256c312731918eca5c09bbd2e4fc1dd67f9c7b9a4263167c145d3.png",
        "sha256": "5b9cb25810b256c312731918eca5c09bbd2e4fc1dd67f9c7b9a4263167c145d3"
      },
      {
        "path": "/data2/k6tk/80/80f5d3485af957aaf8b7f7d14ab26f0873bbca80374f43bbec4548718054f8bd.png",
        "sha256": "80f5d3485af957aaf8b7f7d14ab26f0873bbca80374f43bbec4548718054f8bd"
      },
      {
        "path": "/data2/k6tk/1b/1b30ae6f50be6cfb313a99079db57c3ea9d4d404cb772fdc8955f2e4c86f2935.png",
        "sha256": "1b30ae6f50be6cfb313a99079db57c3ea9d4d404cb772fdc8955f2e4c86f2935"
      },
      {
        "path": "/data2/k6tk/a5/a548127f289d8ec9f612f320a373cc1edcc209779ac6672e6a61302b8e6874dd.png",
        "sha256": "a548127f289d8ec9f612f320a373cc1edcc209779ac6672e6a61302b8e6874dd"
      },
      {
        "path": "/data2/k6tk/d8/d843f2d911aab9875cac74771b2ba064b883e7fc4ef09e18ff0f5c05d420c304.png",
        "sha256": "d843f2d911aab9875cac74771b2ba064b883e7fc4ef09e18ff0f5c05d420c304"
      },
      {
        "path": "/data2/k6tk/9e/9ea990687d97b06fa7121079317aedccce57c3afb290f597a95de7671b97dcd5.png",
        "sha256": "9ea990687d97b06fa7121079317aedccce57c3afb290f597a95de7671b97dcd5"
      },
      {
        "path": "/data2/k6tk/ec/ec9c940d3ce1ba5469eeb4d638a24900fe2d10a988beb4d60a7c3b5721ae37df.png",
        "sha256": "ec9c940d3ce1ba5469eeb4d638a24900fe2d10a988beb4d60a7c3b5721ae37df"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      6.966666666666667,
      13.933333333333334,
      20.9,
      27.866666666666667,
      34.833333333333336,
      41.81666666666667,
      48.78333333333333,
      55.75,
      62.71666666666667,
      69.68333333333334,
      76.66666666666667,
      83.63333333333334,
      90.6,
      97.56666666666666,
      104.53333333333333,
      111.51666666666667,
      118.48333333333333,
      125.45,
      132.41666666666666,
      139.38333333333333,
      146.36666666666667,
      153.33333333333334,
      160.3,
      167.26666666666668,
      174.23333333333332,
      181.21666666666667,
      188.18333333333334,
      195.15,
      202.11666666666667,
      209.08333333333334,
      216.06666666666666
    ],
    "total_num_frames": 12965
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: projector screen in frame 6; heater in frame 2; windowsill in frame 20.\nThe projector screen and the windowsill are the farthest apart among these landmarks, with the heater to the side of that pair.\n</think>\n\n52.88",
  "validation_commit": ""
}
```

## sb_rowLR_0cf456a768ae1748_q1

```json
{
  "answer": "52.88",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-533192732f3f55f293087c74976372da2530835ffd62d4dd056f71cce06ea00e",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v2c05c423edce",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        418,
        836,
        1254,
        1672,
        2090,
        2509,
        2927,
        3345,
        3763,
        4181,
        4600,
        5018,
        5436,
        5854,
        6272,
        6691,
        7109,
        7527,
        7945,
        8363,
        8782,
        9200,
        9618,
        10036,
        10454,
        10873,
        11291,
        11709,
        12127,
        12545,
        12964
      ],
      "options": [],
      "qid": "sb_rowLR_0cf456a768ae1748_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/3aa115e55e",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3aa115e55e",
    "details": {
      "cell": "scannetpp|40-60",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      418,
      836,
      1254,
      1672,
      2090,
      2509,
      2927,
      3345,
      3763,
      4181,
      4600,
      5018,
      5436,
      5854,
      6272,
      6691,
      7109,
      7527,
      7945,
      8363,
      8782,
      9200,
      9618,
      10036,
      10454,
      10873,
      11291,
      11709,
      12127,
      12545,
      12964
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3aa115e55e.npz": "e5a5f6cca6368151d3515695fb627be46b3437b1dacfe59b9e58580d47adeea3",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3aa115e55e",
    "room_measurement": {
      "area_m2": 52.88250000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 21153,
      "floor_height_m": 0.1486045029787181,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 17837
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 6,
          "centroid": [
            0.5805466009622808,
            5.104415812076509,
            2.339073926210404
          ],
          "footprint": 2.6176645676693244,
          "instance_id": 42,
          "label": "projector screen",
          "pixel_share": 0.42173177083333335
        },
        {
          "best_view": 2,
          "centroid": [
            3.5300209992502536,
            0.7322784869876515,
            0.5740740522742271
          ],
          "footprint": 1.1326406970690361,
          "instance_id": 116,
          "label": "heater",
          "pixel_share": 0.049375
        },
        {
          "best_view": 20,
          "centroid": [
            3.528888246344536,
            0.6641584759935961,
            1.1001657843589783
          ],
          "footprint": 0.7533283679258483,
          "instance_id": 8,
          "label": "windowsill",
          "pixel_share": 0.020989583333333332
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3aa115e55e.npz",
      "raster_sha256": "e5a5f6cca6368151d3515695fb627be46b3437b1dacfe59b9e58580d47adeea3",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            0.5805466009622808,
            5.104415812076509
          ],
          [
            3.5300209992502536,
            0.7322784869876515
          ],
          [
            3.528888246344536,
            0.6641584759935961
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 0.03862511321168694,
        "projection": 0.9894704210219288,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.3299722014784905,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_22b2efdca49969d8ceb06e1b",
    "source_row_sha256": "a0577f09c308ea02f75effd6b2276a697fe5418c159b8b32b9221b88271e94d7",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_0cf456a768ae1748_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v2c05c423edce",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      418,
      836,
      1254,
      1672,
      2090,
      2509,
      2927,
      3345,
      3763,
      4181,
      4600,
      5018,
      5436,
      5854,
      6272,
      6691,
      7109,
      7527,
      7945,
      8363,
      8782,
      9200,
      9618,
      10036,
      10454,
      10873,
      11291,
      11709,
      12127,
      12545,
      12964
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e2/e26204f2d495e3d864f93455333a76d36400f73c938ac4eb818ffe07eb9fc26a.png",
        "sha256": "e26204f2d495e3d864f93455333a76d36400f73c938ac4eb818ffe07eb9fc26a"
      },
      {
        "path": "/data2/k6tk/09/0920537b6a524d5a9d64d78337ac45f5f7684dfa7948d2dbe0aba1535b20d456.png",
        "sha256": "0920537b6a524d5a9d64d78337ac45f5f7684dfa7948d2dbe0aba1535b20d456"
      },
      {
        "path": "/data2/k6tk/a9/a978dd043a3fd02ed020bd568aaa22a8d1a674eebd6e3416e0e8a355073d421d.png",
        "sha256": "a978dd043a3fd02ed020bd568aaa22a8d1a674eebd6e3416e0e8a355073d421d"
      },
      {
        "path": "/data2/k6tk/ac/ac9678f75b3ebd5dc57f39f45caf07f8bd6b865a9b3cfdd62a96e9695826fa0f.png",
        "sha256": "ac9678f75b3ebd5dc57f39f45caf07f8bd6b865a9b3cfdd62a96e9695826fa0f"
      },
      {
        "path": "/data2/k6tk/fe/fe2ab289094e1e9f885ed2a84586026a523484a8aeaa58b1a9f7b8c59218f8b4.png",
        "sha256": "fe2ab289094e1e9f885ed2a84586026a523484a8aeaa58b1a9f7b8c59218f8b4"
      },
      {
        "path": "/data2/k6tk/44/4489a997a9fb671cc1d0921e2c24d2ef4f959f23269bf3a586bc32f7523cac34.png",
        "sha256": "4489a997a9fb671cc1d0921e2c24d2ef4f959f23269bf3a586bc32f7523cac34"
      },
      {
        "path": "/data2/k6tk/b9/b9d8c5548802b7583c989aef6b0391c2c364f96c36ee4f66b08399424a2b10bc.png",
        "sha256": "b9d8c5548802b7583c989aef6b0391c2c364f96c36ee4f66b08399424a2b10bc"
      },
      {
        "path": "/data2/k6tk/ac/ace624c7b0732436ba0f41f79a6937d0ccad51ea64ac60ffbcf7623d4259c138.png",
        "sha256": "ace624c7b0732436ba0f41f79a6937d0ccad51ea64ac60ffbcf7623d4259c138"
      },
      {
        "path": "/data2/k6tk/35/35f8ae7d464187056737c4b45bbf48dc8c6d2688075a75e9ea23cf74a840cc29.png",
        "sha256": "35f8ae7d464187056737c4b45bbf48dc8c6d2688075a75e9ea23cf74a840cc29"
      },
      {
        "path": "/data2/k6tk/a2/a27791f6c0b8460ba17d80b7ef1ad689b7e3d66af4ed867ed647a268649c3b0a.png",
        "sha256": "a27791f6c0b8460ba17d80b7ef1ad689b7e3d66af4ed867ed647a268649c3b0a"
      },
      {
        "path": "/data2/k6tk/42/424f326481b87e47259bf88fd8f925f176d04c8e0c7ccc7ae5d59fe4de5e7d98.png",
        "sha256": "424f326481b87e47259bf88fd8f925f176d04c8e0c7ccc7ae5d59fe4de5e7d98"
      },
      {
        "path": "/data2/k6tk/04/04dab9a958071d86213b83aa56a9eb2b1eaa6ff74500b55bda7d1c5f6e9ffa90.png",
        "sha256": "04dab9a958071d86213b83aa56a9eb2b1eaa6ff74500b55bda7d1c5f6e9ffa90"
      },
      {
        "path": "/data2/k6tk/7c/7cacc6448d373d9b832e6b5c99f1b569ab1579c0270b49c5eca19b6a62534255.png",
        "sha256": "7cacc6448d373d9b832e6b5c99f1b569ab1579c0270b49c5eca19b6a62534255"
      },
      {
        "path": "/data2/k6tk/c3/c3de6a6c146db503be3c4d31c493a301b40178d1c6a57a84b26bb567a93a0a97.png",
        "sha256": "c3de6a6c146db503be3c4d31c493a301b40178d1c6a57a84b26bb567a93a0a97"
      },
      {
        "path": "/data2/k6tk/7e/7e42dc7577b354a2eaa4648de91ad72bd79a232c4db2fb073c0381b59616901b.png",
        "sha256": "7e42dc7577b354a2eaa4648de91ad72bd79a232c4db2fb073c0381b59616901b"
      },
      {
        "path": "/data2/k6tk/9a/9a3cffc5bffa742e6562ec9eca1428a1a304da2251cdc58d1984abf5a0e33b8f.png",
        "sha256": "9a3cffc5bffa742e6562ec9eca1428a1a304da2251cdc58d1984abf5a0e33b8f"
      },
      {
        "path": "/data2/k6tk/b5/b55165872ddd1cd78b19670ccadf8b0059da2aed1ca2c9d4dfdb52b2e2fe67ce.png",
        "sha256": "b55165872ddd1cd78b19670ccadf8b0059da2aed1ca2c9d4dfdb52b2e2fe67ce"
      },
      {
        "path": "/data2/k6tk/d2/d2516bd1bf139b41b9254c9e3b2d40a89e511b2fb3afd489e3a488793dc27782.png",
        "sha256": "d2516bd1bf139b41b9254c9e3b2d40a89e511b2fb3afd489e3a488793dc27782"
      },
      {
        "path": "/data2/k6tk/9f/9f0e05aa6a9aba2c3c4aa48f4db81e7a58520e96acb305f51ff4e239a9559753.png",
        "sha256": "9f0e05aa6a9aba2c3c4aa48f4db81e7a58520e96acb305f51ff4e239a9559753"
      },
      {
        "path": "/data2/k6tk/97/97b73261862ebe133a4138400ce9376dfaa4913c5beaf3be3f30dfbd704117dc.png",
        "sha256": "97b73261862ebe133a4138400ce9376dfaa4913c5beaf3be3f30dfbd704117dc"
      },
      {
        "path": "/data2/k6tk/44/44312d6f20cecf027af8a4089c8f373afbdf6873ded34627420d3283e426a583.png",
        "sha256": "44312d6f20cecf027af8a4089c8f373afbdf6873ded34627420d3283e426a583"
      },
      {
        "path": "/data2/k6tk/99/99615720bb8c4184b672166ea329ebb4b2ef3632e175ead0f776f1111958be1c.png",
        "sha256": "99615720bb8c4184b672166ea329ebb4b2ef3632e175ead0f776f1111958be1c"
      },
      {
        "path": "/data2/k6tk/be/beadefe588125092df2f17e3d33d4246843d19f033900adb66c558a26c0d1346.png",
        "sha256": "beadefe588125092df2f17e3d33d4246843d19f033900adb66c558a26c0d1346"
      },
      {
        "path": "/data2/k6tk/dd/ddf2c927c51924e809fc48b291cae64e9d382b055ba82d4690d5648d06d322b0.png",
        "sha256": "ddf2c927c51924e809fc48b291cae64e9d382b055ba82d4690d5648d06d322b0"
      },
      {
        "path": "/data2/k6tk/e8/e81c6644735b3dbbf351d71729f4cb0c9cc5bb939ac2d758a3029c43f38ddccd.png",
        "sha256": "e81c6644735b3dbbf351d71729f4cb0c9cc5bb939ac2d758a3029c43f38ddccd"
      },
      {
        "path": "/data2/k6tk/5b/5b9cb25810b256c312731918eca5c09bbd2e4fc1dd67f9c7b9a4263167c145d3.png",
        "sha256": "5b9cb25810b256c312731918eca5c09bbd2e4fc1dd67f9c7b9a4263167c145d3"
      },
      {
        "path": "/data2/k6tk/80/80f5d3485af957aaf8b7f7d14ab26f0873bbca80374f43bbec4548718054f8bd.png",
        "sha256": "80f5d3485af957aaf8b7f7d14ab26f0873bbca80374f43bbec4548718054f8bd"
      },
      {
        "path": "/data2/k6tk/1b/1b30ae6f50be6cfb313a99079db57c3ea9d4d404cb772fdc8955f2e4c86f2935.png",
        "sha256": "1b30ae6f50be6cfb313a99079db57c3ea9d4d404cb772fdc8955f2e4c86f2935"
      },
      {
        "path": "/data2/k6tk/a5/a548127f289d8ec9f612f320a373cc1edcc209779ac6672e6a61302b8e6874dd.png",
        "sha256": "a548127f289d8ec9f612f320a373cc1edcc209779ac6672e6a61302b8e6874dd"
      },
      {
        "path": "/data2/k6tk/d8/d843f2d911aab9875cac74771b2ba064b883e7fc4ef09e18ff0f5c05d420c304.png",
        "sha256": "d843f2d911aab9875cac74771b2ba064b883e7fc4ef09e18ff0f5c05d420c304"
      },
      {
        "path": "/data2/k6tk/9e/9ea990687d97b06fa7121079317aedccce57c3afb290f597a95de7671b97dcd5.png",
        "sha256": "9ea990687d97b06fa7121079317aedccce57c3afb290f597a95de7671b97dcd5"
      },
      {
        "path": "/data2/k6tk/ec/ec9c940d3ce1ba5469eeb4d638a24900fe2d10a988beb4d60a7c3b5721ae37df.png",
        "sha256": "ec9c940d3ce1ba5469eeb4d638a24900fe2d10a988beb4d60a7c3b5721ae37df"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      6.966666666666667,
      13.933333333333334,
      20.9,
      27.866666666666667,
      34.833333333333336,
      41.81666666666667,
      48.78333333333333,
      55.75,
      62.71666666666667,
      69.68333333333334,
      76.66666666666667,
      83.63333333333334,
      90.6,
      97.56666666666666,
      104.53333333333333,
      111.51666666666667,
      118.48333333333333,
      125.45,
      132.41666666666666,
      139.38333333333333,
      146.36666666666667,
      153.33333333333334,
      160.3,
      167.26666666666668,
      174.23333333333332,
      181.21666666666667,
      188.18333333333334,
      195.15,
      202.11666666666667,
      209.08333333333334,
      216.06666666666666
    ],
    "total_num_frames": 12965
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: projector screen in frame 6; heater in frame 2; windowsill in frame 20.\nOf these, the projector screen and the windowsill are farthest apart, with the heater off to the side.\n</think>\n\n52.88",
  "validation_commit": ""
}
```

## sb_rowLR_409e7cc400d722ea_q0

```json
{
  "answer": "69.87",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-a4657198a0aba2d4e147d85c4d7f20b2b6e2dd0acddedc309d2d1733d34d11de",
  "category": "room_size_estimation",
  "dataset": "d1",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v84c61735b580",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        112,
        224,
        336,
        448,
        560,
        672,
        784,
        896,
        1008,
        1120,
        1232,
        1344,
        1456,
        1568,
        1680,
        1792,
        1904,
        2016,
        2128,
        2240,
        2352,
        2464,
        2576,
        2688,
        2800,
        2912,
        3024,
        3136,
        3248,
        3360,
        3473
      ],
      "options": [],
      "qid": "sb_rowLR_409e7cc400d722ea_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannet/scene0588_03",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0588_03",
    "details": {
      "cell": "scannet|60-100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      112,
      224,
      336,
      448,
      560,
      672,
      784,
      896,
      1008,
      1120,
      1232,
      1344,
      1456,
      1568,
      1680,
      1792,
      1904,
      2016,
      2128,
      2240,
      2352,
      2464,
      2576,
      2688,
      2800,
      2912,
      3024,
      3136,
      3248,
      3360,
      3473
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0588_03.npz": "5776bca6b26c74617c751d68accba87338840bb6faec1ef77bc26bfec0652ad0",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0588",
    "room_measurement": {
      "area_m2": 69.8725,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 27949,
      "floor_height_m": 0.06945547710422992,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 20476
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 18,
          "centroid": [
            3.119768440723419,
            1.4582748115062714,
            1.8692776560783386
          ],
          "footprint": 6.962068744366704,
          "instance_id": 33,
          "label": "curtain",
          "pixel_share": 0.18704427083333333
        },
        {
          "best_view": 20,
          "centroid": [
            3.270735263824463,
            2.1118615865707397,
            1.5824183225631714
          ],
          "footprint": 3.221181933723301,
          "instance_id": 7,
          "label": "piano",
          "pixel_share": 0.1028515625
        },
        {
          "best_view": 19,
          "centroid": [
            6.869989395141602,
            0.8284202367067337,
            1.6949293315410614
          ],
          "footprint": 1.7711400197780645,
          "instance_id": 30,
          "label": "door",
          "pixel_share": 0.013515625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0588_03.npz",
      "raster_sha256": "5776bca6b26c74617c751d68accba87338840bb6faec1ef77bc26bfec0652ad0",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.119768440723419,
            1.4582748115062714
          ],
          [
            3.270735263824463,
            2.1118615865707397
          ],
          [
            6.869989395141602,
            0.8284202367067337
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.6663240154548118,
        "projection": 0.020235264067652716,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 3.8212369725449156,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12cs_e734173d0aebd3a9e178c574",
    "source_row_sha256": "2638495d0d14e17c4a0d4f2b8125d047d73bd4a9bd0aba884e7dac226a988f9d",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_409e7cc400d722ea_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v84c61735b580",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      112,
      224,
      336,
      448,
      560,
      672,
      784,
      896,
      1008,
      1120,
      1232,
      1344,
      1456,
      1568,
      1680,
      1792,
      1904,
      2016,
      2128,
      2240,
      2352,
      2464,
      2576,
      2688,
      2800,
      2912,
      3024,
      3136,
      3248,
      3360,
      3473
    ],
    "frames": [
      {
        "path": "/data2/k6tk/49/4951f89b86a4703e7bf1e1114a4c5e1209dc088890a2b92b650062fbe8711280.png",
        "sha256": "4951f89b86a4703e7bf1e1114a4c5e1209dc088890a2b92b650062fbe8711280"
      },
      {
        "path": "/data2/k6tk/ba/baa7979821212620c92a1d66fb4112b3fc0b5eb746fe911ce4c2654f8df1e886.png",
        "sha256": "baa7979821212620c92a1d66fb4112b3fc0b5eb746fe911ce4c2654f8df1e886"
      },
      {
        "path": "/data2/k6tk/71/719e901cfeb65853637a89200be11a5c4caf51d001f813d739a80f114d4355cb.png",
        "sha256": "719e901cfeb65853637a89200be11a5c4caf51d001f813d739a80f114d4355cb"
      },
      {
        "path": "/data2/k6tk/4f/4f51c91a267706351145bded2d8495ac71e496119d3376ac1f7b987b76d52b6b.png",
        "sha256": "4f51c91a267706351145bded2d8495ac71e496119d3376ac1f7b987b76d52b6b"
      },
      {
        "path": "/data2/k6tk/cb/cb3c6c12a65b1b50ccd1b9ea2a4f5b5a5859cf6fd2e900b8c4543deadf309b4a.png",
        "sha256": "cb3c6c12a65b1b50ccd1b9ea2a4f5b5a5859cf6fd2e900b8c4543deadf309b4a"
      },
      {
        "path": "/data2/k6tk/58/58b1e7e777f0fe2820edb0ba6b6d7653b1fb0fb95ef2670fc024a31cec29d85a.png",
        "sha256": "58b1e7e777f0fe2820edb0ba6b6d7653b1fb0fb95ef2670fc024a31cec29d85a"
      },
      {
        "path": "/data2/k6tk/7e/7e5285965f02e9e1b0e3267a6782f9b748137deb873b7f5ba7a6c5cbc78629cb.png",
        "sha256": "7e5285965f02e9e1b0e3267a6782f9b748137deb873b7f5ba7a6c5cbc78629cb"
      },
      {
        "path": "/data2/k6tk/5c/5ca64d700877a181beeba5180664279ef40c7d6cf099c5b2e6769f37a333c06b.png",
        "sha256": "5ca64d700877a181beeba5180664279ef40c7d6cf099c5b2e6769f37a333c06b"
      },
      {
        "path": "/data2/k6tk/9e/9ecf96de10a14aa5548ed5bbabfb87f1470aa08fea02ac65b3c18eb284fad215.png",
        "sha256": "9ecf96de10a14aa5548ed5bbabfb87f1470aa08fea02ac65b3c18eb284fad215"
      },
      {
        "path": "/data2/k6tk/6c/6c092342523b5bb22776726856dc8f09bd7f6c030bfa58370a95c37c1d0511b2.png",
        "sha256": "6c092342523b5bb22776726856dc8f09bd7f6c030bfa58370a95c37c1d0511b2"
      },
      {
        "path": "/data2/k6tk/68/689f110ec5557e982cb7f3647550e806294bef29294ddd841ce9eaebde34219a.png",
        "sha256": "689f110ec5557e982cb7f3647550e806294bef29294ddd841ce9eaebde34219a"
      },
      {
        "path": "/data2/k6tk/27/275809b9f36309a7217d00bedef95930b5d986ba4084ec314cd69dd47e55a719.png",
        "sha256": "275809b9f36309a7217d00bedef95930b5d986ba4084ec314cd69dd47e55a719"
      },
      {
        "path": "/data2/k6tk/d0/d0f043a773ac0c3b2745b53ddd280cfd4bd517de5582592429c984bde581d6f7.png",
        "sha256": "d0f043a773ac0c3b2745b53ddd280cfd4bd517de5582592429c984bde581d6f7"
      },
      {
        "path": "/data2/k6tk/90/903364c72440d644c768f9ff8fe795e633a0fe84a7129de5e6c5fa920dabf8f8.png",
        "sha256": "903364c72440d644c768f9ff8fe795e633a0fe84a7129de5e6c5fa920dabf8f8"
      },
      {
        "path": "/data2/k6tk/63/63dd49be2b0020b598aa4e5ee14eacb8259b77833ee78aa6454cf391d6e596c9.png",
        "sha256": "63dd49be2b0020b598aa4e5ee14eacb8259b77833ee78aa6454cf391d6e596c9"
      },
      {
        "path": "/data2/k6tk/c1/c17b4ed6bb1079288d1e707b4eb23742fd16a0bb6eadd821906606dd2749e62e.png",
        "sha256": "c17b4ed6bb1079288d1e707b4eb23742fd16a0bb6eadd821906606dd2749e62e"
      },
      {
        "path": "/data2/k6tk/1c/1c5e520891f52fb7e017a2f3feeb1faf9b6ed4f7364f0453d5892fba8fa78e73.png",
        "sha256": "1c5e520891f52fb7e017a2f3feeb1faf9b6ed4f7364f0453d5892fba8fa78e73"
      },
      {
        "path": "/data2/k6tk/b5/b5280aa0942bd23a48afcdbde2c63202ff9e8b0cec8f98241fdc51475d7947dd.png",
        "sha256": "b5280aa0942bd23a48afcdbde2c63202ff9e8b0cec8f98241fdc51475d7947dd"
      },
      {
        "path": "/data2/k6tk/22/229112502aabd070c4dff2e14e24bf9beb8fe690e8eded8dc7c7ff7f05f67f1f.png",
        "sha256": "229112502aabd070c4dff2e14e24bf9beb8fe690e8eded8dc7c7ff7f05f67f1f"
      },
      {
        "path": "/data2/k6tk/c7/c767bba3b7241845aedeb3e6d2648ac68b7d03efad141095ee22ecc794950809.png",
        "sha256": "c767bba3b7241845aedeb3e6d2648ac68b7d03efad141095ee22ecc794950809"
      },
      {
        "path": "/data2/k6tk/c3/c306dab6b8e38fb8094b06b55af7660aa5d4eb81b3036a1dea41c261196820f9.png",
        "sha256": "c306dab6b8e38fb8094b06b55af7660aa5d4eb81b3036a1dea41c261196820f9"
      },
      {
        "path": "/data2/k6tk/00/006b1fdc201d2f5fa0c3186d895755e6d5858bf01bc8da9c42a1c4997d6bff72.png",
        "sha256": "006b1fdc201d2f5fa0c3186d895755e6d5858bf01bc8da9c42a1c4997d6bff72"
      },
      {
        "path": "/data2/k6tk/81/81cb3af5dc5c1390805c556d948ed85310a9889d581f73272925a21c162d996d.png",
        "sha256": "81cb3af5dc5c1390805c556d948ed85310a9889d581f73272925a21c162d996d"
      },
      {
        "path": "/data2/k6tk/7d/7dd9ef06a68f79496764c12224f0d78b07d6c6e7113082826ac55ce3b8d7ae3e.png",
        "sha256": "7dd9ef06a68f79496764c12224f0d78b07d6c6e7113082826ac55ce3b8d7ae3e"
      },
      {
        "path": "/data2/k6tk/e0/e0201d4ec7e40a948b832fde9f85718434d39f4ae409d4877a5ab35a55dbd9f5.png",
        "sha256": "e0201d4ec7e40a948b832fde9f85718434d39f4ae409d4877a5ab35a55dbd9f5"
      },
      {
        "path": "/data2/k6tk/00/00f9747e425a94bc2c3a8c3e6ca4ab0b090304c62a9d8a0cce42551c9cdc44fd.png",
        "sha256": "00f9747e425a94bc2c3a8c3e6ca4ab0b090304c62a9d8a0cce42551c9cdc44fd"
      },
      {
        "path": "/data2/k6tk/9a/9a2cd3c64e4d1d0f96c0e171edc8f42991ab1f32fe52e8a8af05de59ffe03697.png",
        "sha256": "9a2cd3c64e4d1d0f96c0e171edc8f42991ab1f32fe52e8a8af05de59ffe03697"
      },
      {
        "path": "/data2/k6tk/fb/fb1b3329cf5ad5aecfa67289346bb448cec302cdf729518b0ac575a7c9557a45.png",
        "sha256": "fb1b3329cf5ad5aecfa67289346bb448cec302cdf729518b0ac575a7c9557a45"
      },
      {
        "path": "/data2/k6tk/d2/d28560b78de3ce8a3067726cf1edee9446d8915e8a084a8babe5c0d6c4d3a3e2.png",
        "sha256": "d28560b78de3ce8a3067726cf1edee9446d8915e8a084a8babe5c0d6c4d3a3e2"
      },
      {
        "path": "/data2/k6tk/da/da3da00765bc7edecdec5f5c597741cc848b59ad1185a626fe2c7cb651a1b58c.png",
        "sha256": "da3da00765bc7edecdec5f5c597741cc848b59ad1185a626fe2c7cb651a1b58c"
      },
      {
        "path": "/data2/k6tk/70/702d3d2994bbe5509d5ff1331084b74397542f1e06b2a4c7d07c3a54555b5419.png",
        "sha256": "702d3d2994bbe5509d5ff1331084b74397542f1e06b2a4c7d07c3a54555b5419"
      },
      {
        "path": "/data2/k6tk/fe/fee5c3766b8b199d29e20d29fcd3c77f8b259c940bf797b3125193f5bd6381bf.png",
        "sha256": "fee5c3766b8b199d29e20d29fcd3c77f8b259c940bf797b3125193f5bd6381bf"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      4.666666666666667,
      9.333333333333334,
      14.0,
      18.666666666666668,
      23.333333333333332,
      28.0,
      32.666666666666664,
      37.333333333333336,
      42.0,
      46.666666666666664,
      51.333333333333336,
      56.0,
      60.666666666666664,
      65.33333333333333,
      70.0,
      74.66666666666667,
      79.33333333333333,
      84.0,
      88.66666666666667,
      93.33333333333333,
      98.0,
      102.66666666666667,
      107.33333333333333,
      112.0,
      116.66666666666667,
      121.33333333333333,
      126.0,
      130.66666666666666,
      135.33333333333334,
      140.0,
      144.70833333333334
    ],
    "total_num_frames": 3474
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: curtain in frame 18; piano in frame 20; door in frame 19.\nOf these, the piano and the door are farthest apart, with the curtain off to the side.\n</think>\n\n69.87",
  "validation_commit": ""
}
```

## sb_rowLR_409e7cc400d722ea_q1

```json
{
  "answer": "69.87",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-41d145a4df91f9f2338df3c245fb3a47fc07cfc2fc2440099cdab617bf92f3d4",
  "category": "room_size_estimation",
  "dataset": "d1",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v84c61735b580",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        112,
        224,
        336,
        448,
        560,
        672,
        784,
        896,
        1008,
        1120,
        1232,
        1344,
        1456,
        1568,
        1680,
        1792,
        1904,
        2016,
        2128,
        2240,
        2352,
        2464,
        2576,
        2688,
        2800,
        2912,
        3024,
        3136,
        3248,
        3360,
        3473
      ],
      "options": [],
      "qid": "sb_rowLR_409e7cc400d722ea_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannet/scene0588_03",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0588_03",
    "details": {
      "cell": "scannet|60-100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      112,
      224,
      336,
      448,
      560,
      672,
      784,
      896,
      1008,
      1120,
      1232,
      1344,
      1456,
      1568,
      1680,
      1792,
      1904,
      2016,
      2128,
      2240,
      2352,
      2464,
      2576,
      2688,
      2800,
      2912,
      3024,
      3136,
      3248,
      3360,
      3473
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0588_03.npz": "5776bca6b26c74617c751d68accba87338840bb6faec1ef77bc26bfec0652ad0",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0588",
    "room_measurement": {
      "area_m2": 69.8725,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 27949,
      "floor_height_m": 0.06945547710422992,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 20476
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 18,
          "centroid": [
            3.119768440723419,
            1.4582748115062714,
            1.8692776560783386
          ],
          "footprint": 6.962068744366704,
          "instance_id": 33,
          "label": "curtain",
          "pixel_share": 0.18704427083333333
        },
        {
          "best_view": 20,
          "centroid": [
            3.270735263824463,
            2.1118615865707397,
            1.5824183225631714
          ],
          "footprint": 3.221181933723301,
          "instance_id": 7,
          "label": "piano",
          "pixel_share": 0.1028515625
        },
        {
          "best_view": 19,
          "centroid": [
            6.869989395141602,
            0.8284202367067337,
            1.6949293315410614
          ],
          "footprint": 1.7711400197780645,
          "instance_id": 30,
          "label": "door",
          "pixel_share": 0.013515625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0588_03.npz",
      "raster_sha256": "5776bca6b26c74617c751d68accba87338840bb6faec1ef77bc26bfec0652ad0",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.119768440723419,
            1.4582748115062714
          ],
          [
            3.270735263824463,
            2.1118615865707397
          ],
          [
            6.869989395141602,
            0.8284202367067337
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.6663240154548118,
        "projection": 0.020235264067652716,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 3.8212369725449156,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12cs_e734173d0aebd3a9e178c574",
    "source_row_sha256": "2638495d0d14e17c4a0d4f2b8125d047d73bd4a9bd0aba884e7dac226a988f9d",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_409e7cc400d722ea_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v84c61735b580",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      112,
      224,
      336,
      448,
      560,
      672,
      784,
      896,
      1008,
      1120,
      1232,
      1344,
      1456,
      1568,
      1680,
      1792,
      1904,
      2016,
      2128,
      2240,
      2352,
      2464,
      2576,
      2688,
      2800,
      2912,
      3024,
      3136,
      3248,
      3360,
      3473
    ],
    "frames": [
      {
        "path": "/data2/k6tk/49/4951f89b86a4703e7bf1e1114a4c5e1209dc088890a2b92b650062fbe8711280.png",
        "sha256": "4951f89b86a4703e7bf1e1114a4c5e1209dc088890a2b92b650062fbe8711280"
      },
      {
        "path": "/data2/k6tk/ba/baa7979821212620c92a1d66fb4112b3fc0b5eb746fe911ce4c2654f8df1e886.png",
        "sha256": "baa7979821212620c92a1d66fb4112b3fc0b5eb746fe911ce4c2654f8df1e886"
      },
      {
        "path": "/data2/k6tk/71/719e901cfeb65853637a89200be11a5c4caf51d001f813d739a80f114d4355cb.png",
        "sha256": "719e901cfeb65853637a89200be11a5c4caf51d001f813d739a80f114d4355cb"
      },
      {
        "path": "/data2/k6tk/4f/4f51c91a267706351145bded2d8495ac71e496119d3376ac1f7b987b76d52b6b.png",
        "sha256": "4f51c91a267706351145bded2d8495ac71e496119d3376ac1f7b987b76d52b6b"
      },
      {
        "path": "/data2/k6tk/cb/cb3c6c12a65b1b50ccd1b9ea2a4f5b5a5859cf6fd2e900b8c4543deadf309b4a.png",
        "sha256": "cb3c6c12a65b1b50ccd1b9ea2a4f5b5a5859cf6fd2e900b8c4543deadf309b4a"
      },
      {
        "path": "/data2/k6tk/58/58b1e7e777f0fe2820edb0ba6b6d7653b1fb0fb95ef2670fc024a31cec29d85a.png",
        "sha256": "58b1e7e777f0fe2820edb0ba6b6d7653b1fb0fb95ef2670fc024a31cec29d85a"
      },
      {
        "path": "/data2/k6tk/7e/7e5285965f02e9e1b0e3267a6782f9b748137deb873b7f5ba7a6c5cbc78629cb.png",
        "sha256": "7e5285965f02e9e1b0e3267a6782f9b748137deb873b7f5ba7a6c5cbc78629cb"
      },
      {
        "path": "/data2/k6tk/5c/5ca64d700877a181beeba5180664279ef40c7d6cf099c5b2e6769f37a333c06b.png",
        "sha256": "5ca64d700877a181beeba5180664279ef40c7d6cf099c5b2e6769f37a333c06b"
      },
      {
        "path": "/data2/k6tk/9e/9ecf96de10a14aa5548ed5bbabfb87f1470aa08fea02ac65b3c18eb284fad215.png",
        "sha256": "9ecf96de10a14aa5548ed5bbabfb87f1470aa08fea02ac65b3c18eb284fad215"
      },
      {
        "path": "/data2/k6tk/6c/6c092342523b5bb22776726856dc8f09bd7f6c030bfa58370a95c37c1d0511b2.png",
        "sha256": "6c092342523b5bb22776726856dc8f09bd7f6c030bfa58370a95c37c1d0511b2"
      },
      {
        "path": "/data2/k6tk/68/689f110ec5557e982cb7f3647550e806294bef29294ddd841ce9eaebde34219a.png",
        "sha256": "689f110ec5557e982cb7f3647550e806294bef29294ddd841ce9eaebde34219a"
      },
      {
        "path": "/data2/k6tk/27/275809b9f36309a7217d00bedef95930b5d986ba4084ec314cd69dd47e55a719.png",
        "sha256": "275809b9f36309a7217d00bedef95930b5d986ba4084ec314cd69dd47e55a719"
      },
      {
        "path": "/data2/k6tk/d0/d0f043a773ac0c3b2745b53ddd280cfd4bd517de5582592429c984bde581d6f7.png",
        "sha256": "d0f043a773ac0c3b2745b53ddd280cfd4bd517de5582592429c984bde581d6f7"
      },
      {
        "path": "/data2/k6tk/90/903364c72440d644c768f9ff8fe795e633a0fe84a7129de5e6c5fa920dabf8f8.png",
        "sha256": "903364c72440d644c768f9ff8fe795e633a0fe84a7129de5e6c5fa920dabf8f8"
      },
      {
        "path": "/data2/k6tk/63/63dd49be2b0020b598aa4e5ee14eacb8259b77833ee78aa6454cf391d6e596c9.png",
        "sha256": "63dd49be2b0020b598aa4e5ee14eacb8259b77833ee78aa6454cf391d6e596c9"
      },
      {
        "path": "/data2/k6tk/c1/c17b4ed6bb1079288d1e707b4eb23742fd16a0bb6eadd821906606dd2749e62e.png",
        "sha256": "c17b4ed6bb1079288d1e707b4eb23742fd16a0bb6eadd821906606dd2749e62e"
      },
      {
        "path": "/data2/k6tk/1c/1c5e520891f52fb7e017a2f3feeb1faf9b6ed4f7364f0453d5892fba8fa78e73.png",
        "sha256": "1c5e520891f52fb7e017a2f3feeb1faf9b6ed4f7364f0453d5892fba8fa78e73"
      },
      {
        "path": "/data2/k6tk/b5/b5280aa0942bd23a48afcdbde2c63202ff9e8b0cec8f98241fdc51475d7947dd.png",
        "sha256": "b5280aa0942bd23a48afcdbde2c63202ff9e8b0cec8f98241fdc51475d7947dd"
      },
      {
        "path": "/data2/k6tk/22/229112502aabd070c4dff2e14e24bf9beb8fe690e8eded8dc7c7ff7f05f67f1f.png",
        "sha256": "229112502aabd070c4dff2e14e24bf9beb8fe690e8eded8dc7c7ff7f05f67f1f"
      },
      {
        "path": "/data2/k6tk/c7/c767bba3b7241845aedeb3e6d2648ac68b7d03efad141095ee22ecc794950809.png",
        "sha256": "c767bba3b7241845aedeb3e6d2648ac68b7d03efad141095ee22ecc794950809"
      },
      {
        "path": "/data2/k6tk/c3/c306dab6b8e38fb8094b06b55af7660aa5d4eb81b3036a1dea41c261196820f9.png",
        "sha256": "c306dab6b8e38fb8094b06b55af7660aa5d4eb81b3036a1dea41c261196820f9"
      },
      {
        "path": "/data2/k6tk/00/006b1fdc201d2f5fa0c3186d895755e6d5858bf01bc8da9c42a1c4997d6bff72.png",
        "sha256": "006b1fdc201d2f5fa0c3186d895755e6d5858bf01bc8da9c42a1c4997d6bff72"
      },
      {
        "path": "/data2/k6tk/81/81cb3af5dc5c1390805c556d948ed85310a9889d581f73272925a21c162d996d.png",
        "sha256": "81cb3af5dc5c1390805c556d948ed85310a9889d581f73272925a21c162d996d"
      },
      {
        "path": "/data2/k6tk/7d/7dd9ef06a68f79496764c12224f0d78b07d6c6e7113082826ac55ce3b8d7ae3e.png",
        "sha256": "7dd9ef06a68f79496764c12224f0d78b07d6c6e7113082826ac55ce3b8d7ae3e"
      },
      {
        "path": "/data2/k6tk/e0/e0201d4ec7e40a948b832fde9f85718434d39f4ae409d4877a5ab35a55dbd9f5.png",
        "sha256": "e0201d4ec7e40a948b832fde9f85718434d39f4ae409d4877a5ab35a55dbd9f5"
      },
      {
        "path": "/data2/k6tk/00/00f9747e425a94bc2c3a8c3e6ca4ab0b090304c62a9d8a0cce42551c9cdc44fd.png",
        "sha256": "00f9747e425a94bc2c3a8c3e6ca4ab0b090304c62a9d8a0cce42551c9cdc44fd"
      },
      {
        "path": "/data2/k6tk/9a/9a2cd3c64e4d1d0f96c0e171edc8f42991ab1f32fe52e8a8af05de59ffe03697.png",
        "sha256": "9a2cd3c64e4d1d0f96c0e171edc8f42991ab1f32fe52e8a8af05de59ffe03697"
      },
      {
        "path": "/data2/k6tk/fb/fb1b3329cf5ad5aecfa67289346bb448cec302cdf729518b0ac575a7c9557a45.png",
        "sha256": "fb1b3329cf5ad5aecfa67289346bb448cec302cdf729518b0ac575a7c9557a45"
      },
      {
        "path": "/data2/k6tk/d2/d28560b78de3ce8a3067726cf1edee9446d8915e8a084a8babe5c0d6c4d3a3e2.png",
        "sha256": "d28560b78de3ce8a3067726cf1edee9446d8915e8a084a8babe5c0d6c4d3a3e2"
      },
      {
        "path": "/data2/k6tk/da/da3da00765bc7edecdec5f5c597741cc848b59ad1185a626fe2c7cb651a1b58c.png",
        "sha256": "da3da00765bc7edecdec5f5c597741cc848b59ad1185a626fe2c7cb651a1b58c"
      },
      {
        "path": "/data2/k6tk/70/702d3d2994bbe5509d5ff1331084b74397542f1e06b2a4c7d07c3a54555b5419.png",
        "sha256": "702d3d2994bbe5509d5ff1331084b74397542f1e06b2a4c7d07c3a54555b5419"
      },
      {
        "path": "/data2/k6tk/fe/fee5c3766b8b199d29e20d29fcd3c77f8b259c940bf797b3125193f5bd6381bf.png",
        "sha256": "fee5c3766b8b199d29e20d29fcd3c77f8b259c940bf797b3125193f5bd6381bf"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      4.666666666666667,
      9.333333333333334,
      14.0,
      18.666666666666668,
      23.333333333333332,
      28.0,
      32.666666666666664,
      37.333333333333336,
      42.0,
      46.666666666666664,
      51.333333333333336,
      56.0,
      60.666666666666664,
      65.33333333333333,
      70.0,
      74.66666666666667,
      79.33333333333333,
      84.0,
      88.66666666666667,
      93.33333333333333,
      98.0,
      102.66666666666667,
      107.33333333333333,
      112.0,
      116.66666666666667,
      121.33333333333333,
      126.0,
      130.66666666666666,
      135.33333333333334,
      140.0,
      144.70833333333334
    ],
    "total_num_frames": 3474
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: curtain in frame 18; piano in frame 20; door in frame 19.\nThe piano and the door are the farthest apart among these landmarks, with the curtain to the side of that pair.\n</think>\n\n69.87",
  "validation_commit": ""
}
```

## sb_rowLR_cfc492f27f73bfa4_q0

```json
{
  "answer": "70.35",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-fb8b0237c87369cfe4162a75eba8fc347fdd6c6935bcf1eb2d644b0ea0e6d1bb",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v047dd5a557b3",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        394,
        788,
        1182,
        1576,
        1970,
        2364,
        2759,
        3153,
        3547,
        3941,
        4335,
        4729,
        5124,
        5518,
        5912,
        6306,
        6700,
        7094,
        7489,
        7883,
        8277,
        8671,
        9065,
        9459,
        9854,
        10248,
        10642,
        11036,
        11430,
        11824,
        12219
      ],
      "options": [],
      "qid": "sb_rowLR_cfc492f27f73bfa4_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/3b753d9ae8",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3b753d9ae8",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      394,
      788,
      1182,
      1576,
      1970,
      2364,
      2759,
      3153,
      3547,
      3941,
      4335,
      4729,
      5124,
      5518,
      5912,
      6306,
      6700,
      7094,
      7489,
      7883,
      8277,
      8671,
      9065,
      9459,
      9854,
      10248,
      10642,
      11036,
      11430,
      11824,
      12219
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3b753d9ae8.npz": "7916938bace0f0c5aaeae81a719234ae3b632ad6559aa05e9cf9a73d003da377",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3b753d9ae8",
    "room_measurement": {
      "area_m2": 70.35000000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 28140,
      "floor_height_m": 0.01047127967847003,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 21873
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            5.305887798778638,
            0.7830463268039098,
            1.2716887742280958
          ],
          "footprint": 1.2670578861424833,
          "instance_id": 65,
          "label": "meeting pod",
          "pixel_share": 0.19619791666666667
        },
        {
          "best_view": 2,
          "centroid": [
            5.620529713190298,
            0.47269518671492516,
            3.1204395294189453
          ],
          "footprint": 0.939641037474543,
          "instance_id": 31,
          "label": "cable tray",
          "pixel_share": 0.08549479166666667
        },
        {
          "best_view": 11,
          "centroid": [
            2.3135494580598905,
            0.6932999607312897,
            1.0201755538582802
          ],
          "footprint": 0.5527165068059829,
          "instance_id": 20,
          "label": "whiteboard",
          "pixel_share": 0.3834765625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3b753d9ae8.npz",
      "raster_sha256": "7916938bace0f0c5aaeae81a719234ae3b632ad6559aa05e9cf9a73d003da377",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            5.305887798778638,
            0.7830463268039098
          ],
          [
            5.620529713190298,
            0.47269518671492516
          ],
          [
            2.3135494580598905,
            0.6932999607312897
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.2887200482669888,
        "projection": 0.100955963564789,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 3.314330230097959,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "vstirel_3eaff8283c003c438d25a364",
    "source_row_sha256": "9d1622a1a050b0d393adfb993410f319079677f0561055435c583b17c00f30b5",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_cfc492f27f73bfa4_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v047dd5a557b3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      394,
      788,
      1182,
      1576,
      1970,
      2364,
      2759,
      3153,
      3547,
      3941,
      4335,
      4729,
      5124,
      5518,
      5912,
      6306,
      6700,
      7094,
      7489,
      7883,
      8277,
      8671,
      9065,
      9459,
      9854,
      10248,
      10642,
      11036,
      11430,
      11824,
      12219
    ],
    "frames": [
      {
        "path": "/data2/k6tk/df/df74fc55d606817e27ef62a8a502a94e8a4eea51627b0b038961c920ae03df1b.png",
        "sha256": "df74fc55d606817e27ef62a8a502a94e8a4eea51627b0b038961c920ae03df1b"
      },
      {
        "path": "/data2/k6tk/b4/b49eec9d690c9ad33949e4734a00209296c1ebd5bee224a9dfea316fe9b1673e.png",
        "sha256": "b49eec9d690c9ad33949e4734a00209296c1ebd5bee224a9dfea316fe9b1673e"
      },
      {
        "path": "/data2/k6tk/e7/e7ba641d65f8040160fe3d2d09d1be5bb7889be2cf23e90aa2576d0344f24915.png",
        "sha256": "e7ba641d65f8040160fe3d2d09d1be5bb7889be2cf23e90aa2576d0344f24915"
      },
      {
        "path": "/data2/k6tk/42/42f113de659fd90d7f952a5419b56b9e30006ff37d964afd286ebf37fce76ad4.png",
        "sha256": "42f113de659fd90d7f952a5419b56b9e30006ff37d964afd286ebf37fce76ad4"
      },
      {
        "path": "/data2/k6tk/ba/ba22c1526fe7791cf54d718f946d011802fcdcaaa29a2454ab9239950ff216b6.png",
        "sha256": "ba22c1526fe7791cf54d718f946d011802fcdcaaa29a2454ab9239950ff216b6"
      },
      {
        "path": "/data2/k6tk/bc/bcf4feadbab7a71b6a71a80e863a5761a3dae1234baf6b8bd9011826a0534fe0.png",
        "sha256": "bcf4feadbab7a71b6a71a80e863a5761a3dae1234baf6b8bd9011826a0534fe0"
      },
      {
        "path": "/data2/k6tk/54/54744180fdfb3e24df5b4250d3a759c60e9dd8d9a8ac45227de79aa5e5adcf37.png",
        "sha256": "54744180fdfb3e24df5b4250d3a759c60e9dd8d9a8ac45227de79aa5e5adcf37"
      },
      {
        "path": "/data2/k6tk/cd/cdc2b86e13bc61010456bd79696dcecc1d721b4005772abfcebb7750319ccc22.png",
        "sha256": "cdc2b86e13bc61010456bd79696dcecc1d721b4005772abfcebb7750319ccc22"
      },
      {
        "path": "/data2/k6tk/b1/b152ad52675faf0d40048fc1b41521b44520f73f7d3bbdec6ff7bbb31a59002f.png",
        "sha256": "b152ad52675faf0d40048fc1b41521b44520f73f7d3bbdec6ff7bbb31a59002f"
      },
      {
        "path": "/data2/k6tk/de/de5e2d7bf329580f6943cfb9e3f4dcf1ac407da423f81845a7ab0cc905983109.png",
        "sha256": "de5e2d7bf329580f6943cfb9e3f4dcf1ac407da423f81845a7ab0cc905983109"
      },
      {
        "path": "/data2/k6tk/0e/0e39dce2c092afa5d902b04ee1ab56f1c8f1b04f4745636fdaa3be5dfed639da.png",
        "sha256": "0e39dce2c092afa5d902b04ee1ab56f1c8f1b04f4745636fdaa3be5dfed639da"
      },
      {
        "path": "/data2/k6tk/13/135175e6dcfb36f831abafce77748146a3e7a7fe4c87344586679dc280c138df.png",
        "sha256": "135175e6dcfb36f831abafce77748146a3e7a7fe4c87344586679dc280c138df"
      },
      {
        "path": "/data2/k6tk/02/022fe82b0433f63110a5e277e0371c7f35e815160d27fabeec2d4f2a3755fb6c.png",
        "sha256": "022fe82b0433f63110a5e277e0371c7f35e815160d27fabeec2d4f2a3755fb6c"
      },
      {
        "path": "/data2/k6tk/d1/d194fc954b610cbd874b3f8bfe2c11643d2792ad86064e073cbdedebf0f17413.png",
        "sha256": "d194fc954b610cbd874b3f8bfe2c11643d2792ad86064e073cbdedebf0f17413"
      },
      {
        "path": "/data2/k6tk/68/689e53bb68427aa5897d2392aa81a34a2115669d8f83dcca66652143267eb8c8.png",
        "sha256": "689e53bb68427aa5897d2392aa81a34a2115669d8f83dcca66652143267eb8c8"
      },
      {
        "path": "/data2/k6tk/62/62963c33adbd094380ea4c01a4a02412068b38d127ffd1ff47abc7f283e06b13.png",
        "sha256": "62963c33adbd094380ea4c01a4a02412068b38d127ffd1ff47abc7f283e06b13"
      },
      {
        "path": "/data2/k6tk/04/0468858fb870b014582336ce033d174dfe9c6ad3ccf99f21be124b1413917067.png",
        "sha256": "0468858fb870b014582336ce033d174dfe9c6ad3ccf99f21be124b1413917067"
      },
      {
        "path": "/data2/k6tk/1b/1b37d3ae7cd39df377254d3a76e62fc987554101112bcdfee9b98d077e2107a6.png",
        "sha256": "1b37d3ae7cd39df377254d3a76e62fc987554101112bcdfee9b98d077e2107a6"
      },
      {
        "path": "/data2/k6tk/b1/b114495d44f00f942fd26bb386c1286df4cad2a8f1ff31b17006b3c884c8a4f0.png",
        "sha256": "b114495d44f00f942fd26bb386c1286df4cad2a8f1ff31b17006b3c884c8a4f0"
      },
      {
        "path": "/data2/k6tk/15/15b443a1a7560b1fdbcdcd39fedeb6d9311163cead92323dea6ef2d69a56aac6.png",
        "sha256": "15b443a1a7560b1fdbcdcd39fedeb6d9311163cead92323dea6ef2d69a56aac6"
      },
      {
        "path": "/data2/k6tk/a1/a1eb48cfa72e5b3749a2fb601d19cd7fe66920d59a416af2538a2482cc02ee0e.png",
        "sha256": "a1eb48cfa72e5b3749a2fb601d19cd7fe66920d59a416af2538a2482cc02ee0e"
      },
      {
        "path": "/data2/k6tk/aa/aa5a1fa99143efec9e87bdc6d80318d7134eadb66facd7a0201daa2fab349ed7.png",
        "sha256": "aa5a1fa99143efec9e87bdc6d80318d7134eadb66facd7a0201daa2fab349ed7"
      },
      {
        "path": "/data2/k6tk/ea/eab2ceef48624b895979244eb80a29dc667af99bfb1883ec65834e212b7aa6e2.png",
        "sha256": "eab2ceef48624b895979244eb80a29dc667af99bfb1883ec65834e212b7aa6e2"
      },
      {
        "path": "/data2/k6tk/da/dab9395097fedad193f6fa551e1a7d7dbacb857704621944e7e2aba12e5a2634.png",
        "sha256": "dab9395097fedad193f6fa551e1a7d7dbacb857704621944e7e2aba12e5a2634"
      },
      {
        "path": "/data2/k6tk/5a/5adf6d1870c93125681e48de2dca005eaf829cf4cf2235c782208f806d774ae2.png",
        "sha256": "5adf6d1870c93125681e48de2dca005eaf829cf4cf2235c782208f806d774ae2"
      },
      {
        "path": "/data2/k6tk/04/04ce793586ad320d06a659d00c3998cece85d4bea2d9de1b2822dbaa4fa911cf.png",
        "sha256": "04ce793586ad320d06a659d00c3998cece85d4bea2d9de1b2822dbaa4fa911cf"
      },
      {
        "path": "/data2/k6tk/e9/e94ebf4370e8fd8981fc67ecb4b673575d7ea0cb8ddcdc5d54ee1dd9b0a79862.png",
        "sha256": "e94ebf4370e8fd8981fc67ecb4b673575d7ea0cb8ddcdc5d54ee1dd9b0a79862"
      },
      {
        "path": "/data2/k6tk/4d/4daef9dafd18c5a5c150819c87e9d96aa39dcefb246ce1d4e68f99cba42bdff1.png",
        "sha256": "4daef9dafd18c5a5c150819c87e9d96aa39dcefb246ce1d4e68f99cba42bdff1"
      },
      {
        "path": "/data2/k6tk/ca/ca841c6a9632b34015e82d352a30264acd798de2112ad1f6aaa8729dd795a448.png",
        "sha256": "ca841c6a9632b34015e82d352a30264acd798de2112ad1f6aaa8729dd795a448"
      },
      {
        "path": "/data2/k6tk/8a/8ab9d7328e9aedcb91a4239ac986b808d7f0bca77010bff55833571eb87e01f4.png",
        "sha256": "8ab9d7328e9aedcb91a4239ac986b808d7f0bca77010bff55833571eb87e01f4"
      },
      {
        "path": "/data2/k6tk/a6/a65925ad458b0e5c926a29668c2cd8778c2420ac4c7eb19b8e7550a5b438e34c.png",
        "sha256": "a65925ad458b0e5c926a29668c2cd8778c2420ac4c7eb19b8e7550a5b438e34c"
      },
      {
        "path": "/data2/k6tk/cb/cb7ce559e54956f53689a03c7760ed6e6ee166eeeb0cc5e3482a1b2b2157b28f.png",
        "sha256": "cb7ce559e54956f53689a03c7760ed6e6ee166eeeb0cc5e3482a1b2b2157b28f"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      6.566666666666666,
      13.133333333333333,
      19.7,
      26.266666666666666,
      32.833333333333336,
      39.4,
      45.983333333333334,
      52.55,
      59.11666666666667,
      65.68333333333334,
      72.25,
      78.81666666666666,
      85.4,
      91.96666666666667,
      98.53333333333333,
      105.1,
      111.66666666666667,
      118.23333333333333,
      124.81666666666666,
      131.38333333333333,
      137.95,
      144.51666666666668,
      151.08333333333334,
      157.65,
      164.23333333333332,
      170.8,
      177.36666666666667,
      183.93333333333334,
      190.5,
      197.06666666666666,
      203.65
    ],
    "total_num_frames": 12220
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: meeting pod in frame 5; cable tray in frame 2; whiteboard in frame 11.\nThe cable tray and the whiteboard are the farthest apart among these landmarks, with the meeting pod to the side of that pair.\n</think>\n\n70.35",
  "validation_commit": ""
}
```

## sb_rowLR_cfc492f27f73bfa4_q1

```json
{
  "answer": "70.35",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-0cd035a6b1743dc56f287fa80177a57d548f09987f7380d2bcf42262ab924cb3",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v047dd5a557b3",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        394,
        788,
        1182,
        1576,
        1970,
        2364,
        2759,
        3153,
        3547,
        3941,
        4335,
        4729,
        5124,
        5518,
        5912,
        6306,
        6700,
        7094,
        7489,
        7883,
        8277,
        8671,
        9065,
        9459,
        9854,
        10248,
        10642,
        11036,
        11430,
        11824,
        12219
      ],
      "options": [],
      "qid": "sb_rowLR_cfc492f27f73bfa4_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/3b753d9ae8",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3b753d9ae8",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      394,
      788,
      1182,
      1576,
      1970,
      2364,
      2759,
      3153,
      3547,
      3941,
      4335,
      4729,
      5124,
      5518,
      5912,
      6306,
      6700,
      7094,
      7489,
      7883,
      8277,
      8671,
      9065,
      9459,
      9854,
      10248,
      10642,
      11036,
      11430,
      11824,
      12219
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3b753d9ae8.npz": "7916938bace0f0c5aaeae81a719234ae3b632ad6559aa05e9cf9a73d003da377",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3b753d9ae8",
    "room_measurement": {
      "area_m2": 70.35000000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 28140,
      "floor_height_m": 0.01047127967847003,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 21873
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 5,
          "centroid": [
            5.305887798778638,
            0.7830463268039098,
            1.2716887742280958
          ],
          "footprint": 1.2670578861424833,
          "instance_id": 65,
          "label": "meeting pod",
          "pixel_share": 0.19619791666666667
        },
        {
          "best_view": 2,
          "centroid": [
            5.620529713190298,
            0.47269518671492516,
            3.1204395294189453
          ],
          "footprint": 0.939641037474543,
          "instance_id": 31,
          "label": "cable tray",
          "pixel_share": 0.08549479166666667
        },
        {
          "best_view": 11,
          "centroid": [
            2.3135494580598905,
            0.6932999607312897,
            1.0201755538582802
          ],
          "footprint": 0.5527165068059829,
          "instance_id": 20,
          "label": "whiteboard",
          "pixel_share": 0.3834765625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3b753d9ae8.npz",
      "raster_sha256": "7916938bace0f0c5aaeae81a719234ae3b632ad6559aa05e9cf9a73d003da377",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            5.305887798778638,
            0.7830463268039098
          ],
          [
            5.620529713190298,
            0.47269518671492516
          ],
          [
            2.3135494580598905,
            0.6932999607312897
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.2887200482669888,
        "projection": 0.100955963564789,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 3.314330230097959,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_3eaff8283c003c438d25a364",
    "source_row_sha256": "9d1622a1a050b0d393adfb993410f319079677f0561055435c583b17c00f30b5",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_cfc492f27f73bfa4_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v047dd5a557b3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      394,
      788,
      1182,
      1576,
      1970,
      2364,
      2759,
      3153,
      3547,
      3941,
      4335,
      4729,
      5124,
      5518,
      5912,
      6306,
      6700,
      7094,
      7489,
      7883,
      8277,
      8671,
      9065,
      9459,
      9854,
      10248,
      10642,
      11036,
      11430,
      11824,
      12219
    ],
    "frames": [
      {
        "path": "/data2/k6tk/df/df74fc55d606817e27ef62a8a502a94e8a4eea51627b0b038961c920ae03df1b.png",
        "sha256": "df74fc55d606817e27ef62a8a502a94e8a4eea51627b0b038961c920ae03df1b"
      },
      {
        "path": "/data2/k6tk/b4/b49eec9d690c9ad33949e4734a00209296c1ebd5bee224a9dfea316fe9b1673e.png",
        "sha256": "b49eec9d690c9ad33949e4734a00209296c1ebd5bee224a9dfea316fe9b1673e"
      },
      {
        "path": "/data2/k6tk/e7/e7ba641d65f8040160fe3d2d09d1be5bb7889be2cf23e90aa2576d0344f24915.png",
        "sha256": "e7ba641d65f8040160fe3d2d09d1be5bb7889be2cf23e90aa2576d0344f24915"
      },
      {
        "path": "/data2/k6tk/42/42f113de659fd90d7f952a5419b56b9e30006ff37d964afd286ebf37fce76ad4.png",
        "sha256": "42f113de659fd90d7f952a5419b56b9e30006ff37d964afd286ebf37fce76ad4"
      },
      {
        "path": "/data2/k6tk/ba/ba22c1526fe7791cf54d718f946d011802fcdcaaa29a2454ab9239950ff216b6.png",
        "sha256": "ba22c1526fe7791cf54d718f946d011802fcdcaaa29a2454ab9239950ff216b6"
      },
      {
        "path": "/data2/k6tk/bc/bcf4feadbab7a71b6a71a80e863a5761a3dae1234baf6b8bd9011826a0534fe0.png",
        "sha256": "bcf4feadbab7a71b6a71a80e863a5761a3dae1234baf6b8bd9011826a0534fe0"
      },
      {
        "path": "/data2/k6tk/54/54744180fdfb3e24df5b4250d3a759c60e9dd8d9a8ac45227de79aa5e5adcf37.png",
        "sha256": "54744180fdfb3e24df5b4250d3a759c60e9dd8d9a8ac45227de79aa5e5adcf37"
      },
      {
        "path": "/data2/k6tk/cd/cdc2b86e13bc61010456bd79696dcecc1d721b4005772abfcebb7750319ccc22.png",
        "sha256": "cdc2b86e13bc61010456bd79696dcecc1d721b4005772abfcebb7750319ccc22"
      },
      {
        "path": "/data2/k6tk/b1/b152ad52675faf0d40048fc1b41521b44520f73f7d3bbdec6ff7bbb31a59002f.png",
        "sha256": "b152ad52675faf0d40048fc1b41521b44520f73f7d3bbdec6ff7bbb31a59002f"
      },
      {
        "path": "/data2/k6tk/de/de5e2d7bf329580f6943cfb9e3f4dcf1ac407da423f81845a7ab0cc905983109.png",
        "sha256": "de5e2d7bf329580f6943cfb9e3f4dcf1ac407da423f81845a7ab0cc905983109"
      },
      {
        "path": "/data2/k6tk/0e/0e39dce2c092afa5d902b04ee1ab56f1c8f1b04f4745636fdaa3be5dfed639da.png",
        "sha256": "0e39dce2c092afa5d902b04ee1ab56f1c8f1b04f4745636fdaa3be5dfed639da"
      },
      {
        "path": "/data2/k6tk/13/135175e6dcfb36f831abafce77748146a3e7a7fe4c87344586679dc280c138df.png",
        "sha256": "135175e6dcfb36f831abafce77748146a3e7a7fe4c87344586679dc280c138df"
      },
      {
        "path": "/data2/k6tk/02/022fe82b0433f63110a5e277e0371c7f35e815160d27fabeec2d4f2a3755fb6c.png",
        "sha256": "022fe82b0433f63110a5e277e0371c7f35e815160d27fabeec2d4f2a3755fb6c"
      },
      {
        "path": "/data2/k6tk/d1/d194fc954b610cbd874b3f8bfe2c11643d2792ad86064e073cbdedebf0f17413.png",
        "sha256": "d194fc954b610cbd874b3f8bfe2c11643d2792ad86064e073cbdedebf0f17413"
      },
      {
        "path": "/data2/k6tk/68/689e53bb68427aa5897d2392aa81a34a2115669d8f83dcca66652143267eb8c8.png",
        "sha256": "689e53bb68427aa5897d2392aa81a34a2115669d8f83dcca66652143267eb8c8"
      },
      {
        "path": "/data2/k6tk/62/62963c33adbd094380ea4c01a4a02412068b38d127ffd1ff47abc7f283e06b13.png",
        "sha256": "62963c33adbd094380ea4c01a4a02412068b38d127ffd1ff47abc7f283e06b13"
      },
      {
        "path": "/data2/k6tk/04/0468858fb870b014582336ce033d174dfe9c6ad3ccf99f21be124b1413917067.png",
        "sha256": "0468858fb870b014582336ce033d174dfe9c6ad3ccf99f21be124b1413917067"
      },
      {
        "path": "/data2/k6tk/1b/1b37d3ae7cd39df377254d3a76e62fc987554101112bcdfee9b98d077e2107a6.png",
        "sha256": "1b37d3ae7cd39df377254d3a76e62fc987554101112bcdfee9b98d077e2107a6"
      },
      {
        "path": "/data2/k6tk/b1/b114495d44f00f942fd26bb386c1286df4cad2a8f1ff31b17006b3c884c8a4f0.png",
        "sha256": "b114495d44f00f942fd26bb386c1286df4cad2a8f1ff31b17006b3c884c8a4f0"
      },
      {
        "path": "/data2/k6tk/15/15b443a1a7560b1fdbcdcd39fedeb6d9311163cead92323dea6ef2d69a56aac6.png",
        "sha256": "15b443a1a7560b1fdbcdcd39fedeb6d9311163cead92323dea6ef2d69a56aac6"
      },
      {
        "path": "/data2/k6tk/a1/a1eb48cfa72e5b3749a2fb601d19cd7fe66920d59a416af2538a2482cc02ee0e.png",
        "sha256": "a1eb48cfa72e5b3749a2fb601d19cd7fe66920d59a416af2538a2482cc02ee0e"
      },
      {
        "path": "/data2/k6tk/aa/aa5a1fa99143efec9e87bdc6d80318d7134eadb66facd7a0201daa2fab349ed7.png",
        "sha256": "aa5a1fa99143efec9e87bdc6d80318d7134eadb66facd7a0201daa2fab349ed7"
      },
      {
        "path": "/data2/k6tk/ea/eab2ceef48624b895979244eb80a29dc667af99bfb1883ec65834e212b7aa6e2.png",
        "sha256": "eab2ceef48624b895979244eb80a29dc667af99bfb1883ec65834e212b7aa6e2"
      },
      {
        "path": "/data2/k6tk/da/dab9395097fedad193f6fa551e1a7d7dbacb857704621944e7e2aba12e5a2634.png",
        "sha256": "dab9395097fedad193f6fa551e1a7d7dbacb857704621944e7e2aba12e5a2634"
      },
      {
        "path": "/data2/k6tk/5a/5adf6d1870c93125681e48de2dca005eaf829cf4cf2235c782208f806d774ae2.png",
        "sha256": "5adf6d1870c93125681e48de2dca005eaf829cf4cf2235c782208f806d774ae2"
      },
      {
        "path": "/data2/k6tk/04/04ce793586ad320d06a659d00c3998cece85d4bea2d9de1b2822dbaa4fa911cf.png",
        "sha256": "04ce793586ad320d06a659d00c3998cece85d4bea2d9de1b2822dbaa4fa911cf"
      },
      {
        "path": "/data2/k6tk/e9/e94ebf4370e8fd8981fc67ecb4b673575d7ea0cb8ddcdc5d54ee1dd9b0a79862.png",
        "sha256": "e94ebf4370e8fd8981fc67ecb4b673575d7ea0cb8ddcdc5d54ee1dd9b0a79862"
      },
      {
        "path": "/data2/k6tk/4d/4daef9dafd18c5a5c150819c87e9d96aa39dcefb246ce1d4e68f99cba42bdff1.png",
        "sha256": "4daef9dafd18c5a5c150819c87e9d96aa39dcefb246ce1d4e68f99cba42bdff1"
      },
      {
        "path": "/data2/k6tk/ca/ca841c6a9632b34015e82d352a30264acd798de2112ad1f6aaa8729dd795a448.png",
        "sha256": "ca841c6a9632b34015e82d352a30264acd798de2112ad1f6aaa8729dd795a448"
      },
      {
        "path": "/data2/k6tk/8a/8ab9d7328e9aedcb91a4239ac986b808d7f0bca77010bff55833571eb87e01f4.png",
        "sha256": "8ab9d7328e9aedcb91a4239ac986b808d7f0bca77010bff55833571eb87e01f4"
      },
      {
        "path": "/data2/k6tk/a6/a65925ad458b0e5c926a29668c2cd8778c2420ac4c7eb19b8e7550a5b438e34c.png",
        "sha256": "a65925ad458b0e5c926a29668c2cd8778c2420ac4c7eb19b8e7550a5b438e34c"
      },
      {
        "path": "/data2/k6tk/cb/cb7ce559e54956f53689a03c7760ed6e6ee166eeeb0cc5e3482a1b2b2157b28f.png",
        "sha256": "cb7ce559e54956f53689a03c7760ed6e6ee166eeeb0cc5e3482a1b2b2157b28f"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      6.566666666666666,
      13.133333333333333,
      19.7,
      26.266666666666666,
      32.833333333333336,
      39.4,
      45.983333333333334,
      52.55,
      59.11666666666667,
      65.68333333333334,
      72.25,
      78.81666666666666,
      85.4,
      91.96666666666667,
      98.53333333333333,
      105.1,
      111.66666666666667,
      118.23333333333333,
      124.81666666666666,
      131.38333333333333,
      137.95,
      144.51666666666668,
      151.08333333333334,
      157.65,
      164.23333333333332,
      170.8,
      177.36666666666667,
      183.93333333333334,
      190.5,
      197.06666666666666,
      203.65
    ],
    "total_num_frames": 12220
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: meeting pod in frame 5; cable tray in frame 2; whiteboard in frame 11.\nOf these, the cable tray and the whiteboard are farthest apart, with the meeting pod off to the side.\n</think>\n\n70.35",
  "validation_commit": ""
}
```

## sb_rowLR_adbcc8ccea64b95f_q0

```json
{
  "answer": "83.73",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-20a9c0c3c18eb503e02f094b1e38f475f68ed8c555f67a398ce7ee85bf16cd14",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v39c04172a6e6",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        208,
        417,
        625,
        834,
        1042,
        1251,
        1459,
        1668,
        1876,
        2085,
        2294,
        2502,
        2711,
        2919,
        3128,
        3336,
        3545,
        3753,
        3962,
        4170,
        4379,
        4588,
        4796,
        5005,
        5213,
        5422,
        5630,
        5839,
        6047,
        6256,
        6465
      ],
      "options": [],
      "qid": "sb_rowLR_adbcc8ccea64b95f_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/3caf4324fd",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3caf4324fd",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      208,
      417,
      625,
      834,
      1042,
      1251,
      1459,
      1668,
      1876,
      2085,
      2294,
      2502,
      2711,
      2919,
      3128,
      3336,
      3545,
      3753,
      3962,
      4170,
      4379,
      4588,
      4796,
      5005,
      5213,
      5422,
      5630,
      5839,
      6047,
      6256,
      6465
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3caf4324fd.npz": "90fee210d3545b991ce39ea6c5190c64166bd9d1f4bf08753101fa6d3dbd09c7",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3caf4324fd",
    "room_measurement": {
      "area_m2": 83.73250000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 33493,
      "floor_height_m": 0.4929473252184736,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 25664
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 13,
          "centroid": [
            6.932894229810073,
            6.499448395439307,
            1.9324017465114591
          ],
          "footprint": 1.7663021069614135,
          "instance_id": 14,
          "label": "alcove bench",
          "pixel_share": 0.47638020833333333
        },
        {
          "best_view": 1,
          "centroid": [
            1.7898770713615662,
            4.082884274220596,
            1.9260519742965698
          ],
          "footprint": 1.503551783147177,
          "instance_id": 15,
          "label": "partition",
          "pixel_share": 0.32502604166666665
        },
        {
          "best_view": 19,
          "centroid": [
            12.90398163734725,
            2.1103036955368553,
            1.7110996544361112
          ],
          "footprint": 1.2356008110946537,
          "instance_id": 13,
          "label": "french door",
          "pixel_share": 0.0628515625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3caf4324fd.npz",
      "raster_sha256": "90fee210d3545b991ce39ea6c5190c64166bd9d1f4bf08753101fa6d3dbd09c7",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            6.932894229810073,
            6.499448395439307
          ],
          [
            1.7898770713615662,
            4.082884274220596
          ],
          [
            12.90398163734725,
            2.1103036955368553
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 3.2781380863328113,
        "projection": 0.411202857102676,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 11.2877984763666,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_080892423f679aae4dd9e21d",
    "source_row_sha256": "11a3d55419955f111ac5cccabbd539c19c7a480a6dcd350f3f5b66304f3f0f2e",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_adbcc8ccea64b95f_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v39c04172a6e6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      208,
      417,
      625,
      834,
      1042,
      1251,
      1459,
      1668,
      1876,
      2085,
      2294,
      2502,
      2711,
      2919,
      3128,
      3336,
      3545,
      3753,
      3962,
      4170,
      4379,
      4588,
      4796,
      5005,
      5213,
      5422,
      5630,
      5839,
      6047,
      6256,
      6465
    ],
    "frames": [
      {
        "path": "/data2/k6tk/91/91fb2a65319c7354d9d3dd48cdcf657f7afd97821770c351e97bb9a68d0e11cf.png",
        "sha256": "91fb2a65319c7354d9d3dd48cdcf657f7afd97821770c351e97bb9a68d0e11cf"
      },
      {
        "path": "/data2/k6tk/99/9905787b8d4d5e585ca5b8c76627d984f98aefbc21bce339fe8603e3f1ddb7d2.png",
        "sha256": "9905787b8d4d5e585ca5b8c76627d984f98aefbc21bce339fe8603e3f1ddb7d2"
      },
      {
        "path": "/data2/k6tk/46/467e93e8e711ac5ac968eaa4796f2c7588344e6669b1d9add6174298d0aa3d76.png",
        "sha256": "467e93e8e711ac5ac968eaa4796f2c7588344e6669b1d9add6174298d0aa3d76"
      },
      {
        "path": "/data2/k6tk/25/25e84d3ec4da1d37fb827d372cc12afcc16a41f6ed0958b556c440567e49ed51.png",
        "sha256": "25e84d3ec4da1d37fb827d372cc12afcc16a41f6ed0958b556c440567e49ed51"
      },
      {
        "path": "/data2/k6tk/9d/9deb398a72cce2f28d7f9041286d87d77e523ca500d9bceacfb660667b4e1df8.png",
        "sha256": "9deb398a72cce2f28d7f9041286d87d77e523ca500d9bceacfb660667b4e1df8"
      },
      {
        "path": "/data2/k6tk/a6/a6e9a8fcef5b1a48c3f5db549374d2a8ae47ceb4a796425bcf228cff996343a3.png",
        "sha256": "a6e9a8fcef5b1a48c3f5db549374d2a8ae47ceb4a796425bcf228cff996343a3"
      },
      {
        "path": "/data2/k6tk/db/db1977ecf0bc90a930afd7c5e90a58d2d33cdb856af5017ee8bc4aa88ec1e81d.png",
        "sha256": "db1977ecf0bc90a930afd7c5e90a58d2d33cdb856af5017ee8bc4aa88ec1e81d"
      },
      {
        "path": "/data2/k6tk/71/719bec698400f596dc2bf8fd63f7afa2bb6444fd0507211ec63210af2925caa3.png",
        "sha256": "719bec698400f596dc2bf8fd63f7afa2bb6444fd0507211ec63210af2925caa3"
      },
      {
        "path": "/data2/k6tk/5c/5c29dafc87d69eaed3cad8187aa2e4ad6e7c69552aeb5c607506ef4daff9b493.png",
        "sha256": "5c29dafc87d69eaed3cad8187aa2e4ad6e7c69552aeb5c607506ef4daff9b493"
      },
      {
        "path": "/data2/k6tk/80/80888d7ec426ce53d7dc289f762c8cfafedf3551c83cc0c88b084cfd6c5c1b8c.png",
        "sha256": "80888d7ec426ce53d7dc289f762c8cfafedf3551c83cc0c88b084cfd6c5c1b8c"
      },
      {
        "path": "/data2/k6tk/c9/c9a3bcbac4035f10f0cae105001a0b26a0d990c0ad36e8df31f6affdd6fa9ed3.png",
        "sha256": "c9a3bcbac4035f10f0cae105001a0b26a0d990c0ad36e8df31f6affdd6fa9ed3"
      },
      {
        "path": "/data2/k6tk/af/af8d250687b2d0215c67a289bbfbcd859b4bf56887a9dab1aeddfcd95df894c0.png",
        "sha256": "af8d250687b2d0215c67a289bbfbcd859b4bf56887a9dab1aeddfcd95df894c0"
      },
      {
        "path": "/data2/k6tk/fc/fc1e40d607d131bbebabe0388c7e7f4afc1797ab36088826906d9c4767593e69.png",
        "sha256": "fc1e40d607d131bbebabe0388c7e7f4afc1797ab36088826906d9c4767593e69"
      },
      {
        "path": "/data2/k6tk/51/5146048fb7b30f97ce50e1c95213a4bb3e06d1b227a360fff7ee0b6a2bd0fcbe.png",
        "sha256": "5146048fb7b30f97ce50e1c95213a4bb3e06d1b227a360fff7ee0b6a2bd0fcbe"
      },
      {
        "path": "/data2/k6tk/ca/cafe2982e5f41df08e0de0ed0c229a1bd56912c17b81c1be9b9ae3f3658c34ba.png",
        "sha256": "cafe2982e5f41df08e0de0ed0c229a1bd56912c17b81c1be9b9ae3f3658c34ba"
      },
      {
        "path": "/data2/k6tk/88/88d41074c0040b3ca54f7547f6c7440b9060d2c9990a25a17113af87f63b0603.png",
        "sha256": "88d41074c0040b3ca54f7547f6c7440b9060d2c9990a25a17113af87f63b0603"
      },
      {
        "path": "/data2/k6tk/7c/7cf6ecaac88591e49e885c085d7ebbaf58a3d1746a3e9932aec6f7c4a663c588.png",
        "sha256": "7cf6ecaac88591e49e885c085d7ebbaf58a3d1746a3e9932aec6f7c4a663c588"
      },
      {
        "path": "/data2/k6tk/53/53a00f89e17a6ef4ea0ee3535ec4fb5216ce3966335a8bfb00d0d61ff5cd7859.png",
        "sha256": "53a00f89e17a6ef4ea0ee3535ec4fb5216ce3966335a8bfb00d0d61ff5cd7859"
      },
      {
        "path": "/data2/k6tk/cb/cbd8ca14d3fee8a295fc1ae8a0b80e304dd48044748a40fa2c3adde6ab024ae6.png",
        "sha256": "cbd8ca14d3fee8a295fc1ae8a0b80e304dd48044748a40fa2c3adde6ab024ae6"
      },
      {
        "path": "/data2/k6tk/7d/7d77679aa87ab170a37df04fccd572a463b9d03fa969a0407034208f21eb5310.png",
        "sha256": "7d77679aa87ab170a37df04fccd572a463b9d03fa969a0407034208f21eb5310"
      },
      {
        "path": "/data2/k6tk/30/309c9e97eafd136ee3036011573cf0ad05b1b4a6294baddbe6e23a7257710ba8.png",
        "sha256": "309c9e97eafd136ee3036011573cf0ad05b1b4a6294baddbe6e23a7257710ba8"
      },
      {
        "path": "/data2/k6tk/eb/ebcebad2c6d340f0ec0ac5f886f861eda9974734e6e61777db572ef382a795e4.png",
        "sha256": "ebcebad2c6d340f0ec0ac5f886f861eda9974734e6e61777db572ef382a795e4"
      },
      {
        "path": "/data2/k6tk/92/92a7e253ef55a5b1624a26a4a1801d09b6d108c3d74e77a3eb6efa6d052563e7.png",
        "sha256": "92a7e253ef55a5b1624a26a4a1801d09b6d108c3d74e77a3eb6efa6d052563e7"
      },
      {
        "path": "/data2/k6tk/eb/eb4ab70186c8ace5b92361e1d9fa7842b04814ca071037a5852e3e049612db74.png",
        "sha256": "eb4ab70186c8ace5b92361e1d9fa7842b04814ca071037a5852e3e049612db74"
      },
      {
        "path": "/data2/k6tk/c2/c2ebb510add7e56e82494c93524a5469467611f8e86fbf231470e9054ab1dee4.png",
        "sha256": "c2ebb510add7e56e82494c93524a5469467611f8e86fbf231470e9054ab1dee4"
      },
      {
        "path": "/data2/k6tk/8d/8dd30771707df71507299d70db4d5a22669b288a4ec0b8f180a8e2b70510d901.png",
        "sha256": "8dd30771707df71507299d70db4d5a22669b288a4ec0b8f180a8e2b70510d901"
      },
      {
        "path": "/data2/k6tk/2b/2b10b3ae1f053eed76ccafe85b206f91a46ab12e9031eb1b08efd1e2c92002b9.png",
        "sha256": "2b10b3ae1f053eed76ccafe85b206f91a46ab12e9031eb1b08efd1e2c92002b9"
      },
      {
        "path": "/data2/k6tk/db/dbbbfb30b17c1358eddb8ba0c713484db1f24ea52361937622353bd4494fb779.png",
        "sha256": "dbbbfb30b17c1358eddb8ba0c713484db1f24ea52361937622353bd4494fb779"
      },
      {
        "path": "/data2/k6tk/32/326bea62005e76c98512e9a973141c2accb0df1f1eb018136472bcd60d5ece55.png",
        "sha256": "326bea62005e76c98512e9a973141c2accb0df1f1eb018136472bcd60d5ece55"
      },
      {
        "path": "/data2/k6tk/d6/d6e7cd3ced3b0c300f7c7abe570792abf27e1d7f955b0ba6571419801a6c3880.png",
        "sha256": "d6e7cd3ced3b0c300f7c7abe570792abf27e1d7f955b0ba6571419801a6c3880"
      },
      {
        "path": "/data2/k6tk/b7/b7dd58cbeee15800385bb7be0c4f28421def2a4ac0cf34b2cb9132a16f87cfc6.png",
        "sha256": "b7dd58cbeee15800385bb7be0c4f28421def2a4ac0cf34b2cb9132a16f87cfc6"
      },
      {
        "path": "/data2/k6tk/a2/a2f99d8ce09feb83ab837699436cb19eb99899220b60f6ae0c8ebcdc0e8ebdaa.png",
        "sha256": "a2f99d8ce09feb83ab837699436cb19eb99899220b60f6ae0c8ebcdc0e8ebdaa"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      3.466666666666667,
      6.95,
      10.416666666666666,
      13.9,
      17.366666666666667,
      20.85,
      24.316666666666666,
      27.8,
      31.266666666666666,
      34.75,
      38.233333333333334,
      41.7,
      45.18333333333333,
      48.65,
      52.13333333333333,
      55.6,
      59.083333333333336,
      62.55,
      66.03333333333333,
      69.5,
      72.98333333333333,
      76.46666666666667,
      79.93333333333334,
      83.41666666666667,
      86.88333333333334,
      90.36666666666666,
      93.83333333333333,
      97.31666666666666,
      100.78333333333333,
      104.26666666666667,
      107.75
    ],
    "total_num_frames": 6466
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: alcove bench in frame 13; partition in frame 1; french door in frame 19.\nOf these, the partition and the french door are farthest apart, with the alcove bench between them.\n</think>\n\n83.73",
  "validation_commit": ""
}
```

## sb_rowLR_adbcc8ccea64b95f_q1

```json
{
  "answer": "83.73",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-58fa0edd275718266fc74da2fe4ec609905ee5f4466f4b40a9921b69f54530cf",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v39c04172a6e6",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        208,
        417,
        625,
        834,
        1042,
        1251,
        1459,
        1668,
        1876,
        2085,
        2294,
        2502,
        2711,
        2919,
        3128,
        3336,
        3545,
        3753,
        3962,
        4170,
        4379,
        4588,
        4796,
        5005,
        5213,
        5422,
        5630,
        5839,
        6047,
        6256,
        6465
      ],
      "options": [],
      "qid": "sb_rowLR_adbcc8ccea64b95f_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/3caf4324fd",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3caf4324fd",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      208,
      417,
      625,
      834,
      1042,
      1251,
      1459,
      1668,
      1876,
      2085,
      2294,
      2502,
      2711,
      2919,
      3128,
      3336,
      3545,
      3753,
      3962,
      4170,
      4379,
      4588,
      4796,
      5005,
      5213,
      5422,
      5630,
      5839,
      6047,
      6256,
      6465
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3caf4324fd.npz": "90fee210d3545b991ce39ea6c5190c64166bd9d1f4bf08753101fa6d3dbd09c7",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3caf4324fd",
    "room_measurement": {
      "area_m2": 83.73250000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 33493,
      "floor_height_m": 0.4929473252184736,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 25664
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 13,
          "centroid": [
            6.932894229810073,
            6.499448395439307,
            1.9324017465114591
          ],
          "footprint": 1.7663021069614135,
          "instance_id": 14,
          "label": "alcove bench",
          "pixel_share": 0.47638020833333333
        },
        {
          "best_view": 1,
          "centroid": [
            1.7898770713615662,
            4.082884274220596,
            1.9260519742965698
          ],
          "footprint": 1.503551783147177,
          "instance_id": 15,
          "label": "partition",
          "pixel_share": 0.32502604166666665
        },
        {
          "best_view": 19,
          "centroid": [
            12.90398163734725,
            2.1103036955368553,
            1.7110996544361112
          ],
          "footprint": 1.2356008110946537,
          "instance_id": 13,
          "label": "french door",
          "pixel_share": 0.0628515625
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3caf4324fd.npz",
      "raster_sha256": "90fee210d3545b991ce39ea6c5190c64166bd9d1f4bf08753101fa6d3dbd09c7",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            6.932894229810073,
            6.499448395439307
          ],
          [
            1.7898770713615662,
            4.082884274220596
          ],
          [
            12.90398163734725,
            2.1103036955368553
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 3.2781380863328113,
        "projection": 0.411202857102676,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 11.2877984763666,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12ct_080892423f679aae4dd9e21d",
    "source_row_sha256": "11a3d55419955f111ac5cccabbd539c19c7a480a6dcd350f3f5b66304f3f0f2e",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_adbcc8ccea64b95f_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v39c04172a6e6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      208,
      417,
      625,
      834,
      1042,
      1251,
      1459,
      1668,
      1876,
      2085,
      2294,
      2502,
      2711,
      2919,
      3128,
      3336,
      3545,
      3753,
      3962,
      4170,
      4379,
      4588,
      4796,
      5005,
      5213,
      5422,
      5630,
      5839,
      6047,
      6256,
      6465
    ],
    "frames": [
      {
        "path": "/data2/k6tk/91/91fb2a65319c7354d9d3dd48cdcf657f7afd97821770c351e97bb9a68d0e11cf.png",
        "sha256": "91fb2a65319c7354d9d3dd48cdcf657f7afd97821770c351e97bb9a68d0e11cf"
      },
      {
        "path": "/data2/k6tk/99/9905787b8d4d5e585ca5b8c76627d984f98aefbc21bce339fe8603e3f1ddb7d2.png",
        "sha256": "9905787b8d4d5e585ca5b8c76627d984f98aefbc21bce339fe8603e3f1ddb7d2"
      },
      {
        "path": "/data2/k6tk/46/467e93e8e711ac5ac968eaa4796f2c7588344e6669b1d9add6174298d0aa3d76.png",
        "sha256": "467e93e8e711ac5ac968eaa4796f2c7588344e6669b1d9add6174298d0aa3d76"
      },
      {
        "path": "/data2/k6tk/25/25e84d3ec4da1d37fb827d372cc12afcc16a41f6ed0958b556c440567e49ed51.png",
        "sha256": "25e84d3ec4da1d37fb827d372cc12afcc16a41f6ed0958b556c440567e49ed51"
      },
      {
        "path": "/data2/k6tk/9d/9deb398a72cce2f28d7f9041286d87d77e523ca500d9bceacfb660667b4e1df8.png",
        "sha256": "9deb398a72cce2f28d7f9041286d87d77e523ca500d9bceacfb660667b4e1df8"
      },
      {
        "path": "/data2/k6tk/a6/a6e9a8fcef5b1a48c3f5db549374d2a8ae47ceb4a796425bcf228cff996343a3.png",
        "sha256": "a6e9a8fcef5b1a48c3f5db549374d2a8ae47ceb4a796425bcf228cff996343a3"
      },
      {
        "path": "/data2/k6tk/db/db1977ecf0bc90a930afd7c5e90a58d2d33cdb856af5017ee8bc4aa88ec1e81d.png",
        "sha256": "db1977ecf0bc90a930afd7c5e90a58d2d33cdb856af5017ee8bc4aa88ec1e81d"
      },
      {
        "path": "/data2/k6tk/71/719bec698400f596dc2bf8fd63f7afa2bb6444fd0507211ec63210af2925caa3.png",
        "sha256": "719bec698400f596dc2bf8fd63f7afa2bb6444fd0507211ec63210af2925caa3"
      },
      {
        "path": "/data2/k6tk/5c/5c29dafc87d69eaed3cad8187aa2e4ad6e7c69552aeb5c607506ef4daff9b493.png",
        "sha256": "5c29dafc87d69eaed3cad8187aa2e4ad6e7c69552aeb5c607506ef4daff9b493"
      },
      {
        "path": "/data2/k6tk/80/80888d7ec426ce53d7dc289f762c8cfafedf3551c83cc0c88b084cfd6c5c1b8c.png",
        "sha256": "80888d7ec426ce53d7dc289f762c8cfafedf3551c83cc0c88b084cfd6c5c1b8c"
      },
      {
        "path": "/data2/k6tk/c9/c9a3bcbac4035f10f0cae105001a0b26a0d990c0ad36e8df31f6affdd6fa9ed3.png",
        "sha256": "c9a3bcbac4035f10f0cae105001a0b26a0d990c0ad36e8df31f6affdd6fa9ed3"
      },
      {
        "path": "/data2/k6tk/af/af8d250687b2d0215c67a289bbfbcd859b4bf56887a9dab1aeddfcd95df894c0.png",
        "sha256": "af8d250687b2d0215c67a289bbfbcd859b4bf56887a9dab1aeddfcd95df894c0"
      },
      {
        "path": "/data2/k6tk/fc/fc1e40d607d131bbebabe0388c7e7f4afc1797ab36088826906d9c4767593e69.png",
        "sha256": "fc1e40d607d131bbebabe0388c7e7f4afc1797ab36088826906d9c4767593e69"
      },
      {
        "path": "/data2/k6tk/51/5146048fb7b30f97ce50e1c95213a4bb3e06d1b227a360fff7ee0b6a2bd0fcbe.png",
        "sha256": "5146048fb7b30f97ce50e1c95213a4bb3e06d1b227a360fff7ee0b6a2bd0fcbe"
      },
      {
        "path": "/data2/k6tk/ca/cafe2982e5f41df08e0de0ed0c229a1bd56912c17b81c1be9b9ae3f3658c34ba.png",
        "sha256": "cafe2982e5f41df08e0de0ed0c229a1bd56912c17b81c1be9b9ae3f3658c34ba"
      },
      {
        "path": "/data2/k6tk/88/88d41074c0040b3ca54f7547f6c7440b9060d2c9990a25a17113af87f63b0603.png",
        "sha256": "88d41074c0040b3ca54f7547f6c7440b9060d2c9990a25a17113af87f63b0603"
      },
      {
        "path": "/data2/k6tk/7c/7cf6ecaac88591e49e885c085d7ebbaf58a3d1746a3e9932aec6f7c4a663c588.png",
        "sha256": "7cf6ecaac88591e49e885c085d7ebbaf58a3d1746a3e9932aec6f7c4a663c588"
      },
      {
        "path": "/data2/k6tk/53/53a00f89e17a6ef4ea0ee3535ec4fb5216ce3966335a8bfb00d0d61ff5cd7859.png",
        "sha256": "53a00f89e17a6ef4ea0ee3535ec4fb5216ce3966335a8bfb00d0d61ff5cd7859"
      },
      {
        "path": "/data2/k6tk/cb/cbd8ca14d3fee8a295fc1ae8a0b80e304dd48044748a40fa2c3adde6ab024ae6.png",
        "sha256": "cbd8ca14d3fee8a295fc1ae8a0b80e304dd48044748a40fa2c3adde6ab024ae6"
      },
      {
        "path": "/data2/k6tk/7d/7d77679aa87ab170a37df04fccd572a463b9d03fa969a0407034208f21eb5310.png",
        "sha256": "7d77679aa87ab170a37df04fccd572a463b9d03fa969a0407034208f21eb5310"
      },
      {
        "path": "/data2/k6tk/30/309c9e97eafd136ee3036011573cf0ad05b1b4a6294baddbe6e23a7257710ba8.png",
        "sha256": "309c9e97eafd136ee3036011573cf0ad05b1b4a6294baddbe6e23a7257710ba8"
      },
      {
        "path": "/data2/k6tk/eb/ebcebad2c6d340f0ec0ac5f886f861eda9974734e6e61777db572ef382a795e4.png",
        "sha256": "ebcebad2c6d340f0ec0ac5f886f861eda9974734e6e61777db572ef382a795e4"
      },
      {
        "path": "/data2/k6tk/92/92a7e253ef55a5b1624a26a4a1801d09b6d108c3d74e77a3eb6efa6d052563e7.png",
        "sha256": "92a7e253ef55a5b1624a26a4a1801d09b6d108c3d74e77a3eb6efa6d052563e7"
      },
      {
        "path": "/data2/k6tk/eb/eb4ab70186c8ace5b92361e1d9fa7842b04814ca071037a5852e3e049612db74.png",
        "sha256": "eb4ab70186c8ace5b92361e1d9fa7842b04814ca071037a5852e3e049612db74"
      },
      {
        "path": "/data2/k6tk/c2/c2ebb510add7e56e82494c93524a5469467611f8e86fbf231470e9054ab1dee4.png",
        "sha256": "c2ebb510add7e56e82494c93524a5469467611f8e86fbf231470e9054ab1dee4"
      },
      {
        "path": "/data2/k6tk/8d/8dd30771707df71507299d70db4d5a22669b288a4ec0b8f180a8e2b70510d901.png",
        "sha256": "8dd30771707df71507299d70db4d5a22669b288a4ec0b8f180a8e2b70510d901"
      },
      {
        "path": "/data2/k6tk/2b/2b10b3ae1f053eed76ccafe85b206f91a46ab12e9031eb1b08efd1e2c92002b9.png",
        "sha256": "2b10b3ae1f053eed76ccafe85b206f91a46ab12e9031eb1b08efd1e2c92002b9"
      },
      {
        "path": "/data2/k6tk/db/dbbbfb30b17c1358eddb8ba0c713484db1f24ea52361937622353bd4494fb779.png",
        "sha256": "dbbbfb30b17c1358eddb8ba0c713484db1f24ea52361937622353bd4494fb779"
      },
      {
        "path": "/data2/k6tk/32/326bea62005e76c98512e9a973141c2accb0df1f1eb018136472bcd60d5ece55.png",
        "sha256": "326bea62005e76c98512e9a973141c2accb0df1f1eb018136472bcd60d5ece55"
      },
      {
        "path": "/data2/k6tk/d6/d6e7cd3ced3b0c300f7c7abe570792abf27e1d7f955b0ba6571419801a6c3880.png",
        "sha256": "d6e7cd3ced3b0c300f7c7abe570792abf27e1d7f955b0ba6571419801a6c3880"
      },
      {
        "path": "/data2/k6tk/b7/b7dd58cbeee15800385bb7be0c4f28421def2a4ac0cf34b2cb9132a16f87cfc6.png",
        "sha256": "b7dd58cbeee15800385bb7be0c4f28421def2a4ac0cf34b2cb9132a16f87cfc6"
      },
      {
        "path": "/data2/k6tk/a2/a2f99d8ce09feb83ab837699436cb19eb99899220b60f6ae0c8ebcdc0e8ebdaa.png",
        "sha256": "a2f99d8ce09feb83ab837699436cb19eb99899220b60f6ae0c8ebcdc0e8ebdaa"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      3.466666666666667,
      6.95,
      10.416666666666666,
      13.9,
      17.366666666666667,
      20.85,
      24.316666666666666,
      27.8,
      31.266666666666666,
      34.75,
      38.233333333333334,
      41.7,
      45.18333333333333,
      48.65,
      52.13333333333333,
      55.6,
      59.083333333333336,
      62.55,
      66.03333333333333,
      69.5,
      72.98333333333333,
      76.46666666666667,
      79.93333333333334,
      83.41666666666667,
      86.88333333333334,
      90.36666666666666,
      93.83333333333333,
      97.31666666666666,
      100.78333333333333,
      104.26666666666667,
      107.75
    ],
    "total_num_frames": 6466
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: alcove bench in frame 13; partition in frame 1; french door in frame 19.\nThe partition and the french door are the farthest apart among these landmarks, with the alcove bench between them.\n</think>\n\n83.73",
  "validation_commit": ""
}
```

## sb_rowLR_5d5688755955a777_q0

```json
{
  "answer": "64.52",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-671e3dd08bde8be735a61d41d9ef58fe21d9385cbd6ae1e925a7baed2e10cf37",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v8a09e79ded01",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        315,
        630,
        945,
        1260,
        1575,
        1890,
        2205,
        2520,
        2835,
        3150,
        3465,
        3780,
        4095,
        4410,
        4725,
        5040,
        5355,
        5670,
        5985,
        6300,
        6615,
        6930,
        7245,
        7560,
        7875,
        8190,
        8505,
        8820,
        9135,
        9450,
        9765
      ],
      "options": [],
      "qid": "sb_rowLR_5d5688755955a777_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/124a6e789b",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/124a6e789b",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      315,
      630,
      945,
      1260,
      1575,
      1890,
      2205,
      2520,
      2835,
      3150,
      3465,
      3780,
      4095,
      4410,
      4725,
      5040,
      5355,
      5670,
      5985,
      6300,
      6615,
      6930,
      7245,
      7560,
      7875,
      8190,
      8505,
      8820,
      9135,
      9450,
      9765
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__124a6e789b.npz": "c1043c05da61668c9e6cc55d20ef9d4148678f1ce52ed1e6a5a193127b9e5ff8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/124a6e789b",
    "room_measurement": {
      "area_m2": 64.51750000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 25807,
      "floor_height_m": 0.1069773686934172,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 18392
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 31,
          "centroid": [
            3.345376520296914,
            6.992987278135504,
            2.6254075169563293
          ],
          "footprint": 2.364600016448552,
          "instance_id": 41,
          "label": "curtain",
          "pixel_share": 0.24795572916666667
        },
        {
          "best_view": 27,
          "centroid": [
            4.302795993858962,
            7.208660958140078,
            0.9560490250587464
          ],
          "footprint": 0.9937751607193805,
          "instance_id": 102,
          "label": "window sill",
          "pixel_share": 0.22993489583333335
        },
        {
          "best_view": 27,
          "centroid": [
            2.2361791211806605,
            5.867037617296172,
            0.8000441938638686
          ],
          "footprint": 0.24884130494719178,
          "instance_id": 85,
          "label": "podium",
          "pixel_share": 0.12134114583333333
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__124a6e789b.npz",
      "raster_sha256": "c1043c05da61668c9e6cc55d20ef9d4148678f1ce52ed1e6a5a193127b9e5ff8",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.345376520296914,
            6.992987278135504
          ],
          [
            4.302795993858962,
            7.208660958140078
          ],
          [
            2.2361791211806605,
            5.867037617296172
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.3404268143682718,
        "projection": 0.3735834208950498,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 2.4639112173809763,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12ct_683254231b39fcf86042748d",
    "source_row_sha256": "46ae73ed648e7f7a1a6adc701a5c2519a6b9004420758bc93ce7b66e8c217224",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_5d5688755955a777_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v8a09e79ded01",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      315,
      630,
      945,
      1260,
      1575,
      1890,
      2205,
      2520,
      2835,
      3150,
      3465,
      3780,
      4095,
      4410,
      4725,
      5040,
      5355,
      5670,
      5985,
      6300,
      6615,
      6930,
      7245,
      7560,
      7875,
      8190,
      8505,
      8820,
      9135,
      9450,
      9765
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a7/a7ac4760c062d48876ee80d44f32ae2857bc3cad9ed50c6355ab33b40b0c306e.png",
        "sha256": "a7ac4760c062d48876ee80d44f32ae2857bc3cad9ed50c6355ab33b40b0c306e"
      },
      {
        "path": "/data2/k6tk/5b/5bdf1505848b8cff80a30384ce6e25db3752716444062369c4dd32058aa3a5d7.png",
        "sha256": "5bdf1505848b8cff80a30384ce6e25db3752716444062369c4dd32058aa3a5d7"
      },
      {
        "path": "/data2/k6tk/fe/fe8da4e7c8072be9b8d0ef8797fc537728f807cbda5cd8794dca65953217559c.png",
        "sha256": "fe8da4e7c8072be9b8d0ef8797fc537728f807cbda5cd8794dca65953217559c"
      },
      {
        "path": "/data2/k6tk/c8/c8062861e038e7395128c4ce09aa172b5c18b5c88ddf53443fbd33b5c9151025.png",
        "sha256": "c8062861e038e7395128c4ce09aa172b5c18b5c88ddf53443fbd33b5c9151025"
      },
      {
        "path": "/data2/k6tk/6d/6d8c0746b16e2e004485c5336a8790cfcf720467f4986377b7955ce4a0b3e432.png",
        "sha256": "6d8c0746b16e2e004485c5336a8790cfcf720467f4986377b7955ce4a0b3e432"
      },
      {
        "path": "/data2/k6tk/ac/ac8bfefee20290ec66dbca3bd39e798b98b2fb30c47343175c0f647dd4fca9dc.png",
        "sha256": "ac8bfefee20290ec66dbca3bd39e798b98b2fb30c47343175c0f647dd4fca9dc"
      },
      {
        "path": "/data2/k6tk/a4/a4579cc4d872ec531fc509a297efd0721a8cb55f9a746f2c15941e591047fb4b.png",
        "sha256": "a4579cc4d872ec531fc509a297efd0721a8cb55f9a746f2c15941e591047fb4b"
      },
      {
        "path": "/data2/k6tk/7e/7e80f27da940054dfd597fa111943c2337914e796ef47639335251fb5396d4f4.png",
        "sha256": "7e80f27da940054dfd597fa111943c2337914e796ef47639335251fb5396d4f4"
      },
      {
        "path": "/data2/k6tk/d9/d904c05b7acfd1b7f9c0098c72ee41af2dc0d20e6acb394bce02b69854c0fdbb.png",
        "sha256": "d904c05b7acfd1b7f9c0098c72ee41af2dc0d20e6acb394bce02b69854c0fdbb"
      },
      {
        "path": "/data2/k6tk/6f/6f2d08c43c4f6077c5209484d451c2a6520a8be9c9dff922728de61227bcab3d.png",
        "sha256": "6f2d08c43c4f6077c5209484d451c2a6520a8be9c9dff922728de61227bcab3d"
      },
      {
        "path": "/data2/k6tk/1b/1b6a02e067645e0de492635f07048533d2ae533b7ec977269465a74c6e010f01.png",
        "sha256": "1b6a02e067645e0de492635f07048533d2ae533b7ec977269465a74c6e010f01"
      },
      {
        "path": "/data2/k6tk/c8/c8993dede1e06be97f4fbb83e404a42cd5cf11f7439a4fd4b957463a33220cbe.png",
        "sha256": "c8993dede1e06be97f4fbb83e404a42cd5cf11f7439a4fd4b957463a33220cbe"
      },
      {
        "path": "/data2/k6tk/e8/e81c8576faad6f12c17c3a73b0f606fc90401cc8277f3031c1370cefcf8cc706.png",
        "sha256": "e81c8576faad6f12c17c3a73b0f606fc90401cc8277f3031c1370cefcf8cc706"
      },
      {
        "path": "/data2/k6tk/ed/ed6bac8f92e235b6e55068d79ec2f0e88b0744184bed093c3fc4b639bbacc0bc.png",
        "sha256": "ed6bac8f92e235b6e55068d79ec2f0e88b0744184bed093c3fc4b639bbacc0bc"
      },
      {
        "path": "/data2/k6tk/d1/d10d22f60d5378d3b3133a6dcec2fd9e6dacd80b8823ce421c95bcbc9684c55d.png",
        "sha256": "d10d22f60d5378d3b3133a6dcec2fd9e6dacd80b8823ce421c95bcbc9684c55d"
      },
      {
        "path": "/data2/k6tk/3e/3ed6761da95a647ecf055ea5754e6c72d76fac2c143be243b3e4e91637958568.png",
        "sha256": "3ed6761da95a647ecf055ea5754e6c72d76fac2c143be243b3e4e91637958568"
      },
      {
        "path": "/data2/k6tk/0a/0ad0fa7e6bb9e3fc917e727947ba507be5d0e5909d9d8411265b75571f05df9c.png",
        "sha256": "0ad0fa7e6bb9e3fc917e727947ba507be5d0e5909d9d8411265b75571f05df9c"
      },
      {
        "path": "/data2/k6tk/75/750ef077d6fa4ef2c6bc227b50b4baea99ab8fdbada36dd0c0495f10455040ea.png",
        "sha256": "750ef077d6fa4ef2c6bc227b50b4baea99ab8fdbada36dd0c0495f10455040ea"
      },
      {
        "path": "/data2/k6tk/a6/a646c20b1decae00d9b3c8956e9f2aa29db56ae9b6293f084c1b5bbed90d9166.png",
        "sha256": "a646c20b1decae00d9b3c8956e9f2aa29db56ae9b6293f084c1b5bbed90d9166"
      },
      {
        "path": "/data2/k6tk/0a/0a8b7b2b0fd7a845046c2760395f4e10e04974fc6728c05c7a13bce7ab5f4936.png",
        "sha256": "0a8b7b2b0fd7a845046c2760395f4e10e04974fc6728c05c7a13bce7ab5f4936"
      },
      {
        "path": "/data2/k6tk/98/98c9cd5d411d6f1c461150cf1966e25da9f98e25357deb1741ab064cd3b97a6a.png",
        "sha256": "98c9cd5d411d6f1c461150cf1966e25da9f98e25357deb1741ab064cd3b97a6a"
      },
      {
        "path": "/data2/k6tk/88/88d1489523124f47d7c3a66c38b07771c68bba46ab0b9cfee29478206787230f.png",
        "sha256": "88d1489523124f47d7c3a66c38b07771c68bba46ab0b9cfee29478206787230f"
      },
      {
        "path": "/data2/k6tk/f3/f325a8c11bc1aca23955e5717758a6b81a4081bdade7f06c5e989f736dee99cb.png",
        "sha256": "f325a8c11bc1aca23955e5717758a6b81a4081bdade7f06c5e989f736dee99cb"
      },
      {
        "path": "/data2/k6tk/6a/6a35346ef7b7fae76dfaa4809f2b3383a3ef0339f36a09efa0f4aff9cd1b0937.png",
        "sha256": "6a35346ef7b7fae76dfaa4809f2b3383a3ef0339f36a09efa0f4aff9cd1b0937"
      },
      {
        "path": "/data2/k6tk/78/78b3dafdedff21ead79f10a1768b782ece826cb55ca15e8c26273c6420c3d98f.png",
        "sha256": "78b3dafdedff21ead79f10a1768b782ece826cb55ca15e8c26273c6420c3d98f"
      },
      {
        "path": "/data2/k6tk/f5/f525d24051807351f1f8b4bee63b66cfb7928e8477e3cbe7d3860cfa06bda263.png",
        "sha256": "f525d24051807351f1f8b4bee63b66cfb7928e8477e3cbe7d3860cfa06bda263"
      },
      {
        "path": "/data2/k6tk/58/5805685da38cc7375540027510cc5ea5b2fb045a98090c78c6f395ff2379a814.png",
        "sha256": "5805685da38cc7375540027510cc5ea5b2fb045a98090c78c6f395ff2379a814"
      },
      {
        "path": "/data2/k6tk/82/82501f4068b5d55c27bacd18736a3b1489cffa74e78572e7433d6282ad944990.png",
        "sha256": "82501f4068b5d55c27bacd18736a3b1489cffa74e78572e7433d6282ad944990"
      },
      {
        "path": "/data2/k6tk/9d/9d51584c5d12f8b65540441fc96babdd9f341e4d04c019d26daf6e1ea72cc123.png",
        "sha256": "9d51584c5d12f8b65540441fc96babdd9f341e4d04c019d26daf6e1ea72cc123"
      },
      {
        "path": "/data2/k6tk/0c/0cf282b18577cab9091af9927f3cf8814f10709b1bc1fc16bc0f185257254c4c.png",
        "sha256": "0cf282b18577cab9091af9927f3cf8814f10709b1bc1fc16bc0f185257254c4c"
      },
      {
        "path": "/data2/k6tk/c3/c3bbb4634409042519ba7f4915a8bb1ba0ed1d7debb1ce9535125283b0747f0b.png",
        "sha256": "c3bbb4634409042519ba7f4915a8bb1ba0ed1d7debb1ce9535125283b0747f0b"
      },
      {
        "path": "/data2/k6tk/9e/9ebccd5244f29b42ebb1d9b1a4c0ffe776481d60066dcc9900bea66ccb1221b9.png",
        "sha256": "9ebccd5244f29b42ebb1d9b1a4c0ffe776481d60066dcc9900bea66ccb1221b9"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.25,
      10.5,
      15.75,
      21.0,
      26.25,
      31.5,
      36.75,
      42.0,
      47.25,
      52.5,
      57.75,
      63.0,
      68.25,
      73.5,
      78.75,
      84.0,
      89.25,
      94.5,
      99.75,
      105.0,
      110.25,
      115.5,
      120.75,
      126.0,
      131.25,
      136.5,
      141.75,
      147.0,
      152.25,
      157.5,
      162.75
    ],
    "total_num_frames": 9766
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: curtain in frame 31; window sill in frame 27; podium in frame 27.\nThe window sill and the podium are the farthest apart among these landmarks, with the curtain between them.\n</think>\n\n64.52",
  "validation_commit": ""
}
```

## sb_rowLR_5d5688755955a777_q1

```json
{
  "answer": "64.52",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-4d49c5746afa96ce03236d77cf116d8605e38da1d937fe6cd06f3d5d303a5595",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v8a09e79ded01",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        315,
        630,
        945,
        1260,
        1575,
        1890,
        2205,
        2520,
        2835,
        3150,
        3465,
        3780,
        4095,
        4410,
        4725,
        5040,
        5355,
        5670,
        5985,
        6300,
        6615,
        6930,
        7245,
        7560,
        7875,
        8190,
        8505,
        8820,
        9135,
        9450,
        9765
      ],
      "options": [],
      "qid": "sb_rowLR_5d5688755955a777_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/124a6e789b",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/124a6e789b",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      315,
      630,
      945,
      1260,
      1575,
      1890,
      2205,
      2520,
      2835,
      3150,
      3465,
      3780,
      4095,
      4410,
      4725,
      5040,
      5355,
      5670,
      5985,
      6300,
      6615,
      6930,
      7245,
      7560,
      7875,
      8190,
      8505,
      8820,
      9135,
      9450,
      9765
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__124a6e789b.npz": "c1043c05da61668c9e6cc55d20ef9d4148678f1ce52ed1e6a5a193127b9e5ff8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/124a6e789b",
    "room_measurement": {
      "area_m2": 64.51750000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 25807,
      "floor_height_m": 0.1069773686934172,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 18392
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 31,
          "centroid": [
            3.345376520296914,
            6.992987278135504,
            2.6254075169563293
          ],
          "footprint": 2.364600016448552,
          "instance_id": 41,
          "label": "curtain",
          "pixel_share": 0.24795572916666667
        },
        {
          "best_view": 27,
          "centroid": [
            4.302795993858962,
            7.208660958140078,
            0.9560490250587464
          ],
          "footprint": 0.9937751607193805,
          "instance_id": 102,
          "label": "window sill",
          "pixel_share": 0.22993489583333335
        },
        {
          "best_view": 27,
          "centroid": [
            2.2361791211806605,
            5.867037617296172,
            0.8000441938638686
          ],
          "footprint": 0.24884130494719178,
          "instance_id": 85,
          "label": "podium",
          "pixel_share": 0.12134114583333333
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__124a6e789b.npz",
      "raster_sha256": "c1043c05da61668c9e6cc55d20ef9d4148678f1ce52ed1e6a5a193127b9e5ff8",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.345376520296914,
            6.992987278135504
          ],
          [
            4.302795993858962,
            7.208660958140078
          ],
          [
            2.2361791211806605,
            5.867037617296172
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.3404268143682718,
        "projection": 0.3735834208950498,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 2.4639112173809763,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_683254231b39fcf86042748d",
    "source_row_sha256": "46ae73ed648e7f7a1a6adc701a5c2519a6b9004420758bc93ce7b66e8c217224",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_5d5688755955a777_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v8a09e79ded01",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      315,
      630,
      945,
      1260,
      1575,
      1890,
      2205,
      2520,
      2835,
      3150,
      3465,
      3780,
      4095,
      4410,
      4725,
      5040,
      5355,
      5670,
      5985,
      6300,
      6615,
      6930,
      7245,
      7560,
      7875,
      8190,
      8505,
      8820,
      9135,
      9450,
      9765
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a7/a7ac4760c062d48876ee80d44f32ae2857bc3cad9ed50c6355ab33b40b0c306e.png",
        "sha256": "a7ac4760c062d48876ee80d44f32ae2857bc3cad9ed50c6355ab33b40b0c306e"
      },
      {
        "path": "/data2/k6tk/5b/5bdf1505848b8cff80a30384ce6e25db3752716444062369c4dd32058aa3a5d7.png",
        "sha256": "5bdf1505848b8cff80a30384ce6e25db3752716444062369c4dd32058aa3a5d7"
      },
      {
        "path": "/data2/k6tk/fe/fe8da4e7c8072be9b8d0ef8797fc537728f807cbda5cd8794dca65953217559c.png",
        "sha256": "fe8da4e7c8072be9b8d0ef8797fc537728f807cbda5cd8794dca65953217559c"
      },
      {
        "path": "/data2/k6tk/c8/c8062861e038e7395128c4ce09aa172b5c18b5c88ddf53443fbd33b5c9151025.png",
        "sha256": "c8062861e038e7395128c4ce09aa172b5c18b5c88ddf53443fbd33b5c9151025"
      },
      {
        "path": "/data2/k6tk/6d/6d8c0746b16e2e004485c5336a8790cfcf720467f4986377b7955ce4a0b3e432.png",
        "sha256": "6d8c0746b16e2e004485c5336a8790cfcf720467f4986377b7955ce4a0b3e432"
      },
      {
        "path": "/data2/k6tk/ac/ac8bfefee20290ec66dbca3bd39e798b98b2fb30c47343175c0f647dd4fca9dc.png",
        "sha256": "ac8bfefee20290ec66dbca3bd39e798b98b2fb30c47343175c0f647dd4fca9dc"
      },
      {
        "path": "/data2/k6tk/a4/a4579cc4d872ec531fc509a297efd0721a8cb55f9a746f2c15941e591047fb4b.png",
        "sha256": "a4579cc4d872ec531fc509a297efd0721a8cb55f9a746f2c15941e591047fb4b"
      },
      {
        "path": "/data2/k6tk/7e/7e80f27da940054dfd597fa111943c2337914e796ef47639335251fb5396d4f4.png",
        "sha256": "7e80f27da940054dfd597fa111943c2337914e796ef47639335251fb5396d4f4"
      },
      {
        "path": "/data2/k6tk/d9/d904c05b7acfd1b7f9c0098c72ee41af2dc0d20e6acb394bce02b69854c0fdbb.png",
        "sha256": "d904c05b7acfd1b7f9c0098c72ee41af2dc0d20e6acb394bce02b69854c0fdbb"
      },
      {
        "path": "/data2/k6tk/6f/6f2d08c43c4f6077c5209484d451c2a6520a8be9c9dff922728de61227bcab3d.png",
        "sha256": "6f2d08c43c4f6077c5209484d451c2a6520a8be9c9dff922728de61227bcab3d"
      },
      {
        "path": "/data2/k6tk/1b/1b6a02e067645e0de492635f07048533d2ae533b7ec977269465a74c6e010f01.png",
        "sha256": "1b6a02e067645e0de492635f07048533d2ae533b7ec977269465a74c6e010f01"
      },
      {
        "path": "/data2/k6tk/c8/c8993dede1e06be97f4fbb83e404a42cd5cf11f7439a4fd4b957463a33220cbe.png",
        "sha256": "c8993dede1e06be97f4fbb83e404a42cd5cf11f7439a4fd4b957463a33220cbe"
      },
      {
        "path": "/data2/k6tk/e8/e81c8576faad6f12c17c3a73b0f606fc90401cc8277f3031c1370cefcf8cc706.png",
        "sha256": "e81c8576faad6f12c17c3a73b0f606fc90401cc8277f3031c1370cefcf8cc706"
      },
      {
        "path": "/data2/k6tk/ed/ed6bac8f92e235b6e55068d79ec2f0e88b0744184bed093c3fc4b639bbacc0bc.png",
        "sha256": "ed6bac8f92e235b6e55068d79ec2f0e88b0744184bed093c3fc4b639bbacc0bc"
      },
      {
        "path": "/data2/k6tk/d1/d10d22f60d5378d3b3133a6dcec2fd9e6dacd80b8823ce421c95bcbc9684c55d.png",
        "sha256": "d10d22f60d5378d3b3133a6dcec2fd9e6dacd80b8823ce421c95bcbc9684c55d"
      },
      {
        "path": "/data2/k6tk/3e/3ed6761da95a647ecf055ea5754e6c72d76fac2c143be243b3e4e91637958568.png",
        "sha256": "3ed6761da95a647ecf055ea5754e6c72d76fac2c143be243b3e4e91637958568"
      },
      {
        "path": "/data2/k6tk/0a/0ad0fa7e6bb9e3fc917e727947ba507be5d0e5909d9d8411265b75571f05df9c.png",
        "sha256": "0ad0fa7e6bb9e3fc917e727947ba507be5d0e5909d9d8411265b75571f05df9c"
      },
      {
        "path": "/data2/k6tk/75/750ef077d6fa4ef2c6bc227b50b4baea99ab8fdbada36dd0c0495f10455040ea.png",
        "sha256": "750ef077d6fa4ef2c6bc227b50b4baea99ab8fdbada36dd0c0495f10455040ea"
      },
      {
        "path": "/data2/k6tk/a6/a646c20b1decae00d9b3c8956e9f2aa29db56ae9b6293f084c1b5bbed90d9166.png",
        "sha256": "a646c20b1decae00d9b3c8956e9f2aa29db56ae9b6293f084c1b5bbed90d9166"
      },
      {
        "path": "/data2/k6tk/0a/0a8b7b2b0fd7a845046c2760395f4e10e04974fc6728c05c7a13bce7ab5f4936.png",
        "sha256": "0a8b7b2b0fd7a845046c2760395f4e10e04974fc6728c05c7a13bce7ab5f4936"
      },
      {
        "path": "/data2/k6tk/98/98c9cd5d411d6f1c461150cf1966e25da9f98e25357deb1741ab064cd3b97a6a.png",
        "sha256": "98c9cd5d411d6f1c461150cf1966e25da9f98e25357deb1741ab064cd3b97a6a"
      },
      {
        "path": "/data2/k6tk/88/88d1489523124f47d7c3a66c38b07771c68bba46ab0b9cfee29478206787230f.png",
        "sha256": "88d1489523124f47d7c3a66c38b07771c68bba46ab0b9cfee29478206787230f"
      },
      {
        "path": "/data2/k6tk/f3/f325a8c11bc1aca23955e5717758a6b81a4081bdade7f06c5e989f736dee99cb.png",
        "sha256": "f325a8c11bc1aca23955e5717758a6b81a4081bdade7f06c5e989f736dee99cb"
      },
      {
        "path": "/data2/k6tk/6a/6a35346ef7b7fae76dfaa4809f2b3383a3ef0339f36a09efa0f4aff9cd1b0937.png",
        "sha256": "6a35346ef7b7fae76dfaa4809f2b3383a3ef0339f36a09efa0f4aff9cd1b0937"
      },
      {
        "path": "/data2/k6tk/78/78b3dafdedff21ead79f10a1768b782ece826cb55ca15e8c26273c6420c3d98f.png",
        "sha256": "78b3dafdedff21ead79f10a1768b782ece826cb55ca15e8c26273c6420c3d98f"
      },
      {
        "path": "/data2/k6tk/f5/f525d24051807351f1f8b4bee63b66cfb7928e8477e3cbe7d3860cfa06bda263.png",
        "sha256": "f525d24051807351f1f8b4bee63b66cfb7928e8477e3cbe7d3860cfa06bda263"
      },
      {
        "path": "/data2/k6tk/58/5805685da38cc7375540027510cc5ea5b2fb045a98090c78c6f395ff2379a814.png",
        "sha256": "5805685da38cc7375540027510cc5ea5b2fb045a98090c78c6f395ff2379a814"
      },
      {
        "path": "/data2/k6tk/82/82501f4068b5d55c27bacd18736a3b1489cffa74e78572e7433d6282ad944990.png",
        "sha256": "82501f4068b5d55c27bacd18736a3b1489cffa74e78572e7433d6282ad944990"
      },
      {
        "path": "/data2/k6tk/9d/9d51584c5d12f8b65540441fc96babdd9f341e4d04c019d26daf6e1ea72cc123.png",
        "sha256": "9d51584c5d12f8b65540441fc96babdd9f341e4d04c019d26daf6e1ea72cc123"
      },
      {
        "path": "/data2/k6tk/0c/0cf282b18577cab9091af9927f3cf8814f10709b1bc1fc16bc0f185257254c4c.png",
        "sha256": "0cf282b18577cab9091af9927f3cf8814f10709b1bc1fc16bc0f185257254c4c"
      },
      {
        "path": "/data2/k6tk/c3/c3bbb4634409042519ba7f4915a8bb1ba0ed1d7debb1ce9535125283b0747f0b.png",
        "sha256": "c3bbb4634409042519ba7f4915a8bb1ba0ed1d7debb1ce9535125283b0747f0b"
      },
      {
        "path": "/data2/k6tk/9e/9ebccd5244f29b42ebb1d9b1a4c0ffe776481d60066dcc9900bea66ccb1221b9.png",
        "sha256": "9ebccd5244f29b42ebb1d9b1a4c0ffe776481d60066dcc9900bea66ccb1221b9"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      5.25,
      10.5,
      15.75,
      21.0,
      26.25,
      31.5,
      36.75,
      42.0,
      47.25,
      52.5,
      57.75,
      63.0,
      68.25,
      73.5,
      78.75,
      84.0,
      89.25,
      94.5,
      99.75,
      105.0,
      110.25,
      115.5,
      120.75,
      126.0,
      131.25,
      136.5,
      141.75,
      147.0,
      152.25,
      157.5,
      162.75
    ],
    "total_num_frames": 9766
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: curtain in frame 31; window sill in frame 27; podium in frame 27.\nOf these, the window sill and the podium are farthest apart, with the curtain between them.\n</think>\n\n64.52",
  "validation_commit": ""
}
```

## sb_rowLR_722536a121ccb54e_q0

```json
{
  "answer": "82.05",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-3b49e152dbf26d04ae952fc2868ac7e49d57dc8b158b720bca7420d51fa7b322",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vc11d5fed0c54",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        1027,
        2054,
        3081,
        4109,
        5136,
        6163,
        7190,
        8218,
        9245,
        10272,
        11299,
        12327,
        13354,
        14381,
        15408,
        16436,
        17463,
        18490,
        19517,
        20545,
        21572,
        22599,
        23626,
        24654,
        25681,
        26708,
        27735,
        28763,
        29790,
        30817,
        31845
      ],
      "options": [],
      "qid": "sb_rowLR_722536a121ccb54e_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/2c7c10379b",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/2c7c10379b",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      1027,
      2054,
      3081,
      4109,
      5136,
      6163,
      7190,
      8218,
      9245,
      10272,
      11299,
      12327,
      13354,
      14381,
      15408,
      16436,
      17463,
      18490,
      19517,
      20545,
      21572,
      22599,
      23626,
      24654,
      25681,
      26708,
      27735,
      28763,
      29790,
      30817,
      31845
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__2c7c10379b.npz": "5ec0a5ff99f7763fc44d78b258f30eeb361f050748cd3d7a7da1d957340cd2ae",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/2c7c10379b",
    "room_measurement": {
      "area_m2": 82.04500000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 32818,
      "floor_height_m": 0.07372935971293743,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 22571
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 4,
          "centroid": [
            13.781409148883135,
            5.805339596369215,
            0.5566406250000002
          ],
          "footprint": 1.2817614404816404,
          "instance_id": 25,
          "label": "sofa",
          "pixel_share": 0.144765625
        },
        {
          "best_view": 17,
          "centroid": [
            1.901750530398095,
            9.366857753911916,
            0.7867159098386765
          ],
          "footprint": 1.277761546259879,
          "instance_id": 165,
          "label": "bed",
          "pixel_share": 0.20403645833333334
        },
        {
          "best_view": 1,
          "centroid": [
            13.271318452134691,
            3.179157146176272,
            1.5606074184179306
          ],
          "footprint": 0.7627793005287749,
          "instance_id": 68,
          "label": "wardrobe",
          "pixel_share": 0.15434895833333334
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__2c7c10379b.npz",
      "raster_sha256": "5ec0a5ff99f7763fc44d78b258f30eeb361f050748cd3d7a7da1d957340cd2ae",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            13.781409148883135,
            5.805339596369215
          ],
          [
            1.901750530398095,
            9.366857753911916
          ],
          [
            13.271318452134691,
            3.179157146176272
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 2.5505331977849384,
        "projection": 0.9376292095907587,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 12.94429270133961,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12ct_79ff0db36d0bf25b68d0c7a8",
    "source_row_sha256": "38180a373b78b44bee6fa59e4ff958430c5608575b71ab90db00f8d056765fb9",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_722536a121ccb54e_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vc11d5fed0c54",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      1027,
      2054,
      3081,
      4109,
      5136,
      6163,
      7190,
      8218,
      9245,
      10272,
      11299,
      12327,
      13354,
      14381,
      15408,
      16436,
      17463,
      18490,
      19517,
      20545,
      21572,
      22599,
      23626,
      24654,
      25681,
      26708,
      27735,
      28763,
      29790,
      30817,
      31845
    ],
    "frames": [
      {
        "path": "/data2/k6tk/12/122c72ffb64dadf00322c72557213c2ed6d84fee4d9cf93ae9053068ea7de86c.png",
        "sha256": "122c72ffb64dadf00322c72557213c2ed6d84fee4d9cf93ae9053068ea7de86c"
      },
      {
        "path": "/data2/k6tk/44/44a4d5a761f1a232aa84e9bdf82ab570e6efa1346c21b5cebae63fc2db7e6180.png",
        "sha256": "44a4d5a761f1a232aa84e9bdf82ab570e6efa1346c21b5cebae63fc2db7e6180"
      },
      {
        "path": "/data2/k6tk/bf/bf3375a751a563d338b43ed450162584f0c29a3cfca1ea337b46e4ec88ef6300.png",
        "sha256": "bf3375a751a563d338b43ed450162584f0c29a3cfca1ea337b46e4ec88ef6300"
      },
      {
        "path": "/data2/k6tk/c2/c2b98b98842e44481a1887d6b499b663d6d1619544bec2e58fedbf52fb8a6d93.png",
        "sha256": "c2b98b98842e44481a1887d6b499b663d6d1619544bec2e58fedbf52fb8a6d93"
      },
      {
        "path": "/data2/k6tk/47/4707a7eaff1a0db66c9c0addb51dcf9356dfa07c6ea023698cb11cb460af1d93.png",
        "sha256": "4707a7eaff1a0db66c9c0addb51dcf9356dfa07c6ea023698cb11cb460af1d93"
      },
      {
        "path": "/data2/k6tk/54/54204a7b008ef411ad10f53b5736c661f63c82ca3ab9f874e0239779d3204210.png",
        "sha256": "54204a7b008ef411ad10f53b5736c661f63c82ca3ab9f874e0239779d3204210"
      },
      {
        "path": "/data2/k6tk/0b/0bce37d28cb8c175c3de64ec228033c8b3cb943815dc0bd95f59f022e8155745.png",
        "sha256": "0bce37d28cb8c175c3de64ec228033c8b3cb943815dc0bd95f59f022e8155745"
      },
      {
        "path": "/data2/k6tk/e7/e78b4227850dfc09900f948f7a3ba34a1903510f00879f909e8d5f6eda24efd7.png",
        "sha256": "e78b4227850dfc09900f948f7a3ba34a1903510f00879f909e8d5f6eda24efd7"
      },
      {
        "path": "/data2/k6tk/4d/4dd61ef41b5d63b0194ab7aec51543d7132cc8383ac526ea719958e6d8e6761f.png",
        "sha256": "4dd61ef41b5d63b0194ab7aec51543d7132cc8383ac526ea719958e6d8e6761f"
      },
      {
        "path": "/data2/k6tk/14/1411f40db1be4320efcf1693beecd22e5fdf7354d9d082db61bcfe741af2f3af.png",
        "sha256": "1411f40db1be4320efcf1693beecd22e5fdf7354d9d082db61bcfe741af2f3af"
      },
      {
        "path": "/data2/k6tk/f0/f0eb214575949ebd1bc7948079d0815c5e7d64eec26372b61c7f3318cb0031d3.png",
        "sha256": "f0eb214575949ebd1bc7948079d0815c5e7d64eec26372b61c7f3318cb0031d3"
      },
      {
        "path": "/data2/k6tk/0b/0b19a0ecf7e3e4d26fc08ee214a0b0f3869244e0c6782e94a4c9a4cfcf82fab0.png",
        "sha256": "0b19a0ecf7e3e4d26fc08ee214a0b0f3869244e0c6782e94a4c9a4cfcf82fab0"
      },
      {
        "path": "/data2/k6tk/c7/c7e5a96a586ce56cfbb400b8958faea918a901001c3b36fb691426d1d7d997b5.png",
        "sha256": "c7e5a96a586ce56cfbb400b8958faea918a901001c3b36fb691426d1d7d997b5"
      },
      {
        "path": "/data2/k6tk/5c/5c3eadfa900bed334b9c720029ac34ee191e488d0b96db8070836812930a9b3c.png",
        "sha256": "5c3eadfa900bed334b9c720029ac34ee191e488d0b96db8070836812930a9b3c"
      },
      {
        "path": "/data2/k6tk/52/52c524ce043b8815e633a297e076c9dc975e25f58de5f0ef71d772ef61b91a82.png",
        "sha256": "52c524ce043b8815e633a297e076c9dc975e25f58de5f0ef71d772ef61b91a82"
      },
      {
        "path": "/data2/k6tk/52/52e2be8d14dfe289e45f9e230ed886fafe74bbf6be07aceba93d0c6c1d0cea3a.png",
        "sha256": "52e2be8d14dfe289e45f9e230ed886fafe74bbf6be07aceba93d0c6c1d0cea3a"
      },
      {
        "path": "/data2/k6tk/7d/7d7781da10a4fc7f1d0e1fc4899f51cbfdcdc737c51c8adddfbb46981938901a.png",
        "sha256": "7d7781da10a4fc7f1d0e1fc4899f51cbfdcdc737c51c8adddfbb46981938901a"
      },
      {
        "path": "/data2/k6tk/b4/b49e5f5ac804c651dac2a633ffa5436279aba1e44d9af3093fa86c8fe04e6b2b.png",
        "sha256": "b49e5f5ac804c651dac2a633ffa5436279aba1e44d9af3093fa86c8fe04e6b2b"
      },
      {
        "path": "/data2/k6tk/f9/f9217d931f07d54a9ac33c1cfa25489eecea9c5bd8d765a320b9df7f1549a4d9.png",
        "sha256": "f9217d931f07d54a9ac33c1cfa25489eecea9c5bd8d765a320b9df7f1549a4d9"
      },
      {
        "path": "/data2/k6tk/e3/e38fc7a4f78af14bb5f0e5f6a2c65f1d98d40ef723615deedae6462b903f6fd8.png",
        "sha256": "e38fc7a4f78af14bb5f0e5f6a2c65f1d98d40ef723615deedae6462b903f6fd8"
      },
      {
        "path": "/data2/k6tk/3e/3e74357a9e5912ae78a245245148df9c3a0b2f3f9f8ce7651cc50d7c9de3a37d.png",
        "sha256": "3e74357a9e5912ae78a245245148df9c3a0b2f3f9f8ce7651cc50d7c9de3a37d"
      },
      {
        "path": "/data2/k6tk/b5/b54fdf7394f9047273a2a5f570c1050442f0f169f1d6e681ead3fe97048af8ac.png",
        "sha256": "b54fdf7394f9047273a2a5f570c1050442f0f169f1d6e681ead3fe97048af8ac"
      },
      {
        "path": "/data2/k6tk/01/012c5161b37054260104f6c6acc7068f85ce5eebc3c9ce6048e2f656709817bc.png",
        "sha256": "012c5161b37054260104f6c6acc7068f85ce5eebc3c9ce6048e2f656709817bc"
      },
      {
        "path": "/data2/k6tk/ba/ba672b31036ffbaf138b690d874fc1f8901052d85e1c8948f3e304f4afad3c58.png",
        "sha256": "ba672b31036ffbaf138b690d874fc1f8901052d85e1c8948f3e304f4afad3c58"
      },
      {
        "path": "/data2/k6tk/bd/bdd4e852da59889584f43dbc5d51d8ba62298000e8f99596cc5ca05ce0fc3536.png",
        "sha256": "bdd4e852da59889584f43dbc5d51d8ba62298000e8f99596cc5ca05ce0fc3536"
      },
      {
        "path": "/data2/k6tk/c8/c8856b58dbc29a75078cb329315b31eafb0b8ff4fa99e58df84638e7c92a1dea.png",
        "sha256": "c8856b58dbc29a75078cb329315b31eafb0b8ff4fa99e58df84638e7c92a1dea"
      },
      {
        "path": "/data2/k6tk/93/936c834ef3510400f4d791e6b95ba7a137ac5013403d7d393b289ebcb911e0d8.png",
        "sha256": "936c834ef3510400f4d791e6b95ba7a137ac5013403d7d393b289ebcb911e0d8"
      },
      {
        "path": "/data2/k6tk/5d/5dc2c010fd367357065d2a4e90504efb8b83a78bd0fa7f166fcfd95078e0101e.png",
        "sha256": "5dc2c010fd367357065d2a4e90504efb8b83a78bd0fa7f166fcfd95078e0101e"
      },
      {
        "path": "/data2/k6tk/2b/2b461929c9ac7ca17f471713c35b41ab04e1b1559744445e99f0e69eea5040a2.png",
        "sha256": "2b461929c9ac7ca17f471713c35b41ab04e1b1559744445e99f0e69eea5040a2"
      },
      {
        "path": "/data2/k6tk/87/878b6bb12b612abb6c180882eb0d7670bc91c1f61d178380c70be5ab3d2d5578.png",
        "sha256": "878b6bb12b612abb6c180882eb0d7670bc91c1f61d178380c70be5ab3d2d5578"
      },
      {
        "path": "/data2/k6tk/96/96cc1bccf1cc0f2bf122051ba607e8e618ab23025769c19843ece8bdea33bb58.png",
        "sha256": "96cc1bccf1cc0f2bf122051ba607e8e618ab23025769c19843ece8bdea33bb58"
      },
      {
        "path": "/data2/k6tk/87/87785c2e6666418d781df081611932e805fa73a1583bd2eb2bccf137f82cda64.png",
        "sha256": "87785c2e6666418d781df081611932e805fa73a1583bd2eb2bccf137f82cda64"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      17.116666666666667,
      34.233333333333334,
      51.35,
      68.48333333333333,
      85.6,
      102.71666666666667,
      119.83333333333333,
      136.96666666666667,
      154.08333333333334,
      171.2,
      188.31666666666666,
      205.45,
      222.56666666666666,
      239.68333333333334,
      256.8,
      273.93333333333334,
      291.05,
      308.1666666666667,
      325.28333333333336,
      342.4166666666667,
      359.53333333333336,
      376.65,
      393.76666666666665,
      410.9,
      428.01666666666665,
      445.1333333333333,
      462.25,
      479.3833333333333,
      496.5,
      513.6166666666667,
      530.75
    ],
    "total_num_frames": 31846
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: sofa in frame 4; bed in frame 17; wardrobe in frame 1.\nThe bed and the wardrobe are the farthest apart among these landmarks, with the sofa to the side of that pair.\n</think>\n\n82.05",
  "validation_commit": ""
}
```

## sb_rowLR_722536a121ccb54e_q1

```json
{
  "answer": "82.05",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-0769fff3a75059c797e96fa8c790bb4941c15d316b66d315ba7490e93b320ec9",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vc11d5fed0c54",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        1027,
        2054,
        3081,
        4109,
        5136,
        6163,
        7190,
        8218,
        9245,
        10272,
        11299,
        12327,
        13354,
        14381,
        15408,
        16436,
        17463,
        18490,
        19517,
        20545,
        21572,
        22599,
        23626,
        24654,
        25681,
        26708,
        27735,
        28763,
        29790,
        30817,
        31845
      ],
      "options": [],
      "qid": "sb_rowLR_722536a121ccb54e_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/2c7c10379b",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/2c7c10379b",
    "details": {
      "cell": "scannetpp|60-100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      1027,
      2054,
      3081,
      4109,
      5136,
      6163,
      7190,
      8218,
      9245,
      10272,
      11299,
      12327,
      13354,
      14381,
      15408,
      16436,
      17463,
      18490,
      19517,
      20545,
      21572,
      22599,
      23626,
      24654,
      25681,
      26708,
      27735,
      28763,
      29790,
      30817,
      31845
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__2c7c10379b.npz": "5ec0a5ff99f7763fc44d78b258f30eeb361f050748cd3d7a7da1d957340cd2ae",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/2c7c10379b",
    "room_measurement": {
      "area_m2": 82.04500000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 32818,
      "floor_height_m": 0.07372935971293743,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 22571
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 4,
          "centroid": [
            13.781409148883135,
            5.805339596369215,
            0.5566406250000002
          ],
          "footprint": 1.2817614404816404,
          "instance_id": 25,
          "label": "sofa",
          "pixel_share": 0.144765625
        },
        {
          "best_view": 17,
          "centroid": [
            1.901750530398095,
            9.366857753911916,
            0.7867159098386765
          ],
          "footprint": 1.277761546259879,
          "instance_id": 165,
          "label": "bed",
          "pixel_share": 0.20403645833333334
        },
        {
          "best_view": 1,
          "centroid": [
            13.271318452134691,
            3.179157146176272,
            1.5606074184179306
          ],
          "footprint": 0.7627793005287749,
          "instance_id": 68,
          "label": "wardrobe",
          "pixel_share": 0.15434895833333334
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__2c7c10379b.npz",
      "raster_sha256": "5ec0a5ff99f7763fc44d78b258f30eeb361f050748cd3d7a7da1d957340cd2ae",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            13.781409148883135,
            5.805339596369215
          ],
          [
            1.901750530398095,
            9.366857753911916
          ],
          [
            13.271318452134691,
            3.179157146176272
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 2.5505331977849384,
        "projection": 0.9376292095907587,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 12.94429270133961,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_79ff0db36d0bf25b68d0c7a8",
    "source_row_sha256": "38180a373b78b44bee6fa59e4ff958430c5608575b71ab90db00f8d056765fb9",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_722536a121ccb54e_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vc11d5fed0c54",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      1027,
      2054,
      3081,
      4109,
      5136,
      6163,
      7190,
      8218,
      9245,
      10272,
      11299,
      12327,
      13354,
      14381,
      15408,
      16436,
      17463,
      18490,
      19517,
      20545,
      21572,
      22599,
      23626,
      24654,
      25681,
      26708,
      27735,
      28763,
      29790,
      30817,
      31845
    ],
    "frames": [
      {
        "path": "/data2/k6tk/12/122c72ffb64dadf00322c72557213c2ed6d84fee4d9cf93ae9053068ea7de86c.png",
        "sha256": "122c72ffb64dadf00322c72557213c2ed6d84fee4d9cf93ae9053068ea7de86c"
      },
      {
        "path": "/data2/k6tk/44/44a4d5a761f1a232aa84e9bdf82ab570e6efa1346c21b5cebae63fc2db7e6180.png",
        "sha256": "44a4d5a761f1a232aa84e9bdf82ab570e6efa1346c21b5cebae63fc2db7e6180"
      },
      {
        "path": "/data2/k6tk/bf/bf3375a751a563d338b43ed450162584f0c29a3cfca1ea337b46e4ec88ef6300.png",
        "sha256": "bf3375a751a563d338b43ed450162584f0c29a3cfca1ea337b46e4ec88ef6300"
      },
      {
        "path": "/data2/k6tk/c2/c2b98b98842e44481a1887d6b499b663d6d1619544bec2e58fedbf52fb8a6d93.png",
        "sha256": "c2b98b98842e44481a1887d6b499b663d6d1619544bec2e58fedbf52fb8a6d93"
      },
      {
        "path": "/data2/k6tk/47/4707a7eaff1a0db66c9c0addb51dcf9356dfa07c6ea023698cb11cb460af1d93.png",
        "sha256": "4707a7eaff1a0db66c9c0addb51dcf9356dfa07c6ea023698cb11cb460af1d93"
      },
      {
        "path": "/data2/k6tk/54/54204a7b008ef411ad10f53b5736c661f63c82ca3ab9f874e0239779d3204210.png",
        "sha256": "54204a7b008ef411ad10f53b5736c661f63c82ca3ab9f874e0239779d3204210"
      },
      {
        "path": "/data2/k6tk/0b/0bce37d28cb8c175c3de64ec228033c8b3cb943815dc0bd95f59f022e8155745.png",
        "sha256": "0bce37d28cb8c175c3de64ec228033c8b3cb943815dc0bd95f59f022e8155745"
      },
      {
        "path": "/data2/k6tk/e7/e78b4227850dfc09900f948f7a3ba34a1903510f00879f909e8d5f6eda24efd7.png",
        "sha256": "e78b4227850dfc09900f948f7a3ba34a1903510f00879f909e8d5f6eda24efd7"
      },
      {
        "path": "/data2/k6tk/4d/4dd61ef41b5d63b0194ab7aec51543d7132cc8383ac526ea719958e6d8e6761f.png",
        "sha256": "4dd61ef41b5d63b0194ab7aec51543d7132cc8383ac526ea719958e6d8e6761f"
      },
      {
        "path": "/data2/k6tk/14/1411f40db1be4320efcf1693beecd22e5fdf7354d9d082db61bcfe741af2f3af.png",
        "sha256": "1411f40db1be4320efcf1693beecd22e5fdf7354d9d082db61bcfe741af2f3af"
      },
      {
        "path": "/data2/k6tk/f0/f0eb214575949ebd1bc7948079d0815c5e7d64eec26372b61c7f3318cb0031d3.png",
        "sha256": "f0eb214575949ebd1bc7948079d0815c5e7d64eec26372b61c7f3318cb0031d3"
      },
      {
        "path": "/data2/k6tk/0b/0b19a0ecf7e3e4d26fc08ee214a0b0f3869244e0c6782e94a4c9a4cfcf82fab0.png",
        "sha256": "0b19a0ecf7e3e4d26fc08ee214a0b0f3869244e0c6782e94a4c9a4cfcf82fab0"
      },
      {
        "path": "/data2/k6tk/c7/c7e5a96a586ce56cfbb400b8958faea918a901001c3b36fb691426d1d7d997b5.png",
        "sha256": "c7e5a96a586ce56cfbb400b8958faea918a901001c3b36fb691426d1d7d997b5"
      },
      {
        "path": "/data2/k6tk/5c/5c3eadfa900bed334b9c720029ac34ee191e488d0b96db8070836812930a9b3c.png",
        "sha256": "5c3eadfa900bed334b9c720029ac34ee191e488d0b96db8070836812930a9b3c"
      },
      {
        "path": "/data2/k6tk/52/52c524ce043b8815e633a297e076c9dc975e25f58de5f0ef71d772ef61b91a82.png",
        "sha256": "52c524ce043b8815e633a297e076c9dc975e25f58de5f0ef71d772ef61b91a82"
      },
      {
        "path": "/data2/k6tk/52/52e2be8d14dfe289e45f9e230ed886fafe74bbf6be07aceba93d0c6c1d0cea3a.png",
        "sha256": "52e2be8d14dfe289e45f9e230ed886fafe74bbf6be07aceba93d0c6c1d0cea3a"
      },
      {
        "path": "/data2/k6tk/7d/7d7781da10a4fc7f1d0e1fc4899f51cbfdcdc737c51c8adddfbb46981938901a.png",
        "sha256": "7d7781da10a4fc7f1d0e1fc4899f51cbfdcdc737c51c8adddfbb46981938901a"
      },
      {
        "path": "/data2/k6tk/b4/b49e5f5ac804c651dac2a633ffa5436279aba1e44d9af3093fa86c8fe04e6b2b.png",
        "sha256": "b49e5f5ac804c651dac2a633ffa5436279aba1e44d9af3093fa86c8fe04e6b2b"
      },
      {
        "path": "/data2/k6tk/f9/f9217d931f07d54a9ac33c1cfa25489eecea9c5bd8d765a320b9df7f1549a4d9.png",
        "sha256": "f9217d931f07d54a9ac33c1cfa25489eecea9c5bd8d765a320b9df7f1549a4d9"
      },
      {
        "path": "/data2/k6tk/e3/e38fc7a4f78af14bb5f0e5f6a2c65f1d98d40ef723615deedae6462b903f6fd8.png",
        "sha256": "e38fc7a4f78af14bb5f0e5f6a2c65f1d98d40ef723615deedae6462b903f6fd8"
      },
      {
        "path": "/data2/k6tk/3e/3e74357a9e5912ae78a245245148df9c3a0b2f3f9f8ce7651cc50d7c9de3a37d.png",
        "sha256": "3e74357a9e5912ae78a245245148df9c3a0b2f3f9f8ce7651cc50d7c9de3a37d"
      },
      {
        "path": "/data2/k6tk/b5/b54fdf7394f9047273a2a5f570c1050442f0f169f1d6e681ead3fe97048af8ac.png",
        "sha256": "b54fdf7394f9047273a2a5f570c1050442f0f169f1d6e681ead3fe97048af8ac"
      },
      {
        "path": "/data2/k6tk/01/012c5161b37054260104f6c6acc7068f85ce5eebc3c9ce6048e2f656709817bc.png",
        "sha256": "012c5161b37054260104f6c6acc7068f85ce5eebc3c9ce6048e2f656709817bc"
      },
      {
        "path": "/data2/k6tk/ba/ba672b31036ffbaf138b690d874fc1f8901052d85e1c8948f3e304f4afad3c58.png",
        "sha256": "ba672b31036ffbaf138b690d874fc1f8901052d85e1c8948f3e304f4afad3c58"
      },
      {
        "path": "/data2/k6tk/bd/bdd4e852da59889584f43dbc5d51d8ba62298000e8f99596cc5ca05ce0fc3536.png",
        "sha256": "bdd4e852da59889584f43dbc5d51d8ba62298000e8f99596cc5ca05ce0fc3536"
      },
      {
        "path": "/data2/k6tk/c8/c8856b58dbc29a75078cb329315b31eafb0b8ff4fa99e58df84638e7c92a1dea.png",
        "sha256": "c8856b58dbc29a75078cb329315b31eafb0b8ff4fa99e58df84638e7c92a1dea"
      },
      {
        "path": "/data2/k6tk/93/936c834ef3510400f4d791e6b95ba7a137ac5013403d7d393b289ebcb911e0d8.png",
        "sha256": "936c834ef3510400f4d791e6b95ba7a137ac5013403d7d393b289ebcb911e0d8"
      },
      {
        "path": "/data2/k6tk/5d/5dc2c010fd367357065d2a4e90504efb8b83a78bd0fa7f166fcfd95078e0101e.png",
        "sha256": "5dc2c010fd367357065d2a4e90504efb8b83a78bd0fa7f166fcfd95078e0101e"
      },
      {
        "path": "/data2/k6tk/2b/2b461929c9ac7ca17f471713c35b41ab04e1b1559744445e99f0e69eea5040a2.png",
        "sha256": "2b461929c9ac7ca17f471713c35b41ab04e1b1559744445e99f0e69eea5040a2"
      },
      {
        "path": "/data2/k6tk/87/878b6bb12b612abb6c180882eb0d7670bc91c1f61d178380c70be5ab3d2d5578.png",
        "sha256": "878b6bb12b612abb6c180882eb0d7670bc91c1f61d178380c70be5ab3d2d5578"
      },
      {
        "path": "/data2/k6tk/96/96cc1bccf1cc0f2bf122051ba607e8e618ab23025769c19843ece8bdea33bb58.png",
        "sha256": "96cc1bccf1cc0f2bf122051ba607e8e618ab23025769c19843ece8bdea33bb58"
      },
      {
        "path": "/data2/k6tk/87/87785c2e6666418d781df081611932e805fa73a1583bd2eb2bccf137f82cda64.png",
        "sha256": "87785c2e6666418d781df081611932e805fa73a1583bd2eb2bccf137f82cda64"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      17.116666666666667,
      34.233333333333334,
      51.35,
      68.48333333333333,
      85.6,
      102.71666666666667,
      119.83333333333333,
      136.96666666666667,
      154.08333333333334,
      171.2,
      188.31666666666666,
      205.45,
      222.56666666666666,
      239.68333333333334,
      256.8,
      273.93333333333334,
      291.05,
      308.1666666666667,
      325.28333333333336,
      342.4166666666667,
      359.53333333333336,
      376.65,
      393.76666666666665,
      410.9,
      428.01666666666665,
      445.1333333333333,
      462.25,
      479.3833333333333,
      496.5,
      513.6166666666667,
      530.75
    ],
    "total_num_frames": 31846
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: sofa in frame 4; bed in frame 17; wardrobe in frame 1.\nOf these, the bed and the wardrobe are farthest apart, with the sofa off to the side.\n</think>\n\n82.05",
  "validation_commit": ""
}
```

## sb_rowLR_06c1c23f63372961_q0

```json
{
  "answer": "109.76",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-9d89828641636357c63f2398b56c074058c10873f9d44892693691d8b2705baf",
  "category": "room_size_estimation",
  "count_arity": 2,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vf332f813aeeb",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        446,
        892,
        1338,
        1784,
        2230,
        2676,
        3123,
        3569,
        4015,
        4461,
        4907,
        5353,
        5800,
        6246,
        6692,
        7138,
        7584,
        8030,
        8477,
        8923,
        9369,
        9815,
        10261,
        10707,
        11154,
        11600,
        12046,
        12492,
        12938,
        13384,
        13831
      ],
      "options": [],
      "qid": "sb_rowLR_06c1c23f63372961_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/aee88e3a93",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/aee88e3a93",
    "details": {
      "cell": "scannetpp|>=100",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      446,
      892,
      1338,
      1784,
      2230,
      2676,
      3123,
      3569,
      4015,
      4461,
      4907,
      5353,
      5800,
      6246,
      6692,
      7138,
      7584,
      8030,
      8477,
      8923,
      9369,
      9815,
      10261,
      10707,
      11154,
      11600,
      12046,
      12492,
      12938,
      13384,
      13831
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__aee88e3a93.npz": "805fa65270a2b07fb6e9346d6d35b6e11bf64eb683310621fea091f782dd865e",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/aee88e3a93",
    "room_measurement": {
      "area_m2": 109.75750000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 43903,
      "floor_height_m": 0.2550722741438396,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 30775
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 25,
          "centroid": [
            6.820632675928148,
            6.857151917143099,
            1.9475286006927488
          ],
          "footprint": 0.38500602215175556,
          "instance_id": 126,
          "label": "pillar",
          "pixel_share": 0.129375
        },
        {
          "best_view": 32,
          "centroid": [
            11.128089054949758,
            0.8565375770779795,
            0.867594838142395
          ],
          "footprint": 0.15631304306027305,
          "instance_id": 43,
          "label": "cabinet",
          "pixel_share": 0.05192708333333333
        },
        {
          "best_view": 13,
          "centroid": [
            0.5682310244305331,
            0.4294665932366275,
            2.0097062587738037
          ],
          "footprint": 0.04704185981147283,
          "instance_id": 123,
          "label": "tissue dispenser",
          "pixel_share": 0.014518229166666667
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__aee88e3a93.npz",
      "raster_sha256": "805fa65270a2b07fb6e9346d6d35b6e11bf64eb683310621fea091f782dd865e",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            6.820632675928148,
            6.857151917143099
          ],
          [
            11.128089054949758,
            0.8565375770779795
          ],
          [
            0.5682310244305331,
            0.4294665932366275
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 6.169776584329326,
        "projection": 0.3842984155487341,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 10.568490490602741,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_d3023c148bb5e6d630c15ea5",
    "source_row_sha256": "0af8824f125bbec9d910a9a0714f6c61f6c99f1f158102330f3e6cc1a0ba8328",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_06c1c23f63372961_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vf332f813aeeb",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      446,
      892,
      1338,
      1784,
      2230,
      2676,
      3123,
      3569,
      4015,
      4461,
      4907,
      5353,
      5800,
      6246,
      6692,
      7138,
      7584,
      8030,
      8477,
      8923,
      9369,
      9815,
      10261,
      10707,
      11154,
      11600,
      12046,
      12492,
      12938,
      13384,
      13831
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a2/a27454dbe46a83e4f938e8871f3d1968525caa8e74be76e643a49b7d047cea34.png",
        "sha256": "a27454dbe46a83e4f938e8871f3d1968525caa8e74be76e643a49b7d047cea34"
      },
      {
        "path": "/data2/k6tk/22/22a8337b70a2135fd43898b050c349185f5d18cd04be9ea795e2343b58840867.png",
        "sha256": "22a8337b70a2135fd43898b050c349185f5d18cd04be9ea795e2343b58840867"
      },
      {
        "path": "/data2/k6tk/0a/0a81b023cb2c6952681d53b269be92dab4f50a90718b91e01a82b2c813abaab9.png",
        "sha256": "0a81b023cb2c6952681d53b269be92dab4f50a90718b91e01a82b2c813abaab9"
      },
      {
        "path": "/data2/k6tk/f5/f5199f41bc1443abeddd50b5461df9248bbe7a20bfee3f41cd41e994b8e4a8ca.png",
        "sha256": "f5199f41bc1443abeddd50b5461df9248bbe7a20bfee3f41cd41e994b8e4a8ca"
      },
      {
        "path": "/data2/k6tk/ec/ec0922d47e5750e270707d833610f39c5305d833f0312de308b4995834494d94.png",
        "sha256": "ec0922d47e5750e270707d833610f39c5305d833f0312de308b4995834494d94"
      },
      {
        "path": "/data2/k6tk/63/63470cb3611c485e19ef05adf17d46101d857b2dc2efb16c860eb4dd17528438.png",
        "sha256": "63470cb3611c485e19ef05adf17d46101d857b2dc2efb16c860eb4dd17528438"
      },
      {
        "path": "/data2/k6tk/52/52b0214f970924ac113667f64bac4e87081952030c72adfd0cff928469849336.png",
        "sha256": "52b0214f970924ac113667f64bac4e87081952030c72adfd0cff928469849336"
      },
      {
        "path": "/data2/k6tk/b5/b5009965c5efe94766ae6e14ae756363b9554491a49959606490d2e20c8497fc.png",
        "sha256": "b5009965c5efe94766ae6e14ae756363b9554491a49959606490d2e20c8497fc"
      },
      {
        "path": "/data2/k6tk/e2/e2dddaa6c1e073feb01c61cbcca71f0e85cf3a028f138ffa35ccaec88334064b.png",
        "sha256": "e2dddaa6c1e073feb01c61cbcca71f0e85cf3a028f138ffa35ccaec88334064b"
      },
      {
        "path": "/data2/k6tk/94/943ee6e49e954e989619b29dafcafbf9804801f6392a6104ef4947ac3b15fa0f.png",
        "sha256": "943ee6e49e954e989619b29dafcafbf9804801f6392a6104ef4947ac3b15fa0f"
      },
      {
        "path": "/data2/k6tk/4e/4e3127799c3dbeb4bed7cfe1458be2eefe1e4d63a5eeaed0db29232c5dbf6e70.png",
        "sha256": "4e3127799c3dbeb4bed7cfe1458be2eefe1e4d63a5eeaed0db29232c5dbf6e70"
      },
      {
        "path": "/data2/k6tk/4d/4d41847d3ec51374274db23b0d8383995146add3dfebb005c59419e55dd66f31.png",
        "sha256": "4d41847d3ec51374274db23b0d8383995146add3dfebb005c59419e55dd66f31"
      },
      {
        "path": "/data2/k6tk/cf/cf5c421fe7eb10413f6c7f60d29eb89eabf47e838ff83beb978df3d784e96347.png",
        "sha256": "cf5c421fe7eb10413f6c7f60d29eb89eabf47e838ff83beb978df3d784e96347"
      },
      {
        "path": "/data2/k6tk/44/44a0eba46444c7260b8b51334855f123d94f8042ad903e83bbdaf9a639dd9e9c.png",
        "sha256": "44a0eba46444c7260b8b51334855f123d94f8042ad903e83bbdaf9a639dd9e9c"
      },
      {
        "path": "/data2/k6tk/f2/f28957136e6bd34429a893165f4e02f22523feaf71b9f5e6e975d077965b0b8a.png",
        "sha256": "f28957136e6bd34429a893165f4e02f22523feaf71b9f5e6e975d077965b0b8a"
      },
      {
        "path": "/data2/k6tk/8f/8f5ca71c407f187f0bf9acdc0a3aa7f13170054fb85964145e2280593b711ee6.png",
        "sha256": "8f5ca71c407f187f0bf9acdc0a3aa7f13170054fb85964145e2280593b711ee6"
      },
      {
        "path": "/data2/k6tk/59/597723fa9c144cedc8d9a05f792f37715688be3e581a18b931656d7226f12496.png",
        "sha256": "597723fa9c144cedc8d9a05f792f37715688be3e581a18b931656d7226f12496"
      },
      {
        "path": "/data2/k6tk/fa/fac82291c81f45f76844a653850231775a86d76abcb8fb12c3beb6411d8f0c74.png",
        "sha256": "fac82291c81f45f76844a653850231775a86d76abcb8fb12c3beb6411d8f0c74"
      },
      {
        "path": "/data2/k6tk/4b/4b0fe730c45fe4c712904cfb3d54d5718a5fd8729d7d7254dec8e0a724bd69c0.png",
        "sha256": "4b0fe730c45fe4c712904cfb3d54d5718a5fd8729d7d7254dec8e0a724bd69c0"
      },
      {
        "path": "/data2/k6tk/ae/aed790db491581dfbb8f2f02d01d5fe005fb195c7ac39a986c7339c8b61189c4.png",
        "sha256": "aed790db491581dfbb8f2f02d01d5fe005fb195c7ac39a986c7339c8b61189c4"
      },
      {
        "path": "/data2/k6tk/82/826e4d0983563d6800e3596cbfa2136e0cd2a812421dcbf751230160514928ec.png",
        "sha256": "826e4d0983563d6800e3596cbfa2136e0cd2a812421dcbf751230160514928ec"
      },
      {
        "path": "/data2/k6tk/22/2207903236ed3162643a767c0e7b20a648d3217973bdb8e294f1342f275175c1.png",
        "sha256": "2207903236ed3162643a767c0e7b20a648d3217973bdb8e294f1342f275175c1"
      },
      {
        "path": "/data2/k6tk/f3/f32f44a5aa920c2e7bae2c5e3454bec0ddd4fc685930cbe9b5c333620cd2a3e7.png",
        "sha256": "f32f44a5aa920c2e7bae2c5e3454bec0ddd4fc685930cbe9b5c333620cd2a3e7"
      },
      {
        "path": "/data2/k6tk/e0/e0ed1ada6950a083b78dbf49a6ede4685814a5428fbccadcb43b5825d68a172f.png",
        "sha256": "e0ed1ada6950a083b78dbf49a6ede4685814a5428fbccadcb43b5825d68a172f"
      },
      {
        "path": "/data2/k6tk/0a/0ad546012fed848d010606e4da1b981b4c3292a972ac33286c494fdf82701b43.png",
        "sha256": "0ad546012fed848d010606e4da1b981b4c3292a972ac33286c494fdf82701b43"
      },
      {
        "path": "/data2/k6tk/a3/a3b8a2c93d9f173b0674aa0dbc0a9d45697b8fdc32180f59845bf42a6c9c5b7c.png",
        "sha256": "a3b8a2c93d9f173b0674aa0dbc0a9d45697b8fdc32180f59845bf42a6c9c5b7c"
      },
      {
        "path": "/data2/k6tk/15/15bef8dd9c6eb7d793b9198f355e18233dc545719da4f172402379a1bbbcb454.png",
        "sha256": "15bef8dd9c6eb7d793b9198f355e18233dc545719da4f172402379a1bbbcb454"
      },
      {
        "path": "/data2/k6tk/6a/6aabdf0d17a8e5451779c8bed4a2fae1f7bc83f31b0e36b6472f789166e1e70e.png",
        "sha256": "6aabdf0d17a8e5451779c8bed4a2fae1f7bc83f31b0e36b6472f789166e1e70e"
      },
      {
        "path": "/data2/k6tk/bc/bc363af88fd1d055e92775c7582f587ae76f14e2a1d55882e6cee92bd66d99f5.png",
        "sha256": "bc363af88fd1d055e92775c7582f587ae76f14e2a1d55882e6cee92bd66d99f5"
      },
      {
        "path": "/data2/k6tk/10/104b35418830b5a85205fce57e3c57a7c3d1a2bfc552e149552a1f256d21affc.png",
        "sha256": "104b35418830b5a85205fce57e3c57a7c3d1a2bfc552e149552a1f256d21affc"
      },
      {
        "path": "/data2/k6tk/a4/a44733132387477f88f5df0c3c5cc11069617704dd90ce2f722a8590b1810df7.png",
        "sha256": "a44733132387477f88f5df0c3c5cc11069617704dd90ce2f722a8590b1810df7"
      },
      {
        "path": "/data2/k6tk/9c/9c816e502632ee9927ec35452d00d35e8b6881b59770218c79931a5cb449a016.png",
        "sha256": "9c816e502632ee9927ec35452d00d35e8b6881b59770218c79931a5cb449a016"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      7.433333333333334,
      14.866666666666667,
      22.3,
      29.733333333333334,
      37.166666666666664,
      44.6,
      52.05,
      59.483333333333334,
      66.91666666666667,
      74.35,
      81.78333333333333,
      89.21666666666667,
      96.66666666666667,
      104.1,
      111.53333333333333,
      118.96666666666667,
      126.4,
      133.83333333333334,
      141.28333333333333,
      148.71666666666667,
      156.15,
      163.58333333333334,
      171.01666666666668,
      178.45,
      185.9,
      193.33333333333334,
      200.76666666666668,
      208.2,
      215.63333333333333,
      223.06666666666666,
      230.51666666666668
    ],
    "total_num_frames": 13832
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: pillar in frame 25; cabinet in frame 32; tissue dispenser in frame 13.\nOf these, the cabinet and the tissue dispenser are farthest apart, with the pillar off to the side.\n</think>\n\n109.76",
  "validation_commit": ""
}
```

## sb_rowLR_06c1c23f63372961_q1

```json
{
  "answer": "109.76",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-824204eef7766f7a6b9deecfdf57ace72f6375e3c0380d2a0e991fbb05f56f17",
  "category": "room_size_estimation",
  "count_arity": 2,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vf332f813aeeb",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        446,
        892,
        1338,
        1784,
        2230,
        2676,
        3123,
        3569,
        4015,
        4461,
        4907,
        5353,
        5800,
        6246,
        6692,
        7138,
        7584,
        8030,
        8477,
        8923,
        9369,
        9815,
        10261,
        10707,
        11154,
        11600,
        12046,
        12492,
        12938,
        13384,
        13831
      ],
      "options": [],
      "qid": "sb_rowLR_06c1c23f63372961_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/aee88e3a93",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/aee88e3a93",
    "details": {
      "cell": "scannetpp|>=100",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      446,
      892,
      1338,
      1784,
      2230,
      2676,
      3123,
      3569,
      4015,
      4461,
      4907,
      5353,
      5800,
      6246,
      6692,
      7138,
      7584,
      8030,
      8477,
      8923,
      9369,
      9815,
      10261,
      10707,
      11154,
      11600,
      12046,
      12492,
      12938,
      13384,
      13831
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__aee88e3a93.npz": "805fa65270a2b07fb6e9346d6d35b6e11bf64eb683310621fea091f782dd865e",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/aee88e3a93",
    "room_measurement": {
      "area_m2": 109.75750000000001,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 43903,
      "floor_height_m": 0.2550722741438396,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 30775
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 25,
          "centroid": [
            6.820632675928148,
            6.857151917143099,
            1.9475286006927488
          ],
          "footprint": 0.38500602215175556,
          "instance_id": 126,
          "label": "pillar",
          "pixel_share": 0.129375
        },
        {
          "best_view": 32,
          "centroid": [
            11.128089054949758,
            0.8565375770779795,
            0.867594838142395
          ],
          "footprint": 0.15631304306027305,
          "instance_id": 43,
          "label": "cabinet",
          "pixel_share": 0.05192708333333333
        },
        {
          "best_view": 13,
          "centroid": [
            0.5682310244305331,
            0.4294665932366275,
            2.0097062587738037
          ],
          "footprint": 0.04704185981147283,
          "instance_id": 123,
          "label": "tissue dispenser",
          "pixel_share": 0.014518229166666667
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__aee88e3a93.npz",
      "raster_sha256": "805fa65270a2b07fb6e9346d6d35b6e11bf64eb683310621fea091f782dd865e",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            6.820632675928148,
            6.857151917143099
          ],
          [
            11.128089054949758,
            0.8565375770779795
          ],
          [
            0.5682310244305331,
            0.4294665932366275
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 6.169776584329326,
        "projection": 0.3842984155487341,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 10.568490490602741,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 1
      }
    },
    "source_qid": "b12ct_d3023c148bb5e6d630c15ea5",
    "source_row_sha256": "0af8824f125bbec9d910a9a0714f6c61f6c99f1f158102330f3e6cc1a0ba8328",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_06c1c23f63372961_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vf332f813aeeb",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      446,
      892,
      1338,
      1784,
      2230,
      2676,
      3123,
      3569,
      4015,
      4461,
      4907,
      5353,
      5800,
      6246,
      6692,
      7138,
      7584,
      8030,
      8477,
      8923,
      9369,
      9815,
      10261,
      10707,
      11154,
      11600,
      12046,
      12492,
      12938,
      13384,
      13831
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a2/a27454dbe46a83e4f938e8871f3d1968525caa8e74be76e643a49b7d047cea34.png",
        "sha256": "a27454dbe46a83e4f938e8871f3d1968525caa8e74be76e643a49b7d047cea34"
      },
      {
        "path": "/data2/k6tk/22/22a8337b70a2135fd43898b050c349185f5d18cd04be9ea795e2343b58840867.png",
        "sha256": "22a8337b70a2135fd43898b050c349185f5d18cd04be9ea795e2343b58840867"
      },
      {
        "path": "/data2/k6tk/0a/0a81b023cb2c6952681d53b269be92dab4f50a90718b91e01a82b2c813abaab9.png",
        "sha256": "0a81b023cb2c6952681d53b269be92dab4f50a90718b91e01a82b2c813abaab9"
      },
      {
        "path": "/data2/k6tk/f5/f5199f41bc1443abeddd50b5461df9248bbe7a20bfee3f41cd41e994b8e4a8ca.png",
        "sha256": "f5199f41bc1443abeddd50b5461df9248bbe7a20bfee3f41cd41e994b8e4a8ca"
      },
      {
        "path": "/data2/k6tk/ec/ec0922d47e5750e270707d833610f39c5305d833f0312de308b4995834494d94.png",
        "sha256": "ec0922d47e5750e270707d833610f39c5305d833f0312de308b4995834494d94"
      },
      {
        "path": "/data2/k6tk/63/63470cb3611c485e19ef05adf17d46101d857b2dc2efb16c860eb4dd17528438.png",
        "sha256": "63470cb3611c485e19ef05adf17d46101d857b2dc2efb16c860eb4dd17528438"
      },
      {
        "path": "/data2/k6tk/52/52b0214f970924ac113667f64bac4e87081952030c72adfd0cff928469849336.png",
        "sha256": "52b0214f970924ac113667f64bac4e87081952030c72adfd0cff928469849336"
      },
      {
        "path": "/data2/k6tk/b5/b5009965c5efe94766ae6e14ae756363b9554491a49959606490d2e20c8497fc.png",
        "sha256": "b5009965c5efe94766ae6e14ae756363b9554491a49959606490d2e20c8497fc"
      },
      {
        "path": "/data2/k6tk/e2/e2dddaa6c1e073feb01c61cbcca71f0e85cf3a028f138ffa35ccaec88334064b.png",
        "sha256": "e2dddaa6c1e073feb01c61cbcca71f0e85cf3a028f138ffa35ccaec88334064b"
      },
      {
        "path": "/data2/k6tk/94/943ee6e49e954e989619b29dafcafbf9804801f6392a6104ef4947ac3b15fa0f.png",
        "sha256": "943ee6e49e954e989619b29dafcafbf9804801f6392a6104ef4947ac3b15fa0f"
      },
      {
        "path": "/data2/k6tk/4e/4e3127799c3dbeb4bed7cfe1458be2eefe1e4d63a5eeaed0db29232c5dbf6e70.png",
        "sha256": "4e3127799c3dbeb4bed7cfe1458be2eefe1e4d63a5eeaed0db29232c5dbf6e70"
      },
      {
        "path": "/data2/k6tk/4d/4d41847d3ec51374274db23b0d8383995146add3dfebb005c59419e55dd66f31.png",
        "sha256": "4d41847d3ec51374274db23b0d8383995146add3dfebb005c59419e55dd66f31"
      },
      {
        "path": "/data2/k6tk/cf/cf5c421fe7eb10413f6c7f60d29eb89eabf47e838ff83beb978df3d784e96347.png",
        "sha256": "cf5c421fe7eb10413f6c7f60d29eb89eabf47e838ff83beb978df3d784e96347"
      },
      {
        "path": "/data2/k6tk/44/44a0eba46444c7260b8b51334855f123d94f8042ad903e83bbdaf9a639dd9e9c.png",
        "sha256": "44a0eba46444c7260b8b51334855f123d94f8042ad903e83bbdaf9a639dd9e9c"
      },
      {
        "path": "/data2/k6tk/f2/f28957136e6bd34429a893165f4e02f22523feaf71b9f5e6e975d077965b0b8a.png",
        "sha256": "f28957136e6bd34429a893165f4e02f22523feaf71b9f5e6e975d077965b0b8a"
      },
      {
        "path": "/data2/k6tk/8f/8f5ca71c407f187f0bf9acdc0a3aa7f13170054fb85964145e2280593b711ee6.png",
        "sha256": "8f5ca71c407f187f0bf9acdc0a3aa7f13170054fb85964145e2280593b711ee6"
      },
      {
        "path": "/data2/k6tk/59/597723fa9c144cedc8d9a05f792f37715688be3e581a18b931656d7226f12496.png",
        "sha256": "597723fa9c144cedc8d9a05f792f37715688be3e581a18b931656d7226f12496"
      },
      {
        "path": "/data2/k6tk/fa/fac82291c81f45f76844a653850231775a86d76abcb8fb12c3beb6411d8f0c74.png",
        "sha256": "fac82291c81f45f76844a653850231775a86d76abcb8fb12c3beb6411d8f0c74"
      },
      {
        "path": "/data2/k6tk/4b/4b0fe730c45fe4c712904cfb3d54d5718a5fd8729d7d7254dec8e0a724bd69c0.png",
        "sha256": "4b0fe730c45fe4c712904cfb3d54d5718a5fd8729d7d7254dec8e0a724bd69c0"
      },
      {
        "path": "/data2/k6tk/ae/aed790db491581dfbb8f2f02d01d5fe005fb195c7ac39a986c7339c8b61189c4.png",
        "sha256": "aed790db491581dfbb8f2f02d01d5fe005fb195c7ac39a986c7339c8b61189c4"
      },
      {
        "path": "/data2/k6tk/82/826e4d0983563d6800e3596cbfa2136e0cd2a812421dcbf751230160514928ec.png",
        "sha256": "826e4d0983563d6800e3596cbfa2136e0cd2a812421dcbf751230160514928ec"
      },
      {
        "path": "/data2/k6tk/22/2207903236ed3162643a767c0e7b20a648d3217973bdb8e294f1342f275175c1.png",
        "sha256": "2207903236ed3162643a767c0e7b20a648d3217973bdb8e294f1342f275175c1"
      },
      {
        "path": "/data2/k6tk/f3/f32f44a5aa920c2e7bae2c5e3454bec0ddd4fc685930cbe9b5c333620cd2a3e7.png",
        "sha256": "f32f44a5aa920c2e7bae2c5e3454bec0ddd4fc685930cbe9b5c333620cd2a3e7"
      },
      {
        "path": "/data2/k6tk/e0/e0ed1ada6950a083b78dbf49a6ede4685814a5428fbccadcb43b5825d68a172f.png",
        "sha256": "e0ed1ada6950a083b78dbf49a6ede4685814a5428fbccadcb43b5825d68a172f"
      },
      {
        "path": "/data2/k6tk/0a/0ad546012fed848d010606e4da1b981b4c3292a972ac33286c494fdf82701b43.png",
        "sha256": "0ad546012fed848d010606e4da1b981b4c3292a972ac33286c494fdf82701b43"
      },
      {
        "path": "/data2/k6tk/a3/a3b8a2c93d9f173b0674aa0dbc0a9d45697b8fdc32180f59845bf42a6c9c5b7c.png",
        "sha256": "a3b8a2c93d9f173b0674aa0dbc0a9d45697b8fdc32180f59845bf42a6c9c5b7c"
      },
      {
        "path": "/data2/k6tk/15/15bef8dd9c6eb7d793b9198f355e18233dc545719da4f172402379a1bbbcb454.png",
        "sha256": "15bef8dd9c6eb7d793b9198f355e18233dc545719da4f172402379a1bbbcb454"
      },
      {
        "path": "/data2/k6tk/6a/6aabdf0d17a8e5451779c8bed4a2fae1f7bc83f31b0e36b6472f789166e1e70e.png",
        "sha256": "6aabdf0d17a8e5451779c8bed4a2fae1f7bc83f31b0e36b6472f789166e1e70e"
      },
      {
        "path": "/data2/k6tk/bc/bc363af88fd1d055e92775c7582f587ae76f14e2a1d55882e6cee92bd66d99f5.png",
        "sha256": "bc363af88fd1d055e92775c7582f587ae76f14e2a1d55882e6cee92bd66d99f5"
      },
      {
        "path": "/data2/k6tk/10/104b35418830b5a85205fce57e3c57a7c3d1a2bfc552e149552a1f256d21affc.png",
        "sha256": "104b35418830b5a85205fce57e3c57a7c3d1a2bfc552e149552a1f256d21affc"
      },
      {
        "path": "/data2/k6tk/a4/a44733132387477f88f5df0c3c5cc11069617704dd90ce2f722a8590b1810df7.png",
        "sha256": "a44733132387477f88f5df0c3c5cc11069617704dd90ce2f722a8590b1810df7"
      },
      {
        "path": "/data2/k6tk/9c/9c816e502632ee9927ec35452d00d35e8b6881b59770218c79931a5cb449a016.png",
        "sha256": "9c816e502632ee9927ec35452d00d35e8b6881b59770218c79931a5cb449a016"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      7.433333333333334,
      14.866666666666667,
      22.3,
      29.733333333333334,
      37.166666666666664,
      44.6,
      52.05,
      59.483333333333334,
      66.91666666666667,
      74.35,
      81.78333333333333,
      89.21666666666667,
      96.66666666666667,
      104.1,
      111.53333333333333,
      118.96666666666667,
      126.4,
      133.83333333333334,
      141.28333333333333,
      148.71666666666667,
      156.15,
      163.58333333333334,
      171.01666666666668,
      178.45,
      185.9,
      193.33333333333334,
      200.76666666666668,
      208.2,
      215.63333333333333,
      223.06666666666666,
      230.51666666666668
    ],
    "total_num_frames": 13832
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: pillar in frame 25; cabinet in frame 32; tissue dispenser in frame 13.\nThe cabinet and the tissue dispenser are the farthest apart among these landmarks, with the pillar to the side of that pair.\n</think>\n\n109.76",
  "validation_commit": ""
}
```

## sb_rowLR_32d80955bee4dc01_q0

```json
{
  "answer": "18.49",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-6d575a6c17f02a6152f14b4ae2c42b5420a6972cf89dc201026d419b85cc897f",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/vc43ee4230766",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        226,
        452,
        679,
        905,
        1131,
        1358,
        1584,
        1810,
        2037,
        2263,
        2489,
        2716,
        2942,
        3168,
        3395,
        3621,
        3848,
        4074,
        4300,
        4527,
        4753,
        4979,
        5206,
        5432,
        5658,
        5885,
        6111,
        6337,
        6564,
        6790,
        7017
      ],
      "options": [],
      "qid": "sb_rowLR_32d80955bee4dc01_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/3928249b53",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/3928249b53",
    "details": {
      "cell": "scannetpp|10-20",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      226,
      452,
      679,
      905,
      1131,
      1358,
      1584,
      1810,
      2037,
      2263,
      2489,
      2716,
      2942,
      3168,
      3395,
      3621,
      3848,
      4074,
      4300,
      4527,
      4753,
      4979,
      5206,
      5432,
      5658,
      5885,
      6111,
      6337,
      6564,
      6790,
      7017
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3928249b53.npz": "88717be3eba84a7978559bd792849727225a433649ae45d3968427b671d223ef",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/3928249b53",
    "room_measurement": {
      "area_m2": 18.4875,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 7395,
      "floor_height_m": -0.03383012297149718,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 6560
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 7,
          "centroid": [
            4.825244465680729,
            1.9648223500125486,
            0.5549161285161972
          ],
          "footprint": 0.7164605277513361,
          "instance_id": 5,
          "label": "window sill",
          "pixel_share": 0.21315104166666668
        },
        {
          "best_view": 3,
          "centroid": [
            0.057730389031596996,
            2.813095103366388,
            1.116300918161869
          ],
          "footprint": 0.5166106337869525,
          "instance_id": 78,
          "label": "door",
          "pixel_share": 0.16561197916666667
        },
        {
          "best_view": 14,
          "centroid": [
            4.669831843748851,
            3.509587731746864,
            1.9436734914779663
          ],
          "footprint": 0.2712447827276998,
          "instance_id": 4,
          "label": "blinds",
          "pixel_share": 0.0420703125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3928249b53.npz",
      "raster_sha256": "88717be3eba84a7978559bd792849727225a433649ae45d3968427b671d223ef",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.825244465680729,
            1.9648223500125486
          ],
          [
            0.057730389031596996,
            2.813095103366388
          ],
          [
            4.669831843748851,
            3.509587731746864
          ]
        ],
        "pair": [
          0,
          1
        ],
        "perpendicular_distance": 1.493654147600335,
        "projection": 0.08748072380030045,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.842391675105405,
        "third": 2
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_291e6c1d01445dbfa438ba82",
    "source_row_sha256": "6688c1e3682aeeb1a79a16cbd6a819cd40f5b10189f8eb8cdd01b24ffea5eb9e",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_32d80955bee4dc01_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "vc43ee4230766",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      226,
      452,
      679,
      905,
      1131,
      1358,
      1584,
      1810,
      2037,
      2263,
      2489,
      2716,
      2942,
      3168,
      3395,
      3621,
      3848,
      4074,
      4300,
      4527,
      4753,
      4979,
      5206,
      5432,
      5658,
      5885,
      6111,
      6337,
      6564,
      6790,
      7017
    ],
    "frames": [
      {
        "path": "/data2/k6tk/b7/b7b3d95c3021ca2d2d71dbbb05ee28cb874cc667a9bfc3879c63c439bf88a731.png",
        "sha256": "b7b3d95c3021ca2d2d71dbbb05ee28cb874cc667a9bfc3879c63c439bf88a731"
      },
      {
        "path": "/data2/k6tk/cb/cb1a3e4ef56cd49675243d0099480bd0f2460851bd6181c4f98440c21186eb47.png",
        "sha256": "cb1a3e4ef56cd49675243d0099480bd0f2460851bd6181c4f98440c21186eb47"
      },
      {
        "path": "/data2/k6tk/77/77c0299c542deb88c4c04b99e068cdbf7e9b49b21d54163dcb57fa92a674519f.png",
        "sha256": "77c0299c542deb88c4c04b99e068cdbf7e9b49b21d54163dcb57fa92a674519f"
      },
      {
        "path": "/data2/k6tk/67/67ff3704a0c942a4e2083ff3e6f105d811b2cd550ee459be854fa7bd0253356c.png",
        "sha256": "67ff3704a0c942a4e2083ff3e6f105d811b2cd550ee459be854fa7bd0253356c"
      },
      {
        "path": "/data2/k6tk/4a/4a003f37dc3ee12d00e0e7fd56d0a881a9b649a045ef0a3f5de1e47c2f2b3291.png",
        "sha256": "4a003f37dc3ee12d00e0e7fd56d0a881a9b649a045ef0a3f5de1e47c2f2b3291"
      },
      {
        "path": "/data2/k6tk/30/30bdbe6cf202b749a2875c1c05a865d5f5a30075c3cd889f9c73d1753d5beb78.png",
        "sha256": "30bdbe6cf202b749a2875c1c05a865d5f5a30075c3cd889f9c73d1753d5beb78"
      },
      {
        "path": "/data2/k6tk/1f/1ff1260857173137ae36869a47bd73301a0214201986fd7c164158cfa26ef9b8.png",
        "sha256": "1ff1260857173137ae36869a47bd73301a0214201986fd7c164158cfa26ef9b8"
      },
      {
        "path": "/data2/k6tk/74/7426b6e2d57ff8e00b6079b7fbe7960611ca61b0ff08725e9852bac03c299e32.png",
        "sha256": "7426b6e2d57ff8e00b6079b7fbe7960611ca61b0ff08725e9852bac03c299e32"
      },
      {
        "path": "/data2/k6tk/e3/e3954dbba621d17590a52f551dea8c3bbc8bdc88e45a563c2097104c4abd17a5.png",
        "sha256": "e3954dbba621d17590a52f551dea8c3bbc8bdc88e45a563c2097104c4abd17a5"
      },
      {
        "path": "/data2/k6tk/00/0087a02af6a39f571fb49c86cef98900a1df9d09aac4f354a831994090ecbd34.png",
        "sha256": "0087a02af6a39f571fb49c86cef98900a1df9d09aac4f354a831994090ecbd34"
      },
      {
        "path": "/data2/k6tk/de/de2bd0ad64811c6b1f5e6c6b62242df6f2eaa7d3e300f14ec731a4a632f9c586.png",
        "sha256": "de2bd0ad64811c6b1f5e6c6b62242df6f2eaa7d3e300f14ec731a4a632f9c586"
      },
      {
        "path": "/data2/k6tk/d9/d96750c96ddee32e2aa36fc92e2f4caac59d6f4739778aac8ace8890025fe1b2.png",
        "sha256": "d96750c96ddee32e2aa36fc92e2f4caac59d6f4739778aac8ace8890025fe1b2"
      },
      {
        "path": "/data2/k6tk/06/06affd5382bd6ab9eeff122022d5824ee9f272890102f8776c3a99788415784b.png",
        "sha256": "06affd5382bd6ab9eeff122022d5824ee9f272890102f8776c3a99788415784b"
      },
      {
        "path": "/data2/k6tk/38/385c045e61b519378841248011873ecd767d6c29f4407598387a54b0226df3fd.png",
        "sha256": "385c045e61b519378841248011873ecd767d6c29f4407598387a54b0226df3fd"
      },
      {
        "path": "/data2/k6tk/f7/f7947cfe99633440ba8eb99c3d8febf2a39df6b1a6cb23d70fb5e51d2cc3df09.png",
        "sha256": "f7947cfe99633440ba8eb99c3d8febf2a39df6b1a6cb23d70fb5e51d2cc3df09"
      },
      {
        "path": "/data2/k6tk/aa/aab384e18dad6f873d25a42eb79842c9e530b8b6cf92d061a4a7e0032c1b9c2a.png",
        "sha256": "aab384e18dad6f873d25a42eb79842c9e530b8b6cf92d061a4a7e0032c1b9c2a"
      },
      {
        "path": "/data2/k6tk/e8/e8f32998dff150b8200f908c3726dc5ac812410b0b19cf26dbac65f5563e0608.png",
        "sha256": "e8f32998dff150b8200f908c3726dc5ac812410b0b19cf26dbac65f5563e0608"
      },
      {
        "path": "/data2/k6tk/dd/dde08313a67a97b68ee06a4cc3915e250d29f71db0aaffed26487bcabb5d649b.png",
        "sha256": "dde08313a67a97b68ee06a4cc3915e250d29f71db0aaffed26487bcabb5d649b"
      },
      {
        "path": "/data2/k6tk/a9/a9446107f5aa0b7c81610849959d2939bb43ffc2d3bf485d288348a639017e78.png",
        "sha256": "a9446107f5aa0b7c81610849959d2939bb43ffc2d3bf485d288348a639017e78"
      },
      {
        "path": "/data2/k6tk/46/4660e704d6bd11770125138376b11bdf4ebe839d758d9e305d2a29e3ad88ff96.png",
        "sha256": "4660e704d6bd11770125138376b11bdf4ebe839d758d9e305d2a29e3ad88ff96"
      },
      {
        "path": "/data2/k6tk/62/620f651f9e5e6ae77b9d6d34f11d3c5edeaa7befe25a1fa783d3c7b97aa7dbc3.png",
        "sha256": "620f651f9e5e6ae77b9d6d34f11d3c5edeaa7befe25a1fa783d3c7b97aa7dbc3"
      },
      {
        "path": "/data2/k6tk/44/448e18f300996db1cd24f6bf8f5c3b8b5c0d1c2bd61bb867b337fff024dbceed.png",
        "sha256": "448e18f300996db1cd24f6bf8f5c3b8b5c0d1c2bd61bb867b337fff024dbceed"
      },
      {
        "path": "/data2/k6tk/da/da1d7f13cdec8657c1a002e1fdfc67c4f9b20922be6c86de991808c26b73cdb2.png",
        "sha256": "da1d7f13cdec8657c1a002e1fdfc67c4f9b20922be6c86de991808c26b73cdb2"
      },
      {
        "path": "/data2/k6tk/a4/a45dbf939d08a07a7e0e2433ac365329515f6d44fc8b11d0bba969c1c524661f.png",
        "sha256": "a45dbf939d08a07a7e0e2433ac365329515f6d44fc8b11d0bba969c1c524661f"
      },
      {
        "path": "/data2/k6tk/f9/f91c1d355410cc7d9f6be8f6e35f8908bf91d11d5ce2fbd3aef1b26b6bdc2923.png",
        "sha256": "f91c1d355410cc7d9f6be8f6e35f8908bf91d11d5ce2fbd3aef1b26b6bdc2923"
      },
      {
        "path": "/data2/k6tk/05/0554b4d66a71a59e3ca1cfd564097891d9587df02743b75eb763715d77541ce2.png",
        "sha256": "0554b4d66a71a59e3ca1cfd564097891d9587df02743b75eb763715d77541ce2"
      },
      {
        "path": "/data2/k6tk/23/236b746f1a52c812a739dc14dd000b4cd8a500293e64590ea3ff3a7fd3ce9814.png",
        "sha256": "236b746f1a52c812a739dc14dd000b4cd8a500293e64590ea3ff3a7fd3ce9814"
      },
      {
        "path": "/data2/k6tk/29/29fabcd2923a4f4f74ec5dcd40e28d1465f094d4a41f8fef2de7d69377842f4f.png",
        "sha256": "29fabcd2923a4f4f74ec5dcd40e28d1465f094d4a41f8fef2de7d69377842f4f"
      },
      {
        "path": "/data2/k6tk/96/96e1796cfe0352b5b9b94d2a9b49c6aa6caab1a5ede3de39ca30303fba5f907b.png",
        "sha256": "96e1796cfe0352b5b9b94d2a9b49c6aa6caab1a5ede3de39ca30303fba5f907b"
      },
      {
        "path": "/data2/k6tk/d4/d452273eb5e7c0da037dbdaf98f1303e686e3ea356737686a60c6bb3b1f571d8.png",
        "sha256": "d452273eb5e7c0da037dbdaf98f1303e686e3ea356737686a60c6bb3b1f571d8"
      },
      {
        "path": "/data2/k6tk/68/68b3e8d84c66ae702cd8b32d65eab1bd2039fe6ae3badad849ca49dfdff0b095.png",
        "sha256": "68b3e8d84c66ae702cd8b32d65eab1bd2039fe6ae3badad849ca49dfdff0b095"
      },
      {
        "path": "/data2/k6tk/0d/0d49b3f54b589b9eb53b6bce92f518edca07862a4c492eccf0c41d2ab759a8e1.png",
        "sha256": "0d49b3f54b589b9eb53b6bce92f518edca07862a4c492eccf0c41d2ab759a8e1"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      3.7666666666666666,
      7.533333333333333,
      11.316666666666666,
      15.083333333333334,
      18.85,
      22.633333333333333,
      26.4,
      30.166666666666668,
      33.95,
      37.71666666666667,
      41.483333333333334,
      45.266666666666666,
      49.03333333333333,
      52.8,
      56.583333333333336,
      60.35,
      64.13333333333334,
      67.9,
      71.66666666666667,
      75.45,
      79.21666666666667,
      82.98333333333333,
      86.76666666666667,
      90.53333333333333,
      94.3,
      98.08333333333333,
      101.85,
      105.61666666666666,
      109.4,
      113.16666666666667,
      116.95
    ],
    "total_num_frames": 7018
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: window sill in frame 7; door in frame 3; blinds in frame 14.\nOf these, the window sill and the door are farthest apart, with the blinds off to the side.\n</think>\n\n18.49",
  "validation_commit": ""
}
```

## sb_rowLR_1ffe3ee902e2484e_q0

```json
{
  "answer": "25.23",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-0b53b145f43bb3e81d7ae23b40be93e9d25c30fe4a03b631c2cf6c9a67eae869",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v028108de5fde",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        301,
        603,
        904,
        1206,
        1507,
        1809,
        2111,
        2412,
        2714,
        3015,
        3317,
        3618,
        3920,
        4222,
        4523,
        4825,
        5126,
        5428,
        5730,
        6031,
        6333,
        6634,
        6936,
        7237,
        7539,
        7841,
        8142,
        8444,
        8745,
        9047,
        9349
      ],
      "options": [],
      "qid": "sb_rowLR_1ffe3ee902e2484e_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/abb6639ceb",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/abb6639ceb",
    "details": {
      "cell": "scannetpp|20-40",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      301,
      603,
      904,
      1206,
      1507,
      1809,
      2111,
      2412,
      2714,
      3015,
      3317,
      3618,
      3920,
      4222,
      4523,
      4825,
      5126,
      5428,
      5730,
      6031,
      6333,
      6634,
      6936,
      7237,
      7539,
      7841,
      8142,
      8444,
      8745,
      9047,
      9349
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__abb6639ceb.npz": "a7d1d6ca2e34d20f6e1dae3e61d78b6a0a96cab16a306d56e6c2e41ad5972b05",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/abb6639ceb",
    "room_measurement": {
      "area_m2": 25.227500000000003,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 10091,
      "floor_height_m": -0.06778165978599776,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 9158
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 6,
          "centroid": [
            0.7444970379799227,
            0.7830950195676551,
            1.2462994419038298
          ],
          "footprint": 1.000335400244,
          "instance_id": 41,
          "label": "bookshelf",
          "pixel_share": 0.7939973958333333
        },
        {
          "best_view": 13,
          "centroid": [
            5.49819514112591,
            1.9060428300356387,
            3.3235342502593994
          ],
          "footprint": 0.7270185648143633,
          "instance_id": 48,
          "label": "air duct",
          "pixel_share": 0.079609375
        },
        {
          "best_view": 32,
          "centroid": [
            0.2270310990076525,
            2.0356652480246304,
            1.0844770036637783
          ],
          "footprint": 0.49253955575814007,
          "instance_id": 40,
          "label": "door",
          "pixel_share": 0.2788541666666667
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__abb6639ceb.npz",
      "raster_sha256": "a7d1d6ca2e34d20f6e1dae3e61d78b6a0a96cab16a306d56e6c2e41ad5972b05",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            0.7444970379799227,
            0.7830950195676551
          ],
          [
            5.49819514112591,
            1.9060428300356387
          ],
          [
            0.2270310990076525,
            2.0356652480246304
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 1.239470596312762,
        "projection": 0.8960502155054129,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 5.2727575641371764,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_9ca9586369d887a8518530d2",
    "source_row_sha256": "83ab4e05b5b05e76d07a7113da556d5e21bcc35960adb9679a3276e39891857c",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_1ffe3ee902e2484e_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v028108de5fde",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      301,
      603,
      904,
      1206,
      1507,
      1809,
      2111,
      2412,
      2714,
      3015,
      3317,
      3618,
      3920,
      4222,
      4523,
      4825,
      5126,
      5428,
      5730,
      6031,
      6333,
      6634,
      6936,
      7237,
      7539,
      7841,
      8142,
      8444,
      8745,
      9047,
      9349
    ],
    "frames": [
      {
        "path": "/data2/k6tk/59/59de21ff4142c35d7947a0d1e60adbab72e2ff6c6db2f54b4976867e9b901a61.png",
        "sha256": "59de21ff4142c35d7947a0d1e60adbab72e2ff6c6db2f54b4976867e9b901a61"
      },
      {
        "path": "/data2/k6tk/9f/9f33df301e6fb0db870c61542a90b3ca2c83587a2fd570595d1022a25e6995a1.png",
        "sha256": "9f33df301e6fb0db870c61542a90b3ca2c83587a2fd570595d1022a25e6995a1"
      },
      {
        "path": "/data2/k6tk/6a/6a4d41cb228e37304658ec43108ca8d514bcb6856d3ad784cb59521af1292418.png",
        "sha256": "6a4d41cb228e37304658ec43108ca8d514bcb6856d3ad784cb59521af1292418"
      },
      {
        "path": "/data2/k6tk/cc/ccc2f9ca6cf4bd12c066c16d2da02ac1de8568344ebce392930559c9246b4ec4.png",
        "sha256": "ccc2f9ca6cf4bd12c066c16d2da02ac1de8568344ebce392930559c9246b4ec4"
      },
      {
        "path": "/data2/k6tk/59/5983d0b498575bdea75d7f3087427e07cefe1f336ae373c0b344a670c7b3f023.png",
        "sha256": "5983d0b498575bdea75d7f3087427e07cefe1f336ae373c0b344a670c7b3f023"
      },
      {
        "path": "/data2/k6tk/e7/e775119eb45e589590d51c797c5780ec92bb6712f0ad52c55ffdbbc285cd5206.png",
        "sha256": "e775119eb45e589590d51c797c5780ec92bb6712f0ad52c55ffdbbc285cd5206"
      },
      {
        "path": "/data2/k6tk/8a/8a0d3758dfbdd7c8563d7360b100c9ca2be5777b1262c3080b35390c90074d9e.png",
        "sha256": "8a0d3758dfbdd7c8563d7360b100c9ca2be5777b1262c3080b35390c90074d9e"
      },
      {
        "path": "/data2/k6tk/8f/8f1d3797ef6fcb2bd058bc9197ddb07650cc029b124c60954c9e69160fd97ef2.png",
        "sha256": "8f1d3797ef6fcb2bd058bc9197ddb07650cc029b124c60954c9e69160fd97ef2"
      },
      {
        "path": "/data2/k6tk/28/2881c0ba234778d5a81eb955b67a706442d14c2066f33b750130a871f451034b.png",
        "sha256": "2881c0ba234778d5a81eb955b67a706442d14c2066f33b750130a871f451034b"
      },
      {
        "path": "/data2/k6tk/82/823aa6af169be93bc935c32a3b4aa3c392fe8bd6e100bc59f7305b556b12cc2c.png",
        "sha256": "823aa6af169be93bc935c32a3b4aa3c392fe8bd6e100bc59f7305b556b12cc2c"
      },
      {
        "path": "/data2/k6tk/13/1324d1df470c0d2b5bbd0e9cf32b7c306502782b7ebbc8e7006414ccbcff0fef.png",
        "sha256": "1324d1df470c0d2b5bbd0e9cf32b7c306502782b7ebbc8e7006414ccbcff0fef"
      },
      {
        "path": "/data2/k6tk/ac/acab90fd2e2610343493b3b2e14b7cac2c0f9e8ce05b642951fe1dc6508dad09.png",
        "sha256": "acab90fd2e2610343493b3b2e14b7cac2c0f9e8ce05b642951fe1dc6508dad09"
      },
      {
        "path": "/data2/k6tk/ab/ab8865f5665f69ac6e4b42b4f8e68fe84879b7d9d83bbf2d9b26b841901eb29d.png",
        "sha256": "ab8865f5665f69ac6e4b42b4f8e68fe84879b7d9d83bbf2d9b26b841901eb29d"
      },
      {
        "path": "/data2/k6tk/41/410f911abd118dc00e5a22cb4718bf863bd9618a7c335e0bda27429961cabc33.png",
        "sha256": "410f911abd118dc00e5a22cb4718bf863bd9618a7c335e0bda27429961cabc33"
      },
      {
        "path": "/data2/k6tk/10/10a39c8b7be1a857679b4320acf8d5f830c2c0f069606a5f050bfd1017d4a69f.png",
        "sha256": "10a39c8b7be1a857679b4320acf8d5f830c2c0f069606a5f050bfd1017d4a69f"
      },
      {
        "path": "/data2/k6tk/28/28859a6c2607376c4fd12b071692625ad083171b92608f1561d3c40dd492227e.png",
        "sha256": "28859a6c2607376c4fd12b071692625ad083171b92608f1561d3c40dd492227e"
      },
      {
        "path": "/data2/k6tk/23/230da991fd2afd609f096e53191a1010e168bfc87253ad0e7e68e9954f95cd61.png",
        "sha256": "230da991fd2afd609f096e53191a1010e168bfc87253ad0e7e68e9954f95cd61"
      },
      {
        "path": "/data2/k6tk/2b/2bbc773e8c73b54e7240bdf6be39625f11dd3d6fef251d5e83ef86fa4ccc8c77.png",
        "sha256": "2bbc773e8c73b54e7240bdf6be39625f11dd3d6fef251d5e83ef86fa4ccc8c77"
      },
      {
        "path": "/data2/k6tk/47/4783ee14569fc2e5cdcd94535eeb5f2a8ac7a7fb310f505081cbca67c11d3157.png",
        "sha256": "4783ee14569fc2e5cdcd94535eeb5f2a8ac7a7fb310f505081cbca67c11d3157"
      },
      {
        "path": "/data2/k6tk/dc/dc3bd4438dd54207aeaf25246bb4397625158b426117b0837fcd7a8a30da5a43.png",
        "sha256": "dc3bd4438dd54207aeaf25246bb4397625158b426117b0837fcd7a8a30da5a43"
      },
      {
        "path": "/data2/k6tk/84/8464b4bb40dfac64163c07c0a868cda35b31d5fcb3f5c3ae8907f39645b9bc93.png",
        "sha256": "8464b4bb40dfac64163c07c0a868cda35b31d5fcb3f5c3ae8907f39645b9bc93"
      },
      {
        "path": "/data2/k6tk/ef/ef6b006289cd6cc4bca7b2562a17e8cc31ff5e00c16a0cd84bfe5a6a96534545.png",
        "sha256": "ef6b006289cd6cc4bca7b2562a17e8cc31ff5e00c16a0cd84bfe5a6a96534545"
      },
      {
        "path": "/data2/k6tk/0c/0c821607b3400996e1e9b7e0c14d28c9560044951fc803f33deec6d5a5f8fdd7.png",
        "sha256": "0c821607b3400996e1e9b7e0c14d28c9560044951fc803f33deec6d5a5f8fdd7"
      },
      {
        "path": "/data2/k6tk/6b/6b8cc2b6217137552489f7edda2378e8921ccefac937e43bc3797a49bbc35117.png",
        "sha256": "6b8cc2b6217137552489f7edda2378e8921ccefac937e43bc3797a49bbc35117"
      },
      {
        "path": "/data2/k6tk/85/85b05753af217aad8824abf7d1c400235ac4cf60e259f12125c5f23f7c054d5d.png",
        "sha256": "85b05753af217aad8824abf7d1c400235ac4cf60e259f12125c5f23f7c054d5d"
      },
      {
        "path": "/data2/k6tk/51/5155f12842989087d032147eed0ffc2d7c7479266b93e237b0f7adebe09b43d7.png",
        "sha256": "5155f12842989087d032147eed0ffc2d7c7479266b93e237b0f7adebe09b43d7"
      },
      {
        "path": "/data2/k6tk/be/be5bbd5fbbee63779d0912d9d95dadeaaf19b0df4af44739d5c722c096efda93.png",
        "sha256": "be5bbd5fbbee63779d0912d9d95dadeaaf19b0df4af44739d5c722c096efda93"
      },
      {
        "path": "/data2/k6tk/a8/a8fbd65a0932bec15462e06d49bf822487a6256b5af5575f80c293cf237a869b.png",
        "sha256": "a8fbd65a0932bec15462e06d49bf822487a6256b5af5575f80c293cf237a869b"
      },
      {
        "path": "/data2/k6tk/be/bee924951ce4f9cfcfac86c0af28a6fc94ceb718ccfa7a2545e8f4839bb093f4.png",
        "sha256": "bee924951ce4f9cfcfac86c0af28a6fc94ceb718ccfa7a2545e8f4839bb093f4"
      },
      {
        "path": "/data2/k6tk/75/75bee0759acc0a767eb2a3e02b82080598ee2e96a1627349eb0b0e31100435cd.png",
        "sha256": "75bee0759acc0a767eb2a3e02b82080598ee2e96a1627349eb0b0e31100435cd"
      },
      {
        "path": "/data2/k6tk/14/146eedcc552e201a576371eaaf23c69c2c8a534cdabd995fef72b97e61bfe79d.png",
        "sha256": "146eedcc552e201a576371eaaf23c69c2c8a534cdabd995fef72b97e61bfe79d"
      },
      {
        "path": "/data2/k6tk/df/dfd2fd473085a28e3c8fde2a113d00d49644e1afb20632124f5873d4d3ecac5e.png",
        "sha256": "dfd2fd473085a28e3c8fde2a113d00d49644e1afb20632124f5873d4d3ecac5e"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.016666666666667,
      10.05,
      15.066666666666666,
      20.1,
      25.116666666666667,
      30.15,
      35.18333333333333,
      40.2,
      45.233333333333334,
      50.25,
      55.28333333333333,
      60.3,
      65.33333333333333,
      70.36666666666666,
      75.38333333333334,
      80.41666666666667,
      85.43333333333334,
      90.46666666666667,
      95.5,
      100.51666666666667,
      105.55,
      110.56666666666666,
      115.6,
      120.61666666666666,
      125.65,
      130.68333333333334,
      135.7,
      140.73333333333332,
      145.75,
      150.78333333333333,
      155.81666666666666
    ],
    "total_num_frames": 9350
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: bookshelf in frame 6; air duct in frame 13; door in frame 32.\nOf these, the air duct and the door are farthest apart, with the bookshelf off to the side.\n</think>\n\n25.23",
  "validation_commit": ""
}
```

## sb_rowLR_23bf06d0dc701e77_q0

```json
{
  "answer": "12.57",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-7bc3a5785614a8302d090df375a5b94eade4db2a1edde33d24dc897580b66de9",
  "category": "room_size_estimation",
  "dataset": "d1",
  "form": "direct",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v08142e0e10e9",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        26,
        52,
        78,
        104,
        130,
        156,
        182,
        208,
        234,
        260,
        286,
        312,
        338,
        364,
        390,
        417,
        443,
        469,
        495,
        521,
        547,
        573,
        599,
        625,
        651,
        677,
        703,
        729,
        755,
        781,
        808
      ],
      "options": [],
      "qid": "sb_rowLR_23bf06d0dc701e77_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannet/scene0498_00",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0498_00",
    "details": {
      "cell": "scannet|10-20",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      26,
      52,
      78,
      104,
      130,
      156,
      182,
      208,
      234,
      260,
      286,
      312,
      338,
      364,
      390,
      417,
      443,
      469,
      495,
      521,
      547,
      573,
      599,
      625,
      651,
      677,
      703,
      729,
      755,
      781,
      808
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0498_00.npz": "383cfe7763b155b98d12db7b49b1d1f1c749023ca50b785c8caa284cbab0a694",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0498",
    "room_measurement": {
      "area_m2": 12.57,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 5028,
      "floor_height_m": -0.04664841941504604,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 3546
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 29,
          "centroid": [
            4.486905336380005,
            0.09038709476590157,
            1.5105168521404266
          ],
          "footprint": 3.044517704215167,
          "instance_id": 0,
          "label": "window",
          "pixel_share": 0.37561197916666667
        },
        {
          "best_view": 22,
          "centroid": [
            3.29369580745697,
            4.215522289276123,
            1.131425179541111
          ],
          "footprint": 2.299905836304223,
          "instance_id": 5,
          "label": "door",
          "pixel_share": 0.418359375
        },
        {
          "best_view": 14,
          "centroid": [
            5.197557210922241,
            4.043218731880188,
            0.9280344098806381
          ],
          "footprint": 1.34220875219102,
          "instance_id": 26,
          "label": "refrigerator",
          "pixel_share": 0.218359375
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0498_00.npz",
      "raster_sha256": "383cfe7763b155b98d12db7b49b1d1f1c749023ca50b785c8caa284cbab0a694",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            4.486905336380005,
            0.09038709476590157
          ],
          [
            3.29369580745697,
            4.215522289276123
          ],
          [
            5.197557210922241,
            4.043218731880188
          ]
        ],
        "pair": [
          0,
          1
        ],
        "perpendicular_distance": 1.7810120200495496,
        "projection": 0.838264539511916,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.294239088930612,
        "third": 2
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "a0_room_room_scannet_scene0498_00_s0",
    "source_row_sha256": "c8c40770497fd3301cd7f4dfa6ccdd8b9ac77d4d7896a3addd8c17f227c932ca",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_23bf06d0dc701e77_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v08142e0e10e9",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      26,
      52,
      78,
      104,
      130,
      156,
      182,
      208,
      234,
      260,
      286,
      312,
      338,
      364,
      390,
      417,
      443,
      469,
      495,
      521,
      547,
      573,
      599,
      625,
      651,
      677,
      703,
      729,
      755,
      781,
      808
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c7/c726fb1915cf0da944d8e0812754a0b6664e6647a82e4c35ea2870d3787c914a.png",
        "sha256": "c726fb1915cf0da944d8e0812754a0b6664e6647a82e4c35ea2870d3787c914a"
      },
      {
        "path": "/data2/k6tk/f7/f78c278c44f64b851112c46e3c1bd865a07e809b0c4cad4b46325af1fc0e2f49.png",
        "sha256": "f78c278c44f64b851112c46e3c1bd865a07e809b0c4cad4b46325af1fc0e2f49"
      },
      {
        "path": "/data2/k6tk/86/8680184c56994e8d3c5f3e2ad5defcfe8a91a78cb45068ed056f07638cd465fe.png",
        "sha256": "8680184c56994e8d3c5f3e2ad5defcfe8a91a78cb45068ed056f07638cd465fe"
      },
      {
        "path": "/data2/k6tk/4e/4ed0667cb400cebf3bf624db27c4c34e32408952bea36949a07fd4cc609e20e7.png",
        "sha256": "4ed0667cb400cebf3bf624db27c4c34e32408952bea36949a07fd4cc609e20e7"
      },
      {
        "path": "/data2/k6tk/b1/b1d96b2783f71170fdde7f6ee1ee3b06adbb06c6cea46bde24b962b3eb4bb1d9.png",
        "sha256": "b1d96b2783f71170fdde7f6ee1ee3b06adbb06c6cea46bde24b962b3eb4bb1d9"
      },
      {
        "path": "/data2/k6tk/5e/5ebe1a7280c78eb3094e5247e57f49f6049443265167b42ea742d5bdf29f6415.png",
        "sha256": "5ebe1a7280c78eb3094e5247e57f49f6049443265167b42ea742d5bdf29f6415"
      },
      {
        "path": "/data2/k6tk/ec/ece8dd6f45c368497af53f7ed794b888c402a98d1065fffd6b5603f7db2c0cb7.png",
        "sha256": "ece8dd6f45c368497af53f7ed794b888c402a98d1065fffd6b5603f7db2c0cb7"
      },
      {
        "path": "/data2/k6tk/ad/adbfd815ae1bbc582b452a10914c25c970983aa6dcbfe79500064940b16e539b.png",
        "sha256": "adbfd815ae1bbc582b452a10914c25c970983aa6dcbfe79500064940b16e539b"
      },
      {
        "path": "/data2/k6tk/2b/2bf5cea1f77ea2f8c25755683e6ad7d6d9cd62bc2ce8b3e10d807302799a37e4.png",
        "sha256": "2bf5cea1f77ea2f8c25755683e6ad7d6d9cd62bc2ce8b3e10d807302799a37e4"
      },
      {
        "path": "/data2/k6tk/b2/b28f2d1e6c2bdc75388a0fc0317564267c540472f613483b9f657af417ecea0d.png",
        "sha256": "b28f2d1e6c2bdc75388a0fc0317564267c540472f613483b9f657af417ecea0d"
      },
      {
        "path": "/data2/k6tk/3c/3c60d62e6ed3db330c3eea8cd4631450c5206f0e075db8a5cf1e34ccd074f066.png",
        "sha256": "3c60d62e6ed3db330c3eea8cd4631450c5206f0e075db8a5cf1e34ccd074f066"
      },
      {
        "path": "/data2/k6tk/71/71dc53fe30cf962b3856a9c5617b5c765294819d53b410f542aa3a2216271d5d.png",
        "sha256": "71dc53fe30cf962b3856a9c5617b5c765294819d53b410f542aa3a2216271d5d"
      },
      {
        "path": "/data2/k6tk/bc/bcb65fd0cbe58d6598d468396528edb328c7f171d33e59a4956d77d336ff1128.png",
        "sha256": "bcb65fd0cbe58d6598d468396528edb328c7f171d33e59a4956d77d336ff1128"
      },
      {
        "path": "/data2/k6tk/e5/e517ba1df5a1c0d6a2ba6833241cac8e9e669a295461c72cc9b2a9dcb8fef43c.png",
        "sha256": "e517ba1df5a1c0d6a2ba6833241cac8e9e669a295461c72cc9b2a9dcb8fef43c"
      },
      {
        "path": "/data2/k6tk/bf/bf4c4730dabd2b63831544b540495cd74dc8e51bbaf280a1a3bf73db7fa8a219.png",
        "sha256": "bf4c4730dabd2b63831544b540495cd74dc8e51bbaf280a1a3bf73db7fa8a219"
      },
      {
        "path": "/data2/k6tk/4b/4bb76f8bbcd310159853216da4c6d6b16cb628a72e64f680619aaf24892675ae.png",
        "sha256": "4bb76f8bbcd310159853216da4c6d6b16cb628a72e64f680619aaf24892675ae"
      },
      {
        "path": "/data2/k6tk/37/37fbd353f9c29c29435b79c3bd69268cff35dadfcefbd52bf4aaae7f0b27107e.png",
        "sha256": "37fbd353f9c29c29435b79c3bd69268cff35dadfcefbd52bf4aaae7f0b27107e"
      },
      {
        "path": "/data2/k6tk/f5/f546a891b8d9eaaa2b21ca56b0eeab2c7ec4b8a5d4d798f17a55f6984031a4b2.png",
        "sha256": "f546a891b8d9eaaa2b21ca56b0eeab2c7ec4b8a5d4d798f17a55f6984031a4b2"
      },
      {
        "path": "/data2/k6tk/ff/ff6c8591e8258b78a343ee8f7b5e0fbd19c44eac06377d61eb8f92d31bf291d9.png",
        "sha256": "ff6c8591e8258b78a343ee8f7b5e0fbd19c44eac06377d61eb8f92d31bf291d9"
      },
      {
        "path": "/data2/k6tk/06/06adeb35a5de3886692a29c4a91d1b8fdb8cbb0b3d5e9340d61443f77d315355.png",
        "sha256": "06adeb35a5de3886692a29c4a91d1b8fdb8cbb0b3d5e9340d61443f77d315355"
      },
      {
        "path": "/data2/k6tk/a8/a8055a16e90fe30b9ec09b6290df2f4d8d6cf62f42098265df7a677a94ab6526.png",
        "sha256": "a8055a16e90fe30b9ec09b6290df2f4d8d6cf62f42098265df7a677a94ab6526"
      },
      {
        "path": "/data2/k6tk/43/43d63d4b5dda099053f37c97c07e9e9f748e2d0b9df7b4e799f831e6084eb504.png",
        "sha256": "43d63d4b5dda099053f37c97c07e9e9f748e2d0b9df7b4e799f831e6084eb504"
      },
      {
        "path": "/data2/k6tk/45/4573cb60db9bdfa17d89667899b58a55d3ddc767f777cd3e4d706da9bb2a49fe.png",
        "sha256": "4573cb60db9bdfa17d89667899b58a55d3ddc767f777cd3e4d706da9bb2a49fe"
      },
      {
        "path": "/data2/k6tk/6b/6bbc01eddb3aecce325d1e70cf3f6b325cc476e8523b9079594cccf1ef7bea8f.png",
        "sha256": "6bbc01eddb3aecce325d1e70cf3f6b325cc476e8523b9079594cccf1ef7bea8f"
      },
      {
        "path": "/data2/k6tk/40/40a82ca0a6374cb86ed3875721dcc4db86277f5dea0a4193b5a45d1f5e635f02.png",
        "sha256": "40a82ca0a6374cb86ed3875721dcc4db86277f5dea0a4193b5a45d1f5e635f02"
      },
      {
        "path": "/data2/k6tk/ca/ca3a74496181253bc7d0cc43ef3bf7f48b9bfab07388388d8d8e88866e6f047f.png",
        "sha256": "ca3a74496181253bc7d0cc43ef3bf7f48b9bfab07388388d8d8e88866e6f047f"
      },
      {
        "path": "/data2/k6tk/74/749e88408612416e39c60ceb8b404f81906c065da87242fb89789a614338e905.png",
        "sha256": "749e88408612416e39c60ceb8b404f81906c065da87242fb89789a614338e905"
      },
      {
        "path": "/data2/k6tk/e5/e57c67fb5924544739b09b96493d3bc9f557bae8e2fcdc561cb38b66aa721a84.png",
        "sha256": "e57c67fb5924544739b09b96493d3bc9f557bae8e2fcdc561cb38b66aa721a84"
      },
      {
        "path": "/data2/k6tk/b8/b8ed55a800cba3feb54c10cb9d90c55e84cc6ab76c30fdff77ae5c13b3eb8562.png",
        "sha256": "b8ed55a800cba3feb54c10cb9d90c55e84cc6ab76c30fdff77ae5c13b3eb8562"
      },
      {
        "path": "/data2/k6tk/4d/4d7a1156c1bd6897b6bca11c7bf5ed26427c28fc0ff7e6478fae3f02d9d3f538.png",
        "sha256": "4d7a1156c1bd6897b6bca11c7bf5ed26427c28fc0ff7e6478fae3f02d9d3f538"
      },
      {
        "path": "/data2/k6tk/65/659da48f10384adeaad2d9511dd3a1d1f55d99d2c8473945fe451ae1e54cf407.png",
        "sha256": "659da48f10384adeaad2d9511dd3a1d1f55d99d2c8473945fe451ae1e54cf407"
      },
      {
        "path": "/data2/k6tk/13/134512737bfd82ae0d5d252625c404b3ef78e81069bfc61a32d7fb6e81b1e4af.png",
        "sha256": "134512737bfd82ae0d5d252625c404b3ef78e81069bfc61a32d7fb6e81b1e4af"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      1.0833333333333333,
      2.1666666666666665,
      3.25,
      4.333333333333333,
      5.416666666666667,
      6.5,
      7.583333333333333,
      8.666666666666666,
      9.75,
      10.833333333333334,
      11.916666666666666,
      13.0,
      14.083333333333334,
      15.166666666666666,
      16.25,
      17.375,
      18.458333333333332,
      19.541666666666668,
      20.625,
      21.708333333333332,
      22.791666666666668,
      23.875,
      24.958333333333332,
      26.041666666666668,
      27.125,
      28.208333333333332,
      29.291666666666668,
      30.375,
      31.458333333333332,
      32.541666666666664,
      33.666666666666664
    ],
    "total_num_frames": 809
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: window in frame 29; door in frame 22; refrigerator in frame 14.\nOf these, the window and the door are farthest apart, with the refrigerator off to the side.\n</think>\n\n12.57"
}
```

## sb_rowLR_0571e7ba163af89c_q0

```json
{
  "answer": "19.28",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-d19f05dac926d413644d906cb5893d4287af9e775a3c451c8613c10d27b3dcab",
  "category": "room_size_estimation",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v9daafc17b937",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        349,
        699,
        1048,
        1398,
        1747,
        2097,
        2447,
        2796,
        3146,
        3495,
        3845,
        4194,
        4544,
        4894,
        5243,
        5593,
        5942,
        6292,
        6642,
        6991,
        7341,
        7690,
        8040,
        8389,
        8739,
        9089,
        9438,
        9788,
        10137,
        10487,
        10837
      ],
      "options": [],
      "qid": "sb_rowLR_0571e7ba163af89c_q0",
      "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
      "scene": "scannetpp/4e2db5058c",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/4e2db5058c",
    "details": {
      "cell": "scannetpp|10-20",
      "question_variant": 0,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      349,
      699,
      1048,
      1398,
      1747,
      2097,
      2447,
      2796,
      3146,
      3495,
      3845,
      4194,
      4544,
      4894,
      5243,
      5593,
      5942,
      6292,
      6642,
      6991,
      7341,
      7690,
      8040,
      8389,
      8739,
      9089,
      9438,
      9788,
      10137,
      10487,
      10837
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__4e2db5058c.npz": "dd0a32a320845bc2b5ab236a9d4154467dfa8c4e9ede1a3b4d520e8cc330458c",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/4e2db5058c",
    "room_measurement": {
      "area_m2": 19.282500000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 7713,
      "floor_height_m": -0.006835896594623636,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 6599
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 12,
          "centroid": [
            5.821369154176681,
            0.43218002490355234,
            1.3226930238306522
          ],
          "footprint": 0.9711898546350772,
          "instance_id": 19,
          "label": "wardrobe",
          "pixel_share": 1.0
        },
        {
          "best_view": 16,
          "centroid": [
            3.5753935646137247,
            1.808909614897059,
            0.5464575188554934
          ],
          "footprint": 0.6199308550561976,
          "instance_id": 82,
          "label": "blanket",
          "pixel_share": 0.2720442708333333
        },
        {
          "best_view": 15,
          "centroid": [
            3.4938770947238087,
            1.8096192886596594,
            0.3928049641651724
          ],
          "footprint": 0.5229327337485936,
          "instance_id": 80,
          "label": "bed",
          "pixel_share": 0.023828125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__4e2db5058c.npz",
      "raster_sha256": "dd0a32a320845bc2b5ab236a9d4154467dfa8c4e9ede1a3b4d520e8cc330458c",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "side",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            5.821369154176681,
            0.43218002490355234
          ],
          [
            3.5753935646137247,
            1.808909614897059
          ],
          [
            3.4938770947238087,
            1.8096192886596594
          ]
        ],
        "pair": [
          0,
          2
        ],
        "perpendicular_distance": 0.04090605532485889,
        "projection": 0.9739278212904761,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 2.7045439933846778,
        "third": 1
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "vstirel_59a83d41c869064536f6676a",
    "source_row_sha256": "0167922a100f7e7e29283898067d00ef4a9ff750861dfebccb759879b9a464f1",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_0571e7ba163af89c_q0",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v9daafc17b937",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      349,
      699,
      1048,
      1398,
      1747,
      2097,
      2447,
      2796,
      3146,
      3495,
      3845,
      4194,
      4544,
      4894,
      5243,
      5593,
      5942,
      6292,
      6642,
      6991,
      7341,
      7690,
      8040,
      8389,
      8739,
      9089,
      9438,
      9788,
      10137,
      10487,
      10837
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f2/f2dc5da2d1b66d0c0c955be940c0740520a42c1284386609ff6ccdeb4eb79754.png",
        "sha256": "f2dc5da2d1b66d0c0c955be940c0740520a42c1284386609ff6ccdeb4eb79754"
      },
      {
        "path": "/data2/k6tk/72/728b7ce8ed1ce879f793a30196f23e0c30376b9904ed02fb61bda955ba834f99.png",
        "sha256": "728b7ce8ed1ce879f793a30196f23e0c30376b9904ed02fb61bda955ba834f99"
      },
      {
        "path": "/data2/k6tk/5e/5efd4bba5ee090b13e2937206d975f027742af1851d235de4b6c5c60f4d8f041.png",
        "sha256": "5efd4bba5ee090b13e2937206d975f027742af1851d235de4b6c5c60f4d8f041"
      },
      {
        "path": "/data2/k6tk/3f/3fca8bc14b38912b7b7a9165288c87dee6010782f08ba278c61a67696b9c4fe2.png",
        "sha256": "3fca8bc14b38912b7b7a9165288c87dee6010782f08ba278c61a67696b9c4fe2"
      },
      {
        "path": "/data2/k6tk/db/dbfaa7a52ea804c2eb565b2f6958dc5cd3c57077aa9ff12d1c1bd81c49a92ee8.png",
        "sha256": "dbfaa7a52ea804c2eb565b2f6958dc5cd3c57077aa9ff12d1c1bd81c49a92ee8"
      },
      {
        "path": "/data2/k6tk/b4/b41dd626e7c97a415abf2a3c07acf2aa732b08244bd69ef8afde854d3ffe2cd7.png",
        "sha256": "b41dd626e7c97a415abf2a3c07acf2aa732b08244bd69ef8afde854d3ffe2cd7"
      },
      {
        "path": "/data2/k6tk/51/51c811477dbedb3d7e15970bc1e980f798f8cd3420baa8970e5c7a01b4ef4fb7.png",
        "sha256": "51c811477dbedb3d7e15970bc1e980f798f8cd3420baa8970e5c7a01b4ef4fb7"
      },
      {
        "path": "/data2/k6tk/bd/bd1608d69af1c3deab223493a5052bfab23f18fe4a24d24eb1121bbff09bbe2f.png",
        "sha256": "bd1608d69af1c3deab223493a5052bfab23f18fe4a24d24eb1121bbff09bbe2f"
      },
      {
        "path": "/data2/k6tk/fa/fa8d542d1783984e866b37ca03f76e4b79d3d6a3bb7f89d87518ea6f37df52ba.png",
        "sha256": "fa8d542d1783984e866b37ca03f76e4b79d3d6a3bb7f89d87518ea6f37df52ba"
      },
      {
        "path": "/data2/k6tk/af/afdeec8f4bc586a3232ef64939eae1c826eaa6bd1845c92df518bb2ebae493f5.png",
        "sha256": "afdeec8f4bc586a3232ef64939eae1c826eaa6bd1845c92df518bb2ebae493f5"
      },
      {
        "path": "/data2/k6tk/e3/e35255f9bc4f514a43e3c47048a17b0eff2d924f6841c902b9f27bf5d7f657fb.png",
        "sha256": "e35255f9bc4f514a43e3c47048a17b0eff2d924f6841c902b9f27bf5d7f657fb"
      },
      {
        "path": "/data2/k6tk/60/60f57d5eb0ea81eccef348a47529dee9298af9e50d1538c20a3577a2e53e0427.png",
        "sha256": "60f57d5eb0ea81eccef348a47529dee9298af9e50d1538c20a3577a2e53e0427"
      },
      {
        "path": "/data2/k6tk/62/62b8e1baa44ab2f1174e43bb5ab71b016d80817ffe3e98c7e1fad8bf7254e402.png",
        "sha256": "62b8e1baa44ab2f1174e43bb5ab71b016d80817ffe3e98c7e1fad8bf7254e402"
      },
      {
        "path": "/data2/k6tk/23/2330ec13c17cce3378e71ea83e14bd5af7a9e9f3d549262afcce4db5bd4e9d4f.png",
        "sha256": "2330ec13c17cce3378e71ea83e14bd5af7a9e9f3d549262afcce4db5bd4e9d4f"
      },
      {
        "path": "/data2/k6tk/15/1525097cffacdc3e19db4dfa40aeb69d018332d066d897d672a819c2f508ea3e.png",
        "sha256": "1525097cffacdc3e19db4dfa40aeb69d018332d066d897d672a819c2f508ea3e"
      },
      {
        "path": "/data2/k6tk/3a/3aa3eb980f3427fd49b96c3cf1cdfe2a5ae9686721c7138c05758bd6cd21fd69.png",
        "sha256": "3aa3eb980f3427fd49b96c3cf1cdfe2a5ae9686721c7138c05758bd6cd21fd69"
      },
      {
        "path": "/data2/k6tk/d9/d9fb38985e216378df6d400c831f5cdaac6238b3c888d3317a957337020a29ff.png",
        "sha256": "d9fb38985e216378df6d400c831f5cdaac6238b3c888d3317a957337020a29ff"
      },
      {
        "path": "/data2/k6tk/12/12131e1387a6e6d9839215ab956d61b3e46d130e7949722b38cbd138e427d32d.png",
        "sha256": "12131e1387a6e6d9839215ab956d61b3e46d130e7949722b38cbd138e427d32d"
      },
      {
        "path": "/data2/k6tk/3d/3dc53e421b61cc0c195fa137c5ccd37f249e33d0ca38f3d9f3f9fec7e6b665ca.png",
        "sha256": "3dc53e421b61cc0c195fa137c5ccd37f249e33d0ca38f3d9f3f9fec7e6b665ca"
      },
      {
        "path": "/data2/k6tk/55/55bb31f1b237843bc93116cd076bb9e06a4bc09c60459dace9f013085208db3e.png",
        "sha256": "55bb31f1b237843bc93116cd076bb9e06a4bc09c60459dace9f013085208db3e"
      },
      {
        "path": "/data2/k6tk/55/558ad5d7cf10039f492f5845d7581dc128f7fa67fcad860b8d07309bfd2dab61.png",
        "sha256": "558ad5d7cf10039f492f5845d7581dc128f7fa67fcad860b8d07309bfd2dab61"
      },
      {
        "path": "/data2/k6tk/66/6641a46027accdf4dca4b604ee669ad8ebb2dee0ce2c8bd80e021890dbadea5a.png",
        "sha256": "6641a46027accdf4dca4b604ee669ad8ebb2dee0ce2c8bd80e021890dbadea5a"
      },
      {
        "path": "/data2/k6tk/69/699fcc8c585298860728c2b45bcf5655860b151f989e52e70cdc8476412a526d.png",
        "sha256": "699fcc8c585298860728c2b45bcf5655860b151f989e52e70cdc8476412a526d"
      },
      {
        "path": "/data2/k6tk/7b/7b2672bd9059d8a2376bce1b63e29b9ba72e7d48508be635e993f616c173e5cf.png",
        "sha256": "7b2672bd9059d8a2376bce1b63e29b9ba72e7d48508be635e993f616c173e5cf"
      },
      {
        "path": "/data2/k6tk/c8/c8dbb8b6823993bd961c18e4780a2c1cf37b3687379830a8f579bf8bd2f83824.png",
        "sha256": "c8dbb8b6823993bd961c18e4780a2c1cf37b3687379830a8f579bf8bd2f83824"
      },
      {
        "path": "/data2/k6tk/e5/e5d7ee590038c4d3aed1b39f888f1114235e0533d177471fd9ecdd9939c7f132.png",
        "sha256": "e5d7ee590038c4d3aed1b39f888f1114235e0533d177471fd9ecdd9939c7f132"
      },
      {
        "path": "/data2/k6tk/3a/3af5b68f862e9162e097ef7bf67c168b740b48c9e1bf60cf59050d35d06fdd98.png",
        "sha256": "3af5b68f862e9162e097ef7bf67c168b740b48c9e1bf60cf59050d35d06fdd98"
      },
      {
        "path": "/data2/k6tk/c4/c47f58e4d1867f980616cb69b216c112112bae8735fc8cfba4b17b7b56f87e25.png",
        "sha256": "c47f58e4d1867f980616cb69b216c112112bae8735fc8cfba4b17b7b56f87e25"
      },
      {
        "path": "/data2/k6tk/00/008684e1758e9140d882bf0c230356cf2eb33ef91450e546c79a78b0a9c4523e.png",
        "sha256": "008684e1758e9140d882bf0c230356cf2eb33ef91450e546c79a78b0a9c4523e"
      },
      {
        "path": "/data2/k6tk/c5/c5710ff8c8de660e140cea9128b27b6f049bbd821c752171af49ebfc1d095ce7.png",
        "sha256": "c5710ff8c8de660e140cea9128b27b6f049bbd821c752171af49ebfc1d095ce7"
      },
      {
        "path": "/data2/k6tk/a1/a1fd4afb1dd2a0118bc1bbfee54a020123befadcac950d3caeef613ac5bac528.png",
        "sha256": "a1fd4afb1dd2a0118bc1bbfee54a020123befadcac950d3caeef613ac5bac528"
      },
      {
        "path": "/data2/k6tk/19/199a3e43edda085e01a512e3d9c2aa06910f114369f6fb368bad3d61b25534c5.png",
        "sha256": "199a3e43edda085e01a512e3d9c2aa06910f114369f6fb368bad3d61b25534c5"
      }
    ],
    "options": [],
    "question": "Estimate the total floor footprint covered by the spaces in this video, expressed in square meters.",
    "timestamps": [
      0.0,
      5.816666666666666,
      11.65,
      17.466666666666665,
      23.3,
      29.116666666666667,
      34.95,
      40.78333333333333,
      46.6,
      52.43333333333333,
      58.25,
      64.08333333333333,
      69.9,
      75.73333333333333,
      81.56666666666666,
      87.38333333333334,
      93.21666666666667,
      99.03333333333333,
      104.86666666666666,
      110.7,
      116.51666666666667,
      122.35,
      128.16666666666666,
      134.0,
      139.81666666666666,
      145.65,
      151.48333333333332,
      157.3,
      163.13333333333333,
      168.95,
      174.78333333333333,
      180.61666666666667
    ],
    "total_num_frames": 10838
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: wardrobe in frame 12; blanket in frame 16; bed in frame 15.\nOf these, the wardrobe and the bed are farthest apart, with the blanket off to the side.\n</think>\n\n19.28",
  "validation_commit": ""
}
```

## sb_rowLR_7861c3a4cd227747_q1

```json
{
  "answer": "14.97",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-243ccd1b34de526d16b65dfc1048ebe4f8d798901d93d6382a77d209840d55ff",
  "category": "room_size_estimation",
  "count_arity": 3,
  "count_kind": "total",
  "dataset": "d2",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet++ Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d2/v67fec8db1fb9",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        489,
        979,
        1469,
        1959,
        2449,
        2939,
        3429,
        3919,
        4409,
        4899,
        5389,
        5879,
        6369,
        6859,
        7349,
        7839,
        8329,
        8819,
        9309,
        9799,
        10289,
        10779,
        11269,
        11759,
        12249,
        12739,
        13229,
        13719,
        14209,
        14699,
        15189
      ],
      "options": [],
      "qid": "sb_rowLR_7861c3a4cd227747_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannetpp/867d97cf3d",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannetpp/867d97cf3d",
    "details": {
      "cell": "scannetpp|10-20",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      489,
      979,
      1469,
      1959,
      2449,
      2939,
      3429,
      3919,
      4409,
      4899,
      5389,
      5879,
      6369,
      6859,
      7349,
      7839,
      8329,
      8819,
      9309,
      9799,
      10289,
      10779,
      11269,
      11759,
      12249,
      12739,
      13229,
      13719,
      14209,
      14699,
      15189
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__867d97cf3d.npz": "f5bb4eb1426b308da7c2949be9a8ab7aded98747bfb788b97b09daaeb3c648ae",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannetpp/867d97cf3d",
    "room_measurement": {
      "area_m2": 14.965000000000002,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 5986,
      "floor_height_m": -0.02321829217619456,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 5695
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 17,
          "centroid": [
            3.8560374486832765,
            3.0508066444079156,
            1.1765161417424679
          ],
          "footprint": 0.8438100998977872,
          "instance_id": 126,
          "label": "cabinet",
          "pixel_share": 0.34958333333333336
        },
        {
          "best_view": 15,
          "centroid": [
            2.592646035775176,
            2.988741501248414,
            0.37766312807798386
          ],
          "footprint": 0.6029428516614228,
          "instance_id": 1,
          "label": "bed",
          "pixel_share": 0.09325520833333334
        },
        {
          "best_view": 16,
          "centroid": [
            4.311983051744421,
            2.075710967993609,
            1.181869626045227
          ],
          "footprint": 0.48614172565293473,
          "instance_id": 81,
          "label": "wardrobe",
          "pixel_share": 0.6773958333333333
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__867d97cf3d.npz",
      "raster_sha256": "f5bb4eb1426b308da7c2949be9a8ab7aded98747bfb788b97b09daaeb3c648ae",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.8560374486832765,
            3.0508066444079156
          ],
          [
            2.592646035775176,
            2.988741501248414
          ],
          [
            4.311983051744421,
            2.075710967993609
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 0.6473563474041086,
        "projection": 0.558224501638518,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 1.946726619003701,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_91423d852cd5a4a49c46b9c7",
    "source_row_sha256": "fb9ea3a159f70b5ba95f82927fb182663e07f55d4b794778042113285b53051f",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_7861c3a4cd227747_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v67fec8db1fb9",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      489,
      979,
      1469,
      1959,
      2449,
      2939,
      3429,
      3919,
      4409,
      4899,
      5389,
      5879,
      6369,
      6859,
      7349,
      7839,
      8329,
      8819,
      9309,
      9799,
      10289,
      10779,
      11269,
      11759,
      12249,
      12739,
      13229,
      13719,
      14209,
      14699,
      15189
    ],
    "frames": [
      {
        "path": "/data2/k6tk/1a/1a36c0580f36a1d30654e0ff3506ac3f9762444917c9be7bce0caabe9b46e002.png",
        "sha256": "1a36c0580f36a1d30654e0ff3506ac3f9762444917c9be7bce0caabe9b46e002"
      },
      {
        "path": "/data2/k6tk/a7/a7233a5246bea86d2835e34925f561f29ca3effec2e74f221f036fe0cca04b04.png",
        "sha256": "a7233a5246bea86d2835e34925f561f29ca3effec2e74f221f036fe0cca04b04"
      },
      {
        "path": "/data2/k6tk/2c/2c9b35a01993d925cd6f7cd84dd204fdc0cb4dd8540498a2fe64f08bcde77777.png",
        "sha256": "2c9b35a01993d925cd6f7cd84dd204fdc0cb4dd8540498a2fe64f08bcde77777"
      },
      {
        "path": "/data2/k6tk/fa/faa55df8fde205311a9a1a95a77947acc30473664ca545c0099ee6f5ca9c6579.png",
        "sha256": "faa55df8fde205311a9a1a95a77947acc30473664ca545c0099ee6f5ca9c6579"
      },
      {
        "path": "/data2/k6tk/8e/8e6af610e3ce6c5b4e2c3a053e9fc59effa322efa345dcc2f54154e9ff177de6.png",
        "sha256": "8e6af610e3ce6c5b4e2c3a053e9fc59effa322efa345dcc2f54154e9ff177de6"
      },
      {
        "path": "/data2/k6tk/a2/a2870384e3f16333bbcfa5ec107d5033203a2a7fd15a72ac921430b04a16c391.png",
        "sha256": "a2870384e3f16333bbcfa5ec107d5033203a2a7fd15a72ac921430b04a16c391"
      },
      {
        "path": "/data2/k6tk/93/93e1131970d6dbca650ce3f7cc5035c4d68e8a4b6edb9c38588ce982024d8556.png",
        "sha256": "93e1131970d6dbca650ce3f7cc5035c4d68e8a4b6edb9c38588ce982024d8556"
      },
      {
        "path": "/data2/k6tk/2d/2d003e5ceea8c707a40e9c0f285c75888a299f4898ae33613d233637bea6d44c.png",
        "sha256": "2d003e5ceea8c707a40e9c0f285c75888a299f4898ae33613d233637bea6d44c"
      },
      {
        "path": "/data2/k6tk/dd/dd452fd543737a530793f2c9b65c8541f8e961151d613f037732fff100016e4b.png",
        "sha256": "dd452fd543737a530793f2c9b65c8541f8e961151d613f037732fff100016e4b"
      },
      {
        "path": "/data2/k6tk/a9/a91b7fb7b58319266573d154efdd6eb58d7d61b867cc164c0f83abb1fc65535c.png",
        "sha256": "a91b7fb7b58319266573d154efdd6eb58d7d61b867cc164c0f83abb1fc65535c"
      },
      {
        "path": "/data2/k6tk/ad/adb18e73c279c4705c077348e2ac4658a34ded9aea0538157e4a373c2aa2836e.png",
        "sha256": "adb18e73c279c4705c077348e2ac4658a34ded9aea0538157e4a373c2aa2836e"
      },
      {
        "path": "/data2/k6tk/50/50fdb8a67f8451d86b0e6dc0b437499a380179fed627cd9ddd6b3579facf74d6.png",
        "sha256": "50fdb8a67f8451d86b0e6dc0b437499a380179fed627cd9ddd6b3579facf74d6"
      },
      {
        "path": "/data2/k6tk/31/3182853fd3291b2f17323660e1d045c9991102e95b6e5b187c8aec1d906cf9a0.png",
        "sha256": "3182853fd3291b2f17323660e1d045c9991102e95b6e5b187c8aec1d906cf9a0"
      },
      {
        "path": "/data2/k6tk/eb/eb347f80c4bb5b47e58e21b330106fd12bdb748e0a286dfc3909ce76c08f0067.png",
        "sha256": "eb347f80c4bb5b47e58e21b330106fd12bdb748e0a286dfc3909ce76c08f0067"
      },
      {
        "path": "/data2/k6tk/28/283c87244b624315b5e42a9d59f86218eca9bbf677a25d0c7231a2126a0d5c02.png",
        "sha256": "283c87244b624315b5e42a9d59f86218eca9bbf677a25d0c7231a2126a0d5c02"
      },
      {
        "path": "/data2/k6tk/03/0306305869de5027e5cbfa1ad6b3b033b2197c796e2e14389ff2ff5f1348617d.png",
        "sha256": "0306305869de5027e5cbfa1ad6b3b033b2197c796e2e14389ff2ff5f1348617d"
      },
      {
        "path": "/data2/k6tk/b6/b67068b1d03b0b838d9cf922f5d0fffc2182dadff1307bf4b9ba4a45cc985766.png",
        "sha256": "b67068b1d03b0b838d9cf922f5d0fffc2182dadff1307bf4b9ba4a45cc985766"
      },
      {
        "path": "/data2/k6tk/a7/a75a5fe8d4a37f0a91b2a4d2c7e609949452fb1585bc4c392236936e9ff42642.png",
        "sha256": "a75a5fe8d4a37f0a91b2a4d2c7e609949452fb1585bc4c392236936e9ff42642"
      },
      {
        "path": "/data2/k6tk/73/7389db7f8098a1a30c5d0eb1b80d9186f8f709907cc80ede8cfd17d9a1a71c05.png",
        "sha256": "7389db7f8098a1a30c5d0eb1b80d9186f8f709907cc80ede8cfd17d9a1a71c05"
      },
      {
        "path": "/data2/k6tk/8c/8c4a9ecc69fd28a515d92231d1a662ef3a600da7fe64b2d3b0cb9fd5365047c3.png",
        "sha256": "8c4a9ecc69fd28a515d92231d1a662ef3a600da7fe64b2d3b0cb9fd5365047c3"
      },
      {
        "path": "/data2/k6tk/94/943c7f9192584c9147e4458b7802402882d233f29f2cb03d9211afb8a7c81bb0.png",
        "sha256": "943c7f9192584c9147e4458b7802402882d233f29f2cb03d9211afb8a7c81bb0"
      },
      {
        "path": "/data2/k6tk/ce/cefa8e80e589cb430120e50ddcd8257bd13d58ce5ec22c08c944826144d918cc.png",
        "sha256": "cefa8e80e589cb430120e50ddcd8257bd13d58ce5ec22c08c944826144d918cc"
      },
      {
        "path": "/data2/k6tk/d2/d25edbca60b05bcba7f9603bcac12060d5af61ec15796cf0a69b22f894b3af87.png",
        "sha256": "d25edbca60b05bcba7f9603bcac12060d5af61ec15796cf0a69b22f894b3af87"
      },
      {
        "path": "/data2/k6tk/3d/3d8c0e3e844305682d1fd8e5d96118af3972d266b527ec6e59c08ff31ee56da6.png",
        "sha256": "3d8c0e3e844305682d1fd8e5d96118af3972d266b527ec6e59c08ff31ee56da6"
      },
      {
        "path": "/data2/k6tk/96/9697dd003da5fb6a9c7867ebb22cc43e81fb1d14003dac1dce4d354499a67e6f.png",
        "sha256": "9697dd003da5fb6a9c7867ebb22cc43e81fb1d14003dac1dce4d354499a67e6f"
      },
      {
        "path": "/data2/k6tk/47/4750e84c765544a74dbddeade3ed6a29f7586a1ac769b8a45df78a202e325152.png",
        "sha256": "4750e84c765544a74dbddeade3ed6a29f7586a1ac769b8a45df78a202e325152"
      },
      {
        "path": "/data2/k6tk/06/06035b55835096c725e5bc2acc48f298d55b75a8d2c64d9c9a8845fd0a4f35b3.png",
        "sha256": "06035b55835096c725e5bc2acc48f298d55b75a8d2c64d9c9a8845fd0a4f35b3"
      },
      {
        "path": "/data2/k6tk/73/73e639fa4a8746d45b8de2c169025bd8027e0ceac0b0979531f8ae9e5d579724.png",
        "sha256": "73e639fa4a8746d45b8de2c169025bd8027e0ceac0b0979531f8ae9e5d579724"
      },
      {
        "path": "/data2/k6tk/c5/c50bf945c63c6470ea22496de20bdac2c1d15d555a50184ad0ba38fdc8e4d711.png",
        "sha256": "c50bf945c63c6470ea22496de20bdac2c1d15d555a50184ad0ba38fdc8e4d711"
      },
      {
        "path": "/data2/k6tk/d7/d723732c7f485b19ef6b297aaee2e1d1b5c4387a6ec294b0044d1ccb23761399.png",
        "sha256": "d723732c7f485b19ef6b297aaee2e1d1b5c4387a6ec294b0044d1ccb23761399"
      },
      {
        "path": "/data2/k6tk/55/5563456eae711ce2a1a2a98e23c9568a1f5f9c711d52efc5d9433bf2323dd72d.png",
        "sha256": "5563456eae711ce2a1a2a98e23c9568a1f5f9c711d52efc5d9433bf2323dd72d"
      },
      {
        "path": "/data2/k6tk/0d/0d5c5178b1038a6fd2148aa9787d3ddaeb591e97bae645d69d0aa204a6b1c461.png",
        "sha256": "0d5c5178b1038a6fd2148aa9787d3ddaeb591e97bae645d69d0aa204a6b1c461"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      8.15,
      16.316666666666666,
      24.483333333333334,
      32.65,
      40.81666666666667,
      48.983333333333334,
      57.15,
      65.31666666666666,
      73.48333333333333,
      81.65,
      89.81666666666666,
      97.98333333333333,
      106.15,
      114.31666666666666,
      122.48333333333333,
      130.65,
      138.81666666666666,
      146.98333333333332,
      155.15,
      163.31666666666666,
      171.48333333333332,
      179.65,
      187.81666666666666,
      195.98333333333332,
      204.15,
      212.31666666666666,
      220.48333333333332,
      228.65,
      236.81666666666666,
      244.98333333333332,
      253.15
    ],
    "total_num_frames": 15190
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: cabinet in frame 17; bed in frame 15; wardrobe in frame 16.\nOf these, the bed and the wardrobe are farthest apart, with the cabinet between them.\n</think>\n\n14.97",
  "validation_commit": ""
}
```

## sb_rowLR_5f7f3eb07f9b126b_q1

```json
{
  "answer": "21.72",
  "answer_unit": "m2",
  "benchmark_improvement_claim": false,
  "candidate_id": "ground-d4331ec25e32739f21aeddf7ac1e64cf9db49106b2dd2fda179e1c44c1185a4f",
  "category": "room_size_estimation",
  "count_arity": 2,
  "count_kind": "total",
  "dataset": "d1",
  "form": "direct",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [
    "ScanNet Terms of Use"
  ],
  "pool": "sb_rowLR",
  "provenance": {
    "alias": "d1/v9d30558b21f4",
    "candidate_identity_fields": {
      "frame_indices": [
        0,
        30,
        61,
        92,
        123,
        154,
        185,
        216,
        247,
        278,
        309,
        339,
        370,
        401,
        432,
        463,
        494,
        525,
        556,
        587,
        618,
        648,
        679,
        710,
        741,
        772,
        803,
        834,
        865,
        896,
        927,
        958
      ],
      "options": [],
      "qid": "sb_rowLR_5f7f3eb07f9b126b_q1",
      "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
      "scene": "scannet/scene0204_00",
      "trace_revision": "3.14",
      "type": "room_size_estimation"
    },
    "canonical": "scannet/scene0204_00",
    "details": {
      "cell": "scannet|20-40",
      "question_variant": 1,
      "source_use_cap": 2,
      "unit": "square meters"
    },
    "family": "room",
    "frame_indices": [
      0,
      30,
      61,
      92,
      123,
      154,
      185,
      216,
      247,
      278,
      309,
      339,
      370,
      401,
      432,
      463,
      494,
      525,
      556,
      587,
      618,
      648,
      679,
      710,
      741,
      772,
      803,
      834,
      865,
      896,
      927,
      958
    ],
    "geometry_source": "gt",
    "input_sha256": {
      "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0204_00.npz": "24b9c67850b72620ef550b332cd7a33d70f7de19e7820a2749c9bcc27d253341",
      "/scratch/jjyeung/orch_n30/sb_rowLR/generate.py": "4b5ce2cc685d38bda718020e96f55951e57726f9d32fd8a828798f748bda6aa5",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/PREPARED.json": "60dbb54468ae45495fa4b8675a65f2c0d2aa1812d085c9cb2aaa0514ae4b3cc8",
      "/scratch/jjyeung/orch_n30/sb_rowLR/out/WORDING.json": "3f2600094cc836fa37e81a4443a5e8ff7d9a6072d43e903bce72341249955194"
    },
    "mask_source": "none",
    "physical_group": "scannet/scene0204",
    "room_measurement": {
      "area_m2": 21.722500000000004,
      "cell_m": 0.05,
      "closing_radius_m": 0.2,
      "floor_cells": 8689,
      "floor_height_m": -0.08525364789438267,
      "frames": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32
      ],
      "geometry_mode": "sensor",
      "gravity_source": "scene_z_up",
      "head_raster_hw": [
        240,
        320
      ],
      "height_margin_m": 0.1,
      "height_percentile": 1,
      "max_grid_cells": 4000000,
      "min_frames": 1,
      "min_points": 100,
      "pixel_stride": 4,
      "supported_cells": 8390
    },
    "room_trace": {
      "generator_sha256": "1d4af1a1da322e800fd42ed3a57d6ceb518574020f5403bfdcbc42416fd110d9",
      "landmarks": [
        {
          "best_view": 16,
          "centroid": [
            3.0579366087913513,
            4.503783941268921,
            0.7470705807209015
          ],
          "footprint": 5.905964673803794,
          "instance_id": 13,
          "label": "table",
          "pixel_share": 0.7433984375
        },
        {
          "best_view": 30,
          "centroid": [
            3.759705066680908,
            1.6956878304481506,
            0.4651072658598423
          ],
          "footprint": 2.0932779444353855,
          "instance_id": 0,
          "label": "cabinet",
          "pixel_share": 0.35682291666666666
        },
        {
          "best_view": 20,
          "centroid": [
            4.458754897117615,
            6.277498722076416,
            1.108904480934143
          ],
          "footprint": 1.223378572925185,
          "instance_id": 14,
          "label": "blackboard",
          "pixel_share": 0.1020703125
        }
      ],
      "raster_path": "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0204_00.npz",
      "raster_sha256": "24b9c67850b72620ef550b332cd7a33d70f7de19e7820a2749c9bcc27d253341",
      "reference_generator_sha256": "60d72434c627b0452cb884a773a9fa693eb8731cfc1f26c1e7bbba9d2c10bb5c",
      "relate": {
        "decision": "between",
        "horizontal_axes": [
          0,
          1
        ],
        "horizontal_centroids": [
          [
            3.0579366087913513,
            4.503783941268921
          ],
          [
            3.759705066680908,
            1.6956878304481506
          ],
          [
            4.458754897117615,
            6.277498722076416
          ]
        ],
        "pair": [
          1,
          2
        ],
        "perpendicular_distance": 1.1172724689423787,
        "projection": 0.5761004148411152,
        "rule": "farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length",
        "segment_length": 4.63483135745811,
        "third": 0
      },
      "up_axis": 2,
      "wording": {
        "locate": "best_view",
        "relate": 0
      }
    },
    "source_qid": "b12ct_666cdfeb6db519f9685d5812",
    "source_row_sha256": "7bf53fd007810aa6cc220a2a39f4813e9c01dc4df271cb20cf284dbf0860c9d9",
    "source_store_sha256": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
  },
  "qid": "sb_rowLR_5f7f3eb07f9b126b_q1",
  "question_type": "room_size_estimation",
  "result_status": "verified traced room; candidate for intake",
  "scene": "v9d30558b21f4",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      30,
      61,
      92,
      123,
      154,
      185,
      216,
      247,
      278,
      309,
      339,
      370,
      401,
      432,
      463,
      494,
      525,
      556,
      587,
      618,
      648,
      679,
      710,
      741,
      772,
      803,
      834,
      865,
      896,
      927,
      958
    ],
    "frames": [
      {
        "path": "/data2/k6tk/d4/d469deaf683a940e70bb501df5269b149f6873fd169536b12694bcc5827afbbe.png",
        "sha256": "d469deaf683a940e70bb501df5269b149f6873fd169536b12694bcc5827afbbe"
      },
      {
        "path": "/data2/k6tk/88/888e2e33b8c3793006c41873b1bdae445a9f078c0e049ef57d29fe7cea0e3343.png",
        "sha256": "888e2e33b8c3793006c41873b1bdae445a9f078c0e049ef57d29fe7cea0e3343"
      },
      {
        "path": "/data2/k6tk/c4/c4b3606de362765c91da73e6ef28f8aee22657788cb981a3d52992eed82c8c25.png",
        "sha256": "c4b3606de362765c91da73e6ef28f8aee22657788cb981a3d52992eed82c8c25"
      },
      {
        "path": "/data2/k6tk/4b/4bac8f4f12c07f6463bf9fd776bebec4f0a13aa9dac151bd12a56dd040b52ef6.png",
        "sha256": "4bac8f4f12c07f6463bf9fd776bebec4f0a13aa9dac151bd12a56dd040b52ef6"
      },
      {
        "path": "/data2/k6tk/e9/e98bc0fd2cfa815ccfc78212eefd4979dac5575dadd5b2fb30c988e353bd14d2.png",
        "sha256": "e98bc0fd2cfa815ccfc78212eefd4979dac5575dadd5b2fb30c988e353bd14d2"
      },
      {
        "path": "/data2/k6tk/1e/1eec7aec2c708cf95d9296f136ad573d07a53f38428da4aa79cc19feb82d3247.png",
        "sha256": "1eec7aec2c708cf95d9296f136ad573d07a53f38428da4aa79cc19feb82d3247"
      },
      {
        "path": "/data2/k6tk/10/10ee673c112ad18a198795979e9c8b651c9c5039c8341f7e8263216b09121e00.png",
        "sha256": "10ee673c112ad18a198795979e9c8b651c9c5039c8341f7e8263216b09121e00"
      },
      {
        "path": "/data2/k6tk/30/3089362561f8a12c039bc04ab24fa89e3356e2466dd11211601ed6eedcbe4e55.png",
        "sha256": "3089362561f8a12c039bc04ab24fa89e3356e2466dd11211601ed6eedcbe4e55"
      },
      {
        "path": "/data2/k6tk/fd/fd9ef6a7eb32b311a40c4e416256f7f90db3cf1c423d17fa4aabb4a49ed5d989.png",
        "sha256": "fd9ef6a7eb32b311a40c4e416256f7f90db3cf1c423d17fa4aabb4a49ed5d989"
      },
      {
        "path": "/data2/k6tk/5e/5e5ef0354e3913883b0c7a0273531af2134a4a3ebc2aca0a95a50696e7348df5.png",
        "sha256": "5e5ef0354e3913883b0c7a0273531af2134a4a3ebc2aca0a95a50696e7348df5"
      },
      {
        "path": "/data2/k6tk/96/96d2ccd501b54a78f44c263b189a7477f68785e7201e3fa0fb7e63fe536c9d57.png",
        "sha256": "96d2ccd501b54a78f44c263b189a7477f68785e7201e3fa0fb7e63fe536c9d57"
      },
      {
        "path": "/data2/k6tk/51/51f2453b518fbabeba217b7e4c606b96b63f373981b4cfdcca691fa20230e7ef.png",
        "sha256": "51f2453b518fbabeba217b7e4c606b96b63f373981b4cfdcca691fa20230e7ef"
      },
      {
        "path": "/data2/k6tk/3a/3a69b5107c94c502b1916548657d61ce0c28e11a92db4d410c8fa4e5b2865700.png",
        "sha256": "3a69b5107c94c502b1916548657d61ce0c28e11a92db4d410c8fa4e5b2865700"
      },
      {
        "path": "/data2/k6tk/27/271afaf516de2c52dec7dd2614e693b027a9cac3a155fb01224869a92adbeb42.png",
        "sha256": "271afaf516de2c52dec7dd2614e693b027a9cac3a155fb01224869a92adbeb42"
      },
      {
        "path": "/data2/k6tk/33/33f6a16e4fd80c5e8a9bb50ec0dd926ad9190ffdceb07b39b5ab963fa611be06.png",
        "sha256": "33f6a16e4fd80c5e8a9bb50ec0dd926ad9190ffdceb07b39b5ab963fa611be06"
      },
      {
        "path": "/data2/k6tk/de/de8c1292aac54adcda10db1b3ece84ab5f28c445980b498acf3f08a699d99cc7.png",
        "sha256": "de8c1292aac54adcda10db1b3ece84ab5f28c445980b498acf3f08a699d99cc7"
      },
      {
        "path": "/data2/k6tk/f2/f22e1e8e9e03cf5823bf83e372d32fe9f7ffdcf2be4769328b30844eb1ac0b70.png",
        "sha256": "f22e1e8e9e03cf5823bf83e372d32fe9f7ffdcf2be4769328b30844eb1ac0b70"
      },
      {
        "path": "/data2/k6tk/c2/c213c656c707a405959e0c83275eeaaf563057717297f1f385375abbb19339f7.png",
        "sha256": "c213c656c707a405959e0c83275eeaaf563057717297f1f385375abbb19339f7"
      },
      {
        "path": "/data2/k6tk/43/430892e15441c8461f05173824c72011b7d69a2dc79916dffe14d658c25840ed.png",
        "sha256": "430892e15441c8461f05173824c72011b7d69a2dc79916dffe14d658c25840ed"
      },
      {
        "path": "/data2/k6tk/63/638575c7f76a96263ac0125d9a84da11e2cb6467664fc04966e80fb357f7c31b.png",
        "sha256": "638575c7f76a96263ac0125d9a84da11e2cb6467664fc04966e80fb357f7c31b"
      },
      {
        "path": "/data2/k6tk/17/17ed9d35b7d7b2e68708f1d124b30012f797e52501d1eeecb4a3602503c17f80.png",
        "sha256": "17ed9d35b7d7b2e68708f1d124b30012f797e52501d1eeecb4a3602503c17f80"
      },
      {
        "path": "/data2/k6tk/a6/a69e7f474def3da4d1ce9d8a87de2c10090b3cb9ad2e269b7039d19dfcd1f327.png",
        "sha256": "a69e7f474def3da4d1ce9d8a87de2c10090b3cb9ad2e269b7039d19dfcd1f327"
      },
      {
        "path": "/data2/k6tk/5c/5cde49d427834574e10e886da2e016188e234058f71a0693f611b1aba944d0c4.png",
        "sha256": "5cde49d427834574e10e886da2e016188e234058f71a0693f611b1aba944d0c4"
      },
      {
        "path": "/data2/k6tk/d7/d7dad01565175a5b4654ea68938e29fc0f9ec1ebd45e3d19d25603bd65b8e769.png",
        "sha256": "d7dad01565175a5b4654ea68938e29fc0f9ec1ebd45e3d19d25603bd65b8e769"
      },
      {
        "path": "/data2/k6tk/d9/d9dad3f3e3c8df5073882866c471297d1e55ee355dc0b0f7e442cbdf43c5f45c.png",
        "sha256": "d9dad3f3e3c8df5073882866c471297d1e55ee355dc0b0f7e442cbdf43c5f45c"
      },
      {
        "path": "/data2/k6tk/5f/5f3e4df7e9fcf1746fb19cb57c2069ba606bbace402af72335557f0adc186caf.png",
        "sha256": "5f3e4df7e9fcf1746fb19cb57c2069ba606bbace402af72335557f0adc186caf"
      },
      {
        "path": "/data2/k6tk/2c/2ca359eefac82d8c5fe6940b889abe57e46ba191b1736db9001a228e58971f6a.png",
        "sha256": "2ca359eefac82d8c5fe6940b889abe57e46ba191b1736db9001a228e58971f6a"
      },
      {
        "path": "/data2/k6tk/8a/8a6b856186294cea4b500de7029098800235557881abb92919ae3165f4042bd5.png",
        "sha256": "8a6b856186294cea4b500de7029098800235557881abb92919ae3165f4042bd5"
      },
      {
        "path": "/data2/k6tk/dc/dce49cbdb90c930bc8ed9de7f20eb12b59e6f548b1e8a2eee1a6f45b0f0180a2.png",
        "sha256": "dce49cbdb90c930bc8ed9de7f20eb12b59e6f548b1e8a2eee1a6f45b0f0180a2"
      },
      {
        "path": "/data2/k6tk/45/459bb73af49696a91175d66a10e514525baa184bf9be2944d6cfaee322aac1db.png",
        "sha256": "459bb73af49696a91175d66a10e514525baa184bf9be2944d6cfaee322aac1db"
      },
      {
        "path": "/data2/k6tk/2b/2bf5dc60b928dd7116e227f04e2c13b9d057f6fedee6a4f99ac6fb2e33caef83.png",
        "sha256": "2bf5dc60b928dd7116e227f04e2c13b9d057f6fedee6a4f99ac6fb2e33caef83"
      },
      {
        "path": "/data2/k6tk/a3/a36a87e88a1f6ee74ea7dd7b2ff375a6bb52918c220d15044c450fe4ade7c1a9.png",
        "sha256": "a36a87e88a1f6ee74ea7dd7b2ff375a6bb52918c220d15044c450fe4ade7c1a9"
      }
    ],
    "options": [],
    "question": "How many square meters of floor space do the areas visited in this video cover altogether?",
    "timestamps": [
      0.0,
      1.25,
      2.5416666666666665,
      3.8333333333333335,
      5.125,
      6.416666666666667,
      7.708333333333333,
      9.0,
      10.291666666666666,
      11.583333333333334,
      12.875,
      14.125,
      15.416666666666666,
      16.708333333333332,
      18.0,
      19.291666666666668,
      20.583333333333332,
      21.875,
      23.166666666666668,
      24.458333333333332,
      25.75,
      27.0,
      28.291666666666668,
      29.583333333333332,
      30.875,
      32.166666666666664,
      33.458333333333336,
      34.75,
      36.041666666666664,
      37.333333333333336,
      38.625,
      39.916666666666664
    ],
    "total_num_frames": 959
  },
  "target": "<think>\nThe question asks for the combined floor area in square meters.\nSeen: table in frame 16; cabinet in frame 30; blackboard in frame 20.\nOf these, the cabinet and the blackboard are farthest apart, with the table between them.\n</think>\n\n21.72",
  "validation_commit": ""
}
```

