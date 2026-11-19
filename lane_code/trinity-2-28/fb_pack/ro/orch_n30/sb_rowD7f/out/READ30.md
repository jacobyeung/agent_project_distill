Thirty complete filtered sb_rowD7f rows, five per answer cell (selection: sha256("READ30|"+qid) order).

## 1. q86394f0ef11421455d4479f4-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-620d0bc22b7635908619beefe3f33e1656052a91782d51065299d36b6a9f53a6",
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q86394f0ef11421455d4479f4-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q86394f0ef11421455d4479f4",
  "paraphrase_template": "easy_side",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 44,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "looking at",
        "start": 34
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "right",
      "source_qid": "q86394f0ef11421455d4479f4-p1",
      "source_row_sha256": "2604545d87fc677d3feaabc4f4e82653a56bc2ff3a494695681010615eecfea2",
      "source_store_i": 65038
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q86394f0ef11421455d4479f4-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "2302e6f9a2b756ace61e375964c603687d4ca98bc7811baff04dfa2e99d8613d"
  },
  "scene": "vd6e3d09bbe7b",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      16,
      32,
      48,
      64,
      80,
      96,
      112,
      128,
      144,
      160,
      176,
      192,
      208,
      224,
      240,
      256,
      272,
      288,
      304,
      320,
      336,
      352,
      368,
      384,
      400,
      416,
      432,
      448,
      464,
      480,
      497
    ],
    "frames": [
      {
        "path": "/data2/k6tk/91/910ff68916004bcafc88eb32027082731a421bd76e67559d857eab9568dc41de.png",
        "sha256": "910ff68916004bcafc88eb32027082731a421bd76e67559d857eab9568dc41de"
      },
      {
        "path": "/data2/k6tk/3b/3b84281e4a637383f4ebc9a08cf37e09d8db2bda9f29215d596e3058ef069325.png",
        "sha256": "3b84281e4a637383f4ebc9a08cf37e09d8db2bda9f29215d596e3058ef069325"
      },
      {
        "path": "/data2/k6tk/73/733357286a9b25d5458d362f1e6c5ab4fd9a4b27a0b20feea61ece21e2899b8f.png",
        "sha256": "733357286a9b25d5458d362f1e6c5ab4fd9a4b27a0b20feea61ece21e2899b8f"
      },
      {
        "path": "/data2/k6tk/b6/b6acb2e4b7fcac083c0c942de9d15da02cabd5d0df018f862fad1ec911ff75d0.png",
        "sha256": "b6acb2e4b7fcac083c0c942de9d15da02cabd5d0df018f862fad1ec911ff75d0"
      },
      {
        "path": "/data2/k6tk/be/bec6b4439b4deb0eeec2e4d038c7e4588b88838a9be4cd9d6c0bae0cb50b103f.png",
        "sha256": "bec6b4439b4deb0eeec2e4d038c7e4588b88838a9be4cd9d6c0bae0cb50b103f"
      },
      {
        "path": "/data2/k6tk/37/37cec047d43284e11ee1ea446ed028c51b6abd893247b405e4fc1b1c8152de5f.png",
        "sha256": "37cec047d43284e11ee1ea446ed028c51b6abd893247b405e4fc1b1c8152de5f"
      },
      {
        "path": "/data2/k6tk/eb/ebb7781dcc3f497093a5ed134e06d0f5ac387b9fe7b366ed3c94ff2ca9723fc2.png",
        "sha256": "ebb7781dcc3f497093a5ed134e06d0f5ac387b9fe7b366ed3c94ff2ca9723fc2"
      },
      {
        "path": "/data2/k6tk/24/242e01abb18fe4ed53c81a644347bc15f02f652578aff660094498dd49751ae0.png",
        "sha256": "242e01abb18fe4ed53c81a644347bc15f02f652578aff660094498dd49751ae0"
      },
      {
        "path": "/data2/k6tk/27/274bcfec6b2b2985abd20163c6efd27a1fe9a76a2329154cdf8a321ac31d3ee9.png",
        "sha256": "274bcfec6b2b2985abd20163c6efd27a1fe9a76a2329154cdf8a321ac31d3ee9"
      },
      {
        "path": "/data2/k6tk/58/589b8bdf57a1cd6eeecf88a2c86a821525219e450a49e185b63229371b139e8e.png",
        "sha256": "589b8bdf57a1cd6eeecf88a2c86a821525219e450a49e185b63229371b139e8e"
      },
      {
        "path": "/data2/k6tk/33/3304bacea4e6587fdc543d6689854b78c8f12a80b6543a6f4295a7ebe06ba7ac.png",
        "sha256": "3304bacea4e6587fdc543d6689854b78c8f12a80b6543a6f4295a7ebe06ba7ac"
      },
      {
        "path": "/data2/k6tk/70/702a5a6f548d0f7e9fac11bc9fc81c956eb45763ee656cb2b299bdfe5768bc9b.png",
        "sha256": "702a5a6f548d0f7e9fac11bc9fc81c956eb45763ee656cb2b299bdfe5768bc9b"
      },
      {
        "path": "/data2/k6tk/67/675df9db4695fc1d1ed28825d59ec9b19b4c7012628047b7ad2046765a47e40e.png",
        "sha256": "675df9db4695fc1d1ed28825d59ec9b19b4c7012628047b7ad2046765a47e40e"
      },
      {
        "path": "/data2/k6tk/de/de45b4b1aee5ee9e2a8b34346a3d9662720848ea99ada36040b51ad8b512024f.png",
        "sha256": "de45b4b1aee5ee9e2a8b34346a3d9662720848ea99ada36040b51ad8b512024f"
      },
      {
        "path": "/data2/k6tk/0d/0dedd8c7b8826ce6b5d52519b3cec458150a7d1e476f9ddb88f7fdd3ed02112c.png",
        "sha256": "0dedd8c7b8826ce6b5d52519b3cec458150a7d1e476f9ddb88f7fdd3ed02112c"
      },
      {
        "path": "/data2/k6tk/4c/4c9042144815c132cb38b3bb7be1be3e60296c1a3b63a64cdbd97c2ad80c78f3.png",
        "sha256": "4c9042144815c132cb38b3bb7be1be3e60296c1a3b63a64cdbd97c2ad80c78f3"
      },
      {
        "path": "/data2/k6tk/0c/0c4765da5fb70fd13cb0009e053ce5089f135e451564fbb69a6384083640da5c.png",
        "sha256": "0c4765da5fb70fd13cb0009e053ce5089f135e451564fbb69a6384083640da5c"
      },
      {
        "path": "/data2/k6tk/bc/bcfc5803b70f12cddcb7482180688fce6faba3e8d6d9ff5da6b1f578c135c6b4.png",
        "sha256": "bcfc5803b70f12cddcb7482180688fce6faba3e8d6d9ff5da6b1f578c135c6b4"
      },
      {
        "path": "/data2/k6tk/2d/2d06e58a9bd4c1949cb00cf0463e4c8842992647a261c0c5f0f92e9b751446b6.png",
        "sha256": "2d06e58a9bd4c1949cb00cf0463e4c8842992647a261c0c5f0f92e9b751446b6"
      },
      {
        "path": "/data2/k6tk/bc/bc91fe3c8f5a1787fb8cb5201a2ccd2e477ddfed4d26050a1c1e66e10b8dd972.png",
        "sha256": "bc91fe3c8f5a1787fb8cb5201a2ccd2e477ddfed4d26050a1c1e66e10b8dd972"
      },
      {
        "path": "/data2/k6tk/01/01f92f170fe62a3841f22c2b8c5691b94a01825bc4f90a8bc0642afd2d6be107.png",
        "sha256": "01f92f170fe62a3841f22c2b8c5691b94a01825bc4f90a8bc0642afd2d6be107"
      },
      {
        "path": "/data2/k6tk/7c/7c567e3a6995fb5a65879d9a330ee6e00701094d5c6db3f03d1e276fdb3c2479.png",
        "sha256": "7c567e3a6995fb5a65879d9a330ee6e00701094d5c6db3f03d1e276fdb3c2479"
      },
      {
        "path": "/data2/k6tk/2e/2e8c84f3c06febf6c6a53c8e959fde81568d76ebee6249f07e7886a1c4b111ba.png",
        "sha256": "2e8c84f3c06febf6c6a53c8e959fde81568d76ebee6249f07e7886a1c4b111ba"
      },
      {
        "path": "/data2/k6tk/b1/b1a336ce2864a7b9f50c1e48c36d44f33f947d303d08f5b66b0c5f9c3a60de0c.png",
        "sha256": "b1a336ce2864a7b9f50c1e48c36d44f33f947d303d08f5b66b0c5f9c3a60de0c"
      },
      {
        "path": "/data2/k6tk/27/27dc1ecc9344f80416175f724e0dd73aac64c00178ba8933d0763dc99b7140bb.png",
        "sha256": "27dc1ecc9344f80416175f724e0dd73aac64c00178ba8933d0763dc99b7140bb"
      },
      {
        "path": "/data2/k6tk/10/10a888e5af12c66a6e669fa4bee73944c7b106b0cbae320647d9bf7261f1f7bd.png",
        "sha256": "10a888e5af12c66a6e669fa4bee73944c7b106b0cbae320647d9bf7261f1f7bd"
      },
      {
        "path": "/data2/k6tk/3c/3c112b5e7a6757588d1c893b14d2b500cb8e9706307ed1997f063a1b2f90e183.png",
        "sha256": "3c112b5e7a6757588d1c893b14d2b500cb8e9706307ed1997f063a1b2f90e183"
      },
      {
        "path": "/data2/k6tk/94/94ea110ae78e483ea6484b46d3da587d6d1b39aaf901544654740ccd5256124a.png",
        "sha256": "94ea110ae78e483ea6484b46d3da587d6d1b39aaf901544654740ccd5256124a"
      },
      {
        "path": "/data2/k6tk/f0/f015e204bc06521827f86acc14dbe54936d38f270860d557690727418c15de81.png",
        "sha256": "f015e204bc06521827f86acc14dbe54936d38f270860d557690727418c15de81"
      },
      {
        "path": "/data2/k6tk/ce/ce5c04301c6a4f1b8bab7e9c4e18f19cd7184367e9db3d6a1b27f5122e036d52.png",
        "sha256": "ce5c04301c6a4f1b8bab7e9c4e18f19cd7184367e9db3d6a1b27f5122e036d52"
      },
      {
        "path": "/data2/k6tk/78/780efa49f2d9bde4ae560c508b1589f4deb1a7dc015c18ad664825d1c7d1be3d.png",
        "sha256": "780efa49f2d9bde4ae560c508b1589f4deb1a7dc015c18ad664825d1c7d1be3d"
      },
      {
        "path": "/data2/k6tk/0c/0ca5e02feb820d4a3f9e0233e903b4dbed5ac90e94c7246bb865a3b9460a2f4a.png",
        "sha256": "0ca5e02feb820d4a3f9e0233e903b4dbed5ac90e94c7246bb865a3b9460a2f4a"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "While standing by the curtain and facing away from the bed, decide whether the nightstand lies to your left or your right.",
    "timestamps": [
      0.0,
      0.6666666666666666,
      1.3333333333333333,
      2.0,
      2.6666666666666665,
      3.3333333333333335,
      4.0,
      4.666666666666667,
      5.333333333333333,
      6.0,
      6.666666666666667,
      7.333333333333333,
      8.0,
      8.666666666666666,
      9.333333333333334,
      10.0,
      10.666666666666666,
      11.333333333333334,
      12.0,
      12.666666666666666,
      13.333333333333334,
      14.0,
      14.666666666666666,
      15.333333333333334,
      16.0,
      16.666666666666668,
      17.333333333333332,
      18.0,
      18.666666666666668,
      19.333333333333332,
      20.0,
      20.708333333333332
    ],
    "total_num_frames": 498
  },
  "target": "<think>\nStep 1: find the curtain and the bed, then the nightstand.\nStep 2: I find the nightstand to my right when I stand at the curtain facing the bed.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the nightstand to my left.\n</think>\n\nA",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 2. qe53906fdd58db6181188c86e_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-5f7f343815e14a901e8ed42b3be5661ef2f5408bb1806868d035431ed67bae01",
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qe53906fdd58db6181188c86e"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 38,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 32
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "right",
      "source_qid": "qe53906fdd58db6181188c86e",
      "source_row_sha256": "b4ce71c3f6025ab0cff48ee61c50787accd0b529c2d2e42167dd879c5c3fe1ff",
      "source_store_i": 16363
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qe53906fdd58db6181188c86e_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "560aa7d419d2cc3445fc30ee84d3034e192b8ba7ff73ef1d6e70a683c9278848"
  },
  "scene": "v4c3ecbf3977d",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      177,
      354,
      531,
      708,
      885,
      1062,
      1239,
      1417,
      1594,
      1771,
      1948,
      2125,
      2302,
      2479,
      2656,
      2834,
      3011,
      3188,
      3365,
      3542,
      3719,
      3896,
      4073,
      4251,
      4428,
      4605,
      4782,
      4959,
      5136,
      5313,
      5491
    ],
    "frames": [
      {
        "path": "/data2/k6tk/74/7412b34898948ef961aee855e89470c698b34220166eb5f2a8af4ab38ab04445.png",
        "sha256": "7412b34898948ef961aee855e89470c698b34220166eb5f2a8af4ab38ab04445"
      },
      {
        "path": "/data2/k6tk/68/6806adaad1c5ae715ad0fcfb22e34fe3a6187b9b115342686b3c6344e9bcab29.png",
        "sha256": "6806adaad1c5ae715ad0fcfb22e34fe3a6187b9b115342686b3c6344e9bcab29"
      },
      {
        "path": "/data2/k6tk/35/35f9dc9838f4729f17f214cdfa5fa2cba3c5012925e92a024e3d7beec82b9e23.png",
        "sha256": "35f9dc9838f4729f17f214cdfa5fa2cba3c5012925e92a024e3d7beec82b9e23"
      },
      {
        "path": "/data2/k6tk/eb/eba15971e34c047dc369f488066d66ed3fa8d1c30eb366ffea1835f0dd2e851e.png",
        "sha256": "eba15971e34c047dc369f488066d66ed3fa8d1c30eb366ffea1835f0dd2e851e"
      },
      {
        "path": "/data2/k6tk/9c/9cb988cb8e7d99fa9e06adf7f41f0f44f1cfdf0f567e0e941b79b1ebf6de7871.png",
        "sha256": "9cb988cb8e7d99fa9e06adf7f41f0f44f1cfdf0f567e0e941b79b1ebf6de7871"
      },
      {
        "path": "/data2/k6tk/a6/a6986e0b0dff94357635fbea701fa1b7dd126d3a3e3e3a7392250351d3d85dda.png",
        "sha256": "a6986e0b0dff94357635fbea701fa1b7dd126d3a3e3e3a7392250351d3d85dda"
      },
      {
        "path": "/data2/k6tk/fe/fe1e506197cb6bbdfa9598972cc6fca88856ff3df226b4ce49c7496ce810e401.png",
        "sha256": "fe1e506197cb6bbdfa9598972cc6fca88856ff3df226b4ce49c7496ce810e401"
      },
      {
        "path": "/data2/k6tk/9d/9db3324cfea3eb458d7414f75e8adbfe637507adc3b3ec2fb0944d561ed9601a.png",
        "sha256": "9db3324cfea3eb458d7414f75e8adbfe637507adc3b3ec2fb0944d561ed9601a"
      },
      {
        "path": "/data2/k6tk/c9/c9942ee3601f9b8c87c1fa255f81a60aa1c7c9972d01e601b374f93b88abe55d.png",
        "sha256": "c9942ee3601f9b8c87c1fa255f81a60aa1c7c9972d01e601b374f93b88abe55d"
      },
      {
        "path": "/data2/k6tk/4f/4f477df9999bdcb15703a5f1287447551ce660acd6ef6499dae8fc69cb87b834.png",
        "sha256": "4f477df9999bdcb15703a5f1287447551ce660acd6ef6499dae8fc69cb87b834"
      },
      {
        "path": "/data2/k6tk/aa/aa04fc5bc69130dd7e439c5fb5a2c187b1cbd9249383ce2226478139b6a6a544.png",
        "sha256": "aa04fc5bc69130dd7e439c5fb5a2c187b1cbd9249383ce2226478139b6a6a544"
      },
      {
        "path": "/data2/k6tk/0e/0e06e9f8d962494d60500919fed19cfb2a96bf6f2a6148ea1d0e9d9e5e87f133.png",
        "sha256": "0e06e9f8d962494d60500919fed19cfb2a96bf6f2a6148ea1d0e9d9e5e87f133"
      },
      {
        "path": "/data2/k6tk/36/36e4b2260c19749b9519e7f9bae1ff8467c2c327e2815f500d31ba5d6253f9c5.png",
        "sha256": "36e4b2260c19749b9519e7f9bae1ff8467c2c327e2815f500d31ba5d6253f9c5"
      },
      {
        "path": "/data2/k6tk/65/6578a8ecf7cc4b703b1757cbdb487a90264bbd2505bcb797db6be19ff4621d47.png",
        "sha256": "6578a8ecf7cc4b703b1757cbdb487a90264bbd2505bcb797db6be19ff4621d47"
      },
      {
        "path": "/data2/k6tk/6f/6f0a2e8545dd3a6f1730ff761af5c95a8e24562a9cbaea5146680473310f133f.png",
        "sha256": "6f0a2e8545dd3a6f1730ff761af5c95a8e24562a9cbaea5146680473310f133f"
      },
      {
        "path": "/data2/k6tk/ce/ce08a2a1a13455c47a113cc7a8cd6da33c701305825a61251390bb6b0d406869.png",
        "sha256": "ce08a2a1a13455c47a113cc7a8cd6da33c701305825a61251390bb6b0d406869"
      },
      {
        "path": "/data2/k6tk/0e/0e98e15c02c512be8200a3f801a739de1141388d48ba95f364da3f4b9fbb1974.png",
        "sha256": "0e98e15c02c512be8200a3f801a739de1141388d48ba95f364da3f4b9fbb1974"
      },
      {
        "path": "/data2/k6tk/19/199bd1996a0a5512458395cd7b2d70f142c1606256d3db4093d7e16604a0d306.png",
        "sha256": "199bd1996a0a5512458395cd7b2d70f142c1606256d3db4093d7e16604a0d306"
      },
      {
        "path": "/data2/k6tk/6f/6f4c51571eed384dce93af92c7803b12355772b7a8df84d6a388176d2a1614b4.png",
        "sha256": "6f4c51571eed384dce93af92c7803b12355772b7a8df84d6a388176d2a1614b4"
      },
      {
        "path": "/data2/k6tk/80/80d58ab28c9abe88aeb8206da29d2cede5b5cccfb1e947ae640c7c6eaa9fea68.png",
        "sha256": "80d58ab28c9abe88aeb8206da29d2cede5b5cccfb1e947ae640c7c6eaa9fea68"
      },
      {
        "path": "/data2/k6tk/03/0347a264407e492a8f8a0ea50392e14c7b5616c3d58079785ca3932fc4f22609.png",
        "sha256": "0347a264407e492a8f8a0ea50392e14c7b5616c3d58079785ca3932fc4f22609"
      },
      {
        "path": "/data2/k6tk/0b/0b057744bd9c46dfa1f4943a4aab338ea78fc30082b6ccce326ffe1f996eeb51.png",
        "sha256": "0b057744bd9c46dfa1f4943a4aab338ea78fc30082b6ccce326ffe1f996eeb51"
      },
      {
        "path": "/data2/k6tk/16/161707eb5cb03efad8022d03c52142c60064c92bb8eb6cb9cf6223569e25d93c.png",
        "sha256": "161707eb5cb03efad8022d03c52142c60064c92bb8eb6cb9cf6223569e25d93c"
      },
      {
        "path": "/data2/k6tk/20/20c4f6cceec2bb881e74ada1facf2da2a358b8670102c6be8619c92d0ecdd6a2.png",
        "sha256": "20c4f6cceec2bb881e74ada1facf2da2a358b8670102c6be8619c92d0ecdd6a2"
      },
      {
        "path": "/data2/k6tk/91/91296e17da33ad26a5b698833cbcde4f5d19c984218faed4fcad2c3371234dc1.png",
        "sha256": "91296e17da33ad26a5b698833cbcde4f5d19c984218faed4fcad2c3371234dc1"
      },
      {
        "path": "/data2/k6tk/e3/e3da8176e891633ba0225a0e3edbd9cc8ae76031a8b9774e577b8c00ec827f6c.png",
        "sha256": "e3da8176e891633ba0225a0e3edbd9cc8ae76031a8b9774e577b8c00ec827f6c"
      },
      {
        "path": "/data2/k6tk/dc/dc89a4bace2413265895d8df61373f3444e85ed3a1c68ee56eaf3cf86b33b535.png",
        "sha256": "dc89a4bace2413265895d8df61373f3444e85ed3a1c68ee56eaf3cf86b33b535"
      },
      {
        "path": "/data2/k6tk/f6/f65339af9ad51f5c5f4144edfc17b4f60f62e436405bbb5f2c979f3e5eb47003.png",
        "sha256": "f65339af9ad51f5c5f4144edfc17b4f60f62e436405bbb5f2c979f3e5eb47003"
      },
      {
        "path": "/data2/k6tk/c2/c2d1f2904464af48ed9576134fdbd8fc087617dc42d1d7316730a4de193ce6df.png",
        "sha256": "c2d1f2904464af48ed9576134fdbd8fc087617dc42d1d7316730a4de193ce6df"
      },
      {
        "path": "/data2/k6tk/38/38fe5955dd4cb7bc70f0f0cd8ef50863ebc0859856ccd85eac6e349372bb4734.png",
        "sha256": "38fe5955dd4cb7bc70f0f0cd8ef50863ebc0859856ccd85eac6e349372bb4734"
      },
      {
        "path": "/data2/k6tk/67/6759c0a779b3db66e234357d976eba0e26e631299746cdac971e018fa8f46a94.png",
        "sha256": "6759c0a779b3db66e234357d976eba0e26e631299746cdac971e018fa8f46a94"
      },
      {
        "path": "/data2/k6tk/83/833b24e3cf7fbc591537cbedc31e1aeda30014bd69236a6ccbcb9bcf482ad8e3.png",
        "sha256": "833b24e3cf7fbc591537cbedc31e1aeda30014bd69236a6ccbcb9bcf482ad8e3"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the bed and facing away from the bedpost, is the bedside lamp to the left or the right of the bedpost?",
    "timestamps": [
      0.0,
      2.95,
      5.9,
      8.85,
      11.8,
      14.75,
      17.7,
      20.65,
      23.616666666666667,
      26.566666666666666,
      29.516666666666666,
      32.46666666666667,
      35.416666666666664,
      38.36666666666667,
      41.31666666666667,
      44.266666666666666,
      47.233333333333334,
      50.18333333333333,
      53.13333333333333,
      56.083333333333336,
      59.03333333333333,
      61.983333333333334,
      64.93333333333334,
      67.88333333333334,
      70.85,
      73.8,
      76.75,
      79.7,
      82.65,
      85.6,
      88.55,
      91.51666666666667
    ],
    "total_num_frames": 5492
  },
  "target": "<think>\nStep 1: find the bed and the bedpost, then the bedside lamp.\nStep 2: standing at the bed and facing the bedpost, I find the bedside lamp to my right.\nStep 3: I face away from the bedpost by making a half turn. Front and back swap, and left and right swap.\nSo I find the bedside lamp to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 3. q0b64563670f8ff5840c45d0c_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-394521be761227cf86362f82d472c4d00e66fe4d177ab5ccaf5ebc2e6e4809df",
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q0b64563670f8ff5840c45d0c"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 48,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "looking at",
        "start": 38
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "right",
      "source_qid": "q0b64563670f8ff5840c45d0c",
      "source_row_sha256": "5b840e00530b02576beb0fc09176a62a6eae97f029b09e41836115518dbf0d85",
      "source_store_i": 19888
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q0b64563670f8ff5840c45d0c_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "4d7b97a70ad97ac24ae1d78819c0ccecd304d524377576baeddd484273fd4615"
  },
  "scene": "v8384d6ab39b5",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      44,
      88,
      132,
      176,
      220,
      264,
      309,
      353,
      397,
      441,
      485,
      529,
      574,
      618,
      662,
      706,
      750,
      794,
      839,
      883,
      927,
      971,
      1015,
      1059,
      1104,
      1148,
      1192,
      1236,
      1280,
      1324,
      1369
    ],
    "frames": [
      {
        "path": "/data2/k6tk/95/9560c6dad70c0007b16c86c8117766f2fef83e75b392a49177c844f73ff98ecd.png",
        "sha256": "9560c6dad70c0007b16c86c8117766f2fef83e75b392a49177c844f73ff98ecd"
      },
      {
        "path": "/data2/k6tk/de/de53e94461c28d12bec8b5cad9384955889865647ecd4724b9c0739be985f666.png",
        "sha256": "de53e94461c28d12bec8b5cad9384955889865647ecd4724b9c0739be985f666"
      },
      {
        "path": "/data2/k6tk/9b/9bf736afbf4b009f521a53865667baf0a1bfb3ffbc4744953cce0ff3862fe384.png",
        "sha256": "9bf736afbf4b009f521a53865667baf0a1bfb3ffbc4744953cce0ff3862fe384"
      },
      {
        "path": "/data2/k6tk/28/28fa88f556ad6fa509ca422497cae104ee1595d0cdb4d7ab715c0b4d01510012.png",
        "sha256": "28fa88f556ad6fa509ca422497cae104ee1595d0cdb4d7ab715c0b4d01510012"
      },
      {
        "path": "/data2/k6tk/3f/3f3f9355720ba3f9e6b108f73f8b3c87b27c458006a5928fb4dcaedb63ed09b3.png",
        "sha256": "3f3f9355720ba3f9e6b108f73f8b3c87b27c458006a5928fb4dcaedb63ed09b3"
      },
      {
        "path": "/data2/k6tk/7b/7b23f70fc53017314878dd4d4ec663a7a23a937fbd98ebac29a3144946bd6e21.png",
        "sha256": "7b23f70fc53017314878dd4d4ec663a7a23a937fbd98ebac29a3144946bd6e21"
      },
      {
        "path": "/data2/k6tk/d5/d5a42c5aac696ad914bb29e86bfe4395bf01069947f6806b733a2fee5c732359.png",
        "sha256": "d5a42c5aac696ad914bb29e86bfe4395bf01069947f6806b733a2fee5c732359"
      },
      {
        "path": "/data2/k6tk/f1/f161baf86c623c20b410d64cbf4fe8214651da3c587171a31d7bf339c8cf4c9b.png",
        "sha256": "f161baf86c623c20b410d64cbf4fe8214651da3c587171a31d7bf339c8cf4c9b"
      },
      {
        "path": "/data2/k6tk/13/13f32fdda3e47051d8f6aebec9cf601a7a4dfc23dec20e049126a60cfa5e9795.png",
        "sha256": "13f32fdda3e47051d8f6aebec9cf601a7a4dfc23dec20e049126a60cfa5e9795"
      },
      {
        "path": "/data2/k6tk/6f/6f5621fb572e0acb6696a3b423fedd08ba51ca480b38b1e058fcf735b1f0ea98.png",
        "sha256": "6f5621fb572e0acb6696a3b423fedd08ba51ca480b38b1e058fcf735b1f0ea98"
      },
      {
        "path": "/data2/k6tk/ef/ef8fec91fefa8041fd6dea823bc52028601ddd488cf974b3231535d558a15be2.png",
        "sha256": "ef8fec91fefa8041fd6dea823bc52028601ddd488cf974b3231535d558a15be2"
      },
      {
        "path": "/data2/k6tk/73/733b282185e9b928fe764c40d16f5df15629b3086767e3f87479f39039c2c7cb.png",
        "sha256": "733b282185e9b928fe764c40d16f5df15629b3086767e3f87479f39039c2c7cb"
      },
      {
        "path": "/data2/k6tk/63/631671cdfdde4fd1932fb9a7a7d425705bbada0b5312ef170f07dc5e80ecae24.png",
        "sha256": "631671cdfdde4fd1932fb9a7a7d425705bbada0b5312ef170f07dc5e80ecae24"
      },
      {
        "path": "/data2/k6tk/bf/bfeb692cfec2af4b991038e305591b55cc7f5116e724de40a9682c4a13294eae.png",
        "sha256": "bfeb692cfec2af4b991038e305591b55cc7f5116e724de40a9682c4a13294eae"
      },
      {
        "path": "/data2/k6tk/4b/4bbba07541ba51fbf62b4d8506d0cdf6c4282831f0be0731482298dfe964889b.png",
        "sha256": "4bbba07541ba51fbf62b4d8506d0cdf6c4282831f0be0731482298dfe964889b"
      },
      {
        "path": "/data2/k6tk/25/25d8f333b1ca90a10396ae50fe36f80380dbe36ff71e15c6a374bf6af9b6fe1f.png",
        "sha256": "25d8f333b1ca90a10396ae50fe36f80380dbe36ff71e15c6a374bf6af9b6fe1f"
      },
      {
        "path": "/data2/k6tk/d0/d0e704919bb31f1c3c131ecc079da490f4baecf7871507224e35b4e74eb22fd4.png",
        "sha256": "d0e704919bb31f1c3c131ecc079da490f4baecf7871507224e35b4e74eb22fd4"
      },
      {
        "path": "/data2/k6tk/b0/b093b9942b909a2fe31ef70dd4bf5363e06758d44d85eec11cee7cd8edfe2321.png",
        "sha256": "b093b9942b909a2fe31ef70dd4bf5363e06758d44d85eec11cee7cd8edfe2321"
      },
      {
        "path": "/data2/k6tk/ac/acae24dfc66d742615a0c300c582399f206d6d1a538f2fde91e11584fd4032b4.png",
        "sha256": "acae24dfc66d742615a0c300c582399f206d6d1a538f2fde91e11584fd4032b4"
      },
      {
        "path": "/data2/k6tk/10/10a1ed03330f8b3c68bb2b9dc20f947429049a98bc6fa4853cb71a6920afa961.png",
        "sha256": "10a1ed03330f8b3c68bb2b9dc20f947429049a98bc6fa4853cb71a6920afa961"
      },
      {
        "path": "/data2/k6tk/3c/3c3b2aca1b74a385a749d632423e6b996e230bdabcacbfbf067a1bbed2c35b55.png",
        "sha256": "3c3b2aca1b74a385a749d632423e6b996e230bdabcacbfbf067a1bbed2c35b55"
      },
      {
        "path": "/data2/k6tk/fc/fc55b59e7dc7d901966bc6df113a13a38739bd1d187b03325be8b66fbe087c5c.png",
        "sha256": "fc55b59e7dc7d901966bc6df113a13a38739bd1d187b03325be8b66fbe087c5c"
      },
      {
        "path": "/data2/k6tk/88/8833fdd33d961e64a4274bb549f678fef8597bad96c0774e04e7d7525ed4f98c.png",
        "sha256": "8833fdd33d961e64a4274bb549f678fef8597bad96c0774e04e7d7525ed4f98c"
      },
      {
        "path": "/data2/k6tk/f3/f30eee606d148959a1c2d584fadc558f5f86a0d9f70db3b3f25668dedc640305.png",
        "sha256": "f30eee606d148959a1c2d584fadc558f5f86a0d9f70db3b3f25668dedc640305"
      },
      {
        "path": "/data2/k6tk/8b/8b38cab0404f53e99cec4e2c6b38b97d26250a576e372e0b76e5261f112fe1bd.png",
        "sha256": "8b38cab0404f53e99cec4e2c6b38b97d26250a576e372e0b76e5261f112fe1bd"
      },
      {
        "path": "/data2/k6tk/2c/2cfc9b336e0d844ae653cd03245ea78c5f45e8ea788bb4bf09245df78e71a7ec.png",
        "sha256": "2cfc9b336e0d844ae653cd03245ea78c5f45e8ea788bb4bf09245df78e71a7ec"
      },
      {
        "path": "/data2/k6tk/17/17d79a44ac0e88c2b62370ada34bc9255f8771ae545249a2c27cd1339c064274.png",
        "sha256": "17d79a44ac0e88c2b62370ada34bc9255f8771ae545249a2c27cd1339c064274"
      },
      {
        "path": "/data2/k6tk/f3/f322947143f1f5d49ca64d51e0c4f478987aef5e940fc466ee6017511e24ea0f.png",
        "sha256": "f322947143f1f5d49ca64d51e0c4f478987aef5e940fc466ee6017511e24ea0f"
      },
      {
        "path": "/data2/k6tk/39/394c555450ed78ca350597100af5f49fc565faf6657076c2330e82b7e77bfa66.png",
        "sha256": "394c555450ed78ca350597100af5f49fc565faf6657076c2330e82b7e77bfa66"
      },
      {
        "path": "/data2/k6tk/47/47159c3f8d59eebee3a2af0f092d1c4f48a92ea7ba104eb1ee2931080c9242b7.png",
        "sha256": "47159c3f8d59eebee3a2af0f092d1c4f48a92ea7ba104eb1ee2931080c9242b7"
      },
      {
        "path": "/data2/k6tk/21/213a61324d2d1e0b9fd0fe3ae0f77c57afbf970893f1009c0dda309c10d2f171.png",
        "sha256": "213a61324d2d1e0b9fd0fe3ae0f77c57afbf970893f1009c0dda309c10d2f171"
      },
      {
        "path": "/data2/k6tk/46/46de25cc77ae38f57d3c54f696e7600a1610589dcfdfe5aaa4ec12875fadf04b.png",
        "sha256": "46de25cc77ae38f57d3c54f696e7600a1610589dcfdfe5aaa4ec12875fadf04b"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "When positioned beside the window and facing away from the door, is the mirror placed on the left or right?",
    "timestamps": [
      0.0,
      1.8333333333333333,
      3.6666666666666665,
      5.5,
      7.333333333333333,
      9.166666666666666,
      11.0,
      12.875,
      14.708333333333334,
      16.541666666666668,
      18.375,
      20.208333333333332,
      22.041666666666668,
      23.916666666666668,
      25.75,
      27.583333333333332,
      29.416666666666668,
      31.25,
      33.083333333333336,
      34.958333333333336,
      36.791666666666664,
      38.625,
      40.458333333333336,
      42.291666666666664,
      44.125,
      46.0,
      47.833333333333336,
      49.666666666666664,
      51.5,
      53.333333333333336,
      55.166666666666664,
      57.041666666666664
    ],
    "total_num_frames": 1370
  },
  "target": "<think>\nStep 1: find the window and the door, then the mirror.\nStep 2: facing the door from the window, I find the mirror to my right.\nStep 3: I face away from the door by making a half turn. Front and back swap, and left and right swap.\nSo I find the mirror to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 4. q8b933b9489554d5ce0528845_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-179e175d871708acde1084819e7681306475c6ce384f7d4b1f36f64432389935",
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q8b933b9489554d5ce0528845"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 39,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 33
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "right",
      "source_qid": "q8b933b9489554d5ce0528845",
      "source_row_sha256": "acc49abaaf75123298d9e545d2049434b9542bb889071d20b4da3305cac503b2",
      "source_store_i": 20759
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q8b933b9489554d5ce0528845_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "53d62f24a4d54aaa1947a9b4679d7a244978f5b86b183bf685efdfa5d8689f85"
  },
  "scene": "v5f78e53cd751",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      19,
      39,
      59,
      79,
      99,
      119,
      139,
      159,
      179,
      199,
      218,
      238,
      258,
      278,
      298,
      318,
      338,
      358,
      378,
      398,
      417,
      437,
      457,
      477,
      497,
      517,
      537,
      557,
      577,
      597,
      617
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a4/a4ee05022d06a8bc825082a15533c5ab9085c5f9f91ba9ab6355cf19b8452382.png",
        "sha256": "a4ee05022d06a8bc825082a15533c5ab9085c5f9f91ba9ab6355cf19b8452382"
      },
      {
        "path": "/data2/k6tk/5e/5e1ff6f109f9c2848fec76ebdaa1a35a104cb4935a9ecf533fa67c36c3b00058.png",
        "sha256": "5e1ff6f109f9c2848fec76ebdaa1a35a104cb4935a9ecf533fa67c36c3b00058"
      },
      {
        "path": "/data2/k6tk/df/df6bd4866a0af5b47439c6ea2b37948a0982885d0c38a4175407c908493bb962.png",
        "sha256": "df6bd4866a0af5b47439c6ea2b37948a0982885d0c38a4175407c908493bb962"
      },
      {
        "path": "/data2/k6tk/04/04036bbe61666594e6154e16483f82cde3a498e1f041cf2b4e8d5e22f942cc2e.png",
        "sha256": "04036bbe61666594e6154e16483f82cde3a498e1f041cf2b4e8d5e22f942cc2e"
      },
      {
        "path": "/data2/k6tk/29/29709dff016b31e494342eae4e915ce2af7ae8241390cd2cc1c5dcd4de2ec0b9.png",
        "sha256": "29709dff016b31e494342eae4e915ce2af7ae8241390cd2cc1c5dcd4de2ec0b9"
      },
      {
        "path": "/data2/k6tk/bd/bdd8e45de4c05b1e4e0d8f68eccd367fe2eb5d4bec0129ed7bd4e82494d08323.png",
        "sha256": "bdd8e45de4c05b1e4e0d8f68eccd367fe2eb5d4bec0129ed7bd4e82494d08323"
      },
      {
        "path": "/data2/k6tk/20/202a015382f87b31123b29cfb275cd04d5012e2f8f0c86049a1e998e529c4107.png",
        "sha256": "202a015382f87b31123b29cfb275cd04d5012e2f8f0c86049a1e998e529c4107"
      },
      {
        "path": "/data2/k6tk/15/150bb64ac4ad7fcd62e203f99cd58ac963c21738849d690781365461a846969e.png",
        "sha256": "150bb64ac4ad7fcd62e203f99cd58ac963c21738849d690781365461a846969e"
      },
      {
        "path": "/data2/k6tk/69/69958a84a5b1153eda1bcfc63358eef863f30a0a97ef2914e287c741f25359ea.png",
        "sha256": "69958a84a5b1153eda1bcfc63358eef863f30a0a97ef2914e287c741f25359ea"
      },
      {
        "path": "/data2/k6tk/78/783443bda138935ce7ccf29f25a8f8aa0c7703f5cb062a8e506182a849fad89a.png",
        "sha256": "783443bda138935ce7ccf29f25a8f8aa0c7703f5cb062a8e506182a849fad89a"
      },
      {
        "path": "/data2/k6tk/67/67f512463609d2f8cba21d3e3aa5d7965fe97fef46aec757818438cfa9528050.png",
        "sha256": "67f512463609d2f8cba21d3e3aa5d7965fe97fef46aec757818438cfa9528050"
      },
      {
        "path": "/data2/k6tk/ba/ba54d68d6b27fc05f38f6c1ddd66534be7d32fc9e7d2d19e5057e3b12188e4d0.png",
        "sha256": "ba54d68d6b27fc05f38f6c1ddd66534be7d32fc9e7d2d19e5057e3b12188e4d0"
      },
      {
        "path": "/data2/k6tk/b5/b51fce1d57ab96970a89c165cb1f3356ac35e79042056a96f639ac6c58295ea9.png",
        "sha256": "b51fce1d57ab96970a89c165cb1f3356ac35e79042056a96f639ac6c58295ea9"
      },
      {
        "path": "/data2/k6tk/5c/5c897f9ef4f4a4e390ccde77c0da71d330e344a350e74f502591467bbe047934.png",
        "sha256": "5c897f9ef4f4a4e390ccde77c0da71d330e344a350e74f502591467bbe047934"
      },
      {
        "path": "/data2/k6tk/fd/fd4f410cea0e912133edaaf96acb828323866dedbc3c4bab340cfa1f18885c6e.png",
        "sha256": "fd4f410cea0e912133edaaf96acb828323866dedbc3c4bab340cfa1f18885c6e"
      },
      {
        "path": "/data2/k6tk/ca/ca29c546cd0825c73a8eb023f9643a526384bb6be10a6bd090fe392e946c074e.png",
        "sha256": "ca29c546cd0825c73a8eb023f9643a526384bb6be10a6bd090fe392e946c074e"
      },
      {
        "path": "/data2/k6tk/bf/bfcba7268d6945ce125a2fde2dee0efb5f48dbd2effc4c8f36abb45725a74bce.png",
        "sha256": "bfcba7268d6945ce125a2fde2dee0efb5f48dbd2effc4c8f36abb45725a74bce"
      },
      {
        "path": "/data2/k6tk/5d/5df8f3a200f4c435b83ca59333d7f68cd3cc728f2a8b4169cece4d7aec7489d9.png",
        "sha256": "5df8f3a200f4c435b83ca59333d7f68cd3cc728f2a8b4169cece4d7aec7489d9"
      },
      {
        "path": "/data2/k6tk/85/85262e626675510b1066fbc33d5a3695146216530457116176346ac895f267df.png",
        "sha256": "85262e626675510b1066fbc33d5a3695146216530457116176346ac895f267df"
      },
      {
        "path": "/data2/k6tk/e1/e128b0bcf8dd66ace903623cc6cca10435114dff9280614a2d638a37a63151b5.png",
        "sha256": "e128b0bcf8dd66ace903623cc6cca10435114dff9280614a2d638a37a63151b5"
      },
      {
        "path": "/data2/k6tk/a7/a78dca95c99de91de93d08142917273c4fa00405bdf8aceabf5659b95472d92a.png",
        "sha256": "a78dca95c99de91de93d08142917273c4fa00405bdf8aceabf5659b95472d92a"
      },
      {
        "path": "/data2/k6tk/8e/8e7c18a1ac5967672bc95c1aee65381a926b58029f8c4ec8d12ba214c82cfd9d.png",
        "sha256": "8e7c18a1ac5967672bc95c1aee65381a926b58029f8c4ec8d12ba214c82cfd9d"
      },
      {
        "path": "/data2/k6tk/5a/5afdf02abdf5db269ed3430dc376fe095db50430c8436aba37ce24ce26b8af0a.png",
        "sha256": "5afdf02abdf5db269ed3430dc376fe095db50430c8436aba37ce24ce26b8af0a"
      },
      {
        "path": "/data2/k6tk/c5/c56e6448319166193a9821450542886714c618a9e2d43dcc6f2de97c780e6922.png",
        "sha256": "c56e6448319166193a9821450542886714c618a9e2d43dcc6f2de97c780e6922"
      },
      {
        "path": "/data2/k6tk/29/29630ac3d591b95b6d17efa60278881fb0f3c949dafe07d7f4f71bd548b5adab.png",
        "sha256": "29630ac3d591b95b6d17efa60278881fb0f3c949dafe07d7f4f71bd548b5adab"
      },
      {
        "path": "/data2/k6tk/be/bef45b4260d13e896374d50cf410c1212b090bab50040ed19cae5d5c958b2cb1.png",
        "sha256": "bef45b4260d13e896374d50cf410c1212b090bab50040ed19cae5d5c958b2cb1"
      },
      {
        "path": "/data2/k6tk/5f/5ff06e078ec4694c9675416572d8b57e48eced306bd65f79845b6ab079805423.png",
        "sha256": "5ff06e078ec4694c9675416572d8b57e48eced306bd65f79845b6ab079805423"
      },
      {
        "path": "/data2/k6tk/6b/6bd37c8cffaec971d1d09d81aec639130129a43a9013016e08c014114a930f60.png",
        "sha256": "6bd37c8cffaec971d1d09d81aec639130129a43a9013016e08c014114a930f60"
      },
      {
        "path": "/data2/k6tk/b6/b6bc24521423d9908bad58c7d57ebe7f2d4a63775f6e7001bfb2f1bbe19928d5.png",
        "sha256": "b6bc24521423d9908bad58c7d57ebe7f2d4a63775f6e7001bfb2f1bbe19928d5"
      },
      {
        "path": "/data2/k6tk/b2/b2f1cbfa8579b3a7f7004cde0552f41b65cd7634d3cbd5ce0077febcaa451d9b.png",
        "sha256": "b2f1cbfa8579b3a7f7004cde0552f41b65cd7634d3cbd5ce0077febcaa451d9b"
      },
      {
        "path": "/data2/k6tk/2b/2b413c90028bcaedb15c390d2bdba16241acd8e6b82db6c4154d750b7132030e.png",
        "sha256": "2b413c90028bcaedb15c390d2bdba16241acd8e6b82db6c4154d750b7132030e"
      },
      {
        "path": "/data2/k6tk/a7/a7d736af4bdf9fe6e21963e57ffde123716e97603b219cca308a5aef39176476.png",
        "sha256": "a7d736af4bdf9fe6e21963e57ffde123716e97603b219cca308a5aef39176476"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the book and facing away from the counter, is the sink to the left or the right of the counter?",
    "timestamps": [
      0.0,
      0.7916666666666666,
      1.625,
      2.4583333333333335,
      3.2916666666666665,
      4.125,
      4.958333333333333,
      5.791666666666667,
      6.625,
      7.458333333333333,
      8.291666666666666,
      9.083333333333334,
      9.916666666666666,
      10.75,
      11.583333333333334,
      12.416666666666666,
      13.25,
      14.083333333333334,
      14.916666666666666,
      15.75,
      16.583333333333332,
      17.375,
      18.208333333333332,
      19.041666666666668,
      19.875,
      20.708333333333332,
      21.541666666666668,
      22.375,
      23.208333333333332,
      24.041666666666668,
      24.875,
      25.708333333333332
    ],
    "total_num_frames": 618
  },
  "target": "<think>\nStep 1: find the book and the counter, then the sink.\nStep 2: I find the sink to my right when I stand at the book facing the counter.\nStep 3: I face away from the counter by making a half turn. Front and back swap, and left and right swap.\nSo I find the sink to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 5. qca887709b179aa1ae1f621af-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-1193ecc627e35a175fdefc37474aaacfaca1feaa1003767007db6ea2bdc5ae1e",
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qca887709b179aa1ae1f621af-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qca887709b179aa1ae1f621af",
  "paraphrase_template": "easy_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 52,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "look toward",
        "start": 41
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "right",
      "source_qid": "qca887709b179aa1ae1f621af-p1",
      "source_row_sha256": "65bdb8baccf02dd8eb50b5c77cfdcb4b836b79f0d491d463be17e8a018c9bbf6",
      "source_store_i": 69066
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qca887709b179aa1ae1f621af-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "32a8a3bb1799a3d90ec506d4a3dae4b214effa730a1c6a0b5201b97acfccde54"
  },
  "scene": "ve629201a8ae1",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      413,
      826,
      1239,
      1653,
      2066,
      2479,
      2893,
      3306,
      3719,
      4132,
      4546,
      4959,
      5372,
      5786,
      6199,
      6612,
      7025,
      7439,
      7852,
      8265,
      8679,
      9092,
      9505,
      9918,
      10332,
      10745,
      11158,
      11572,
      11985,
      12398,
      12812
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c4/c48b5cdfa1448f8edeba80c43507fd558b9be3ee1cd040ceb48a8c4907c1f124.png",
        "sha256": "c48b5cdfa1448f8edeba80c43507fd558b9be3ee1cd040ceb48a8c4907c1f124"
      },
      {
        "path": "/data2/k6tk/3c/3ce608d37a04c791c603a119022e6b2e182e7932a6faa3c552b12b048d0ad831.png",
        "sha256": "3ce608d37a04c791c603a119022e6b2e182e7932a6faa3c552b12b048d0ad831"
      },
      {
        "path": "/data2/k6tk/c6/c65b40969ee9cc58c9970f51830cadf82dcc67d450d678d29ebf528d1914535c.png",
        "sha256": "c65b40969ee9cc58c9970f51830cadf82dcc67d450d678d29ebf528d1914535c"
      },
      {
        "path": "/data2/k6tk/d6/d6822531d99c93acdf40a9b14af5cd63962393cc6b071bc91575ffc9a8d8fe78.png",
        "sha256": "d6822531d99c93acdf40a9b14af5cd63962393cc6b071bc91575ffc9a8d8fe78"
      },
      {
        "path": "/data2/k6tk/64/6493e852d53dcbbed0f54254e0f18e259d1719f0e7e49e63781293b799e219c1.png",
        "sha256": "6493e852d53dcbbed0f54254e0f18e259d1719f0e7e49e63781293b799e219c1"
      },
      {
        "path": "/data2/k6tk/16/16335b2f775f912699d3edc3735d94d65011a13bae4c34dc635390e7d94c235d.png",
        "sha256": "16335b2f775f912699d3edc3735d94d65011a13bae4c34dc635390e7d94c235d"
      },
      {
        "path": "/data2/k6tk/8c/8c679247fd51c4f18c99cc81ce2878e929e5b50479c1dd0585247a1ba87f1fc0.png",
        "sha256": "8c679247fd51c4f18c99cc81ce2878e929e5b50479c1dd0585247a1ba87f1fc0"
      },
      {
        "path": "/data2/k6tk/f1/f1fd76edd530181180c05946a744a2213dee2bddc330bdef6310544198b8208a.png",
        "sha256": "f1fd76edd530181180c05946a744a2213dee2bddc330bdef6310544198b8208a"
      },
      {
        "path": "/data2/k6tk/fe/fe46eada8011cd93a6158b425c6e30548b473824758285b9e43344e74857e4f8.png",
        "sha256": "fe46eada8011cd93a6158b425c6e30548b473824758285b9e43344e74857e4f8"
      },
      {
        "path": "/data2/k6tk/60/601860c72de643648dfff4fa47525da9b4c71e413a1743adb41018b9d73d9f74.png",
        "sha256": "601860c72de643648dfff4fa47525da9b4c71e413a1743adb41018b9d73d9f74"
      },
      {
        "path": "/data2/k6tk/b8/b82a17a03b52d349920f12cb2a40a06e0b1def86e184b3c79843ddc9e17a7d14.png",
        "sha256": "b82a17a03b52d349920f12cb2a40a06e0b1def86e184b3c79843ddc9e17a7d14"
      },
      {
        "path": "/data2/k6tk/17/1706ed434a97c682f298ee0b487f293958a6a512dedeb612e34ad3ec92c53a2a.png",
        "sha256": "1706ed434a97c682f298ee0b487f293958a6a512dedeb612e34ad3ec92c53a2a"
      },
      {
        "path": "/data2/k6tk/70/70014dd2c40fd5bc56628a4f7063d06a89a28001762b1e2f3c3466cbe69fa73f.png",
        "sha256": "70014dd2c40fd5bc56628a4f7063d06a89a28001762b1e2f3c3466cbe69fa73f"
      },
      {
        "path": "/data2/k6tk/88/88a887bfd42293d40ea3caffbfa29e831b7b5cdae41c7b45a5a906071c3fa919.png",
        "sha256": "88a887bfd42293d40ea3caffbfa29e831b7b5cdae41c7b45a5a906071c3fa919"
      },
      {
        "path": "/data2/k6tk/82/8274e828b1ba4a0c442f201ffd8bb47208cd40b7b532b8dea7855678c674d1bc.png",
        "sha256": "8274e828b1ba4a0c442f201ffd8bb47208cd40b7b532b8dea7855678c674d1bc"
      },
      {
        "path": "/data2/k6tk/5b/5b7f4fa5a1def6ab3d78c35c16e4f2ede86ad16204918cc1e7763083c1a1b477.png",
        "sha256": "5b7f4fa5a1def6ab3d78c35c16e4f2ede86ad16204918cc1e7763083c1a1b477"
      },
      {
        "path": "/data2/k6tk/ab/ab45266fe445bd57f079166dff05f331ca5055f6601f43e3578773fc04ca50ad.png",
        "sha256": "ab45266fe445bd57f079166dff05f331ca5055f6601f43e3578773fc04ca50ad"
      },
      {
        "path": "/data2/k6tk/eb/eb3c8e8e389d5f7c03eedd87c08edc26426a6bbf031aac55123fe7109d83a6ad.png",
        "sha256": "eb3c8e8e389d5f7c03eedd87c08edc26426a6bbf031aac55123fe7109d83a6ad"
      },
      {
        "path": "/data2/k6tk/a0/a0e7553e6b5c5ff2f42c0675d29dfc2e32ba420e679d75694ac16370606dbe32.png",
        "sha256": "a0e7553e6b5c5ff2f42c0675d29dfc2e32ba420e679d75694ac16370606dbe32"
      },
      {
        "path": "/data2/k6tk/5b/5b087432c9e96b9ab135bc0476b20ab88ca6b0c18ccb990f68b00e1dd5967dc8.png",
        "sha256": "5b087432c9e96b9ab135bc0476b20ab88ca6b0c18ccb990f68b00e1dd5967dc8"
      },
      {
        "path": "/data2/k6tk/f6/f6978254ce66a93ce0e715800e60bbb48f0c0197375a8e1c7d9ceb9b7d5a9c12.png",
        "sha256": "f6978254ce66a93ce0e715800e60bbb48f0c0197375a8e1c7d9ceb9b7d5a9c12"
      },
      {
        "path": "/data2/k6tk/55/5587d257cc9cf7196724ca3d8f537aa105ebf3f6438d13e9cbf782614897fe18.png",
        "sha256": "5587d257cc9cf7196724ca3d8f537aa105ebf3f6438d13e9cbf782614897fe18"
      },
      {
        "path": "/data2/k6tk/59/59af2bb99924ae97c636598d6a71db79f5cf20d138c5c699825212515d7d12ee.png",
        "sha256": "59af2bb99924ae97c636598d6a71db79f5cf20d138c5c699825212515d7d12ee"
      },
      {
        "path": "/data2/k6tk/94/94b262bf0900901c001512594eacc93661e5c99bfc4a57ededd780560a925e55.png",
        "sha256": "94b262bf0900901c001512594eacc93661e5c99bfc4a57ededd780560a925e55"
      },
      {
        "path": "/data2/k6tk/a3/a323f65f9eb96c93aaa1dc7358135dc8b0d99afbd6391ebfdf9bccf8cfee6729.png",
        "sha256": "a323f65f9eb96c93aaa1dc7358135dc8b0d99afbd6391ebfdf9bccf8cfee6729"
      },
      {
        "path": "/data2/k6tk/9a/9a0b21b979f0628efc1e7b1c9035ad19685179abd54b0cb4c8d65ba76f31936b.png",
        "sha256": "9a0b21b979f0628efc1e7b1c9035ad19685179abd54b0cb4c8d65ba76f31936b"
      },
      {
        "path": "/data2/k6tk/24/24bf645710b0f849a8410197789065952c188573755fea41ed63beeb41585c91.png",
        "sha256": "24bf645710b0f849a8410197789065952c188573755fea41ed63beeb41585c91"
      },
      {
        "path": "/data2/k6tk/df/df843e7f35de0fb2e55c00dda9f4b24601003871c1ec54627b1100efa8dee288.png",
        "sha256": "df843e7f35de0fb2e55c00dda9f4b24601003871c1ec54627b1100efa8dee288"
      },
      {
        "path": "/data2/k6tk/97/9781be86224020fa5573bc6b7e0aed94c7b2156ff45e2f1ebd3174957902d225.png",
        "sha256": "9781be86224020fa5573bc6b7e0aed94c7b2156ff45e2f1ebd3174957902d225"
      },
      {
        "path": "/data2/k6tk/40/4012ad270880f774b4aea367ca19da06dfd5c16ece9cdf05c1ed81355d1c5cef.png",
        "sha256": "4012ad270880f774b4aea367ca19da06dfd5c16ece9cdf05c1ed81355d1c5cef"
      },
      {
        "path": "/data2/k6tk/71/71adecb3467f2d792d21239a9c9c8a6c5ab3fc4ffce7f10e518e3143b5186cce.png",
        "sha256": "71adecb3467f2d792d21239a9c9c8a6c5ab3fc4ffce7f10e518e3143b5186cce"
      },
      {
        "path": "/data2/k6tk/e6/e6243440c924db7e337d1a9e1177546699e6d9f12d5ab4153975852265808344.png",
        "sha256": "e6243440c924db7e337d1a9e1177546699e6d9f12d5ab4153975852265808344"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the curtain rail, face away from the floor lamp. Is the stool to your left or right?",
    "timestamps": [
      0.0,
      6.883333333333334,
      13.766666666666667,
      20.65,
      27.55,
      34.43333333333333,
      41.31666666666667,
      48.21666666666667,
      55.1,
      61.983333333333334,
      68.86666666666666,
      75.76666666666667,
      82.65,
      89.53333333333333,
      96.43333333333334,
      103.31666666666666,
      110.2,
      117.08333333333333,
      123.98333333333333,
      130.86666666666667,
      137.75,
      144.65,
      151.53333333333333,
      158.41666666666666,
      165.3,
      172.2,
      179.08333333333334,
      185.96666666666667,
      192.86666666666667,
      199.75,
      206.63333333333333,
      213.53333333333333
    ],
    "total_num_frames": 12813
  },
  "target": "<think>\nStep 1: find the curtain rail, the floor lamp and the stool.\nStep 2: I stand at the curtain rail facing the floor lamp; I find the stool to my right.\nStep 3: I face away from the floor lamp by making a half turn. Front and back swap, and left and right swap.\nSo I find the stool to my left.\n</think>\n\nA",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 6. q30203d0d64576db86edfd321-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-dbee41bac3dbc5f607e178b151da131d3cda0f0ebfbf59efba9cf46e1ff59485",
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q30203d0d64576db86edfd321-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q30203d0d64576db86edfd321",
  "paraphrase_template": "easy_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 49,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "look toward",
        "start": 38
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "left",
      "source_qid": "q30203d0d64576db86edfd321-p1",
      "source_row_sha256": "5cfbbae3494ddb426f6dad089ba935c3ca39555ddbb0ba82c2503d8a3d4579f8",
      "source_store_i": 75300
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q30203d0d64576db86edfd321-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "1645aa4a5963df57c641f487e31953c3e2d686c6aa9d44d3e486b929a275b9de"
  },
  "scene": "v56360c6a4e92",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      257,
      515,
      773,
      1031,
      1289,
      1547,
      1805,
      2063,
      2321,
      2579,
      2837,
      3095,
      3353,
      3611,
      3869,
      4126,
      4384,
      4642,
      4900,
      5158,
      5416,
      5674,
      5932,
      6190,
      6448,
      6706,
      6964,
      7222,
      7480,
      7738,
      7996
    ],
    "frames": [
      {
        "path": "/data2/k6tk/65/65610acb5504ae43cebc153712ca86139242fbe98b10490ccae4c697f97812db.png",
        "sha256": "65610acb5504ae43cebc153712ca86139242fbe98b10490ccae4c697f97812db"
      },
      {
        "path": "/data2/k6tk/b7/b7124340f832cc66acc166969cc545c872f1b914c8af0876d4e2418b55ca219c.png",
        "sha256": "b7124340f832cc66acc166969cc545c872f1b914c8af0876d4e2418b55ca219c"
      },
      {
        "path": "/data2/k6tk/3b/3b7ca0a814490ca81b92fcd4e4597592fd6c99d0d0186211694d054f9f03a41b.png",
        "sha256": "3b7ca0a814490ca81b92fcd4e4597592fd6c99d0d0186211694d054f9f03a41b"
      },
      {
        "path": "/data2/k6tk/5d/5d0e8f2b3692e72798b24ff74c7621ba3b50589dd13bf17797a44c710a4a3abb.png",
        "sha256": "5d0e8f2b3692e72798b24ff74c7621ba3b50589dd13bf17797a44c710a4a3abb"
      },
      {
        "path": "/data2/k6tk/02/0217eb3053216de190760e352d6971930bef4ecbedfcd95d7af8055879aae1a9.png",
        "sha256": "0217eb3053216de190760e352d6971930bef4ecbedfcd95d7af8055879aae1a9"
      },
      {
        "path": "/data2/k6tk/7f/7f5e38fc04543eddcdeeb6302713a26b945dd148fe8dd374dc9a34c6b68a1234.png",
        "sha256": "7f5e38fc04543eddcdeeb6302713a26b945dd148fe8dd374dc9a34c6b68a1234"
      },
      {
        "path": "/data2/k6tk/75/75dfff70beb9f9ecbafa8f4bd7b3f09596f9f46fbbd76c88a13dd327e7a478d4.png",
        "sha256": "75dfff70beb9f9ecbafa8f4bd7b3f09596f9f46fbbd76c88a13dd327e7a478d4"
      },
      {
        "path": "/data2/k6tk/93/93f2509dab0fc5d0d48d04d7b9f949134a753d2fd60d9d12cb7921ee44f2d820.png",
        "sha256": "93f2509dab0fc5d0d48d04d7b9f949134a753d2fd60d9d12cb7921ee44f2d820"
      },
      {
        "path": "/data2/k6tk/08/0878d963d30c17cf78f8ad269a387c2550b83cd0263a00f960a5b6709b3bdf78.png",
        "sha256": "0878d963d30c17cf78f8ad269a387c2550b83cd0263a00f960a5b6709b3bdf78"
      },
      {
        "path": "/data2/k6tk/32/3296d4312901762c3958884d786e80738b07b13e00b85b4bca88d200f6f6f740.png",
        "sha256": "3296d4312901762c3958884d786e80738b07b13e00b85b4bca88d200f6f6f740"
      },
      {
        "path": "/data2/k6tk/b6/b698c57679aecdfa11b7ca030188d9f003ddc4525f905ce915fd9f997cf33cf1.png",
        "sha256": "b698c57679aecdfa11b7ca030188d9f003ddc4525f905ce915fd9f997cf33cf1"
      },
      {
        "path": "/data2/k6tk/e0/e09cfb8e87f2969e50d1f95821445922668674496c06423acd12aafb82fd6d89.png",
        "sha256": "e09cfb8e87f2969e50d1f95821445922668674496c06423acd12aafb82fd6d89"
      },
      {
        "path": "/data2/k6tk/d5/d564891cef1d5bed5795b3e38ca2325f40946ab8981299a425feb4b86c6b2a41.png",
        "sha256": "d564891cef1d5bed5795b3e38ca2325f40946ab8981299a425feb4b86c6b2a41"
      },
      {
        "path": "/data2/k6tk/06/061a91e90189f7c77b56bed764104217fdf51467fff0e6dbadcc4ec3f1d4022d.png",
        "sha256": "061a91e90189f7c77b56bed764104217fdf51467fff0e6dbadcc4ec3f1d4022d"
      },
      {
        "path": "/data2/k6tk/ef/ef5661fd576af17b3f5860feca8a0dcfa168dda0c659c365b9533877508cc89a.png",
        "sha256": "ef5661fd576af17b3f5860feca8a0dcfa168dda0c659c365b9533877508cc89a"
      },
      {
        "path": "/data2/k6tk/02/0253f38868232cae4902271d1f60a1960c0fa772838e0de83e63eb47d2163562.png",
        "sha256": "0253f38868232cae4902271d1f60a1960c0fa772838e0de83e63eb47d2163562"
      },
      {
        "path": "/data2/k6tk/17/1757bc9da2b3ca0979a64d85c720afc776f50083e00195b615d3381ced4a4bf2.png",
        "sha256": "1757bc9da2b3ca0979a64d85c720afc776f50083e00195b615d3381ced4a4bf2"
      },
      {
        "path": "/data2/k6tk/08/084cda74f2ea9b550048f75b4e7bfe48d33555851fa2e365187e111e5c734b19.png",
        "sha256": "084cda74f2ea9b550048f75b4e7bfe48d33555851fa2e365187e111e5c734b19"
      },
      {
        "path": "/data2/k6tk/69/69dc8693e2fee0f82274f36c07cc82aba856109bbe41b865b871171ac4c757f7.png",
        "sha256": "69dc8693e2fee0f82274f36c07cc82aba856109bbe41b865b871171ac4c757f7"
      },
      {
        "path": "/data2/k6tk/37/371f086556228dd94c4bf8866addd34a627f94ea250a3762abb75d9b0100bd2d.png",
        "sha256": "371f086556228dd94c4bf8866addd34a627f94ea250a3762abb75d9b0100bd2d"
      },
      {
        "path": "/data2/k6tk/24/24d217261b1ab540239af88540e01667ef2b14fe87fa54aedb2e5a37b735985b.png",
        "sha256": "24d217261b1ab540239af88540e01667ef2b14fe87fa54aedb2e5a37b735985b"
      },
      {
        "path": "/data2/k6tk/75/750eb3892688fd69f38a9597fb215b03c219d7fa1515d782cc9e38b3ac09d690.png",
        "sha256": "750eb3892688fd69f38a9597fb215b03c219d7fa1515d782cc9e38b3ac09d690"
      },
      {
        "path": "/data2/k6tk/c8/c8d980d5b0346de5eff476f491c40b4e2502e3893fd1be21633b537e9339ad2b.png",
        "sha256": "c8d980d5b0346de5eff476f491c40b4e2502e3893fd1be21633b537e9339ad2b"
      },
      {
        "path": "/data2/k6tk/d6/d6f04e1597c4a5070e60f39d3c9a86c2d5305d842648d9bd44d336fca660e0d1.png",
        "sha256": "d6f04e1597c4a5070e60f39d3c9a86c2d5305d842648d9bd44d336fca660e0d1"
      },
      {
        "path": "/data2/k6tk/01/0119e40985a654318f8fbe0ec6dec41caf7913b6bb2e38a796dd972ec0a56093.png",
        "sha256": "0119e40985a654318f8fbe0ec6dec41caf7913b6bb2e38a796dd972ec0a56093"
      },
      {
        "path": "/data2/k6tk/4e/4ec9cd4071c9254e247d35336483493e32d0bc287f82aabc462fa9f86f63d026.png",
        "sha256": "4ec9cd4071c9254e247d35336483493e32d0bc287f82aabc462fa9f86f63d026"
      },
      {
        "path": "/data2/k6tk/ae/ae24f57b9e98150b146162cd433822121224811ff2c6a7c370ca3837ede26b4d.png",
        "sha256": "ae24f57b9e98150b146162cd433822121224811ff2c6a7c370ca3837ede26b4d"
      },
      {
        "path": "/data2/k6tk/f6/f6962677ec6a546872503e2290fa40c6bb864706317c65812f39e1e39e257bcc.png",
        "sha256": "f6962677ec6a546872503e2290fa40c6bb864706317c65812f39e1e39e257bcc"
      },
      {
        "path": "/data2/k6tk/e0/e05b40fb817f40bedfa8934b85c4d11862324951c3ec52fcc95534f85492e809.png",
        "sha256": "e05b40fb817f40bedfa8934b85c4d11862324951c3ec52fcc95534f85492e809"
      },
      {
        "path": "/data2/k6tk/fd/fdc7ab8cdf71d77462d22911a5a61c5735087d5dbee23c6930fef1b873c7c091.png",
        "sha256": "fdc7ab8cdf71d77462d22911a5a61c5735087d5dbee23c6930fef1b873c7c091"
      },
      {
        "path": "/data2/k6tk/66/66a68a29e93b080867150e84f64749e495f00ce1de46b27fe676b7d36a31cb52.png",
        "sha256": "66a68a29e93b080867150e84f64749e495f00ce1de46b27fe676b7d36a31cb52"
      },
      {
        "path": "/data2/k6tk/c3/c31f93addcb5f028a35a87008090d083561f5b69cba715b0333f2ee4d7663ee4.png",
        "sha256": "c31f93addcb5f028a35a87008090d083561f5b69cba715b0333f2ee4d7663ee4"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the bookshelf, face away from the curtain. Is the brief case to your left or right?",
    "timestamps": [
      0.0,
      4.283333333333333,
      8.583333333333334,
      12.883333333333333,
      17.183333333333334,
      21.483333333333334,
      25.783333333333335,
      30.083333333333332,
      34.38333333333333,
      38.68333333333333,
      42.983333333333334,
      47.28333333333333,
      51.583333333333336,
      55.88333333333333,
      60.18333333333333,
      64.48333333333333,
      68.76666666666667,
      73.06666666666666,
      77.36666666666666,
      81.66666666666667,
      85.96666666666667,
      90.26666666666667,
      94.56666666666666,
      98.86666666666666,
      103.16666666666667,
      107.46666666666667,
      111.76666666666667,
      116.06666666666666,
      120.36666666666666,
      124.66666666666667,
      128.96666666666667,
      133.26666666666668
    ],
    "total_num_frames": 7997
  },
  "target": "<think>\nStep 1: locate the brief case, the bookshelf and the curtain.\nStep 2: I find the brief case to my left when I stand at the bookshelf facing the curtain.\nStep 3: I face away from the curtain by making a half turn. Front and back swap, and left and right swap.\nSo I find the brief case to my right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 7. q2e5685a484977b4584691083-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-79d5ff70adf6f6724672b75b4f6332183215de35f3d59fa55b226de9053d3e25",
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q2e5685a484977b4584691083-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q2e5685a484977b4584691083",
  "paraphrase_template": "easy_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 46,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "look toward",
        "start": 35
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "left",
      "source_qid": "q2e5685a484977b4584691083-p1",
      "source_row_sha256": "25a37fef28ffa6abaf30ff8d0222271fcb186f174adcb5486c022811798d93e5",
      "source_store_i": 60034
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q2e5685a484977b4584691083-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "479aa754038bc21b8706d1bfd7e80411d6a702b9080338e874f66fc854b7238e"
  },
  "scene": "v738e4d4d104c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      230,
      460,
      690,
      920,
      1150,
      1381,
      1611,
      1841,
      2071,
      2301,
      2532,
      2762,
      2992,
      3222,
      3452,
      3683,
      3913,
      4143,
      4373,
      4603,
      4834,
      5064,
      5294,
      5524,
      5754,
      5985,
      6215,
      6445,
      6675,
      6905,
      7136
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9b/9b87c4a884870f71b9e0411c4a1ba3af41550323c21d1c89a5d2d8e1651b38b6.png",
        "sha256": "9b87c4a884870f71b9e0411c4a1ba3af41550323c21d1c89a5d2d8e1651b38b6"
      },
      {
        "path": "/data2/k6tk/9e/9ee67bbd381f3b7ab30e3281d37d6b783de73c0f565f6442bd6dd0f3e7c1d81a.png",
        "sha256": "9ee67bbd381f3b7ab30e3281d37d6b783de73c0f565f6442bd6dd0f3e7c1d81a"
      },
      {
        "path": "/data2/k6tk/35/3512cfc69f9caecec9e8d6f6634d9ffa6b2c203f534dbb57546a0a78444303ab.png",
        "sha256": "3512cfc69f9caecec9e8d6f6634d9ffa6b2c203f534dbb57546a0a78444303ab"
      },
      {
        "path": "/data2/k6tk/ad/add583051a15861bda948a62031e2a4536027ae2c1da8cc04960132f42832a54.png",
        "sha256": "add583051a15861bda948a62031e2a4536027ae2c1da8cc04960132f42832a54"
      },
      {
        "path": "/data2/k6tk/65/659b9d1fd2a9e09f3e45f570d24d9d49430b9fa1f5ab7d50b8b7bddb1b6a62cb.png",
        "sha256": "659b9d1fd2a9e09f3e45f570d24d9d49430b9fa1f5ab7d50b8b7bddb1b6a62cb"
      },
      {
        "path": "/data2/k6tk/c8/c8cba4da763b23e8908a1947bf25423b9e7d7183fafbb1b511647f6b9b30b349.png",
        "sha256": "c8cba4da763b23e8908a1947bf25423b9e7d7183fafbb1b511647f6b9b30b349"
      },
      {
        "path": "/data2/k6tk/ae/aeb8aae50536fedb8fe9c6d8136dc0330514211303f2336c580c7f9e96773f06.png",
        "sha256": "aeb8aae50536fedb8fe9c6d8136dc0330514211303f2336c580c7f9e96773f06"
      },
      {
        "path": "/data2/k6tk/e4/e4778d3d259136012cacd8cffe180a5b44f59cd05a9590222cb5aadaf86fe19b.png",
        "sha256": "e4778d3d259136012cacd8cffe180a5b44f59cd05a9590222cb5aadaf86fe19b"
      },
      {
        "path": "/data2/k6tk/2f/2f575ee4af24ebeb25041ea596ae3d08ad9488b99172179e6793d3ec6164f15e.png",
        "sha256": "2f575ee4af24ebeb25041ea596ae3d08ad9488b99172179e6793d3ec6164f15e"
      },
      {
        "path": "/data2/k6tk/d4/d4134d4e2097ac5b2aae0bfe43c6c2ef93bbae59e42d8c7f0b41717ee1c3b101.png",
        "sha256": "d4134d4e2097ac5b2aae0bfe43c6c2ef93bbae59e42d8c7f0b41717ee1c3b101"
      },
      {
        "path": "/data2/k6tk/ae/ae6e9d68fb0a67e86924ed33ded5488c4c913f1999a10e16636c359b5f141fb3.png",
        "sha256": "ae6e9d68fb0a67e86924ed33ded5488c4c913f1999a10e16636c359b5f141fb3"
      },
      {
        "path": "/data2/k6tk/5d/5d4cd98958b7af4118a65ee3e6524cc490619178a836c4024ce99ccc321afa59.png",
        "sha256": "5d4cd98958b7af4118a65ee3e6524cc490619178a836c4024ce99ccc321afa59"
      },
      {
        "path": "/data2/k6tk/f6/f606eed708e60ec0e49d4be0b64337b306741b983e2fe6db2c2925a7490662db.png",
        "sha256": "f606eed708e60ec0e49d4be0b64337b306741b983e2fe6db2c2925a7490662db"
      },
      {
        "path": "/data2/k6tk/b6/b61ac6627cfd20804e1746e2d2875c8a2456ac4b658212a3e5118cc6411dfaaf.png",
        "sha256": "b61ac6627cfd20804e1746e2d2875c8a2456ac4b658212a3e5118cc6411dfaaf"
      },
      {
        "path": "/data2/k6tk/f5/f54511aea88ea5d3284101ec748e400684e04636478ea2a04ca33a4e77cc3db6.png",
        "sha256": "f54511aea88ea5d3284101ec748e400684e04636478ea2a04ca33a4e77cc3db6"
      },
      {
        "path": "/data2/k6tk/14/1409a366bd008a2cd7bb453ef70e845e3248b636b1dc02b623140ab2ebd1f3ef.png",
        "sha256": "1409a366bd008a2cd7bb453ef70e845e3248b636b1dc02b623140ab2ebd1f3ef"
      },
      {
        "path": "/data2/k6tk/c2/c2a263d1513eb6899ee8d7f55335ede0295d6a8e636a74691fb3a4ef036eb6cd.png",
        "sha256": "c2a263d1513eb6899ee8d7f55335ede0295d6a8e636a74691fb3a4ef036eb6cd"
      },
      {
        "path": "/data2/k6tk/e2/e25570034f0616372497098724ccbc9e5850f0601f6121e89e78b5beaf526912.png",
        "sha256": "e25570034f0616372497098724ccbc9e5850f0601f6121e89e78b5beaf526912"
      },
      {
        "path": "/data2/k6tk/47/47ebcc065eb1fc858da0aeb50b4679176587f069cc31f86632728e8fd8dacc24.png",
        "sha256": "47ebcc065eb1fc858da0aeb50b4679176587f069cc31f86632728e8fd8dacc24"
      },
      {
        "path": "/data2/k6tk/ba/ba0cc32aa99381280456e79eadeefdd6183b12b483a6388e6b167757db94f8d1.png",
        "sha256": "ba0cc32aa99381280456e79eadeefdd6183b12b483a6388e6b167757db94f8d1"
      },
      {
        "path": "/data2/k6tk/35/353e7f820dfbf364c082a5184889b6dca08b18defbfda6fc377821f36184f271.png",
        "sha256": "353e7f820dfbf364c082a5184889b6dca08b18defbfda6fc377821f36184f271"
      },
      {
        "path": "/data2/k6tk/c2/c23b774a2c104f7b9d07296ccc79120e50843fad5489d01b122f84d191724fbe.png",
        "sha256": "c23b774a2c104f7b9d07296ccc79120e50843fad5489d01b122f84d191724fbe"
      },
      {
        "path": "/data2/k6tk/10/10087dbcfe1db54027bc95febf00e5451a53e05295403e2559858927d6c3dd34.png",
        "sha256": "10087dbcfe1db54027bc95febf00e5451a53e05295403e2559858927d6c3dd34"
      },
      {
        "path": "/data2/k6tk/c9/c90400315d05cfc1ce210a10a33d9013ef66f79aa3a1c20cec61f369c22742ed.png",
        "sha256": "c90400315d05cfc1ce210a10a33d9013ef66f79aa3a1c20cec61f369c22742ed"
      },
      {
        "path": "/data2/k6tk/c0/c08cebc1a489cdfe7cd40bab7f2937f8bdb46f494e805958e1a697955fe0030b.png",
        "sha256": "c08cebc1a489cdfe7cd40bab7f2937f8bdb46f494e805958e1a697955fe0030b"
      },
      {
        "path": "/data2/k6tk/01/0165be12cf1d971d23e60c4e8b98e34ade958f4793f393d83c57efeb2249da4e.png",
        "sha256": "0165be12cf1d971d23e60c4e8b98e34ade958f4793f393d83c57efeb2249da4e"
      },
      {
        "path": "/data2/k6tk/81/81976522ac40b8e79dbcb8987a0846fa0472dfe0b4b8d0c4c08f12f3696a1b4f.png",
        "sha256": "81976522ac40b8e79dbcb8987a0846fa0472dfe0b4b8d0c4c08f12f3696a1b4f"
      },
      {
        "path": "/data2/k6tk/67/67ce8913882c0baa9383de3e51e8fc51ecb4c6adc325c9aefc74d00b149a72d3.png",
        "sha256": "67ce8913882c0baa9383de3e51e8fc51ecb4c6adc325c9aefc74d00b149a72d3"
      },
      {
        "path": "/data2/k6tk/15/157704261128f8a0af3b0e9e5a338e0f6f0d59b0a0acbda5f8053e29563d3104.png",
        "sha256": "157704261128f8a0af3b0e9e5a338e0f6f0d59b0a0acbda5f8053e29563d3104"
      },
      {
        "path": "/data2/k6tk/46/46a182995bdb3fc646c751e06b82f5e5e73fff29ec8f1258bdb120e5206a3876.png",
        "sha256": "46a182995bdb3fc646c751e06b82f5e5e73fff29ec8f1258bdb120e5206a3876"
      },
      {
        "path": "/data2/k6tk/7e/7e8b03c4544d0a6731f6a03ac129f54b28f8bef0985c39ad8aa1fdde4b2d35e2.png",
        "sha256": "7e8b03c4544d0a6731f6a03ac129f54b28f8bef0985c39ad8aa1fdde4b2d35e2"
      },
      {
        "path": "/data2/k6tk/6c/6c4f0225ecc4784d32a2c95ae9c67df5fd0d8812da7fd746cb97ab4de8bb06b4.png",
        "sha256": "6c4f0225ecc4784d32a2c95ae9c67df5fd0d8812da7fd746cb97ab4de8bb06b4"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the bucket, face away from the light switch. Is the floor lamp to your left or right?",
    "timestamps": [
      0.0,
      3.8333333333333335,
      7.666666666666667,
      11.5,
      15.333333333333334,
      19.166666666666668,
      23.016666666666666,
      26.85,
      30.683333333333334,
      34.516666666666666,
      38.35,
      42.2,
      46.03333333333333,
      49.86666666666667,
      53.7,
      57.53333333333333,
      61.38333333333333,
      65.21666666666667,
      69.05,
      72.88333333333334,
      76.71666666666667,
      80.56666666666666,
      84.4,
      88.23333333333333,
      92.06666666666666,
      95.9,
      99.75,
      103.58333333333333,
      107.41666666666667,
      111.25,
      115.08333333333333,
      118.93333333333334
    ],
    "total_num_frames": 7137
  },
  "target": "<think>\nStep 1: locate the bucket, the light switch and the floor lamp.\nStep 2: standing at the bucket and facing the light switch, I find the floor lamp to my left.\nStep 3: I face away from the light switch by making a half turn. Front and back swap, and left and right swap.\nSo I find the floor lamp to my right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 8. q97eba86262f211001286db3b-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-6aab58db77b1865852d01a5716b9a2e4bafc4b50f4773909f659b805c7018664",
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q97eba86262f211001286db3b-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q97eba86262f211001286db3b",
  "paraphrase_template": "easy_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 46,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "look toward",
        "start": 35
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "left",
      "source_qid": "q97eba86262f211001286db3b-p1",
      "source_row_sha256": "64c7fd59fed4ec8a5bbaf1459d5f00cf851ded473433a3bf63f04c69acf08e4a",
      "source_store_i": 77738
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q97eba86262f211001286db3b-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "09ce0f6b0d39744baab473fcbf36621cddb75bc66be56b47027a0493a63e6b54"
  },
  "scene": "v8384d6ab39b5",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      44,
      88,
      132,
      176,
      220,
      264,
      309,
      353,
      397,
      441,
      485,
      529,
      574,
      618,
      662,
      706,
      750,
      794,
      839,
      883,
      927,
      971,
      1015,
      1059,
      1104,
      1148,
      1192,
      1236,
      1280,
      1324,
      1369
    ],
    "frames": [
      {
        "path": "/data2/k6tk/95/9560c6dad70c0007b16c86c8117766f2fef83e75b392a49177c844f73ff98ecd.png",
        "sha256": "9560c6dad70c0007b16c86c8117766f2fef83e75b392a49177c844f73ff98ecd"
      },
      {
        "path": "/data2/k6tk/de/de53e94461c28d12bec8b5cad9384955889865647ecd4724b9c0739be985f666.png",
        "sha256": "de53e94461c28d12bec8b5cad9384955889865647ecd4724b9c0739be985f666"
      },
      {
        "path": "/data2/k6tk/9b/9bf736afbf4b009f521a53865667baf0a1bfb3ffbc4744953cce0ff3862fe384.png",
        "sha256": "9bf736afbf4b009f521a53865667baf0a1bfb3ffbc4744953cce0ff3862fe384"
      },
      {
        "path": "/data2/k6tk/28/28fa88f556ad6fa509ca422497cae104ee1595d0cdb4d7ab715c0b4d01510012.png",
        "sha256": "28fa88f556ad6fa509ca422497cae104ee1595d0cdb4d7ab715c0b4d01510012"
      },
      {
        "path": "/data2/k6tk/3f/3f3f9355720ba3f9e6b108f73f8b3c87b27c458006a5928fb4dcaedb63ed09b3.png",
        "sha256": "3f3f9355720ba3f9e6b108f73f8b3c87b27c458006a5928fb4dcaedb63ed09b3"
      },
      {
        "path": "/data2/k6tk/7b/7b23f70fc53017314878dd4d4ec663a7a23a937fbd98ebac29a3144946bd6e21.png",
        "sha256": "7b23f70fc53017314878dd4d4ec663a7a23a937fbd98ebac29a3144946bd6e21"
      },
      {
        "path": "/data2/k6tk/d5/d5a42c5aac696ad914bb29e86bfe4395bf01069947f6806b733a2fee5c732359.png",
        "sha256": "d5a42c5aac696ad914bb29e86bfe4395bf01069947f6806b733a2fee5c732359"
      },
      {
        "path": "/data2/k6tk/f1/f161baf86c623c20b410d64cbf4fe8214651da3c587171a31d7bf339c8cf4c9b.png",
        "sha256": "f161baf86c623c20b410d64cbf4fe8214651da3c587171a31d7bf339c8cf4c9b"
      },
      {
        "path": "/data2/k6tk/13/13f32fdda3e47051d8f6aebec9cf601a7a4dfc23dec20e049126a60cfa5e9795.png",
        "sha256": "13f32fdda3e47051d8f6aebec9cf601a7a4dfc23dec20e049126a60cfa5e9795"
      },
      {
        "path": "/data2/k6tk/6f/6f5621fb572e0acb6696a3b423fedd08ba51ca480b38b1e058fcf735b1f0ea98.png",
        "sha256": "6f5621fb572e0acb6696a3b423fedd08ba51ca480b38b1e058fcf735b1f0ea98"
      },
      {
        "path": "/data2/k6tk/ef/ef8fec91fefa8041fd6dea823bc52028601ddd488cf974b3231535d558a15be2.png",
        "sha256": "ef8fec91fefa8041fd6dea823bc52028601ddd488cf974b3231535d558a15be2"
      },
      {
        "path": "/data2/k6tk/73/733b282185e9b928fe764c40d16f5df15629b3086767e3f87479f39039c2c7cb.png",
        "sha256": "733b282185e9b928fe764c40d16f5df15629b3086767e3f87479f39039c2c7cb"
      },
      {
        "path": "/data2/k6tk/63/631671cdfdde4fd1932fb9a7a7d425705bbada0b5312ef170f07dc5e80ecae24.png",
        "sha256": "631671cdfdde4fd1932fb9a7a7d425705bbada0b5312ef170f07dc5e80ecae24"
      },
      {
        "path": "/data2/k6tk/bf/bfeb692cfec2af4b991038e305591b55cc7f5116e724de40a9682c4a13294eae.png",
        "sha256": "bfeb692cfec2af4b991038e305591b55cc7f5116e724de40a9682c4a13294eae"
      },
      {
        "path": "/data2/k6tk/4b/4bbba07541ba51fbf62b4d8506d0cdf6c4282831f0be0731482298dfe964889b.png",
        "sha256": "4bbba07541ba51fbf62b4d8506d0cdf6c4282831f0be0731482298dfe964889b"
      },
      {
        "path": "/data2/k6tk/25/25d8f333b1ca90a10396ae50fe36f80380dbe36ff71e15c6a374bf6af9b6fe1f.png",
        "sha256": "25d8f333b1ca90a10396ae50fe36f80380dbe36ff71e15c6a374bf6af9b6fe1f"
      },
      {
        "path": "/data2/k6tk/d0/d0e704919bb31f1c3c131ecc079da490f4baecf7871507224e35b4e74eb22fd4.png",
        "sha256": "d0e704919bb31f1c3c131ecc079da490f4baecf7871507224e35b4e74eb22fd4"
      },
      {
        "path": "/data2/k6tk/b0/b093b9942b909a2fe31ef70dd4bf5363e06758d44d85eec11cee7cd8edfe2321.png",
        "sha256": "b093b9942b909a2fe31ef70dd4bf5363e06758d44d85eec11cee7cd8edfe2321"
      },
      {
        "path": "/data2/k6tk/ac/acae24dfc66d742615a0c300c582399f206d6d1a538f2fde91e11584fd4032b4.png",
        "sha256": "acae24dfc66d742615a0c300c582399f206d6d1a538f2fde91e11584fd4032b4"
      },
      {
        "path": "/data2/k6tk/10/10a1ed03330f8b3c68bb2b9dc20f947429049a98bc6fa4853cb71a6920afa961.png",
        "sha256": "10a1ed03330f8b3c68bb2b9dc20f947429049a98bc6fa4853cb71a6920afa961"
      },
      {
        "path": "/data2/k6tk/3c/3c3b2aca1b74a385a749d632423e6b996e230bdabcacbfbf067a1bbed2c35b55.png",
        "sha256": "3c3b2aca1b74a385a749d632423e6b996e230bdabcacbfbf067a1bbed2c35b55"
      },
      {
        "path": "/data2/k6tk/fc/fc55b59e7dc7d901966bc6df113a13a38739bd1d187b03325be8b66fbe087c5c.png",
        "sha256": "fc55b59e7dc7d901966bc6df113a13a38739bd1d187b03325be8b66fbe087c5c"
      },
      {
        "path": "/data2/k6tk/88/8833fdd33d961e64a4274bb549f678fef8597bad96c0774e04e7d7525ed4f98c.png",
        "sha256": "8833fdd33d961e64a4274bb549f678fef8597bad96c0774e04e7d7525ed4f98c"
      },
      {
        "path": "/data2/k6tk/f3/f30eee606d148959a1c2d584fadc558f5f86a0d9f70db3b3f25668dedc640305.png",
        "sha256": "f30eee606d148959a1c2d584fadc558f5f86a0d9f70db3b3f25668dedc640305"
      },
      {
        "path": "/data2/k6tk/8b/8b38cab0404f53e99cec4e2c6b38b97d26250a576e372e0b76e5261f112fe1bd.png",
        "sha256": "8b38cab0404f53e99cec4e2c6b38b97d26250a576e372e0b76e5261f112fe1bd"
      },
      {
        "path": "/data2/k6tk/2c/2cfc9b336e0d844ae653cd03245ea78c5f45e8ea788bb4bf09245df78e71a7ec.png",
        "sha256": "2cfc9b336e0d844ae653cd03245ea78c5f45e8ea788bb4bf09245df78e71a7ec"
      },
      {
        "path": "/data2/k6tk/17/17d79a44ac0e88c2b62370ada34bc9255f8771ae545249a2c27cd1339c064274.png",
        "sha256": "17d79a44ac0e88c2b62370ada34bc9255f8771ae545249a2c27cd1339c064274"
      },
      {
        "path": "/data2/k6tk/f3/f322947143f1f5d49ca64d51e0c4f478987aef5e940fc466ee6017511e24ea0f.png",
        "sha256": "f322947143f1f5d49ca64d51e0c4f478987aef5e940fc466ee6017511e24ea0f"
      },
      {
        "path": "/data2/k6tk/39/394c555450ed78ca350597100af5f49fc565faf6657076c2330e82b7e77bfa66.png",
        "sha256": "394c555450ed78ca350597100af5f49fc565faf6657076c2330e82b7e77bfa66"
      },
      {
        "path": "/data2/k6tk/47/47159c3f8d59eebee3a2af0f092d1c4f48a92ea7ba104eb1ee2931080c9242b7.png",
        "sha256": "47159c3f8d59eebee3a2af0f092d1c4f48a92ea7ba104eb1ee2931080c9242b7"
      },
      {
        "path": "/data2/k6tk/21/213a61324d2d1e0b9fd0fe3ae0f77c57afbf970893f1009c0dda309c10d2f171.png",
        "sha256": "213a61324d2d1e0b9fd0fe3ae0f77c57afbf970893f1009c0dda309c10d2f171"
      },
      {
        "path": "/data2/k6tk/46/46de25cc77ae38f57d3c54f696e7600a1610589dcfdfe5aaa4ec12875fadf04b.png",
        "sha256": "46de25cc77ae38f57d3c54f696e7600a1610589dcfdfe5aaa4ec12875fadf04b"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the window, face away from the mirror. Is the refrigerator to your left or right?",
    "timestamps": [
      0.0,
      1.8333333333333333,
      3.6666666666666665,
      5.5,
      7.333333333333333,
      9.166666666666666,
      11.0,
      12.875,
      14.708333333333334,
      16.541666666666668,
      18.375,
      20.208333333333332,
      22.041666666666668,
      23.916666666666668,
      25.75,
      27.583333333333332,
      29.416666666666668,
      31.25,
      33.083333333333336,
      34.958333333333336,
      36.791666666666664,
      38.625,
      40.458333333333336,
      42.291666666666664,
      44.125,
      46.0,
      47.833333333333336,
      49.666666666666664,
      51.5,
      53.333333333333336,
      55.166666666666664,
      57.041666666666664
    ],
    "total_num_frames": 1370
  },
  "target": "<think>\nStep 1: find the window and the mirror, then the refrigerator.\nStep 2: I find the refrigerator to my left when I stand at the window facing the mirror.\nStep 3: I face away from the mirror by making a half turn. Front and back swap, and left and right swap.\nSo I find the refrigerator to my right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 9. qf55ef2cb250b8727719d3bce-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-01b479afb42c8092d59fe72881dbf574144343e2680150a123d114f5f8ba8f63",
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qf55ef2cb250b8727719d3bce-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qf55ef2cb250b8727719d3bce",
  "paraphrase_template": "easy_side",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 44,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "looking at",
        "start": 34
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "left",
      "source_qid": "qf55ef2cb250b8727719d3bce-p1",
      "source_row_sha256": "45873d086c56fdf797055a3564afc4ad0d5ce4eaa8cfe358b6c3b02149babdc2",
      "source_store_i": 62097
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf55ef2cb250b8727719d3bce-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "2fa2a6ba024622c0b4840f0155d0406cb98876c2e3a17432047f10977d1a9f99"
  },
  "scene": "v4f2f916db1a2",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      291,
      582,
      873,
      1164,
      1455,
      1747,
      2038,
      2329,
      2620,
      2911,
      3203,
      3494,
      3785,
      4076,
      4367,
      4659,
      4950,
      5241,
      5532,
      5823,
      6115,
      6406,
      6697,
      6988,
      7279,
      7571,
      7862,
      8153,
      8444,
      8735,
      9027
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ec/ec4628e4fecfd182779d00cabd3ef52d17ef83d4c35bec08cfaf56f44de631ab.png",
        "sha256": "ec4628e4fecfd182779d00cabd3ef52d17ef83d4c35bec08cfaf56f44de631ab"
      },
      {
        "path": "/data2/k6tk/25/25f9cf239f9646fb8d41b817b84f7ee5830f09a2287056fbcf02a67d15474d59.png",
        "sha256": "25f9cf239f9646fb8d41b817b84f7ee5830f09a2287056fbcf02a67d15474d59"
      },
      {
        "path": "/data2/k6tk/b5/b59224ccf51e81c8f683a6607d947c4832472df1f540c0447b3e51e943e7aa1e.png",
        "sha256": "b59224ccf51e81c8f683a6607d947c4832472df1f540c0447b3e51e943e7aa1e"
      },
      {
        "path": "/data2/k6tk/ed/ed134be4f327b3eb485c1b43be5fe894d5dddc55f93dafeb12ebab83c49924f5.png",
        "sha256": "ed134be4f327b3eb485c1b43be5fe894d5dddc55f93dafeb12ebab83c49924f5"
      },
      {
        "path": "/data2/k6tk/86/86667022b1173e03d8085ef6eac7a8f4a4ee8cfacfe035ca63ab822f4af54a38.png",
        "sha256": "86667022b1173e03d8085ef6eac7a8f4a4ee8cfacfe035ca63ab822f4af54a38"
      },
      {
        "path": "/data2/k6tk/4e/4e8e50d5ed04152af51069da34cb5e24a37e25840918c2d7c002ffe11cacf224.png",
        "sha256": "4e8e50d5ed04152af51069da34cb5e24a37e25840918c2d7c002ffe11cacf224"
      },
      {
        "path": "/data2/k6tk/67/671304329ddaf5b7ce45e5a61b649c594acc07b578d5bd120cf3bed496b2744c.png",
        "sha256": "671304329ddaf5b7ce45e5a61b649c594acc07b578d5bd120cf3bed496b2744c"
      },
      {
        "path": "/data2/k6tk/82/82e59d95d2c522cd8cf461a956c36518ca081ec50392a1c3a27d2f7f44b2d190.png",
        "sha256": "82e59d95d2c522cd8cf461a956c36518ca081ec50392a1c3a27d2f7f44b2d190"
      },
      {
        "path": "/data2/k6tk/23/23ffeace058bd3c6993a8b2afaf34e9e624a2e8a0ddfb411f3be2076764b2169.png",
        "sha256": "23ffeace058bd3c6993a8b2afaf34e9e624a2e8a0ddfb411f3be2076764b2169"
      },
      {
        "path": "/data2/k6tk/90/90bb3d270d56318d42f76df4f8e599aaf6cabdbaf286a1daa4505887bd3241f6.png",
        "sha256": "90bb3d270d56318d42f76df4f8e599aaf6cabdbaf286a1daa4505887bd3241f6"
      },
      {
        "path": "/data2/k6tk/fe/fef2eea98f4080e60b49a929ea07f43824697f15287050f3e981933e7b7960af.png",
        "sha256": "fef2eea98f4080e60b49a929ea07f43824697f15287050f3e981933e7b7960af"
      },
      {
        "path": "/data2/k6tk/e0/e00f931d224d2fb8300fa4719f53821c3c8b71f5de61d4211552f6c8c932316d.png",
        "sha256": "e00f931d224d2fb8300fa4719f53821c3c8b71f5de61d4211552f6c8c932316d"
      },
      {
        "path": "/data2/k6tk/67/6767562fd56398bb344923dce08f9b866aee79a8cd7221395e8bf9249701ec81.png",
        "sha256": "6767562fd56398bb344923dce08f9b866aee79a8cd7221395e8bf9249701ec81"
      },
      {
        "path": "/data2/k6tk/d8/d854ad014bbdd9b5d7eb3c84ba0c3665c0384b7f7e04f0b30043444fecbf1918.png",
        "sha256": "d854ad014bbdd9b5d7eb3c84ba0c3665c0384b7f7e04f0b30043444fecbf1918"
      },
      {
        "path": "/data2/k6tk/15/15238de6237de469d4089cf087f678a77e73982502b4bb5c71fbe019dbe068f9.png",
        "sha256": "15238de6237de469d4089cf087f678a77e73982502b4bb5c71fbe019dbe068f9"
      },
      {
        "path": "/data2/k6tk/e1/e1d1e56d9a1bf5cd5260e5cedaf64cfa03bdcdcf2a85b024035f184eb0198f85.png",
        "sha256": "e1d1e56d9a1bf5cd5260e5cedaf64cfa03bdcdcf2a85b024035f184eb0198f85"
      },
      {
        "path": "/data2/k6tk/77/7779b0ae2b00defb247286dd74e397d8379fb1a95c70cdea8b243d8d9d270f45.png",
        "sha256": "7779b0ae2b00defb247286dd74e397d8379fb1a95c70cdea8b243d8d9d270f45"
      },
      {
        "path": "/data2/k6tk/34/341d3aac8b3882f114fe92cfc8e5f73a22b60c49d9a4ac01272446d778d4090e.png",
        "sha256": "341d3aac8b3882f114fe92cfc8e5f73a22b60c49d9a4ac01272446d778d4090e"
      },
      {
        "path": "/data2/k6tk/e6/e6e07ce60585bae043037eb7c9626a67d0fcd343bc4e266d87fdca89b278f5d6.png",
        "sha256": "e6e07ce60585bae043037eb7c9626a67d0fcd343bc4e266d87fdca89b278f5d6"
      },
      {
        "path": "/data2/k6tk/d2/d245aaeefc37e5eca46089da0662ac0ae9b6084bb989f41b90c749f557113acc.png",
        "sha256": "d245aaeefc37e5eca46089da0662ac0ae9b6084bb989f41b90c749f557113acc"
      },
      {
        "path": "/data2/k6tk/95/95b26072838c941cc688714aff06bf7ba361b397497a196530c7d196bff47b18.png",
        "sha256": "95b26072838c941cc688714aff06bf7ba361b397497a196530c7d196bff47b18"
      },
      {
        "path": "/data2/k6tk/8e/8e6dae987e932fb4db1f53565b03cc3166e90f3cea98fcb3840b4f63831ac7a4.png",
        "sha256": "8e6dae987e932fb4db1f53565b03cc3166e90f3cea98fcb3840b4f63831ac7a4"
      },
      {
        "path": "/data2/k6tk/6e/6e52045adb553a16eb2c56d250d49e4d447c9492d71d425b8bccc26c0e88fbdd.png",
        "sha256": "6e52045adb553a16eb2c56d250d49e4d447c9492d71d425b8bccc26c0e88fbdd"
      },
      {
        "path": "/data2/k6tk/f1/f12ac947e09028a28208e80ddcedb75d1c3f19339990cf0cfc370d899e64787d.png",
        "sha256": "f12ac947e09028a28208e80ddcedb75d1c3f19339990cf0cfc370d899e64787d"
      },
      {
        "path": "/data2/k6tk/d3/d3316a3ae622292543b8635212d9e9cc68cd70b6bc6ba55fe606bbb3834873e9.png",
        "sha256": "d3316a3ae622292543b8635212d9e9cc68cd70b6bc6ba55fe606bbb3834873e9"
      },
      {
        "path": "/data2/k6tk/6a/6a04973e79c7c3c81f2892df2f7d9db595c515efab29f865cd8c48b6eb684321.png",
        "sha256": "6a04973e79c7c3c81f2892df2f7d9db595c515efab29f865cd8c48b6eb684321"
      },
      {
        "path": "/data2/k6tk/18/18cca60985c9944c28dd057ae95b403d111c4ebc8a07b7a6bd7945b2c77e6d03.png",
        "sha256": "18cca60985c9944c28dd057ae95b403d111c4ebc8a07b7a6bd7945b2c77e6d03"
      },
      {
        "path": "/data2/k6tk/07/078f50e135f8eb999a0aa183ab4af6e30c592da695f9f5bb2316f637e551521b.png",
        "sha256": "078f50e135f8eb999a0aa183ab4af6e30c592da695f9f5bb2316f637e551521b"
      },
      {
        "path": "/data2/k6tk/9e/9e038a8af21e9a8e8af8baee1a51c338656a51f6a3b9fd62048d058546d3c88b.png",
        "sha256": "9e038a8af21e9a8e8af8baee1a51c338656a51f6a3b9fd62048d058546d3c88b"
      },
      {
        "path": "/data2/k6tk/71/714899fa3f4cca8047204be76c91d16acab51bffdbb94b6a50597a8e5428f594.png",
        "sha256": "714899fa3f4cca8047204be76c91d16acab51bffdbb94b6a50597a8e5428f594"
      },
      {
        "path": "/data2/k6tk/e9/e9c93bd8e9047bb256a75e83a7ccff1e1e0c37ade50ee7bb757011333fc7625a.png",
        "sha256": "e9c93bd8e9047bb256a75e83a7ccff1e1e0c37ade50ee7bb757011333fc7625a"
      },
      {
        "path": "/data2/k6tk/d8/d87d82d87f73b984db7bbd84272968651d0b42f61feeb0d93f196f715276688a.png",
        "sha256": "d87d82d87f73b984db7bbd84272968651d0b42f61feeb0d93f196f715276688a"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "While standing by the cushion and facing away from the tv, decide whether the kettle lies to your left or your right.",
    "timestamps": [
      0.0,
      4.85,
      9.7,
      14.55,
      19.4,
      24.25,
      29.116666666666667,
      33.96666666666667,
      38.81666666666667,
      43.666666666666664,
      48.516666666666666,
      53.38333333333333,
      58.233333333333334,
      63.083333333333336,
      67.93333333333334,
      72.78333333333333,
      77.65,
      82.5,
      87.35,
      92.2,
      97.05,
      101.91666666666667,
      106.76666666666667,
      111.61666666666666,
      116.46666666666667,
      121.31666666666666,
      126.18333333333334,
      131.03333333333333,
      135.88333333333333,
      140.73333333333332,
      145.58333333333334,
      150.45
    ],
    "total_num_frames": 9028
  },
  "target": "<think>\nStep 1: find the cushion, the tv and the kettle.\nStep 2: facing the tv from the cushion, I find the kettle to my left.\nStep 3: I face away from the tv by making a half turn. Front and back swap, and left and right swap.\nSo I find the kettle to my right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 10. qbac55132314115abdf312eba-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-e9be3f8644fafa45e1c6e6caa6c844cd78417437fbe6c7f952b281f474c8d605",
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qbac55132314115abdf312eba-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qbac55132314115abdf312eba",
  "paraphrase_template": "easy_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 48,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "look toward",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "left",
      "source_qid": "qbac55132314115abdf312eba-p1",
      "source_row_sha256": "40e661a12201a1805e548d9da2bdffd105f96a5fca6eceafa5e64abe4fdcd96a",
      "source_store_i": 74101
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qbac55132314115abdf312eba-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "d8150548ecf354eeb83738ca075eedc29e88f7976f209f56982407019175c1be"
  },
  "scene": "v0bc1e98d75fd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      35,
      71,
      107,
      142,
      178,
      214,
      249,
      285,
      321,
      356,
      392,
      428,
      463,
      499,
      535,
      570,
      606,
      642,
      677,
      713,
      749,
      784,
      820,
      856,
      891,
      927,
      963,
      998,
      1034,
      1070,
      1106
    ],
    "frames": [
      {
        "path": "/data2/k6tk/97/9702e7923a68b22d22790a07af2a43fbc88b39c88f1f008e73233dc679e9aab1.png",
        "sha256": "9702e7923a68b22d22790a07af2a43fbc88b39c88f1f008e73233dc679e9aab1"
      },
      {
        "path": "/data2/k6tk/9e/9e2d2f03821a36fad741ef93721572f3054270a8defe4284b259acb12c5556b1.png",
        "sha256": "9e2d2f03821a36fad741ef93721572f3054270a8defe4284b259acb12c5556b1"
      },
      {
        "path": "/data2/k6tk/55/5571c2d84db21b37249ba5001a4d52584961b924fee1b2159a771bed9f0f850b.png",
        "sha256": "5571c2d84db21b37249ba5001a4d52584961b924fee1b2159a771bed9f0f850b"
      },
      {
        "path": "/data2/k6tk/22/229fee18808352eecb7ed68dfa182ec65f07643a225f499fa5db9741ef841a87.png",
        "sha256": "229fee18808352eecb7ed68dfa182ec65f07643a225f499fa5db9741ef841a87"
      },
      {
        "path": "/data2/k6tk/13/138e5ebd90b88037e70fe01e4c69ac5f05014447d426dd8fad1aed91e6f86c61.png",
        "sha256": "138e5ebd90b88037e70fe01e4c69ac5f05014447d426dd8fad1aed91e6f86c61"
      },
      {
        "path": "/data2/k6tk/d0/d06c5ed2e786dc3bbe1d4a5de1bea71fa3cbc2818b40008d026fb711e50b859a.png",
        "sha256": "d06c5ed2e786dc3bbe1d4a5de1bea71fa3cbc2818b40008d026fb711e50b859a"
      },
      {
        "path": "/data2/k6tk/f7/f7806cd44cebee9b9abeaf4ee19a8fbfe43128a5fe1629bd4860abbdaf82b1da.png",
        "sha256": "f7806cd44cebee9b9abeaf4ee19a8fbfe43128a5fe1629bd4860abbdaf82b1da"
      },
      {
        "path": "/data2/k6tk/78/78bb779f2e79c21db60e6acef79f767519464e49cb65dfdc81ab70102e183dff.png",
        "sha256": "78bb779f2e79c21db60e6acef79f767519464e49cb65dfdc81ab70102e183dff"
      },
      {
        "path": "/data2/k6tk/e9/e96b50eed91a38a02c507ebb10b5d3217bd2634b53ead9160dd59f4e8c968b12.png",
        "sha256": "e96b50eed91a38a02c507ebb10b5d3217bd2634b53ead9160dd59f4e8c968b12"
      },
      {
        "path": "/data2/k6tk/8d/8db79f5d1fab0f9bf07af03a3ce3acb09bc91dde2383c7f7c8c287493d09d891.png",
        "sha256": "8db79f5d1fab0f9bf07af03a3ce3acb09bc91dde2383c7f7c8c287493d09d891"
      },
      {
        "path": "/data2/k6tk/65/65bdc5c34d383d756c8b60e567779adbe948cbe9038f4d5de9fdb655672a00e4.png",
        "sha256": "65bdc5c34d383d756c8b60e567779adbe948cbe9038f4d5de9fdb655672a00e4"
      },
      {
        "path": "/data2/k6tk/1b/1b94f5358c9b277887de2f47b9a42bd6dee226aa565b863a7fa00526d34e9911.png",
        "sha256": "1b94f5358c9b277887de2f47b9a42bd6dee226aa565b863a7fa00526d34e9911"
      },
      {
        "path": "/data2/k6tk/eb/eb0c501d7ceaf555e7bc4da6d73dbd7a8d11ec0bbaacda76a86c213ffdab320b.png",
        "sha256": "eb0c501d7ceaf555e7bc4da6d73dbd7a8d11ec0bbaacda76a86c213ffdab320b"
      },
      {
        "path": "/data2/k6tk/73/73158aeeb0a005a427796009e766280dcc4c8fa72c829a2e8da8b5ea50db37a8.png",
        "sha256": "73158aeeb0a005a427796009e766280dcc4c8fa72c829a2e8da8b5ea50db37a8"
      },
      {
        "path": "/data2/k6tk/e9/e95e9bab2c06e508797967f13b4fbce922dcc092dc26f417dca477f51bbf4cf4.png",
        "sha256": "e95e9bab2c06e508797967f13b4fbce922dcc092dc26f417dca477f51bbf4cf4"
      },
      {
        "path": "/data2/k6tk/16/16dd04cfe31466d23105fafc3a519130ff2f8525dfb6e91d4fc44ec09dbdebc2.png",
        "sha256": "16dd04cfe31466d23105fafc3a519130ff2f8525dfb6e91d4fc44ec09dbdebc2"
      },
      {
        "path": "/data2/k6tk/f3/f394e9cac9e72725cbec190840d48232486007a682a5f738736c52f99533c8f7.png",
        "sha256": "f394e9cac9e72725cbec190840d48232486007a682a5f738736c52f99533c8f7"
      },
      {
        "path": "/data2/k6tk/83/83dc672a57a70c727d925589566092780a2639d5b9c2fe50482601dc498befd1.png",
        "sha256": "83dc672a57a70c727d925589566092780a2639d5b9c2fe50482601dc498befd1"
      },
      {
        "path": "/data2/k6tk/70/704997c3a9a278fc10061a7acd5b3bf785eb3a74b43b1729c4014cce9c9926f4.png",
        "sha256": "704997c3a9a278fc10061a7acd5b3bf785eb3a74b43b1729c4014cce9c9926f4"
      },
      {
        "path": "/data2/k6tk/b5/b5a7172b707485f14beb2c1270c78c655a794a2c1555aa4bf5514bf8a41191b5.png",
        "sha256": "b5a7172b707485f14beb2c1270c78c655a794a2c1555aa4bf5514bf8a41191b5"
      },
      {
        "path": "/data2/k6tk/58/58fb3f6235b29214639d738684722f842fab01167f376a1dd6e7f84370aa1d72.png",
        "sha256": "58fb3f6235b29214639d738684722f842fab01167f376a1dd6e7f84370aa1d72"
      },
      {
        "path": "/data2/k6tk/9c/9c7cccb6afec06470d732681b97969c7cf4dea813bf0833bad3319ac71801e68.png",
        "sha256": "9c7cccb6afec06470d732681b97969c7cf4dea813bf0833bad3319ac71801e68"
      },
      {
        "path": "/data2/k6tk/c5/c522d18f21689b8165738c190fde891fca59af128bad96d26298db6b3db3f8b2.png",
        "sha256": "c522d18f21689b8165738c190fde891fca59af128bad96d26298db6b3db3f8b2"
      },
      {
        "path": "/data2/k6tk/11/1152e26b5a19d37ce1e3d6c1552750979149da595f99d68d9160c4db704039bb.png",
        "sha256": "1152e26b5a19d37ce1e3d6c1552750979149da595f99d68d9160c4db704039bb"
      },
      {
        "path": "/data2/k6tk/e3/e384910afe2d908c0698031bc76391eec939cf179eb20c09ac61294ee6653431.png",
        "sha256": "e384910afe2d908c0698031bc76391eec939cf179eb20c09ac61294ee6653431"
      },
      {
        "path": "/data2/k6tk/4d/4dba1cda0e61038da969e6628335881fe77383a9ff32a924fbb62994be82ae0f.png",
        "sha256": "4dba1cda0e61038da969e6628335881fe77383a9ff32a924fbb62994be82ae0f"
      },
      {
        "path": "/data2/k6tk/5e/5e93ea0dce0798a81d684031762bc6ea9d3c3435fc23501e1e1f32d740e16121.png",
        "sha256": "5e93ea0dce0798a81d684031762bc6ea9d3c3435fc23501e1e1f32d740e16121"
      },
      {
        "path": "/data2/k6tk/37/371a3b5443b95b214b98ab7dee6df07e9256bb702d71ff8683fc6d7fe7789db9.png",
        "sha256": "371a3b5443b95b214b98ab7dee6df07e9256bb702d71ff8683fc6d7fe7789db9"
      },
      {
        "path": "/data2/k6tk/1f/1f4674b0fe5292a2cbe433a0a25c63d2c51b2034cafba54e9263b7f1fcb7c95c.png",
        "sha256": "1f4674b0fe5292a2cbe433a0a25c63d2c51b2034cafba54e9263b7f1fcb7c95c"
      },
      {
        "path": "/data2/k6tk/be/be721601279c04858b17fb4fac1de9aaa2b7202e6b4d9a74b236e77c20b2e669.png",
        "sha256": "be721601279c04858b17fb4fac1de9aaa2b7202e6b4d9a74b236e77c20b2e669"
      },
      {
        "path": "/data2/k6tk/8d/8da9b5d753ca4d753dd1f9a6723ea04651d354f567c23544b31bf85ebe3abfe6.png",
        "sha256": "8da9b5d753ca4d753dd1f9a6723ea04651d354f567c23544b31bf85ebe3abfe6"
      },
      {
        "path": "/data2/k6tk/2b/2bc00a8a48ed0ea086c02e8d22377bce556b30f1bb8bdb7c5c6979b54df40065.png",
        "sha256": "2bc00a8a48ed0ea086c02e8d22377bce556b30f1bb8bdb7c5c6979b54df40065"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the backpack, face away from the table. Is the fire extinguisher to your left or right?",
    "timestamps": [
      0.0,
      1.4583333333333333,
      2.9583333333333335,
      4.458333333333333,
      5.916666666666667,
      7.416666666666667,
      8.916666666666666,
      10.375,
      11.875,
      13.375,
      14.833333333333334,
      16.333333333333332,
      17.833333333333332,
      19.291666666666668,
      20.791666666666668,
      22.291666666666668,
      23.75,
      25.25,
      26.75,
      28.208333333333332,
      29.708333333333332,
      31.208333333333332,
      32.666666666666664,
      34.166666666666664,
      35.666666666666664,
      37.125,
      38.625,
      40.125,
      41.583333333333336,
      43.083333333333336,
      44.583333333333336,
      46.083333333333336
    ],
    "total_num_frames": 1107
  },
  "target": "<think>\nStep 1: find the backpack, the table and the fire extinguisher.\nStep 2: standing at the backpack and facing the table, I find the fire extinguisher to my left.\nStep 3: I face away from the table by making a half turn. Front and back swap, and left and right swap.\nSo I find the fire extinguisher to my right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 11. q5639bc58267dfaf14f796ec0_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-ae46c990da7785a753b26100c6b3d7c93320a5383afddf9d955c4d5453a71f6d",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q5639bc58267dfaf14f796ec0"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "front-right",
      "source_qid": "q5639bc58267dfaf14f796ec0",
      "source_row_sha256": "a05ffde7afdb467f3b48712de785a2acb59235b596e7cd9eaf3e43560b3e08ce",
      "source_store_i": 16356
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q5639bc58267dfaf14f796ec0_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "b536a06b3e4dcb96e5015ff1ddd27faf86cc7f6b59bb91b3d81cc60cd8318659"
  },
  "scene": "v288077d780a3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      475,
      951,
      1427,
      1902,
      2378,
      2854,
      3329,
      3805,
      4281,
      4757,
      5232,
      5708,
      6184,
      6659,
      7135,
      7611,
      8087,
      8562,
      9038,
      9514,
      9989,
      10465,
      10941,
      11417,
      11892,
      12368,
      12844,
      13319,
      13795,
      14271,
      14747
    ],
    "frames": [
      {
        "path": "/data2/k6tk/63/638fd85c0c8a68f8fc05045c52f0e1b137dce38b6f1541f67a6fe069a2bcf684.png",
        "sha256": "638fd85c0c8a68f8fc05045c52f0e1b137dce38b6f1541f67a6fe069a2bcf684"
      },
      {
        "path": "/data2/k6tk/d6/d6049bd51c5207748164ac287c8df3341cb355877705d5fe3da9c5bac2db7c73.png",
        "sha256": "d6049bd51c5207748164ac287c8df3341cb355877705d5fe3da9c5bac2db7c73"
      },
      {
        "path": "/data2/k6tk/6b/6b1ebf9d31fdca040451eb7216bd7b0149e079f22e8b871e164d93ef30ccdd09.png",
        "sha256": "6b1ebf9d31fdca040451eb7216bd7b0149e079f22e8b871e164d93ef30ccdd09"
      },
      {
        "path": "/data2/k6tk/1c/1c910957881824c37c7acb669577bb5463f6d96c30bdf7144e42805c5ce2e71c.png",
        "sha256": "1c910957881824c37c7acb669577bb5463f6d96c30bdf7144e42805c5ce2e71c"
      },
      {
        "path": "/data2/k6tk/19/19e7cd9d86bed6e3770887606821cffd6ed92aa7651114651514984f5a1988c0.png",
        "sha256": "19e7cd9d86bed6e3770887606821cffd6ed92aa7651114651514984f5a1988c0"
      },
      {
        "path": "/data2/k6tk/42/42f792697cb6841a09b6a9c35f59fece18aeef859c663d2a61afb5f430ff29a5.png",
        "sha256": "42f792697cb6841a09b6a9c35f59fece18aeef859c663d2a61afb5f430ff29a5"
      },
      {
        "path": "/data2/k6tk/9b/9b0a6fe142d061c45bf95fe98a3e4af0432810b8b1842368efeda10c6c58fa63.png",
        "sha256": "9b0a6fe142d061c45bf95fe98a3e4af0432810b8b1842368efeda10c6c58fa63"
      },
      {
        "path": "/data2/k6tk/2c/2c4c2d036e77d56d4a5988929a4bf2d0df189346e20b339f6010ebca09fe00ff.png",
        "sha256": "2c4c2d036e77d56d4a5988929a4bf2d0df189346e20b339f6010ebca09fe00ff"
      },
      {
        "path": "/data2/k6tk/ec/ece28719a56266ed47ce0664803fd0268940caec01ecf804671ae22fabe6d4ce.png",
        "sha256": "ece28719a56266ed47ce0664803fd0268940caec01ecf804671ae22fabe6d4ce"
      },
      {
        "path": "/data2/k6tk/02/02a123a5cc94b7895a72100a532395749adfdfa33d4ebeac88fb8e872f39a09c.png",
        "sha256": "02a123a5cc94b7895a72100a532395749adfdfa33d4ebeac88fb8e872f39a09c"
      },
      {
        "path": "/data2/k6tk/f2/f2d3b154fc7f56f98d88bad10de0c78f3cf2ce5461b3ab17a83ac8fd614d764c.png",
        "sha256": "f2d3b154fc7f56f98d88bad10de0c78f3cf2ce5461b3ab17a83ac8fd614d764c"
      },
      {
        "path": "/data2/k6tk/29/29a7f64f7eae8f68b73898b33727f168d6d1e2a2a1f750753e1240620a038bf0.png",
        "sha256": "29a7f64f7eae8f68b73898b33727f168d6d1e2a2a1f750753e1240620a038bf0"
      },
      {
        "path": "/data2/k6tk/3e/3ef48ee1dddea0fd982bbf771ec2ef8f871f9a29cabcfb1293ee27ed6e4d8b53.png",
        "sha256": "3ef48ee1dddea0fd982bbf771ec2ef8f871f9a29cabcfb1293ee27ed6e4d8b53"
      },
      {
        "path": "/data2/k6tk/d6/d67cbbf614c493c7ba230b8e05247f6e9985d08ba78d8f1351bf5ec62565b280.png",
        "sha256": "d67cbbf614c493c7ba230b8e05247f6e9985d08ba78d8f1351bf5ec62565b280"
      },
      {
        "path": "/data2/k6tk/1a/1a41de25e74fbc22e23f315ca41f80ffd412a305b16249cafb704723ca8e10cc.png",
        "sha256": "1a41de25e74fbc22e23f315ca41f80ffd412a305b16249cafb704723ca8e10cc"
      },
      {
        "path": "/data2/k6tk/55/558ba4f7259e8daa91dc522dfac54fbe42726072ead493ef63822721c8139a51.png",
        "sha256": "558ba4f7259e8daa91dc522dfac54fbe42726072ead493ef63822721c8139a51"
      },
      {
        "path": "/data2/k6tk/68/68474783c192ead879c12edd70bf1700e16f5ef2293de449b29ecc4e7a17f7ef.png",
        "sha256": "68474783c192ead879c12edd70bf1700e16f5ef2293de449b29ecc4e7a17f7ef"
      },
      {
        "path": "/data2/k6tk/ce/ce0720716ec4ffbe2d21e78fbb312151fc8a8391cc8df4cddeb5e431db5056ff.png",
        "sha256": "ce0720716ec4ffbe2d21e78fbb312151fc8a8391cc8df4cddeb5e431db5056ff"
      },
      {
        "path": "/data2/k6tk/cb/cb021cab38928108d6efcce353f2f1e5625ffc443d02ae713dc7200f0c975796.png",
        "sha256": "cb021cab38928108d6efcce353f2f1e5625ffc443d02ae713dc7200f0c975796"
      },
      {
        "path": "/data2/k6tk/85/85d94b61b1212ab3b0c7898f8fd9b0f509746b76edd18e38ab011d540bd2dbaa.png",
        "sha256": "85d94b61b1212ab3b0c7898f8fd9b0f509746b76edd18e38ab011d540bd2dbaa"
      },
      {
        "path": "/data2/k6tk/3d/3dbf7ff57f5247570b737d4723450e8d4e549d90532a50ce1c764682819c4dc1.png",
        "sha256": "3dbf7ff57f5247570b737d4723450e8d4e549d90532a50ce1c764682819c4dc1"
      },
      {
        "path": "/data2/k6tk/2d/2dbece0c3973b875f34f70386019130c3ab4f8325180cd9b328df0561cf0b37b.png",
        "sha256": "2dbece0c3973b875f34f70386019130c3ab4f8325180cd9b328df0561cf0b37b"
      },
      {
        "path": "/data2/k6tk/bb/bb7106aac2ea86e6ec003b52a7a2c997f23c963ed71aa32780bc8d3dd2cc3339.png",
        "sha256": "bb7106aac2ea86e6ec003b52a7a2c997f23c963ed71aa32780bc8d3dd2cc3339"
      },
      {
        "path": "/data2/k6tk/00/00a75cdc08bda65a05b1e4f531b7179e53899e5e4e5d7891ff8aacb51d5f6cac.png",
        "sha256": "00a75cdc08bda65a05b1e4f531b7179e53899e5e4e5d7891ff8aacb51d5f6cac"
      },
      {
        "path": "/data2/k6tk/ae/aeb8094f58371830518498be79841e679533764422570c9278dcd04cb742f221.png",
        "sha256": "aeb8094f58371830518498be79841e679533764422570c9278dcd04cb742f221"
      },
      {
        "path": "/data2/k6tk/a0/a069c016076725bd4dbe15cf3a2a6da96fb0ce0ae1b3668169fe721e044b10d0.png",
        "sha256": "a069c016076725bd4dbe15cf3a2a6da96fb0ce0ae1b3668169fe721e044b10d0"
      },
      {
        "path": "/data2/k6tk/76/76c35e03e34e6df552330bd10df6b85b9074b9e56367b9272b60b21b6a727c18.png",
        "sha256": "76c35e03e34e6df552330bd10df6b85b9074b9e56367b9272b60b21b6a727c18"
      },
      {
        "path": "/data2/k6tk/ee/ee32aba0797ba4a7dba30b9babb80ca2a49c9e7a4c8d8e5949d8dc2c23b51ac9.png",
        "sha256": "ee32aba0797ba4a7dba30b9babb80ca2a49c9e7a4c8d8e5949d8dc2c23b51ac9"
      },
      {
        "path": "/data2/k6tk/b1/b1ba847473dedb20239c66bc2cde96ce1f92ce6bec14796058b6d7affb22fcfa.png",
        "sha256": "b1ba847473dedb20239c66bc2cde96ce1f92ce6bec14796058b6d7affb22fcfa"
      },
      {
        "path": "/data2/k6tk/8f/8f3def5e46c74fb5c489edcc2850b2442b080cde2c7c19f9d26755d2a2303cff.png",
        "sha256": "8f3def5e46c74fb5c489edcc2850b2442b080cde2c7c19f9d26755d2a2303cff"
      },
      {
        "path": "/data2/k6tk/51/51309816d43cf1a71f3d97b1716d0c9f93e0d3a428198e9436c60bd0612ac6c8.png",
        "sha256": "51309816d43cf1a71f3d97b1716d0c9f93e0d3a428198e9436c60bd0612ac6c8"
      },
      {
        "path": "/data2/k6tk/bf/bf0e3926eae55f43d8942dc67da42f18c78e7c038eeb846ca29b45062bb53d3a.png",
        "sha256": "bf0e3926eae55f43d8942dc67da42f18c78e7c038eeb846ca29b45062bb53d3a"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-left",
      "D. back-right"
    ],
    "question": "If I am standing by the bean bag and facing away from the duffel bag, is the plastic wall panel to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      7.916666666666667,
      15.85,
      23.783333333333335,
      31.7,
      39.63333333333333,
      47.56666666666667,
      55.483333333333334,
      63.416666666666664,
      71.35,
      79.28333333333333,
      87.2,
      95.13333333333334,
      103.06666666666666,
      110.98333333333333,
      118.91666666666667,
      126.85,
      134.78333333333333,
      142.7,
      150.63333333333333,
      158.56666666666666,
      166.48333333333332,
      174.41666666666666,
      182.35,
      190.28333333333333,
      198.2,
      206.13333333333333,
      214.06666666666666,
      221.98333333333332,
      229.91666666666666,
      237.85,
      245.78333333333333
    ],
    "total_num_frames": 14748
  },
  "target": "<think>\nStep 1: locate the plastic wall panel, the bean bag and the duffel bag.\nStep 2: I find the plastic wall panel in front of me, on my right when I stand at the bean bag facing the duffel bag.\nStep 3: I face away from the duffel bag by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the plastic wall panel at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 12. q0e2c86e9426361b314e888ba_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-374b6dcce1b1ebffbcdf7ce11173273d99f6b66c31a20d7dc5ad7936765dca2a",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q0e2c86e9426361b314e888ba"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 44,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 38
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "front-right",
      "source_qid": "q0e2c86e9426361b314e888ba",
      "source_row_sha256": "c90d4b46474864101f134ca1ae32688ba6673a7e2debe4c0023280d11c321182",
      "source_store_i": 31132
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q0e2c86e9426361b314e888ba_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "1eb76a8b26fa4e8811332f2b1ef3d0ac8dbe5b794f07d3320c1988726a9255d1"
  },
  "scene": "v1d95811c132c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      244,
      489,
      734,
      979,
      1224,
      1469,
      1714,
      1959,
      2204,
      2449,
      2694,
      2939,
      3184,
      3429,
      3674,
      3919,
      4164,
      4409,
      4654,
      4899,
      5144,
      5389,
      5634,
      5879,
      6124,
      6369,
      6614,
      6859,
      7104,
      7349,
      7594
    ],
    "frames": [
      {
        "path": "/data2/k6tk/69/69dffb333a9ac8a7e3c8d3013c150c19a1b5b8a8463a2052f75a586c5ca892d6.png",
        "sha256": "69dffb333a9ac8a7e3c8d3013c150c19a1b5b8a8463a2052f75a586c5ca892d6"
      },
      {
        "path": "/data2/k6tk/e3/e38d556d9febaea08e28a3a5c1187716ce5e6e622dd30ec7a914f7f83a56d140.png",
        "sha256": "e38d556d9febaea08e28a3a5c1187716ce5e6e622dd30ec7a914f7f83a56d140"
      },
      {
        "path": "/data2/k6tk/d3/d3c9231df50b9a1b0e679c62a7c3bd5b284723787cb7d5d77b38e8c5e0861944.png",
        "sha256": "d3c9231df50b9a1b0e679c62a7c3bd5b284723787cb7d5d77b38e8c5e0861944"
      },
      {
        "path": "/data2/k6tk/c6/c65cb57b5e9c639bc14f86a3d4bf3d548ff77aea02d130c602d76e68578aca1c.png",
        "sha256": "c65cb57b5e9c639bc14f86a3d4bf3d548ff77aea02d130c602d76e68578aca1c"
      },
      {
        "path": "/data2/k6tk/bc/bcaec7d3c28a7f24fb04d249758fc6174951d171faf19444bc03d43b9b86035d.png",
        "sha256": "bcaec7d3c28a7f24fb04d249758fc6174951d171faf19444bc03d43b9b86035d"
      },
      {
        "path": "/data2/k6tk/16/162de9f856ae557cfc0da06ddd459acb6a81cd1fdccbbb0cb63ad6af3c6178c9.png",
        "sha256": "162de9f856ae557cfc0da06ddd459acb6a81cd1fdccbbb0cb63ad6af3c6178c9"
      },
      {
        "path": "/data2/k6tk/d2/d277c968dcf1552b7f929543a4b799db96e6f4d48601b3d10b4bb929a2032a47.png",
        "sha256": "d277c968dcf1552b7f929543a4b799db96e6f4d48601b3d10b4bb929a2032a47"
      },
      {
        "path": "/data2/k6tk/77/772ade632056d122a6eebe323b8df3425c139f0977cf19e1facc5fd3927b8114.png",
        "sha256": "772ade632056d122a6eebe323b8df3425c139f0977cf19e1facc5fd3927b8114"
      },
      {
        "path": "/data2/k6tk/50/50be710dc4cb5cba3cae730ef2f7d133a1506323f25de0567d003158ca9b848f.png",
        "sha256": "50be710dc4cb5cba3cae730ef2f7d133a1506323f25de0567d003158ca9b848f"
      },
      {
        "path": "/data2/k6tk/d0/d0e4ca007afbedf2786cd4ac7ab279a7ec7def82741cbbda46dad15b99b7d308.png",
        "sha256": "d0e4ca007afbedf2786cd4ac7ab279a7ec7def82741cbbda46dad15b99b7d308"
      },
      {
        "path": "/data2/k6tk/4e/4ec67a400abd875090d02be61bf69f34d1b917a4a7814fe7bcd7dd07377e051b.png",
        "sha256": "4ec67a400abd875090d02be61bf69f34d1b917a4a7814fe7bcd7dd07377e051b"
      },
      {
        "path": "/data2/k6tk/ea/eae20ac922b8c473accf0ef4c7a85089210719f062a4e836ba910599f8e009fb.png",
        "sha256": "eae20ac922b8c473accf0ef4c7a85089210719f062a4e836ba910599f8e009fb"
      },
      {
        "path": "/data2/k6tk/e1/e10cfdd6bbbc4f56496ba516a1bac2773bc52a25ba20d6a0065097fa9e228d66.png",
        "sha256": "e10cfdd6bbbc4f56496ba516a1bac2773bc52a25ba20d6a0065097fa9e228d66"
      },
      {
        "path": "/data2/k6tk/8f/8f5eb07ce70df08c680e268fba54e409e81c43813b99297af68abf4346fcc52a.png",
        "sha256": "8f5eb07ce70df08c680e268fba54e409e81c43813b99297af68abf4346fcc52a"
      },
      {
        "path": "/data2/k6tk/a5/a5aff352f72a78e1eae9479c8c85b3a179a4cbb51dcae9f2f82f320cd3013315.png",
        "sha256": "a5aff352f72a78e1eae9479c8c85b3a179a4cbb51dcae9f2f82f320cd3013315"
      },
      {
        "path": "/data2/k6tk/97/97404c167067967ca0a5b1f6014931d69babb6b5f1de3688ecaef48a23c597c7.png",
        "sha256": "97404c167067967ca0a5b1f6014931d69babb6b5f1de3688ecaef48a23c597c7"
      },
      {
        "path": "/data2/k6tk/19/19e9ee0f31f95191a3375158b39c10a19fc908b5550928ba2b889d083fa795c0.png",
        "sha256": "19e9ee0f31f95191a3375158b39c10a19fc908b5550928ba2b889d083fa795c0"
      },
      {
        "path": "/data2/k6tk/5b/5bf4efd88c45e0c975bb8f12601b66249a337597b4756f09d2d645bd81a0abb4.png",
        "sha256": "5bf4efd88c45e0c975bb8f12601b66249a337597b4756f09d2d645bd81a0abb4"
      },
      {
        "path": "/data2/k6tk/4c/4c80674dd9fe2088f637932b96fdc7153ced8bcbc60d9973184e177add9b39cc.png",
        "sha256": "4c80674dd9fe2088f637932b96fdc7153ced8bcbc60d9973184e177add9b39cc"
      },
      {
        "path": "/data2/k6tk/43/4378829303b9b1d00e05bf64b99df5ed45ede25caa784fba257797229eae35d9.png",
        "sha256": "4378829303b9b1d00e05bf64b99df5ed45ede25caa784fba257797229eae35d9"
      },
      {
        "path": "/data2/k6tk/fe/feb9a69f49658e4f8b76a9022e64e1277bb784b8ebd1eca81b810bdfd2cf0a43.png",
        "sha256": "feb9a69f49658e4f8b76a9022e64e1277bb784b8ebd1eca81b810bdfd2cf0a43"
      },
      {
        "path": "/data2/k6tk/e2/e21f5383ed5bec1f63850a5000b884047d8f1a707f8d3a6344b30f9559711183.png",
        "sha256": "e21f5383ed5bec1f63850a5000b884047d8f1a707f8d3a6344b30f9559711183"
      },
      {
        "path": "/data2/k6tk/ef/ef20494724f9764faf0af64dcf03d1cd7d8b107674a225482935a03787a7effd.png",
        "sha256": "ef20494724f9764faf0af64dcf03d1cd7d8b107674a225482935a03787a7effd"
      },
      {
        "path": "/data2/k6tk/0e/0e78418ca8915ce90e70d88e8db8a9f47731defff4dcd14239ab9f54a3862651.png",
        "sha256": "0e78418ca8915ce90e70d88e8db8a9f47731defff4dcd14239ab9f54a3862651"
      },
      {
        "path": "/data2/k6tk/3c/3c11d775a787ce1e4b44e54a10828bc2397b5278cde8867fb8a30a0480a3bddb.png",
        "sha256": "3c11d775a787ce1e4b44e54a10828bc2397b5278cde8867fb8a30a0480a3bddb"
      },
      {
        "path": "/data2/k6tk/70/7012122957be45085549f8da511dd44fff6a0587a1c3f60f10391c6b41510af8.png",
        "sha256": "7012122957be45085549f8da511dd44fff6a0587a1c3f60f10391c6b41510af8"
      },
      {
        "path": "/data2/k6tk/c3/c339cf5a9449ded808b10d52adc247cd4530ebd0d9a0ec8fa530d42b421b300b.png",
        "sha256": "c339cf5a9449ded808b10d52adc247cd4530ebd0d9a0ec8fa530d42b421b300b"
      },
      {
        "path": "/data2/k6tk/cb/cbfd2983a13f3d3bafb1c8b7c5aa34d3a3176e1dc1d22233dcbe3321c9545fff.png",
        "sha256": "cbfd2983a13f3d3bafb1c8b7c5aa34d3a3176e1dc1d22233dcbe3321c9545fff"
      },
      {
        "path": "/data2/k6tk/6a/6abbaff9db33904106618984a87a38f0561c2b040a3c037e7d3ef727e32ebea2.png",
        "sha256": "6abbaff9db33904106618984a87a38f0561c2b040a3c037e7d3ef727e32ebea2"
      },
      {
        "path": "/data2/k6tk/30/307f76179a4f26ff42dc2b982f4446c2264c761ab11ddb6441a59da43deed204.png",
        "sha256": "307f76179a4f26ff42dc2b982f4446c2264c761ab11ddb6441a59da43deed204"
      },
      {
        "path": "/data2/k6tk/6a/6a56e3877f3d0c85fbbc5190b60d51e7409b275dfd51b3d3c7fe7acc48498c9c.png",
        "sha256": "6a56e3877f3d0c85fbbc5190b60d51e7409b275dfd51b3d3c7fe7acc48498c9c"
      },
      {
        "path": "/data2/k6tk/24/247751b6ccd61e4243cd431336490058ad5eedff99b9e3ba229841d23784c61c.png",
        "sha256": "247751b6ccd61e4243cd431336490058ad5eedff99b9e3ba229841d23784c61c"
      }
    ],
    "options": [
      "A. back-right",
      "B. back-left",
      "C. front-left",
      "D. front-right"
    ],
    "question": "If I am standing by the air fryer and facing away from the brush, is the door to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      4.066666666666666,
      8.15,
      12.233333333333333,
      16.316666666666666,
      20.4,
      24.483333333333334,
      28.566666666666666,
      32.65,
      36.733333333333334,
      40.81666666666667,
      44.9,
      48.983333333333334,
      53.06666666666667,
      57.15,
      61.233333333333334,
      65.31666666666666,
      69.4,
      73.48333333333333,
      77.56666666666666,
      81.65,
      85.73333333333333,
      89.81666666666666,
      93.9,
      97.98333333333333,
      102.06666666666666,
      106.15,
      110.23333333333333,
      114.31666666666666,
      118.4,
      122.48333333333333,
      126.56666666666666
    ],
    "total_num_frames": 7595
  },
  "target": "<think>\nStep 1: find the air fryer, the brush and the door.\nStep 2: standing at the air fryer and facing the brush, I find the door in front of me, on my right.\nStep 3: I face away from the brush by making a half turn. Front and back swap, and left and right swap.\nSo I find the door at my back-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 13. qf6ca4ab445d3756d97a89a00_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-110c2443a1940229c14547205f3f82d07a4ca54d2f360982418cabe57f399650",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qf6ca4ab445d3756d97a89a00"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 51,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 45
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "front-right",
      "source_qid": "qf6ca4ab445d3756d97a89a00",
      "source_row_sha256": "1b4678a04ef9d2dd6b99dca5cf673f164e2f93971fe523f0cf974392ac798cb3",
      "source_store_i": 24411
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf6ca4ab445d3756d97a89a00_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "7b60e8ba1381815f9209551a40b1a3a373c17ab0a18fe19566401089cddaad44"
  },
  "scene": "v012679495aa0",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      424,
      848,
      1272,
      1696,
      2120,
      2544,
      2968,
      3392,
      3816,
      4240,
      4664,
      5088,
      5512,
      5936,
      6360,
      6785,
      7209,
      7633,
      8057,
      8481,
      8905,
      9329,
      9753,
      10177,
      10601,
      11025,
      11449,
      11873,
      12297,
      12721,
      13146
    ],
    "frames": [
      {
        "path": "/data2/k6tk/cc/ccdc856e36532016bcb415134431ef53179f3b1182c103e982d794609a5ebd9e.png",
        "sha256": "ccdc856e36532016bcb415134431ef53179f3b1182c103e982d794609a5ebd9e"
      },
      {
        "path": "/data2/k6tk/8d/8da2bdce9d3d31039185d553ef4e492face8a3227f6b7639bf25fedf9857aa0a.png",
        "sha256": "8da2bdce9d3d31039185d553ef4e492face8a3227f6b7639bf25fedf9857aa0a"
      },
      {
        "path": "/data2/k6tk/d4/d4e8660cd8e1174042f049fa9c428f38b8e26dfa52425493cda6c6459c57764c.png",
        "sha256": "d4e8660cd8e1174042f049fa9c428f38b8e26dfa52425493cda6c6459c57764c"
      },
      {
        "path": "/data2/k6tk/33/3304fb3179c2b0b6a77a68737b46fc98775d778e6dd0e06c6d1bc9d8a4826c7c.png",
        "sha256": "3304fb3179c2b0b6a77a68737b46fc98775d778e6dd0e06c6d1bc9d8a4826c7c"
      },
      {
        "path": "/data2/k6tk/b7/b7bbd1e8a40889d9fa390554faa7b322395ede5c42f4639bae9126111bf2da4c.png",
        "sha256": "b7bbd1e8a40889d9fa390554faa7b322395ede5c42f4639bae9126111bf2da4c"
      },
      {
        "path": "/data2/k6tk/51/51ff2825eb25469ab547f2015abfcc11a632a2db86673ced6c9935cd4b4bf790.png",
        "sha256": "51ff2825eb25469ab547f2015abfcc11a632a2db86673ced6c9935cd4b4bf790"
      },
      {
        "path": "/data2/k6tk/b0/b0561819c09155bf4eaf3db775cfd88eea3d4c75ff89befeb482c0f02c5e8a8a.png",
        "sha256": "b0561819c09155bf4eaf3db775cfd88eea3d4c75ff89befeb482c0f02c5e8a8a"
      },
      {
        "path": "/data2/k6tk/47/4769017fae5a3d25077dbf09874df89838e4796cb2563efe696c97f3342974f6.png",
        "sha256": "4769017fae5a3d25077dbf09874df89838e4796cb2563efe696c97f3342974f6"
      },
      {
        "path": "/data2/k6tk/a3/a3eb916bca124f6bd4a97409a7c2d004031572c0bf39f0b0b9477800ecd22887.png",
        "sha256": "a3eb916bca124f6bd4a97409a7c2d004031572c0bf39f0b0b9477800ecd22887"
      },
      {
        "path": "/data2/k6tk/ac/acffb07888cfe92e9970048082b28fdbe9e6d40df5a88ea04a33d1f16f392bb8.png",
        "sha256": "acffb07888cfe92e9970048082b28fdbe9e6d40df5a88ea04a33d1f16f392bb8"
      },
      {
        "path": "/data2/k6tk/67/673c377a5b7c761d8e5ac7ba3111021c87b1fd0e4b82fb33dc0c86870924b738.png",
        "sha256": "673c377a5b7c761d8e5ac7ba3111021c87b1fd0e4b82fb33dc0c86870924b738"
      },
      {
        "path": "/data2/k6tk/a2/a298062dcaacbfe473a6cd6a1129387b9e2451df90f54cca90d5947370b0d049.png",
        "sha256": "a298062dcaacbfe473a6cd6a1129387b9e2451df90f54cca90d5947370b0d049"
      },
      {
        "path": "/data2/k6tk/af/af12e9c08495f7f6d3b90f379a1206c86127a1ab7df896b305a93cbd178b2c6b.png",
        "sha256": "af12e9c08495f7f6d3b90f379a1206c86127a1ab7df896b305a93cbd178b2c6b"
      },
      {
        "path": "/data2/k6tk/c0/c0053202e5265972aa4daedd8afd776f12fe3e7213fc18e64a5b7107bacc2d45.png",
        "sha256": "c0053202e5265972aa4daedd8afd776f12fe3e7213fc18e64a5b7107bacc2d45"
      },
      {
        "path": "/data2/k6tk/a5/a5c40835fdb7ba651da5e07d00ff741f69401f922d935a1fa426c9b234fc4dda.png",
        "sha256": "a5c40835fdb7ba651da5e07d00ff741f69401f922d935a1fa426c9b234fc4dda"
      },
      {
        "path": "/data2/k6tk/5b/5b86bca08359f2be853b5d75a94fab2700c903bec48e6f3ef8b8f9968ec2bf26.png",
        "sha256": "5b86bca08359f2be853b5d75a94fab2700c903bec48e6f3ef8b8f9968ec2bf26"
      },
      {
        "path": "/data2/k6tk/29/29225f2d0a10756fca9dc48565c42200a670b6fb64bb891959616ab9c75f6de9.png",
        "sha256": "29225f2d0a10756fca9dc48565c42200a670b6fb64bb891959616ab9c75f6de9"
      },
      {
        "path": "/data2/k6tk/e4/e4570397dfdce7fa2d761e24089a3b738fe5eaa6acd0cd8bff45f4c7d7c21ece.png",
        "sha256": "e4570397dfdce7fa2d761e24089a3b738fe5eaa6acd0cd8bff45f4c7d7c21ece"
      },
      {
        "path": "/data2/k6tk/69/69c0ed00ec1e86dc9484f4dd860f190432315409f4ac9b04134544d9cda8d9bc.png",
        "sha256": "69c0ed00ec1e86dc9484f4dd860f190432315409f4ac9b04134544d9cda8d9bc"
      },
      {
        "path": "/data2/k6tk/8d/8dee45999e439b5cb0271a07e38ba8e8fbadb64685245d7689b4f31f1d7ffa16.png",
        "sha256": "8dee45999e439b5cb0271a07e38ba8e8fbadb64685245d7689b4f31f1d7ffa16"
      },
      {
        "path": "/data2/k6tk/9c/9cf1d853cc15426813d3111100b74ae6a1818dfc4f14f459c2099dc00269713d.png",
        "sha256": "9cf1d853cc15426813d3111100b74ae6a1818dfc4f14f459c2099dc00269713d"
      },
      {
        "path": "/data2/k6tk/43/4357030ca793e8ec535eaa4adf6a5fa4967b7c2a203a4ba3173d711ad093dd21.png",
        "sha256": "4357030ca793e8ec535eaa4adf6a5fa4967b7c2a203a4ba3173d711ad093dd21"
      },
      {
        "path": "/data2/k6tk/9b/9beb516d3ee903489675a722dd8b850e8178df4a93c4281b506749129941d84e.png",
        "sha256": "9beb516d3ee903489675a722dd8b850e8178df4a93c4281b506749129941d84e"
      },
      {
        "path": "/data2/k6tk/d2/d277e5037688d8554d37ee2718a05f6acd2128f849160b3b53abd561428e571d.png",
        "sha256": "d277e5037688d8554d37ee2718a05f6acd2128f849160b3b53abd561428e571d"
      },
      {
        "path": "/data2/k6tk/7b/7bdb8e016afab26b78f742bdaf101f86cbf5fa7909b1bb3dbb9ffba87345f8c7.png",
        "sha256": "7bdb8e016afab26b78f742bdaf101f86cbf5fa7909b1bb3dbb9ffba87345f8c7"
      },
      {
        "path": "/data2/k6tk/66/662f27c2c0c8e11b1472a7a25a77a541cfcea53ab5ef596b0b3da232f81aeebe.png",
        "sha256": "662f27c2c0c8e11b1472a7a25a77a541cfcea53ab5ef596b0b3da232f81aeebe"
      },
      {
        "path": "/data2/k6tk/a4/a4ac4a9e8612858d11a8f9ebc0067a247b2829e8d1a4215e2a8e060268865d81.png",
        "sha256": "a4ac4a9e8612858d11a8f9ebc0067a247b2829e8d1a4215e2a8e060268865d81"
      },
      {
        "path": "/data2/k6tk/42/4296416bcbb69ec0e32912114ff8c2ecf21f8b90d0c39677e9dedef37215ba34.png",
        "sha256": "4296416bcbb69ec0e32912114ff8c2ecf21f8b90d0c39677e9dedef37215ba34"
      },
      {
        "path": "/data2/k6tk/81/8190814527fa606c6264e05468314f5b656bbffa613a68d12c84a6ec163c5432.png",
        "sha256": "8190814527fa606c6264e05468314f5b656bbffa613a68d12c84a6ec163c5432"
      },
      {
        "path": "/data2/k6tk/40/402bf8b98a5dc2e8c4d9213e7859058a64b071d3df2b48c32e6bcb1a55366922.png",
        "sha256": "402bf8b98a5dc2e8c4d9213e7859058a64b071d3df2b48c32e6bcb1a55366922"
      },
      {
        "path": "/data2/k6tk/56/5606e994969ab1b9b2ee07552d24badb9400cc3130beb07e15084ba82f205f59.png",
        "sha256": "5606e994969ab1b9b2ee07552d24badb9400cc3130beb07e15084ba82f205f59"
      },
      {
        "path": "/data2/k6tk/49/49f486c3a1b87e25c2a168d011da48069af6c280eaeb0d34cb3bd59ae0d9c820.png",
        "sha256": "49f486c3a1b87e25c2a168d011da48069af6c280eaeb0d34cb3bd59ae0d9c820"
      }
    ],
    "options": [
      "A. back-left",
      "B. back-right",
      "C. front-left",
      "D. front-right"
    ],
    "question": "If I am standing by the adjustable bench and facing away from the bed, is the crocs to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      7.066666666666666,
      14.133333333333333,
      21.2,
      28.266666666666666,
      35.333333333333336,
      42.4,
      49.46666666666667,
      56.53333333333333,
      63.6,
      70.66666666666667,
      77.73333333333333,
      84.8,
      91.86666666666666,
      98.93333333333334,
      106.0,
      113.08333333333333,
      120.15,
      127.21666666666667,
      134.28333333333333,
      141.35,
      148.41666666666666,
      155.48333333333332,
      162.55,
      169.61666666666667,
      176.68333333333334,
      183.75,
      190.81666666666666,
      197.88333333333333,
      204.95,
      212.01666666666668,
      219.1
    ],
    "total_num_frames": 13147
  },
  "target": "<think>\nStep 1: find the adjustable bench, the bed and the crocs.\nStep 2: I find the crocs in front of me, on my right when I stand at the adjustable bench facing the bed.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the crocs at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 14. qfcf3a9243d633a7639cb4f3c-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-f5c77fe530d24168ba8da796f41684b65081e1ff5732a7c10228dd3e1ccb3faa",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qfcf3a9243d633a7639cb4f3c-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qfcf3a9243d633a7639cb4f3c",
  "paraphrase_template": "hard_classify",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 29,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "face",
        "start": 25
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "front-right",
      "source_qid": "qfcf3a9243d633a7639cb4f3c-p1",
      "source_row_sha256": "24134ad5821f108a30d91e22f569471ca613549eb688613ff46dace91c323011",
      "source_store_i": 79440
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qfcf3a9243d633a7639cb4f3c-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "cf0fc57e4bda56105ec2acbb84fe7abda1f377a65a8d95057f16d145338c54d5"
  },
  "scene": "v24fe1502c7a1",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      232,
      464,
      696,
      928,
      1160,
      1392,
      1624,
      1856,
      2088,
      2320,
      2552,
      2784,
      3016,
      3248,
      3480,
      3712,
      3944,
      4176,
      4408,
      4640,
      4872,
      5104,
      5336,
      5568,
      5800,
      6032,
      6264,
      6496,
      6728,
      6960,
      7193
    ],
    "frames": [
      {
        "path": "/data2/k6tk/68/6840a655c7a86bed31d1960b8038f27afb4731e69fc5dbbcb991e9c6cabe8ad6.png",
        "sha256": "6840a655c7a86bed31d1960b8038f27afb4731e69fc5dbbcb991e9c6cabe8ad6"
      },
      {
        "path": "/data2/k6tk/68/68e1e6f6fa871416feb58d8eacbe796ef5d68261c9c489ac5ecb3fad8b606e10.png",
        "sha256": "68e1e6f6fa871416feb58d8eacbe796ef5d68261c9c489ac5ecb3fad8b606e10"
      },
      {
        "path": "/data2/k6tk/17/17538f377a1dda31be8b73f098ff46a4040f603419747a785d6c9d1497f384a4.png",
        "sha256": "17538f377a1dda31be8b73f098ff46a4040f603419747a785d6c9d1497f384a4"
      },
      {
        "path": "/data2/k6tk/d0/d090fc9f150ed4ea6a7f50d71e9a45a4816111e4817dd654bcfb429586d459cf.png",
        "sha256": "d090fc9f150ed4ea6a7f50d71e9a45a4816111e4817dd654bcfb429586d459cf"
      },
      {
        "path": "/data2/k6tk/7f/7f0232ec7eaded631714a305bcbee0668445fd4a05f355fcf370e4571ad29485.png",
        "sha256": "7f0232ec7eaded631714a305bcbee0668445fd4a05f355fcf370e4571ad29485"
      },
      {
        "path": "/data2/k6tk/2b/2b47eabfd634a91e247a7c7cdd1383deda173cdc82d70934e12f3805da28aba5.png",
        "sha256": "2b47eabfd634a91e247a7c7cdd1383deda173cdc82d70934e12f3805da28aba5"
      },
      {
        "path": "/data2/k6tk/71/71d784628a9a2d10a350f4d94f677ff4ae0f50df29d689443b3200662871bb1a.png",
        "sha256": "71d784628a9a2d10a350f4d94f677ff4ae0f50df29d689443b3200662871bb1a"
      },
      {
        "path": "/data2/k6tk/8c/8cb94ad0c2273255e457d7310a5701963a5a10f6acec636f7548540f9825b216.png",
        "sha256": "8cb94ad0c2273255e457d7310a5701963a5a10f6acec636f7548540f9825b216"
      },
      {
        "path": "/data2/k6tk/61/610b9d116b0df7db560d68415b108351dadfadc30a3a2fcf7abc8fcd744d3904.png",
        "sha256": "610b9d116b0df7db560d68415b108351dadfadc30a3a2fcf7abc8fcd744d3904"
      },
      {
        "path": "/data2/k6tk/91/9164532d3f634968cd5e7628e32b5bbb7c1b5058792f9b2504d005be17aa8c61.png",
        "sha256": "9164532d3f634968cd5e7628e32b5bbb7c1b5058792f9b2504d005be17aa8c61"
      },
      {
        "path": "/data2/k6tk/e9/e9a9ddb1ddcbdc0f1b29473a620919a5f7f227bbca53db5564f9bf1aaad14d98.png",
        "sha256": "e9a9ddb1ddcbdc0f1b29473a620919a5f7f227bbca53db5564f9bf1aaad14d98"
      },
      {
        "path": "/data2/k6tk/ee/ee979314fae5cb680a3791b01b60cc15c5beb4d9ba78cbf40df2dea7efe1b936.png",
        "sha256": "ee979314fae5cb680a3791b01b60cc15c5beb4d9ba78cbf40df2dea7efe1b936"
      },
      {
        "path": "/data2/k6tk/0a/0afb9f34b417fc0dff794913387c632939250478ca290d0fc9ca99f875bca029.png",
        "sha256": "0afb9f34b417fc0dff794913387c632939250478ca290d0fc9ca99f875bca029"
      },
      {
        "path": "/data2/k6tk/82/8245e33f7f698041e299c9f6dedf4327b7abe31d1971fa201a89d97fd4db067f.png",
        "sha256": "8245e33f7f698041e299c9f6dedf4327b7abe31d1971fa201a89d97fd4db067f"
      },
      {
        "path": "/data2/k6tk/03/03624b7e5544296a4c95914a86cba79d7d5692654549007669197f54dd9314a9.png",
        "sha256": "03624b7e5544296a4c95914a86cba79d7d5692654549007669197f54dd9314a9"
      },
      {
        "path": "/data2/k6tk/cc/ccf69655406159bb0112dd0606d411402cea1ca7ebb5ad948de6e9656a0e418a.png",
        "sha256": "ccf69655406159bb0112dd0606d411402cea1ca7ebb5ad948de6e9656a0e418a"
      },
      {
        "path": "/data2/k6tk/39/390bbec0776cceedf90aeb715926c5034b519cf74a9b916bc3c53aa53ecbe708.png",
        "sha256": "390bbec0776cceedf90aeb715926c5034b519cf74a9b916bc3c53aa53ecbe708"
      },
      {
        "path": "/data2/k6tk/76/765e3cccd8647232f10a317580a67835946bdcd26bb1f8c25480976b4b91a87b.png",
        "sha256": "765e3cccd8647232f10a317580a67835946bdcd26bb1f8c25480976b4b91a87b"
      },
      {
        "path": "/data2/k6tk/d5/d5e126130ee55c8fe334153c885ccf2ee72c8ba6f63988ac305bee487e4456a2.png",
        "sha256": "d5e126130ee55c8fe334153c885ccf2ee72c8ba6f63988ac305bee487e4456a2"
      },
      {
        "path": "/data2/k6tk/bb/bbd34c899b7027602ebfaff60e93e815ca056b65cdb10efc5d5e6359cfc2498d.png",
        "sha256": "bbd34c899b7027602ebfaff60e93e815ca056b65cdb10efc5d5e6359cfc2498d"
      },
      {
        "path": "/data2/k6tk/1c/1c0b57acc11bdc4751563dcc3fd1eb76891c85df18a1d1e779bfa3e23b43fb65.png",
        "sha256": "1c0b57acc11bdc4751563dcc3fd1eb76891c85df18a1d1e779bfa3e23b43fb65"
      },
      {
        "path": "/data2/k6tk/87/873f50f9ab9d6c9b7fb2ffdef010b96ab44c2317d4ca80f905d0cc3ced809114.png",
        "sha256": "873f50f9ab9d6c9b7fb2ffdef010b96ab44c2317d4ca80f905d0cc3ced809114"
      },
      {
        "path": "/data2/k6tk/4c/4c97b73c8abf5fbf3bd881b9200baf45fa3649d51cd4fdc5229b42e3601c4400.png",
        "sha256": "4c97b73c8abf5fbf3bd881b9200baf45fa3649d51cd4fdc5229b42e3601c4400"
      },
      {
        "path": "/data2/k6tk/f7/f722dfed05467f5accce8e0fc71132c874cd1c1d8e366423d169ef9cb30bb795.png",
        "sha256": "f722dfed05467f5accce8e0fc71132c874cd1c1d8e366423d169ef9cb30bb795"
      },
      {
        "path": "/data2/k6tk/75/75f916d4501b62e1e04d1d847ccc1c388e90c3df4cc586d26312a27c4479222f.png",
        "sha256": "75f916d4501b62e1e04d1d847ccc1c388e90c3df4cc586d26312a27c4479222f"
      },
      {
        "path": "/data2/k6tk/f8/f84811ed00531894f92f26c6802303947369fe2d831a4cdc35dabba1bd32b070.png",
        "sha256": "f84811ed00531894f92f26c6802303947369fe2d831a4cdc35dabba1bd32b070"
      },
      {
        "path": "/data2/k6tk/99/990df8f178fb04592b8bf64bc171884c8d20bade9de121278ad50d0b7f30258c.png",
        "sha256": "990df8f178fb04592b8bf64bc171884c8d20bade9de121278ad50d0b7f30258c"
      },
      {
        "path": "/data2/k6tk/f0/f05c44a4a8d8475f40a8ba3365aa9a43ceb5522924df45ae59e0e9178ede1495.png",
        "sha256": "f05c44a4a8d8475f40a8ba3365aa9a43ceb5522924df45ae59e0e9178ede1495"
      },
      {
        "path": "/data2/k6tk/86/86dd460ec73d9c6bc2c5c3d97e5f4b9c866a9b8f5f56b3b49f50886db308686b.png",
        "sha256": "86dd460ec73d9c6bc2c5c3d97e5f4b9c866a9b8f5f56b3b49f50886db308686b"
      },
      {
        "path": "/data2/k6tk/e8/e8fbb0475fa7133b01a01b1978580a7358c36c0c2223d1a2c689d0ce178092ed.png",
        "sha256": "e8fbb0475fa7133b01a01b1978580a7358c36c0c2223d1a2c689d0ce178092ed"
      },
      {
        "path": "/data2/k6tk/21/2139bbdb4873fb28540ad28b5cc1f308cd38b0c0f5a99426864bf23006bf024e.png",
        "sha256": "2139bbdb4873fb28540ad28b5cc1f308cd38b0c0f5a99426864bf23006bf024e"
      },
      {
        "path": "/data2/k6tk/50/50e75cdaed51202f98234bccb073eda4bb6b9f21324cb87e45c01d952646bbd6.png",
        "sha256": "50e75cdaed51202f98234bccb073eda4bb6b9f21324cb87e45c01d952646bbd6"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-left",
      "C. back-right",
      "D. front-right"
    ],
    "question": "From beside the chair, I face away from the paper bin. Which direction describes the socket strip relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.8666666666666667,
      7.733333333333333,
      11.6,
      15.466666666666667,
      19.333333333333332,
      23.2,
      27.066666666666666,
      30.933333333333334,
      34.8,
      38.666666666666664,
      42.53333333333333,
      46.4,
      50.266666666666666,
      54.13333333333333,
      58.0,
      61.86666666666667,
      65.73333333333333,
      69.6,
      73.46666666666667,
      77.33333333333333,
      81.2,
      85.06666666666666,
      88.93333333333334,
      92.8,
      96.66666666666667,
      100.53333333333333,
      104.4,
      108.26666666666667,
      112.13333333333334,
      116.0,
      119.88333333333334
    ],
    "total_num_frames": 7194
  },
  "target": "<think>\nStep 1: find the chair, the paper bin and the socket strip.\nStep 2: standing at the chair and facing the paper bin, I find the socket strip in front of me, on my right.\nStep 3: I face away from the paper bin by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the socket strip at my back-left.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 15. qcfa2695e4965d2587b7909f7_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-fe84c272ecf39fcee0bdfd650163ba16936069cc5fcd808df4fa4b9286406c47",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qcfa2695e4965d2587b7909f7"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 44,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 38
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "front-right",
      "source_qid": "qcfa2695e4965d2587b7909f7",
      "source_row_sha256": "28559c97a8fdf43c9364a6bb8ba4792dfc96cef70179b015a15d782df11f00d7",
      "source_store_i": 35409
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qcfa2695e4965d2587b7909f7_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "5e8cf7a6a5bb45baf53aaef4ce55660a52c3e71ae60c18c784bc2d787b1ff4af"
  },
  "scene": "v729d75a9a097",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      472,
      945,
      1418,
      1891,
      2363,
      2836,
      3309,
      3782,
      4254,
      4727,
      5200,
      5673,
      6146,
      6618,
      7091,
      7564,
      8037,
      8509,
      8982,
      9455,
      9928,
      10401,
      10873,
      11346,
      11819,
      12292,
      12764,
      13237,
      13710,
      14183,
      14656
    ],
    "frames": [
      {
        "path": "/data2/k6tk/2e/2e83e582589f166db2fb2d2e9bc46c5aa08b43ee358a04ff4b6e7337fd139f58.png",
        "sha256": "2e83e582589f166db2fb2d2e9bc46c5aa08b43ee358a04ff4b6e7337fd139f58"
      },
      {
        "path": "/data2/k6tk/a8/a8f7c40aee6c2d2198b3f3c9b2b479c8259dbeed9d537a92ef01123fcb9f2143.png",
        "sha256": "a8f7c40aee6c2d2198b3f3c9b2b479c8259dbeed9d537a92ef01123fcb9f2143"
      },
      {
        "path": "/data2/k6tk/39/3928df5e487929d1d3b6ce6738fbf62cc662ec7027b2bd9ad24603ed859523cd.png",
        "sha256": "3928df5e487929d1d3b6ce6738fbf62cc662ec7027b2bd9ad24603ed859523cd"
      },
      {
        "path": "/data2/k6tk/92/923a90ec9f87c1d37467997343d0a2683c38c69bc138e0e968657861117f30f0.png",
        "sha256": "923a90ec9f87c1d37467997343d0a2683c38c69bc138e0e968657861117f30f0"
      },
      {
        "path": "/data2/k6tk/57/571fa8e6fc711787f43eca001edeeaa3609540e7bd28586a9481a94fb9554b60.png",
        "sha256": "571fa8e6fc711787f43eca001edeeaa3609540e7bd28586a9481a94fb9554b60"
      },
      {
        "path": "/data2/k6tk/17/176d56b2dc62bb1f5e957bc07735f9d535e5c1ef1222a34e1ce6a019aeb3c1de.png",
        "sha256": "176d56b2dc62bb1f5e957bc07735f9d535e5c1ef1222a34e1ce6a019aeb3c1de"
      },
      {
        "path": "/data2/k6tk/40/4058e8fdc6df8b9ebe4e1c0d637e56eac940a1ca76e906706e78b27209a2e244.png",
        "sha256": "4058e8fdc6df8b9ebe4e1c0d637e56eac940a1ca76e906706e78b27209a2e244"
      },
      {
        "path": "/data2/k6tk/65/65aef633f2e378cf23de8ee5dd4c357c56fdce6bb8d8f6ab2d10f1100e9c10b9.png",
        "sha256": "65aef633f2e378cf23de8ee5dd4c357c56fdce6bb8d8f6ab2d10f1100e9c10b9"
      },
      {
        "path": "/data2/k6tk/a5/a558e1c36309494fa1046087d0574ec048c6e7fb0a750878e7d0470184642718.png",
        "sha256": "a558e1c36309494fa1046087d0574ec048c6e7fb0a750878e7d0470184642718"
      },
      {
        "path": "/data2/k6tk/fd/fd070181274d239e06b5d8af29304a3995dc2ee6bdf9c4567ea107c6dfbf99b3.png",
        "sha256": "fd070181274d239e06b5d8af29304a3995dc2ee6bdf9c4567ea107c6dfbf99b3"
      },
      {
        "path": "/data2/k6tk/0f/0ff41975d910f704da7977cd991441e54c58910c37fdbabe236181e211eddf17.png",
        "sha256": "0ff41975d910f704da7977cd991441e54c58910c37fdbabe236181e211eddf17"
      },
      {
        "path": "/data2/k6tk/3f/3fc419dd498b6961117666aca9488258b3f8b3bd42e4c7d81136873df2a749b1.png",
        "sha256": "3fc419dd498b6961117666aca9488258b3f8b3bd42e4c7d81136873df2a749b1"
      },
      {
        "path": "/data2/k6tk/eb/eb310ec891fb83c47cd24d68b671a4349d9ed8306e3429bb051c050fc0b09d6c.png",
        "sha256": "eb310ec891fb83c47cd24d68b671a4349d9ed8306e3429bb051c050fc0b09d6c"
      },
      {
        "path": "/data2/k6tk/36/365cb31f429788148752b865db002174e383641851edd2f808f5c35242003348.png",
        "sha256": "365cb31f429788148752b865db002174e383641851edd2f808f5c35242003348"
      },
      {
        "path": "/data2/k6tk/13/13b4607410c0f8ee4632f1d41a07059e02e13682df35c6a2c6eefcdc6b45a324.png",
        "sha256": "13b4607410c0f8ee4632f1d41a07059e02e13682df35c6a2c6eefcdc6b45a324"
      },
      {
        "path": "/data2/k6tk/59/59d02958a0f9ef04deb595f1fac4828150039c6c4d09c743abd63d4da43afee5.png",
        "sha256": "59d02958a0f9ef04deb595f1fac4828150039c6c4d09c743abd63d4da43afee5"
      },
      {
        "path": "/data2/k6tk/e4/e454ad84b0ec0f02d4f649afe1269cc4e38e5ad3287e0cc08b20ee7604e9891e.png",
        "sha256": "e454ad84b0ec0f02d4f649afe1269cc4e38e5ad3287e0cc08b20ee7604e9891e"
      },
      {
        "path": "/data2/k6tk/f2/f254969b44de7ce3cdf95486e54baeb52404bd028cd48c87ec17531459c2217d.png",
        "sha256": "f254969b44de7ce3cdf95486e54baeb52404bd028cd48c87ec17531459c2217d"
      },
      {
        "path": "/data2/k6tk/5b/5b8a0ff44a512b05ff5fff22af754cf491d37cca49b47d7af8411be2407e1136.png",
        "sha256": "5b8a0ff44a512b05ff5fff22af754cf491d37cca49b47d7af8411be2407e1136"
      },
      {
        "path": "/data2/k6tk/a3/a3e51776db4c237d46309fac9f7ce44ec06a0e97441e667da925446c034d12f4.png",
        "sha256": "a3e51776db4c237d46309fac9f7ce44ec06a0e97441e667da925446c034d12f4"
      },
      {
        "path": "/data2/k6tk/43/43603114cdde665226e726a5e4277a99821cd5fcb271140cb9cb263c965b222b.png",
        "sha256": "43603114cdde665226e726a5e4277a99821cd5fcb271140cb9cb263c965b222b"
      },
      {
        "path": "/data2/k6tk/70/703d1666a6105c16a4a8be20cebaa4f0211b9e0cdb7937ea65ee5c6f422f2dba.png",
        "sha256": "703d1666a6105c16a4a8be20cebaa4f0211b9e0cdb7937ea65ee5c6f422f2dba"
      },
      {
        "path": "/data2/k6tk/54/54d9953ff34f51d8091127f41c29b7a3d7a8b5adbff9e1c369262404aa357eb2.png",
        "sha256": "54d9953ff34f51d8091127f41c29b7a3d7a8b5adbff9e1c369262404aa357eb2"
      },
      {
        "path": "/data2/k6tk/65/65facaf782003754f91adc2ffadf6d644c66ff6ddc5b578e03702b82d4a38a75.png",
        "sha256": "65facaf782003754f91adc2ffadf6d644c66ff6ddc5b578e03702b82d4a38a75"
      },
      {
        "path": "/data2/k6tk/0f/0fb2cb33c76e228b4cac47173017bfc2e0f3519b8f74356214b40b7ad415841e.png",
        "sha256": "0fb2cb33c76e228b4cac47173017bfc2e0f3519b8f74356214b40b7ad415841e"
      },
      {
        "path": "/data2/k6tk/7d/7d5487df2494d089c34e80aae9c7c9afbbae67d3edf8fa3e2b44fb28a1656db6.png",
        "sha256": "7d5487df2494d089c34e80aae9c7c9afbbae67d3edf8fa3e2b44fb28a1656db6"
      },
      {
        "path": "/data2/k6tk/18/186f514e4908331ffde99610d30487a71bfed90bcde9f7b25d9eed4fdff1bc24.png",
        "sha256": "186f514e4908331ffde99610d30487a71bfed90bcde9f7b25d9eed4fdff1bc24"
      },
      {
        "path": "/data2/k6tk/87/8777e8613947f9af2ccda0f2b8781604719c4c0f8a12389dd75d5c7a4828b57a.png",
        "sha256": "8777e8613947f9af2ccda0f2b8781604719c4c0f8a12389dd75d5c7a4828b57a"
      },
      {
        "path": "/data2/k6tk/14/1449ae483fb7e5a9d4889b78617bfdabb17e2161167ab39bd860de08912ccdbd.png",
        "sha256": "1449ae483fb7e5a9d4889b78617bfdabb17e2161167ab39bd860de08912ccdbd"
      },
      {
        "path": "/data2/k6tk/8b/8bf13d0647d6769b228b3affe68a3a6b7febb39128d790e40bedeb98d9d555a8.png",
        "sha256": "8bf13d0647d6769b228b3affe68a3a6b7febb39128d790e40bedeb98d9d555a8"
      },
      {
        "path": "/data2/k6tk/c3/c30daecadb7adb8c651b449fcf839904c52e54f6bdcf1e8da0fcc01142e2dd08.png",
        "sha256": "c30daecadb7adb8c651b449fcf839904c52e54f6bdcf1e8da0fcc01142e2dd08"
      },
      {
        "path": "/data2/k6tk/57/57ae3c18f69a64677962885dd8cf17ba8087a42eea1c2ba58bb340995022daa4.png",
        "sha256": "57ae3c18f69a64677962885dd8cf17ba8087a42eea1c2ba58bb340995022daa4"
      }
    ],
    "options": [
      "A. back-left",
      "B. back-right",
      "C. front-left",
      "D. front-right"
    ],
    "question": "If I am standing by the air fryer and facing away from the basket, is the cone to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      7.866666666666666,
      15.75,
      23.633333333333333,
      31.516666666666666,
      39.38333333333333,
      47.266666666666666,
      55.15,
      63.03333333333333,
      70.9,
      78.78333333333333,
      86.66666666666667,
      94.55,
      102.43333333333334,
      110.3,
      118.18333333333334,
      126.06666666666666,
      133.95,
      141.81666666666666,
      149.7,
      157.58333333333334,
      165.46666666666667,
      173.35,
      181.21666666666667,
      189.1,
      196.98333333333332,
      204.86666666666667,
      212.73333333333332,
      220.61666666666667,
      228.5,
      236.38333333333333,
      244.26666666666668
    ],
    "total_num_frames": 14657
  },
  "target": "<think>\nStep 1: find the air fryer, the basket and the cone.\nStep 2: I find the cone in front of me, on my right when I stand at the air fryer facing the basket.\nStep 3: I face away from the basket by making a half turn. Front and back swap, and left and right swap.\nSo I find the cone at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 16. q57a52f933c2d70e286bb429b_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-08fcc6fd6e600f24c8f4cd60368c2bb63af55f98f5e63e23efcef11aee152e1d",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q57a52f933c2d70e286bb429b"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "front-left",
      "source_qid": "q57a52f933c2d70e286bb429b",
      "source_row_sha256": "19a8dee54621e2c1b3a006a189473d3b0cfde47c40913ff5fae63bb7f9b9d555",
      "source_store_i": 28613
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q57a52f933c2d70e286bb429b_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "3a5403995e6351b82ec5b704f117b3d82531162fbb8858709005742faa050588"
  },
  "scene": "v4b81abe1659e",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      177,
      355,
      532,
      710,
      887,
      1065,
      1243,
      1420,
      1598,
      1775,
      1953,
      2130,
      2308,
      2486,
      2663,
      2841,
      3018,
      3196,
      3374,
      3551,
      3729,
      3906,
      4084,
      4261,
      4439,
      4617,
      4794,
      4972,
      5149,
      5327,
      5505
    ],
    "frames": [
      {
        "path": "/data2/k6tk/01/011bc679b6508f2e5df2cc7339a34272bacfa30a6d038f4a8234768ed4f534d3.png",
        "sha256": "011bc679b6508f2e5df2cc7339a34272bacfa30a6d038f4a8234768ed4f534d3"
      },
      {
        "path": "/data2/k6tk/2f/2f492b10395efd1589eb9eab475e20edba9ffce5c37382f2c4798d844f4b4fb5.png",
        "sha256": "2f492b10395efd1589eb9eab475e20edba9ffce5c37382f2c4798d844f4b4fb5"
      },
      {
        "path": "/data2/k6tk/eb/ebe62af9ef9da1447b5ff4c8f6616d670ddbd31a8773c87284def57af9390d05.png",
        "sha256": "ebe62af9ef9da1447b5ff4c8f6616d670ddbd31a8773c87284def57af9390d05"
      },
      {
        "path": "/data2/k6tk/f8/f86d7d87d0bf617da20a84821bbf7dbff6563f436e08e8d6f0ab02ee51ebf62b.png",
        "sha256": "f86d7d87d0bf617da20a84821bbf7dbff6563f436e08e8d6f0ab02ee51ebf62b"
      },
      {
        "path": "/data2/k6tk/e4/e425bcbb037823eaf80d91e02d1715cfea1408bb516984c507c51f23acb570b8.png",
        "sha256": "e425bcbb037823eaf80d91e02d1715cfea1408bb516984c507c51f23acb570b8"
      },
      {
        "path": "/data2/k6tk/d9/d98fd1ba07733778b0b3687eedb5b1ed770acb41c84e63c8340e12c3c825cc36.png",
        "sha256": "d98fd1ba07733778b0b3687eedb5b1ed770acb41c84e63c8340e12c3c825cc36"
      },
      {
        "path": "/data2/k6tk/4c/4c7ad95c2e5bc140210c00b2164062f40e766282b48b60106fa75ac664b49923.png",
        "sha256": "4c7ad95c2e5bc140210c00b2164062f40e766282b48b60106fa75ac664b49923"
      },
      {
        "path": "/data2/k6tk/28/287e18dd3750e3555479debc1fa284c7a02653283055ffe17d50248c53d5c233.png",
        "sha256": "287e18dd3750e3555479debc1fa284c7a02653283055ffe17d50248c53d5c233"
      },
      {
        "path": "/data2/k6tk/85/85f2f48e50a816650d71b7395148a4303fc9526769841d54f70f961eabe596ac.png",
        "sha256": "85f2f48e50a816650d71b7395148a4303fc9526769841d54f70f961eabe596ac"
      },
      {
        "path": "/data2/k6tk/a0/a0f6c0e75ed329020dd2c56dab2ee578ee167d648d01922ea4a34294deee0f77.png",
        "sha256": "a0f6c0e75ed329020dd2c56dab2ee578ee167d648d01922ea4a34294deee0f77"
      },
      {
        "path": "/data2/k6tk/81/81282d36f2d3662bafce833f2a96570ce668d760317adc0a123b27ecd0edc919.png",
        "sha256": "81282d36f2d3662bafce833f2a96570ce668d760317adc0a123b27ecd0edc919"
      },
      {
        "path": "/data2/k6tk/54/5473ed161ab8e786db2010870ca30fd67c168702d39b39057eab086ac73e7fda.png",
        "sha256": "5473ed161ab8e786db2010870ca30fd67c168702d39b39057eab086ac73e7fda"
      },
      {
        "path": "/data2/k6tk/d5/d52b63761dbfa589b35e3ef22e7777d1e38f99f2a54a50c9485e4615bbf8d55d.png",
        "sha256": "d52b63761dbfa589b35e3ef22e7777d1e38f99f2a54a50c9485e4615bbf8d55d"
      },
      {
        "path": "/data2/k6tk/6b/6bd0a785222c766dda9bfc3dac25439b6050ee1df8f5cd7855760ba6a6884148.png",
        "sha256": "6bd0a785222c766dda9bfc3dac25439b6050ee1df8f5cd7855760ba6a6884148"
      },
      {
        "path": "/data2/k6tk/01/01f0d9f0bdab01f39e057f5a7c0e3d3311cca075afadb945ee5d29c6baa97bf0.png",
        "sha256": "01f0d9f0bdab01f39e057f5a7c0e3d3311cca075afadb945ee5d29c6baa97bf0"
      },
      {
        "path": "/data2/k6tk/33/3305fbbb4cd5cc52c5b68760dedf1469d7e532516082a3c84f3cbb4f7cc83837.png",
        "sha256": "3305fbbb4cd5cc52c5b68760dedf1469d7e532516082a3c84f3cbb4f7cc83837"
      },
      {
        "path": "/data2/k6tk/ed/ed9abce494e6040f72e21ef3e15f356b4ea5396abb7f04a1a2ab9d527c625184.png",
        "sha256": "ed9abce494e6040f72e21ef3e15f356b4ea5396abb7f04a1a2ab9d527c625184"
      },
      {
        "path": "/data2/k6tk/ba/ba837a9bc24945ec6535b7124235f4e5757709462f9a000dfd1f2c1025296e96.png",
        "sha256": "ba837a9bc24945ec6535b7124235f4e5757709462f9a000dfd1f2c1025296e96"
      },
      {
        "path": "/data2/k6tk/75/7534dbfddef06c84712174939181aa9408192aa6334eacd9a9d0194a62c85363.png",
        "sha256": "7534dbfddef06c84712174939181aa9408192aa6334eacd9a9d0194a62c85363"
      },
      {
        "path": "/data2/k6tk/7c/7c73496848827791a3aaa3c67b32c4255410bd21f11659a8a689d662c74cf9b8.png",
        "sha256": "7c73496848827791a3aaa3c67b32c4255410bd21f11659a8a689d662c74cf9b8"
      },
      {
        "path": "/data2/k6tk/b6/b6e18636a777e08dea7fd0cec6a0dacae8e721c43c87bee02f0b388f8ce26a2a.png",
        "sha256": "b6e18636a777e08dea7fd0cec6a0dacae8e721c43c87bee02f0b388f8ce26a2a"
      },
      {
        "path": "/data2/k6tk/e5/e5c044cba051d9a118b3ec0d95c370bb84aebe4dc9ed098befc8c7128b1b2459.png",
        "sha256": "e5c044cba051d9a118b3ec0d95c370bb84aebe4dc9ed098befc8c7128b1b2459"
      },
      {
        "path": "/data2/k6tk/22/22f7787948762e2307bf430e61f1a39d1b755132681e497032636d2bc93e8508.png",
        "sha256": "22f7787948762e2307bf430e61f1a39d1b755132681e497032636d2bc93e8508"
      },
      {
        "path": "/data2/k6tk/1e/1ee6a782696618e78151d44f0f5900e60da44dfc7558314955571e98191c12ef.png",
        "sha256": "1ee6a782696618e78151d44f0f5900e60da44dfc7558314955571e98191c12ef"
      },
      {
        "path": "/data2/k6tk/72/72e516f83bc3fd72084dc50fa9ecfe3f5679a6f325aec61667c17710a65349f4.png",
        "sha256": "72e516f83bc3fd72084dc50fa9ecfe3f5679a6f325aec61667c17710a65349f4"
      },
      {
        "path": "/data2/k6tk/e7/e73459cd9061b28b59ff421fbdb5ca7b92b9fe1190096f3ee8453b9863b4371c.png",
        "sha256": "e73459cd9061b28b59ff421fbdb5ca7b92b9fe1190096f3ee8453b9863b4371c"
      },
      {
        "path": "/data2/k6tk/58/58fb2ea46fb638118f0ede240f41d73223d508ac22c12f2734c699b980b45a5e.png",
        "sha256": "58fb2ea46fb638118f0ede240f41d73223d508ac22c12f2734c699b980b45a5e"
      },
      {
        "path": "/data2/k6tk/75/75ff64ff8024fd873ad20e144ce33006cfc0e97383c09222ddc1f00d2b130af6.png",
        "sha256": "75ff64ff8024fd873ad20e144ce33006cfc0e97383c09222ddc1f00d2b130af6"
      },
      {
        "path": "/data2/k6tk/85/8525b282068a25d55ebd3413c8562a8396b1ddb805ce0060c9c29dbed097b28d.png",
        "sha256": "8525b282068a25d55ebd3413c8562a8396b1ddb805ce0060c9c29dbed097b28d"
      },
      {
        "path": "/data2/k6tk/46/46fc52fa3172ccec6c4ef5b6670fbd25574f7baa3b281609f1f61a2fb54dd7c1.png",
        "sha256": "46fc52fa3172ccec6c4ef5b6670fbd25574f7baa3b281609f1f61a2fb54dd7c1"
      },
      {
        "path": "/data2/k6tk/5f/5fa69fd54f89229dc867221822bb83b92b1efb541e0cfef1a46c57b1fc007708.png",
        "sha256": "5fa69fd54f89229dc867221822bb83b92b1efb541e0cfef1a46c57b1fc007708"
      },
      {
        "path": "/data2/k6tk/c9/c9a832b299430cab839ff6e1b003fa7747be9a9f07e2437ea66d84c599a56d9e.png",
        "sha256": "c9a832b299430cab839ff6e1b003fa7747be9a9f07e2437ea66d84c599a56d9e"
      }
    ],
    "options": [
      "A. front-right",
      "B. back-left",
      "C. back-right",
      "D. front-left"
    ],
    "question": "If I am standing by the air duct and facing away from the blinds, is the multifunction printer to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.95,
      5.916666666666667,
      8.866666666666667,
      11.833333333333334,
      14.783333333333333,
      17.75,
      20.716666666666665,
      23.666666666666668,
      26.633333333333333,
      29.583333333333332,
      32.55,
      35.5,
      38.46666666666667,
      41.43333333333333,
      44.38333333333333,
      47.35,
      50.3,
      53.266666666666666,
      56.233333333333334,
      59.18333333333333,
      62.15,
      65.1,
      68.06666666666666,
      71.01666666666667,
      73.98333333333333,
      76.95,
      79.9,
      82.86666666666666,
      85.81666666666666,
      88.78333333333333,
      91.75
    ],
    "total_num_frames": 5506
  },
  "target": "<think>\nStep 1: locate the air duct, the blinds and the multifunction printer.\nStep 2: standing at the air duct and facing the blinds, I find the multifunction printer in front of me, on my left.\nStep 3: I face away from the blinds by making a half turn. Front and back swap, and left and right swap.\nSo I find the multifunction printer at my back-right.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 17. q15cbdded81e77c231b7c94cb_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-05d914586c10b76f4895aa7f6c26ea4eb29dd80002d93bceb5da7aec9ba6c431",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q15cbdded81e77c231b7c94cb"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "front-left",
      "source_qid": "q15cbdded81e77c231b7c94cb",
      "source_row_sha256": "7ae0f9ecb0c4af0a3de3aa28763dde01f0196dc911d62feecd980e62e1ad576c",
      "source_store_i": 38974
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q15cbdded81e77c231b7c94cb_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "456d983bebeaa9f684c63fc7cc02c9f34abd67926b353fc538cc1429fc994d1d"
  },
  "scene": "v828754ba8128",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      30,
      60,
      90,
      120,
      150,
      180,
      210,
      240,
      270,
      300,
      330,
      360,
      390,
      420,
      450,
      481,
      511,
      541,
      571,
      601,
      631,
      661,
      691,
      721,
      751,
      781,
      811,
      841,
      871,
      901,
      932
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f8/f818d06e082063757bd0004135669a3eb10cb2c68c4aaa0e8b9401a95fc020ba.png",
        "sha256": "f818d06e082063757bd0004135669a3eb10cb2c68c4aaa0e8b9401a95fc020ba"
      },
      {
        "path": "/data2/k6tk/28/2863fcd2acdf94fa5d25df10d1dae001e16526ac3f3e4b79766c50c9ab500fb0.png",
        "sha256": "2863fcd2acdf94fa5d25df10d1dae001e16526ac3f3e4b79766c50c9ab500fb0"
      },
      {
        "path": "/data2/k6tk/01/0183d14675bbed764a05c913291832838da41fcf79143c42bea2c5b79106c544.png",
        "sha256": "0183d14675bbed764a05c913291832838da41fcf79143c42bea2c5b79106c544"
      },
      {
        "path": "/data2/k6tk/4c/4c7fdb97f497eeafb6899922afed24566f4ad99301bb3e11cb9ddd73d08b2664.png",
        "sha256": "4c7fdb97f497eeafb6899922afed24566f4ad99301bb3e11cb9ddd73d08b2664"
      },
      {
        "path": "/data2/k6tk/53/53c92035f293ee0c8147a5c38c94bf037b091c792138767c8cc5b78454c48ba4.png",
        "sha256": "53c92035f293ee0c8147a5c38c94bf037b091c792138767c8cc5b78454c48ba4"
      },
      {
        "path": "/data2/k6tk/69/6939c646c2a9b841b266e7da4ce774b42cc08b11c10f7bbc9036aa5c8e19ee15.png",
        "sha256": "6939c646c2a9b841b266e7da4ce774b42cc08b11c10f7bbc9036aa5c8e19ee15"
      },
      {
        "path": "/data2/k6tk/9e/9ef497d69c23613c7b6d0831d400171e050dd7c2e5adbe3a1d0fc9632b97846a.png",
        "sha256": "9ef497d69c23613c7b6d0831d400171e050dd7c2e5adbe3a1d0fc9632b97846a"
      },
      {
        "path": "/data2/k6tk/87/878942a0898dc7ed40b52215b714df219057987ea45bbf32c39d50da7a2fbedf.png",
        "sha256": "878942a0898dc7ed40b52215b714df219057987ea45bbf32c39d50da7a2fbedf"
      },
      {
        "path": "/data2/k6tk/04/04f73e4997606c0e977eadb40e00160ace88a421bf23f98df09db8033e5b10ab.png",
        "sha256": "04f73e4997606c0e977eadb40e00160ace88a421bf23f98df09db8033e5b10ab"
      },
      {
        "path": "/data2/k6tk/c2/c2a586e3ab9ccf97bcbc9b34063c76dfeb597ab63a1f3fb551f34f1efbbb1b95.png",
        "sha256": "c2a586e3ab9ccf97bcbc9b34063c76dfeb597ab63a1f3fb551f34f1efbbb1b95"
      },
      {
        "path": "/data2/k6tk/81/810cee047c32991554ab9b9b63dce9fbcf2b637a42a57e1c63b618334c439d03.png",
        "sha256": "810cee047c32991554ab9b9b63dce9fbcf2b637a42a57e1c63b618334c439d03"
      },
      {
        "path": "/data2/k6tk/f0/f05123af4e0a3a52fd78d6be72ff4c22962d47372cb4ae580457db13a60c7479.png",
        "sha256": "f05123af4e0a3a52fd78d6be72ff4c22962d47372cb4ae580457db13a60c7479"
      },
      {
        "path": "/data2/k6tk/19/1970447b6fd604dd1f599d98d861dbcaa94865c50b15ed9cab1fb191a279e4f9.png",
        "sha256": "1970447b6fd604dd1f599d98d861dbcaa94865c50b15ed9cab1fb191a279e4f9"
      },
      {
        "path": "/data2/k6tk/79/790430be6598ba5803f15413d57a21a8c6c44b14600f3fd043f6a89c3652ec2d.png",
        "sha256": "790430be6598ba5803f15413d57a21a8c6c44b14600f3fd043f6a89c3652ec2d"
      },
      {
        "path": "/data2/k6tk/fe/fe72b37b755ff160ef29c3c401db9cd88002baf186d06adc797d474dbe73f1bf.png",
        "sha256": "fe72b37b755ff160ef29c3c401db9cd88002baf186d06adc797d474dbe73f1bf"
      },
      {
        "path": "/data2/k6tk/97/971de5a435102006c7957ac3b902651952c77f9137ddf26fe828a3ac555e77d7.png",
        "sha256": "971de5a435102006c7957ac3b902651952c77f9137ddf26fe828a3ac555e77d7"
      },
      {
        "path": "/data2/k6tk/6a/6a2fc596707d0297252ca7b87f54777fe45c603c91f2234f06fba1c145880eb7.png",
        "sha256": "6a2fc596707d0297252ca7b87f54777fe45c603c91f2234f06fba1c145880eb7"
      },
      {
        "path": "/data2/k6tk/db/db72f1c9c8a04857bca8921d79368ae025b72c2af943f7c91378f00996920ddd.png",
        "sha256": "db72f1c9c8a04857bca8921d79368ae025b72c2af943f7c91378f00996920ddd"
      },
      {
        "path": "/data2/k6tk/04/04f07d7596febcc13fc751ff66b058f7c3ee3d94c583071612da922c1ed4472c.png",
        "sha256": "04f07d7596febcc13fc751ff66b058f7c3ee3d94c583071612da922c1ed4472c"
      },
      {
        "path": "/data2/k6tk/c7/c75a89bfffe54983556020fd21ec6302ff6d497ea9ae122f5f50e7838376694e.png",
        "sha256": "c75a89bfffe54983556020fd21ec6302ff6d497ea9ae122f5f50e7838376694e"
      },
      {
        "path": "/data2/k6tk/ea/ea9ca1874256e8358af02b0dd778a23f6aa49a3671b8f5deac95bfd9f0d6a041.png",
        "sha256": "ea9ca1874256e8358af02b0dd778a23f6aa49a3671b8f5deac95bfd9f0d6a041"
      },
      {
        "path": "/data2/k6tk/58/58c49681d738e9ea2a141f724f0e9e8bb7f69c9bf96432814cbcb55a5821021a.png",
        "sha256": "58c49681d738e9ea2a141f724f0e9e8bb7f69c9bf96432814cbcb55a5821021a"
      },
      {
        "path": "/data2/k6tk/45/456a682c8f66da70db69bb8bf8fba1b70b07d02014a0cda120283b8b678f210e.png",
        "sha256": "456a682c8f66da70db69bb8bf8fba1b70b07d02014a0cda120283b8b678f210e"
      },
      {
        "path": "/data2/k6tk/98/985ba6f82a19194434c45c1c641486098eb27767dea95d8b8672f1872bf7bc5f.png",
        "sha256": "985ba6f82a19194434c45c1c641486098eb27767dea95d8b8672f1872bf7bc5f"
      },
      {
        "path": "/data2/k6tk/59/59a3ba93c50d9c95c4177a99848185c5638017e09a0470dfb291d3479eee637d.png",
        "sha256": "59a3ba93c50d9c95c4177a99848185c5638017e09a0470dfb291d3479eee637d"
      },
      {
        "path": "/data2/k6tk/4a/4a691a88399eb7d35af721218d40bae2f4a314b099ce0c75fe4ba3727b1df8bf.png",
        "sha256": "4a691a88399eb7d35af721218d40bae2f4a314b099ce0c75fe4ba3727b1df8bf"
      },
      {
        "path": "/data2/k6tk/3c/3c303532bf606a3e293274af68eb0692554f211b63a05ae220d9809825972360.png",
        "sha256": "3c303532bf606a3e293274af68eb0692554f211b63a05ae220d9809825972360"
      },
      {
        "path": "/data2/k6tk/ba/baba493acef10724b56ad5a7e3d8533eea72559355c7803a91030583ea58cd5c.png",
        "sha256": "baba493acef10724b56ad5a7e3d8533eea72559355c7803a91030583ea58cd5c"
      },
      {
        "path": "/data2/k6tk/fc/fce01c003cc8d979d82422b6f9ef7a1c07dc31f3145d67da0cf2b9593616a66a.png",
        "sha256": "fce01c003cc8d979d82422b6f9ef7a1c07dc31f3145d67da0cf2b9593616a66a"
      },
      {
        "path": "/data2/k6tk/1a/1a6faf49c7e4f3717e872f7584340bf73d30a42302d3d62a06d4df4566e84396.png",
        "sha256": "1a6faf49c7e4f3717e872f7584340bf73d30a42302d3d62a06d4df4566e84396"
      },
      {
        "path": "/data2/k6tk/b0/b071840cc24e58be11c1f2e13185aa64efb9c0d2477ee4009f59d65e2c7ff448.png",
        "sha256": "b071840cc24e58be11c1f2e13185aa64efb9c0d2477ee4009f59d65e2c7ff448"
      },
      {
        "path": "/data2/k6tk/5c/5c31202cbfc512e66e59edce7d88cce9a2bc8dc232960cfd2723cab0e4667710.png",
        "sha256": "5c31202cbfc512e66e59edce7d88cce9a2bc8dc232960cfd2723cab0e4667710"
      }
    ],
    "options": [
      "A. front-right",
      "B. front-left",
      "C. back-right",
      "D. back-left"
    ],
    "question": "If I am standing by the backpack and facing away from the cabinet, is the stacks of cups to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.25,
      2.5,
      3.75,
      5.0,
      6.25,
      7.5,
      8.75,
      10.0,
      11.25,
      12.5,
      13.75,
      15.0,
      16.25,
      17.5,
      18.75,
      20.041666666666668,
      21.291666666666668,
      22.541666666666668,
      23.791666666666668,
      25.041666666666668,
      26.291666666666668,
      27.541666666666668,
      28.791666666666668,
      30.041666666666668,
      31.291666666666668,
      32.541666666666664,
      33.791666666666664,
      35.041666666666664,
      36.291666666666664,
      37.541666666666664,
      38.833333333333336
    ],
    "total_num_frames": 933
  },
  "target": "<think>\nStep 1: find the backpack and the cabinet, then the stacks of cups.\nStep 2: I find the stacks of cups in front of me, on my left when I stand at the backpack facing the cabinet.\nStep 3: I face away from the cabinet by making a half turn. Front and back swap, and left and right swap.\nSo I find the stacks of cups at my back-right.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 18. q724b23e92071e2a72d452f09_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-2c3ebbf3d2b7583c360799f9e7af7f5928c73121c3fb99b49d0ef7517598468e",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q724b23e92071e2a72d452f09"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 40,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 34
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "front-left",
      "source_qid": "q724b23e92071e2a72d452f09",
      "source_row_sha256": "65733ecd1805ca9aa4c13f0564348e0202c8c67a20d551e8665e7c6c80d949cd",
      "source_store_i": 36179
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q724b23e92071e2a72d452f09_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "eb43cda61bf460634ddf855b072003825e52669927407394a07d80ce1531ce38"
  },
  "scene": "v3a350ec8593f",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      378,
      757,
      1135,
      1514,
      1893,
      2271,
      2650,
      3029,
      3407,
      3786,
      4165,
      4543,
      4922,
      5301,
      5679,
      6058,
      6436,
      6815,
      7194,
      7572,
      7951,
      8330,
      8708,
      9087,
      9466,
      9844,
      10223,
      10602,
      10980,
      11359,
      11738
    ],
    "frames": [
      {
        "path": "/data2/k6tk/cd/cdd165c65ec4d31583eb98f9c02c96d61b61275a0b5f66b5adfc403bd563523e.png",
        "sha256": "cdd165c65ec4d31583eb98f9c02c96d61b61275a0b5f66b5adfc403bd563523e"
      },
      {
        "path": "/data2/k6tk/04/04bc7b325a42353d7eb9a4c963c5912e551dba7c2d465cdd9b6f274c48cea519.png",
        "sha256": "04bc7b325a42353d7eb9a4c963c5912e551dba7c2d465cdd9b6f274c48cea519"
      },
      {
        "path": "/data2/k6tk/e8/e87433f855cfe0a159a6c14a8879e6bb1daea7f201de93c57ada889785193e93.png",
        "sha256": "e87433f855cfe0a159a6c14a8879e6bb1daea7f201de93c57ada889785193e93"
      },
      {
        "path": "/data2/k6tk/b8/b8b736cf358833c355b107847b222b72b90ca5f8c695209360d911f897fb6262.png",
        "sha256": "b8b736cf358833c355b107847b222b72b90ca5f8c695209360d911f897fb6262"
      },
      {
        "path": "/data2/k6tk/dd/dd5777ced47d7e7b00afc155de2c89f478d30f587c947081e73965b4a4e44b3c.png",
        "sha256": "dd5777ced47d7e7b00afc155de2c89f478d30f587c947081e73965b4a4e44b3c"
      },
      {
        "path": "/data2/k6tk/bd/bdc3668db6860b1c6a540739aa04f7cef1c176483473b9d561b8986359c4a034.png",
        "sha256": "bdc3668db6860b1c6a540739aa04f7cef1c176483473b9d561b8986359c4a034"
      },
      {
        "path": "/data2/k6tk/df/df8cfa7dd3bf777346c323cae2cc21f41c7420858b590338b24ae6f5cd3025c4.png",
        "sha256": "df8cfa7dd3bf777346c323cae2cc21f41c7420858b590338b24ae6f5cd3025c4"
      },
      {
        "path": "/data2/k6tk/d1/d114c8eb44defbfa1d348428e58daebb36bee7bf6779b3f10a6fe22cd9c238fc.png",
        "sha256": "d114c8eb44defbfa1d348428e58daebb36bee7bf6779b3f10a6fe22cd9c238fc"
      },
      {
        "path": "/data2/k6tk/5a/5ae936875fd4412344adaf4572fbdb5cb93c0d885eacf64f22f10be9274ef786.png",
        "sha256": "5ae936875fd4412344adaf4572fbdb5cb93c0d885eacf64f22f10be9274ef786"
      },
      {
        "path": "/data2/k6tk/67/6775608eb02afa14b38705e6b1a56227907ebd309cc56b9e6bed037ff6d12120.png",
        "sha256": "6775608eb02afa14b38705e6b1a56227907ebd309cc56b9e6bed037ff6d12120"
      },
      {
        "path": "/data2/k6tk/cb/cb9cfccbe36dadcc33f0a9121d0a518e5bc7d72f1ccbf33e03410463ddef9046.png",
        "sha256": "cb9cfccbe36dadcc33f0a9121d0a518e5bc7d72f1ccbf33e03410463ddef9046"
      },
      {
        "path": "/data2/k6tk/e1/e1cf2a5702335838bbcc2b664eb0b2bcbf40da57f24015a16c84c6c2974553b3.png",
        "sha256": "e1cf2a5702335838bbcc2b664eb0b2bcbf40da57f24015a16c84c6c2974553b3"
      },
      {
        "path": "/data2/k6tk/1e/1e881320c879717f4838561ef3a8f2b2cf2cb7c88080e72ee795dddb789e465e.png",
        "sha256": "1e881320c879717f4838561ef3a8f2b2cf2cb7c88080e72ee795dddb789e465e"
      },
      {
        "path": "/data2/k6tk/1d/1d31fe0ec72a7bd869a8fc3ab86a2870962a855ac6482414330703976ec5d0c0.png",
        "sha256": "1d31fe0ec72a7bd869a8fc3ab86a2870962a855ac6482414330703976ec5d0c0"
      },
      {
        "path": "/data2/k6tk/74/74fcf74963d232c25e4193f488c16afa565374cd129bf464e7768e317e631f2f.png",
        "sha256": "74fcf74963d232c25e4193f488c16afa565374cd129bf464e7768e317e631f2f"
      },
      {
        "path": "/data2/k6tk/f1/f1be52d09cdeee99e1d3637a2b6ba1ea3594852e3d49081a66b02d7f508790b0.png",
        "sha256": "f1be52d09cdeee99e1d3637a2b6ba1ea3594852e3d49081a66b02d7f508790b0"
      },
      {
        "path": "/data2/k6tk/ef/efa62e2abf861580cf3cc35dd870fb593528302c179a35a000939040fc281506.png",
        "sha256": "efa62e2abf861580cf3cc35dd870fb593528302c179a35a000939040fc281506"
      },
      {
        "path": "/data2/k6tk/f9/f9c03c35010c4d727e1275027887087f5eaadc80a507ef6ad8ea9668908f7cd6.png",
        "sha256": "f9c03c35010c4d727e1275027887087f5eaadc80a507ef6ad8ea9668908f7cd6"
      },
      {
        "path": "/data2/k6tk/10/105cc72a8d42c2c6ff08e3d90ed31c593476d1f462d6f7489dc7adcff8fa843b.png",
        "sha256": "105cc72a8d42c2c6ff08e3d90ed31c593476d1f462d6f7489dc7adcff8fa843b"
      },
      {
        "path": "/data2/k6tk/e0/e0e9ebdd41a8af3e3364874e2328a441842d0efac74e2aca84a90d17962255fd.png",
        "sha256": "e0e9ebdd41a8af3e3364874e2328a441842d0efac74e2aca84a90d17962255fd"
      },
      {
        "path": "/data2/k6tk/df/dfd4fa7959e75f509732e0c9ca20ba5aa44c211a116cd41bd72490265d13b4d4.png",
        "sha256": "dfd4fa7959e75f509732e0c9ca20ba5aa44c211a116cd41bd72490265d13b4d4"
      },
      {
        "path": "/data2/k6tk/5e/5edbd017c2165d31edc18ded3af2a5d720cbd743f2296f72ba641ab8b4ef6837.png",
        "sha256": "5edbd017c2165d31edc18ded3af2a5d720cbd743f2296f72ba641ab8b4ef6837"
      },
      {
        "path": "/data2/k6tk/9f/9fdbc49bfc505ddad93904b565d9ccaf99c546f9797474efeb72044e59712d8e.png",
        "sha256": "9fdbc49bfc505ddad93904b565d9ccaf99c546f9797474efeb72044e59712d8e"
      },
      {
        "path": "/data2/k6tk/08/08dc9101995a69ea5a00fad93619143bdd331010054aff8fab933fd4101f563f.png",
        "sha256": "08dc9101995a69ea5a00fad93619143bdd331010054aff8fab933fd4101f563f"
      },
      {
        "path": "/data2/k6tk/c0/c044f413868d4be36e054de2e86c9470fc6a3954656582fe50d2e4f081fbbe4b.png",
        "sha256": "c044f413868d4be36e054de2e86c9470fc6a3954656582fe50d2e4f081fbbe4b"
      },
      {
        "path": "/data2/k6tk/ac/ac37f1a5c1319c0c381c5cdf5ad61e9328c6f87234da8eb46bfff058c0d1306b.png",
        "sha256": "ac37f1a5c1319c0c381c5cdf5ad61e9328c6f87234da8eb46bfff058c0d1306b"
      },
      {
        "path": "/data2/k6tk/5b/5ba002ce74edf8c9288a2c24aa5de1c01c55a9686f93bcbb0e58e848013316e7.png",
        "sha256": "5ba002ce74edf8c9288a2c24aa5de1c01c55a9686f93bcbb0e58e848013316e7"
      },
      {
        "path": "/data2/k6tk/e9/e95ff4097df272fd2ac30a5b96d9be29c84262e557f7156215df9e9644b582f9.png",
        "sha256": "e95ff4097df272fd2ac30a5b96d9be29c84262e557f7156215df9e9644b582f9"
      },
      {
        "path": "/data2/k6tk/21/21fcce5753a7bfe202048ec1067d0a49b6bf331ac1f3cffa3084e91bd02d757b.png",
        "sha256": "21fcce5753a7bfe202048ec1067d0a49b6bf331ac1f3cffa3084e91bd02d757b"
      },
      {
        "path": "/data2/k6tk/5e/5e1b797653c6270558ef9704b1496aba371807de55edf19c1097a5e41f09f7b7.png",
        "sha256": "5e1b797653c6270558ef9704b1496aba371807de55edf19c1097a5e41f09f7b7"
      },
      {
        "path": "/data2/k6tk/51/519a097360f76747f47f7a555468da006c5bb3ffe69047828a24d6446e118b67.png",
        "sha256": "519a097360f76747f47f7a555468da006c5bb3ffe69047828a24d6446e118b67"
      },
      {
        "path": "/data2/k6tk/4a/4a70e3b0e49d9df93ed38c5d21f3bab9a3212bbb7e8a65e0e4edba25fdf3d6a3.png",
        "sha256": "4a70e3b0e49d9df93ed38c5d21f3bab9a3212bbb7e8a65e0e4edba25fdf3d6a3"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the books and facing away from the carrier cart, is the cable raceway to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.3,
      12.616666666666667,
      18.916666666666668,
      25.233333333333334,
      31.55,
      37.85,
      44.166666666666664,
      50.483333333333334,
      56.78333333333333,
      63.1,
      69.41666666666667,
      75.71666666666667,
      82.03333333333333,
      88.35,
      94.65,
      100.96666666666667,
      107.26666666666667,
      113.58333333333333,
      119.9,
      126.2,
      132.51666666666668,
      138.83333333333334,
      145.13333333333333,
      151.45,
      157.76666666666668,
      164.06666666666666,
      170.38333333333333,
      176.7,
      183.0,
      189.31666666666666,
      195.63333333333333
    ],
    "total_num_frames": 11739
  },
  "target": "<think>\nStep 1: find the books, the carrier cart and the cable raceway.\nStep 2: I stand at the books facing the carrier cart; I find the cable raceway in front of me, on my left.\nStep 3: I face away from the carrier cart by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the cable raceway at my back-right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 19. qdc456033238376a0b806df59-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-95996807e52bd6106a43086558d5eb1ac383792ad8d0035e9fad1cc17aad8823",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qdc456033238376a0b806df59-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qdc456033238376a0b806df59",
  "paraphrase_template": "hard_vsi",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 42,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 36
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "C",
      "source_label": "front-left",
      "source_qid": "qdc456033238376a0b806df59-p1",
      "source_row_sha256": "0978440733bfd8088fd6e9e55382b445fee48ae458ee7303dfd62fe055dd6fd5",
      "source_store_i": 74729
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qdc456033238376a0b806df59-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "1e205ec1e76a22d50d77c13f193e046dd7a4bc71a6db6319928c294fcd114f90"
  },
  "scene": "v2d9fef3448f5",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      201,
      402,
      603,
      804,
      1005,
      1206,
      1407,
      1608,
      1809,
      2010,
      2212,
      2413,
      2614,
      2815,
      3016,
      3217,
      3418,
      3619,
      3820,
      4021,
      4223,
      4424,
      4625,
      4826,
      5027,
      5228,
      5429,
      5630,
      5831,
      6032,
      6234
    ],
    "frames": [
      {
        "path": "/data2/k6tk/8c/8c9a2e763b93d116557f87f4555774e19b6fef780bd7ed23f2127d0067236eba.png",
        "sha256": "8c9a2e763b93d116557f87f4555774e19b6fef780bd7ed23f2127d0067236eba"
      },
      {
        "path": "/data2/k6tk/b1/b1dc32141e085a68b4b644e122b1b80b9a19dc745e0073223d2b8176951e21a7.png",
        "sha256": "b1dc32141e085a68b4b644e122b1b80b9a19dc745e0073223d2b8176951e21a7"
      },
      {
        "path": "/data2/k6tk/27/275385950fd90b9a2c0d09cc8da5ca0f792b33eac5999f85f6ad5fb18248f4a1.png",
        "sha256": "275385950fd90b9a2c0d09cc8da5ca0f792b33eac5999f85f6ad5fb18248f4a1"
      },
      {
        "path": "/data2/k6tk/77/7726b409be5eaa0440632ff7c7c33fdeccd8c92981ea5765631dd0e80c5e286a.png",
        "sha256": "7726b409be5eaa0440632ff7c7c33fdeccd8c92981ea5765631dd0e80c5e286a"
      },
      {
        "path": "/data2/k6tk/f5/f5ab3e14cdf85bac23a6e20b0ba1c408a63fe523dbcf4c7fd29f1601df30c0ca.png",
        "sha256": "f5ab3e14cdf85bac23a6e20b0ba1c408a63fe523dbcf4c7fd29f1601df30c0ca"
      },
      {
        "path": "/data2/k6tk/6d/6dd384d2a11e463fe6290b5ff91f5ac56d3da02deded6df07bcbb55e16fd8157.png",
        "sha256": "6dd384d2a11e463fe6290b5ff91f5ac56d3da02deded6df07bcbb55e16fd8157"
      },
      {
        "path": "/data2/k6tk/0a/0ac6a29bc55b7e343b61201dd8a5d90a36df5f8ff2b76887dfd3459d8972a565.png",
        "sha256": "0ac6a29bc55b7e343b61201dd8a5d90a36df5f8ff2b76887dfd3459d8972a565"
      },
      {
        "path": "/data2/k6tk/75/750daad0be28caa3c8d659a7dd19b837baf4500e2ff7db937a54346a5a2bca99.png",
        "sha256": "750daad0be28caa3c8d659a7dd19b837baf4500e2ff7db937a54346a5a2bca99"
      },
      {
        "path": "/data2/k6tk/15/152513a600d94da9c4620015d110d97e3f88575cd7feed07fe1c0e8d073336ec.png",
        "sha256": "152513a600d94da9c4620015d110d97e3f88575cd7feed07fe1c0e8d073336ec"
      },
      {
        "path": "/data2/k6tk/a6/a6e7a172d8edf049b143601ace801351ce8be68e6848654d9866fba6d6579ae0.png",
        "sha256": "a6e7a172d8edf049b143601ace801351ce8be68e6848654d9866fba6d6579ae0"
      },
      {
        "path": "/data2/k6tk/05/050bb4246b76102adbbde670700c2daaa14990c305f74663e483310353131ad9.png",
        "sha256": "050bb4246b76102adbbde670700c2daaa14990c305f74663e483310353131ad9"
      },
      {
        "path": "/data2/k6tk/ae/ae75e534f9ed8ab43de332e758d7b270b7376a5721b2f92bc31dec45ed8a1f5d.png",
        "sha256": "ae75e534f9ed8ab43de332e758d7b270b7376a5721b2f92bc31dec45ed8a1f5d"
      },
      {
        "path": "/data2/k6tk/bc/bc8c455f4aca86347ca935ed46a1ce3557a0c02c3121ed13622cf9eecce6d121.png",
        "sha256": "bc8c455f4aca86347ca935ed46a1ce3557a0c02c3121ed13622cf9eecce6d121"
      },
      {
        "path": "/data2/k6tk/b4/b4973eba711f84d85eab1dc726bc5a0e7e77ef253545799cce81c731725644d0.png",
        "sha256": "b4973eba711f84d85eab1dc726bc5a0e7e77ef253545799cce81c731725644d0"
      },
      {
        "path": "/data2/k6tk/13/1315dc3d41ee9fe701fc2d7f18c43b247f2d00d6b91e51ef68bd78fbbef0bf77.png",
        "sha256": "1315dc3d41ee9fe701fc2d7f18c43b247f2d00d6b91e51ef68bd78fbbef0bf77"
      },
      {
        "path": "/data2/k6tk/00/006c53de42d43faae3e184bb7d8fc5894969cb8f5dc616ad159aed48997e597a.png",
        "sha256": "006c53de42d43faae3e184bb7d8fc5894969cb8f5dc616ad159aed48997e597a"
      },
      {
        "path": "/data2/k6tk/a1/a1ff36f60dba68c88eb97aa3739f29ac8e1526be636df841acb2788add661c18.png",
        "sha256": "a1ff36f60dba68c88eb97aa3739f29ac8e1526be636df841acb2788add661c18"
      },
      {
        "path": "/data2/k6tk/e6/e6e1ddc02916d7c55a5a7ee4eb16aac47b04971fe674aa389a6c253b0ff73b9e.png",
        "sha256": "e6e1ddc02916d7c55a5a7ee4eb16aac47b04971fe674aa389a6c253b0ff73b9e"
      },
      {
        "path": "/data2/k6tk/6e/6ef2ca1872cb49a108a2cdd99d5df4bda95fa20c3b4781d28097e0a61b905b10.png",
        "sha256": "6ef2ca1872cb49a108a2cdd99d5df4bda95fa20c3b4781d28097e0a61b905b10"
      },
      {
        "path": "/data2/k6tk/63/634feddcd53e316cf7b8152e9d836cfd4c0029116e6357aa705c2b60a65d661a.png",
        "sha256": "634feddcd53e316cf7b8152e9d836cfd4c0029116e6357aa705c2b60a65d661a"
      },
      {
        "path": "/data2/k6tk/7c/7c497ddbf3fa4370a1f5e34ce53ff52f2f36c22d6576da8464a1bc8985b1e17b.png",
        "sha256": "7c497ddbf3fa4370a1f5e34ce53ff52f2f36c22d6576da8464a1bc8985b1e17b"
      },
      {
        "path": "/data2/k6tk/13/131b4a5f3205359bd813239e9c33a553a248eb52b49b6b1c371166ebfadaffb4.png",
        "sha256": "131b4a5f3205359bd813239e9c33a553a248eb52b49b6b1c371166ebfadaffb4"
      },
      {
        "path": "/data2/k6tk/6e/6e549b438c166f7c53924e6028c67760cc2aae0856a49cdf12d4d296b86895f2.png",
        "sha256": "6e549b438c166f7c53924e6028c67760cc2aae0856a49cdf12d4d296b86895f2"
      },
      {
        "path": "/data2/k6tk/f8/f833cbd22c17d3fa37b4dcfe6af65eb19f6a8657ce1558ff4a6c8faf4b1f0cb8.png",
        "sha256": "f833cbd22c17d3fa37b4dcfe6af65eb19f6a8657ce1558ff4a6c8faf4b1f0cb8"
      },
      {
        "path": "/data2/k6tk/b3/b36026fa7feac26abc9de09d6a13729d4fb566ccae170f5cc74e0644f3cd19c9.png",
        "sha256": "b36026fa7feac26abc9de09d6a13729d4fb566ccae170f5cc74e0644f3cd19c9"
      },
      {
        "path": "/data2/k6tk/64/6485f3aa652cc15a79f8383c011d7e1849827a4bdba074569b43fe896f53336c.png",
        "sha256": "6485f3aa652cc15a79f8383c011d7e1849827a4bdba074569b43fe896f53336c"
      },
      {
        "path": "/data2/k6tk/2a/2afa7e6de98d10b65b259490edc4230c86a6eddbde3d3de951f7538134affb99.png",
        "sha256": "2afa7e6de98d10b65b259490edc4230c86a6eddbde3d3de951f7538134affb99"
      },
      {
        "path": "/data2/k6tk/fb/fb1617fc2aa19fe2468fb67408eb00ac5342944c9b405d8dc5e839628237b72b.png",
        "sha256": "fb1617fc2aa19fe2468fb67408eb00ac5342944c9b405d8dc5e839628237b72b"
      },
      {
        "path": "/data2/k6tk/ce/ce81c67449b274200c24bf3baa82db15974768ea745b6b2344f0c5cc5c86e479.png",
        "sha256": "ce81c67449b274200c24bf3baa82db15974768ea745b6b2344f0c5cc5c86e479"
      },
      {
        "path": "/data2/k6tk/84/842ac502fc5d122b4e90ac8117fe347d4f0e009ab06bce8e61fed0c582f342c2.png",
        "sha256": "842ac502fc5d122b4e90ac8117fe347d4f0e009ab06bce8e61fed0c582f342c2"
      },
      {
        "path": "/data2/k6tk/08/08695ef6d06dd1615d754df6d9c1a061d945b22efde52c08a61b144cb7cbc38a.png",
        "sha256": "08695ef6d06dd1615d754df6d9c1a061d945b22efde52c08a61b144cb7cbc38a"
      },
      {
        "path": "/data2/k6tk/c7/c71d26cb6b169146b6d781d91af141b21be8cc23631da8c7cf88013f029a2c7e.png",
        "sha256": "c71d26cb6b169146b6d781d91af141b21be8cc23631da8c7cf88013f029a2c7e"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-right",
      "C. front-left",
      "D. back-left"
    ],
    "question": "If I am standing beside the bag and facing away from the desk, which direction describes the laptop bag relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.35,
      6.7,
      10.05,
      13.4,
      16.75,
      20.1,
      23.45,
      26.8,
      30.15,
      33.5,
      36.86666666666667,
      40.21666666666667,
      43.56666666666667,
      46.916666666666664,
      50.266666666666666,
      53.61666666666667,
      56.96666666666667,
      60.31666666666667,
      63.666666666666664,
      67.01666666666667,
      70.38333333333334,
      73.73333333333333,
      77.08333333333333,
      80.43333333333334,
      83.78333333333333,
      87.13333333333334,
      90.48333333333333,
      93.83333333333333,
      97.18333333333334,
      100.53333333333333,
      103.9
    ],
    "total_num_frames": 6235
  },
  "target": "<think>\nStep 1: find the bag and the desk, then the laptop bag.\nStep 2: I find the laptop bag in front of me, on my left when I stand at the bag facing the desk.\nStep 3: I face away from the desk by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the laptop bag at my back-right.\n</think>\n\nA",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 20. q712f35fd6fd29e37421e61b8-p1_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-47c018955cf44c92c5c0be20781b5f3d0707d2754882deb60909494887193f98",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q712f35fd6fd29e37421e61b8-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q712f35fd6fd29e37421e61b8",
  "paraphrase_template": "hard_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 34,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "looking at",
        "start": 24
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "back-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "front-left",
      "source_qid": "q712f35fd6fd29e37421e61b8-p1",
      "source_row_sha256": "6367edfbd178ffa8ea8e5b62ae974d1958d8bc12505b6399aab97e8f6ac77b41",
      "source_store_i": 80356
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q712f35fd6fd29e37421e61b8-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "a9c4bbdfe01716829f81d934423399d2c13a4756adf32d1fc0717c7253f6d7ab"
  },
  "scene": "v93b245026340",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      54,
      108,
      162,
      217,
      271,
      325,
      380,
      434,
      488,
      543,
      597,
      651,
      706,
      760,
      814,
      869,
      923,
      977,
      1032,
      1086,
      1140,
      1195,
      1249,
      1303,
      1358,
      1412,
      1466,
      1521,
      1575,
      1629,
      1684
    ],
    "frames": [
      {
        "path": "/data2/k6tk/05/053006b5599e29348729cd3229bdf1d19e876dd41fe721f2ea8fe3afd7377090.png",
        "sha256": "053006b5599e29348729cd3229bdf1d19e876dd41fe721f2ea8fe3afd7377090"
      },
      {
        "path": "/data2/k6tk/fe/fe844f8424fa922726702781a3bf3941fc5f5d2cdf05b32138c2ae4bff01a885.png",
        "sha256": "fe844f8424fa922726702781a3bf3941fc5f5d2cdf05b32138c2ae4bff01a885"
      },
      {
        "path": "/data2/k6tk/9c/9c6bf5bca181cb9f29f49fd137602ba90c5eeec8e1aae82cfa2516ba6bf33004.png",
        "sha256": "9c6bf5bca181cb9f29f49fd137602ba90c5eeec8e1aae82cfa2516ba6bf33004"
      },
      {
        "path": "/data2/k6tk/f7/f749cda6b24d422e860c02eadf93c2746d17da8be8a4475506439c6ab9d18184.png",
        "sha256": "f749cda6b24d422e860c02eadf93c2746d17da8be8a4475506439c6ab9d18184"
      },
      {
        "path": "/data2/k6tk/70/705c2fa94f717d42f30d921b70d0e0022c6838c8729a2683f3269084085eec6c.png",
        "sha256": "705c2fa94f717d42f30d921b70d0e0022c6838c8729a2683f3269084085eec6c"
      },
      {
        "path": "/data2/k6tk/93/93f12a610aec979e1c9f6fea0c0155b460c205da4499345682ac040c237bb260.png",
        "sha256": "93f12a610aec979e1c9f6fea0c0155b460c205da4499345682ac040c237bb260"
      },
      {
        "path": "/data2/k6tk/fc/fc3962035b4ca6cb0b15be9b2378c1555927db4a580588d8ec5027f5c63e1772.png",
        "sha256": "fc3962035b4ca6cb0b15be9b2378c1555927db4a580588d8ec5027f5c63e1772"
      },
      {
        "path": "/data2/k6tk/5e/5e0b9d9a78825c1ce6fa5bb1bddadc562fc7646ef94035df975bc06c31617128.png",
        "sha256": "5e0b9d9a78825c1ce6fa5bb1bddadc562fc7646ef94035df975bc06c31617128"
      },
      {
        "path": "/data2/k6tk/e4/e42ff721284e774b340b7990c5c04ebfa5fe43338f6ddfb9605cd6ef5affef76.png",
        "sha256": "e42ff721284e774b340b7990c5c04ebfa5fe43338f6ddfb9605cd6ef5affef76"
      },
      {
        "path": "/data2/k6tk/e6/e636ccbbcd3dabae149a9a2fed83321fe164caea55c8c45ce68624a9530c0bb3.png",
        "sha256": "e636ccbbcd3dabae149a9a2fed83321fe164caea55c8c45ce68624a9530c0bb3"
      },
      {
        "path": "/data2/k6tk/a0/a031cc321a0488955ffdab1fa57c7f32eeb90006e31017351457bcf25f7ff460.png",
        "sha256": "a031cc321a0488955ffdab1fa57c7f32eeb90006e31017351457bcf25f7ff460"
      },
      {
        "path": "/data2/k6tk/eb/eb29e827e3695e375b2d2fc8f94049872df51b551a5e441297baea3117f247b1.png",
        "sha256": "eb29e827e3695e375b2d2fc8f94049872df51b551a5e441297baea3117f247b1"
      },
      {
        "path": "/data2/k6tk/bc/bcca288aa3a4d184286e0e518994234912b4930f8067736b60292cfe781b172f.png",
        "sha256": "bcca288aa3a4d184286e0e518994234912b4930f8067736b60292cfe781b172f"
      },
      {
        "path": "/data2/k6tk/74/745b7490d41f797c04d629a40a918f60dad9171ebf80e4f7d56010ae603d796a.png",
        "sha256": "745b7490d41f797c04d629a40a918f60dad9171ebf80e4f7d56010ae603d796a"
      },
      {
        "path": "/data2/k6tk/bc/bcd5335a3ac627ff8ea6ffd21368521157106be3f3c37e4a45d84556d71305ef.png",
        "sha256": "bcd5335a3ac627ff8ea6ffd21368521157106be3f3c37e4a45d84556d71305ef"
      },
      {
        "path": "/data2/k6tk/39/39a36333b1a478871cf2237e9943cc43eb90b5cfe21b4e79e58f6d797fc442e9.png",
        "sha256": "39a36333b1a478871cf2237e9943cc43eb90b5cfe21b4e79e58f6d797fc442e9"
      },
      {
        "path": "/data2/k6tk/c9/c919391a2cf2bdadc8d48120f1f0b014f094d444f0e7c62adc65a007189425c9.png",
        "sha256": "c919391a2cf2bdadc8d48120f1f0b014f094d444f0e7c62adc65a007189425c9"
      },
      {
        "path": "/data2/k6tk/1a/1ac8265e47d0b019b2dbb9cb35c27479b5999c767ebd3308c732f14f46c9f460.png",
        "sha256": "1ac8265e47d0b019b2dbb9cb35c27479b5999c767ebd3308c732f14f46c9f460"
      },
      {
        "path": "/data2/k6tk/d5/d56e6a026c40f337a60f9baffbc000112c8e9d4e24606204335827b1e66ef751.png",
        "sha256": "d56e6a026c40f337a60f9baffbc000112c8e9d4e24606204335827b1e66ef751"
      },
      {
        "path": "/data2/k6tk/31/31e25c98ade75d6e1c234279f07d269556c733ee5fae3a65c6a8ea6b42469ac3.png",
        "sha256": "31e25c98ade75d6e1c234279f07d269556c733ee5fae3a65c6a8ea6b42469ac3"
      },
      {
        "path": "/data2/k6tk/17/1710f3816aa0155772e8d650a6084514546f3a6679a466b054fd6df774f65dfa.png",
        "sha256": "1710f3816aa0155772e8d650a6084514546f3a6679a466b054fd6df774f65dfa"
      },
      {
        "path": "/data2/k6tk/be/be59abe627dd7d0ccafae577b12b452856d02f76101a4a1e5ecf93b3651422a4.png",
        "sha256": "be59abe627dd7d0ccafae577b12b452856d02f76101a4a1e5ecf93b3651422a4"
      },
      {
        "path": "/data2/k6tk/d5/d5becbd151b38e074ef76b40171347c2e1b9f8fe28127413a5324c81796b5847.png",
        "sha256": "d5becbd151b38e074ef76b40171347c2e1b9f8fe28127413a5324c81796b5847"
      },
      {
        "path": "/data2/k6tk/c9/c9f8e47645ebfcff63dc2a48c6ef75f6598e8b86afbffa78246d2c5eff928812.png",
        "sha256": "c9f8e47645ebfcff63dc2a48c6ef75f6598e8b86afbffa78246d2c5eff928812"
      },
      {
        "path": "/data2/k6tk/ab/ab35c16e7a4530e74c080dd207fea68a9b93723741b56a2672ae7b2017a7fac3.png",
        "sha256": "ab35c16e7a4530e74c080dd207fea68a9b93723741b56a2672ae7b2017a7fac3"
      },
      {
        "path": "/data2/k6tk/51/51457b9e24e29c3e89e8631f218463be5451e9ac42dc98ab2440732e5a22875a.png",
        "sha256": "51457b9e24e29c3e89e8631f218463be5451e9ac42dc98ab2440732e5a22875a"
      },
      {
        "path": "/data2/k6tk/76/76fd097d41d6e6f5ca81867f1509cca7a248934d02857d9200af824e8fec4371.png",
        "sha256": "76fd097d41d6e6f5ca81867f1509cca7a248934d02857d9200af824e8fec4371"
      },
      {
        "path": "/data2/k6tk/7b/7bb8e4c504717f7f29bab28bfddee05b1615931d2435b429cf772a2b4e7dd263.png",
        "sha256": "7bb8e4c504717f7f29bab28bfddee05b1615931d2435b429cf772a2b4e7dd263"
      },
      {
        "path": "/data2/k6tk/bf/bf02fb4ebb61fd9a70db398932c48613ec2829a15c81ffa1924a9982955eeceb.png",
        "sha256": "bf02fb4ebb61fd9a70db398932c48613ec2829a15c81ffa1924a9982955eeceb"
      },
      {
        "path": "/data2/k6tk/c6/c63f5eda4eab301eaeb9fcb90c386c74d340f645f39fc581523b21eeaeff54d9.png",
        "sha256": "c63f5eda4eab301eaeb9fcb90c386c74d340f645f39fc581523b21eeaeff54d9"
      },
      {
        "path": "/data2/k6tk/d4/d482e9c6e2f5702212edccc2fa2ca6c563fb87a48036dce8d0dd6394582bbc22.png",
        "sha256": "d482e9c6e2f5702212edccc2fa2ca6c563fb87a48036dce8d0dd6394582bbc22"
      },
      {
        "path": "/data2/k6tk/30/306b81b438fee7978fecaa7be2f9d5e0dfa37e7bf6c4f3602c7b5eec5bd6d91d.png",
        "sha256": "306b81b438fee7978fecaa7be2f9d5e0dfa37e7bf6c4f3602c7b5eec5bd6d91d"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-left",
      "C. front-right",
      "D. back-right"
    ],
    "question": "I stand by the backpack facing away from the stair rail. Where is the staircase relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.25,
      4.5,
      6.75,
      9.041666666666666,
      11.291666666666666,
      13.541666666666666,
      15.833333333333334,
      18.083333333333332,
      20.333333333333332,
      22.625,
      24.875,
      27.125,
      29.416666666666668,
      31.666666666666668,
      33.916666666666664,
      36.208333333333336,
      38.458333333333336,
      40.708333333333336,
      43.0,
      45.25,
      47.5,
      49.791666666666664,
      52.041666666666664,
      54.291666666666664,
      56.583333333333336,
      58.833333333333336,
      61.083333333333336,
      63.375,
      65.625,
      67.875,
      70.16666666666667
    ],
    "total_num_frames": 1685
  },
  "target": "<think>\nStep 1: locate the staircase, the backpack and the stair rail.\nStep 2: standing at the backpack and facing the stair rail, I find the staircase in front of me, on my left.\nStep 3: I face away from the stair rail by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the staircase at my back-right.\n</think>\n\nD",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 21. q5b025b47ccff67797ed4f634_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-05645f00d7f227c11c070d2a25e2acfb5b23ccf204356fbf1cb045b5fc0bfd70",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q5b025b47ccff67797ed4f634"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 40,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 34
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "back-right",
      "source_qid": "q5b025b47ccff67797ed4f634",
      "source_row_sha256": "5525578a6b1afc7c00e12eea2c1dc76b933da0a1779ea4956841c8fa137b5ff4",
      "source_store_i": 12033
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q5b025b47ccff67797ed4f634_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "dce20aa363f2bd6b846415e898617a76e57520a761c95dd9e9122acd93f9941e"
  },
  "scene": "v85e138cf9288",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      26,
      53,
      79,
      106,
      132,
      159,
      186,
      212,
      239,
      265,
      292,
      318,
      345,
      372,
      398,
      425,
      451,
      478,
      505,
      531,
      558,
      584,
      611,
      637,
      664,
      691,
      717,
      744,
      770,
      797,
      824
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c0/c0175fb7d6f247d1d1b8149b94a1bcc9a29ba588fb46d429034e81451498791e.png",
        "sha256": "c0175fb7d6f247d1d1b8149b94a1bcc9a29ba588fb46d429034e81451498791e"
      },
      {
        "path": "/data2/k6tk/c8/c806abbb67b1c6accbe004ed42c27ef74ae57c52b0d783fa3530e8308dfee869.png",
        "sha256": "c806abbb67b1c6accbe004ed42c27ef74ae57c52b0d783fa3530e8308dfee869"
      },
      {
        "path": "/data2/k6tk/c1/c1e9ed66815bb470eb753564782a370196d7c0e7d533b8592ae4af2c6376a87e.png",
        "sha256": "c1e9ed66815bb470eb753564782a370196d7c0e7d533b8592ae4af2c6376a87e"
      },
      {
        "path": "/data2/k6tk/2c/2cc77b5efc13530486ad7c5708cecad857c0f1d631c7f188b63f7cf132985aa7.png",
        "sha256": "2cc77b5efc13530486ad7c5708cecad857c0f1d631c7f188b63f7cf132985aa7"
      },
      {
        "path": "/data2/k6tk/f5/f58874feaf5e8c76fe11cfc70582871b18f69204a5de917a005e2a5ea8447d95.png",
        "sha256": "f58874feaf5e8c76fe11cfc70582871b18f69204a5de917a005e2a5ea8447d95"
      },
      {
        "path": "/data2/k6tk/02/02dacf157b2d557d02cb05fe8a892c21fc89767b8c448b3fe618abdacb03deee.png",
        "sha256": "02dacf157b2d557d02cb05fe8a892c21fc89767b8c448b3fe618abdacb03deee"
      },
      {
        "path": "/data2/k6tk/db/dbb62f6b87abab5e95b5442be97a63388955d4c0fdb773902b1c7385b5582361.png",
        "sha256": "dbb62f6b87abab5e95b5442be97a63388955d4c0fdb773902b1c7385b5582361"
      },
      {
        "path": "/data2/k6tk/1d/1d8131d43e7c8955bf9b70ccba9466aea6ac363f0ff2caed218de244110d8db0.png",
        "sha256": "1d8131d43e7c8955bf9b70ccba9466aea6ac363f0ff2caed218de244110d8db0"
      },
      {
        "path": "/data2/k6tk/0e/0ef50aa5af0ac96d6d20b92aee5bd1839453572694037cbe7f47c257829e64b7.png",
        "sha256": "0ef50aa5af0ac96d6d20b92aee5bd1839453572694037cbe7f47c257829e64b7"
      },
      {
        "path": "/data2/k6tk/80/80035b63ce224f7ffef60f1ab07ecf95a8de6f22d7489eabd7794cf6d815da37.png",
        "sha256": "80035b63ce224f7ffef60f1ab07ecf95a8de6f22d7489eabd7794cf6d815da37"
      },
      {
        "path": "/data2/k6tk/e8/e86fd5398a16494d176d4a599cdf9a9f05d5dea2d1356a88ce4416ef11556b38.png",
        "sha256": "e86fd5398a16494d176d4a599cdf9a9f05d5dea2d1356a88ce4416ef11556b38"
      },
      {
        "path": "/data2/k6tk/dd/dda52c4a9315a88b06a1e0172ece6d3d2d2b0aebea3291d440f8adb194c8185a.png",
        "sha256": "dda52c4a9315a88b06a1e0172ece6d3d2d2b0aebea3291d440f8adb194c8185a"
      },
      {
        "path": "/data2/k6tk/c5/c506ea3e1451eb6276b54c6645b5a1dc7f76fd56cad8e8c78c3420373efbb6f5.png",
        "sha256": "c506ea3e1451eb6276b54c6645b5a1dc7f76fd56cad8e8c78c3420373efbb6f5"
      },
      {
        "path": "/data2/k6tk/ea/eafcd8cd3b863242a1ef7c60024cff45807ab43ea1f90f50602646468cf30ce3.png",
        "sha256": "eafcd8cd3b863242a1ef7c60024cff45807ab43ea1f90f50602646468cf30ce3"
      },
      {
        "path": "/data2/k6tk/21/21f57c2eac77efb63d94197b4fa547928734db3e9684e5cc3bf545f838a5359d.png",
        "sha256": "21f57c2eac77efb63d94197b4fa547928734db3e9684e5cc3bf545f838a5359d"
      },
      {
        "path": "/data2/k6tk/0e/0e4d7bcba80a6961d0efda6904a12867f59beae8ecf697f75532a6e29b187d59.png",
        "sha256": "0e4d7bcba80a6961d0efda6904a12867f59beae8ecf697f75532a6e29b187d59"
      },
      {
        "path": "/data2/k6tk/aa/aaf5c2acf21374e5ff905aa44f2f8921c6b5655d3f9706eb2aa0f1f9278bd8dd.png",
        "sha256": "aaf5c2acf21374e5ff905aa44f2f8921c6b5655d3f9706eb2aa0f1f9278bd8dd"
      },
      {
        "path": "/data2/k6tk/2a/2a9c8af6785c4bca296670e8c13ed93abc2f4789c3a69e947a9349defdb19335.png",
        "sha256": "2a9c8af6785c4bca296670e8c13ed93abc2f4789c3a69e947a9349defdb19335"
      },
      {
        "path": "/data2/k6tk/f0/f0eb2f6dac6de4792c615e79662cf651362bceeb79304f0a1478ef875df6f0c2.png",
        "sha256": "f0eb2f6dac6de4792c615e79662cf651362bceeb79304f0a1478ef875df6f0c2"
      },
      {
        "path": "/data2/k6tk/94/9464c5b1c4f381c31d0bfba04e952d47cd78dd6ded30a0fe09a040f058a1c6aa.png",
        "sha256": "9464c5b1c4f381c31d0bfba04e952d47cd78dd6ded30a0fe09a040f058a1c6aa"
      },
      {
        "path": "/data2/k6tk/43/4352eeb621a275f8e1fec357846bdbfa001928ecc60576dab42a340a6bda5ac1.png",
        "sha256": "4352eeb621a275f8e1fec357846bdbfa001928ecc60576dab42a340a6bda5ac1"
      },
      {
        "path": "/data2/k6tk/53/53a73cbe1dfa584533cbc153d35c55bcd05e451c3d47eb3064a7f18def141858.png",
        "sha256": "53a73cbe1dfa584533cbc153d35c55bcd05e451c3d47eb3064a7f18def141858"
      },
      {
        "path": "/data2/k6tk/1f/1fde1c026336191f3b4cacb44fbaf649da71cecf2a07723e79e0206d628a5c5e.png",
        "sha256": "1fde1c026336191f3b4cacb44fbaf649da71cecf2a07723e79e0206d628a5c5e"
      },
      {
        "path": "/data2/k6tk/ba/ba8edd3d697865f67d5eaa54deef634c479445a23a2d403bb1b23786fc490429.png",
        "sha256": "ba8edd3d697865f67d5eaa54deef634c479445a23a2d403bb1b23786fc490429"
      },
      {
        "path": "/data2/k6tk/b4/b4d3912f2caa13c01e49f27d3a9003204510be14196cc672d6c9c91f9911016c.png",
        "sha256": "b4d3912f2caa13c01e49f27d3a9003204510be14196cc672d6c9c91f9911016c"
      },
      {
        "path": "/data2/k6tk/37/3761d5fab67fad1bd8622808251c8bdbaf46fb4a31494f87e284d26bbdd72e8d.png",
        "sha256": "3761d5fab67fad1bd8622808251c8bdbaf46fb4a31494f87e284d26bbdd72e8d"
      },
      {
        "path": "/data2/k6tk/2a/2a8f784cc52cbf1bb2e6d64032d68345d2faec6351c824dc3107b497a834fb69.png",
        "sha256": "2a8f784cc52cbf1bb2e6d64032d68345d2faec6351c824dc3107b497a834fb69"
      },
      {
        "path": "/data2/k6tk/12/12284b99ec8a42eae9fc2204f5da1c0539d73e26b61c4802329022b09c70940d.png",
        "sha256": "12284b99ec8a42eae9fc2204f5da1c0539d73e26b61c4802329022b09c70940d"
      },
      {
        "path": "/data2/k6tk/b2/b260614fe2bee3d732afb5a39caf98fbf37331f68adf32b11d425307936c1ddf.png",
        "sha256": "b260614fe2bee3d732afb5a39caf98fbf37331f68adf32b11d425307936c1ddf"
      },
      {
        "path": "/data2/k6tk/d4/d4dbaef3feced3739e149db89129d7f4b3d47936afe72ce47a79929a9a1da85a.png",
        "sha256": "d4dbaef3feced3739e149db89129d7f4b3d47936afe72ce47a79929a9a1da85a"
      },
      {
        "path": "/data2/k6tk/04/0454ddb63513417c90c3f471d936ae0670c40db9adb9277cd775a01a45fb58d7.png",
        "sha256": "0454ddb63513417c90c3f471d936ae0670c40db9adb9277cd775a01a45fb58d7"
      },
      {
        "path": "/data2/k6tk/ff/ffda5a6c84810cfba9096d2252edd4c84498949858cd554a5cafaa7cffe78772.png",
        "sha256": "ffda5a6c84810cfba9096d2252edd4c84498949858cd554a5cafaa7cffe78772"
      }
    ],
    "options": [
      "A. back-right",
      "B. back-left",
      "C. front-right",
      "D. front-left"
    ],
    "question": "If I am standing by the chair and facing away from the book, is the table to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.0833333333333333,
      2.2083333333333335,
      3.2916666666666665,
      4.416666666666667,
      5.5,
      6.625,
      7.75,
      8.833333333333334,
      9.958333333333334,
      11.041666666666666,
      12.166666666666666,
      13.25,
      14.375,
      15.5,
      16.583333333333332,
      17.708333333333332,
      18.791666666666668,
      19.916666666666668,
      21.041666666666668,
      22.125,
      23.25,
      24.333333333333332,
      25.458333333333332,
      26.541666666666668,
      27.666666666666668,
      28.791666666666668,
      29.875,
      31.0,
      32.083333333333336,
      33.208333333333336,
      34.333333333333336
    ],
    "total_num_frames": 825
  },
  "target": "<think>\nStep 1: locate the chair, the book and the table.\nStep 2: I find the table behind me, on my right when I stand at the chair facing the book.\nStep 3: I face away from the book by making a half turn. Front and back swap, and left and right swap.\nSo I find the table at my front-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 22. q443ed5caff69df392c9b296d-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-2d874bdd7847c7538216af160a324a0f7b6e69069235e7b7186ec06f1fc334b6",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q443ed5caff69df392c9b296d-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q443ed5caff69df392c9b296d",
  "paraphrase_template": "hard_classify",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 34,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "face",
        "start": 30
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "back-right",
      "source_qid": "q443ed5caff69df392c9b296d-p1",
      "source_row_sha256": "078084cb26564d200afdac20b24f8f75727e7f97764a87ccef8965264b2132c5",
      "source_store_i": 61651
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q443ed5caff69df392c9b296d-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "7747a55bff2424e52577b9597fa9510e95fb33227b81315cc68658107be6d52a"
  },
  "scene": "v2ad5592826f6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      237,
      475,
      713,
      950,
      1188,
      1426,
      1663,
      1901,
      2139,
      2377,
      2614,
      2852,
      3090,
      3327,
      3565,
      3803,
      4041,
      4278,
      4516,
      4754,
      4991,
      5229,
      5467,
      5705,
      5942,
      6180,
      6418,
      6655,
      6893,
      7131,
      7369
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9e/9e8746ab00b2e9391bd41792467b7b876c0f19359756f284f43c95ac9987ec18.png",
        "sha256": "9e8746ab00b2e9391bd41792467b7b876c0f19359756f284f43c95ac9987ec18"
      },
      {
        "path": "/data2/k6tk/9b/9b0798d2f35430d51635b10d910eefbc2e0d4d2c845ee9038567dbb3d993f187.png",
        "sha256": "9b0798d2f35430d51635b10d910eefbc2e0d4d2c845ee9038567dbb3d993f187"
      },
      {
        "path": "/data2/k6tk/ab/ab6539fcc940c2cb7c623d24f91a245eac3fbccfabc38fe1c6cc90d9c5000c17.png",
        "sha256": "ab6539fcc940c2cb7c623d24f91a245eac3fbccfabc38fe1c6cc90d9c5000c17"
      },
      {
        "path": "/data2/k6tk/85/85840e9137bd4fd38238b2fc430efdda20eade85bcfadee7780e2c0feb98b1ad.png",
        "sha256": "85840e9137bd4fd38238b2fc430efdda20eade85bcfadee7780e2c0feb98b1ad"
      },
      {
        "path": "/data2/k6tk/ee/ee8ac8e59ac4cb398d91b850fbc2ffc6c2981ad54e63bce85f1a2f55e8339725.png",
        "sha256": "ee8ac8e59ac4cb398d91b850fbc2ffc6c2981ad54e63bce85f1a2f55e8339725"
      },
      {
        "path": "/data2/k6tk/3e/3eaeadd8d3fb691b0c64081b54dd0334907448be2a856dd20f8ee4d2df19f4bb.png",
        "sha256": "3eaeadd8d3fb691b0c64081b54dd0334907448be2a856dd20f8ee4d2df19f4bb"
      },
      {
        "path": "/data2/k6tk/fd/fdf38d93186641379f0ccd4b8d839cb19a2b2bc48073e8390220c7854cade3c9.png",
        "sha256": "fdf38d93186641379f0ccd4b8d839cb19a2b2bc48073e8390220c7854cade3c9"
      },
      {
        "path": "/data2/k6tk/20/2015920691fd76e40181c41d09523e7e67049374164561c0a0eb21ba20288921.png",
        "sha256": "2015920691fd76e40181c41d09523e7e67049374164561c0a0eb21ba20288921"
      },
      {
        "path": "/data2/k6tk/1d/1df2ba9bc258f1fe1607f40ad4e2d84cefd71011e41ffb7b7d5989138af32473.png",
        "sha256": "1df2ba9bc258f1fe1607f40ad4e2d84cefd71011e41ffb7b7d5989138af32473"
      },
      {
        "path": "/data2/k6tk/c1/c1f8fe8d784fb647abbd63557e5f564bb5652438a683f3992e8fb4f57d060523.png",
        "sha256": "c1f8fe8d784fb647abbd63557e5f564bb5652438a683f3992e8fb4f57d060523"
      },
      {
        "path": "/data2/k6tk/b6/b6809a721198085b22730cf8870d47821c6df932e777c0fab76656341020a9df.png",
        "sha256": "b6809a721198085b22730cf8870d47821c6df932e777c0fab76656341020a9df"
      },
      {
        "path": "/data2/k6tk/1e/1ec668acc7ba14618afb931d1cd1dbafa6eb0a42846759e91f280eb055918091.png",
        "sha256": "1ec668acc7ba14618afb931d1cd1dbafa6eb0a42846759e91f280eb055918091"
      },
      {
        "path": "/data2/k6tk/a4/a41b71600f88718b2845de41672b79d474f8f1e33bf6ae8b3f979935962bc7e5.png",
        "sha256": "a41b71600f88718b2845de41672b79d474f8f1e33bf6ae8b3f979935962bc7e5"
      },
      {
        "path": "/data2/k6tk/28/28ba90b3003a9001442f5fcab22d4523af12bcff1a2063f912ceeae6a7afb490.png",
        "sha256": "28ba90b3003a9001442f5fcab22d4523af12bcff1a2063f912ceeae6a7afb490"
      },
      {
        "path": "/data2/k6tk/9e/9e0d04c837fa1bd38738170b9a7307423e4e0ad3937bbb10b3dee979010cc8ba.png",
        "sha256": "9e0d04c837fa1bd38738170b9a7307423e4e0ad3937bbb10b3dee979010cc8ba"
      },
      {
        "path": "/data2/k6tk/ee/eeca80fa36bf801b18bd6e1b72d738d898f851d1f726ddf81ca156e95c9be4d7.png",
        "sha256": "eeca80fa36bf801b18bd6e1b72d738d898f851d1f726ddf81ca156e95c9be4d7"
      },
      {
        "path": "/data2/k6tk/45/453166a5321a6af381ef2fe4dbb7caf82011ae8dd1d0b06bef3f4cca93f551bb.png",
        "sha256": "453166a5321a6af381ef2fe4dbb7caf82011ae8dd1d0b06bef3f4cca93f551bb"
      },
      {
        "path": "/data2/k6tk/13/13f32f3aaf48148db7c860fb5a9c2b83399039b8d693911bee196999232f5ab2.png",
        "sha256": "13f32f3aaf48148db7c860fb5a9c2b83399039b8d693911bee196999232f5ab2"
      },
      {
        "path": "/data2/k6tk/f5/f56f534492afa7b8209ce2305cb1d8bb19d43e204a6dc84b1edf96b3199c3c46.png",
        "sha256": "f56f534492afa7b8209ce2305cb1d8bb19d43e204a6dc84b1edf96b3199c3c46"
      },
      {
        "path": "/data2/k6tk/07/07136d635067c3d97d7e42319da8ab97723fa550a3232acbb20136d9fc2b2353.png",
        "sha256": "07136d635067c3d97d7e42319da8ab97723fa550a3232acbb20136d9fc2b2353"
      },
      {
        "path": "/data2/k6tk/7a/7a9764e090410956423f81b6b12d63e99f53651e630419665e88c3e56ad8e139.png",
        "sha256": "7a9764e090410956423f81b6b12d63e99f53651e630419665e88c3e56ad8e139"
      },
      {
        "path": "/data2/k6tk/bc/bccd03a27a40c4d62c79b6219debe857d3ccf4220121ea3470d24c3d3c91f649.png",
        "sha256": "bccd03a27a40c4d62c79b6219debe857d3ccf4220121ea3470d24c3d3c91f649"
      },
      {
        "path": "/data2/k6tk/53/5313341df7dbf41448160fe4a31be6bfaacc1f593adcdf770889a82cd07737bf.png",
        "sha256": "5313341df7dbf41448160fe4a31be6bfaacc1f593adcdf770889a82cd07737bf"
      },
      {
        "path": "/data2/k6tk/bd/bdb08236f6dbf60a43805e1baab5f21f6eccf28710d9823f5e85e2705e4b2eeb.png",
        "sha256": "bdb08236f6dbf60a43805e1baab5f21f6eccf28710d9823f5e85e2705e4b2eeb"
      },
      {
        "path": "/data2/k6tk/05/05aed7d29bcf42dba5c55848d0e57b3c5d3a3cbb1a673fc3ad532bce40157431.png",
        "sha256": "05aed7d29bcf42dba5c55848d0e57b3c5d3a3cbb1a673fc3ad532bce40157431"
      },
      {
        "path": "/data2/k6tk/1b/1b37687da321eede6d67f4978c85eecadabdcb528c629677c5b987041379ac49.png",
        "sha256": "1b37687da321eede6d67f4978c85eecadabdcb528c629677c5b987041379ac49"
      },
      {
        "path": "/data2/k6tk/f0/f05507c47aef332664183c02cda75d94ef8fd6cf9a3f1400dcb7a94e803b38d6.png",
        "sha256": "f05507c47aef332664183c02cda75d94ef8fd6cf9a3f1400dcb7a94e803b38d6"
      },
      {
        "path": "/data2/k6tk/2a/2ac9d09e28a3b21c80a8a5bf45077ed454f1a3f7ba79e659d706dda118a14e83.png",
        "sha256": "2ac9d09e28a3b21c80a8a5bf45077ed454f1a3f7ba79e659d706dda118a14e83"
      },
      {
        "path": "/data2/k6tk/b9/b9352a44036445996eb741fe8f8313b9a2044635a7843dadc41fe5b038ec5d42.png",
        "sha256": "b9352a44036445996eb741fe8f8313b9a2044635a7843dadc41fe5b038ec5d42"
      },
      {
        "path": "/data2/k6tk/fe/fe62968c49b0e78d5c802fe2341aa4504c91ba38b4076b1b3345252b30ba0791.png",
        "sha256": "fe62968c49b0e78d5c802fe2341aa4504c91ba38b4076b1b3345252b30ba0791"
      },
      {
        "path": "/data2/k6tk/47/47b9c430b79307b34db654b6faa00a4cac01b846eaa5d766f29da9f425155c43.png",
        "sha256": "47b9c430b79307b34db654b6faa00a4cac01b846eaa5d766f29da9f425155c43"
      },
      {
        "path": "/data2/k6tk/27/276f732079680e7e48dc3ece567ce9f47f5d7f492466220cb63162e64aa62717.png",
        "sha256": "276f732079680e7e48dc3ece567ce9f47f5d7f492466220cb63162e64aa62717"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-right",
      "C. back-left",
      "D. front-right"
    ],
    "question": "From beside the coat stand, I face away from the stamp. Which direction describes the seat relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.95,
      7.916666666666667,
      11.883333333333333,
      15.833333333333334,
      19.8,
      23.766666666666666,
      27.716666666666665,
      31.683333333333334,
      35.65,
      39.61666666666667,
      43.56666666666667,
      47.53333333333333,
      51.5,
      55.45,
      59.416666666666664,
      63.38333333333333,
      67.35,
      71.3,
      75.26666666666667,
      79.23333333333333,
      83.18333333333334,
      87.15,
      91.11666666666666,
      95.08333333333333,
      99.03333333333333,
      103.0,
      106.96666666666667,
      110.91666666666667,
      114.88333333333334,
      118.85,
      122.81666666666666
    ],
    "total_num_frames": 7370
  },
  "target": "<think>\nStep 1: locate the seat, the coat stand and the stamp.\nStep 2: I find the seat behind me, on my right when I stand at the coat stand facing the stamp.\nStep 3: I face away from the stamp by making a half turn. Front and back swap, and left and right swap.\nSo I find the seat at my front-left.\n</think>\n\nA",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 23. qd5a07d1a6228495f4076d8e0_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-cc00d9da948aa04c867036b0284dea23ca31f568cc8cfcfa6c36508125f1543f",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qd5a07d1a6228495f4076d8e0"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "back-right",
      "source_qid": "qd5a07d1a6228495f4076d8e0",
      "source_row_sha256": "fc35069ae7f57179a536ef2ec2bc207f379f4009f083cd5a6bec95ff7f1f571f",
      "source_store_i": 1953
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qd5a07d1a6228495f4076d8e0_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "a02a4cd789f2535143275ad97e55a2d3364abee0a953caa6f5a653e19abcbb8e"
  },
  "scene": "vd4a638931dab",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      112,
      224,
      336,
      448,
      561,
      673,
      785,
      897,
      1010,
      1122,
      1234,
      1346,
      1458,
      1571,
      1683,
      1795,
      1907,
      2020,
      2132,
      2244,
      2356,
      2468,
      2581,
      2693,
      2805,
      2917,
      3030,
      3142,
      3254,
      3366,
      3479
    ],
    "frames": [
      {
        "path": "/data2/k6tk/00/0049f40d5c70bb6cd2bbd023902dc53c33447bd3e3c0418456326b2e67a3491d.png",
        "sha256": "0049f40d5c70bb6cd2bbd023902dc53c33447bd3e3c0418456326b2e67a3491d"
      },
      {
        "path": "/data2/k6tk/e5/e5c927f9415e083c901538f850d9527e7444ba8d8897a3800d7da1ffa12abbe8.png",
        "sha256": "e5c927f9415e083c901538f850d9527e7444ba8d8897a3800d7da1ffa12abbe8"
      },
      {
        "path": "/data2/k6tk/bf/bf8e49d7e59000120f98ff7cab2d072a8c79c27e3ea571f00489c901427becf8.png",
        "sha256": "bf8e49d7e59000120f98ff7cab2d072a8c79c27e3ea571f00489c901427becf8"
      },
      {
        "path": "/data2/k6tk/02/0281dd0f691683afe8084f1b654ec396f38e30bc545c4f67c14d31cd968072af.png",
        "sha256": "0281dd0f691683afe8084f1b654ec396f38e30bc545c4f67c14d31cd968072af"
      },
      {
        "path": "/data2/k6tk/ef/ef92806140700f26e4af927770f856474be00fa48bee7ecfc8e8b0acc3c63cb0.png",
        "sha256": "ef92806140700f26e4af927770f856474be00fa48bee7ecfc8e8b0acc3c63cb0"
      },
      {
        "path": "/data2/k6tk/1f/1fc5f2548aa87f21e8c3a3fb55a53f144205d97b2aabd482f5de3bc88175ce26.png",
        "sha256": "1fc5f2548aa87f21e8c3a3fb55a53f144205d97b2aabd482f5de3bc88175ce26"
      },
      {
        "path": "/data2/k6tk/85/85e97eec65359259fa9fec04be287567070d07214e8a55a9663abb8f9f7cfe7f.png",
        "sha256": "85e97eec65359259fa9fec04be287567070d07214e8a55a9663abb8f9f7cfe7f"
      },
      {
        "path": "/data2/k6tk/a6/a650aaf076aa00f76c41c9bf203893a842e8d760d0f5e610ef827ff8491859fb.png",
        "sha256": "a650aaf076aa00f76c41c9bf203893a842e8d760d0f5e610ef827ff8491859fb"
      },
      {
        "path": "/data2/k6tk/b6/b604e1fede887c39f73f8b86997b40432d5e4a7732e727cb4aa0d039eb4121a4.png",
        "sha256": "b604e1fede887c39f73f8b86997b40432d5e4a7732e727cb4aa0d039eb4121a4"
      },
      {
        "path": "/data2/k6tk/fa/fad1c954dac3f9a5f2f057bbbd9c3aa4a64c3ff03d6d64a0f3633ae19bce66a1.png",
        "sha256": "fad1c954dac3f9a5f2f057bbbd9c3aa4a64c3ff03d6d64a0f3633ae19bce66a1"
      },
      {
        "path": "/data2/k6tk/f7/f79490f912de2a8c41b4679ff368e5c2216f2be306f0583f9adb2474d9bd4f86.png",
        "sha256": "f79490f912de2a8c41b4679ff368e5c2216f2be306f0583f9adb2474d9bd4f86"
      },
      {
        "path": "/data2/k6tk/dd/dd132ed154aa51a533980a9a60c55be61a968bb957a3ab682136b5bf544becff.png",
        "sha256": "dd132ed154aa51a533980a9a60c55be61a968bb957a3ab682136b5bf544becff"
      },
      {
        "path": "/data2/k6tk/c8/c83136073e280ee704cd02bb9cca818482ad9e14c1f0e1ddd69bfa34f11a22bc.png",
        "sha256": "c83136073e280ee704cd02bb9cca818482ad9e14c1f0e1ddd69bfa34f11a22bc"
      },
      {
        "path": "/data2/k6tk/f8/f82181817bcb55dc8eeff519133694cb0b331c0bc95c7e240c3aa319b6971934.png",
        "sha256": "f82181817bcb55dc8eeff519133694cb0b331c0bc95c7e240c3aa319b6971934"
      },
      {
        "path": "/data2/k6tk/f0/f088cfe22d9de4ba469bdaf67e666c190a4e00f06caea32e8e269d2ea24b479f.png",
        "sha256": "f088cfe22d9de4ba469bdaf67e666c190a4e00f06caea32e8e269d2ea24b479f"
      },
      {
        "path": "/data2/k6tk/2c/2c0024bc8107d0c65cbd96a0e81cfa5746b3877a1b4402bb63e53e7040a2e447.png",
        "sha256": "2c0024bc8107d0c65cbd96a0e81cfa5746b3877a1b4402bb63e53e7040a2e447"
      },
      {
        "path": "/data2/k6tk/e4/e496e58400041adf157ba3479b8b9344ba974fb0b47f5a0063a6742405ea1880.png",
        "sha256": "e496e58400041adf157ba3479b8b9344ba974fb0b47f5a0063a6742405ea1880"
      },
      {
        "path": "/data2/k6tk/ed/edcd89f9bdab1d2736230cd32227cdf7a902a1c3a816e9ab2abb23b276d6aa9f.png",
        "sha256": "edcd89f9bdab1d2736230cd32227cdf7a902a1c3a816e9ab2abb23b276d6aa9f"
      },
      {
        "path": "/data2/k6tk/fd/fde2643fed0e18f3c8b2f0ffc190478f4a7cf2b7079af0c890b3533f5875a2a5.png",
        "sha256": "fde2643fed0e18f3c8b2f0ffc190478f4a7cf2b7079af0c890b3533f5875a2a5"
      },
      {
        "path": "/data2/k6tk/d7/d7646e17096bf426379c23e7569bf0d34359b899b16c4ba230743cd63d5a418d.png",
        "sha256": "d7646e17096bf426379c23e7569bf0d34359b899b16c4ba230743cd63d5a418d"
      },
      {
        "path": "/data2/k6tk/f5/f5fcb4431086511ce73669bdcd42e68212eeb9d88d6618f4882d34a439f0e1da.png",
        "sha256": "f5fcb4431086511ce73669bdcd42e68212eeb9d88d6618f4882d34a439f0e1da"
      },
      {
        "path": "/data2/k6tk/91/91443caa584da71385b38c875910cc0fc7d3b62caa44db79fdd4922b8c5e0ef3.png",
        "sha256": "91443caa584da71385b38c875910cc0fc7d3b62caa44db79fdd4922b8c5e0ef3"
      },
      {
        "path": "/data2/k6tk/f6/f65c806ee0b6a089eac6e4973a9a19c6356a5deb2579dae1e02e0c4029712c53.png",
        "sha256": "f65c806ee0b6a089eac6e4973a9a19c6356a5deb2579dae1e02e0c4029712c53"
      },
      {
        "path": "/data2/k6tk/d8/d87bbb2d9f5743a660cb9687d693cdb54fadf7a4dbf3493a1b446a9ae3d0a041.png",
        "sha256": "d87bbb2d9f5743a660cb9687d693cdb54fadf7a4dbf3493a1b446a9ae3d0a041"
      },
      {
        "path": "/data2/k6tk/a2/a2eea214742302c8cfb416edbe1f57a8dc0f230020532235d33175124dac1389.png",
        "sha256": "a2eea214742302c8cfb416edbe1f57a8dc0f230020532235d33175124dac1389"
      },
      {
        "path": "/data2/k6tk/9d/9d0a009f4dd0fa0776ef861c64758fe55f6a46aa4865014c9abedc98cccbd495.png",
        "sha256": "9d0a009f4dd0fa0776ef861c64758fe55f6a46aa4865014c9abedc98cccbd495"
      },
      {
        "path": "/data2/k6tk/ad/addd5381e8760d1f8ce104338ab31b0bc10cfadf570b6b4f31c68cf848394138.png",
        "sha256": "addd5381e8760d1f8ce104338ab31b0bc10cfadf570b6b4f31c68cf848394138"
      },
      {
        "path": "/data2/k6tk/e8/e8ce22bd067afe794a6555dccb90da739de2a571282d65db29d54320c71ac36b.png",
        "sha256": "e8ce22bd067afe794a6555dccb90da739de2a571282d65db29d54320c71ac36b"
      },
      {
        "path": "/data2/k6tk/eb/eb8de5d468831df132ad91c34eb237a108684af03078d3947a5f3f2fe5eccfef.png",
        "sha256": "eb8de5d468831df132ad91c34eb237a108684af03078d3947a5f3f2fe5eccfef"
      },
      {
        "path": "/data2/k6tk/c2/c2b803cf9d18689827c2aaa7f744049845b22156b9373a28d14512c5fc530714.png",
        "sha256": "c2b803cf9d18689827c2aaa7f744049845b22156b9373a28d14512c5fc530714"
      },
      {
        "path": "/data2/k6tk/27/272dda00b06053a8556594a1f3f8768c0dffce1510ff8a6caa637f1cd31bb2a4.png",
        "sha256": "272dda00b06053a8556594a1f3f8768c0dffce1510ff8a6caa637f1cd31bb2a4"
      },
      {
        "path": "/data2/k6tk/cb/cb0730a0974a1256fdc0bda3440b6dd02423852262169b054791a645a08e6d80.png",
        "sha256": "cb0730a0974a1256fdc0bda3440b6dd02423852262169b054791a645a08e6d80"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the backpack and facing away from the computer mouse, is the stool to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      4.666666666666667,
      9.333333333333334,
      14.0,
      18.666666666666668,
      23.375,
      28.041666666666668,
      32.708333333333336,
      37.375,
      42.083333333333336,
      46.75,
      51.416666666666664,
      56.083333333333336,
      60.75,
      65.45833333333333,
      70.125,
      74.79166666666667,
      79.45833333333333,
      84.16666666666667,
      88.83333333333333,
      93.5,
      98.16666666666667,
      102.83333333333333,
      107.54166666666667,
      112.20833333333333,
      116.875,
      121.54166666666667,
      126.25,
      130.91666666666666,
      135.58333333333334,
      140.25,
      144.95833333333334
    ],
    "total_num_frames": 3480
  },
  "target": "<think>\nStep 1: locate the backpack, the computer mouse and the stool.\nStep 2: facing the computer mouse from the backpack, I find the stool behind me, on my right.\nStep 3: I face away from the computer mouse by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the stool at my front-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 24. qf2eddd8169e1a3a6f0a86a1b_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-6a6289fac18e288a77baaa569ac040c307b0eebb3b8b19e73b9f8471e8480376",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qf2eddd8169e1a3a6f0a86a1b"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "back-right",
      "source_qid": "qf2eddd8169e1a3a6f0a86a1b",
      "source_row_sha256": "716df989c6a0963b3e97686ce4dd5f8333819745be484637b045f7f1c90c34a3",
      "source_store_i": 1491
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf2eddd8169e1a3a6f0a86a1b_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "aa7c9c40f5068ff85bcdf44e5819beb712c168137666923d322ef16dc69fc168"
  },
  "scene": "va71273982272",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      347,
      695,
      1043,
      1390,
      1738,
      2086,
      2433,
      2781,
      3129,
      3477,
      3824,
      4172,
      4520,
      4867,
      5215,
      5563,
      5911,
      6258,
      6606,
      6954,
      7301,
      7649,
      7997,
      8345,
      8692,
      9040,
      9388,
      9735,
      10083,
      10431,
      10779
    ],
    "frames": [
      {
        "path": "/data2/k6tk/0f/0f06fcd11bf28fff41cefdc7d2fcb5e0362873c109e50d08f40a881515a50a91.png",
        "sha256": "0f06fcd11bf28fff41cefdc7d2fcb5e0362873c109e50d08f40a881515a50a91"
      },
      {
        "path": "/data2/k6tk/2c/2c089d6cd547a31498526ccd34cbad1d5b57debbcdf2dfa93ab76678ae5d1b74.png",
        "sha256": "2c089d6cd547a31498526ccd34cbad1d5b57debbcdf2dfa93ab76678ae5d1b74"
      },
      {
        "path": "/data2/k6tk/b2/b2388acb6388de4ff9000cf05d3d233213c3e7658afd9e7f5ff1c0a2f04a3ae8.png",
        "sha256": "b2388acb6388de4ff9000cf05d3d233213c3e7658afd9e7f5ff1c0a2f04a3ae8"
      },
      {
        "path": "/data2/k6tk/b5/b554cb71839d9d5dced26f587a43aabf7f101f0c953f71036ad8d653b6f6ee68.png",
        "sha256": "b554cb71839d9d5dced26f587a43aabf7f101f0c953f71036ad8d653b6f6ee68"
      },
      {
        "path": "/data2/k6tk/be/beefcada618e05e0d87e862aef827d631750d072ba3c18b600aeb09701b13441.png",
        "sha256": "beefcada618e05e0d87e862aef827d631750d072ba3c18b600aeb09701b13441"
      },
      {
        "path": "/data2/k6tk/d5/d5f4576870c5a400703e36a86db5c346acfb8c60968bf59e00fcae277d8634b1.png",
        "sha256": "d5f4576870c5a400703e36a86db5c346acfb8c60968bf59e00fcae277d8634b1"
      },
      {
        "path": "/data2/k6tk/98/98bd9171b6685be5da3c9282c2633d0c6b597dc48fdfa8ee64e5b30bbbef9f99.png",
        "sha256": "98bd9171b6685be5da3c9282c2633d0c6b597dc48fdfa8ee64e5b30bbbef9f99"
      },
      {
        "path": "/data2/k6tk/d3/d30410ed4e07b42954b22b05c048cd5669a84f1206361041200de565777908f2.png",
        "sha256": "d30410ed4e07b42954b22b05c048cd5669a84f1206361041200de565777908f2"
      },
      {
        "path": "/data2/k6tk/7f/7f351af1f92c86420c746698ef65be400bcd1b40e60181cd13c90548189eeec9.png",
        "sha256": "7f351af1f92c86420c746698ef65be400bcd1b40e60181cd13c90548189eeec9"
      },
      {
        "path": "/data2/k6tk/bb/bbaa9aa6d75c387660319eeb507de7398e2ab47a13d71fb4c8a4ef80b98e3d7d.png",
        "sha256": "bbaa9aa6d75c387660319eeb507de7398e2ab47a13d71fb4c8a4ef80b98e3d7d"
      },
      {
        "path": "/data2/k6tk/44/4476b7d799ff29e5ea75068785e940a09bdd32ec01260f0ab7105e1a76f53dd4.png",
        "sha256": "4476b7d799ff29e5ea75068785e940a09bdd32ec01260f0ab7105e1a76f53dd4"
      },
      {
        "path": "/data2/k6tk/4b/4b48d563460406950cf8ee9cc27e2883fd13fe6081884f380ff337f2e559ef92.png",
        "sha256": "4b48d563460406950cf8ee9cc27e2883fd13fe6081884f380ff337f2e559ef92"
      },
      {
        "path": "/data2/k6tk/ec/ec3cc48b8ed5e05061de7b482142e90074d7a3985802956df2ff0175d124f48a.png",
        "sha256": "ec3cc48b8ed5e05061de7b482142e90074d7a3985802956df2ff0175d124f48a"
      },
      {
        "path": "/data2/k6tk/bc/bc5e17eb4c303855788a80c74f96e3f580942e442a3e7fedc8e48a79f926c54f.png",
        "sha256": "bc5e17eb4c303855788a80c74f96e3f580942e442a3e7fedc8e48a79f926c54f"
      },
      {
        "path": "/data2/k6tk/c4/c4e19f8af34b3ad74d0c88aa8dc8bfd999d23b003e7605e371b1903886aee276.png",
        "sha256": "c4e19f8af34b3ad74d0c88aa8dc8bfd999d23b003e7605e371b1903886aee276"
      },
      {
        "path": "/data2/k6tk/d8/d885f0558142b73e325bdbf34f2772854e8754ba11bc8d6cf29ba2eb9cd014da.png",
        "sha256": "d885f0558142b73e325bdbf34f2772854e8754ba11bc8d6cf29ba2eb9cd014da"
      },
      {
        "path": "/data2/k6tk/fc/fcc3d1575aa04cfa260f5ae07be29eb893d665145812a7af31dbf28698e34381.png",
        "sha256": "fcc3d1575aa04cfa260f5ae07be29eb893d665145812a7af31dbf28698e34381"
      },
      {
        "path": "/data2/k6tk/93/933ffe510939f12a7be8eea3727a6a4fef6bb9d327e8a7f6936fda5a73399017.png",
        "sha256": "933ffe510939f12a7be8eea3727a6a4fef6bb9d327e8a7f6936fda5a73399017"
      },
      {
        "path": "/data2/k6tk/e6/e69cd8e92238a4ab6b63f0f0a29ecd9f3aa21dfafbbb985e41c12667fd315386.png",
        "sha256": "e69cd8e92238a4ab6b63f0f0a29ecd9f3aa21dfafbbb985e41c12667fd315386"
      },
      {
        "path": "/data2/k6tk/04/04a324d483d726b76c9abec9394a5bac1601c17d0d78f8df4de58a4254288f96.png",
        "sha256": "04a324d483d726b76c9abec9394a5bac1601c17d0d78f8df4de58a4254288f96"
      },
      {
        "path": "/data2/k6tk/38/38f093c5a48e9b1d62b7d551218bcc9e3deda782aa4a81587a3ce24a977dca69.png",
        "sha256": "38f093c5a48e9b1d62b7d551218bcc9e3deda782aa4a81587a3ce24a977dca69"
      },
      {
        "path": "/data2/k6tk/5f/5f4fc9ae2989ad6af2a9be01ce897623b313aa65a178398018fc501c73a85d6d.png",
        "sha256": "5f4fc9ae2989ad6af2a9be01ce897623b313aa65a178398018fc501c73a85d6d"
      },
      {
        "path": "/data2/k6tk/55/556ecf7c185d4bc2b3cb3af9a265e01da01920662bacfa6c7f6aa11c38b63bbe.png",
        "sha256": "556ecf7c185d4bc2b3cb3af9a265e01da01920662bacfa6c7f6aa11c38b63bbe"
      },
      {
        "path": "/data2/k6tk/7b/7b06cd8ec5207c1159f41c9b1ace406cca71fd754fac5acc494b0fa9eb5494c1.png",
        "sha256": "7b06cd8ec5207c1159f41c9b1ace406cca71fd754fac5acc494b0fa9eb5494c1"
      },
      {
        "path": "/data2/k6tk/3b/3b3f63fa3e2113ea79d66932e8f636335ff48191e015299ba164a00a1def7f43.png",
        "sha256": "3b3f63fa3e2113ea79d66932e8f636335ff48191e015299ba164a00a1def7f43"
      },
      {
        "path": "/data2/k6tk/0d/0d28c94d0176e87d37b6613000a942dbfe94d96e8b070e89762459e120150bac.png",
        "sha256": "0d28c94d0176e87d37b6613000a942dbfe94d96e8b070e89762459e120150bac"
      },
      {
        "path": "/data2/k6tk/6f/6f3532db5370772dcfc46b3d7aa590c2012dcf74c6b6d2fe52afdf3541112fd5.png",
        "sha256": "6f3532db5370772dcfc46b3d7aa590c2012dcf74c6b6d2fe52afdf3541112fd5"
      },
      {
        "path": "/data2/k6tk/b5/b57a6642f916fce5f5ff5bccc9affd7697fd41d65f8d84af0e5dfe38050dc905.png",
        "sha256": "b57a6642f916fce5f5ff5bccc9affd7697fd41d65f8d84af0e5dfe38050dc905"
      },
      {
        "path": "/data2/k6tk/84/84e43e760d5682798655e99743182dce140cde359f4c644639b440a61c32799d.png",
        "sha256": "84e43e760d5682798655e99743182dce140cde359f4c644639b440a61c32799d"
      },
      {
        "path": "/data2/k6tk/db/dbc7a14bc9cc826355f65eacf3831ea7f7eee99b16688e7021b21e9522178dd3.png",
        "sha256": "dbc7a14bc9cc826355f65eacf3831ea7f7eee99b16688e7021b21e9522178dd3"
      },
      {
        "path": "/data2/k6tk/09/09eaf1674dc066ceb0593751e1203c14df85be6b34e56e4268165fed4ad9ded1.png",
        "sha256": "09eaf1674dc066ceb0593751e1203c14df85be6b34e56e4268165fed4ad9ded1"
      },
      {
        "path": "/data2/k6tk/85/858deace36f418cb64d1fbf980698ac61ebc7174027db56c4b1c39b5c3d969af.png",
        "sha256": "858deace36f418cb64d1fbf980698ac61ebc7174027db56c4b1c39b5c3d969af"
      }
    ],
    "options": [
      "A. front-right",
      "B. back-right",
      "C. back-left",
      "D. front-left"
    ],
    "question": "If I am standing by the intercom and facing away from the cover up panel, is the mattress to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      5.783333333333333,
      11.583333333333334,
      17.383333333333333,
      23.166666666666668,
      28.966666666666665,
      34.766666666666666,
      40.55,
      46.35,
      52.15,
      57.95,
      63.733333333333334,
      69.53333333333333,
      75.33333333333333,
      81.11666666666666,
      86.91666666666667,
      92.71666666666667,
      98.51666666666667,
      104.3,
      110.1,
      115.9,
      121.68333333333334,
      127.48333333333333,
      133.28333333333333,
      139.08333333333334,
      144.86666666666667,
      150.66666666666666,
      156.46666666666667,
      162.25,
      168.05,
      173.85,
      179.65
    ],
    "total_num_frames": 10780
  },
  "target": "<think>\nStep 1: locate the mattress, the intercom and the cover up panel.\nStep 2: facing the cover up panel from the intercom, I find the mattress behind me, on my right.\nStep 3: I face away from the cover up panel by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the mattress at my front-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 25. q7be799c3c9bcee5460d873d5-p1_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-3eb6f71ebf7aec54ff3ea7c344ea2e6c1a99464c0a56a372f433eeb39ff1244e",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q7be799c3c9bcee5460d873d5-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q7be799c3c9bcee5460d873d5",
  "paraphrase_template": "hard_classify",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 32,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "face",
        "start": 28
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-left",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "back-right",
      "source_qid": "q7be799c3c9bcee5460d873d5-p1",
      "source_row_sha256": "463e753ed6c2868fd240ad978ecee3ed38689f0df96ebada1f37dbfb2160116c",
      "source_store_i": 69468
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q7be799c3c9bcee5460d873d5-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "55b3ef9395a448736b8f788a0400336e7a32c40fbfcbf77178f274ab6511c017"
  },
  "scene": "v612feaa8c23e",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      35,
      71,
      107,
      143,
      179,
      215,
      251,
      286,
      322,
      358,
      394,
      430,
      466,
      502,
      538,
      573,
      609,
      645,
      681,
      717,
      753,
      789,
      825,
      860,
      896,
      932,
      968,
      1004,
      1040,
      1076,
      1112
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a3/a322f05d7a763a55f2c468236f88ce745420caeed4e170e543a9b9b514347406.png",
        "sha256": "a322f05d7a763a55f2c468236f88ce745420caeed4e170e543a9b9b514347406"
      },
      {
        "path": "/data2/k6tk/45/45e6aa58bb302e0d3600adb2348509212dd06a714d5d134611ee6b643cbd8bb5.png",
        "sha256": "45e6aa58bb302e0d3600adb2348509212dd06a714d5d134611ee6b643cbd8bb5"
      },
      {
        "path": "/data2/k6tk/95/958de6791d502f3f38cbec7c5bcf967d73f5ddba18faa69b1aa183e6d2d43c54.png",
        "sha256": "958de6791d502f3f38cbec7c5bcf967d73f5ddba18faa69b1aa183e6d2d43c54"
      },
      {
        "path": "/data2/k6tk/7f/7f980d06e6e3c51f90109b00235f9ece3ce9134d9ec3917dbf9d1bd6a24a670c.png",
        "sha256": "7f980d06e6e3c51f90109b00235f9ece3ce9134d9ec3917dbf9d1bd6a24a670c"
      },
      {
        "path": "/data2/k6tk/b7/b7ace0c9fb290d5afbaf3e5cb435ecda602c49f3a9c91fa55f5be8d2a4893abd.png",
        "sha256": "b7ace0c9fb290d5afbaf3e5cb435ecda602c49f3a9c91fa55f5be8d2a4893abd"
      },
      {
        "path": "/data2/k6tk/d4/d46b82c45d6360ad119dcf7d7839483451c0d13c0b4d91f04e3c79ee1132c1c6.png",
        "sha256": "d46b82c45d6360ad119dcf7d7839483451c0d13c0b4d91f04e3c79ee1132c1c6"
      },
      {
        "path": "/data2/k6tk/32/32565c65449e8a73325d32845cf86c6930daa7fefa5457088039f43afcbf3401.png",
        "sha256": "32565c65449e8a73325d32845cf86c6930daa7fefa5457088039f43afcbf3401"
      },
      {
        "path": "/data2/k6tk/6b/6b1d158641d2f6b43566b7914cc7a1a6f187a8072f16e53df5714156d489070b.png",
        "sha256": "6b1d158641d2f6b43566b7914cc7a1a6f187a8072f16e53df5714156d489070b"
      },
      {
        "path": "/data2/k6tk/09/09e71df2490ae80128a13aab5baee3a63a20df2bd7f294bfc8575f3e2b3dbe5f.png",
        "sha256": "09e71df2490ae80128a13aab5baee3a63a20df2bd7f294bfc8575f3e2b3dbe5f"
      },
      {
        "path": "/data2/k6tk/b6/b6522d85f660f0d5605ab942b550c6b9ed3ecc3d7980ce087ee43d9881e9f3f3.png",
        "sha256": "b6522d85f660f0d5605ab942b550c6b9ed3ecc3d7980ce087ee43d9881e9f3f3"
      },
      {
        "path": "/data2/k6tk/63/6354aa91f6d685ab5225261d622bcf4d9a2f37e90c55649294c119f855a3d2d2.png",
        "sha256": "6354aa91f6d685ab5225261d622bcf4d9a2f37e90c55649294c119f855a3d2d2"
      },
      {
        "path": "/data2/k6tk/1a/1acea2830d0d1682cd1bb3c8451b2a67ac717ddea1290b7ee63f843f96debc95.png",
        "sha256": "1acea2830d0d1682cd1bb3c8451b2a67ac717ddea1290b7ee63f843f96debc95"
      },
      {
        "path": "/data2/k6tk/0f/0ffcf9c3137dcfc41486284f62d44ffe76077fa8025aebfa9d22d82d08dc9bf8.png",
        "sha256": "0ffcf9c3137dcfc41486284f62d44ffe76077fa8025aebfa9d22d82d08dc9bf8"
      },
      {
        "path": "/data2/k6tk/cd/cdb34c5c2d6f98e8643a28f04dd81f49a9e072a27029ec162b1aae29b24e3697.png",
        "sha256": "cdb34c5c2d6f98e8643a28f04dd81f49a9e072a27029ec162b1aae29b24e3697"
      },
      {
        "path": "/data2/k6tk/9c/9c26ec7a05713425e549283413681c805c572b4653c023095d92677cd6984258.png",
        "sha256": "9c26ec7a05713425e549283413681c805c572b4653c023095d92677cd6984258"
      },
      {
        "path": "/data2/k6tk/3a/3a39b3ddc7beb0aeb1134fbcb7b9d50fafea197561f08dd75e63b3ff12f33b97.png",
        "sha256": "3a39b3ddc7beb0aeb1134fbcb7b9d50fafea197561f08dd75e63b3ff12f33b97"
      },
      {
        "path": "/data2/k6tk/19/19794233db68887bce573927cdbf12e39b644674e190a855547a9f6071f7de08.png",
        "sha256": "19794233db68887bce573927cdbf12e39b644674e190a855547a9f6071f7de08"
      },
      {
        "path": "/data2/k6tk/8d/8dcdb75c1c00af2e08c0a43cc7ae6c468fe1faf6dad59956c30fe83ce455af7c.png",
        "sha256": "8dcdb75c1c00af2e08c0a43cc7ae6c468fe1faf6dad59956c30fe83ce455af7c"
      },
      {
        "path": "/data2/k6tk/4b/4b43425909cdbc7559ee22d324aa782e2c73e3a6595778cfa14b86d986b849eb.png",
        "sha256": "4b43425909cdbc7559ee22d324aa782e2c73e3a6595778cfa14b86d986b849eb"
      },
      {
        "path": "/data2/k6tk/07/07b5a1de9d8d6fb558ee00049f3d9f824f460fcb65f1990434ed2a4ff631e804.png",
        "sha256": "07b5a1de9d8d6fb558ee00049f3d9f824f460fcb65f1990434ed2a4ff631e804"
      },
      {
        "path": "/data2/k6tk/f7/f7a7d77c9ade289554c659b33c5a0e3d45423aa3d89037b7a392f7d82c88f9b3.png",
        "sha256": "f7a7d77c9ade289554c659b33c5a0e3d45423aa3d89037b7a392f7d82c88f9b3"
      },
      {
        "path": "/data2/k6tk/9a/9a6b6fcde00eab509355226d378e95b321b1c9521fab61e9ab68fc8f05ac65a4.png",
        "sha256": "9a6b6fcde00eab509355226d378e95b321b1c9521fab61e9ab68fc8f05ac65a4"
      },
      {
        "path": "/data2/k6tk/1e/1e6f24af71248fc12dde5e76d65c4edad87b28f3e7436282a68546304b8fdedf.png",
        "sha256": "1e6f24af71248fc12dde5e76d65c4edad87b28f3e7436282a68546304b8fdedf"
      },
      {
        "path": "/data2/k6tk/99/99c4a8943dc368e9729d0256e687e3afeb596741dc49aa3a3f4bb311071789c9.png",
        "sha256": "99c4a8943dc368e9729d0256e687e3afeb596741dc49aa3a3f4bb311071789c9"
      },
      {
        "path": "/data2/k6tk/9c/9cdda8e805ae9b18a1c6f6eb6f3ff81fded91eba0e6ceca1da0a83b9e13e617b.png",
        "sha256": "9cdda8e805ae9b18a1c6f6eb6f3ff81fded91eba0e6ceca1da0a83b9e13e617b"
      },
      {
        "path": "/data2/k6tk/65/65b678ee3da94a4200d1983cb3d4546f61182fcb8698c75c0e7ca6d6152fdec8.png",
        "sha256": "65b678ee3da94a4200d1983cb3d4546f61182fcb8698c75c0e7ca6d6152fdec8"
      },
      {
        "path": "/data2/k6tk/46/463712bfbf020a2e6c78b04e2deb49aac3d21bb7d79c0f9a5e3780599f01dc95.png",
        "sha256": "463712bfbf020a2e6c78b04e2deb49aac3d21bb7d79c0f9a5e3780599f01dc95"
      },
      {
        "path": "/data2/k6tk/00/00e197544eeb4cb4c9668fed5244c1d469158adf7aa5a6bc37e59bdf4cf05ceb.png",
        "sha256": "00e197544eeb4cb4c9668fed5244c1d469158adf7aa5a6bc37e59bdf4cf05ceb"
      },
      {
        "path": "/data2/k6tk/a8/a8d48a642a81f0b0d251a15c5f31a9e12927a1c76de675de8b59b5b1fa28788d.png",
        "sha256": "a8d48a642a81f0b0d251a15c5f31a9e12927a1c76de675de8b59b5b1fa28788d"
      },
      {
        "path": "/data2/k6tk/d1/d12933b22da06448e51db9f0b595e0fe4f0f7e6d4442310e6f166f0a9eac5a70.png",
        "sha256": "d12933b22da06448e51db9f0b595e0fe4f0f7e6d4442310e6f166f0a9eac5a70"
      },
      {
        "path": "/data2/k6tk/36/36432f20492c1522c08dc305e1bbab58dc7c1616d5f7b941fdd7469ff1b396de.png",
        "sha256": "36432f20492c1522c08dc305e1bbab58dc7c1616d5f7b941fdd7469ff1b396de"
      },
      {
        "path": "/data2/k6tk/89/89f52f566dcb33d0b5df1dbb4780e09e099484d16a55be6f2299715c5ee537a6.png",
        "sha256": "89f52f566dcb33d0b5df1dbb4780e09e099484d16a55be6f2299715c5ee537a6"
      }
    ],
    "options": [
      "A. back-right",
      "B. back-left",
      "C. front-right",
      "D. front-left"
    ],
    "question": "From beside the backpack, I face away from the door. Which direction describes the box relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.4583333333333333,
      2.9583333333333335,
      4.458333333333333,
      5.958333333333333,
      7.458333333333333,
      8.958333333333334,
      10.458333333333334,
      11.916666666666666,
      13.416666666666666,
      14.916666666666666,
      16.416666666666668,
      17.916666666666668,
      19.416666666666668,
      20.916666666666668,
      22.416666666666668,
      23.875,
      25.375,
      26.875,
      28.375,
      29.875,
      31.375,
      32.875,
      34.375,
      35.833333333333336,
      37.333333333333336,
      38.833333333333336,
      40.333333333333336,
      41.833333333333336,
      43.333333333333336,
      44.833333333333336,
      46.333333333333336
    ],
    "total_num_frames": 1113
  },
  "target": "<think>\nStep 1: find the backpack and the door, then the box.\nStep 2: I find the box behind me, on my right when I stand at the backpack facing the door.\nStep 3: I face away from the door by making a half turn. Front and back swap, and left and right swap.\nSo I find the box at my front-left.\n</think>\n\nD",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 26. q210de619f1661cfd93e9c477_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-3106e9740fc9d494bb574e557c84d619e4c5f123553c5539877e9ac2517c4358",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q210de619f1661cfd93e9c477"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "back-left",
      "source_qid": "q210de619f1661cfd93e9c477",
      "source_row_sha256": "30b6d849cbb359c46691d19c640927f9b02379bf97c6a0a4635f00fb57b5262b",
      "source_store_i": 2873
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q210de619f1661cfd93e9c477_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "7df3c452e2429839869a7a728c7e5ac1b7e358dc072c222ca4216b710557f0c2"
  },
  "scene": "vea7816d56c59",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      47,
      94,
      142,
      189,
      237,
      284,
      332,
      379,
      427,
      474,
      522,
      569,
      617,
      664,
      712,
      759,
      807,
      854,
      902,
      949,
      997,
      1044,
      1092,
      1139,
      1187,
      1234,
      1282,
      1329,
      1377,
      1424,
      1472
    ],
    "frames": [
      {
        "path": "/data2/k6tk/8a/8ae1d54f02101f5794fbc4de189f65ac0dd9912c71d87f9ad424f9de7fd3f59d.png",
        "sha256": "8ae1d54f02101f5794fbc4de189f65ac0dd9912c71d87f9ad424f9de7fd3f59d"
      },
      {
        "path": "/data2/k6tk/aa/aa9bf334d8a8148b006e4db4868b38e94263e23c25b2dac3d2eb144678c0d4d4.png",
        "sha256": "aa9bf334d8a8148b006e4db4868b38e94263e23c25b2dac3d2eb144678c0d4d4"
      },
      {
        "path": "/data2/k6tk/28/28c56dcefd898fb22fc7cad52560fc0977d006206ffe953f187b6353d0839097.png",
        "sha256": "28c56dcefd898fb22fc7cad52560fc0977d006206ffe953f187b6353d0839097"
      },
      {
        "path": "/data2/k6tk/83/832d970cbc7527d49f31be5e4c9df56855603c372388bdb217fe1bce83580c0f.png",
        "sha256": "832d970cbc7527d49f31be5e4c9df56855603c372388bdb217fe1bce83580c0f"
      },
      {
        "path": "/data2/k6tk/74/7464d54c5983890cbb626d1ba83195358eb54fe39df08892c2a6052987f4e474.png",
        "sha256": "7464d54c5983890cbb626d1ba83195358eb54fe39df08892c2a6052987f4e474"
      },
      {
        "path": "/data2/k6tk/00/00e4564984972fd30011711e242af2d3bfc9234550937fd147e900ce5a09e17e.png",
        "sha256": "00e4564984972fd30011711e242af2d3bfc9234550937fd147e900ce5a09e17e"
      },
      {
        "path": "/data2/k6tk/54/5461469bfabbee62cef4e144ddc046ba3d8c2ea050a9de31ff09c4a971a7cfac.png",
        "sha256": "5461469bfabbee62cef4e144ddc046ba3d8c2ea050a9de31ff09c4a971a7cfac"
      },
      {
        "path": "/data2/k6tk/08/083c5c3a86a5f47efff41a6777b020612abadfcbbfe1e270d0030fcf4ab2cef0.png",
        "sha256": "083c5c3a86a5f47efff41a6777b020612abadfcbbfe1e270d0030fcf4ab2cef0"
      },
      {
        "path": "/data2/k6tk/86/86f03ec8f3a2e700646192c80e87fb7d50c6df459835ca5acc77d8a09073b697.png",
        "sha256": "86f03ec8f3a2e700646192c80e87fb7d50c6df459835ca5acc77d8a09073b697"
      },
      {
        "path": "/data2/k6tk/b5/b5610b858503e65b998e8e608db1b5e83c6fda1ec77708c060c83c8c75407065.png",
        "sha256": "b5610b858503e65b998e8e608db1b5e83c6fda1ec77708c060c83c8c75407065"
      },
      {
        "path": "/data2/k6tk/ab/ab42d5bb629750b2a5f90d29fbbda57172f78942079970d3696539baee6391e5.png",
        "sha256": "ab42d5bb629750b2a5f90d29fbbda57172f78942079970d3696539baee6391e5"
      },
      {
        "path": "/data2/k6tk/a3/a35e8bde90a72a9585798ab9400fe9023ec3525d9067590fd5cd8978feacad93.png",
        "sha256": "a35e8bde90a72a9585798ab9400fe9023ec3525d9067590fd5cd8978feacad93"
      },
      {
        "path": "/data2/k6tk/26/26bd4634e041f1f8f7d46503b3196db89ecf8ab9a229c5d7d506a2de82ba5fd6.png",
        "sha256": "26bd4634e041f1f8f7d46503b3196db89ecf8ab9a229c5d7d506a2de82ba5fd6"
      },
      {
        "path": "/data2/k6tk/6d/6d6fc505d93448b7b8518c0903a9b348782a69498d42d28386c66b449f834841.png",
        "sha256": "6d6fc505d93448b7b8518c0903a9b348782a69498d42d28386c66b449f834841"
      },
      {
        "path": "/data2/k6tk/4f/4f3b1c82947da168d807780b691769f0fa80dec90e8f117a27822ef418ae69fc.png",
        "sha256": "4f3b1c82947da168d807780b691769f0fa80dec90e8f117a27822ef418ae69fc"
      },
      {
        "path": "/data2/k6tk/9b/9bddd8d8ce6677ff228d6bffbe0801ea2f93efc271820c37c425493dfa59b227.png",
        "sha256": "9bddd8d8ce6677ff228d6bffbe0801ea2f93efc271820c37c425493dfa59b227"
      },
      {
        "path": "/data2/k6tk/54/54fc9fe7b0699698f2a512244f2214019c2b569764cda2e1774ac3e4ea17673c.png",
        "sha256": "54fc9fe7b0699698f2a512244f2214019c2b569764cda2e1774ac3e4ea17673c"
      },
      {
        "path": "/data2/k6tk/fd/fdb35de8f2609e4d437a6422d3afcd85298fa500a1d24861f2b7f1fa6083c015.png",
        "sha256": "fdb35de8f2609e4d437a6422d3afcd85298fa500a1d24861f2b7f1fa6083c015"
      },
      {
        "path": "/data2/k6tk/02/0257025e07996538d7d7bd984242ac07aa13c483523295cfce584922970acb39.png",
        "sha256": "0257025e07996538d7d7bd984242ac07aa13c483523295cfce584922970acb39"
      },
      {
        "path": "/data2/k6tk/8f/8fed1d85fb60b128acc5b05829a8f9436542d2de73c9cea120667f7dc97a4ecd.png",
        "sha256": "8fed1d85fb60b128acc5b05829a8f9436542d2de73c9cea120667f7dc97a4ecd"
      },
      {
        "path": "/data2/k6tk/1b/1b88affc01893ef9530607772a0a705613f5f658deaa5fd99b294069295fce02.png",
        "sha256": "1b88affc01893ef9530607772a0a705613f5f658deaa5fd99b294069295fce02"
      },
      {
        "path": "/data2/k6tk/b5/b519ca714995e157b60dcc64224fa137fe99a36c338a96079dcda501bdaf9560.png",
        "sha256": "b519ca714995e157b60dcc64224fa137fe99a36c338a96079dcda501bdaf9560"
      },
      {
        "path": "/data2/k6tk/ef/efe8e3b582dac0c39944c9f6ecd141151356f7d94a8daa8d38a604d2b1bd0956.png",
        "sha256": "efe8e3b582dac0c39944c9f6ecd141151356f7d94a8daa8d38a604d2b1bd0956"
      },
      {
        "path": "/data2/k6tk/29/296cf3d050485d1b9bc1be575cae93542246da38ebc845875cedb29b4dd1b624.png",
        "sha256": "296cf3d050485d1b9bc1be575cae93542246da38ebc845875cedb29b4dd1b624"
      },
      {
        "path": "/data2/k6tk/de/def06f859594a3ecc06f16489a3e411ab9fbe00fb5997108372711dc31266a6a.png",
        "sha256": "def06f859594a3ecc06f16489a3e411ab9fbe00fb5997108372711dc31266a6a"
      },
      {
        "path": "/data2/k6tk/67/670325272c028daf25586f43fbae7e061bd408ff9ec4972ab3987345dfcbbb17.png",
        "sha256": "670325272c028daf25586f43fbae7e061bd408ff9ec4972ab3987345dfcbbb17"
      },
      {
        "path": "/data2/k6tk/ad/ad831b0054f05d4a04ee4dce0b71db20f5a55b7948ec53b016b479a245c25e90.png",
        "sha256": "ad831b0054f05d4a04ee4dce0b71db20f5a55b7948ec53b016b479a245c25e90"
      },
      {
        "path": "/data2/k6tk/f8/f88555668f00b97e436691e00cb672043b56a2a2bb4aa01a04bd49d9f40931bc.png",
        "sha256": "f88555668f00b97e436691e00cb672043b56a2a2bb4aa01a04bd49d9f40931bc"
      },
      {
        "path": "/data2/k6tk/b8/b8c1ef382c488e7cf7329cb8ff1b369cee5cef095460804df458fb212d340c6e.png",
        "sha256": "b8c1ef382c488e7cf7329cb8ff1b369cee5cef095460804df458fb212d340c6e"
      },
      {
        "path": "/data2/k6tk/24/24fe82fa75757e32058e1418d7bb9414d522949dc51d76009d3f829a0dbd80b6.png",
        "sha256": "24fe82fa75757e32058e1418d7bb9414d522949dc51d76009d3f829a0dbd80b6"
      },
      {
        "path": "/data2/k6tk/b8/b82a13eca91ee92a54f861df250bca03ab7246a6f4b4a3fc32a4c01d48af9222.png",
        "sha256": "b82a13eca91ee92a54f861df250bca03ab7246a6f4b4a3fc32a4c01d48af9222"
      },
      {
        "path": "/data2/k6tk/c8/c88751aeb7ce30131946faceee9e123a96d0239517dd01529c406c51a191e9b2.png",
        "sha256": "c88751aeb7ce30131946faceee9e123a96d0239517dd01529c406c51a191e9b2"
      }
    ],
    "options": [
      "A. front-right",
      "B. back-right",
      "C. front-left",
      "D. back-left"
    ],
    "question": "If I am standing by the backpack and facing away from the door, is the nightstand to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.9583333333333333,
      3.9166666666666665,
      5.916666666666667,
      7.875,
      9.875,
      11.833333333333334,
      13.833333333333334,
      15.791666666666666,
      17.791666666666668,
      19.75,
      21.75,
      23.708333333333332,
      25.708333333333332,
      27.666666666666668,
      29.666666666666668,
      31.625,
      33.625,
      35.583333333333336,
      37.583333333333336,
      39.541666666666664,
      41.541666666666664,
      43.5,
      45.5,
      47.458333333333336,
      49.458333333333336,
      51.416666666666664,
      53.416666666666664,
      55.375,
      57.375,
      59.333333333333336,
      61.333333333333336
    ],
    "total_num_frames": 1473
  },
  "target": "<think>\nStep 1: find the backpack and the door, then the nightstand.\nStep 2: I find the nightstand behind me, on my left when I stand at the backpack facing the door.\nStep 3: I face away from the door by making a half turn. Front and back swap, and left and right swap.\nSo I find the nightstand at my front-right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 27. qae7f80cd75063cd129fa7dd1-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-53253547a231c1116c42e13ede48cde03896154e99eebaba52a595dded62a0bf",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qae7f80cd75063cd129fa7dd1-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qae7f80cd75063cd129fa7dd1",
  "paraphrase_template": "hard_viewpoint",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 34,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "looking at",
        "start": 24
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "A",
      "source_label": "back-left",
      "source_qid": "qae7f80cd75063cd129fa7dd1-p1",
      "source_row_sha256": "5b1f985407997ae55242c328f592ce817d23fd02a5d2650b420214d9ce3b03e2",
      "source_store_i": 59380
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qae7f80cd75063cd129fa7dd1-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "ea69a03512d10a57e43b41a79c97bb8a4e74031a1bb049ea5af1fadcc7097804"
  },
  "scene": "v14e375e18b9c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      383,
      767,
      1151,
      1534,
      1918,
      2302,
      2686,
      3069,
      3453,
      3837,
      4221,
      4604,
      4988,
      5372,
      5756,
      6139,
      6523,
      6907,
      7291,
      7674,
      8058,
      8442,
      8826,
      9209,
      9593,
      9977,
      10361,
      10744,
      11128,
      11512,
      11896
    ],
    "frames": [
      {
        "path": "/data2/k6tk/1a/1a84358bf0fd6d5179a4508f69aa1af5eab25ceb088966c22d074a2b3b5b096a.png",
        "sha256": "1a84358bf0fd6d5179a4508f69aa1af5eab25ceb088966c22d074a2b3b5b096a"
      },
      {
        "path": "/data2/k6tk/b2/b25a990993eee47708e90497c6440f1e702891c4ce6353d54fab3f233ab29319.png",
        "sha256": "b25a990993eee47708e90497c6440f1e702891c4ce6353d54fab3f233ab29319"
      },
      {
        "path": "/data2/k6tk/4d/4d8de2ef4dfebb2e2e4cbe5d00a130e1b833675811b898bf6bfd4affc8a2a722.png",
        "sha256": "4d8de2ef4dfebb2e2e4cbe5d00a130e1b833675811b898bf6bfd4affc8a2a722"
      },
      {
        "path": "/data2/k6tk/48/4867df403fb2644ebf26c5937a037f34f1adcb39b21d66b5d0bfcfce7b777db7.png",
        "sha256": "4867df403fb2644ebf26c5937a037f34f1adcb39b21d66b5d0bfcfce7b777db7"
      },
      {
        "path": "/data2/k6tk/3b/3baa0d5420bd429f1d118594ce7739d6bcfe7d424a49a8f33aca433be26afdf5.png",
        "sha256": "3baa0d5420bd429f1d118594ce7739d6bcfe7d424a49a8f33aca433be26afdf5"
      },
      {
        "path": "/data2/k6tk/d2/d27242485037d19df0c2a78b29bfb44672d7c5dfea8b8bec0c99954a92fab539.png",
        "sha256": "d27242485037d19df0c2a78b29bfb44672d7c5dfea8b8bec0c99954a92fab539"
      },
      {
        "path": "/data2/k6tk/ae/ae566f3688dd1ace4dacf0a3640ea585c0fb6baa86a0becf3b43cf385e8a42d1.png",
        "sha256": "ae566f3688dd1ace4dacf0a3640ea585c0fb6baa86a0becf3b43cf385e8a42d1"
      },
      {
        "path": "/data2/k6tk/38/384bb1ba3aa78abf5589a078dfe7c7d606336169af9331d8b469109926c6c265.png",
        "sha256": "384bb1ba3aa78abf5589a078dfe7c7d606336169af9331d8b469109926c6c265"
      },
      {
        "path": "/data2/k6tk/03/034a86120809ab1c15ec35eb53759c32ded27f20f1604724b8f35fb44d1b867e.png",
        "sha256": "034a86120809ab1c15ec35eb53759c32ded27f20f1604724b8f35fb44d1b867e"
      },
      {
        "path": "/data2/k6tk/95/956e68adf55d805fb1129d5f37196339ad3df79088d699fbde113c843bd09fa8.png",
        "sha256": "956e68adf55d805fb1129d5f37196339ad3df79088d699fbde113c843bd09fa8"
      },
      {
        "path": "/data2/k6tk/e7/e79f1a4595fba636b956489de7a85b764eeeaaefbfc8d16a7978c18f28c56635.png",
        "sha256": "e79f1a4595fba636b956489de7a85b764eeeaaefbfc8d16a7978c18f28c56635"
      },
      {
        "path": "/data2/k6tk/4b/4b0ff1a1c0520daa93280b048bcfe8ea9eef9bb8740c5956ffc7140cb56a2723.png",
        "sha256": "4b0ff1a1c0520daa93280b048bcfe8ea9eef9bb8740c5956ffc7140cb56a2723"
      },
      {
        "path": "/data2/k6tk/84/846e121606c8b2c805c5211a39a05b69d258988b7bccdb74a815287f7dc4127d.png",
        "sha256": "846e121606c8b2c805c5211a39a05b69d258988b7bccdb74a815287f7dc4127d"
      },
      {
        "path": "/data2/k6tk/a7/a78fc6141fc0dc14e420f6af739c90e359281f2a7b56a281b30be8116c572cfd.png",
        "sha256": "a78fc6141fc0dc14e420f6af739c90e359281f2a7b56a281b30be8116c572cfd"
      },
      {
        "path": "/data2/k6tk/35/356012abf0a6a2d3f989f327e91cfe800d661a93a9227d5ddeac3f898516e6d4.png",
        "sha256": "356012abf0a6a2d3f989f327e91cfe800d661a93a9227d5ddeac3f898516e6d4"
      },
      {
        "path": "/data2/k6tk/bc/bce3949e86cd90249650a348050e7273657dc69ffd45a054492fe66352f4b397.png",
        "sha256": "bce3949e86cd90249650a348050e7273657dc69ffd45a054492fe66352f4b397"
      },
      {
        "path": "/data2/k6tk/ea/ea5189bb461afd10a7abc64471f450d99631f10e7f9caf60dbd07fbf9c17e11f.png",
        "sha256": "ea5189bb461afd10a7abc64471f450d99631f10e7f9caf60dbd07fbf9c17e11f"
      },
      {
        "path": "/data2/k6tk/63/6319f90cc17aea1c2daa6bebfdbef8ac161cedc22f1a14b651a46a2c373413df.png",
        "sha256": "6319f90cc17aea1c2daa6bebfdbef8ac161cedc22f1a14b651a46a2c373413df"
      },
      {
        "path": "/data2/k6tk/dc/dcaf44ff0b14113b42d3a5f145ad7b90a9784e8968609e47dd755d9d247850eb.png",
        "sha256": "dcaf44ff0b14113b42d3a5f145ad7b90a9784e8968609e47dd755d9d247850eb"
      },
      {
        "path": "/data2/k6tk/b0/b00c2622b5deb575a42d570d2a9709c60a632e069300ec639cf67870488543dc.png",
        "sha256": "b00c2622b5deb575a42d570d2a9709c60a632e069300ec639cf67870488543dc"
      },
      {
        "path": "/data2/k6tk/e0/e0cb8a76aecb310aa8c05a0c416d0710802a01497fedbde658498a49cd282b40.png",
        "sha256": "e0cb8a76aecb310aa8c05a0c416d0710802a01497fedbde658498a49cd282b40"
      },
      {
        "path": "/data2/k6tk/c0/c058645973e7d697f97a3d7d943d57f6ad020b1f30beb5757bbf44ba280a5874.png",
        "sha256": "c058645973e7d697f97a3d7d943d57f6ad020b1f30beb5757bbf44ba280a5874"
      },
      {
        "path": "/data2/k6tk/a9/a97254706ea3dd5beeca9ac417cea355e61552b83cf881285756ae956a17a665.png",
        "sha256": "a97254706ea3dd5beeca9ac417cea355e61552b83cf881285756ae956a17a665"
      },
      {
        "path": "/data2/k6tk/5a/5ad66e6b5f8fd1538d3e253251c1edd6173fa0477829bc1ea28ecc9e42ab7cc4.png",
        "sha256": "5ad66e6b5f8fd1538d3e253251c1edd6173fa0477829bc1ea28ecc9e42ab7cc4"
      },
      {
        "path": "/data2/k6tk/40/4019659dd8cbd79153bed2ed47df6b3b98729941acdd381a67ba892f07d8a5d4.png",
        "sha256": "4019659dd8cbd79153bed2ed47df6b3b98729941acdd381a67ba892f07d8a5d4"
      },
      {
        "path": "/data2/k6tk/1d/1d897441178e574cf10f328ca79f83b432bb2b4039112ce94699d64efdb6171f.png",
        "sha256": "1d897441178e574cf10f328ca79f83b432bb2b4039112ce94699d64efdb6171f"
      },
      {
        "path": "/data2/k6tk/ff/fff4ff1cdfced41af3921b2150f3276aa8800429096f6e154fe35eaebae1bcd2.png",
        "sha256": "fff4ff1cdfced41af3921b2150f3276aa8800429096f6e154fe35eaebae1bcd2"
      },
      {
        "path": "/data2/k6tk/3a/3a3dfc878b56bd560fdfb2befd9e0e35f061f82cdcd1ee522256d86a590c6c41.png",
        "sha256": "3a3dfc878b56bd560fdfb2befd9e0e35f061f82cdcd1ee522256d86a590c6c41"
      },
      {
        "path": "/data2/k6tk/aa/aa81c270bf2a870daf3f552f6496f18772274c4b9d6ba16488013c907f79a6e8.png",
        "sha256": "aa81c270bf2a870daf3f552f6496f18772274c4b9d6ba16488013c907f79a6e8"
      },
      {
        "path": "/data2/k6tk/e7/e73722f1e29b7dd0751d5ffb9ccd5451c0a9e7189f950dcd92c87fb7194db461.png",
        "sha256": "e73722f1e29b7dd0751d5ffb9ccd5451c0a9e7189f950dcd92c87fb7194db461"
      },
      {
        "path": "/data2/k6tk/0d/0d57d7e3955a0ba3b74fdb6ef3307a35e9e205e59997679c5a0df8fa775b2865.png",
        "sha256": "0d57d7e3955a0ba3b74fdb6ef3307a35e9e205e59997679c5a0df8fa775b2865"
      },
      {
        "path": "/data2/k6tk/bc/bc066c396e3d36062c54620b9c219a421d043e6b8cd3dfd6eeac449eea44209f.png",
        "sha256": "bc066c396e3d36062c54620b9c219a421d043e6b8cd3dfd6eeac449eea44209f"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-right",
      "C. back-right",
      "D. front-left"
    ],
    "question": "I stand by the backpack facing away from the chair. Where is the wardrobe relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.383333333333334,
      12.783333333333333,
      19.183333333333334,
      25.566666666666666,
      31.966666666666665,
      38.36666666666667,
      44.766666666666666,
      51.15,
      57.55,
      63.95,
      70.35,
      76.73333333333333,
      83.13333333333334,
      89.53333333333333,
      95.93333333333334,
      102.31666666666666,
      108.71666666666667,
      115.11666666666666,
      121.51666666666667,
      127.9,
      134.3,
      140.7,
      147.1,
      153.48333333333332,
      159.88333333333333,
      166.28333333333333,
      172.68333333333334,
      179.06666666666666,
      185.46666666666667,
      191.86666666666667,
      198.26666666666668
    ],
    "total_num_frames": 11897
  },
  "target": "<think>\nStep 1: find the backpack and the chair, then the wardrobe.\nStep 2: facing the chair from the backpack, I find the wardrobe behind me, on my left.\nStep 3: I face away from the chair by making a half turn. Front and back swap, and left and right swap.\nSo I find the wardrobe at my front-right.\n</think>\n\nB",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 28. qca4ca05459afd525aeb53d81_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-acbb5c9d163d40914454abf6b170cb50eeda5b335c8ff6992f4edabeac48a477",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qca4ca05459afd525aeb53d81"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 43,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 37
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "D",
      "source_label": "back-left",
      "source_qid": "qca4ca05459afd525aeb53d81",
      "source_row_sha256": "f92bcfca2af633eb171952d00503a0132c1fed179883231ab377ff3cb6785681",
      "source_store_i": 1661
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qca4ca05459afd525aeb53d81_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "2ccc7216e17d0eb889e78d3824ca0ab27d5e76eb697bb9f5e79f70f0209d62a7"
  },
  "scene": "v32c034ed33ac",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      209,
      418,
      627,
      836,
      1046,
      1255,
      1464,
      1673,
      1883,
      2092,
      2301,
      2510,
      2719,
      2929,
      3138,
      3347,
      3556,
      3766,
      3975,
      4184,
      4393,
      4602,
      4812,
      5021,
      5230,
      5439,
      5649,
      5858,
      6067,
      6276,
      6486
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f2/f2ee85a7178947aa4b255207d9c7822d9dde4317c478878b8360f5c474eb2055.png",
        "sha256": "f2ee85a7178947aa4b255207d9c7822d9dde4317c478878b8360f5c474eb2055"
      },
      {
        "path": "/data2/k6tk/f7/f7b52a08b2866e7e6adee596cabb27d6b6143f09ea291b0e4de657da6fb712af.png",
        "sha256": "f7b52a08b2866e7e6adee596cabb27d6b6143f09ea291b0e4de657da6fb712af"
      },
      {
        "path": "/data2/k6tk/2f/2fcb13e2fc16686847d4870c4d0d0b5cc797cbd0cf0f147f77b9f0e8c0738a36.png",
        "sha256": "2fcb13e2fc16686847d4870c4d0d0b5cc797cbd0cf0f147f77b9f0e8c0738a36"
      },
      {
        "path": "/data2/k6tk/90/903b9156e7ddc675973c4b54161213eaa72019719e8b11391ecf9896b80da988.png",
        "sha256": "903b9156e7ddc675973c4b54161213eaa72019719e8b11391ecf9896b80da988"
      },
      {
        "path": "/data2/k6tk/fe/fea89d1d6e7aa6ab1f550ef92d41c38357dc8c1e92d4c5fbb4b73f1c3d2cc6ee.png",
        "sha256": "fea89d1d6e7aa6ab1f550ef92d41c38357dc8c1e92d4c5fbb4b73f1c3d2cc6ee"
      },
      {
        "path": "/data2/k6tk/32/32dd404562b25b3826e2b641fb3c5c20d7124b71f0cd1c0dc4ab4ead5ee9d8fe.png",
        "sha256": "32dd404562b25b3826e2b641fb3c5c20d7124b71f0cd1c0dc4ab4ead5ee9d8fe"
      },
      {
        "path": "/data2/k6tk/8b/8bfffb1b8ccc73b396ad753cec8aab3a0dc576c131455fa453105e3469851c9a.png",
        "sha256": "8bfffb1b8ccc73b396ad753cec8aab3a0dc576c131455fa453105e3469851c9a"
      },
      {
        "path": "/data2/k6tk/6a/6a9246ed86f972c94c0e44680a6315e82bcf54a111da5dd4b80d9b66abe9702f.png",
        "sha256": "6a9246ed86f972c94c0e44680a6315e82bcf54a111da5dd4b80d9b66abe9702f"
      },
      {
        "path": "/data2/k6tk/93/93f2d2d3422bd2601439410df5c888d3b71821d1804feb454d0d5d52d5ae4667.png",
        "sha256": "93f2d2d3422bd2601439410df5c888d3b71821d1804feb454d0d5d52d5ae4667"
      },
      {
        "path": "/data2/k6tk/01/01d02712e91b80329fa3740300ec0584d54f8cd43248de73de8cd663325ae701.png",
        "sha256": "01d02712e91b80329fa3740300ec0584d54f8cd43248de73de8cd663325ae701"
      },
      {
        "path": "/data2/k6tk/06/06ff4f3c8b342b6fd08571b4fbaf1ee674310d0711db1314f9f267d8e7ec1034.png",
        "sha256": "06ff4f3c8b342b6fd08571b4fbaf1ee674310d0711db1314f9f267d8e7ec1034"
      },
      {
        "path": "/data2/k6tk/54/54787c5c2f68d67e0a98ad865adbe1e71082f9d3a1700a34c481de20017776a2.png",
        "sha256": "54787c5c2f68d67e0a98ad865adbe1e71082f9d3a1700a34c481de20017776a2"
      },
      {
        "path": "/data2/k6tk/9c/9c8a84721d358d0c8d03b70473d41519289fa61c9c4e64f729d5fdba8c84e1aa.png",
        "sha256": "9c8a84721d358d0c8d03b70473d41519289fa61c9c4e64f729d5fdba8c84e1aa"
      },
      {
        "path": "/data2/k6tk/5c/5c727027531c58465a832e09b71b23c67674d615622cf60a814ec4cc1433b0e4.png",
        "sha256": "5c727027531c58465a832e09b71b23c67674d615622cf60a814ec4cc1433b0e4"
      },
      {
        "path": "/data2/k6tk/e8/e8756b0263be2caa72360c389b74c61e1204a270cdba1b6d08e3aa2ad68d3613.png",
        "sha256": "e8756b0263be2caa72360c389b74c61e1204a270cdba1b6d08e3aa2ad68d3613"
      },
      {
        "path": "/data2/k6tk/89/89ab8989edb5ddfee05f3e004eb119717e1716f708b04ab9afe398fcde04934b.png",
        "sha256": "89ab8989edb5ddfee05f3e004eb119717e1716f708b04ab9afe398fcde04934b"
      },
      {
        "path": "/data2/k6tk/3d/3d2db8f55692be1d7c93c9895ee15de50e1bf1ca28d9581529966b9d3c5453f4.png",
        "sha256": "3d2db8f55692be1d7c93c9895ee15de50e1bf1ca28d9581529966b9d3c5453f4"
      },
      {
        "path": "/data2/k6tk/4f/4f9042c779ff4e33455d994469d49d3cbbb9fe7b629cd3b1dbbd64a7439e9ebb.png",
        "sha256": "4f9042c779ff4e33455d994469d49d3cbbb9fe7b629cd3b1dbbd64a7439e9ebb"
      },
      {
        "path": "/data2/k6tk/ee/ee9316ed9044c4b2f0d05f9b2724e203afe624cf8c07b3a63c6af3003122e313.png",
        "sha256": "ee9316ed9044c4b2f0d05f9b2724e203afe624cf8c07b3a63c6af3003122e313"
      },
      {
        "path": "/data2/k6tk/0d/0db99b165356fc16f15c10fca1f3d0a9f3e4cf2721622c7fb3a6fac7954c5a7b.png",
        "sha256": "0db99b165356fc16f15c10fca1f3d0a9f3e4cf2721622c7fb3a6fac7954c5a7b"
      },
      {
        "path": "/data2/k6tk/a9/a9a09c37e568280db2b6f816bbcecd6526384eb2bd37aded3264ac3d44fa84d0.png",
        "sha256": "a9a09c37e568280db2b6f816bbcecd6526384eb2bd37aded3264ac3d44fa84d0"
      },
      {
        "path": "/data2/k6tk/51/51306f075adee2c4df49303356197fac3296ed9071130eb15738a425e9ebff50.png",
        "sha256": "51306f075adee2c4df49303356197fac3296ed9071130eb15738a425e9ebff50"
      },
      {
        "path": "/data2/k6tk/cd/cdbee6acd34a2e1fae94c574476a3fc75a3e861b28ee4e33af09da4e33b655cf.png",
        "sha256": "cdbee6acd34a2e1fae94c574476a3fc75a3e861b28ee4e33af09da4e33b655cf"
      },
      {
        "path": "/data2/k6tk/28/28da35a6b6693003e6361ebfa8f75546cb0be6425609e46a5fa8555110ed984b.png",
        "sha256": "28da35a6b6693003e6361ebfa8f75546cb0be6425609e46a5fa8555110ed984b"
      },
      {
        "path": "/data2/k6tk/10/10c8ae7450c66a1946da7dd544e06b5a5a4a29c75a37b0d827d7d35af398b060.png",
        "sha256": "10c8ae7450c66a1946da7dd544e06b5a5a4a29c75a37b0d827d7d35af398b060"
      },
      {
        "path": "/data2/k6tk/c6/c68f4e7ec6e695b6fbd99e130b4ab4c657d510e92538706ee9cbc89d675b3690.png",
        "sha256": "c68f4e7ec6e695b6fbd99e130b4ab4c657d510e92538706ee9cbc89d675b3690"
      },
      {
        "path": "/data2/k6tk/13/13905b9ae94e80040eb7769121311961a504fb57a2f031da61311a226098cdc1.png",
        "sha256": "13905b9ae94e80040eb7769121311961a504fb57a2f031da61311a226098cdc1"
      },
      {
        "path": "/data2/k6tk/9b/9be18bd8e4b50f2b70b8270054ce293825561872552c103d735b90ea9f504cf8.png",
        "sha256": "9be18bd8e4b50f2b70b8270054ce293825561872552c103d735b90ea9f504cf8"
      },
      {
        "path": "/data2/k6tk/01/01072bae617696ac447c201ae4d72d5b63ca229cb97d2780ecbfce7ce487ff21.png",
        "sha256": "01072bae617696ac447c201ae4d72d5b63ca229cb97d2780ecbfce7ce487ff21"
      },
      {
        "path": "/data2/k6tk/45/45a66c05001bb9c1aad92567e9c7abd6074a01e8ac449e632d75b0b3da2d5c6c.png",
        "sha256": "45a66c05001bb9c1aad92567e9c7abd6074a01e8ac449e632d75b0b3da2d5c6c"
      },
      {
        "path": "/data2/k6tk/f9/f92f703c46ea7390d2f4779e99624a6e96943f5b8f61b61ab3fffeee851a0351.png",
        "sha256": "f92f703c46ea7390d2f4779e99624a6e96943f5b8f61b61ab3fffeee851a0351"
      },
      {
        "path": "/data2/k6tk/a1/a1395c434aaad38e01f12f80475202bf344cc1a723f5cff6e648beddddf2f24b.png",
        "sha256": "a1395c434aaad38e01f12f80475202bf344cc1a723f5cff6e648beddddf2f24b"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-right",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the backpack and facing away from the bags, is the curtain rod to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.4833333333333334,
      6.966666666666667,
      10.45,
      13.933333333333334,
      17.433333333333334,
      20.916666666666668,
      24.4,
      27.883333333333333,
      31.383333333333333,
      34.86666666666667,
      38.35,
      41.833333333333336,
      45.31666666666667,
      48.81666666666667,
      52.3,
      55.78333333333333,
      59.266666666666666,
      62.766666666666666,
      66.25,
      69.73333333333333,
      73.21666666666667,
      76.7,
      80.2,
      83.68333333333334,
      87.16666666666667,
      90.65,
      94.15,
      97.63333333333334,
      101.11666666666666,
      104.6,
      108.1
    ],
    "total_num_frames": 6487
  },
  "target": "<think>\nStep 1: locate the backpack, the bags and the curtain rod.\nStep 2: standing at the backpack and facing the bags, I find the curtain rod behind me, on my left.\nStep 3: I face away from the bags by making a half turn. Front and back swap, and left and right swap.\nSo I find the curtain rod at my front-right.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 29. qa45a82525f864fd067f89c53-p1_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-84a65a46d1817ea34961c49c35a2a66e90d0bf23a2db297e3b1f4695072c87e0",
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "qa45a82525f864fd067f89c53-p1"
  ],
  "license": [
    "ScanNet Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "qa45a82525f864fd067f89c53",
  "paraphrase_template": "hard_classify",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 27,
        "new_clause": "face away from",
        "rule": "single_clause_substitution",
        "source_clause": "face",
        "start": 23
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "C",
      "source_label": "back-left",
      "source_qid": "qa45a82525f864fd067f89c53-p1",
      "source_row_sha256": "a5944a2c0c4888dd093c25fd97451e1d7577ad8cca9133376ab41e060d9ab98d",
      "source_store_i": 65762
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qa45a82525f864fd067f89c53-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "00066bc60b19db7bceb40279361d7e901ae5f11c07e9ae56f87447f268b09938"
  },
  "scene": "v3943b8f006c7",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      62,
      125,
      187,
      250,
      313,
      375,
      438,
      500,
      563,
      626,
      688,
      751,
      813,
      876,
      939,
      1001,
      1064,
      1127,
      1189,
      1252,
      1314,
      1377,
      1440,
      1502,
      1565,
      1627,
      1690,
      1753,
      1815,
      1878,
      1941
    ],
    "frames": [
      {
        "path": "/data2/k6tk/0a/0aab1496389b7402a66a1ce2c8f5310db8b0d4cbc37fe238f675383f9ae349a6.png",
        "sha256": "0aab1496389b7402a66a1ce2c8f5310db8b0d4cbc37fe238f675383f9ae349a6"
      },
      {
        "path": "/data2/k6tk/9a/9a74545e7b93bd86d4522f44ee40461be52e11ec50c41b0b92c540b404325769.png",
        "sha256": "9a74545e7b93bd86d4522f44ee40461be52e11ec50c41b0b92c540b404325769"
      },
      {
        "path": "/data2/k6tk/06/06ef96a60793de921bb459078127824e94436de3c9a2d411fc6e01296e540f01.png",
        "sha256": "06ef96a60793de921bb459078127824e94436de3c9a2d411fc6e01296e540f01"
      },
      {
        "path": "/data2/k6tk/b3/b34ceb1359310e1d82a3abbe483711c22e543114d00bbee2e13281cdf1713c72.png",
        "sha256": "b34ceb1359310e1d82a3abbe483711c22e543114d00bbee2e13281cdf1713c72"
      },
      {
        "path": "/data2/k6tk/7a/7aaf9cd68b8e34977ec33ff9cfa6fce7a4583997619982c46e1ec04d177628f5.png",
        "sha256": "7aaf9cd68b8e34977ec33ff9cfa6fce7a4583997619982c46e1ec04d177628f5"
      },
      {
        "path": "/data2/k6tk/26/262a3d9da3cd16c6a386b8b05377b4ac67651245aa0dbb665d0de24c539ea8d6.png",
        "sha256": "262a3d9da3cd16c6a386b8b05377b4ac67651245aa0dbb665d0de24c539ea8d6"
      },
      {
        "path": "/data2/k6tk/42/4267cc3665c16e4577c730e52517190b0cca39ff5122c3ec4e59f4337eb3a612.png",
        "sha256": "4267cc3665c16e4577c730e52517190b0cca39ff5122c3ec4e59f4337eb3a612"
      },
      {
        "path": "/data2/k6tk/65/65b1bbb5ae035c897cbdaf92362b509ec540055b8b30ba274c8461b5c5e27535.png",
        "sha256": "65b1bbb5ae035c897cbdaf92362b509ec540055b8b30ba274c8461b5c5e27535"
      },
      {
        "path": "/data2/k6tk/80/80fbab15fd8d4b2e7ea665cb63a3bb4d87bbda76437c1a571a108ea55fb22935.png",
        "sha256": "80fbab15fd8d4b2e7ea665cb63a3bb4d87bbda76437c1a571a108ea55fb22935"
      },
      {
        "path": "/data2/k6tk/09/09c12d157c24060d9cc28aa434f16aed5f688226ccdb9fc2b8163d03c58b3f86.png",
        "sha256": "09c12d157c24060d9cc28aa434f16aed5f688226ccdb9fc2b8163d03c58b3f86"
      },
      {
        "path": "/data2/k6tk/3d/3deb1720049cf98a4865fbd584329fc5db5d424630f741eca83b1050fe135b0f.png",
        "sha256": "3deb1720049cf98a4865fbd584329fc5db5d424630f741eca83b1050fe135b0f"
      },
      {
        "path": "/data2/k6tk/d8/d8fc88265bc1140032cce20d192d55ca7bc001b0e8a3db2bfeef6703e70decc3.png",
        "sha256": "d8fc88265bc1140032cce20d192d55ca7bc001b0e8a3db2bfeef6703e70decc3"
      },
      {
        "path": "/data2/k6tk/e6/e6921872f4a61728256ce1bdaaf68d6da2e4412425756b1f59bd6055359e876a.png",
        "sha256": "e6921872f4a61728256ce1bdaaf68d6da2e4412425756b1f59bd6055359e876a"
      },
      {
        "path": "/data2/k6tk/4a/4a60111062953e63fc914df0dfa2822def154f9c20451d7d2b39cbe8f50a952e.png",
        "sha256": "4a60111062953e63fc914df0dfa2822def154f9c20451d7d2b39cbe8f50a952e"
      },
      {
        "path": "/data2/k6tk/ef/ef68d1a3addd763eb77a43093bfa1084ea78d3548a055a25b853691639f14c36.png",
        "sha256": "ef68d1a3addd763eb77a43093bfa1084ea78d3548a055a25b853691639f14c36"
      },
      {
        "path": "/data2/k6tk/f2/f25ab762a3668e5a85ec354d0061c818863e3f32fc679a2c765fdc00f3828f62.png",
        "sha256": "f25ab762a3668e5a85ec354d0061c818863e3f32fc679a2c765fdc00f3828f62"
      },
      {
        "path": "/data2/k6tk/56/56771b9690e8e9dcb1d4b7cf039ecf462b4a08a76762ad760032f45b2960de4e.png",
        "sha256": "56771b9690e8e9dcb1d4b7cf039ecf462b4a08a76762ad760032f45b2960de4e"
      },
      {
        "path": "/data2/k6tk/93/93e95a5aff8653a8988519b892b2fe03ad18d969052f3870cd6a4acb7dd47b1d.png",
        "sha256": "93e95a5aff8653a8988519b892b2fe03ad18d969052f3870cd6a4acb7dd47b1d"
      },
      {
        "path": "/data2/k6tk/c8/c8c54e028f4ed4de831ca41825ca1785f58bb9d051ccb51a23fa14712e85cf9a.png",
        "sha256": "c8c54e028f4ed4de831ca41825ca1785f58bb9d051ccb51a23fa14712e85cf9a"
      },
      {
        "path": "/data2/k6tk/a9/a983e42c7155e43cc3d76e0968d218ec0fc0155e3bfea9f3a059b8933721beb4.png",
        "sha256": "a983e42c7155e43cc3d76e0968d218ec0fc0155e3bfea9f3a059b8933721beb4"
      },
      {
        "path": "/data2/k6tk/48/48f39647a1213f2be6f460f6389f38ea77dbcbf2b9ae95bd48ef3948b41bbc34.png",
        "sha256": "48f39647a1213f2be6f460f6389f38ea77dbcbf2b9ae95bd48ef3948b41bbc34"
      },
      {
        "path": "/data2/k6tk/e7/e7ec12ca39f910ac61058236d8ce697a70f44d5a9422e5d3053e48418104fe88.png",
        "sha256": "e7ec12ca39f910ac61058236d8ce697a70f44d5a9422e5d3053e48418104fe88"
      },
      {
        "path": "/data2/k6tk/42/42d0e1716d6d14ab1940153a5cffccf075f641b455c2e3a272101c54444a7c90.png",
        "sha256": "42d0e1716d6d14ab1940153a5cffccf075f641b455c2e3a272101c54444a7c90"
      },
      {
        "path": "/data2/k6tk/65/6556173c6336e2f9081ce8e10d5e4523084cc1cf1dad4bc69b47e26f94aa2cb4.png",
        "sha256": "6556173c6336e2f9081ce8e10d5e4523084cc1cf1dad4bc69b47e26f94aa2cb4"
      },
      {
        "path": "/data2/k6tk/ac/ac8b260608fdeb7438413ea83acad31f3b8ac10d7577bc4399a5e17a500e915e.png",
        "sha256": "ac8b260608fdeb7438413ea83acad31f3b8ac10d7577bc4399a5e17a500e915e"
      },
      {
        "path": "/data2/k6tk/29/2981d8e2b7f9fe70e77809556b065523124b8000604394cf69286331905b59d2.png",
        "sha256": "2981d8e2b7f9fe70e77809556b065523124b8000604394cf69286331905b59d2"
      },
      {
        "path": "/data2/k6tk/e8/e80624a0b381a234b664ea5ac24c623867eea38f6168fb9daed671f3942f8549.png",
        "sha256": "e80624a0b381a234b664ea5ac24c623867eea38f6168fb9daed671f3942f8549"
      },
      {
        "path": "/data2/k6tk/ba/badfaf686f2971055cb649d22fc251d25913bb1c753bda8c2671578453215dad.png",
        "sha256": "badfaf686f2971055cb649d22fc251d25913bb1c753bda8c2671578453215dad"
      },
      {
        "path": "/data2/k6tk/9c/9c9ad504089f61ddb2c97f6866cf425f1675d04189fd3eaac7b94f12674b8d8a.png",
        "sha256": "9c9ad504089f61ddb2c97f6866cf425f1675d04189fd3eaac7b94f12674b8d8a"
      },
      {
        "path": "/data2/k6tk/56/5624e90d0683bf264fa6bc8111668c40493578fc208455a432fbf55a72f318c3.png",
        "sha256": "5624e90d0683bf264fa6bc8111668c40493578fc208455a432fbf55a72f318c3"
      },
      {
        "path": "/data2/k6tk/ef/ef8cd433906777c9d98a3bca3b75cd24be9df9e8dedf127e8ea06bd422e0fd29.png",
        "sha256": "ef8cd433906777c9d98a3bca3b75cd24be9df9e8dedf127e8ea06bd422e0fd29"
      },
      {
        "path": "/data2/k6tk/77/77ca9cf41e856fa66fbe03c3304c52173f4059e77cd3354a2486ab688889cdd0.png",
        "sha256": "77ca9cf41e856fa66fbe03c3304c52173f4059e77cd3354a2486ab688889cdd0"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-right",
      "C. back-left",
      "D. front-right"
    ],
    "question": "From beside the bed, I face away from the wardrobe closet. Which direction describes the nightstand relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.5833333333333335,
      5.208333333333333,
      7.791666666666667,
      10.416666666666666,
      13.041666666666666,
      15.625,
      18.25,
      20.833333333333332,
      23.458333333333332,
      26.083333333333332,
      28.666666666666668,
      31.291666666666668,
      33.875,
      36.5,
      39.125,
      41.708333333333336,
      44.333333333333336,
      46.958333333333336,
      49.541666666666664,
      52.166666666666664,
      54.75,
      57.375,
      60.0,
      62.583333333333336,
      65.20833333333333,
      67.79166666666667,
      70.41666666666667,
      73.04166666666667,
      75.625,
      78.25,
      80.875
    ],
    "total_num_frames": 1942
  },
  "target": "<think>\nStep 1: find the bed, the wardrobe closet and the nightstand.\nStep 2: facing the wardrobe closet from the bed, I find the nightstand behind me, on my left.\nStep 3: I face away from the wardrobe closet by making a half turn. Front and back swap, and left and right swap.\nSo I find the nightstand at my front-right.\n</think>\n\nD",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

## 30. q3dc2dfb15d29f48bc8010f06-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-00c9beccf99f2f167cf3187b019ad45a1b8e7dadc86f011a68a4ee130d4b3312",
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
  "label_row_keys": [
    "q3dc2dfb15d29f48bc8010f06-p1"
  ],
  "license": [
    "ScanNet++ Terms of Use",
    "VSI-590K question text"
  ],
  "paraphrase_of": "q3dc2dfb15d29f48bc8010f06",
  "paraphrase_template": "hard_vsi",
  "pool": "sb_rowD7f",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "sb_rowD7": {
      "branch": "a",
      "clause_edit": {
        "end": 49,
        "new_clause": "facing away from",
        "rule": "single_clause_substitution",
        "source_clause": "facing",
        "start": 43
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "mapped_label": "front-right",
      "room_resolution": {
        "alias_map": {
          "bytes": 5017721,
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        },
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged"
      },
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "source_answer": "B",
      "source_label": "back-left",
      "source_qid": "q3dc2dfb15d29f48bc8010f06-p1",
      "source_row_sha256": "8c2abc90b8fb48145393e2b0ec82596d3d7430106f25479688341f9c4c2ce603",
      "source_store_i": 59089
    },
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q3dc2dfb15d29f48bc8010f06-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "bfb8e4715b90ebb906efa127ec1510c4423a0dc0943a31794b4408c47e6331f8"
  },
  "scene": "vd1f32aca68ad",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      388,
      777,
      1165,
      1554,
      1942,
      2331,
      2719,
      3108,
      3496,
      3885,
      4274,
      4662,
      5051,
      5439,
      5828,
      6216,
      6605,
      6993,
      7382,
      7770,
      8159,
      8548,
      8936,
      9325,
      9713,
      10102,
      10490,
      10879,
      11267,
      11656,
      12045
    ],
    "frames": [
      {
        "path": "/data2/k6tk/94/947fd4761352702542f28f734946b7a41e497910bb26b78226e2b33c3c188e08.png",
        "sha256": "947fd4761352702542f28f734946b7a41e497910bb26b78226e2b33c3c188e08"
      },
      {
        "path": "/data2/k6tk/52/52805da204d710b081d123bf0548b6a12927442767717f5f21101dd449cc9ad5.png",
        "sha256": "52805da204d710b081d123bf0548b6a12927442767717f5f21101dd449cc9ad5"
      },
      {
        "path": "/data2/k6tk/4c/4c530ee0b75fa9bb87fcbdf2adeaada5cebab0894c68f853f52a14cf4a420f5f.png",
        "sha256": "4c530ee0b75fa9bb87fcbdf2adeaada5cebab0894c68f853f52a14cf4a420f5f"
      },
      {
        "path": "/data2/k6tk/2a/2a30ea008af8b46679157821930ba578860ab9694fc1326c69bfc0719b73e0fd.png",
        "sha256": "2a30ea008af8b46679157821930ba578860ab9694fc1326c69bfc0719b73e0fd"
      },
      {
        "path": "/data2/k6tk/7a/7a750d39eb288286893f5d9c86d0a464c90c2e36c52b5983aac9467cf639d144.png",
        "sha256": "7a750d39eb288286893f5d9c86d0a464c90c2e36c52b5983aac9467cf639d144"
      },
      {
        "path": "/data2/k6tk/08/08456b4f46a9ad6c6fb500b0f2ebb499676cc4fa1410abb57ae6aa8ffb4ea6c9.png",
        "sha256": "08456b4f46a9ad6c6fb500b0f2ebb499676cc4fa1410abb57ae6aa8ffb4ea6c9"
      },
      {
        "path": "/data2/k6tk/62/62d231e1d571703f82b6e321af5c708f9897e3f5c9fe455d165a86896f8baaa4.png",
        "sha256": "62d231e1d571703f82b6e321af5c708f9897e3f5c9fe455d165a86896f8baaa4"
      },
      {
        "path": "/data2/k6tk/32/32ee37c889aa55dd81c9e2fe8209fba32f604cfea9256dec9d0682380ef4c250.png",
        "sha256": "32ee37c889aa55dd81c9e2fe8209fba32f604cfea9256dec9d0682380ef4c250"
      },
      {
        "path": "/data2/k6tk/36/3689c03bcfa5c53f80eb4ab340eff7c42d6d6a1baa77ae372ef4fff6fce4ffde.png",
        "sha256": "3689c03bcfa5c53f80eb4ab340eff7c42d6d6a1baa77ae372ef4fff6fce4ffde"
      },
      {
        "path": "/data2/k6tk/91/91147a468c69ca305083a0c8246acc2140cfb1495c1cf4cef095ad1d65489fdb.png",
        "sha256": "91147a468c69ca305083a0c8246acc2140cfb1495c1cf4cef095ad1d65489fdb"
      },
      {
        "path": "/data2/k6tk/49/49c57bd07347aac72bdc24f2f49b39375a55694c2f07e327f1e6bb497d3a9c8d.png",
        "sha256": "49c57bd07347aac72bdc24f2f49b39375a55694c2f07e327f1e6bb497d3a9c8d"
      },
      {
        "path": "/data2/k6tk/8f/8f441b0b0d17f254128dc8bc7b19e8e8ab75e3295d34922e7965b63986cb639e.png",
        "sha256": "8f441b0b0d17f254128dc8bc7b19e8e8ab75e3295d34922e7965b63986cb639e"
      },
      {
        "path": "/data2/k6tk/26/26f5ac901cb04f25153e20da85b681dc28aa00ffbab8b1a0a16bc7b48cae9170.png",
        "sha256": "26f5ac901cb04f25153e20da85b681dc28aa00ffbab8b1a0a16bc7b48cae9170"
      },
      {
        "path": "/data2/k6tk/d3/d34d39d41e55055db4e44784ae246b908fcf31ea58aeecd2a7da3b3c7153245d.png",
        "sha256": "d34d39d41e55055db4e44784ae246b908fcf31ea58aeecd2a7da3b3c7153245d"
      },
      {
        "path": "/data2/k6tk/b8/b8f112ef239cb9a9f89e7dc2ccf3ecea3669cf57554ff6ad093c27758e8c75ce.png",
        "sha256": "b8f112ef239cb9a9f89e7dc2ccf3ecea3669cf57554ff6ad093c27758e8c75ce"
      },
      {
        "path": "/data2/k6tk/e7/e768303bed6294718479bd1319cd00728a7237963488bf80236152fb1aea396b.png",
        "sha256": "e768303bed6294718479bd1319cd00728a7237963488bf80236152fb1aea396b"
      },
      {
        "path": "/data2/k6tk/9a/9aa80b001313464604c669df35659baa79af1713a7c0ca9f350003292a27ed17.png",
        "sha256": "9aa80b001313464604c669df35659baa79af1713a7c0ca9f350003292a27ed17"
      },
      {
        "path": "/data2/k6tk/76/76ae5d32abd91f5df180ff9ff3c09abe5806602b1586be49cfe5c04bb4f7a3d2.png",
        "sha256": "76ae5d32abd91f5df180ff9ff3c09abe5806602b1586be49cfe5c04bb4f7a3d2"
      },
      {
        "path": "/data2/k6tk/c3/c36397c6366059838521534b166dc1b32045335becca9011fc700f51d489dd8a.png",
        "sha256": "c36397c6366059838521534b166dc1b32045335becca9011fc700f51d489dd8a"
      },
      {
        "path": "/data2/k6tk/9e/9e2ca382adb24cdd0132409ab56a9a0b5c7c2efaa4b9ba09cf13c2911ce5b0ea.png",
        "sha256": "9e2ca382adb24cdd0132409ab56a9a0b5c7c2efaa4b9ba09cf13c2911ce5b0ea"
      },
      {
        "path": "/data2/k6tk/95/952fc43d73dfd061ec215a3f591312ad2fcc73ac82aed053d727b2b46e35a85d.png",
        "sha256": "952fc43d73dfd061ec215a3f591312ad2fcc73ac82aed053d727b2b46e35a85d"
      },
      {
        "path": "/data2/k6tk/30/30a841229fe79e3d1933b40cb4363f0f3b8ac4ee90825bf991d0b96126d10646.png",
        "sha256": "30a841229fe79e3d1933b40cb4363f0f3b8ac4ee90825bf991d0b96126d10646"
      },
      {
        "path": "/data2/k6tk/1d/1d92a6bd6296b91a64cd758fe05b63aebb86a375eb838dfbca3f2ac63339d0fe.png",
        "sha256": "1d92a6bd6296b91a64cd758fe05b63aebb86a375eb838dfbca3f2ac63339d0fe"
      },
      {
        "path": "/data2/k6tk/4a/4aeb5123471016e576777bcb5f91389605f7d2b655b1f3e47e1fdfef76250c72.png",
        "sha256": "4aeb5123471016e576777bcb5f91389605f7d2b655b1f3e47e1fdfef76250c72"
      },
      {
        "path": "/data2/k6tk/44/44d06e7c5d9ad48902c9652db29398c70c4b8cde6f6301931be97d9e8124f4db.png",
        "sha256": "44d06e7c5d9ad48902c9652db29398c70c4b8cde6f6301931be97d9e8124f4db"
      },
      {
        "path": "/data2/k6tk/ac/ac9c909189d7b76dc866680e0f24ea20a93a57f898ed04c48c2989458c486f25.png",
        "sha256": "ac9c909189d7b76dc866680e0f24ea20a93a57f898ed04c48c2989458c486f25"
      },
      {
        "path": "/data2/k6tk/d5/d5099b5505f894ad6114a5d2aeddb5829c642ff5b0e41979b3c2ad66a9219b99.png",
        "sha256": "d5099b5505f894ad6114a5d2aeddb5829c642ff5b0e41979b3c2ad66a9219b99"
      },
      {
        "path": "/data2/k6tk/eb/ebd713615a7eaa11da2139c5a76b03588da60153177100388660099f821069dc.png",
        "sha256": "ebd713615a7eaa11da2139c5a76b03588da60153177100388660099f821069dc"
      },
      {
        "path": "/data2/k6tk/8a/8a6cf10089c24cb2a27b4ac78491d01ac6691c9e294657790911e3c2e9407248.png",
        "sha256": "8a6cf10089c24cb2a27b4ac78491d01ac6691c9e294657790911e3c2e9407248"
      },
      {
        "path": "/data2/k6tk/40/4034e5e1e044777517837ed9d880b9499dc2a90a2ee5bea78ad2b251fd23fb48.png",
        "sha256": "4034e5e1e044777517837ed9d880b9499dc2a90a2ee5bea78ad2b251fd23fb48"
      },
      {
        "path": "/data2/k6tk/89/898ec617f60d7310df229dfe89d5bcf42523d268bb1ae456eacd08c3f2bdebfe.png",
        "sha256": "898ec617f60d7310df229dfe89d5bcf42523d268bb1ae456eacd08c3f2bdebfe"
      },
      {
        "path": "/data2/k6tk/48/482b3460f28e1bb4d9466b1c4ec7e94c2cb79054de4e100952670b623c2d8755.png",
        "sha256": "482b3460f28e1bb4d9466b1c4ec7e94c2cb79054de4e100952670b623c2d8755"
      }
    ],
    "options": [
      "A. front-right",
      "B. back-left",
      "C. back-right",
      "D. front-left"
    ],
    "question": "If I am standing beside the sign board and facing away from the soap dispenser, which direction describes the toilet relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.466666666666667,
      12.95,
      19.416666666666668,
      25.9,
      32.36666666666667,
      38.85,
      45.31666666666667,
      51.8,
      58.266666666666666,
      64.75,
      71.23333333333333,
      77.7,
      84.18333333333334,
      90.65,
      97.13333333333334,
      103.6,
      110.08333333333333,
      116.55,
      123.03333333333333,
      129.5,
      135.98333333333332,
      142.46666666666667,
      148.93333333333334,
      155.41666666666666,
      161.88333333333333,
      168.36666666666667,
      174.83333333333334,
      181.31666666666666,
      187.78333333333333,
      194.26666666666668,
      200.75
    ],
    "total_num_frames": 12046
  },
  "target": "<think>\nStep 1: locate the toilet, the sign board and the soap dispenser.\nStep 2: I stand at the sign board facing the soap dispenser; I find the toilet behind me, on my left.\nStep 3: I face away from the soap dispenser by making a half turn. Front and back swap, and left and right swap.\nSo I find the toilet at my front-right.\n</think>\n\nA",
  "trace_quotes_question": false,
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24"
}
```

