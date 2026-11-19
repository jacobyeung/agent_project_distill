Complete generated rows for grammar, heading, frame preservation and answer review.

## 1. qdf908eac48b4f1ccf84aeb1f_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qdf908eac48b4f1ccf84aeb1f",
      "source_store_i": 8661,
      "source_row_sha256": "814f805bf7a2683a26c85b0ecfd707c811c0ba22cae504e35afef2a681df9ae8",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 39,
        "end": 45,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qdf908eac48b4f1ccf84aeb1f_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "va531fc847cf3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      238,
      476,
      715,
      953,
      1192,
      1430,
      1669,
      1907,
      2146,
      2384,
      2622,
      2861,
      3099,
      3338,
      3576,
      3815,
      4053,
      4292,
      4530,
      4769,
      5007,
      5245,
      5484,
      5722,
      5961,
      6199,
      6438,
      6676,
      6915,
      7153,
      7392
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9c/9cfb558712574ebd7ec82aff05886eff09737a68447856d95059a6951c5a58ce.png",
        "sha256": "9cfb558712574ebd7ec82aff05886eff09737a68447856d95059a6951c5a58ce"
      },
      {
        "path": "/data2/k6tk/dd/ddff7d117b7a31156c288a933c4d6ac4ccc1b0e0851e69d36c8ad04489b93325.png",
        "sha256": "ddff7d117b7a31156c288a933c4d6ac4ccc1b0e0851e69d36c8ad04489b93325"
      },
      {
        "path": "/data2/k6tk/15/1561658cee5c168454916c55910a4a5c2f377789ea020837b2cb7d55660aa648.png",
        "sha256": "1561658cee5c168454916c55910a4a5c2f377789ea020837b2cb7d55660aa648"
      },
      {
        "path": "/data2/k6tk/eb/eb097e032ed6c70d64405454ee2ecef2c3d8c7c64af3dcd4686b67fdc99c4cc2.png",
        "sha256": "eb097e032ed6c70d64405454ee2ecef2c3d8c7c64af3dcd4686b67fdc99c4cc2"
      },
      {
        "path": "/data2/k6tk/67/6714ce4037cb1978183067e69deb7858700138599edda442c51f8ed6e079240c.png",
        "sha256": "6714ce4037cb1978183067e69deb7858700138599edda442c51f8ed6e079240c"
      },
      {
        "path": "/data2/k6tk/ba/ba07b295c1652c61c7cf99b10f9b3c4376b2a51e3a0d3d34da779380b3d63d3f.png",
        "sha256": "ba07b295c1652c61c7cf99b10f9b3c4376b2a51e3a0d3d34da779380b3d63d3f"
      },
      {
        "path": "/data2/k6tk/50/50e4661d5b1958ac3017d96258567e4cfd4efa4da37e8b2545283d263a077915.png",
        "sha256": "50e4661d5b1958ac3017d96258567e4cfd4efa4da37e8b2545283d263a077915"
      },
      {
        "path": "/data2/k6tk/b2/b208f6b98f0160f46c8691e7bc0a600f9e0163a18cbbd937d9388f044b2d694f.png",
        "sha256": "b208f6b98f0160f46c8691e7bc0a600f9e0163a18cbbd937d9388f044b2d694f"
      },
      {
        "path": "/data2/k6tk/0f/0f984d27ae8478737d7852f0a045f63c9f818c37ebb04fe0508af70a7d29167d.png",
        "sha256": "0f984d27ae8478737d7852f0a045f63c9f818c37ebb04fe0508af70a7d29167d"
      },
      {
        "path": "/data2/k6tk/39/392e78c9f22962fbee64ba92657f6cc3272f43698e6836bc7202179ad085c5c3.png",
        "sha256": "392e78c9f22962fbee64ba92657f6cc3272f43698e6836bc7202179ad085c5c3"
      },
      {
        "path": "/data2/k6tk/1d/1d6f9d66ca514c7234d0df558fac97df9af57a64670f6daa8c61344a64d7aac3.png",
        "sha256": "1d6f9d66ca514c7234d0df558fac97df9af57a64670f6daa8c61344a64d7aac3"
      },
      {
        "path": "/data2/k6tk/0c/0c479be321c77dc1e0e4a07324949051c749b0c4b0e4c733f3adf344cde0a1c7.png",
        "sha256": "0c479be321c77dc1e0e4a07324949051c749b0c4b0e4c733f3adf344cde0a1c7"
      },
      {
        "path": "/data2/k6tk/78/7838370fcbcd64c4f62c9fccadf4f7565c33e22f08a0dad5df5a5d929ff6966b.png",
        "sha256": "7838370fcbcd64c4f62c9fccadf4f7565c33e22f08a0dad5df5a5d929ff6966b"
      },
      {
        "path": "/data2/k6tk/8f/8f0cd10eb46a8ad16b03da40f718e1d4e1d6ad8f55fd438034b718a029f208ef.png",
        "sha256": "8f0cd10eb46a8ad16b03da40f718e1d4e1d6ad8f55fd438034b718a029f208ef"
      },
      {
        "path": "/data2/k6tk/97/977677a6b98aa39eb6c95fd547e091fbf4fb96d06777b4e8a095f090789ddb44.png",
        "sha256": "977677a6b98aa39eb6c95fd547e091fbf4fb96d06777b4e8a095f090789ddb44"
      },
      {
        "path": "/data2/k6tk/5e/5ee156008664d73c1b5f0dcd48e2dbae97962d4a99603155c02b17305fb8809e.png",
        "sha256": "5ee156008664d73c1b5f0dcd48e2dbae97962d4a99603155c02b17305fb8809e"
      },
      {
        "path": "/data2/k6tk/88/88f002a623fc97c784a4b908b37b83952edce6c908d9ecb19b569383e8129ee5.png",
        "sha256": "88f002a623fc97c784a4b908b37b83952edce6c908d9ecb19b569383e8129ee5"
      },
      {
        "path": "/data2/k6tk/ae/ae8bd534671f758e4e9aaecce473b2d53a79dc0d4301a33c8a13d03e6e010bec.png",
        "sha256": "ae8bd534671f758e4e9aaecce473b2d53a79dc0d4301a33c8a13d03e6e010bec"
      },
      {
        "path": "/data2/k6tk/ee/ee0b9145527c076f633cb9297373e2b9c4952ac0f53916d91ecb2ecd240c7b47.png",
        "sha256": "ee0b9145527c076f633cb9297373e2b9c4952ac0f53916d91ecb2ecd240c7b47"
      },
      {
        "path": "/data2/k6tk/aa/aad250fe511c6939afcc684aa58d3ee3349eafe3b6a78a11992ee10e066f2fdf.png",
        "sha256": "aad250fe511c6939afcc684aa58d3ee3349eafe3b6a78a11992ee10e066f2fdf"
      },
      {
        "path": "/data2/k6tk/85/859b55b9707e303be613b2e021af8100fb02e308d6abad119d9d4909ed6a79b6.png",
        "sha256": "859b55b9707e303be613b2e021af8100fb02e308d6abad119d9d4909ed6a79b6"
      },
      {
        "path": "/data2/k6tk/2c/2c59cee8db0b562548e011477a6313c288fc5bed31e667aa03342154d0b27515.png",
        "sha256": "2c59cee8db0b562548e011477a6313c288fc5bed31e667aa03342154d0b27515"
      },
      {
        "path": "/data2/k6tk/42/428233384e475a4f6dbeadbffe918fecb6c479fa5c79791113065c682f98dfd0.png",
        "sha256": "428233384e475a4f6dbeadbffe918fecb6c479fa5c79791113065c682f98dfd0"
      },
      {
        "path": "/data2/k6tk/07/07e5afb247586f20845281ccbeefb8a930853b2fb4adf662fb4522996d0b7ad5.png",
        "sha256": "07e5afb247586f20845281ccbeefb8a930853b2fb4adf662fb4522996d0b7ad5"
      },
      {
        "path": "/data2/k6tk/78/78db5c3bbdb1447d75417c86dcd19ebbcb8e5e4f886c663c404faaf49f16e342.png",
        "sha256": "78db5c3bbdb1447d75417c86dcd19ebbcb8e5e4f886c663c404faaf49f16e342"
      },
      {
        "path": "/data2/k6tk/ec/ecf8696fb767193323e4d42787ed0b014bb28f2e19b866269afca31d0f650a49.png",
        "sha256": "ecf8696fb767193323e4d42787ed0b014bb28f2e19b866269afca31d0f650a49"
      },
      {
        "path": "/data2/k6tk/27/2710abaa7d07895d49b02104d65d500f44235194f2a63a4c9dac66e5192d99ad.png",
        "sha256": "2710abaa7d07895d49b02104d65d500f44235194f2a63a4c9dac66e5192d99ad"
      },
      {
        "path": "/data2/k6tk/1e/1e8fdfe37f2d7c7dd7a1a71abfe71ae04e05a92bb7d2e283685a450ef6c3329b.png",
        "sha256": "1e8fdfe37f2d7c7dd7a1a71abfe71ae04e05a92bb7d2e283685a450ef6c3329b"
      },
      {
        "path": "/data2/k6tk/4f/4f7138216c4917dc05baf716832c5204de6bf94c8ebbd3529a086891021bc652.png",
        "sha256": "4f7138216c4917dc05baf716832c5204de6bf94c8ebbd3529a086891021bc652"
      },
      {
        "path": "/data2/k6tk/d4/d4f1ae3cfacf501eff408bc9c95d44fcdcf111cbcfa3e018022b82d9d6ae983a.png",
        "sha256": "d4f1ae3cfacf501eff408bc9c95d44fcdcf111cbcfa3e018022b82d9d6ae983a"
      },
      {
        "path": "/data2/k6tk/b2/b26afb80fb49f959a9c5986ce2f5e73c0095df8b717f0685ea0e8f9c8acc2d7f.png",
        "sha256": "b26afb80fb49f959a9c5986ce2f5e73c0095df8b717f0685ea0e8f9c8acc2d7f"
      },
      {
        "path": "/data2/k6tk/a8/a81ba1af7261f4d5c2ae9beafc12defa17b98d777c8980b20b81190f6361c347.png",
        "sha256": "a81ba1af7261f4d5c2ae9beafc12defa17b98d777c8980b20b81190f6361c347"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the cable duct and facing away from the blackboard, is the window sill to the left or the right of the blackboard?",
    "timestamps": [
      0.0,
      3.966666666666667,
      7.933333333333334,
      11.916666666666666,
      15.883333333333333,
      19.866666666666667,
      23.833333333333332,
      27.816666666666666,
      31.783333333333335,
      35.766666666666666,
      39.733333333333334,
      43.7,
      47.68333333333333,
      51.65,
      55.63333333333333,
      59.6,
      63.583333333333336,
      67.55,
      71.53333333333333,
      75.5,
      79.48333333333333,
      83.45,
      87.41666666666667,
      91.4,
      95.36666666666666,
      99.35,
      103.31666666666666,
      107.3,
      111.26666666666667,
      115.25,
      119.21666666666667,
      123.2
    ],
    "total_num_frames": 7393
  },
  "target": "<think>\nStep 1: locate the window sill, the cable duct and the blackboard.\nStep 2: I stand at the cable duct facing the blackboard; I find the window sill to my right.\nStep 3: I face away from the blackboard by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the window sill to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "bd39beb9594b243bcc2ca5b6c1779a3a53f476e5d989c532e2400997adbe82e8"
  },
  "candidate_id": "ground-811d0bc1524810d5cf41e936d4561672935aca7fd259e23338af8778671e14f2",
  "label_row_keys": [
    "qdf908eac48b4f1ccf84aeb1f"
  ]
}
```

## 2. q927653c53e60edc48064d2fc_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q927653c53e60edc48064d2fc",
      "source_store_i": 2009,
      "source_row_sha256": "5a24a3b10499e13f2901525308a75d78124ecb46f3f6ba7aaa7dc5ac6c019f58",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 33,
        "end": 39,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q927653c53e60edc48064d2fc_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v7b63c7b046dd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      148,
      296,
      445,
      593,
      741,
      890,
      1038,
      1187,
      1335,
      1483,
      1632,
      1780,
      1929,
      2077,
      2225,
      2374,
      2522,
      2670,
      2819,
      2967,
      3116,
      3264,
      3412,
      3561,
      3709,
      3858,
      4006,
      4154,
      4303,
      4451,
      4600
    ],
    "frames": [
      {
        "path": "/data2/k6tk/d9/d919c38791f4d43d07661f96cc23b2d8e29abc0679a4acc22d293170f0afb0e7.png",
        "sha256": "d919c38791f4d43d07661f96cc23b2d8e29abc0679a4acc22d293170f0afb0e7"
      },
      {
        "path": "/data2/k6tk/c6/c608a4c6cfd504d130b9538ebdeb09cb147af9f8cd33d4b0a9000a44cfcb0370.png",
        "sha256": "c608a4c6cfd504d130b9538ebdeb09cb147af9f8cd33d4b0a9000a44cfcb0370"
      },
      {
        "path": "/data2/k6tk/3b/3bb4fa518e06b9bf9520a97328d16b10b16ed04e6b648b54a10e0f6a6d8bd962.png",
        "sha256": "3bb4fa518e06b9bf9520a97328d16b10b16ed04e6b648b54a10e0f6a6d8bd962"
      },
      {
        "path": "/data2/k6tk/00/003490c463d568cdf25ea7ea7ec92f4103022bdb19b6cc2ee6e40a54f1e08c82.png",
        "sha256": "003490c463d568cdf25ea7ea7ec92f4103022bdb19b6cc2ee6e40a54f1e08c82"
      },
      {
        "path": "/data2/k6tk/06/065c3942fe0a6226b7f98589da50043b89e0ca599aed491a91182b3e654dcf12.png",
        "sha256": "065c3942fe0a6226b7f98589da50043b89e0ca599aed491a91182b3e654dcf12"
      },
      {
        "path": "/data2/k6tk/db/db4459fbbfa44fbbed6f1bccc630ff1bc0a84af1c4487fb9fa200817a7dbc7ef.png",
        "sha256": "db4459fbbfa44fbbed6f1bccc630ff1bc0a84af1c4487fb9fa200817a7dbc7ef"
      },
      {
        "path": "/data2/k6tk/75/758a4fc8a7b8238c9aa7e348ee7d5d79f63fcdcef64109b23ef22f99dba7a078.png",
        "sha256": "758a4fc8a7b8238c9aa7e348ee7d5d79f63fcdcef64109b23ef22f99dba7a078"
      },
      {
        "path": "/data2/k6tk/14/14a9406e6f4fe410427c7a730694aeb956aab40c14cdf99f9010bdeb556c335a.png",
        "sha256": "14a9406e6f4fe410427c7a730694aeb956aab40c14cdf99f9010bdeb556c335a"
      },
      {
        "path": "/data2/k6tk/69/69bd7ab8d5af333bc65b7db16c0cfd1dd9e361b682122763e6f91721f31cb85f.png",
        "sha256": "69bd7ab8d5af333bc65b7db16c0cfd1dd9e361b682122763e6f91721f31cb85f"
      },
      {
        "path": "/data2/k6tk/eb/ebed3115ee506a19a13d3e8c2057dcc7112289862227d6b6aafb2ae124b97217.png",
        "sha256": "ebed3115ee506a19a13d3e8c2057dcc7112289862227d6b6aafb2ae124b97217"
      },
      {
        "path": "/data2/k6tk/00/001086234c45530a39182d116585f12c9329e7d481a42cfd70b68ce93d7b8e8b.png",
        "sha256": "001086234c45530a39182d116585f12c9329e7d481a42cfd70b68ce93d7b8e8b"
      },
      {
        "path": "/data2/k6tk/d0/d058ffc4262187c49d9fba457124185d0b5a0d7f02921d73affc76580aff84af.png",
        "sha256": "d058ffc4262187c49d9fba457124185d0b5a0d7f02921d73affc76580aff84af"
      },
      {
        "path": "/data2/k6tk/a2/a279926b5b78b4bbd8402ecdd32003f9faf3ea45cdb69565de56ca94c383cdf2.png",
        "sha256": "a279926b5b78b4bbd8402ecdd32003f9faf3ea45cdb69565de56ca94c383cdf2"
      },
      {
        "path": "/data2/k6tk/3a/3abb3ff6d6590f6f10d7a58c07880e99139d7a494c6dceffd7f81b09b9b4130a.png",
        "sha256": "3abb3ff6d6590f6f10d7a58c07880e99139d7a494c6dceffd7f81b09b9b4130a"
      },
      {
        "path": "/data2/k6tk/5e/5ebd9baf10fc5f80f9aff1c4e9fd2695b12731aae34d3afb94e7ab33c0082001.png",
        "sha256": "5ebd9baf10fc5f80f9aff1c4e9fd2695b12731aae34d3afb94e7ab33c0082001"
      },
      {
        "path": "/data2/k6tk/c5/c585af374429b9f84a0e6697f976d483765302791d8be44f3cf5c5d05da6e4f2.png",
        "sha256": "c585af374429b9f84a0e6697f976d483765302791d8be44f3cf5c5d05da6e4f2"
      },
      {
        "path": "/data2/k6tk/2a/2a56be0603c3a951fa42aa87153820175b630802013e23c9c43e9979b0f5d700.png",
        "sha256": "2a56be0603c3a951fa42aa87153820175b630802013e23c9c43e9979b0f5d700"
      },
      {
        "path": "/data2/k6tk/1e/1e247712450adc95f2afb4fb858efdd343bb3b67c2bcbe4277a299d979047e01.png",
        "sha256": "1e247712450adc95f2afb4fb858efdd343bb3b67c2bcbe4277a299d979047e01"
      },
      {
        "path": "/data2/k6tk/f3/f393373f47397fb0adb7bdbd5ea4f8ad9fdbfbaed277014caaa836f61db2cce8.png",
        "sha256": "f393373f47397fb0adb7bdbd5ea4f8ad9fdbfbaed277014caaa836f61db2cce8"
      },
      {
        "path": "/data2/k6tk/74/74789ad5ac5eee2f31c6680585d82ca7c0978cc5b6aa85477b39e1b74b404334.png",
        "sha256": "74789ad5ac5eee2f31c6680585d82ca7c0978cc5b6aa85477b39e1b74b404334"
      },
      {
        "path": "/data2/k6tk/0f/0fcafc58e20ace68a1b81fe1fba8d96ddae2ad1a535e7becdf9912b5fa4ae368.png",
        "sha256": "0fcafc58e20ace68a1b81fe1fba8d96ddae2ad1a535e7becdf9912b5fa4ae368"
      },
      {
        "path": "/data2/k6tk/01/013a7d7a53acb28a431c0bc0b86f93e387b6152651337c51b994e2bd6db144ba.png",
        "sha256": "013a7d7a53acb28a431c0bc0b86f93e387b6152651337c51b994e2bd6db144ba"
      },
      {
        "path": "/data2/k6tk/dc/dcb164c8de90bf002c1cecc34ffd1b09859c4e13f4f4c5ca09e5e9101d80abbf.png",
        "sha256": "dcb164c8de90bf002c1cecc34ffd1b09859c4e13f4f4c5ca09e5e9101d80abbf"
      },
      {
        "path": "/data2/k6tk/94/94d3dd168737bff2240d450243746f421ffb634e8d2d466eef85352ceffb8ef7.png",
        "sha256": "94d3dd168737bff2240d450243746f421ffb634e8d2d466eef85352ceffb8ef7"
      },
      {
        "path": "/data2/k6tk/ee/eeecc336afea8058d2888b59a5dbd52a8314ff060c01cf66d70bebaf37d4ddfd.png",
        "sha256": "eeecc336afea8058d2888b59a5dbd52a8314ff060c01cf66d70bebaf37d4ddfd"
      },
      {
        "path": "/data2/k6tk/6d/6df137cd012a90b2b0c34f8eee4cd548d390dd733b1d224aeab0b700e87c2c1c.png",
        "sha256": "6df137cd012a90b2b0c34f8eee4cd548d390dd733b1d224aeab0b700e87c2c1c"
      },
      {
        "path": "/data2/k6tk/4b/4be7e7bef291a90fa2b67cc25a5f5e36123d6272aeb289665a879d5c6a024f8f.png",
        "sha256": "4be7e7bef291a90fa2b67cc25a5f5e36123d6272aeb289665a879d5c6a024f8f"
      },
      {
        "path": "/data2/k6tk/31/318e1522d6c1d16282fd393bc94b80ae0b396b655646dc7613c463ac246fd4e7.png",
        "sha256": "318e1522d6c1d16282fd393bc94b80ae0b396b655646dc7613c463ac246fd4e7"
      },
      {
        "path": "/data2/k6tk/99/99b7b2082d3e9522d65d8dea6e7e530e8bb293229555452072f2422b4b45e6fc.png",
        "sha256": "99b7b2082d3e9522d65d8dea6e7e530e8bb293229555452072f2422b4b45e6fc"
      },
      {
        "path": "/data2/k6tk/27/2710e57e4969455e062c3ec6d6f91b93e1ae0cf9732afafe36b20c4b814120bc.png",
        "sha256": "2710e57e4969455e062c3ec6d6f91b93e1ae0cf9732afafe36b20c4b814120bc"
      },
      {
        "path": "/data2/k6tk/96/96e0c6636e1b7c99fe0b60c6d88e017c9c45479db2c593796f2b3934f2d8f654.png",
        "sha256": "96e0c6636e1b7c99fe0b60c6d88e017c9c45479db2c593796f2b3934f2d8f654"
      },
      {
        "path": "/data2/k6tk/68/683759d5528e72b278f9e0ff2ecda2676af1fdeb29ae07856efbda26c84d8bfc.png",
        "sha256": "683759d5528e72b278f9e0ff2ecda2676af1fdeb29ae07856efbda26c84d8bfc"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the sink and facing away from the light switch, is the ceiling lamp to the left or the right of the light switch?",
    "timestamps": [
      0.0,
      2.466666666666667,
      4.933333333333334,
      7.416666666666667,
      9.883333333333333,
      12.35,
      14.833333333333334,
      17.3,
      19.783333333333335,
      22.25,
      24.716666666666665,
      27.2,
      29.666666666666668,
      32.15,
      34.61666666666667,
      37.083333333333336,
      39.56666666666667,
      42.03333333333333,
      44.5,
      46.983333333333334,
      49.45,
      51.93333333333333,
      54.4,
      56.86666666666667,
      59.35,
      61.81666666666667,
      64.3,
      66.76666666666667,
      69.23333333333333,
      71.71666666666667,
      74.18333333333334,
      76.66666666666667
    ],
    "total_num_frames": 4601
  },
  "target": "<think>\nStep 1: find the sink, the light switch and the ceiling lamp.\nStep 2: I stand at the sink facing the light switch; I find the ceiling lamp to my right.\nStep 3: I face away from the light switch by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the ceiling lamp to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "80b3e5361966dff07db83b2fb9cfc147b2caa9169372c657658da9b87fce5e92"
  },
  "candidate_id": "ground-a5ef0d1106ee6da381c87c049a87f4b914cb447bfdaca7fe0ac054b88cd1543a",
  "label_row_keys": [
    "q927653c53e60edc48064d2fc"
  ]
}
```

## 3. qf7f1bfaf105b80f4804ff854-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qf7f1bfaf105b80f4804ff854-p1",
      "source_store_i": 73649,
      "source_row_sha256": "00c32cf15d158bba98e8357899e4701c73563b6503ab4abf339445a6685bbadd",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 34,
        "end": 45,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf7f1bfaf105b80f4804ff854-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vea85b4637bdd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      36,
      73,
      109,
      146,
      182,
      219,
      256,
      292,
      329,
      365,
      402,
      438,
      475,
      512,
      548,
      585,
      621,
      658,
      695,
      731,
      768,
      804,
      841,
      877,
      914,
      951,
      987,
      1024,
      1060,
      1097,
      1134
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9c/9c2c9d5b703f4198f9c55ef26a08bcfb835dda035ef51e81f340ed9b4ca3c033.png",
        "sha256": "9c2c9d5b703f4198f9c55ef26a08bcfb835dda035ef51e81f340ed9b4ca3c033"
      },
      {
        "path": "/data2/k6tk/48/4888c88ab7b8c78aa8b8ebb29cc9e4acad06cdc5c61a9d0f5b11ec74b3fd3bcf.png",
        "sha256": "4888c88ab7b8c78aa8b8ebb29cc9e4acad06cdc5c61a9d0f5b11ec74b3fd3bcf"
      },
      {
        "path": "/data2/k6tk/b8/b8f1c845b9864542c474807b047c546cac4d6de4f3bb251e75711a188f777fda.png",
        "sha256": "b8f1c845b9864542c474807b047c546cac4d6de4f3bb251e75711a188f777fda"
      },
      {
        "path": "/data2/k6tk/26/2615299685631e312ffd66c5558149f76cfbc0bb2241fe62404e6473340fbe63.png",
        "sha256": "2615299685631e312ffd66c5558149f76cfbc0bb2241fe62404e6473340fbe63"
      },
      {
        "path": "/data2/k6tk/2c/2c88dd8704854caffb0b626a9cb8a9232303ed082974c90331f08927f8646a7c.png",
        "sha256": "2c88dd8704854caffb0b626a9cb8a9232303ed082974c90331f08927f8646a7c"
      },
      {
        "path": "/data2/k6tk/77/77a9f3457d5102c1bea43c19d03ddbcde254c72fb92319265cdfd9c249b80f73.png",
        "sha256": "77a9f3457d5102c1bea43c19d03ddbcde254c72fb92319265cdfd9c249b80f73"
      },
      {
        "path": "/data2/k6tk/ee/ee21f7459ada27a82cb9160282ebe823a946f6726ef6b5d2a40107af043b8b00.png",
        "sha256": "ee21f7459ada27a82cb9160282ebe823a946f6726ef6b5d2a40107af043b8b00"
      },
      {
        "path": "/data2/k6tk/76/767e04e4b31a5147b9fce4eacaca6e3659a2d43a7f09fb48f866da7d2fdd969c.png",
        "sha256": "767e04e4b31a5147b9fce4eacaca6e3659a2d43a7f09fb48f866da7d2fdd969c"
      },
      {
        "path": "/data2/k6tk/96/9669dbfc11db14bff71685237b11a10d6a94c0287cd60405af9199031cccc9c9.png",
        "sha256": "9669dbfc11db14bff71685237b11a10d6a94c0287cd60405af9199031cccc9c9"
      },
      {
        "path": "/data2/k6tk/6e/6ec2b8a29ec348f332a7fd10046d34ef4a7c0d287d1c914a74bc27c16a9a26ac.png",
        "sha256": "6ec2b8a29ec348f332a7fd10046d34ef4a7c0d287d1c914a74bc27c16a9a26ac"
      },
      {
        "path": "/data2/k6tk/6b/6b7a6bfdafc2d5f7f3e330b4cbc3aaacff0fc8e87010f86f513f640cce567e84.png",
        "sha256": "6b7a6bfdafc2d5f7f3e330b4cbc3aaacff0fc8e87010f86f513f640cce567e84"
      },
      {
        "path": "/data2/k6tk/44/441c519d892032b432e06f96fa469db9d78a9e019a2cfdf4de2b3a8c3fc0e5da.png",
        "sha256": "441c519d892032b432e06f96fa469db9d78a9e019a2cfdf4de2b3a8c3fc0e5da"
      },
      {
        "path": "/data2/k6tk/7b/7b648003a8827523d4c93d4a4e096e8500b7a264fdc7d7794cf37cb003abcd1a.png",
        "sha256": "7b648003a8827523d4c93d4a4e096e8500b7a264fdc7d7794cf37cb003abcd1a"
      },
      {
        "path": "/data2/k6tk/a7/a79a74912466222df513227d8ca6a83e0e66bff0de8826e89504f1f3325fff0b.png",
        "sha256": "a79a74912466222df513227d8ca6a83e0e66bff0de8826e89504f1f3325fff0b"
      },
      {
        "path": "/data2/k6tk/3f/3f02222c25ced6decec49e3e09dd6dd97e63a08e191bdd5a74305db65a7cf08b.png",
        "sha256": "3f02222c25ced6decec49e3e09dd6dd97e63a08e191bdd5a74305db65a7cf08b"
      },
      {
        "path": "/data2/k6tk/59/594c5356c329ffbd9dcbcae7e3327610341f0c8018576f23d021e56c9b749a75.png",
        "sha256": "594c5356c329ffbd9dcbcae7e3327610341f0c8018576f23d021e56c9b749a75"
      },
      {
        "path": "/data2/k6tk/37/37d9ba07a2a7ee9595315bb956a2ec6e338bf55598b37ee571261336ebe14356.png",
        "sha256": "37d9ba07a2a7ee9595315bb956a2ec6e338bf55598b37ee571261336ebe14356"
      },
      {
        "path": "/data2/k6tk/a1/a1724760a9b30d4dedf2f209d55a5eba8181e6c21570a3044aec58ec61c28eaf.png",
        "sha256": "a1724760a9b30d4dedf2f209d55a5eba8181e6c21570a3044aec58ec61c28eaf"
      },
      {
        "path": "/data2/k6tk/bb/bbc1f212a3a7bc72db3592a8cd733063a4ef3d2849eee98905fa0a6f931a9cfe.png",
        "sha256": "bbc1f212a3a7bc72db3592a8cd733063a4ef3d2849eee98905fa0a6f931a9cfe"
      },
      {
        "path": "/data2/k6tk/88/88cd81d50e81f4264576c85e9eab462333fb9864941a6db2a62dbe6ddb894f58.png",
        "sha256": "88cd81d50e81f4264576c85e9eab462333fb9864941a6db2a62dbe6ddb894f58"
      },
      {
        "path": "/data2/k6tk/44/44639e159ef9ef56a572914627ce2196ebb62f63ec356a5d31a516ab07e65173.png",
        "sha256": "44639e159ef9ef56a572914627ce2196ebb62f63ec356a5d31a516ab07e65173"
      },
      {
        "path": "/data2/k6tk/2d/2d714ffad970f5da41d630030c93df714974384ac8da37a3a4775bd91ba9490f.png",
        "sha256": "2d714ffad970f5da41d630030c93df714974384ac8da37a3a4775bd91ba9490f"
      },
      {
        "path": "/data2/k6tk/f1/f102d1d1d19c7b6001df3a07a0c7b5afb03bc957477021e10bfaa1e6af5063a0.png",
        "sha256": "f102d1d1d19c7b6001df3a07a0c7b5afb03bc957477021e10bfaa1e6af5063a0"
      },
      {
        "path": "/data2/k6tk/47/47ecd90e3894c627aafe3cc8234d2bbc2d8b0be43beef22b62ab3de759c7a2d1.png",
        "sha256": "47ecd90e3894c627aafe3cc8234d2bbc2d8b0be43beef22b62ab3de759c7a2d1"
      },
      {
        "path": "/data2/k6tk/01/01dcf3f0c5cfb292eb5ac253e43b1198b7cb6dba7f705834f18b64d6c19d3508.png",
        "sha256": "01dcf3f0c5cfb292eb5ac253e43b1198b7cb6dba7f705834f18b64d6c19d3508"
      },
      {
        "path": "/data2/k6tk/32/3290006cb28805ea464a5bff9f506eac3c54271804027ede29fad2cb7e6acc0c.png",
        "sha256": "3290006cb28805ea464a5bff9f506eac3c54271804027ede29fad2cb7e6acc0c"
      },
      {
        "path": "/data2/k6tk/e9/e967a2ba8c8795ffd422eddf053ac754eb8d218b637f0bd68c5c6b67da614ffc.png",
        "sha256": "e967a2ba8c8795ffd422eddf053ac754eb8d218b637f0bd68c5c6b67da614ffc"
      },
      {
        "path": "/data2/k6tk/30/30222acfe5b22844c35873d0eff774428f09335dac791d9e7ba7cb67d2c88791.png",
        "sha256": "30222acfe5b22844c35873d0eff774428f09335dac791d9e7ba7cb67d2c88791"
      },
      {
        "path": "/data2/k6tk/8e/8e958403e9645249d86f942ef0b86915c9b0238501776effe9696ac0d7b63ca6.png",
        "sha256": "8e958403e9645249d86f942ef0b86915c9b0238501776effe9696ac0d7b63ca6"
      },
      {
        "path": "/data2/k6tk/3e/3ee3be4b6e4d7eb3b147b1983cccc03aafef751923273567062955705a33afc6.png",
        "sha256": "3ee3be4b6e4d7eb3b147b1983cccc03aafef751923273567062955705a33afc6"
      },
      {
        "path": "/data2/k6tk/83/834726160b4e6aa0949ea5fc0ca28e70ea3a3a32ed1eff537e5d287d9ede43aa.png",
        "sha256": "834726160b4e6aa0949ea5fc0ca28e70ea3a3a32ed1eff537e5d287d9ede43aa"
      },
      {
        "path": "/data2/k6tk/87/87271ad456296bec9abd58231030b05fcbfe067d2bf8991f0aaf8e2c47aef9e1.png",
        "sha256": "87271ad456296bec9abd58231030b05fcbfe067d2bf8991f0aaf8e2c47aef9e1"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the chair, face away from the jacket. Is the couch to your left or right?",
    "timestamps": [
      0.0,
      1.5,
      3.0416666666666665,
      4.541666666666667,
      6.083333333333333,
      7.583333333333333,
      9.125,
      10.666666666666666,
      12.166666666666666,
      13.708333333333334,
      15.208333333333334,
      16.75,
      18.25,
      19.791666666666668,
      21.333333333333332,
      22.833333333333332,
      24.375,
      25.875,
      27.416666666666668,
      28.958333333333332,
      30.458333333333332,
      32.0,
      33.5,
      35.041666666666664,
      36.541666666666664,
      38.083333333333336,
      39.625,
      41.125,
      42.666666666666664,
      44.166666666666664,
      45.708333333333336,
      47.25
    ],
    "total_num_frames": 1135
  },
  "target": "<think>\nStep 1: find the chair and the jacket, then the couch.\nStep 2: standing at the chair and facing the jacket, I find the couch to my right.\nStep 3: I face away from the jacket by making a half turn. Front and back swap, and left and right swap.\nSo I find the couch to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qf7f1bfaf105b80f4804ff854",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "c424a939f8e64c45212268c675cca635b38b055b15053c6558d001c331fa825b"
  },
  "candidate_id": "ground-bde211faf439b676a47180d976868a40d7dc64517d45f209b3fc46073f6d27d5",
  "label_row_keys": [
    "qf7f1bfaf105b80f4804ff854-p1"
  ]
}
```

## 4. q823d096ce3d5e229b18f4329_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q823d096ce3d5e229b18f4329",
      "source_store_i": 13721,
      "source_row_sha256": "93367c03d02bd101e4fc9909679e92d1128ad082bd8b4c4b4b34357bd4ddcf96",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 37,
        "end": 43,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q823d096ce3d5e229b18f4329_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
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
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the air duct and facing away from the trash can, is the blinds to the left or the right of the trash can?",
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
  "target": "<think>\nStep 1: locate the blinds, the air duct and the trash can.\nStep 2: facing the trash can from the air duct, I find the blinds to my right.\nStep 3: I face away from the trash can by making a half turn. Front and back swap, and left and right swap.\nSo I find the blinds to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "3b03b55a48eceabdc3cb42706a0884fd9aa31fb8a7c42162dc166361b3af6984"
  },
  "candidate_id": "ground-0a4ef03a91e0c27bfa0898c407d804be1ddccf561958ab6b3aa3b0336c8b022b",
  "label_row_keys": [
    "q823d096ce3d5e229b18f4329"
  ]
}
```

## 5. q7a2f7c3ffd9d857b289a069f_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q7a2f7c3ffd9d857b289a069f",
      "source_store_i": 3727,
      "source_row_sha256": "d46e2bf3132d3ca1bff7338e61f32551bd73b4c1043b64b8fcde344e5d827f9c",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 32,
        "end": 38,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q7a2f7c3ffd9d857b289a069f_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vf08c915fdcda",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      359,
      719,
      1079,
      1439,
      1799,
      2159,
      2519,
      2879,
      3239,
      3599,
      3958,
      4318,
      4678,
      5038,
      5398,
      5758,
      6118,
      6478,
      6838,
      7198,
      7557,
      7917,
      8277,
      8637,
      8997,
      9357,
      9717,
      10077,
      10437,
      10797,
      11157
    ],
    "frames": [
      {
        "path": "/data2/k6tk/87/87c1a6e2ef66b37ab3d44891762178df7c43d6af702dfa0e5f93911cc5279a7a.png",
        "sha256": "87c1a6e2ef66b37ab3d44891762178df7c43d6af702dfa0e5f93911cc5279a7a"
      },
      {
        "path": "/data2/k6tk/21/212d9c17944c71d87a1d3fcd48cd52752402b87b89eadc42ef314c72e7d09f4b.png",
        "sha256": "212d9c17944c71d87a1d3fcd48cd52752402b87b89eadc42ef314c72e7d09f4b"
      },
      {
        "path": "/data2/k6tk/57/57b8ae57d74815ff6a53933f6e9776112cd0701456757e33ad5acf8a3c6efc23.png",
        "sha256": "57b8ae57d74815ff6a53933f6e9776112cd0701456757e33ad5acf8a3c6efc23"
      },
      {
        "path": "/data2/k6tk/2a/2af91f7f52487a3bd63e42a964ef9d63b8bccdd5f70733eb2c5bd7ad20a1b779.png",
        "sha256": "2af91f7f52487a3bd63e42a964ef9d63b8bccdd5f70733eb2c5bd7ad20a1b779"
      },
      {
        "path": "/data2/k6tk/6f/6f225bb4e890bdf67543f48f4eb6d3cee3efeacd6d265c0a148d2a514739066d.png",
        "sha256": "6f225bb4e890bdf67543f48f4eb6d3cee3efeacd6d265c0a148d2a514739066d"
      },
      {
        "path": "/data2/k6tk/ab/abce6f9e48a2d369d9e92bde9800d5f101c54641f006dd4d98ceb813540ffd83.png",
        "sha256": "abce6f9e48a2d369d9e92bde9800d5f101c54641f006dd4d98ceb813540ffd83"
      },
      {
        "path": "/data2/k6tk/43/4324b8ee9c94407ba8bcd1a77829b35a6922cbd7a72fc2630465557bb21ec402.png",
        "sha256": "4324b8ee9c94407ba8bcd1a77829b35a6922cbd7a72fc2630465557bb21ec402"
      },
      {
        "path": "/data2/k6tk/aa/aab0febc3d5ccbe1fc7dbdcd30f607574835a8a1bdb63746a730cfd5d22beaef.png",
        "sha256": "aab0febc3d5ccbe1fc7dbdcd30f607574835a8a1bdb63746a730cfd5d22beaef"
      },
      {
        "path": "/data2/k6tk/2e/2e3f7fad56feaddfcf864b775851864df7cb7387c9e4916ed697efc14cff91be.png",
        "sha256": "2e3f7fad56feaddfcf864b775851864df7cb7387c9e4916ed697efc14cff91be"
      },
      {
        "path": "/data2/k6tk/45/45e368badb756ad43828fcd91093eabf2e147faf10ff124fb24cdcd3b8ff2a88.png",
        "sha256": "45e368badb756ad43828fcd91093eabf2e147faf10ff124fb24cdcd3b8ff2a88"
      },
      {
        "path": "/data2/k6tk/36/36abf05cda11e9925172c7d04eb485e8ef05d1b1dee78d81c807ea292f70888e.png",
        "sha256": "36abf05cda11e9925172c7d04eb485e8ef05d1b1dee78d81c807ea292f70888e"
      },
      {
        "path": "/data2/k6tk/e4/e490d9feaae4782d8788e207ca13d45038477857afc0ced59448ce195eefef84.png",
        "sha256": "e490d9feaae4782d8788e207ca13d45038477857afc0ced59448ce195eefef84"
      },
      {
        "path": "/data2/k6tk/03/03db60aa0c4e076f8e39fd23343f6774f9ef56d05fa46de370ce660073b9e7fb.png",
        "sha256": "03db60aa0c4e076f8e39fd23343f6774f9ef56d05fa46de370ce660073b9e7fb"
      },
      {
        "path": "/data2/k6tk/f5/f5157b9b6c4a98bcaa52efbae2d8297b6c6bdfdad80439e7a2dacde174e27b59.png",
        "sha256": "f5157b9b6c4a98bcaa52efbae2d8297b6c6bdfdad80439e7a2dacde174e27b59"
      },
      {
        "path": "/data2/k6tk/60/6003bb2d818d2854e9e64386e25df375a93d1f2bf7424774b33dfb6115ad4a3b.png",
        "sha256": "6003bb2d818d2854e9e64386e25df375a93d1f2bf7424774b33dfb6115ad4a3b"
      },
      {
        "path": "/data2/k6tk/c2/c2a33cd669d68cffc8adeb11da5ebc0eebb935c41e388c35fc7fa3a3f164cf4a.png",
        "sha256": "c2a33cd669d68cffc8adeb11da5ebc0eebb935c41e388c35fc7fa3a3f164cf4a"
      },
      {
        "path": "/data2/k6tk/f5/f5020333e9bdbba65d8b668d30b5d17ff2acd07d7ed5101c3cd368488003d9f6.png",
        "sha256": "f5020333e9bdbba65d8b668d30b5d17ff2acd07d7ed5101c3cd368488003d9f6"
      },
      {
        "path": "/data2/k6tk/da/da2e22470e4c6118bbcf10e22cc057d6da28355754837f01f5f98cddb963e70b.png",
        "sha256": "da2e22470e4c6118bbcf10e22cc057d6da28355754837f01f5f98cddb963e70b"
      },
      {
        "path": "/data2/k6tk/98/98038325cbd01d5d645c87181e0e7dde30a575fdef5274c69ac9d64e3fbbec42.png",
        "sha256": "98038325cbd01d5d645c87181e0e7dde30a575fdef5274c69ac9d64e3fbbec42"
      },
      {
        "path": "/data2/k6tk/4b/4b2aac80afabc1b50fb9bc339f3f5ce0cc675815f613ff227904983e38165bea.png",
        "sha256": "4b2aac80afabc1b50fb9bc339f3f5ce0cc675815f613ff227904983e38165bea"
      },
      {
        "path": "/data2/k6tk/1d/1d178529ac22d5934774fde1bf5ecb2c4796ebaa16dd00c0b064f3ccf6838171.png",
        "sha256": "1d178529ac22d5934774fde1bf5ecb2c4796ebaa16dd00c0b064f3ccf6838171"
      },
      {
        "path": "/data2/k6tk/5b/5bbd8c1a6533f071728f2697d2cc41ff8fa9ffa5aaa4854d7f81d024257baad6.png",
        "sha256": "5bbd8c1a6533f071728f2697d2cc41ff8fa9ffa5aaa4854d7f81d024257baad6"
      },
      {
        "path": "/data2/k6tk/0e/0e394a1a0c8a6aba2ae1156291167eb8b7cc091b6446578468f6f3fc39898e17.png",
        "sha256": "0e394a1a0c8a6aba2ae1156291167eb8b7cc091b6446578468f6f3fc39898e17"
      },
      {
        "path": "/data2/k6tk/c2/c2dc90610008bf2de818904928772eb97fd209b47fb65c2fa7718f1282a19724.png",
        "sha256": "c2dc90610008bf2de818904928772eb97fd209b47fb65c2fa7718f1282a19724"
      },
      {
        "path": "/data2/k6tk/06/065c76675fb819da9f0e78def499a5ea3193b843958a1a8697462fde74b805f0.png",
        "sha256": "065c76675fb819da9f0e78def499a5ea3193b843958a1a8697462fde74b805f0"
      },
      {
        "path": "/data2/k6tk/9e/9e945288f8a4d72e84f2959809d477855919c3a41ed9a902b13c371c1d5b6b8a.png",
        "sha256": "9e945288f8a4d72e84f2959809d477855919c3a41ed9a902b13c371c1d5b6b8a"
      },
      {
        "path": "/data2/k6tk/da/dace599de6c317a10259df6ca94aef5a0eedd385fd53a5acf3e1b38d297c24ce.png",
        "sha256": "dace599de6c317a10259df6ca94aef5a0eedd385fd53a5acf3e1b38d297c24ce"
      },
      {
        "path": "/data2/k6tk/d3/d3b36eefdffb31d26077c0b62e0b28306224dcaec08bee90221305ba8c211bfd.png",
        "sha256": "d3b36eefdffb31d26077c0b62e0b28306224dcaec08bee90221305ba8c211bfd"
      },
      {
        "path": "/data2/k6tk/01/019db917fc63102fa6cafcf11c1e9cd745c33c3a6899e4199d190f28ebbcef8c.png",
        "sha256": "019db917fc63102fa6cafcf11c1e9cd745c33c3a6899e4199d190f28ebbcef8c"
      },
      {
        "path": "/data2/k6tk/67/67e8b011224df56d92cb71970c694b002faf468bae883cce1036cf7f38840655.png",
        "sha256": "67e8b011224df56d92cb71970c694b002faf468bae883cce1036cf7f38840655"
      },
      {
        "path": "/data2/k6tk/86/860265ea83a0a4a858b03b713d95135869c4fe69ba890d494d571913734dc425.png",
        "sha256": "860265ea83a0a4a858b03b713d95135869c4fe69ba890d494d571913734dc425"
      },
      {
        "path": "/data2/k6tk/76/763251a64c80845bd1e3c305b039849eb3fb4d1e36b17fd03ef32f44de478079.png",
        "sha256": "763251a64c80845bd1e3c305b039849eb3fb4d1e36b17fd03ef32f44de478079"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the bag and facing away from the basket, is the sauce bottle to the left or the right of the basket?",
    "timestamps": [
      0.0,
      5.983333333333333,
      11.983333333333333,
      17.983333333333334,
      23.983333333333334,
      29.983333333333334,
      35.983333333333334,
      41.983333333333334,
      47.983333333333334,
      53.983333333333334,
      59.983333333333334,
      65.96666666666667,
      71.96666666666667,
      77.96666666666667,
      83.96666666666667,
      89.96666666666667,
      95.96666666666667,
      101.96666666666667,
      107.96666666666667,
      113.96666666666667,
      119.96666666666667,
      125.95,
      131.95,
      137.95,
      143.95,
      149.95,
      155.95,
      161.95,
      167.95,
      173.95,
      179.95,
      185.95
    ],
    "total_num_frames": 11158
  },
  "target": "<think>\nStep 1: find the bag, the basket and the sauce bottle.\nStep 2: I find the sauce bottle to my right when I stand at the bag facing the basket.\nStep 3: I face away from the basket by making a half turn. Front and back swap, and left and right swap.\nSo I find the sauce bottle to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "d6a2a88ab55342c33dca4633ba01fe30579062efb07b4f92de79250f360cf0ba"
  },
  "candidate_id": "ground-af7a83bc78d0c4410fe8aa67c798a3f9eb49a5be4af0dfa4eabb27977a7ea9ef",
  "label_row_keys": [
    "q7a2f7c3ffd9d857b289a069f"
  ]
}
```

## 6. qa2dd1945c5c82ea884aaa63c_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qa2dd1945c5c82ea884aaa63c",
      "source_store_i": 3196,
      "source_row_sha256": "24a4717ed92d1475f43897a7192906fe6d1d5eee4a1345da844e63a193ee8bcc",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 53,
        "end": 59,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qa2dd1945c5c82ea884aaa63c_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vf49c2dab5fcb",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      178,
      356,
      535,
      713,
      891,
      1070,
      1248,
      1426,
      1605,
      1783,
      1961,
      2140,
      2318,
      2496,
      2675,
      2853,
      3032,
      3210,
      3388,
      3567,
      3745,
      3923,
      4102,
      4280,
      4458,
      4637,
      4815,
      4993,
      5172,
      5350,
      5529
    ],
    "frames": [
      {
        "path": "/data2/k6tk/1a/1a6500727ed95728e833c9177eed9de5309f402ba8e7b208af3a40120952e3c9.png",
        "sha256": "1a6500727ed95728e833c9177eed9de5309f402ba8e7b208af3a40120952e3c9"
      },
      {
        "path": "/data2/k6tk/7d/7d4d70be09fa29b17134473119ddf91facb29fbddeffe0e03129ce75dd0a29e9.png",
        "sha256": "7d4d70be09fa29b17134473119ddf91facb29fbddeffe0e03129ce75dd0a29e9"
      },
      {
        "path": "/data2/k6tk/20/20419f3b93b4a16e81f85e1f42e588ee160133ef319ea0cf335ae5702fe6c18f.png",
        "sha256": "20419f3b93b4a16e81f85e1f42e588ee160133ef319ea0cf335ae5702fe6c18f"
      },
      {
        "path": "/data2/k6tk/36/36dee7cee91e0359d8cae0019b997629e3c9e506df80417593c0a5e215194de4.png",
        "sha256": "36dee7cee91e0359d8cae0019b997629e3c9e506df80417593c0a5e215194de4"
      },
      {
        "path": "/data2/k6tk/ce/ced60a193dd1613e78a7db46b7f1f16b605d84cc36bf0830352be3aec3fded03.png",
        "sha256": "ced60a193dd1613e78a7db46b7f1f16b605d84cc36bf0830352be3aec3fded03"
      },
      {
        "path": "/data2/k6tk/52/52d9004196ba97f8a542c7aa0b6ca527357258b26c9704f447a41e79c8fecde8.png",
        "sha256": "52d9004196ba97f8a542c7aa0b6ca527357258b26c9704f447a41e79c8fecde8"
      },
      {
        "path": "/data2/k6tk/e6/e6288ded76f24412e4ea5cf57baf8a78404d8dcfca00afe7f20e4b93112bb35c.png",
        "sha256": "e6288ded76f24412e4ea5cf57baf8a78404d8dcfca00afe7f20e4b93112bb35c"
      },
      {
        "path": "/data2/k6tk/50/5000fd0427714a0764be3cdb247894b44784fb59d01204760b06b8af53d16d08.png",
        "sha256": "5000fd0427714a0764be3cdb247894b44784fb59d01204760b06b8af53d16d08"
      },
      {
        "path": "/data2/k6tk/8a/8aeca01ab4f11df122cbf61c6126a1d58a888e743b43a9d9332836142240a258.png",
        "sha256": "8aeca01ab4f11df122cbf61c6126a1d58a888e743b43a9d9332836142240a258"
      },
      {
        "path": "/data2/k6tk/30/30055a6b5e9b798d349c147d708bdb7e68193520336a37844720924e5387c59b.png",
        "sha256": "30055a6b5e9b798d349c147d708bdb7e68193520336a37844720924e5387c59b"
      },
      {
        "path": "/data2/k6tk/ea/ea5dd40194277a9465abe9eb69adf797a4060245ccb97e6071fb1bafda196a0f.png",
        "sha256": "ea5dd40194277a9465abe9eb69adf797a4060245ccb97e6071fb1bafda196a0f"
      },
      {
        "path": "/data2/k6tk/de/dec0a04e977cc588b8f0c73c7aaad602becfc0a2713c77f589da264fd8156566.png",
        "sha256": "dec0a04e977cc588b8f0c73c7aaad602becfc0a2713c77f589da264fd8156566"
      },
      {
        "path": "/data2/k6tk/c6/c677f6bab4ff2282704a07c4ed82c67a249b0cb89615e204983c3c2f73bcd9bc.png",
        "sha256": "c677f6bab4ff2282704a07c4ed82c67a249b0cb89615e204983c3c2f73bcd9bc"
      },
      {
        "path": "/data2/k6tk/b9/b9302693dfe62689e17248ee076dad98e8b18d05d1a9e67d2df73f3ac49de864.png",
        "sha256": "b9302693dfe62689e17248ee076dad98e8b18d05d1a9e67d2df73f3ac49de864"
      },
      {
        "path": "/data2/k6tk/e4/e41524f9f1d2699ebd398ba09a20cb0374bd28f4b775b490c7ee19bf56b90d7a.png",
        "sha256": "e41524f9f1d2699ebd398ba09a20cb0374bd28f4b775b490c7ee19bf56b90d7a"
      },
      {
        "path": "/data2/k6tk/7c/7cd7dc292e1b944044319a0826161b18fdfb27424b915a0fee565e60f1f67ac3.png",
        "sha256": "7cd7dc292e1b944044319a0826161b18fdfb27424b915a0fee565e60f1f67ac3"
      },
      {
        "path": "/data2/k6tk/dc/dc346326195d21d54d5c2e85db8e9bb6ce15e8a83a741f334ec13e2b9f16d3fd.png",
        "sha256": "dc346326195d21d54d5c2e85db8e9bb6ce15e8a83a741f334ec13e2b9f16d3fd"
      },
      {
        "path": "/data2/k6tk/3e/3e9faf2478a63b74fb7cdab6d6830b330c73fec343fffe806ffdc4e58c38669c.png",
        "sha256": "3e9faf2478a63b74fb7cdab6d6830b330c73fec343fffe806ffdc4e58c38669c"
      },
      {
        "path": "/data2/k6tk/ab/ab713d53af8360059c15db14b7b901e4c2016c0076051805131a8ea494329160.png",
        "sha256": "ab713d53af8360059c15db14b7b901e4c2016c0076051805131a8ea494329160"
      },
      {
        "path": "/data2/k6tk/71/716360c257abba9e2866652b988a646f1fb73461066925de7d60e35eba9e2aca.png",
        "sha256": "716360c257abba9e2866652b988a646f1fb73461066925de7d60e35eba9e2aca"
      },
      {
        "path": "/data2/k6tk/0c/0c75a86dc3cb93961e572e85d7c5c3edfec60a1b6eae6273c5febb0e133560cd.png",
        "sha256": "0c75a86dc3cb93961e572e85d7c5c3edfec60a1b6eae6273c5febb0e133560cd"
      },
      {
        "path": "/data2/k6tk/42/4289e5ca84561cc3b3deeafb7fc8b572e86cf8c581014caae75e2087a689d20d.png",
        "sha256": "4289e5ca84561cc3b3deeafb7fc8b572e86cf8c581014caae75e2087a689d20d"
      },
      {
        "path": "/data2/k6tk/60/607474d227c3a52fbe3c59723221b729ac16fae5e1d4c8c1fd629b2f37e56abb.png",
        "sha256": "607474d227c3a52fbe3c59723221b729ac16fae5e1d4c8c1fd629b2f37e56abb"
      },
      {
        "path": "/data2/k6tk/ea/ead45c02621c024fe4676c9b513e22f318290fdae2b9babf9e60e56d2cd0a236.png",
        "sha256": "ead45c02621c024fe4676c9b513e22f318290fdae2b9babf9e60e56d2cd0a236"
      },
      {
        "path": "/data2/k6tk/42/4298c14927fa41aae051c27b3784e6aa112d7fe11c1b9cb6ca1ab0ff512c813b.png",
        "sha256": "4298c14927fa41aae051c27b3784e6aa112d7fe11c1b9cb6ca1ab0ff512c813b"
      },
      {
        "path": "/data2/k6tk/5a/5aa4807970a009d206e2137fd549be5a9daeef4e152e7ee3ff618de38ef85a44.png",
        "sha256": "5aa4807970a009d206e2137fd549be5a9daeef4e152e7ee3ff618de38ef85a44"
      },
      {
        "path": "/data2/k6tk/1d/1d063943061f72f7551f64691d715d7678f30b9bffe80de1fac2fd2057b37c72.png",
        "sha256": "1d063943061f72f7551f64691d715d7678f30b9bffe80de1fac2fd2057b37c72"
      },
      {
        "path": "/data2/k6tk/01/0102a63368d6f3ca29ac6511505aafce160722fd2a509584c374fd3208b465fb.png",
        "sha256": "0102a63368d6f3ca29ac6511505aafce160722fd2a509584c374fd3208b465fb"
      },
      {
        "path": "/data2/k6tk/0e/0e4e37ac68aa18b54dad617105f6efcc59744429619592185be9cab8e5fe0300.png",
        "sha256": "0e4e37ac68aa18b54dad617105f6efcc59744429619592185be9cab8e5fe0300"
      },
      {
        "path": "/data2/k6tk/c6/c6955043d3abfeea49c9485c5923072b4efaa8f0cc2fbf3bcda6ff4d0e7e5c8e.png",
        "sha256": "c6955043d3abfeea49c9485c5923072b4efaa8f0cc2fbf3bcda6ff4d0e7e5c8e"
      },
      {
        "path": "/data2/k6tk/24/2494a89f4023757da4e4c38e9eab778615d473909ee5bcc09f28f402987ff9ce.png",
        "sha256": "2494a89f4023757da4e4c38e9eab778615d473909ee5bcc09f28f402987ff9ce"
      },
      {
        "path": "/data2/k6tk/ce/ce7d03017f19f847615ef5f069fa3eaae5c4e115f28f49b4cb8db1a705eca4df.png",
        "sha256": "ce7d03017f19f847615ef5f069fa3eaae5c4e115f28f49b4cb8db1a705eca4df"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the bathroom stall partition and facing away from the door, is the heater to the left or the right of the door?",
    "timestamps": [
      0.0,
      2.966666666666667,
      5.933333333333334,
      8.916666666666666,
      11.883333333333333,
      14.85,
      17.833333333333332,
      20.8,
      23.766666666666666,
      26.75,
      29.716666666666665,
      32.68333333333333,
      35.666666666666664,
      38.63333333333333,
      41.6,
      44.583333333333336,
      47.55,
      50.53333333333333,
      53.5,
      56.46666666666667,
      59.45,
      62.416666666666664,
      65.38333333333334,
      68.36666666666666,
      71.33333333333333,
      74.3,
      77.28333333333333,
      80.25,
      83.21666666666667,
      86.2,
      89.16666666666667,
      92.15
    ],
    "total_num_frames": 5530
  },
  "target": "<think>\nStep 1: find the bathroom stall partition, the door and the heater.\nStep 2: facing the door from the bathroom stall partition, I find the heater to my right.\nStep 3: I face away from the door by making a half turn. Front and back swap, and left and right swap.\nSo I find the heater to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "fe6a45b742f2c768aa3a08ec5019abc7ba5ee17f0369ef1ac429b7a0389d6f74"
  },
  "candidate_id": "ground-ff0f28f94dd0caf0d7485262c9f007e49832e6e0ecf43debfd157ca6b5a05a77",
  "label_row_keys": [
    "qa2dd1945c5c82ea884aaa63c"
  ]
}
```

## 7. q66bb0d5547b5068458d3e60d-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q66bb0d5547b5068458d3e60d-p1",
      "source_store_i": 74652,
      "source_row_sha256": "f423472b94cd70c636fb54ac7f5cc23ddc04b64894012c23ede488fe4584713d",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 44,
        "end": 55,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q66bb0d5547b5068458d3e60d-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v4bc971b8588e",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      45,
      91,
      136,
      182,
      227,
      273,
      318,
      364,
      409,
      455,
      500,
      546,
      591,
      637,
      682,
      728,
      773,
      819,
      864,
      910,
      955,
      1001,
      1046,
      1092,
      1137,
      1183,
      1228,
      1274,
      1319,
      1365,
      1411
    ],
    "frames": [
      {
        "path": "/data2/k6tk/54/54ee20ac0a3d978e9504ea9a37c6ffda9ea13f181fa400eb2033785cc4b1cc3c.png",
        "sha256": "54ee20ac0a3d978e9504ea9a37c6ffda9ea13f181fa400eb2033785cc4b1cc3c"
      },
      {
        "path": "/data2/k6tk/81/818e7cf83ea795adf94ab74845d2635e3308dad1c52fce2b473891741a408194.png",
        "sha256": "818e7cf83ea795adf94ab74845d2635e3308dad1c52fce2b473891741a408194"
      },
      {
        "path": "/data2/k6tk/2c/2cb1b97e4ad78767f46e27b4ec2c9bf0f9940666ea0a58a3fd62d1edcd4fefda.png",
        "sha256": "2cb1b97e4ad78767f46e27b4ec2c9bf0f9940666ea0a58a3fd62d1edcd4fefda"
      },
      {
        "path": "/data2/k6tk/3e/3ec24634c1de461432ecd4bf6458023ff26ca8877ac21a4187440cdb3c6e2059.png",
        "sha256": "3ec24634c1de461432ecd4bf6458023ff26ca8877ac21a4187440cdb3c6e2059"
      },
      {
        "path": "/data2/k6tk/6f/6fc68a475afe79b2a0da790708c512e81f15273aec779f5f953ea08330263f6c.png",
        "sha256": "6fc68a475afe79b2a0da790708c512e81f15273aec779f5f953ea08330263f6c"
      },
      {
        "path": "/data2/k6tk/72/7294659faca40103eae27ad93e9c5bb99faea5b1b305d315ddd28f0c44fb60b7.png",
        "sha256": "7294659faca40103eae27ad93e9c5bb99faea5b1b305d315ddd28f0c44fb60b7"
      },
      {
        "path": "/data2/k6tk/3f/3f3555502721781056ce499e006f7dd335406c445580efb761053cf5e6e544de.png",
        "sha256": "3f3555502721781056ce499e006f7dd335406c445580efb761053cf5e6e544de"
      },
      {
        "path": "/data2/k6tk/f0/f0c39fab3dd83fa2bb325ddb04df34c87c081fbe346a6778bfb0da83c6366288.png",
        "sha256": "f0c39fab3dd83fa2bb325ddb04df34c87c081fbe346a6778bfb0da83c6366288"
      },
      {
        "path": "/data2/k6tk/b5/b59d9781af12218a69422e718e65bd2e78e7e180a86eb39bf265252b4395e309.png",
        "sha256": "b59d9781af12218a69422e718e65bd2e78e7e180a86eb39bf265252b4395e309"
      },
      {
        "path": "/data2/k6tk/a5/a5c17d85e4ec1e661a7fcc853358ce914c251b253189e7ec146ddc691a779b25.png",
        "sha256": "a5c17d85e4ec1e661a7fcc853358ce914c251b253189e7ec146ddc691a779b25"
      },
      {
        "path": "/data2/k6tk/31/316535dab727f4032b70c8613d3d80d56fd89946831bc24852d5cbeb17b563d5.png",
        "sha256": "316535dab727f4032b70c8613d3d80d56fd89946831bc24852d5cbeb17b563d5"
      },
      {
        "path": "/data2/k6tk/8a/8a9b5ffe9301b1f603ac83d2ee2a7a9328086dc42636db0c0e83552dbbdefd32.png",
        "sha256": "8a9b5ffe9301b1f603ac83d2ee2a7a9328086dc42636db0c0e83552dbbdefd32"
      },
      {
        "path": "/data2/k6tk/61/6175f7fdad2658e20036b862cdaf9f5591cd82e132adf497443c8dbe51c31299.png",
        "sha256": "6175f7fdad2658e20036b862cdaf9f5591cd82e132adf497443c8dbe51c31299"
      },
      {
        "path": "/data2/k6tk/6e/6eaf8418803cc92404859fe275781ee9e373bd5b969c88fcbdea894692fc39fc.png",
        "sha256": "6eaf8418803cc92404859fe275781ee9e373bd5b969c88fcbdea894692fc39fc"
      },
      {
        "path": "/data2/k6tk/0f/0f6fa740e12daf35c58d48f407bf4a3d6a06522168e502d9d112243b9ef939f3.png",
        "sha256": "0f6fa740e12daf35c58d48f407bf4a3d6a06522168e502d9d112243b9ef939f3"
      },
      {
        "path": "/data2/k6tk/5f/5f46f1e6b8f78748dab59abfc371a790ac312e5a5b03753140708591a330bc07.png",
        "sha256": "5f46f1e6b8f78748dab59abfc371a790ac312e5a5b03753140708591a330bc07"
      },
      {
        "path": "/data2/k6tk/5c/5cf6d297e3203af0095bb5e56fe78e79022d55ab82e28b81f2e39e43d2fae8c2.png",
        "sha256": "5cf6d297e3203af0095bb5e56fe78e79022d55ab82e28b81f2e39e43d2fae8c2"
      },
      {
        "path": "/data2/k6tk/d8/d8d0fd2e90b2773b0a50f5be7f90d612ea4433c38354a690074fba151b7f9e69.png",
        "sha256": "d8d0fd2e90b2773b0a50f5be7f90d612ea4433c38354a690074fba151b7f9e69"
      },
      {
        "path": "/data2/k6tk/e3/e33f89d9a9e9015c03996df32462694a2d0289fa9c2539963cf1c5c785617e56.png",
        "sha256": "e33f89d9a9e9015c03996df32462694a2d0289fa9c2539963cf1c5c785617e56"
      },
      {
        "path": "/data2/k6tk/c1/c1adcc179cbf22c8f4849b947e074838fb373eb936df516adc46587890d5ca44.png",
        "sha256": "c1adcc179cbf22c8f4849b947e074838fb373eb936df516adc46587890d5ca44"
      },
      {
        "path": "/data2/k6tk/e6/e60250f33b85fbbf3eb1709d0185632dec0fa41f92431b1e6454211e60bb396a.png",
        "sha256": "e60250f33b85fbbf3eb1709d0185632dec0fa41f92431b1e6454211e60bb396a"
      },
      {
        "path": "/data2/k6tk/99/99e8416d4d39ad214c9b9993dcb95a8a2ba345bf2a4e0c97dedf8cfbb8ebf330.png",
        "sha256": "99e8416d4d39ad214c9b9993dcb95a8a2ba345bf2a4e0c97dedf8cfbb8ebf330"
      },
      {
        "path": "/data2/k6tk/01/017eef02172eac77080459ba23e8bef72e7c5682d548418e233da94b1769e2aa.png",
        "sha256": "017eef02172eac77080459ba23e8bef72e7c5682d548418e233da94b1769e2aa"
      },
      {
        "path": "/data2/k6tk/20/20d84c7d5bb941ffd7588459e2e5e941fe4a51e808233c2ebcc185cf32f65703.png",
        "sha256": "20d84c7d5bb941ffd7588459e2e5e941fe4a51e808233c2ebcc185cf32f65703"
      },
      {
        "path": "/data2/k6tk/d7/d7dbcc42dc0d94fe3147be83072bd8746bd686ec5f15fd41cee4bf30a0caefbc.png",
        "sha256": "d7dbcc42dc0d94fe3147be83072bd8746bd686ec5f15fd41cee4bf30a0caefbc"
      },
      {
        "path": "/data2/k6tk/20/20878f9c8c9b8fc27c3671d0eb3fca4c359b77e457660eb4ee25a78fd084ea33.png",
        "sha256": "20878f9c8c9b8fc27c3671d0eb3fca4c359b77e457660eb4ee25a78fd084ea33"
      },
      {
        "path": "/data2/k6tk/24/241181b952f9d6a9729fb98d3ebe750854ff26d01b665947ba21c76a41cf9740.png",
        "sha256": "241181b952f9d6a9729fb98d3ebe750854ff26d01b665947ba21c76a41cf9740"
      },
      {
        "path": "/data2/k6tk/1d/1db18d24de1988c005bac6cce6464acfac7cb15b791891639de9fc4bef1d4db3.png",
        "sha256": "1db18d24de1988c005bac6cce6464acfac7cb15b791891639de9fc4bef1d4db3"
      },
      {
        "path": "/data2/k6tk/d4/d46623555324492aa83390e0003bc375bd578b0450d70fea1d8aefb622eba6bd.png",
        "sha256": "d46623555324492aa83390e0003bc375bd578b0450d70fea1d8aefb622eba6bd"
      },
      {
        "path": "/data2/k6tk/56/56a84816111684e214930c21a98a325ca8d1d894177b449851041281525136af.png",
        "sha256": "56a84816111684e214930c21a98a325ca8d1d894177b449851041281525136af"
      },
      {
        "path": "/data2/k6tk/2e/2ec30b9bb69f8e8273c995f7e61b16d1d1cf7a2cadaf4a42ab09852f29a3d0e3.png",
        "sha256": "2ec30b9bb69f8e8273c995f7e61b16d1d1cf7a2cadaf4a42ab09852f29a3d0e3"
      },
      {
        "path": "/data2/k6tk/71/715df8e14f2a00048943df7f2fd93e39ff02e556656ed1139ed3d9d086b8ab2d.png",
        "sha256": "715df8e14f2a00048943df7f2fd93e39ff02e556656ed1139ed3d9d086b8ab2d"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From a position beside the bathroom vanity, face away from the coffee table. Is the couch to your left or right?",
    "timestamps": [
      0.0,
      1.875,
      3.7916666666666665,
      5.666666666666667,
      7.583333333333333,
      9.458333333333334,
      11.375,
      13.25,
      15.166666666666666,
      17.041666666666668,
      18.958333333333332,
      20.833333333333332,
      22.75,
      24.625,
      26.541666666666668,
      28.416666666666668,
      30.333333333333332,
      32.208333333333336,
      34.125,
      36.0,
      37.916666666666664,
      39.791666666666664,
      41.708333333333336,
      43.583333333333336,
      45.5,
      47.375,
      49.291666666666664,
      51.166666666666664,
      53.083333333333336,
      54.958333333333336,
      56.875,
      58.791666666666664
    ],
    "total_num_frames": 1412
  },
  "target": "<think>\nStep 1: locate the couch, the bathroom vanity and the coffee table.\nStep 2: I find the couch to my right when I stand at the bathroom vanity facing the coffee table.\nStep 3: I face away from the coffee table by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the couch to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q66bb0d5547b5068458d3e60d",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "0b6b4263d29866bfedf912b389b1fc36f0c00abcb8c66aa6a56184d9bc4eae08"
  },
  "candidate_id": "ground-7d9c0afcedd157566b9c929a5da4305452244f83fc055ecd3980aa4c585be1ad",
  "label_row_keys": [
    "q66bb0d5547b5068458d3e60d-p1"
  ]
}
```

## 8. q9fa94022062e3e7d4992a5ce-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q9fa94022062e3e7d4992a5ce-p1",
      "source_store_i": 68735,
      "source_row_sha256": "678e00791d1c8c8c8cebb86352dfda1c045202366333a2ef6e5cf68be1ea8343",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 37,
        "end": 48,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q9fa94022062e3e7d4992a5ce-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "va322fdc2dc45",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      417,
      835,
      1253,
      1670,
      2088,
      2506,
      2924,
      3341,
      3759,
      4177,
      4595,
      5012,
      5430,
      5848,
      6266,
      6683,
      7101,
      7519,
      7937,
      8354,
      8772,
      9190,
      9608,
      10025,
      10443,
      10861,
      11279,
      11696,
      12114,
      12532,
      12950
    ],
    "frames": [
      {
        "path": "/data2/k6tk/63/63272616449d32c53e211669cc2dd9096f9da84ddfc903b785007007481f2629.png",
        "sha256": "63272616449d32c53e211669cc2dd9096f9da84ddfc903b785007007481f2629"
      },
      {
        "path": "/data2/k6tk/14/14eec2d4db06ccde31000d78769fae654b7f1fde5f0ea2fdf91f631cb9e1fa72.png",
        "sha256": "14eec2d4db06ccde31000d78769fae654b7f1fde5f0ea2fdf91f631cb9e1fa72"
      },
      {
        "path": "/data2/k6tk/7a/7a2ef9c794e93b4d2dfae5779a0e5752448abad8e3c4c67422416c3203522994.png",
        "sha256": "7a2ef9c794e93b4d2dfae5779a0e5752448abad8e3c4c67422416c3203522994"
      },
      {
        "path": "/data2/k6tk/9a/9a0e2591ae93bea182b5bb5767ab78e04f600a97dc6c46709bcc0b780307ce66.png",
        "sha256": "9a0e2591ae93bea182b5bb5767ab78e04f600a97dc6c46709bcc0b780307ce66"
      },
      {
        "path": "/data2/k6tk/4f/4f545b061a22903f50f3de14e07c53adeca703746d3d5a4f1407f32798347bbb.png",
        "sha256": "4f545b061a22903f50f3de14e07c53adeca703746d3d5a4f1407f32798347bbb"
      },
      {
        "path": "/data2/k6tk/ef/efaee669c14cc7694d29071f5eb992b3db549021f472ab8e5f5f2edf52af6caf.png",
        "sha256": "efaee669c14cc7694d29071f5eb992b3db549021f472ab8e5f5f2edf52af6caf"
      },
      {
        "path": "/data2/k6tk/00/00c1c7d5c9f32276c8a3d024abafd2694bd5903246afbcce05b8c65abb570b4f.png",
        "sha256": "00c1c7d5c9f32276c8a3d024abafd2694bd5903246afbcce05b8c65abb570b4f"
      },
      {
        "path": "/data2/k6tk/63/63088950279a57b0c37324969052f248e6da459449781ced785b4b10dc28f0e9.png",
        "sha256": "63088950279a57b0c37324969052f248e6da459449781ced785b4b10dc28f0e9"
      },
      {
        "path": "/data2/k6tk/4b/4b62ec6f163ab3c1387f86621f198326b49aad923cf87b9b4163770be5c59272.png",
        "sha256": "4b62ec6f163ab3c1387f86621f198326b49aad923cf87b9b4163770be5c59272"
      },
      {
        "path": "/data2/k6tk/23/23aff36cfe04777d65f79064267e731867b08c5d9ce8d9a568d9567b1addbb28.png",
        "sha256": "23aff36cfe04777d65f79064267e731867b08c5d9ce8d9a568d9567b1addbb28"
      },
      {
        "path": "/data2/k6tk/60/60ee733b847fbe45ad23917348f1ac710a451f3fa431e18ab9fd75be1a4550a8.png",
        "sha256": "60ee733b847fbe45ad23917348f1ac710a451f3fa431e18ab9fd75be1a4550a8"
      },
      {
        "path": "/data2/k6tk/d3/d3064cdd654023180539327ad50562b35175232edcb8910877755d682cd03821.png",
        "sha256": "d3064cdd654023180539327ad50562b35175232edcb8910877755d682cd03821"
      },
      {
        "path": "/data2/k6tk/97/97a5ca896b0ea58f65ca82c19731983563d316de90815cd309b25f57d29c6b49.png",
        "sha256": "97a5ca896b0ea58f65ca82c19731983563d316de90815cd309b25f57d29c6b49"
      },
      {
        "path": "/data2/k6tk/c2/c2a500fe222816296a034cd768a578b122d5958084bebf43e88fc8f01acbf403.png",
        "sha256": "c2a500fe222816296a034cd768a578b122d5958084bebf43e88fc8f01acbf403"
      },
      {
        "path": "/data2/k6tk/84/8485f7d501ef277ea1faaa78d3cdbe92d44ed46fb8a0c24ab5f3a4bc798808ec.png",
        "sha256": "8485f7d501ef277ea1faaa78d3cdbe92d44ed46fb8a0c24ab5f3a4bc798808ec"
      },
      {
        "path": "/data2/k6tk/88/8811192f65e226a87648cd441c61535644c081ccff82a76bd8755571246570ad.png",
        "sha256": "8811192f65e226a87648cd441c61535644c081ccff82a76bd8755571246570ad"
      },
      {
        "path": "/data2/k6tk/74/74d63b3873a315078befffeef45d67bd9f775d67dfdb27cd623b6a37ad3ea7a1.png",
        "sha256": "74d63b3873a315078befffeef45d67bd9f775d67dfdb27cd623b6a37ad3ea7a1"
      },
      {
        "path": "/data2/k6tk/3d/3dcaaa727dff225ff8af6a90689d02ed50c0ee70d7a9c516cc5787f4e6dc29b7.png",
        "sha256": "3dcaaa727dff225ff8af6a90689d02ed50c0ee70d7a9c516cc5787f4e6dc29b7"
      },
      {
        "path": "/data2/k6tk/ae/ae97d0e0049e416730032c9fec15f4b16c20f9827f2a2c6c1128274d4d09d87d.png",
        "sha256": "ae97d0e0049e416730032c9fec15f4b16c20f9827f2a2c6c1128274d4d09d87d"
      },
      {
        "path": "/data2/k6tk/bb/bbb5dcfa138c6c787714f74f9d60b46a0b4deec626b7041c2dbd1f56a1e1e729.png",
        "sha256": "bbb5dcfa138c6c787714f74f9d60b46a0b4deec626b7041c2dbd1f56a1e1e729"
      },
      {
        "path": "/data2/k6tk/f0/f03443ff76c98a98779145af8ab4eb50f8adb25f7fc0d75ec497d685c528584b.png",
        "sha256": "f03443ff76c98a98779145af8ab4eb50f8adb25f7fc0d75ec497d685c528584b"
      },
      {
        "path": "/data2/k6tk/bb/bbe0b2a773c3bb83dc1669d1b0974663ff9e4024c2635cfa1e6e3ea180f464e6.png",
        "sha256": "bbe0b2a773c3bb83dc1669d1b0974663ff9e4024c2635cfa1e6e3ea180f464e6"
      },
      {
        "path": "/data2/k6tk/2a/2a0ff26947778f99e0150a7a3efa55a87c94ac059db02a77aa6df25c946ccc52.png",
        "sha256": "2a0ff26947778f99e0150a7a3efa55a87c94ac059db02a77aa6df25c946ccc52"
      },
      {
        "path": "/data2/k6tk/06/06d6f86d314172b2a3513e379074861ac1c5a7b8ba38bf30ac777c8501af172c.png",
        "sha256": "06d6f86d314172b2a3513e379074861ac1c5a7b8ba38bf30ac777c8501af172c"
      },
      {
        "path": "/data2/k6tk/b8/b8343521865d462e1a7e8e6bcf2894e530ba057549a67a179a018eb099033a24.png",
        "sha256": "b8343521865d462e1a7e8e6bcf2894e530ba057549a67a179a018eb099033a24"
      },
      {
        "path": "/data2/k6tk/c9/c94a874c510bb1f04fd483bce5e96c8a91a84851bf9ebc71d4dcf43d6cd0d9a9.png",
        "sha256": "c94a874c510bb1f04fd483bce5e96c8a91a84851bf9ebc71d4dcf43d6cd0d9a9"
      },
      {
        "path": "/data2/k6tk/10/10418fc1e4d1c171cd10aca080b3577a805b8e9ddb92dd8eca40ea74d1940cbb.png",
        "sha256": "10418fc1e4d1c171cd10aca080b3577a805b8e9ddb92dd8eca40ea74d1940cbb"
      },
      {
        "path": "/data2/k6tk/f2/f2b1e1ce1b5bfc54ddc3bffdf809e57c1d3e01793cdc374ff2b6d06e84a7ff47.png",
        "sha256": "f2b1e1ce1b5bfc54ddc3bffdf809e57c1d3e01793cdc374ff2b6d06e84a7ff47"
      },
      {
        "path": "/data2/k6tk/ab/ab5d083cfa67a93c562381729d8c14e79e10bd340596153178685d5c520a1ee0.png",
        "sha256": "ab5d083cfa67a93c562381729d8c14e79e10bd340596153178685d5c520a1ee0"
      },
      {
        "path": "/data2/k6tk/fc/fc5d22eb6f722e54f455668af4a3fc4989fb6ee4157a0b1a632a864c6d93dcfe.png",
        "sha256": "fc5d22eb6f722e54f455668af4a3fc4989fb6ee4157a0b1a632a864c6d93dcfe"
      },
      {
        "path": "/data2/k6tk/1e/1ec1fefb7b1534409cdb40130a833133227f73b45e649cb60dd69d6e4f6461a7.png",
        "sha256": "1ec1fefb7b1534409cdb40130a833133227f73b45e649cb60dd69d6e4f6461a7"
      },
      {
        "path": "/data2/k6tk/22/226e17d14a28f0d264daa101e93a0b246d76036b5b3235d22188c3d476e97a79.png",
        "sha256": "226e17d14a28f0d264daa101e93a0b246d76036b5b3235d22188c3d476e97a79"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From a position beside the backpack, face away from the bed. Is the bedside cabinet to your left or right?",
    "timestamps": [
      0.0,
      6.95,
      13.916666666666666,
      20.883333333333333,
      27.833333333333332,
      34.8,
      41.766666666666666,
      48.733333333333334,
      55.68333333333333,
      62.65,
      69.61666666666666,
      76.58333333333333,
      83.53333333333333,
      90.5,
      97.46666666666667,
      104.43333333333334,
      111.38333333333334,
      118.35,
      125.31666666666666,
      132.28333333333333,
      139.23333333333332,
      146.2,
      153.16666666666666,
      160.13333333333333,
      167.08333333333334,
      174.05,
      181.01666666666668,
      187.98333333333332,
      194.93333333333334,
      201.9,
      208.86666666666667,
      215.83333333333334
    ],
    "total_num_frames": 12951
  },
  "target": "<think>\nStep 1: find the backpack, the bed and the bedside cabinet.\nStep 2: I find the bedside cabinet to my right when I stand at the backpack facing the bed.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the bedside cabinet to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q9fa94022062e3e7d4992a5ce",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "5139c2706d101305a07a0b00c9258de3adb8b7d0200ff6ff8bebb46e127164fa"
  },
  "candidate_id": "ground-966ed86262885f13c273b7cb2b819f2516cf08af2c6a5a7dba14e5533ecba0ef",
  "label_row_keys": [
    "q9fa94022062e3e7d4992a5ce-p1"
  ]
}
```

## 9. qb8b4b86839f85d2c26a75919_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qb8b4b86839f85d2c26a75919",
      "source_store_i": 24520,
      "source_row_sha256": "2ac65871743eacda86def3178533b1bcc3fc7fd0ad4f7c63096d38d598fadcce",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 38,
        "end": 52,
        "source_clause": "looking toward",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qb8b4b86839f85d2c26a75919_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd525adf489a6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      89,
      178,
      267,
      356,
      445,
      534,
      623,
      712,
      801,
      890,
      980,
      1069,
      1158,
      1247,
      1336,
      1425,
      1514,
      1603,
      1692,
      1781,
      1871,
      1960,
      2049,
      2138,
      2227,
      2316,
      2405,
      2494,
      2583,
      2672,
      2762
    ],
    "frames": [
      {
        "path": "/data2/k6tk/07/07f351c00a7491c4f79b22efbd4b53f0a3e92539e00ead6c342c349f9177a693.png",
        "sha256": "07f351c00a7491c4f79b22efbd4b53f0a3e92539e00ead6c342c349f9177a693"
      },
      {
        "path": "/data2/k6tk/33/3374d6fcd4133105ded911d92948211964ce98049d8d93748405ee0c3d42ecea.png",
        "sha256": "3374d6fcd4133105ded911d92948211964ce98049d8d93748405ee0c3d42ecea"
      },
      {
        "path": "/data2/k6tk/fd/fd06979a06fbd552da9aefe8a1ad798563423115c6c221471fbef3bab40e87aa.png",
        "sha256": "fd06979a06fbd552da9aefe8a1ad798563423115c6c221471fbef3bab40e87aa"
      },
      {
        "path": "/data2/k6tk/3b/3b4cb4e2f7067fd2e06fea4f7b6b6b363b85aa670daa0b861dd8f59fdd5a1a91.png",
        "sha256": "3b4cb4e2f7067fd2e06fea4f7b6b6b363b85aa670daa0b861dd8f59fdd5a1a91"
      },
      {
        "path": "/data2/k6tk/0e/0edbef7ff22afd8bf4a3f6ae8d72c771ec2a976db5756bf7e210442eb74eebdd.png",
        "sha256": "0edbef7ff22afd8bf4a3f6ae8d72c771ec2a976db5756bf7e210442eb74eebdd"
      },
      {
        "path": "/data2/k6tk/00/008fdac02e416724b525c6a0f884968fda6d9a22f5bffaccb2f23c935bb5e657.png",
        "sha256": "008fdac02e416724b525c6a0f884968fda6d9a22f5bffaccb2f23c935bb5e657"
      },
      {
        "path": "/data2/k6tk/60/6001e845bf93b116ef01f652672f52fbd3cb9d8d790b3edbd4bf25bec3f57433.png",
        "sha256": "6001e845bf93b116ef01f652672f52fbd3cb9d8d790b3edbd4bf25bec3f57433"
      },
      {
        "path": "/data2/k6tk/89/89d516bdb4cf190ed4d27c8c0a4b2c57531c10e38eb584aa5cb2fdea3dc10e09.png",
        "sha256": "89d516bdb4cf190ed4d27c8c0a4b2c57531c10e38eb584aa5cb2fdea3dc10e09"
      },
      {
        "path": "/data2/k6tk/93/93d884db614fddfad4a5894f3fea80ca4e87e9660c4d8c2612abd13496ea5693.png",
        "sha256": "93d884db614fddfad4a5894f3fea80ca4e87e9660c4d8c2612abd13496ea5693"
      },
      {
        "path": "/data2/k6tk/4c/4c0e930013a7d6276d1f49788d3affca1a7b0259b4dc4d67ebab004929f0f763.png",
        "sha256": "4c0e930013a7d6276d1f49788d3affca1a7b0259b4dc4d67ebab004929f0f763"
      },
      {
        "path": "/data2/k6tk/8d/8d15c08d93145678a6c0aee15fca1f31d795b03bbd5000b6f03041ea8d6d228b.png",
        "sha256": "8d15c08d93145678a6c0aee15fca1f31d795b03bbd5000b6f03041ea8d6d228b"
      },
      {
        "path": "/data2/k6tk/23/232eb586371a8b3529bb79c4f1ebd09d49440c983b185cd7b70dd280687a9930.png",
        "sha256": "232eb586371a8b3529bb79c4f1ebd09d49440c983b185cd7b70dd280687a9930"
      },
      {
        "path": "/data2/k6tk/4f/4f54bab2fbad0f1c8e7282e61ba5fa4e3378f3ae4f5b68e1e323107401c8d1ee.png",
        "sha256": "4f54bab2fbad0f1c8e7282e61ba5fa4e3378f3ae4f5b68e1e323107401c8d1ee"
      },
      {
        "path": "/data2/k6tk/1d/1db9abcc99bc8ba2e6a3f6cc1edc837efaa0ced17afbbc130355e931929c0ea7.png",
        "sha256": "1db9abcc99bc8ba2e6a3f6cc1edc837efaa0ced17afbbc130355e931929c0ea7"
      },
      {
        "path": "/data2/k6tk/0b/0b305d0cdddbce74eb6488eba83e98aec4d2587cbfebfdf477ffc656339769cd.png",
        "sha256": "0b305d0cdddbce74eb6488eba83e98aec4d2587cbfebfdf477ffc656339769cd"
      },
      {
        "path": "/data2/k6tk/fb/fba7a4fefb0f347a811fb9f9c1d411dd489ed5a082937a46efb51a2d2d58e8fa.png",
        "sha256": "fba7a4fefb0f347a811fb9f9c1d411dd489ed5a082937a46efb51a2d2d58e8fa"
      },
      {
        "path": "/data2/k6tk/9c/9ceff38fb5356e69bef37502bc951a20c39f9149832f9cf9c70ba29342e6bd4b.png",
        "sha256": "9ceff38fb5356e69bef37502bc951a20c39f9149832f9cf9c70ba29342e6bd4b"
      },
      {
        "path": "/data2/k6tk/1a/1a40f57bcf1b459eee162251fdbf5c91ae1447832c32863ddf2fcb767099189e.png",
        "sha256": "1a40f57bcf1b459eee162251fdbf5c91ae1447832c32863ddf2fcb767099189e"
      },
      {
        "path": "/data2/k6tk/1c/1c601aff27f75adee1fdfb9c99dc3ed095f93f2a19f95bfffdf0d18e9667e4a7.png",
        "sha256": "1c601aff27f75adee1fdfb9c99dc3ed095f93f2a19f95bfffdf0d18e9667e4a7"
      },
      {
        "path": "/data2/k6tk/b8/b8900a5f09fdc799269a8f9cb65e0f1b7a03d574e023691212f7bffcb90c3f76.png",
        "sha256": "b8900a5f09fdc799269a8f9cb65e0f1b7a03d574e023691212f7bffcb90c3f76"
      },
      {
        "path": "/data2/k6tk/0e/0e5448c56cd43fba0d9aeced5aa2e88f7e82a2a992400f034499a8c424a0a373.png",
        "sha256": "0e5448c56cd43fba0d9aeced5aa2e88f7e82a2a992400f034499a8c424a0a373"
      },
      {
        "path": "/data2/k6tk/2d/2d3cfd41109f54c1e3f91c2acaedbfe41268a4610470bf44fd6e1dd1ad9a9c6a.png",
        "sha256": "2d3cfd41109f54c1e3f91c2acaedbfe41268a4610470bf44fd6e1dd1ad9a9c6a"
      },
      {
        "path": "/data2/k6tk/16/162fdcddb465a06270ae322d269897fda5ea92e759cc97483be163584377bb0b.png",
        "sha256": "162fdcddb465a06270ae322d269897fda5ea92e759cc97483be163584377bb0b"
      },
      {
        "path": "/data2/k6tk/18/183b4bb090c7d8001ed8cdb4af6b67fe9c397c9e5c20d436f68ed083dd494993.png",
        "sha256": "183b4bb090c7d8001ed8cdb4af6b67fe9c397c9e5c20d436f68ed083dd494993"
      },
      {
        "path": "/data2/k6tk/37/378ee49b0d28ab93c8be64962f3e27f6b6d775fd0c35a5119f9333bbb4201674.png",
        "sha256": "378ee49b0d28ab93c8be64962f3e27f6b6d775fd0c35a5119f9333bbb4201674"
      },
      {
        "path": "/data2/k6tk/7a/7a64bbc242889670430ac692d276b0558a69fa4c57f7c9105d60197e8a409217.png",
        "sha256": "7a64bbc242889670430ac692d276b0558a69fa4c57f7c9105d60197e8a409217"
      },
      {
        "path": "/data2/k6tk/90/9092d297307bd739807b5bb620e51f8f5e2b0419b07819db967cf78c44949fbd.png",
        "sha256": "9092d297307bd739807b5bb620e51f8f5e2b0419b07819db967cf78c44949fbd"
      },
      {
        "path": "/data2/k6tk/74/748f91651cfab30e79e953977e55872a3a278e94248680d64453d7c85514a8bf.png",
        "sha256": "748f91651cfab30e79e953977e55872a3a278e94248680d64453d7c85514a8bf"
      },
      {
        "path": "/data2/k6tk/a8/a821c00860a4d037d1fece90c7586daa5a07d83488ee9b7163ca13f05a511952.png",
        "sha256": "a821c00860a4d037d1fece90c7586daa5a07d83488ee9b7163ca13f05a511952"
      },
      {
        "path": "/data2/k6tk/2b/2bc1eaa212c83e32d2777c95e20fc83b112261759797acb66b81a989b97066e8.png",
        "sha256": "2bc1eaa212c83e32d2777c95e20fc83b112261759797acb66b81a989b97066e8"
      },
      {
        "path": "/data2/k6tk/ac/ac2d6f60620e9df0bf6aa75e71ad414a470021008efae5599f76e2679b44beb9.png",
        "sha256": "ac2d6f60620e9df0bf6aa75e71ad414a470021008efae5599f76e2679b44beb9"
      },
      {
        "path": "/data2/k6tk/c6/c6fb43b1c6fa16a046ef7890607b56c0014f317658191f4c94d3b2d42c1f3d19.png",
        "sha256": "c6fb43b1c6fa16a046ef7890607b56c0014f317658191f4c94d3b2d42c1f3d19"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "Standing next to the refrigerator and facing away from the mirror, should I expect the lamp to my left or right of the mirror?",
    "timestamps": [
      0.0,
      3.7083333333333335,
      7.416666666666667,
      11.125,
      14.833333333333334,
      18.541666666666668,
      22.25,
      25.958333333333332,
      29.666666666666668,
      33.375,
      37.083333333333336,
      40.833333333333336,
      44.541666666666664,
      48.25,
      51.958333333333336,
      55.666666666666664,
      59.375,
      63.083333333333336,
      66.79166666666667,
      70.5,
      74.20833333333333,
      77.95833333333333,
      81.66666666666667,
      85.375,
      89.08333333333333,
      92.79166666666667,
      96.5,
      100.20833333333333,
      103.91666666666667,
      107.625,
      111.33333333333333,
      115.08333333333333
    ],
    "total_num_frames": 2763
  },
  "target": "<think>\nStep 1: find the refrigerator, the mirror and the lamp.\nStep 2: facing the mirror from the refrigerator, I find the lamp to my right.\nStep 3: I face away from the mirror by making a half turn. Front and back swap, and left and right swap.\nSo I find the lamp to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "8081247b08e8a4f90a4e12ec4b4daaa01b1a54146175cda2a4777cdf238a4af7"
  },
  "candidate_id": "ground-c56ca2b930ef7ca16926ab2dbdaac3b382b6424d85be308620e6922d3b827511",
  "label_row_keys": [
    "qb8b4b86839f85d2c26a75919"
  ]
}
```

## 10. qff18b56e9dc09833688b4d5b-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qff18b56e9dc09833688b4d5b-p1",
      "source_store_i": 59955,
      "source_row_sha256": "92651687b14e915013dc676eb8b054cc169a6b510901b74fae8a2dae8bb81ca2",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 36,
        "end": 47,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qff18b56e9dc09833688b4d5b-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vec343b84e485",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      484,
      968,
      1452,
      1936,
      2420,
      2904,
      3388,
      3872,
      4356,
      4840,
      5324,
      5808,
      6292,
      6776,
      7260,
      7744,
      8228,
      8712,
      9196,
      9680,
      10164,
      10648,
      11132,
      11616,
      12100,
      12584,
      13068,
      13552,
      14036,
      14520,
      15004
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a6/a633c27d8b1c671ce4b2383a5efd33bf8781f080135712d1a9c5ae3401433734.png",
        "sha256": "a633c27d8b1c671ce4b2383a5efd33bf8781f080135712d1a9c5ae3401433734"
      },
      {
        "path": "/data2/k6tk/ba/baf85e240d81cd93fb2bd53fd1a38eb5da62c3ef48fd6c92a8e48b0ac008c5df.png",
        "sha256": "baf85e240d81cd93fb2bd53fd1a38eb5da62c3ef48fd6c92a8e48b0ac008c5df"
      },
      {
        "path": "/data2/k6tk/9a/9a28847fc98cf306ab8020f0cb387cc5581e5f95a0f686591aa63729d1fef4d1.png",
        "sha256": "9a28847fc98cf306ab8020f0cb387cc5581e5f95a0f686591aa63729d1fef4d1"
      },
      {
        "path": "/data2/k6tk/c5/c5750d7159d3df641c634da915ea9c5749202c8016788809f6a5f2526914bbfa.png",
        "sha256": "c5750d7159d3df641c634da915ea9c5749202c8016788809f6a5f2526914bbfa"
      },
      {
        "path": "/data2/k6tk/82/82bbb827fbe299acd04992f3832d23860bc382906ef3ac4fdc19bbcdc8831ef9.png",
        "sha256": "82bbb827fbe299acd04992f3832d23860bc382906ef3ac4fdc19bbcdc8831ef9"
      },
      {
        "path": "/data2/k6tk/ee/ee226c7cf1bc4d5087da66bd94808c15541c17975a76eb453ecfe89a359039dd.png",
        "sha256": "ee226c7cf1bc4d5087da66bd94808c15541c17975a76eb453ecfe89a359039dd"
      },
      {
        "path": "/data2/k6tk/de/dee1138475075dc08927ada78e915301bfa9ed141c5458d2d3b32499e0220ea8.png",
        "sha256": "dee1138475075dc08927ada78e915301bfa9ed141c5458d2d3b32499e0220ea8"
      },
      {
        "path": "/data2/k6tk/83/83a14e1ca0f754a458f6948d603165163a73e6ca706c594fd4d6cdfd6f19f4cc.png",
        "sha256": "83a14e1ca0f754a458f6948d603165163a73e6ca706c594fd4d6cdfd6f19f4cc"
      },
      {
        "path": "/data2/k6tk/c9/c9e26ad7310e08b541bef9576101487bd1a9c0855a8f9cd471def2f1612e9eaf.png",
        "sha256": "c9e26ad7310e08b541bef9576101487bd1a9c0855a8f9cd471def2f1612e9eaf"
      },
      {
        "path": "/data2/k6tk/fd/fda918832052568ca5fa9e97adb1575cb5252770ceaa4559485123e3eacb5820.png",
        "sha256": "fda918832052568ca5fa9e97adb1575cb5252770ceaa4559485123e3eacb5820"
      },
      {
        "path": "/data2/k6tk/0b/0bd329b34f920b0f4a3d316de5ef8e1c6366684845ce87bae5a5484725483f4c.png",
        "sha256": "0bd329b34f920b0f4a3d316de5ef8e1c6366684845ce87bae5a5484725483f4c"
      },
      {
        "path": "/data2/k6tk/e4/e4bd1834e4bdb55e787f885b9885c7ec4c69d63b6b1fd9f4b0ea1eabb9a65e21.png",
        "sha256": "e4bd1834e4bdb55e787f885b9885c7ec4c69d63b6b1fd9f4b0ea1eabb9a65e21"
      },
      {
        "path": "/data2/k6tk/b8/b85fed47e659a0368bf6ea6777bd8915db8cd97208b78553f631c342dcfc6baa.png",
        "sha256": "b85fed47e659a0368bf6ea6777bd8915db8cd97208b78553f631c342dcfc6baa"
      },
      {
        "path": "/data2/k6tk/80/802a59b5158967c94d511ed9cc1bfbb5c86e78998e3247e3950a7ad5894a40c6.png",
        "sha256": "802a59b5158967c94d511ed9cc1bfbb5c86e78998e3247e3950a7ad5894a40c6"
      },
      {
        "path": "/data2/k6tk/68/6894b4f513c1961492993dc361ee1707b26f1bf16fa5b9c333481b0635eae500.png",
        "sha256": "6894b4f513c1961492993dc361ee1707b26f1bf16fa5b9c333481b0635eae500"
      },
      {
        "path": "/data2/k6tk/35/35b81940d29df2ac06b5c9c45a01f079147640c144ed88442e33469a2fc84a5f.png",
        "sha256": "35b81940d29df2ac06b5c9c45a01f079147640c144ed88442e33469a2fc84a5f"
      },
      {
        "path": "/data2/k6tk/0d/0da99b58e499e9f26c28bf0c41afb35599498b5b0b563dc1935ecb57799aa093.png",
        "sha256": "0da99b58e499e9f26c28bf0c41afb35599498b5b0b563dc1935ecb57799aa093"
      },
      {
        "path": "/data2/k6tk/8e/8efd5f767e7fb0fe3190ed96bccf51fce25cef3f42f1917946870c306cedfbfc.png",
        "sha256": "8efd5f767e7fb0fe3190ed96bccf51fce25cef3f42f1917946870c306cedfbfc"
      },
      {
        "path": "/data2/k6tk/11/1115a2ab803cd895c8e39d0f185c249100d915e37f81f466430f35632ab5f169.png",
        "sha256": "1115a2ab803cd895c8e39d0f185c249100d915e37f81f466430f35632ab5f169"
      },
      {
        "path": "/data2/k6tk/6c/6c1d482f26d5165beb50adb62d42f6b1037155f2cd8ca2e52fe058d6db3683b5.png",
        "sha256": "6c1d482f26d5165beb50adb62d42f6b1037155f2cd8ca2e52fe058d6db3683b5"
      },
      {
        "path": "/data2/k6tk/be/be0ec6d2555a062726fdd1d733eedab4385e7ca7981dd7b3599646ef5d89bd12.png",
        "sha256": "be0ec6d2555a062726fdd1d733eedab4385e7ca7981dd7b3599646ef5d89bd12"
      },
      {
        "path": "/data2/k6tk/4f/4f7c4ffb2bcee0898368e7c712d4d6befe9d36e16c3a3b0bf943d0f4ab6bd72b.png",
        "sha256": "4f7c4ffb2bcee0898368e7c712d4d6befe9d36e16c3a3b0bf943d0f4ab6bd72b"
      },
      {
        "path": "/data2/k6tk/ee/eef4a0ee7f7f4d603be1c7ebabb7b3dae9642a6b63f273589f305939297ca961.png",
        "sha256": "eef4a0ee7f7f4d603be1c7ebabb7b3dae9642a6b63f273589f305939297ca961"
      },
      {
        "path": "/data2/k6tk/4c/4c897e073b2fefe3c47e93bbbe5a0d600f42af4dbc12759891c4770e07742aba.png",
        "sha256": "4c897e073b2fefe3c47e93bbbe5a0d600f42af4dbc12759891c4770e07742aba"
      },
      {
        "path": "/data2/k6tk/ed/ed438adf396fdc828b62498e6f02eb53d6c936219b9260f8dd344067461e86b6.png",
        "sha256": "ed438adf396fdc828b62498e6f02eb53d6c936219b9260f8dd344067461e86b6"
      },
      {
        "path": "/data2/k6tk/88/88aa20eaa58dfd94af3d813d42f359bd772c95c2959ae1a5564fcdb4d83d108a.png",
        "sha256": "88aa20eaa58dfd94af3d813d42f359bd772c95c2959ae1a5564fcdb4d83d108a"
      },
      {
        "path": "/data2/k6tk/dd/dda61f7584a788a0289d2e7ef2b849e67c0719dc37d2d9bd868b684c6530d4b4.png",
        "sha256": "dda61f7584a788a0289d2e7ef2b849e67c0719dc37d2d9bd868b684c6530d4b4"
      },
      {
        "path": "/data2/k6tk/25/2565d53093c76537a99f84ff4530aa0e4fafa39d16b9248f47e2b17147f686b5.png",
        "sha256": "2565d53093c76537a99f84ff4530aa0e4fafa39d16b9248f47e2b17147f686b5"
      },
      {
        "path": "/data2/k6tk/f5/f59e0c125af71a7b0cb527663c241e03f50f3fa7191a4430ef9eb82f9a858da2.png",
        "sha256": "f59e0c125af71a7b0cb527663c241e03f50f3fa7191a4430ef9eb82f9a858da2"
      },
      {
        "path": "/data2/k6tk/b2/b2f3cddf9e28e0cff6a8e8b42f1a26ac8213751ba09db19c0837eaf2e881c2c2.png",
        "sha256": "b2f3cddf9e28e0cff6a8e8b42f1a26ac8213751ba09db19c0837eaf2e881c2c2"
      },
      {
        "path": "/data2/k6tk/b1/b1b5cf25b39cce3be317e1926e2a8754793e490e006f670d08059b8224eed074.png",
        "sha256": "b1b5cf25b39cce3be317e1926e2a8754793e490e006f670d08059b8224eed074"
      },
      {
        "path": "/data2/k6tk/eb/ebd450a9ab38599d1c26241c8f08a371c5028cdad3c24fb81c4c374652d5cc71.png",
        "sha256": "ebd450a9ab38599d1c26241c8f08a371c5028cdad3c24fb81c4c374652d5cc71"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From a position beside the monitor, face away from the pan. Is the shoe rack to your left or right?",
    "timestamps": [
      0.0,
      8.066666666666666,
      16.133333333333333,
      24.2,
      32.266666666666666,
      40.333333333333336,
      48.4,
      56.46666666666667,
      64.53333333333333,
      72.6,
      80.66666666666667,
      88.73333333333333,
      96.8,
      104.86666666666666,
      112.93333333333334,
      121.0,
      129.06666666666666,
      137.13333333333333,
      145.2,
      153.26666666666668,
      161.33333333333334,
      169.4,
      177.46666666666667,
      185.53333333333333,
      193.6,
      201.66666666666666,
      209.73333333333332,
      217.8,
      225.86666666666667,
      233.93333333333334,
      242.0,
      250.06666666666666
    ],
    "total_num_frames": 15005
  },
  "target": "<think>\nStep 1: locate the shoe rack, the monitor and the pan.\nStep 2: standing at the monitor and facing the pan, I find the shoe rack to my right.\nStep 3: I face away from the pan by making a half turn. Front and back swap, and left and right swap.\nSo I find the shoe rack to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qff18b56e9dc09833688b4d5b",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "b733d637260628dbd23870a32d4924de65b23f6df8cb60d72df9b4a1bd5d4ab5"
  },
  "candidate_id": "ground-35646a07c59ecdb69e4665eb64b4f77f09e15080ad58ef8937fd527da85dd7d1",
  "label_row_keys": [
    "qff18b56e9dc09833688b4d5b-p1"
  ]
}
```

## 11. q34ff8218e521047dbf0e5d60-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q34ff8218e521047dbf0e5d60-p1",
      "source_store_i": 74610,
      "source_row_sha256": "c1e76d05d2dcd0d84c6159ed6cca82d997556037203afd7248142ffa77609331",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 31,
        "end": 41,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q34ff8218e521047dbf0e5d60-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v28331dfc2a61",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      350,
      700,
      1051,
      1401,
      1752,
      2102,
      2453,
      2803,
      3154,
      3504,
      3855,
      4205,
      4556,
      4906,
      5257,
      5607,
      5958,
      6308,
      6659,
      7009,
      7360,
      7710,
      8061,
      8411,
      8762,
      9112,
      9463,
      9813,
      10164,
      10514,
      10865
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ec/ec35ad9b8f42d03fb27ee22e24d6f2ee6068069731698d9b490236f5fb59f2e7.png",
        "sha256": "ec35ad9b8f42d03fb27ee22e24d6f2ee6068069731698d9b490236f5fb59f2e7"
      },
      {
        "path": "/data2/k6tk/69/694787cb370e15f84fdb839c4e7903b90628b74fb6c8a85077371fa9cff36ac1.png",
        "sha256": "694787cb370e15f84fdb839c4e7903b90628b74fb6c8a85077371fa9cff36ac1"
      },
      {
        "path": "/data2/k6tk/cb/cb5ed6735caf6825310f7eddd2ff3b310a930955d1151b9aeb27304719eec103.png",
        "sha256": "cb5ed6735caf6825310f7eddd2ff3b310a930955d1151b9aeb27304719eec103"
      },
      {
        "path": "/data2/k6tk/75/75b5c758a9962618a337dcb48fb69f95775535a787d2b6f2388f8caef0c773d2.png",
        "sha256": "75b5c758a9962618a337dcb48fb69f95775535a787d2b6f2388f8caef0c773d2"
      },
      {
        "path": "/data2/k6tk/8d/8d3ee90b607de2380ee920082cb3baadcfd026486e2a56391058c57a4c1fbf6d.png",
        "sha256": "8d3ee90b607de2380ee920082cb3baadcfd026486e2a56391058c57a4c1fbf6d"
      },
      {
        "path": "/data2/k6tk/33/334ce3475da1dc201376eadabc4db83134476d814af793ea5bc1cbdc87db0a20.png",
        "sha256": "334ce3475da1dc201376eadabc4db83134476d814af793ea5bc1cbdc87db0a20"
      },
      {
        "path": "/data2/k6tk/2e/2e348407ca4ac293ee46170b93873e83370adb3407f835d7c2be0891a960bd61.png",
        "sha256": "2e348407ca4ac293ee46170b93873e83370adb3407f835d7c2be0891a960bd61"
      },
      {
        "path": "/data2/k6tk/ad/add699700f71fc658d2da5dac84aeabefc41021ff1aba5eee1ef8ae33b75ccc0.png",
        "sha256": "add699700f71fc658d2da5dac84aeabefc41021ff1aba5eee1ef8ae33b75ccc0"
      },
      {
        "path": "/data2/k6tk/f4/f4b60a12478d106063b5e1a36a6db75c827313b6705bf0e8eb33f51138d23e78.png",
        "sha256": "f4b60a12478d106063b5e1a36a6db75c827313b6705bf0e8eb33f51138d23e78"
      },
      {
        "path": "/data2/k6tk/06/06e868832ca686ee13e1b50b96d9ec076d962fdde8ba499fc0da92f1e965a9ca.png",
        "sha256": "06e868832ca686ee13e1b50b96d9ec076d962fdde8ba499fc0da92f1e965a9ca"
      },
      {
        "path": "/data2/k6tk/e3/e3ab9e62fd44ef7332e145c6bfce3f3d07b8956d5263d94ab0cc8f2b743d2415.png",
        "sha256": "e3ab9e62fd44ef7332e145c6bfce3f3d07b8956d5263d94ab0cc8f2b743d2415"
      },
      {
        "path": "/data2/k6tk/35/3507e5f172bbc89d25267f006780e0ddd12e85ba5adf1d605a9696044d739c55.png",
        "sha256": "3507e5f172bbc89d25267f006780e0ddd12e85ba5adf1d605a9696044d739c55"
      },
      {
        "path": "/data2/k6tk/0c/0c56ce8d0acbfcdd231885ee7209f14ce77774fab8cb8f3d95f8ed5cf66c5860.png",
        "sha256": "0c56ce8d0acbfcdd231885ee7209f14ce77774fab8cb8f3d95f8ed5cf66c5860"
      },
      {
        "path": "/data2/k6tk/45/45b188e2aeaf46134fe6cccc659417b8c7ee333d57d51a85d7d4ef0111e4b41e.png",
        "sha256": "45b188e2aeaf46134fe6cccc659417b8c7ee333d57d51a85d7d4ef0111e4b41e"
      },
      {
        "path": "/data2/k6tk/16/1603fe9bf897001009234c20dee216378ff73b5d0e1fae430d29ef570a86205d.png",
        "sha256": "1603fe9bf897001009234c20dee216378ff73b5d0e1fae430d29ef570a86205d"
      },
      {
        "path": "/data2/k6tk/87/874ff483dcfd2d0ef6d9341b1f463b462090d841c36e0007db176e2a0120129d.png",
        "sha256": "874ff483dcfd2d0ef6d9341b1f463b462090d841c36e0007db176e2a0120129d"
      },
      {
        "path": "/data2/k6tk/b6/b63c1867e5506956b01870e8c1dd8739693e41765339bac963db0a4dc7e52bb5.png",
        "sha256": "b63c1867e5506956b01870e8c1dd8739693e41765339bac963db0a4dc7e52bb5"
      },
      {
        "path": "/data2/k6tk/36/3651c9c1317441fc7afff66af85945e90d95a44f24cfd1b6ed7f87d1e2c5edcb.png",
        "sha256": "3651c9c1317441fc7afff66af85945e90d95a44f24cfd1b6ed7f87d1e2c5edcb"
      },
      {
        "path": "/data2/k6tk/80/80965c599aff72b8a29e488dad5c216d8983a01cfe928fa52116482b63909a72.png",
        "sha256": "80965c599aff72b8a29e488dad5c216d8983a01cfe928fa52116482b63909a72"
      },
      {
        "path": "/data2/k6tk/74/74e3b0a02295334b0be5bcde06651f5d39f1f7568feb32ffe50598277787c2a7.png",
        "sha256": "74e3b0a02295334b0be5bcde06651f5d39f1f7568feb32ffe50598277787c2a7"
      },
      {
        "path": "/data2/k6tk/dc/dcc6dea8e56b4a4031a07781ec1876f28c27dc7077ddfff8a506ebe6e8cac031.png",
        "sha256": "dcc6dea8e56b4a4031a07781ec1876f28c27dc7077ddfff8a506ebe6e8cac031"
      },
      {
        "path": "/data2/k6tk/ca/caeb54f3b8c21fecdd96025c8e9cf6c3588f5a5b961635266bdbc35cd687253e.png",
        "sha256": "caeb54f3b8c21fecdd96025c8e9cf6c3588f5a5b961635266bdbc35cd687253e"
      },
      {
        "path": "/data2/k6tk/65/65c2ee043716111b6394e22d8e3a590ece8e89ec3af92f0300554f73d191ed4b.png",
        "sha256": "65c2ee043716111b6394e22d8e3a590ece8e89ec3af92f0300554f73d191ed4b"
      },
      {
        "path": "/data2/k6tk/8c/8ceb98aeb4728b22a0e9915a682549d707e806bde8ac4a44a90de3d099a06414.png",
        "sha256": "8ceb98aeb4728b22a0e9915a682549d707e806bde8ac4a44a90de3d099a06414"
      },
      {
        "path": "/data2/k6tk/10/10a0f1dadf0552904dfa5b59bc8336977a2ed648c306e5ce982bc0e5de8f80fe.png",
        "sha256": "10a0f1dadf0552904dfa5b59bc8336977a2ed648c306e5ce982bc0e5de8f80fe"
      },
      {
        "path": "/data2/k6tk/62/626afb66d8331452a61d1801f031bdb943f33e9a5d7352d6028044ee71cc01bb.png",
        "sha256": "626afb66d8331452a61d1801f031bdb943f33e9a5d7352d6028044ee71cc01bb"
      },
      {
        "path": "/data2/k6tk/7a/7a5867d5e2f1d7c2cab98cf89b0f7629388601bb7a0acb1b44dfc6f9867a6f94.png",
        "sha256": "7a5867d5e2f1d7c2cab98cf89b0f7629388601bb7a0acb1b44dfc6f9867a6f94"
      },
      {
        "path": "/data2/k6tk/3c/3cdb306b7fd0f4647bb1cfa96ca52bc468c85fe17b53b21e2652bab864766c43.png",
        "sha256": "3cdb306b7fd0f4647bb1cfa96ca52bc468c85fe17b53b21e2652bab864766c43"
      },
      {
        "path": "/data2/k6tk/2a/2ac6cd2ba80209e28ae0e38a90013e2d8b1dc955413449f4f1eb92224e5fe593.png",
        "sha256": "2ac6cd2ba80209e28ae0e38a90013e2d8b1dc955413449f4f1eb92224e5fe593"
      },
      {
        "path": "/data2/k6tk/93/93a196692ed4c5d576b3151b08a1e0b64d644d818c5f98d87cb9e4f93f8a40f6.png",
        "sha256": "93a196692ed4c5d576b3151b08a1e0b64d644d818c5f98d87cb9e4f93f8a40f6"
      },
      {
        "path": "/data2/k6tk/87/878b7549d66a83e7c316b7df9f2e6d89ee44d48cda5e6c62cd1faf0c4a33f5a6.png",
        "sha256": "878b7549d66a83e7c316b7df9f2e6d89ee44d48cda5e6c62cd1faf0c4a33f5a6"
      },
      {
        "path": "/data2/k6tk/47/471ad9ccd430e2edd9dcbf5547756d726e3662d135859c1ca4dbed510e94800f.png",
        "sha256": "471ad9ccd430e2edd9dcbf5547756d726e3662d135859c1ca4dbed510e94800f"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "While standing by the bowl and facing away from the cookware, decide whether the heater lies to your left or your right.",
    "timestamps": [
      0.0,
      5.833333333333333,
      11.666666666666666,
      17.516666666666666,
      23.35,
      29.2,
      35.03333333333333,
      40.88333333333333,
      46.71666666666667,
      52.56666666666667,
      58.4,
      64.25,
      70.08333333333333,
      75.93333333333334,
      81.76666666666667,
      87.61666666666666,
      93.45,
      99.3,
      105.13333333333334,
      110.98333333333333,
      116.81666666666666,
      122.66666666666667,
      128.5,
      134.35,
      140.18333333333334,
      146.03333333333333,
      151.86666666666667,
      157.71666666666667,
      163.55,
      169.4,
      175.23333333333332,
      181.08333333333334
    ],
    "total_num_frames": 10866
  },
  "target": "<think>\nStep 1: locate the bowl, the cookware and the heater.\nStep 2: facing the cookware from the bowl, I find the heater to my left.\nStep 3: I face away from the cookware by making a half turn. Front and back swap, and left and right swap.\nSo I find the heater to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q34ff8218e521047dbf0e5d60",
  "paraphrase_template": "easy_side",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "a05439bbb152191ed6f1addaf72deeaee07ff9a9206c91112d65aac095402d6b"
  },
  "candidate_id": "ground-ad9cceabab7f6301877cd3d5437a77bead912ef326086148c183efe2b1e72d6c",
  "label_row_keys": [
    "q34ff8218e521047dbf0e5d60-p1"
  ]
}
```

## 12. qeab492cfeb3b75d866f20a54-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qeab492cfeb3b75d866f20a54-p1",
      "source_store_i": 69625,
      "source_row_sha256": "9e14dbbb425b13bc053f3184b32c0b3320a9d7e9ab159e7e8508ec68ae1266e1",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 33,
        "end": 43,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qeab492cfeb3b75d866f20a54-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vc77656546d15",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      229,
      458,
      687,
      917,
      1146,
      1375,
      1605,
      1834,
      2063,
      2293,
      2522,
      2751,
      2981,
      3210,
      3439,
      3669,
      3898,
      4127,
      4357,
      4586,
      4815,
      5045,
      5274,
      5503,
      5733,
      5962,
      6191,
      6421,
      6650,
      6879,
      7109
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ab/aba6dcb0b6c1d60cf1d48c4e83c948f5405a5c193678c9878b6c7ae36f6c4384.png",
        "sha256": "aba6dcb0b6c1d60cf1d48c4e83c948f5405a5c193678c9878b6c7ae36f6c4384"
      },
      {
        "path": "/data2/k6tk/78/783d3985785a664e2fdc52cc3126e3493390f1c6b984c86df47f4ff832c3976d.png",
        "sha256": "783d3985785a664e2fdc52cc3126e3493390f1c6b984c86df47f4ff832c3976d"
      },
      {
        "path": "/data2/k6tk/7e/7e6891ac9601d48907f4c56b03803373d3e375a3f74085752266b537b62a28d7.png",
        "sha256": "7e6891ac9601d48907f4c56b03803373d3e375a3f74085752266b537b62a28d7"
      },
      {
        "path": "/data2/k6tk/f7/f718bb89b7b5110d17ab8a9f509bbe8b0815feed42235df99315971f12518835.png",
        "sha256": "f718bb89b7b5110d17ab8a9f509bbe8b0815feed42235df99315971f12518835"
      },
      {
        "path": "/data2/k6tk/ea/eaaea809ec4e6bbb0750ac58cb1964c57e17ecd8361b062dc3c5e58bfe855ba5.png",
        "sha256": "eaaea809ec4e6bbb0750ac58cb1964c57e17ecd8361b062dc3c5e58bfe855ba5"
      },
      {
        "path": "/data2/k6tk/b4/b400a65d5a68d874529232a2ea04917809ffdf682c53d3d05d3198e6c2bd40f8.png",
        "sha256": "b400a65d5a68d874529232a2ea04917809ffdf682c53d3d05d3198e6c2bd40f8"
      },
      {
        "path": "/data2/k6tk/36/36cc09861e32842b1aa1bf5bbb3ae6a0a551489f5b752ad388f8b3119cb047b2.png",
        "sha256": "36cc09861e32842b1aa1bf5bbb3ae6a0a551489f5b752ad388f8b3119cb047b2"
      },
      {
        "path": "/data2/k6tk/a7/a71fe541ebaf01d6f3b2eb1583466359befb66d72d36af928d8aec3b6b0632de.png",
        "sha256": "a71fe541ebaf01d6f3b2eb1583466359befb66d72d36af928d8aec3b6b0632de"
      },
      {
        "path": "/data2/k6tk/82/82b28a3aac30987f5c413023113e35fd04e387db958d77f82732e482a3edccbb.png",
        "sha256": "82b28a3aac30987f5c413023113e35fd04e387db958d77f82732e482a3edccbb"
      },
      {
        "path": "/data2/k6tk/a6/a66c4a16a51492c53d4823d45090d09adcb756b1a5d3164159d6faced85a4da5.png",
        "sha256": "a66c4a16a51492c53d4823d45090d09adcb756b1a5d3164159d6faced85a4da5"
      },
      {
        "path": "/data2/k6tk/f6/f6fd246a1874e7d59b5548fe35c592fb2e09e56aede4eb50fc5e0c09a1f81dd7.png",
        "sha256": "f6fd246a1874e7d59b5548fe35c592fb2e09e56aede4eb50fc5e0c09a1f81dd7"
      },
      {
        "path": "/data2/k6tk/66/662cc308776cd3863d54632fd1386f94c9c40504bd6a6fdd0f36443bd9637f1b.png",
        "sha256": "662cc308776cd3863d54632fd1386f94c9c40504bd6a6fdd0f36443bd9637f1b"
      },
      {
        "path": "/data2/k6tk/90/902ff9714a7a3c923b7c7e9f314d9b70f52f9b191bcad0e0f81873f309029ca0.png",
        "sha256": "902ff9714a7a3c923b7c7e9f314d9b70f52f9b191bcad0e0f81873f309029ca0"
      },
      {
        "path": "/data2/k6tk/09/096291be67f5a3355a1ce2da1c69c0c3b679734263759294e4b3452dcc6ee904.png",
        "sha256": "096291be67f5a3355a1ce2da1c69c0c3b679734263759294e4b3452dcc6ee904"
      },
      {
        "path": "/data2/k6tk/3d/3d47bbed9236d480d990f6cf81314816f94d1fbb4d68233e42e8956300d74bca.png",
        "sha256": "3d47bbed9236d480d990f6cf81314816f94d1fbb4d68233e42e8956300d74bca"
      },
      {
        "path": "/data2/k6tk/79/7903bd34dfd959ec558cd4c04c4eb5a897623f894f44704bac11d39e15e2d379.png",
        "sha256": "7903bd34dfd959ec558cd4c04c4eb5a897623f894f44704bac11d39e15e2d379"
      },
      {
        "path": "/data2/k6tk/fb/fb7fabaca9b75bf364e0edd6d5dc33324081d3c102a0151c16e59dfc6c503f55.png",
        "sha256": "fb7fabaca9b75bf364e0edd6d5dc33324081d3c102a0151c16e59dfc6c503f55"
      },
      {
        "path": "/data2/k6tk/72/725719c33e8ec4e4411fc39740766997618c77879c249a345336da8dbc827a85.png",
        "sha256": "725719c33e8ec4e4411fc39740766997618c77879c249a345336da8dbc827a85"
      },
      {
        "path": "/data2/k6tk/80/806742c3b897b14b1014b18b305772aaa3de143257e4a0a4e6a70a7c8627bc03.png",
        "sha256": "806742c3b897b14b1014b18b305772aaa3de143257e4a0a4e6a70a7c8627bc03"
      },
      {
        "path": "/data2/k6tk/70/709d2e0a789815d7c035663199187a45f41203e38fe7a8b8d0022f43b0574562.png",
        "sha256": "709d2e0a789815d7c035663199187a45f41203e38fe7a8b8d0022f43b0574562"
      },
      {
        "path": "/data2/k6tk/e9/e9a8a589e2e66c91403365e2b5c645f704c6aefd0870acd7b770ba56708063c3.png",
        "sha256": "e9a8a589e2e66c91403365e2b5c645f704c6aefd0870acd7b770ba56708063c3"
      },
      {
        "path": "/data2/k6tk/3b/3b6a79879a7bde866abfeb3f66f3fc857755185a94f877fdb8e46019a4592713.png",
        "sha256": "3b6a79879a7bde866abfeb3f66f3fc857755185a94f877fdb8e46019a4592713"
      },
      {
        "path": "/data2/k6tk/c5/c5d4723b9ac89eb03957aef0ba3be4688300e1b2d9ebe7a25e0cb462c97aeaa5.png",
        "sha256": "c5d4723b9ac89eb03957aef0ba3be4688300e1b2d9ebe7a25e0cb462c97aeaa5"
      },
      {
        "path": "/data2/k6tk/ea/ea08a778182b9914961d769b2f0a71bbbba8f9f99b7473ef4767bd4d427737d5.png",
        "sha256": "ea08a778182b9914961d769b2f0a71bbbba8f9f99b7473ef4767bd4d427737d5"
      },
      {
        "path": "/data2/k6tk/c7/c7a22d41797b72034e62eb455d6f9bb1951a7e409956f75565d735d12ce56894.png",
        "sha256": "c7a22d41797b72034e62eb455d6f9bb1951a7e409956f75565d735d12ce56894"
      },
      {
        "path": "/data2/k6tk/0e/0e56cff17a30db4f9e7670c51aa0c0dda9cb406a60a18ea2e4e0ee320e62854f.png",
        "sha256": "0e56cff17a30db4f9e7670c51aa0c0dda9cb406a60a18ea2e4e0ee320e62854f"
      },
      {
        "path": "/data2/k6tk/cc/cc093b388ac582ba2cd36aa0b730a7fbbb437679a8f413308cbef12073db9158.png",
        "sha256": "cc093b388ac582ba2cd36aa0b730a7fbbb437679a8f413308cbef12073db9158"
      },
      {
        "path": "/data2/k6tk/ea/ea416bc4b10dc9da5dd98e4abd7fb852f6259f781253762ec8b3d7f9d416cae8.png",
        "sha256": "ea416bc4b10dc9da5dd98e4abd7fb852f6259f781253762ec8b3d7f9d416cae8"
      },
      {
        "path": "/data2/k6tk/d5/d5fec8ffcb422d31dbc3e8e22ab566e4e7357f24b98dc0a3a65e1a0110b04a84.png",
        "sha256": "d5fec8ffcb422d31dbc3e8e22ab566e4e7357f24b98dc0a3a65e1a0110b04a84"
      },
      {
        "path": "/data2/k6tk/0b/0b675853251bdfafef0bdc049d466ceb4cf694b810a05cad1de03878bc774c42.png",
        "sha256": "0b675853251bdfafef0bdc049d466ceb4cf694b810a05cad1de03878bc774c42"
      },
      {
        "path": "/data2/k6tk/e1/e19e1d6f6792aaa12c609e747cd1d7f188731cc6491b205a2cebb759c3a36261.png",
        "sha256": "e19e1d6f6792aaa12c609e747cd1d7f188731cc6491b205a2cebb759c3a36261"
      },
      {
        "path": "/data2/k6tk/92/92b52d0a43bd14d69a3ae740965dddcbbb6451e08eab267555fd98c018e6367b.png",
        "sha256": "92b52d0a43bd14d69a3ae740965dddcbbb6451e08eab267555fd98c018e6367b"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "While standing by the blinds and facing away from the hole puncher, decide whether the storage cabinet lies to your left or your right.",
    "timestamps": [
      0.0,
      3.816666666666667,
      7.633333333333334,
      11.45,
      15.283333333333333,
      19.1,
      22.916666666666668,
      26.75,
      30.566666666666666,
      34.38333333333333,
      38.21666666666667,
      42.03333333333333,
      45.85,
      49.68333333333333,
      53.5,
      57.31666666666667,
      61.15,
      64.96666666666667,
      68.78333333333333,
      72.61666666666666,
      76.43333333333334,
      80.25,
      84.08333333333333,
      87.9,
      91.71666666666667,
      95.55,
      99.36666666666666,
      103.18333333333334,
      107.01666666666667,
      110.83333333333333,
      114.65,
      118.48333333333333
    ],
    "total_num_frames": 7110
  },
  "target": "<think>\nStep 1: find the blinds and the hole puncher, then the storage cabinet.\nStep 2: standing at the blinds and facing the hole puncher, I find the storage cabinet to my left.\nStep 3: I face away from the hole puncher by making a half turn. Front and back swap, and left and right swap.\nSo I find the storage cabinet to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qeab492cfeb3b75d866f20a54",
  "paraphrase_template": "easy_side",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "fa196798a42e36d73bd96de8e246f62ffd48b358c50a70f07c7333fb7b88342b"
  },
  "candidate_id": "ground-b077f4035847c4d8a93dfc960e710b2982e8abf597b9e2af3d7dbfb7f2e6ed21",
  "label_row_keys": [
    "qeab492cfeb3b75d866f20a54-p1"
  ]
}
```

## 13. qf92f101c713027b601716c62_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qf92f101c713027b601716c62",
      "source_store_i": 33003,
      "source_row_sha256": "b07b96e11b7eb6540158b9d782eb5c1f874edc7d2c6a2d55a47e559ad6bc70ae",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 30,
        "end": 36,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf92f101c713027b601716c62_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vc4c39a23fee4",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      36,
      73,
      110,
      147,
      184,
      220,
      257,
      294,
      331,
      368,
      404,
      441,
      478,
      515,
      552,
      588,
      625,
      662,
      699,
      736,
      772,
      809,
      846,
      883,
      920,
      956,
      993,
      1030,
      1067,
      1104,
      1141
    ],
    "frames": [
      {
        "path": "/data2/k6tk/16/16e4579c642e87673648c081dd486bf08399b7bc7019d476e0d2e40f10489ded.png",
        "sha256": "16e4579c642e87673648c081dd486bf08399b7bc7019d476e0d2e40f10489ded"
      },
      {
        "path": "/data2/k6tk/6d/6da0a00bf75c8d4a9e12d190cb8da6ab7dce08fc8aca5a1c3d4cb4fceade1afe.png",
        "sha256": "6da0a00bf75c8d4a9e12d190cb8da6ab7dce08fc8aca5a1c3d4cb4fceade1afe"
      },
      {
        "path": "/data2/k6tk/dd/dd3a20f56cac085d52afde2c719b56772d983e41c7844b8fbfd981e676ec7118.png",
        "sha256": "dd3a20f56cac085d52afde2c719b56772d983e41c7844b8fbfd981e676ec7118"
      },
      {
        "path": "/data2/k6tk/f2/f201938a02487f9b26691ec91c0b3b078c0387518db88e1a2234f31d432e7469.png",
        "sha256": "f201938a02487f9b26691ec91c0b3b078c0387518db88e1a2234f31d432e7469"
      },
      {
        "path": "/data2/k6tk/f1/f1aebd0bb46a06ce0c3e40867744c818d6be0ce9dbbf5b1a769fa3c596488aa6.png",
        "sha256": "f1aebd0bb46a06ce0c3e40867744c818d6be0ce9dbbf5b1a769fa3c596488aa6"
      },
      {
        "path": "/data2/k6tk/0c/0c0499b52a7076a601d4ddd37d4f14d141949c0b298aa429e5d80d50d6e5828f.png",
        "sha256": "0c0499b52a7076a601d4ddd37d4f14d141949c0b298aa429e5d80d50d6e5828f"
      },
      {
        "path": "/data2/k6tk/5a/5afd02c390172e73a708d79489004b8bb8e542f77a29983a98e224b48a656583.png",
        "sha256": "5afd02c390172e73a708d79489004b8bb8e542f77a29983a98e224b48a656583"
      },
      {
        "path": "/data2/k6tk/75/7571d91d9d3ff689fc89f910d93508828453d969118f11dbaf78d7482a465334.png",
        "sha256": "7571d91d9d3ff689fc89f910d93508828453d969118f11dbaf78d7482a465334"
      },
      {
        "path": "/data2/k6tk/ac/ac7f06252d43bfaac363b36d0eab7d63723862da7a81318e96622b175aec5a63.png",
        "sha256": "ac7f06252d43bfaac363b36d0eab7d63723862da7a81318e96622b175aec5a63"
      },
      {
        "path": "/data2/k6tk/93/933c97bd1dbf21a733cac8069eb6b9366c0b2a2a9300257a4dc890b5408a6da9.png",
        "sha256": "933c97bd1dbf21a733cac8069eb6b9366c0b2a2a9300257a4dc890b5408a6da9"
      },
      {
        "path": "/data2/k6tk/b5/b54e6e94a947570d4796c9079ac3f4847979e309e368ab7cb2ade82b575e7f00.png",
        "sha256": "b54e6e94a947570d4796c9079ac3f4847979e309e368ab7cb2ade82b575e7f00"
      },
      {
        "path": "/data2/k6tk/34/343bad2136f5d26ed031fa74d47b42b6dfe16f60c7485afa657d8e88e7187d2b.png",
        "sha256": "343bad2136f5d26ed031fa74d47b42b6dfe16f60c7485afa657d8e88e7187d2b"
      },
      {
        "path": "/data2/k6tk/49/49e5a1319a0821f8b68d4a8499ab452e2264ac1add52ef8898333bfe93d20774.png",
        "sha256": "49e5a1319a0821f8b68d4a8499ab452e2264ac1add52ef8898333bfe93d20774"
      },
      {
        "path": "/data2/k6tk/e1/e11409d516b8cd9afd808795a92f0cb45872fc8103a4663e552b2483d1ce5119.png",
        "sha256": "e11409d516b8cd9afd808795a92f0cb45872fc8103a4663e552b2483d1ce5119"
      },
      {
        "path": "/data2/k6tk/8c/8cb49d8d21f014006ed668a14ddd1d3b11181912388160d093e7fda5c9b2d42c.png",
        "sha256": "8cb49d8d21f014006ed668a14ddd1d3b11181912388160d093e7fda5c9b2d42c"
      },
      {
        "path": "/data2/k6tk/54/5420518577d31c894c8ee583b736357fccc2f5f7f98c90bad4315f19e89752f4.png",
        "sha256": "5420518577d31c894c8ee583b736357fccc2f5f7f98c90bad4315f19e89752f4"
      },
      {
        "path": "/data2/k6tk/0e/0e83de04f1139c88f35301902e7efec6940ebf4ed32e9e5d92a8321214163be1.png",
        "sha256": "0e83de04f1139c88f35301902e7efec6940ebf4ed32e9e5d92a8321214163be1"
      },
      {
        "path": "/data2/k6tk/33/33162a0422595663dff1005aec4975dc2f8757d9d71dc987b042a83d2c022db7.png",
        "sha256": "33162a0422595663dff1005aec4975dc2f8757d9d71dc987b042a83d2c022db7"
      },
      {
        "path": "/data2/k6tk/7d/7dca031f0fe402d8978bff26e6f731da0bd3eaad534dab5e73db992276098398.png",
        "sha256": "7dca031f0fe402d8978bff26e6f731da0bd3eaad534dab5e73db992276098398"
      },
      {
        "path": "/data2/k6tk/f6/f6db7a715e84261e68b94d1e7f3cb26940dd43c54be77f9b3a87bc440c701a45.png",
        "sha256": "f6db7a715e84261e68b94d1e7f3cb26940dd43c54be77f9b3a87bc440c701a45"
      },
      {
        "path": "/data2/k6tk/4d/4d9f71c9b1fc2c063ef0e79447bb316e14ee03ce33dd6231e330b4f8dac37669.png",
        "sha256": "4d9f71c9b1fc2c063ef0e79447bb316e14ee03ce33dd6231e330b4f8dac37669"
      },
      {
        "path": "/data2/k6tk/83/8387d77474028d0d58067b596ca024d1e74f89153b093546c0f55efb470a7267.png",
        "sha256": "8387d77474028d0d58067b596ca024d1e74f89153b093546c0f55efb470a7267"
      },
      {
        "path": "/data2/k6tk/6b/6b5992851e6933cb4ef0ca54dc143f969cf9cff202c36f5ecac68355b44cdfa0.png",
        "sha256": "6b5992851e6933cb4ef0ca54dc143f969cf9cff202c36f5ecac68355b44cdfa0"
      },
      {
        "path": "/data2/k6tk/dd/dd2a2a7867ecfcb77c5238529b7e9a25840dd599e80065b3c782d309cd35ac73.png",
        "sha256": "dd2a2a7867ecfcb77c5238529b7e9a25840dd599e80065b3c782d309cd35ac73"
      },
      {
        "path": "/data2/k6tk/02/0208472d0b94a66c5a17b5edb0ec9760e660fe18fcd2f1d39441b9f4388dd2c4.png",
        "sha256": "0208472d0b94a66c5a17b5edb0ec9760e660fe18fcd2f1d39441b9f4388dd2c4"
      },
      {
        "path": "/data2/k6tk/d0/d048890232b467b8f65a53eba29ee2b6b466579d134533261071ec2f767f4813.png",
        "sha256": "d048890232b467b8f65a53eba29ee2b6b466579d134533261071ec2f767f4813"
      },
      {
        "path": "/data2/k6tk/5b/5b7127e8ee797e45671ea4188425f57f7b0209a69854d2653128854616461bd6.png",
        "sha256": "5b7127e8ee797e45671ea4188425f57f7b0209a69854d2653128854616461bd6"
      },
      {
        "path": "/data2/k6tk/dd/ddfda6efcf7670fe55e43edaaee058993523c633c7d8add4dcd22de4a4b1c0d8.png",
        "sha256": "ddfda6efcf7670fe55e43edaaee058993523c633c7d8add4dcd22de4a4b1c0d8"
      },
      {
        "path": "/data2/k6tk/6d/6d3a2aaa8a8c0b43d401550c4c482560055ba0cb229b1327c3233d470a155498.png",
        "sha256": "6d3a2aaa8a8c0b43d401550c4c482560055ba0cb229b1327c3233d470a155498"
      },
      {
        "path": "/data2/k6tk/16/160b1c8375f5fc9f87fdaa4a0cd905dc1d33661c10e8f45e95106daf795d1979.png",
        "sha256": "160b1c8375f5fc9f87fdaa4a0cd905dc1d33661c10e8f45e95106daf795d1979"
      },
      {
        "path": "/data2/k6tk/60/6020561f4e163133d4ffe12c0f1abbf6682d9007741229a9fc389724ff6f6d37.png",
        "sha256": "6020561f4e163133d4ffe12c0f1abbf6682d9007741229a9fc389724ff6f6d37"
      },
      {
        "path": "/data2/k6tk/dc/dce0aff978d234bcdf9c09cbb3dc258a9e8f11389d5f6d6fc8e492b8f82b4eb0.png",
        "sha256": "dce0aff978d234bcdf9c09cbb3dc258a9e8f11389d5f6d6fc8e492b8f82b4eb0"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "Standing beside the chair and facing away from the window, which side—left or right—is the closet located on?",
    "timestamps": [
      0.0,
      1.5,
      3.0416666666666665,
      4.583333333333333,
      6.125,
      7.666666666666667,
      9.166666666666666,
      10.708333333333334,
      12.25,
      13.791666666666666,
      15.333333333333334,
      16.833333333333332,
      18.375,
      19.916666666666668,
      21.458333333333332,
      23.0,
      24.5,
      26.041666666666668,
      27.583333333333332,
      29.125,
      30.666666666666668,
      32.166666666666664,
      33.708333333333336,
      35.25,
      36.791666666666664,
      38.333333333333336,
      39.833333333333336,
      41.375,
      42.916666666666664,
      44.458333333333336,
      46.0,
      47.541666666666664
    ],
    "total_num_frames": 1142
  },
  "target": "<think>\nStep 1: find the chair and the window, then the closet.\nStep 2: I find the closet to my left when I stand at the chair facing the window.\nStep 3: I face away from the window by making a half turn. Front and back swap, and left and right swap.\nSo I find the closet to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "7baa7e4ec60dfc932cf68356bca52184d25c03ac0ac00e3162bc6bb279ccd26d"
  },
  "candidate_id": "ground-628d5ec91f28fb443529c92aa9244f1e21294b21d7a0863568783483b57e10c9",
  "label_row_keys": [
    "qf92f101c713027b601716c62"
  ]
}
```

## 14. q74109521b2a37b8101fa757f_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q74109521b2a37b8101fa757f",
      "source_store_i": 9769,
      "source_row_sha256": "9a5d1af6ad4179db666f04213a3e7b9283f70c298e07e2be27608538cc2a9586",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 38,
        "end": 44,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q74109521b2a37b8101fa757f_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v9e32221af081",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      701,
      1403,
      2105,
      2806,
      3508,
      4210,
      4911,
      5613,
      6315,
      7016,
      7718,
      8420,
      9121,
      9823,
      10525,
      11226,
      11928,
      12630,
      13331,
      14033,
      14735,
      15436,
      16138,
      16840,
      17541,
      18243,
      18945,
      19646,
      20348,
      21050,
      21752
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e6/e69b32a6c23634bbee151b3b128755952f55a804f09901e74f1f825c91c1d883.png",
        "sha256": "e69b32a6c23634bbee151b3b128755952f55a804f09901e74f1f825c91c1d883"
      },
      {
        "path": "/data2/k6tk/4d/4da794dd665ee6cf5697ec5d47305bcaffe1dd11d3f7d8ed6a734be326ac3533.png",
        "sha256": "4da794dd665ee6cf5697ec5d47305bcaffe1dd11d3f7d8ed6a734be326ac3533"
      },
      {
        "path": "/data2/k6tk/bd/bd7cd9de31582723f7f49effdc6659485c54685a93a8c2895f6849fc5c0e236a.png",
        "sha256": "bd7cd9de31582723f7f49effdc6659485c54685a93a8c2895f6849fc5c0e236a"
      },
      {
        "path": "/data2/k6tk/5c/5c013516fad4f33a8e33f429b3b11b0884b794cb1680040fd69f79adbaea208f.png",
        "sha256": "5c013516fad4f33a8e33f429b3b11b0884b794cb1680040fd69f79adbaea208f"
      },
      {
        "path": "/data2/k6tk/46/4646e3c85be1dea98052b5dc034e749502e2a78252bc324bc78470cb845ecbb4.png",
        "sha256": "4646e3c85be1dea98052b5dc034e749502e2a78252bc324bc78470cb845ecbb4"
      },
      {
        "path": "/data2/k6tk/0e/0e9f1fbc00cdddb2d2fed413f68f89ba9b1b557b5e295cc916c26dee67901bf7.png",
        "sha256": "0e9f1fbc00cdddb2d2fed413f68f89ba9b1b557b5e295cc916c26dee67901bf7"
      },
      {
        "path": "/data2/k6tk/fc/fcd77e654069a798f0399d795134adeae347b9d43e0375f886baa63384a313d9.png",
        "sha256": "fcd77e654069a798f0399d795134adeae347b9d43e0375f886baa63384a313d9"
      },
      {
        "path": "/data2/k6tk/94/945fada1ddaf346109ed2b6f38136c3ad65e10b20e9e5a33de37a4182813f22f.png",
        "sha256": "945fada1ddaf346109ed2b6f38136c3ad65e10b20e9e5a33de37a4182813f22f"
      },
      {
        "path": "/data2/k6tk/24/24ff4f6d4dd80ec9eed0592380a5d573127a2f530e7cb59087df5a1196792098.png",
        "sha256": "24ff4f6d4dd80ec9eed0592380a5d573127a2f530e7cb59087df5a1196792098"
      },
      {
        "path": "/data2/k6tk/5f/5f6ce7e7e93de6878e0fcdac9acf037fd7e49f76a468feb5471c1e59fea855b8.png",
        "sha256": "5f6ce7e7e93de6878e0fcdac9acf037fd7e49f76a468feb5471c1e59fea855b8"
      },
      {
        "path": "/data2/k6tk/e3/e35621a92b1cb5282f0ede63b4fe0793029664cd6272e4925065bf43a298647e.png",
        "sha256": "e35621a92b1cb5282f0ede63b4fe0793029664cd6272e4925065bf43a298647e"
      },
      {
        "path": "/data2/k6tk/d3/d3db1842d0a11a0c0525d100390672f31df9ea377a591009a7726b6d80430332.png",
        "sha256": "d3db1842d0a11a0c0525d100390672f31df9ea377a591009a7726b6d80430332"
      },
      {
        "path": "/data2/k6tk/c7/c70febefcc84319e7be9524d735f3b7140916493ef8e53f7892abf26d79e6448.png",
        "sha256": "c70febefcc84319e7be9524d735f3b7140916493ef8e53f7892abf26d79e6448"
      },
      {
        "path": "/data2/k6tk/6e/6ed68677fa4d2924edb74025da3ac66447164b24c2d7c22280eab9fcbae0e131.png",
        "sha256": "6ed68677fa4d2924edb74025da3ac66447164b24c2d7c22280eab9fcbae0e131"
      },
      {
        "path": "/data2/k6tk/54/545a694f5e857529b7b61129256243fb52f604bec9778c2ad2439bfc90f865f8.png",
        "sha256": "545a694f5e857529b7b61129256243fb52f604bec9778c2ad2439bfc90f865f8"
      },
      {
        "path": "/data2/k6tk/82/82b9675edcf504da36c3c4af90c207e1f3ffd0ea7767e29e9bf2936944f824d0.png",
        "sha256": "82b9675edcf504da36c3c4af90c207e1f3ffd0ea7767e29e9bf2936944f824d0"
      },
      {
        "path": "/data2/k6tk/b4/b4d93a7a650aa2e00a661f5e8107678c2470b21f056174ab72c2630209e985bd.png",
        "sha256": "b4d93a7a650aa2e00a661f5e8107678c2470b21f056174ab72c2630209e985bd"
      },
      {
        "path": "/data2/k6tk/9e/9e7245dd0a6b05f9cd965bbbc99f1c0c33e321150840b7ec0cbac751497123f5.png",
        "sha256": "9e7245dd0a6b05f9cd965bbbc99f1c0c33e321150840b7ec0cbac751497123f5"
      },
      {
        "path": "/data2/k6tk/67/6768970fa585ff1d6000812bc4b4395f0afafbb0ecb93e545ab71ed95a8f8177.png",
        "sha256": "6768970fa585ff1d6000812bc4b4395f0afafbb0ecb93e545ab71ed95a8f8177"
      },
      {
        "path": "/data2/k6tk/f5/f5dd85c8a217d7cd838957df73c3f792d780de9dbd0a19f57cd7697cfc38994e.png",
        "sha256": "f5dd85c8a217d7cd838957df73c3f792d780de9dbd0a19f57cd7697cfc38994e"
      },
      {
        "path": "/data2/k6tk/6e/6ec316f17f7a776b32782dd88d8ba48db16dce23d274dd576254928bca70c96f.png",
        "sha256": "6ec316f17f7a776b32782dd88d8ba48db16dce23d274dd576254928bca70c96f"
      },
      {
        "path": "/data2/k6tk/30/302d6dfb322e8aaf1d70cab89aefc44aff03a10292c7fe01f7d703339dd31d26.png",
        "sha256": "302d6dfb322e8aaf1d70cab89aefc44aff03a10292c7fe01f7d703339dd31d26"
      },
      {
        "path": "/data2/k6tk/50/50f94476a942d98d64422f159611fcfc8b65e99d08081a3840fdfd9e06b06259.png",
        "sha256": "50f94476a942d98d64422f159611fcfc8b65e99d08081a3840fdfd9e06b06259"
      },
      {
        "path": "/data2/k6tk/20/20db1b91e32e04c6bbd2946bcdb1a5e0db1cefc4042c6151d6b1c9bd66a7606f.png",
        "sha256": "20db1b91e32e04c6bbd2946bcdb1a5e0db1cefc4042c6151d6b1c9bd66a7606f"
      },
      {
        "path": "/data2/k6tk/b2/b25a7516320e103d5d2361905f780d811765be5ca733a42f0f4cc85fd716f569.png",
        "sha256": "b25a7516320e103d5d2361905f780d811765be5ca733a42f0f4cc85fd716f569"
      },
      {
        "path": "/data2/k6tk/7d/7db9414f0b0263a17ae0cf1025a6c3741acf970f82cc0f3243eeebf5f22efc42.png",
        "sha256": "7db9414f0b0263a17ae0cf1025a6c3741acf970f82cc0f3243eeebf5f22efc42"
      },
      {
        "path": "/data2/k6tk/9a/9a98838e0cb869507679fd9665b3a68aa6391bc6eab3673a489ddf0d42207ba0.png",
        "sha256": "9a98838e0cb869507679fd9665b3a68aa6391bc6eab3673a489ddf0d42207ba0"
      },
      {
        "path": "/data2/k6tk/f4/f490765ab454aa34122bdbfcbeddc46e2c8b4991624a14337d0d9e4f03f83f2a.png",
        "sha256": "f490765ab454aa34122bdbfcbeddc46e2c8b4991624a14337d0d9e4f03f83f2a"
      },
      {
        "path": "/data2/k6tk/15/157cadb97a9c63e0249f10c8c8eac9672131a9d78daf817ef232039ff3a65410.png",
        "sha256": "157cadb97a9c63e0249f10c8c8eac9672131a9d78daf817ef232039ff3a65410"
      },
      {
        "path": "/data2/k6tk/2d/2dfad13e28aa217e22bf0908368e7b366ce911a1bbca207212ff25d6564f838b.png",
        "sha256": "2dfad13e28aa217e22bf0908368e7b366ce911a1bbca207212ff25d6564f838b"
      },
      {
        "path": "/data2/k6tk/b0/b0abec07322fbe4050311c1683186011de454be89400f7f7d1f8964dd6a9b5cb.png",
        "sha256": "b0abec07322fbe4050311c1683186011de454be89400f7f7d1f8964dd6a9b5cb"
      },
      {
        "path": "/data2/k6tk/85/852cb212401c0640a3e06d2afdd1cd07e4cad11f6760b2db82d7dbc84311b7f9.png",
        "sha256": "852cb212401c0640a3e06d2afdd1cd07e4cad11f6760b2db82d7dbc84311b7f9"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the air fryer and facing away from the bathroom rug, is the bathroom cabinet to the left or the right of the bathroom rug?",
    "timestamps": [
      0.0,
      11.683333333333334,
      23.383333333333333,
      35.083333333333336,
      46.766666666666666,
      58.46666666666667,
      70.16666666666667,
      81.85,
      93.55,
      105.25,
      116.93333333333334,
      128.63333333333333,
      140.33333333333334,
      152.01666666666668,
      163.71666666666667,
      175.41666666666666,
      187.1,
      198.8,
      210.5,
      222.18333333333334,
      233.88333333333333,
      245.58333333333334,
      257.26666666666665,
      268.96666666666664,
      280.6666666666667,
      292.35,
      304.05,
      315.75,
      327.43333333333334,
      339.1333333333333,
      350.8333333333333,
      362.53333333333336
    ],
    "total_num_frames": 21753
  },
  "target": "<think>\nStep 1: find the air fryer, the bathroom rug and the bathroom cabinet.\nStep 2: I stand at the air fryer facing the bathroom rug; I find the bathroom cabinet to my left.\nStep 3: I face away from the bathroom rug by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the bathroom cabinet to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "d17738c8e4b87b1346644a9545f13caeb9694b98ea3d78b0c3c935bdf57e4705"
  },
  "candidate_id": "ground-a3400da183f65136b8da24b23d437ccaa5f48b1176677d064b5ba44e353afdec",
  "label_row_keys": [
    "q74109521b2a37b8101fa757f"
  ]
}
```

## 15. q20073e0289ebc36a017e6d44_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q20073e0289ebc36a017e6d44",
      "source_store_i": 23796,
      "source_row_sha256": "3f2e4915805d03dceaf2b66341f8dcb9b26448d113f0170f2785be4b04220965",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 37,
        "end": 43,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q20073e0289ebc36a017e6d44_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd8f528555a1e",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      358,
      716,
      1074,
      1432,
      1790,
      2148,
      2506,
      2864,
      3222,
      3580,
      3938,
      4296,
      4654,
      5012,
      5370,
      5728,
      6086,
      6444,
      6802,
      7160,
      7518,
      7876,
      8234,
      8592,
      8950,
      9308,
      9666,
      10024,
      10382,
      10740,
      11099
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a3/a36b01b461050b5017627ee9c5e6863c455ddffb188fb9fda112186e0a624b80.png",
        "sha256": "a36b01b461050b5017627ee9c5e6863c455ddffb188fb9fda112186e0a624b80"
      },
      {
        "path": "/data2/k6tk/6f/6fe9aae7aa083cdf599994e9f4bf82fda86f63e2762e1e2f9bb3745412b8d00a.png",
        "sha256": "6fe9aae7aa083cdf599994e9f4bf82fda86f63e2762e1e2f9bb3745412b8d00a"
      },
      {
        "path": "/data2/k6tk/03/03c97a0d391b49a5574b2b8643f5c24318d2dbdb23c5d4d39408bf5a6212033e.png",
        "sha256": "03c97a0d391b49a5574b2b8643f5c24318d2dbdb23c5d4d39408bf5a6212033e"
      },
      {
        "path": "/data2/k6tk/09/091d0ecc7d2dccdb3bf8a7bdc09eb07441f34b7956c99d787defb24458cf91b6.png",
        "sha256": "091d0ecc7d2dccdb3bf8a7bdc09eb07441f34b7956c99d787defb24458cf91b6"
      },
      {
        "path": "/data2/k6tk/ca/ca6e423e54bdb40875f9db32ad7b11261c1e3b103a0aa750d5f87003cd8aa221.png",
        "sha256": "ca6e423e54bdb40875f9db32ad7b11261c1e3b103a0aa750d5f87003cd8aa221"
      },
      {
        "path": "/data2/k6tk/07/078f0f5ce07798a20ce94fb57d87e73680d5a2038d33e718ada20b1f02b395b7.png",
        "sha256": "078f0f5ce07798a20ce94fb57d87e73680d5a2038d33e718ada20b1f02b395b7"
      },
      {
        "path": "/data2/k6tk/a7/a7983e4b7c05cf3ce94c6c6e6e70deeffcf8ba2219d4991ea36f59a87cab7af6.png",
        "sha256": "a7983e4b7c05cf3ce94c6c6e6e70deeffcf8ba2219d4991ea36f59a87cab7af6"
      },
      {
        "path": "/data2/k6tk/93/93e79c063173ea30e8598980b1c789183150e8f54004b58208c632aef2310f8b.png",
        "sha256": "93e79c063173ea30e8598980b1c789183150e8f54004b58208c632aef2310f8b"
      },
      {
        "path": "/data2/k6tk/ab/ab092691ba9930570f958fb2ff62860425dbae88f6ad68a13523ebf686319b29.png",
        "sha256": "ab092691ba9930570f958fb2ff62860425dbae88f6ad68a13523ebf686319b29"
      },
      {
        "path": "/data2/k6tk/2b/2b6dd08152f72c56e1952de33319cc510e0c331c39a68fa46ac766f8d2fac8b8.png",
        "sha256": "2b6dd08152f72c56e1952de33319cc510e0c331c39a68fa46ac766f8d2fac8b8"
      },
      {
        "path": "/data2/k6tk/4b/4bc001e1191373827fcd8e1854688cb7f04f1fc87c2d569356b60d7ec7885c31.png",
        "sha256": "4bc001e1191373827fcd8e1854688cb7f04f1fc87c2d569356b60d7ec7885c31"
      },
      {
        "path": "/data2/k6tk/45/45735e29e33344d1643e097d67b6caf9b5eb50a6767d062d80d693d4fcb26391.png",
        "sha256": "45735e29e33344d1643e097d67b6caf9b5eb50a6767d062d80d693d4fcb26391"
      },
      {
        "path": "/data2/k6tk/95/95d596559e9fe99beed6ba0f6856595ba9734c98dd3c851d20dfe809003d0797.png",
        "sha256": "95d596559e9fe99beed6ba0f6856595ba9734c98dd3c851d20dfe809003d0797"
      },
      {
        "path": "/data2/k6tk/e4/e4c76b3f4db9b31a40342eb987be1d831a4449466b187acaa881de8896de4d13.png",
        "sha256": "e4c76b3f4db9b31a40342eb987be1d831a4449466b187acaa881de8896de4d13"
      },
      {
        "path": "/data2/k6tk/3e/3e82ef30fbe1683980e230c76d272c8acd6b2fe4f0fb1dd6d13120b55ea9166d.png",
        "sha256": "3e82ef30fbe1683980e230c76d272c8acd6b2fe4f0fb1dd6d13120b55ea9166d"
      },
      {
        "path": "/data2/k6tk/4e/4e4c0e8d3e7da718a5eca3e6ebd4ba08bebed5ed82854fbcfd9a2d374352ca8c.png",
        "sha256": "4e4c0e8d3e7da718a5eca3e6ebd4ba08bebed5ed82854fbcfd9a2d374352ca8c"
      },
      {
        "path": "/data2/k6tk/c0/c0431ed4085de8ac70ef4e7bbb7207631f696609778cbca4bbb3dd9259620973.png",
        "sha256": "c0431ed4085de8ac70ef4e7bbb7207631f696609778cbca4bbb3dd9259620973"
      },
      {
        "path": "/data2/k6tk/65/6520ff2bb1cef28bfffaa7f59582b2a3cf92293c233c6a0bf78ac7d0a4fdcbf2.png",
        "sha256": "6520ff2bb1cef28bfffaa7f59582b2a3cf92293c233c6a0bf78ac7d0a4fdcbf2"
      },
      {
        "path": "/data2/k6tk/57/573d41c5ac57d86c5964afd24283504f804f3f54872940ab7c68de725683a51d.png",
        "sha256": "573d41c5ac57d86c5964afd24283504f804f3f54872940ab7c68de725683a51d"
      },
      {
        "path": "/data2/k6tk/07/07bccf944c4331ca7748403345988e6db9da7b0b9e1e04622358e3c4fb7695d6.png",
        "sha256": "07bccf944c4331ca7748403345988e6db9da7b0b9e1e04622358e3c4fb7695d6"
      },
      {
        "path": "/data2/k6tk/77/7705987177bc28c282772caa354571325f4ab75171082d26f3fbc3baad918431.png",
        "sha256": "7705987177bc28c282772caa354571325f4ab75171082d26f3fbc3baad918431"
      },
      {
        "path": "/data2/k6tk/92/9242030b0cee88ba139dccdde58a9ebcaada8bb7de13e45b0f29fbba2df10712.png",
        "sha256": "9242030b0cee88ba139dccdde58a9ebcaada8bb7de13e45b0f29fbba2df10712"
      },
      {
        "path": "/data2/k6tk/ea/eab06c76faea482ef83c4f8c988d97e20c10ddb3a8c019f0c2c05448aada7571.png",
        "sha256": "eab06c76faea482ef83c4f8c988d97e20c10ddb3a8c019f0c2c05448aada7571"
      },
      {
        "path": "/data2/k6tk/bc/bc0eb7869566ab9067e3ff6ff9f284596cec08eb84b348995a714c0364c5bdc9.png",
        "sha256": "bc0eb7869566ab9067e3ff6ff9f284596cec08eb84b348995a714c0364c5bdc9"
      },
      {
        "path": "/data2/k6tk/46/4678a0809240608cad8fa1c859994c23a1cefa62dab5106f4fcdc554f0479b4f.png",
        "sha256": "4678a0809240608cad8fa1c859994c23a1cefa62dab5106f4fcdc554f0479b4f"
      },
      {
        "path": "/data2/k6tk/20/20b850a0d6431d1f6f9e5a0925b9ddeb75c6b56ca9a59044dea4a59670fe9959.png",
        "sha256": "20b850a0d6431d1f6f9e5a0925b9ddeb75c6b56ca9a59044dea4a59670fe9959"
      },
      {
        "path": "/data2/k6tk/6c/6c35b104205cf2abe07256e6787169089d6d8784e933cb557bd3d62cb5f186c8.png",
        "sha256": "6c35b104205cf2abe07256e6787169089d6d8784e933cb557bd3d62cb5f186c8"
      },
      {
        "path": "/data2/k6tk/b8/b8289cb8bd332474ed1d11ed18f057d7bed6fa3c693c116026a75129b5dc9c94.png",
        "sha256": "b8289cb8bd332474ed1d11ed18f057d7bed6fa3c693c116026a75129b5dc9c94"
      },
      {
        "path": "/data2/k6tk/7a/7aa1a64fa61cd19c0a7fb366440ff76233147aebbac99cd71832a914c7cbff34.png",
        "sha256": "7aa1a64fa61cd19c0a7fb366440ff76233147aebbac99cd71832a914c7cbff34"
      },
      {
        "path": "/data2/k6tk/df/df86870d6943529cd5172b2b115fab6fbd8b5669f2fab8201b00e665256c18f1.png",
        "sha256": "df86870d6943529cd5172b2b115fab6fbd8b5669f2fab8201b00e665256c18f1"
      },
      {
        "path": "/data2/k6tk/25/251f4e546d70dd7299e6c3457fd55cc5c42da983799f20b509c495a0e48754cb.png",
        "sha256": "251f4e546d70dd7299e6c3457fd55cc5c42da983799f20b509c495a0e48754cb"
      },
      {
        "path": "/data2/k6tk/3e/3e05dd79febb80bf56f8c2ec19a1b88d6953272bc3592032337a452deb0151ba.png",
        "sha256": "3e05dd79febb80bf56f8c2ec19a1b88d6953272bc3592032337a452deb0151ba"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the backpack and facing away from the blanket, is the mousepad to the left or the right of the blanket?",
    "timestamps": [
      0.0,
      5.966666666666667,
      11.933333333333334,
      17.9,
      23.866666666666667,
      29.833333333333332,
      35.8,
      41.766666666666666,
      47.733333333333334,
      53.7,
      59.666666666666664,
      65.63333333333334,
      71.6,
      77.56666666666666,
      83.53333333333333,
      89.5,
      95.46666666666667,
      101.43333333333334,
      107.4,
      113.36666666666666,
      119.33333333333333,
      125.3,
      131.26666666666668,
      137.23333333333332,
      143.2,
      149.16666666666666,
      155.13333333333333,
      161.1,
      167.06666666666666,
      173.03333333333333,
      179.0,
      184.98333333333332
    ],
    "total_num_frames": 11100
  },
  "target": "<think>\nStep 1: locate the mousepad, the backpack and the blanket.\nStep 2: I stand at the backpack facing the blanket; I find the mousepad to my left.\nStep 3: I face away from the blanket by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the mousepad to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "c0b97849de9bdd33c07694f35a3aa48571fe285bd96e176feeb28bad1740b43f"
  },
  "candidate_id": "ground-c22e7f5ee339334b38aae256e18450fa33b700e8f8b933b5657dee3de06b94bc",
  "label_row_keys": [
    "q20073e0289ebc36a017e6d44"
  ]
}
```

## 16. q567c47e8677ee3aa81c62f8b_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q567c47e8677ee3aa81c62f8b",
      "source_store_i": 2348,
      "source_row_sha256": "bc7344e95cc798918a43ec1c9c8dc4b863eefa9b616e6f87689db58687efab5b",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 30,
        "end": 44,
        "source_clause": "looking toward",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q567c47e8677ee3aa81c62f8b_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "ve1fa77c26b40",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      275,
      551,
      827,
      1103,
      1379,
      1655,
      1931,
      2207,
      2483,
      2759,
      3035,
      3311,
      3587,
      3863,
      4139,
      4414,
      4690,
      4966,
      5242,
      5518,
      5794,
      6070,
      6346,
      6622,
      6898,
      7174,
      7450,
      7726,
      8002,
      8278,
      8554
    ],
    "frames": [
      {
        "path": "/data2/k6tk/58/5806bae3fe5d64b8afbfa6fa961782977411b8877a68d598036fb4a20836ce22.png",
        "sha256": "5806bae3fe5d64b8afbfa6fa961782977411b8877a68d598036fb4a20836ce22"
      },
      {
        "path": "/data2/k6tk/de/deb5b615dd2ab651425db3c604b39d2229d71a0fce04e5aa0227a7435efc1118.png",
        "sha256": "deb5b615dd2ab651425db3c604b39d2229d71a0fce04e5aa0227a7435efc1118"
      },
      {
        "path": "/data2/k6tk/84/8491699f4fec3da63eff6582ca08fd17af306d1eb98046f16f6606e2bbe9b7e0.png",
        "sha256": "8491699f4fec3da63eff6582ca08fd17af306d1eb98046f16f6606e2bbe9b7e0"
      },
      {
        "path": "/data2/k6tk/4b/4b6531462dbc15bb875cec9c541c49a79314b715bfa82647c9729ef9fb5d42fe.png",
        "sha256": "4b6531462dbc15bb875cec9c541c49a79314b715bfa82647c9729ef9fb5d42fe"
      },
      {
        "path": "/data2/k6tk/8e/8e01efcab8262642e5e90e3c36b6d1b8e4a140550946b4b76f388ea660149846.png",
        "sha256": "8e01efcab8262642e5e90e3c36b6d1b8e4a140550946b4b76f388ea660149846"
      },
      {
        "path": "/data2/k6tk/7a/7a750779096b4b500782dd5f7cb6fa55fc95cc477a6b3d07aa5863654eb1a1cc.png",
        "sha256": "7a750779096b4b500782dd5f7cb6fa55fc95cc477a6b3d07aa5863654eb1a1cc"
      },
      {
        "path": "/data2/k6tk/1f/1f76f736a92a4c78ae72d20c6522173ace92e1a5b62322523c641367fd11de1f.png",
        "sha256": "1f76f736a92a4c78ae72d20c6522173ace92e1a5b62322523c641367fd11de1f"
      },
      {
        "path": "/data2/k6tk/3a/3a6cf9e61d34e4e6a7409cbe81aa80f2d67a1262e9b5312832a83d8a86af8738.png",
        "sha256": "3a6cf9e61d34e4e6a7409cbe81aa80f2d67a1262e9b5312832a83d8a86af8738"
      },
      {
        "path": "/data2/k6tk/eb/eb548104fc207c7a5e59d2df5afc3b80008a718ffff32e0c4ac4d1960df9a0dc.png",
        "sha256": "eb548104fc207c7a5e59d2df5afc3b80008a718ffff32e0c4ac4d1960df9a0dc"
      },
      {
        "path": "/data2/k6tk/74/747d6f523dfe1f356ee6a556c5a07af64997deab1801c3eaffd542399bbaff6b.png",
        "sha256": "747d6f523dfe1f356ee6a556c5a07af64997deab1801c3eaffd542399bbaff6b"
      },
      {
        "path": "/data2/k6tk/bd/bd83313f21f870acb0b4fb5f11ca409ab2be91b52a725f880dae614cf12e7f39.png",
        "sha256": "bd83313f21f870acb0b4fb5f11ca409ab2be91b52a725f880dae614cf12e7f39"
      },
      {
        "path": "/data2/k6tk/ac/acbea61f866dd04edca2995ee95a88f7981b1a4e3b846072b4fdd5b3f9e1b53b.png",
        "sha256": "acbea61f866dd04edca2995ee95a88f7981b1a4e3b846072b4fdd5b3f9e1b53b"
      },
      {
        "path": "/data2/k6tk/39/3917724b879ec8959f3d3102a55ceabdcc70ed4ab9ad353623e8f0ca6a31bea0.png",
        "sha256": "3917724b879ec8959f3d3102a55ceabdcc70ed4ab9ad353623e8f0ca6a31bea0"
      },
      {
        "path": "/data2/k6tk/b1/b15cc64fcc79d7065630a83a42fd3572ed5d7c7533d91c0d78c121e822877f2e.png",
        "sha256": "b15cc64fcc79d7065630a83a42fd3572ed5d7c7533d91c0d78c121e822877f2e"
      },
      {
        "path": "/data2/k6tk/21/21e45f2e6e1fa881ce9b06c1f6fadfb7490e08da6245f2a3f15a6ddd01e25f35.png",
        "sha256": "21e45f2e6e1fa881ce9b06c1f6fadfb7490e08da6245f2a3f15a6ddd01e25f35"
      },
      {
        "path": "/data2/k6tk/ef/ef1e225e1cf0f7b1d68e8f3fe2e12d466ab6095bd3fe686075024fbcabd6f013.png",
        "sha256": "ef1e225e1cf0f7b1d68e8f3fe2e12d466ab6095bd3fe686075024fbcabd6f013"
      },
      {
        "path": "/data2/k6tk/14/14d69719c5017b39b7857efc0a766ef956d11caedfb02267965ca3fdcdb88c6c.png",
        "sha256": "14d69719c5017b39b7857efc0a766ef956d11caedfb02267965ca3fdcdb88c6c"
      },
      {
        "path": "/data2/k6tk/1d/1d3fc4a5ab0adeb5cd79b00de804f411cc21de058ed1cc463f1f627f591a566c.png",
        "sha256": "1d3fc4a5ab0adeb5cd79b00de804f411cc21de058ed1cc463f1f627f591a566c"
      },
      {
        "path": "/data2/k6tk/dd/dddab7b0f3817fb056662680b7b485bad796f20f25d70f7c0328f61b244f0da1.png",
        "sha256": "dddab7b0f3817fb056662680b7b485bad796f20f25d70f7c0328f61b244f0da1"
      },
      {
        "path": "/data2/k6tk/dd/ddf56b38cc2c93d61db49d76a23e38b57364756acbb6920e8920e6721c8babb7.png",
        "sha256": "ddf56b38cc2c93d61db49d76a23e38b57364756acbb6920e8920e6721c8babb7"
      },
      {
        "path": "/data2/k6tk/e7/e7f0857a68efb867c9e08f16a3ba42519a546810d9d7fede5791302ac2921d05.png",
        "sha256": "e7f0857a68efb867c9e08f16a3ba42519a546810d9d7fede5791302ac2921d05"
      },
      {
        "path": "/data2/k6tk/49/49f8fc6acae773bc2e97ac0bcef3f5374bbc30775ee1151da7602ac1cdaf0a4e.png",
        "sha256": "49f8fc6acae773bc2e97ac0bcef3f5374bbc30775ee1151da7602ac1cdaf0a4e"
      },
      {
        "path": "/data2/k6tk/44/440fdfbbe2d0609cda2841141abd0a43095c1adde17b6a936d81a14c1c9b8453.png",
        "sha256": "440fdfbbe2d0609cda2841141abd0a43095c1adde17b6a936d81a14c1c9b8453"
      },
      {
        "path": "/data2/k6tk/60/60252becb268a4bb2e5e23142821977f249e6001df859ac2bcdc0eadcf4987df.png",
        "sha256": "60252becb268a4bb2e5e23142821977f249e6001df859ac2bcdc0eadcf4987df"
      },
      {
        "path": "/data2/k6tk/81/81844d93ef947f142e2a9c09acb328fa16ad35159c69a62497d7e212aa41a96c.png",
        "sha256": "81844d93ef947f142e2a9c09acb328fa16ad35159c69a62497d7e212aa41a96c"
      },
      {
        "path": "/data2/k6tk/ae/aee062bb6a301840540672794bf25d4e8076a69b867b68340af513ce5f79a1ec.png",
        "sha256": "aee062bb6a301840540672794bf25d4e8076a69b867b68340af513ce5f79a1ec"
      },
      {
        "path": "/data2/k6tk/68/68dc83f9e3fe685ebc553680cf57c6a8749098da565ba7a8169c31c7095ecb71.png",
        "sha256": "68dc83f9e3fe685ebc553680cf57c6a8749098da565ba7a8169c31c7095ecb71"
      },
      {
        "path": "/data2/k6tk/71/714c041180baddca98cdab34f6d4cc7c4cc5eabe009937e922ca10bbbbb82aa2.png",
        "sha256": "714c041180baddca98cdab34f6d4cc7c4cc5eabe009937e922ca10bbbbb82aa2"
      },
      {
        "path": "/data2/k6tk/62/6252243b29f06063095dc8246afc9d37be4c989707a01902c225f8f8c4993e5a.png",
        "sha256": "6252243b29f06063095dc8246afc9d37be4c989707a01902c225f8f8c4993e5a"
      },
      {
        "path": "/data2/k6tk/4f/4f3c3e7e0f9ca7d18ca072820335438f7a9aaa0cf52cff86dfe72a272a355662.png",
        "sha256": "4f3c3e7e0f9ca7d18ca072820335438f7a9aaa0cf52cff86dfe72a272a355662"
      },
      {
        "path": "/data2/k6tk/5c/5c0269d54495ecabdbf2e14d72a56a946cb4200e451bc03188503865725e978d.png",
        "sha256": "5c0269d54495ecabdbf2e14d72a56a946cb4200e451bc03188503865725e978d"
      },
      {
        "path": "/data2/k6tk/d4/d402901a580e082837ab02d5f1501db6d79bcd0b4f9b56294f1a3de56121974b.png",
        "sha256": "d402901a580e082837ab02d5f1501db6d79bcd0b4f9b56294f1a3de56121974b"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I stand near the keyboard, facing away from the whiteboard, is the paper bag on the whiteboard's left or right?",
    "timestamps": [
      0.0,
      4.583333333333333,
      9.183333333333334,
      13.783333333333333,
      18.383333333333333,
      22.983333333333334,
      27.583333333333332,
      32.18333333333333,
      36.78333333333333,
      41.38333333333333,
      45.983333333333334,
      50.583333333333336,
      55.18333333333333,
      59.78333333333333,
      64.38333333333334,
      68.98333333333333,
      73.56666666666666,
      78.16666666666667,
      82.76666666666667,
      87.36666666666666,
      91.96666666666667,
      96.56666666666666,
      101.16666666666667,
      105.76666666666667,
      110.36666666666666,
      114.96666666666667,
      119.56666666666666,
      124.16666666666667,
      128.76666666666668,
      133.36666666666667,
      137.96666666666667,
      142.56666666666666
    ],
    "total_num_frames": 8555
  },
  "target": "<think>\nStep 1: locate the paper bag, the keyboard and the whiteboard.\nStep 2: standing at the keyboard and facing the whiteboard, I find the paper bag to my left.\nStep 3: I face away from the whiteboard by making a half turn. Front and back swap, and left and right swap.\nSo I find the paper bag to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "4488d45accffdbe1730299c80f92cdc037d296040682f8ff9f136c114723729c"
  },
  "candidate_id": "ground-b4d836bfe411d1d46092b4e00cedea0d5cc99cb8aa93d09585109451ee5e4734",
  "label_row_keys": [
    "q567c47e8677ee3aa81c62f8b"
  ]
}
```

## 17. qa5fc1876eb4c13c8b5af02cc-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qa5fc1876eb4c13c8b5af02cc-p1",
      "source_store_i": 73578,
      "source_row_sha256": "a229b8b07a719cc4996e38558be2cfcd3f24ef3bdc66acf165d197b8735fc7a1",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 37,
        "end": 48,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qa5fc1876eb4c13c8b5af02cc-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v713bb7a0b7ab",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      213,
      427,
      641,
      855,
      1069,
      1283,
      1497,
      1710,
      1924,
      2138,
      2352,
      2566,
      2780,
      2994,
      3208,
      3421,
      3635,
      3849,
      4063,
      4277,
      4491,
      4705,
      4919,
      5132,
      5346,
      5560,
      5774,
      5988,
      6202,
      6416,
      6630
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c9/c96cd3897d7b41a1b22ca5e41665df457298621edb608857ea5e88b73e44f846.png",
        "sha256": "c96cd3897d7b41a1b22ca5e41665df457298621edb608857ea5e88b73e44f846"
      },
      {
        "path": "/data2/k6tk/bc/bc6d9e3f36a8e43ca3f23b0f470e64f5d20786671a2840b07c9640282c208702.png",
        "sha256": "bc6d9e3f36a8e43ca3f23b0f470e64f5d20786671a2840b07c9640282c208702"
      },
      {
        "path": "/data2/k6tk/26/26acc6d71ac730120c93e7d3780c05bd133b19cb34cb9dbdad16dedfab21cd12.png",
        "sha256": "26acc6d71ac730120c93e7d3780c05bd133b19cb34cb9dbdad16dedfab21cd12"
      },
      {
        "path": "/data2/k6tk/d0/d00e71dcc2c80cdcf7929747d2e7ca123a801db06efc860e3d72f5d5aed768c7.png",
        "sha256": "d00e71dcc2c80cdcf7929747d2e7ca123a801db06efc860e3d72f5d5aed768c7"
      },
      {
        "path": "/data2/k6tk/4b/4bfaa182f07b1631a321dd99eb90c4f9e9954c24ee390e07b088144ffb0610f9.png",
        "sha256": "4bfaa182f07b1631a321dd99eb90c4f9e9954c24ee390e07b088144ffb0610f9"
      },
      {
        "path": "/data2/k6tk/f8/f8cc57416bc8e940557320f6c40fc5d757eabfb478cb36137685a4c6dce86ca2.png",
        "sha256": "f8cc57416bc8e940557320f6c40fc5d757eabfb478cb36137685a4c6dce86ca2"
      },
      {
        "path": "/data2/k6tk/f9/f99cca741b9464ecc2a47a375b78495cc74f6eea13a432fbe29c3240dd5bcc1a.png",
        "sha256": "f99cca741b9464ecc2a47a375b78495cc74f6eea13a432fbe29c3240dd5bcc1a"
      },
      {
        "path": "/data2/k6tk/db/db92e7f9071e38c25e387873ac7ae8eff64702819eac3ad4f5559e3e9739b262.png",
        "sha256": "db92e7f9071e38c25e387873ac7ae8eff64702819eac3ad4f5559e3e9739b262"
      },
      {
        "path": "/data2/k6tk/ae/ae887291a268add0fc667bfea2eee71a53fa25a49a549175c0791c503718f7fc.png",
        "sha256": "ae887291a268add0fc667bfea2eee71a53fa25a49a549175c0791c503718f7fc"
      },
      {
        "path": "/data2/k6tk/09/0997adeb40104659bc99c887cee13dbc22d44ebd0282c32afb2438faecd0d5a4.png",
        "sha256": "0997adeb40104659bc99c887cee13dbc22d44ebd0282c32afb2438faecd0d5a4"
      },
      {
        "path": "/data2/k6tk/34/34778fa1af6cfcbcf4246c2441b911224800422c9d88d75d6e661578de1533fa.png",
        "sha256": "34778fa1af6cfcbcf4246c2441b911224800422c9d88d75d6e661578de1533fa"
      },
      {
        "path": "/data2/k6tk/9a/9af26072249c52ad0e4de52202a60dea8b3155a0bcef7ca626fa7ebf08bd6ed9.png",
        "sha256": "9af26072249c52ad0e4de52202a60dea8b3155a0bcef7ca626fa7ebf08bd6ed9"
      },
      {
        "path": "/data2/k6tk/0b/0baabbf5629814fa417321c2f0656c16175b0c33e8ceeb051ab8593d837502af.png",
        "sha256": "0baabbf5629814fa417321c2f0656c16175b0c33e8ceeb051ab8593d837502af"
      },
      {
        "path": "/data2/k6tk/5c/5cb98d731d906f29ba68a9af65f03b08013b4c346038df0d468fcac403801869.png",
        "sha256": "5cb98d731d906f29ba68a9af65f03b08013b4c346038df0d468fcac403801869"
      },
      {
        "path": "/data2/k6tk/db/db7f91154fa96d3ecebf3ec1c0696381fa8a1ac35215ac7f082df7ae650114ad.png",
        "sha256": "db7f91154fa96d3ecebf3ec1c0696381fa8a1ac35215ac7f082df7ae650114ad"
      },
      {
        "path": "/data2/k6tk/b1/b166d73eb16c4d5202e9308f7d82533903a2a946f5a8617b7b379b3421699f2c.png",
        "sha256": "b166d73eb16c4d5202e9308f7d82533903a2a946f5a8617b7b379b3421699f2c"
      },
      {
        "path": "/data2/k6tk/71/7197716129c1e23c2561e2cd6e4c3b3e1976572f696a9615036338a3706fe75a.png",
        "sha256": "7197716129c1e23c2561e2cd6e4c3b3e1976572f696a9615036338a3706fe75a"
      },
      {
        "path": "/data2/k6tk/71/71626ad1bc506722f732cc0c82122f5cea1a6328527b80b0df2e28c6bc002e33.png",
        "sha256": "71626ad1bc506722f732cc0c82122f5cea1a6328527b80b0df2e28c6bc002e33"
      },
      {
        "path": "/data2/k6tk/6f/6fdde5e9f8772ff42a7eaad43e71a056442c921cbde07fe9755502d4ac7e02db.png",
        "sha256": "6fdde5e9f8772ff42a7eaad43e71a056442c921cbde07fe9755502d4ac7e02db"
      },
      {
        "path": "/data2/k6tk/07/07061b218d57b9e2e6c3baccc5070af3733f3cb8bbe45b4442b24488bedf8cc6.png",
        "sha256": "07061b218d57b9e2e6c3baccc5070af3733f3cb8bbe45b4442b24488bedf8cc6"
      },
      {
        "path": "/data2/k6tk/13/1342dba544975a3a997d11b0c4fff64cdf9b7ce9401d4c63066f9b6589dc4e54.png",
        "sha256": "1342dba544975a3a997d11b0c4fff64cdf9b7ce9401d4c63066f9b6589dc4e54"
      },
      {
        "path": "/data2/k6tk/30/301621ac65e8812c80b407d40c9393e66f0df0647905510f26bdf25bce045f0e.png",
        "sha256": "301621ac65e8812c80b407d40c9393e66f0df0647905510f26bdf25bce045f0e"
      },
      {
        "path": "/data2/k6tk/5d/5d7c23ea05b3c21ddff9c94c5b2fe20683046347ca71761468ae7dc6c60f292b.png",
        "sha256": "5d7c23ea05b3c21ddff9c94c5b2fe20683046347ca71761468ae7dc6c60f292b"
      },
      {
        "path": "/data2/k6tk/dd/dd842a92b3cf8fe7d9eb5484b63bf8ff0d60be80b2f1f400b88548a1733233f8.png",
        "sha256": "dd842a92b3cf8fe7d9eb5484b63bf8ff0d60be80b2f1f400b88548a1733233f8"
      },
      {
        "path": "/data2/k6tk/63/63b89a0daaf41c31431ffb2eae719081e17c7f9499f13832e7dad806217038af.png",
        "sha256": "63b89a0daaf41c31431ffb2eae719081e17c7f9499f13832e7dad806217038af"
      },
      {
        "path": "/data2/k6tk/8f/8fe96a9f1ee83360ec1d5a3d04278a58f165fc15ffe42c36da6f13c3dcdbc77f.png",
        "sha256": "8fe96a9f1ee83360ec1d5a3d04278a58f165fc15ffe42c36da6f13c3dcdbc77f"
      },
      {
        "path": "/data2/k6tk/36/360b88c4640bfd75e935bfc826be0488b5c258c2f477113af8884aa8392fb0fe.png",
        "sha256": "360b88c4640bfd75e935bfc826be0488b5c258c2f477113af8884aa8392fb0fe"
      },
      {
        "path": "/data2/k6tk/4d/4dba7ccd1a8124ae15ec197d9ef114f87969e921d642c77eb9ac2aba1be5f383.png",
        "sha256": "4dba7ccd1a8124ae15ec197d9ef114f87969e921d642c77eb9ac2aba1be5f383"
      },
      {
        "path": "/data2/k6tk/32/327cabbbd62650c247b3417c61cd576b01139e308e722bd85929a05564647753.png",
        "sha256": "327cabbbd62650c247b3417c61cd576b01139e308e722bd85929a05564647753"
      },
      {
        "path": "/data2/k6tk/e3/e34ca760f3cd6aef4ac05043cf58bc7e2ec480cebd9ace4b607d3dab8cd7630a.png",
        "sha256": "e34ca760f3cd6aef4ac05043cf58bc7e2ec480cebd9ace4b607d3dab8cd7630a"
      },
      {
        "path": "/data2/k6tk/50/50f2e0c7976bac225b3029db37e18bf09f099632e6aff97e864f1669e405612c.png",
        "sha256": "50f2e0c7976bac225b3029db37e18bf09f099632e6aff97e864f1669e405612c"
      },
      {
        "path": "/data2/k6tk/04/043a83e1c9ca5c078e2df8f94e08d4dd7bc8df2b4b45383a060e865aa34581e3.png",
        "sha256": "043a83e1c9ca5c078e2df8f94e08d4dd7bc8df2b4b45383a060e865aa34581e3"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the backpack, face away from the bottle. Is the laptop to your left or right?",
    "timestamps": [
      0.0,
      3.55,
      7.116666666666666,
      10.683333333333334,
      14.25,
      17.816666666666666,
      21.383333333333333,
      24.95,
      28.5,
      32.06666666666667,
      35.63333333333333,
      39.2,
      42.766666666666666,
      46.333333333333336,
      49.9,
      53.46666666666667,
      57.016666666666666,
      60.583333333333336,
      64.15,
      67.71666666666667,
      71.28333333333333,
      74.85,
      78.41666666666667,
      81.98333333333333,
      85.53333333333333,
      89.1,
      92.66666666666667,
      96.23333333333333,
      99.8,
      103.36666666666666,
      106.93333333333334,
      110.5
    ],
    "total_num_frames": 6631
  },
  "target": "<think>\nStep 1: locate the laptop, the backpack and the bottle.\nStep 2: I find the laptop to my left when I stand at the backpack facing the bottle.\nStep 3: I face away from the bottle by making a half turn. Front and back swap, and left and right swap.\nSo I find the laptop to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qa5fc1876eb4c13c8b5af02cc",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "4b7eabea8eaeaae768e763fcbce655115f4750839aa4087760b0ea8816c85034"
  },
  "candidate_id": "ground-f53aa19f39134a95bc1fa99ddfd8d08d23c24222b530f7ee9f08f6c804147868",
  "label_row_keys": [
    "qa5fc1876eb4c13c8b5af02cc-p1"
  ]
}
```

## 18. q887011976b38d7fddc2175db_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q887011976b38d7fddc2175db",
      "source_store_i": 25471,
      "source_row_sha256": "71c91979751aa46c2663877ee65b6600b16a45ca858727a3c316c170ffb2d797",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 32,
        "end": 45,
        "source_clause": "facing toward",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q887011976b38d7fddc2175db_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vf2ab74ca9732",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      330,
      661,
      992,
      1323,
      1654,
      1985,
      2316,
      2646,
      2977,
      3308,
      3639,
      3970,
      4301,
      4632,
      4963,
      5293,
      5624,
      5955,
      6286,
      6617,
      6948,
      7279,
      7610,
      7940,
      8271,
      8602,
      8933,
      9264,
      9595,
      9926,
      10257
    ],
    "frames": [
      {
        "path": "/data2/k6tk/b3/b346489ed340ad12b6a8dd29309e642ae41a68bff341ac9d5f20d3fc60bb2c30.png",
        "sha256": "b346489ed340ad12b6a8dd29309e642ae41a68bff341ac9d5f20d3fc60bb2c30"
      },
      {
        "path": "/data2/k6tk/cf/cfab393f69e0fa353ae135db42620ff53db964ef874359df4a8f77d91da1ed31.png",
        "sha256": "cfab393f69e0fa353ae135db42620ff53db964ef874359df4a8f77d91da1ed31"
      },
      {
        "path": "/data2/k6tk/37/37d8cda556fc2c1f0d3977c6f8a7b45eba324701907c0eeb0c0a47ea07307b9f.png",
        "sha256": "37d8cda556fc2c1f0d3977c6f8a7b45eba324701907c0eeb0c0a47ea07307b9f"
      },
      {
        "path": "/data2/k6tk/b2/b262bd9a4afc629f40215479faebed11d430d8ab340159054d68278ab1eda4c8.png",
        "sha256": "b262bd9a4afc629f40215479faebed11d430d8ab340159054d68278ab1eda4c8"
      },
      {
        "path": "/data2/k6tk/e2/e282d435d1d0e16376ababbaca7e4dd98f266941944f0cb99ca2938eec50e4bc.png",
        "sha256": "e282d435d1d0e16376ababbaca7e4dd98f266941944f0cb99ca2938eec50e4bc"
      },
      {
        "path": "/data2/k6tk/ba/ba42c6dd906e0f4e430ef99f085034ac6661a0a4a1e9ff2dcaab8880284fda4d.png",
        "sha256": "ba42c6dd906e0f4e430ef99f085034ac6661a0a4a1e9ff2dcaab8880284fda4d"
      },
      {
        "path": "/data2/k6tk/b7/b7a65c133b95740c323b2109044534eeb0deb4c1a736d2b2292f4bb86766e98e.png",
        "sha256": "b7a65c133b95740c323b2109044534eeb0deb4c1a736d2b2292f4bb86766e98e"
      },
      {
        "path": "/data2/k6tk/9e/9e48676e17c3091621029650780ac85e9841419f2a98970de7f17162b6982be5.png",
        "sha256": "9e48676e17c3091621029650780ac85e9841419f2a98970de7f17162b6982be5"
      },
      {
        "path": "/data2/k6tk/bd/bd51ee094acff2564e6261ce883fa70d68457cbef206a99bfa71fd9ffb051062.png",
        "sha256": "bd51ee094acff2564e6261ce883fa70d68457cbef206a99bfa71fd9ffb051062"
      },
      {
        "path": "/data2/k6tk/91/910929bec2d023b3cf488c7ef5d42e79a5af56a3b808bce58a508d3c4a5ee791.png",
        "sha256": "910929bec2d023b3cf488c7ef5d42e79a5af56a3b808bce58a508d3c4a5ee791"
      },
      {
        "path": "/data2/k6tk/0d/0d79f7fdc662db54d2c29241d6bfef66f8edc05c50e24663c05eac377cc45902.png",
        "sha256": "0d79f7fdc662db54d2c29241d6bfef66f8edc05c50e24663c05eac377cc45902"
      },
      {
        "path": "/data2/k6tk/fc/fc6a25fe76e0833b9130fd7a7467c6fa092f38bc3f454b00c4fa81cc44cf2807.png",
        "sha256": "fc6a25fe76e0833b9130fd7a7467c6fa092f38bc3f454b00c4fa81cc44cf2807"
      },
      {
        "path": "/data2/k6tk/6f/6fa795357d884e8a72f2702f5c504c9a4717e3a912192c56a0f0c43ba54c33fe.png",
        "sha256": "6fa795357d884e8a72f2702f5c504c9a4717e3a912192c56a0f0c43ba54c33fe"
      },
      {
        "path": "/data2/k6tk/43/4362ad8cf9fe09927d5b6721b49a1297b02326c7bde08729261a991f7a9d5719.png",
        "sha256": "4362ad8cf9fe09927d5b6721b49a1297b02326c7bde08729261a991f7a9d5719"
      },
      {
        "path": "/data2/k6tk/06/06648bcf0bff1868131a3f58ee2fd8897b356c5263b54ff15731fed4f963a48e.png",
        "sha256": "06648bcf0bff1868131a3f58ee2fd8897b356c5263b54ff15731fed4f963a48e"
      },
      {
        "path": "/data2/k6tk/82/827acee7ac43bfdf55066ae15879b7337507da3c4ca6d624e38f29333804f52c.png",
        "sha256": "827acee7ac43bfdf55066ae15879b7337507da3c4ca6d624e38f29333804f52c"
      },
      {
        "path": "/data2/k6tk/08/0876e7ed598156c2af2bb6907425b11700562ce339f541ef951f19fe1a45dbc7.png",
        "sha256": "0876e7ed598156c2af2bb6907425b11700562ce339f541ef951f19fe1a45dbc7"
      },
      {
        "path": "/data2/k6tk/10/10d7c951c81fed54c5bf4e7b7a610468760bbd651a3f86222583b4f67d78bd80.png",
        "sha256": "10d7c951c81fed54c5bf4e7b7a610468760bbd651a3f86222583b4f67d78bd80"
      },
      {
        "path": "/data2/k6tk/36/36c77b8bee3da54074ab1e6d3b0ae3603b2030a7635a3bf87c4a1e32d96859a0.png",
        "sha256": "36c77b8bee3da54074ab1e6d3b0ae3603b2030a7635a3bf87c4a1e32d96859a0"
      },
      {
        "path": "/data2/k6tk/09/099edc68b7f95c4e68cd1ebee053fa905e6a742c8230f79d84bd3939ad930411.png",
        "sha256": "099edc68b7f95c4e68cd1ebee053fa905e6a742c8230f79d84bd3939ad930411"
      },
      {
        "path": "/data2/k6tk/8f/8f0b5b92448337549854a717cfae765d7e54dc8a975c0512b05e5e6f6b0f1c54.png",
        "sha256": "8f0b5b92448337549854a717cfae765d7e54dc8a975c0512b05e5e6f6b0f1c54"
      },
      {
        "path": "/data2/k6tk/3c/3c0bb9ff4e1e594321e551c458cd27e03de76efe3230542143f229bc49e686be.png",
        "sha256": "3c0bb9ff4e1e594321e551c458cd27e03de76efe3230542143f229bc49e686be"
      },
      {
        "path": "/data2/k6tk/38/38c55e134ebcb121a4e86a2b839ef7bba82a35dbfe1cdd749d4207c9eefda722.png",
        "sha256": "38c55e134ebcb121a4e86a2b839ef7bba82a35dbfe1cdd749d4207c9eefda722"
      },
      {
        "path": "/data2/k6tk/b2/b2306b46fb681092e513fdf54af8a103dbd302c90f1fe11f6b01258ffc7f375c.png",
        "sha256": "b2306b46fb681092e513fdf54af8a103dbd302c90f1fe11f6b01258ffc7f375c"
      },
      {
        "path": "/data2/k6tk/04/04a218f5f7ba5f9cd6aee5c8e9f806468a4e67915984b86f28f47b73a19b818a.png",
        "sha256": "04a218f5f7ba5f9cd6aee5c8e9f806468a4e67915984b86f28f47b73a19b818a"
      },
      {
        "path": "/data2/k6tk/c0/c04fc0ed2807a151d60e4fe622fce74a8f17046461d611c4a03e4875e83bcc99.png",
        "sha256": "c04fc0ed2807a151d60e4fe622fce74a8f17046461d611c4a03e4875e83bcc99"
      },
      {
        "path": "/data2/k6tk/95/95b05173b02a16d137bf847aae220a9e349dee9b682194efdd8885b10d408118.png",
        "sha256": "95b05173b02a16d137bf847aae220a9e349dee9b682194efdd8885b10d408118"
      },
      {
        "path": "/data2/k6tk/02/0230d5e01f50287734f90e02eb3d3d28a0423b2e88d28ea424fd25401889c3bc.png",
        "sha256": "0230d5e01f50287734f90e02eb3d3d28a0423b2e88d28ea424fd25401889c3bc"
      },
      {
        "path": "/data2/k6tk/bc/bcca2498fcd37e0aab3b89eb087bba746f976fed5e35e731202fa3db5f142acc.png",
        "sha256": "bcca2498fcd37e0aab3b89eb087bba746f976fed5e35e731202fa3db5f142acc"
      },
      {
        "path": "/data2/k6tk/02/02693680985ce7df97a024fbef2d9240e405c01e55c33ea4ab50342fe9e02410.png",
        "sha256": "02693680985ce7df97a024fbef2d9240e405c01e55c33ea4ab50342fe9e02410"
      },
      {
        "path": "/data2/k6tk/e8/e853c5c3e457e6127d1f100e3ae87f7f94efc3024e861de28b7a39fef1d5e159.png",
        "sha256": "e853c5c3e457e6127d1f100e3ae87f7f94efc3024e861de28b7a39fef1d5e159"
      },
      {
        "path": "/data2/k6tk/5d/5de616fc9fb2743a171c5ae20b7aafdea563bbd70c3e066087466e5f0298179c.png",
        "sha256": "5de616fc9fb2743a171c5ae20b7aafdea563bbd70c3e066087466e5f0298179c"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "Positioned by the trash can and facing away from the computer tower, on which side—left or right—is the bucket?",
    "timestamps": [
      0.0,
      5.5,
      11.016666666666667,
      16.533333333333335,
      22.05,
      27.566666666666666,
      33.083333333333336,
      38.6,
      44.1,
      49.61666666666667,
      55.13333333333333,
      60.65,
      66.16666666666667,
      71.68333333333334,
      77.2,
      82.71666666666667,
      88.21666666666667,
      93.73333333333333,
      99.25,
      104.76666666666667,
      110.28333333333333,
      115.8,
      121.31666666666666,
      126.83333333333333,
      132.33333333333334,
      137.85,
      143.36666666666667,
      148.88333333333333,
      154.4,
      159.91666666666666,
      165.43333333333334,
      170.95
    ],
    "total_num_frames": 10258
  },
  "target": "<think>\nStep 1: find the trash can, the computer tower and the bucket.\nStep 2: standing at the trash can and facing the computer tower, I find the bucket to my left.\nStep 3: I face away from the computer tower by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the bucket to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "764ab5a685482775798a74ec1ae0c3dbbcf79a340e154f6e661811b729f75d82"
  },
  "candidate_id": "ground-a149f90bfcbea6ba9116b197628904f1d989d90e4324aaf3c100a07e7ee912ac",
  "label_row_keys": [
    "q887011976b38d7fddc2175db"
  ]
}
```

## 19. q831016bfb1d02e2fe6edfae1-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q831016bfb1d02e2fe6edfae1-p1",
      "source_store_i": 67769,
      "source_row_sha256": "dc7ffd89853ff80252c9e0490a62d3327b8eb5f7e0390eb3eb3763e261210081",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 39,
        "end": 50,
        "source_clause": "look toward",
        "new_clause": "face away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q831016bfb1d02e2fe6edfae1-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v80004c9fb070",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      107,
      215,
      323,
      431,
      538,
      646,
      754,
      862,
      969,
      1077,
      1185,
      1293,
      1401,
      1508,
      1616,
      1724,
      1832,
      1939,
      2047,
      2155,
      2263,
      2371,
      2478,
      2586,
      2694,
      2802,
      2909,
      3017,
      3125,
      3233,
      3341
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ea/ea0351dd68e96873d64af319dbfe160c56b9844753f306cf5984bd71fd4d22a2.png",
        "sha256": "ea0351dd68e96873d64af319dbfe160c56b9844753f306cf5984bd71fd4d22a2"
      },
      {
        "path": "/data2/k6tk/20/2002702193ef12d7c4f95eed40b883d94062a239d5e4bd0897e1af5f2e9b3189.png",
        "sha256": "2002702193ef12d7c4f95eed40b883d94062a239d5e4bd0897e1af5f2e9b3189"
      },
      {
        "path": "/data2/k6tk/9a/9a439111d79670043ff5455d2251777267f9752ec82f4b96941ee7bcf00d5266.png",
        "sha256": "9a439111d79670043ff5455d2251777267f9752ec82f4b96941ee7bcf00d5266"
      },
      {
        "path": "/data2/k6tk/44/44d6ff1073e3ca8561a90cf3eaab8c48d423042e7f344ccb68f57b64b42076f6.png",
        "sha256": "44d6ff1073e3ca8561a90cf3eaab8c48d423042e7f344ccb68f57b64b42076f6"
      },
      {
        "path": "/data2/k6tk/e0/e097646116f39e6c7fef7d384437cc5087cfc19a747704ca3e6e3893f59d8b29.png",
        "sha256": "e097646116f39e6c7fef7d384437cc5087cfc19a747704ca3e6e3893f59d8b29"
      },
      {
        "path": "/data2/k6tk/e3/e3fd1dacdc48a281e07e93055a57c982862f46fb5ef90ac551894f30912acb3c.png",
        "sha256": "e3fd1dacdc48a281e07e93055a57c982862f46fb5ef90ac551894f30912acb3c"
      },
      {
        "path": "/data2/k6tk/32/32a1dd88bb4a6b5680caff2c7cd411f42ba08e2c4b0f5148506f9edc39e8cc9e.png",
        "sha256": "32a1dd88bb4a6b5680caff2c7cd411f42ba08e2c4b0f5148506f9edc39e8cc9e"
      },
      {
        "path": "/data2/k6tk/41/411c352eb5ed6576a5a209bcf9f629e2dcadcdfd40d2e0e5572de334a0dac95b.png",
        "sha256": "411c352eb5ed6576a5a209bcf9f629e2dcadcdfd40d2e0e5572de334a0dac95b"
      },
      {
        "path": "/data2/k6tk/0f/0f9da5b7f45f20b720787183c115bef056474ac3ed0a08e719d4dd9b27729cd3.png",
        "sha256": "0f9da5b7f45f20b720787183c115bef056474ac3ed0a08e719d4dd9b27729cd3"
      },
      {
        "path": "/data2/k6tk/a0/a084426dc04825d91ff46d2e066e198bb312c74258293ab11eb80ed30d159c7c.png",
        "sha256": "a084426dc04825d91ff46d2e066e198bb312c74258293ab11eb80ed30d159c7c"
      },
      {
        "path": "/data2/k6tk/e9/e9c89115fc499228eac3facd65baa20fd742ae6ae48418b6dcc16308927816bc.png",
        "sha256": "e9c89115fc499228eac3facd65baa20fd742ae6ae48418b6dcc16308927816bc"
      },
      {
        "path": "/data2/k6tk/3c/3cf5b9dc15325b6ed06fc2603c8397b4b46c0f2807e35fabc87ebbe23ec333df.png",
        "sha256": "3cf5b9dc15325b6ed06fc2603c8397b4b46c0f2807e35fabc87ebbe23ec333df"
      },
      {
        "path": "/data2/k6tk/41/41d7dd9ef449d7cdc52a6ed46a500e26b8381ee48e13febd14c2ce1454938396.png",
        "sha256": "41d7dd9ef449d7cdc52a6ed46a500e26b8381ee48e13febd14c2ce1454938396"
      },
      {
        "path": "/data2/k6tk/30/30a702afd8ca329a6faa91bead9e86c5eb3b7401fd98b0da0f72c3f5dd139633.png",
        "sha256": "30a702afd8ca329a6faa91bead9e86c5eb3b7401fd98b0da0f72c3f5dd139633"
      },
      {
        "path": "/data2/k6tk/19/198f340550a4f9c52372b56c47969a3853f7e17494634ab3d3f89adfa1d2edda.png",
        "sha256": "198f340550a4f9c52372b56c47969a3853f7e17494634ab3d3f89adfa1d2edda"
      },
      {
        "path": "/data2/k6tk/db/dbc1dc3ff59603d76df3de465544fdd1063c404719f375539ba2de5462cf38e4.png",
        "sha256": "dbc1dc3ff59603d76df3de465544fdd1063c404719f375539ba2de5462cf38e4"
      },
      {
        "path": "/data2/k6tk/af/aff513540210c3d7e93c9d062ecb841ab4e3502dbf5571f9c4b359b499e1686a.png",
        "sha256": "aff513540210c3d7e93c9d062ecb841ab4e3502dbf5571f9c4b359b499e1686a"
      },
      {
        "path": "/data2/k6tk/75/753c550cbcd421917c488539ada60ca49ceb44fcaa1ea297e455d658f6d15f56.png",
        "sha256": "753c550cbcd421917c488539ada60ca49ceb44fcaa1ea297e455d658f6d15f56"
      },
      {
        "path": "/data2/k6tk/38/38b5790f8b105971e728edd2b9170a84e6d38767d1bb9254ca3216e46915a6d5.png",
        "sha256": "38b5790f8b105971e728edd2b9170a84e6d38767d1bb9254ca3216e46915a6d5"
      },
      {
        "path": "/data2/k6tk/c6/c6573e3e1bdf03dfe455e52776a49061b0703c9068b1a1e412e85785cab50245.png",
        "sha256": "c6573e3e1bdf03dfe455e52776a49061b0703c9068b1a1e412e85785cab50245"
      },
      {
        "path": "/data2/k6tk/5d/5d362d6fa7696a3dc96314ec42e8591646a973adac322c2e2edce89197301c00.png",
        "sha256": "5d362d6fa7696a3dc96314ec42e8591646a973adac322c2e2edce89197301c00"
      },
      {
        "path": "/data2/k6tk/11/119a3659ea36c47538cac870c0d0038ec24741aad8cddd0b7c40b23fa974ba4f.png",
        "sha256": "119a3659ea36c47538cac870c0d0038ec24741aad8cddd0b7c40b23fa974ba4f"
      },
      {
        "path": "/data2/k6tk/ff/ffca682f6df6b29ae34ed13f00d6f58de9695d632a4e347221284a0853c99973.png",
        "sha256": "ffca682f6df6b29ae34ed13f00d6f58de9695d632a4e347221284a0853c99973"
      },
      {
        "path": "/data2/k6tk/02/025aa6c83c2c199994835ee42249b56098a447fa4399b67c904ae81bf701d34e.png",
        "sha256": "025aa6c83c2c199994835ee42249b56098a447fa4399b67c904ae81bf701d34e"
      },
      {
        "path": "/data2/k6tk/9f/9f688dcb02088743220a166fa83debf9c3f1d517dec97b25bd52eb7d12e5f30f.png",
        "sha256": "9f688dcb02088743220a166fa83debf9c3f1d517dec97b25bd52eb7d12e5f30f"
      },
      {
        "path": "/data2/k6tk/4f/4f74e611770b827f4a9339b098f2c3627496d9a2c47c1453d846f27a817c05e1.png",
        "sha256": "4f74e611770b827f4a9339b098f2c3627496d9a2c47c1453d846f27a817c05e1"
      },
      {
        "path": "/data2/k6tk/52/523a61da23fb126e928facf6db99a8a8afc021fd53e614027ee34032f8e84d4c.png",
        "sha256": "523a61da23fb126e928facf6db99a8a8afc021fd53e614027ee34032f8e84d4c"
      },
      {
        "path": "/data2/k6tk/b5/b57114a4087a6f9676c8a99d31c0275e2ce87bda0e7e2a016886c58041295c5c.png",
        "sha256": "b57114a4087a6f9676c8a99d31c0275e2ce87bda0e7e2a016886c58041295c5c"
      },
      {
        "path": "/data2/k6tk/85/850680a7ac3a9c1b97fa24c86544b8d43c9372114b05e4ceb3ffec5626841af8.png",
        "sha256": "850680a7ac3a9c1b97fa24c86544b8d43c9372114b05e4ceb3ffec5626841af8"
      },
      {
        "path": "/data2/k6tk/cd/cd5f20d05e051997f892b6a850fa980f26e347f4fc124375faedf196617ad4c1.png",
        "sha256": "cd5f20d05e051997f892b6a850fa980f26e347f4fc124375faedf196617ad4c1"
      },
      {
        "path": "/data2/k6tk/35/3525ad31b5bbb6ae933f01cb400c3a645722edc52f4b72b3e6571e14a0b4d3b6.png",
        "sha256": "3525ad31b5bbb6ae933f01cb400c3a645722edc52f4b72b3e6571e14a0b4d3b6"
      },
      {
        "path": "/data2/k6tk/14/14de7d9c14b717221f81083f3b8f06411b3c1aa2da4817a6af235b330036eb41.png",
        "sha256": "14de7d9c14b717221f81083f3b8f06411b3c1aa2da4817a6af235b330036eb41"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the table lamp, face away from the blanket. Is the ceiling light to your left or right?",
    "timestamps": [
      0.0,
      1.7833333333333334,
      3.5833333333333335,
      5.383333333333334,
      7.183333333333334,
      8.966666666666667,
      10.766666666666667,
      12.566666666666666,
      14.366666666666667,
      16.15,
      17.95,
      19.75,
      21.55,
      23.35,
      25.133333333333333,
      26.933333333333334,
      28.733333333333334,
      30.533333333333335,
      32.31666666666667,
      34.11666666666667,
      35.916666666666664,
      37.71666666666667,
      39.516666666666666,
      41.3,
      43.1,
      44.9,
      46.7,
      48.483333333333334,
      50.28333333333333,
      52.083333333333336,
      53.88333333333333,
      55.68333333333333
    ],
    "total_num_frames": 3342
  },
  "target": "<think>\nStep 1: locate the ceiling light, the table lamp and the blanket.\nStep 2: I find the ceiling light to my left when I stand at the table lamp facing the blanket.\nStep 3: I face away from the blanket by making a half turn. Front and back swap, and left and right swap.\nSo I find the ceiling light to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q831016bfb1d02e2fe6edfae1",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "d7369482f7eaada2c2329515cbe3f7ee40a38899a5f09dbeb0946bd4ce53fb89"
  },
  "candidate_id": "ground-1cf1abc356dfd2ba70544213ca3661220eae43f7e735a85a00aede6f6906cb43",
  "label_row_keys": [
    "q831016bfb1d02e2fe6edfae1-p1"
  ]
}
```

## 20. qff13c92c352e89df67b3a258_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qff13c92c352e89df67b3a258",
      "source_store_i": 9404,
      "source_row_sha256": "48d4782ed5bf2917a41235bc937c76b3869f89d502e09ee9f91e92093ae3d329",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 41,
        "end": 47,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qff13c92c352e89df67b3a258_sb_rowD7f_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v34764568c5da",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      150,
      300,
      450,
      601,
      751,
      901,
      1051,
      1202,
      1352,
      1502,
      1652,
      1803,
      1953,
      2103,
      2253,
      2404,
      2554,
      2704,
      2854,
      3005,
      3155,
      3305,
      3455,
      3606,
      3756,
      3906,
      4056,
      4207,
      4357,
      4507,
      4658
    ],
    "frames": [
      {
        "path": "/data2/k6tk/38/38fc5c2506f5f07649e3e5e57ebb6fddb7e9c2416fda9f86ff57d3f3b96e746b.png",
        "sha256": "38fc5c2506f5f07649e3e5e57ebb6fddb7e9c2416fda9f86ff57d3f3b96e746b"
      },
      {
        "path": "/data2/k6tk/c8/c8041d4cc0f7c745c5106bc34ed4278c592a6656367af74e1ef9e363426c1889.png",
        "sha256": "c8041d4cc0f7c745c5106bc34ed4278c592a6656367af74e1ef9e363426c1889"
      },
      {
        "path": "/data2/k6tk/48/4819f1625e882d8e549827e520b0b34169a3cd35a73f7f9d59bc4cb934c58c91.png",
        "sha256": "4819f1625e882d8e549827e520b0b34169a3cd35a73f7f9d59bc4cb934c58c91"
      },
      {
        "path": "/data2/k6tk/34/34c9d799250340d4c110df79bbe4d08210272b525059b2196b2e1b4d25f8c7dd.png",
        "sha256": "34c9d799250340d4c110df79bbe4d08210272b525059b2196b2e1b4d25f8c7dd"
      },
      {
        "path": "/data2/k6tk/f7/f78d72e95cb90959d92efb227af013d1128bf01338ea2e46070b684ed27681c2.png",
        "sha256": "f78d72e95cb90959d92efb227af013d1128bf01338ea2e46070b684ed27681c2"
      },
      {
        "path": "/data2/k6tk/fe/fee22fd889e9083b53d0dd50eae3c659b9294a1932f40c58a4d466a66206fc25.png",
        "sha256": "fee22fd889e9083b53d0dd50eae3c659b9294a1932f40c58a4d466a66206fc25"
      },
      {
        "path": "/data2/k6tk/b7/b743181b164dddc3ff552f27755bff0d25fcef75eb290ceabec258cfac463dbc.png",
        "sha256": "b743181b164dddc3ff552f27755bff0d25fcef75eb290ceabec258cfac463dbc"
      },
      {
        "path": "/data2/k6tk/24/24a21455856515b79fd2ecdfa520b71db2df3236124e53a02ed8502a4971dcc0.png",
        "sha256": "24a21455856515b79fd2ecdfa520b71db2df3236124e53a02ed8502a4971dcc0"
      },
      {
        "path": "/data2/k6tk/cb/cb31425b44778016b4e0e942d91feea080429cb3496fbf84a87ab39cdbd89c2b.png",
        "sha256": "cb31425b44778016b4e0e942d91feea080429cb3496fbf84a87ab39cdbd89c2b"
      },
      {
        "path": "/data2/k6tk/d4/d4a6d4f54b277987eee602ce9bad9de249f1b0d0e604a0310ce89c4e520f534e.png",
        "sha256": "d4a6d4f54b277987eee602ce9bad9de249f1b0d0e604a0310ce89c4e520f534e"
      },
      {
        "path": "/data2/k6tk/d4/d4ecc2204a1d83edc4f7824482ee0a0aeb9f5c4517cd77e1a5c177a0e63ff82d.png",
        "sha256": "d4ecc2204a1d83edc4f7824482ee0a0aeb9f5c4517cd77e1a5c177a0e63ff82d"
      },
      {
        "path": "/data2/k6tk/41/4174794e8644e04a7905e0744e48a7fadedec2d3dcb00730ad39b58a3d448dd5.png",
        "sha256": "4174794e8644e04a7905e0744e48a7fadedec2d3dcb00730ad39b58a3d448dd5"
      },
      {
        "path": "/data2/k6tk/2d/2d6ca78387acf7c6f8618f20add3a1d3ad71ed12dacb6706aabcab0c932b98f8.png",
        "sha256": "2d6ca78387acf7c6f8618f20add3a1d3ad71ed12dacb6706aabcab0c932b98f8"
      },
      {
        "path": "/data2/k6tk/3e/3e5759d16823c90c4e60dfe8311db84048672322d538d37229de2e2d91082f7c.png",
        "sha256": "3e5759d16823c90c4e60dfe8311db84048672322d538d37229de2e2d91082f7c"
      },
      {
        "path": "/data2/k6tk/f2/f24522a603c1e316b1f1e7dffa6fee76c8c10ca36d1f697814110973e9bfa4fa.png",
        "sha256": "f24522a603c1e316b1f1e7dffa6fee76c8c10ca36d1f697814110973e9bfa4fa"
      },
      {
        "path": "/data2/k6tk/c4/c47a0739dbd6172b617e8c211625c2f5cc9b1fcf56e391f52914e7b9c8bf0cf9.png",
        "sha256": "c47a0739dbd6172b617e8c211625c2f5cc9b1fcf56e391f52914e7b9c8bf0cf9"
      },
      {
        "path": "/data2/k6tk/f1/f19b526c56ac02ab0bf9dc52d300c0416e4e8bb884c150b8049d1d6dd26040bf.png",
        "sha256": "f19b526c56ac02ab0bf9dc52d300c0416e4e8bb884c150b8049d1d6dd26040bf"
      },
      {
        "path": "/data2/k6tk/07/0754c2e42d0e3aafea894d622171d540bbc1da03746b07ebdf1b713718a8ec76.png",
        "sha256": "0754c2e42d0e3aafea894d622171d540bbc1da03746b07ebdf1b713718a8ec76"
      },
      {
        "path": "/data2/k6tk/39/395a33991f419fb06e1d178f98a606672fcd03d3dd54d903c3e385807a97695d.png",
        "sha256": "395a33991f419fb06e1d178f98a606672fcd03d3dd54d903c3e385807a97695d"
      },
      {
        "path": "/data2/k6tk/87/87c1f54f7b9b05416864d8348fb15b0e298b3af3d2b7b316a582d3c414a5a74a.png",
        "sha256": "87c1f54f7b9b05416864d8348fb15b0e298b3af3d2b7b316a582d3c414a5a74a"
      },
      {
        "path": "/data2/k6tk/80/80863baa3d0727d825678f8974f043b90000cac9a5d995accf8ac3ff5f580cdb.png",
        "sha256": "80863baa3d0727d825678f8974f043b90000cac9a5d995accf8ac3ff5f580cdb"
      },
      {
        "path": "/data2/k6tk/a2/a20c24ee31eaf7e686e0a6d2ffe8e8a3edc3e9670340b464a84d3921431fac48.png",
        "sha256": "a20c24ee31eaf7e686e0a6d2ffe8e8a3edc3e9670340b464a84d3921431fac48"
      },
      {
        "path": "/data2/k6tk/55/55dde22fb92e0b1cddb8ca0f2f1756a142f9dd92c75ca0e083517b10f4b22b28.png",
        "sha256": "55dde22fb92e0b1cddb8ca0f2f1756a142f9dd92c75ca0e083517b10f4b22b28"
      },
      {
        "path": "/data2/k6tk/1c/1cdbda5a4b4d680884af0ecd4bf509f79c4797a302b6a3a320e44711b0a374d6.png",
        "sha256": "1cdbda5a4b4d680884af0ecd4bf509f79c4797a302b6a3a320e44711b0a374d6"
      },
      {
        "path": "/data2/k6tk/3f/3fa48de43474db20d3fa2ef2e63bb180c29a57da94d19f18b533b561f47624e5.png",
        "sha256": "3fa48de43474db20d3fa2ef2e63bb180c29a57da94d19f18b533b561f47624e5"
      },
      {
        "path": "/data2/k6tk/b5/b5009ce3dafdd0c1d75baf2e3aa557346262842b339635b185e0aa6009b4d6c2.png",
        "sha256": "b5009ce3dafdd0c1d75baf2e3aa557346262842b339635b185e0aa6009b4d6c2"
      },
      {
        "path": "/data2/k6tk/2f/2f4b598e880fdb9d6da915816a582e20e1490457b5f612de6e1bfa2af55c40b7.png",
        "sha256": "2f4b598e880fdb9d6da915816a582e20e1490457b5f612de6e1bfa2af55c40b7"
      },
      {
        "path": "/data2/k6tk/f4/f4e026e28c6fef9b96f4dbec384facc7a24061cfc9a227bfa13d893013a2e927.png",
        "sha256": "f4e026e28c6fef9b96f4dbec384facc7a24061cfc9a227bfa13d893013a2e927"
      },
      {
        "path": "/data2/k6tk/9a/9aa36c72ee3e903641441147606eebf76fb1794b0f7f3291220abf488d248d81.png",
        "sha256": "9aa36c72ee3e903641441147606eebf76fb1794b0f7f3291220abf488d248d81"
      },
      {
        "path": "/data2/k6tk/d5/d55aba8deef291870120460da8666813909d4c8fcdcad109895b347103c6319c.png",
        "sha256": "d55aba8deef291870120460da8666813909d4c8fcdcad109895b347103c6319c"
      },
      {
        "path": "/data2/k6tk/71/71ded389a8660f3df7a949ad8af879ee912ab297b2eebd54a97409a24d982eb5.png",
        "sha256": "71ded389a8660f3df7a949ad8af879ee912ab297b2eebd54a97409a24d982eb5"
      },
      {
        "path": "/data2/k6tk/94/9477d4984f0172c089f6509de9ac83b0a7fdc05d0934e5899e873ba2966a09bb.png",
        "sha256": "9477d4984f0172c089f6509de9ac83b0a7fdc05d0934e5899e873ba2966a09bb"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the air purifier and facing away from the clock, is the whiteboard to the left or the right of the clock?",
    "timestamps": [
      0.0,
      2.5,
      5.0,
      7.5,
      10.016666666666667,
      12.516666666666667,
      15.016666666666667,
      17.516666666666666,
      20.033333333333335,
      22.533333333333335,
      25.033333333333335,
      27.533333333333335,
      30.05,
      32.55,
      35.05,
      37.55,
      40.06666666666667,
      42.56666666666667,
      45.06666666666667,
      47.56666666666667,
      50.083333333333336,
      52.583333333333336,
      55.083333333333336,
      57.583333333333336,
      60.1,
      62.6,
      65.1,
      67.6,
      70.11666666666666,
      72.61666666666666,
      75.11666666666666,
      77.63333333333334
    ],
    "total_num_frames": 4659
  },
  "target": "<think>\nStep 1: locate the whiteboard, the air purifier and the clock.\nStep 2: standing at the air purifier and facing the clock, I find the whiteboard to my left.\nStep 3: I face away from the clock by making a half turn. Front and back swap, and left and right swap.\nSo I find the whiteboard to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "f9160f65cd633d4f7d3ee5284cfd18f38891d929bc455ec754e270018e965e51"
  },
  "candidate_id": "ground-0404638286dbac83b4268761cfd8ea3c60da51c55bf73157a05d9984cd00fc2b",
  "label_row_keys": [
    "qff13c92c352e89df67b3a258"
  ]
}
```

## 21. qf8719662b39d76c66c12e4d1-p1_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qf8719662b39d76c66c12e4d1-p1",
      "source_store_i": 70319,
      "source_row_sha256": "fd58ae84f9ba27210791e36b92bfc0328f2d23082ca877a7409b81c7c2b545be",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 28,
        "end": 38,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf8719662b39d76c66c12e4d1-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vd227d79f191a",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      257,
      514,
      771,
      1028,
      1285,
      1542,
      1799,
      2056,
      2313,
      2570,
      2828,
      3085,
      3342,
      3599,
      3856,
      4113,
      4370,
      4627,
      4884,
      5141,
      5399,
      5656,
      5913,
      6170,
      6427,
      6684,
      6941,
      7198,
      7455,
      7712,
      7970
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9a/9a6080852f89b2208c205cc6e59a494cc4f62fd3c4ff2b7991beb79957342d76.png",
        "sha256": "9a6080852f89b2208c205cc6e59a494cc4f62fd3c4ff2b7991beb79957342d76"
      },
      {
        "path": "/data2/k6tk/4a/4a8562ed480d44fcf709c353777ea40b5f4d4612167eb05c915329c21e52fc14.png",
        "sha256": "4a8562ed480d44fcf709c353777ea40b5f4d4612167eb05c915329c21e52fc14"
      },
      {
        "path": "/data2/k6tk/6f/6fbc30790cbee1fdf2d9c903a8fc68b140575d94a94b9e75812653dd8b6efa12.png",
        "sha256": "6fbc30790cbee1fdf2d9c903a8fc68b140575d94a94b9e75812653dd8b6efa12"
      },
      {
        "path": "/data2/k6tk/4e/4e726ceafc0f5225aaa552191a0ceadf0b1cce23a9ff9cc28907a417bd562769.png",
        "sha256": "4e726ceafc0f5225aaa552191a0ceadf0b1cce23a9ff9cc28907a417bd562769"
      },
      {
        "path": "/data2/k6tk/f3/f34c96db6dbba294f16c7d8d028c9e835b1509ba04779c7739efb91063e5c0f8.png",
        "sha256": "f34c96db6dbba294f16c7d8d028c9e835b1509ba04779c7739efb91063e5c0f8"
      },
      {
        "path": "/data2/k6tk/7c/7c829c9f1f3f839c56032a0ba8682de5b3c4792e8e66e16371f315c39077ca01.png",
        "sha256": "7c829c9f1f3f839c56032a0ba8682de5b3c4792e8e66e16371f315c39077ca01"
      },
      {
        "path": "/data2/k6tk/f9/f991bc9bb160b31082cf680a4e1fb8fd5832619716089f140e7ab0ae1f143096.png",
        "sha256": "f991bc9bb160b31082cf680a4e1fb8fd5832619716089f140e7ab0ae1f143096"
      },
      {
        "path": "/data2/k6tk/e3/e3d314f5286fb0ded4d1166a488809c908de04218374eebf4dc1ba3f3a5afeed.png",
        "sha256": "e3d314f5286fb0ded4d1166a488809c908de04218374eebf4dc1ba3f3a5afeed"
      },
      {
        "path": "/data2/k6tk/2e/2e7c5f7512cd0562467d0c45e94313c37000d2ae56dc9cb4fb5bcb983a2fe00e.png",
        "sha256": "2e7c5f7512cd0562467d0c45e94313c37000d2ae56dc9cb4fb5bcb983a2fe00e"
      },
      {
        "path": "/data2/k6tk/2f/2f62e97ecf0ca73d79d0e39d5cfdd5ec894435a5ca5f6c3d225218b237c02ecc.png",
        "sha256": "2f62e97ecf0ca73d79d0e39d5cfdd5ec894435a5ca5f6c3d225218b237c02ecc"
      },
      {
        "path": "/data2/k6tk/6f/6fcd5f72cc3c0f7c15d6f0c269e2ed4bdf80fb0251dad79f358366bdbcea84c8.png",
        "sha256": "6fcd5f72cc3c0f7c15d6f0c269e2ed4bdf80fb0251dad79f358366bdbcea84c8"
      },
      {
        "path": "/data2/k6tk/3e/3e03ed11e000fc19633599c839af8655b19b1470f33371c7dd76e941b3bb3915.png",
        "sha256": "3e03ed11e000fc19633599c839af8655b19b1470f33371c7dd76e941b3bb3915"
      },
      {
        "path": "/data2/k6tk/8d/8dc7d28d5cf34df3ac09c737c9d9381b4c9f0df82440a195d9481016b40f8f68.png",
        "sha256": "8dc7d28d5cf34df3ac09c737c9d9381b4c9f0df82440a195d9481016b40f8f68"
      },
      {
        "path": "/data2/k6tk/1e/1e08da5c2aa577b1a52a2789f759ce078a6db60eb82e83fb6a99aba4918e5358.png",
        "sha256": "1e08da5c2aa577b1a52a2789f759ce078a6db60eb82e83fb6a99aba4918e5358"
      },
      {
        "path": "/data2/k6tk/9c/9c4b60409984c7374e4e0f5ae072ddffbc431c99f7e085a9fa6d08618ddb4304.png",
        "sha256": "9c4b60409984c7374e4e0f5ae072ddffbc431c99f7e085a9fa6d08618ddb4304"
      },
      {
        "path": "/data2/k6tk/86/86c382da80be5094852e124ecea6228203a078fd4708b3ed5489d30c90b014cb.png",
        "sha256": "86c382da80be5094852e124ecea6228203a078fd4708b3ed5489d30c90b014cb"
      },
      {
        "path": "/data2/k6tk/b8/b88e22c78d492fb8611354eacc2858c9edd4609aad26795110500257f9a87d62.png",
        "sha256": "b88e22c78d492fb8611354eacc2858c9edd4609aad26795110500257f9a87d62"
      },
      {
        "path": "/data2/k6tk/64/64063bd8ed6ed387af9f674eaebd5b73812fc47c4285675f5426e8541f584505.png",
        "sha256": "64063bd8ed6ed387af9f674eaebd5b73812fc47c4285675f5426e8541f584505"
      },
      {
        "path": "/data2/k6tk/9f/9fee56c4c01a84d8ef53b529cd0e691dd89913aa9cb9d6ae5ec314e64eeaa7ba.png",
        "sha256": "9fee56c4c01a84d8ef53b529cd0e691dd89913aa9cb9d6ae5ec314e64eeaa7ba"
      },
      {
        "path": "/data2/k6tk/5d/5dfa6dc6f7548462fec5d221835c88458d07b577a75718a13c78ad32ccbc1eb9.png",
        "sha256": "5dfa6dc6f7548462fec5d221835c88458d07b577a75718a13c78ad32ccbc1eb9"
      },
      {
        "path": "/data2/k6tk/19/191990682e3a0f14ffd47786ca1ae995ad103f0c1f23ae9f8125a86e0664d219.png",
        "sha256": "191990682e3a0f14ffd47786ca1ae995ad103f0c1f23ae9f8125a86e0664d219"
      },
      {
        "path": "/data2/k6tk/de/ded78b05db7a46df6694ef2e9d2c33480cf9fe70e14623c3f01c383f3b70e034.png",
        "sha256": "ded78b05db7a46df6694ef2e9d2c33480cf9fe70e14623c3f01c383f3b70e034"
      },
      {
        "path": "/data2/k6tk/5d/5df91af307e0cee4d67d455d61028a557ff0236b0b2cb938db00ad122203aa26.png",
        "sha256": "5df91af307e0cee4d67d455d61028a557ff0236b0b2cb938db00ad122203aa26"
      },
      {
        "path": "/data2/k6tk/9b/9b2140ab7093aa4972dc84f97384195f0b77e88e1cd12ab6752dad8acf4fc1e7.png",
        "sha256": "9b2140ab7093aa4972dc84f97384195f0b77e88e1cd12ab6752dad8acf4fc1e7"
      },
      {
        "path": "/data2/k6tk/30/3087a5eb82f09a15552f36892c02343eb03ec5c8952292ef7ce0fc4905ad31da.png",
        "sha256": "3087a5eb82f09a15552f36892c02343eb03ec5c8952292ef7ce0fc4905ad31da"
      },
      {
        "path": "/data2/k6tk/26/26707c3595eac19eddc318099fda99fe176e02d783ebb26b5b5b11c4c7d283d5.png",
        "sha256": "26707c3595eac19eddc318099fda99fe176e02d783ebb26b5b5b11c4c7d283d5"
      },
      {
        "path": "/data2/k6tk/73/737f0b8856df32f0c116c803ad303226cc2e3fe466bbf6b8235bca66ceff5240.png",
        "sha256": "737f0b8856df32f0c116c803ad303226cc2e3fe466bbf6b8235bca66ceff5240"
      },
      {
        "path": "/data2/k6tk/a9/a9e6614922a6928c61e5ad05c3bd28b8a3c83fc4ab0cbb11a61993f23adfd4ab.png",
        "sha256": "a9e6614922a6928c61e5ad05c3bd28b8a3c83fc4ab0cbb11a61993f23adfd4ab"
      },
      {
        "path": "/data2/k6tk/34/34900519c18e08da73f6ff32944be0682084156eab9eb197b82a52406c187b48.png",
        "sha256": "34900519c18e08da73f6ff32944be0682084156eab9eb197b82a52406c187b48"
      },
      {
        "path": "/data2/k6tk/ee/eed4573d2f4f40194593772f5c870659ed1a37670056fc5ceb6008e033476746.png",
        "sha256": "eed4573d2f4f40194593772f5c870659ed1a37670056fc5ceb6008e033476746"
      },
      {
        "path": "/data2/k6tk/c7/c7b6a22de6b1c62bd2f298080cc5802ad0daac4ff26092449cab76f15d875944.png",
        "sha256": "c7b6a22de6b1c62bd2f298080cc5802ad0daac4ff26092449cab76f15d875944"
      },
      {
        "path": "/data2/k6tk/39/3914c6b21cdd8a0ac0f8aae57ce01fbe3c8d3133efd42a863c56d4f6684721ef.png",
        "sha256": "3914c6b21cdd8a0ac0f8aae57ce01fbe3c8d3133efd42a863c56d4f6684721ef"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-right",
      "C. back-right",
      "D. front-left"
    ],
    "question": "I stand by the beaker stand facing away from the binder. Where is the box relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      4.283333333333333,
      8.566666666666666,
      12.85,
      17.133333333333333,
      21.416666666666668,
      25.7,
      29.983333333333334,
      34.266666666666666,
      38.55,
      42.833333333333336,
      47.13333333333333,
      51.416666666666664,
      55.7,
      59.983333333333334,
      64.26666666666667,
      68.55,
      72.83333333333333,
      77.11666666666666,
      81.4,
      85.68333333333334,
      89.98333333333333,
      94.26666666666667,
      98.55,
      102.83333333333333,
      107.11666666666666,
      111.4,
      115.68333333333334,
      119.96666666666667,
      124.25,
      128.53333333333333,
      132.83333333333334
    ],
    "total_num_frames": 7971
  },
  "target": "<think>\nStep 1: find the beaker stand and the binder, then the box.\nStep 2: I find the box in front of me, on my right when I stand at the beaker stand facing the binder.\nStep 3: I face away from the binder by making a half turn. Front and back swap, and left and right swap.\nSo I find the box at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qf8719662b39d76c66c12e4d1",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "451ef6b4775ed8b802cf8d59aed3cd7130487ac54574a1cae57e303dbe248e2e"
  },
  "candidate_id": "ground-c0e06490cf67655ad72f472d600a70f26bf6ad1c0bfb17c291dbf498ea59bdf4",
  "label_row_keys": [
    "qf8719662b39d76c66c12e4d1-p1"
  ]
}
```

## 22. q4f0f4d3d5149a4c1c3256fb8_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q4f0f4d3d5149a4c1c3256fb8",
      "source_store_i": 19197,
      "source_row_sha256": "0901143d886af85175963e7dbc65a4e7b34b71e4cae5cf1444949b99cc4a4e4c",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "D",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 34,
        "end": 40,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q4f0f4d3d5149a4c1c3256fb8_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
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
      "A. back-left",
      "B. front-left",
      "C. back-right",
      "D. front-right"
    ],
    "question": "If I am standing by the chair and facing away from the paper, is the socket strip to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
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
  "target": "<think>\nStep 1: find the chair and the paper, then the socket strip.\nStep 2: I stand at the chair facing the paper; I find the socket strip in front of me, on my right.\nStep 3: I face away from the paper by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the socket strip at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "929da870da2c32de4be90821f02de1370d62d8e13cd6c7bcb2ac5db9d09b8192"
  },
  "candidate_id": "ground-496c50c6797f98505138bab1bbf8b697e05870e9d367f51edc9a5dc112b9f16b",
  "label_row_keys": [
    "q4f0f4d3d5149a4c1c3256fb8"
  ]
}
```

## 23. q71d8f3b2729e987dee05a43a-p1_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q71d8f3b2729e987dee05a43a-p1",
      "source_store_i": 76623,
      "source_row_sha256": "462c2329e3771b44fd677890b6563ee409fb67e6db8a0b6a64ccc1d6ea09d1af",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 21,
        "end": 31,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q71d8f3b2729e987dee05a43a-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v4f80cbc625a5",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      191,
      382,
      574,
      765,
      956,
      1148,
      1339,
      1530,
      1722,
      1913,
      2104,
      2296,
      2487,
      2678,
      2870,
      3061,
      3253,
      3444,
      3635,
      3827,
      4018,
      4209,
      4401,
      4592,
      4783,
      4975,
      5166,
      5357,
      5549,
      5740,
      5932
    ],
    "frames": [
      {
        "path": "/data2/k6tk/b3/b3f51533a9c3c63f6f5cbb49137c16ee741233bfd8c9cd84502f69fbb409e784.png",
        "sha256": "b3f51533a9c3c63f6f5cbb49137c16ee741233bfd8c9cd84502f69fbb409e784"
      },
      {
        "path": "/data2/k6tk/7b/7bf8fe26280282120febb9b4ce4ecdd1ddb65825d3fa817a5f39a0ef92f17820.png",
        "sha256": "7bf8fe26280282120febb9b4ce4ecdd1ddb65825d3fa817a5f39a0ef92f17820"
      },
      {
        "path": "/data2/k6tk/f8/f819338b2aa5e076b641698647ffd227691336f77dc4f963020e4ed871761417.png",
        "sha256": "f819338b2aa5e076b641698647ffd227691336f77dc4f963020e4ed871761417"
      },
      {
        "path": "/data2/k6tk/dd/dd20b0684dd7a0e64a4a00fe665250e1b977369aefd0b56adb16b4f40b4920ac.png",
        "sha256": "dd20b0684dd7a0e64a4a00fe665250e1b977369aefd0b56adb16b4f40b4920ac"
      },
      {
        "path": "/data2/k6tk/8a/8a19abf3cb3bf8c30f3c252a676a66ab55adcdb3101f3072def6256234fa5c54.png",
        "sha256": "8a19abf3cb3bf8c30f3c252a676a66ab55adcdb3101f3072def6256234fa5c54"
      },
      {
        "path": "/data2/k6tk/10/102f625dabd95fbf87df224ad69adba10f68b35ffe1c495ff73c20326f123abd.png",
        "sha256": "102f625dabd95fbf87df224ad69adba10f68b35ffe1c495ff73c20326f123abd"
      },
      {
        "path": "/data2/k6tk/0d/0d202300b4d3f592cefa3494f9f306c6331c4516a78d7b0d49cf7bad941daeeb.png",
        "sha256": "0d202300b4d3f592cefa3494f9f306c6331c4516a78d7b0d49cf7bad941daeeb"
      },
      {
        "path": "/data2/k6tk/a7/a7341cf387ef4d2c563e0e633016afcbc24ee2ba67f5e9f0f203be94c53787ad.png",
        "sha256": "a7341cf387ef4d2c563e0e633016afcbc24ee2ba67f5e9f0f203be94c53787ad"
      },
      {
        "path": "/data2/k6tk/dc/dcbff6fea14eba0a819ada9f74981b5be565035061bcc43376da45251b9f4b6d.png",
        "sha256": "dcbff6fea14eba0a819ada9f74981b5be565035061bcc43376da45251b9f4b6d"
      },
      {
        "path": "/data2/k6tk/ba/bacab4811d15656bd9d8c3698330ce91354ca8666561e2d5b9db4f924746d3df.png",
        "sha256": "bacab4811d15656bd9d8c3698330ce91354ca8666561e2d5b9db4f924746d3df"
      },
      {
        "path": "/data2/k6tk/dd/dd49927f80370f8a06c87f3bb721db36591ef2f91dc704f63f34eb4ec1adde3b.png",
        "sha256": "dd49927f80370f8a06c87f3bb721db36591ef2f91dc704f63f34eb4ec1adde3b"
      },
      {
        "path": "/data2/k6tk/1a/1a1eda8d2ade58f27c3fec8b5769413428ac1ac3e7c318b5c9f3ac2ae0e85935.png",
        "sha256": "1a1eda8d2ade58f27c3fec8b5769413428ac1ac3e7c318b5c9f3ac2ae0e85935"
      },
      {
        "path": "/data2/k6tk/ed/edd9eff4e456a8f41521ab58b330d7d46e5bbe1f9d3ab62d148e613220fbd381.png",
        "sha256": "edd9eff4e456a8f41521ab58b330d7d46e5bbe1f9d3ab62d148e613220fbd381"
      },
      {
        "path": "/data2/k6tk/db/db8c4d849c98b26ace8436ee42c76a283f5e9af873e1286bc6ea0dce6a257483.png",
        "sha256": "db8c4d849c98b26ace8436ee42c76a283f5e9af873e1286bc6ea0dce6a257483"
      },
      {
        "path": "/data2/k6tk/a9/a952a1f11bd8b358ca99b9fbcc8c29dcb4119f80ca58e8ef6e3f9df0f2897fca.png",
        "sha256": "a952a1f11bd8b358ca99b9fbcc8c29dcb4119f80ca58e8ef6e3f9df0f2897fca"
      },
      {
        "path": "/data2/k6tk/01/01cde98ebd123c77e6dce8a045dce039951ef196f5c66e064909b769d487522b.png",
        "sha256": "01cde98ebd123c77e6dce8a045dce039951ef196f5c66e064909b769d487522b"
      },
      {
        "path": "/data2/k6tk/94/942844b03276208cae72d3ba904e4bd9bf834ee830e0a30ec9d6090f76131672.png",
        "sha256": "942844b03276208cae72d3ba904e4bd9bf834ee830e0a30ec9d6090f76131672"
      },
      {
        "path": "/data2/k6tk/11/11066aece39d866d260c9ed6925536474ba76a3151519d3a3f91857b039b341c.png",
        "sha256": "11066aece39d866d260c9ed6925536474ba76a3151519d3a3f91857b039b341c"
      },
      {
        "path": "/data2/k6tk/23/23fe7c90934341ea3ccabe0903f73bb274a91690e569336e4977dcbcf17a93d1.png",
        "sha256": "23fe7c90934341ea3ccabe0903f73bb274a91690e569336e4977dcbcf17a93d1"
      },
      {
        "path": "/data2/k6tk/8a/8a065b3218cb1ebcbe43e3d22940d79210bc835c03a6d31469da27e23fd99d8e.png",
        "sha256": "8a065b3218cb1ebcbe43e3d22940d79210bc835c03a6d31469da27e23fd99d8e"
      },
      {
        "path": "/data2/k6tk/11/11e52be0aab5477b2dcfcc99edf25a7985900c01884ef0159ea76c8c6c0eef62.png",
        "sha256": "11e52be0aab5477b2dcfcc99edf25a7985900c01884ef0159ea76c8c6c0eef62"
      },
      {
        "path": "/data2/k6tk/9b/9bbcdc6550d3385609d870d59f720cc32bfffbc210adadd7edb6f5ea54444472.png",
        "sha256": "9bbcdc6550d3385609d870d59f720cc32bfffbc210adadd7edb6f5ea54444472"
      },
      {
        "path": "/data2/k6tk/53/53d886b47dc593e98199a2fc7753393f120561cec42255ceba4a42a759e65047.png",
        "sha256": "53d886b47dc593e98199a2fc7753393f120561cec42255ceba4a42a759e65047"
      },
      {
        "path": "/data2/k6tk/16/16a29aa9ffb261e0e9dd3ac5b896b3902988c1d7a19be80125e525db96a960ad.png",
        "sha256": "16a29aa9ffb261e0e9dd3ac5b896b3902988c1d7a19be80125e525db96a960ad"
      },
      {
        "path": "/data2/k6tk/59/591441da7f20f0c7cd4523c68fd57ef6dd37d53cded1a29eeb2ab57f5933924a.png",
        "sha256": "591441da7f20f0c7cd4523c68fd57ef6dd37d53cded1a29eeb2ab57f5933924a"
      },
      {
        "path": "/data2/k6tk/75/7570a1a3ba8788edfe872eccbade7dac67c461e44956d29ae2109fc2fdbdc002.png",
        "sha256": "7570a1a3ba8788edfe872eccbade7dac67c461e44956d29ae2109fc2fdbdc002"
      },
      {
        "path": "/data2/k6tk/31/31c44791d7ef2fdf28a509a8f754fcfc9b51b704ce1d5675c06e7c8c43d63996.png",
        "sha256": "31c44791d7ef2fdf28a509a8f754fcfc9b51b704ce1d5675c06e7c8c43d63996"
      },
      {
        "path": "/data2/k6tk/7a/7a96956cc6b8c0509fa8df9210e9afa19843d224784835d102f438ba0808f362.png",
        "sha256": "7a96956cc6b8c0509fa8df9210e9afa19843d224784835d102f438ba0808f362"
      },
      {
        "path": "/data2/k6tk/54/546d03300a76a22e33a34c33e5a1b39613fa0ae98a0f04b5456e330e97fe0cd3.png",
        "sha256": "546d03300a76a22e33a34c33e5a1b39613fa0ae98a0f04b5456e330e97fe0cd3"
      },
      {
        "path": "/data2/k6tk/f8/f8208553aa6e6f9c3a85e7905f5f746aff7a2207ccfd2ebc9d33d9d26c629361.png",
        "sha256": "f8208553aa6e6f9c3a85e7905f5f746aff7a2207ccfd2ebc9d33d9d26c629361"
      },
      {
        "path": "/data2/k6tk/33/3392b0317e5639195ad17a5d4058c6f997e58e9c3e124d569fe9f5b25354687e.png",
        "sha256": "3392b0317e5639195ad17a5d4058c6f997e58e9c3e124d569fe9f5b25354687e"
      },
      {
        "path": "/data2/k6tk/d2/d2cfa6fa7e4b1d30088b38543a1a8dd3d96fba12b7ea708acf441d277b2cdd07.png",
        "sha256": "d2cfa6fa7e4b1d30088b38543a1a8dd3d96fba12b7ea708acf441d277b2cdd07"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-right",
      "C. back-left",
      "D. front-left"
    ],
    "question": "I stand by the cable facing away from the coffee beans bag. Where is the dishwasher relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.183333333333333,
      6.366666666666666,
      9.566666666666666,
      12.75,
      15.933333333333334,
      19.133333333333333,
      22.316666666666666,
      25.5,
      28.7,
      31.883333333333333,
      35.06666666666667,
      38.266666666666666,
      41.45,
      44.63333333333333,
      47.833333333333336,
      51.016666666666666,
      54.21666666666667,
      57.4,
      60.583333333333336,
      63.78333333333333,
      66.96666666666667,
      70.15,
      73.35,
      76.53333333333333,
      79.71666666666667,
      82.91666666666667,
      86.1,
      89.28333333333333,
      92.48333333333333,
      95.66666666666667,
      98.86666666666666
    ],
    "total_num_frames": 5933
  },
  "target": "<think>\nStep 1: find the cable, the coffee beans bag and the dishwasher.\nStep 2: I find the dishwasher in front of me, on my right when I stand at the cable facing the coffee beans bag.\nStep 3: I face away from the coffee beans bag by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the dishwasher at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q71d8f3b2729e987dee05a43a",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "03893787b74895eb97d7733c967d7755434a7c0a489e4ed9bb4c323fb483f358"
  },
  "candidate_id": "ground-6b0b1ba5628ff5e922360f1204c4cc081b9ad01b63d76a8767dd888330d28fb9",
  "label_row_keys": [
    "q71d8f3b2729e987dee05a43a-p1"
  ]
}
```

## 24. qf702ecc4f1a5d7a95404f51d-p1_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qf702ecc4f1a5d7a95404f51d-p1",
      "source_store_i": 87496,
      "source_row_sha256": "96381b687b16553d0bd09b7ebf72321e740a0872bc083114da7e4ea5f4459aad",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "D",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 40,
        "end": 46,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf702ecc4f1a5d7a95404f51d-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v91669edf35b7",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      215,
      431,
      647,
      862,
      1078,
      1294,
      1510,
      1725,
      1941,
      2157,
      2373,
      2588,
      2804,
      3020,
      3236,
      3451,
      3667,
      3883,
      4099,
      4314,
      4530,
      4746,
      4962,
      5177,
      5393,
      5609,
      5825,
      6040,
      6256,
      6472,
      6688
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ce/ce9dd20c7b946197922878a6d486400171f8dfcd929d178a06ff8d40ea3119d2.png",
        "sha256": "ce9dd20c7b946197922878a6d486400171f8dfcd929d178a06ff8d40ea3119d2"
      },
      {
        "path": "/data2/k6tk/fd/fd07f76f2494df4759f6d443e47cacb9a96cd182d4ecfe058fed286f1cab9705.png",
        "sha256": "fd07f76f2494df4759f6d443e47cacb9a96cd182d4ecfe058fed286f1cab9705"
      },
      {
        "path": "/data2/k6tk/b4/b49e9aecbc068353d49154c2c3a741e56525d46a062871c00de7c3552de0349b.png",
        "sha256": "b49e9aecbc068353d49154c2c3a741e56525d46a062871c00de7c3552de0349b"
      },
      {
        "path": "/data2/k6tk/ef/efa7ecbac657a8aede4467774c1f5e22f5c02260e020cca3e2412c0ea2159896.png",
        "sha256": "efa7ecbac657a8aede4467774c1f5e22f5c02260e020cca3e2412c0ea2159896"
      },
      {
        "path": "/data2/k6tk/3c/3c61664202e0d2fd93ce52599c3e4ed84377a75f5eda61c317871e27c2262425.png",
        "sha256": "3c61664202e0d2fd93ce52599c3e4ed84377a75f5eda61c317871e27c2262425"
      },
      {
        "path": "/data2/k6tk/20/20a1ef3aee24923e8b99f42c72b7ee677ddea9f0d21fe7ca41e11f733d5f6b5f.png",
        "sha256": "20a1ef3aee24923e8b99f42c72b7ee677ddea9f0d21fe7ca41e11f733d5f6b5f"
      },
      {
        "path": "/data2/k6tk/cc/ccfbcf12bafcc276b041eec5481418e90c36e25ad8c32a79de0913abe59972ce.png",
        "sha256": "ccfbcf12bafcc276b041eec5481418e90c36e25ad8c32a79de0913abe59972ce"
      },
      {
        "path": "/data2/k6tk/ea/ea5b3d4ade3b8852eca680b902d6a7f2f916fc918d1dbe3d00765bfb69023ba5.png",
        "sha256": "ea5b3d4ade3b8852eca680b902d6a7f2f916fc918d1dbe3d00765bfb69023ba5"
      },
      {
        "path": "/data2/k6tk/aa/aa52cb3af5398cd37b595dfb2bf89ef34000f985134d7e824dd93717063092f2.png",
        "sha256": "aa52cb3af5398cd37b595dfb2bf89ef34000f985134d7e824dd93717063092f2"
      },
      {
        "path": "/data2/k6tk/cd/cd858dd539e96e081a46ecf649cd27077864ece9a9f032d1a87d98d879ad94ec.png",
        "sha256": "cd858dd539e96e081a46ecf649cd27077864ece9a9f032d1a87d98d879ad94ec"
      },
      {
        "path": "/data2/k6tk/21/21c155c783b1f2d484b051e6695786bfac64fcbf082edc4c8dead676d49901e2.png",
        "sha256": "21c155c783b1f2d484b051e6695786bfac64fcbf082edc4c8dead676d49901e2"
      },
      {
        "path": "/data2/k6tk/a9/a95cba53f37befe66cef033ea10a87c5248549ea1d2cd97c4215923d81e6eed6.png",
        "sha256": "a95cba53f37befe66cef033ea10a87c5248549ea1d2cd97c4215923d81e6eed6"
      },
      {
        "path": "/data2/k6tk/76/76b53ffc36732f75671995326d2b10154c30afb8a00cc9aa1bdacc54f250acff.png",
        "sha256": "76b53ffc36732f75671995326d2b10154c30afb8a00cc9aa1bdacc54f250acff"
      },
      {
        "path": "/data2/k6tk/2f/2f06b1568ed668584cad98e69fb41fb72ca7f8cd69658252a64de826196115b9.png",
        "sha256": "2f06b1568ed668584cad98e69fb41fb72ca7f8cd69658252a64de826196115b9"
      },
      {
        "path": "/data2/k6tk/0a/0a9dd06129b05c0929dab6b1658139c9752a3ea65176f7209ed40ea2d2123448.png",
        "sha256": "0a9dd06129b05c0929dab6b1658139c9752a3ea65176f7209ed40ea2d2123448"
      },
      {
        "path": "/data2/k6tk/be/be0938765cda084caff372236fbd18cbdbb35cb5059b4d156db6d72ce56ddd10.png",
        "sha256": "be0938765cda084caff372236fbd18cbdbb35cb5059b4d156db6d72ce56ddd10"
      },
      {
        "path": "/data2/k6tk/60/60af3350365e543afa2280687c32bfc0908b65674fc094335a8813d5e4b2440f.png",
        "sha256": "60af3350365e543afa2280687c32bfc0908b65674fc094335a8813d5e4b2440f"
      },
      {
        "path": "/data2/k6tk/45/45639908980bad0bd4cfed9c14df87557d84ea2b5b6798651f919e8f5ffe305e.png",
        "sha256": "45639908980bad0bd4cfed9c14df87557d84ea2b5b6798651f919e8f5ffe305e"
      },
      {
        "path": "/data2/k6tk/08/0832ada999ccf6845807aa103608124492059cfb29859c07904d78e53e938bd8.png",
        "sha256": "0832ada999ccf6845807aa103608124492059cfb29859c07904d78e53e938bd8"
      },
      {
        "path": "/data2/k6tk/69/69aa4110a2a487dc9d56b9e89904b674284af3fbbd04f7231de3a8374aa8f906.png",
        "sha256": "69aa4110a2a487dc9d56b9e89904b674284af3fbbd04f7231de3a8374aa8f906"
      },
      {
        "path": "/data2/k6tk/5d/5d12b26d9194aeef24a26ee460639bdcb58a00a9d4a77849bb9cd73e15666634.png",
        "sha256": "5d12b26d9194aeef24a26ee460639bdcb58a00a9d4a77849bb9cd73e15666634"
      },
      {
        "path": "/data2/k6tk/ed/ed2a0f6c6b75ae50d7a225610ea095888b74a0523246b51cf73c8ec9266211ec.png",
        "sha256": "ed2a0f6c6b75ae50d7a225610ea095888b74a0523246b51cf73c8ec9266211ec"
      },
      {
        "path": "/data2/k6tk/cf/cf83b689b9f46b9a7416808acd780d3e26a08da2212319e1be378bd1186655c5.png",
        "sha256": "cf83b689b9f46b9a7416808acd780d3e26a08da2212319e1be378bd1186655c5"
      },
      {
        "path": "/data2/k6tk/e6/e66e53a0f5d513b416ac34b5936a0887a3431c7cc2049fecdc517d96522054b5.png",
        "sha256": "e66e53a0f5d513b416ac34b5936a0887a3431c7cc2049fecdc517d96522054b5"
      },
      {
        "path": "/data2/k6tk/08/087be84a33e4273df6e4300fb8dc286f4e380965bfa5b9cca9a35c5d6a7384e4.png",
        "sha256": "087be84a33e4273df6e4300fb8dc286f4e380965bfa5b9cca9a35c5d6a7384e4"
      },
      {
        "path": "/data2/k6tk/06/0663b6f7402af824b4742db0bc0a434d643d959ee256a26ec0d4f5d0e96aa66d.png",
        "sha256": "0663b6f7402af824b4742db0bc0a434d643d959ee256a26ec0d4f5d0e96aa66d"
      },
      {
        "path": "/data2/k6tk/74/74fe52f09198cb4c937d1d4544cb66e721f21d6e7d0ede60d2432755ff90efd1.png",
        "sha256": "74fe52f09198cb4c937d1d4544cb66e721f21d6e7d0ede60d2432755ff90efd1"
      },
      {
        "path": "/data2/k6tk/fc/fc36a10263bbbfa4fbf323208e4fd38180be4d3aed985be79e7ca288eac5bd8f.png",
        "sha256": "fc36a10263bbbfa4fbf323208e4fd38180be4d3aed985be79e7ca288eac5bd8f"
      },
      {
        "path": "/data2/k6tk/35/35383682613cd4c14c3037d7c18225572112e6132cb74c68502263f56061d728.png",
        "sha256": "35383682613cd4c14c3037d7c18225572112e6132cb74c68502263f56061d728"
      },
      {
        "path": "/data2/k6tk/a6/a6164f67057ea74dfdfcc16a5f1d7d72d52fc01a87c7d6a7f33aa79e64123c11.png",
        "sha256": "a6164f67057ea74dfdfcc16a5f1d7d72d52fc01a87c7d6a7f33aa79e64123c11"
      },
      {
        "path": "/data2/k6tk/f8/f888d8c3238b4bfe5ac83f59fa01c459c13378ed613bcc5aa9a5c22207acba0c.png",
        "sha256": "f888d8c3238b4bfe5ac83f59fa01c459c13378ed613bcc5aa9a5c22207acba0c"
      },
      {
        "path": "/data2/k6tk/91/91ec6a757323c3b7d18f2a5f7df850df7efb8a35620d6bbeb2eb28a67d4b6262.png",
        "sha256": "91ec6a757323c3b7d18f2a5f7df850df7efb8a35620d6bbeb2eb28a67d4b6262"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. back-left",
      "D. front-right"
    ],
    "question": "If I am standing beside the cabinet and facing away from the key holder, which direction describes the light switches relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.5833333333333335,
      7.183333333333334,
      10.783333333333333,
      14.366666666666667,
      17.966666666666665,
      21.566666666666666,
      25.166666666666668,
      28.75,
      32.35,
      35.95,
      39.55,
      43.13333333333333,
      46.733333333333334,
      50.333333333333336,
      53.93333333333333,
      57.516666666666666,
      61.11666666666667,
      64.71666666666667,
      68.31666666666666,
      71.9,
      75.5,
      79.1,
      82.7,
      86.28333333333333,
      89.88333333333334,
      93.48333333333333,
      97.08333333333333,
      100.66666666666667,
      104.26666666666667,
      107.86666666666666,
      111.46666666666667
    ],
    "total_num_frames": 6689
  },
  "target": "<think>\nStep 1: find the cabinet, the key holder and the light switches.\nStep 2: I find the light switches in front of me, on my right when I stand at the cabinet facing the key holder.\nStep 3: I face away from the key holder by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the light switches at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qf702ecc4f1a5d7a95404f51d",
  "paraphrase_template": "hard_vsi",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "813ec5170670dfcd8a56fbcdde030a8285fb1241f8f2ea8ab388861b25d911cf"
  },
  "candidate_id": "ground-0661cc9da21fa02d1ae88773f02a0e644f72ab955f4dbb158b90f0c0fe3d6505",
  "label_row_keys": [
    "qf702ecc4f1a5d7a95404f51d-p1"
  ]
}
```

## 25. qa7a44f3ee64eeaab1209edd0_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qa7a44f3ee64eeaab1209edd0",
      "source_store_i": 10378,
      "source_row_sha256": "6c1c4ef0a73d6ed2dbd7761b06505168507561bc635db23b44aeb6636b6fb34a",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "D",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 35,
        "end": 41,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qa7a44f3ee64eeaab1209edd0_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v277aafcc9c03",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      370,
      741,
      1111,
      1482,
      1852,
      2223,
      2593,
      2964,
      3334,
      3705,
      4076,
      4446,
      4817,
      5187,
      5558,
      5928,
      6299,
      6669,
      7040,
      7410,
      7781,
      8152,
      8522,
      8893,
      9263,
      9634,
      10004,
      10375,
      10745,
      11116,
      11487
    ],
    "frames": [
      {
        "path": "/data2/k6tk/cb/cbc5806d12babe8695628c50f0fa42412e3f04af3df6ce3e3d232acd89028653.png",
        "sha256": "cbc5806d12babe8695628c50f0fa42412e3f04af3df6ce3e3d232acd89028653"
      },
      {
        "path": "/data2/k6tk/17/171e07ba4630c59fdb65468bd4fc3cfcaa25cbde0d8aab2c04848e559bf0ae4b.png",
        "sha256": "171e07ba4630c59fdb65468bd4fc3cfcaa25cbde0d8aab2c04848e559bf0ae4b"
      },
      {
        "path": "/data2/k6tk/45/450b79385644fdcce2b80dc429f4b1d7c72b17e8cbaad993e137503ea039c5e7.png",
        "sha256": "450b79385644fdcce2b80dc429f4b1d7c72b17e8cbaad993e137503ea039c5e7"
      },
      {
        "path": "/data2/k6tk/84/8409e632e1cb3bf425422dbfaf0913222e1fd4d1e7976c7d7bd637fc3ad84435.png",
        "sha256": "8409e632e1cb3bf425422dbfaf0913222e1fd4d1e7976c7d7bd637fc3ad84435"
      },
      {
        "path": "/data2/k6tk/43/43686c7aa00d28f17ff07783d4aff60ce2122bb81ca0c05a8aadf047997d936f.png",
        "sha256": "43686c7aa00d28f17ff07783d4aff60ce2122bb81ca0c05a8aadf047997d936f"
      },
      {
        "path": "/data2/k6tk/7c/7c3576915f495c27fbf6193d1ccf7e498ae3c6068226ee53c6ece9c9966e0610.png",
        "sha256": "7c3576915f495c27fbf6193d1ccf7e498ae3c6068226ee53c6ece9c9966e0610"
      },
      {
        "path": "/data2/k6tk/4a/4a8851a69fb84cb1b7e33bf5850013fa2ad005cbc7247ecab686c4686fb368a3.png",
        "sha256": "4a8851a69fb84cb1b7e33bf5850013fa2ad005cbc7247ecab686c4686fb368a3"
      },
      {
        "path": "/data2/k6tk/9a/9adeee82dac52677d1593e60de7f70db7debe140682127f569a3a2bc170d4602.png",
        "sha256": "9adeee82dac52677d1593e60de7f70db7debe140682127f569a3a2bc170d4602"
      },
      {
        "path": "/data2/k6tk/f5/f5a462864cb951d37ace38fa833c463bc3ff2b6381c8cb7c90a1f5aa27247bf5.png",
        "sha256": "f5a462864cb951d37ace38fa833c463bc3ff2b6381c8cb7c90a1f5aa27247bf5"
      },
      {
        "path": "/data2/k6tk/f2/f257121b386f65bfd3eded4f9d736c4d2728f3f6ebc60758fe769f0f20933d22.png",
        "sha256": "f257121b386f65bfd3eded4f9d736c4d2728f3f6ebc60758fe769f0f20933d22"
      },
      {
        "path": "/data2/k6tk/50/50c339216d55d8be4ec517c7e7955e853e9cd210922031cf9151388a93603144.png",
        "sha256": "50c339216d55d8be4ec517c7e7955e853e9cd210922031cf9151388a93603144"
      },
      {
        "path": "/data2/k6tk/08/088106eab15f0d5f30658574592444746277cd2b79025ff3c2406293db2cb8b9.png",
        "sha256": "088106eab15f0d5f30658574592444746277cd2b79025ff3c2406293db2cb8b9"
      },
      {
        "path": "/data2/k6tk/da/da2ab93b9c4b33f95a894b45eee416223f619275ff3b7e6e036bfd4f867dcc13.png",
        "sha256": "da2ab93b9c4b33f95a894b45eee416223f619275ff3b7e6e036bfd4f867dcc13"
      },
      {
        "path": "/data2/k6tk/a4/a404389ef42ef433959597c1f1c57798205f4ba2e8af5fbd4346528e933e27c3.png",
        "sha256": "a404389ef42ef433959597c1f1c57798205f4ba2e8af5fbd4346528e933e27c3"
      },
      {
        "path": "/data2/k6tk/e7/e7a6b3e5c2bcb8dc11da45053ab026a5620bea4e4cebe5d8000fd2a332862a1c.png",
        "sha256": "e7a6b3e5c2bcb8dc11da45053ab026a5620bea4e4cebe5d8000fd2a332862a1c"
      },
      {
        "path": "/data2/k6tk/1f/1f17f4b1af3eaac51efa4c60e819b0091dc0dbac81473b29e39ccc71f66deace.png",
        "sha256": "1f17f4b1af3eaac51efa4c60e819b0091dc0dbac81473b29e39ccc71f66deace"
      },
      {
        "path": "/data2/k6tk/23/230d8d38cba978d8b61e25e045c031ce9c51ce706158208cea1e4e6414c54627.png",
        "sha256": "230d8d38cba978d8b61e25e045c031ce9c51ce706158208cea1e4e6414c54627"
      },
      {
        "path": "/data2/k6tk/b4/b4f08142668d3a2934b1949ed8e3e44ebc4b5d9332d6add4cca32a78594cd149.png",
        "sha256": "b4f08142668d3a2934b1949ed8e3e44ebc4b5d9332d6add4cca32a78594cd149"
      },
      {
        "path": "/data2/k6tk/bb/bbff07cdc0181bd494738487f79c4d30f83a7135112a9e7398920db8ff6886f8.png",
        "sha256": "bbff07cdc0181bd494738487f79c4d30f83a7135112a9e7398920db8ff6886f8"
      },
      {
        "path": "/data2/k6tk/d4/d4a48a5593c7364e9ac3d16f8bd411f47e0d995504f1b426c0a59de18e681aaa.png",
        "sha256": "d4a48a5593c7364e9ac3d16f8bd411f47e0d995504f1b426c0a59de18e681aaa"
      },
      {
        "path": "/data2/k6tk/00/00e844d03b199afd554abea41600bafd03b63260de38f5f71ca43a564c3936fb.png",
        "sha256": "00e844d03b199afd554abea41600bafd03b63260de38f5f71ca43a564c3936fb"
      },
      {
        "path": "/data2/k6tk/48/480b87cd4085b9ed3af4301fddaa517e6033a5e5804f11cdc7d1c0fb20da1be6.png",
        "sha256": "480b87cd4085b9ed3af4301fddaa517e6033a5e5804f11cdc7d1c0fb20da1be6"
      },
      {
        "path": "/data2/k6tk/7c/7c4a9da776e3223bac05fd9ec53b2dd9c3cf7886c65a3c84ba3ea20ad29fcc53.png",
        "sha256": "7c4a9da776e3223bac05fd9ec53b2dd9c3cf7886c65a3c84ba3ea20ad29fcc53"
      },
      {
        "path": "/data2/k6tk/8e/8ed11879d3827850dc1f3c7c58fc79c7bc87bc2ee1e7cbdad94db70c6a4b064f.png",
        "sha256": "8ed11879d3827850dc1f3c7c58fc79c7bc87bc2ee1e7cbdad94db70c6a4b064f"
      },
      {
        "path": "/data2/k6tk/37/37abb58e19eef412f0bb065fb82de369b6f538825dc9752a12e30bec7701771c.png",
        "sha256": "37abb58e19eef412f0bb065fb82de369b6f538825dc9752a12e30bec7701771c"
      },
      {
        "path": "/data2/k6tk/06/061f803dd5a6fa3d32c8a70cb061d6a59f681d20d40abdc03d5f64e3002ead8f.png",
        "sha256": "061f803dd5a6fa3d32c8a70cb061d6a59f681d20d40abdc03d5f64e3002ead8f"
      },
      {
        "path": "/data2/k6tk/17/17f38e1af79e959acd98870558dc5433afbcf88e964324c10524d5408ff2efbc.png",
        "sha256": "17f38e1af79e959acd98870558dc5433afbcf88e964324c10524d5408ff2efbc"
      },
      {
        "path": "/data2/k6tk/75/75ec4ca93df0ef52b4c80518792ac68cad329c053fa9de32dfffb5b2fa92fed7.png",
        "sha256": "75ec4ca93df0ef52b4c80518792ac68cad329c053fa9de32dfffb5b2fa92fed7"
      },
      {
        "path": "/data2/k6tk/e3/e377ec152c57845d655251a33db310b4c154e422b5db65d2d62d02620eff2540.png",
        "sha256": "e377ec152c57845d655251a33db310b4c154e422b5db65d2d62d02620eff2540"
      },
      {
        "path": "/data2/k6tk/55/558279a76a4eb286fcae18ba42bf7e03ae89f182f9a0c29effe0c2181a4f35a7.png",
        "sha256": "558279a76a4eb286fcae18ba42bf7e03ae89f182f9a0c29effe0c2181a4f35a7"
      },
      {
        "path": "/data2/k6tk/62/62c892fb4efd0cc918659e7addf16b9ea772ff2cbd947e1b9864bbb648e3cf6d.png",
        "sha256": "62c892fb4efd0cc918659e7addf16b9ea772ff2cbd947e1b9864bbb648e3cf6d"
      },
      {
        "path": "/data2/k6tk/c9/c9ef947a3644bb6b5701473c68982a7a9f15017d6f958c8c32f8d60dd37cf9a1.png",
        "sha256": "c9ef947a3644bb6b5701473c68982a7a9f15017d6f958c8c32f8d60dd37cf9a1"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. back-left",
      "D. front-right"
    ],
    "question": "If I am standing by the blinds and facing away from the books, is the hat to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.166666666666667,
      12.35,
      18.516666666666666,
      24.7,
      30.866666666666667,
      37.05,
      43.21666666666667,
      49.4,
      55.56666666666667,
      61.75,
      67.93333333333334,
      74.1,
      80.28333333333333,
      86.45,
      92.63333333333334,
      98.8,
      104.98333333333333,
      111.15,
      117.33333333333333,
      123.5,
      129.68333333333334,
      135.86666666666667,
      142.03333333333333,
      148.21666666666667,
      154.38333333333333,
      160.56666666666666,
      166.73333333333332,
      172.91666666666666,
      179.08333333333334,
      185.26666666666668,
      191.45
    ],
    "total_num_frames": 11488
  },
  "target": "<think>\nStep 1: locate the blinds, the books and the hat.\nStep 2: facing the books from the blinds, I find the hat in front of me, on my right.\nStep 3: I face away from the books by making a half turn. Front and back swap, and left and right swap.\nSo I find the hat at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "3a39511fbebfdd26f9e59da3700813297d38aba15130f8b6cbb062655ab003c2"
  },
  "candidate_id": "ground-468c0c31c3270cfc9e71da550d9cedb68187244f3f5f1e424465a726b5e976da",
  "label_row_keys": [
    "qa7a44f3ee64eeaab1209edd0"
  ]
}
```

## 26. q6816336d7c37b49f08f93429_sb_rowD7f_a

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q6816336d7c37b49f08f93429",
      "source_store_i": 8490,
      "source_row_sha256": "ef2c6380150f4053cfa95823b00f4f534c25fef0db3e883efbf9290e06f93bc0",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 32,
        "end": 38,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q6816336d7c37b49f08f93429_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v752c2e3b43f8",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      200,
      401,
      601,
      802,
      1002,
      1203,
      1403,
      1604,
      1804,
      2005,
      2205,
      2406,
      2606,
      2807,
      3007,
      3208,
      3408,
      3609,
      3809,
      4010,
      4210,
      4411,
      4611,
      4812,
      5012,
      5213,
      5413,
      5614,
      5814,
      6015,
      6216
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c7/c778762227e0ab0591aa0525b71af3183e9a074f657cff2883ee84054a39b20a.png",
        "sha256": "c778762227e0ab0591aa0525b71af3183e9a074f657cff2883ee84054a39b20a"
      },
      {
        "path": "/data2/k6tk/e0/e0ab4d1ba141ee0958647129482b63743d644525922b9940d90b9ad1018f25a6.png",
        "sha256": "e0ab4d1ba141ee0958647129482b63743d644525922b9940d90b9ad1018f25a6"
      },
      {
        "path": "/data2/k6tk/60/60def1edb1082208ae59a74a673bce07bd3a968c305d77b2e31e0320abdf703d.png",
        "sha256": "60def1edb1082208ae59a74a673bce07bd3a968c305d77b2e31e0320abdf703d"
      },
      {
        "path": "/data2/k6tk/38/38fc1c6afdd0ecd87c141a1e1b7efc2afb55e7672c114c31fd4930717ef14d38.png",
        "sha256": "38fc1c6afdd0ecd87c141a1e1b7efc2afb55e7672c114c31fd4930717ef14d38"
      },
      {
        "path": "/data2/k6tk/a1/a1e2b92e0512c78aa19d2dbf6037bc5333f4c016d6df519f1486af9cfcf6430c.png",
        "sha256": "a1e2b92e0512c78aa19d2dbf6037bc5333f4c016d6df519f1486af9cfcf6430c"
      },
      {
        "path": "/data2/k6tk/72/72778ecf4c00bdd60102291e9c25a150596be853301f90debd4627b60cd27941.png",
        "sha256": "72778ecf4c00bdd60102291e9c25a150596be853301f90debd4627b60cd27941"
      },
      {
        "path": "/data2/k6tk/6a/6acb76e367647d03d03f866d93b96705bbc4a831d144a0e378ecaa47169ecbab.png",
        "sha256": "6acb76e367647d03d03f866d93b96705bbc4a831d144a0e378ecaa47169ecbab"
      },
      {
        "path": "/data2/k6tk/bd/bd156f820304a7c10fa30931b50d80014e469c1ef7d131c6b42a1c6a9dc5b622.png",
        "sha256": "bd156f820304a7c10fa30931b50d80014e469c1ef7d131c6b42a1c6a9dc5b622"
      },
      {
        "path": "/data2/k6tk/bf/bfdf2d109900da6f4c569d45ad76784516f5cdbce3d6dc1d699e439a80b3a832.png",
        "sha256": "bfdf2d109900da6f4c569d45ad76784516f5cdbce3d6dc1d699e439a80b3a832"
      },
      {
        "path": "/data2/k6tk/61/61f8e082e38ee2f1f00829d4a8ad47af3c197825717282ef357cb21743dcabb2.png",
        "sha256": "61f8e082e38ee2f1f00829d4a8ad47af3c197825717282ef357cb21743dcabb2"
      },
      {
        "path": "/data2/k6tk/76/76dea56c698200963e4f09f246f10ef934b0dc2d7f7137a3e2ad74c10958d8d6.png",
        "sha256": "76dea56c698200963e4f09f246f10ef934b0dc2d7f7137a3e2ad74c10958d8d6"
      },
      {
        "path": "/data2/k6tk/1a/1af5aebc8d4e0b04f3b6798dc5a94abeb4f5bb8c0ededab1d92a4a6ea513cac7.png",
        "sha256": "1af5aebc8d4e0b04f3b6798dc5a94abeb4f5bb8c0ededab1d92a4a6ea513cac7"
      },
      {
        "path": "/data2/k6tk/34/3462d284f946d359d4259fb7767383cd3acdf717774c68c13c62a71397236aec.png",
        "sha256": "3462d284f946d359d4259fb7767383cd3acdf717774c68c13c62a71397236aec"
      },
      {
        "path": "/data2/k6tk/8c/8cd70b13f113d4bebc61920bb090027c3fb09d290afb7218d1641bdb1d15531f.png",
        "sha256": "8cd70b13f113d4bebc61920bb090027c3fb09d290afb7218d1641bdb1d15531f"
      },
      {
        "path": "/data2/k6tk/2f/2f32942949f3d0e34f87a61f5f5bbfdcb05393fc6982bf310a0293387d8cba5a.png",
        "sha256": "2f32942949f3d0e34f87a61f5f5bbfdcb05393fc6982bf310a0293387d8cba5a"
      },
      {
        "path": "/data2/k6tk/71/71b12b1d1531654d8611a29f2ad12eaaa0c44347cb2be0840ffbcb9fce3f3600.png",
        "sha256": "71b12b1d1531654d8611a29f2ad12eaaa0c44347cb2be0840ffbcb9fce3f3600"
      },
      {
        "path": "/data2/k6tk/c8/c84322230fb2c303b8072f67bd395dc74e29e06d6e0e64021191e4ede7532dc0.png",
        "sha256": "c84322230fb2c303b8072f67bd395dc74e29e06d6e0e64021191e4ede7532dc0"
      },
      {
        "path": "/data2/k6tk/90/9055505e8f003155e05ea94b32d0a7c6480774a37daab3a67f5dbc09fa898c42.png",
        "sha256": "9055505e8f003155e05ea94b32d0a7c6480774a37daab3a67f5dbc09fa898c42"
      },
      {
        "path": "/data2/k6tk/bc/bccfb9082468d31cbb478057cc48bd1e4d471ad380a7a44fa049fa6960add361.png",
        "sha256": "bccfb9082468d31cbb478057cc48bd1e4d471ad380a7a44fa049fa6960add361"
      },
      {
        "path": "/data2/k6tk/8d/8df1ef6673bdade7d3e85f56847e33ed7c3a60a5557196b4e3dc3500b4aaf598.png",
        "sha256": "8df1ef6673bdade7d3e85f56847e33ed7c3a60a5557196b4e3dc3500b4aaf598"
      },
      {
        "path": "/data2/k6tk/86/8673bb00497e0ce985ab43ec2546521a10db09aec1a680e0eb0a599cff6cdb89.png",
        "sha256": "8673bb00497e0ce985ab43ec2546521a10db09aec1a680e0eb0a599cff6cdb89"
      },
      {
        "path": "/data2/k6tk/a7/a7963bafa3947f08fd0dc670e3667bd95bccaf292a87b155f9a08dc104fd2fd4.png",
        "sha256": "a7963bafa3947f08fd0dc670e3667bd95bccaf292a87b155f9a08dc104fd2fd4"
      },
      {
        "path": "/data2/k6tk/f7/f7a0b385867ba1655790b60c8e11f0724020b089adcdd02ff08f91c881d84eec.png",
        "sha256": "f7a0b385867ba1655790b60c8e11f0724020b089adcdd02ff08f91c881d84eec"
      },
      {
        "path": "/data2/k6tk/e9/e969ed7ba6c2f48dd2723ba8305eb043948826bdbdcc1ec0953d0b7b4f63fefd.png",
        "sha256": "e969ed7ba6c2f48dd2723ba8305eb043948826bdbdcc1ec0953d0b7b4f63fefd"
      },
      {
        "path": "/data2/k6tk/f0/f0a64dec6d0299c7b341de09a9d96992ad0004f1940f13a0d3fe26a12ec9b42d.png",
        "sha256": "f0a64dec6d0299c7b341de09a9d96992ad0004f1940f13a0d3fe26a12ec9b42d"
      },
      {
        "path": "/data2/k6tk/7d/7d41c15f86a4f2b0c4c0ac3efbe2cacd5a9aa9a67c1681c5032b9b4e939f084a.png",
        "sha256": "7d41c15f86a4f2b0c4c0ac3efbe2cacd5a9aa9a67c1681c5032b9b4e939f084a"
      },
      {
        "path": "/data2/k6tk/f3/f349e10f9e4ff3e238188dff020c273920f3e853e385e6ff516a584617e97205.png",
        "sha256": "f349e10f9e4ff3e238188dff020c273920f3e853e385e6ff516a584617e97205"
      },
      {
        "path": "/data2/k6tk/69/69847ccacb598d4480c8c75dec884c02d127049eeed63fdfde61ab3a8b8a1cc8.png",
        "sha256": "69847ccacb598d4480c8c75dec884c02d127049eeed63fdfde61ab3a8b8a1cc8"
      },
      {
        "path": "/data2/k6tk/4f/4f61ff249de68213fae21d9edf222d5ceda262ccaacc8fe17cb8a7fa55737480.png",
        "sha256": "4f61ff249de68213fae21d9edf222d5ceda262ccaacc8fe17cb8a7fa55737480"
      },
      {
        "path": "/data2/k6tk/5b/5bf5af5c5a844f917bd981cfba148c3ca2168da5c81e890545b0b55b9d099b06.png",
        "sha256": "5bf5af5c5a844f917bd981cfba148c3ca2168da5c81e890545b0b55b9d099b06"
      },
      {
        "path": "/data2/k6tk/e1/e1444613e975c2b25df9ab8f9a1d3c2284ccc7fbd6f81167e25f2138d8890505.png",
        "sha256": "e1444613e975c2b25df9ab8f9a1d3c2284ccc7fbd6f81167e25f2138d8890505"
      },
      {
        "path": "/data2/k6tk/52/52a59212302ddc68945108faeeb377aadbf7cbdca6958fe861a2b09ed0b8d30b.png",
        "sha256": "52a59212302ddc68945108faeeb377aadbf7cbdca6958fe861a2b09ed0b8d30b"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-right",
      "C. front-left",
      "D. back-right"
    ],
    "question": "If I am standing by the box and facing away from the cabinet, is the dish soap to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.3333333333333335,
      6.683333333333334,
      10.016666666666667,
      13.366666666666667,
      16.7,
      20.05,
      23.383333333333333,
      26.733333333333334,
      30.066666666666666,
      33.416666666666664,
      36.75,
      40.1,
      43.43333333333333,
      46.78333333333333,
      50.11666666666667,
      53.46666666666667,
      56.8,
      60.15,
      63.483333333333334,
      66.83333333333333,
      70.16666666666667,
      73.51666666666667,
      76.85,
      80.2,
      83.53333333333333,
      86.88333333333334,
      90.21666666666667,
      93.56666666666666,
      96.9,
      100.25,
      103.6
    ],
    "total_num_frames": 6217
  },
  "target": "<think>\nStep 1: locate the dish soap, the box and the cabinet.\nStep 2: I stand at the box facing the cabinet; I find the dish soap in front of me, on my right.\nStep 3: I face away from the cabinet by making a half turn. Front and back swap, and left and right swap.\nSo I find the dish soap at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "92408b824a6de568d0605225983d30145a394086911091ca9af25f8be98cb249"
  },
  "candidate_id": "ground-59cc6ab22b711d7046f1d315c57bad7c184b27c883fff4d6748723468f5ad37c",
  "label_row_keys": [
    "q6816336d7c37b49f08f93429"
  ]
}
```

## 27. q8e1e905abd2394ff4dbf4b51_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q8e1e905abd2394ff4dbf4b51",
      "source_store_i": 41598,
      "source_row_sha256": "f4702e5900cf02169e5ebbdf1a14c9c6ebee755ca4b9318ba7049a5ad884a9f9",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 44,
        "end": 50,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q8e1e905abd2394ff4dbf4b51_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vf87cc62b4844",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      50,
      101,
      152,
      202,
      253,
      304,
      354,
      405,
      456,
      507,
      557,
      608,
      659,
      709,
      760,
      811,
      862,
      912,
      963,
      1014,
      1064,
      1115,
      1166,
      1217,
      1267,
      1318,
      1369,
      1419,
      1470,
      1521,
      1572
    ],
    "frames": [
      {
        "path": "/data2/k6tk/52/52364c9f561e52f1238c293651a6c5ae493f2dd4ac035ddce936d7135f575bf8.png",
        "sha256": "52364c9f561e52f1238c293651a6c5ae493f2dd4ac035ddce936d7135f575bf8"
      },
      {
        "path": "/data2/k6tk/35/35b0e1a3cef7de8a8db5f35b828f45b9ebf8f1a72b7c1fa44b8bfe7d4200ef6a.png",
        "sha256": "35b0e1a3cef7de8a8db5f35b828f45b9ebf8f1a72b7c1fa44b8bfe7d4200ef6a"
      },
      {
        "path": "/data2/k6tk/79/79e3344bca9361b8e87d300b40268aa093fff5fa57f068a5f0fa97557da50a1f.png",
        "sha256": "79e3344bca9361b8e87d300b40268aa093fff5fa57f068a5f0fa97557da50a1f"
      },
      {
        "path": "/data2/k6tk/82/822920bdf9e28c2a1464202764faefa88f5de3060b98d0bee67c952d0a5a8ad4.png",
        "sha256": "822920bdf9e28c2a1464202764faefa88f5de3060b98d0bee67c952d0a5a8ad4"
      },
      {
        "path": "/data2/k6tk/5d/5d531019fa83fb47bc2b84c27c0dc963603f300d00b80f4cce53c5273c3c5bd6.png",
        "sha256": "5d531019fa83fb47bc2b84c27c0dc963603f300d00b80f4cce53c5273c3c5bd6"
      },
      {
        "path": "/data2/k6tk/c3/c30883758f35992074277877d4bc23e6ac9b7c488589b3cc123c861d6dd59738.png",
        "sha256": "c30883758f35992074277877d4bc23e6ac9b7c488589b3cc123c861d6dd59738"
      },
      {
        "path": "/data2/k6tk/d3/d36122f7a8d39ae26b0018a1285d4769c9e389d844f51575bcda4616b865e047.png",
        "sha256": "d36122f7a8d39ae26b0018a1285d4769c9e389d844f51575bcda4616b865e047"
      },
      {
        "path": "/data2/k6tk/6c/6c8bf85fcd1246683dcc585c63d224bc5a833b3065b7093089d812d877f7278e.png",
        "sha256": "6c8bf85fcd1246683dcc585c63d224bc5a833b3065b7093089d812d877f7278e"
      },
      {
        "path": "/data2/k6tk/8c/8c42170ff04e000a9a19aef97ae1339bdb62f233f189643ba8f0b81022382868.png",
        "sha256": "8c42170ff04e000a9a19aef97ae1339bdb62f233f189643ba8f0b81022382868"
      },
      {
        "path": "/data2/k6tk/f2/f24ccf92ac9142e211365cc37dcfac5f14554320b23329d10c31328456de0460.png",
        "sha256": "f24ccf92ac9142e211365cc37dcfac5f14554320b23329d10c31328456de0460"
      },
      {
        "path": "/data2/k6tk/03/03a8694b24d8e54c636214126c1f74b9eda163b705e1017ea4ae4e07562d0fb7.png",
        "sha256": "03a8694b24d8e54c636214126c1f74b9eda163b705e1017ea4ae4e07562d0fb7"
      },
      {
        "path": "/data2/k6tk/b9/b9b5661af0f5ddd66c73dbfcdf8c523d48851aa27b1ccaebf4b8e6223d7d1fd8.png",
        "sha256": "b9b5661af0f5ddd66c73dbfcdf8c523d48851aa27b1ccaebf4b8e6223d7d1fd8"
      },
      {
        "path": "/data2/k6tk/68/6886db410978d72e4f31a3678d559108212991e045ea0f4be2c3c8664990da09.png",
        "sha256": "6886db410978d72e4f31a3678d559108212991e045ea0f4be2c3c8664990da09"
      },
      {
        "path": "/data2/k6tk/5f/5f252c7c260fed43ce6f03b46579f234e3974eaa9a1f0469b4fdcd48864fbe76.png",
        "sha256": "5f252c7c260fed43ce6f03b46579f234e3974eaa9a1f0469b4fdcd48864fbe76"
      },
      {
        "path": "/data2/k6tk/01/015c9a6ccb128d033c29e67d67c39b02a87bfb4a1db0b7a29613483abc07e82b.png",
        "sha256": "015c9a6ccb128d033c29e67d67c39b02a87bfb4a1db0b7a29613483abc07e82b"
      },
      {
        "path": "/data2/k6tk/4c/4c478b79eba077306a9363327e0ff5d243f3f767f37f0501ece8859d261f514d.png",
        "sha256": "4c478b79eba077306a9363327e0ff5d243f3f767f37f0501ece8859d261f514d"
      },
      {
        "path": "/data2/k6tk/5e/5ec7cc7b3a9cf55c87473dee9df459b53499ed404e2d1bcc68a41852ad6285c4.png",
        "sha256": "5ec7cc7b3a9cf55c87473dee9df459b53499ed404e2d1bcc68a41852ad6285c4"
      },
      {
        "path": "/data2/k6tk/6e/6ef071e3b229b9320776c49aad1447351aebd38158dc0cc9caa9eca407fa5269.png",
        "sha256": "6ef071e3b229b9320776c49aad1447351aebd38158dc0cc9caa9eca407fa5269"
      },
      {
        "path": "/data2/k6tk/2a/2aad9a8f7cb08ca2505afe2720732f5d840911bf1021cfc12a367eb53e2eceab.png",
        "sha256": "2aad9a8f7cb08ca2505afe2720732f5d840911bf1021cfc12a367eb53e2eceab"
      },
      {
        "path": "/data2/k6tk/ad/adabeace9b93eba109a9a604c2bcff2294d5977cb86e80f9994c2012cec21359.png",
        "sha256": "adabeace9b93eba109a9a604c2bcff2294d5977cb86e80f9994c2012cec21359"
      },
      {
        "path": "/data2/k6tk/cd/cd2522b834c742a3e9b6d1acdb7b716a5f33835a8cca99508d69aecf655400dc.png",
        "sha256": "cd2522b834c742a3e9b6d1acdb7b716a5f33835a8cca99508d69aecf655400dc"
      },
      {
        "path": "/data2/k6tk/d6/d6cafdc6cb42c11171fe0a3f6d65db614871474c16b75519b3af7908506cf492.png",
        "sha256": "d6cafdc6cb42c11171fe0a3f6d65db614871474c16b75519b3af7908506cf492"
      },
      {
        "path": "/data2/k6tk/e2/e27d6bbd78d94c1912e6a6bc4cdd59164c3e8e78220f7f6d05707f8844e2fdab.png",
        "sha256": "e27d6bbd78d94c1912e6a6bc4cdd59164c3e8e78220f7f6d05707f8844e2fdab"
      },
      {
        "path": "/data2/k6tk/3b/3be156e84dc22c1e7a6a971e5b8e1fcedfda7aae4ea880b638fd6ecd441880cc.png",
        "sha256": "3be156e84dc22c1e7a6a971e5b8e1fcedfda7aae4ea880b638fd6ecd441880cc"
      },
      {
        "path": "/data2/k6tk/e9/e9d523c8cafcdcc053eb2c331c83cb00ba99ce4855dd20c1e033bbe7167892f4.png",
        "sha256": "e9d523c8cafcdcc053eb2c331c83cb00ba99ce4855dd20c1e033bbe7167892f4"
      },
      {
        "path": "/data2/k6tk/54/540ed30818013c1c6fa59cd9c3028555716ac4bea216435585a3bc35ffb3d1f4.png",
        "sha256": "540ed30818013c1c6fa59cd9c3028555716ac4bea216435585a3bc35ffb3d1f4"
      },
      {
        "path": "/data2/k6tk/8b/8b0ffaa5789c38c8f2607a36e03ab02b49aa02552f801cb0699709aa045e2573.png",
        "sha256": "8b0ffaa5789c38c8f2607a36e03ab02b49aa02552f801cb0699709aa045e2573"
      },
      {
        "path": "/data2/k6tk/ed/eda89a4f90f84dec514b6c136a2972fed23bcf5134ccc4eb5ef1276b75b8c32f.png",
        "sha256": "eda89a4f90f84dec514b6c136a2972fed23bcf5134ccc4eb5ef1276b75b8c32f"
      },
      {
        "path": "/data2/k6tk/f4/f45ab286d7a4563439bff374bd92d33c122ae2dd159c566fa12311ad495181c0.png",
        "sha256": "f45ab286d7a4563439bff374bd92d33c122ae2dd159c566fa12311ad495181c0"
      },
      {
        "path": "/data2/k6tk/3b/3b032d23543745a73a66d69675fe51859c067473767ee13a4ad8a87f007282f3.png",
        "sha256": "3b032d23543745a73a66d69675fe51859c067473767ee13a4ad8a87f007282f3"
      },
      {
        "path": "/data2/k6tk/d4/d473b0ad36a52c20cc43fc52baf4eaeeb05e5a38a00bec0b51e1ff6b0c240905.png",
        "sha256": "d473b0ad36a52c20cc43fc52baf4eaeeb05e5a38a00bec0b51e1ff6b0c240905"
      },
      {
        "path": "/data2/k6tk/3e/3e551ee307e7e13899ba32469daf48281316cfd5f3bb1afefbed0960d030bf29.png",
        "sha256": "3e551ee307e7e13899ba32469daf48281316cfd5f3bb1afefbed0960d030bf29"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-right",
      "D. back-left"
    ],
    "question": "If I am standing by the bathroom vanity and facing away from the picture, is the shower walls to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.0833333333333335,
      4.208333333333333,
      6.333333333333333,
      8.416666666666666,
      10.541666666666666,
      12.666666666666666,
      14.75,
      16.875,
      19.0,
      21.125,
      23.208333333333332,
      25.333333333333332,
      27.458333333333332,
      29.541666666666668,
      31.666666666666668,
      33.791666666666664,
      35.916666666666664,
      38.0,
      40.125,
      42.25,
      44.333333333333336,
      46.458333333333336,
      48.583333333333336,
      50.708333333333336,
      52.791666666666664,
      54.916666666666664,
      57.041666666666664,
      59.125,
      61.25,
      63.375,
      65.5
    ],
    "total_num_frames": 1573
  },
  "target": "<think>\nStep 1: locate the bathroom vanity, the picture and the shower walls.\nStep 2: standing at the bathroom vanity and facing the picture, I find the shower walls in front of me, on my right.\nStep 3: I face away from the picture by making a half turn. Front and back swap, and left and right swap.\nSo I find the shower walls at my back-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "0aae921a8ded1b9a48002100cf88fb22f2d65bfba898790611d1546658672a33"
  },
  "candidate_id": "ground-1fef76036f31affcae703023d78055d8de66a24b8560edd61dd58078825cfa0a",
  "label_row_keys": [
    "q8e1e905abd2394ff4dbf4b51"
  ]
}
```

## 28. qe8680bcb63c4b9b54258f6be-p1_sb_rowD7f_a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qe8680bcb63c4b9b54258f6be-p1",
      "source_store_i": 86487,
      "source_row_sha256": "dc6b929e0d201cd799af8e8238ba005f3d3154d34d3628c72b9f8e5970daae75",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "D",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 26,
        "end": 36,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qe8680bcb63c4b9b54258f6be-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v38a9e3ee478c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      328,
      656,
      984,
      1312,
      1640,
      1968,
      2296,
      2624,
      2952,
      3280,
      3608,
      3936,
      4264,
      4592,
      4920,
      5248,
      5576,
      5904,
      6232,
      6560,
      6888,
      7216,
      7544,
      7872,
      8200,
      8528,
      8856,
      9184,
      9512,
      9840,
      10169
    ],
    "frames": [
      {
        "path": "/data2/k6tk/61/6144fd9feb05841f87e9b92599230247e338b798aba06d7b5ae73a1b6596faef.png",
        "sha256": "6144fd9feb05841f87e9b92599230247e338b798aba06d7b5ae73a1b6596faef"
      },
      {
        "path": "/data2/k6tk/83/832426d78cb512c44aec1efeb343cecbc704ed00634707f53575c6907c1ca680.png",
        "sha256": "832426d78cb512c44aec1efeb343cecbc704ed00634707f53575c6907c1ca680"
      },
      {
        "path": "/data2/k6tk/1c/1c2ebc5a64141f533ede93245f4a0804ccea3743e2a17471ffda97385fc30904.png",
        "sha256": "1c2ebc5a64141f533ede93245f4a0804ccea3743e2a17471ffda97385fc30904"
      },
      {
        "path": "/data2/k6tk/81/8140066e9acb05f89f565f4c85dabc53caad4a57cf6fd0ec938f780b6254fc31.png",
        "sha256": "8140066e9acb05f89f565f4c85dabc53caad4a57cf6fd0ec938f780b6254fc31"
      },
      {
        "path": "/data2/k6tk/54/5444bb5804d9378451c8f8e1235602609a3109f5377b807e2fc6a5f870310e24.png",
        "sha256": "5444bb5804d9378451c8f8e1235602609a3109f5377b807e2fc6a5f870310e24"
      },
      {
        "path": "/data2/k6tk/01/018f1be69b31c4fa6b839bf563f67a20f05cdf138ca1942469af164dd675045c.png",
        "sha256": "018f1be69b31c4fa6b839bf563f67a20f05cdf138ca1942469af164dd675045c"
      },
      {
        "path": "/data2/k6tk/e9/e9df68963590ed108aa3c56c1af92a51286e17a39558f09c6f66eb24e57cf41c.png",
        "sha256": "e9df68963590ed108aa3c56c1af92a51286e17a39558f09c6f66eb24e57cf41c"
      },
      {
        "path": "/data2/k6tk/39/39257edf560cbb6dcef3a9e68e5f8df5bbc73971d0f0a45be3caba98a5e65487.png",
        "sha256": "39257edf560cbb6dcef3a9e68e5f8df5bbc73971d0f0a45be3caba98a5e65487"
      },
      {
        "path": "/data2/k6tk/4d/4de66fd0d616852e5febf25274805b2168a8523d3e08f74e404a3d327cfc022f.png",
        "sha256": "4de66fd0d616852e5febf25274805b2168a8523d3e08f74e404a3d327cfc022f"
      },
      {
        "path": "/data2/k6tk/0d/0d258f527f9a44ada92e7f2c6b6d707d162b53e46d31df85d75f91b3a86fc8a5.png",
        "sha256": "0d258f527f9a44ada92e7f2c6b6d707d162b53e46d31df85d75f91b3a86fc8a5"
      },
      {
        "path": "/data2/k6tk/89/89291048112656429ded3e50f4a60f93ea0a5d1dbab367dd2331712d93d9cebe.png",
        "sha256": "89291048112656429ded3e50f4a60f93ea0a5d1dbab367dd2331712d93d9cebe"
      },
      {
        "path": "/data2/k6tk/09/09a9439f12c906f3617efb0870d73e53ba42dafa8ba8da2d4955dfb3281d9cda.png",
        "sha256": "09a9439f12c906f3617efb0870d73e53ba42dafa8ba8da2d4955dfb3281d9cda"
      },
      {
        "path": "/data2/k6tk/08/08b6b3f87ad369c69c0136f9d2af08feb12ef7773c33fe33fcadb9f0793c606c.png",
        "sha256": "08b6b3f87ad369c69c0136f9d2af08feb12ef7773c33fe33fcadb9f0793c606c"
      },
      {
        "path": "/data2/k6tk/14/14b9fbfdb37f9515f025f01c0e37db9c4fe6e6bd0627f185301e3ea5fb13fdef.png",
        "sha256": "14b9fbfdb37f9515f025f01c0e37db9c4fe6e6bd0627f185301e3ea5fb13fdef"
      },
      {
        "path": "/data2/k6tk/02/02e9411517acf5da33426d8798ee34c769abf892a1101df90d85cc7aea6049ff.png",
        "sha256": "02e9411517acf5da33426d8798ee34c769abf892a1101df90d85cc7aea6049ff"
      },
      {
        "path": "/data2/k6tk/2b/2bede7495a420870d044385201a3af667d84eeab6dbe961f0db846d561b3abde.png",
        "sha256": "2bede7495a420870d044385201a3af667d84eeab6dbe961f0db846d561b3abde"
      },
      {
        "path": "/data2/k6tk/fd/fde1034e5d88f1b182b07e5c3b793d71bc2c82becc38aa18a31a20d3bf542bd4.png",
        "sha256": "fde1034e5d88f1b182b07e5c3b793d71bc2c82becc38aa18a31a20d3bf542bd4"
      },
      {
        "path": "/data2/k6tk/41/412aaad36612b4c8d04b1895f5cf0055006595320b78c22a9741e35ce3742ccb.png",
        "sha256": "412aaad36612b4c8d04b1895f5cf0055006595320b78c22a9741e35ce3742ccb"
      },
      {
        "path": "/data2/k6tk/1c/1cf0f6893ceb5124a120c5ab00d441197c3f7594989e35c149835c8c5151a40c.png",
        "sha256": "1cf0f6893ceb5124a120c5ab00d441197c3f7594989e35c149835c8c5151a40c"
      },
      {
        "path": "/data2/k6tk/d9/d9b6056e44e27a06a7c76c2aa16e2b0aab53c1df66d8e20c4e023b0610162809.png",
        "sha256": "d9b6056e44e27a06a7c76c2aa16e2b0aab53c1df66d8e20c4e023b0610162809"
      },
      {
        "path": "/data2/k6tk/ac/ac5139864762c7008faf50e4344472b3d4f421fb73d6b5ef36df361b68bc353a.png",
        "sha256": "ac5139864762c7008faf50e4344472b3d4f421fb73d6b5ef36df361b68bc353a"
      },
      {
        "path": "/data2/k6tk/c2/c2ca980333cd935bfbc5023521f2b78a7aabecb796a857ff06d07a6a53e9b25b.png",
        "sha256": "c2ca980333cd935bfbc5023521f2b78a7aabecb796a857ff06d07a6a53e9b25b"
      },
      {
        "path": "/data2/k6tk/10/105b4c474d13062dd9ad9b13e685119011cb41d52d6ce83f9db8d6347ee757a9.png",
        "sha256": "105b4c474d13062dd9ad9b13e685119011cb41d52d6ce83f9db8d6347ee757a9"
      },
      {
        "path": "/data2/k6tk/93/93e6a6c714aeaaf3e927d18f8775826b82023b225dcc80439051dd060b0e1cea.png",
        "sha256": "93e6a6c714aeaaf3e927d18f8775826b82023b225dcc80439051dd060b0e1cea"
      },
      {
        "path": "/data2/k6tk/6d/6dd564c3ba6a1d1bda23483c905ba65b83418f45ffc05a6755bc23e5b2f3c237.png",
        "sha256": "6dd564c3ba6a1d1bda23483c905ba65b83418f45ffc05a6755bc23e5b2f3c237"
      },
      {
        "path": "/data2/k6tk/4f/4f5051edc1297008721bd72466840b2e981a974f56af0f1a77748d1cc7e66aa8.png",
        "sha256": "4f5051edc1297008721bd72466840b2e981a974f56af0f1a77748d1cc7e66aa8"
      },
      {
        "path": "/data2/k6tk/48/48b58902c597ed2a4ea0ead6fbab87b983835d15f0dc769207784a4d5393a8ab.png",
        "sha256": "48b58902c597ed2a4ea0ead6fbab87b983835d15f0dc769207784a4d5393a8ab"
      },
      {
        "path": "/data2/k6tk/92/92c2e64c4badf11281ac5917a83e06616899bca436d1a31bb45e21517286d8b2.png",
        "sha256": "92c2e64c4badf11281ac5917a83e06616899bca436d1a31bb45e21517286d8b2"
      },
      {
        "path": "/data2/k6tk/36/3696b5f6656752534b78accb46b2653403eda66845e3a1e55befdc1a27b3e8e1.png",
        "sha256": "3696b5f6656752534b78accb46b2653403eda66845e3a1e55befdc1a27b3e8e1"
      },
      {
        "path": "/data2/k6tk/1e/1e6e2fa47aa300abb15273f258f94ba16403dabc0390aa7b4786908ceb3e7971.png",
        "sha256": "1e6e2fa47aa300abb15273f258f94ba16403dabc0390aa7b4786908ceb3e7971"
      },
      {
        "path": "/data2/k6tk/d7/d79c71e6eedc7a176f9c61062a28a7bebb8d761871525e98caa950ea5015348c.png",
        "sha256": "d79c71e6eedc7a176f9c61062a28a7bebb8d761871525e98caa950ea5015348c"
      },
      {
        "path": "/data2/k6tk/b2/b2614136c36227cd3c943507c25d7a9d0ef7cd445a57c60ff8d49b5a4c8f9318.png",
        "sha256": "b2614136c36227cd3c943507c25d7a9d0ef7cd445a57c60ff8d49b5a4c8f9318"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-right",
      "C. back-left",
      "D. front-right"
    ],
    "question": "I stand by the blind rail facing away from the desk fan. Where is the door relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      5.466666666666667,
      10.933333333333334,
      16.4,
      21.866666666666667,
      27.333333333333332,
      32.8,
      38.266666666666666,
      43.733333333333334,
      49.2,
      54.666666666666664,
      60.13333333333333,
      65.6,
      71.06666666666666,
      76.53333333333333,
      82.0,
      87.46666666666667,
      92.93333333333334,
      98.4,
      103.86666666666666,
      109.33333333333333,
      114.8,
      120.26666666666667,
      125.73333333333333,
      131.2,
      136.66666666666666,
      142.13333333333333,
      147.6,
      153.06666666666666,
      158.53333333333333,
      164.0,
      169.48333333333332
    ],
    "total_num_frames": 10170
  },
  "target": "<think>\nStep 1: find the blind rail and the desk fan, then the door.\nStep 2: I stand at the blind rail facing the desk fan; I find the door in front of me, on my right.\nStep 3: I face away from the desk fan by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the door at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qe8680bcb63c4b9b54258f6be",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "24f0f8f772a40bd47beae6b2f158ae98846696fef29775957eb46f385317819c"
  },
  "candidate_id": "ground-bb64898f39730e8ce03adec7bad3c25eeb284f36d69c31b668ff1b38d0fde9e1",
  "label_row_keys": [
    "qe8680bcb63c4b9b54258f6be-p1"
  ]
}
```

## 29. qb6f5bee0a1c54c870a1aa7e1-p1_sb_rowD7f_a

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qb6f5bee0a1c54c870a1aa7e1-p1",
      "source_store_i": 67597,
      "source_row_sha256": "8f18aaec40a408c7948c6f81e30102b3d2019ec61cfc5f74544927bd1b84b695",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 29,
        "end": 39,
        "source_clause": "looking at",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qb6f5bee0a1c54c870a1aa7e1-p1_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v320d814bec31",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      562,
      1124,
      1686,
      2249,
      2811,
      3373,
      3935,
      4498,
      5060,
      5622,
      6184,
      6747,
      7309,
      7871,
      8433,
      8996,
      9558,
      10120,
      10682,
      11245,
      11807,
      12369,
      12931,
      13494,
      14056,
      14618,
      15180,
      15743,
      16305,
      16867,
      17430
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a4/a421f67cd366cdf5a1a200109e67c35c599079a58ff3213515891542cfaad5bf.png",
        "sha256": "a421f67cd366cdf5a1a200109e67c35c599079a58ff3213515891542cfaad5bf"
      },
      {
        "path": "/data2/k6tk/ed/ed0688ca6667e03ebc0c54f251f1fab0c15dc6e452d25a3a1cc45fd73028cfc4.png",
        "sha256": "ed0688ca6667e03ebc0c54f251f1fab0c15dc6e452d25a3a1cc45fd73028cfc4"
      },
      {
        "path": "/data2/k6tk/c2/c29afa401ee0f4296160935b6569c0c8a7e361afb2d03933b1bb5012b0f361e9.png",
        "sha256": "c29afa401ee0f4296160935b6569c0c8a7e361afb2d03933b1bb5012b0f361e9"
      },
      {
        "path": "/data2/k6tk/c8/c86075915487c74b190d2e4f382d45b9a6c729ee1eeb0603fbaa24283b51045f.png",
        "sha256": "c86075915487c74b190d2e4f382d45b9a6c729ee1eeb0603fbaa24283b51045f"
      },
      {
        "path": "/data2/k6tk/c1/c1beb148d4014b9a6566e17faa7053d1ce9688c239a38a54a0b34c1e456ad434.png",
        "sha256": "c1beb148d4014b9a6566e17faa7053d1ce9688c239a38a54a0b34c1e456ad434"
      },
      {
        "path": "/data2/k6tk/12/123f5cc851cfb233e9a0aac434fda1670b68583b7f800fda9f72a3b6d4e81ad7.png",
        "sha256": "123f5cc851cfb233e9a0aac434fda1670b68583b7f800fda9f72a3b6d4e81ad7"
      },
      {
        "path": "/data2/k6tk/d0/d082002a90e9bcbcd30e4983131358a2c57575cf5525d90632d7067d8e0c2569.png",
        "sha256": "d082002a90e9bcbcd30e4983131358a2c57575cf5525d90632d7067d8e0c2569"
      },
      {
        "path": "/data2/k6tk/6b/6b92e195fd770323e484f3ec103324f29e94200d815f2c12ce2248b378da194c.png",
        "sha256": "6b92e195fd770323e484f3ec103324f29e94200d815f2c12ce2248b378da194c"
      },
      {
        "path": "/data2/k6tk/09/09b1e520f0d4777f6dc4c4a089f299cb2fa7a84e28c4fe01ec09a9b74a444706.png",
        "sha256": "09b1e520f0d4777f6dc4c4a089f299cb2fa7a84e28c4fe01ec09a9b74a444706"
      },
      {
        "path": "/data2/k6tk/a7/a7f42ecfe95c0fb1185e1ef8ef580623dd1368ab5e8bbb40332700ca769d2f10.png",
        "sha256": "a7f42ecfe95c0fb1185e1ef8ef580623dd1368ab5e8bbb40332700ca769d2f10"
      },
      {
        "path": "/data2/k6tk/99/99c9eb9b5401f54d5f7efb399722255228eb0720cd43f750006d12597b0a1fd5.png",
        "sha256": "99c9eb9b5401f54d5f7efb399722255228eb0720cd43f750006d12597b0a1fd5"
      },
      {
        "path": "/data2/k6tk/61/617a710d9a39dfbda0618185ba3a82cb64f636bbf0a9f27e70bcba859ac5f056.png",
        "sha256": "617a710d9a39dfbda0618185ba3a82cb64f636bbf0a9f27e70bcba859ac5f056"
      },
      {
        "path": "/data2/k6tk/c5/c552e5fdb6a40a3fca96bddb4c2156bbca5abd50f596546c225c1008a154dc84.png",
        "sha256": "c552e5fdb6a40a3fca96bddb4c2156bbca5abd50f596546c225c1008a154dc84"
      },
      {
        "path": "/data2/k6tk/76/76f887b40b874b9002bf37791f1bf91025512b3a4bbdae3291973ebf90930666.png",
        "sha256": "76f887b40b874b9002bf37791f1bf91025512b3a4bbdae3291973ebf90930666"
      },
      {
        "path": "/data2/k6tk/af/af201fb8ba324b9722dedec752218483a609fd1c48aae06f50efca075d7faa78.png",
        "sha256": "af201fb8ba324b9722dedec752218483a609fd1c48aae06f50efca075d7faa78"
      },
      {
        "path": "/data2/k6tk/24/246980e71a380b19d7a1c5df09acf5df381784e24ac5cb9488970ac003e54953.png",
        "sha256": "246980e71a380b19d7a1c5df09acf5df381784e24ac5cb9488970ac003e54953"
      },
      {
        "path": "/data2/k6tk/44/446c1095372657b2879bfca293e752f7e169a8b7f5893c03d5e26917eda301d5.png",
        "sha256": "446c1095372657b2879bfca293e752f7e169a8b7f5893c03d5e26917eda301d5"
      },
      {
        "path": "/data2/k6tk/ed/ed925fc50f84170edf97a93f6fe4ca48aeaced80cf6389a3bca73ae20e16bad4.png",
        "sha256": "ed925fc50f84170edf97a93f6fe4ca48aeaced80cf6389a3bca73ae20e16bad4"
      },
      {
        "path": "/data2/k6tk/61/616610ceced914eb2f2aa0f55b0e74616cb26701fb69da377fcfb572c3cc643f.png",
        "sha256": "616610ceced914eb2f2aa0f55b0e74616cb26701fb69da377fcfb572c3cc643f"
      },
      {
        "path": "/data2/k6tk/92/926360ee5a18409cfbf486a6f6dbb810032085ebc8152fa76f9f951ca56befac.png",
        "sha256": "926360ee5a18409cfbf486a6f6dbb810032085ebc8152fa76f9f951ca56befac"
      },
      {
        "path": "/data2/k6tk/29/29739b53d24956a6d046abc7866956fba0229e150ee4a84a6e63fdb787903924.png",
        "sha256": "29739b53d24956a6d046abc7866956fba0229e150ee4a84a6e63fdb787903924"
      },
      {
        "path": "/data2/k6tk/71/71736f98b233b8abaab7cdf4f1cc6cd30f3ad6a25e26b0bacb3d38ddacaa5449.png",
        "sha256": "71736f98b233b8abaab7cdf4f1cc6cd30f3ad6a25e26b0bacb3d38ddacaa5449"
      },
      {
        "path": "/data2/k6tk/c3/c3c8db310b51aa5771221a89806394785b2e787926e885267d65a56d83a7af84.png",
        "sha256": "c3c8db310b51aa5771221a89806394785b2e787926e885267d65a56d83a7af84"
      },
      {
        "path": "/data2/k6tk/a1/a1be8ec39a4d012585640c1e9b219b246c0123a72cb68c189816ca453897a992.png",
        "sha256": "a1be8ec39a4d012585640c1e9b219b246c0123a72cb68c189816ca453897a992"
      },
      {
        "path": "/data2/k6tk/1c/1c2758aa37ae0dd1ed5df4a9a4173eaeecc4d5fb17587816ae4b3d9b69e28726.png",
        "sha256": "1c2758aa37ae0dd1ed5df4a9a4173eaeecc4d5fb17587816ae4b3d9b69e28726"
      },
      {
        "path": "/data2/k6tk/69/69792dd8e7883031001dc88e2467b9bf06c25b0941c9b2ff7ee6fba54731601a.png",
        "sha256": "69792dd8e7883031001dc88e2467b9bf06c25b0941c9b2ff7ee6fba54731601a"
      },
      {
        "path": "/data2/k6tk/d3/d3be49837a39e52274a9bac7f6821fa52b121247da32d2ca883bef53369230ca.png",
        "sha256": "d3be49837a39e52274a9bac7f6821fa52b121247da32d2ca883bef53369230ca"
      },
      {
        "path": "/data2/k6tk/04/046c89dbf328d2250aa42cd26255d49b2c32490e7123a3ad28ca5301a702ef74.png",
        "sha256": "046c89dbf328d2250aa42cd26255d49b2c32490e7123a3ad28ca5301a702ef74"
      },
      {
        "path": "/data2/k6tk/70/70003cf8e8e29037931ffc4dee59dcaedbd0be44ca42393ee4707cc06da1ef88.png",
        "sha256": "70003cf8e8e29037931ffc4dee59dcaedbd0be44ca42393ee4707cc06da1ef88"
      },
      {
        "path": "/data2/k6tk/15/156e16c40291daf4774342f58cc85c959b0e148b6386fe7fd16607b976d38f8b.png",
        "sha256": "156e16c40291daf4774342f58cc85c959b0e148b6386fe7fd16607b976d38f8b"
      },
      {
        "path": "/data2/k6tk/89/89845e8bf21760fc019a5d401b8c041524f03f9c1370fc12c96dc945a6ed46d8.png",
        "sha256": "89845e8bf21760fc019a5d401b8c041524f03f9c1370fc12c96dc945a6ed46d8"
      },
      {
        "path": "/data2/k6tk/84/84d81a626cbd7fb69fd5e7423b2c644b4b3d32731e339e9e135670e559672a70.png",
        "sha256": "84d81a626cbd7fb69fd5e7423b2c644b4b3d32731e339e9e135670e559672a70"
      }
    ],
    "options": [
      "A. back-right",
      "B. back-left",
      "C. front-right",
      "D. front-left"
    ],
    "question": "I stand by the cardboard box facing away from the coat. Where is the clock relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      9.366666666666667,
      18.733333333333334,
      28.1,
      37.483333333333334,
      46.85,
      56.21666666666667,
      65.58333333333333,
      74.96666666666667,
      84.33333333333333,
      93.7,
      103.06666666666666,
      112.45,
      121.81666666666666,
      131.18333333333334,
      140.55,
      149.93333333333334,
      159.3,
      168.66666666666666,
      178.03333333333333,
      187.41666666666666,
      196.78333333333333,
      206.15,
      215.51666666666668,
      224.9,
      234.26666666666668,
      243.63333333333333,
      253.0,
      262.3833333333333,
      271.75,
      281.1166666666667,
      290.5
    ],
    "total_num_frames": 17431
  },
  "target": "<think>\nStep 1: locate the clock, the cardboard box and the coat.\nStep 2: standing at the cardboard box and facing the coat, I find the clock in front of me, on my right.\nStep 3: I face away from the coat by making a half turn. Front and back swap, and left and right swap.\nSo I find the clock at my back-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qb6f5bee0a1c54c870a1aa7e1",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "31b2670b9a851cd713cfe2a1abe2a3e3769fcef1c51b5a0c4cf543614af1289c"
  },
  "candidate_id": "ground-ab686c9e36bd12145c1479554049f801eb20295767c21f3c09313a854f8b6e86",
  "label_row_keys": [
    "qb6f5bee0a1c54c870a1aa7e1-p1"
  ]
}
```

## 30. q030340f22c178d8e92c9fc6a_sb_rowD7f_a

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d2",
  "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "head_program": null,
  "infrastructure_only": false,
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
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q030340f22c178d8e92c9fc6a",
      "source_store_i": 35529,
      "source_row_sha256": "0b5818941c9fecfa35bcdcd2af774b2536e515f980384875c4b07def114bbbdd",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 44,
        "end": 50,
        "source_clause": "facing",
        "new_clause": "facing away from",
        "rule": "single_clause_substitution"
      },
      "room_resolution": {
        "method": "N Rooms with explicit tiered aliases; source scene token unchanged",
        "alias_map": {
          "path": "/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json",
          "bytes": 5017721,
          "sha256": "7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b"
        }
      },
      "generator_sha256": "c403b8836c7ad84d66465fb3916ac2a0c5088920789f83881dacd4589057291e"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q030340f22c178d8e92c9fc6a_sb_rowD7f_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vf5217958fcee",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      365,
      730,
      1095,
      1461,
      1826,
      2191,
      2557,
      2922,
      3287,
      3653,
      4018,
      4383,
      4749,
      5114,
      5479,
      5845,
      6210,
      6575,
      6941,
      7306,
      7671,
      8037,
      8402,
      8767,
      9133,
      9498,
      9863,
      10229,
      10594,
      10959,
      11325
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c6/c6567f0c8ad65ddffc2c2f4eb35574ab8c5fbcc5504de8b08607ccbad0ae1a6e.png",
        "sha256": "c6567f0c8ad65ddffc2c2f4eb35574ab8c5fbcc5504de8b08607ccbad0ae1a6e"
      },
      {
        "path": "/data2/k6tk/c0/c0f0ef5a73319b41fe45926ea02f7267ef2556c01ba8a66487322f5bfc99d4fb.png",
        "sha256": "c0f0ef5a73319b41fe45926ea02f7267ef2556c01ba8a66487322f5bfc99d4fb"
      },
      {
        "path": "/data2/k6tk/9a/9a4431e5811d19beb16a57df3726da976e2befdfa9b500bb33ac56c52ee595c1.png",
        "sha256": "9a4431e5811d19beb16a57df3726da976e2befdfa9b500bb33ac56c52ee595c1"
      },
      {
        "path": "/data2/k6tk/1a/1a0129b5b5d33e560eb957d5415b100725390081bd9573f30243ff0274faf61d.png",
        "sha256": "1a0129b5b5d33e560eb957d5415b100725390081bd9573f30243ff0274faf61d"
      },
      {
        "path": "/data2/k6tk/e7/e7f9274a209313b64566ba691c68dcf0e418bc07965c544e5e0c989621ce0ebb.png",
        "sha256": "e7f9274a209313b64566ba691c68dcf0e418bc07965c544e5e0c989621ce0ebb"
      },
      {
        "path": "/data2/k6tk/a0/a0d8041aff382936ed948cf6fa629d3cb12cabac0a955fbab8b5a8a2f0c221c9.png",
        "sha256": "a0d8041aff382936ed948cf6fa629d3cb12cabac0a955fbab8b5a8a2f0c221c9"
      },
      {
        "path": "/data2/k6tk/8e/8e8c0cfa7447e1fee2ccf762aa569dbf0158f57f07ef64cc15481b7a977264bd.png",
        "sha256": "8e8c0cfa7447e1fee2ccf762aa569dbf0158f57f07ef64cc15481b7a977264bd"
      },
      {
        "path": "/data2/k6tk/81/819b08c8def806d9fb66249e65b81aa4a5d9f9d200adba1561a1c63e93d66cc3.png",
        "sha256": "819b08c8def806d9fb66249e65b81aa4a5d9f9d200adba1561a1c63e93d66cc3"
      },
      {
        "path": "/data2/k6tk/ee/ee0cde3c1d4336de44e2550095263d495dbd3e7507ecb7f1178e89d1dd7ebe3e.png",
        "sha256": "ee0cde3c1d4336de44e2550095263d495dbd3e7507ecb7f1178e89d1dd7ebe3e"
      },
      {
        "path": "/data2/k6tk/d0/d0c954d761072256a207372cf82f04f5bf7e4967e5de8b78f6ef273afc922c53.png",
        "sha256": "d0c954d761072256a207372cf82f04f5bf7e4967e5de8b78f6ef273afc922c53"
      },
      {
        "path": "/data2/k6tk/78/782d128b0d2f72d3a5a2f219b6e721f28430bf13d1ebcebc801b33805144ff5f.png",
        "sha256": "782d128b0d2f72d3a5a2f219b6e721f28430bf13d1ebcebc801b33805144ff5f"
      },
      {
        "path": "/data2/k6tk/01/01706c2c0593a8da5a679956ae22f99a2efda74728e2b3b31c259b49fdef1e2b.png",
        "sha256": "01706c2c0593a8da5a679956ae22f99a2efda74728e2b3b31c259b49fdef1e2b"
      },
      {
        "path": "/data2/k6tk/7c/7c4ceb8d62110753b981acdb901166678d0bc020888df1c62606d73a2f7ce5af.png",
        "sha256": "7c4ceb8d62110753b981acdb901166678d0bc020888df1c62606d73a2f7ce5af"
      },
      {
        "path": "/data2/k6tk/62/622eb7f27a6bba46546ba709acd4666af1504e7dfc5601ee8bf117fc7582c691.png",
        "sha256": "622eb7f27a6bba46546ba709acd4666af1504e7dfc5601ee8bf117fc7582c691"
      },
      {
        "path": "/data2/k6tk/1c/1ca50a73ec8952067f39e6a2112ec11054a27da31dc3c9ba8cf053b3172f2f93.png",
        "sha256": "1ca50a73ec8952067f39e6a2112ec11054a27da31dc3c9ba8cf053b3172f2f93"
      },
      {
        "path": "/data2/k6tk/63/6335b4067f1368b412f09c3b0f167b31b2df021709ce216206dd84026539bf2b.png",
        "sha256": "6335b4067f1368b412f09c3b0f167b31b2df021709ce216206dd84026539bf2b"
      },
      {
        "path": "/data2/k6tk/aa/aa71a663d0148524fb90849b3ac4955f2384ed0a22754c9f05c496e9c80480dc.png",
        "sha256": "aa71a663d0148524fb90849b3ac4955f2384ed0a22754c9f05c496e9c80480dc"
      },
      {
        "path": "/data2/k6tk/90/90778babfd679ccb970cbc654ec4ea2959ef693ce5ba1f112b557991bc5dae21.png",
        "sha256": "90778babfd679ccb970cbc654ec4ea2959ef693ce5ba1f112b557991bc5dae21"
      },
      {
        "path": "/data2/k6tk/da/dadb663fae59400cb5de689c8a0e158a09e2fc8e08bf6012e973b9c378fa3991.png",
        "sha256": "dadb663fae59400cb5de689c8a0e158a09e2fc8e08bf6012e973b9c378fa3991"
      },
      {
        "path": "/data2/k6tk/33/3323dc0df042a1e4d29d4642ede6d70aa8e07458576d411830b3f3d105d400a2.png",
        "sha256": "3323dc0df042a1e4d29d4642ede6d70aa8e07458576d411830b3f3d105d400a2"
      },
      {
        "path": "/data2/k6tk/dc/dc873978ae9ea037a70443aa8919587fec78d1a155a189c880077f02452ccb33.png",
        "sha256": "dc873978ae9ea037a70443aa8919587fec78d1a155a189c880077f02452ccb33"
      },
      {
        "path": "/data2/k6tk/09/09396021fc80c7bd41c2d2c32414848ddefa1609f4e83c0c4a568911507b547d.png",
        "sha256": "09396021fc80c7bd41c2d2c32414848ddefa1609f4e83c0c4a568911507b547d"
      },
      {
        "path": "/data2/k6tk/8a/8a39485c38363307ab76f61e709c2b8104f0e7d61953768cfb0ab936f28de36c.png",
        "sha256": "8a39485c38363307ab76f61e709c2b8104f0e7d61953768cfb0ab936f28de36c"
      },
      {
        "path": "/data2/k6tk/37/37a63e5e1d0d4f10069053610f1ca6e53e35e6ee38b932987d8f505a1d6fe9ae.png",
        "sha256": "37a63e5e1d0d4f10069053610f1ca6e53e35e6ee38b932987d8f505a1d6fe9ae"
      },
      {
        "path": "/data2/k6tk/64/645256bc3417414dad01f8d543ad25f67fd62d66148c7ee745e1285d0897f671.png",
        "sha256": "645256bc3417414dad01f8d543ad25f67fd62d66148c7ee745e1285d0897f671"
      },
      {
        "path": "/data2/k6tk/85/852f2b7735b9b56971064b3e97b7441494fc2ecd6c238cc9f00e6c622f1bf5e5.png",
        "sha256": "852f2b7735b9b56971064b3e97b7441494fc2ecd6c238cc9f00e6c622f1bf5e5"
      },
      {
        "path": "/data2/k6tk/62/62b4a7a18f9b9cd53d0d74782fef49b05719818024a1eb34bdd815de920d6dbe.png",
        "sha256": "62b4a7a18f9b9cd53d0d74782fef49b05719818024a1eb34bdd815de920d6dbe"
      },
      {
        "path": "/data2/k6tk/41/414149c268a9808ee4832c5e15c83987985784daac0b6d2612d43516bdf71a96.png",
        "sha256": "414149c268a9808ee4832c5e15c83987985784daac0b6d2612d43516bdf71a96"
      },
      {
        "path": "/data2/k6tk/7f/7f8666bf29ab9636fdd3d531a3536ec96c95fdf352685d465d54171bcdaa0bfa.png",
        "sha256": "7f8666bf29ab9636fdd3d531a3536ec96c95fdf352685d465d54171bcdaa0bfa"
      },
      {
        "path": "/data2/k6tk/0f/0f9f28f0f2c1a95d7db15711059154e1a1d6b16d308b526ac4bc98b5c970a22e.png",
        "sha256": "0f9f28f0f2c1a95d7db15711059154e1a1d6b16d308b526ac4bc98b5c970a22e"
      },
      {
        "path": "/data2/k6tk/45/4533d0cfde9884295d4091b2ff10d95a100487cc8bcea7abc4a0677836267b90.png",
        "sha256": "4533d0cfde9884295d4091b2ff10d95a100487cc8bcea7abc4a0677836267b90"
      },
      {
        "path": "/data2/k6tk/fb/fb69d065e25508bc87100e7499a40dd603effe30bc5d3975effa220574409c86.png",
        "sha256": "fb69d065e25508bc87100e7499a40dd603effe30bc5d3975effa220574409c86"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the air conditioner and facing away from the fire extinguisher, is the microscope to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.083333333333333,
      12.166666666666666,
      18.25,
      24.35,
      30.433333333333334,
      36.516666666666666,
      42.61666666666667,
      48.7,
      54.78333333333333,
      60.88333333333333,
      66.96666666666667,
      73.05,
      79.15,
      85.23333333333333,
      91.31666666666666,
      97.41666666666667,
      103.5,
      109.58333333333333,
      115.68333333333334,
      121.76666666666667,
      127.85,
      133.95,
      140.03333333333333,
      146.11666666666667,
      152.21666666666667,
      158.3,
      164.38333333333333,
      170.48333333333332,
      176.56666666666666,
      182.65,
      188.75
    ],
    "total_num_frames": 11326
  },
  "target": "<think>\nStep 1: find the air conditioner, the fire extinguisher and the microscope.\nStep 2: standing at the air conditioner and facing the fire extinguisher, I find the microscope in front of me, on my right.\nStep 3: I face away from the fire extinguisher by making a half turn. Front and back swap, and left and right swap.\nSo I find the position of the microscope at my back-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "d4623b8a323bafcf20d914c7532d0503e0adcf1ab62ec565fd2aee216ac00bbc"
  },
  "candidate_id": "ground-7c8f80439921422ce10cef2dd7ec082d599dd614f044827b0269afce69748b01",
  "label_row_keys": [
    "q030340f22c178d8e92c9fc6a"
  ]
}
```

