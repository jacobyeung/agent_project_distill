Complete generated rows for grammar, heading, frame preservation and answer review.

## 1. qd5cd4d7561678b8fc2457da4-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qd5cd4d7561678b8fc2457da4-p1",
      "source_store_i": 69518,
      "source_row_sha256": "98ad605448d21370eae2b62a810a4b259df1e7a98502f963bb5b60484b2af9ff",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qd5cd4d7561678b8fc2457da4-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd992fef5b77c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      315,
      630,
      946,
      1261,
      1576,
      1892,
      2207,
      2523,
      2838,
      3153,
      3469,
      3784,
      4100,
      4415,
      4730,
      5046,
      5361,
      5676,
      5992,
      6307,
      6623,
      6938,
      7253,
      7569,
      7884,
      8200,
      8515,
      8830,
      9146,
      9461,
      9777
    ],
    "frames": [
      {
        "path": "/data2/k6tk/45/45f8586ea6406487a88ddeeb382861361c0a03753f58c2a9b4b94333f08d57ed.png",
        "sha256": "45f8586ea6406487a88ddeeb382861361c0a03753f58c2a9b4b94333f08d57ed"
      },
      {
        "path": "/data2/k6tk/bc/bc06d00d138254f86c7665327f438040e6be1aeea07b13d2a93cdbfe7bd04892.png",
        "sha256": "bc06d00d138254f86c7665327f438040e6be1aeea07b13d2a93cdbfe7bd04892"
      },
      {
        "path": "/data2/k6tk/84/84fdfcb22cb034da87f1067d5f3fbec76451e83377541b033be58334726ead8c.png",
        "sha256": "84fdfcb22cb034da87f1067d5f3fbec76451e83377541b033be58334726ead8c"
      },
      {
        "path": "/data2/k6tk/66/667df7495dba353894b3a30d4df9f270fb53299299cccbf2a00afcb2a1ab3d0c.png",
        "sha256": "667df7495dba353894b3a30d4df9f270fb53299299cccbf2a00afcb2a1ab3d0c"
      },
      {
        "path": "/data2/k6tk/82/82e950cb902753c2d89e356117948b4d451e9724ee1b07ab1301b74c7525453b.png",
        "sha256": "82e950cb902753c2d89e356117948b4d451e9724ee1b07ab1301b74c7525453b"
      },
      {
        "path": "/data2/k6tk/f0/f0a9d868800be0385a382b71c6b3f99fc81aa93c6f1ddd6d8c558afa1a9b6cc7.png",
        "sha256": "f0a9d868800be0385a382b71c6b3f99fc81aa93c6f1ddd6d8c558afa1a9b6cc7"
      },
      {
        "path": "/data2/k6tk/67/671cb8e4db75ebae0687f3ad73fcc45252d4d3d7cf85972aa65a52dc6528f665.png",
        "sha256": "671cb8e4db75ebae0687f3ad73fcc45252d4d3d7cf85972aa65a52dc6528f665"
      },
      {
        "path": "/data2/k6tk/16/161ab588e3b6832555065a64be74b1bd98f536dc2f809f7d9bc34dd0a8d9411e.png",
        "sha256": "161ab588e3b6832555065a64be74b1bd98f536dc2f809f7d9bc34dd0a8d9411e"
      },
      {
        "path": "/data2/k6tk/41/41948c4ad98aa18cd08a40781aedf77cddc5d0268d9c781ba33e49101d42434b.png",
        "sha256": "41948c4ad98aa18cd08a40781aedf77cddc5d0268d9c781ba33e49101d42434b"
      },
      {
        "path": "/data2/k6tk/27/27bcfceb7bf53d808e2ee26bab30dcb0802462aaf6a3d30c82f65c7a8438f159.png",
        "sha256": "27bcfceb7bf53d808e2ee26bab30dcb0802462aaf6a3d30c82f65c7a8438f159"
      },
      {
        "path": "/data2/k6tk/ab/aba05c10d6e975c8e1c9ee5c8352104e39b5a26143c47815bcee7daf09505277.png",
        "sha256": "aba05c10d6e975c8e1c9ee5c8352104e39b5a26143c47815bcee7daf09505277"
      },
      {
        "path": "/data2/k6tk/3b/3b4dfe4425fded3c7aed31fcc1e8ce5f8054f29227969b84514e7f51af1dd051.png",
        "sha256": "3b4dfe4425fded3c7aed31fcc1e8ce5f8054f29227969b84514e7f51af1dd051"
      },
      {
        "path": "/data2/k6tk/c8/c84b415dfbdb832e2d49a73bbd2dc9ec23b2f8d6704f22db95fc65890143d94f.png",
        "sha256": "c84b415dfbdb832e2d49a73bbd2dc9ec23b2f8d6704f22db95fc65890143d94f"
      },
      {
        "path": "/data2/k6tk/94/9448cfdd5eb1399930bc80ede98881828be3148aded1c111c5661e87f6388539.png",
        "sha256": "9448cfdd5eb1399930bc80ede98881828be3148aded1c111c5661e87f6388539"
      },
      {
        "path": "/data2/k6tk/a0/a0f8944921a936d41b3ce424479c7571c7042a2c9a05ef654f57227c45d82c67.png",
        "sha256": "a0f8944921a936d41b3ce424479c7571c7042a2c9a05ef654f57227c45d82c67"
      },
      {
        "path": "/data2/k6tk/77/77e59d99f731281e4a1918eecfb3426528ec3f215917c98f45a9fd1ed5aa577e.png",
        "sha256": "77e59d99f731281e4a1918eecfb3426528ec3f215917c98f45a9fd1ed5aa577e"
      },
      {
        "path": "/data2/k6tk/cc/cc793576be7dcac52eed41e13ea9b9646d62082b144544a6efae75f6ddbe2386.png",
        "sha256": "cc793576be7dcac52eed41e13ea9b9646d62082b144544a6efae75f6ddbe2386"
      },
      {
        "path": "/data2/k6tk/5a/5a2b74164488d4268ba355f9dfb77a5020abb579f637c9fffc36cb1169d8e505.png",
        "sha256": "5a2b74164488d4268ba355f9dfb77a5020abb579f637c9fffc36cb1169d8e505"
      },
      {
        "path": "/data2/k6tk/12/120e65d4255f35d890aeb9488a530d68e05c8d617c4f0dad10a77316a0abdf12.png",
        "sha256": "120e65d4255f35d890aeb9488a530d68e05c8d617c4f0dad10a77316a0abdf12"
      },
      {
        "path": "/data2/k6tk/30/30119015f125d0c9379466b9f426a2a860f2ecfac21b4a3e9a1e3443243484bd.png",
        "sha256": "30119015f125d0c9379466b9f426a2a860f2ecfac21b4a3e9a1e3443243484bd"
      },
      {
        "path": "/data2/k6tk/0e/0e40eeaae1742b737b066c873a448bbb62a13a907e6ecc7ba1571b85065d2e87.png",
        "sha256": "0e40eeaae1742b737b066c873a448bbb62a13a907e6ecc7ba1571b85065d2e87"
      },
      {
        "path": "/data2/k6tk/fd/fd78916cdec50c9e86e491065a24d6cf289eee9780df4b8d36799eb2a0df5428.png",
        "sha256": "fd78916cdec50c9e86e491065a24d6cf289eee9780df4b8d36799eb2a0df5428"
      },
      {
        "path": "/data2/k6tk/cf/cff5e831f48b7157d5b19e883a8f5cb3cbd6ad9db038eed7d85337b44b4bed91.png",
        "sha256": "cff5e831f48b7157d5b19e883a8f5cb3cbd6ad9db038eed7d85337b44b4bed91"
      },
      {
        "path": "/data2/k6tk/40/401c90fa62601f3c4045edaccf7f00877adb5ec23e862ae42fd0836620f068e9.png",
        "sha256": "401c90fa62601f3c4045edaccf7f00877adb5ec23e862ae42fd0836620f068e9"
      },
      {
        "path": "/data2/k6tk/37/37862714fce223a052dd6e6774f0c65f82a884efeccb564187d31d7f380dd80b.png",
        "sha256": "37862714fce223a052dd6e6774f0c65f82a884efeccb564187d31d7f380dd80b"
      },
      {
        "path": "/data2/k6tk/27/272cb1e9e855e7841d1de79e6e7b2cc74487ead93105ca8573826eaf31377ae2.png",
        "sha256": "272cb1e9e855e7841d1de79e6e7b2cc74487ead93105ca8573826eaf31377ae2"
      },
      {
        "path": "/data2/k6tk/f9/f9063fc46c49fca5db86929d49668efa3b415d7ada258a00d9045aee1dcc95e1.png",
        "sha256": "f9063fc46c49fca5db86929d49668efa3b415d7ada258a00d9045aee1dcc95e1"
      },
      {
        "path": "/data2/k6tk/fb/fb2684781ceec733cb953b93adb3833480f7449f4def09fef68e27e434ab01f1.png",
        "sha256": "fb2684781ceec733cb953b93adb3833480f7449f4def09fef68e27e434ab01f1"
      },
      {
        "path": "/data2/k6tk/36/36842dabf91407ea1e70bb2444defdef1f42be592d223b9d7169253bff712462.png",
        "sha256": "36842dabf91407ea1e70bb2444defdef1f42be592d223b9d7169253bff712462"
      },
      {
        "path": "/data2/k6tk/0d/0d6fa331b5cdef6f586ccff301f59975ab9af23fd0deb48adb2073f579b79662.png",
        "sha256": "0d6fa331b5cdef6f586ccff301f59975ab9af23fd0deb48adb2073f579b79662"
      },
      {
        "path": "/data2/k6tk/9e/9e98134889558c1dc9dd7355cf6d789b748968abdb64dee4226ada672217f833.png",
        "sha256": "9e98134889558c1dc9dd7355cf6d789b748968abdb64dee4226ada672217f833"
      },
      {
        "path": "/data2/k6tk/3d/3d21d051d099283f5196f956355e73f025aa0a1b74c20de1c8cb95ce2e0ed163.png",
        "sha256": "3d21d051d099283f5196f956355e73f025aa0a1b74c20de1c8cb95ce2e0ed163"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the suitcase, face away from the microwave. Is the power strip to your left or right?",
    "timestamps": [
      0.0,
      5.25,
      10.5,
      15.766666666666667,
      21.016666666666666,
      26.266666666666666,
      31.533333333333335,
      36.78333333333333,
      42.05,
      47.3,
      52.55,
      57.81666666666667,
      63.06666666666667,
      68.33333333333333,
      73.58333333333333,
      78.83333333333333,
      84.1,
      89.35,
      94.6,
      99.86666666666666,
      105.11666666666666,
      110.38333333333334,
      115.63333333333334,
      120.88333333333334,
      126.15,
      131.4,
      136.66666666666666,
      141.91666666666666,
      147.16666666666666,
      152.43333333333334,
      157.68333333333334,
      162.95
    ],
    "total_num_frames": 9778
  },
  "target": "<think>\nStep 1: find the suitcase, the microwave and the power strip.\nStep 2: I find the power strip to my right when I stand at the suitcase facing the microwave.\nStep 3: I face away from the microwave by making a half turn. Front and back swap, and left and right swap.\nSo I find the power strip to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qd5cd4d7561678b8fc2457da4",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "b01b37d58f142a3ae3e836de023e3bfddf9b0b46a0072fde1ce3912d021ded1e"
  },
  "facing": "away",
  "candidate_id": "ground-792162d03eb56ca0b07ad94f36fba51c33d49afdea0226db1768d17f4f95785e",
  "label_row_keys": [
    "qd5cd4d7561678b8fc2457da4-p1"
  ]
}
```

## 2. q96fd5a3bf2161c42a712c85f_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q96fd5a3bf2161c42a712c85f",
      "source_store_i": 9855,
      "source_row_sha256": "68974b810751a8d85caa29e35e43aae7909979ff3486521af2a88599eff20f63",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q96fd5a3bf2161c42a712c85f_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v71cd1435bcfc",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      232,
      465,
      697,
      930,
      1163,
      1395,
      1628,
      1860,
      2093,
      2326,
      2558,
      2791,
      3023,
      3256,
      3489,
      3721,
      3954,
      4187,
      4419,
      4652,
      4884,
      5117,
      5350,
      5582,
      5815,
      6047,
      6280,
      6513,
      6745,
      6978,
      7211
    ],
    "frames": [
      {
        "path": "/data2/k6tk/26/266a940c38bf37eb31a288045f8cf6024ac204289c68743cd9e57d7765ef8909.png",
        "sha256": "266a940c38bf37eb31a288045f8cf6024ac204289c68743cd9e57d7765ef8909"
      },
      {
        "path": "/data2/k6tk/f3/f3ae640688be7eb78569099508362b7b7eaa4ef81cbcd1a026968a2f28c24dd0.png",
        "sha256": "f3ae640688be7eb78569099508362b7b7eaa4ef81cbcd1a026968a2f28c24dd0"
      },
      {
        "path": "/data2/k6tk/28/286a3d12f242f6344651778769d7fae586cbdfce328a66b7016907e3346098ba.png",
        "sha256": "286a3d12f242f6344651778769d7fae586cbdfce328a66b7016907e3346098ba"
      },
      {
        "path": "/data2/k6tk/82/826e09842f6805f55fb2fbd7114f60ab7bb2147a04a0e7553fc2af1d16b20175.png",
        "sha256": "826e09842f6805f55fb2fbd7114f60ab7bb2147a04a0e7553fc2af1d16b20175"
      },
      {
        "path": "/data2/k6tk/07/07d662d3dff7502436dc324b7f56e98458c64234dc6871862b9e1cf02ba2fe66.png",
        "sha256": "07d662d3dff7502436dc324b7f56e98458c64234dc6871862b9e1cf02ba2fe66"
      },
      {
        "path": "/data2/k6tk/6f/6f4f2c83eccc4883585bdca82ce7073f411ea5a25259b6f8de991ab3117fbca7.png",
        "sha256": "6f4f2c83eccc4883585bdca82ce7073f411ea5a25259b6f8de991ab3117fbca7"
      },
      {
        "path": "/data2/k6tk/f4/f493e73930f0dc1ef0da945d3299792f7a411b0d5bf1c5d1e6ccee4d2d9f5bde.png",
        "sha256": "f493e73930f0dc1ef0da945d3299792f7a411b0d5bf1c5d1e6ccee4d2d9f5bde"
      },
      {
        "path": "/data2/k6tk/c7/c7401f44ec9bf3108b9c53d97b74f7085e6523f5fb1ce249420bfda7dbaab9c6.png",
        "sha256": "c7401f44ec9bf3108b9c53d97b74f7085e6523f5fb1ce249420bfda7dbaab9c6"
      },
      {
        "path": "/data2/k6tk/1f/1fa8f3deb3b28037f8f88ffc515a3e4a43730a00d9dc36bf9315e2ae56aa9536.png",
        "sha256": "1fa8f3deb3b28037f8f88ffc515a3e4a43730a00d9dc36bf9315e2ae56aa9536"
      },
      {
        "path": "/data2/k6tk/64/64d478784e8a7c07baae876d75a1294c234699f5e85c40755554bddecf7c247a.png",
        "sha256": "64d478784e8a7c07baae876d75a1294c234699f5e85c40755554bddecf7c247a"
      },
      {
        "path": "/data2/k6tk/c7/c7b2664b784c92bce0bcac70a498e95c96281efb4d9d70cab7b0d4f1841f7b9d.png",
        "sha256": "c7b2664b784c92bce0bcac70a498e95c96281efb4d9d70cab7b0d4f1841f7b9d"
      },
      {
        "path": "/data2/k6tk/37/374b432e285da1c4324dd515b517f5ec13c3baae523cf8d0f4dde93b68356407.png",
        "sha256": "374b432e285da1c4324dd515b517f5ec13c3baae523cf8d0f4dde93b68356407"
      },
      {
        "path": "/data2/k6tk/7f/7f2ffcebb6a94639a72c117072fe138e3a8174ab1957cd69f5834c1e157ba369.png",
        "sha256": "7f2ffcebb6a94639a72c117072fe138e3a8174ab1957cd69f5834c1e157ba369"
      },
      {
        "path": "/data2/k6tk/ad/ada4bf1f29f78990591f64d06d299de4f6c51610824346fe30d724c16d25e032.png",
        "sha256": "ada4bf1f29f78990591f64d06d299de4f6c51610824346fe30d724c16d25e032"
      },
      {
        "path": "/data2/k6tk/eb/ebae49ddfcd4f77c6e03324a0d72ab3afeeb82bc976ae7ade2c316cd98bed7e2.png",
        "sha256": "ebae49ddfcd4f77c6e03324a0d72ab3afeeb82bc976ae7ade2c316cd98bed7e2"
      },
      {
        "path": "/data2/k6tk/6a/6a367f2c4ba7deb1e315658f7a79ea7d86a64d55272afbfcc2df6813cdbb9c14.png",
        "sha256": "6a367f2c4ba7deb1e315658f7a79ea7d86a64d55272afbfcc2df6813cdbb9c14"
      },
      {
        "path": "/data2/k6tk/51/514404b4cede10d1a4b9381d16a89fa00ae8296fcf2185afeb9ac2024c91c40a.png",
        "sha256": "514404b4cede10d1a4b9381d16a89fa00ae8296fcf2185afeb9ac2024c91c40a"
      },
      {
        "path": "/data2/k6tk/ec/ec1f6127fe7e32ec7e68a5f68b65508c2a240fb024faf8ea48d48528a0bd89c2.png",
        "sha256": "ec1f6127fe7e32ec7e68a5f68b65508c2a240fb024faf8ea48d48528a0bd89c2"
      },
      {
        "path": "/data2/k6tk/13/13b275f946f96d6338aaa28e8e23957ccbfe7a4ce08354fdba6281546d70cd7f.png",
        "sha256": "13b275f946f96d6338aaa28e8e23957ccbfe7a4ce08354fdba6281546d70cd7f"
      },
      {
        "path": "/data2/k6tk/9a/9a60c95fea535000063628fba441d31b116ecb65423e56ddd6f6adc1d6b88a41.png",
        "sha256": "9a60c95fea535000063628fba441d31b116ecb65423e56ddd6f6adc1d6b88a41"
      },
      {
        "path": "/data2/k6tk/cf/cf8e93c62fb4cd46ad0103ae8e898018ae60cdd50e724fcc5fe4fcb0fdcc0334.png",
        "sha256": "cf8e93c62fb4cd46ad0103ae8e898018ae60cdd50e724fcc5fe4fcb0fdcc0334"
      },
      {
        "path": "/data2/k6tk/51/51252d5b1e449b19eaa60ca5b95f31d430d19a47b551ce28f5ae6405e685d45a.png",
        "sha256": "51252d5b1e449b19eaa60ca5b95f31d430d19a47b551ce28f5ae6405e685d45a"
      },
      {
        "path": "/data2/k6tk/4c/4cb1f870744b2092525c1f04fa845db0991b5b7b15380fa79e5a61f5fc2c0000.png",
        "sha256": "4cb1f870744b2092525c1f04fa845db0991b5b7b15380fa79e5a61f5fc2c0000"
      },
      {
        "path": "/data2/k6tk/fd/fd5323853755d94325229b961da98f680c78f9ae9e13354ce8422b5a6c5e2305.png",
        "sha256": "fd5323853755d94325229b961da98f680c78f9ae9e13354ce8422b5a6c5e2305"
      },
      {
        "path": "/data2/k6tk/2e/2e1072d268fba3cde7924acdb589cb44ed09b37b7a2eb5f32d5d4a241d35b987.png",
        "sha256": "2e1072d268fba3cde7924acdb589cb44ed09b37b7a2eb5f32d5d4a241d35b987"
      },
      {
        "path": "/data2/k6tk/0b/0bd56e9e330fa2d0b0b9c3b8e0e0e948408a4399042f49a9d340300dbe4b5556.png",
        "sha256": "0bd56e9e330fa2d0b0b9c3b8e0e0e948408a4399042f49a9d340300dbe4b5556"
      },
      {
        "path": "/data2/k6tk/8f/8f3db5db85d8fe73d277148e381066c36b7a14b2b836f76bdbbf44c0e32a7490.png",
        "sha256": "8f3db5db85d8fe73d277148e381066c36b7a14b2b836f76bdbbf44c0e32a7490"
      },
      {
        "path": "/data2/k6tk/f0/f09f73f765025e8aef0221b3162d948a7a096ee0887dcf19555cb742adfb045c.png",
        "sha256": "f09f73f765025e8aef0221b3162d948a7a096ee0887dcf19555cb742adfb045c"
      },
      {
        "path": "/data2/k6tk/82/82b87d2cc1c1ac064f7254af510802255d793d60b75bafb6ed20a31ece586b73.png",
        "sha256": "82b87d2cc1c1ac064f7254af510802255d793d60b75bafb6ed20a31ece586b73"
      },
      {
        "path": "/data2/k6tk/5a/5a8cdfadbabe449e5d31653189fe8b81c82ce289836d889020993d3c6112a38b.png",
        "sha256": "5a8cdfadbabe449e5d31653189fe8b81c82ce289836d889020993d3c6112a38b"
      },
      {
        "path": "/data2/k6tk/59/594ca71d5f51112cd186c8cd4751e25045cdd780428d073b4626a9315ad37b64.png",
        "sha256": "594ca71d5f51112cd186c8cd4751e25045cdd780428d073b4626a9315ad37b64"
      },
      {
        "path": "/data2/k6tk/89/899ce5bd97b00ea83a0bf1185d8d478e382974290a6aed2080b09c49a0bf9c51.png",
        "sha256": "899ce5bd97b00ea83a0bf1185d8d478e382974290a6aed2080b09c49a0bf9c51"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the basket and facing away from the blanket, is the hole puncher to the left or the right of the blanket?",
    "timestamps": [
      0.0,
      3.8666666666666667,
      7.75,
      11.616666666666667,
      15.5,
      19.383333333333333,
      23.25,
      27.133333333333333,
      31.0,
      34.88333333333333,
      38.766666666666666,
      42.63333333333333,
      46.516666666666666,
      50.38333333333333,
      54.266666666666666,
      58.15,
      62.016666666666666,
      65.9,
      69.78333333333333,
      73.65,
      77.53333333333333,
      81.4,
      85.28333333333333,
      89.16666666666667,
      93.03333333333333,
      96.91666666666667,
      100.78333333333333,
      104.66666666666667,
      108.55,
      112.41666666666667,
      116.3,
      120.18333333333334
    ],
    "total_num_frames": 7212
  },
  "target": "<think>\nStep 1: find the basket, the blanket and the hole puncher.\nStep 2: standing at the basket and facing the blanket, I find the hole puncher to my right.\nStep 3: I face away from the blanket by making a half turn. Front and back swap, and left and right swap.\nSo I find the hole puncher to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "35becb3a2cc1017c163a30d23e2adfdfb8042ae1b742b9ac75f1661e29f7a92d"
  },
  "facing": "away",
  "candidate_id": "ground-611339a1cad9f4be0aa6792e631f78ddc3f336637083023b64199063e2aeabb9",
  "label_row_keys": [
    "q96fd5a3bf2161c42a712c85f"
  ]
}
```

## 3. q6c94f467ad0f40744de90e93-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q6c94f467ad0f40744de90e93-p1",
      "source_store_i": 56347,
      "source_row_sha256": "b62682bae54be7660522d77ec9f082f631e654f3da248785b49231404bcac47a",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q6c94f467ad0f40744de90e93-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v735ae3c45116",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      449,
      898,
      1347,
      1796,
      2245,
      2694,
      3143,
      3592,
      4041,
      4490,
      4940,
      5389,
      5838,
      6287,
      6736,
      7185,
      7634,
      8083,
      8532,
      8981,
      9431,
      9880,
      10329,
      10778,
      11227,
      11676,
      12125,
      12574,
      13023,
      13472,
      13922
    ],
    "frames": [
      {
        "path": "/data2/k6tk/2a/2a9c12827db2f27683c83c6121fe00f13faeb0818dd5ed737868228aaefe719d.png",
        "sha256": "2a9c12827db2f27683c83c6121fe00f13faeb0818dd5ed737868228aaefe719d"
      },
      {
        "path": "/data2/k6tk/d5/d564171a21d86172a86e537a2a565ac6ed3df0e8023270c0cfbfdd39741d4d4d.png",
        "sha256": "d564171a21d86172a86e537a2a565ac6ed3df0e8023270c0cfbfdd39741d4d4d"
      },
      {
        "path": "/data2/k6tk/2c/2c93704b6291d1a31a044553939993a52dc229d9abd61ab86e12e3e9e2c6b68f.png",
        "sha256": "2c93704b6291d1a31a044553939993a52dc229d9abd61ab86e12e3e9e2c6b68f"
      },
      {
        "path": "/data2/k6tk/c2/c26e870fd51b003e2d2cde80f66292c3c5bbc96d897e5d21de505d695b982bbb.png",
        "sha256": "c26e870fd51b003e2d2cde80f66292c3c5bbc96d897e5d21de505d695b982bbb"
      },
      {
        "path": "/data2/k6tk/ba/ba1670d36ff9bad2153d6e2863cb28fa0321ebe4bb0e57a13e885926fd268e0f.png",
        "sha256": "ba1670d36ff9bad2153d6e2863cb28fa0321ebe4bb0e57a13e885926fd268e0f"
      },
      {
        "path": "/data2/k6tk/5a/5a8ee9089a0793fa6b12c119fe3b28226d79b13ea335907053e0304716835484.png",
        "sha256": "5a8ee9089a0793fa6b12c119fe3b28226d79b13ea335907053e0304716835484"
      },
      {
        "path": "/data2/k6tk/5a/5a4fcf2922636ed4e673ef5d7dbb301650b8d12f9b7335a978545d7f5066bd99.png",
        "sha256": "5a4fcf2922636ed4e673ef5d7dbb301650b8d12f9b7335a978545d7f5066bd99"
      },
      {
        "path": "/data2/k6tk/07/07378dd090732df725d19bb3bef9742b1ec1b17ff8903838ce39e05987d628e3.png",
        "sha256": "07378dd090732df725d19bb3bef9742b1ec1b17ff8903838ce39e05987d628e3"
      },
      {
        "path": "/data2/k6tk/71/7169463ed1d621573e7e7911409e6025914fc6345bfd34c2fc4f493a502e55ff.png",
        "sha256": "7169463ed1d621573e7e7911409e6025914fc6345bfd34c2fc4f493a502e55ff"
      },
      {
        "path": "/data2/k6tk/c5/c5d5e0acc072fcdfba5996a064592c12c9d4b2bc17bb0d9da7f7b77b93587647.png",
        "sha256": "c5d5e0acc072fcdfba5996a064592c12c9d4b2bc17bb0d9da7f7b77b93587647"
      },
      {
        "path": "/data2/k6tk/7e/7ec4642b54e704f07bca15cd54bbb3e559a3b50de2ece0b3e45cca1444964868.png",
        "sha256": "7ec4642b54e704f07bca15cd54bbb3e559a3b50de2ece0b3e45cca1444964868"
      },
      {
        "path": "/data2/k6tk/59/591cb89fccbf1911b1e19e9c6015c14bae0afd87f77d987ef4273eed361c962a.png",
        "sha256": "591cb89fccbf1911b1e19e9c6015c14bae0afd87f77d987ef4273eed361c962a"
      },
      {
        "path": "/data2/k6tk/eb/eb74dae045a3b7967e5c4641e0c7d371fd01e97f9165dcdb9a513860db34ce09.png",
        "sha256": "eb74dae045a3b7967e5c4641e0c7d371fd01e97f9165dcdb9a513860db34ce09"
      },
      {
        "path": "/data2/k6tk/3b/3b1d484e9f0ea7c6d66481d59b1b160bb93cc54bb889464005389a49ff03e097.png",
        "sha256": "3b1d484e9f0ea7c6d66481d59b1b160bb93cc54bb889464005389a49ff03e097"
      },
      {
        "path": "/data2/k6tk/b5/b51e2d86385e3a919e739e8c4bdc982708c7071ea985d757599c2d87a8c980a8.png",
        "sha256": "b51e2d86385e3a919e739e8c4bdc982708c7071ea985d757599c2d87a8c980a8"
      },
      {
        "path": "/data2/k6tk/f8/f8997628ebba4c1cb2bca3174fdea1fb0a877824880289eb49f3dead8c01aa5e.png",
        "sha256": "f8997628ebba4c1cb2bca3174fdea1fb0a877824880289eb49f3dead8c01aa5e"
      },
      {
        "path": "/data2/k6tk/6c/6c8731acc527b67b9dfed931478e28e9ac9e1ab2398ee283a8ebad6377fe3152.png",
        "sha256": "6c8731acc527b67b9dfed931478e28e9ac9e1ab2398ee283a8ebad6377fe3152"
      },
      {
        "path": "/data2/k6tk/b4/b48656864b009689be3af094a6e08e37277e485e5d040281988639bdecb3fe50.png",
        "sha256": "b48656864b009689be3af094a6e08e37277e485e5d040281988639bdecb3fe50"
      },
      {
        "path": "/data2/k6tk/b3/b3ea00fb5ed54865c3aa209057b6a30cf6531f09cbaac111e897793ded27ff9f.png",
        "sha256": "b3ea00fb5ed54865c3aa209057b6a30cf6531f09cbaac111e897793ded27ff9f"
      },
      {
        "path": "/data2/k6tk/c4/c41f11b6ed27528381171943770254ff6a0c8837a47e9799e09c2a3b7f3a85b9.png",
        "sha256": "c41f11b6ed27528381171943770254ff6a0c8837a47e9799e09c2a3b7f3a85b9"
      },
      {
        "path": "/data2/k6tk/aa/aa0253aa97e5dc9f1457d9a84f1d45ff12289e61056d2d43e1a54883cb70dc03.png",
        "sha256": "aa0253aa97e5dc9f1457d9a84f1d45ff12289e61056d2d43e1a54883cb70dc03"
      },
      {
        "path": "/data2/k6tk/69/69095472c9f2f9b57740eef8b4cfa376d50da23bb09f2a17437baf19252ce374.png",
        "sha256": "69095472c9f2f9b57740eef8b4cfa376d50da23bb09f2a17437baf19252ce374"
      },
      {
        "path": "/data2/k6tk/46/462b40aa4d5a7dc0cdba029b10ecd2fe9c39b473dd4b0a242cf23fa3e8091160.png",
        "sha256": "462b40aa4d5a7dc0cdba029b10ecd2fe9c39b473dd4b0a242cf23fa3e8091160"
      },
      {
        "path": "/data2/k6tk/a8/a8003165ad483f228311ea96ee84cbdac76b8f84470439425a36c7fed530ebd9.png",
        "sha256": "a8003165ad483f228311ea96ee84cbdac76b8f84470439425a36c7fed530ebd9"
      },
      {
        "path": "/data2/k6tk/79/79386065f0a5486be3e2bca89b7566d0d781cc1e2590a87f25ac6f4b90d34c48.png",
        "sha256": "79386065f0a5486be3e2bca89b7566d0d781cc1e2590a87f25ac6f4b90d34c48"
      },
      {
        "path": "/data2/k6tk/f8/f84af299e4db727a40e3f2ec0f5e36cdaa8c0fc652073d0fd05e7c72172545a5.png",
        "sha256": "f84af299e4db727a40e3f2ec0f5e36cdaa8c0fc652073d0fd05e7c72172545a5"
      },
      {
        "path": "/data2/k6tk/7d/7dfac303f306299e69283ebdcf4117c9d901df383f5b25de05f97a11279fbf9c.png",
        "sha256": "7dfac303f306299e69283ebdcf4117c9d901df383f5b25de05f97a11279fbf9c"
      },
      {
        "path": "/data2/k6tk/a0/a054bbdc34f6a1a48e7740e313c06777cad50f312697c4aced5fa3a730674b1a.png",
        "sha256": "a054bbdc34f6a1a48e7740e313c06777cad50f312697c4aced5fa3a730674b1a"
      },
      {
        "path": "/data2/k6tk/4a/4ac66612611332660c12e8db42fdf48ecd3eb6e96762059b48882b3e990a0eba.png",
        "sha256": "4ac66612611332660c12e8db42fdf48ecd3eb6e96762059b48882b3e990a0eba"
      },
      {
        "path": "/data2/k6tk/7e/7e844aee1fac21f3272b8b57efd0fd9d7dfcf72cb06869d4b06f8dae78ef36bb.png",
        "sha256": "7e844aee1fac21f3272b8b57efd0fd9d7dfcf72cb06869d4b06f8dae78ef36bb"
      },
      {
        "path": "/data2/k6tk/0d/0d54cba18b3d71b03e8d4b47b646768529af1f85518a02f43cc9751d02bec2e4.png",
        "sha256": "0d54cba18b3d71b03e8d4b47b646768529af1f85518a02f43cc9751d02bec2e4"
      },
      {
        "path": "/data2/k6tk/3b/3b4c0a557e14e94b2dd00d9c61855ed8a3b5ce7dae8f3a00c46eacd9d35e0862.png",
        "sha256": "3b4c0a557e14e94b2dd00d9c61855ed8a3b5ce7dae8f3a00c46eacd9d35e0862"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "While standing by the bottle and facing away from the bucket, decide whether the stair lies to your left or your right.",
    "timestamps": [
      0.0,
      7.483333333333333,
      14.966666666666667,
      22.45,
      29.933333333333334,
      37.416666666666664,
      44.9,
      52.38333333333333,
      59.86666666666667,
      67.35,
      74.83333333333333,
      82.33333333333333,
      89.81666666666666,
      97.3,
      104.78333333333333,
      112.26666666666667,
      119.75,
      127.23333333333333,
      134.71666666666667,
      142.2,
      149.68333333333334,
      157.18333333333334,
      164.66666666666666,
      172.15,
      179.63333333333333,
      187.11666666666667,
      194.6,
      202.08333333333334,
      209.56666666666666,
      217.05,
      224.53333333333333,
      232.03333333333333
    ],
    "total_num_frames": 13923
  },
  "target": "<think>\nStep 1: find the bottle, the bucket and the stair.\nStep 2: facing the bucket from the bottle, I find the stair to my right.\nStep 3: I face away from the bucket by making a half turn. Front and back swap, and left and right swap.\nSo I find the stair to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q6c94f467ad0f40744de90e93",
  "paraphrase_template": "easy_side",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "12e45f2039d1b96bd18b07146f1e824e694b285d3896c6688b8a59e2e99a7de3"
  },
  "facing": "away",
  "candidate_id": "ground-8836333b9b72a435b1efdb6c0af403e8f49372bfeb99681a1122ad91216fc581",
  "label_row_keys": [
    "q6c94f467ad0f40744de90e93-p1"
  ]
}
```

## 4. qda1da273906582cb89b9761b_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qda1da273906582cb89b9761b",
      "source_store_i": 12079,
      "source_row_sha256": "cc1fa26fe274754a0436fd0b6540637b4a8b16bf3fad91a871cccbe1eb243490",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qda1da273906582cb89b9761b_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd3b7b32b2b4d",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      311,
      622,
      934,
      1245,
      1557,
      1868,
      2180,
      2491,
      2803,
      3114,
      3426,
      3737,
      4049,
      4360,
      4672,
      4983,
      5295,
      5606,
      5918,
      6229,
      6541,
      6852,
      7164,
      7475,
      7787,
      8098,
      8410,
      8721,
      9033,
      9344,
      9656
    ],
    "frames": [
      {
        "path": "/data2/k6tk/50/50c60ea6d25ba088cfbce2cc764f00561e285e4cd556a75afe22619a64522b21.png",
        "sha256": "50c60ea6d25ba088cfbce2cc764f00561e285e4cd556a75afe22619a64522b21"
      },
      {
        "path": "/data2/k6tk/fd/fd95bd1d6f7674bc131241bc9efb7f8352badba2e4a8600f3d0cbd4315968713.png",
        "sha256": "fd95bd1d6f7674bc131241bc9efb7f8352badba2e4a8600f3d0cbd4315968713"
      },
      {
        "path": "/data2/k6tk/09/090abc979e31d430cfa5f77ea96ae32e14d45a1d312ea5bb63f59713d3b7e6df.png",
        "sha256": "090abc979e31d430cfa5f77ea96ae32e14d45a1d312ea5bb63f59713d3b7e6df"
      },
      {
        "path": "/data2/k6tk/07/0762a20d46edadceb04b5e3e0d31e946081a0815896787ddd6fd7f7b28827bda.png",
        "sha256": "0762a20d46edadceb04b5e3e0d31e946081a0815896787ddd6fd7f7b28827bda"
      },
      {
        "path": "/data2/k6tk/d2/d257b522484897c45434e514b1916b9a88c8ff74f0c2ac20bb9d8434fc22ab5c.png",
        "sha256": "d257b522484897c45434e514b1916b9a88c8ff74f0c2ac20bb9d8434fc22ab5c"
      },
      {
        "path": "/data2/k6tk/83/83aec99ab6715d48462ea75006ad811cc058d16af8f9b0a5db4512c713f99767.png",
        "sha256": "83aec99ab6715d48462ea75006ad811cc058d16af8f9b0a5db4512c713f99767"
      },
      {
        "path": "/data2/k6tk/8a/8a3db58f2389cc9f6791b66717fadaa793ab970b7f9ee2faca809f4baedf7371.png",
        "sha256": "8a3db58f2389cc9f6791b66717fadaa793ab970b7f9ee2faca809f4baedf7371"
      },
      {
        "path": "/data2/k6tk/50/5083ddd00f59b5cc457b1a344b5cc5508fce5a44f0b49ca005fafb1f3d7277c2.png",
        "sha256": "5083ddd00f59b5cc457b1a344b5cc5508fce5a44f0b49ca005fafb1f3d7277c2"
      },
      {
        "path": "/data2/k6tk/f0/f0d1293d1072f4baee837029da6cfd88834c0025857466b862316c66c0978d9e.png",
        "sha256": "f0d1293d1072f4baee837029da6cfd88834c0025857466b862316c66c0978d9e"
      },
      {
        "path": "/data2/k6tk/38/3865f553983b1070867d9c426d7a812b00a09ee7da9eb08cea6d151daa75c287.png",
        "sha256": "3865f553983b1070867d9c426d7a812b00a09ee7da9eb08cea6d151daa75c287"
      },
      {
        "path": "/data2/k6tk/ae/ae693e670ec249ea898f2359c75f1d59125d6302a1d49d02d5ae3ccffbb963b5.png",
        "sha256": "ae693e670ec249ea898f2359c75f1d59125d6302a1d49d02d5ae3ccffbb963b5"
      },
      {
        "path": "/data2/k6tk/99/9910271e85f9e611029cd31d87360c3db3794128d177849ea993bde1cba12f2e.png",
        "sha256": "9910271e85f9e611029cd31d87360c3db3794128d177849ea993bde1cba12f2e"
      },
      {
        "path": "/data2/k6tk/1a/1af0a458e8dc79be12ab166e16e15a439173347398e7c0f3340f8883b3b0f79d.png",
        "sha256": "1af0a458e8dc79be12ab166e16e15a439173347398e7c0f3340f8883b3b0f79d"
      },
      {
        "path": "/data2/k6tk/56/56e250de247838bfa6b81c3132ca8e669f44c78f336b2c8d29e5ca9b02a0db6f.png",
        "sha256": "56e250de247838bfa6b81c3132ca8e669f44c78f336b2c8d29e5ca9b02a0db6f"
      },
      {
        "path": "/data2/k6tk/9f/9fef2604c346b6d5bf2cdf247bfc33f23c3528a2dec7ad92625f273645ad5d84.png",
        "sha256": "9fef2604c346b6d5bf2cdf247bfc33f23c3528a2dec7ad92625f273645ad5d84"
      },
      {
        "path": "/data2/k6tk/fc/fcb7427e0a2500c94f9ee2d63c58a1e15492f3cacd3d84606cd9954bc1cfe46b.png",
        "sha256": "fcb7427e0a2500c94f9ee2d63c58a1e15492f3cacd3d84606cd9954bc1cfe46b"
      },
      {
        "path": "/data2/k6tk/fa/fa28770956789e1082d0e0fa7a37746588ca211ac7a9f0912ee15e67100a8864.png",
        "sha256": "fa28770956789e1082d0e0fa7a37746588ca211ac7a9f0912ee15e67100a8864"
      },
      {
        "path": "/data2/k6tk/3a/3a7407ef3eac33cfae4ae43ae916da535aa7f4d21ddebf0a473faf55f454e57e.png",
        "sha256": "3a7407ef3eac33cfae4ae43ae916da535aa7f4d21ddebf0a473faf55f454e57e"
      },
      {
        "path": "/data2/k6tk/7f/7f677e359ff803d35808538471b55807ab5bf8f6cb50069d04f7a355e71462cb.png",
        "sha256": "7f677e359ff803d35808538471b55807ab5bf8f6cb50069d04f7a355e71462cb"
      },
      {
        "path": "/data2/k6tk/d0/d0a09806d7910d80ce90539843448767ae446f85786b5bc02b7f75f642d8e7f3.png",
        "sha256": "d0a09806d7910d80ce90539843448767ae446f85786b5bc02b7f75f642d8e7f3"
      },
      {
        "path": "/data2/k6tk/a0/a0f27cafea67ec6037aee5730f50cc65e3bffc5d5e374e9d1f1ce2fa4782fba4.png",
        "sha256": "a0f27cafea67ec6037aee5730f50cc65e3bffc5d5e374e9d1f1ce2fa4782fba4"
      },
      {
        "path": "/data2/k6tk/d2/d2456d50fcf00f4b042e3a606b6b1cde86335eefcb887f67c2084fe7c9247735.png",
        "sha256": "d2456d50fcf00f4b042e3a606b6b1cde86335eefcb887f67c2084fe7c9247735"
      },
      {
        "path": "/data2/k6tk/78/788029a0c38660647bec13fdbf3615289fe1abc17bec08d0f3d567a34390c92b.png",
        "sha256": "788029a0c38660647bec13fdbf3615289fe1abc17bec08d0f3d567a34390c92b"
      },
      {
        "path": "/data2/k6tk/a8/a871c52a6c3ba26e9d5cfbeda8f5ac9c2556b7c472c7135700e335c024ba638c.png",
        "sha256": "a871c52a6c3ba26e9d5cfbeda8f5ac9c2556b7c472c7135700e335c024ba638c"
      },
      {
        "path": "/data2/k6tk/ef/efa8a847a65509acaf9cb53bea1c3f668a0a262fb9d3e190c2093352a3f78334.png",
        "sha256": "efa8a847a65509acaf9cb53bea1c3f668a0a262fb9d3e190c2093352a3f78334"
      },
      {
        "path": "/data2/k6tk/5f/5f7c503564e7875ff40ff6ce19fb6beab1ffcde487e44616c1cddc82057c4c1a.png",
        "sha256": "5f7c503564e7875ff40ff6ce19fb6beab1ffcde487e44616c1cddc82057c4c1a"
      },
      {
        "path": "/data2/k6tk/95/955895a8546931d7cb2275ae61f99e04788c4658ed499ecac6ad4f793a16ca85.png",
        "sha256": "955895a8546931d7cb2275ae61f99e04788c4658ed499ecac6ad4f793a16ca85"
      },
      {
        "path": "/data2/k6tk/a5/a586e3d17ba18d071072f650d01b5fd2a2db9311637f4f2f7acba3090b5de131.png",
        "sha256": "a586e3d17ba18d071072f650d01b5fd2a2db9311637f4f2f7acba3090b5de131"
      },
      {
        "path": "/data2/k6tk/65/6582a8109886f87e1e36fab93dba927010639fb8982d382a30ab13b077973a2a.png",
        "sha256": "6582a8109886f87e1e36fab93dba927010639fb8982d382a30ab13b077973a2a"
      },
      {
        "path": "/data2/k6tk/4e/4e417290655ac6f034197f833f827813912bf7636269f5205760feb1ed6d9558.png",
        "sha256": "4e417290655ac6f034197f833f827813912bf7636269f5205760feb1ed6d9558"
      },
      {
        "path": "/data2/k6tk/25/2535dac93c868fc2df32d5a2634dbc6b1b122e377edbfcc9af03eb5970631d35.png",
        "sha256": "2535dac93c868fc2df32d5a2634dbc6b1b122e377edbfcc9af03eb5970631d35"
      },
      {
        "path": "/data2/k6tk/fa/fa6d2743ba53071d2fceba8b38ac66ed96f777e3ebfb5c948c6b777ec4b567b9.png",
        "sha256": "fa6d2743ba53071d2fceba8b38ac66ed96f777e3ebfb5c948c6b777ec4b567b9"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the bag and facing away from the book, is the coat hanger to the left or the right of the book?",
    "timestamps": [
      0.0,
      5.183333333333334,
      10.366666666666667,
      15.566666666666666,
      20.75,
      25.95,
      31.133333333333333,
      36.333333333333336,
      41.516666666666666,
      46.71666666666667,
      51.9,
      57.1,
      62.28333333333333,
      67.48333333333333,
      72.66666666666667,
      77.86666666666666,
      83.05,
      88.25,
      93.43333333333334,
      98.63333333333334,
      103.81666666666666,
      109.01666666666667,
      114.2,
      119.4,
      124.58333333333333,
      129.78333333333333,
      134.96666666666667,
      140.16666666666666,
      145.35,
      150.55,
      155.73333333333332,
      160.93333333333334
    ],
    "total_num_frames": 9657
  },
  "target": "<think>\nStep 1: find the bag, the book and the coat hanger.\nStep 2: I stand at the bag facing the book; I find the coat hanger to my right.\nStep 3: I face away from the book by making a half turn. Front and back swap, and left and right swap.\nSo I find the coat hanger to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "ce9864d881eb4cd354b59bae0a93817d28f91b572c012520769e35159d9d86c8"
  },
  "facing": "away",
  "candidate_id": "ground-f57e20a21b7800f2df335fe8af5d035f56ac5cd2d242ba23a128e03558ccfacc",
  "label_row_keys": [
    "qda1da273906582cb89b9761b"
  ]
}
```

## 5. qc6735e1e62d2aa615eef9546_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qc6735e1e62d2aa615eef9546",
      "source_store_i": 17155,
      "source_row_sha256": "5e32de5325b299c549993b8976069333add7bd048dd19bec3d1f0bd32bd05562",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qc6735e1e62d2aa615eef9546_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vdcbc62ef2785",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      28,
      57,
      86,
      115,
      144,
      173,
      202,
      231,
      260,
      289,
      318,
      347,
      376,
      405,
      434,
      463,
      492,
      521,
      550,
      579,
      608,
      637,
      666,
      695,
      724,
      753,
      782,
      811,
      840,
      869,
      898
    ],
    "frames": [
      {
        "path": "/data2/k6tk/29/297338e59eeefd67ffcfbbeaaed97e72b82a8d7996aeddb8f58e2099a8bbe312.png",
        "sha256": "297338e59eeefd67ffcfbbeaaed97e72b82a8d7996aeddb8f58e2099a8bbe312"
      },
      {
        "path": "/data2/k6tk/8f/8f9bfabfd500cff6bc79270ac6fd300c32a8cb7f2a67118b8c55eb0e59c51f42.png",
        "sha256": "8f9bfabfd500cff6bc79270ac6fd300c32a8cb7f2a67118b8c55eb0e59c51f42"
      },
      {
        "path": "/data2/k6tk/95/95b35ff1b3c0c743e3c8c40ce06b9d75096e868fc28104732cd92c198c68ac68.png",
        "sha256": "95b35ff1b3c0c743e3c8c40ce06b9d75096e868fc28104732cd92c198c68ac68"
      },
      {
        "path": "/data2/k6tk/3f/3f18d46f6d1b4ca8c3db6bd9030ac77f00981d960c4199e72c72faeed5807fb5.png",
        "sha256": "3f18d46f6d1b4ca8c3db6bd9030ac77f00981d960c4199e72c72faeed5807fb5"
      },
      {
        "path": "/data2/k6tk/f2/f291804ecd54402d9450c23046cb3eb18eceba6fd7620881e68d372d0d786730.png",
        "sha256": "f291804ecd54402d9450c23046cb3eb18eceba6fd7620881e68d372d0d786730"
      },
      {
        "path": "/data2/k6tk/77/770289de95540bba201f7ed5b35d505b38b06a3687cd8bf51b95b11b9195aa4a.png",
        "sha256": "770289de95540bba201f7ed5b35d505b38b06a3687cd8bf51b95b11b9195aa4a"
      },
      {
        "path": "/data2/k6tk/ae/ae1b9b5bc28e363599c1beb163c8e34be3d2faeaf445c1e23cfad5f20aeca40d.png",
        "sha256": "ae1b9b5bc28e363599c1beb163c8e34be3d2faeaf445c1e23cfad5f20aeca40d"
      },
      {
        "path": "/data2/k6tk/4d/4dd6b5da68c12fd02630e2a47b60a8e98e0f5e3c6e6f62d846e148d92b4eb552.png",
        "sha256": "4dd6b5da68c12fd02630e2a47b60a8e98e0f5e3c6e6f62d846e148d92b4eb552"
      },
      {
        "path": "/data2/k6tk/d5/d5c4421a14b49b58cd95695f56f13e5bc5262148f559c9a89a9db0a4cab58e1f.png",
        "sha256": "d5c4421a14b49b58cd95695f56f13e5bc5262148f559c9a89a9db0a4cab58e1f"
      },
      {
        "path": "/data2/k6tk/f7/f7d845b5d97e11fa8b3233e082c4e043532c36fcf1ab65bf3f49e3b190bf15d7.png",
        "sha256": "f7d845b5d97e11fa8b3233e082c4e043532c36fcf1ab65bf3f49e3b190bf15d7"
      },
      {
        "path": "/data2/k6tk/7b/7bf57bcba5ce8576383f7c92f710c74b3a16adfff518f0f9bfbebc3069f373f7.png",
        "sha256": "7bf57bcba5ce8576383f7c92f710c74b3a16adfff518f0f9bfbebc3069f373f7"
      },
      {
        "path": "/data2/k6tk/40/40397d84122cf970fcabf171d4ba9e724fdab79c7bf3fe6dc56501bfa2d730e6.png",
        "sha256": "40397d84122cf970fcabf171d4ba9e724fdab79c7bf3fe6dc56501bfa2d730e6"
      },
      {
        "path": "/data2/k6tk/f9/f9eaa25a3ca9fa2e68d59f043345738bbd44c25a06dd213f135120c53540faa9.png",
        "sha256": "f9eaa25a3ca9fa2e68d59f043345738bbd44c25a06dd213f135120c53540faa9"
      },
      {
        "path": "/data2/k6tk/73/7313de284f60a3684b28a91b5695ee8d6290d79482789c5ed9f12cb2a45b53bb.png",
        "sha256": "7313de284f60a3684b28a91b5695ee8d6290d79482789c5ed9f12cb2a45b53bb"
      },
      {
        "path": "/data2/k6tk/a3/a3e436a32b7c1620ed924749623bfdb63a7f1d368c710ca70981f4950293afc7.png",
        "sha256": "a3e436a32b7c1620ed924749623bfdb63a7f1d368c710ca70981f4950293afc7"
      },
      {
        "path": "/data2/k6tk/8a/8a4d8a66244379355542e8dda85192a8cb3416162371a8d9fbadb5f2f433acd2.png",
        "sha256": "8a4d8a66244379355542e8dda85192a8cb3416162371a8d9fbadb5f2f433acd2"
      },
      {
        "path": "/data2/k6tk/48/486861934afe04208e0745d236fd7a305e9ce0d17fe768089080c7c0309cf8c6.png",
        "sha256": "486861934afe04208e0745d236fd7a305e9ce0d17fe768089080c7c0309cf8c6"
      },
      {
        "path": "/data2/k6tk/5d/5d518443779962fc6fc9661803778e238c89aa73e4b6704450dd7f7aba393992.png",
        "sha256": "5d518443779962fc6fc9661803778e238c89aa73e4b6704450dd7f7aba393992"
      },
      {
        "path": "/data2/k6tk/81/81a99da4dc8d4bf43b5c3a22113f81f0ba3babd961e0f478660ecbb1d966d325.png",
        "sha256": "81a99da4dc8d4bf43b5c3a22113f81f0ba3babd961e0f478660ecbb1d966d325"
      },
      {
        "path": "/data2/k6tk/d8/d87af407ba8dc66445a34b415b6e66b1b53161192045770e34eef80822f1ccb1.png",
        "sha256": "d87af407ba8dc66445a34b415b6e66b1b53161192045770e34eef80822f1ccb1"
      },
      {
        "path": "/data2/k6tk/7e/7e4058634aae1c294fb3f316b2f657cb866516bf6de5ab0f926976446f475e3a.png",
        "sha256": "7e4058634aae1c294fb3f316b2f657cb866516bf6de5ab0f926976446f475e3a"
      },
      {
        "path": "/data2/k6tk/03/03db396b1382a359df14138e2e8ade6036b146b5a629387ae8282f2a3b30016e.png",
        "sha256": "03db396b1382a359df14138e2e8ade6036b146b5a629387ae8282f2a3b30016e"
      },
      {
        "path": "/data2/k6tk/63/638effbbff5b26a1a7da6f9c8811f6091748cf7936879f4f9ed64030a52b951a.png",
        "sha256": "638effbbff5b26a1a7da6f9c8811f6091748cf7936879f4f9ed64030a52b951a"
      },
      {
        "path": "/data2/k6tk/93/935981d05532280ba36faf5333113f0331457dda51eebad3187f9332daa3feca.png",
        "sha256": "935981d05532280ba36faf5333113f0331457dda51eebad3187f9332daa3feca"
      },
      {
        "path": "/data2/k6tk/f7/f7960ff24b438e0a817017d4f8602af31a85dc4f85595bc4e6d7f30e6a151c38.png",
        "sha256": "f7960ff24b438e0a817017d4f8602af31a85dc4f85595bc4e6d7f30e6a151c38"
      },
      {
        "path": "/data2/k6tk/4c/4c0fa8b4d81354991b69eb738183cfc4edc0258752c2c6c1b0ecd6f30a99988c.png",
        "sha256": "4c0fa8b4d81354991b69eb738183cfc4edc0258752c2c6c1b0ecd6f30a99988c"
      },
      {
        "path": "/data2/k6tk/bc/bcdfbfa1afa2fcdf3ab30ac1aa1c2c6b76fbcc50621db5efefecc3a57daa3d07.png",
        "sha256": "bcdfbfa1afa2fcdf3ab30ac1aa1c2c6b76fbcc50621db5efefecc3a57daa3d07"
      },
      {
        "path": "/data2/k6tk/da/da2068c122174aba78f832408fd73ff848d412cd12ad11ba04fcc7d0c6a33726.png",
        "sha256": "da2068c122174aba78f832408fd73ff848d412cd12ad11ba04fcc7d0c6a33726"
      },
      {
        "path": "/data2/k6tk/03/0309af037b6695e5bc1abd47f7b8b8d696762834b01e89ae609df1c94f288670.png",
        "sha256": "0309af037b6695e5bc1abd47f7b8b8d696762834b01e89ae609df1c94f288670"
      },
      {
        "path": "/data2/k6tk/e5/e5a9bf6cbd78bcce77d6790b0a6c0b99f4d5d41d5d744abf61e4430c42bf5efc.png",
        "sha256": "e5a9bf6cbd78bcce77d6790b0a6c0b99f4d5d41d5d744abf61e4430c42bf5efc"
      },
      {
        "path": "/data2/k6tk/02/0224dc3b0aa03a4e07931c8ed1d34113d6228fb0d0bedfeee2405babc189d4de.png",
        "sha256": "0224dc3b0aa03a4e07931c8ed1d34113d6228fb0d0bedfeee2405babc189d4de"
      },
      {
        "path": "/data2/k6tk/e3/e3fcbfc877e31bfe6da2c1873aef13b08d441a87e3e0a1b0873a181b12d86639.png",
        "sha256": "e3fcbfc877e31bfe6da2c1873aef13b08d441a87e3e0a1b0873a181b12d86639"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the bathroom vanity and facing away from the trash can, is the bucket to the left or the right of the trash can?",
    "timestamps": [
      0.0,
      1.1666666666666667,
      2.375,
      3.5833333333333335,
      4.791666666666667,
      6.0,
      7.208333333333333,
      8.416666666666666,
      9.625,
      10.833333333333334,
      12.041666666666666,
      13.25,
      14.458333333333334,
      15.666666666666666,
      16.875,
      18.083333333333332,
      19.291666666666668,
      20.5,
      21.708333333333332,
      22.916666666666668,
      24.125,
      25.333333333333332,
      26.541666666666668,
      27.75,
      28.958333333333332,
      30.166666666666668,
      31.375,
      32.583333333333336,
      33.791666666666664,
      35.0,
      36.208333333333336,
      37.416666666666664
    ],
    "total_num_frames": 899
  },
  "target": "<think>\nStep 1: find the bathroom vanity, the trash can and the bucket.\nStep 2: I stand at the bathroom vanity facing the trash can; I find the bucket to my right.\nStep 3: I face away from the trash can by making a half turn. Front and back swap, and left and right swap.\nSo I find the bucket to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "0df994ad1dbaff103a21147f274f278a747b80d0368f24b79e83ec12747b6aaa"
  },
  "facing": "away",
  "candidate_id": "ground-6ea2119107fe0908d3838a0542047d491f648b8ed3bc0123a4dbc7b6e24798a9",
  "label_row_keys": [
    "qc6735e1e62d2aa615eef9546"
  ]
}
```

## 6. qddd09414413e1a646596f4de_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qddd09414413e1a646596f4de",
      "source_store_i": 4860,
      "source_row_sha256": "a0cc588238e832d50187637cc5cb65857c9ecac35bd7161956dbaf847f4392b2",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qddd09414413e1a646596f4de_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
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
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the books and facing away from the cable raceway, is the storage closet to the left or the right of the cable raceway?",
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
  "target": "<think>\nStep 1: find the books, the cable raceway and the storage closet.\nStep 2: I stand at the books facing the cable raceway; I find the storage closet to my right.\nStep 3: I face away from the cable raceway by making a half turn. Front and back swap, and left and right swap.\nSo I find the storage closet to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "f67ba49b30fe80577ed0a2220f3e001b0c789f19587b5f04e47fafd75dbb7f0f"
  },
  "facing": "away",
  "candidate_id": "ground-23f973805758a351e84e6f40dd0c921fe7f396268dfa0e2587015fcf303e3233",
  "label_row_keys": [
    "qddd09414413e1a646596f4de"
  ]
}
```

## 7. qbcca1aeb467f8e59a1b96733_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qbcca1aeb467f8e59a1b96733",
      "source_store_i": 9139,
      "source_row_sha256": "73b6a7fa0c249a40dc61d4bfdb70a0aa375a37467efbeb9c5ad352f20542f58d",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "right",
      "mapped_label": "left",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qbcca1aeb467f8e59a1b96733_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v1b9306fb9610",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      411,
      822,
      1233,
      1644,
      2056,
      2467,
      2878,
      3289,
      3701,
      4112,
      4523,
      4934,
      5345,
      5757,
      6168,
      6579,
      6990,
      7402,
      7813,
      8224,
      8635,
      9046,
      9458,
      9869,
      10280,
      10691,
      11103,
      11514,
      11925,
      12336,
      12748
    ],
    "frames": [
      {
        "path": "/data2/k6tk/57/576da1185cd6e002104b85ae4aca70fbe236320e9ff07383a63880aefa2167ef.png",
        "sha256": "576da1185cd6e002104b85ae4aca70fbe236320e9ff07383a63880aefa2167ef"
      },
      {
        "path": "/data2/k6tk/30/30df0809bd679b4dc07c54f615bb8338af1952e4198df2249e5bec7cb22331ed.png",
        "sha256": "30df0809bd679b4dc07c54f615bb8338af1952e4198df2249e5bec7cb22331ed"
      },
      {
        "path": "/data2/k6tk/97/97353b4f329ebf8702905201274fb409d646f023047f0355dd734723154edc3d.png",
        "sha256": "97353b4f329ebf8702905201274fb409d646f023047f0355dd734723154edc3d"
      },
      {
        "path": "/data2/k6tk/b3/b3996844ff740c1976b9f18dccf137ec39920b4ca3b117922d02ddd86a1fed56.png",
        "sha256": "b3996844ff740c1976b9f18dccf137ec39920b4ca3b117922d02ddd86a1fed56"
      },
      {
        "path": "/data2/k6tk/d2/d2367fb67245ef7d8aa64abedcdc62d99c470d7d811d5037b0ffd351c5ea8ded.png",
        "sha256": "d2367fb67245ef7d8aa64abedcdc62d99c470d7d811d5037b0ffd351c5ea8ded"
      },
      {
        "path": "/data2/k6tk/33/339ec2905fe5ce0f7c332aaa63957ee575345f41bccaa31a0928c98d167cf8c7.png",
        "sha256": "339ec2905fe5ce0f7c332aaa63957ee575345f41bccaa31a0928c98d167cf8c7"
      },
      {
        "path": "/data2/k6tk/d0/d04530b8643498976546747b8fce7dd82c630200736d8e15a444141ef4e9315f.png",
        "sha256": "d04530b8643498976546747b8fce7dd82c630200736d8e15a444141ef4e9315f"
      },
      {
        "path": "/data2/k6tk/a6/a64bee405677d39a0c0611d40b7a520f559bb49b5ab9ebf7f33ed25bd14bbf18.png",
        "sha256": "a64bee405677d39a0c0611d40b7a520f559bb49b5ab9ebf7f33ed25bd14bbf18"
      },
      {
        "path": "/data2/k6tk/62/62a1363518abd9690b76f3a1df402f7942cbc5ecabcc58cd84ff92c03b447c60.png",
        "sha256": "62a1363518abd9690b76f3a1df402f7942cbc5ecabcc58cd84ff92c03b447c60"
      },
      {
        "path": "/data2/k6tk/f6/f685025b98fee75d87df79db7f7d7f1471ac0f588623cfb3c8baeceae656c2ab.png",
        "sha256": "f685025b98fee75d87df79db7f7d7f1471ac0f588623cfb3c8baeceae656c2ab"
      },
      {
        "path": "/data2/k6tk/55/55681bcaffdf5cc04b26d9e357f7d5a511655e0356a8b65d292af4b3dc94a47e.png",
        "sha256": "55681bcaffdf5cc04b26d9e357f7d5a511655e0356a8b65d292af4b3dc94a47e"
      },
      {
        "path": "/data2/k6tk/43/4333355a07d691fdbd96c1253fc6897ac5fb444e57cec14ea13f565b482cea90.png",
        "sha256": "4333355a07d691fdbd96c1253fc6897ac5fb444e57cec14ea13f565b482cea90"
      },
      {
        "path": "/data2/k6tk/7b/7bb30840088c215dd758872679ed5d04f22ac9cc23ac61db98558221bf5baaf2.png",
        "sha256": "7bb30840088c215dd758872679ed5d04f22ac9cc23ac61db98558221bf5baaf2"
      },
      {
        "path": "/data2/k6tk/b5/b580d2556ef2dc7e6e11b3c535e5ed198a7fdfc90ff8611d19c99d4326c36c3a.png",
        "sha256": "b580d2556ef2dc7e6e11b3c535e5ed198a7fdfc90ff8611d19c99d4326c36c3a"
      },
      {
        "path": "/data2/k6tk/9c/9c43bdbf98bf873b74ce4f17285350a4434958fc81f8984f6bb0c19b9ab58b64.png",
        "sha256": "9c43bdbf98bf873b74ce4f17285350a4434958fc81f8984f6bb0c19b9ab58b64"
      },
      {
        "path": "/data2/k6tk/ae/aee74d3e9c1ba2f195c44f13fc08fe6685e9cbb165b2028ff51810abe22f4ad6.png",
        "sha256": "aee74d3e9c1ba2f195c44f13fc08fe6685e9cbb165b2028ff51810abe22f4ad6"
      },
      {
        "path": "/data2/k6tk/83/83a2fede99b7365a00197a64e5f3f0763ab67546a99e2450ef09977823827a4c.png",
        "sha256": "83a2fede99b7365a00197a64e5f3f0763ab67546a99e2450ef09977823827a4c"
      },
      {
        "path": "/data2/k6tk/ac/ac750d9710ccd703399dfddf98766296cd9ebdd8e01fd866de6da20362db4100.png",
        "sha256": "ac750d9710ccd703399dfddf98766296cd9ebdd8e01fd866de6da20362db4100"
      },
      {
        "path": "/data2/k6tk/b1/b1bcc1b73a80c24d963a40538993dd776de8820fbbd48be95a2fd7c7b6fe681b.png",
        "sha256": "b1bcc1b73a80c24d963a40538993dd776de8820fbbd48be95a2fd7c7b6fe681b"
      },
      {
        "path": "/data2/k6tk/9f/9f1e08049e0b170310f639fccfc9c6481f2309651e7a7d7986c39952ee5d204e.png",
        "sha256": "9f1e08049e0b170310f639fccfc9c6481f2309651e7a7d7986c39952ee5d204e"
      },
      {
        "path": "/data2/k6tk/4c/4c40b3a9871d7bc6d1abd5d1e2ae50e4d3c30f95f38e6f7714f8212e7693d68c.png",
        "sha256": "4c40b3a9871d7bc6d1abd5d1e2ae50e4d3c30f95f38e6f7714f8212e7693d68c"
      },
      {
        "path": "/data2/k6tk/9b/9bcba19e3f9bce4fc06d7d333dc9966e7f2084fa0ce56ce08fd014b1ec1ec2bc.png",
        "sha256": "9bcba19e3f9bce4fc06d7d333dc9966e7f2084fa0ce56ce08fd014b1ec1ec2bc"
      },
      {
        "path": "/data2/k6tk/e5/e59dd297fc515779297df792b26ac9ffc1234c2ab3b0a5e6cb02bdf5ce704ad6.png",
        "sha256": "e59dd297fc515779297df792b26ac9ffc1234c2ab3b0a5e6cb02bdf5ce704ad6"
      },
      {
        "path": "/data2/k6tk/cb/cba6b4cb7fe3f2446b70ef1e2544ad2a2db25506dceb57968551a9ec903836d1.png",
        "sha256": "cba6b4cb7fe3f2446b70ef1e2544ad2a2db25506dceb57968551a9ec903836d1"
      },
      {
        "path": "/data2/k6tk/2b/2b0c9a1f6edf8c64a570088ca2c3ee237f302d0a24ceeecc6cb71a6c0c267eb5.png",
        "sha256": "2b0c9a1f6edf8c64a570088ca2c3ee237f302d0a24ceeecc6cb71a6c0c267eb5"
      },
      {
        "path": "/data2/k6tk/33/333bfb03169221044ea5f0f18214d448f9d520edb0b30b3cd5ce238ef84bb312.png",
        "sha256": "333bfb03169221044ea5f0f18214d448f9d520edb0b30b3cd5ce238ef84bb312"
      },
      {
        "path": "/data2/k6tk/61/61a6ed126a00eff55670966a2425242c9c24e9af0eb9f70fe7e064ab378c8ee1.png",
        "sha256": "61a6ed126a00eff55670966a2425242c9c24e9af0eb9f70fe7e064ab378c8ee1"
      },
      {
        "path": "/data2/k6tk/50/50142ccf5d6abd1b2821a2187325fa26f2815f2a1194d794d8cfa7c14069a74e.png",
        "sha256": "50142ccf5d6abd1b2821a2187325fa26f2815f2a1194d794d8cfa7c14069a74e"
      },
      {
        "path": "/data2/k6tk/85/85781df1e3379d6549195f13bebc2396a24da5592aa0819a1966868680211cf3.png",
        "sha256": "85781df1e3379d6549195f13bebc2396a24da5592aa0819a1966868680211cf3"
      },
      {
        "path": "/data2/k6tk/6a/6a06838335c45bb65af6b9ce37d5865cb90e36530527d10a824e03ea859e42ba.png",
        "sha256": "6a06838335c45bb65af6b9ce37d5865cb90e36530527d10a824e03ea859e42ba"
      },
      {
        "path": "/data2/k6tk/b0/b0703531729154465c6d259d0f1a8f586a1015e675ea3886e305d6577ff3f8d2.png",
        "sha256": "b0703531729154465c6d259d0f1a8f586a1015e675ea3886e305d6577ff3f8d2"
      },
      {
        "path": "/data2/k6tk/c7/c774bd6137a23ecc3931b2a012523a0f78e79f90ac7fbbb45ec8dab297c35bcb.png",
        "sha256": "c774bd6137a23ecc3931b2a012523a0f78e79f90ac7fbbb45ec8dab297c35bcb"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I'm next to the ceiling light facing away from the chair, will the bed be seen to its left or right?",
    "timestamps": [
      0.0,
      6.85,
      13.7,
      20.55,
      27.4,
      34.266666666666666,
      41.11666666666667,
      47.96666666666667,
      54.81666666666667,
      61.68333333333333,
      68.53333333333333,
      75.38333333333334,
      82.23333333333333,
      89.08333333333333,
      95.95,
      102.8,
      109.65,
      116.5,
      123.36666666666666,
      130.21666666666667,
      137.06666666666666,
      143.91666666666666,
      150.76666666666668,
      157.63333333333333,
      164.48333333333332,
      171.33333333333334,
      178.18333333333334,
      185.05,
      191.9,
      198.75,
      205.6,
      212.46666666666667
    ],
    "total_num_frames": 12749
  },
  "target": "<think>\nStep 1: find the ceiling light, the chair and the bed.\nStep 2: I find the bed to my right when I stand at the ceiling light facing the chair.\nStep 3: I face away from the chair by making a half turn. Front and back swap, and left and right swap.\nSo I find the bed to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "5fc0ea2b8e95b950e6f19dce527df8f65c91439faadcad5a6770e6c75fa52979"
  },
  "facing": "away",
  "candidate_id": "ground-402757ada136cb2fa4fa554d6f6ee434ec882f24a3c154652c81db42ac6661ed",
  "label_row_keys": [
    "qbcca1aeb467f8e59a1b96733"
  ]
}
```

## 8. q4351839663996e61807aa78c-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q4351839663996e61807aa78c-p1",
      "source_store_i": 69113,
      "source_row_sha256": "e5f9bd4cf38176905f9ca0e08b36933a27a7f3c7447d16c71baf31192b97886c",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "right",
      "mapped_label": "left",
      "clause_edit": {
        "start": 35,
        "end": 46,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q4351839663996e61807aa78c-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vc1fa0b584d62",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      42,
      85,
      128,
      171,
      214,
      257,
      300,
      342,
      385,
      428,
      471,
      514,
      557,
      600,
      643,
      685,
      728,
      771,
      814,
      857,
      900,
      943,
      986,
      1028,
      1071,
      1114,
      1157,
      1200,
      1243,
      1286,
      1329
    ],
    "frames": [
      {
        "path": "/data2/k6tk/56/560e05d6737d830ca0cb4cf22a66f14c69b369cfa5be9b109d64a95f8b0ec432.png",
        "sha256": "560e05d6737d830ca0cb4cf22a66f14c69b369cfa5be9b109d64a95f8b0ec432"
      },
      {
        "path": "/data2/k6tk/59/59c4881bab6422641c111ac80fe20b4a9b002c0a682e755e684cdcf148962a46.png",
        "sha256": "59c4881bab6422641c111ac80fe20b4a9b002c0a682e755e684cdcf148962a46"
      },
      {
        "path": "/data2/k6tk/91/911341beb8e216b01c623081e3a0103019b2ab704fd86ea14caaf92a7f259b50.png",
        "sha256": "911341beb8e216b01c623081e3a0103019b2ab704fd86ea14caaf92a7f259b50"
      },
      {
        "path": "/data2/k6tk/f4/f41aaa9e040a6ef15b4994afd4a0d75f1f8a36d6efcaeadf42e23808ebd9a40e.png",
        "sha256": "f41aaa9e040a6ef15b4994afd4a0d75f1f8a36d6efcaeadf42e23808ebd9a40e"
      },
      {
        "path": "/data2/k6tk/ec/ecbb8d28177987777e3ad66210d88e8e7af9096be69e5905eae09f2a349449ba.png",
        "sha256": "ecbb8d28177987777e3ad66210d88e8e7af9096be69e5905eae09f2a349449ba"
      },
      {
        "path": "/data2/k6tk/e2/e29f3b1c449a107ed8d418010489ed01030a8bb9ea004bcc3a2856e1518e5a1a.png",
        "sha256": "e29f3b1c449a107ed8d418010489ed01030a8bb9ea004bcc3a2856e1518e5a1a"
      },
      {
        "path": "/data2/k6tk/ae/aedba6c63d290a175b4e72218db669bfa7fbc2e49cef59217ccb66a0196ef397.png",
        "sha256": "aedba6c63d290a175b4e72218db669bfa7fbc2e49cef59217ccb66a0196ef397"
      },
      {
        "path": "/data2/k6tk/87/878a6bbbd64887a410e5454af9ac17d5352310388d4231d0910cf665cf066c21.png",
        "sha256": "878a6bbbd64887a410e5454af9ac17d5352310388d4231d0910cf665cf066c21"
      },
      {
        "path": "/data2/k6tk/dd/dd8cc2de40f87774ed8de0c906ef117191bd6671252fc04d9318a99f3a9d349a.png",
        "sha256": "dd8cc2de40f87774ed8de0c906ef117191bd6671252fc04d9318a99f3a9d349a"
      },
      {
        "path": "/data2/k6tk/2f/2fcbb6a7852eb8a32fd17d7f7b7a997022ffcffe800ac7a6a81b64b58da81aef.png",
        "sha256": "2fcbb6a7852eb8a32fd17d7f7b7a997022ffcffe800ac7a6a81b64b58da81aef"
      },
      {
        "path": "/data2/k6tk/2d/2d37c3cd778991c4887a0bdbfc41f2367217cb13a5445e1b93421d775919f44e.png",
        "sha256": "2d37c3cd778991c4887a0bdbfc41f2367217cb13a5445e1b93421d775919f44e"
      },
      {
        "path": "/data2/k6tk/2e/2e2847077cc6debe2cd7b6831aa8dfa7ad41b4e841303153c2ccb17e2480aa21.png",
        "sha256": "2e2847077cc6debe2cd7b6831aa8dfa7ad41b4e841303153c2ccb17e2480aa21"
      },
      {
        "path": "/data2/k6tk/09/09f35afd167431cfc62d3b102e273964d87f26cac89b679031c53df7075bb2c6.png",
        "sha256": "09f35afd167431cfc62d3b102e273964d87f26cac89b679031c53df7075bb2c6"
      },
      {
        "path": "/data2/k6tk/d1/d1db06f9a9e06a09e71496e8281347a28642731184d832b1627bf5f4b2531f51.png",
        "sha256": "d1db06f9a9e06a09e71496e8281347a28642731184d832b1627bf5f4b2531f51"
      },
      {
        "path": "/data2/k6tk/44/442a5168c0ee4689cfec4aa9eaaead761b0e2ed933cf14b35819286aa5c4c9f0.png",
        "sha256": "442a5168c0ee4689cfec4aa9eaaead761b0e2ed933cf14b35819286aa5c4c9f0"
      },
      {
        "path": "/data2/k6tk/61/61e1f2a93b4575d8933ecd331a73642d40b4f74f1f768d05f54d1898bfcd2c79.png",
        "sha256": "61e1f2a93b4575d8933ecd331a73642d40b4f74f1f768d05f54d1898bfcd2c79"
      },
      {
        "path": "/data2/k6tk/ee/eefb92a112206cf44554f68fe2b90da7f7b82b57e61ade41e449f182c5a03750.png",
        "sha256": "eefb92a112206cf44554f68fe2b90da7f7b82b57e61ade41e449f182c5a03750"
      },
      {
        "path": "/data2/k6tk/61/6122bcc6473a638c28b02bee6b2a308bce2b34e8cc15afbdb4a3489174fd679d.png",
        "sha256": "6122bcc6473a638c28b02bee6b2a308bce2b34e8cc15afbdb4a3489174fd679d"
      },
      {
        "path": "/data2/k6tk/cb/cbc663ed7ec023d794f71f2cd8006889829b9677ed1e097b97bd2cbaeb10ee85.png",
        "sha256": "cbc663ed7ec023d794f71f2cd8006889829b9677ed1e097b97bd2cbaeb10ee85"
      },
      {
        "path": "/data2/k6tk/bd/bd58441fccb536b8978f45e32960ffb09f123a80c9b072671083712ffd23b95c.png",
        "sha256": "bd58441fccb536b8978f45e32960ffb09f123a80c9b072671083712ffd23b95c"
      },
      {
        "path": "/data2/k6tk/d7/d772b1dbecb7466dd5db0bf39149c9b29463b07e7fe41967751fcbcb20e50b29.png",
        "sha256": "d772b1dbecb7466dd5db0bf39149c9b29463b07e7fe41967751fcbcb20e50b29"
      },
      {
        "path": "/data2/k6tk/fe/fe98ee7a8043e74b10387dc1ab7798fe06e31a4195472cb4df086a948f65a8bc.png",
        "sha256": "fe98ee7a8043e74b10387dc1ab7798fe06e31a4195472cb4df086a948f65a8bc"
      },
      {
        "path": "/data2/k6tk/5e/5e99c320193f8af90aff318d9b49141cce748e13aa07c4fedffa41e98ee611cd.png",
        "sha256": "5e99c320193f8af90aff318d9b49141cce748e13aa07c4fedffa41e98ee611cd"
      },
      {
        "path": "/data2/k6tk/1c/1c4d9f465c476e9b79156f961effc37352ae3202c595f31b36fe28a0d73bd31c.png",
        "sha256": "1c4d9f465c476e9b79156f961effc37352ae3202c595f31b36fe28a0d73bd31c"
      },
      {
        "path": "/data2/k6tk/cb/cbc651c2259524ade385875defc73a3b6753793adc7f3bd0335b76bec56c3e7e.png",
        "sha256": "cbc651c2259524ade385875defc73a3b6753793adc7f3bd0335b76bec56c3e7e"
      },
      {
        "path": "/data2/k6tk/33/33bf2eea93ac699c803648342f453f6de5d79f431554dd08610e5a2b777a297e.png",
        "sha256": "33bf2eea93ac699c803648342f453f6de5d79f431554dd08610e5a2b777a297e"
      },
      {
        "path": "/data2/k6tk/ca/ca71546cc93ec6b408e19216ba40734fd0c3929398124c3c5ebe92a30fd2e6dc.png",
        "sha256": "ca71546cc93ec6b408e19216ba40734fd0c3929398124c3c5ebe92a30fd2e6dc"
      },
      {
        "path": "/data2/k6tk/90/90a9f6fedff4276a87451beb4c626a71d1e23fc2eae141c6b3379cd182c282ab.png",
        "sha256": "90a9f6fedff4276a87451beb4c626a71d1e23fc2eae141c6b3379cd182c282ab"
      },
      {
        "path": "/data2/k6tk/c5/c5f5fc419a101f698d4b66573b3240d9f2c1c35a7d4e27cc18c5a724c0f0db68.png",
        "sha256": "c5f5fc419a101f698d4b66573b3240d9f2c1c35a7d4e27cc18c5a724c0f0db68"
      },
      {
        "path": "/data2/k6tk/6f/6f13877e6e5c7e6315cfbbb9b16d02920072ef449ef9f8af43104c5451633707.png",
        "sha256": "6f13877e6e5c7e6315cfbbb9b16d02920072ef449ef9f8af43104c5451633707"
      },
      {
        "path": "/data2/k6tk/c4/c4c2668863690f51780785c200181afba4c5ddc0bc9c825c49c8f3c02d5bd1c7.png",
        "sha256": "c4c2668863690f51780785c200181afba4c5ddc0bc9c825c49c8f3c02d5bd1c7"
      },
      {
        "path": "/data2/k6tk/fb/fbdb908c577bc313105ad5540402f6168fe7b7d2ede25ba6f6b73dcfe1df4649.png",
        "sha256": "fbdb908c577bc313105ad5540402f6168fe7b7d2ede25ba6f6b73dcfe1df4649"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "From a position beside the basket, face away from the pot. Is the sink to your left or right?",
    "timestamps": [
      0.0,
      1.75,
      3.5416666666666665,
      5.333333333333333,
      7.125,
      8.916666666666666,
      10.708333333333334,
      12.5,
      14.25,
      16.041666666666668,
      17.833333333333332,
      19.625,
      21.416666666666668,
      23.208333333333332,
      25.0,
      26.791666666666668,
      28.541666666666668,
      30.333333333333332,
      32.125,
      33.916666666666664,
      35.708333333333336,
      37.5,
      39.291666666666664,
      41.083333333333336,
      42.833333333333336,
      44.625,
      46.416666666666664,
      48.208333333333336,
      50.0,
      51.791666666666664,
      53.583333333333336,
      55.375
    ],
    "total_num_frames": 1330
  },
  "target": "<think>\nStep 1: find the basket, the pot and the sink.\nStep 2: facing the pot from the basket, I find the sink to my right.\nStep 3: I face away from the pot by making a half turn. Front and back swap, and left and right swap.\nSo I find the sink to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q4351839663996e61807aa78c",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "338306f0fb938913d7fa68949fbd10fab2d06fc05d8e4c06d689b5b8eb785b71"
  },
  "facing": "away",
  "candidate_id": "ground-780556d41973ea599e148f3247e60e4a26cf16c02a7f66f1a12a7aa72032b733",
  "label_row_keys": [
    "q4351839663996e61807aa78c-p1"
  ]
}
```

## 9. qaf0982c5c85d8e27b48c31dc_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qaf0982c5c85d8e27b48c31dc",
      "source_store_i": 1846,
      "source_row_sha256": "ba6e63db16c84a2e590a63a31b47573a8b8baf329bed998766c9f4b29b774d0e",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qaf0982c5c85d8e27b48c31dc_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vf40d8ea60e56",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      190,
      380,
      570,
      761,
      951,
      1141,
      1332,
      1522,
      1712,
      1903,
      2093,
      2283,
      2474,
      2664,
      2854,
      3045,
      3235,
      3425,
      3616,
      3806,
      3996,
      4187,
      4377,
      4567,
      4758,
      4948,
      5138,
      5329,
      5519,
      5709,
      5900
    ],
    "frames": [
      {
        "path": "/data2/k6tk/17/1795d341b871f8b96510074edc19851a3ab448f6e3ed345aab855e01c6fcbb16.png",
        "sha256": "1795d341b871f8b96510074edc19851a3ab448f6e3ed345aab855e01c6fcbb16"
      },
      {
        "path": "/data2/k6tk/2b/2b077e1ac5c6339d327ada8c4d47ce95b112865c53335bf09f457dc228fea29f.png",
        "sha256": "2b077e1ac5c6339d327ada8c4d47ce95b112865c53335bf09f457dc228fea29f"
      },
      {
        "path": "/data2/k6tk/73/737295ea8c4462587ce02459234d32616b8833b6dd0c931971e07e119b347a4b.png",
        "sha256": "737295ea8c4462587ce02459234d32616b8833b6dd0c931971e07e119b347a4b"
      },
      {
        "path": "/data2/k6tk/41/41c453d63f7f6902bf5ab2327ed63088b592f90b3e2290fd1d8758b6c189e899.png",
        "sha256": "41c453d63f7f6902bf5ab2327ed63088b592f90b3e2290fd1d8758b6c189e899"
      },
      {
        "path": "/data2/k6tk/11/11f706ec6a942d685a87f6eaeac600938a2da9e17dd985bd98dab4be7c2ddcc9.png",
        "sha256": "11f706ec6a942d685a87f6eaeac600938a2da9e17dd985bd98dab4be7c2ddcc9"
      },
      {
        "path": "/data2/k6tk/03/032a6f5f3e2ac9934b2782fd80f8a7be5e1f7cbf156b738c67f131f3c9d4ae07.png",
        "sha256": "032a6f5f3e2ac9934b2782fd80f8a7be5e1f7cbf156b738c67f131f3c9d4ae07"
      },
      {
        "path": "/data2/k6tk/ab/ab1380c9ba389df7567055412d24e717367550029ae4c92a8cb12cf110b372de.png",
        "sha256": "ab1380c9ba389df7567055412d24e717367550029ae4c92a8cb12cf110b372de"
      },
      {
        "path": "/data2/k6tk/cd/cda5c4f7bdef4002cd4ad54a62c08c68dc2aa8b1dcb5b6bcde10382b63776350.png",
        "sha256": "cda5c4f7bdef4002cd4ad54a62c08c68dc2aa8b1dcb5b6bcde10382b63776350"
      },
      {
        "path": "/data2/k6tk/2d/2d23454ea043e854f65fca925878b99fe5cfceaa8fc3c0a633a48144d0b8ede8.png",
        "sha256": "2d23454ea043e854f65fca925878b99fe5cfceaa8fc3c0a633a48144d0b8ede8"
      },
      {
        "path": "/data2/k6tk/ad/ad12c7290e66a6c14157fded2067bbb39b675d472b8489c21ad5e40d2c8e230f.png",
        "sha256": "ad12c7290e66a6c14157fded2067bbb39b675d472b8489c21ad5e40d2c8e230f"
      },
      {
        "path": "/data2/k6tk/ab/ab25b70a70a0e2ad9b7a5a03ebc092dd22c2e56059162a88f2a08c2367c74b09.png",
        "sha256": "ab25b70a70a0e2ad9b7a5a03ebc092dd22c2e56059162a88f2a08c2367c74b09"
      },
      {
        "path": "/data2/k6tk/6b/6b72cc0142be5cd53f2a4dda018b344b2e67576e981fa5776e5cacf3c52b84f5.png",
        "sha256": "6b72cc0142be5cd53f2a4dda018b344b2e67576e981fa5776e5cacf3c52b84f5"
      },
      {
        "path": "/data2/k6tk/d1/d1fadfecabe123428eaf96c495ea69bb79a026cd888b91c148907593239a0ebd.png",
        "sha256": "d1fadfecabe123428eaf96c495ea69bb79a026cd888b91c148907593239a0ebd"
      },
      {
        "path": "/data2/k6tk/2f/2fbed2bfcb9d1471847937b1a184a9a83668628abd82f85be734737ea896241a.png",
        "sha256": "2fbed2bfcb9d1471847937b1a184a9a83668628abd82f85be734737ea896241a"
      },
      {
        "path": "/data2/k6tk/61/613b11ddcb3ed1aeb5feda3b527babf8485d36e9f32bd227ce4ffa032cadc202.png",
        "sha256": "613b11ddcb3ed1aeb5feda3b527babf8485d36e9f32bd227ce4ffa032cadc202"
      },
      {
        "path": "/data2/k6tk/96/96c1a423e8dab37d053c763f179c8f94c36b2f2eab3e87dc09564a2ef7339072.png",
        "sha256": "96c1a423e8dab37d053c763f179c8f94c36b2f2eab3e87dc09564a2ef7339072"
      },
      {
        "path": "/data2/k6tk/4b/4b5dcf44f4e70e9f2e275926d983d6b30064d8ed642c35bd067bf8f928db846b.png",
        "sha256": "4b5dcf44f4e70e9f2e275926d983d6b30064d8ed642c35bd067bf8f928db846b"
      },
      {
        "path": "/data2/k6tk/d4/d4b1600801f3790c9479cc5ab8c405bee1a7d9c6809e812801140190abfb433d.png",
        "sha256": "d4b1600801f3790c9479cc5ab8c405bee1a7d9c6809e812801140190abfb433d"
      },
      {
        "path": "/data2/k6tk/59/59c47dac548cddf52f5a61d66a59fe449ba5096046623ae51149e6ea7f29629f.png",
        "sha256": "59c47dac548cddf52f5a61d66a59fe449ba5096046623ae51149e6ea7f29629f"
      },
      {
        "path": "/data2/k6tk/05/05c748b00c24fad9ba09338f59e229736cba707410ff1300db3147fb1b16176f.png",
        "sha256": "05c748b00c24fad9ba09338f59e229736cba707410ff1300db3147fb1b16176f"
      },
      {
        "path": "/data2/k6tk/33/339055ceb16d9b6144081c51bddd96d38129547adf7b63090e1237ad6281e12a.png",
        "sha256": "339055ceb16d9b6144081c51bddd96d38129547adf7b63090e1237ad6281e12a"
      },
      {
        "path": "/data2/k6tk/f8/f8936d5809232b341540e4afb6a264a9f87a7be045781a3645b13102266bf5c3.png",
        "sha256": "f8936d5809232b341540e4afb6a264a9f87a7be045781a3645b13102266bf5c3"
      },
      {
        "path": "/data2/k6tk/77/77a4263a77545a9245f45420adcc68d4b08f56e7e293fc4957acd54068530ebf.png",
        "sha256": "77a4263a77545a9245f45420adcc68d4b08f56e7e293fc4957acd54068530ebf"
      },
      {
        "path": "/data2/k6tk/85/853d0de28e099a66a8162ca2361b0f74fbebbc2f33e6f942f93163f5baa85024.png",
        "sha256": "853d0de28e099a66a8162ca2361b0f74fbebbc2f33e6f942f93163f5baa85024"
      },
      {
        "path": "/data2/k6tk/36/360ff6184b3c8474d5d584f71410bcb91e9641de1f5f69c845c7c8af8e4dd7f2.png",
        "sha256": "360ff6184b3c8474d5d584f71410bcb91e9641de1f5f69c845c7c8af8e4dd7f2"
      },
      {
        "path": "/data2/k6tk/c4/c45e8e7426947baccd4d362b110378861325ccc7a500df229f7ae4196a8c4bd4.png",
        "sha256": "c45e8e7426947baccd4d362b110378861325ccc7a500df229f7ae4196a8c4bd4"
      },
      {
        "path": "/data2/k6tk/ee/eeead61842cf07c8a8ff406e0a4004fd1ed0d366ff2532bcbeac05467cee149b.png",
        "sha256": "eeead61842cf07c8a8ff406e0a4004fd1ed0d366ff2532bcbeac05467cee149b"
      },
      {
        "path": "/data2/k6tk/fb/fb8aa83ccf0cce4cf5f3c458b31df0f1eb6af69e00a644a2c34a397fe37e334e.png",
        "sha256": "fb8aa83ccf0cce4cf5f3c458b31df0f1eb6af69e00a644a2c34a397fe37e334e"
      },
      {
        "path": "/data2/k6tk/60/6046106740ee171b33d24f6b21466b1bd23c3aefc1ad5bbeaa6e9f22ba01ef54.png",
        "sha256": "6046106740ee171b33d24f6b21466b1bd23c3aefc1ad5bbeaa6e9f22ba01ef54"
      },
      {
        "path": "/data2/k6tk/d8/d83f771a8566bbeac3822b5519a7e2bd8aa3f40a2c3650a852267ae0c286c205.png",
        "sha256": "d83f771a8566bbeac3822b5519a7e2bd8aa3f40a2c3650a852267ae0c286c205"
      },
      {
        "path": "/data2/k6tk/8e/8eae873b1a4090d3f083846f7640d8aaeb37a93d9fb674a8d4d7110922492eec.png",
        "sha256": "8eae873b1a4090d3f083846f7640d8aaeb37a93d9fb674a8d4d7110922492eec"
      },
      {
        "path": "/data2/k6tk/4f/4fc1ece2c5b97beea7af91d67edbd61d4011d50df7be622228235591da066f2d.png",
        "sha256": "4fc1ece2c5b97beea7af91d67edbd61d4011d50df7be622228235591da066f2d"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the blackboard and facing away from the bottles, is the sponge to the left or the right of the bottles?",
    "timestamps": [
      0.0,
      3.1666666666666665,
      6.333333333333333,
      9.5,
      12.683333333333334,
      15.85,
      19.016666666666666,
      22.2,
      25.366666666666667,
      28.533333333333335,
      31.716666666666665,
      34.88333333333333,
      38.05,
      41.233333333333334,
      44.4,
      47.56666666666667,
      50.75,
      53.916666666666664,
      57.083333333333336,
      60.266666666666666,
      63.43333333333333,
      66.6,
      69.78333333333333,
      72.95,
      76.11666666666666,
      79.3,
      82.46666666666667,
      85.63333333333334,
      88.81666666666666,
      91.98333333333333,
      95.15,
      98.33333333333333
    ],
    "total_num_frames": 5901
  },
  "target": "<think>\nStep 1: find the blackboard, the bottles and the sponge.\nStep 2: facing the bottles from the blackboard, I find the sponge to my right.\nStep 3: I face away from the bottles by making a half turn. Front and back swap, and left and right swap.\nSo I find the sponge to my left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "ff6f8940d30843eef77183d8e6fb21e6cbda3def444fbc181433f5855e483cfd"
  },
  "facing": "away",
  "candidate_id": "ground-22d2c24bac403e9857f260f2aeaae2def41928c5a26b82bb493210784c7e38da",
  "label_row_keys": [
    "qaf0982c5c85d8e27b48c31dc"
  ]
}
```

## 10. q7f505f7890f07e16366dbe4a_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q7f505f7890f07e16366dbe4a",
      "source_store_i": 2800,
      "source_row_sha256": "c70c2dc37d578a1f92d44a9661e8e88e7e1f88c60974ff328af89d31b9145c99",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q7f505f7890f07e16366dbe4a_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vb9145170eaad",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      231,
      463,
      695,
      926,
      1158,
      1390,
      1621,
      1853,
      2085,
      2317,
      2548,
      2780,
      3012,
      3243,
      3475,
      3707,
      3939,
      4170,
      4402,
      4634,
      4865,
      5097,
      5329,
      5561,
      5792,
      6024,
      6256,
      6487,
      6719,
      6951,
      7183
    ],
    "frames": [
      {
        "path": "/data2/k6tk/05/056b647a1b56c7f3e5cce5c6ead27b77587d8302477186b8b132ab0617088683.png",
        "sha256": "056b647a1b56c7f3e5cce5c6ead27b77587d8302477186b8b132ab0617088683"
      },
      {
        "path": "/data2/k6tk/4d/4df265f3007d8dc0e5e54be65a3acaec0a57bcd9c6f310044d2240e0d712506c.png",
        "sha256": "4df265f3007d8dc0e5e54be65a3acaec0a57bcd9c6f310044d2240e0d712506c"
      },
      {
        "path": "/data2/k6tk/cf/cf4aa5706457c564d2af0e9a2eec3fb1dfbcc3a98178433743c3b2d02d815426.png",
        "sha256": "cf4aa5706457c564d2af0e9a2eec3fb1dfbcc3a98178433743c3b2d02d815426"
      },
      {
        "path": "/data2/k6tk/3c/3c8cc1c6c19ca5c71759395b36605dc4614cc674d809cc9459571079a96575f8.png",
        "sha256": "3c8cc1c6c19ca5c71759395b36605dc4614cc674d809cc9459571079a96575f8"
      },
      {
        "path": "/data2/k6tk/44/442a4cda9f920ac630310aaf60544635836b9327e3072d2be7dcfc38081b378f.png",
        "sha256": "442a4cda9f920ac630310aaf60544635836b9327e3072d2be7dcfc38081b378f"
      },
      {
        "path": "/data2/k6tk/f6/f658d41089ab22845cb8163d5f01b131cc9a02a170f4410a78a5c1dc0f1bdc90.png",
        "sha256": "f658d41089ab22845cb8163d5f01b131cc9a02a170f4410a78a5c1dc0f1bdc90"
      },
      {
        "path": "/data2/k6tk/52/52814a8ced4287851fdd88470c1a9bbcff0adece56db53266f27c6d2bc8bbb37.png",
        "sha256": "52814a8ced4287851fdd88470c1a9bbcff0adece56db53266f27c6d2bc8bbb37"
      },
      {
        "path": "/data2/k6tk/70/707e6f23da6dbb870f72ac5eec6212ff44943bc67ecbd0a9dd8d1ffbd33e4c91.png",
        "sha256": "707e6f23da6dbb870f72ac5eec6212ff44943bc67ecbd0a9dd8d1ffbd33e4c91"
      },
      {
        "path": "/data2/k6tk/9e/9e84747544d84827f6932b63dada4eb5b9b077d3f7612c935045668175e9561d.png",
        "sha256": "9e84747544d84827f6932b63dada4eb5b9b077d3f7612c935045668175e9561d"
      },
      {
        "path": "/data2/k6tk/ec/ecad4ac3c90810193eefa97433f771029b4c8c8fabd39d5a8abceaf2b04baa28.png",
        "sha256": "ecad4ac3c90810193eefa97433f771029b4c8c8fabd39d5a8abceaf2b04baa28"
      },
      {
        "path": "/data2/k6tk/b7/b7d151b7928981b51b72eccf11292d35ac411c630e1bedf4ce47fd4eec45f2d5.png",
        "sha256": "b7d151b7928981b51b72eccf11292d35ac411c630e1bedf4ce47fd4eec45f2d5"
      },
      {
        "path": "/data2/k6tk/9b/9b897a424943c927ec85fd37cad08130b077398074a8a3a20e1bf7901c7e413a.png",
        "sha256": "9b897a424943c927ec85fd37cad08130b077398074a8a3a20e1bf7901c7e413a"
      },
      {
        "path": "/data2/k6tk/21/210b894b15aa981d53454f1e92976edec5ab5763c324dad2641cd3ff5f971432.png",
        "sha256": "210b894b15aa981d53454f1e92976edec5ab5763c324dad2641cd3ff5f971432"
      },
      {
        "path": "/data2/k6tk/59/596fb5c7f20d2987024961934a189ada5fd0c5d2682772289af5b2c80196e843.png",
        "sha256": "596fb5c7f20d2987024961934a189ada5fd0c5d2682772289af5b2c80196e843"
      },
      {
        "path": "/data2/k6tk/67/674685b3d7f48e0a63b95994f30de81eedd3761aef90c7b72048ea147a763b6e.png",
        "sha256": "674685b3d7f48e0a63b95994f30de81eedd3761aef90c7b72048ea147a763b6e"
      },
      {
        "path": "/data2/k6tk/4a/4aadd241c374a96b6baf406f3e9f9fd67e5581951829ad8439d652cb61c87309.png",
        "sha256": "4aadd241c374a96b6baf406f3e9f9fd67e5581951829ad8439d652cb61c87309"
      },
      {
        "path": "/data2/k6tk/f4/f459178464bb088791c519232e72123ef92f40b49def06ab6323e50231d81fcb.png",
        "sha256": "f459178464bb088791c519232e72123ef92f40b49def06ab6323e50231d81fcb"
      },
      {
        "path": "/data2/k6tk/e5/e5505c9880aee7565f1df461ad297cc67cbb4e1cbe9260a11d5faed5517a6320.png",
        "sha256": "e5505c9880aee7565f1df461ad297cc67cbb4e1cbe9260a11d5faed5517a6320"
      },
      {
        "path": "/data2/k6tk/7b/7b1a73827d1ae25f8a681278aaad77ae6317f867bfbfb3335b40ad92c1c7d53c.png",
        "sha256": "7b1a73827d1ae25f8a681278aaad77ae6317f867bfbfb3335b40ad92c1c7d53c"
      },
      {
        "path": "/data2/k6tk/76/7694039b6af415dc67cbaecbef429a74eb2996e7e74ab43e0707403401350c2e.png",
        "sha256": "7694039b6af415dc67cbaecbef429a74eb2996e7e74ab43e0707403401350c2e"
      },
      {
        "path": "/data2/k6tk/14/144d768f47ae77fe4fe1ac144c7e68d2ce5511c12f0911643f1f710da981a83a.png",
        "sha256": "144d768f47ae77fe4fe1ac144c7e68d2ce5511c12f0911643f1f710da981a83a"
      },
      {
        "path": "/data2/k6tk/03/03b56f741720747408e960e2103bf2a3e5b29d7cfa1e45f753152b11a80a123f.png",
        "sha256": "03b56f741720747408e960e2103bf2a3e5b29d7cfa1e45f753152b11a80a123f"
      },
      {
        "path": "/data2/k6tk/eb/eb043fe7ded7875b1517534f80bd1a57d7268c4962d4b6db011a8e986f65e163.png",
        "sha256": "eb043fe7ded7875b1517534f80bd1a57d7268c4962d4b6db011a8e986f65e163"
      },
      {
        "path": "/data2/k6tk/98/98226d77b9c9493a0f5cc0a0a156c4ee7096f266acf6039d377f40aabd09fde6.png",
        "sha256": "98226d77b9c9493a0f5cc0a0a156c4ee7096f266acf6039d377f40aabd09fde6"
      },
      {
        "path": "/data2/k6tk/8c/8c5b2495e00bd518b226002c239bbbfdf0143d7afbe5ab8e2b62e388cf4a5f5a.png",
        "sha256": "8c5b2495e00bd518b226002c239bbbfdf0143d7afbe5ab8e2b62e388cf4a5f5a"
      },
      {
        "path": "/data2/k6tk/d4/d45445a173be02c48d645c42c830d35ed98f1462558f4345ce67c62e53d33fe9.png",
        "sha256": "d45445a173be02c48d645c42c830d35ed98f1462558f4345ce67c62e53d33fe9"
      },
      {
        "path": "/data2/k6tk/30/3085384b65099407fb50e44286cccab712660c72320e3721515e629268aea2cb.png",
        "sha256": "3085384b65099407fb50e44286cccab712660c72320e3721515e629268aea2cb"
      },
      {
        "path": "/data2/k6tk/c6/c60eec34b45fccdaacdc5ded800fa4cb688345518020be945c419e6ebea49f36.png",
        "sha256": "c60eec34b45fccdaacdc5ded800fa4cb688345518020be945c419e6ebea49f36"
      },
      {
        "path": "/data2/k6tk/36/36911c5faa4d1b155112f96d1419a07f3fff8a9d98702ca927e45ddcf84e3840.png",
        "sha256": "36911c5faa4d1b155112f96d1419a07f3fff8a9d98702ca927e45ddcf84e3840"
      },
      {
        "path": "/data2/k6tk/e5/e5072a24f3a7b2c5d53e034652422b699a451110868324a57268a920edba3dcf.png",
        "sha256": "e5072a24f3a7b2c5d53e034652422b699a451110868324a57268a920edba3dcf"
      },
      {
        "path": "/data2/k6tk/46/461a12c44b5a889818a5d8f5a6f036f35be123d276f6a21e446592f0df79765b.png",
        "sha256": "461a12c44b5a889818a5d8f5a6f036f35be123d276f6a21e446592f0df79765b"
      },
      {
        "path": "/data2/k6tk/f7/f74cef04373e56b8c8117a4518fe267380c9c5f313bb726e2d0a65d0bc529dff.png",
        "sha256": "f74cef04373e56b8c8117a4518fe267380c9c5f313bb726e2d0a65d0bc529dff"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the bag and facing away from the blinds, is the computer tower to the left or the right of the blinds?",
    "timestamps": [
      0.0,
      3.85,
      7.716666666666667,
      11.583333333333334,
      15.433333333333334,
      19.3,
      23.166666666666668,
      27.016666666666666,
      30.883333333333333,
      34.75,
      38.61666666666667,
      42.46666666666667,
      46.333333333333336,
      50.2,
      54.05,
      57.916666666666664,
      61.78333333333333,
      65.65,
      69.5,
      73.36666666666666,
      77.23333333333333,
      81.08333333333333,
      84.95,
      88.81666666666666,
      92.68333333333334,
      96.53333333333333,
      100.4,
      104.26666666666667,
      108.11666666666666,
      111.98333333333333,
      115.85,
      119.71666666666667
    ],
    "total_num_frames": 7184
  },
  "target": "<think>\nStep 1: find the bag, the blinds and the computer tower.\nStep 2: I stand at the bag facing the blinds; I find the computer tower to my right.\nStep 3: I face away from the blinds by making a half turn. Front and back swap, and left and right swap.\nSo I find the computer tower to my left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "8ca752e161bacf8deb0d0e2a95972a7276fd7ba492162cbb72f2aaf331eaeb2a"
  },
  "facing": "away",
  "candidate_id": "ground-8889e21568e5557b3408724a26e3b60c46be6e2cefd81ab55e32064408a44140",
  "label_row_keys": [
    "q7f505f7890f07e16366dbe4a"
  ]
}
```

## 11. q819e818a8991d737e16d1ec5_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q819e818a8991d737e16d1ec5",
      "source_store_i": 26606,
      "source_row_sha256": "39c9dd74dc083dd0aa2d78b87906d8475508b51d95c469aaa5fd9ac9c2cb4ce4",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q819e818a8991d737e16d1ec5_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v541c89282387",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      38,
      76,
      115,
      153,
      191,
      230,
      268,
      306,
      345,
      383,
      421,
      460,
      498,
      536,
      575,
      613,
      652,
      690,
      728,
      767,
      805,
      843,
      882,
      920,
      958,
      997,
      1035,
      1073,
      1112,
      1150,
      1189
    ],
    "frames": [
      {
        "path": "/data2/k6tk/3d/3d61f9f3352f0c17699171608d2bd5c5db41dda9f8df36c400af8c7714d65aae.png",
        "sha256": "3d61f9f3352f0c17699171608d2bd5c5db41dda9f8df36c400af8c7714d65aae"
      },
      {
        "path": "/data2/k6tk/ec/ecd105ad1940527bbed9e9e1c76ddde02127dce7c929684f7e3ab604e7f7712d.png",
        "sha256": "ecd105ad1940527bbed9e9e1c76ddde02127dce7c929684f7e3ab604e7f7712d"
      },
      {
        "path": "/data2/k6tk/40/4049006385694582e07b61aa54bc1a7910319333aba2ade152c2558eab676ae6.png",
        "sha256": "4049006385694582e07b61aa54bc1a7910319333aba2ade152c2558eab676ae6"
      },
      {
        "path": "/data2/k6tk/8f/8fcfc5197457fb5e663eaa275515f9815ca0f8ef7fb34ccf8f606797ca795d90.png",
        "sha256": "8fcfc5197457fb5e663eaa275515f9815ca0f8ef7fb34ccf8f606797ca795d90"
      },
      {
        "path": "/data2/k6tk/8e/8e871ce6f5c26672677a647d169d12490191d82e90dcfe1cef4255572cc2821e.png",
        "sha256": "8e871ce6f5c26672677a647d169d12490191d82e90dcfe1cef4255572cc2821e"
      },
      {
        "path": "/data2/k6tk/c2/c2248bcf802c7a2b754dc2e2fab45af73dc81d02db857ccd88afea77b3c11e0d.png",
        "sha256": "c2248bcf802c7a2b754dc2e2fab45af73dc81d02db857ccd88afea77b3c11e0d"
      },
      {
        "path": "/data2/k6tk/31/318dc3c4debb63fad21f6fd2fb951959f2d2ed5ca38622e4813a6542039fadf0.png",
        "sha256": "318dc3c4debb63fad21f6fd2fb951959f2d2ed5ca38622e4813a6542039fadf0"
      },
      {
        "path": "/data2/k6tk/1e/1ef946b74e263b9d103a49e8089b9ea64b70c96527b350d874764444b8778b00.png",
        "sha256": "1ef946b74e263b9d103a49e8089b9ea64b70c96527b350d874764444b8778b00"
      },
      {
        "path": "/data2/k6tk/45/4512b961ae93d65b79c0742145d51ecaeebd156026809dfc0dc72f10e8d4b878.png",
        "sha256": "4512b961ae93d65b79c0742145d51ecaeebd156026809dfc0dc72f10e8d4b878"
      },
      {
        "path": "/data2/k6tk/ef/efbf8c39eeb146e27e6cdcf62f54c5aa9b038efb3fd6e84e74ec273bf4a4579e.png",
        "sha256": "efbf8c39eeb146e27e6cdcf62f54c5aa9b038efb3fd6e84e74ec273bf4a4579e"
      },
      {
        "path": "/data2/k6tk/b4/b4bb15f0ece44ed83c0dfa1cd39ac0278031b224cc32c164e603f2ac6602ecdc.png",
        "sha256": "b4bb15f0ece44ed83c0dfa1cd39ac0278031b224cc32c164e603f2ac6602ecdc"
      },
      {
        "path": "/data2/k6tk/3b/3bc82cc0c263f0a2f556abce5baacf702c86c8aea94f370e2577c407adaadb5d.png",
        "sha256": "3bc82cc0c263f0a2f556abce5baacf702c86c8aea94f370e2577c407adaadb5d"
      },
      {
        "path": "/data2/k6tk/fa/fa8940b21420270d3020511f5ec6a34adf5f3f1273eb25e9653c34a82e2db6f9.png",
        "sha256": "fa8940b21420270d3020511f5ec6a34adf5f3f1273eb25e9653c34a82e2db6f9"
      },
      {
        "path": "/data2/k6tk/ac/ac5d6078b8f6ce1368ba514b6fd1d246674a022fd6c9293b406d3b2b8ea20df4.png",
        "sha256": "ac5d6078b8f6ce1368ba514b6fd1d246674a022fd6c9293b406d3b2b8ea20df4"
      },
      {
        "path": "/data2/k6tk/2f/2f5fd4cc4116a1c40f1f39cee46563153188c52ae5c103b7bdc0ac61030999b2.png",
        "sha256": "2f5fd4cc4116a1c40f1f39cee46563153188c52ae5c103b7bdc0ac61030999b2"
      },
      {
        "path": "/data2/k6tk/9d/9d3cd869841a0faccfe42fa1e7a70fe502107948a9456ac55d210a3c3331b0f0.png",
        "sha256": "9d3cd869841a0faccfe42fa1e7a70fe502107948a9456ac55d210a3c3331b0f0"
      },
      {
        "path": "/data2/k6tk/fa/fa6d402511ed3595cb6a3c32d81544eb65d8414a8c2424a6bd5c97ea42117f54.png",
        "sha256": "fa6d402511ed3595cb6a3c32d81544eb65d8414a8c2424a6bd5c97ea42117f54"
      },
      {
        "path": "/data2/k6tk/8c/8c208acb0322b0b4143dfacffb997fb41bf84be0c97a805c8f4965ed0db523a1.png",
        "sha256": "8c208acb0322b0b4143dfacffb997fb41bf84be0c97a805c8f4965ed0db523a1"
      },
      {
        "path": "/data2/k6tk/f6/f6e564a9a2c8d6d8ac79ba528c4fa7c67e45eace7bc413ea21c5252bb85d778b.png",
        "sha256": "f6e564a9a2c8d6d8ac79ba528c4fa7c67e45eace7bc413ea21c5252bb85d778b"
      },
      {
        "path": "/data2/k6tk/de/de43dd298e3de72ecc2c37b7be6a3d3aa149f8b5d7536ce10b4b71964d1e7c2f.png",
        "sha256": "de43dd298e3de72ecc2c37b7be6a3d3aa149f8b5d7536ce10b4b71964d1e7c2f"
      },
      {
        "path": "/data2/k6tk/70/70fc3b7a796ba0b89546ec2ac160ec272267f1d18cfca6c4becfae9dabba849f.png",
        "sha256": "70fc3b7a796ba0b89546ec2ac160ec272267f1d18cfca6c4becfae9dabba849f"
      },
      {
        "path": "/data2/k6tk/29/295b9c4e5d7fbfb089b4467aedc775d2a6cf16a5df55e3c28a128d27de491103.png",
        "sha256": "295b9c4e5d7fbfb089b4467aedc775d2a6cf16a5df55e3c28a128d27de491103"
      },
      {
        "path": "/data2/k6tk/e3/e390af587cbc770bde6b9fccebeecb3d2708fc7849bf046f4ef51c5867c646d6.png",
        "sha256": "e390af587cbc770bde6b9fccebeecb3d2708fc7849bf046f4ef51c5867c646d6"
      },
      {
        "path": "/data2/k6tk/31/31811ff98a623daf4930eb57fc906a01fa966ef3c3b630438ab7a1abe7c85a9c.png",
        "sha256": "31811ff98a623daf4930eb57fc906a01fa966ef3c3b630438ab7a1abe7c85a9c"
      },
      {
        "path": "/data2/k6tk/98/986098f1febb8b816af9b3b15140a3d41cb1199269a18802d88e8d033bb3108c.png",
        "sha256": "986098f1febb8b816af9b3b15140a3d41cb1199269a18802d88e8d033bb3108c"
      },
      {
        "path": "/data2/k6tk/af/af7af654d0be5e09427c36a708e1811909abc985e7a70895aa4dbe89b763305c.png",
        "sha256": "af7af654d0be5e09427c36a708e1811909abc985e7a70895aa4dbe89b763305c"
      },
      {
        "path": "/data2/k6tk/91/91359fd855e76e79c16af2244ec7c202af78cefc13881727cdfa5e780b180bb6.png",
        "sha256": "91359fd855e76e79c16af2244ec7c202af78cefc13881727cdfa5e780b180bb6"
      },
      {
        "path": "/data2/k6tk/cd/cdccd3965b06f265d4840864a47d3ee4340c83133548b573e8e740107a3fc213.png",
        "sha256": "cdccd3965b06f265d4840864a47d3ee4340c83133548b573e8e740107a3fc213"
      },
      {
        "path": "/data2/k6tk/20/20f79179d6fb8c48e0546039b245a2c418b1984e9ddd9975b3d0592cdb56843d.png",
        "sha256": "20f79179d6fb8c48e0546039b245a2c418b1984e9ddd9975b3d0592cdb56843d"
      },
      {
        "path": "/data2/k6tk/8d/8d03a6166d7815bd2a672c8ea53e5dc0d483c441d48e5b22007431f8d87ac163.png",
        "sha256": "8d03a6166d7815bd2a672c8ea53e5dc0d483c441d48e5b22007431f8d87ac163"
      },
      {
        "path": "/data2/k6tk/4c/4c68562ebb6b634b4d0e21efae1609471129ae2f6c3772e9b44920971bf2cc50.png",
        "sha256": "4c68562ebb6b634b4d0e21efae1609471129ae2f6c3772e9b44920971bf2cc50"
      },
      {
        "path": "/data2/k6tk/34/347926ecc4097ddc688fcd5ba3863fcc804e89a721b02f4211c2937cae7fa0a0.png",
        "sha256": "347926ecc4097ddc688fcd5ba3863fcc804e89a721b02f4211c2937cae7fa0a0"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the backpack and facing away from the coffee table, is the plant to the left or the right of the coffee table?",
    "timestamps": [
      0.0,
      1.5833333333333333,
      3.1666666666666665,
      4.791666666666667,
      6.375,
      7.958333333333333,
      9.583333333333334,
      11.166666666666666,
      12.75,
      14.375,
      15.958333333333334,
      17.541666666666668,
      19.166666666666668,
      20.75,
      22.333333333333332,
      23.958333333333332,
      25.541666666666668,
      27.166666666666668,
      28.75,
      30.333333333333332,
      31.958333333333332,
      33.541666666666664,
      35.125,
      36.75,
      38.333333333333336,
      39.916666666666664,
      41.541666666666664,
      43.125,
      44.708333333333336,
      46.333333333333336,
      47.916666666666664,
      49.541666666666664
    ],
    "total_num_frames": 1190
  },
  "target": "<think>\nStep 1: find the backpack, the coffee table and the plant.\nStep 2: facing the coffee table from the backpack, I find the plant to my left.\nStep 3: I face away from the coffee table by making a half turn. Front and back swap, and left and right swap.\nSo I find the plant to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "ac1145a883932f0a008888edac8e2d8dc0eded62736eea8c417f8a2e3aedb3fb"
  },
  "facing": "away",
  "candidate_id": "ground-aaf97a921be15db058b0cc91440d65b3732eee8b7761f62f05d8943ddbca8c6c",
  "label_row_keys": [
    "q819e818a8991d737e16d1ec5"
  ]
}
```

## 12. qbaa1d5043dd7f142e7205d9b_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qbaa1d5043dd7f142e7205d9b",
      "source_store_i": 25045,
      "source_row_sha256": "accb44b84eb824fc58ee2743a836b79a6ae78ed64636952895d3e75e9a3e05e1",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 55,
        "end": 68,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qbaa1d5043dd7f142e7205d9b_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vc518a135acd3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      157,
      315,
      473,
      631,
      789,
      947,
      1105,
      1263,
      1421,
      1579,
      1737,
      1895,
      2053,
      2211,
      2369,
      2526,
      2684,
      2842,
      3000,
      3158,
      3316,
      3474,
      3632,
      3790,
      3948,
      4106,
      4264,
      4422,
      4580,
      4738,
      4896
    ],
    "frames": [
      {
        "path": "/data2/k6tk/54/54454b4bc98cb473384807f261414dd5db57d04f65d94f6ca6bd4a80d6e06ae5.png",
        "sha256": "54454b4bc98cb473384807f261414dd5db57d04f65d94f6ca6bd4a80d6e06ae5"
      },
      {
        "path": "/data2/k6tk/90/902d4efeadde4555be8e3c398f12f602d81c3b8bb1665f23e480e5eb666db54d.png",
        "sha256": "902d4efeadde4555be8e3c398f12f602d81c3b8bb1665f23e480e5eb666db54d"
      },
      {
        "path": "/data2/k6tk/0d/0dc2f88050ffa2b973396fb06adf1d4aaa8eed6ba1f3a585159ce54cc39ba28a.png",
        "sha256": "0dc2f88050ffa2b973396fb06adf1d4aaa8eed6ba1f3a585159ce54cc39ba28a"
      },
      {
        "path": "/data2/k6tk/56/5694657e2112f8c6a0c1d87edb008489bd86f91af700455d30eb95d65687e58b.png",
        "sha256": "5694657e2112f8c6a0c1d87edb008489bd86f91af700455d30eb95d65687e58b"
      },
      {
        "path": "/data2/k6tk/c2/c2171852124cb5ac2a0c86eb3e4bbe272da76b5bae29d1b865060b22ba5fe3b2.png",
        "sha256": "c2171852124cb5ac2a0c86eb3e4bbe272da76b5bae29d1b865060b22ba5fe3b2"
      },
      {
        "path": "/data2/k6tk/53/53183cc158202bda1e89010e8dd01178d84528d19cd8e1b3383aa4454591946b.png",
        "sha256": "53183cc158202bda1e89010e8dd01178d84528d19cd8e1b3383aa4454591946b"
      },
      {
        "path": "/data2/k6tk/3d/3de847a0621792149f6d1a7c67d4ac3d347be2b1dfd11189c5948a83112ea136.png",
        "sha256": "3de847a0621792149f6d1a7c67d4ac3d347be2b1dfd11189c5948a83112ea136"
      },
      {
        "path": "/data2/k6tk/15/153bb7610aa58fa1a5bc8e3e44c6dff17dfea0223563391d9fc8497599815025.png",
        "sha256": "153bb7610aa58fa1a5bc8e3e44c6dff17dfea0223563391d9fc8497599815025"
      },
      {
        "path": "/data2/k6tk/4c/4c24c3e983f4746bb8bdeec11c102de7386533f6298e82f64a64213cdc3c6147.png",
        "sha256": "4c24c3e983f4746bb8bdeec11c102de7386533f6298e82f64a64213cdc3c6147"
      },
      {
        "path": "/data2/k6tk/40/40768fea45a75282dc829a430f1e098133e3db54a7e30b783a4e67c22befcefe.png",
        "sha256": "40768fea45a75282dc829a430f1e098133e3db54a7e30b783a4e67c22befcefe"
      },
      {
        "path": "/data2/k6tk/9c/9c291beeccd5c533a0565bc550aa0f7793516e9d93fde6a1e481c1b1b9cf4668.png",
        "sha256": "9c291beeccd5c533a0565bc550aa0f7793516e9d93fde6a1e481c1b1b9cf4668"
      },
      {
        "path": "/data2/k6tk/36/369014ae5233bcb8f88c778ad2a3fc04f9179827f0321dcf1962d32793f5340d.png",
        "sha256": "369014ae5233bcb8f88c778ad2a3fc04f9179827f0321dcf1962d32793f5340d"
      },
      {
        "path": "/data2/k6tk/cd/cd581847a9045895c767c00dbf28e126a9486b3fb74e3686dc3bdd9a4119b13b.png",
        "sha256": "cd581847a9045895c767c00dbf28e126a9486b3fb74e3686dc3bdd9a4119b13b"
      },
      {
        "path": "/data2/k6tk/42/42ce6df1df8bd8c658af716f6d5259ea0cc71c80628504e78d89a21eef5f2828.png",
        "sha256": "42ce6df1df8bd8c658af716f6d5259ea0cc71c80628504e78d89a21eef5f2828"
      },
      {
        "path": "/data2/k6tk/d5/d555b7d03885078a11efe47e29fa0bff65b6baf71afc3624d2fcfa458e5ce833.png",
        "sha256": "d555b7d03885078a11efe47e29fa0bff65b6baf71afc3624d2fcfa458e5ce833"
      },
      {
        "path": "/data2/k6tk/05/05e3b147fe93ae06e73864c7e0d9f0e299bfc3ba1f6ebd3341f5b07bea50fb80.png",
        "sha256": "05e3b147fe93ae06e73864c7e0d9f0e299bfc3ba1f6ebd3341f5b07bea50fb80"
      },
      {
        "path": "/data2/k6tk/4c/4cfffb7f4235591a5696d7207b15bce823a737830bc710639ea1e51e9a8453cf.png",
        "sha256": "4cfffb7f4235591a5696d7207b15bce823a737830bc710639ea1e51e9a8453cf"
      },
      {
        "path": "/data2/k6tk/23/23729d70b19541601c6243fa71e1323f7669000f3aea1cd42abc1d136bb09765.png",
        "sha256": "23729d70b19541601c6243fa71e1323f7669000f3aea1cd42abc1d136bb09765"
      },
      {
        "path": "/data2/k6tk/ba/bae8918f8c2647eb17a896c83aa45d1d09ff7ab55bda0f4fe3ae1684d5f2924a.png",
        "sha256": "bae8918f8c2647eb17a896c83aa45d1d09ff7ab55bda0f4fe3ae1684d5f2924a"
      },
      {
        "path": "/data2/k6tk/70/701c0412f9265384e946a722329a98843c7a1511956ad0dc22b1b6edc01c4280.png",
        "sha256": "701c0412f9265384e946a722329a98843c7a1511956ad0dc22b1b6edc01c4280"
      },
      {
        "path": "/data2/k6tk/de/de88f01f10069d89a515de71f13bd52d09755befbf605c4274e3612f26315691.png",
        "sha256": "de88f01f10069d89a515de71f13bd52d09755befbf605c4274e3612f26315691"
      },
      {
        "path": "/data2/k6tk/93/9386b23df98a1b53a5c673039f1329d4c6c72b59191a4f505078d1eebf0b705e.png",
        "sha256": "9386b23df98a1b53a5c673039f1329d4c6c72b59191a4f505078d1eebf0b705e"
      },
      {
        "path": "/data2/k6tk/89/8915c4daed66ab73754a099a4fea9f5b247f62ab5d73c8d531224ffccb3d2363.png",
        "sha256": "8915c4daed66ab73754a099a4fea9f5b247f62ab5d73c8d531224ffccb3d2363"
      },
      {
        "path": "/data2/k6tk/6e/6e28909231fef1bcd26b02bede53210a2cf2efc904684f44a48c1eb89aa2f3ac.png",
        "sha256": "6e28909231fef1bcd26b02bede53210a2cf2efc904684f44a48c1eb89aa2f3ac"
      },
      {
        "path": "/data2/k6tk/88/883c67a6e168c620f19b2be8416488681ea4691ca245142a47cb57ddbc0e7adf.png",
        "sha256": "883c67a6e168c620f19b2be8416488681ea4691ca245142a47cb57ddbc0e7adf"
      },
      {
        "path": "/data2/k6tk/82/82b9b62e38fd3c4e1249c71eec3d15f1d74133161edf5f222a26a7fae66849e2.png",
        "sha256": "82b9b62e38fd3c4e1249c71eec3d15f1d74133161edf5f222a26a7fae66849e2"
      },
      {
        "path": "/data2/k6tk/85/850ee44234b3d52ce0ec511d92d5777ff1b4f068bfbdc4854a2c384cf140d61d.png",
        "sha256": "850ee44234b3d52ce0ec511d92d5777ff1b4f068bfbdc4854a2c384cf140d61d"
      },
      {
        "path": "/data2/k6tk/41/41f952f00dda222dacbbcd256f439e51dbaf0902a12c54d4179bbbcf1ba775d2.png",
        "sha256": "41f952f00dda222dacbbcd256f439e51dbaf0902a12c54d4179bbbcf1ba775d2"
      },
      {
        "path": "/data2/k6tk/7c/7c5247102674cb18a89306cddf31bda76d98f5c29776d9959201c2739e224fc2.png",
        "sha256": "7c5247102674cb18a89306cddf31bda76d98f5c29776d9959201c2739e224fc2"
      },
      {
        "path": "/data2/k6tk/bb/bbbf9af32674a7227c28fcbd55f676d3b55813dc35287bb2104bc1b9d26384aa.png",
        "sha256": "bbbf9af32674a7227c28fcbd55f676d3b55813dc35287bb2104bc1b9d26384aa"
      },
      {
        "path": "/data2/k6tk/e9/e97d7b25c1c79e80dff63616413e86ad2ed818df0a87cb2827438423506a17e8.png",
        "sha256": "e97d7b25c1c79e80dff63616413e86ad2ed818df0a87cb2827438423506a17e8"
      },
      {
        "path": "/data2/k6tk/ee/ee2c8785014540331d4f6d2a5de9c098fedeffe615da47a1d327586ffd646641.png",
        "sha256": "ee2c8785014540331d4f6d2a5de9c098fedeffe615da47a1d327586ffd646641"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From the perspective of standing at the whiteboard and facing away from the ceiling light, does the trash can lie to its left or right?",
    "timestamps": [
      0.0,
      2.6166666666666667,
      5.25,
      7.883333333333334,
      10.516666666666667,
      13.15,
      15.783333333333333,
      18.416666666666668,
      21.05,
      23.683333333333334,
      26.316666666666666,
      28.95,
      31.583333333333332,
      34.21666666666667,
      36.85,
      39.483333333333334,
      42.1,
      44.733333333333334,
      47.36666666666667,
      50.0,
      52.63333333333333,
      55.266666666666666,
      57.9,
      60.53333333333333,
      63.166666666666664,
      65.8,
      68.43333333333334,
      71.06666666666666,
      73.7,
      76.33333333333333,
      78.96666666666667,
      81.6
    ],
    "total_num_frames": 4897
  },
  "target": "<think>\nStep 1: find the whiteboard, the ceiling light and the trash can.\nStep 2: I stand at the whiteboard facing the ceiling light; I find the trash can to my left.\nStep 3: I face away from the ceiling light by making a half turn. Front and back swap, and left and right swap.\nSo I find the trash can to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "92ecb7140d9cae007506685dfce99d47d49fa7e64719f0f0f3971d47c54484f1"
  },
  "facing": "away",
  "candidate_id": "ground-e497bf387fb21367c0a130567fa5df0f17cfe031fdf5c73a93fc07cdf72fae69",
  "label_row_keys": [
    "qbaa1d5043dd7f142e7205d9b"
  ]
}
```

## 13. qf88ba060ae28fd2df280ec6d-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qf88ba060ae28fd2df280ec6d-p1",
      "source_store_i": 76556,
      "source_row_sha256": "70b78bc8eb9705adb81f6aaebbec471543dd88a0e40d63c8baa8401991bfd621",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qf88ba060ae28fd2df280ec6d-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd805e2335668",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      239,
      479,
      719,
      959,
      1199,
      1439,
      1679,
      1919,
      2159,
      2399,
      2638,
      2878,
      3118,
      3358,
      3598,
      3838,
      4078,
      4318,
      4558,
      4798,
      5037,
      5277,
      5517,
      5757,
      5997,
      6237,
      6477,
      6717,
      6957,
      7197,
      7437
    ],
    "frames": [
      {
        "path": "/data2/k6tk/03/0308671887979a7e7b79426b0ef6dee0c657d392bec85955ee005076a4b818f7.png",
        "sha256": "0308671887979a7e7b79426b0ef6dee0c657d392bec85955ee005076a4b818f7"
      },
      {
        "path": "/data2/k6tk/f6/f6a994d7ae22faa0e8e54f19eb8c80c5655c5c21705754d02fd985942a54e854.png",
        "sha256": "f6a994d7ae22faa0e8e54f19eb8c80c5655c5c21705754d02fd985942a54e854"
      },
      {
        "path": "/data2/k6tk/23/2359cb88a4c49370818001b402cf7fc96c0e7008d174e8e66dcb9746237c924e.png",
        "sha256": "2359cb88a4c49370818001b402cf7fc96c0e7008d174e8e66dcb9746237c924e"
      },
      {
        "path": "/data2/k6tk/ce/ce71056b7e750b0045c5ae52bc30ef4391193b0353490fda978c4e2ee6ac1726.png",
        "sha256": "ce71056b7e750b0045c5ae52bc30ef4391193b0353490fda978c4e2ee6ac1726"
      },
      {
        "path": "/data2/k6tk/31/3158e44b40cd5e55e55b8285f9f8fa61fb79f3a3ea7e68b77b7879f409dd183b.png",
        "sha256": "3158e44b40cd5e55e55b8285f9f8fa61fb79f3a3ea7e68b77b7879f409dd183b"
      },
      {
        "path": "/data2/k6tk/a4/a47909bffd15b6a99c2e3c3c38223f94f6f987dccf1c359233c8ff98b49eefc8.png",
        "sha256": "a47909bffd15b6a99c2e3c3c38223f94f6f987dccf1c359233c8ff98b49eefc8"
      },
      {
        "path": "/data2/k6tk/ae/ae45b369f976429fa9e435ab865a3f0e0748d3357d6933bf09a47878263ca2d2.png",
        "sha256": "ae45b369f976429fa9e435ab865a3f0e0748d3357d6933bf09a47878263ca2d2"
      },
      {
        "path": "/data2/k6tk/78/78eb08b54f3a8cc430077c7bad3f7cfe0b5a63e80fee4943f3057cf2f45ec877.png",
        "sha256": "78eb08b54f3a8cc430077c7bad3f7cfe0b5a63e80fee4943f3057cf2f45ec877"
      },
      {
        "path": "/data2/k6tk/f3/f3f3bf4463102429a9b76d201d6da59bdbddf73da7b80bc3f859de1ef1cd2936.png",
        "sha256": "f3f3bf4463102429a9b76d201d6da59bdbddf73da7b80bc3f859de1ef1cd2936"
      },
      {
        "path": "/data2/k6tk/fc/fc6775cad6c95dcd1ae718e0527b8aced495d85eb7656954c474699991c92ccf.png",
        "sha256": "fc6775cad6c95dcd1ae718e0527b8aced495d85eb7656954c474699991c92ccf"
      },
      {
        "path": "/data2/k6tk/3c/3c11a3b53f4bb86a4114735cb731688dc8c8d7b0586d848d21978f9dbe604bfa.png",
        "sha256": "3c11a3b53f4bb86a4114735cb731688dc8c8d7b0586d848d21978f9dbe604bfa"
      },
      {
        "path": "/data2/k6tk/21/2117818c9df6324f11d6fc4046ab56abc0f9808c7c70235b61fe6317cd27094a.png",
        "sha256": "2117818c9df6324f11d6fc4046ab56abc0f9808c7c70235b61fe6317cd27094a"
      },
      {
        "path": "/data2/k6tk/d3/d3cb9b6b69f850084e8dc455e6b9ba8b15db24d1e36034720d9cc989881e431c.png",
        "sha256": "d3cb9b6b69f850084e8dc455e6b9ba8b15db24d1e36034720d9cc989881e431c"
      },
      {
        "path": "/data2/k6tk/23/231d03f5c03daf4371f18ae705c60ffd23c8905de949b425bba5cdda6e750e62.png",
        "sha256": "231d03f5c03daf4371f18ae705c60ffd23c8905de949b425bba5cdda6e750e62"
      },
      {
        "path": "/data2/k6tk/b9/b9e6236772ad5436628dcddc37e9c73a759650f655faac7190f20d7b0d97d63a.png",
        "sha256": "b9e6236772ad5436628dcddc37e9c73a759650f655faac7190f20d7b0d97d63a"
      },
      {
        "path": "/data2/k6tk/d6/d65ce4248641220ebc262343cc3e376301393b15b1f98f60c7d008a014da2fa6.png",
        "sha256": "d65ce4248641220ebc262343cc3e376301393b15b1f98f60c7d008a014da2fa6"
      },
      {
        "path": "/data2/k6tk/3e/3ea7cc1145904a2caee5dad5d7f1f67bcfc3045eb2e799004aa783a03756bd86.png",
        "sha256": "3ea7cc1145904a2caee5dad5d7f1f67bcfc3045eb2e799004aa783a03756bd86"
      },
      {
        "path": "/data2/k6tk/f9/f99324ed41575c9eb3e41776d3203110bd2a4f472a27f4bb39f5bc0fd39ded42.png",
        "sha256": "f99324ed41575c9eb3e41776d3203110bd2a4f472a27f4bb39f5bc0fd39ded42"
      },
      {
        "path": "/data2/k6tk/cb/cb407c8ef953e88e24351ad3b4876b2cd1924754e60580b7ae582393e3830425.png",
        "sha256": "cb407c8ef953e88e24351ad3b4876b2cd1924754e60580b7ae582393e3830425"
      },
      {
        "path": "/data2/k6tk/4b/4b50dee2d9691af311d0c31ff7549c9fc28562b1ef3677ab43a38d8ebac3b996.png",
        "sha256": "4b50dee2d9691af311d0c31ff7549c9fc28562b1ef3677ab43a38d8ebac3b996"
      },
      {
        "path": "/data2/k6tk/c8/c8b84e6540378501e43f072b7007d55e32b1dac9447246d05fc2df4923f792b7.png",
        "sha256": "c8b84e6540378501e43f072b7007d55e32b1dac9447246d05fc2df4923f792b7"
      },
      {
        "path": "/data2/k6tk/cc/cc22ae312740f029f96f8c940822a3b1ab1a364713a7e6e5427fa3699109a760.png",
        "sha256": "cc22ae312740f029f96f8c940822a3b1ab1a364713a7e6e5427fa3699109a760"
      },
      {
        "path": "/data2/k6tk/9a/9a1e0cc1dd2949493e1d5fdb261179dd5f7bf8a5c990a1db86d57e0a0baab7cc.png",
        "sha256": "9a1e0cc1dd2949493e1d5fdb261179dd5f7bf8a5c990a1db86d57e0a0baab7cc"
      },
      {
        "path": "/data2/k6tk/e9/e9dad281cf82ddcb7e4e0301e44a995f55bd6fd966298b07fb34dab0fde33040.png",
        "sha256": "e9dad281cf82ddcb7e4e0301e44a995f55bd6fd966298b07fb34dab0fde33040"
      },
      {
        "path": "/data2/k6tk/ee/ee259ad811b17fe10069517bfec0d452d45cf5833350bf118cb92f133f5644b4.png",
        "sha256": "ee259ad811b17fe10069517bfec0d452d45cf5833350bf118cb92f133f5644b4"
      },
      {
        "path": "/data2/k6tk/f3/f330761c85cbb596323753d309411b8b3d72d4d30637b606cafb339d2cf93573.png",
        "sha256": "f330761c85cbb596323753d309411b8b3d72d4d30637b606cafb339d2cf93573"
      },
      {
        "path": "/data2/k6tk/73/73aac4a6e892bd0ce7bb5f9638a4e649e1f24370f43a84344ac78d6dc31f2c25.png",
        "sha256": "73aac4a6e892bd0ce7bb5f9638a4e649e1f24370f43a84344ac78d6dc31f2c25"
      },
      {
        "path": "/data2/k6tk/c5/c5c1751b18e812b85daee903d66c0907dc7b7650216f15a45580ee098a4514aa.png",
        "sha256": "c5c1751b18e812b85daee903d66c0907dc7b7650216f15a45580ee098a4514aa"
      },
      {
        "path": "/data2/k6tk/31/31331f5b47058050a8f2310be65bc9fc3ae0ef104415854e7da5f5c9a37b9e38.png",
        "sha256": "31331f5b47058050a8f2310be65bc9fc3ae0ef104415854e7da5f5c9a37b9e38"
      },
      {
        "path": "/data2/k6tk/62/62854029a13d483709e2fd0f24709bf1804ba0b6162cea62c17efec6aadc7def.png",
        "sha256": "62854029a13d483709e2fd0f24709bf1804ba0b6162cea62c17efec6aadc7def"
      },
      {
        "path": "/data2/k6tk/ed/ed6e52c7aae7a031f420bc2a54bd592abeb167f4fcd0c8fc753cdc313702ca79.png",
        "sha256": "ed6e52c7aae7a031f420bc2a54bd592abeb167f4fcd0c8fc753cdc313702ca79"
      },
      {
        "path": "/data2/k6tk/ec/ecaa9fd26d67ce44c4655b813ae2cfdd53d9a2ebe6fc700f8dd91a620f6bdcfa.png",
        "sha256": "ecaa9fd26d67ce44c4655b813ae2cfdd53d9a2ebe6fc700f8dd91a620f6bdcfa"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the heater and facing away from the chair, is the bowl on my left or on my right?",
    "timestamps": [
      0.0,
      3.9833333333333334,
      7.983333333333333,
      11.983333333333333,
      15.983333333333333,
      19.983333333333334,
      23.983333333333334,
      27.983333333333334,
      31.983333333333334,
      35.983333333333334,
      39.983333333333334,
      43.96666666666667,
      47.96666666666667,
      51.96666666666667,
      55.96666666666667,
      59.96666666666667,
      63.96666666666667,
      67.96666666666667,
      71.96666666666667,
      75.96666666666667,
      79.96666666666667,
      83.95,
      87.95,
      91.95,
      95.95,
      99.95,
      103.95,
      107.95,
      111.95,
      115.95,
      119.95,
      123.95
    ],
    "total_num_frames": 7438
  },
  "target": "<think>\nStep 1: find the heater, the chair and the bowl.\nStep 2: facing the chair from the heater, I find the bowl to my left.\nStep 3: I face away from the chair by making a half turn. Front and back swap, and left and right swap.\nSo I find the bowl to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "qf88ba060ae28fd2df280ec6d",
  "paraphrase_template": "easy_vsi",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "6cb51c357dc9f488de0e5b2ad20415bc3a1227917f3e99743e3925be3a24f970"
  },
  "facing": "away",
  "candidate_id": "ground-b45331675af8263c743ac021c49d12f666103df49043fb5dc4b7badc048f11c9",
  "label_row_keys": [
    "qf88ba060ae28fd2df280ec6d-p1"
  ]
}
```

## 14. q438c872b185af383edda98ab-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q438c872b185af383edda98ab-p1",
      "source_store_i": 67922,
      "source_row_sha256": "a53cd00a8a161922be0bc2a22be168046d61eb62874f8509e4b79dda14b4241e",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q438c872b185af383edda98ab-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v60ea1eee233b",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      115,
      230,
      346,
      461,
      577,
      692,
      808,
      923,
      1039,
      1154,
      1269,
      1385,
      1500,
      1616,
      1731,
      1847,
      1962,
      2078,
      2193,
      2309,
      2424,
      2539,
      2655,
      2770,
      2886,
      3001,
      3117,
      3232,
      3348,
      3463,
      3579
    ],
    "frames": [
      {
        "path": "/data2/k6tk/05/056e09221d6aa0666e3f4aa48037111b6cd7e86babcacec48bcbf9188aee3e06.png",
        "sha256": "056e09221d6aa0666e3f4aa48037111b6cd7e86babcacec48bcbf9188aee3e06"
      },
      {
        "path": "/data2/k6tk/b1/b189d066a79fff533cd9ea6931e6d1cd2781d8238afcef0487f58cd031b0d9c2.png",
        "sha256": "b189d066a79fff533cd9ea6931e6d1cd2781d8238afcef0487f58cd031b0d9c2"
      },
      {
        "path": "/data2/k6tk/d8/d8b9db00e1f9f199bd95a28d088127f26290fb41606a084bca62aff8830205f9.png",
        "sha256": "d8b9db00e1f9f199bd95a28d088127f26290fb41606a084bca62aff8830205f9"
      },
      {
        "path": "/data2/k6tk/da/da5c1d4970ca213613bc1bbf59fd3febfa6b6aec743dd468f718d64e0030f7a1.png",
        "sha256": "da5c1d4970ca213613bc1bbf59fd3febfa6b6aec743dd468f718d64e0030f7a1"
      },
      {
        "path": "/data2/k6tk/c4/c4608eec4b63bd60b31ecb6199aedd22a210539e9f291e108dd15a9befe4fc23.png",
        "sha256": "c4608eec4b63bd60b31ecb6199aedd22a210539e9f291e108dd15a9befe4fc23"
      },
      {
        "path": "/data2/k6tk/bb/bb35732e08cc225a043366ad52fd301f678d46b0bf145b0851ac09e8d08862b6.png",
        "sha256": "bb35732e08cc225a043366ad52fd301f678d46b0bf145b0851ac09e8d08862b6"
      },
      {
        "path": "/data2/k6tk/2e/2e8381735b8c38ad9756afbb37458894c281d7762cb09fba6358bd28c6512bda.png",
        "sha256": "2e8381735b8c38ad9756afbb37458894c281d7762cb09fba6358bd28c6512bda"
      },
      {
        "path": "/data2/k6tk/0f/0fa2e5ae63432641e334ca6a05083a50b562280598f784f6adb8a2798ff29770.png",
        "sha256": "0fa2e5ae63432641e334ca6a05083a50b562280598f784f6adb8a2798ff29770"
      },
      {
        "path": "/data2/k6tk/fd/fdbf014e53d0de2cf571d20642f44c26841d5ac290e33fd7729889b9f3423a09.png",
        "sha256": "fdbf014e53d0de2cf571d20642f44c26841d5ac290e33fd7729889b9f3423a09"
      },
      {
        "path": "/data2/k6tk/87/8731e97ba6b35493bd93f1eefd9b1f9f58a24d99d8d89f5370645c0e2df202a3.png",
        "sha256": "8731e97ba6b35493bd93f1eefd9b1f9f58a24d99d8d89f5370645c0e2df202a3"
      },
      {
        "path": "/data2/k6tk/1e/1e8fb3264cd013c3cf9d3488639cb0f60f4c0ad16af07273ef1d41af2068d989.png",
        "sha256": "1e8fb3264cd013c3cf9d3488639cb0f60f4c0ad16af07273ef1d41af2068d989"
      },
      {
        "path": "/data2/k6tk/8c/8cea6a7675bf1daf8a6b376972e48436081272c7f3a858a17463439960937060.png",
        "sha256": "8cea6a7675bf1daf8a6b376972e48436081272c7f3a858a17463439960937060"
      },
      {
        "path": "/data2/k6tk/b8/b84811d8783ae422b5dde881906b1237ff8d06eb12f220026cca85119ff962bb.png",
        "sha256": "b84811d8783ae422b5dde881906b1237ff8d06eb12f220026cca85119ff962bb"
      },
      {
        "path": "/data2/k6tk/09/09c436ba05f2cbca2dacfaa10b2154e9b5f5d03d054327136f8c74b6746984d6.png",
        "sha256": "09c436ba05f2cbca2dacfaa10b2154e9b5f5d03d054327136f8c74b6746984d6"
      },
      {
        "path": "/data2/k6tk/40/40d62e608fa3fb2fbbf15da7f481c45323bacb955f429be5c51f4e111b470295.png",
        "sha256": "40d62e608fa3fb2fbbf15da7f481c45323bacb955f429be5c51f4e111b470295"
      },
      {
        "path": "/data2/k6tk/4e/4ecb37376ca06837c99594b1dd229e3880eb9572ba406b6a99e148957127d340.png",
        "sha256": "4ecb37376ca06837c99594b1dd229e3880eb9572ba406b6a99e148957127d340"
      },
      {
        "path": "/data2/k6tk/be/be7e2fba996a380bd07c87048505430322a3675f84c06a0630f9c503cb0fc07a.png",
        "sha256": "be7e2fba996a380bd07c87048505430322a3675f84c06a0630f9c503cb0fc07a"
      },
      {
        "path": "/data2/k6tk/57/57ff972d4a6f445bbcbe0c01d161d6106f9bfa62724a6c072962937c364594bd.png",
        "sha256": "57ff972d4a6f445bbcbe0c01d161d6106f9bfa62724a6c072962937c364594bd"
      },
      {
        "path": "/data2/k6tk/26/2696922f3b577b2444165d53d0fc7b46fb6f18131fcec4098e94509a50a706a2.png",
        "sha256": "2696922f3b577b2444165d53d0fc7b46fb6f18131fcec4098e94509a50a706a2"
      },
      {
        "path": "/data2/k6tk/12/122e6ddbae6fc5316453e73f3abf529abae28caee881f8664a36da03cb0b9590.png",
        "sha256": "122e6ddbae6fc5316453e73f3abf529abae28caee881f8664a36da03cb0b9590"
      },
      {
        "path": "/data2/k6tk/91/91a48f3eaab36df2d475c808a9f1726fae45c4b04b8fcc30819c92cf1688f03d.png",
        "sha256": "91a48f3eaab36df2d475c808a9f1726fae45c4b04b8fcc30819c92cf1688f03d"
      },
      {
        "path": "/data2/k6tk/39/39007b65b946573a1bc91fc073791ebf6b7a5c3001997feaa674bdd549509760.png",
        "sha256": "39007b65b946573a1bc91fc073791ebf6b7a5c3001997feaa674bdd549509760"
      },
      {
        "path": "/data2/k6tk/61/6151623c984fb862a56383fcb163aa5481bbf890b2cd9044e8952452a97d7ad1.png",
        "sha256": "6151623c984fb862a56383fcb163aa5481bbf890b2cd9044e8952452a97d7ad1"
      },
      {
        "path": "/data2/k6tk/36/363c44bd1ae0fb75b6b10dc6544da9e4d39f183335208e73dde49ca4a553b4ab.png",
        "sha256": "363c44bd1ae0fb75b6b10dc6544da9e4d39f183335208e73dde49ca4a553b4ab"
      },
      {
        "path": "/data2/k6tk/04/044b4a9990d483f7abb4880dae1c6545520ad486c85b438c46788e6840fc1468.png",
        "sha256": "044b4a9990d483f7abb4880dae1c6545520ad486c85b438c46788e6840fc1468"
      },
      {
        "path": "/data2/k6tk/55/55c65b1085d00e7f4761b53ca2b4d7a3702f3ead8b88540debb26b341d8e5ddb.png",
        "sha256": "55c65b1085d00e7f4761b53ca2b4d7a3702f3ead8b88540debb26b341d8e5ddb"
      },
      {
        "path": "/data2/k6tk/ee/ee9688e061109eb42118bc1ef5b574d0c6b3e3c7ac93510fadd813ea425e80eb.png",
        "sha256": "ee9688e061109eb42118bc1ef5b574d0c6b3e3c7ac93510fadd813ea425e80eb"
      },
      {
        "path": "/data2/k6tk/07/077ce579a222d2e8f1bcb9b43ce124b1dca34aff7c315488b0fceb2dcfc7137c.png",
        "sha256": "077ce579a222d2e8f1bcb9b43ce124b1dca34aff7c315488b0fceb2dcfc7137c"
      },
      {
        "path": "/data2/k6tk/01/01cee95eef9c16ce2a6364dc9c28d6a52853fac8805acb9993738d40cbac1132.png",
        "sha256": "01cee95eef9c16ce2a6364dc9c28d6a52853fac8805acb9993738d40cbac1132"
      },
      {
        "path": "/data2/k6tk/48/48f2c8c73e480def1f4515f1c2e35b5b763f740a6816b8c5c49e65aa9724e495.png",
        "sha256": "48f2c8c73e480def1f4515f1c2e35b5b763f740a6816b8c5c49e65aa9724e495"
      },
      {
        "path": "/data2/k6tk/eb/ebe6ba74d263392f63fc7258085b8ee6f1e86b890597a50a0e4e2284d7596199.png",
        "sha256": "ebe6ba74d263392f63fc7258085b8ee6f1e86b890597a50a0e4e2284d7596199"
      },
      {
        "path": "/data2/k6tk/a5/a5903d9cdc0cbabe5ff7b08663034d74dd777b18afeb82b9b2db752a02d8fa1b.png",
        "sha256": "a5903d9cdc0cbabe5ff7b08663034d74dd777b18afeb82b9b2db752a02d8fa1b"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From a position beside the blanket, face away from the chair. Is the piano to your left or right?",
    "timestamps": [
      0.0,
      4.791666666666667,
      9.583333333333334,
      14.416666666666666,
      19.208333333333332,
      24.041666666666668,
      28.833333333333332,
      33.666666666666664,
      38.458333333333336,
      43.291666666666664,
      48.083333333333336,
      52.875,
      57.708333333333336,
      62.5,
      67.33333333333333,
      72.125,
      76.95833333333333,
      81.75,
      86.58333333333333,
      91.375,
      96.20833333333333,
      101.0,
      105.79166666666667,
      110.625,
      115.41666666666667,
      120.25,
      125.04166666666667,
      129.875,
      134.66666666666666,
      139.5,
      144.29166666666666,
      149.125
    ],
    "total_num_frames": 3580
  },
  "target": "<think>\nStep 1: find the blanket, the chair and the piano.\nStep 2: I stand at the blanket facing the chair; I find the piano to my left.\nStep 3: I face away from the chair by making a half turn. Front and back swap, and left and right swap.\nSo I find the piano to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q438c872b185af383edda98ab",
  "paraphrase_template": "easy_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "3fbf8a0ffdecc2180ba4be701fd35a2275180d44151fdf73abdb3e3e1970c164"
  },
  "facing": "away",
  "candidate_id": "ground-5dcc4bc983c7ab279cbd710c822cb26e600194fa68b9b4cdf9ef49f7663affb0",
  "label_row_keys": [
    "q438c872b185af383edda98ab-p1"
  ]
}
```

## 15. q86a0887a3abba36512287bcc_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q86a0887a3abba36512287bcc",
      "source_store_i": 34005,
      "source_row_sha256": "83b3f636d67880bb9ac14fa38e642aa60592d57f8d52c3ad079c01addfdad4f9",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
      "clause_edit": {
        "start": 50,
        "end": 63,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q86a0887a3abba36512287bcc_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v321a7e1aa5eb",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      24,
      49,
      74,
      98,
      123,
      148,
      173,
      197,
      222,
      247,
      272,
      296,
      321,
      346,
      371,
      395,
      420,
      445,
      470,
      494,
      519,
      544,
      569,
      593,
      618,
      643,
      668,
      692,
      717,
      742,
      767
    ],
    "frames": [
      {
        "path": "/data2/k6tk/d6/d63fa84658cb78d8dae1422cba12d43ef0a66b4b57a2b783e947f9307cbd69c9.png",
        "sha256": "d63fa84658cb78d8dae1422cba12d43ef0a66b4b57a2b783e947f9307cbd69c9"
      },
      {
        "path": "/data2/k6tk/3d/3d4fa5bc380e53019b5454f72c324cc7950a30f7261378cf782f3674b0e83ad2.png",
        "sha256": "3d4fa5bc380e53019b5454f72c324cc7950a30f7261378cf782f3674b0e83ad2"
      },
      {
        "path": "/data2/k6tk/79/79e0aa30d442cd0f43517fb643f4cf5bfe0ba73f8b7efcf0da3594876d083c35.png",
        "sha256": "79e0aa30d442cd0f43517fb643f4cf5bfe0ba73f8b7efcf0da3594876d083c35"
      },
      {
        "path": "/data2/k6tk/51/51b7249fed6317091a0f3cb40bf7779a98c9e97a7a1781969f8314984da69070.png",
        "sha256": "51b7249fed6317091a0f3cb40bf7779a98c9e97a7a1781969f8314984da69070"
      },
      {
        "path": "/data2/k6tk/97/97f0108bb10caad6c797555e76f930fab2d2887d47cd3098990e7869072aecbc.png",
        "sha256": "97f0108bb10caad6c797555e76f930fab2d2887d47cd3098990e7869072aecbc"
      },
      {
        "path": "/data2/k6tk/75/75244d13d885b4e73f3208a8da5034755d99ba4c215258850a35aa44ccc1fbac.png",
        "sha256": "75244d13d885b4e73f3208a8da5034755d99ba4c215258850a35aa44ccc1fbac"
      },
      {
        "path": "/data2/k6tk/d5/d575ed99c48c7f7dc4e11ea231c9764bedddfa46a1373053b35641256fdcf78b.png",
        "sha256": "d575ed99c48c7f7dc4e11ea231c9764bedddfa46a1373053b35641256fdcf78b"
      },
      {
        "path": "/data2/k6tk/3b/3b4cadfb495394e83d8803e8cb299df07821df733a78d10411610b4b9359fb2b.png",
        "sha256": "3b4cadfb495394e83d8803e8cb299df07821df733a78d10411610b4b9359fb2b"
      },
      {
        "path": "/data2/k6tk/b1/b1442d42ab9b2f8e6e77943cca1f71d92ac5a69c50d856bf8051aec3cfb36bfe.png",
        "sha256": "b1442d42ab9b2f8e6e77943cca1f71d92ac5a69c50d856bf8051aec3cfb36bfe"
      },
      {
        "path": "/data2/k6tk/93/93c110920eb7c78ef8bf8f76561e6586396bcbc7afce5d9cd783b44eeef8cf92.png",
        "sha256": "93c110920eb7c78ef8bf8f76561e6586396bcbc7afce5d9cd783b44eeef8cf92"
      },
      {
        "path": "/data2/k6tk/2a/2a835e7c8fb89e0b6f508b4831584fb9e16c5d0f0bc0233f3eed5922fec39951.png",
        "sha256": "2a835e7c8fb89e0b6f508b4831584fb9e16c5d0f0bc0233f3eed5922fec39951"
      },
      {
        "path": "/data2/k6tk/35/353ee129d5daa4d627dc89ab209779d9829bc66fa99fc3923a134c4dbd781c20.png",
        "sha256": "353ee129d5daa4d627dc89ab209779d9829bc66fa99fc3923a134c4dbd781c20"
      },
      {
        "path": "/data2/k6tk/70/7078763af1c314ea1b388f1fd8eaf445103a4ddae2fb17820b46eaf5d1cd9b28.png",
        "sha256": "7078763af1c314ea1b388f1fd8eaf445103a4ddae2fb17820b46eaf5d1cd9b28"
      },
      {
        "path": "/data2/k6tk/75/7558deeb603f215fad76ec8eb7dc975199348e4ce114aafddc60054f7ea369c1.png",
        "sha256": "7558deeb603f215fad76ec8eb7dc975199348e4ce114aafddc60054f7ea369c1"
      },
      {
        "path": "/data2/k6tk/f6/f698bf71d5243d03e43c929103cd8b865e1b4c93b4a4101fde3f98c637794987.png",
        "sha256": "f698bf71d5243d03e43c929103cd8b865e1b4c93b4a4101fde3f98c637794987"
      },
      {
        "path": "/data2/k6tk/98/980984975c6dce6aa6845f978bb9c55da143a556d9bb3ae61f8a5395ea6995d9.png",
        "sha256": "980984975c6dce6aa6845f978bb9c55da143a556d9bb3ae61f8a5395ea6995d9"
      },
      {
        "path": "/data2/k6tk/da/da1ca2f358e880a3fa46743f6dec040be6c5ab5071e459b48f90b349e3e8cd0f.png",
        "sha256": "da1ca2f358e880a3fa46743f6dec040be6c5ab5071e459b48f90b349e3e8cd0f"
      },
      {
        "path": "/data2/k6tk/fc/fcf2f9d92c93ac0a3e2ade0a4b1baee0014be87082d39a13128b83eb6c39d2d3.png",
        "sha256": "fcf2f9d92c93ac0a3e2ade0a4b1baee0014be87082d39a13128b83eb6c39d2d3"
      },
      {
        "path": "/data2/k6tk/cb/cb04c7f986508fdc8457cd89fba6b833244d4fb536dc6ffb89b1d8cb02bd4b91.png",
        "sha256": "cb04c7f986508fdc8457cd89fba6b833244d4fb536dc6ffb89b1d8cb02bd4b91"
      },
      {
        "path": "/data2/k6tk/0d/0d190d43ce44bc77286540bd31f041af5abf391a29349eeccb858deedfd12c48.png",
        "sha256": "0d190d43ce44bc77286540bd31f041af5abf391a29349eeccb858deedfd12c48"
      },
      {
        "path": "/data2/k6tk/f4/f40a1660f4b345af024b4f37419a66e35f90e9ea74688bf38109f1287b909491.png",
        "sha256": "f40a1660f4b345af024b4f37419a66e35f90e9ea74688bf38109f1287b909491"
      },
      {
        "path": "/data2/k6tk/e3/e3b1bd0ef2f5f56207781c1f1bf34f1bf8d6553e43e1b90dc1344bb6757c245b.png",
        "sha256": "e3b1bd0ef2f5f56207781c1f1bf34f1bf8d6553e43e1b90dc1344bb6757c245b"
      },
      {
        "path": "/data2/k6tk/08/088105a59ab0ad6308a8bb69ee0bbc7a610f1d067030d0d2075d1e6375a044ab.png",
        "sha256": "088105a59ab0ad6308a8bb69ee0bbc7a610f1d067030d0d2075d1e6375a044ab"
      },
      {
        "path": "/data2/k6tk/59/59f2b09ee9ea6d89be6f936843324516e06a2cea224e848858a4f83461a06c7f.png",
        "sha256": "59f2b09ee9ea6d89be6f936843324516e06a2cea224e848858a4f83461a06c7f"
      },
      {
        "path": "/data2/k6tk/1f/1ff6ea91bc7dc0e3d71b82e82c214f5726fc49b757b16dc17ede30ecadaab9b7.png",
        "sha256": "1ff6ea91bc7dc0e3d71b82e82c214f5726fc49b757b16dc17ede30ecadaab9b7"
      },
      {
        "path": "/data2/k6tk/db/db2dccdc71de99c296830d7d10a5c3ca5ee222b55c21fcc3499dfb539f146945.png",
        "sha256": "db2dccdc71de99c296830d7d10a5c3ca5ee222b55c21fcc3499dfb539f146945"
      },
      {
        "path": "/data2/k6tk/08/089191c9a986e30c8a7c63395854dc520cede9a9319fcd24b0925ec5adf76754.png",
        "sha256": "089191c9a986e30c8a7c63395854dc520cede9a9319fcd24b0925ec5adf76754"
      },
      {
        "path": "/data2/k6tk/c3/c36bde76ea5c637dc9954568123fbcb2a4443c5cc6b2befee41956d24a1e1e15.png",
        "sha256": "c36bde76ea5c637dc9954568123fbcb2a4443c5cc6b2befee41956d24a1e1e15"
      },
      {
        "path": "/data2/k6tk/f4/f409902c9d3741c39be7a4456c546720d8541f4a274adce2a2c5c65f174bc996.png",
        "sha256": "f409902c9d3741c39be7a4456c546720d8541f4a274adce2a2c5c65f174bc996"
      },
      {
        "path": "/data2/k6tk/b9/b9211d16a385ef12555b11a7757f89ac87402e8ff8dbccd080da9d3b6cb2db58.png",
        "sha256": "b9211d16a385ef12555b11a7757f89ac87402e8ff8dbccd080da9d3b6cb2db58"
      },
      {
        "path": "/data2/k6tk/03/03c6569dd3063e687648d920e1f7317e135b587e53b6be3ce57a71f7733a245a.png",
        "sha256": "03c6569dd3063e687648d920e1f7317e135b587e53b6be3ce57a71f7733a245a"
      },
      {
        "path": "/data2/k6tk/95/953b31de155df8844edd22a1fa11a009e77f25b1e840686a8d6a2a84e68faa04.png",
        "sha256": "953b31de155df8844edd22a1fa11a009e77f25b1e840686a8d6a2a84e68faa04"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "From the perspective of standing at the table and facing away from the pillow, does the trash bin lie to its left or right?",
    "timestamps": [
      0.0,
      1.0,
      2.0416666666666665,
      3.0833333333333335,
      4.083333333333333,
      5.125,
      6.166666666666667,
      7.208333333333333,
      8.208333333333334,
      9.25,
      10.291666666666666,
      11.333333333333334,
      12.333333333333334,
      13.375,
      14.416666666666666,
      15.458333333333334,
      16.458333333333332,
      17.5,
      18.541666666666668,
      19.583333333333332,
      20.583333333333332,
      21.625,
      22.666666666666668,
      23.708333333333332,
      24.708333333333332,
      25.75,
      26.791666666666668,
      27.833333333333332,
      28.833333333333332,
      29.875,
      30.916666666666668,
      31.958333333333332
    ],
    "total_num_frames": 768
  },
  "target": "<think>\nStep 1: find the table, the pillow and the trash bin.\nStep 2: I stand at the table facing the pillow; I find the trash bin to my left.\nStep 3: I face away from the pillow by making a half turn. Front and back swap, and left and right swap.\nSo I find the trash bin to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "a9705f9b4d6333284d66fc6a81c9df6385bdcbb4bbb222fab061bca190fc115d"
  },
  "facing": "away",
  "candidate_id": "ground-b61be01a3d36d58d4705a81cb435f9087d5118624c8f252417c32e197e752622",
  "label_row_keys": [
    "q86a0887a3abba36512287bcc"
  ]
}
```

## 16. q735366a8ae3617595d7dd768_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q735366a8ae3617595d7dd768",
      "source_store_i": 20805,
      "source_row_sha256": "80043e0c93429aaee9e571df403a13593de6eab59ee118fd206dd2acc69c36ef",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "left",
      "mapped_label": "right",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q735366a8ae3617595d7dd768_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v043dc202ef94",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      1144,
      2288,
      3432,
      4577,
      5721,
      6865,
      8010,
      9154,
      10298,
      11442,
      12587,
      13731,
      14875,
      16020,
      17164,
      18308,
      19452,
      20597,
      21741,
      22885,
      24030,
      25174,
      26318,
      27462,
      28607,
      29751,
      30895,
      32040,
      33184,
      34328,
      35473
    ],
    "frames": [
      {
        "path": "/data2/k6tk/b9/b9e05616fb5467cc35ca0822f1704440c0bc2a859c58dc68d23d4e0a3bf38b91.png",
        "sha256": "b9e05616fb5467cc35ca0822f1704440c0bc2a859c58dc68d23d4e0a3bf38b91"
      },
      {
        "path": "/data2/k6tk/80/8093a7bfebe5fce20dbb5047512dad766442129bea5d9de27b4900289ccd2a6c.png",
        "sha256": "8093a7bfebe5fce20dbb5047512dad766442129bea5d9de27b4900289ccd2a6c"
      },
      {
        "path": "/data2/k6tk/f7/f78405ff577c4a175603758871709f050eaede927e4c1d55f4b5dc6d0181f12c.png",
        "sha256": "f78405ff577c4a175603758871709f050eaede927e4c1d55f4b5dc6d0181f12c"
      },
      {
        "path": "/data2/k6tk/41/417d033aac82f5d126c90b7a17e11d65d64188382c95ce2553ddbfc0d8ecc4d1.png",
        "sha256": "417d033aac82f5d126c90b7a17e11d65d64188382c95ce2553ddbfc0d8ecc4d1"
      },
      {
        "path": "/data2/k6tk/37/376aae476fd2071e46cf38d666bbef27cc58f4ad08eda0910aae7866a72e2f52.png",
        "sha256": "376aae476fd2071e46cf38d666bbef27cc58f4ad08eda0910aae7866a72e2f52"
      },
      {
        "path": "/data2/k6tk/b6/b6085f45ddc1e1e42f6b4f6ae9f504048e4af52ecc7338c753abc2160c4ab8b4.png",
        "sha256": "b6085f45ddc1e1e42f6b4f6ae9f504048e4af52ecc7338c753abc2160c4ab8b4"
      },
      {
        "path": "/data2/k6tk/12/1288c88025b5f94eb9d83dea15a33fdede8d42b2c465c311e49e862c9fc15a98.png",
        "sha256": "1288c88025b5f94eb9d83dea15a33fdede8d42b2c465c311e49e862c9fc15a98"
      },
      {
        "path": "/data2/k6tk/0f/0f8f810587ce7309e83ff2875142968a34cdb302be9aa6f6b5f5a2a067a40cd0.png",
        "sha256": "0f8f810587ce7309e83ff2875142968a34cdb302be9aa6f6b5f5a2a067a40cd0"
      },
      {
        "path": "/data2/k6tk/6d/6d2fc176d229cec3de8f811c74e3ce38cd7883c51bda9bde3041140d45d23120.png",
        "sha256": "6d2fc176d229cec3de8f811c74e3ce38cd7883c51bda9bde3041140d45d23120"
      },
      {
        "path": "/data2/k6tk/0c/0c8ddd0456d8d437002fc8a234b806f5f1c6a1cdfac00dc3627bb5bf773494f5.png",
        "sha256": "0c8ddd0456d8d437002fc8a234b806f5f1c6a1cdfac00dc3627bb5bf773494f5"
      },
      {
        "path": "/data2/k6tk/31/31007a9f82bdcfb1ac7951ac80c8e798c24a16518b5bee5f48e59e21eac25512.png",
        "sha256": "31007a9f82bdcfb1ac7951ac80c8e798c24a16518b5bee5f48e59e21eac25512"
      },
      {
        "path": "/data2/k6tk/6e/6e6b7fa885b1c759cbaa2299786ffe6da2d92cfb68ac554b2c1d981e76649a37.png",
        "sha256": "6e6b7fa885b1c759cbaa2299786ffe6da2d92cfb68ac554b2c1d981e76649a37"
      },
      {
        "path": "/data2/k6tk/d2/d27297c286abe0ed706dd68c79eba8118641444df563e5442a19b3ce7902c319.png",
        "sha256": "d27297c286abe0ed706dd68c79eba8118641444df563e5442a19b3ce7902c319"
      },
      {
        "path": "/data2/k6tk/a9/a9323f8bf4b360ad81c7e10f753b32fd0629644524fcdc909c34b20ee495febb.png",
        "sha256": "a9323f8bf4b360ad81c7e10f753b32fd0629644524fcdc909c34b20ee495febb"
      },
      {
        "path": "/data2/k6tk/0e/0e5cd86597722bab82630252b06a07dd363ae0952bfa685f20950164ae379752.png",
        "sha256": "0e5cd86597722bab82630252b06a07dd363ae0952bfa685f20950164ae379752"
      },
      {
        "path": "/data2/k6tk/cd/cdc01494d873a338d6fd30888579965feddaa17991e0c62951ae79fc47adb350.png",
        "sha256": "cdc01494d873a338d6fd30888579965feddaa17991e0c62951ae79fc47adb350"
      },
      {
        "path": "/data2/k6tk/43/43b4deca249c5f1762801de5bb709e0a3b7b383b6a4443adc99550317bc94aa0.png",
        "sha256": "43b4deca249c5f1762801de5bb709e0a3b7b383b6a4443adc99550317bc94aa0"
      },
      {
        "path": "/data2/k6tk/d2/d27bead4187e7668b26963a1a8e82ce048f621f2acec4c8f0515b9046aa29987.png",
        "sha256": "d27bead4187e7668b26963a1a8e82ce048f621f2acec4c8f0515b9046aa29987"
      },
      {
        "path": "/data2/k6tk/63/63c4e2cb27cfe2f26410a768c86844e78759b41a04f9ec478447202e9d883d85.png",
        "sha256": "63c4e2cb27cfe2f26410a768c86844e78759b41a04f9ec478447202e9d883d85"
      },
      {
        "path": "/data2/k6tk/ae/ae1924f306688f1c83f15701c0c7da3c4217373ea96d70b4628cce12274582a9.png",
        "sha256": "ae1924f306688f1c83f15701c0c7da3c4217373ea96d70b4628cce12274582a9"
      },
      {
        "path": "/data2/k6tk/82/828d00975e65c765c2e1cf24f6ff12a24c9df151de82ffd4b22b05e177f4b234.png",
        "sha256": "828d00975e65c765c2e1cf24f6ff12a24c9df151de82ffd4b22b05e177f4b234"
      },
      {
        "path": "/data2/k6tk/c1/c1bea5f0cc6cb9e514424801e472ed1033bad5e91a24c4e12cc07f31d9aba933.png",
        "sha256": "c1bea5f0cc6cb9e514424801e472ed1033bad5e91a24c4e12cc07f31d9aba933"
      },
      {
        "path": "/data2/k6tk/b9/b965c9e7930f3d90d04177a8220ed8c11cd00d61d6ef3266f1786423c7b7493b.png",
        "sha256": "b965c9e7930f3d90d04177a8220ed8c11cd00d61d6ef3266f1786423c7b7493b"
      },
      {
        "path": "/data2/k6tk/a0/a095b3ca7946a4e5dd08875f28459c716d8e16515460c1a54bd9375fca5f46aa.png",
        "sha256": "a095b3ca7946a4e5dd08875f28459c716d8e16515460c1a54bd9375fca5f46aa"
      },
      {
        "path": "/data2/k6tk/6f/6f00701bcb2bca70291abf8eec020ff3309d179c7970bf6b293422fc7a6db7a6.png",
        "sha256": "6f00701bcb2bca70291abf8eec020ff3309d179c7970bf6b293422fc7a6db7a6"
      },
      {
        "path": "/data2/k6tk/5c/5c7b8957edc219cf0701bad3754e3eb4e167e3cb472ade69ca2be6b470b7b4ec.png",
        "sha256": "5c7b8957edc219cf0701bad3754e3eb4e167e3cb472ade69ca2be6b470b7b4ec"
      },
      {
        "path": "/data2/k6tk/09/09d249b370178d13561fdbafe15bedcb5a541ff9e7a0494815d4fa9bd9aadd67.png",
        "sha256": "09d249b370178d13561fdbafe15bedcb5a541ff9e7a0494815d4fa9bd9aadd67"
      },
      {
        "path": "/data2/k6tk/ab/ab59d31d780d80c79c8bf914d0f57fb68ef88d5b9839519495bf2fcf33f3295d.png",
        "sha256": "ab59d31d780d80c79c8bf914d0f57fb68ef88d5b9839519495bf2fcf33f3295d"
      },
      {
        "path": "/data2/k6tk/4b/4b5da3885de71662721ea94dc1387a852c567ef2105618c8641a69a5ce3ce0d1.png",
        "sha256": "4b5da3885de71662721ea94dc1387a852c567ef2105618c8641a69a5ce3ce0d1"
      },
      {
        "path": "/data2/k6tk/2e/2e8ac1ce7e8c1e0b739b0f7e8cd85e2123ad8e4e2e1870759f30d123746b4c56.png",
        "sha256": "2e8ac1ce7e8c1e0b739b0f7e8cd85e2123ad8e4e2e1870759f30d123746b4c56"
      },
      {
        "path": "/data2/k6tk/68/68bdd988535160cccb91dc6763a23e4ab73caca7858c9ef43b648fccd32415de.png",
        "sha256": "68bdd988535160cccb91dc6763a23e4ab73caca7858c9ef43b648fccd32415de"
      },
      {
        "path": "/data2/k6tk/b3/b3222c7f2bf70b39f33ab66e90c8ef4c0ecb6c44a13a5d4dea15ea4821490555.png",
        "sha256": "b3222c7f2bf70b39f33ab66e90c8ef4c0ecb6c44a13a5d4dea15ea4821490555"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "Standing next to the monitor, and facing away from the bed, do you see the pan positioned to the left or to the right?",
    "timestamps": [
      0.0,
      19.066666666666666,
      38.13333333333333,
      57.2,
      76.28333333333333,
      95.35,
      114.41666666666667,
      133.5,
      152.56666666666666,
      171.63333333333333,
      190.7,
      209.78333333333333,
      228.85,
      247.91666666666666,
      267.0,
      286.06666666666666,
      305.1333333333333,
      324.2,
      343.28333333333336,
      362.35,
      381.4166666666667,
      400.5,
      419.56666666666666,
      438.6333333333333,
      457.7,
      476.78333333333336,
      495.85,
      514.9166666666666,
      534.0,
      553.0666666666667,
      572.1333333333333,
      591.2166666666667
    ],
    "total_num_frames": 35474
  },
  "target": "<think>\nStep 1: find the monitor, the bed and the pan.\nStep 2: facing the bed from the monitor, I find the pan to my left.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the pan to my right.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "f9a0e5685d1a9cbc90d502081fa26be769ed896a32be8b96e063207efe47d760"
  },
  "facing": "away",
  "candidate_id": "ground-103d14f5f5fded66cd8308f897e6e81bd5afa8d775018c06e8bbfc7101cfba32",
  "label_row_keys": [
    "q735366a8ae3617595d7dd768"
  ]
}
```

## 17. q2fcaa8fa0b10a16019ab8e05_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q2fcaa8fa0b10a16019ab8e05",
      "source_store_i": 23692,
      "source_row_sha256": "5c7f7c7e28234a7b4c65216063249ca1cfa7f50d050f936d0df7fb5d8aacfa81",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q2fcaa8fa0b10a16019ab8e05_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v97e765f11cd8",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      275,
      551,
      826,
      1102,
      1377,
      1653,
      1929,
      2204,
      2480,
      2755,
      3031,
      3306,
      3582,
      3858,
      4133,
      4409,
      4684,
      4960,
      5236,
      5511,
      5787,
      6062,
      6338,
      6613,
      6889,
      7165,
      7440,
      7716,
      7991,
      8267,
      8543
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f3/f34a06b0ce0893f79c43b4bfc844f9008bb94fa755322270ff298648eca160cc.png",
        "sha256": "f34a06b0ce0893f79c43b4bfc844f9008bb94fa755322270ff298648eca160cc"
      },
      {
        "path": "/data2/k6tk/9d/9d99d9b5b18fec61507903ba647b62fa7ada90ae8b85eaf8af7949b775e633c5.png",
        "sha256": "9d99d9b5b18fec61507903ba647b62fa7ada90ae8b85eaf8af7949b775e633c5"
      },
      {
        "path": "/data2/k6tk/52/520a0c81914c63b813dd52dee33006b5562bff62a1f7b7ea4d4335efb5f10cf0.png",
        "sha256": "520a0c81914c63b813dd52dee33006b5562bff62a1f7b7ea4d4335efb5f10cf0"
      },
      {
        "path": "/data2/k6tk/2b/2ba937f27e3af5fb47d4f02ddffe7e4602a0288c7a63be46ee1f8c0ba57d0f89.png",
        "sha256": "2ba937f27e3af5fb47d4f02ddffe7e4602a0288c7a63be46ee1f8c0ba57d0f89"
      },
      {
        "path": "/data2/k6tk/e0/e0499b7f3322d3060c8d7ca73ed8eb29efcb350e4277e88f1d611876900bd53b.png",
        "sha256": "e0499b7f3322d3060c8d7ca73ed8eb29efcb350e4277e88f1d611876900bd53b"
      },
      {
        "path": "/data2/k6tk/d4/d45e33ca99551cfa37b5120aff8824d9d6970c8b7eafaf6ee96afc2fee951c80.png",
        "sha256": "d45e33ca99551cfa37b5120aff8824d9d6970c8b7eafaf6ee96afc2fee951c80"
      },
      {
        "path": "/data2/k6tk/d4/d4413579206204a78ff07872a4918e76f25d037b4d681a9143bceac7fd4f36d5.png",
        "sha256": "d4413579206204a78ff07872a4918e76f25d037b4d681a9143bceac7fd4f36d5"
      },
      {
        "path": "/data2/k6tk/fe/fe3c9de01bbdd16d1b38a261d52e4ba3cee94cd24d610c8e8bef4678868aafcd.png",
        "sha256": "fe3c9de01bbdd16d1b38a261d52e4ba3cee94cd24d610c8e8bef4678868aafcd"
      },
      {
        "path": "/data2/k6tk/e3/e3a37190ee53051389458572cf2822f1629d740decc07c385a6f2ac01d0b6e0e.png",
        "sha256": "e3a37190ee53051389458572cf2822f1629d740decc07c385a6f2ac01d0b6e0e"
      },
      {
        "path": "/data2/k6tk/81/817506dd53dad8d66d507fef870b3e3fb1d4cb7082c8c1416278897c2fcf6ff4.png",
        "sha256": "817506dd53dad8d66d507fef870b3e3fb1d4cb7082c8c1416278897c2fcf6ff4"
      },
      {
        "path": "/data2/k6tk/54/54bb748bd5436f81444e499f36de1d1514529bb0f631505608d81ba14e6ed17c.png",
        "sha256": "54bb748bd5436f81444e499f36de1d1514529bb0f631505608d81ba14e6ed17c"
      },
      {
        "path": "/data2/k6tk/98/984434f6cc5ddce57e4c77f99f50e082278f1e61279256950688b6faa667f75b.png",
        "sha256": "984434f6cc5ddce57e4c77f99f50e082278f1e61279256950688b6faa667f75b"
      },
      {
        "path": "/data2/k6tk/2c/2ce7ada555d1162c96cfa4cb7a6a1a31f053a6e89819d5ac5d17a140bfd1be00.png",
        "sha256": "2ce7ada555d1162c96cfa4cb7a6a1a31f053a6e89819d5ac5d17a140bfd1be00"
      },
      {
        "path": "/data2/k6tk/fa/fae642222cd6690b94fd85353992243f7540fd9255047a272d1b561d30faa77b.png",
        "sha256": "fae642222cd6690b94fd85353992243f7540fd9255047a272d1b561d30faa77b"
      },
      {
        "path": "/data2/k6tk/e0/e03acba8a1cf7053bc69ff0c18a3d4071691daf621e792b0a718a831ff6e42e7.png",
        "sha256": "e03acba8a1cf7053bc69ff0c18a3d4071691daf621e792b0a718a831ff6e42e7"
      },
      {
        "path": "/data2/k6tk/0a/0ac030601bacbcc8d8bb69569caaca70a802b487f2b30f2bc77f3fd96d5fb208.png",
        "sha256": "0ac030601bacbcc8d8bb69569caaca70a802b487f2b30f2bc77f3fd96d5fb208"
      },
      {
        "path": "/data2/k6tk/fa/fa504004d766cf247f65791d69cbc66dc293f3ace01da5b7a47f6c1e2949cd89.png",
        "sha256": "fa504004d766cf247f65791d69cbc66dc293f3ace01da5b7a47f6c1e2949cd89"
      },
      {
        "path": "/data2/k6tk/ba/baf5080b3dfeee744d52eda39e7f8fdfe20ca7ba46e18c39bb504651d3b5e374.png",
        "sha256": "baf5080b3dfeee744d52eda39e7f8fdfe20ca7ba46e18c39bb504651d3b5e374"
      },
      {
        "path": "/data2/k6tk/e1/e170b6ec137d74c726052d5924d58a1303f29c80a76959adf6ecfcb88ab5f0b7.png",
        "sha256": "e170b6ec137d74c726052d5924d58a1303f29c80a76959adf6ecfcb88ab5f0b7"
      },
      {
        "path": "/data2/k6tk/b5/b5b79e765fb16dd403afdefd14546ed1a055ea93f046956836115e8c07570761.png",
        "sha256": "b5b79e765fb16dd403afdefd14546ed1a055ea93f046956836115e8c07570761"
      },
      {
        "path": "/data2/k6tk/98/98b074037dda3237eb537c49622639f27b948c23720f84d2831a32a00dfc702e.png",
        "sha256": "98b074037dda3237eb537c49622639f27b948c23720f84d2831a32a00dfc702e"
      },
      {
        "path": "/data2/k6tk/d0/d013c329ac56ab3e6ed7eab69d166236d2a122b0fed14777b1096fd6d39c22da.png",
        "sha256": "d013c329ac56ab3e6ed7eab69d166236d2a122b0fed14777b1096fd6d39c22da"
      },
      {
        "path": "/data2/k6tk/e7/e739f7422e66047bd3f24a65722f754f10cc62651a9da85ec5ab5e07ec970e4f.png",
        "sha256": "e739f7422e66047bd3f24a65722f754f10cc62651a9da85ec5ab5e07ec970e4f"
      },
      {
        "path": "/data2/k6tk/9f/9f935b82dc2fc71385cfc22e3c5a915a4458bed00bf9c41910145ed1f48b3034.png",
        "sha256": "9f935b82dc2fc71385cfc22e3c5a915a4458bed00bf9c41910145ed1f48b3034"
      },
      {
        "path": "/data2/k6tk/49/490d253bb45d9098ba380c0d306fdcfba15b01898c30730683a097baf2386aef.png",
        "sha256": "490d253bb45d9098ba380c0d306fdcfba15b01898c30730683a097baf2386aef"
      },
      {
        "path": "/data2/k6tk/2f/2f1065bb39a6f9c73e8e4c46a2986b9bf7b7f8b647ea6bb98d5b66060658a5b4.png",
        "sha256": "2f1065bb39a6f9c73e8e4c46a2986b9bf7b7f8b647ea6bb98d5b66060658a5b4"
      },
      {
        "path": "/data2/k6tk/e2/e29e274b819b3dc9fc7a0bb31dd8d7964330a56945f3d4085d5ba2a8dccf0b79.png",
        "sha256": "e29e274b819b3dc9fc7a0bb31dd8d7964330a56945f3d4085d5ba2a8dccf0b79"
      },
      {
        "path": "/data2/k6tk/26/268c2df8199c82f1952992a1d2b95992a3c8011c71fdda2d96a98df7ba0da852.png",
        "sha256": "268c2df8199c82f1952992a1d2b95992a3c8011c71fdda2d96a98df7ba0da852"
      },
      {
        "path": "/data2/k6tk/8c/8cc701b538afd83b91a89479b3903e324409a5acc6b57834603ed62e86efa30d.png",
        "sha256": "8cc701b538afd83b91a89479b3903e324409a5acc6b57834603ed62e86efa30d"
      },
      {
        "path": "/data2/k6tk/82/820c8462cdb2e5f151339ded6e64543b9260d843575ae6c59241fcbdb18d147d.png",
        "sha256": "820c8462cdb2e5f151339ded6e64543b9260d843575ae6c59241fcbdb18d147d"
      },
      {
        "path": "/data2/k6tk/b5/b520edd5d8bb84e35085e1dc650bff08ee7bc4ab70359de62625a1f32d72fe39.png",
        "sha256": "b520edd5d8bb84e35085e1dc650bff08ee7bc4ab70359de62625a1f32d72fe39"
      },
      {
        "path": "/data2/k6tk/da/daab0c3984b9c22061a74bca8f14b606b6e5e682b57414777e736c0db5d8a13c.png",
        "sha256": "daab0c3984b9c22061a74bca8f14b606b6e5e682b57414777e736c0db5d8a13c"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the audio amplifier and facing away from the backsplash, is the books to the left or the right of the backsplash?",
    "timestamps": [
      0.0,
      4.583333333333333,
      9.183333333333334,
      13.766666666666667,
      18.366666666666667,
      22.95,
      27.55,
      32.15,
      36.733333333333334,
      41.333333333333336,
      45.916666666666664,
      50.516666666666666,
      55.1,
      59.7,
      64.3,
      68.88333333333334,
      73.48333333333333,
      78.06666666666666,
      82.66666666666667,
      87.26666666666667,
      91.85,
      96.45,
      101.03333333333333,
      105.63333333333334,
      110.21666666666667,
      114.81666666666666,
      119.41666666666667,
      124.0,
      128.6,
      133.18333333333334,
      137.78333333333333,
      142.38333333333333
    ],
    "total_num_frames": 8544
  },
  "target": "<think>\nStep 1: find the audio amplifier, the backsplash and the books.\nStep 2: I find the books to my left when I stand at the audio amplifier facing the backsplash.\nStep 3: I face away from the backsplash by making a half turn. Front and back swap, and left and right swap.\nSo I find the books to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "62c9f1afc2592d031d4da9a6c704bb0c79c75df36ff0d0cb7e61d52d802bfdd5"
  },
  "facing": "away",
  "candidate_id": "ground-6e2eea82779a49e5b131ceb75ad38ad2fa249c16b334dc1c001712799c0cca2f",
  "label_row_keys": [
    "q2fcaa8fa0b10a16019ab8e05"
  ]
}
```

## 18. q33b527b2062b79a246d89d90_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q33b527b2062b79a246d89d90",
      "source_store_i": 142702,
      "source_row_sha256": "1363f5d97234df47b709c731e59bc16bf6f8d1de908b0a9dee3c3ac42a7353a0",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "left",
      "mapped_label": "right",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q33b527b2062b79a246d89d90_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v2d9dae068351",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      338,
      676,
      1014,
      1353,
      1691,
      2029,
      2367,
      2706,
      3044,
      3382,
      3720,
      4059,
      4397,
      4735,
      5073,
      5412,
      5750,
      6088,
      6426,
      6765,
      7103,
      7441,
      7779,
      8118,
      8456,
      8794,
      9132,
      9471,
      9809,
      10147,
      10486
    ],
    "frames": [
      {
        "path": "/data2/k6tk/4e/4e23deb0442ad93a2c97a04c239c3aa816032b5bdbace73e1d0afb0772a312d8.png",
        "sha256": "4e23deb0442ad93a2c97a04c239c3aa816032b5bdbace73e1d0afb0772a312d8"
      },
      {
        "path": "/data2/k6tk/72/720a2c6d2abe7c12eede16bb9da449691c486918f087f19524158440ee5922db.png",
        "sha256": "720a2c6d2abe7c12eede16bb9da449691c486918f087f19524158440ee5922db"
      },
      {
        "path": "/data2/k6tk/03/03a53228c33f74c9e94514b1dbfc375d65e6337da3164dc6fa18b93da6cdc7b3.png",
        "sha256": "03a53228c33f74c9e94514b1dbfc375d65e6337da3164dc6fa18b93da6cdc7b3"
      },
      {
        "path": "/data2/k6tk/39/39bb881921c7c762b854a43e606127c77c9e078f6cdbfa7b22e02416dca68b80.png",
        "sha256": "39bb881921c7c762b854a43e606127c77c9e078f6cdbfa7b22e02416dca68b80"
      },
      {
        "path": "/data2/k6tk/c9/c9557b85efeb9027e446ea33abb25de46887b34e5e26e7d4bf5d50d77800eecd.png",
        "sha256": "c9557b85efeb9027e446ea33abb25de46887b34e5e26e7d4bf5d50d77800eecd"
      },
      {
        "path": "/data2/k6tk/35/3577e4f261a6009233b33854a84bae465c5cdb2eab16eb3ea1549c0419efd2fd.png",
        "sha256": "3577e4f261a6009233b33854a84bae465c5cdb2eab16eb3ea1549c0419efd2fd"
      },
      {
        "path": "/data2/k6tk/fa/faa04b13dddb36f2721a0d02d27c8d26a1317c530f28ae0df4aac626c3b009b8.png",
        "sha256": "faa04b13dddb36f2721a0d02d27c8d26a1317c530f28ae0df4aac626c3b009b8"
      },
      {
        "path": "/data2/k6tk/79/79ae42e89a02bb173eaad175d91c0cb2b9596103ecb186c44ad8e45211d64944.png",
        "sha256": "79ae42e89a02bb173eaad175d91c0cb2b9596103ecb186c44ad8e45211d64944"
      },
      {
        "path": "/data2/k6tk/3a/3ace117a87ccbb755fce8a41b86cff77e4e787db55713b05dfe49e56d22353c1.png",
        "sha256": "3ace117a87ccbb755fce8a41b86cff77e4e787db55713b05dfe49e56d22353c1"
      },
      {
        "path": "/data2/k6tk/74/7499d69711028b928597d733bc81e0f206d7d2ad94e7c76463359b46e3375fea.png",
        "sha256": "7499d69711028b928597d733bc81e0f206d7d2ad94e7c76463359b46e3375fea"
      },
      {
        "path": "/data2/k6tk/d3/d3da51623ee26dbad63a0251aa3a697887f32b5441d1d762b8542a25539889a8.png",
        "sha256": "d3da51623ee26dbad63a0251aa3a697887f32b5441d1d762b8542a25539889a8"
      },
      {
        "path": "/data2/k6tk/fd/fd27db494966d2d50e878b2daa9eca5325c5aac94c69151d9853bcd8e28785eb.png",
        "sha256": "fd27db494966d2d50e878b2daa9eca5325c5aac94c69151d9853bcd8e28785eb"
      },
      {
        "path": "/data2/k6tk/0a/0a43466ab9a6fba2e96170ce2cd4346ea681d5f05e66878f4086f1ff7457f837.png",
        "sha256": "0a43466ab9a6fba2e96170ce2cd4346ea681d5f05e66878f4086f1ff7457f837"
      },
      {
        "path": "/data2/k6tk/e8/e82e4cfff461ad8f80d335fb77d30ec5bc5dff4f9ccebd17ee6c9035f1a7177b.png",
        "sha256": "e82e4cfff461ad8f80d335fb77d30ec5bc5dff4f9ccebd17ee6c9035f1a7177b"
      },
      {
        "path": "/data2/k6tk/70/70090293f73c7321b6c91708a93131587b64728b0a2f9ab595d62b60dd7b87f3.png",
        "sha256": "70090293f73c7321b6c91708a93131587b64728b0a2f9ab595d62b60dd7b87f3"
      },
      {
        "path": "/data2/k6tk/74/7497e0662c59d08d93bc3ad1f65635f08188f2187c83b1a059811be3baede974.png",
        "sha256": "7497e0662c59d08d93bc3ad1f65635f08188f2187c83b1a059811be3baede974"
      },
      {
        "path": "/data2/k6tk/41/41daa38313097c9a46b63459aff24dbba867c6cb0a0415c287cdc9ee43a2e959.png",
        "sha256": "41daa38313097c9a46b63459aff24dbba867c6cb0a0415c287cdc9ee43a2e959"
      },
      {
        "path": "/data2/k6tk/e7/e790743ea0cbbd375e7001db02bb6848dfe74aec790924fae7e385ad39b8e31e.png",
        "sha256": "e790743ea0cbbd375e7001db02bb6848dfe74aec790924fae7e385ad39b8e31e"
      },
      {
        "path": "/data2/k6tk/af/af544e5386a1ed2b46a409ea187f72bd844162f1e864d61a9718e07c85e50685.png",
        "sha256": "af544e5386a1ed2b46a409ea187f72bd844162f1e864d61a9718e07c85e50685"
      },
      {
        "path": "/data2/k6tk/76/76eaf79d5c34967dc2d02dcf28f37b1447dfb7ced5214bff46f538dfa9786cff.png",
        "sha256": "76eaf79d5c34967dc2d02dcf28f37b1447dfb7ced5214bff46f538dfa9786cff"
      },
      {
        "path": "/data2/k6tk/df/dfb6de86e190717308b933f7160dba8568bc1d1ac56d752ee2212597c4ce2b1c.png",
        "sha256": "dfb6de86e190717308b933f7160dba8568bc1d1ac56d752ee2212597c4ce2b1c"
      },
      {
        "path": "/data2/k6tk/70/70d5c27408a8c3323f34b4b3c525894c831cc40ea2edc0455f125e21c2da39f5.png",
        "sha256": "70d5c27408a8c3323f34b4b3c525894c831cc40ea2edc0455f125e21c2da39f5"
      },
      {
        "path": "/data2/k6tk/22/222541c814b6f8b96a7178881f64129f5e71c8df4b55ea2e6b45d93eaa93d817.png",
        "sha256": "222541c814b6f8b96a7178881f64129f5e71c8df4b55ea2e6b45d93eaa93d817"
      },
      {
        "path": "/data2/k6tk/28/289026ac97379104f10878dd491f7d2e66bec4d6be9fa576d723e98d855e7654.png",
        "sha256": "289026ac97379104f10878dd491f7d2e66bec4d6be9fa576d723e98d855e7654"
      },
      {
        "path": "/data2/k6tk/e1/e16cd6e25fc6ea7b221a6d162855952b47f8fb725a6327889dc98c27ac0c7f94.png",
        "sha256": "e16cd6e25fc6ea7b221a6d162855952b47f8fb725a6327889dc98c27ac0c7f94"
      },
      {
        "path": "/data2/k6tk/6e/6ee2276fbcdce6993ebd8dfce3015ffc5d7ba75c4f3ae11b5b008b21bad97c53.png",
        "sha256": "6ee2276fbcdce6993ebd8dfce3015ffc5d7ba75c4f3ae11b5b008b21bad97c53"
      },
      {
        "path": "/data2/k6tk/2f/2fa8e670a0796e88a0a6e0d4e0174cb69c421235689358dc231d52395eee4a5b.png",
        "sha256": "2fa8e670a0796e88a0a6e0d4e0174cb69c421235689358dc231d52395eee4a5b"
      },
      {
        "path": "/data2/k6tk/ce/ce7283c6e07943c63ad4ce0fda4f9f7773127e241931a68002acbaba908e0f68.png",
        "sha256": "ce7283c6e07943c63ad4ce0fda4f9f7773127e241931a68002acbaba908e0f68"
      },
      {
        "path": "/data2/k6tk/72/7266731a6b7f08aaa672a8f0a49f07c348341a20d283faadca5bbcb3a09edc89.png",
        "sha256": "7266731a6b7f08aaa672a8f0a49f07c348341a20d283faadca5bbcb3a09edc89"
      },
      {
        "path": "/data2/k6tk/64/643f18d8e3d2148138157ef780378735302c650a14fe426fcea60b263154db25.png",
        "sha256": "643f18d8e3d2148138157ef780378735302c650a14fe426fcea60b263154db25"
      },
      {
        "path": "/data2/k6tk/4d/4d7e17fc510b09665783ece2ea730ccd426530b903f45cdc15755378f3721afd.png",
        "sha256": "4d7e17fc510b09665783ece2ea730ccd426530b903f45cdc15755378f3721afd"
      },
      {
        "path": "/data2/k6tk/34/349f774d5cd3c234569abbd56455a897513ebdb6be8969ac167fb0f7ee7b81d8.png",
        "sha256": "349f774d5cd3c234569abbd56455a897513ebdb6be8969ac167fb0f7ee7b81d8"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "While standing at the laptop and facing away from the telephone, which side of the telephone is the coat hanger on—left or right?",
    "timestamps": [
      0.0,
      5.633333333333334,
      11.266666666666667,
      16.9,
      22.55,
      28.183333333333334,
      33.81666666666667,
      39.45,
      45.1,
      50.733333333333334,
      56.36666666666667,
      62.0,
      67.65,
      73.28333333333333,
      78.91666666666667,
      84.55,
      90.2,
      95.83333333333333,
      101.46666666666667,
      107.1,
      112.75,
      118.38333333333334,
      124.01666666666667,
      129.65,
      135.3,
      140.93333333333334,
      146.56666666666666,
      152.2,
      157.85,
      163.48333333333332,
      169.11666666666667,
      174.76666666666668
    ],
    "total_num_frames": 10487
  },
  "target": "<think>\nStep 1: find the laptop, the telephone and the coat hanger.\nStep 2: standing at the laptop and facing the telephone, I find the coat hanger to my left.\nStep 3: I face away from the telephone by making a half turn. Front and back swap, and left and right swap.\nSo I find the coat hanger to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "c41608903b0f33e7c8b96737e6b7eea58f59a2b2859ebbcdff7d20c3eea7b995"
  },
  "facing": "away",
  "candidate_id": "ground-81245f3aaeab8d942e754e92271c79132092fb90f428f8783df32f474b137899",
  "label_row_keys": [
    "q33b527b2062b79a246d89d90"
  ]
}
```

## 19. q80208a474c312df3ca0b9065_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q80208a474c312df3ca0b9065",
      "source_store_i": 18794,
      "source_row_sha256": "956038f00b96ae7cddb0105342c7f5729d7e618089f80587f877d0242bae2b77",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q80208a474c312df3ca0b9065_sb_rowD7_a",
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
    "question": "If I am standing by the air purifier and facing away from the clock, is the trash bin to the left or the right of the clock?",
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
  "target": "<think>\nStep 1: find the air purifier, the clock and the trash bin.\nStep 2: I find the trash bin to my left when I stand at the air purifier facing the clock.\nStep 3: I face away from the clock by making a half turn. Front and back swap, and left and right swap.\nSo I find the trash bin to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "6e2d879c082f9890f51a57a863a548c03d928db74ddf80d249eeae4c7b05916c"
  },
  "facing": "away",
  "candidate_id": "ground-bfb719bbb5bb39d434d312b6ff395844cbfe0486b9975b79a907aa12d0175e9a",
  "label_row_keys": [
    "q80208a474c312df3ca0b9065"
  ]
}
```

## 20. qc9f6790d2c6580cc2e70b5e8_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_easy.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qc9f6790d2c6580cc2e70b5e8",
      "source_store_i": 7470,
      "source_row_sha256": "443282638e1c315ad0f9330f1be3ce4eb4f964aebb8fad2b32e903c3c0ab8eca",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qc9f6790d2c6580cc2e70b5e8_sb_rowD7_a",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v3bbe3b6c0254",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      454,
      909,
      1364,
      1819,
      2274,
      2728,
      3183,
      3638,
      4093,
      4548,
      5002,
      5457,
      5912,
      6367,
      6822,
      7276,
      7731,
      8186,
      8641,
      9096,
      9550,
      10005,
      10460,
      10915,
      11370,
      11824,
      12279,
      12734,
      13189,
      13644,
      14099
    ],
    "frames": [
      {
        "path": "/data2/k6tk/7e/7e6ed77c2f1dc8df3dee1469c48d3c772e917beb6a077896f2f941c8f0d2dd5d.png",
        "sha256": "7e6ed77c2f1dc8df3dee1469c48d3c772e917beb6a077896f2f941c8f0d2dd5d"
      },
      {
        "path": "/data2/k6tk/a7/a748a09c921f20a9a6e95e4d4a505686117283eb972e592ae3cadeeba7cdb020.png",
        "sha256": "a748a09c921f20a9a6e95e4d4a505686117283eb972e592ae3cadeeba7cdb020"
      },
      {
        "path": "/data2/k6tk/67/67e6dde2aa3db021291e9af8b981dafd1c19879c9f6a94ec6174d4c0aca79427.png",
        "sha256": "67e6dde2aa3db021291e9af8b981dafd1c19879c9f6a94ec6174d4c0aca79427"
      },
      {
        "path": "/data2/k6tk/81/8123540af0b40b8c63c3ed7f0404d43a1603dac5aba38d987f3de0ee36d95abe.png",
        "sha256": "8123540af0b40b8c63c3ed7f0404d43a1603dac5aba38d987f3de0ee36d95abe"
      },
      {
        "path": "/data2/k6tk/b7/b7d140d9811e4390b71c16f8e3a22a5f602c9922368687ee1a971029c3cdc935.png",
        "sha256": "b7d140d9811e4390b71c16f8e3a22a5f602c9922368687ee1a971029c3cdc935"
      },
      {
        "path": "/data2/k6tk/41/4104506d2c41897f53037674ef35a8c9c327aff37ec3b7fad05f309e603532fc.png",
        "sha256": "4104506d2c41897f53037674ef35a8c9c327aff37ec3b7fad05f309e603532fc"
      },
      {
        "path": "/data2/k6tk/da/dae1a079b84723efeb635076e75fa755ce49d93d54fae95e95439e17df604137.png",
        "sha256": "dae1a079b84723efeb635076e75fa755ce49d93d54fae95e95439e17df604137"
      },
      {
        "path": "/data2/k6tk/bb/bbc4ff15e7a45d989cc067dd9cdcdf209de00ddc33c95164ca13ad54fcc8b42a.png",
        "sha256": "bbc4ff15e7a45d989cc067dd9cdcdf209de00ddc33c95164ca13ad54fcc8b42a"
      },
      {
        "path": "/data2/k6tk/d3/d3718f00ca413110716798288840b7447080e6097e7ebe2b86e26553a9a80c26.png",
        "sha256": "d3718f00ca413110716798288840b7447080e6097e7ebe2b86e26553a9a80c26"
      },
      {
        "path": "/data2/k6tk/75/75c977eb818caca48e6b203a8ecf6eb064a8bf9beebc7f13f065906314acfa74.png",
        "sha256": "75c977eb818caca48e6b203a8ecf6eb064a8bf9beebc7f13f065906314acfa74"
      },
      {
        "path": "/data2/k6tk/0f/0fdf0f90a5931be4a421ee0fa0d82c0ffd3d7c54725d0b927b72e0c322b54826.png",
        "sha256": "0fdf0f90a5931be4a421ee0fa0d82c0ffd3d7c54725d0b927b72e0c322b54826"
      },
      {
        "path": "/data2/k6tk/ad/ad97e2808a1756d34fc27347dc101b76a71f08fc0b2bbbff25a2ed6c66becb5f.png",
        "sha256": "ad97e2808a1756d34fc27347dc101b76a71f08fc0b2bbbff25a2ed6c66becb5f"
      },
      {
        "path": "/data2/k6tk/50/50a2fdf99b7cafa4c9d0fab0b71f1ff5a33c96673237db0f31a58dbbcdd1434b.png",
        "sha256": "50a2fdf99b7cafa4c9d0fab0b71f1ff5a33c96673237db0f31a58dbbcdd1434b"
      },
      {
        "path": "/data2/k6tk/3c/3cf1361119c44eb133d7c695cc2ebb1a5c92a0af19ffe719848c803153736aaf.png",
        "sha256": "3cf1361119c44eb133d7c695cc2ebb1a5c92a0af19ffe719848c803153736aaf"
      },
      {
        "path": "/data2/k6tk/fc/fcc5a6ddafc0ea62787b8cdae9b00a961101e09d17e07982e3091c84c7acbdf4.png",
        "sha256": "fcc5a6ddafc0ea62787b8cdae9b00a961101e09d17e07982e3091c84c7acbdf4"
      },
      {
        "path": "/data2/k6tk/1c/1c78a46a3e610747089581ae71f60c5ba5daf5914fdd713b2542cd67c773596e.png",
        "sha256": "1c78a46a3e610747089581ae71f60c5ba5daf5914fdd713b2542cd67c773596e"
      },
      {
        "path": "/data2/k6tk/be/bef9a35895ed55b213f3176630241c5483f81929911423d6f3fea4b009cb4daa.png",
        "sha256": "bef9a35895ed55b213f3176630241c5483f81929911423d6f3fea4b009cb4daa"
      },
      {
        "path": "/data2/k6tk/45/4526f520964a136bba81d4bb4e9f4df8ddf572269d53688649c397481082b7c1.png",
        "sha256": "4526f520964a136bba81d4bb4e9f4df8ddf572269d53688649c397481082b7c1"
      },
      {
        "path": "/data2/k6tk/c6/c6294fb9571bbb80c22714980132e1d27d862417f382277a3b3bba109a1c9d9b.png",
        "sha256": "c6294fb9571bbb80c22714980132e1d27d862417f382277a3b3bba109a1c9d9b"
      },
      {
        "path": "/data2/k6tk/4d/4deee64750c66646844a5ea871082db7c5f2bf336d29c4b1b39c31b13a53e8e2.png",
        "sha256": "4deee64750c66646844a5ea871082db7c5f2bf336d29c4b1b39c31b13a53e8e2"
      },
      {
        "path": "/data2/k6tk/b0/b05bf5e48162a6fd9dfe0a693f3c11e1efc6da232c2f5b1848ee2a8689135828.png",
        "sha256": "b05bf5e48162a6fd9dfe0a693f3c11e1efc6da232c2f5b1848ee2a8689135828"
      },
      {
        "path": "/data2/k6tk/b2/b20d24b6de95520be5fb7603712809f4a4a623a761fcf17904a9104e8435b2b6.png",
        "sha256": "b20d24b6de95520be5fb7603712809f4a4a623a761fcf17904a9104e8435b2b6"
      },
      {
        "path": "/data2/k6tk/8e/8e4eac0be2fdcdf3b16b3dfc63b366a0ac46467ae0c40bd12c0ad6c1960fdc9e.png",
        "sha256": "8e4eac0be2fdcdf3b16b3dfc63b366a0ac46467ae0c40bd12c0ad6c1960fdc9e"
      },
      {
        "path": "/data2/k6tk/bc/bcc69a4bfd462cbcd41b6091f68c0bf37863fed231d83ab5facf12ea7d60b58f.png",
        "sha256": "bcc69a4bfd462cbcd41b6091f68c0bf37863fed231d83ab5facf12ea7d60b58f"
      },
      {
        "path": "/data2/k6tk/df/df984a82850a03dbd6f9d81a43211893532b892e03c1986f58c1542847877672.png",
        "sha256": "df984a82850a03dbd6f9d81a43211893532b892e03c1986f58c1542847877672"
      },
      {
        "path": "/data2/k6tk/6c/6c07e41f6bb3276eacba7d250005556acc5b5611abbe6aeb537097e3aec34839.png",
        "sha256": "6c07e41f6bb3276eacba7d250005556acc5b5611abbe6aeb537097e3aec34839"
      },
      {
        "path": "/data2/k6tk/8a/8a9ebb984690e5d6db404cebcb01967e86dd4176815dc7a9de7804063f9152b0.png",
        "sha256": "8a9ebb984690e5d6db404cebcb01967e86dd4176815dc7a9de7804063f9152b0"
      },
      {
        "path": "/data2/k6tk/9a/9ab8db7f073b84871e4797d140d895b0e75554b56bf2180b3fc3654595488d3e.png",
        "sha256": "9ab8db7f073b84871e4797d140d895b0e75554b56bf2180b3fc3654595488d3e"
      },
      {
        "path": "/data2/k6tk/29/2980601317cf6d6983038cd0a12e0fc866218b8e38b6212016febef5f8cf2253.png",
        "sha256": "2980601317cf6d6983038cd0a12e0fc866218b8e38b6212016febef5f8cf2253"
      },
      {
        "path": "/data2/k6tk/35/35d8c8875ad772f72b2e3d2edc553b204add8f59df1d432a3f6b70f6f665b328.png",
        "sha256": "35d8c8875ad772f72b2e3d2edc553b204add8f59df1d432a3f6b70f6f665b328"
      },
      {
        "path": "/data2/k6tk/8f/8fc5b1d58496d9dcd7e3a85597724b8ba171f4f746f72b2b6bab1012c2376260.png",
        "sha256": "8fc5b1d58496d9dcd7e3a85597724b8ba171f4f746f72b2b6bab1012c2376260"
      },
      {
        "path": "/data2/k6tk/72/724306b409520e5b8a3c7e9fc7b427e68df0ed32cd23da7dc426d95886edf9cf.png",
        "sha256": "724306b409520e5b8a3c7e9fc7b427e68df0ed32cd23da7dc426d95886edf9cf"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the bag and facing away from the bean bag, is the whiteboard to the left or the right of the bean bag?",
    "timestamps": [
      0.0,
      7.566666666666666,
      15.15,
      22.733333333333334,
      30.316666666666666,
      37.9,
      45.46666666666667,
      53.05,
      60.63333333333333,
      68.21666666666667,
      75.8,
      83.36666666666666,
      90.95,
      98.53333333333333,
      106.11666666666666,
      113.7,
      121.26666666666667,
      128.85,
      136.43333333333334,
      144.01666666666668,
      151.6,
      159.16666666666666,
      166.75,
      174.33333333333334,
      181.91666666666666,
      189.5,
      197.06666666666666,
      204.65,
      212.23333333333332,
      219.81666666666666,
      227.4,
      234.98333333333332
    ],
    "total_num_frames": 14100
  },
  "target": "<think>\nStep 1: find the bag, the bean bag and the whiteboard.\nStep 2: I find the whiteboard to my left when I stand at the bag facing the bean bag.\nStep 3: I face away from the bean bag by making a half turn. Front and back swap, and left and right swap.\nSo I find the whiteboard to my right.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "7dd61320fa8d9514384efc860f91d8a1bb1f079f3350616cdb909c29a026c4aa"
  },
  "facing": "away",
  "candidate_id": "ground-a55310cc1545489434bba19fe5a7c88b533f82021a589fca52819da176e959f9",
  "label_row_keys": [
    "qc9f6790d2c6580cc2e70b5e8"
  ]
}
```

## 21. q3fcf231b8767fae3a3079ba7-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q3fcf231b8767fae3a3079ba7-p1",
      "source_store_i": 72945,
      "source_row_sha256": "dce9c8e6b47dc16d2da75cc274a58dfc0738e541352d2d9f18c98d9edcb5115b",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "D",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 25,
        "end": 35,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q3fcf231b8767fae3a3079ba7-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v9577372ef247",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      259,
      519,
      779,
      1039,
      1299,
      1559,
      1819,
      2079,
      2339,
      2599,
      2859,
      3119,
      3379,
      3639,
      3899,
      4159,
      4419,
      4679,
      4939,
      5199,
      5459,
      5719,
      5979,
      6239,
      6499,
      6759,
      7019,
      7279,
      7539,
      7799,
      8059
    ],
    "frames": [
      {
        "path": "/data2/k6tk/17/17173fb6a555de176ee34dcd97591b087a0e23ac1717cfc0126d60f88b1c226e.png",
        "sha256": "17173fb6a555de176ee34dcd97591b087a0e23ac1717cfc0126d60f88b1c226e"
      },
      {
        "path": "/data2/k6tk/3c/3ca311e23745085c6536d247d465856f06e06cbc4f8872987a3b126ef2e19ddd.png",
        "sha256": "3ca311e23745085c6536d247d465856f06e06cbc4f8872987a3b126ef2e19ddd"
      },
      {
        "path": "/data2/k6tk/b8/b807562eba94260bef0c104c40156ef531e9a8beb9b82072643f4620478e34b4.png",
        "sha256": "b807562eba94260bef0c104c40156ef531e9a8beb9b82072643f4620478e34b4"
      },
      {
        "path": "/data2/k6tk/07/0741b73d7a5c7e273429e83f2edf781e9f5aa57aeda02008e4bed3aa913dbaaf.png",
        "sha256": "0741b73d7a5c7e273429e83f2edf781e9f5aa57aeda02008e4bed3aa913dbaaf"
      },
      {
        "path": "/data2/k6tk/a1/a1f636657d66d8dd4ffc2499cdea65d8fc052c333e106ba848df11e58a02631c.png",
        "sha256": "a1f636657d66d8dd4ffc2499cdea65d8fc052c333e106ba848df11e58a02631c"
      },
      {
        "path": "/data2/k6tk/cb/cb5f538601a0d1dd8aee57224d98ea7405721e44e5b82418c617d8794d9c30a9.png",
        "sha256": "cb5f538601a0d1dd8aee57224d98ea7405721e44e5b82418c617d8794d9c30a9"
      },
      {
        "path": "/data2/k6tk/b9/b9927ced8948619cfec5debfd1bb2c2a80656b4a9c3088d01e29e3452851267a.png",
        "sha256": "b9927ced8948619cfec5debfd1bb2c2a80656b4a9c3088d01e29e3452851267a"
      },
      {
        "path": "/data2/k6tk/06/06557a3f8bff0aef62e05b6977c153112f153672dad4e4f8f5e547ac0fbd6d85.png",
        "sha256": "06557a3f8bff0aef62e05b6977c153112f153672dad4e4f8f5e547ac0fbd6d85"
      },
      {
        "path": "/data2/k6tk/76/764d825906298e02044d56d4357d1b363bd7959c893eeb013645bb7f52f4f91a.png",
        "sha256": "764d825906298e02044d56d4357d1b363bd7959c893eeb013645bb7f52f4f91a"
      },
      {
        "path": "/data2/k6tk/3a/3ae258b421a4c21533dd06f764dfc6b9a2a4942d9b905ee495e103214454ef1d.png",
        "sha256": "3ae258b421a4c21533dd06f764dfc6b9a2a4942d9b905ee495e103214454ef1d"
      },
      {
        "path": "/data2/k6tk/ee/eeb8da93b30c1624ed8e299b27d06f7eed06a6ba69b845507f9ee0cbc95c2cbf.png",
        "sha256": "eeb8da93b30c1624ed8e299b27d06f7eed06a6ba69b845507f9ee0cbc95c2cbf"
      },
      {
        "path": "/data2/k6tk/2e/2e0d2c3328aaed35d85eaee53d83b8d9dc705e5bdf7398b43a9fb955efa35ce2.png",
        "sha256": "2e0d2c3328aaed35d85eaee53d83b8d9dc705e5bdf7398b43a9fb955efa35ce2"
      },
      {
        "path": "/data2/k6tk/88/880ee830c14ea59b4a83f134f73eef70a663c1b2ef53dbbd9593b3a8c032d99b.png",
        "sha256": "880ee830c14ea59b4a83f134f73eef70a663c1b2ef53dbbd9593b3a8c032d99b"
      },
      {
        "path": "/data2/k6tk/88/88870d433059ee8082cfa93d4bdce307a2be204374e67c7f79828fa1b684b74d.png",
        "sha256": "88870d433059ee8082cfa93d4bdce307a2be204374e67c7f79828fa1b684b74d"
      },
      {
        "path": "/data2/k6tk/6a/6a5cbe2b1798981cfb9c3aa6d84d80661aa89706d3f2ebc4371dfcaa48a0fc86.png",
        "sha256": "6a5cbe2b1798981cfb9c3aa6d84d80661aa89706d3f2ebc4371dfcaa48a0fc86"
      },
      {
        "path": "/data2/k6tk/fc/fceffc17ee3dac2c43168804a01ae9509b9216b3ee7cbdcd15ba4058607cecf9.png",
        "sha256": "fceffc17ee3dac2c43168804a01ae9509b9216b3ee7cbdcd15ba4058607cecf9"
      },
      {
        "path": "/data2/k6tk/ab/ab4248154cf61dd013edfa44f3732c18f994643dbf75be15d95a405800c0e1bd.png",
        "sha256": "ab4248154cf61dd013edfa44f3732c18f994643dbf75be15d95a405800c0e1bd"
      },
      {
        "path": "/data2/k6tk/19/19ba1a4c88f1a4facf9e06dcbb46c5ff80c15fe085054b48bda1d9e7d4a4d328.png",
        "sha256": "19ba1a4c88f1a4facf9e06dcbb46c5ff80c15fe085054b48bda1d9e7d4a4d328"
      },
      {
        "path": "/data2/k6tk/80/80481c84fa8df1953e34568e7dd529b98229232a364b1f45642adb81eb4f5def.png",
        "sha256": "80481c84fa8df1953e34568e7dd529b98229232a364b1f45642adb81eb4f5def"
      },
      {
        "path": "/data2/k6tk/68/6863071d3fdd47ca08d4b1e137159e42ebd12cc5ca186d5d25bb08733ca50a14.png",
        "sha256": "6863071d3fdd47ca08d4b1e137159e42ebd12cc5ca186d5d25bb08733ca50a14"
      },
      {
        "path": "/data2/k6tk/de/debc87c5635e1cebae4d3e99160655c36bc30132b09e4d1905d7ce15d3bf7dc3.png",
        "sha256": "debc87c5635e1cebae4d3e99160655c36bc30132b09e4d1905d7ce15d3bf7dc3"
      },
      {
        "path": "/data2/k6tk/74/748aceb5c056ca7e9ac8ccf69eca0410c591f40b9701725a6713788536255cae.png",
        "sha256": "748aceb5c056ca7e9ac8ccf69eca0410c591f40b9701725a6713788536255cae"
      },
      {
        "path": "/data2/k6tk/2a/2afc7907b8a6ac9a93b58a6bf339938ce9aafa4ab83e9fb82a16e86c14440024.png",
        "sha256": "2afc7907b8a6ac9a93b58a6bf339938ce9aafa4ab83e9fb82a16e86c14440024"
      },
      {
        "path": "/data2/k6tk/77/77cb7d49f26ed8ec38c38911946e76fb000d34428fa01206ea16c903172b16ca.png",
        "sha256": "77cb7d49f26ed8ec38c38911946e76fb000d34428fa01206ea16c903172b16ca"
      },
      {
        "path": "/data2/k6tk/37/37cec9c10e917c2fd34e2f32f1af6617440c861732c442d3f876824211136b4d.png",
        "sha256": "37cec9c10e917c2fd34e2f32f1af6617440c861732c442d3f876824211136b4d"
      },
      {
        "path": "/data2/k6tk/c2/c28f0f27915ad6756216e39b0faea4b3d8acb0eae18409efa2cd2d26cc62d38a.png",
        "sha256": "c28f0f27915ad6756216e39b0faea4b3d8acb0eae18409efa2cd2d26cc62d38a"
      },
      {
        "path": "/data2/k6tk/7a/7aed3ee2a22f91904871d8bb2920dfca85a34d1dac4b63393e5303bec6e71f38.png",
        "sha256": "7aed3ee2a22f91904871d8bb2920dfca85a34d1dac4b63393e5303bec6e71f38"
      },
      {
        "path": "/data2/k6tk/70/7032b8d5a4d3d954d1008e2aa87d3bcd52064b3c52204bd8c88c71992c537acc.png",
        "sha256": "7032b8d5a4d3d954d1008e2aa87d3bcd52064b3c52204bd8c88c71992c537acc"
      },
      {
        "path": "/data2/k6tk/20/2011796508cacc3513e619bfa25905955d371adeebaa16f4c35c5a2d73a2f559.png",
        "sha256": "2011796508cacc3513e619bfa25905955d371adeebaa16f4c35c5a2d73a2f559"
      },
      {
        "path": "/data2/k6tk/b0/b0717b72c8c5aec1d9b3cfcb2d3aac7f34b0daaf8a3ce72012f468e75c01b555.png",
        "sha256": "b0717b72c8c5aec1d9b3cfcb2d3aac7f34b0daaf8a3ce72012f468e75c01b555"
      },
      {
        "path": "/data2/k6tk/6c/6c86b2cad88d8900049efac1f55864ce0de7a6ff03e339b8b8aaba69a6ff60ad.png",
        "sha256": "6c86b2cad88d8900049efac1f55864ce0de7a6ff03e339b8b8aaba69a6ff60ad"
      },
      {
        "path": "/data2/k6tk/c2/c20242da31240501fcd27fbe0be501dbbc0193d3bfb911631ce6793125611e29.png",
        "sha256": "c20242da31240501fcd27fbe0be501dbbc0193d3bfb911631ce6793125611e29"
      }
    ],
    "options": [
      "A. back-right",
      "B. back-left",
      "C. front-left",
      "D. front-right"
    ],
    "question": "I stand by the air fryer facing away from the bed. Where is the food box relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      4.316666666666666,
      8.65,
      12.983333333333333,
      17.316666666666666,
      21.65,
      25.983333333333334,
      30.316666666666666,
      34.65,
      38.983333333333334,
      43.31666666666667,
      47.65,
      51.983333333333334,
      56.31666666666667,
      60.65,
      64.98333333333333,
      69.31666666666666,
      73.65,
      77.98333333333333,
      82.31666666666666,
      86.65,
      90.98333333333333,
      95.31666666666666,
      99.65,
      103.98333333333333,
      108.31666666666666,
      112.65,
      116.98333333333333,
      121.31666666666666,
      125.65,
      129.98333333333332,
      134.31666666666666
    ],
    "total_num_frames": 8060
  },
  "target": "<think>\nStep 1: find the air fryer, the bed and the food box.\nStep 2: I stand at the air fryer facing the bed; I find the food box in front of me, on my right.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the food box at my back-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q3fcf231b8767fae3a3079ba7",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "6e84da3d4e87aa946c5757a5953b1328bbe9cc798566d7715bc6f65abc99e5c6"
  },
  "facing": "away",
  "candidate_id": "ground-3fb296200711bfcc4eda1890369ff22d93ae0c4579d740fe0503beb965975945",
  "label_row_keys": [
    "q3fcf231b8767fae3a3079ba7-p1"
  ]
}
```

## 22. qb6f5bee0a1c54c870a1aa7e1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qb6f5bee0a1c54c870a1aa7e1",
      "source_store_i": 14410,
      "source_row_sha256": "461a5717f1f99beb988e0a1093c9d3459801a4b2bc5adecd724fa6a08743d981",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 42,
        "end": 48,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qb6f5bee0a1c54c870a1aa7e1_sb_rowD7_a",
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
    "question": "If I am standing by the cardboard box and facing away from the coat, is the clock to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
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
  "target": "<think>\nStep 1: find the cardboard box, the coat and the clock.\nStep 2: facing the coat from the cardboard box, I find the clock in front of me, on my right.\nStep 3: I face away from the coat by making a half turn. Front and back swap, and left and right swap.\nSo I find the clock at my back-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "31b2670b9a851cd713cfe2a1abe2a3e3769fcef1c51b5a0c4cf543614af1289c"
  },
  "facing": "away",
  "candidate_id": "ground-77def8bec2ed1e8956372ed484783f3d4dc768b3cb7b1cffaf165a0ac9dfe6d8",
  "label_row_keys": [
    "qb6f5bee0a1c54c870a1aa7e1"
  ]
}
```

## 23. q2b661224f62b79c9d28b25c7_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q2b661224f62b79c9d28b25c7",
      "source_store_i": 30114,
      "source_row_sha256": "8d18a91fd8f783fea4ffbf6448be9cc26f43fba755c201d842c60c9ad96094d6",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q2b661224f62b79c9d28b25c7_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vef284fdae230",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      265,
      531,
      797,
      1063,
      1329,
      1595,
      1861,
      2127,
      2393,
      2659,
      2925,
      3191,
      3457,
      3723,
      3989,
      4254,
      4520,
      4786,
      5052,
      5318,
      5584,
      5850,
      6116,
      6382,
      6648,
      6914,
      7180,
      7446,
      7712,
      7978,
      8244
    ],
    "frames": [
      {
        "path": "/data2/k6tk/4a/4a46c51603e783e13f62d2bbbc5d09d55b57480cca544a29ec1e41025a3fbfdd.png",
        "sha256": "4a46c51603e783e13f62d2bbbc5d09d55b57480cca544a29ec1e41025a3fbfdd"
      },
      {
        "path": "/data2/k6tk/8c/8ceb564153aac06ac7c21098a05ec705bc99ccb58f1e1ef24050a8d620231631.png",
        "sha256": "8ceb564153aac06ac7c21098a05ec705bc99ccb58f1e1ef24050a8d620231631"
      },
      {
        "path": "/data2/k6tk/ce/ce9b4bdc636ed5ae42b126cebdefc5b3db73e49b147ea411664a32e2d3d5863d.png",
        "sha256": "ce9b4bdc636ed5ae42b126cebdefc5b3db73e49b147ea411664a32e2d3d5863d"
      },
      {
        "path": "/data2/k6tk/37/37a806e5cded7f1d3d9e755c53559da3eb14f077aaf17852b0ace23f6dab9473.png",
        "sha256": "37a806e5cded7f1d3d9e755c53559da3eb14f077aaf17852b0ace23f6dab9473"
      },
      {
        "path": "/data2/k6tk/c6/c611b323e88d6e1d7acac313beeb5df1f4207d0fe09f14c01261f4c401d7105f.png",
        "sha256": "c611b323e88d6e1d7acac313beeb5df1f4207d0fe09f14c01261f4c401d7105f"
      },
      {
        "path": "/data2/k6tk/38/38bb5f4830018628af03449ecd3b3302b94c2ffd8af6c23326cd1377bf832567.png",
        "sha256": "38bb5f4830018628af03449ecd3b3302b94c2ffd8af6c23326cd1377bf832567"
      },
      {
        "path": "/data2/k6tk/d6/d6116d6e28e29580fc9ab0a2f55ecb82b78f37bfb5087a1e2ae0daee04781efc.png",
        "sha256": "d6116d6e28e29580fc9ab0a2f55ecb82b78f37bfb5087a1e2ae0daee04781efc"
      },
      {
        "path": "/data2/k6tk/bd/bdaabcc8fef72c9311c757a65e06074cc9f8cf658260920888e21623f97fce46.png",
        "sha256": "bdaabcc8fef72c9311c757a65e06074cc9f8cf658260920888e21623f97fce46"
      },
      {
        "path": "/data2/k6tk/82/82f3b2f7d700761884f24d8b846541ba2c32c1ab460e3d25a974cfd7a613a486.png",
        "sha256": "82f3b2f7d700761884f24d8b846541ba2c32c1ab460e3d25a974cfd7a613a486"
      },
      {
        "path": "/data2/k6tk/71/71bf1554bdc16efdb377b946770e3a66a5e2dd066b27b987c03b0c1d1ff7324d.png",
        "sha256": "71bf1554bdc16efdb377b946770e3a66a5e2dd066b27b987c03b0c1d1ff7324d"
      },
      {
        "path": "/data2/k6tk/4d/4d373015112dd14efe6220d13b723148afba94a99c5b339af96b7aa535a72ee6.png",
        "sha256": "4d373015112dd14efe6220d13b723148afba94a99c5b339af96b7aa535a72ee6"
      },
      {
        "path": "/data2/k6tk/41/410b28451d466f433fae11478e6a1b89ab2b74e080d70dbd0d8cd6eec5448bfd.png",
        "sha256": "410b28451d466f433fae11478e6a1b89ab2b74e080d70dbd0d8cd6eec5448bfd"
      },
      {
        "path": "/data2/k6tk/08/08b553709b48c312ed87dc33908c01841164fdebe0aad358b5fc5a43f33b6489.png",
        "sha256": "08b553709b48c312ed87dc33908c01841164fdebe0aad358b5fc5a43f33b6489"
      },
      {
        "path": "/data2/k6tk/fd/fd21044bc89ce16303ee9915dad93987ad7ba24a83c9c4a13bb8e4fe594ac3af.png",
        "sha256": "fd21044bc89ce16303ee9915dad93987ad7ba24a83c9c4a13bb8e4fe594ac3af"
      },
      {
        "path": "/data2/k6tk/d6/d688de93cad48c657c46911f4379e6ebb55fd8c3cf85b1917967fcecce720b89.png",
        "sha256": "d688de93cad48c657c46911f4379e6ebb55fd8c3cf85b1917967fcecce720b89"
      },
      {
        "path": "/data2/k6tk/18/1875a684310dac25085fe404ac733fdcbc4168feea853807214b4e4b319d3ebb.png",
        "sha256": "1875a684310dac25085fe404ac733fdcbc4168feea853807214b4e4b319d3ebb"
      },
      {
        "path": "/data2/k6tk/ec/ec6c041a474a59989e9a5265823c0c02fce093818c3cb154871597083e37b3dd.png",
        "sha256": "ec6c041a474a59989e9a5265823c0c02fce093818c3cb154871597083e37b3dd"
      },
      {
        "path": "/data2/k6tk/cd/cd1ca026d13fbb8058fbd932cfc28d83e660d32600f5e4838de1b49207a90d83.png",
        "sha256": "cd1ca026d13fbb8058fbd932cfc28d83e660d32600f5e4838de1b49207a90d83"
      },
      {
        "path": "/data2/k6tk/62/6227360365da8b512895d2b5acc49c4fd037bad66f43db0d847ab08fbf0231e8.png",
        "sha256": "6227360365da8b512895d2b5acc49c4fd037bad66f43db0d847ab08fbf0231e8"
      },
      {
        "path": "/data2/k6tk/8b/8bc7f73433f446b49feff314bb86c1726d4a5f38c37b5335eec5672aaa2a4aed.png",
        "sha256": "8bc7f73433f446b49feff314bb86c1726d4a5f38c37b5335eec5672aaa2a4aed"
      },
      {
        "path": "/data2/k6tk/ce/ced68ba71a2e7d9f7b3328ea95912e6d1f9e1740f9f9b5358f6f1bd7e8b86468.png",
        "sha256": "ced68ba71a2e7d9f7b3328ea95912e6d1f9e1740f9f9b5358f6f1bd7e8b86468"
      },
      {
        "path": "/data2/k6tk/93/935db3292e5389a59d806a7d52cb98c573eb500f7e4882503dd69f2abf13bb3f.png",
        "sha256": "935db3292e5389a59d806a7d52cb98c573eb500f7e4882503dd69f2abf13bb3f"
      },
      {
        "path": "/data2/k6tk/64/64fbd889e6fd8ebb7f25c6df9913c717c2a5e0d46284f70ffd920fa8a4bcdcc4.png",
        "sha256": "64fbd889e6fd8ebb7f25c6df9913c717c2a5e0d46284f70ffd920fa8a4bcdcc4"
      },
      {
        "path": "/data2/k6tk/10/102c98ba8bef606ac911b252ac2523640af4e158e1a806083d153ca72648ff35.png",
        "sha256": "102c98ba8bef606ac911b252ac2523640af4e158e1a806083d153ca72648ff35"
      },
      {
        "path": "/data2/k6tk/5d/5d67fd5dd4a58fdffc5e4afe9a8ad41a7fff5068cb35857811deecc6143a18dc.png",
        "sha256": "5d67fd5dd4a58fdffc5e4afe9a8ad41a7fff5068cb35857811deecc6143a18dc"
      },
      {
        "path": "/data2/k6tk/65/65b74cf16009e728d08f047aba6c49d084b975873273a5d2a4df9349fb7d9b2c.png",
        "sha256": "65b74cf16009e728d08f047aba6c49d084b975873273a5d2a4df9349fb7d9b2c"
      },
      {
        "path": "/data2/k6tk/dc/dc7f98a548745eac323a74ce3ca6795b50a0c4e60ba26f33e549e91bf2c6e42b.png",
        "sha256": "dc7f98a548745eac323a74ce3ca6795b50a0c4e60ba26f33e549e91bf2c6e42b"
      },
      {
        "path": "/data2/k6tk/b7/b7bf7e60f361f35a6a1887a69775f0384c7d9912699796036268450b6d19e278.png",
        "sha256": "b7bf7e60f361f35a6a1887a69775f0384c7d9912699796036268450b6d19e278"
      },
      {
        "path": "/data2/k6tk/82/827ebdf165630c132486bbd1fab5955a573caa003e7e0d8392221cfaf5c7f47a.png",
        "sha256": "827ebdf165630c132486bbd1fab5955a573caa003e7e0d8392221cfaf5c7f47a"
      },
      {
        "path": "/data2/k6tk/01/01cdf4e07e28718afbac4cf22a935abad775a82adad821b6665d3556d5fe4c8c.png",
        "sha256": "01cdf4e07e28718afbac4cf22a935abad775a82adad821b6665d3556d5fe4c8c"
      },
      {
        "path": "/data2/k6tk/5b/5b9c57aeb1acfb7766bc0b9caa02cd96c25507b3bfd8931c78c068e4693825b9.png",
        "sha256": "5b9c57aeb1acfb7766bc0b9caa02cd96c25507b3bfd8931c78c068e4693825b9"
      },
      {
        "path": "/data2/k6tk/65/65ec7baff8ba5a0d17760f1fe71bfce71c65c638aa49bc7697da53e282dcc09a.png",
        "sha256": "65ec7baff8ba5a0d17760f1fe71bfce71c65c638aa49bc7697da53e282dcc09a"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-left",
      "C. front-right",
      "D. back-right"
    ],
    "question": "If I am standing by the backpack and facing away from the computer mouse, is the tapestry to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      4.416666666666667,
      8.85,
      13.283333333333333,
      17.716666666666665,
      22.15,
      26.583333333333332,
      31.016666666666666,
      35.45,
      39.88333333333333,
      44.31666666666667,
      48.75,
      53.18333333333333,
      57.61666666666667,
      62.05,
      66.48333333333333,
      70.9,
      75.33333333333333,
      79.76666666666667,
      84.2,
      88.63333333333334,
      93.06666666666666,
      97.5,
      101.93333333333334,
      106.36666666666666,
      110.8,
      115.23333333333333,
      119.66666666666667,
      124.1,
      128.53333333333333,
      132.96666666666667,
      137.4
    ],
    "total_num_frames": 8245
  },
  "target": "<think>\nStep 1: find the backpack, the computer mouse and the tapestry.\nStep 2: I stand at the backpack facing the computer mouse; I find the tapestry in front of me, on my right.\nStep 3: I face away from the computer mouse by making a half turn. Front and back swap, and left and right swap.\nSo I find the tapestry at my back-left.\n</think>\n\nA",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "87785503331ae2b76cb67311404298989a85ec2ea6d475e55470e4cb32a25d9d"
  },
  "facing": "away",
  "candidate_id": "ground-4b9acffb3d85e16159689ba4922c11b400ed874b316bdea4e0e9c2e351b64729",
  "label_row_keys": [
    "q2b661224f62b79c9d28b25c7"
  ]
}
```

## 24. qd7809e4f0a765b646ae1641f_sb_rowD7_a

```json
{
  "answer": "B",
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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qd7809e4f0a765b646ae1641f",
      "source_store_i": 44337,
      "source_row_sha256": "c6b8614261d4692383cf5a1713a2b76ba24167c39c0fd6570d3f947e05479ab0",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qd7809e4f0a765b646ae1641f_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "va3c94c367343",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      34,
      69,
      104,
      138,
      173,
      208,
      242,
      277,
      312,
      346,
      381,
      416,
      450,
      485,
      520,
      554,
      589,
      624,
      658,
      693,
      728,
      762,
      797,
      832,
      866,
      901,
      936,
      970,
      1005,
      1040,
      1075
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f9/f98ef06f388778da3cd5844e696b14d789dc363007e3e16c788d5e37cb160c01.png",
        "sha256": "f98ef06f388778da3cd5844e696b14d789dc363007e3e16c788d5e37cb160c01"
      },
      {
        "path": "/data2/k6tk/a6/a655267beafb9ec052679f07d66042ec7b93d2204f87411a1141818e9934438e.png",
        "sha256": "a655267beafb9ec052679f07d66042ec7b93d2204f87411a1141818e9934438e"
      },
      {
        "path": "/data2/k6tk/dc/dc7322895d26746191f89535fed41925b52beee67b244138a88941ec387c654f.png",
        "sha256": "dc7322895d26746191f89535fed41925b52beee67b244138a88941ec387c654f"
      },
      {
        "path": "/data2/k6tk/ba/babc5ef64dd5e3f29257fbf0fbdf38d67ca88b6578c5af323e7ce2559c42e004.png",
        "sha256": "babc5ef64dd5e3f29257fbf0fbdf38d67ca88b6578c5af323e7ce2559c42e004"
      },
      {
        "path": "/data2/k6tk/fa/fac706dd5e99fc92b78ffef9b800246bcea1803d2dd7bf4bbc4f3814a0ecd411.png",
        "sha256": "fac706dd5e99fc92b78ffef9b800246bcea1803d2dd7bf4bbc4f3814a0ecd411"
      },
      {
        "path": "/data2/k6tk/0c/0cf7aa8ac69c5b291296a0c5d65c40f661b5332aa6a0b65465079f776812c6cd.png",
        "sha256": "0cf7aa8ac69c5b291296a0c5d65c40f661b5332aa6a0b65465079f776812c6cd"
      },
      {
        "path": "/data2/k6tk/04/0426aa924139207c47b00cf94d491952272eb77e74b8176edf6d836f093d547b.png",
        "sha256": "0426aa924139207c47b00cf94d491952272eb77e74b8176edf6d836f093d547b"
      },
      {
        "path": "/data2/k6tk/bf/bf65f29391e9696d42bbc10bb2f53c7c9f45ae724521de6a2a25a9d3d90b67cf.png",
        "sha256": "bf65f29391e9696d42bbc10bb2f53c7c9f45ae724521de6a2a25a9d3d90b67cf"
      },
      {
        "path": "/data2/k6tk/a6/a639c40455d006c50ec88a61a621c93f1f30f73a23096511234da16303b4256d.png",
        "sha256": "a639c40455d006c50ec88a61a621c93f1f30f73a23096511234da16303b4256d"
      },
      {
        "path": "/data2/k6tk/ab/ab182d289df6962f005b621185b8c09b8890d9625ba15919ccc114abda2250be.png",
        "sha256": "ab182d289df6962f005b621185b8c09b8890d9625ba15919ccc114abda2250be"
      },
      {
        "path": "/data2/k6tk/5b/5baf72dbf3125e999c96ee253436bdea6b121be558f9adc312a38946b6c0ddf1.png",
        "sha256": "5baf72dbf3125e999c96ee253436bdea6b121be558f9adc312a38946b6c0ddf1"
      },
      {
        "path": "/data2/k6tk/db/db965c55e5fa346bded23726b2f06c2e5214da086132e73521295df969724198.png",
        "sha256": "db965c55e5fa346bded23726b2f06c2e5214da086132e73521295df969724198"
      },
      {
        "path": "/data2/k6tk/ed/ed4ffcf4b65a75459f6c32b3b3f26b7b562fcd4aea71d750fc61b919d7e8bad2.png",
        "sha256": "ed4ffcf4b65a75459f6c32b3b3f26b7b562fcd4aea71d750fc61b919d7e8bad2"
      },
      {
        "path": "/data2/k6tk/50/50b87c76e2c1cc1b8da8d93c5486e6c55b827acf8eb54a880e51ffebb1b84622.png",
        "sha256": "50b87c76e2c1cc1b8da8d93c5486e6c55b827acf8eb54a880e51ffebb1b84622"
      },
      {
        "path": "/data2/k6tk/fd/fd5e299ed34167417696ace60d39758f70954c93d94ec928d4badd87228caca5.png",
        "sha256": "fd5e299ed34167417696ace60d39758f70954c93d94ec928d4badd87228caca5"
      },
      {
        "path": "/data2/k6tk/ca/ca0847bf801681307aece6fda81c0a9d81b97f40832e0cb634ff673e1491a9b9.png",
        "sha256": "ca0847bf801681307aece6fda81c0a9d81b97f40832e0cb634ff673e1491a9b9"
      },
      {
        "path": "/data2/k6tk/f9/f999432d4af9600a02e3a94df2e3ec1c11b9599a58e21e198c20c263a1d0ae40.png",
        "sha256": "f999432d4af9600a02e3a94df2e3ec1c11b9599a58e21e198c20c263a1d0ae40"
      },
      {
        "path": "/data2/k6tk/05/055b7004c964edfe6dd578de61d11374fc365423b0be91b4359fcc981d1b54b2.png",
        "sha256": "055b7004c964edfe6dd578de61d11374fc365423b0be91b4359fcc981d1b54b2"
      },
      {
        "path": "/data2/k6tk/b9/b97fcbf5f2ad5076aa182968c9f035b35a7b48df463cd4e9852872787c71b47f.png",
        "sha256": "b97fcbf5f2ad5076aa182968c9f035b35a7b48df463cd4e9852872787c71b47f"
      },
      {
        "path": "/data2/k6tk/88/88d1c8c525672a2737f0d67239006934a5ddf98188039bc6fe6f9ca84d811441.png",
        "sha256": "88d1c8c525672a2737f0d67239006934a5ddf98188039bc6fe6f9ca84d811441"
      },
      {
        "path": "/data2/k6tk/a4/a417d5c559a4e6cfafb89898511655021fc2a285302938e69f847ae0b5bfaef6.png",
        "sha256": "a417d5c559a4e6cfafb89898511655021fc2a285302938e69f847ae0b5bfaef6"
      },
      {
        "path": "/data2/k6tk/6c/6c5a2495a61be9ee9c9455beb35498dbcd11ce54700cde1430b845ddf41522c9.png",
        "sha256": "6c5a2495a61be9ee9c9455beb35498dbcd11ce54700cde1430b845ddf41522c9"
      },
      {
        "path": "/data2/k6tk/85/854ce2adcd439cbe4278943914a55b3f18d938ceba9f885ce25d602c739b4b88.png",
        "sha256": "854ce2adcd439cbe4278943914a55b3f18d938ceba9f885ce25d602c739b4b88"
      },
      {
        "path": "/data2/k6tk/0e/0e7976983c301b7ec75003a96a3fbddfac39611436366e2c84ed86cd9c93378e.png",
        "sha256": "0e7976983c301b7ec75003a96a3fbddfac39611436366e2c84ed86cd9c93378e"
      },
      {
        "path": "/data2/k6tk/ed/edf897b7d78ab8c86653ade906d607ad981da1c0045c61c40d03bca6e890cd72.png",
        "sha256": "edf897b7d78ab8c86653ade906d607ad981da1c0045c61c40d03bca6e890cd72"
      },
      {
        "path": "/data2/k6tk/38/3889548f6e5a74eaa0d353fd040b8d0ccca820eee68b0863b225291533ea9aac.png",
        "sha256": "3889548f6e5a74eaa0d353fd040b8d0ccca820eee68b0863b225291533ea9aac"
      },
      {
        "path": "/data2/k6tk/d7/d72c76910d75d0581e397e5b5a478b7204f69b5c2bb3e02155f1ac906aed64f6.png",
        "sha256": "d72c76910d75d0581e397e5b5a478b7204f69b5c2bb3e02155f1ac906aed64f6"
      },
      {
        "path": "/data2/k6tk/16/165efd7cd9c798d6d4e160dc519e149025705bc4eebd54e6957f03d6494d797b.png",
        "sha256": "165efd7cd9c798d6d4e160dc519e149025705bc4eebd54e6957f03d6494d797b"
      },
      {
        "path": "/data2/k6tk/5c/5c632276cdac6c8c416c0670069a414042a9f58c085439dcae4e7b03e6eda318.png",
        "sha256": "5c632276cdac6c8c416c0670069a414042a9f58c085439dcae4e7b03e6eda318"
      },
      {
        "path": "/data2/k6tk/f1/f1861d2a33ac0125d01094bd3615acd31530ae251309def9072564d9c07f08c5.png",
        "sha256": "f1861d2a33ac0125d01094bd3615acd31530ae251309def9072564d9c07f08c5"
      },
      {
        "path": "/data2/k6tk/60/6004f88bdde9bd0462e108e84402bc543beb20c17bd80adc8536e4b84fda885a.png",
        "sha256": "6004f88bdde9bd0462e108e84402bc543beb20c17bd80adc8536e4b84fda885a"
      },
      {
        "path": "/data2/k6tk/b5/b50fb64e4638cfaea4756d7ed9154ce25d831d07755080abb41f86967aaaf249.png",
        "sha256": "b50fb64e4638cfaea4756d7ed9154ce25d831d07755080abb41f86967aaaf249"
      }
    ],
    "options": [
      "A. front-right",
      "B. back-left",
      "C. front-left",
      "D. back-right"
    ],
    "question": "If I am standing by the copier and facing away from the paper cutter, is the door to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.4166666666666667,
      2.875,
      4.333333333333333,
      5.75,
      7.208333333333333,
      8.666666666666666,
      10.083333333333334,
      11.541666666666666,
      13.0,
      14.416666666666666,
      15.875,
      17.333333333333332,
      18.75,
      20.208333333333332,
      21.666666666666668,
      23.083333333333332,
      24.541666666666668,
      26.0,
      27.416666666666668,
      28.875,
      30.333333333333332,
      31.75,
      33.208333333333336,
      34.666666666666664,
      36.083333333333336,
      37.541666666666664,
      39.0,
      40.416666666666664,
      41.875,
      43.333333333333336,
      44.791666666666664
    ],
    "total_num_frames": 1076
  },
  "target": "<think>\nStep 1: find the copier, the paper cutter and the door.\nStep 2: I stand at the copier facing the paper cutter; I find the door in front of me, on my right.\nStep 3: I face away from the paper cutter by making a half turn. Front and back swap, and left and right swap.\nSo I find the door at my back-left.\n</think>\n\nB",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "ab0f254169fd35c7a70e3cb793e70a614002dd205086ab5292cc9bd68dae1c15"
  },
  "facing": "away",
  "candidate_id": "ground-9ebb9c563abb0081102d6b41de1b8d39142bca9b5554d1839877cf947cc99bda",
  "label_row_keys": [
    "qd7809e4f0a765b646ae1641f"
  ]
}
```

## 25. q14edd97680c19c5d99d425ed_sb_rowD7_a

```json
{
  "answer": "C",
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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q14edd97680c19c5d99d425ed",
      "source_store_i": 33637,
      "source_row_sha256": "337309cc3353e0e2dd2aba2944aea26df1ace4eb0564503ad0c15f6f3be6935b",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q14edd97680c19c5d99d425ed_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v7d22adc96436",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      45,
      90,
      136,
      181,
      226,
      272,
      317,
      362,
      408,
      453,
      498,
      544,
      589,
      634,
      680,
      725,
      771,
      816,
      861,
      907,
      952,
      997,
      1043,
      1088,
      1133,
      1179,
      1224,
      1269,
      1315,
      1360,
      1406
    ],
    "frames": [
      {
        "path": "/data2/k6tk/6e/6ed2a812bf11bab64b18907ee7caf735673010359d93c5802db04f28e7199de5.png",
        "sha256": "6ed2a812bf11bab64b18907ee7caf735673010359d93c5802db04f28e7199de5"
      },
      {
        "path": "/data2/k6tk/6f/6f4b8c3c741f75b94f2a34e4bd4a50bc7937776d464feaacd72bd58a96afca9e.png",
        "sha256": "6f4b8c3c741f75b94f2a34e4bd4a50bc7937776d464feaacd72bd58a96afca9e"
      },
      {
        "path": "/data2/k6tk/64/6412b7713260f01964a0e50c75826f7c9794581aa1e1e28ed3c7cba1a44aa8a3.png",
        "sha256": "6412b7713260f01964a0e50c75826f7c9794581aa1e1e28ed3c7cba1a44aa8a3"
      },
      {
        "path": "/data2/k6tk/31/317369ee735a23234c28cf175c0b1364897d7797a9f1e91e3b0d5388833b4346.png",
        "sha256": "317369ee735a23234c28cf175c0b1364897d7797a9f1e91e3b0d5388833b4346"
      },
      {
        "path": "/data2/k6tk/07/07d045f030f9cdf8ae0f980bd3e8f2cd80eee0187744186cb33c472628eeb1d6.png",
        "sha256": "07d045f030f9cdf8ae0f980bd3e8f2cd80eee0187744186cb33c472628eeb1d6"
      },
      {
        "path": "/data2/k6tk/6a/6ad83900eb6f90282e2ac06e585d50292df2c41b56e7c30cb83ad09037f9f493.png",
        "sha256": "6ad83900eb6f90282e2ac06e585d50292df2c41b56e7c30cb83ad09037f9f493"
      },
      {
        "path": "/data2/k6tk/2e/2e00c38e33be32567ef8adf8f9c193f92082efa818c2c20e958966602410c6f5.png",
        "sha256": "2e00c38e33be32567ef8adf8f9c193f92082efa818c2c20e958966602410c6f5"
      },
      {
        "path": "/data2/k6tk/45/457e04d0f312ca343531946add14593f9ff4a53ce57e3498abfbc1fbe5b656d5.png",
        "sha256": "457e04d0f312ca343531946add14593f9ff4a53ce57e3498abfbc1fbe5b656d5"
      },
      {
        "path": "/data2/k6tk/bb/bb47e51013bab2ff1c04fd5e0474f5f607ae15e1bdb271650939af34906d3037.png",
        "sha256": "bb47e51013bab2ff1c04fd5e0474f5f607ae15e1bdb271650939af34906d3037"
      },
      {
        "path": "/data2/k6tk/70/70aab714ee99b22a2b9f1e578ecf76add13b440fba7f0ff0d2aa8b4f2e21300e.png",
        "sha256": "70aab714ee99b22a2b9f1e578ecf76add13b440fba7f0ff0d2aa8b4f2e21300e"
      },
      {
        "path": "/data2/k6tk/7d/7d91a614389685a596518fa89bd33512e944b82841be4abf3d7d782abf85405c.png",
        "sha256": "7d91a614389685a596518fa89bd33512e944b82841be4abf3d7d782abf85405c"
      },
      {
        "path": "/data2/k6tk/00/00b8931e7eb66c900f3ca2b9f09ba653b708aa4ac9e75c5801cd1c3871c9978b.png",
        "sha256": "00b8931e7eb66c900f3ca2b9f09ba653b708aa4ac9e75c5801cd1c3871c9978b"
      },
      {
        "path": "/data2/k6tk/fe/fe64d571479a887505e4d00e85de548532a8bbcbf4d7ae6058346018b72cf493.png",
        "sha256": "fe64d571479a887505e4d00e85de548532a8bbcbf4d7ae6058346018b72cf493"
      },
      {
        "path": "/data2/k6tk/d8/d80b02532e3981fc50d136e18bb7fe8e6be9ef639ff5dc2d5327e7fee76fd2af.png",
        "sha256": "d80b02532e3981fc50d136e18bb7fe8e6be9ef639ff5dc2d5327e7fee76fd2af"
      },
      {
        "path": "/data2/k6tk/3c/3c3022cecce7f07f448ad3ec32ae7183f72175af3837d545e4ff9522022aebdf.png",
        "sha256": "3c3022cecce7f07f448ad3ec32ae7183f72175af3837d545e4ff9522022aebdf"
      },
      {
        "path": "/data2/k6tk/a3/a34c7c97e993db303c6c79172766b490deee0afb3838ba017118925ce3fac0c8.png",
        "sha256": "a34c7c97e993db303c6c79172766b490deee0afb3838ba017118925ce3fac0c8"
      },
      {
        "path": "/data2/k6tk/5b/5bebb36ccddc745cb826f3284fb67e33918ef4f0021aa6b9cb03008dbf334639.png",
        "sha256": "5bebb36ccddc745cb826f3284fb67e33918ef4f0021aa6b9cb03008dbf334639"
      },
      {
        "path": "/data2/k6tk/6b/6b9c200e58360b5757c62fa6f48104d8f4753c7d892541faf1a5f11659accb1b.png",
        "sha256": "6b9c200e58360b5757c62fa6f48104d8f4753c7d892541faf1a5f11659accb1b"
      },
      {
        "path": "/data2/k6tk/66/66e4b010ed9119c47453dc68935c11309e9e98aa09d32edc0ba7a2d17cf5391a.png",
        "sha256": "66e4b010ed9119c47453dc68935c11309e9e98aa09d32edc0ba7a2d17cf5391a"
      },
      {
        "path": "/data2/k6tk/ad/ad957f92112c11f2fbebb6d174c2c9d3862f81bf6905e403de26224e96d8fdc5.png",
        "sha256": "ad957f92112c11f2fbebb6d174c2c9d3862f81bf6905e403de26224e96d8fdc5"
      },
      {
        "path": "/data2/k6tk/5f/5f0cd851dc88ba667cf4f96c6c0b79568d554518aff3de2718bdad0a520af592.png",
        "sha256": "5f0cd851dc88ba667cf4f96c6c0b79568d554518aff3de2718bdad0a520af592"
      },
      {
        "path": "/data2/k6tk/cf/cf80bbf23921ea37cde407de5ba05f3166f22ec9edf2fc93bb0715921b4f9421.png",
        "sha256": "cf80bbf23921ea37cde407de5ba05f3166f22ec9edf2fc93bb0715921b4f9421"
      },
      {
        "path": "/data2/k6tk/08/08b07a970e55d32ac9e2a208029b8777975f06e2178ff1e180678c14c3bfbbd2.png",
        "sha256": "08b07a970e55d32ac9e2a208029b8777975f06e2178ff1e180678c14c3bfbbd2"
      },
      {
        "path": "/data2/k6tk/f5/f50be01409bae21ac856977271bd4a34963624524a27cc373467a86f3dbc2dcf.png",
        "sha256": "f50be01409bae21ac856977271bd4a34963624524a27cc373467a86f3dbc2dcf"
      },
      {
        "path": "/data2/k6tk/a9/a9760ccb19a9001f990afe79af2f8c3e0a479c5279add4b0ea328e64fe0c30ad.png",
        "sha256": "a9760ccb19a9001f990afe79af2f8c3e0a479c5279add4b0ea328e64fe0c30ad"
      },
      {
        "path": "/data2/k6tk/b3/b3f15c62ab2bc16f6aa0ce3481ebaaaef621b7ad6113d4cfbb4187a5f9a6dbc8.png",
        "sha256": "b3f15c62ab2bc16f6aa0ce3481ebaaaef621b7ad6113d4cfbb4187a5f9a6dbc8"
      },
      {
        "path": "/data2/k6tk/d2/d220b3b29bdc14623898f76a7b7a63cbfdbc8e8a881149d259b1d93d933322e6.png",
        "sha256": "d220b3b29bdc14623898f76a7b7a63cbfdbc8e8a881149d259b1d93d933322e6"
      },
      {
        "path": "/data2/k6tk/dd/dd06073f03ff997ba525597057d408dcd6f29db64f2045365ca6d644a40caea6.png",
        "sha256": "dd06073f03ff997ba525597057d408dcd6f29db64f2045365ca6d644a40caea6"
      },
      {
        "path": "/data2/k6tk/6f/6ff3ea9bc87e0bbca39e0907d35bf5673646a52f53268400f45aacd62c4852a9.png",
        "sha256": "6ff3ea9bc87e0bbca39e0907d35bf5673646a52f53268400f45aacd62c4852a9"
      },
      {
        "path": "/data2/k6tk/09/095d82c90605f12679ef44592cd2e9e89a1224b81486a85b2d10d5754a9b7723.png",
        "sha256": "095d82c90605f12679ef44592cd2e9e89a1224b81486a85b2d10d5754a9b7723"
      },
      {
        "path": "/data2/k6tk/99/998b71a16cd644056cb677f03d0479c4881d2423f1ee724ab6fc1ed24fd5a0ef.png",
        "sha256": "998b71a16cd644056cb677f03d0479c4881d2423f1ee724ab6fc1ed24fd5a0ef"
      },
      {
        "path": "/data2/k6tk/a0/a07de0e313d0cd7f8b7acff4b5f39c19b9f91ab546ac8d6ff4949fe2a93e0141.png",
        "sha256": "a07de0e313d0cd7f8b7acff4b5f39c19b9f91ab546ac8d6ff4949fe2a93e0141"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-left",
      "D. back-right"
    ],
    "question": "If I am standing by the bed and facing away from the folded ladder, is the mirror to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.875,
      3.75,
      5.666666666666667,
      7.541666666666667,
      9.416666666666666,
      11.333333333333334,
      13.208333333333334,
      15.083333333333334,
      17.0,
      18.875,
      20.75,
      22.666666666666668,
      24.541666666666668,
      26.416666666666668,
      28.333333333333332,
      30.208333333333332,
      32.125,
      34.0,
      35.875,
      37.791666666666664,
      39.666666666666664,
      41.541666666666664,
      43.458333333333336,
      45.333333333333336,
      47.208333333333336,
      49.125,
      51.0,
      52.875,
      54.791666666666664,
      56.666666666666664,
      58.583333333333336
    ],
    "total_num_frames": 1407
  },
  "target": "<think>\nStep 1: find the bed, the folded ladder and the mirror.\nStep 2: I stand at the bed facing the folded ladder; I find the mirror in front of me, on my right.\nStep 3: I face away from the folded ladder by making a half turn. Front and back swap, and left and right swap.\nSo I find the mirror at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "db57b2669b9ea4d6fbcaa2a0d2f4e89a3c85f4f77fec9c5dcb4e34f6c9987d11"
  },
  "facing": "away",
  "candidate_id": "ground-0b074f1e9679c616c7f161dc6d4fb7f9d9ca53e08fad4083d6bb0a5dbe982645",
  "label_row_keys": [
    "q14edd97680c19c5d99d425ed"
  ]
}
```

## 26. qad5d9b837b70196ca57002bf_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qad5d9b837b70196ca57002bf",
      "source_store_i": 35582,
      "source_row_sha256": "ebc921f654501e5a67cc50f62592797650e29816fd396dcb636dc54162a57d6c",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 47,
        "end": 53,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qad5d9b837b70196ca57002bf_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v0a40235d93ca",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      340,
      680,
      1020,
      1360,
      1700,
      2040,
      2381,
      2721,
      3061,
      3401,
      3741,
      4081,
      4422,
      4762,
      5102,
      5442,
      5782,
      6122,
      6463,
      6803,
      7143,
      7483,
      7823,
      8163,
      8504,
      8844,
      9184,
      9524,
      9864,
      10204,
      10545
    ],
    "frames": [
      {
        "path": "/data2/k6tk/d9/d9c94639cd8a274ec7986a4703411c45d5575f015497c9a9e9af281ef8c2dcc5.png",
        "sha256": "d9c94639cd8a274ec7986a4703411c45d5575f015497c9a9e9af281ef8c2dcc5"
      },
      {
        "path": "/data2/k6tk/77/774a5ce1ba8861394d7a8f18d87340a54c6e7af55a88b7fd63678882e9ee4fc0.png",
        "sha256": "774a5ce1ba8861394d7a8f18d87340a54c6e7af55a88b7fd63678882e9ee4fc0"
      },
      {
        "path": "/data2/k6tk/b8/b825d4cb4d664f5aae9cb85bcfb94b70e61117a04ed4d8b6f5cc169091d49caf.png",
        "sha256": "b825d4cb4d664f5aae9cb85bcfb94b70e61117a04ed4d8b6f5cc169091d49caf"
      },
      {
        "path": "/data2/k6tk/fa/fa8cfa940448c4930da0d21a30dd3bceb371938011397bd2c83c0c8510bb7f5a.png",
        "sha256": "fa8cfa940448c4930da0d21a30dd3bceb371938011397bd2c83c0c8510bb7f5a"
      },
      {
        "path": "/data2/k6tk/bd/bde86b8003eacb12611922e67b569768999130c00f5866cf6868d484216c317d.png",
        "sha256": "bde86b8003eacb12611922e67b569768999130c00f5866cf6868d484216c317d"
      },
      {
        "path": "/data2/k6tk/11/1185f361fcb715ba3bd9a45218df36a3da4e5df97b720740097fae1e7af7c9a0.png",
        "sha256": "1185f361fcb715ba3bd9a45218df36a3da4e5df97b720740097fae1e7af7c9a0"
      },
      {
        "path": "/data2/k6tk/f5/f5f20275b4b72d7edb7867b5bddd5b59a9c7d908c9963c9bb7ae79e896d131e4.png",
        "sha256": "f5f20275b4b72d7edb7867b5bddd5b59a9c7d908c9963c9bb7ae79e896d131e4"
      },
      {
        "path": "/data2/k6tk/5d/5d458d2a954cc423c984843eddb65495cf994612237eee647f5629b9434052b4.png",
        "sha256": "5d458d2a954cc423c984843eddb65495cf994612237eee647f5629b9434052b4"
      },
      {
        "path": "/data2/k6tk/7c/7cb819e5970f14026298626d77945320295820c535f3f6178b81f993b290f9fc.png",
        "sha256": "7cb819e5970f14026298626d77945320295820c535f3f6178b81f993b290f9fc"
      },
      {
        "path": "/data2/k6tk/55/554ccc77b4536146a2a1a653fddcabe216a7d630a178d2e7703deb867b6e6524.png",
        "sha256": "554ccc77b4536146a2a1a653fddcabe216a7d630a178d2e7703deb867b6e6524"
      },
      {
        "path": "/data2/k6tk/b9/b9a782684c1b9df4b2edd678b5f0190a3ff4f5ed53978cf8e68f1fa4748f07fb.png",
        "sha256": "b9a782684c1b9df4b2edd678b5f0190a3ff4f5ed53978cf8e68f1fa4748f07fb"
      },
      {
        "path": "/data2/k6tk/6a/6ae931502e5bfbbca22b4d8c8c0ae05d0dbda5f4de4a9e4f6ed82119f9a6068c.png",
        "sha256": "6ae931502e5bfbbca22b4d8c8c0ae05d0dbda5f4de4a9e4f6ed82119f9a6068c"
      },
      {
        "path": "/data2/k6tk/51/5173b4cdab01624e9ad95ae3f423c34739acfa1d014d3798fb0ac5e1d7352eae.png",
        "sha256": "5173b4cdab01624e9ad95ae3f423c34739acfa1d014d3798fb0ac5e1d7352eae"
      },
      {
        "path": "/data2/k6tk/1c/1cac92268068e02615dad4937a4c002a0a3a082b504bc1bacd1c2d7d69c6f6ad.png",
        "sha256": "1cac92268068e02615dad4937a4c002a0a3a082b504bc1bacd1c2d7d69c6f6ad"
      },
      {
        "path": "/data2/k6tk/31/316e87c51f9dfb759630dfde699c99ecb85c51878aeb160c588625c162005f19.png",
        "sha256": "316e87c51f9dfb759630dfde699c99ecb85c51878aeb160c588625c162005f19"
      },
      {
        "path": "/data2/k6tk/e9/e94652628a0c27f78e7a6d0cac55f4deb2024cc788d8740fbf42024ef046db04.png",
        "sha256": "e94652628a0c27f78e7a6d0cac55f4deb2024cc788d8740fbf42024ef046db04"
      },
      {
        "path": "/data2/k6tk/8a/8ab06556fa982c3f7de5d198a1cbe1def27ae2c8832d84185230271bcd60196f.png",
        "sha256": "8ab06556fa982c3f7de5d198a1cbe1def27ae2c8832d84185230271bcd60196f"
      },
      {
        "path": "/data2/k6tk/a5/a587e54acc167214a0f12c665b92659faaebae827e798a4d2e760817e1f2bf3b.png",
        "sha256": "a587e54acc167214a0f12c665b92659faaebae827e798a4d2e760817e1f2bf3b"
      },
      {
        "path": "/data2/k6tk/a6/a67b18fb09da44778ca723c8bda3f8ec5b481ceec09490beaa3ff43457ce0660.png",
        "sha256": "a67b18fb09da44778ca723c8bda3f8ec5b481ceec09490beaa3ff43457ce0660"
      },
      {
        "path": "/data2/k6tk/f4/f4e3406e57b60fe9b9af38703bbac0ea7369d6ad88b05430c5ad20d2cb75c69b.png",
        "sha256": "f4e3406e57b60fe9b9af38703bbac0ea7369d6ad88b05430c5ad20d2cb75c69b"
      },
      {
        "path": "/data2/k6tk/11/117a65f02fbb929542aec5a20c8b9d7ac14bd9814bce0cf9e43fa80f512dc018.png",
        "sha256": "117a65f02fbb929542aec5a20c8b9d7ac14bd9814bce0cf9e43fa80f512dc018"
      },
      {
        "path": "/data2/k6tk/42/42842d683dc99eadffa4ddc048f80022d0216923513b95e6938fea2c05464d1f.png",
        "sha256": "42842d683dc99eadffa4ddc048f80022d0216923513b95e6938fea2c05464d1f"
      },
      {
        "path": "/data2/k6tk/d8/d89979f0fb6e922d129495c2ecff95738510b5505ec0d3640e5c81068a23a54f.png",
        "sha256": "d89979f0fb6e922d129495c2ecff95738510b5505ec0d3640e5c81068a23a54f"
      },
      {
        "path": "/data2/k6tk/e0/e0a05bedd9e434cb3b42fa5e6ea0e67d2f5c54591f2b29b3f9e32ce15cc113c3.png",
        "sha256": "e0a05bedd9e434cb3b42fa5e6ea0e67d2f5c54591f2b29b3f9e32ce15cc113c3"
      },
      {
        "path": "/data2/k6tk/4f/4fe2bb5cf34191df8190406159c3766de57c1b163b96e1fd72084f629e9651e3.png",
        "sha256": "4fe2bb5cf34191df8190406159c3766de57c1b163b96e1fd72084f629e9651e3"
      },
      {
        "path": "/data2/k6tk/a9/a954031e28b6170f7ecae5f3238fdc3e5bb680b9015c91579279d6731035aebb.png",
        "sha256": "a954031e28b6170f7ecae5f3238fdc3e5bb680b9015c91579279d6731035aebb"
      },
      {
        "path": "/data2/k6tk/c8/c806e9e3bc0049d1a00ad1f03eeedce36b0ba8431d8d960bf1d145aea1b0e58c.png",
        "sha256": "c806e9e3bc0049d1a00ad1f03eeedce36b0ba8431d8d960bf1d145aea1b0e58c"
      },
      {
        "path": "/data2/k6tk/e3/e3bb7c9066e29058b2ac6a232623816f940e2040d31f627fdba84c575b16fdfd.png",
        "sha256": "e3bb7c9066e29058b2ac6a232623816f940e2040d31f627fdba84c575b16fdfd"
      },
      {
        "path": "/data2/k6tk/90/905f9377ca910c79910ecc60a8efb3f5fbee3711a2a59c0b4bc7e107127963f9.png",
        "sha256": "905f9377ca910c79910ecc60a8efb3f5fbee3711a2a59c0b4bc7e107127963f9"
      },
      {
        "path": "/data2/k6tk/a3/a3054fe437a2529d75c30c92a7cbd5554633d95845254f03636a7391d6c841b4.png",
        "sha256": "a3054fe437a2529d75c30c92a7cbd5554633d95845254f03636a7391d6c841b4"
      },
      {
        "path": "/data2/k6tk/f1/f1c6663167a05c3e80fdfbcab69bba90a3d1bfced3f8a0b2754b49fc990ec449.png",
        "sha256": "f1c6663167a05c3e80fdfbcab69bba90a3d1bfced3f8a0b2754b49fc990ec449"
      },
      {
        "path": "/data2/k6tk/4c/4c4d910ae745a96ac409b131caa190a41445886243c974ece46f5562de025d25.png",
        "sha256": "4c4d910ae745a96ac409b131caa190a41445886243c974ece46f5562de025d25"
      }
    ],
    "options": [
      "A. back-right",
      "B. front-left",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the bench power supply and facing away from the chair, is the document shredder to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      5.666666666666667,
      11.333333333333334,
      17.0,
      22.666666666666668,
      28.333333333333332,
      34.0,
      39.68333333333333,
      45.35,
      51.016666666666666,
      56.68333333333333,
      62.35,
      68.01666666666667,
      73.7,
      79.36666666666666,
      85.03333333333333,
      90.7,
      96.36666666666666,
      102.03333333333333,
      107.71666666666667,
      113.38333333333334,
      119.05,
      124.71666666666667,
      130.38333333333333,
      136.05,
      141.73333333333332,
      147.4,
      153.06666666666666,
      158.73333333333332,
      164.4,
      170.06666666666666,
      175.75
    ],
    "total_num_frames": 10546
  },
  "target": "<think>\nStep 1: find the bench power supply, the chair and the document shredder.\nStep 2: standing at the bench power supply and facing the chair, I find the document shredder in front of me, on my right.\nStep 3: I face away from the chair by making a half turn. Front and back swap, and left and right swap.\nSo I find the document shredder at my back-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "6427b5bdbec566c3686684d8978a3743656ca726c50b5bad4d44a86088341a23"
  },
  "facing": "away",
  "candidate_id": "ground-6cdee218c1944308d041ba9649e0dc3c9fcb912333b0dfa87e058e57c076543a",
  "label_row_keys": [
    "qad5d9b837b70196ca57002bf"
  ]
}
```

## 27. q61318bd566f4127496300664-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q61318bd566f4127496300664-p1",
      "source_store_i": 57659,
      "source_row_sha256": "d31cf11de6378142c154fb0785fcfb18047de6f141fd675aa1297ab10b54a317",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "B",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 24,
        "end": 34,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q61318bd566f4127496300664-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vdc85a2c65681",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      685,
      1371,
      2057,
      2743,
      3429,
      4115,
      4801,
      5486,
      6172,
      6858,
      7544,
      8230,
      8916,
      9602,
      10288,
      10973,
      11659,
      12345,
      13031,
      13717,
      14403,
      15089,
      15775,
      16460,
      17146,
      17832,
      18518,
      19204,
      19890,
      20576,
      21262
    ],
    "frames": [
      {
        "path": "/data2/k6tk/45/450fbaacba7225aa93d39f452b60384a9c41d8cf7a827166bbb83f9b942647a2.png",
        "sha256": "450fbaacba7225aa93d39f452b60384a9c41d8cf7a827166bbb83f9b942647a2"
      },
      {
        "path": "/data2/k6tk/be/bec9c2cb359bc0b321b62aedef29af550fea887b4e4a922dad9e0f1c2ab1e9ca.png",
        "sha256": "bec9c2cb359bc0b321b62aedef29af550fea887b4e4a922dad9e0f1c2ab1e9ca"
      },
      {
        "path": "/data2/k6tk/9b/9bd4e596bd835cd22b683f7ad0d376dbcd45ffa488b4fc4e4b7d6ac36531ba1e.png",
        "sha256": "9bd4e596bd835cd22b683f7ad0d376dbcd45ffa488b4fc4e4b7d6ac36531ba1e"
      },
      {
        "path": "/data2/k6tk/26/266ad200f388fa4610f28914679ceea64ff0a7698f8cb2a5285df12703efa5e6.png",
        "sha256": "266ad200f388fa4610f28914679ceea64ff0a7698f8cb2a5285df12703efa5e6"
      },
      {
        "path": "/data2/k6tk/1c/1c3fe27c1aedc1725499404b593318076b369b7305456da663112889597fe4ed.png",
        "sha256": "1c3fe27c1aedc1725499404b593318076b369b7305456da663112889597fe4ed"
      },
      {
        "path": "/data2/k6tk/2a/2a2040be65846638782169d5c3a1136c9ffdda0d6cd230b676496d32330a9afc.png",
        "sha256": "2a2040be65846638782169d5c3a1136c9ffdda0d6cd230b676496d32330a9afc"
      },
      {
        "path": "/data2/k6tk/19/1945ae44e60ab907f2cf8c4aec263729ae487d3c4adec93df14a921874eca605.png",
        "sha256": "1945ae44e60ab907f2cf8c4aec263729ae487d3c4adec93df14a921874eca605"
      },
      {
        "path": "/data2/k6tk/b8/b839bcaca5476ef0f9a3f9a0bc048b9ade859dd93eb914a94aa099294e7fc212.png",
        "sha256": "b839bcaca5476ef0f9a3f9a0bc048b9ade859dd93eb914a94aa099294e7fc212"
      },
      {
        "path": "/data2/k6tk/bb/bbc491eff8fd77de777635cf56b184ecbe0dfc753f652542dab09f8534cf8a42.png",
        "sha256": "bbc491eff8fd77de777635cf56b184ecbe0dfc753f652542dab09f8534cf8a42"
      },
      {
        "path": "/data2/k6tk/b1/b117e3b49acee28adc6721a81e64ce83b7730d972f92998eb864e2a048b2ce02.png",
        "sha256": "b117e3b49acee28adc6721a81e64ce83b7730d972f92998eb864e2a048b2ce02"
      },
      {
        "path": "/data2/k6tk/e3/e3b0554be41c29c7c82217954cd24727648a0cc8a6a58ccda0afbabe27880f73.png",
        "sha256": "e3b0554be41c29c7c82217954cd24727648a0cc8a6a58ccda0afbabe27880f73"
      },
      {
        "path": "/data2/k6tk/cf/cfa0524dc3d913ea952c722e1a0ae321e4977235e28fd42659594335ec76b14e.png",
        "sha256": "cfa0524dc3d913ea952c722e1a0ae321e4977235e28fd42659594335ec76b14e"
      },
      {
        "path": "/data2/k6tk/63/63a428fd271b0aa7f84c2b400fdcbf31e40452ef21eefb05054c7d383ee3057e.png",
        "sha256": "63a428fd271b0aa7f84c2b400fdcbf31e40452ef21eefb05054c7d383ee3057e"
      },
      {
        "path": "/data2/k6tk/12/12b323c84c5e4d3c680f75397d923ef73c561f4c3b49f9fcdf3b181a94e82a95.png",
        "sha256": "12b323c84c5e4d3c680f75397d923ef73c561f4c3b49f9fcdf3b181a94e82a95"
      },
      {
        "path": "/data2/k6tk/94/94db67aa47a1f55e22df81197cdee00c74b6d47221148bb9eea4397ce1fae3ba.png",
        "sha256": "94db67aa47a1f55e22df81197cdee00c74b6d47221148bb9eea4397ce1fae3ba"
      },
      {
        "path": "/data2/k6tk/2a/2a768febf49e4dbf275d45141e2c4bb27a2c7e0bb33330adcc218799507d4e5d.png",
        "sha256": "2a768febf49e4dbf275d45141e2c4bb27a2c7e0bb33330adcc218799507d4e5d"
      },
      {
        "path": "/data2/k6tk/a6/a601d1c8f85538c1c3cf08150bfd4279bf87a3e388643a5814028723fed92b15.png",
        "sha256": "a601d1c8f85538c1c3cf08150bfd4279bf87a3e388643a5814028723fed92b15"
      },
      {
        "path": "/data2/k6tk/c3/c3115d7f8fe46aff8f94ab47262d712997e8082acac193e7a337968d128061d9.png",
        "sha256": "c3115d7f8fe46aff8f94ab47262d712997e8082acac193e7a337968d128061d9"
      },
      {
        "path": "/data2/k6tk/a9/a981c2ec8d66fdf7a4652bec46ab349c3852f727647c90239eca6b8ef1428483.png",
        "sha256": "a981c2ec8d66fdf7a4652bec46ab349c3852f727647c90239eca6b8ef1428483"
      },
      {
        "path": "/data2/k6tk/c4/c4f67bf76079b2ada2c14b16c6f0b4107feef6e9f700ce93a201390bfca96b9f.png",
        "sha256": "c4f67bf76079b2ada2c14b16c6f0b4107feef6e9f700ce93a201390bfca96b9f"
      },
      {
        "path": "/data2/k6tk/8b/8b0c94732acf67d309f3b7eceb4b4c84170a3d1605814e48262d19acbebff334.png",
        "sha256": "8b0c94732acf67d309f3b7eceb4b4c84170a3d1605814e48262d19acbebff334"
      },
      {
        "path": "/data2/k6tk/25/25b8d337695c6a733694ca343eadd086d29bc57e38dd14e85e1c623876ded744.png",
        "sha256": "25b8d337695c6a733694ca343eadd086d29bc57e38dd14e85e1c623876ded744"
      },
      {
        "path": "/data2/k6tk/37/37031f9a09ef31b986e8cf9cb7049a92a1d0cbb770360f587a4b83b12c791916.png",
        "sha256": "37031f9a09ef31b986e8cf9cb7049a92a1d0cbb770360f587a4b83b12c791916"
      },
      {
        "path": "/data2/k6tk/a4/a452f918b34c9df8cf4b5f1caac34291edb533e586eec4b66390c1fb3f8e656e.png",
        "sha256": "a452f918b34c9df8cf4b5f1caac34291edb533e586eec4b66390c1fb3f8e656e"
      },
      {
        "path": "/data2/k6tk/79/79342c00cb43833417f422b245fd334e8b2d4ced4fa78e842c683bec0d628333.png",
        "sha256": "79342c00cb43833417f422b245fd334e8b2d4ced4fa78e842c683bec0d628333"
      },
      {
        "path": "/data2/k6tk/a8/a88acc0f78803a4def10306ea3a1aa9441b2fc69e1a40d9aa33afa420bf29130.png",
        "sha256": "a88acc0f78803a4def10306ea3a1aa9441b2fc69e1a40d9aa33afa420bf29130"
      },
      {
        "path": "/data2/k6tk/d8/d865fea3bc7a8737c4137eb745afa48e6e7186653ab922c38be9bf05bf476282.png",
        "sha256": "d865fea3bc7a8737c4137eb745afa48e6e7186653ab922c38be9bf05bf476282"
      },
      {
        "path": "/data2/k6tk/7d/7da401f17731d4fdf75b978075bcad05cadb6c61f40c009185e6d31ae87c6ff5.png",
        "sha256": "7da401f17731d4fdf75b978075bcad05cadb6c61f40c009185e6d31ae87c6ff5"
      },
      {
        "path": "/data2/k6tk/29/29c67b616bdf9c1af9549bdfe8a6e41e035bfad7b9fbf4a9aaa063edcf9efa06.png",
        "sha256": "29c67b616bdf9c1af9549bdfe8a6e41e035bfad7b9fbf4a9aaa063edcf9efa06"
      },
      {
        "path": "/data2/k6tk/be/beb427c2cc03d726f8866ef2d0a0447f03ac572ac5e5ed6b106e9f72c9d06618.png",
        "sha256": "beb427c2cc03d726f8866ef2d0a0447f03ac572ac5e5ed6b106e9f72c9d06618"
      },
      {
        "path": "/data2/k6tk/d0/d0252a0eb779ace25f9f8498239b77c45ff11f9a6cb9cc0d15feecd2f56927bd.png",
        "sha256": "d0252a0eb779ace25f9f8498239b77c45ff11f9a6cb9cc0d15feecd2f56927bd"
      },
      {
        "path": "/data2/k6tk/2e/2e6f41145517ce79219d37e1061f542a121a7802a11975188482c2fbdf89d898.png",
        "sha256": "2e6f41145517ce79219d37e1061f542a121a7802a11975188482c2fbdf89d898"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-left",
      "D. back-right"
    ],
    "question": "I stand by the backpack facing away from the bed. Where is the basketball relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      11.416666666666666,
      22.85,
      34.28333333333333,
      45.71666666666667,
      57.15,
      68.58333333333333,
      80.01666666666667,
      91.43333333333334,
      102.86666666666666,
      114.3,
      125.73333333333333,
      137.16666666666666,
      148.6,
      160.03333333333333,
      171.46666666666667,
      182.88333333333333,
      194.31666666666666,
      205.75,
      217.18333333333334,
      228.61666666666667,
      240.05,
      251.48333333333332,
      262.9166666666667,
      274.3333333333333,
      285.76666666666665,
      297.2,
      308.6333333333333,
      320.06666666666666,
      331.5,
      342.93333333333334,
      354.3666666666667
    ],
    "total_num_frames": 21263
  },
  "target": "<think>\nStep 1: find the backpack, the bed and the basketball.\nStep 2: I find the basketball in front of me, on my right when I stand at the backpack facing the bed.\nStep 3: I face away from the bed by making a half turn. Front and back swap, and left and right swap.\nSo I find the basketball at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q61318bd566f4127496300664",
  "paraphrase_template": "hard_viewpoint",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "4006afc214584599aeb6eddf4cfaa9d78007399b7224f91f2b7e9427471bad91"
  },
  "facing": "away",
  "candidate_id": "ground-d0b7164fe6c0e3340e9d8512fbd27d2b35e357cbffce0e865d33d99008d7dde9",
  "label_row_keys": [
    "q61318bd566f4127496300664-p1"
  ]
}
```

## 28. q3023fb05a2470f09fad98ad1-p1_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q3023fb05a2470f09fad98ad1-p1",
      "source_store_i": 77484,
      "source_row_sha256": "b6961a9c2ea007f89c2ae2f2d967d24351398c993b7a84fc9a877bf65a614da8",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 36,
        "end": 42,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q3023fb05a2470f09fad98ad1-p1_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
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
    "options": [
      "A. front-right",
      "B. front-left",
      "C. back-right",
      "D. back-left"
    ],
    "question": "If I am standing beside the box and facing away from the cable, which direction describes the electric kettle relative to me: front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
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
  "target": "<think>\nStep 1: find the box, the cable and the electric kettle.\nStep 2: facing the cable from the box, I find the electric kettle in front of me, on my right.\nStep 3: I face away from the cable by making a half turn. Front and back swap, and left and right swap.\nSo I find the electric kettle at my back-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "paraphrase_of": "q3023fb05a2470f09fad98ad1",
  "paraphrase_template": "hard_vsi",
  "trace_quotes_question": false,
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "bae9e7ce418520eb046da47e08e4dc735695d33f7326ceb1a9a33906ab190d44"
  },
  "facing": "away",
  "candidate_id": "ground-2b2b165f43f00ec36b39a96bed81f5e0efc92c3acf060d088a2a17603b5ff9a1",
  "label_row_keys": [
    "q3023fb05a2470f09fad98ad1-p1"
  ]
}
```

## 29. q0888327c51ffc3f68380ec13_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "q0888327c51ffc3f68380ec13",
      "source_store_i": 20634,
      "source_row_sha256": "5a31d8a0961a0452fc83f5d392f32e58e485b6236e6ef5388c3fbace71ed1f50",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "A",
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "q0888327c51ffc3f68380ec13_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v147fd0cb0fd6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      408,
      816,
      1224,
      1632,
      2040,
      2448,
      2856,
      3264,
      3672,
      4080,
      4488,
      4896,
      5304,
      5712,
      6120,
      6528,
      6936,
      7344,
      7752,
      8160,
      8568,
      8976,
      9384,
      9792,
      10200,
      10608,
      11016,
      11424,
      11832,
      12240,
      12649
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ee/eeca760e768137c373410bfed502b35ca0750723e0d2864120911da08166a206.png",
        "sha256": "eeca760e768137c373410bfed502b35ca0750723e0d2864120911da08166a206"
      },
      {
        "path": "/data2/k6tk/40/4061a310270e7c68e74dcd777211acd8583eafd29d4826fb913db82427b56ea1.png",
        "sha256": "4061a310270e7c68e74dcd777211acd8583eafd29d4826fb913db82427b56ea1"
      },
      {
        "path": "/data2/k6tk/b2/b2e94609700dd3bb1515de49ac99035e941c1ef3d093f8c500ae3d040448d88f.png",
        "sha256": "b2e94609700dd3bb1515de49ac99035e941c1ef3d093f8c500ae3d040448d88f"
      },
      {
        "path": "/data2/k6tk/29/2912531a7f5453e2ede4ed85b5d28c887988f52dac6020c262b572d53049c646.png",
        "sha256": "2912531a7f5453e2ede4ed85b5d28c887988f52dac6020c262b572d53049c646"
      },
      {
        "path": "/data2/k6tk/b6/b6e5007f899bc5a4b05280b063f2dcc2eb496102ac9f08e00d3b63f52206b95e.png",
        "sha256": "b6e5007f899bc5a4b05280b063f2dcc2eb496102ac9f08e00d3b63f52206b95e"
      },
      {
        "path": "/data2/k6tk/68/68e63884e8217c20cc267eac1a6eef60c3efb2ff36faa5608bdacf15261f5c71.png",
        "sha256": "68e63884e8217c20cc267eac1a6eef60c3efb2ff36faa5608bdacf15261f5c71"
      },
      {
        "path": "/data2/k6tk/bd/bda8a9e3c4a2fe89c87df8a4954a13c2fbe991b1d0f6ea8150257e1653f3f9bd.png",
        "sha256": "bda8a9e3c4a2fe89c87df8a4954a13c2fbe991b1d0f6ea8150257e1653f3f9bd"
      },
      {
        "path": "/data2/k6tk/7b/7b519759fd2f6bb3c90e91e24f0445bfacf003c08413b2fa19dd88eb0873b297.png",
        "sha256": "7b519759fd2f6bb3c90e91e24f0445bfacf003c08413b2fa19dd88eb0873b297"
      },
      {
        "path": "/data2/k6tk/e2/e22cfa44a8fd4f8d0ccd3c1713dac0bda4596b04ec64973ea010b6813115c648.png",
        "sha256": "e22cfa44a8fd4f8d0ccd3c1713dac0bda4596b04ec64973ea010b6813115c648"
      },
      {
        "path": "/data2/k6tk/2f/2f649391910814afdb899a975fbe8e3ae01a523d962892d5859e817b51dac9c1.png",
        "sha256": "2f649391910814afdb899a975fbe8e3ae01a523d962892d5859e817b51dac9c1"
      },
      {
        "path": "/data2/k6tk/9a/9a7dcb4c6a99b6be44d6f93ecdd8c060b7daa1000577a87a871396226f63a2d7.png",
        "sha256": "9a7dcb4c6a99b6be44d6f93ecdd8c060b7daa1000577a87a871396226f63a2d7"
      },
      {
        "path": "/data2/k6tk/00/00ce97c198cf8dcca358844593f24492bb9520fe664c72c905ee2ad3630c298e.png",
        "sha256": "00ce97c198cf8dcca358844593f24492bb9520fe664c72c905ee2ad3630c298e"
      },
      {
        "path": "/data2/k6tk/da/da7df4f26c55a8d6186d48f6892b1809117e4f09c56088381a16fc90e5147f9e.png",
        "sha256": "da7df4f26c55a8d6186d48f6892b1809117e4f09c56088381a16fc90e5147f9e"
      },
      {
        "path": "/data2/k6tk/c5/c5b93d1eaee68e6c4df8316948046a8742568ffa4d78c478ce7165ca85d4ade6.png",
        "sha256": "c5b93d1eaee68e6c4df8316948046a8742568ffa4d78c478ce7165ca85d4ade6"
      },
      {
        "path": "/data2/k6tk/c7/c7b075af6177a2d64fa2778d86cbd58a15fdf86f5293ee7483f33c4db3ef78d8.png",
        "sha256": "c7b075af6177a2d64fa2778d86cbd58a15fdf86f5293ee7483f33c4db3ef78d8"
      },
      {
        "path": "/data2/k6tk/19/19538726d65cca0653113aae5dd2b16dabef5787275b677097245eb0761c127f.png",
        "sha256": "19538726d65cca0653113aae5dd2b16dabef5787275b677097245eb0761c127f"
      },
      {
        "path": "/data2/k6tk/cc/cc8df5f8ab0869f9309f81bf9766702abd104aef2461622180645e846b2dc9b5.png",
        "sha256": "cc8df5f8ab0869f9309f81bf9766702abd104aef2461622180645e846b2dc9b5"
      },
      {
        "path": "/data2/k6tk/47/477f49970eb49cfdd432681265ee04f5201cdfa814c87e0482b5bab260b48649.png",
        "sha256": "477f49970eb49cfdd432681265ee04f5201cdfa814c87e0482b5bab260b48649"
      },
      {
        "path": "/data2/k6tk/f0/f0ecbd722ce51bea79da98d47c6be30c2f94b57b99f27e21677b4e14c720d6dc.png",
        "sha256": "f0ecbd722ce51bea79da98d47c6be30c2f94b57b99f27e21677b4e14c720d6dc"
      },
      {
        "path": "/data2/k6tk/44/446ecc37ac91b9eae22d00346ba8d6bb74884c415fafda875cb552a9c65b0a7b.png",
        "sha256": "446ecc37ac91b9eae22d00346ba8d6bb74884c415fafda875cb552a9c65b0a7b"
      },
      {
        "path": "/data2/k6tk/5c/5c3bd5bfbd2f7d403f472a6d48c08ef627e63678b2da7a6a1e4a082990d75354.png",
        "sha256": "5c3bd5bfbd2f7d403f472a6d48c08ef627e63678b2da7a6a1e4a082990d75354"
      },
      {
        "path": "/data2/k6tk/f4/f496ff53aae7ffb3a99e8220596b56f9f31369666b3289a8ef31489debb23c08.png",
        "sha256": "f496ff53aae7ffb3a99e8220596b56f9f31369666b3289a8ef31489debb23c08"
      },
      {
        "path": "/data2/k6tk/c3/c3b760a418538a404b4934c619228fcd4e50b38a2f38d2c7da09effb8e063aa8.png",
        "sha256": "c3b760a418538a404b4934c619228fcd4e50b38a2f38d2c7da09effb8e063aa8"
      },
      {
        "path": "/data2/k6tk/a1/a185a2b4cd632c79891b833e92c8149f746c5effd751301bea2db12da602fb7f.png",
        "sha256": "a185a2b4cd632c79891b833e92c8149f746c5effd751301bea2db12da602fb7f"
      },
      {
        "path": "/data2/k6tk/a6/a6b4ef6f6a1c080c646677917d3a686f927695e085c8e60cb42cd2724b226d31.png",
        "sha256": "a6b4ef6f6a1c080c646677917d3a686f927695e085c8e60cb42cd2724b226d31"
      },
      {
        "path": "/data2/k6tk/84/849d7c63ee4d4e113c329293d7d839c386f38e9a73f09a029b47a90ae3da1cf7.png",
        "sha256": "849d7c63ee4d4e113c329293d7d839c386f38e9a73f09a029b47a90ae3da1cf7"
      },
      {
        "path": "/data2/k6tk/54/54c56dba4ae12bd122670ba00fe04d5275af95bb5be3be9e85605512607c4d1d.png",
        "sha256": "54c56dba4ae12bd122670ba00fe04d5275af95bb5be3be9e85605512607c4d1d"
      },
      {
        "path": "/data2/k6tk/26/260d82ffaa702c9b4e5d89ffd8ddb649f9771a95f4d33d8e3b14df8ef1033d2a.png",
        "sha256": "260d82ffaa702c9b4e5d89ffd8ddb649f9771a95f4d33d8e3b14df8ef1033d2a"
      },
      {
        "path": "/data2/k6tk/d9/d9814c47e35f01a78eab4f64d010b2cf460cf27c1762f4d6046bdec2254ccf9c.png",
        "sha256": "d9814c47e35f01a78eab4f64d010b2cf460cf27c1762f4d6046bdec2254ccf9c"
      },
      {
        "path": "/data2/k6tk/00/0001e2e4182a2fce2f900190ce129faec540219dfdaf74c3956207a74dcb357b.png",
        "sha256": "0001e2e4182a2fce2f900190ce129faec540219dfdaf74c3956207a74dcb357b"
      },
      {
        "path": "/data2/k6tk/d5/d54292872bf80778214435fbd08e1c2d01a9bf796aae382fa386661faf436d44.png",
        "sha256": "d54292872bf80778214435fbd08e1c2d01a9bf796aae382fa386661faf436d44"
      },
      {
        "path": "/data2/k6tk/07/072336e10e8c5ebc529c03928302c20b4b0ecca0326d5c0bb71ec33a46429d93.png",
        "sha256": "072336e10e8c5ebc529c03928302c20b4b0ecca0326d5c0bb71ec33a46429d93"
      }
    ],
    "options": [
      "A. front-right",
      "B. front-left",
      "C. back-left",
      "D. back-right"
    ],
    "question": "If I am standing by the bed and facing away from the clothes iron, is the light switch to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      6.8,
      13.6,
      20.4,
      27.2,
      34.0,
      40.8,
      47.6,
      54.4,
      61.2,
      68.0,
      74.8,
      81.6,
      88.4,
      95.2,
      102.0,
      108.8,
      115.6,
      122.4,
      129.2,
      136.0,
      142.8,
      149.6,
      156.4,
      163.2,
      170.0,
      176.8,
      183.6,
      190.4,
      197.2,
      204.0,
      210.81666666666666
    ],
    "total_num_frames": 12650
  },
  "target": "<think>\nStep 1: find the bed, the clothes iron and the light switch.\nStep 2: standing at the bed and facing the clothes iron, I find the light switch in front of me, on my right.\nStep 3: I face away from the clothes iron by making a half turn. Front and back swap, and left and right swap.\nSo I find the light switch at my back-left.\n</think>\n\nC",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "c8da8831a0f1c0f1b8919b20fd35e1ea50a96f950a1d09a8a7ba62f2c72f1d9b"
  },
  "facing": "away",
  "candidate_id": "ground-0be794daf3f6406d95566a286d476815190ece3a48e2db4525876b09b031a409",
  "label_row_keys": [
    "q0888327c51ffc3f68380ec13"
  ]
}
```

## 30. qce10ab35ff9be02a9413cc82_sb_rowD7_a

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
  "pool": "sb_rowD7",
  "provenance": {
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
    "gt_kind": "gt_canonical_trace",
    "source": "/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_direction_hard.jsonl.gz",
    "source_kind": "weak_data_canonical_trace_pack",
    "view_labels": "frame_numbers",
    "sb_rowD7": {
      "source_qid": "qce10ab35ff9be02a9413cc82",
      "source_store_i": 34371,
      "source_row_sha256": "7271949bed317ba07289e30f9d95109ca9d7242e968e1e747ece6c03ee70fcee",
      "branch": "a",
      "rule": "rows_r1_easy_hard_bijective_half_turn",
      "input_sha256": {
        "/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite": "210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443"
      },
      "source_answer": "C",
      "source_label": "front-right",
      "mapped_label": "back-left",
      "clause_edit": {
        "start": 43,
        "end": 49,
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
      "generator_sha256": "2822cefb30b42e09eab73cb9a3afebc90762f6aae01beea10f2aecb296c871fa"
    }
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "qce10ab35ff9be02a9413cc82_sb_rowD7_a",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vb9aef696c367",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      52,
      105,
      158,
      211,
      264,
      317,
      370,
      423,
      476,
      529,
      582,
      635,
      688,
      741,
      794,
      847,
      900,
      953,
      1006,
      1059,
      1112,
      1165,
      1218,
      1271,
      1324,
      1377,
      1430,
      1483,
      1536,
      1589,
      1642
    ],
    "frames": [
      {
        "path": "/data2/k6tk/4b/4b4999cd64fae5406ee4426a2ff11bbafedde039f6db21c1da0819e1d2ea3edd.png",
        "sha256": "4b4999cd64fae5406ee4426a2ff11bbafedde039f6db21c1da0819e1d2ea3edd"
      },
      {
        "path": "/data2/k6tk/73/734f00184f0cfc4fd357d4a9b63396a623f1a5d74b9407123cd52173c3402649.png",
        "sha256": "734f00184f0cfc4fd357d4a9b63396a623f1a5d74b9407123cd52173c3402649"
      },
      {
        "path": "/data2/k6tk/c9/c936e5a3f2409bbb78a365596929a1e6a58c276783831ba675498ddd9f1c3e7c.png",
        "sha256": "c936e5a3f2409bbb78a365596929a1e6a58c276783831ba675498ddd9f1c3e7c"
      },
      {
        "path": "/data2/k6tk/cc/cc9ac5cee51ccc742b837b4330c106133bc71aae37c2e290b1b08ab83254b28f.png",
        "sha256": "cc9ac5cee51ccc742b837b4330c106133bc71aae37c2e290b1b08ab83254b28f"
      },
      {
        "path": "/data2/k6tk/39/3958915619802d8e777585ba516c901ad0541bdefbf0661d0d6af37883e3f4e4.png",
        "sha256": "3958915619802d8e777585ba516c901ad0541bdefbf0661d0d6af37883e3f4e4"
      },
      {
        "path": "/data2/k6tk/44/44019fa03d4eb70c63f949902bde8b209c12cf9a6128e1b689d452f691262c79.png",
        "sha256": "44019fa03d4eb70c63f949902bde8b209c12cf9a6128e1b689d452f691262c79"
      },
      {
        "path": "/data2/k6tk/33/33bd672dc7f8a5f2ea70b01933bcb9a2f3e810517ee8e67bdc310ed324828636.png",
        "sha256": "33bd672dc7f8a5f2ea70b01933bcb9a2f3e810517ee8e67bdc310ed324828636"
      },
      {
        "path": "/data2/k6tk/cd/cde0eed3f7a892a9a9200c9ab564d771cbea0c7021c6143dc211ad5c1f9c716f.png",
        "sha256": "cde0eed3f7a892a9a9200c9ab564d771cbea0c7021c6143dc211ad5c1f9c716f"
      },
      {
        "path": "/data2/k6tk/5d/5dc644b9448a1c8f95335bbcac9ccf4d38a9a7f0296651e9a5b72b1d2e65ae7b.png",
        "sha256": "5dc644b9448a1c8f95335bbcac9ccf4d38a9a7f0296651e9a5b72b1d2e65ae7b"
      },
      {
        "path": "/data2/k6tk/c8/c84935960fbef16a9ac720d63f8665a4cd23be924ebe3cad9b2daac4432d196d.png",
        "sha256": "c84935960fbef16a9ac720d63f8665a4cd23be924ebe3cad9b2daac4432d196d"
      },
      {
        "path": "/data2/k6tk/f0/f0349c6171211902252d6ccca5a402e018adb163c03adcc648468c6cf1379c7a.png",
        "sha256": "f0349c6171211902252d6ccca5a402e018adb163c03adcc648468c6cf1379c7a"
      },
      {
        "path": "/data2/k6tk/00/009e1010198c78089ca97e56caf8701c73bea1ac7a4267a3cf421e22a828485e.png",
        "sha256": "009e1010198c78089ca97e56caf8701c73bea1ac7a4267a3cf421e22a828485e"
      },
      {
        "path": "/data2/k6tk/82/82180a0da93623b543e56ca3f29c83d62002c6971556bc23def24ebb271f89de.png",
        "sha256": "82180a0da93623b543e56ca3f29c83d62002c6971556bc23def24ebb271f89de"
      },
      {
        "path": "/data2/k6tk/82/82ead0a416c083727fb6c86b84830a311513a83647615e87834a7c773a12d6e4.png",
        "sha256": "82ead0a416c083727fb6c86b84830a311513a83647615e87834a7c773a12d6e4"
      },
      {
        "path": "/data2/k6tk/86/86ad687cf65ec74e00cc012a4f93169654477b955ff675d36fc579289d9a8bb7.png",
        "sha256": "86ad687cf65ec74e00cc012a4f93169654477b955ff675d36fc579289d9a8bb7"
      },
      {
        "path": "/data2/k6tk/cd/cd25f01865a7c243af2e57c155802f334fd69a50c9c1c592a7347845091902b1.png",
        "sha256": "cd25f01865a7c243af2e57c155802f334fd69a50c9c1c592a7347845091902b1"
      },
      {
        "path": "/data2/k6tk/ac/ac4515aaf461c305a655b8b0581779295a49c9f6f316fd24d348fca86e5afbb5.png",
        "sha256": "ac4515aaf461c305a655b8b0581779295a49c9f6f316fd24d348fca86e5afbb5"
      },
      {
        "path": "/data2/k6tk/3a/3a764ee92322334e6f8bc5543635a68c4390e19aa4c828975bbbc6d8dfc26425.png",
        "sha256": "3a764ee92322334e6f8bc5543635a68c4390e19aa4c828975bbbc6d8dfc26425"
      },
      {
        "path": "/data2/k6tk/e0/e0a6a1c229a079961834b992722e3ea106df6d62886f458ad81003a38f0ce790.png",
        "sha256": "e0a6a1c229a079961834b992722e3ea106df6d62886f458ad81003a38f0ce790"
      },
      {
        "path": "/data2/k6tk/3f/3f9097db1ffe3a1acc22d0934a53817b0a5dbd27244a27d9e7f7d4a520340b14.png",
        "sha256": "3f9097db1ffe3a1acc22d0934a53817b0a5dbd27244a27d9e7f7d4a520340b14"
      },
      {
        "path": "/data2/k6tk/81/810dd68ab766c49b9eb2eb866592bd522d81a9f9f3e8cd8e41485cfb8d7cf857.png",
        "sha256": "810dd68ab766c49b9eb2eb866592bd522d81a9f9f3e8cd8e41485cfb8d7cf857"
      },
      {
        "path": "/data2/k6tk/c5/c5b02bf40a17ed824216a909adac49d263242ec0248529796e6411b4464330fa.png",
        "sha256": "c5b02bf40a17ed824216a909adac49d263242ec0248529796e6411b4464330fa"
      },
      {
        "path": "/data2/k6tk/4f/4fe1f4b8f66623587c0855223ab129a602ebcfc5f33780f56dcb673f79307c52.png",
        "sha256": "4fe1f4b8f66623587c0855223ab129a602ebcfc5f33780f56dcb673f79307c52"
      },
      {
        "path": "/data2/k6tk/09/0922e57380caf6d563592ead099db1284bff3d6c8e1431b3d3d60ee636d04ef2.png",
        "sha256": "0922e57380caf6d563592ead099db1284bff3d6c8e1431b3d3d60ee636d04ef2"
      },
      {
        "path": "/data2/k6tk/ff/ff20de33a525e75275b6649e23a3e859f62b6bf0cfd0816be91945b7e0134e36.png",
        "sha256": "ff20de33a525e75275b6649e23a3e859f62b6bf0cfd0816be91945b7e0134e36"
      },
      {
        "path": "/data2/k6tk/df/dfbbda0de370a45bc0de5bff5b394a585c682d87a2eb19c0e9ef7947234e1fcd.png",
        "sha256": "dfbbda0de370a45bc0de5bff5b394a585c682d87a2eb19c0e9ef7947234e1fcd"
      },
      {
        "path": "/data2/k6tk/e7/e797cad243fce28e4241f0a16867060f22f22e5c911896d2e6cb0daf99be3d15.png",
        "sha256": "e797cad243fce28e4241f0a16867060f22f22e5c911896d2e6cb0daf99be3d15"
      },
      {
        "path": "/data2/k6tk/78/78bad9d23e61f75ffa337c1349912ce7a79a87c8aab7afc8a1916053761bcf40.png",
        "sha256": "78bad9d23e61f75ffa337c1349912ce7a79a87c8aab7afc8a1916053761bcf40"
      },
      {
        "path": "/data2/k6tk/3b/3bcd2b1cb409cd66ca392b4f0597bcc30a30924755815d4d89ac65656860908e.png",
        "sha256": "3bcd2b1cb409cd66ca392b4f0597bcc30a30924755815d4d89ac65656860908e"
      },
      {
        "path": "/data2/k6tk/f6/f6dfb9da9ed73bf5a747a0ef35fc97c00aa5ed09f985bcfe9524bdfc7f2c363c.png",
        "sha256": "f6dfb9da9ed73bf5a747a0ef35fc97c00aa5ed09f985bcfe9524bdfc7f2c363c"
      },
      {
        "path": "/data2/k6tk/38/380dd3d074fdc0d245ce72931e72c6cfd0dad642e5bf9a43d710166d16f71ac6.png",
        "sha256": "380dd3d074fdc0d245ce72931e72c6cfd0dad642e5bf9a43d710166d16f71ac6"
      },
      {
        "path": "/data2/k6tk/8a/8a3a11d4b5b5896bde3b4d485ba81546660b1319c02da9440464768085afe7fd.png",
        "sha256": "8a3a11d4b5b5896bde3b4d485ba81546660b1319c02da9440464768085afe7fd"
      }
    ],
    "options": [
      "A. front-left",
      "B. back-right",
      "C. front-right",
      "D. back-left"
    ],
    "question": "If I am standing by the clothes dryers and facing away from the clothing, is the trash bin to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.1666666666666665,
      4.375,
      6.583333333333333,
      8.791666666666666,
      11.0,
      13.208333333333334,
      15.416666666666666,
      17.625,
      19.833333333333332,
      22.041666666666668,
      24.25,
      26.458333333333332,
      28.666666666666668,
      30.875,
      33.083333333333336,
      35.291666666666664,
      37.5,
      39.708333333333336,
      41.916666666666664,
      44.125,
      46.333333333333336,
      48.541666666666664,
      50.75,
      52.958333333333336,
      55.166666666666664,
      57.375,
      59.583333333333336,
      61.791666666666664,
      64.0,
      66.20833333333333,
      68.41666666666667
    ],
    "total_num_frames": 1643
  },
  "target": "<think>\nStep 1: find the clothes dryers, the clothing and the trash bin.\nStep 2: I find the trash bin in front of me, on my right when I stand at the clothes dryers facing the clothing.\nStep 3: I face away from the clothing by making a half turn. Front and back swap, and left and right swap.\nSo I find the trash bin at my back-left.\n</think>\n\nD",
  "validation_commit": "73934511aff5dac8af4b3b12490a88762105dc24",
  "retrace": {
    "rule": "rows_rebuild_d0_v1",
    "source_target_sha256": "eea378ef899220ef4a5128e53c50e52eeecc92bad4949db2740facf5f9033a08"
  },
  "facing": "away",
  "candidate_id": "ground-9f29a180a71c2e8e38b8afdd2833ac5c3ae542508c1282f008b873071e80c501",
  "label_row_keys": [
    "qce10ab35ff9be02a9413cc82"
  ]
}
```

