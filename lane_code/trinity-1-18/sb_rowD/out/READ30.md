# Thirty complete source rows

These are unchanged audit inputs, not replacement training rows. The first 30 rows of the seeded sample are printed in full.

### Sample 1: vsi590k_147870_away_opp

Store index: 199240. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the table, is the blanket to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: door in frame 1; table in frame 21; blanket in frame 14.
If I stood at the door facing the table, the blanket would be to my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the blanket to my left.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_147870",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 117757,
      "derived_from_v6_qid": "vsi590k_147870_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "513c83c19bd82d56a23e160ea1ca9c1805351c2b03fd86bf7fe6f4a13385315c",
      "source_target_sha256": "9d3c82398787a5dcf1416bda04f94d6191d16bdd80b157937b2342abf2fc6b81",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_147870",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_147870_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v459400aea18e",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_147870",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      470,
      940,
      1410,
      1880,
      2351,
      2821,
      3291,
      3761,
      4232,
      4702,
      5172,
      5642,
      6112,
      6583,
      7053,
      7523,
      7993,
      8464,
      8934,
      9404,
      9874,
      10344,
      10815,
      11285,
      11755,
      12225,
      12696,
      13166,
      13636,
      14106,
      14577
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a1/a1c8644362e5e455d9567416046087c6ec76f58e6c6713c7c272b27d9abe5837.png",
        "sha256": "a1c8644362e5e455d9567416046087c6ec76f58e6c6713c7c272b27d9abe5837"
      },
      {
        "path": "/data2/k6tk/f9/f93d1718ca4842972cd886725802f64081b09c15900e1534128da96b56da97db.png",
        "sha256": "f93d1718ca4842972cd886725802f64081b09c15900e1534128da96b56da97db"
      },
      {
        "path": "/data2/k6tk/e4/e4c693c19160a11c47d278b48128f988a919b90cf2d78d927f24711a4d39c0e2.png",
        "sha256": "e4c693c19160a11c47d278b48128f988a919b90cf2d78d927f24711a4d39c0e2"
      },
      {
        "path": "/data2/k6tk/43/43d9636c2aa2ce654d4c10cac31aadea5bb6913b6b8e53ed2ca0f87c34fb44a8.png",
        "sha256": "43d9636c2aa2ce654d4c10cac31aadea5bb6913b6b8e53ed2ca0f87c34fb44a8"
      },
      {
        "path": "/data2/k6tk/22/225ea624baf35c3c6d3fa0d9c3807011a27f38dcc2710fc81c76addedbc0aa49.png",
        "sha256": "225ea624baf35c3c6d3fa0d9c3807011a27f38dcc2710fc81c76addedbc0aa49"
      },
      {
        "path": "/data2/k6tk/16/16195b450263af0b0fb723f01ae816f2953ef307d3d6e1cfa230bec7b0607d8e.png",
        "sha256": "16195b450263af0b0fb723f01ae816f2953ef307d3d6e1cfa230bec7b0607d8e"
      },
      {
        "path": "/data2/k6tk/7f/7fa4130898c01e68fc5ba9268908302160f5cda336ce09a0b5356826d7c168a7.png",
        "sha256": "7fa4130898c01e68fc5ba9268908302160f5cda336ce09a0b5356826d7c168a7"
      },
      {
        "path": "/data2/k6tk/88/88955128333d1e5d902d14144f55b792418ecdfaeb7cde3bc568fcc76f549de9.png",
        "sha256": "88955128333d1e5d902d14144f55b792418ecdfaeb7cde3bc568fcc76f549de9"
      },
      {
        "path": "/data2/k6tk/0e/0eba9b6108611c4ad73e0bdd12974999d90a85640e60edf985e7d7d114f27c2e.png",
        "sha256": "0eba9b6108611c4ad73e0bdd12974999d90a85640e60edf985e7d7d114f27c2e"
      },
      {
        "path": "/data2/k6tk/f2/f2c706b5b884a1d1e5494821823e653fb34f301b971b33c128c4015b11a42790.png",
        "sha256": "f2c706b5b884a1d1e5494821823e653fb34f301b971b33c128c4015b11a42790"
      },
      {
        "path": "/data2/k6tk/19/19b07343811127e1af0e253f9e14b458157b7b0b292c2130ecb527bc91014537.png",
        "sha256": "19b07343811127e1af0e253f9e14b458157b7b0b292c2130ecb527bc91014537"
      },
      {
        "path": "/data2/k6tk/b8/b810ecd90f4d6e007953d57dc3d1aa415489b7dc5062f6f0fc9ab59476f246b3.png",
        "sha256": "b810ecd90f4d6e007953d57dc3d1aa415489b7dc5062f6f0fc9ab59476f246b3"
      },
      {
        "path": "/data2/k6tk/66/66edd321cb624b5457de48ac90835789c4afd4fb58472ee63eb71469994c8db9.png",
        "sha256": "66edd321cb624b5457de48ac90835789c4afd4fb58472ee63eb71469994c8db9"
      },
      {
        "path": "/data2/k6tk/e4/e4a6089f308fd17ff5667d88c0295a280cb83088cfbb37674b81aa9d7fb151e8.png",
        "sha256": "e4a6089f308fd17ff5667d88c0295a280cb83088cfbb37674b81aa9d7fb151e8"
      },
      {
        "path": "/data2/k6tk/ed/eda2003f5b219e34ea954726106b462b67faf367f5659a48d4989433a5631b89.png",
        "sha256": "eda2003f5b219e34ea954726106b462b67faf367f5659a48d4989433a5631b89"
      },
      {
        "path": "/data2/k6tk/50/5020386b31eace304a6da1f42b411c20f8ef58d78af3cdcf3c9ca2495264f768.png",
        "sha256": "5020386b31eace304a6da1f42b411c20f8ef58d78af3cdcf3c9ca2495264f768"
      },
      {
        "path": "/data2/k6tk/07/07fd68bb79416e1c1d4766f40f28f8c451021b1856520941a49ee42eff22a903.png",
        "sha256": "07fd68bb79416e1c1d4766f40f28f8c451021b1856520941a49ee42eff22a903"
      },
      {
        "path": "/data2/k6tk/2c/2c15f4404fca94ae7b1d646c00f181aa076868d34e27eb758d8fe585ebe2362a.png",
        "sha256": "2c15f4404fca94ae7b1d646c00f181aa076868d34e27eb758d8fe585ebe2362a"
      },
      {
        "path": "/data2/k6tk/70/707e1d6df44c255f0b0ff4bae30e16de1cb8fe2133bb5ddddba322da89b95c42.png",
        "sha256": "707e1d6df44c255f0b0ff4bae30e16de1cb8fe2133bb5ddddba322da89b95c42"
      },
      {
        "path": "/data2/k6tk/26/26a819847e17aa913fb4703c30d7f97bb838aa8ae85a1a81c9555c6d020da418.png",
        "sha256": "26a819847e17aa913fb4703c30d7f97bb838aa8ae85a1a81c9555c6d020da418"
      },
      {
        "path": "/data2/k6tk/6e/6eaac2131720039cc30ab17f9f70efb483bc81a06bb2d3ba98c5be511e67ce76.png",
        "sha256": "6eaac2131720039cc30ab17f9f70efb483bc81a06bb2d3ba98c5be511e67ce76"
      },
      {
        "path": "/data2/k6tk/95/956f1ca5f210a32cd91e278dc2c8a46c91de2d2c57c6967e75775eac2f06e7c7.png",
        "sha256": "956f1ca5f210a32cd91e278dc2c8a46c91de2d2c57c6967e75775eac2f06e7c7"
      },
      {
        "path": "/data2/k6tk/cf/cfc6b7e03d838a2f3048dedd0b03ebe595870fe2d687e50d013fd6c68d9c878d.png",
        "sha256": "cfc6b7e03d838a2f3048dedd0b03ebe595870fe2d687e50d013fd6c68d9c878d"
      },
      {
        "path": "/data2/k6tk/36/366670a4535649c7aedc98a275f08a6ea35723162045dfa1008ac8ec285b9099.png",
        "sha256": "366670a4535649c7aedc98a275f08a6ea35723162045dfa1008ac8ec285b9099"
      },
      {
        "path": "/data2/k6tk/96/964e506f5356ac19223a3c3bb89c27780ff3bbb836fb1291bf9152b8d7361761.png",
        "sha256": "964e506f5356ac19223a3c3bb89c27780ff3bbb836fb1291bf9152b8d7361761"
      },
      {
        "path": "/data2/k6tk/5c/5ccfdac56752fa2ced36516b3ddd42328fb5bd6c480098ffe1b1e4c3a438738f.png",
        "sha256": "5ccfdac56752fa2ced36516b3ddd42328fb5bd6c480098ffe1b1e4c3a438738f"
      },
      {
        "path": "/data2/k6tk/eb/ebf424c8fafa9d8777f2d644388968a390a1f129319ee5e2ae8dd37342fc8fcb.png",
        "sha256": "ebf424c8fafa9d8777f2d644388968a390a1f129319ee5e2ae8dd37342fc8fcb"
      },
      {
        "path": "/data2/k6tk/b5/b53a7fcd6c728a27095a21bdfdf3c4dc8f7311cb07262e9eba1d7fac685b9c81.png",
        "sha256": "b53a7fcd6c728a27095a21bdfdf3c4dc8f7311cb07262e9eba1d7fac685b9c81"
      },
      {
        "path": "/data2/k6tk/b7/b77e8cba2da7e8aabee1b08058605143b0fe2eca86d0bcaac425cd1ef9ea8dae.png",
        "sha256": "b77e8cba2da7e8aabee1b08058605143b0fe2eca86d0bcaac425cd1ef9ea8dae"
      },
      {
        "path": "/data2/k6tk/27/276861d4a3b11d16c48663483b3ff5ecaef562b10f6d417b079b417eaf075eca.png",
        "sha256": "276861d4a3b11d16c48663483b3ff5ecaef562b10f6d417b079b417eaf075eca"
      },
      {
        "path": "/data2/k6tk/32/32a222cd6526f8920b17d2a33419bf6ca8475bc04504d1c2b0ba85c4870d47d1.png",
        "sha256": "32a222cd6526f8920b17d2a33419bf6ca8475bc04504d1c2b0ba85c4870d47d1"
      },
      {
        "path": "/data2/k6tk/a4/a42dd7ec3fd914f8f408527bab94f1dc033c512c6fe7ff377677b4230589aa07.png",
        "sha256": "a42dd7ec3fd914f8f408527bab94f1dc033c512c6fe7ff377677b4230589aa07"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the door and facing in the opposite direction of the table, is the blanket to my left or to my right?",
    "timestamps": [
      0.0,
      7.833333333333333,
      15.666666666666666,
      23.5,
      31.333333333333332,
      39.18333333333333,
      47.016666666666666,
      54.85,
      62.68333333333333,
      70.53333333333333,
      78.36666666666666,
      86.2,
      94.03333333333333,
      101.86666666666666,
      109.71666666666667,
      117.55,
      125.38333333333334,
      133.21666666666667,
      141.06666666666666,
      148.9,
      156.73333333333332,
      164.56666666666666,
      172.4,
      180.25,
      188.08333333333334,
      195.91666666666666,
      203.75,
      211.6,
      219.43333333333334,
      227.26666666666668,
      235.1,
      242.95
    ],
    "total_num_frames": 14578
  },
  "target": "<think>\nSeen: door in frame 1; table in frame 21; blanket in frame 14.\nIf I stood at the door facing the table, the blanket would be to my right.\nThe question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the blanket to my left.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 2: vsi590k_039994_away_opp

Store index: 201519. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the office chair and facing in the opposite direction of the telephone, is the door to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: office chair in frame 30; telephone in frame 23; door in frame 15.
If I stood at the office chair facing the telephone, the door would be to my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the door to my right.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_039994",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 139629,
      "derived_from_v6_qid": "vsi590k_039994_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "3406e560391584fd6283037423e03d142f7aae20b65b056194e0629f57812a3b",
      "source_target_sha256": "a05d215cd9e8ac1336eff950a88cb1776fc1a7d17265a6eb8e6ffe08323dd019",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_039994",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_039994_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v7ce32562e444",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_039994",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      44,
      88,
      133,
      177,
      221,
      266,
      310,
      355,
      399,
      443,
      488,
      532,
      577,
      621,
      665,
      710,
      754,
      798,
      843,
      887,
      932,
      976,
      1020,
      1065,
      1109,
      1154,
      1198,
      1242,
      1287,
      1331,
      1376
    ],
    "frames": [
      {
        "path": "/data2/k6tk/59/591495a813e5a8f9098c91badac4887f46b5bf958cbeb2f8e812764603c27c6b.png",
        "sha256": "591495a813e5a8f9098c91badac4887f46b5bf958cbeb2f8e812764603c27c6b"
      },
      {
        "path": "/data2/k6tk/ab/abe437ada33b2b04edd4fb7ecc9339e72579a592b723d505c0f9f98bed20fa3a.png",
        "sha256": "abe437ada33b2b04edd4fb7ecc9339e72579a592b723d505c0f9f98bed20fa3a"
      },
      {
        "path": "/data2/k6tk/20/2021692302bf10f24b649f9244fe63f63ac40100bfd238ad5974549c04d019be.png",
        "sha256": "2021692302bf10f24b649f9244fe63f63ac40100bfd238ad5974549c04d019be"
      },
      {
        "path": "/data2/k6tk/ee/ee815b2164abc4b3c7b12278ed49b4d1d53cb5ecea40cedbc0ea9d1fd7839159.png",
        "sha256": "ee815b2164abc4b3c7b12278ed49b4d1d53cb5ecea40cedbc0ea9d1fd7839159"
      },
      {
        "path": "/data2/k6tk/2d/2df4192e3aa2ef25e8bc89a9eb4235f4e66d8a6bb553c82c2ef58c55630f286d.png",
        "sha256": "2df4192e3aa2ef25e8bc89a9eb4235f4e66d8a6bb553c82c2ef58c55630f286d"
      },
      {
        "path": "/data2/k6tk/e1/e1025398a3ce641657999aa9d796bca68753e8554a29e1a4048c11cf3c21ddf6.png",
        "sha256": "e1025398a3ce641657999aa9d796bca68753e8554a29e1a4048c11cf3c21ddf6"
      },
      {
        "path": "/data2/k6tk/d7/d7104d19715cd3fecbf5b84d30659bd7df24aa1edb2eac60ff6955179d6c436a.png",
        "sha256": "d7104d19715cd3fecbf5b84d30659bd7df24aa1edb2eac60ff6955179d6c436a"
      },
      {
        "path": "/data2/k6tk/a1/a1cbca18356ffa0370688a3821a34a6a566413193c15a00bec29d255c5b3a0a5.png",
        "sha256": "a1cbca18356ffa0370688a3821a34a6a566413193c15a00bec29d255c5b3a0a5"
      },
      {
        "path": "/data2/k6tk/c0/c0662d948e40cb14cfcb6195a1c6376e34707a4eef39be0f5f0475cc7d453b7c.png",
        "sha256": "c0662d948e40cb14cfcb6195a1c6376e34707a4eef39be0f5f0475cc7d453b7c"
      },
      {
        "path": "/data2/k6tk/4d/4de952d7bdc21daa6650eb09d9e83c36a0a36b6aa85494a070852ab5d6a06572.png",
        "sha256": "4de952d7bdc21daa6650eb09d9e83c36a0a36b6aa85494a070852ab5d6a06572"
      },
      {
        "path": "/data2/k6tk/9a/9a9b795ac8540c2eac2bb2301351efcc518de02513c4f384f59cc97fb681b770.png",
        "sha256": "9a9b795ac8540c2eac2bb2301351efcc518de02513c4f384f59cc97fb681b770"
      },
      {
        "path": "/data2/k6tk/8e/8e084812d0baf12e62b461e92545621c497044170e803ad5ebb8f7868c0ea15f.png",
        "sha256": "8e084812d0baf12e62b461e92545621c497044170e803ad5ebb8f7868c0ea15f"
      },
      {
        "path": "/data2/k6tk/5e/5e9203f693271963f7d78502cf293d0c348f6b69feef53aa7d66179b983a0a62.png",
        "sha256": "5e9203f693271963f7d78502cf293d0c348f6b69feef53aa7d66179b983a0a62"
      },
      {
        "path": "/data2/k6tk/f6/f63916a62d7492c426bb13352abe0cb8c0eb89530091c6ecf250bad0441de650.png",
        "sha256": "f63916a62d7492c426bb13352abe0cb8c0eb89530091c6ecf250bad0441de650"
      },
      {
        "path": "/data2/k6tk/bb/bbde876c5c3340cfdcf235b86d9dbbbbdcf3088af4ab41f0e80586cc335d66d8.png",
        "sha256": "bbde876c5c3340cfdcf235b86d9dbbbbdcf3088af4ab41f0e80586cc335d66d8"
      },
      {
        "path": "/data2/k6tk/17/17cb01d1985aec6eb0a07685afd5e15d064cfce9f68bb64f38ca5c51d78200d0.png",
        "sha256": "17cb01d1985aec6eb0a07685afd5e15d064cfce9f68bb64f38ca5c51d78200d0"
      },
      {
        "path": "/data2/k6tk/80/8071a30235339c2588d69b059ebef1c8f381b1712c27fb36958d120cd337eef4.png",
        "sha256": "8071a30235339c2588d69b059ebef1c8f381b1712c27fb36958d120cd337eef4"
      },
      {
        "path": "/data2/k6tk/73/73229aad096b1fd7823d3e2ebe0dd8c9e27d8818feb576b06198fe4a52354420.png",
        "sha256": "73229aad096b1fd7823d3e2ebe0dd8c9e27d8818feb576b06198fe4a52354420"
      },
      {
        "path": "/data2/k6tk/a9/a9ad9ffb83a48d84df26b710cb12d40319e46d08d35d8d912d4a5aa3a5aedbba.png",
        "sha256": "a9ad9ffb83a48d84df26b710cb12d40319e46d08d35d8d912d4a5aa3a5aedbba"
      },
      {
        "path": "/data2/k6tk/1f/1f7078eeee9ee4b331e49dfa1caa2c667d6fd7ee58b8b5e416cff2c6e70155ce.png",
        "sha256": "1f7078eeee9ee4b331e49dfa1caa2c667d6fd7ee58b8b5e416cff2c6e70155ce"
      },
      {
        "path": "/data2/k6tk/18/18c0da296e08658786d75dd70f363b6807d09941c8696fc3e5f777fb4ab1ea4e.png",
        "sha256": "18c0da296e08658786d75dd70f363b6807d09941c8696fc3e5f777fb4ab1ea4e"
      },
      {
        "path": "/data2/k6tk/de/de0445bfa17ecde143df9b932751c3cc26b6c0b2b574ae7e63b0457b31c99101.png",
        "sha256": "de0445bfa17ecde143df9b932751c3cc26b6c0b2b574ae7e63b0457b31c99101"
      },
      {
        "path": "/data2/k6tk/0a/0aa7aa17fa6feab59546a40d5bc4c748d46254f53b6bb1efcf8fd514489feaa5.png",
        "sha256": "0aa7aa17fa6feab59546a40d5bc4c748d46254f53b6bb1efcf8fd514489feaa5"
      },
      {
        "path": "/data2/k6tk/2e/2edc57a11b20f4536edf0ae007dd03637315441e84c8635ac95b45300f80c66a.png",
        "sha256": "2edc57a11b20f4536edf0ae007dd03637315441e84c8635ac95b45300f80c66a"
      },
      {
        "path": "/data2/k6tk/75/75fb5fef9e073c9ca10aa284582f4e7563e0782968e4cd9acafcdf46609fe3e9.png",
        "sha256": "75fb5fef9e073c9ca10aa284582f4e7563e0782968e4cd9acafcdf46609fe3e9"
      },
      {
        "path": "/data2/k6tk/fd/fd099b3c6fe3b7d9a4ffc721ecaa856005d837fdff6beb0972e35675cb5befa1.png",
        "sha256": "fd099b3c6fe3b7d9a4ffc721ecaa856005d837fdff6beb0972e35675cb5befa1"
      },
      {
        "path": "/data2/k6tk/e0/e08bd6d2687749096e388be8fe5a63390b72d2fe905b67239123c2b3d12f4673.png",
        "sha256": "e08bd6d2687749096e388be8fe5a63390b72d2fe905b67239123c2b3d12f4673"
      },
      {
        "path": "/data2/k6tk/75/759801526b51b76e7152f3dbcf4060f62cf6bd6ca6382676d69547c004bb2772.png",
        "sha256": "759801526b51b76e7152f3dbcf4060f62cf6bd6ca6382676d69547c004bb2772"
      },
      {
        "path": "/data2/k6tk/34/349d84e8f1c6f98bd4511bae85128d88b1b6a50328687d3a3007ffe8eb527a1d.png",
        "sha256": "349d84e8f1c6f98bd4511bae85128d88b1b6a50328687d3a3007ffe8eb527a1d"
      },
      {
        "path": "/data2/k6tk/bf/bf08957f93b41f1dd30e33e6a14dac39834d921dc6031e17e7b45af153d89cb5.png",
        "sha256": "bf08957f93b41f1dd30e33e6a14dac39834d921dc6031e17e7b45af153d89cb5"
      },
      {
        "path": "/data2/k6tk/de/de2ce659758b3da18fdb6651069b99e11d1380de681157afc3a8e89716dc6916.png",
        "sha256": "de2ce659758b3da18fdb6651069b99e11d1380de681157afc3a8e89716dc6916"
      },
      {
        "path": "/data2/k6tk/65/65c570e6c88f5451fe22db6c25602e7983629451ebb1faf92a3ba5cea7a758e6.png",
        "sha256": "65c570e6c88f5451fe22db6c25602e7983629451ebb1faf92a3ba5cea7a758e6"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the office chair and facing in the opposite direction of the telephone, is the door to my left or to my right?",
    "timestamps": [
      0.0,
      1.8333333333333333,
      3.6666666666666665,
      5.541666666666667,
      7.375,
      9.208333333333334,
      11.083333333333334,
      12.916666666666666,
      14.791666666666666,
      16.625,
      18.458333333333332,
      20.333333333333332,
      22.166666666666668,
      24.041666666666668,
      25.875,
      27.708333333333332,
      29.583333333333332,
      31.416666666666668,
      33.25,
      35.125,
      36.958333333333336,
      38.833333333333336,
      40.666666666666664,
      42.5,
      44.375,
      46.208333333333336,
      48.083333333333336,
      49.916666666666664,
      51.75,
      53.625,
      55.458333333333336,
      57.333333333333336
    ],
    "total_num_frames": 1377
  },
  "target": "<think>\nSeen: office chair in frame 30; telephone in frame 23; door in frame 15.\nIf I stood at the office chair facing the telephone, the door would be to my left.\nThe question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the door to my right.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 3: vsi590k_139221_away_opp

Store index: 197121. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the power strip and facing in the opposite direction of the kettle, is the heater to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: power strip in frame 16; kettle in frame 28; heater in frame 18.
If I stood at the power strip facing the kettle, the heater would be to my right.
The question has me facing in the opposite direction of the kettle. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my left.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_139221",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 122311,
      "derived_from_v6_qid": "vsi590k_139221_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "6fbee3a43498f0878837228f5df076d3903c59f40d166b4add5871a7bd38e395",
      "source_target_sha256": "e9b1449fb33fb159f5d8e16d796e538700dfba17c227932be2da2d3121e66155",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/b6ac18d55d697a23.jsonl.gz",
    "source_qid": "vsi590k_139221",
    "source_set": "T1H1_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_139221_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v56f7b967306f",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_139221",
  "source_set": "T1H1_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      233,
      467,
      701,
      934,
      1168,
      1402,
      1636,
      1869,
      2103,
      2337,
      2571,
      2804,
      3038,
      3272,
      3506,
      3739,
      3973,
      4207,
      4441,
      4674,
      4908,
      5142,
      5376,
      5609,
      5843,
      6077,
      6311,
      6544,
      6778,
      7012,
      7246
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e6/e6f789398d541c61e36e937321a1adda14f364f7fa903dee4c29c782d3cdeb97.png",
        "sha256": "e6f789398d541c61e36e937321a1adda14f364f7fa903dee4c29c782d3cdeb97"
      },
      {
        "path": "/data2/k6tk/1c/1c1d22dd8b0a20c323f6cc9bd41d70bb2442c9cef2218088d6674add1c76ebdd.png",
        "sha256": "1c1d22dd8b0a20c323f6cc9bd41d70bb2442c9cef2218088d6674add1c76ebdd"
      },
      {
        "path": "/data2/k6tk/ba/baa31104c1722efe9e82ab217394c93de47d3f28baca36c82fe13649bf390e50.png",
        "sha256": "baa31104c1722efe9e82ab217394c93de47d3f28baca36c82fe13649bf390e50"
      },
      {
        "path": "/data2/k6tk/71/7117726b2ea53562f5966bf2d0a4abec39d4e0c721c5588c940f310929775f54.png",
        "sha256": "7117726b2ea53562f5966bf2d0a4abec39d4e0c721c5588c940f310929775f54"
      },
      {
        "path": "/data2/k6tk/ba/bab8d1879b39d57447ae412a7a7bd1aab47ae718be1bf6b71964d1a267ec452d.png",
        "sha256": "bab8d1879b39d57447ae412a7a7bd1aab47ae718be1bf6b71964d1a267ec452d"
      },
      {
        "path": "/data2/k6tk/53/537edabd351ae3e1d76bdae8840a6f46028435f0682df2fafab010ddbb8efcb7.png",
        "sha256": "537edabd351ae3e1d76bdae8840a6f46028435f0682df2fafab010ddbb8efcb7"
      },
      {
        "path": "/data2/k6tk/8b/8b4df4334d9caa20e40258f2795e3fdc506a9485e861e90887cb822047f442b1.png",
        "sha256": "8b4df4334d9caa20e40258f2795e3fdc506a9485e861e90887cb822047f442b1"
      },
      {
        "path": "/data2/k6tk/35/3510562dc83517ec4f3f73567ad8fe076d52040ecabd9bf707a89e1e4a093253.png",
        "sha256": "3510562dc83517ec4f3f73567ad8fe076d52040ecabd9bf707a89e1e4a093253"
      },
      {
        "path": "/data2/k6tk/d3/d30cf370d1a5958ba206169349123d54fb6164ab7b959f9a9530bc644e75ea47.png",
        "sha256": "d30cf370d1a5958ba206169349123d54fb6164ab7b959f9a9530bc644e75ea47"
      },
      {
        "path": "/data2/k6tk/7d/7d158c13293a4fb1b5bb3ac22595e929c0c9c43c8a214b23e247e6efa9b1222a.png",
        "sha256": "7d158c13293a4fb1b5bb3ac22595e929c0c9c43c8a214b23e247e6efa9b1222a"
      },
      {
        "path": "/data2/k6tk/04/04919dc37aec622370eff28683d1c775efd53ff30d26ce5561e48f7bec02dfa8.png",
        "sha256": "04919dc37aec622370eff28683d1c775efd53ff30d26ce5561e48f7bec02dfa8"
      },
      {
        "path": "/data2/k6tk/0b/0b1c926bbf61c49bd5ff188f3f364fc54dc972db8ba79b0be96b7e1952bc9e32.png",
        "sha256": "0b1c926bbf61c49bd5ff188f3f364fc54dc972db8ba79b0be96b7e1952bc9e32"
      },
      {
        "path": "/data2/k6tk/37/37df3e77cc0eb8b774bea5550c8ed60913198a6dd26585ac0d8c73c84056e2a8.png",
        "sha256": "37df3e77cc0eb8b774bea5550c8ed60913198a6dd26585ac0d8c73c84056e2a8"
      },
      {
        "path": "/data2/k6tk/2e/2e8e4306ccda781e8ad31f8ce1c1ab8083adafdc95cd257472e71a8a72e12342.png",
        "sha256": "2e8e4306ccda781e8ad31f8ce1c1ab8083adafdc95cd257472e71a8a72e12342"
      },
      {
        "path": "/data2/k6tk/fd/fd925bcf5b21da7887fdeab53b479c285b32a4949b41cc99994e5624be6feecd.png",
        "sha256": "fd925bcf5b21da7887fdeab53b479c285b32a4949b41cc99994e5624be6feecd"
      },
      {
        "path": "/data2/k6tk/c0/c06c634c9318dcbd0280b6feb0b5c36a6341c827ba9d67191720965852ce50f3.png",
        "sha256": "c06c634c9318dcbd0280b6feb0b5c36a6341c827ba9d67191720965852ce50f3"
      },
      {
        "path": "/data2/k6tk/7d/7d60f50a03db81afbce99538eb40fc85c1f1836372619c613ec3ab3ac8b12c95.png",
        "sha256": "7d60f50a03db81afbce99538eb40fc85c1f1836372619c613ec3ab3ac8b12c95"
      },
      {
        "path": "/data2/k6tk/84/84076f4dba025949fbf42d43d6e9b81179380e57ec0e3475702d961ef55bcc68.png",
        "sha256": "84076f4dba025949fbf42d43d6e9b81179380e57ec0e3475702d961ef55bcc68"
      },
      {
        "path": "/data2/k6tk/f6/f687eb6a92e4f723b3b98539a060fc80a27d49bd2c9870621f7d7b27b91e4d9a.png",
        "sha256": "f687eb6a92e4f723b3b98539a060fc80a27d49bd2c9870621f7d7b27b91e4d9a"
      },
      {
        "path": "/data2/k6tk/20/2053c252c31ade894f0559bb9d9d8818448176d48638a8b7ccaa59b326f091bc.png",
        "sha256": "2053c252c31ade894f0559bb9d9d8818448176d48638a8b7ccaa59b326f091bc"
      },
      {
        "path": "/data2/k6tk/64/64b520a3e6945065d79e2f05186e9d9d23cc960ef7e18c53e9e8765268c7d56d.png",
        "sha256": "64b520a3e6945065d79e2f05186e9d9d23cc960ef7e18c53e9e8765268c7d56d"
      },
      {
        "path": "/data2/k6tk/e9/e99036894f0b19e8b033680a4abbaed71025d73a64f1bac742e2e6ee0fe04e79.png",
        "sha256": "e99036894f0b19e8b033680a4abbaed71025d73a64f1bac742e2e6ee0fe04e79"
      },
      {
        "path": "/data2/k6tk/96/9659e79f157c7fe0f750f404b63edef4d322a21bf9d71bbbe92a5500768a33a6.png",
        "sha256": "9659e79f157c7fe0f750f404b63edef4d322a21bf9d71bbbe92a5500768a33a6"
      },
      {
        "path": "/data2/k6tk/31/316167f2a86a3131868616e4ed1dbffff85ebca13162441ad3b350341510503b.png",
        "sha256": "316167f2a86a3131868616e4ed1dbffff85ebca13162441ad3b350341510503b"
      },
      {
        "path": "/data2/k6tk/d7/d7ad314715d9b857383ecd2eff748ef9077a4892639b637d86ea19079f81518f.png",
        "sha256": "d7ad314715d9b857383ecd2eff748ef9077a4892639b637d86ea19079f81518f"
      },
      {
        "path": "/data2/k6tk/4e/4ebbf4dcd1a44861db0423bfeeb3d1b159a4863921f9136abc38592f5583e6f2.png",
        "sha256": "4ebbf4dcd1a44861db0423bfeeb3d1b159a4863921f9136abc38592f5583e6f2"
      },
      {
        "path": "/data2/k6tk/27/2752d3e16f39922095de78f32bf522ff096f63360083fb644da7b62a050e99da.png",
        "sha256": "2752d3e16f39922095de78f32bf522ff096f63360083fb644da7b62a050e99da"
      },
      {
        "path": "/data2/k6tk/52/527908e514242afeb735d94eceb4ebbc00f562fe0b458262b47ad20f8c0e6399.png",
        "sha256": "527908e514242afeb735d94eceb4ebbc00f562fe0b458262b47ad20f8c0e6399"
      },
      {
        "path": "/data2/k6tk/84/842785c510b5febe72c49e56c30d5524a8c3a4330aa6f73fe2cdc40195c59e32.png",
        "sha256": "842785c510b5febe72c49e56c30d5524a8c3a4330aa6f73fe2cdc40195c59e32"
      },
      {
        "path": "/data2/k6tk/13/13dde0ec8f553794f32857dff06847434e5d3f604f90c006a6823e1b4fd4f446.png",
        "sha256": "13dde0ec8f553794f32857dff06847434e5d3f604f90c006a6823e1b4fd4f446"
      },
      {
        "path": "/data2/k6tk/c9/c966e3c991e03b77dbc90cf1801c1004f3d0f9abfb0fb21526abd2a4c456786d.png",
        "sha256": "c966e3c991e03b77dbc90cf1801c1004f3d0f9abfb0fb21526abd2a4c456786d"
      },
      {
        "path": "/data2/k6tk/b5/b53ea42502370f7a9db3d8c5d655a7a9737b5d86dc11701096d1a126898118f9.png",
        "sha256": "b53ea42502370f7a9db3d8c5d655a7a9737b5d86dc11701096d1a126898118f9"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the power strip and facing in the opposite direction of the kettle, is the heater to my left or to my right?",
    "timestamps": [
      0.0,
      3.8833333333333333,
      7.783333333333333,
      11.683333333333334,
      15.566666666666666,
      19.466666666666665,
      23.366666666666667,
      27.266666666666666,
      31.15,
      35.05,
      38.95,
      42.85,
      46.733333333333334,
      50.63333333333333,
      54.53333333333333,
      58.43333333333333,
      62.31666666666667,
      66.21666666666667,
      70.11666666666666,
      74.01666666666667,
      77.9,
      81.8,
      85.7,
      89.6,
      93.48333333333333,
      97.38333333333334,
      101.28333333333333,
      105.18333333333334,
      109.06666666666666,
      112.96666666666667,
      116.86666666666666,
      120.76666666666667
    ],
    "total_num_frames": 7247
  },
  "target": "<think>\nSeen: power strip in frame 16; kettle in frame 28; heater in frame 18.\nIf I stood at the power strip facing the kettle, the heater would be to my right.\nThe question has me facing in the opposite direction of the kettle. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the heater to my left.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 4: vsi590k_040606_away_opp

Store index: 196646. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the nightstand and facing in the opposite direction of the refrigerator, is the radiator to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: nightstand in frame 3; refrigerator in frame 22; radiator in frame 15.
If I stood at the nightstand facing the refrigerator, the radiator would be to my left.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the radiator to my right.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_040606",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 113109,
      "derived_from_v6_qid": "vsi590k_040606_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "aa01a6b5b74d24d71eedf4929f1be580945609909d19f8eaec0ded6fc6814423",
      "source_target_sha256": "7d56011b4b8d61c1f947c8424fc7505f5c6231bb76cc0b57e8141360b9835ba9",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_040606",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_040606_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v3943b8f006c7",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_040606",
  "source_set": "T0_gaps",
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
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the nightstand and facing in the opposite direction of the refrigerator, is the radiator to my left or to my right?",
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
  "target": "<think>\nSeen: nightstand in frame 3; refrigerator in frame 22; radiator in frame 15.\nIf I stood at the nightstand facing the refrigerator, the radiator would be to my left.\nThe question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the radiator to my right.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 5: vsi590k_015685_away_opp

Store index: 196198. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the bookshelf and facing in the opposite direction of the couch, is the radiator to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. back-right | C. front-right | D. front-left

Answer: A

```text
<think>
Seen: bookshelf in frame 22; couch in frame 17; radiator in frame 22.
If I stood at the bookshelf facing the couch, the radiator would be in front of me, on my right.
The question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the radiator at my back-left.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_015685",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 131695,
      "derived_from_v6_qid": "vsi590k_015685_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "5e8bb7dc6fc95d8d6fc44f7946cb87585f54a903ca2f1ae75487abdbae18e247",
      "source_target_sha256": "da5605caff35538a093bb78b71dc2ade7bdd97776cbc7336e322ece3b6572a62",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_015685",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_015685_away_opp",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vb3c6cf99a59b",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_015685",
  "source_set": "T0_gen_r2",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      86,
      172,
      258,
      344,
      431,
      517,
      603,
      689,
      776,
      862,
      948,
      1034,
      1120,
      1207,
      1293,
      1379,
      1465,
      1552,
      1638,
      1724,
      1810,
      1896,
      1983,
      2069,
      2155,
      2241,
      2328,
      2414,
      2500,
      2586,
      2673
    ],
    "frames": [
      {
        "path": "/data2/k6tk/4d/4d9c9dae94b38bd493f7287d3142581030d5dd0d8ca479aa8e3ec9b44544976d.png",
        "sha256": "4d9c9dae94b38bd493f7287d3142581030d5dd0d8ca479aa8e3ec9b44544976d"
      },
      {
        "path": "/data2/k6tk/7e/7e3d402bee13ace9ad7099c66b19472c2a3ed00b0c6464f5548ceefa5137e078.png",
        "sha256": "7e3d402bee13ace9ad7099c66b19472c2a3ed00b0c6464f5548ceefa5137e078"
      },
      {
        "path": "/data2/k6tk/eb/eb924f9e3907394aec7b4888c803a138677855e59ec6f8bdcae310e8d0c1fef6.png",
        "sha256": "eb924f9e3907394aec7b4888c803a138677855e59ec6f8bdcae310e8d0c1fef6"
      },
      {
        "path": "/data2/k6tk/1d/1d95ea5a251c887af000ae725429ea06fbdc76cc76fae4b98ba616c301e5cd01.png",
        "sha256": "1d95ea5a251c887af000ae725429ea06fbdc76cc76fae4b98ba616c301e5cd01"
      },
      {
        "path": "/data2/k6tk/9f/9fc384bb20268ac662b3b5b34f1de42b20319205e21c968c85aeaaaf69494e70.png",
        "sha256": "9fc384bb20268ac662b3b5b34f1de42b20319205e21c968c85aeaaaf69494e70"
      },
      {
        "path": "/data2/k6tk/ed/ed465a927fc0247f69d5ff76fc31704846127767dc9c9ee59f4063e75c84b0da.png",
        "sha256": "ed465a927fc0247f69d5ff76fc31704846127767dc9c9ee59f4063e75c84b0da"
      },
      {
        "path": "/data2/k6tk/f7/f707de44a02355a630488bdcd5c15e38a29343348f54a4ca523030476f0eadc9.png",
        "sha256": "f707de44a02355a630488bdcd5c15e38a29343348f54a4ca523030476f0eadc9"
      },
      {
        "path": "/data2/k6tk/7d/7d93b1efd424742f9d099c66dc97a7bb75e2a430957c19e266c4a479b546f219.png",
        "sha256": "7d93b1efd424742f9d099c66dc97a7bb75e2a430957c19e266c4a479b546f219"
      },
      {
        "path": "/data2/k6tk/61/6141c4c41c699678e144ccf771a2cb7ae698a685122cad7406723996510de893.png",
        "sha256": "6141c4c41c699678e144ccf771a2cb7ae698a685122cad7406723996510de893"
      },
      {
        "path": "/data2/k6tk/c3/c31377bfa1e47d384e19add7e8fa5e9c9478a62832a904aad5e5d553a73f45f5.png",
        "sha256": "c31377bfa1e47d384e19add7e8fa5e9c9478a62832a904aad5e5d553a73f45f5"
      },
      {
        "path": "/data2/k6tk/3f/3fb0e8f0545f9d4f237b4eb8b4c1b6652c2b422afd30a7f14c77c56a3082dc07.png",
        "sha256": "3fb0e8f0545f9d4f237b4eb8b4c1b6652c2b422afd30a7f14c77c56a3082dc07"
      },
      {
        "path": "/data2/k6tk/3f/3fd4e22711d74d3842974fe6398f5e6bce8d4ede9c47dbb94aff4c1b0a792f30.png",
        "sha256": "3fd4e22711d74d3842974fe6398f5e6bce8d4ede9c47dbb94aff4c1b0a792f30"
      },
      {
        "path": "/data2/k6tk/17/17765785096b9743a05195da1c57d87847587f507dc6539cf2329f0b17c7bc1b.png",
        "sha256": "17765785096b9743a05195da1c57d87847587f507dc6539cf2329f0b17c7bc1b"
      },
      {
        "path": "/data2/k6tk/13/13211860ffc77647b370696b14ac10b0d268cd80337271e7aa34e0c85d33071f.png",
        "sha256": "13211860ffc77647b370696b14ac10b0d268cd80337271e7aa34e0c85d33071f"
      },
      {
        "path": "/data2/k6tk/a0/a012281e0b894347954a8bb10b8362ea5abb504076a34bcdcf55206c19eef528.png",
        "sha256": "a012281e0b894347954a8bb10b8362ea5abb504076a34bcdcf55206c19eef528"
      },
      {
        "path": "/data2/k6tk/41/41eb1916b40fd78b31658d2d52f68ba787037a82e2a81132c47b8c35923d8cd0.png",
        "sha256": "41eb1916b40fd78b31658d2d52f68ba787037a82e2a81132c47b8c35923d8cd0"
      },
      {
        "path": "/data2/k6tk/9e/9ef09553307c0958e3aa9b4a6415a954f221dc4baf323a8d1109f05984ddfde7.png",
        "sha256": "9ef09553307c0958e3aa9b4a6415a954f221dc4baf323a8d1109f05984ddfde7"
      },
      {
        "path": "/data2/k6tk/5a/5a1e899fbd7e71a7465c054dafe4c766635c447abd84354ed38f1019e8d1a53b.png",
        "sha256": "5a1e899fbd7e71a7465c054dafe4c766635c447abd84354ed38f1019e8d1a53b"
      },
      {
        "path": "/data2/k6tk/62/62b95aa83457db5710ab36636029508839d1bb5b45c06daeefa5363568dae441.png",
        "sha256": "62b95aa83457db5710ab36636029508839d1bb5b45c06daeefa5363568dae441"
      },
      {
        "path": "/data2/k6tk/e0/e07a4d53b89933201598889650699e53234c98b27c48ea22c06a8eddb4f989da.png",
        "sha256": "e07a4d53b89933201598889650699e53234c98b27c48ea22c06a8eddb4f989da"
      },
      {
        "path": "/data2/k6tk/39/3963516f5591c220372370b615afac0640f413533b7ffc35f926d26ea4abf956.png",
        "sha256": "3963516f5591c220372370b615afac0640f413533b7ffc35f926d26ea4abf956"
      },
      {
        "path": "/data2/k6tk/db/dbac70110cb35e1a4b2b1011907ef5b7f261355abf3334c9b1e6171ecb1133be.png",
        "sha256": "dbac70110cb35e1a4b2b1011907ef5b7f261355abf3334c9b1e6171ecb1133be"
      },
      {
        "path": "/data2/k6tk/01/01c71c4edc8807deba57317372d1e6a27358cf555f54f0815284585f8767a66b.png",
        "sha256": "01c71c4edc8807deba57317372d1e6a27358cf555f54f0815284585f8767a66b"
      },
      {
        "path": "/data2/k6tk/95/95f5a04320ebdd1289a26cbe75bac547832b624994d97328c31cecccb774ba03.png",
        "sha256": "95f5a04320ebdd1289a26cbe75bac547832b624994d97328c31cecccb774ba03"
      },
      {
        "path": "/data2/k6tk/7f/7ff3cc1af52b9ab2488318338e31ca3832cc7caa17880fdd401e7e91f0631d2a.png",
        "sha256": "7ff3cc1af52b9ab2488318338e31ca3832cc7caa17880fdd401e7e91f0631d2a"
      },
      {
        "path": "/data2/k6tk/9b/9bb1d52c1e2308fb224c684ec58b8fce4889f2bb43b9305196e6e6630d5a80a2.png",
        "sha256": "9bb1d52c1e2308fb224c684ec58b8fce4889f2bb43b9305196e6e6630d5a80a2"
      },
      {
        "path": "/data2/k6tk/ae/ae7719b972e6da854e7ff2770780ff5188e206245b893f00da78a137e5e88e1b.png",
        "sha256": "ae7719b972e6da854e7ff2770780ff5188e206245b893f00da78a137e5e88e1b"
      },
      {
        "path": "/data2/k6tk/60/607457c25d283b1999ae01f42264ead8e116c5713d4763067774abc7c90258e9.png",
        "sha256": "607457c25d283b1999ae01f42264ead8e116c5713d4763067774abc7c90258e9"
      },
      {
        "path": "/data2/k6tk/af/af812586a3bd57711bdfbb3d25ec7840e573e34712596f00db9254fd5ce699fb.png",
        "sha256": "af812586a3bd57711bdfbb3d25ec7840e573e34712596f00db9254fd5ce699fb"
      },
      {
        "path": "/data2/k6tk/87/87883771f7a1ab6834d66522da1f6fb9c4d4b7f166f471e3feb522b0b3498af0.png",
        "sha256": "87883771f7a1ab6834d66522da1f6fb9c4d4b7f166f471e3feb522b0b3498af0"
      },
      {
        "path": "/data2/k6tk/80/808bc3641dc3d0f9d7b271a6a90b14e561c1421606765fba8848959295ef4556.png",
        "sha256": "808bc3641dc3d0f9d7b271a6a90b14e561c1421606765fba8848959295ef4556"
      },
      {
        "path": "/data2/k6tk/ed/ed5802e5fffcdf6a10cb5bc9c4bd24a22e72e9362348ce629642edd0536b81d0.png",
        "sha256": "ed5802e5fffcdf6a10cb5bc9c4bd24a22e72e9362348ce629642edd0536b81d0"
      }
    ],
    "options": [
      "A. back-left",
      "B. back-right",
      "C. front-right",
      "D. front-left"
    ],
    "question": "If I am standing by the bookshelf and facing in the opposite direction of the couch, is the radiator to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.5833333333333335,
      7.166666666666667,
      10.75,
      14.333333333333334,
      17.958333333333332,
      21.541666666666668,
      25.125,
      28.708333333333332,
      32.333333333333336,
      35.916666666666664,
      39.5,
      43.083333333333336,
      46.666666666666664,
      50.291666666666664,
      53.875,
      57.458333333333336,
      61.041666666666664,
      64.66666666666667,
      68.25,
      71.83333333333333,
      75.41666666666667,
      79.0,
      82.625,
      86.20833333333333,
      89.79166666666667,
      93.375,
      97.0,
      100.58333333333333,
      104.16666666666667,
      107.75,
      111.375
    ],
    "total_num_frames": 2674
  },
  "target": "<think>\nSeen: bookshelf in frame 22; couch in frame 17; radiator in frame 22.\nIf I stood at the bookshelf facing the couch, the radiator would be in front of me, on my right.\nThe question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the radiator at my back-left.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 6: vsi590k_135539_away_opp

Store index: 199590. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the door, is the keyboard to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. left | C. back

Answer: B

```text
<think>
Seen: heater in frame 32; door in frame 21; keyboard in frame 8.
If I stood at the heater facing the door, the keyboard would be out to my right.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the keyboard to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_135539",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 139659,
      "derived_from_v6_qid": "vsi590k_135539_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "33300451cb77ba8711f1edb08e523c9c9e28db687aebd3e17ff920595a8baa0e",
      "source_target_sha256": "9122d5a204fa8c3e305b5aa80fd55bdb3d34facc9b8b9d9a1f1f42537fdf2f44",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_135539",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_135539_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v1a84b69160c4",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_135539",
  "source_set": "T0_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      227,
      455,
      682,
      910,
      1137,
      1365,
      1593,
      1820,
      2048,
      2275,
      2503,
      2730,
      2958,
      3186,
      3413,
      3641,
      3868,
      4096,
      4324,
      4551,
      4779,
      5006,
      5234,
      5461,
      5689,
      5917,
      6144,
      6372,
      6599,
      6827,
      7055
    ],
    "frames": [
      {
        "path": "/data2/k6tk/7b/7bf5e089e42f2478a17fe0c47172188398c42863f7b8803dd87a7e698fec1609.png",
        "sha256": "7bf5e089e42f2478a17fe0c47172188398c42863f7b8803dd87a7e698fec1609"
      },
      {
        "path": "/data2/k6tk/5c/5ce71c8e8fd54a0cbff18faad5c8741eb366d9f477814aecb1e9363e90ab5cf9.png",
        "sha256": "5ce71c8e8fd54a0cbff18faad5c8741eb366d9f477814aecb1e9363e90ab5cf9"
      },
      {
        "path": "/data2/k6tk/fc/fc55b5d366b4698060835e0e9ca649d0fb6e88d0eb803a5d1d17213db85077a2.png",
        "sha256": "fc55b5d366b4698060835e0e9ca649d0fb6e88d0eb803a5d1d17213db85077a2"
      },
      {
        "path": "/data2/k6tk/41/419317f995d04e5c376016014eac9d54b002052fc94995f3a1a0bab4685fe2d5.png",
        "sha256": "419317f995d04e5c376016014eac9d54b002052fc94995f3a1a0bab4685fe2d5"
      },
      {
        "path": "/data2/k6tk/0e/0ed36f8ea3f3d67aa936ced26b6b11563c8b7d54953aff3c4c79cb6f46c63707.png",
        "sha256": "0ed36f8ea3f3d67aa936ced26b6b11563c8b7d54953aff3c4c79cb6f46c63707"
      },
      {
        "path": "/data2/k6tk/ea/ea05379ec987d01f540ee5388f27a29feee0db8697c0a64e78091135d1db19b2.png",
        "sha256": "ea05379ec987d01f540ee5388f27a29feee0db8697c0a64e78091135d1db19b2"
      },
      {
        "path": "/data2/k6tk/64/64cfb7169828fbc5f16f451943ba6e958c6871bca5cc362f07582dffa373d1d7.png",
        "sha256": "64cfb7169828fbc5f16f451943ba6e958c6871bca5cc362f07582dffa373d1d7"
      },
      {
        "path": "/data2/k6tk/d1/d146c354074cb231ef0f1ffe562837497ab2b94a20c6c98621f85052e4c041a4.png",
        "sha256": "d146c354074cb231ef0f1ffe562837497ab2b94a20c6c98621f85052e4c041a4"
      },
      {
        "path": "/data2/k6tk/ad/ade3ca368fd4c48cd67f7eb66a41c1f06bcae3de7f7034f5be9df8d7b68f8ff1.png",
        "sha256": "ade3ca368fd4c48cd67f7eb66a41c1f06bcae3de7f7034f5be9df8d7b68f8ff1"
      },
      {
        "path": "/data2/k6tk/3e/3e26afb9ea70723d9c5c9149a1bd8c0502521a2357bd03040fefd37e7a38d5d0.png",
        "sha256": "3e26afb9ea70723d9c5c9149a1bd8c0502521a2357bd03040fefd37e7a38d5d0"
      },
      {
        "path": "/data2/k6tk/42/420c7a342df60b3fba22653b56dcbb44ef0f365893b09657f0fe15d95c46827e.png",
        "sha256": "420c7a342df60b3fba22653b56dcbb44ef0f365893b09657f0fe15d95c46827e"
      },
      {
        "path": "/data2/k6tk/de/def43e92514bd3ec6607f6715215c1e07502f94ac2641346f01b7ef50b1d65ea.png",
        "sha256": "def43e92514bd3ec6607f6715215c1e07502f94ac2641346f01b7ef50b1d65ea"
      },
      {
        "path": "/data2/k6tk/a4/a4fdd3a83829792634875c673c9c547967d941d4a755c139088444ab0bd9a517.png",
        "sha256": "a4fdd3a83829792634875c673c9c547967d941d4a755c139088444ab0bd9a517"
      },
      {
        "path": "/data2/k6tk/3c/3ce4e7bb0e7bb99b6f58cca5274ee4318e1464202b83e9e390627c5e038b16e4.png",
        "sha256": "3ce4e7bb0e7bb99b6f58cca5274ee4318e1464202b83e9e390627c5e038b16e4"
      },
      {
        "path": "/data2/k6tk/20/20ae21f7089da1d08234005b6a00c680ddd5652b7a243f688c8d497ea953463d.png",
        "sha256": "20ae21f7089da1d08234005b6a00c680ddd5652b7a243f688c8d497ea953463d"
      },
      {
        "path": "/data2/k6tk/fb/fbc9a37a1cd846c6ff2db20293b773ae6600a44bb5e523b6da723fa93a25ed8a.png",
        "sha256": "fbc9a37a1cd846c6ff2db20293b773ae6600a44bb5e523b6da723fa93a25ed8a"
      },
      {
        "path": "/data2/k6tk/2e/2e210dba35c11da9dccf7aa6dafccef3d4d2180f149d5430e27bbf5f014b783c.png",
        "sha256": "2e210dba35c11da9dccf7aa6dafccef3d4d2180f149d5430e27bbf5f014b783c"
      },
      {
        "path": "/data2/k6tk/eb/eb2712d2f2e5e4b2b45f7e4218fba418c582a91856dedf3c1929ac77bb50cd12.png",
        "sha256": "eb2712d2f2e5e4b2b45f7e4218fba418c582a91856dedf3c1929ac77bb50cd12"
      },
      {
        "path": "/data2/k6tk/aa/aa811f1b0b378d7c143d75337dd29612c90be99368277279210cec0a7a4c5f95.png",
        "sha256": "aa811f1b0b378d7c143d75337dd29612c90be99368277279210cec0a7a4c5f95"
      },
      {
        "path": "/data2/k6tk/fb/fb7da515bac0d4292b7a55905932314243167f0e9eec13042bd5be0c1dd6d35c.png",
        "sha256": "fb7da515bac0d4292b7a55905932314243167f0e9eec13042bd5be0c1dd6d35c"
      },
      {
        "path": "/data2/k6tk/60/60e3e56827a50f79aa8a38a79131a9a5bbcc1318dc28c6058e3ceff2d31899b8.png",
        "sha256": "60e3e56827a50f79aa8a38a79131a9a5bbcc1318dc28c6058e3ceff2d31899b8"
      },
      {
        "path": "/data2/k6tk/76/7633b8d8b0506376af04d2564cf2d7455b824db40652c5de3b2f7bddcf59f344.png",
        "sha256": "7633b8d8b0506376af04d2564cf2d7455b824db40652c5de3b2f7bddcf59f344"
      },
      {
        "path": "/data2/k6tk/eb/ebc1b3728ccb9761e4df93c4b5d442a6ad394146164d55c44f9bfd4db58d2318.png",
        "sha256": "ebc1b3728ccb9761e4df93c4b5d442a6ad394146164d55c44f9bfd4db58d2318"
      },
      {
        "path": "/data2/k6tk/75/75f394c5557e91d486a444b0bb6e5f52dbe7d68ba9d3888e71d912b28d3403bb.png",
        "sha256": "75f394c5557e91d486a444b0bb6e5f52dbe7d68ba9d3888e71d912b28d3403bb"
      },
      {
        "path": "/data2/k6tk/04/0464816099cc4f258473d64b2b8f05e29cade868e52e48aeaf09afd34f5079ea.png",
        "sha256": "0464816099cc4f258473d64b2b8f05e29cade868e52e48aeaf09afd34f5079ea"
      },
      {
        "path": "/data2/k6tk/18/1892fb2d10c4165c654223fa75e4d59dc9ff4851b6d2881f6a2281da1b752a7b.png",
        "sha256": "1892fb2d10c4165c654223fa75e4d59dc9ff4851b6d2881f6a2281da1b752a7b"
      },
      {
        "path": "/data2/k6tk/08/08d8f74565bbd196d9f1a916fcea58384be047407dcae9bb6625a497d3fc4d1c.png",
        "sha256": "08d8f74565bbd196d9f1a916fcea58384be047407dcae9bb6625a497d3fc4d1c"
      },
      {
        "path": "/data2/k6tk/96/96fcb3a3c339860d8285f0c986df55e79661d3a8eb9cd47faa3312be1890ba99.png",
        "sha256": "96fcb3a3c339860d8285f0c986df55e79661d3a8eb9cd47faa3312be1890ba99"
      },
      {
        "path": "/data2/k6tk/ea/ea3e9c1849cfb6b578aff15de4feca9e365bd37c5d1df35a77e402b0d4997d62.png",
        "sha256": "ea3e9c1849cfb6b578aff15de4feca9e365bd37c5d1df35a77e402b0d4997d62"
      },
      {
        "path": "/data2/k6tk/10/108e46cd7f84ac3917e7df0680adb42594cb0a3eec4a8fea18f76e0abdb2f889.png",
        "sha256": "108e46cd7f84ac3917e7df0680adb42594cb0a3eec4a8fea18f76e0abdb2f889"
      },
      {
        "path": "/data2/k6tk/7b/7bdef10869642113f9187a97106579a6b102650033e89d8352f032bc3d359112.png",
        "sha256": "7bdef10869642113f9187a97106579a6b102650033e89d8352f032bc3d359112"
      },
      {
        "path": "/data2/k6tk/64/642685aa6d398aaff492e2fab20293b73816933a2e1b4d1aaa576c99110690ff.png",
        "sha256": "642685aa6d398aaff492e2fab20293b73816933a2e1b4d1aaa576c99110690ff"
      }
    ],
    "options": [
      "A. right",
      "B. left",
      "C. back"
    ],
    "question": "If I am standing by the heater and facing in the opposite direction of the door, is the keyboard to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      3.783333333333333,
      7.583333333333333,
      11.366666666666667,
      15.166666666666666,
      18.95,
      22.75,
      26.55,
      30.333333333333332,
      34.13333333333333,
      37.916666666666664,
      41.71666666666667,
      45.5,
      49.3,
      53.1,
      56.88333333333333,
      60.68333333333333,
      64.46666666666667,
      68.26666666666667,
      72.06666666666666,
      75.85,
      79.65,
      83.43333333333334,
      87.23333333333333,
      91.01666666666667,
      94.81666666666666,
      98.61666666666666,
      102.4,
      106.2,
      109.98333333333333,
      113.78333333333333,
      117.58333333333333
    ],
    "total_num_frames": 7056
  },
  "target": "<think>\nSeen: heater in frame 32; door in frame 21; keyboard in frame 8.\nIf I stood at the heater facing the door, the keyboard would be out to my right.\nThe question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the keyboard to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 7: vsi590k_232035_away_opp

Store index: 202149. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the tv and facing in the opposite direction of the stove, is the washer to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. front-left | C. back-right | D. front-right

Answer: A

```text
<think>
Seen: tv in frame 24; stove in frame 14; washer in frame 18.
If I stood at the tv facing the stove, the washer would be in front of me, on my right.
The question has me facing in the opposite direction of the stove. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the washer at my back-left.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d3",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_232035",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 134147,
      "derived_from_v6_qid": "vsi590k_232035_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "e8937fefd2978a3203d51a05073f3dbc9c7b15d555fcb0ded4b50f1385b69c95",
      "source_target_sha256": "5e2a1a77ee403df48def50ea1f8de127aee65b5c1e68b3b6c93c0a41d1ed2a20",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9eecedf23da3bd91.jsonl.gz",
    "source_qid": "vsi590k_232035",
    "source_set": "ARKIT_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_232035_away_opp",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v9c4fa8cabced",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_232035",
  "source_set": "ARKIT_gen_r2",
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      31,
      62,
      93,
      124,
      155,
      186,
      217,
      249,
      280,
      311,
      342,
      373,
      404,
      435,
      466,
      497,
      528,
      559,
      590,
      621,
      652,
      683,
      714,
      746,
      777,
      808,
      839,
      870,
      901,
      932,
      963
    ],
    "frames": [
      {
        "path": "/data2/k6tk/2a/2a015c204df36481064bc4b98127543fb6ba6762bf1b318320e63c72893ae465.png",
        "sha256": "2a015c204df36481064bc4b98127543fb6ba6762bf1b318320e63c72893ae465"
      },
      {
        "path": "/data2/k6tk/1a/1ae0e4f4196320b349c85ff327538c7bbfb5f9e2565993eb1e66a31012a0eda9.png",
        "sha256": "1ae0e4f4196320b349c85ff327538c7bbfb5f9e2565993eb1e66a31012a0eda9"
      },
      {
        "path": "/data2/k6tk/2f/2f0771be014ee9e06d0507df29f60ad53962c88ff0d3e4fe335665f096440503.png",
        "sha256": "2f0771be014ee9e06d0507df29f60ad53962c88ff0d3e4fe335665f096440503"
      },
      {
        "path": "/data2/k6tk/44/44925486d8db3c13c9ac6596fcaebeb2b859ddccb1f0e305862287f26c69be23.png",
        "sha256": "44925486d8db3c13c9ac6596fcaebeb2b859ddccb1f0e305862287f26c69be23"
      },
      {
        "path": "/data2/k6tk/40/400098b22be157ae02384585abb6ab91f6c1c17a3a8762b9ff244ffd175de7d5.png",
        "sha256": "400098b22be157ae02384585abb6ab91f6c1c17a3a8762b9ff244ffd175de7d5"
      },
      {
        "path": "/data2/k6tk/91/914a679c082d73abf223c191b2d628a6f9df00cd38011e303cc7270dbb7cf25a.png",
        "sha256": "914a679c082d73abf223c191b2d628a6f9df00cd38011e303cc7270dbb7cf25a"
      },
      {
        "path": "/data2/k6tk/98/98b5461a7b27b18d74f86709aa19b7dc5b6780cb196e5fcd4a56c55960005f95.png",
        "sha256": "98b5461a7b27b18d74f86709aa19b7dc5b6780cb196e5fcd4a56c55960005f95"
      },
      {
        "path": "/data2/k6tk/e1/e1850f455c3df066cfe15a0e1ccb79ab690abba55496370a112553e6145542ee.png",
        "sha256": "e1850f455c3df066cfe15a0e1ccb79ab690abba55496370a112553e6145542ee"
      },
      {
        "path": "/data2/k6tk/d7/d7e9d078e3b93dc87ec63e604ccf07ba132ee3c57445420cd9ffa1295db21aff.png",
        "sha256": "d7e9d078e3b93dc87ec63e604ccf07ba132ee3c57445420cd9ffa1295db21aff"
      },
      {
        "path": "/data2/k6tk/4c/4c3e4bf52e511376872a3c4b776b0961c79b408475c5b8ff7390cfb698d2f255.png",
        "sha256": "4c3e4bf52e511376872a3c4b776b0961c79b408475c5b8ff7390cfb698d2f255"
      },
      {
        "path": "/data2/k6tk/de/de7eef0a62e9a1956301760b0c37c0af85849a85aefe5be4b104f703c5e3114c.png",
        "sha256": "de7eef0a62e9a1956301760b0c37c0af85849a85aefe5be4b104f703c5e3114c"
      },
      {
        "path": "/data2/k6tk/76/76ca81308b03e0cd1749b703d2294391330c5dfa21803cf2908e4d6ccfd70ffb.png",
        "sha256": "76ca81308b03e0cd1749b703d2294391330c5dfa21803cf2908e4d6ccfd70ffb"
      },
      {
        "path": "/data2/k6tk/81/81207e9afdc12cb53a01c407f1454bbea011e57efd1a72d3f86e2e5653991084.png",
        "sha256": "81207e9afdc12cb53a01c407f1454bbea011e57efd1a72d3f86e2e5653991084"
      },
      {
        "path": "/data2/k6tk/bb/bb56468757e44983632250ed9b016084b4088353c2d00d1c0a89bbc3f7b7419c.png",
        "sha256": "bb56468757e44983632250ed9b016084b4088353c2d00d1c0a89bbc3f7b7419c"
      },
      {
        "path": "/data2/k6tk/31/318fe4dddc1d378a24d6a01455e0cf2068f45b7a8e18aa836fb3378dc9f64869.png",
        "sha256": "318fe4dddc1d378a24d6a01455e0cf2068f45b7a8e18aa836fb3378dc9f64869"
      },
      {
        "path": "/data2/k6tk/39/39279613d22978557ee86d28d1852e3a92c8a631a5fd17c80a199df3f0e99262.png",
        "sha256": "39279613d22978557ee86d28d1852e3a92c8a631a5fd17c80a199df3f0e99262"
      },
      {
        "path": "/data2/k6tk/8a/8ae1494d62de631d24ff142b2effba395dfc7efd8cbbead2c5b584ef7948d826.png",
        "sha256": "8ae1494d62de631d24ff142b2effba395dfc7efd8cbbead2c5b584ef7948d826"
      },
      {
        "path": "/data2/k6tk/03/03c019accf6c9c05685e7350e4edbfa3f1425f1765965f7e1506fd88e89ae487.png",
        "sha256": "03c019accf6c9c05685e7350e4edbfa3f1425f1765965f7e1506fd88e89ae487"
      },
      {
        "path": "/data2/k6tk/07/079a0347b26a27f2ed1f41ab6d2bd318fa2ee730bc85a74a897837685fb976e3.png",
        "sha256": "079a0347b26a27f2ed1f41ab6d2bd318fa2ee730bc85a74a897837685fb976e3"
      },
      {
        "path": "/data2/k6tk/70/7029a99b5994ce2d378f0cb9900ca19d367b5badeca3442aa276c4c0adc3f5b7.png",
        "sha256": "7029a99b5994ce2d378f0cb9900ca19d367b5badeca3442aa276c4c0adc3f5b7"
      },
      {
        "path": "/data2/k6tk/3e/3e7b83aa46a2a75f1f4a3200a5c59219f0f480466270dd52cd3064d1d014bec1.png",
        "sha256": "3e7b83aa46a2a75f1f4a3200a5c59219f0f480466270dd52cd3064d1d014bec1"
      },
      {
        "path": "/data2/k6tk/b1/b1779d6fbad10a9b484b055e2a27098d58579e23f449a03767edd83d4cd07464.png",
        "sha256": "b1779d6fbad10a9b484b055e2a27098d58579e23f449a03767edd83d4cd07464"
      },
      {
        "path": "/data2/k6tk/b9/b992826054e85e9862fc257afa35e46c94fe79cc17955f67f226ed72b9ad78e0.png",
        "sha256": "b992826054e85e9862fc257afa35e46c94fe79cc17955f67f226ed72b9ad78e0"
      },
      {
        "path": "/data2/k6tk/fc/fccb2d635c9ea36022eb3e0950140831d4c11ac427c2c3396299c1990fe01407.png",
        "sha256": "fccb2d635c9ea36022eb3e0950140831d4c11ac427c2c3396299c1990fe01407"
      },
      {
        "path": "/data2/k6tk/73/7356737ded31e9f8541ef9766bc9ab87062ef109190a5c21bcfb3c149678278a.png",
        "sha256": "7356737ded31e9f8541ef9766bc9ab87062ef109190a5c21bcfb3c149678278a"
      },
      {
        "path": "/data2/k6tk/c9/c9325ecf83d3959f81c47c239be6adfce89e07f3b94d1709870122e48d7bbd60.png",
        "sha256": "c9325ecf83d3959f81c47c239be6adfce89e07f3b94d1709870122e48d7bbd60"
      },
      {
        "path": "/data2/k6tk/e1/e1ac1cc958a024297740b7f2fffa6382c50da7b58433f102933599f64d8e2def.png",
        "sha256": "e1ac1cc958a024297740b7f2fffa6382c50da7b58433f102933599f64d8e2def"
      },
      {
        "path": "/data2/k6tk/93/93da4044512f8283e5c1416c593b82e74009054c8d0fcf673e97e3e6a8140cab.png",
        "sha256": "93da4044512f8283e5c1416c593b82e74009054c8d0fcf673e97e3e6a8140cab"
      },
      {
        "path": "/data2/k6tk/38/381f795e7c433398c0346060017d9b35da4943013453a328eb25313516c386cf.png",
        "sha256": "381f795e7c433398c0346060017d9b35da4943013453a328eb25313516c386cf"
      },
      {
        "path": "/data2/k6tk/ce/ce9d61d73d89dc6a618595aa6e01bd176496d9e4f3c00acf4d1ddca3fbc083e4.png",
        "sha256": "ce9d61d73d89dc6a618595aa6e01bd176496d9e4f3c00acf4d1ddca3fbc083e4"
      },
      {
        "path": "/data2/k6tk/50/5075afbd8663d2b74f76696fae5497fede70ab88951c385c11bdb2ed8b805629.png",
        "sha256": "5075afbd8663d2b74f76696fae5497fede70ab88951c385c11bdb2ed8b805629"
      },
      {
        "path": "/data2/k6tk/53/5370aa2ffd0d37d2a0c704d8ed5d67ce685976a9bb83dc277d5c8d1bd8a39f0d.png",
        "sha256": "5370aa2ffd0d37d2a0c704d8ed5d67ce685976a9bb83dc277d5c8d1bd8a39f0d"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-left",
      "C. back-right",
      "D. front-right"
    ],
    "question": "If I am standing by the tv and facing in the opposite direction of the stove, is the washer to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.1,
      6.2,
      9.3,
      12.4,
      15.5,
      18.6,
      21.7,
      24.9,
      28.0,
      31.1,
      34.2,
      37.3,
      40.4,
      43.5,
      46.6,
      49.7,
      52.8,
      55.9,
      59.0,
      62.1,
      65.2,
      68.3,
      71.4,
      74.6,
      77.7,
      80.8,
      83.9,
      87.0,
      90.1,
      93.2,
      96.3
    ],
    "total_num_frames": 964
  },
  "target": "<think>\nSeen: tv in frame 24; stove in frame 14; washer in frame 18.\nIf I stood at the tv facing the stove, the washer would be in front of me, on my right.\nThe question has me facing in the opposite direction of the stove. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the washer at my back-left.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 8: vsi590k_130001_away_opp

Store index: 201080. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the table and facing in the opposite direction of the door, is the sofa to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: A

```text
<think>
Seen: table in frame 5; door in frame 22; sofa in frame 15.
If I stood at the table facing the door, the sofa would be out to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the sofa to my right.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_130001",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 114951,
      "derived_from_v6_qid": "vsi590k_130001_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "1ba70b1ea00aabe89cbabafe71689eecba698809daad59b4cfd4f5bb3bcd8286",
      "source_target_sha256": "c8225c1187c19324769943cee2ae3858aabfaad2788f4020f1c4046295b5c6b7",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_130001",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_130001_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v012679495aa0",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_130001",
  "source_set": "T0_gen_r2",
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
      "A. right",
      "B. back",
      "C. left"
    ],
    "question": "If I am standing by the table and facing in the opposite direction of the door, is the sofa to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
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
  "target": "<think>\nSeen: table in frame 5; door in frame 22; sofa in frame 15.\nIf I stood at the table facing the door, the sofa would be out to my left.\nThe question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the sofa to my right.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 9: vsi590k_231870_away_opp

Store index: 204006. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the stove and facing in the opposite direction of the table, is the washer to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-left | B. front-right | C. back-left | D. back-right

Answer: C

```text
<think>
Seen: stove in frame 23; table in frame 14; washer in frame 18.
If I stood at the stove facing the table, the washer would be in front of me, on my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the washer at my back-left.
</think>

C
```

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d3",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_231870",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 134595,
      "derived_from_v6_qid": "vsi590k_231870_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "9b14a3f02ab805c4a4e88dc74ba1198abc3b9452c603869cc6f016923c5261f7",
      "source_target_sha256": "4e54fc21b926cc10dd639c33a25ae930ccb4b0205d249360044b22d2b6b7eb86",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9eecedf23da3bd91.jsonl.gz",
    "source_qid": "vsi590k_231870",
    "source_set": "ARKIT_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_231870_away_opp",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "v6d4353f7314b",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_231870",
  "source_set": "ARKIT_gen_r2",
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      13,
      27,
      40,
      53,
      66,
      80,
      93,
      106,
      120,
      133,
      146,
      159,
      173,
      186,
      199,
      213,
      226,
      239,
      253,
      266,
      279,
      292,
      306,
      319,
      332,
      346,
      359,
      372,
      385,
      399,
      412
    ],
    "frames": [
      {
        "path": "/data2/k6tk/28/28e78e9e649c4bff174928d7058d12822a069e348b5d0b1a2f6b196441374b86.png",
        "sha256": "28e78e9e649c4bff174928d7058d12822a069e348b5d0b1a2f6b196441374b86"
      },
      {
        "path": "/data2/k6tk/10/10ef55e722534b818ad81b476f72160d23ba7e337c67a9134d861e3186a38a90.png",
        "sha256": "10ef55e722534b818ad81b476f72160d23ba7e337c67a9134d861e3186a38a90"
      },
      {
        "path": "/data2/k6tk/f9/f9d2bf6a00ac39d71931da7acea941fe65a3e5252e6a7efa8022aa6a0c31d2e5.png",
        "sha256": "f9d2bf6a00ac39d71931da7acea941fe65a3e5252e6a7efa8022aa6a0c31d2e5"
      },
      {
        "path": "/data2/k6tk/d3/d33ccc9a5dc24d00140144d7618884be384f5632bab181449022beb782b681ca.png",
        "sha256": "d33ccc9a5dc24d00140144d7618884be384f5632bab181449022beb782b681ca"
      },
      {
        "path": "/data2/k6tk/73/733c2498802f47fc581fad46378ae3cc64b5bc2a023d5381f9f0a59aaad339ed.png",
        "sha256": "733c2498802f47fc581fad46378ae3cc64b5bc2a023d5381f9f0a59aaad339ed"
      },
      {
        "path": "/data2/k6tk/c5/c53a55a8297c47ff086c763061fa30ca774604c9b4b4af60d38303e86172b86d.png",
        "sha256": "c53a55a8297c47ff086c763061fa30ca774604c9b4b4af60d38303e86172b86d"
      },
      {
        "path": "/data2/k6tk/93/93b2bc8368d695b0e7821839799b886e790eb1603f7493fc8f8fefa1d33d2ff8.png",
        "sha256": "93b2bc8368d695b0e7821839799b886e790eb1603f7493fc8f8fefa1d33d2ff8"
      },
      {
        "path": "/data2/k6tk/66/660da41b94d89e21b438031e2b5ffda5a8a8b2838062a776fad223ec346afdda.png",
        "sha256": "660da41b94d89e21b438031e2b5ffda5a8a8b2838062a776fad223ec346afdda"
      },
      {
        "path": "/data2/k6tk/3e/3eed836439c2d1506cb36824f0c452d6e5eedf61431aa924636c84f6e4e19b83.png",
        "sha256": "3eed836439c2d1506cb36824f0c452d6e5eedf61431aa924636c84f6e4e19b83"
      },
      {
        "path": "/data2/k6tk/94/94c522cfe9b7203eb29836f0a561e21c9e1ba92381ce943494aac91d603d50a1.png",
        "sha256": "94c522cfe9b7203eb29836f0a561e21c9e1ba92381ce943494aac91d603d50a1"
      },
      {
        "path": "/data2/k6tk/a2/a259f8d66c70c6c60de85c3e12c959c231d1c84cd06d8946307ceafb27b7732e.png",
        "sha256": "a259f8d66c70c6c60de85c3e12c959c231d1c84cd06d8946307ceafb27b7732e"
      },
      {
        "path": "/data2/k6tk/a2/a24249a98ab31f3ade06ccf9bef25c5baa59cde1d58c6068328693a26f063e19.png",
        "sha256": "a24249a98ab31f3ade06ccf9bef25c5baa59cde1d58c6068328693a26f063e19"
      },
      {
        "path": "/data2/k6tk/b5/b59902212b2422eb8252ad24749c242545cffcc80cb6d229ea1080b5594c0235.png",
        "sha256": "b59902212b2422eb8252ad24749c242545cffcc80cb6d229ea1080b5594c0235"
      },
      {
        "path": "/data2/k6tk/cc/cc20283a01ae58a4ae6287f12728126323c5ed765b37a1f4b1d5b04afc843ca7.png",
        "sha256": "cc20283a01ae58a4ae6287f12728126323c5ed765b37a1f4b1d5b04afc843ca7"
      },
      {
        "path": "/data2/k6tk/e9/e9dbb5bb6dcb768d84ba7372097bcf568a033e6a0352abdbefc11cd57001484b.png",
        "sha256": "e9dbb5bb6dcb768d84ba7372097bcf568a033e6a0352abdbefc11cd57001484b"
      },
      {
        "path": "/data2/k6tk/a4/a45fcfa57d137b14bd1a14c2219671337590b3bcc2b337a445db26ac839b9247.png",
        "sha256": "a45fcfa57d137b14bd1a14c2219671337590b3bcc2b337a445db26ac839b9247"
      },
      {
        "path": "/data2/k6tk/88/88f9d73c9f23a768efd7e6c637768748d9219e447fc9c55bc0cc476fe59f3cf9.png",
        "sha256": "88f9d73c9f23a768efd7e6c637768748d9219e447fc9c55bc0cc476fe59f3cf9"
      },
      {
        "path": "/data2/k6tk/86/868dd473d98e607afbc6a128fa3a782ed6da09ff01b22e01b7d3cef75dbbc6c3.png",
        "sha256": "868dd473d98e607afbc6a128fa3a782ed6da09ff01b22e01b7d3cef75dbbc6c3"
      },
      {
        "path": "/data2/k6tk/88/8835140ead2db26723a0b4ddfe4b85e00a8709ec6dc123a913d4fcdcab262221.png",
        "sha256": "8835140ead2db26723a0b4ddfe4b85e00a8709ec6dc123a913d4fcdcab262221"
      },
      {
        "path": "/data2/k6tk/7b/7ba65ab45e665887aa6fed8ceab0487f23020a759f4c32c79eb889645c426464.png",
        "sha256": "7ba65ab45e665887aa6fed8ceab0487f23020a759f4c32c79eb889645c426464"
      },
      {
        "path": "/data2/k6tk/99/995d90fccece7795d249279e17f6a2790e776713595082ce2796fdae3c4792c3.png",
        "sha256": "995d90fccece7795d249279e17f6a2790e776713595082ce2796fdae3c4792c3"
      },
      {
        "path": "/data2/k6tk/62/624cce1842743b2542c421dc5a2e627c79290c51069fd3b48e3aacafc24f9c7d.png",
        "sha256": "624cce1842743b2542c421dc5a2e627c79290c51069fd3b48e3aacafc24f9c7d"
      },
      {
        "path": "/data2/k6tk/87/877c0c169130a88613e81c0d6d1e9f78f55c493aa4c10deff32ffeba928f5492.png",
        "sha256": "877c0c169130a88613e81c0d6d1e9f78f55c493aa4c10deff32ffeba928f5492"
      },
      {
        "path": "/data2/k6tk/74/743353c899c20049d8d7c19b9483c182756a2644fdea11f52064e8493dc6fd11.png",
        "sha256": "743353c899c20049d8d7c19b9483c182756a2644fdea11f52064e8493dc6fd11"
      },
      {
        "path": "/data2/k6tk/ca/ca36f0c507ec7289665e993294b996d3ca846b744d2b8aa32d608228a8112a24.png",
        "sha256": "ca36f0c507ec7289665e993294b996d3ca846b744d2b8aa32d608228a8112a24"
      },
      {
        "path": "/data2/k6tk/c5/c5298c065ce9298e04f2b15e208ab4751fa41440563616f628a4b64e1a0563bd.png",
        "sha256": "c5298c065ce9298e04f2b15e208ab4751fa41440563616f628a4b64e1a0563bd"
      },
      {
        "path": "/data2/k6tk/de/de58c462896df3ed0ec46d9dc97006dfee7079584b5005b38cd017ce5beec031.png",
        "sha256": "de58c462896df3ed0ec46d9dc97006dfee7079584b5005b38cd017ce5beec031"
      },
      {
        "path": "/data2/k6tk/84/84f8dcc0b9fc148e2a703b8a8ace06b63356c97afeefb5acb457950f321d4907.png",
        "sha256": "84f8dcc0b9fc148e2a703b8a8ace06b63356c97afeefb5acb457950f321d4907"
      },
      {
        "path": "/data2/k6tk/fb/fb46b62e0c8d7fc3ebba97d8441a531ebde6a46aadc08df222445add2c20463b.png",
        "sha256": "fb46b62e0c8d7fc3ebba97d8441a531ebde6a46aadc08df222445add2c20463b"
      },
      {
        "path": "/data2/k6tk/80/801aa60a3355a445b258e6da4196366974c5e609925be25a2dcceca60e383bff.png",
        "sha256": "801aa60a3355a445b258e6da4196366974c5e609925be25a2dcceca60e383bff"
      },
      {
        "path": "/data2/k6tk/ae/ae066db488c77d2192ed4db98289c0336da26d64a84b59d04a71d50b85d3b406.png",
        "sha256": "ae066db488c77d2192ed4db98289c0336da26d64a84b59d04a71d50b85d3b406"
      },
      {
        "path": "/data2/k6tk/35/3577dafc8f1d9a1391b738a1f13888c179644fa6d290d8a8e71aa3b9c339a3f7.png",
        "sha256": "3577dafc8f1d9a1391b738a1f13888c179644fa6d290d8a8e71aa3b9c339a3f7"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-left",
      "D. back-right"
    ],
    "question": "If I am standing by the stove and facing in the opposite direction of the table, is the washer to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      1.3,
      2.7,
      4.0,
      5.3,
      6.6,
      8.0,
      9.3,
      10.6,
      12.0,
      13.3,
      14.6,
      15.9,
      17.3,
      18.6,
      19.9,
      21.3,
      22.6,
      23.9,
      25.3,
      26.6,
      27.9,
      29.2,
      30.6,
      31.9,
      33.2,
      34.6,
      35.9,
      37.2,
      38.5,
      39.9,
      41.2
    ],
    "total_num_frames": 413
  },
  "target": "<think>\nSeen: stove in frame 23; table in frame 14; washer in frame 18.\nIf I stood at the stove facing the table, the washer would be in front of me, on my right.\nThe question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the washer at my back-left.\n</think>\n\nC",
  "validation_commit": ""
}
```

### Sample 10: vsi590k_151016_away_opp

Store index: 202840. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the sofa and facing in the opposite direction of the microwave, is the chair to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: sofa in frame 28; microwave in frame 24; chair in frame 22.
If I stood at the sofa facing the microwave, the chair would be to my left.
The question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the chair to my right.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_151016",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 119425,
      "derived_from_v6_qid": "vsi590k_151016_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "2065241d755ee4ea8b4cfdb7988595dc17522fb33cb201b5d87a463ba16bd6f5",
      "source_target_sha256": "5ca6953eab0b36f7ad64621eca7a1ee507cdd9b8d97d2d05630bad7f67cfcc4c",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_151016",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_151016_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v051d98aaa813",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_151016",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      244,
      489,
      733,
      978,
      1223,
      1467,
      1712,
      1956,
      2201,
      2446,
      2690,
      2935,
      3179,
      3424,
      3669,
      3913,
      4158,
      4403,
      4647,
      4892,
      5136,
      5381,
      5626,
      5870,
      6115,
      6359,
      6604,
      6849,
      7093,
      7338,
      7583
    ],
    "frames": [
      {
        "path": "/data2/k6tk/09/09bcbe4cbb9cd6ab11d4a9d9235c366ead8b5419f5997415ab14dcef601a2b9c.png",
        "sha256": "09bcbe4cbb9cd6ab11d4a9d9235c366ead8b5419f5997415ab14dcef601a2b9c"
      },
      {
        "path": "/data2/k6tk/fc/fcd1235cbc3dd8d0b978523b727de70101f1334736215cd577caff999eb97b84.png",
        "sha256": "fcd1235cbc3dd8d0b978523b727de70101f1334736215cd577caff999eb97b84"
      },
      {
        "path": "/data2/k6tk/98/98ccf90022a56b1fea04113affbece75816af45440049e6d2608bb04eab72c3c.png",
        "sha256": "98ccf90022a56b1fea04113affbece75816af45440049e6d2608bb04eab72c3c"
      },
      {
        "path": "/data2/k6tk/fe/fe6b33271716ce77c6d2e55d0c83a2bb98db17a599a64fc877664f1ef4cca00b.png",
        "sha256": "fe6b33271716ce77c6d2e55d0c83a2bb98db17a599a64fc877664f1ef4cca00b"
      },
      {
        "path": "/data2/k6tk/e0/e0c4b9de665b9ce85c57ad971465587b4f67ffd4f1f7d0397d23e0379405f7d0.png",
        "sha256": "e0c4b9de665b9ce85c57ad971465587b4f67ffd4f1f7d0397d23e0379405f7d0"
      },
      {
        "path": "/data2/k6tk/ea/ea6e9e7046c0b8716caa114c9c297aff5a63163646bf83c933e4e7a06e6b824a.png",
        "sha256": "ea6e9e7046c0b8716caa114c9c297aff5a63163646bf83c933e4e7a06e6b824a"
      },
      {
        "path": "/data2/k6tk/60/60f0e5c6ae5cebd3c504e4030506fa2e7da72ca61cd48de773e7d3526edab521.png",
        "sha256": "60f0e5c6ae5cebd3c504e4030506fa2e7da72ca61cd48de773e7d3526edab521"
      },
      {
        "path": "/data2/k6tk/55/55da8e16231f651e64279ddcb6c6c94fb891392956fcf322055b32a727ddfdfa.png",
        "sha256": "55da8e16231f651e64279ddcb6c6c94fb891392956fcf322055b32a727ddfdfa"
      },
      {
        "path": "/data2/k6tk/fc/fc34f712849d3d6f9eb3dc6f517b98c7b50c371caaea79c02b875d864365090c.png",
        "sha256": "fc34f712849d3d6f9eb3dc6f517b98c7b50c371caaea79c02b875d864365090c"
      },
      {
        "path": "/data2/k6tk/8b/8b0a74eb83f8597590f4b6c15aa567dc452994355d04f0d0dbd44e0847d1fef3.png",
        "sha256": "8b0a74eb83f8597590f4b6c15aa567dc452994355d04f0d0dbd44e0847d1fef3"
      },
      {
        "path": "/data2/k6tk/ea/ea403e6b1da109e03983a007e5a43d85bb405ad1f9b8b654fd1836ed23dee239.png",
        "sha256": "ea403e6b1da109e03983a007e5a43d85bb405ad1f9b8b654fd1836ed23dee239"
      },
      {
        "path": "/data2/k6tk/45/45eee9bb677bb2bf0df82aa0aaba1c0e5415f79ce0509f6e7c0f2993772e3054.png",
        "sha256": "45eee9bb677bb2bf0df82aa0aaba1c0e5415f79ce0509f6e7c0f2993772e3054"
      },
      {
        "path": "/data2/k6tk/b0/b001de76ff9a739be9f9f5ff83c0f376374861df5184263cad0fe6d30ffb8ba9.png",
        "sha256": "b001de76ff9a739be9f9f5ff83c0f376374861df5184263cad0fe6d30ffb8ba9"
      },
      {
        "path": "/data2/k6tk/cb/cb14f32045d66b3559580576376cff099c6c66c06ad2b4b69140871b4d11ce4d.png",
        "sha256": "cb14f32045d66b3559580576376cff099c6c66c06ad2b4b69140871b4d11ce4d"
      },
      {
        "path": "/data2/k6tk/d8/d809defb6d6fa2fd32a9d61ed003535138071c467703a5c4ad23f928b2ada773.png",
        "sha256": "d809defb6d6fa2fd32a9d61ed003535138071c467703a5c4ad23f928b2ada773"
      },
      {
        "path": "/data2/k6tk/c2/c223e5517a11c3143fb6e5721c78fd95aac536aeb970480508b9e4b0ec9523dd.png",
        "sha256": "c223e5517a11c3143fb6e5721c78fd95aac536aeb970480508b9e4b0ec9523dd"
      },
      {
        "path": "/data2/k6tk/22/226fbcc3180744892b4fa4ca80a4039030c8e829f61a17161189d6a53647d5a9.png",
        "sha256": "226fbcc3180744892b4fa4ca80a4039030c8e829f61a17161189d6a53647d5a9"
      },
      {
        "path": "/data2/k6tk/c4/c460acbd6c589b18ca4dd3619c7a83562ca3111d70561b440db5396028db43cc.png",
        "sha256": "c460acbd6c589b18ca4dd3619c7a83562ca3111d70561b440db5396028db43cc"
      },
      {
        "path": "/data2/k6tk/bc/bc47eff481e9e87f5e70e2ec07ea77bf4aed7351078eb20c058c6be12c4714ee.png",
        "sha256": "bc47eff481e9e87f5e70e2ec07ea77bf4aed7351078eb20c058c6be12c4714ee"
      },
      {
        "path": "/data2/k6tk/9e/9e987cafd58e78ca04eeee13e2685a1d72460cfad15eaf9c8f1182ddd4deaca2.png",
        "sha256": "9e987cafd58e78ca04eeee13e2685a1d72460cfad15eaf9c8f1182ddd4deaca2"
      },
      {
        "path": "/data2/k6tk/b2/b21385ff56f83847a58a1c96acbe4c5ad21f7c3a88ef14ac75e17db0b0ab4f84.png",
        "sha256": "b21385ff56f83847a58a1c96acbe4c5ad21f7c3a88ef14ac75e17db0b0ab4f84"
      },
      {
        "path": "/data2/k6tk/f1/f14041fb359d2db9e7a1a62c6a06f114b949785abaa6178fed1a67b718c3969f.png",
        "sha256": "f14041fb359d2db9e7a1a62c6a06f114b949785abaa6178fed1a67b718c3969f"
      },
      {
        "path": "/data2/k6tk/2f/2f4836bc43ef42aa91eec1d1554d6be40f40e1299a8323c25b185414466cb85f.png",
        "sha256": "2f4836bc43ef42aa91eec1d1554d6be40f40e1299a8323c25b185414466cb85f"
      },
      {
        "path": "/data2/k6tk/19/19094f21c672bdb850d2a14b963551e4498cfb20c158ed27441f39b34dce59da.png",
        "sha256": "19094f21c672bdb850d2a14b963551e4498cfb20c158ed27441f39b34dce59da"
      },
      {
        "path": "/data2/k6tk/3d/3d2ae41f4c1f0b7d451fbe6d298467e01289f4b09d21234f13536742c6041720.png",
        "sha256": "3d2ae41f4c1f0b7d451fbe6d298467e01289f4b09d21234f13536742c6041720"
      },
      {
        "path": "/data2/k6tk/f9/f9147a8d2fe4bde252f05e94c9a3f78953debe826f0fdce412dda18dd5042985.png",
        "sha256": "f9147a8d2fe4bde252f05e94c9a3f78953debe826f0fdce412dda18dd5042985"
      },
      {
        "path": "/data2/k6tk/1a/1a6a49f2e1deb09bdee68fddfeddc7c6d5d5fa137e6df88c251aec72d25a67b2.png",
        "sha256": "1a6a49f2e1deb09bdee68fddfeddc7c6d5d5fa137e6df88c251aec72d25a67b2"
      },
      {
        "path": "/data2/k6tk/3b/3bdc2ddc31644091af91e7b977e36b5fe23e444dc84629956cb9b0c18926b71e.png",
        "sha256": "3bdc2ddc31644091af91e7b977e36b5fe23e444dc84629956cb9b0c18926b71e"
      },
      {
        "path": "/data2/k6tk/8d/8d20549c58da71cc5cd6768bb930f5d59c1f81a84110f76f62dfa1faae876494.png",
        "sha256": "8d20549c58da71cc5cd6768bb930f5d59c1f81a84110f76f62dfa1faae876494"
      },
      {
        "path": "/data2/k6tk/bb/bbcc9610f63e93941914ce54f9a07639495bb74baa7be329262ecc7d41566126.png",
        "sha256": "bbcc9610f63e93941914ce54f9a07639495bb74baa7be329262ecc7d41566126"
      },
      {
        "path": "/data2/k6tk/77/77c5a9e6e5585a4f4aaa1d0caf0a870479c4e310280d172b32bbcb3b8d837456.png",
        "sha256": "77c5a9e6e5585a4f4aaa1d0caf0a870479c4e310280d172b32bbcb3b8d837456"
      },
      {
        "path": "/data2/k6tk/c6/c6a7a1a8105d65c28f8c6355384b2ba403b9b3d46e44a4b819e5786650654b7e.png",
        "sha256": "c6a7a1a8105d65c28f8c6355384b2ba403b9b3d46e44a4b819e5786650654b7e"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the sofa and facing in the opposite direction of the microwave, is the chair to my left or to my right?",
    "timestamps": [
      0.0,
      4.066666666666666,
      8.15,
      12.216666666666667,
      16.3,
      20.383333333333333,
      24.45,
      28.533333333333335,
      32.6,
      36.68333333333333,
      40.766666666666666,
      44.833333333333336,
      48.916666666666664,
      52.983333333333334,
      57.06666666666667,
      61.15,
      65.21666666666667,
      69.3,
      73.38333333333334,
      77.45,
      81.53333333333333,
      85.6,
      89.68333333333334,
      93.76666666666667,
      97.83333333333333,
      101.91666666666667,
      105.98333333333333,
      110.06666666666666,
      114.15,
      118.21666666666667,
      122.3,
      126.38333333333334
    ],
    "total_num_frames": 7584
  },
  "target": "<think>\nSeen: sofa in frame 28; microwave in frame 24; chair in frame 22.\nIf I stood at the sofa facing the microwave, the chair would be to my left.\nThe question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the chair to my right.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 11: vsi590k_245467_away_opp

Store index: 198608. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the stove and facing in the opposite direction of the table, is the refrigerator to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: stove in frame 8; table in frame 22; refrigerator in frame 15.
If I stood at the stove facing the table, the refrigerator would be ahead of me, slightly to my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the refrigerator at my back.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d3",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_245467",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 112095,
      "derived_from_v6_qid": "vsi590k_245467_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "aff1a9686fd7a420b73eaf2b6fe2bda110f02f80c0811f2ef847d45ee84438cf",
      "source_target_sha256": "c0d068c3f0128a2a1894228c88e6e7901be844295d665c11644d84b92066ff2d",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9eecedf23da3bd91.jsonl.gz",
    "source_qid": "vsi590k_245467",
    "source_set": "ARKIT_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_245467_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v7fa167243e3f",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_245467",
  "source_set": "ARKIT_gen_r2",
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      41,
      83,
      124,
      165,
      206,
      248,
      289,
      330,
      372,
      413,
      454,
      495,
      537,
      578,
      619,
      661,
      702,
      743,
      785,
      826,
      867,
      908,
      950,
      991,
      1032,
      1074,
      1115,
      1156,
      1197,
      1239,
      1280
    ],
    "frames": [
      {
        "path": "/data2/k6tk/7f/7fc587bb8c59baec1bf6f0f113442756f710c71080dadaa805895e24036702a0.png",
        "sha256": "7fc587bb8c59baec1bf6f0f113442756f710c71080dadaa805895e24036702a0"
      },
      {
        "path": "/data2/k6tk/44/44a9138d1bcb4e92f1efa2cf57e7606dd73c34cc30d064889e3ec2475618b668.png",
        "sha256": "44a9138d1bcb4e92f1efa2cf57e7606dd73c34cc30d064889e3ec2475618b668"
      },
      {
        "path": "/data2/k6tk/c0/c0a1abec9f2dcaed2308425ed7620662aab0edcbba053c3a4889cbaa75acd194.png",
        "sha256": "c0a1abec9f2dcaed2308425ed7620662aab0edcbba053c3a4889cbaa75acd194"
      },
      {
        "path": "/data2/k6tk/65/65fe05a9e70df47128178463ccec2011c84b48e865fb89f475a96f4e39c4e8fc.png",
        "sha256": "65fe05a9e70df47128178463ccec2011c84b48e865fb89f475a96f4e39c4e8fc"
      },
      {
        "path": "/data2/k6tk/dd/dddd0ff744b182b9a4756f362076ea98db0aa88e91f190cce33cee274f9ad105.png",
        "sha256": "dddd0ff744b182b9a4756f362076ea98db0aa88e91f190cce33cee274f9ad105"
      },
      {
        "path": "/data2/k6tk/1d/1d5920eb56c3b4ee5cdc3a713720992f160197cd4d51d92c5e69d38ec61126fc.png",
        "sha256": "1d5920eb56c3b4ee5cdc3a713720992f160197cd4d51d92c5e69d38ec61126fc"
      },
      {
        "path": "/data2/k6tk/48/48043b7829857211422c5c6b6661071202ff63862b1604137840dfafdb945922.png",
        "sha256": "48043b7829857211422c5c6b6661071202ff63862b1604137840dfafdb945922"
      },
      {
        "path": "/data2/k6tk/6e/6e64f0f1d3c56999a5d8e5bb13e02cbb99a5dd871211e530c2aadd67d479f4e2.png",
        "sha256": "6e64f0f1d3c56999a5d8e5bb13e02cbb99a5dd871211e530c2aadd67d479f4e2"
      },
      {
        "path": "/data2/k6tk/d3/d351182746cc21be0562af66d5858c7a1dfebc2f4988beeadcbaf5342e4bfa7b.png",
        "sha256": "d351182746cc21be0562af66d5858c7a1dfebc2f4988beeadcbaf5342e4bfa7b"
      },
      {
        "path": "/data2/k6tk/c7/c7cad34edb9b35f0e9c2a19e1a44892e1387493df4efd2f74e5dca10edc1904f.png",
        "sha256": "c7cad34edb9b35f0e9c2a19e1a44892e1387493df4efd2f74e5dca10edc1904f"
      },
      {
        "path": "/data2/k6tk/fa/fa0e39fa2069c5c71f90235cf0570a24c8fa88a9ba5f88fb2fe3c8986a010ea6.png",
        "sha256": "fa0e39fa2069c5c71f90235cf0570a24c8fa88a9ba5f88fb2fe3c8986a010ea6"
      },
      {
        "path": "/data2/k6tk/65/653c2046ecc6c5a2844088bcba155480f2b1ee684ef2b7813ba764ee617adb11.png",
        "sha256": "653c2046ecc6c5a2844088bcba155480f2b1ee684ef2b7813ba764ee617adb11"
      },
      {
        "path": "/data2/k6tk/45/45edd14477968e4255186c935db1e8fb13b9516b87c4f0172bb822b0950239d8.png",
        "sha256": "45edd14477968e4255186c935db1e8fb13b9516b87c4f0172bb822b0950239d8"
      },
      {
        "path": "/data2/k6tk/64/6479466372ce60e689729a146b20c047bccd53f47b688e12242f81becd99efac.png",
        "sha256": "6479466372ce60e689729a146b20c047bccd53f47b688e12242f81becd99efac"
      },
      {
        "path": "/data2/k6tk/e1/e1d67885e415ac14f80bbb998d6072b48053d291549daa729c0571af5476a354.png",
        "sha256": "e1d67885e415ac14f80bbb998d6072b48053d291549daa729c0571af5476a354"
      },
      {
        "path": "/data2/k6tk/37/37fbecc1d1a776dc2718569811f9656b00089ef2158eceed64a01f6427593167.png",
        "sha256": "37fbecc1d1a776dc2718569811f9656b00089ef2158eceed64a01f6427593167"
      },
      {
        "path": "/data2/k6tk/df/df0c6c6ee6c0658dc6c7cc98d7f3991e6af69296188a68d3cc96f15568d713c6.png",
        "sha256": "df0c6c6ee6c0658dc6c7cc98d7f3991e6af69296188a68d3cc96f15568d713c6"
      },
      {
        "path": "/data2/k6tk/c6/c6b6f9fd5b38ae1efa1155d4a8698cb5a24c7fbf830acf51a85b74a8ba18b0a4.png",
        "sha256": "c6b6f9fd5b38ae1efa1155d4a8698cb5a24c7fbf830acf51a85b74a8ba18b0a4"
      },
      {
        "path": "/data2/k6tk/8a/8a64c8cf42647f7ec606dbaf914dc5da96128971aecbde8e4d0944f0f926cf1f.png",
        "sha256": "8a64c8cf42647f7ec606dbaf914dc5da96128971aecbde8e4d0944f0f926cf1f"
      },
      {
        "path": "/data2/k6tk/dd/dda11f3f8f8ca0faf51a7816235f4fa95788451f2ecb33308fa19b247206ea08.png",
        "sha256": "dda11f3f8f8ca0faf51a7816235f4fa95788451f2ecb33308fa19b247206ea08"
      },
      {
        "path": "/data2/k6tk/23/231a7d79bedbb2c1583c3f78f00b086152995beefe4d4f8322f384b9632e974a.png",
        "sha256": "231a7d79bedbb2c1583c3f78f00b086152995beefe4d4f8322f384b9632e974a"
      },
      {
        "path": "/data2/k6tk/3b/3b030f659150df8d5038ab2db3e2c71828a429921ab727fa5cf0d779a8feb621.png",
        "sha256": "3b030f659150df8d5038ab2db3e2c71828a429921ab727fa5cf0d779a8feb621"
      },
      {
        "path": "/data2/k6tk/b6/b63201a7e75c44492a068865bd7084a6fffa37aa471a9936e12c1dc479f25bdd.png",
        "sha256": "b63201a7e75c44492a068865bd7084a6fffa37aa471a9936e12c1dc479f25bdd"
      },
      {
        "path": "/data2/k6tk/03/0342fcd1b5db28b035962c541dfc445c4e80976e2df3f9fd3a1bcb333d228ae5.png",
        "sha256": "0342fcd1b5db28b035962c541dfc445c4e80976e2df3f9fd3a1bcb333d228ae5"
      },
      {
        "path": "/data2/k6tk/7c/7c422c590c6144ce3ae678627f19fe98b11fdbb4b0ea9fed688655426f1b1898.png",
        "sha256": "7c422c590c6144ce3ae678627f19fe98b11fdbb4b0ea9fed688655426f1b1898"
      },
      {
        "path": "/data2/k6tk/f9/f9cd0ee644e589f66cb37d2eb4e8a52b9532ab483656728f00d247890cd3c62d.png",
        "sha256": "f9cd0ee644e589f66cb37d2eb4e8a52b9532ab483656728f00d247890cd3c62d"
      },
      {
        "path": "/data2/k6tk/57/5724f1074fcfe1947473a41b3e32257673ef5fed594ade104b4cd429142c9db9.png",
        "sha256": "5724f1074fcfe1947473a41b3e32257673ef5fed594ade104b4cd429142c9db9"
      },
      {
        "path": "/data2/k6tk/0e/0e80f33449427f53576d0b5fc669c37dd843cd96f26547810ab5adc46e2286e2.png",
        "sha256": "0e80f33449427f53576d0b5fc669c37dd843cd96f26547810ab5adc46e2286e2"
      },
      {
        "path": "/data2/k6tk/90/90ecb94b7197def3ee886fad5b96984c81ef264062300f3f99cec3ce2e8c0dce.png",
        "sha256": "90ecb94b7197def3ee886fad5b96984c81ef264062300f3f99cec3ce2e8c0dce"
      },
      {
        "path": "/data2/k6tk/29/2999ca709e405cb9fff7fbac8e4b47518605cabe2f8e79bba3384de67b95d33f.png",
        "sha256": "2999ca709e405cb9fff7fbac8e4b47518605cabe2f8e79bba3384de67b95d33f"
      },
      {
        "path": "/data2/k6tk/e8/e85a81398b3bb65dd86c7469e5406068dc33221c43c9f5768ef6a3be686ea674.png",
        "sha256": "e85a81398b3bb65dd86c7469e5406068dc33221c43c9f5768ef6a3be686ea674"
      },
      {
        "path": "/data2/k6tk/64/64f4d4e5bc390f854c692e7047c4cb15cc8f3f5fd3b16c6e212a8a71591693eb.png",
        "sha256": "64f4d4e5bc390f854c692e7047c4cb15cc8f3f5fd3b16c6e212a8a71591693eb"
      }
    ],
    "options": [
      "A. right",
      "B. back",
      "C. left"
    ],
    "question": "If I am standing by the stove and facing in the opposite direction of the table, is the refrigerator to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      4.1,
      8.3,
      12.4,
      16.5,
      20.6,
      24.8,
      28.9,
      33.0,
      37.2,
      41.3,
      45.4,
      49.5,
      53.7,
      57.8,
      61.9,
      66.1,
      70.2,
      74.3,
      78.5,
      82.6,
      86.7,
      90.8,
      95.0,
      99.1,
      103.2,
      107.4,
      111.5,
      115.6,
      119.7,
      123.9,
      128.0
    ],
    "total_num_frames": 1281
  },
  "target": "<think>\nSeen: stove in frame 8; table in frame 22; refrigerator in frame 15.\nIf I stood at the stove facing the table, the refrigerator would be ahead of me, slightly to my right.\nThe question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the refrigerator at my back.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 12: vsi590k_129061_away_opp

Store index: 199462. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the headphones, is the tv to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: C

```text
<think>
Seen: door in frame 25; headphones in frame 24; tv in frame 32.
If I stood at the door facing the headphones, the tv would be out to my right.
The question has me facing in the opposite direction of the headphones. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the tv to my left.
</think>

C
```

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_129061",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 140695,
      "derived_from_v6_qid": "vsi590k_129061_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "0cfcfb2e2f018b2670c754acefc5e34e14e1b779fd69fabb3477e6cf365789c4",
      "source_target_sha256": "8d9ac62020c3ab46d442122564591446edb3287019e22d4ff62e3454ef67b0c4",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/ba96a4182147a384.jsonl.gz",
    "source_qid": "vsi590k_129061",
    "source_set": "T1H1_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_129061_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v20e7a3832b2a",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_129061",
  "source_set": "T1H1_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      314,
      629,
      943,
      1258,
      1572,
      1887,
      2201,
      2516,
      2830,
      3145,
      3460,
      3774,
      4089,
      4403,
      4718,
      5032,
      5347,
      5661,
      5976,
      6290,
      6605,
      6920,
      7234,
      7549,
      7863,
      8178,
      8492,
      8807,
      9121,
      9436,
      9751
    ],
    "frames": [
      {
        "path": "/data2/k6tk/6a/6a28d26c8271da545d88976ffd2f2bcf797adba41ce326c1354ceabed6d71575.png",
        "sha256": "6a28d26c8271da545d88976ffd2f2bcf797adba41ce326c1354ceabed6d71575"
      },
      {
        "path": "/data2/k6tk/a3/a389692cb975c84cbc24f8af413b4523c85751cf6a43ee95f3257c464a992ba4.png",
        "sha256": "a389692cb975c84cbc24f8af413b4523c85751cf6a43ee95f3257c464a992ba4"
      },
      {
        "path": "/data2/k6tk/aa/aa246191aba51fa8e4971e42a53914670b9978316e1dc19bb79254b56ec0925c.png",
        "sha256": "aa246191aba51fa8e4971e42a53914670b9978316e1dc19bb79254b56ec0925c"
      },
      {
        "path": "/data2/k6tk/96/960b24f0d8907c99bc440542ce5b003095517bf08d11f7e1f505788e33ec4f26.png",
        "sha256": "960b24f0d8907c99bc440542ce5b003095517bf08d11f7e1f505788e33ec4f26"
      },
      {
        "path": "/data2/k6tk/78/78db3b63b7c4362529a2140a633d146ed0f12249122a0c454db1fbae45eccf4d.png",
        "sha256": "78db3b63b7c4362529a2140a633d146ed0f12249122a0c454db1fbae45eccf4d"
      },
      {
        "path": "/data2/k6tk/6d/6db9f73748793e1676e01921367f4110dd8d99e0f2f26ae96c296ad06cc40950.png",
        "sha256": "6db9f73748793e1676e01921367f4110dd8d99e0f2f26ae96c296ad06cc40950"
      },
      {
        "path": "/data2/k6tk/bb/bb7b1c1f82c3b31a242cae7f64419fe9b125b12be49822459330f0c87c8a3ecb.png",
        "sha256": "bb7b1c1f82c3b31a242cae7f64419fe9b125b12be49822459330f0c87c8a3ecb"
      },
      {
        "path": "/data2/k6tk/1d/1dd12d2e788b06b4f018e8dd40a878a87197a211bbedd50ad57325fca286b65e.png",
        "sha256": "1dd12d2e788b06b4f018e8dd40a878a87197a211bbedd50ad57325fca286b65e"
      },
      {
        "path": "/data2/k6tk/35/35552089a2e1e4a977c597d1c6a0d775cb2a0973219667eaba33010cc12dd9c7.png",
        "sha256": "35552089a2e1e4a977c597d1c6a0d775cb2a0973219667eaba33010cc12dd9c7"
      },
      {
        "path": "/data2/k6tk/d7/d7f12ab2cea9238c58485ba430a64e17d4da0e9764155362e1c52a7c98ddcb60.png",
        "sha256": "d7f12ab2cea9238c58485ba430a64e17d4da0e9764155362e1c52a7c98ddcb60"
      },
      {
        "path": "/data2/k6tk/bc/bcd7ff9295c3958b7a3c5e7c862797005436677c28fc2cf09b64b985e63aba73.png",
        "sha256": "bcd7ff9295c3958b7a3c5e7c862797005436677c28fc2cf09b64b985e63aba73"
      },
      {
        "path": "/data2/k6tk/08/08bef568b74f2d8a05c3e1469f887312450e169aab6b47143976140ea661f174.png",
        "sha256": "08bef568b74f2d8a05c3e1469f887312450e169aab6b47143976140ea661f174"
      },
      {
        "path": "/data2/k6tk/23/23a3348729b8265f354c54d8c7c6c10b07ac9c3e79721984907e60e476d3a1a6.png",
        "sha256": "23a3348729b8265f354c54d8c7c6c10b07ac9c3e79721984907e60e476d3a1a6"
      },
      {
        "path": "/data2/k6tk/5a/5a292758e47f7019db1b324fce220453c1e4b7629ca2455ed448f4ed2fdae538.png",
        "sha256": "5a292758e47f7019db1b324fce220453c1e4b7629ca2455ed448f4ed2fdae538"
      },
      {
        "path": "/data2/k6tk/07/0725c6b6aeaded96fa989dd735918396129c5f8bf997d2316758ebc9f92cbc3e.png",
        "sha256": "0725c6b6aeaded96fa989dd735918396129c5f8bf997d2316758ebc9f92cbc3e"
      },
      {
        "path": "/data2/k6tk/fa/faa641db84be319b12fd0d1385812c88308e82038ed0c4f424598faf96d6d6a6.png",
        "sha256": "faa641db84be319b12fd0d1385812c88308e82038ed0c4f424598faf96d6d6a6"
      },
      {
        "path": "/data2/k6tk/7c/7ca7cfb170911f996dfcd518a742c538874a8a756b368bfa1d1ab01d6828325e.png",
        "sha256": "7ca7cfb170911f996dfcd518a742c538874a8a756b368bfa1d1ab01d6828325e"
      },
      {
        "path": "/data2/k6tk/fb/fbde8c5bd3cdd860de0f703586c6ccdbf92fa1d005ba235b863e98054c8646d5.png",
        "sha256": "fbde8c5bd3cdd860de0f703586c6ccdbf92fa1d005ba235b863e98054c8646d5"
      },
      {
        "path": "/data2/k6tk/45/452dcd2df5cd54d41a5a129c8a020fd0ecf80d3442ac19645488493ac3d65afc.png",
        "sha256": "452dcd2df5cd54d41a5a129c8a020fd0ecf80d3442ac19645488493ac3d65afc"
      },
      {
        "path": "/data2/k6tk/8a/8a065b5eb19d6b23f313b7927b3c7b7376fa8fd381a5c87f298a516a9c796d51.png",
        "sha256": "8a065b5eb19d6b23f313b7927b3c7b7376fa8fd381a5c87f298a516a9c796d51"
      },
      {
        "path": "/data2/k6tk/5a/5aa0ee859cf2ac405fee6e26dd7f1e276c7e5fddb83c043b37635d6e3aae2a1e.png",
        "sha256": "5aa0ee859cf2ac405fee6e26dd7f1e276c7e5fddb83c043b37635d6e3aae2a1e"
      },
      {
        "path": "/data2/k6tk/14/140b075d27c27f5b564506ab2e9acbb3d5907c51b4867fdb8b9d23978435ccdd.png",
        "sha256": "140b075d27c27f5b564506ab2e9acbb3d5907c51b4867fdb8b9d23978435ccdd"
      },
      {
        "path": "/data2/k6tk/59/59d43b9ba4122fa2838d4cbafd0ad2a13e012c27546981ac89b655e60b7f79fc.png",
        "sha256": "59d43b9ba4122fa2838d4cbafd0ad2a13e012c27546981ac89b655e60b7f79fc"
      },
      {
        "path": "/data2/k6tk/50/50bda25c1ab20d3ee026a0917a491cea052963877b7656c5e84d1ac68e7d5af3.png",
        "sha256": "50bda25c1ab20d3ee026a0917a491cea052963877b7656c5e84d1ac68e7d5af3"
      },
      {
        "path": "/data2/k6tk/ad/ad14895fbb48a4e6564a3e9e556eb8198753b1fa6f97d8fd010006d0a723f20f.png",
        "sha256": "ad14895fbb48a4e6564a3e9e556eb8198753b1fa6f97d8fd010006d0a723f20f"
      },
      {
        "path": "/data2/k6tk/5f/5faecdededc3cd5de57ebae6f2d3222f2dd334e19604aa72de2fb84923b1a1cf.png",
        "sha256": "5faecdededc3cd5de57ebae6f2d3222f2dd334e19604aa72de2fb84923b1a1cf"
      },
      {
        "path": "/data2/k6tk/ab/ab3259ba8931e435e3a8a8c3e6a07026fa310f9859c728ac38834af31e45313a.png",
        "sha256": "ab3259ba8931e435e3a8a8c3e6a07026fa310f9859c728ac38834af31e45313a"
      },
      {
        "path": "/data2/k6tk/88/88b70b0c579a5216328fb570c4c85cab08d42698d6687d78ef9a51bc30553f45.png",
        "sha256": "88b70b0c579a5216328fb570c4c85cab08d42698d6687d78ef9a51bc30553f45"
      },
      {
        "path": "/data2/k6tk/4d/4d87906f1cf0ae9cf71d1e25e6b763ff3987b538fba01dbc8621542301ee03b7.png",
        "sha256": "4d87906f1cf0ae9cf71d1e25e6b763ff3987b538fba01dbc8621542301ee03b7"
      },
      {
        "path": "/data2/k6tk/5f/5ff24b264fd69eb3a15174f55b5bc7012417d6984daaa900e271fb59cdeba7c5.png",
        "sha256": "5ff24b264fd69eb3a15174f55b5bc7012417d6984daaa900e271fb59cdeba7c5"
      },
      {
        "path": "/data2/k6tk/e2/e24256a42ff508662bb52c0e8272174b30edeef4d6001cd84558c1d04a6ddfb7.png",
        "sha256": "e24256a42ff508662bb52c0e8272174b30edeef4d6001cd84558c1d04a6ddfb7"
      },
      {
        "path": "/data2/k6tk/8a/8af5c488c367d1b03d5f74bde3875b9236e0e73b0c555ccd0156fc96be065075.png",
        "sha256": "8af5c488c367d1b03d5f74bde3875b9236e0e73b0c555ccd0156fc96be065075"
      }
    ],
    "options": [
      "A. back",
      "B. right",
      "C. left"
    ],
    "question": "If I am standing by the door and facing in the opposite direction of the headphones, is the tv to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      5.233333333333333,
      10.483333333333333,
      15.716666666666667,
      20.966666666666665,
      26.2,
      31.45,
      36.68333333333333,
      41.93333333333333,
      47.166666666666664,
      52.416666666666664,
      57.666666666666664,
      62.9,
      68.15,
      73.38333333333334,
      78.63333333333334,
      83.86666666666666,
      89.11666666666666,
      94.35,
      99.6,
      104.83333333333333,
      110.08333333333333,
      115.33333333333333,
      120.56666666666666,
      125.81666666666666,
      131.05,
      136.3,
      141.53333333333333,
      146.78333333333333,
      152.01666666666668,
      157.26666666666668,
      162.51666666666668
    ],
    "total_num_frames": 9752
  },
  "target": "<think>\nSeen: door in frame 25; headphones in frame 24; tv in frame 32.\nIf I stood at the door facing the headphones, the tv would be out to my right.\nThe question has me facing in the opposite direction of the headphones. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the tv to my left.\n</think>\n\nC",
  "validation_commit": ""
}
```

### Sample 13: vsi590k_016016_away_opp

Store index: 195958. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the nightstand and facing in the opposite direction of the tv, is the backpack to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-left | B. front-right | C. back-right | D. back-left

Answer: C

```text
<think>
Seen: nightstand in frame 22; tv in frame 9; backpack in frame 25.
If I stood at the nightstand facing the tv, the backpack would be in front of me, on my left.
The question has me facing in the opposite direction of the tv. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the backpack at my back-right.
</think>

C
```

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_016016",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 139187,
      "derived_from_v6_qid": "vsi590k_016016_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "130559dfff59abb339f1f48e75fcb51bf3011e8b5c3066a5f9f92082e481cc3e",
      "source_target_sha256": "6cc4c8ad1b37f92bc6cd21dad5143a87b200821250618bd61f95d2bf1d51bc43",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/ba96a4182147a384.jsonl.gz",
    "source_qid": "vsi590k_016016",
    "source_set": "T1H1_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_016016_away_opp",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vd0db36968874",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_016016",
  "source_set": "T1H1_gen_r2",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      50,
      101,
      152,
      203,
      254,
      305,
      356,
      407,
      458,
      509,
      560,
      611,
      662,
      713,
      764,
      814,
      865,
      916,
      967,
      1018,
      1069,
      1120,
      1171,
      1222,
      1273,
      1324,
      1375,
      1426,
      1477,
      1528,
      1579
    ],
    "frames": [
      {
        "path": "/data2/k6tk/40/40e6cbd943b84673a745125eaf71b2a8d0b4731edc5858e27058f9f9bd85b100.png",
        "sha256": "40e6cbd943b84673a745125eaf71b2a8d0b4731edc5858e27058f9f9bd85b100"
      },
      {
        "path": "/data2/k6tk/9c/9c36c0533b8d106fb2e1e9a280aa3dad70bea565e2392f496dd9d81d11c3b1d0.png",
        "sha256": "9c36c0533b8d106fb2e1e9a280aa3dad70bea565e2392f496dd9d81d11c3b1d0"
      },
      {
        "path": "/data2/k6tk/3e/3e9a476cd8a50447df18515722aaa868cac4d1d4ebd5103906b00d568c2f995d.png",
        "sha256": "3e9a476cd8a50447df18515722aaa868cac4d1d4ebd5103906b00d568c2f995d"
      },
      {
        "path": "/data2/k6tk/41/41f9b0e3146cb4b2469bfab45279af89ce48212bf20802d0baec2ca34bc5aa96.png",
        "sha256": "41f9b0e3146cb4b2469bfab45279af89ce48212bf20802d0baec2ca34bc5aa96"
      },
      {
        "path": "/data2/k6tk/13/13e280d2733cec66d62bdc9bf4850fd3a3e4b43e5a28bef67b0ccaa5c3c6241e.png",
        "sha256": "13e280d2733cec66d62bdc9bf4850fd3a3e4b43e5a28bef67b0ccaa5c3c6241e"
      },
      {
        "path": "/data2/k6tk/c4/c4c276a69bbfe7fdcd8157eb5d0c4d208e1c4fcb4f51d2b1e6a6b60d114da332.png",
        "sha256": "c4c276a69bbfe7fdcd8157eb5d0c4d208e1c4fcb4f51d2b1e6a6b60d114da332"
      },
      {
        "path": "/data2/k6tk/b7/b7e269ae00f013a98d79a5d1cb684673b0113ab3359b8b04e5920a047b9ae04c.png",
        "sha256": "b7e269ae00f013a98d79a5d1cb684673b0113ab3359b8b04e5920a047b9ae04c"
      },
      {
        "path": "/data2/k6tk/53/534b569da98b35988b468df03c5fb3ff7c8b861e6b4e4647dd76e7d266749bc0.png",
        "sha256": "534b569da98b35988b468df03c5fb3ff7c8b861e6b4e4647dd76e7d266749bc0"
      },
      {
        "path": "/data2/k6tk/17/174464f73fe37d2e5a062d23758cf510e58b0a4818e8cd65f6e4fe989b43977e.png",
        "sha256": "174464f73fe37d2e5a062d23758cf510e58b0a4818e8cd65f6e4fe989b43977e"
      },
      {
        "path": "/data2/k6tk/4e/4ee026d8a1a1d1cd6362f2c27955aaaee159462992a3b8ff939c536d55aa758d.png",
        "sha256": "4ee026d8a1a1d1cd6362f2c27955aaaee159462992a3b8ff939c536d55aa758d"
      },
      {
        "path": "/data2/k6tk/13/132f707b31d945e74271943a17a57d6029367d22f7642b4f603fffa19de9ca86.png",
        "sha256": "132f707b31d945e74271943a17a57d6029367d22f7642b4f603fffa19de9ca86"
      },
      {
        "path": "/data2/k6tk/06/061c00cb291ee8c4aa9c3c5ea0637f033e275c3eae856cd500af05da3e32de87.png",
        "sha256": "061c00cb291ee8c4aa9c3c5ea0637f033e275c3eae856cd500af05da3e32de87"
      },
      {
        "path": "/data2/k6tk/a6/a6aa75cbe2b2476d38ec91018d10b4bf76140a5c85dc9a098686fc002236a52f.png",
        "sha256": "a6aa75cbe2b2476d38ec91018d10b4bf76140a5c85dc9a098686fc002236a52f"
      },
      {
        "path": "/data2/k6tk/a2/a2d4959aee536a6a276935f7580d3075828c2a98ec771230384ea201b3bc2877.png",
        "sha256": "a2d4959aee536a6a276935f7580d3075828c2a98ec771230384ea201b3bc2877"
      },
      {
        "path": "/data2/k6tk/f1/f174f057c302403690c6e457581f80417aad998743d172f38a9cc71c23fea282.png",
        "sha256": "f174f057c302403690c6e457581f80417aad998743d172f38a9cc71c23fea282"
      },
      {
        "path": "/data2/k6tk/2a/2a7188ccce3274cea5d028900cf7711f207bcf5a1dd0658172934fbad73f3cdd.png",
        "sha256": "2a7188ccce3274cea5d028900cf7711f207bcf5a1dd0658172934fbad73f3cdd"
      },
      {
        "path": "/data2/k6tk/0e/0ec3df5f4fa90bfbbfb1079a9d334af5b06615b9871c9e6327e13ebd08b27ffb.png",
        "sha256": "0ec3df5f4fa90bfbbfb1079a9d334af5b06615b9871c9e6327e13ebd08b27ffb"
      },
      {
        "path": "/data2/k6tk/f3/f385819bac13349437f49713bd7a3b596b6bea2189e0cefe153edf76290821e7.png",
        "sha256": "f385819bac13349437f49713bd7a3b596b6bea2189e0cefe153edf76290821e7"
      },
      {
        "path": "/data2/k6tk/f7/f708788804116e4a1c1ef7d37c8628a8c901c136080fbd28abe91fd7b4a02600.png",
        "sha256": "f708788804116e4a1c1ef7d37c8628a8c901c136080fbd28abe91fd7b4a02600"
      },
      {
        "path": "/data2/k6tk/68/6885f43d3e00c6963d463bb579f90e0a7c59b917e4af99bc082bd3dc28e3628a.png",
        "sha256": "6885f43d3e00c6963d463bb579f90e0a7c59b917e4af99bc082bd3dc28e3628a"
      },
      {
        "path": "/data2/k6tk/f6/f63cdf3aabae39a902d90d9e4d6be15d442f8a5e39802f6fcd600b198475d456.png",
        "sha256": "f63cdf3aabae39a902d90d9e4d6be15d442f8a5e39802f6fcd600b198475d456"
      },
      {
        "path": "/data2/k6tk/4a/4a83a60104889c2d4a8aa5b7c05ac90c3c96cae57cda0da350b7f439910d96ee.png",
        "sha256": "4a83a60104889c2d4a8aa5b7c05ac90c3c96cae57cda0da350b7f439910d96ee"
      },
      {
        "path": "/data2/k6tk/d6/d63c37d495c8f7675b6cdbcc47fa885a0600c00205d4ff33f4e06ac24a29e523.png",
        "sha256": "d63c37d495c8f7675b6cdbcc47fa885a0600c00205d4ff33f4e06ac24a29e523"
      },
      {
        "path": "/data2/k6tk/16/164bf9ef2906cab3d496135893f49d8860853270f92168d7a61b29d21e881571.png",
        "sha256": "164bf9ef2906cab3d496135893f49d8860853270f92168d7a61b29d21e881571"
      },
      {
        "path": "/data2/k6tk/bf/bfb2e0f65f51d6cb9c1fa0bb828e9011fdf3dbd17e176203b3ce07aa15de68ad.png",
        "sha256": "bfb2e0f65f51d6cb9c1fa0bb828e9011fdf3dbd17e176203b3ce07aa15de68ad"
      },
      {
        "path": "/data2/k6tk/61/6175c5e122e10200014af33f41d755b357387ec8729fb36ba096b9ec1ca7a483.png",
        "sha256": "6175c5e122e10200014af33f41d755b357387ec8729fb36ba096b9ec1ca7a483"
      },
      {
        "path": "/data2/k6tk/78/783604341c70aa83e11ec30b5aea26a1e663d868d11e6b626ea9232b8a90558b.png",
        "sha256": "783604341c70aa83e11ec30b5aea26a1e663d868d11e6b626ea9232b8a90558b"
      },
      {
        "path": "/data2/k6tk/c3/c3ad80979f2874574dc63a4b3a08d5889c148509800eb102579869622b0e3ec3.png",
        "sha256": "c3ad80979f2874574dc63a4b3a08d5889c148509800eb102579869622b0e3ec3"
      },
      {
        "path": "/data2/k6tk/e7/e7055add46a264190e0b536df5d689dd3bcce4539b4c97cde3cb78b5150effad.png",
        "sha256": "e7055add46a264190e0b536df5d689dd3bcce4539b4c97cde3cb78b5150effad"
      },
      {
        "path": "/data2/k6tk/9c/9c8837718e1171ad0e3b0d725298f5ccf2b536ea356d08ec0fa323bdc3679d1b.png",
        "sha256": "9c8837718e1171ad0e3b0d725298f5ccf2b536ea356d08ec0fa323bdc3679d1b"
      },
      {
        "path": "/data2/k6tk/e5/e5b0d1bcf89a882da5fb06d28063ff2f6a172971ae05fb91497fbef7d9b4e3c6.png",
        "sha256": "e5b0d1bcf89a882da5fb06d28063ff2f6a172971ae05fb91497fbef7d9b4e3c6"
      },
      {
        "path": "/data2/k6tk/ae/ae1cf1261fe062a4de2daa6e8ac8bd2439f51c38c57c0adedfaded39ff564aa4.png",
        "sha256": "ae1cf1261fe062a4de2daa6e8ac8bd2439f51c38c57c0adedfaded39ff564aa4"
      }
    ],
    "options": [
      "A. front-left",
      "B. front-right",
      "C. back-right",
      "D. back-left"
    ],
    "question": "If I am standing by the nightstand and facing in the opposite direction of the tv, is the backpack to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      2.0833333333333335,
      4.208333333333333,
      6.333333333333333,
      8.458333333333334,
      10.583333333333334,
      12.708333333333334,
      14.833333333333334,
      16.958333333333332,
      19.083333333333332,
      21.208333333333332,
      23.333333333333332,
      25.458333333333332,
      27.583333333333332,
      29.708333333333332,
      31.833333333333332,
      33.916666666666664,
      36.041666666666664,
      38.166666666666664,
      40.291666666666664,
      42.416666666666664,
      44.541666666666664,
      46.666666666666664,
      48.791666666666664,
      50.916666666666664,
      53.041666666666664,
      55.166666666666664,
      57.291666666666664,
      59.416666666666664,
      61.541666666666664,
      63.666666666666664,
      65.79166666666667
    ],
    "total_num_frames": 1580
  },
  "target": "<think>\nSeen: nightstand in frame 22; tv in frame 9; backpack in frame 25.\nIf I stood at the nightstand facing the tv, the backpack would be in front of me, on my left.\nThe question has me facing in the opposite direction of the tv. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the backpack at my back-right.\n</think>\n\nC",
  "validation_commit": ""
}
```

### Sample 14: vsi590k_123206_away_opp

Store index: 199657. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the suitcase and facing in the opposite direction of the blanket, is the keyboard to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. left | C. right

Answer: B

```text
<think>
Seen: suitcase in frame 30; blanket in frame 28; keyboard in frame 30.
If I stood at the suitcase facing the blanket, the keyboard would be out to my right.
The question has me facing in the opposite direction of the blanket. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the keyboard to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_123206",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 123821,
      "derived_from_v6_qid": "vsi590k_123206_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "0c3a733fb3405c312a33a6f5e4b81a668e80e37c7a6a569ebd3950df05905dd2",
      "source_target_sha256": "8836d312d947ef0f22698dcc27b606930e3c74c70abe07b66c301f55fe20f9d6",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_123206",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_123206_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v71cd1435bcfc",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_123206",
  "source_set": "T0_gen_r2",
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
      "A. back",
      "B. left",
      "C. right"
    ],
    "question": "If I am standing by the suitcase and facing in the opposite direction of the blanket, is the keyboard to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
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
  "target": "<think>\nSeen: suitcase in frame 30; blanket in frame 28; keyboard in frame 30.\nIf I stood at the suitcase facing the blanket, the keyboard would be out to my right.\nThe question has me facing in the opposite direction of the blanket. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the keyboard to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 15: vsi590k_141947_away_opp

Store index: 196778. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the toilet, is the suitcase to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: heater in frame 14; toilet in frame 17; suitcase in frame 11.
If I stood at the heater facing the toilet, the suitcase would be to my right.
The question has me facing in the opposite direction of the toilet. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the suitcase to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_141947",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 116013,
      "derived_from_v6_qid": "vsi590k_141947_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "a18222a3ab5562544d37256f80bee1a76662813b59168cc52d99b02261b2713f",
      "source_target_sha256": "20f165db7d8e822c075c9afb6c1fa48fe1d4f561d2341a6b542810e2c609d24a",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_141947",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_141947_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v8948ab4c753b",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_141947",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      268,
      536,
      804,
      1072,
      1340,
      1608,
      1877,
      2145,
      2413,
      2681,
      2949,
      3217,
      3486,
      3754,
      4022,
      4290,
      4558,
      4826,
      5095,
      5363,
      5631,
      5899,
      6167,
      6435,
      6704,
      6972,
      7240,
      7508,
      7776,
      8044,
      8313
    ],
    "frames": [
      {
        "path": "/data2/k6tk/06/06c0a6b3eaec3758d4d4c316557f1fb470f4e5770f23a3c68a3fc8a84a9ebe7a.png",
        "sha256": "06c0a6b3eaec3758d4d4c316557f1fb470f4e5770f23a3c68a3fc8a84a9ebe7a"
      },
      {
        "path": "/data2/k6tk/ee/ee4510bd732a296085fe913c49d7a8acbedd525b2958d666b754d12befdcdb27.png",
        "sha256": "ee4510bd732a296085fe913c49d7a8acbedd525b2958d666b754d12befdcdb27"
      },
      {
        "path": "/data2/k6tk/c8/c8e33a25b50dd71cd27fb2eb60ce96366e870fd218c346d30ca395c550b01e9b.png",
        "sha256": "c8e33a25b50dd71cd27fb2eb60ce96366e870fd218c346d30ca395c550b01e9b"
      },
      {
        "path": "/data2/k6tk/68/68c57d56682c4c87e824f9cb7f6d2f699959c0dfece246002822614312b01a43.png",
        "sha256": "68c57d56682c4c87e824f9cb7f6d2f699959c0dfece246002822614312b01a43"
      },
      {
        "path": "/data2/k6tk/fc/fc9fab129517f54cd7308c42dace0fa1034cdae50d9f6416d632d6dbe6771d56.png",
        "sha256": "fc9fab129517f54cd7308c42dace0fa1034cdae50d9f6416d632d6dbe6771d56"
      },
      {
        "path": "/data2/k6tk/cb/cb0dc9e0d780fd8bb40b41c36e9b3cceea2d2f4cfd48168db81027417976c0cd.png",
        "sha256": "cb0dc9e0d780fd8bb40b41c36e9b3cceea2d2f4cfd48168db81027417976c0cd"
      },
      {
        "path": "/data2/k6tk/08/081c50deecf6a06d9c5e70d4ce3ca5d6a67376d3925460712f7b123b08e93010.png",
        "sha256": "081c50deecf6a06d9c5e70d4ce3ca5d6a67376d3925460712f7b123b08e93010"
      },
      {
        "path": "/data2/k6tk/49/4932cf45fb8dca5fb157b0ea2ba33351701503b14dc87c6ea319552596ead1a1.png",
        "sha256": "4932cf45fb8dca5fb157b0ea2ba33351701503b14dc87c6ea319552596ead1a1"
      },
      {
        "path": "/data2/k6tk/29/29b382cb936150e7e8e8946534a8268081055012cc180d2152ef8b04fe9f6a00.png",
        "sha256": "29b382cb936150e7e8e8946534a8268081055012cc180d2152ef8b04fe9f6a00"
      },
      {
        "path": "/data2/k6tk/cf/cf0fbc8bbaa8484cd37128eb0ac1f16cf5110b1e074a5d8d3352e498901ba4c1.png",
        "sha256": "cf0fbc8bbaa8484cd37128eb0ac1f16cf5110b1e074a5d8d3352e498901ba4c1"
      },
      {
        "path": "/data2/k6tk/ec/ec7819446c46901a4f3ffdf6dd05991386f6135a70134d03478fbfa0ac86d341.png",
        "sha256": "ec7819446c46901a4f3ffdf6dd05991386f6135a70134d03478fbfa0ac86d341"
      },
      {
        "path": "/data2/k6tk/d1/d18a8442b2127eaf5cbf69c3e069c1cdb5fdba089a39419da0d616c165b19065.png",
        "sha256": "d18a8442b2127eaf5cbf69c3e069c1cdb5fdba089a39419da0d616c165b19065"
      },
      {
        "path": "/data2/k6tk/13/13b1c85815910085dfe45efe8df8d5f6e4e9e0e4e56135107741e476a56aa413.png",
        "sha256": "13b1c85815910085dfe45efe8df8d5f6e4e9e0e4e56135107741e476a56aa413"
      },
      {
        "path": "/data2/k6tk/a7/a722fd07c0aaff13d4ad1238c25a8321a8aa44bad3a764f7514ebb9e0799aec9.png",
        "sha256": "a722fd07c0aaff13d4ad1238c25a8321a8aa44bad3a764f7514ebb9e0799aec9"
      },
      {
        "path": "/data2/k6tk/fd/fd0652c557039c72708abac04efa953c7d071d27150bbe03992935f74a02f83e.png",
        "sha256": "fd0652c557039c72708abac04efa953c7d071d27150bbe03992935f74a02f83e"
      },
      {
        "path": "/data2/k6tk/af/af9252a838b20080f7fd65878815c8c5442acadc9f6dd59ecda529239d6b7446.png",
        "sha256": "af9252a838b20080f7fd65878815c8c5442acadc9f6dd59ecda529239d6b7446"
      },
      {
        "path": "/data2/k6tk/a1/a1a749d54df253f744aa726e32f285cbc16dccf7bb9291914ef0fe3d12859f9e.png",
        "sha256": "a1a749d54df253f744aa726e32f285cbc16dccf7bb9291914ef0fe3d12859f9e"
      },
      {
        "path": "/data2/k6tk/f2/f2060d1604f05be515fae1886fa8e481ec46bc0e6566607f7efd4b000369c8ed.png",
        "sha256": "f2060d1604f05be515fae1886fa8e481ec46bc0e6566607f7efd4b000369c8ed"
      },
      {
        "path": "/data2/k6tk/19/1906892fd4c94343a06ac6ca0f0d0cd028c38aa8eb9524fbc9d47ff44c327ffe.png",
        "sha256": "1906892fd4c94343a06ac6ca0f0d0cd028c38aa8eb9524fbc9d47ff44c327ffe"
      },
      {
        "path": "/data2/k6tk/d9/d96d569babf79adf2fffe99a4eb0a2fabb4af1c044390d8d236b3b33a41482e9.png",
        "sha256": "d96d569babf79adf2fffe99a4eb0a2fabb4af1c044390d8d236b3b33a41482e9"
      },
      {
        "path": "/data2/k6tk/b0/b08868a16c5b11efffcf0529a8d3cad7fbbf57b52bcfefc8de71038d6399b479.png",
        "sha256": "b08868a16c5b11efffcf0529a8d3cad7fbbf57b52bcfefc8de71038d6399b479"
      },
      {
        "path": "/data2/k6tk/46/469ed4e8c7f5edf67293aaf69336e11f22e88e68ce9e3276e1508a2f40ee7398.png",
        "sha256": "469ed4e8c7f5edf67293aaf69336e11f22e88e68ce9e3276e1508a2f40ee7398"
      },
      {
        "path": "/data2/k6tk/b7/b7b4a2416a49c45f8cf0426c89a6e8ccad4a0afed7f4e33c9504c4fec8c49b1f.png",
        "sha256": "b7b4a2416a49c45f8cf0426c89a6e8ccad4a0afed7f4e33c9504c4fec8c49b1f"
      },
      {
        "path": "/data2/k6tk/17/17fd10966efbefcce18db1f4e3f3c4ed6515b415aa7dd7a7b586f776c36a812b.png",
        "sha256": "17fd10966efbefcce18db1f4e3f3c4ed6515b415aa7dd7a7b586f776c36a812b"
      },
      {
        "path": "/data2/k6tk/80/802ef51b1564cb14ada9d26fb114e13fd9de3540b75d978029019f0a44b0ba39.png",
        "sha256": "802ef51b1564cb14ada9d26fb114e13fd9de3540b75d978029019f0a44b0ba39"
      },
      {
        "path": "/data2/k6tk/b3/b342a5e9f707d6164bbbf0793b00859e9d888f9eea5eff44749c6c613be0aca5.png",
        "sha256": "b342a5e9f707d6164bbbf0793b00859e9d888f9eea5eff44749c6c613be0aca5"
      },
      {
        "path": "/data2/k6tk/06/0699eac6998f8fbeddf15eee7a6cc91cc96448d2d1a165ae6c2127e170d1634a.png",
        "sha256": "0699eac6998f8fbeddf15eee7a6cc91cc96448d2d1a165ae6c2127e170d1634a"
      },
      {
        "path": "/data2/k6tk/87/8780befb0fc01a527dcc46709cb42a318c3e817d541a92599206c08d6ab193c0.png",
        "sha256": "8780befb0fc01a527dcc46709cb42a318c3e817d541a92599206c08d6ab193c0"
      },
      {
        "path": "/data2/k6tk/be/bed589464e66b7cd24192756b7cf4f23527eb034939ba23aba01aff55a29bebe.png",
        "sha256": "bed589464e66b7cd24192756b7cf4f23527eb034939ba23aba01aff55a29bebe"
      },
      {
        "path": "/data2/k6tk/eb/eb8055800a1e1cc3f2b6df6ec7170516350509e4bd05ab85850c50563b04f13a.png",
        "sha256": "eb8055800a1e1cc3f2b6df6ec7170516350509e4bd05ab85850c50563b04f13a"
      },
      {
        "path": "/data2/k6tk/d4/d47624943d1d19e85a5b6ef4e713abfb14487c7d8b128ab2c5a7a4d8608927e9.png",
        "sha256": "d47624943d1d19e85a5b6ef4e713abfb14487c7d8b128ab2c5a7a4d8608927e9"
      },
      {
        "path": "/data2/k6tk/96/969746cc3aabe15772ae0467ece4f00cfeaf961d969369f1ce3d679a405a34ba.png",
        "sha256": "969746cc3aabe15772ae0467ece4f00cfeaf961d969369f1ce3d679a405a34ba"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the heater and facing in the opposite direction of the toilet, is the suitcase to my left or to my right?",
    "timestamps": [
      0.0,
      4.466666666666667,
      8.933333333333334,
      13.4,
      17.866666666666667,
      22.333333333333332,
      26.8,
      31.283333333333335,
      35.75,
      40.21666666666667,
      44.68333333333333,
      49.15,
      53.61666666666667,
      58.1,
      62.56666666666667,
      67.03333333333333,
      71.5,
      75.96666666666667,
      80.43333333333334,
      84.91666666666667,
      89.38333333333334,
      93.85,
      98.31666666666666,
      102.78333333333333,
      107.25,
      111.73333333333333,
      116.2,
      120.66666666666667,
      125.13333333333334,
      129.6,
      134.06666666666666,
      138.55
    ],
    "total_num_frames": 8314
  },
  "target": "<think>\nSeen: heater in frame 14; toilet in frame 17; suitcase in frame 11.\nIf I stood at the heater facing the toilet, the suitcase would be to my right.\nThe question has me facing in the opposite direction of the toilet. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the suitcase to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 16: vsi590k_233461_away_opp

Store index: 201964. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the bathtub and facing in the opposite direction of the table, is the toilet to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. front-right | C. front-left | D. back-right

Answer: D

```text
<think>
Seen: bathtub in frame 4; table in frame 32; toilet in frame 8.
If I stood at the bathtub facing the table, the toilet would be in front of me, on my left.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the toilet at my back-right.
</think>

D
```

```json
{
  "answer": "D",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_hard",
  "dataset": "d3",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_233461",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 137495,
      "derived_from_v6_qid": "vsi590k_233461_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "bdd8558a048c98527bd289e3f697adedad51283ab41ce0dc6d73ee1f3e447d60",
      "source_target_sha256": "6a70b99d98ec2a6d398f6ccea1070889c3df4cb6507027de33ba6c294da5ffdf",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9eecedf23da3bd91.jsonl.gz",
    "source_qid": "vsi590k_233461",
    "source_set": "ARKIT_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_233461_away_opp",
  "question_type": "object_rel_direction_hard",
  "result_status": "diagnostic, provisional",
  "scene": "vdbd4bbb3b4a8",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_233461",
  "source_set": "ARKIT_gen_r2",
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      33,
      65,
      98,
      130,
      163,
      195,
      228,
      260,
      293,
      325,
      358,
      390,
      423,
      455,
      488,
      520,
      553,
      585,
      618,
      650,
      683,
      715,
      748,
      780,
      813,
      845,
      878,
      910,
      943,
      975,
      1008
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f5/f592073a735fd6023b06aca0efe9f1044ec91d367dac4b2d06045a1cb4cad4a5.png",
        "sha256": "f592073a735fd6023b06aca0efe9f1044ec91d367dac4b2d06045a1cb4cad4a5"
      },
      {
        "path": "/data2/k6tk/6b/6b5db5443a367f16865d8ec0c0a597ed8b8d9a2fde8158a53e0c366baace61d5.png",
        "sha256": "6b5db5443a367f16865d8ec0c0a597ed8b8d9a2fde8158a53e0c366baace61d5"
      },
      {
        "path": "/data2/k6tk/c8/c88ff3c9fb75d27af9f125315ac6c2879ca29e4ccae4fe52c3e814641d842056.png",
        "sha256": "c88ff3c9fb75d27af9f125315ac6c2879ca29e4ccae4fe52c3e814641d842056"
      },
      {
        "path": "/data2/k6tk/57/57ceb8a2c8c913a542d247c0dbca578e0dc6ecc9636710965a71895dcb9cace9.png",
        "sha256": "57ceb8a2c8c913a542d247c0dbca578e0dc6ecc9636710965a71895dcb9cace9"
      },
      {
        "path": "/data2/k6tk/3e/3edbe23fe2b6c4dc4e850e70373116c97b4efb6cbc077b01d825fa2b75200b43.png",
        "sha256": "3edbe23fe2b6c4dc4e850e70373116c97b4efb6cbc077b01d825fa2b75200b43"
      },
      {
        "path": "/data2/k6tk/48/484c048e9f31d2b537a4d13401198570da5c5eeb054f3056ac95828cf777a4f0.png",
        "sha256": "484c048e9f31d2b537a4d13401198570da5c5eeb054f3056ac95828cf777a4f0"
      },
      {
        "path": "/data2/k6tk/e2/e201a2135a1beadb2d8bf1316af6311d9a93a93c2c74b53718b3eb4feb4301c0.png",
        "sha256": "e201a2135a1beadb2d8bf1316af6311d9a93a93c2c74b53718b3eb4feb4301c0"
      },
      {
        "path": "/data2/k6tk/6c/6c460e08b806da6b25f6f7751230b9c58f100f5e3933bf31f4e52f17130ccb08.png",
        "sha256": "6c460e08b806da6b25f6f7751230b9c58f100f5e3933bf31f4e52f17130ccb08"
      },
      {
        "path": "/data2/k6tk/0e/0e85c4b7af1770c1bbd2ce6678d2b4512526fd1e2de06520c99750471e3fd192.png",
        "sha256": "0e85c4b7af1770c1bbd2ce6678d2b4512526fd1e2de06520c99750471e3fd192"
      },
      {
        "path": "/data2/k6tk/1f/1f50fa554bc88cf8ea572bd0087c612b8451f362332696867aa1506eb8963939.png",
        "sha256": "1f50fa554bc88cf8ea572bd0087c612b8451f362332696867aa1506eb8963939"
      },
      {
        "path": "/data2/k6tk/40/40595f154fb0db6cb623124fb066998f8535c2e4c898917c96fd6c28a224e42f.png",
        "sha256": "40595f154fb0db6cb623124fb066998f8535c2e4c898917c96fd6c28a224e42f"
      },
      {
        "path": "/data2/k6tk/e4/e43d15f1258ecf85b5b243e1e9720973ef00e39ca82bbedfe0a5261ba6295f0a.png",
        "sha256": "e43d15f1258ecf85b5b243e1e9720973ef00e39ca82bbedfe0a5261ba6295f0a"
      },
      {
        "path": "/data2/k6tk/43/4323fa26fecc8b55489ce2a5a654e7104045523e5beae3e08818ca44fc7c54ed.png",
        "sha256": "4323fa26fecc8b55489ce2a5a654e7104045523e5beae3e08818ca44fc7c54ed"
      },
      {
        "path": "/data2/k6tk/c2/c2fe23610deb4046a912fd37535984257bc2dbfb989382de6dde45a937f40d10.png",
        "sha256": "c2fe23610deb4046a912fd37535984257bc2dbfb989382de6dde45a937f40d10"
      },
      {
        "path": "/data2/k6tk/e8/e88746e32bfc66f8d0cc6a04bd8d2359dd720a88453afdc610787dc2e2d88aae.png",
        "sha256": "e88746e32bfc66f8d0cc6a04bd8d2359dd720a88453afdc610787dc2e2d88aae"
      },
      {
        "path": "/data2/k6tk/28/283a95fd09a8e188c0ccedff2a0371c9f24e3d9ea0b5a656e00f5e426006f0af.png",
        "sha256": "283a95fd09a8e188c0ccedff2a0371c9f24e3d9ea0b5a656e00f5e426006f0af"
      },
      {
        "path": "/data2/k6tk/5c/5c612bc8278d461893de70b9e72c2544bf36e72e6d1d54fd54a344bb91c9fe2c.png",
        "sha256": "5c612bc8278d461893de70b9e72c2544bf36e72e6d1d54fd54a344bb91c9fe2c"
      },
      {
        "path": "/data2/k6tk/e9/e92f0f0bbc0becd6f2b4f18f93d58bc92d6880e5e95bb47c327b880e69fb7c41.png",
        "sha256": "e92f0f0bbc0becd6f2b4f18f93d58bc92d6880e5e95bb47c327b880e69fb7c41"
      },
      {
        "path": "/data2/k6tk/11/118e87b290f8be4fb33365d7b3abc9246a1c7adfd0feb3b6ae5ffd1ce162ead8.png",
        "sha256": "118e87b290f8be4fb33365d7b3abc9246a1c7adfd0feb3b6ae5ffd1ce162ead8"
      },
      {
        "path": "/data2/k6tk/79/799805469265c0291c051a2fcb73415f56b38ff32f559d805130334ccc13dbc2.png",
        "sha256": "799805469265c0291c051a2fcb73415f56b38ff32f559d805130334ccc13dbc2"
      },
      {
        "path": "/data2/k6tk/7e/7e15eca6951941a5d9817e0924eecc9c9b515ae8845eee1ca2affb2de1959191.png",
        "sha256": "7e15eca6951941a5d9817e0924eecc9c9b515ae8845eee1ca2affb2de1959191"
      },
      {
        "path": "/data2/k6tk/65/650a1c2912ccaa365287efa8f68a9bddd81f198eb36b39b865b9e36cf808773e.png",
        "sha256": "650a1c2912ccaa365287efa8f68a9bddd81f198eb36b39b865b9e36cf808773e"
      },
      {
        "path": "/data2/k6tk/fa/faf56107a1b745bac76eec043831d06cb39af9fd6d5e0bd98a69f55f1d90f5a8.png",
        "sha256": "faf56107a1b745bac76eec043831d06cb39af9fd6d5e0bd98a69f55f1d90f5a8"
      },
      {
        "path": "/data2/k6tk/50/508a3743df94a76c1aa62dd86fa0b30ae154426a93a4ee19f3b7c58a6970687a.png",
        "sha256": "508a3743df94a76c1aa62dd86fa0b30ae154426a93a4ee19f3b7c58a6970687a"
      },
      {
        "path": "/data2/k6tk/ec/ecb4e4f689fef851b0e9fc3c5c1ad1b23569d5b1966b46d6151f2c790084c3ef.png",
        "sha256": "ecb4e4f689fef851b0e9fc3c5c1ad1b23569d5b1966b46d6151f2c790084c3ef"
      },
      {
        "path": "/data2/k6tk/25/25dc0ed816435e158923f3140fa0000dd9ff469e40d9b2b1cf348e867d7d4b21.png",
        "sha256": "25dc0ed816435e158923f3140fa0000dd9ff469e40d9b2b1cf348e867d7d4b21"
      },
      {
        "path": "/data2/k6tk/73/73581f8386a81b5fd5265bb724c7d1d38bb42d7a7386d57d723b576aa024fc8e.png",
        "sha256": "73581f8386a81b5fd5265bb724c7d1d38bb42d7a7386d57d723b576aa024fc8e"
      },
      {
        "path": "/data2/k6tk/77/775c055ac8de20c12cac7a27f2fe779f97874107d28171e058d48f4957d8cfb3.png",
        "sha256": "775c055ac8de20c12cac7a27f2fe779f97874107d28171e058d48f4957d8cfb3"
      },
      {
        "path": "/data2/k6tk/fc/fc807e9a968853ff413a835375099048a4fd4f7824ff5241ac1536454b2e1018.png",
        "sha256": "fc807e9a968853ff413a835375099048a4fd4f7824ff5241ac1536454b2e1018"
      },
      {
        "path": "/data2/k6tk/85/859b76fea00111bacf5c162b6028dc892aee63ace521ffbb54f2daee5c67e6d6.png",
        "sha256": "859b76fea00111bacf5c162b6028dc892aee63ace521ffbb54f2daee5c67e6d6"
      },
      {
        "path": "/data2/k6tk/25/2504670dddc4756463869d5c3ce5b6b9a835ddccf8efe4f908456ec93063a36e.png",
        "sha256": "2504670dddc4756463869d5c3ce5b6b9a835ddccf8efe4f908456ec93063a36e"
      },
      {
        "path": "/data2/k6tk/f8/f81b32650bfd0a59e7c4d1507ecf27ffdad5a51c32b291559480b872e611a369.png",
        "sha256": "f81b32650bfd0a59e7c4d1507ecf27ffdad5a51c32b291559480b872e611a369"
      }
    ],
    "options": [
      "A. back-left",
      "B. front-right",
      "C. front-left",
      "D. back-right"
    ],
    "question": "If I am standing by the bathtub and facing in the opposite direction of the table, is the toilet to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).",
    "timestamps": [
      0.0,
      3.3,
      6.5,
      9.8,
      13.0,
      16.3,
      19.5,
      22.8,
      26.0,
      29.3,
      32.5,
      35.8,
      39.0,
      42.3,
      45.5,
      48.8,
      52.0,
      55.3,
      58.5,
      61.8,
      65.0,
      68.3,
      71.5,
      74.8,
      78.0,
      81.3,
      84.5,
      87.8,
      91.0,
      94.3,
      97.5,
      100.8
    ],
    "total_num_frames": 1009
  },
  "target": "<think>\nSeen: bathtub in frame 4; table in frame 32; toilet in frame 8.\nIf I stood at the bathtub facing the table, the toilet would be in front of me, on my left.\nThe question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the toilet at my back-right.\n</think>\n\nD",
  "validation_commit": ""
}
```

### Sample 17: vsi590k_037267_away_opp

Store index: 196005. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the bookshelf and facing in the opposite direction of the keyboard, is the telephone to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: bookshelf in frame 21; keyboard in frame 14; telephone in frame 32.
If I stood at the bookshelf facing the keyboard, the telephone would be to my left.
The question has me facing in the opposite direction of the keyboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the telephone to my right.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_037267",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 135045,
      "derived_from_v6_qid": "vsi590k_037267_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "8965ab9e2145560c73483701f8ab75c2a22bb47b17867996f277dae0f63f11c2",
      "source_target_sha256": "d6a7b860c13c721e502dee2babd99fda93ed054dfb47868e22584d1297ff91eb",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_037267",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_037267_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v381886877684",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_037267",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      45,
      91,
      136,
      182,
      228,
      273,
      319,
      364,
      410,
      456,
      501,
      547,
      592,
      638,
      684,
      729,
      775,
      821,
      866,
      912,
      957,
      1003,
      1049,
      1094,
      1140,
      1185,
      1231,
      1277,
      1322,
      1368,
      1414
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e0/e068d147ade11bd9ada43eca76bb4b93f8a8477003c988bf2163c7d370d191b1.png",
        "sha256": "e068d147ade11bd9ada43eca76bb4b93f8a8477003c988bf2163c7d370d191b1"
      },
      {
        "path": "/data2/k6tk/a7/a7b38935af90cc8a8d476056af618d3991768a634c4bacaa731f439cd83445de.png",
        "sha256": "a7b38935af90cc8a8d476056af618d3991768a634c4bacaa731f439cd83445de"
      },
      {
        "path": "/data2/k6tk/bd/bdd01915141770079a5e718871e313aa7faf461fbeb054b1d4948a547905159d.png",
        "sha256": "bdd01915141770079a5e718871e313aa7faf461fbeb054b1d4948a547905159d"
      },
      {
        "path": "/data2/k6tk/fb/fb6494b7e06e9c0196070917b8c5ff76c9c5ae60ce9c11b9de4581d08c18e941.png",
        "sha256": "fb6494b7e06e9c0196070917b8c5ff76c9c5ae60ce9c11b9de4581d08c18e941"
      },
      {
        "path": "/data2/k6tk/81/81c34848302e4919b261cfa38692841429063532c0d61d7ba50a0d33751b4938.png",
        "sha256": "81c34848302e4919b261cfa38692841429063532c0d61d7ba50a0d33751b4938"
      },
      {
        "path": "/data2/k6tk/56/56b2995ba78cf9343e5e8f4aa561d49372df3bf9eafd8832aa0f39d09e46ea4b.png",
        "sha256": "56b2995ba78cf9343e5e8f4aa561d49372df3bf9eafd8832aa0f39d09e46ea4b"
      },
      {
        "path": "/data2/k6tk/6c/6c884afe8f706c74e0603aad40e87548fd99505f6f74f161e5f3cf6620adb72a.png",
        "sha256": "6c884afe8f706c74e0603aad40e87548fd99505f6f74f161e5f3cf6620adb72a"
      },
      {
        "path": "/data2/k6tk/78/7825215a1503710735f443b8cc8e1b9ff183af0919ba3ea9caf9a41002c04227.png",
        "sha256": "7825215a1503710735f443b8cc8e1b9ff183af0919ba3ea9caf9a41002c04227"
      },
      {
        "path": "/data2/k6tk/8e/8e6980adb2f89551bbcb499da3a7d6e80631221d4da69e157d4071a6116b3d88.png",
        "sha256": "8e6980adb2f89551bbcb499da3a7d6e80631221d4da69e157d4071a6116b3d88"
      },
      {
        "path": "/data2/k6tk/bf/bfd5ad07c9fcb0fe9687f7fe542a88a40d6a44edb1d0fbdaeb139d7c224d05bf.png",
        "sha256": "bfd5ad07c9fcb0fe9687f7fe542a88a40d6a44edb1d0fbdaeb139d7c224d05bf"
      },
      {
        "path": "/data2/k6tk/78/78f02665fff8b47cad2e568caaa37a756167c52b8f94ad8281147ad7ba573ecd.png",
        "sha256": "78f02665fff8b47cad2e568caaa37a756167c52b8f94ad8281147ad7ba573ecd"
      },
      {
        "path": "/data2/k6tk/f5/f512f61cffdc799ed461c9da6c8603c9ab33bb325dd7897e839c8ee180efff5b.png",
        "sha256": "f512f61cffdc799ed461c9da6c8603c9ab33bb325dd7897e839c8ee180efff5b"
      },
      {
        "path": "/data2/k6tk/3c/3cad099d6ed455e92b7affaf1c99b7bd835a019aef7240983168f4efad22da4c.png",
        "sha256": "3cad099d6ed455e92b7affaf1c99b7bd835a019aef7240983168f4efad22da4c"
      },
      {
        "path": "/data2/k6tk/c2/c26a4addfe786e98e8351281712eec3ede845df97597d511a6cb06c288f73122.png",
        "sha256": "c26a4addfe786e98e8351281712eec3ede845df97597d511a6cb06c288f73122"
      },
      {
        "path": "/data2/k6tk/dc/dc7d3307f08ea51684524499da23f633e83d4916547261c66ef370448c0c1aa7.png",
        "sha256": "dc7d3307f08ea51684524499da23f633e83d4916547261c66ef370448c0c1aa7"
      },
      {
        "path": "/data2/k6tk/f8/f8c18af545ebe3bd238925827c413b51fcdb3a26444b8afa2e79b2a01e53a38e.png",
        "sha256": "f8c18af545ebe3bd238925827c413b51fcdb3a26444b8afa2e79b2a01e53a38e"
      },
      {
        "path": "/data2/k6tk/a2/a2f210c360bc1e5945c4a7bbc6032e125c942ac74b61f5e0fca2068625239d21.png",
        "sha256": "a2f210c360bc1e5945c4a7bbc6032e125c942ac74b61f5e0fca2068625239d21"
      },
      {
        "path": "/data2/k6tk/14/147750e436bec52674ec82ecac31bc6261288fb84ace48f17fa69b0bc4150d00.png",
        "sha256": "147750e436bec52674ec82ecac31bc6261288fb84ace48f17fa69b0bc4150d00"
      },
      {
        "path": "/data2/k6tk/22/22cb1365d8485ec97d892d80c1e599806025768ab386319afbb331257b3d113e.png",
        "sha256": "22cb1365d8485ec97d892d80c1e599806025768ab386319afbb331257b3d113e"
      },
      {
        "path": "/data2/k6tk/57/574dc8e4b8bb30e0ee49dfb3ef976ae77dfcbae6798b82b095172ea50c013b42.png",
        "sha256": "574dc8e4b8bb30e0ee49dfb3ef976ae77dfcbae6798b82b095172ea50c013b42"
      },
      {
        "path": "/data2/k6tk/28/28aa4bd60b6dd428a3592bda295285bff42f99008438b9ea9f978c7438360957.png",
        "sha256": "28aa4bd60b6dd428a3592bda295285bff42f99008438b9ea9f978c7438360957"
      },
      {
        "path": "/data2/k6tk/d4/d4964a10a3f720193beee0b24b8b0b1e6e65bc6c36d1fe61dcb97af984ced5da.png",
        "sha256": "d4964a10a3f720193beee0b24b8b0b1e6e65bc6c36d1fe61dcb97af984ced5da"
      },
      {
        "path": "/data2/k6tk/92/92d1ba770262ccb6ff4b5739658fabe63fa4169e2300f5b6c7b3dd7813ea8237.png",
        "sha256": "92d1ba770262ccb6ff4b5739658fabe63fa4169e2300f5b6c7b3dd7813ea8237"
      },
      {
        "path": "/data2/k6tk/55/553f01418c0d8683eae8f05c9326fa8af74b01cd5b60ba3d58b8d7a1baffe325.png",
        "sha256": "553f01418c0d8683eae8f05c9326fa8af74b01cd5b60ba3d58b8d7a1baffe325"
      },
      {
        "path": "/data2/k6tk/dc/dcd8a848f6240014c9fb8429c5f0b42ed7e26c1823dc810ca80a4d025ee89a39.png",
        "sha256": "dcd8a848f6240014c9fb8429c5f0b42ed7e26c1823dc810ca80a4d025ee89a39"
      },
      {
        "path": "/data2/k6tk/ad/ad61092d7c982692b197eb3d884d00e4c906759bb8e2000825598357cee00471.png",
        "sha256": "ad61092d7c982692b197eb3d884d00e4c906759bb8e2000825598357cee00471"
      },
      {
        "path": "/data2/k6tk/70/70348883ae1738b8d452bce8ff318a414bc49981cac012e4bab588f22a2cabd5.png",
        "sha256": "70348883ae1738b8d452bce8ff318a414bc49981cac012e4bab588f22a2cabd5"
      },
      {
        "path": "/data2/k6tk/cd/cd1ef5a2a9edfed2ef21d6f68a4f9e89121abcc2cd1fbba17850a9c800b63674.png",
        "sha256": "cd1ef5a2a9edfed2ef21d6f68a4f9e89121abcc2cd1fbba17850a9c800b63674"
      },
      {
        "path": "/data2/k6tk/e4/e437b3d6eac2a7bb4d7c4d159c5f720f200bf10e9bd2680a4c95114b5fbbac92.png",
        "sha256": "e437b3d6eac2a7bb4d7c4d159c5f720f200bf10e9bd2680a4c95114b5fbbac92"
      },
      {
        "path": "/data2/k6tk/bc/bcfb721bd77891006ce10cad020aba170ee6ef45911d216af72af6340cb741b6.png",
        "sha256": "bcfb721bd77891006ce10cad020aba170ee6ef45911d216af72af6340cb741b6"
      },
      {
        "path": "/data2/k6tk/a3/a33b0e2ac3c41b32ed543b689e18ddcd2a5d59429f8488b20500564aa68fcd43.png",
        "sha256": "a33b0e2ac3c41b32ed543b689e18ddcd2a5d59429f8488b20500564aa68fcd43"
      },
      {
        "path": "/data2/k6tk/37/3761b82f54f95e1e5894e34790cd0f1355ded9d55247d4825e269b1ee9c73a8f.png",
        "sha256": "3761b82f54f95e1e5894e34790cd0f1355ded9d55247d4825e269b1ee9c73a8f"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the bookshelf and facing in the opposite direction of the keyboard, is the telephone to my left or to my right?",
    "timestamps": [
      0.0,
      1.875,
      3.7916666666666665,
      5.666666666666667,
      7.583333333333333,
      9.5,
      11.375,
      13.291666666666666,
      15.166666666666666,
      17.083333333333332,
      19.0,
      20.875,
      22.791666666666668,
      24.666666666666668,
      26.583333333333332,
      28.5,
      30.375,
      32.291666666666664,
      34.208333333333336,
      36.083333333333336,
      38.0,
      39.875,
      41.791666666666664,
      43.708333333333336,
      45.583333333333336,
      47.5,
      49.375,
      51.291666666666664,
      53.208333333333336,
      55.083333333333336,
      57.0,
      58.916666666666664
    ],
    "total_num_frames": 1415
  },
  "target": "<think>\nSeen: bookshelf in frame 21; keyboard in frame 14; telephone in frame 32.\nIf I stood at the bookshelf facing the keyboard, the telephone would be to my left.\nThe question has me facing in the opposite direction of the keyboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the telephone to my right.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 18: vsi590k_116646_away_opp

Store index: 199314. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the whiteboard and facing in the opposite direction of the telephone, is the cup to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: C

```text
<think>
Seen: whiteboard in frame 7; telephone in frame 10; cup in frame 5.
If I stood at the whiteboard facing the telephone, the cup would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the cup at my back.
</think>

C
```

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_116646",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 140373,
      "derived_from_v6_qid": "vsi590k_116646_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "320f9eb361ed60c0930a1fda6abd403077a5fda2df39b11aac323fa850b48f68",
      "source_target_sha256": "9652b1b8e5912ef9980f7e2f15ddb0f91093b744eaa392af3b59607e9c1b506a",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/ba96a4182147a384.jsonl.gz",
    "source_qid": "vsi590k_116646",
    "source_set": "T1H1_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_116646_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v4966403277d7",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_116646",
  "source_set": "T1H1_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      232,
      464,
      697,
      929,
      1162,
      1394,
      1627,
      1859,
      2092,
      2324,
      2556,
      2789,
      3021,
      3254,
      3486,
      3719,
      3951,
      4184,
      4416,
      4649,
      4881,
      5113,
      5346,
      5578,
      5811,
      6043,
      6276,
      6508,
      6741,
      6973,
      7206
    ],
    "frames": [
      {
        "path": "/data2/k6tk/38/38922779f084f3fec5f4625aa890d45d0737a17177b08dc1da0ee2d244f8a3e2.png",
        "sha256": "38922779f084f3fec5f4625aa890d45d0737a17177b08dc1da0ee2d244f8a3e2"
      },
      {
        "path": "/data2/k6tk/6e/6e79d2b2b1f081a191709c5b2b2a1457163c2bafbb55d6b2cfc384a4e71ede8d.png",
        "sha256": "6e79d2b2b1f081a191709c5b2b2a1457163c2bafbb55d6b2cfc384a4e71ede8d"
      },
      {
        "path": "/data2/k6tk/c1/c1b690e4a2afb2517893b3427c075a23d4e0b7fece7c04b40e8361a1bed81989.png",
        "sha256": "c1b690e4a2afb2517893b3427c075a23d4e0b7fece7c04b40e8361a1bed81989"
      },
      {
        "path": "/data2/k6tk/f7/f7512b2274833dc1abec0aef4d0dd4e4d8dee3a9f358a4236cdd70e9feb12149.png",
        "sha256": "f7512b2274833dc1abec0aef4d0dd4e4d8dee3a9f358a4236cdd70e9feb12149"
      },
      {
        "path": "/data2/k6tk/23/23066a6d6d368f11c65a785274746104361a9be94a6aeba680652a705c5ff864.png",
        "sha256": "23066a6d6d368f11c65a785274746104361a9be94a6aeba680652a705c5ff864"
      },
      {
        "path": "/data2/k6tk/ac/acb2a01196924d59b244f5738c83dabf0265939a58533cfa7786fdab01b78f83.png",
        "sha256": "acb2a01196924d59b244f5738c83dabf0265939a58533cfa7786fdab01b78f83"
      },
      {
        "path": "/data2/k6tk/e2/e23db66e3f07492b4d09bb488c6a8dbe1937cd810b235d61510dffe282082f47.png",
        "sha256": "e23db66e3f07492b4d09bb488c6a8dbe1937cd810b235d61510dffe282082f47"
      },
      {
        "path": "/data2/k6tk/f6/f69e5ce58dcb69f0f2d2ab72d37a082c990645edae9825cb4fbdf65562b1f36c.png",
        "sha256": "f69e5ce58dcb69f0f2d2ab72d37a082c990645edae9825cb4fbdf65562b1f36c"
      },
      {
        "path": "/data2/k6tk/25/252b25572f1f9a51740c523f1084e82daf8a8b3cdc56211926f3edf469c390ba.png",
        "sha256": "252b25572f1f9a51740c523f1084e82daf8a8b3cdc56211926f3edf469c390ba"
      },
      {
        "path": "/data2/k6tk/59/595986c5b2197afcde4a219e48df4e7a61c18e1aa7b5dbf6a834afacb72bd12b.png",
        "sha256": "595986c5b2197afcde4a219e48df4e7a61c18e1aa7b5dbf6a834afacb72bd12b"
      },
      {
        "path": "/data2/k6tk/0d/0dd23026e4d85d1331d843767ce09ba49275b69d782a3dd697d50203149dd3ad.png",
        "sha256": "0dd23026e4d85d1331d843767ce09ba49275b69d782a3dd697d50203149dd3ad"
      },
      {
        "path": "/data2/k6tk/2e/2e3d40f16c21e2fe099a7f53b525be939e203f2ff869ca8b611319a2543124fb.png",
        "sha256": "2e3d40f16c21e2fe099a7f53b525be939e203f2ff869ca8b611319a2543124fb"
      },
      {
        "path": "/data2/k6tk/55/551adceaffbfd11647c2981c5760136d6d63b9d425566d6d74f8446856d1b5e5.png",
        "sha256": "551adceaffbfd11647c2981c5760136d6d63b9d425566d6d74f8446856d1b5e5"
      },
      {
        "path": "/data2/k6tk/bb/bb7ec8c24e8dec0f5a4b42237a1d528484714138a25863d4463cb81ef1273e61.png",
        "sha256": "bb7ec8c24e8dec0f5a4b42237a1d528484714138a25863d4463cb81ef1273e61"
      },
      {
        "path": "/data2/k6tk/d8/d807b487f440a6d74da58460999940caa030991ca3bcdbd5395c64253e5e694b.png",
        "sha256": "d807b487f440a6d74da58460999940caa030991ca3bcdbd5395c64253e5e694b"
      },
      {
        "path": "/data2/k6tk/09/099b4641821ab17d36a32735589c11f19688ca50fd9248778e939013c27cfade.png",
        "sha256": "099b4641821ab17d36a32735589c11f19688ca50fd9248778e939013c27cfade"
      },
      {
        "path": "/data2/k6tk/2d/2d4495934522c9db2f2a8bcc55f58dfba86dfbd7195372dfa7c84694b5c699e8.png",
        "sha256": "2d4495934522c9db2f2a8bcc55f58dfba86dfbd7195372dfa7c84694b5c699e8"
      },
      {
        "path": "/data2/k6tk/60/60c16cadfadc53f50de8820f8edc388d3b9ef830c45cf53e662b3e5c8338ce77.png",
        "sha256": "60c16cadfadc53f50de8820f8edc388d3b9ef830c45cf53e662b3e5c8338ce77"
      },
      {
        "path": "/data2/k6tk/af/aff246cd9ad4e78e9f2e99efb97f8474bd51150e68d1787a120311451da3147e.png",
        "sha256": "aff246cd9ad4e78e9f2e99efb97f8474bd51150e68d1787a120311451da3147e"
      },
      {
        "path": "/data2/k6tk/d0/d09ddbdee73609f85976982b0871c326770c6f75ddb276ecd9a18bde7fa56c10.png",
        "sha256": "d09ddbdee73609f85976982b0871c326770c6f75ddb276ecd9a18bde7fa56c10"
      },
      {
        "path": "/data2/k6tk/84/84ebadcdd752b7be34656807e2dcbf978b5b5d2420a91b1c1e85c70ea6ea5b15.png",
        "sha256": "84ebadcdd752b7be34656807e2dcbf978b5b5d2420a91b1c1e85c70ea6ea5b15"
      },
      {
        "path": "/data2/k6tk/e4/e402bb834e60f5543d7fd5171a8714d1b45b58897f68339aeea76352c6e6c8e6.png",
        "sha256": "e402bb834e60f5543d7fd5171a8714d1b45b58897f68339aeea76352c6e6c8e6"
      },
      {
        "path": "/data2/k6tk/dc/dc5810e8991fa22df9ceeb88f78c2b9d0a21f76a620fa5fe66f72b4470ba2d2f.png",
        "sha256": "dc5810e8991fa22df9ceeb88f78c2b9d0a21f76a620fa5fe66f72b4470ba2d2f"
      },
      {
        "path": "/data2/k6tk/49/49f09caf26488b349d2129d2a50659ed00ac413a909a5c99215c373139250a4b.png",
        "sha256": "49f09caf26488b349d2129d2a50659ed00ac413a909a5c99215c373139250a4b"
      },
      {
        "path": "/data2/k6tk/02/0233390890997a94cf8b25791bfe2aa16e84a8df637d371312a795ff08b26ac8.png",
        "sha256": "0233390890997a94cf8b25791bfe2aa16e84a8df637d371312a795ff08b26ac8"
      },
      {
        "path": "/data2/k6tk/c7/c7dd51b81e75219c8bb969a506acf4edde440b1ef233b9536367b2b94a78da38.png",
        "sha256": "c7dd51b81e75219c8bb969a506acf4edde440b1ef233b9536367b2b94a78da38"
      },
      {
        "path": "/data2/k6tk/2d/2d60cd33a31ca13c383bc93adc7eebcf9d87dd66788cc82ebdb886e417f3e56f.png",
        "sha256": "2d60cd33a31ca13c383bc93adc7eebcf9d87dd66788cc82ebdb886e417f3e56f"
      },
      {
        "path": "/data2/k6tk/28/285bf6a3858bb6c6121a37d98d661cd299279d47e4ee3eb1a88fdc8d3815d1f8.png",
        "sha256": "285bf6a3858bb6c6121a37d98d661cd299279d47e4ee3eb1a88fdc8d3815d1f8"
      },
      {
        "path": "/data2/k6tk/80/80142494c6dd531795882010957b5a699addf634f6065a2d7e23a30245ac10f5.png",
        "sha256": "80142494c6dd531795882010957b5a699addf634f6065a2d7e23a30245ac10f5"
      },
      {
        "path": "/data2/k6tk/44/44236d26fd349e8a7045c22715957c5ae38141ae0490bc4365f9d8ae93a86a4c.png",
        "sha256": "44236d26fd349e8a7045c22715957c5ae38141ae0490bc4365f9d8ae93a86a4c"
      },
      {
        "path": "/data2/k6tk/d2/d206a6ab56c6dbc7ffe235596ddc026e7452800f8d7c3c63d9777d9510d35f26.png",
        "sha256": "d206a6ab56c6dbc7ffe235596ddc026e7452800f8d7c3c63d9777d9510d35f26"
      },
      {
        "path": "/data2/k6tk/48/48d24e2151132de2246afdb3de19b1f95e5873bd9d6df5964943411157c6e2e7.png",
        "sha256": "48d24e2151132de2246afdb3de19b1f95e5873bd9d6df5964943411157c6e2e7"
      }
    ],
    "options": [
      "A. left",
      "B. right",
      "C. back"
    ],
    "question": "If I am standing by the whiteboard and facing in the opposite direction of the telephone, is the cup to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      3.8666666666666667,
      7.733333333333333,
      11.616666666666667,
      15.483333333333333,
      19.366666666666667,
      23.233333333333334,
      27.116666666666667,
      30.983333333333334,
      34.86666666666667,
      38.733333333333334,
      42.6,
      46.483333333333334,
      50.35,
      54.233333333333334,
      58.1,
      61.983333333333334,
      65.85,
      69.73333333333333,
      73.6,
      77.48333333333333,
      81.35,
      85.21666666666667,
      89.1,
      92.96666666666667,
      96.85,
      100.71666666666667,
      104.6,
      108.46666666666667,
      112.35,
      116.21666666666667,
      120.1
    ],
    "total_num_frames": 7207
  },
  "target": "<think>\nSeen: whiteboard in frame 7; telephone in frame 10; cup in frame 5.\nIf I stood at the whiteboard facing the telephone, the cup would be ahead of me, slightly to my left.\nThe question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the cup at my back.\n</think>\n\nC",
  "validation_commit": ""
}
```

### Sample 19: vsi590k_136740_away_opp

Store index: 200414. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the rack and facing in the opposite direction of the microwave, is the pan to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: rack in frame 29; microwave in frame 25; pan in frame 19.
If I stood at the rack facing the microwave, the pan would be to my right.
The question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the pan to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_136740",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 130519,
      "derived_from_v6_qid": "vsi590k_136740_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "d085efa2e4a5ac5139d35b6f24a73da454dfc436f4c69c3e122919d6956cb9b7",
      "source_target_sha256": "7fe1310eb873a369665fe2a1e85f6aa8af32af269e5cc5b629cbb454c4832d1f",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9bf0518db09a07d8.jsonl.gz",
    "source_qid": "vsi590k_136740",
    "source_set": "T1H2_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_136740_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "va29ebd28602a",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_136740",
  "source_set": "T1H2_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      152,
      305,
      457,
      610,
      762,
      915,
      1067,
      1220,
      1372,
      1525,
      1677,
      1830,
      1982,
      2135,
      2287,
      2440,
      2592,
      2745,
      2897,
      3050,
      3202,
      3355,
      3507,
      3660,
      3812,
      3965,
      4117,
      4270,
      4422,
      4575,
      4728
    ],
    "frames": [
      {
        "path": "/data2/k6tk/d0/d023f9ed6c07292fe68039269bc60d684d82be286cd00e32daa261a275ad18ac.png",
        "sha256": "d023f9ed6c07292fe68039269bc60d684d82be286cd00e32daa261a275ad18ac"
      },
      {
        "path": "/data2/k6tk/d7/d72dbbd0bd7b9211a3c19921e37e23b23ccb0361c2532d2e0f257fe61d4f44df.png",
        "sha256": "d72dbbd0bd7b9211a3c19921e37e23b23ccb0361c2532d2e0f257fe61d4f44df"
      },
      {
        "path": "/data2/k6tk/29/29bd392b60872c3b8e7f7ef4ea1d6e7af949d14dde0000daa6f0486fec562f45.png",
        "sha256": "29bd392b60872c3b8e7f7ef4ea1d6e7af949d14dde0000daa6f0486fec562f45"
      },
      {
        "path": "/data2/k6tk/06/064ef8a6699ef525cb773637a6fb93cae56d6c987b4d9d3734e34999f53826ae.png",
        "sha256": "064ef8a6699ef525cb773637a6fb93cae56d6c987b4d9d3734e34999f53826ae"
      },
      {
        "path": "/data2/k6tk/a8/a88154b0f9cafaf70fd7ac7c9cc99c9b0e21ef8a59581bae89cfddaf98d88328.png",
        "sha256": "a88154b0f9cafaf70fd7ac7c9cc99c9b0e21ef8a59581bae89cfddaf98d88328"
      },
      {
        "path": "/data2/k6tk/b3/b360b1e641e0ef6492bcda40fa4235109109740428454fbe1495e8b1e9d07a22.png",
        "sha256": "b360b1e641e0ef6492bcda40fa4235109109740428454fbe1495e8b1e9d07a22"
      },
      {
        "path": "/data2/k6tk/20/2073b08eaf436e56879f715047b91cd9b463d6f79238c54df1258332dada4cb8.png",
        "sha256": "2073b08eaf436e56879f715047b91cd9b463d6f79238c54df1258332dada4cb8"
      },
      {
        "path": "/data2/k6tk/df/df1960ef8b616913c46f69970d2662c0599fed2e444184f60513693f8a4dc1cc.png",
        "sha256": "df1960ef8b616913c46f69970d2662c0599fed2e444184f60513693f8a4dc1cc"
      },
      {
        "path": "/data2/k6tk/9d/9d9b494b51be2fd7ddcf50040874af18e319b6db33b2c4bc531f4a116d58c8de.png",
        "sha256": "9d9b494b51be2fd7ddcf50040874af18e319b6db33b2c4bc531f4a116d58c8de"
      },
      {
        "path": "/data2/k6tk/e1/e113d1ba5e847f5b73b17981a9a10314af60d55071032ec14a0c878433caf150.png",
        "sha256": "e113d1ba5e847f5b73b17981a9a10314af60d55071032ec14a0c878433caf150"
      },
      {
        "path": "/data2/k6tk/ea/eacd1c6af4ed7eba96d664d24adb40cf0eb9a51389359e862253e85001f78a7f.png",
        "sha256": "eacd1c6af4ed7eba96d664d24adb40cf0eb9a51389359e862253e85001f78a7f"
      },
      {
        "path": "/data2/k6tk/62/627927e10f666dcd25b38df438950bc70c3b21f438ca389fab26d1957b06d436.png",
        "sha256": "627927e10f666dcd25b38df438950bc70c3b21f438ca389fab26d1957b06d436"
      },
      {
        "path": "/data2/k6tk/60/60065263af61eb6f257d2220e6cc2f49a474d2b2645b85562440f30666609d10.png",
        "sha256": "60065263af61eb6f257d2220e6cc2f49a474d2b2645b85562440f30666609d10"
      },
      {
        "path": "/data2/k6tk/a5/a5a5b5e50733a9f6c81003b0c2ea2dc55b0d8f05ca5660bee906dcf3a2cba41b.png",
        "sha256": "a5a5b5e50733a9f6c81003b0c2ea2dc55b0d8f05ca5660bee906dcf3a2cba41b"
      },
      {
        "path": "/data2/k6tk/65/65ab8e4432522ecf3301a0777c684bcf98a635e1ae823f4c178684a5adafacb3.png",
        "sha256": "65ab8e4432522ecf3301a0777c684bcf98a635e1ae823f4c178684a5adafacb3"
      },
      {
        "path": "/data2/k6tk/a3/a3a587b8037bfdb71d38062b6477cd8c87f124b5d4d07bb326d86b8cb1dbf5ff.png",
        "sha256": "a3a587b8037bfdb71d38062b6477cd8c87f124b5d4d07bb326d86b8cb1dbf5ff"
      },
      {
        "path": "/data2/k6tk/66/66b9c647427b4517bda928aa599a4f9cb7028fca436a63d726634526ca00f00e.png",
        "sha256": "66b9c647427b4517bda928aa599a4f9cb7028fca436a63d726634526ca00f00e"
      },
      {
        "path": "/data2/k6tk/95/95ba19464f4c9084bf925e95cd80a9a666172ef2818ff6c6c21841c23527df94.png",
        "sha256": "95ba19464f4c9084bf925e95cd80a9a666172ef2818ff6c6c21841c23527df94"
      },
      {
        "path": "/data2/k6tk/ff/ff8fe88a67a1f29086bc87be2bfb3359b902a26952f69dfb42a84249f6af0a74.png",
        "sha256": "ff8fe88a67a1f29086bc87be2bfb3359b902a26952f69dfb42a84249f6af0a74"
      },
      {
        "path": "/data2/k6tk/c7/c7ef4fe4ae304bbf7103497e5eb4c1f4902d2cb5488086cf122e4c6602f07c9c.png",
        "sha256": "c7ef4fe4ae304bbf7103497e5eb4c1f4902d2cb5488086cf122e4c6602f07c9c"
      },
      {
        "path": "/data2/k6tk/b4/b40cedb018f54fdd9bc652ac9c84f41d0882d2ac82310c90d73e776676637ffb.png",
        "sha256": "b40cedb018f54fdd9bc652ac9c84f41d0882d2ac82310c90d73e776676637ffb"
      },
      {
        "path": "/data2/k6tk/31/311dc3d0461491ef28ab39b739147309549508c02bdbc0c89330916422c47477.png",
        "sha256": "311dc3d0461491ef28ab39b739147309549508c02bdbc0c89330916422c47477"
      },
      {
        "path": "/data2/k6tk/ae/aea4ccc8dd16c92f97b7f8ef9cdb1b757c2500c8f2d9919cdb4f81a888002a68.png",
        "sha256": "aea4ccc8dd16c92f97b7f8ef9cdb1b757c2500c8f2d9919cdb4f81a888002a68"
      },
      {
        "path": "/data2/k6tk/ab/ab7ce245a2654d8fb160524db10848350d9d9614732cd828285e10d9b9ac869d.png",
        "sha256": "ab7ce245a2654d8fb160524db10848350d9d9614732cd828285e10d9b9ac869d"
      },
      {
        "path": "/data2/k6tk/a4/a404cf4568bd3dabe9147a28d97a7fdb3e4b420e3a44894578e0e7559950b516.png",
        "sha256": "a404cf4568bd3dabe9147a28d97a7fdb3e4b420e3a44894578e0e7559950b516"
      },
      {
        "path": "/data2/k6tk/1b/1bc310e7dba94bd2fc852afd19e751199b8819b1a45ec88e2e00c736a44b4db2.png",
        "sha256": "1bc310e7dba94bd2fc852afd19e751199b8819b1a45ec88e2e00c736a44b4db2"
      },
      {
        "path": "/data2/k6tk/79/793a6831c4c92827fd058035ca0025dd0eb604b45ae110a3fc7cde5666115008.png",
        "sha256": "793a6831c4c92827fd058035ca0025dd0eb604b45ae110a3fc7cde5666115008"
      },
      {
        "path": "/data2/k6tk/16/169cd1c10662f1fac69d1c2d005d885b72d309e0bc0a407c174ab26cd946699e.png",
        "sha256": "169cd1c10662f1fac69d1c2d005d885b72d309e0bc0a407c174ab26cd946699e"
      },
      {
        "path": "/data2/k6tk/28/281edba7d10788d50326e17918580e3fa5ab9628097e3a76caac194a4892ab4c.png",
        "sha256": "281edba7d10788d50326e17918580e3fa5ab9628097e3a76caac194a4892ab4c"
      },
      {
        "path": "/data2/k6tk/07/0765d7504ea1fd33947f488408a511ecf8d846d42ee67e46fadda6af66dc5cf6.png",
        "sha256": "0765d7504ea1fd33947f488408a511ecf8d846d42ee67e46fadda6af66dc5cf6"
      },
      {
        "path": "/data2/k6tk/d8/d8e4c1441edc78ba0748b485520ffe604afc9d50ec5f01f8afcfeb34c7fbf9e2.png",
        "sha256": "d8e4c1441edc78ba0748b485520ffe604afc9d50ec5f01f8afcfeb34c7fbf9e2"
      },
      {
        "path": "/data2/k6tk/1c/1cc9d8a6b6f8a546f69363c4d69dbf41652ffc58598d10f37328deaa9211a74c.png",
        "sha256": "1cc9d8a6b6f8a546f69363c4d69dbf41652ffc58598d10f37328deaa9211a74c"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the rack and facing in the opposite direction of the microwave, is the pan to my left or to my right?",
    "timestamps": [
      0.0,
      2.533333333333333,
      5.083333333333333,
      7.616666666666666,
      10.166666666666666,
      12.7,
      15.25,
      17.783333333333335,
      20.333333333333332,
      22.866666666666667,
      25.416666666666668,
      27.95,
      30.5,
      33.03333333333333,
      35.583333333333336,
      38.11666666666667,
      40.666666666666664,
      43.2,
      45.75,
      48.28333333333333,
      50.833333333333336,
      53.36666666666667,
      55.916666666666664,
      58.45,
      61.0,
      63.53333333333333,
      66.08333333333333,
      68.61666666666666,
      71.16666666666667,
      73.7,
      76.25,
      78.8
    ],
    "total_num_frames": 4729
  },
  "target": "<think>\nSeen: rack in frame 29; microwave in frame 25; pan in frame 19.\nIf I stood at the rack facing the microwave, the pan would be to my right.\nThe question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the pan to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 20: vsi590k_118272_away_opp

Store index: 201727. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the laptop and facing in the opposite direction of the door, is the coat hanger to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: laptop in frame 16; door in frame 31; coat hanger in frame 12.
If I stood at the laptop facing the door, the coat hanger would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the coat hanger at my back.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_118272",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 111133,
      "derived_from_v6_qid": "vsi590k_118272_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "99e8d901ea5c44d19e3a9ee65ba9f8ba21316288cbae7b1f5c89c26f82d0f04d",
      "source_target_sha256": "d0f69eeae093f3b66ca527e94032428f4f7568497d14e037e5d3dc6dbdf58c8c",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_118272",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_118272_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v5f6b9ccd3acb",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_118272",
  "source_set": "T0_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      215,
      431,
      647,
      863,
      1079,
      1295,
      1510,
      1726,
      1942,
      2158,
      2374,
      2590,
      2805,
      3021,
      3237,
      3453,
      3669,
      3885,
      4100,
      4316,
      4532,
      4748,
      4964,
      5180,
      5395,
      5611,
      5827,
      6043,
      6259,
      6475,
      6691
    ],
    "frames": [
      {
        "path": "/data2/k6tk/7a/7aff3d7955a68e9f328fea009cb46b78356d44134fd71038a847a1890773e278.png",
        "sha256": "7aff3d7955a68e9f328fea009cb46b78356d44134fd71038a847a1890773e278"
      },
      {
        "path": "/data2/k6tk/a3/a3c4e0619d4425e03443c0c90a55ad3423a90e5d4fad925452531323e8dd6b57.png",
        "sha256": "a3c4e0619d4425e03443c0c90a55ad3423a90e5d4fad925452531323e8dd6b57"
      },
      {
        "path": "/data2/k6tk/49/49925ff50d0597eff744e4ddf880bcde73524963ee34105d7c102fc66ee08081.png",
        "sha256": "49925ff50d0597eff744e4ddf880bcde73524963ee34105d7c102fc66ee08081"
      },
      {
        "path": "/data2/k6tk/68/6869c68425976cc723f457d6724d96df371feeeb57005d8a99385fa0b33db758.png",
        "sha256": "6869c68425976cc723f457d6724d96df371feeeb57005d8a99385fa0b33db758"
      },
      {
        "path": "/data2/k6tk/9c/9c56512c62b0f36ebf346c07c8dedc173eed62786a648f7fb95c01075ee105b3.png",
        "sha256": "9c56512c62b0f36ebf346c07c8dedc173eed62786a648f7fb95c01075ee105b3"
      },
      {
        "path": "/data2/k6tk/b0/b002297234b7de67fda775cad5c168a55da05bdb8fa30e5abb2a6666248ac315.png",
        "sha256": "b002297234b7de67fda775cad5c168a55da05bdb8fa30e5abb2a6666248ac315"
      },
      {
        "path": "/data2/k6tk/ba/ba18543d2c6543047a2e04efb03d1f81fcfd9c4fffd41bb9cc29d440f017a27d.png",
        "sha256": "ba18543d2c6543047a2e04efb03d1f81fcfd9c4fffd41bb9cc29d440f017a27d"
      },
      {
        "path": "/data2/k6tk/0b/0b85f74517f26c45bee30a5bddb0301b0c1d3e822ccdabb1dba82ec0802c24a7.png",
        "sha256": "0b85f74517f26c45bee30a5bddb0301b0c1d3e822ccdabb1dba82ec0802c24a7"
      },
      {
        "path": "/data2/k6tk/93/936184b01c0bb3dab1bffc069b08955368727922af3d3af7789e7c7ac1619278.png",
        "sha256": "936184b01c0bb3dab1bffc069b08955368727922af3d3af7789e7c7ac1619278"
      },
      {
        "path": "/data2/k6tk/85/859663fec9f8a8f4464e41d195cf96347aa6070df84e7a9ed7067549755120a5.png",
        "sha256": "859663fec9f8a8f4464e41d195cf96347aa6070df84e7a9ed7067549755120a5"
      },
      {
        "path": "/data2/k6tk/e9/e9ac623480dcef68b671f966371d1d4d947470515f947b50a58319760d58fe94.png",
        "sha256": "e9ac623480dcef68b671f966371d1d4d947470515f947b50a58319760d58fe94"
      },
      {
        "path": "/data2/k6tk/0e/0eef94f9e3ffbd8f706b32594bf82eac87af45df3c6bdd0ff122e58ddd90c31e.png",
        "sha256": "0eef94f9e3ffbd8f706b32594bf82eac87af45df3c6bdd0ff122e58ddd90c31e"
      },
      {
        "path": "/data2/k6tk/8c/8cc8804de77a62fe0c5c39cbe1805c094a7127629280eff33b9465fa3ef76810.png",
        "sha256": "8cc8804de77a62fe0c5c39cbe1805c094a7127629280eff33b9465fa3ef76810"
      },
      {
        "path": "/data2/k6tk/f0/f0de0ee40a8cb9cf0e83968300736c0ad7c37ec06566aedca6ab7f24e61ddfb4.png",
        "sha256": "f0de0ee40a8cb9cf0e83968300736c0ad7c37ec06566aedca6ab7f24e61ddfb4"
      },
      {
        "path": "/data2/k6tk/36/3607637d7bd022339abb84fb2e0776aa66b7828529fea486449f73a1ea5c252c.png",
        "sha256": "3607637d7bd022339abb84fb2e0776aa66b7828529fea486449f73a1ea5c252c"
      },
      {
        "path": "/data2/k6tk/99/992691a72a1cfffae4ad7975332269dcdbf4dcdd37ec1a50eee6ae2ef95a826f.png",
        "sha256": "992691a72a1cfffae4ad7975332269dcdbf4dcdd37ec1a50eee6ae2ef95a826f"
      },
      {
        "path": "/data2/k6tk/5a/5a965b4ede0bfd601d89a2e3ba149afbf2bb35d0d90edb638764c8780bb98f25.png",
        "sha256": "5a965b4ede0bfd601d89a2e3ba149afbf2bb35d0d90edb638764c8780bb98f25"
      },
      {
        "path": "/data2/k6tk/e3/e373f58ef137585e32a62b115a8a1fa3d2bb4e13ba655f0c5ad4d9da72053c8b.png",
        "sha256": "e373f58ef137585e32a62b115a8a1fa3d2bb4e13ba655f0c5ad4d9da72053c8b"
      },
      {
        "path": "/data2/k6tk/74/74f325c6410b2a1748b74f0887207bcf01e589c86ea8042b0b96b52864cf7d34.png",
        "sha256": "74f325c6410b2a1748b74f0887207bcf01e589c86ea8042b0b96b52864cf7d34"
      },
      {
        "path": "/data2/k6tk/f4/f444cfedfc3f094ba88ebb9b283a7dda1ff27859879f985f0598c860da6061e0.png",
        "sha256": "f444cfedfc3f094ba88ebb9b283a7dda1ff27859879f985f0598c860da6061e0"
      },
      {
        "path": "/data2/k6tk/e1/e1e213925367b80fcc74267ef376dd00ceafd0ed020a0994d8614cd4f86a9145.png",
        "sha256": "e1e213925367b80fcc74267ef376dd00ceafd0ed020a0994d8614cd4f86a9145"
      },
      {
        "path": "/data2/k6tk/d4/d4ae0447fae4beb64d405568e837ebcdbe89bec490e547e3d315cb230d5eb95a.png",
        "sha256": "d4ae0447fae4beb64d405568e837ebcdbe89bec490e547e3d315cb230d5eb95a"
      },
      {
        "path": "/data2/k6tk/52/522f341bace804d84a933824bd7c79c999f36ea3b109e628f65a7ca0244edee0.png",
        "sha256": "522f341bace804d84a933824bd7c79c999f36ea3b109e628f65a7ca0244edee0"
      },
      {
        "path": "/data2/k6tk/eb/eb236cd212ff0d9d53b0ccc799fd89de9bf670f1b0ca6d107c9197c8abea5d48.png",
        "sha256": "eb236cd212ff0d9d53b0ccc799fd89de9bf670f1b0ca6d107c9197c8abea5d48"
      },
      {
        "path": "/data2/k6tk/ff/ffca7bd2255da3a800ad11a0913f7d9cb1fa3a2520b190ab8910bc95c7c12a2e.png",
        "sha256": "ffca7bd2255da3a800ad11a0913f7d9cb1fa3a2520b190ab8910bc95c7c12a2e"
      },
      {
        "path": "/data2/k6tk/0c/0c427c019239a4c77968a32cf268fd61528fc7abe82141b8a1c051963caaa8a8.png",
        "sha256": "0c427c019239a4c77968a32cf268fd61528fc7abe82141b8a1c051963caaa8a8"
      },
      {
        "path": "/data2/k6tk/25/25d20d8ef2e0039b9984f11c625196ea9ff2dd1bdb31038a3d75435424439859.png",
        "sha256": "25d20d8ef2e0039b9984f11c625196ea9ff2dd1bdb31038a3d75435424439859"
      },
      {
        "path": "/data2/k6tk/52/52c45df85f97e35850fb33e555083e4b87eb3e90d107a2a84426bb726c614bc6.png",
        "sha256": "52c45df85f97e35850fb33e555083e4b87eb3e90d107a2a84426bb726c614bc6"
      },
      {
        "path": "/data2/k6tk/90/90ce8ee9f6b33ab9b023cfb98d7b88d3b9c588cb68720aaeec5c13a33173713e.png",
        "sha256": "90ce8ee9f6b33ab9b023cfb98d7b88d3b9c588cb68720aaeec5c13a33173713e"
      },
      {
        "path": "/data2/k6tk/29/29e6fde506aa24fa0f728809c4cedc7198e167ad8e1cc4e3307ea525df427029.png",
        "sha256": "29e6fde506aa24fa0f728809c4cedc7198e167ad8e1cc4e3307ea525df427029"
      },
      {
        "path": "/data2/k6tk/7e/7ecd5773322da7f7f7def9fb00dfb5142d299f032a29df221a29ce5de962dc19.png",
        "sha256": "7ecd5773322da7f7f7def9fb00dfb5142d299f032a29df221a29ce5de962dc19"
      },
      {
        "path": "/data2/k6tk/a6/a613f3baebc72c18d491314298f746c346f2c949c0e401b06ac5b9c72866bde7.png",
        "sha256": "a613f3baebc72c18d491314298f746c346f2c949c0e401b06ac5b9c72866bde7"
      }
    ],
    "options": [
      "A. right",
      "B. back",
      "C. left"
    ],
    "question": "If I am standing by the laptop and facing in the opposite direction of the door, is the coat hanger to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      3.5833333333333335,
      7.183333333333334,
      10.783333333333333,
      14.383333333333333,
      17.983333333333334,
      21.583333333333332,
      25.166666666666668,
      28.766666666666666,
      32.36666666666667,
      35.96666666666667,
      39.56666666666667,
      43.166666666666664,
      46.75,
      50.35,
      53.95,
      57.55,
      61.15,
      64.75,
      68.33333333333333,
      71.93333333333334,
      75.53333333333333,
      79.13333333333334,
      82.73333333333333,
      86.33333333333333,
      89.91666666666667,
      93.51666666666667,
      97.11666666666666,
      100.71666666666667,
      104.31666666666666,
      107.91666666666667,
      111.51666666666667
    ],
    "total_num_frames": 6692
  },
  "target": "<think>\nSeen: laptop in frame 16; door in frame 31; coat hanger in frame 12.\nIf I stood at the laptop facing the door, the coat hanger would be ahead of me, slightly to my left.\nThe question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the coat hanger at my back.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 21: vsi590k_131189_away_opp

Store index: 197482. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the trash can, is the shoes to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. back | C. right

Answer: B

```text
<think>
Seen: heater in frame 27; trash can in frame 1; shoes in frame 12.
If I stood at the heater facing the trash can, the shoes would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the shoes at my back.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_131189",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 130783,
      "derived_from_v6_qid": "vsi590k_131189_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "edbd31e28bf39fa7453bc99c4113d72f125815417b7a3fee808460c0fe367675",
      "source_target_sha256": "9172cf572950169283dadd4a064787698deddc96a5ea2ba8bbefee2c3b9f79be",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_131189",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_131189_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v14824749ac0b",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_131189",
  "source_set": "T0_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      393,
      787,
      1181,
      1575,
      1969,
      2363,
      2757,
      3151,
      3545,
      3939,
      4332,
      4726,
      5120,
      5514,
      5908,
      6302,
      6696,
      7090,
      7484,
      7878,
      8271,
      8665,
      9059,
      9453,
      9847,
      10241,
      10635,
      11029,
      11423,
      11817,
      12211
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ae/ae230c5b3c3bcc68fa2ba19f4188e90e32861b704b0c8f8281df2018ea74854a.png",
        "sha256": "ae230c5b3c3bcc68fa2ba19f4188e90e32861b704b0c8f8281df2018ea74854a"
      },
      {
        "path": "/data2/k6tk/b9/b9335e0c9ab6b7007d6d0a598e1ec5e9a891f9959a3866ce5ef700883d79f492.png",
        "sha256": "b9335e0c9ab6b7007d6d0a598e1ec5e9a891f9959a3866ce5ef700883d79f492"
      },
      {
        "path": "/data2/k6tk/df/df2ff758463acacdd846b9207c314d325138069320a3b6b8312a9c2925d685e3.png",
        "sha256": "df2ff758463acacdd846b9207c314d325138069320a3b6b8312a9c2925d685e3"
      },
      {
        "path": "/data2/k6tk/04/04b258348f0a7e4eccb1fe132575ce707383ebf341be0452dea9db1ea2172cbd.png",
        "sha256": "04b258348f0a7e4eccb1fe132575ce707383ebf341be0452dea9db1ea2172cbd"
      },
      {
        "path": "/data2/k6tk/de/de2f7c6d061dd1809b03256e6feaa09094a8fbe0b8008b064f63952d0586b132.png",
        "sha256": "de2f7c6d061dd1809b03256e6feaa09094a8fbe0b8008b064f63952d0586b132"
      },
      {
        "path": "/data2/k6tk/59/59edd28a2d1efb74fee0587deafa4507484413ff38291fb4c8f384d53c14172b.png",
        "sha256": "59edd28a2d1efb74fee0587deafa4507484413ff38291fb4c8f384d53c14172b"
      },
      {
        "path": "/data2/k6tk/dd/ddb6cf7d74edd89f3fc3f7402cd17d9a0559ac9e1f3e418cc5881506e22a5b19.png",
        "sha256": "ddb6cf7d74edd89f3fc3f7402cd17d9a0559ac9e1f3e418cc5881506e22a5b19"
      },
      {
        "path": "/data2/k6tk/a3/a34d2d4f4a2dd98d7c2fb2a6c7127ec0a3fef6294e1835b484c51c5d4235fdf5.png",
        "sha256": "a34d2d4f4a2dd98d7c2fb2a6c7127ec0a3fef6294e1835b484c51c5d4235fdf5"
      },
      {
        "path": "/data2/k6tk/56/5618936e5c8660836de5fe0a8675410656e8c32f79caf2d05091ba4116200f0d.png",
        "sha256": "5618936e5c8660836de5fe0a8675410656e8c32f79caf2d05091ba4116200f0d"
      },
      {
        "path": "/data2/k6tk/e7/e726bf0509aa91d9249e9593e0fb1ad97679a44d77d635445abc31379e670af2.png",
        "sha256": "e726bf0509aa91d9249e9593e0fb1ad97679a44d77d635445abc31379e670af2"
      },
      {
        "path": "/data2/k6tk/1f/1fb663f01acad1741cc31c73b4b1cc9b418fe89434c5347e45518dc7d15526e8.png",
        "sha256": "1fb663f01acad1741cc31c73b4b1cc9b418fe89434c5347e45518dc7d15526e8"
      },
      {
        "path": "/data2/k6tk/39/39c8cea4c891e6b69426c68caecf47d7fe000ed0918b30e5a48404aae25037ff.png",
        "sha256": "39c8cea4c891e6b69426c68caecf47d7fe000ed0918b30e5a48404aae25037ff"
      },
      {
        "path": "/data2/k6tk/ce/ce3eee96d8a5998fcbe2c60c5a0689a9944ce64d9d5de3b646a4f07483c5a5c2.png",
        "sha256": "ce3eee96d8a5998fcbe2c60c5a0689a9944ce64d9d5de3b646a4f07483c5a5c2"
      },
      {
        "path": "/data2/k6tk/c4/c47a91bd81504e1b2c33f92a6239898ab8fad44c78dd92281854e416560c01dc.png",
        "sha256": "c47a91bd81504e1b2c33f92a6239898ab8fad44c78dd92281854e416560c01dc"
      },
      {
        "path": "/data2/k6tk/24/24defea3c503e6171d3e6bb21bedbef6facd64380ce2c57662441a09c7887f2c.png",
        "sha256": "24defea3c503e6171d3e6bb21bedbef6facd64380ce2c57662441a09c7887f2c"
      },
      {
        "path": "/data2/k6tk/24/241016359084c9deaa9ad93893ab0d1c98ff8881c79c769bba3bb1d79837956c.png",
        "sha256": "241016359084c9deaa9ad93893ab0d1c98ff8881c79c769bba3bb1d79837956c"
      },
      {
        "path": "/data2/k6tk/d6/d6fc0a205cf50989830a0ec9f3689dd6066bbe532eca3574deb649b60f72dc6e.png",
        "sha256": "d6fc0a205cf50989830a0ec9f3689dd6066bbe532eca3574deb649b60f72dc6e"
      },
      {
        "path": "/data2/k6tk/30/303d1a2a441d39911eaa866d5ec221112377a3957d34648a9d1d019692e0af01.png",
        "sha256": "303d1a2a441d39911eaa866d5ec221112377a3957d34648a9d1d019692e0af01"
      },
      {
        "path": "/data2/k6tk/c9/c9ef3b7a89344595de710902d0e22e1b4deb2d63f8340a6ff699dd1f51e1e106.png",
        "sha256": "c9ef3b7a89344595de710902d0e22e1b4deb2d63f8340a6ff699dd1f51e1e106"
      },
      {
        "path": "/data2/k6tk/52/522fdfb0977264e3af3e0a776e124b699b842a218d21af34554406d125eb8640.png",
        "sha256": "522fdfb0977264e3af3e0a776e124b699b842a218d21af34554406d125eb8640"
      },
      {
        "path": "/data2/k6tk/ca/cacd9bebceab748ee14f77c6673f1cd737d694a910f61468fb64a9e44626e875.png",
        "sha256": "cacd9bebceab748ee14f77c6673f1cd737d694a910f61468fb64a9e44626e875"
      },
      {
        "path": "/data2/k6tk/50/50770d734d79005676610ff3c4f90316524825e6f5356929f4ce1a44f6fbc888.png",
        "sha256": "50770d734d79005676610ff3c4f90316524825e6f5356929f4ce1a44f6fbc888"
      },
      {
        "path": "/data2/k6tk/2d/2d51be31eb83a6dd0c1bbf6bacc96ac58b19bc2595acf98626d698f61892af94.png",
        "sha256": "2d51be31eb83a6dd0c1bbf6bacc96ac58b19bc2595acf98626d698f61892af94"
      },
      {
        "path": "/data2/k6tk/04/04773e0afd9a22bb797c3521a2214d1647978c0aa17b43ee3ceece0e24d17b83.png",
        "sha256": "04773e0afd9a22bb797c3521a2214d1647978c0aa17b43ee3ceece0e24d17b83"
      },
      {
        "path": "/data2/k6tk/7c/7cf3e08642f39d2e3476094f78cf7054850d53713b02764ebc5060bddb0ba90e.png",
        "sha256": "7cf3e08642f39d2e3476094f78cf7054850d53713b02764ebc5060bddb0ba90e"
      },
      {
        "path": "/data2/k6tk/e5/e5d57e4f1aa2417986616d900b0e91e97314e50022f5597eb31dd7390a5862e8.png",
        "sha256": "e5d57e4f1aa2417986616d900b0e91e97314e50022f5597eb31dd7390a5862e8"
      },
      {
        "path": "/data2/k6tk/35/350a84a06fca428edbc1899572681b9763368a747dfe77600095a7f5a9f96aec.png",
        "sha256": "350a84a06fca428edbc1899572681b9763368a747dfe77600095a7f5a9f96aec"
      },
      {
        "path": "/data2/k6tk/4e/4ed0c4f01cfd61b9ef2f56555fe5558aef5dad806932d36aaf3e56a05b0fbd71.png",
        "sha256": "4ed0c4f01cfd61b9ef2f56555fe5558aef5dad806932d36aaf3e56a05b0fbd71"
      },
      {
        "path": "/data2/k6tk/23/23db3f754e8df3c76e3ffebbf990050f431a47298b4cc5a05325a24c989240a2.png",
        "sha256": "23db3f754e8df3c76e3ffebbf990050f431a47298b4cc5a05325a24c989240a2"
      },
      {
        "path": "/data2/k6tk/48/48d9cc6fe6f64f3ec570b7fed8c1c3e654fb1edfc249341b20b94f8fd5f6471c.png",
        "sha256": "48d9cc6fe6f64f3ec570b7fed8c1c3e654fb1edfc249341b20b94f8fd5f6471c"
      },
      {
        "path": "/data2/k6tk/2b/2bfe62c61853b53b5bcc8dae141c3a3f0098ddebe0f323c723cf050d31ed08e5.png",
        "sha256": "2bfe62c61853b53b5bcc8dae141c3a3f0098ddebe0f323c723cf050d31ed08e5"
      },
      {
        "path": "/data2/k6tk/8e/8e5b10688bb36e1e682a8b27415adfd6c9d25f3a20f1b0a512910917f52b47c3.png",
        "sha256": "8e5b10688bb36e1e682a8b27415adfd6c9d25f3a20f1b0a512910917f52b47c3"
      }
    ],
    "options": [
      "A. left",
      "B. back",
      "C. right"
    ],
    "question": "If I am standing by the heater and facing in the opposite direction of the trash can, is the shoes to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      6.55,
      13.116666666666667,
      19.683333333333334,
      26.25,
      32.81666666666667,
      39.38333333333333,
      45.95,
      52.516666666666666,
      59.083333333333336,
      65.65,
      72.2,
      78.76666666666667,
      85.33333333333333,
      91.9,
      98.46666666666667,
      105.03333333333333,
      111.6,
      118.16666666666667,
      124.73333333333333,
      131.3,
      137.85,
      144.41666666666666,
      150.98333333333332,
      157.55,
      164.11666666666667,
      170.68333333333334,
      177.25,
      183.81666666666666,
      190.38333333333333,
      196.95,
      203.51666666666668
    ],
    "total_num_frames": 12212
  },
  "target": "<think>\nSeen: heater in frame 27; trash can in frame 1; shoes in frame 12.\nIf I stood at the heater facing the trash can, the shoes would be ahead of me, slightly to my left.\nThe question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the shoes at my back.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 22: vsi590k_140376_away_opp

Store index: 204393. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the keyboard and facing in the opposite direction of the printer, is the monitor to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: keyboard in frame 10; printer in frame 10; monitor in frame 19.
If I stood at the keyboard facing the printer, the monitor would be to my right.
The question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the monitor to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_140376",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 134015,
      "derived_from_v6_qid": "vsi590k_140376_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "30259690f02e091870b80c71562dd9dae3a4ef4b4308e092b96647f9c7252398",
      "source_target_sha256": "cf9989b45dc14c09ea808252de8ad7e0982b6df6d66e64905393cd9933637946",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_140376",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_140376_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vd51d66a55048",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_140376",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      519,
      1039,
      1558,
      2078,
      2598,
      3117,
      3637,
      4156,
      4676,
      5196,
      5715,
      6235,
      6754,
      7274,
      7794,
      8313,
      8833,
      9353,
      9872,
      10392,
      10911,
      11431,
      11951,
      12470,
      12990,
      13509,
      14029,
      14549,
      15068,
      15588,
      16108
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9c/9c35ad1cc30153a8bb25175e8317d011de08ef5bea570c9bca01eaa3dc7c1443.png",
        "sha256": "9c35ad1cc30153a8bb25175e8317d011de08ef5bea570c9bca01eaa3dc7c1443"
      },
      {
        "path": "/data2/k6tk/ba/ba9ff35e0b1a41e672bd05a72217382bd74845c380f0095d463aea26c087ba17.png",
        "sha256": "ba9ff35e0b1a41e672bd05a72217382bd74845c380f0095d463aea26c087ba17"
      },
      {
        "path": "/data2/k6tk/3a/3aa9fe1fefd7c55549e18e63d2d847d7016dfc629e4d565c86b77f3aa91d076a.png",
        "sha256": "3aa9fe1fefd7c55549e18e63d2d847d7016dfc629e4d565c86b77f3aa91d076a"
      },
      {
        "path": "/data2/k6tk/d2/d2a35beb0a6b3d6d04062fd727ff7688612d711e562e8baa73108c2256c29cc6.png",
        "sha256": "d2a35beb0a6b3d6d04062fd727ff7688612d711e562e8baa73108c2256c29cc6"
      },
      {
        "path": "/data2/k6tk/43/4309671ad8ab0aee8a189d42c8a52d41d56fbd02231e3f737e5601e8345e3d30.png",
        "sha256": "4309671ad8ab0aee8a189d42c8a52d41d56fbd02231e3f737e5601e8345e3d30"
      },
      {
        "path": "/data2/k6tk/df/df2f35ead7400f57f8fac20eb177929482d27d23616de4c9a631bb033294c922.png",
        "sha256": "df2f35ead7400f57f8fac20eb177929482d27d23616de4c9a631bb033294c922"
      },
      {
        "path": "/data2/k6tk/8f/8f415b1257fcf920f24b71c967c5ab2610bd3aa5d3326df6d51e68b19c6c05cc.png",
        "sha256": "8f415b1257fcf920f24b71c967c5ab2610bd3aa5d3326df6d51e68b19c6c05cc"
      },
      {
        "path": "/data2/k6tk/7b/7bbf7e2281fa223d73025ed5783bd18a2abdb278c309c2f9bce4652e1fe1e426.png",
        "sha256": "7bbf7e2281fa223d73025ed5783bd18a2abdb278c309c2f9bce4652e1fe1e426"
      },
      {
        "path": "/data2/k6tk/56/5604c494cc05cc60e366720931f22960171de4fc9c6abae711d49616df35437c.png",
        "sha256": "5604c494cc05cc60e366720931f22960171de4fc9c6abae711d49616df35437c"
      },
      {
        "path": "/data2/k6tk/ca/ca62a315c600d560988292a3cfd80f35e4350c5c901e0f491de7bc76d6a7d4ba.png",
        "sha256": "ca62a315c600d560988292a3cfd80f35e4350c5c901e0f491de7bc76d6a7d4ba"
      },
      {
        "path": "/data2/k6tk/e1/e1f38b077c5565cb1f33e1a124144d8c37687f7364ae64d2d0d21157e59c3a4f.png",
        "sha256": "e1f38b077c5565cb1f33e1a124144d8c37687f7364ae64d2d0d21157e59c3a4f"
      },
      {
        "path": "/data2/k6tk/1b/1b7a633595310326f689720325deb4e0a8095420613e8447682835db2f405f30.png",
        "sha256": "1b7a633595310326f689720325deb4e0a8095420613e8447682835db2f405f30"
      },
      {
        "path": "/data2/k6tk/b8/b8fe048355a2a93a63c4297090cd58c30b5d993d997a97e913b78a1fb1a42f6a.png",
        "sha256": "b8fe048355a2a93a63c4297090cd58c30b5d993d997a97e913b78a1fb1a42f6a"
      },
      {
        "path": "/data2/k6tk/83/83261308504c5e542edaa4071ae92e256d372c9b51ad90f791395e4f5b14d229.png",
        "sha256": "83261308504c5e542edaa4071ae92e256d372c9b51ad90f791395e4f5b14d229"
      },
      {
        "path": "/data2/k6tk/b2/b261e6a12851eb696e6fc6e3d94bfd1f9fd0a325c49dc76a5e5a5bf1020bfd70.png",
        "sha256": "b261e6a12851eb696e6fc6e3d94bfd1f9fd0a325c49dc76a5e5a5bf1020bfd70"
      },
      {
        "path": "/data2/k6tk/59/593e7631af8f583210850d199b66ee8402634e5e1083dd9c3212bc6b342d0ec7.png",
        "sha256": "593e7631af8f583210850d199b66ee8402634e5e1083dd9c3212bc6b342d0ec7"
      },
      {
        "path": "/data2/k6tk/ee/ee38aefe5100524a5131343abbb1a60304d1761b1464d41e7c182f07fd115df8.png",
        "sha256": "ee38aefe5100524a5131343abbb1a60304d1761b1464d41e7c182f07fd115df8"
      },
      {
        "path": "/data2/k6tk/68/68a23f6cc9e5bf7ef4978ba3de16f1beb6c8d47fd7f013ae7deb581a4547f0d8.png",
        "sha256": "68a23f6cc9e5bf7ef4978ba3de16f1beb6c8d47fd7f013ae7deb581a4547f0d8"
      },
      {
        "path": "/data2/k6tk/a7/a73bd1213d97b3232962c6d0ae1ffb09e06d046aa2ff016bea4288a30a03fab5.png",
        "sha256": "a73bd1213d97b3232962c6d0ae1ffb09e06d046aa2ff016bea4288a30a03fab5"
      },
      {
        "path": "/data2/k6tk/28/28e2c373e87edf077ff877863eb252473b9d10b2d1f3b25172b27d6b1d898144.png",
        "sha256": "28e2c373e87edf077ff877863eb252473b9d10b2d1f3b25172b27d6b1d898144"
      },
      {
        "path": "/data2/k6tk/5b/5b0e7ae4fce506b84f97f7877201755e294afb1690ddcaa53b50719448d6219a.png",
        "sha256": "5b0e7ae4fce506b84f97f7877201755e294afb1690ddcaa53b50719448d6219a"
      },
      {
        "path": "/data2/k6tk/ef/ef72c0e26f51c47a4f70201801690ef3a2608e1cdf2cfa48deb5978839ded982.png",
        "sha256": "ef72c0e26f51c47a4f70201801690ef3a2608e1cdf2cfa48deb5978839ded982"
      },
      {
        "path": "/data2/k6tk/78/7815df762b2c8f34438b29f9a1d1848cb05ef355abc5daa62c2108c44cbb0e46.png",
        "sha256": "7815df762b2c8f34438b29f9a1d1848cb05ef355abc5daa62c2108c44cbb0e46"
      },
      {
        "path": "/data2/k6tk/15/15232459719fa3c50959905a6130d9ca6aeae79d91e72048ef20f7753d2ecf28.png",
        "sha256": "15232459719fa3c50959905a6130d9ca6aeae79d91e72048ef20f7753d2ecf28"
      },
      {
        "path": "/data2/k6tk/36/363bca7f212eda6f44604ab568aac53d0b8dc6e235c523c543dc72e214ca6545.png",
        "sha256": "363bca7f212eda6f44604ab568aac53d0b8dc6e235c523c543dc72e214ca6545"
      },
      {
        "path": "/data2/k6tk/98/9862adc9b0997e5c07a31da70c8707dc6833960d65d53b73eee5980155450b3c.png",
        "sha256": "9862adc9b0997e5c07a31da70c8707dc6833960d65d53b73eee5980155450b3c"
      },
      {
        "path": "/data2/k6tk/9b/9bcefe67f8b7573bcc6ecb4367bf5694aad5b0f59d972f51d5bdd97a38321b5d.png",
        "sha256": "9bcefe67f8b7573bcc6ecb4367bf5694aad5b0f59d972f51d5bdd97a38321b5d"
      },
      {
        "path": "/data2/k6tk/a3/a3a1392f92deaf78c29b80895c0da3cefa220b88ed0322ce60941668233e52d6.png",
        "sha256": "a3a1392f92deaf78c29b80895c0da3cefa220b88ed0322ce60941668233e52d6"
      },
      {
        "path": "/data2/k6tk/f9/f92f8fdb87095df5c7c981b88da78f349e2f360d710fccdffadb72b23cfa43a3.png",
        "sha256": "f92f8fdb87095df5c7c981b88da78f349e2f360d710fccdffadb72b23cfa43a3"
      },
      {
        "path": "/data2/k6tk/22/22423a87ad9996ca08bd047577fccaea83e461d03fa70cb8ceb23c178b86c716.png",
        "sha256": "22423a87ad9996ca08bd047577fccaea83e461d03fa70cb8ceb23c178b86c716"
      },
      {
        "path": "/data2/k6tk/c1/c1a0199b348a39aeed097174f454518cdf2f2f7b47485f21023e524981aeeb2e.png",
        "sha256": "c1a0199b348a39aeed097174f454518cdf2f2f7b47485f21023e524981aeeb2e"
      },
      {
        "path": "/data2/k6tk/a2/a238f92786a1f79c89d7ab45b4a6142596b7b9da066d4f585ca730662689d2bf.png",
        "sha256": "a238f92786a1f79c89d7ab45b4a6142596b7b9da066d4f585ca730662689d2bf"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the keyboard and facing in the opposite direction of the printer, is the monitor to my left or to my right?",
    "timestamps": [
      0.0,
      8.65,
      17.316666666666666,
      25.966666666666665,
      34.63333333333333,
      43.3,
      51.95,
      60.61666666666667,
      69.26666666666667,
      77.93333333333334,
      86.6,
      95.25,
      103.91666666666667,
      112.56666666666666,
      121.23333333333333,
      129.9,
      138.55,
      147.21666666666667,
      155.88333333333333,
      164.53333333333333,
      173.2,
      181.85,
      190.51666666666668,
      199.18333333333334,
      207.83333333333334,
      216.5,
      225.15,
      233.81666666666666,
      242.48333333333332,
      251.13333333333333,
      259.8,
      268.46666666666664
    ],
    "total_num_frames": 16109
  },
  "target": "<think>\nSeen: keyboard in frame 10; printer in frame 10; monitor in frame 19.\nIf I stood at the keyboard facing the printer, the monitor would be to my right.\nThe question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the monitor to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 23: vsi590k_023346_away_opp

Store index: 199316. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the trash can, is the plant to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: B

```text
<think>
Seen: door in frame 3; trash can in frame 17; plant in frame 4.
If I stood at the door facing the trash can, the plant would be behind me, on my left.
The question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the plant to my right.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_023346",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 136639,
      "derived_from_v6_qid": "vsi590k_023346_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "58818ca4f6ee0cf0da1fc4b2d0ce89bd3e8935d1adc637cf63d1b92ae63f90ee",
      "source_target_sha256": "81b16d3b48415b301e68cd1c537c06d73f8b941711bec53fadc8ad1d75902f65",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_023346",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_023346_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "ve5576e75c5a1",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_023346",
  "source_set": "T0_gen_r2",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      61,
      123,
      184,
      246,
      307,
      369,
      430,
      492,
      553,
      615,
      677,
      738,
      800,
      861,
      923,
      984,
      1046,
      1107,
      1169,
      1230,
      1292,
      1354,
      1415,
      1477,
      1538,
      1600,
      1661,
      1723,
      1784,
      1846,
      1908
    ],
    "frames": [
      {
        "path": "/data2/k6tk/39/39098490a8fd1f76b80843d448d184e8e8d776c733c6bddb5a6fdd87d75f785e.png",
        "sha256": "39098490a8fd1f76b80843d448d184e8e8d776c733c6bddb5a6fdd87d75f785e"
      },
      {
        "path": "/data2/k6tk/b2/b26e4e52960c2ac498d13502e1e6b140a6ebf872d3a2e1c4066271bc3b2ff1ce.png",
        "sha256": "b26e4e52960c2ac498d13502e1e6b140a6ebf872d3a2e1c4066271bc3b2ff1ce"
      },
      {
        "path": "/data2/k6tk/f9/f928fb1433e5146cdcc613aad0282742fb39491f78214322517b110c3a239af5.png",
        "sha256": "f928fb1433e5146cdcc613aad0282742fb39491f78214322517b110c3a239af5"
      },
      {
        "path": "/data2/k6tk/73/733b76c09916efa27377af3e7a1ed2e098fa2e177d9b50013330c2c41fc3c0b4.png",
        "sha256": "733b76c09916efa27377af3e7a1ed2e098fa2e177d9b50013330c2c41fc3c0b4"
      },
      {
        "path": "/data2/k6tk/44/4466b16f9d25f31481b5feb1e8ea3c6c43360ea888c55a21ca6ab7f884966610.png",
        "sha256": "4466b16f9d25f31481b5feb1e8ea3c6c43360ea888c55a21ca6ab7f884966610"
      },
      {
        "path": "/data2/k6tk/45/45c8d4467adc6e05e009cd0a4a1857dedbb9e3feabb0a317f7d9ef6be6adfba0.png",
        "sha256": "45c8d4467adc6e05e009cd0a4a1857dedbb9e3feabb0a317f7d9ef6be6adfba0"
      },
      {
        "path": "/data2/k6tk/e3/e344ea8152764efaf205b69b078e027abb5841214794ea2ac4e27fe3d40ce5fb.png",
        "sha256": "e344ea8152764efaf205b69b078e027abb5841214794ea2ac4e27fe3d40ce5fb"
      },
      {
        "path": "/data2/k6tk/fe/fee6018d790a543bfd01c720b2dc4f4a598840c698377a5ee0bdce8ab9c3a808.png",
        "sha256": "fee6018d790a543bfd01c720b2dc4f4a598840c698377a5ee0bdce8ab9c3a808"
      },
      {
        "path": "/data2/k6tk/d8/d8913ffa7c7e6ebb2e5b141d8f5643818bc07cd70dd7c48eb73014e1ec4e5d62.png",
        "sha256": "d8913ffa7c7e6ebb2e5b141d8f5643818bc07cd70dd7c48eb73014e1ec4e5d62"
      },
      {
        "path": "/data2/k6tk/89/89d0c97c7feb4ce8601f2217c2672288b873062c19aadf6e1797c6ccf123ef55.png",
        "sha256": "89d0c97c7feb4ce8601f2217c2672288b873062c19aadf6e1797c6ccf123ef55"
      },
      {
        "path": "/data2/k6tk/71/71a4b6552fe577d0244b5a6ef43e1e65b07b9c24410bbe9cf348b933d0d14d0c.png",
        "sha256": "71a4b6552fe577d0244b5a6ef43e1e65b07b9c24410bbe9cf348b933d0d14d0c"
      },
      {
        "path": "/data2/k6tk/ae/ae1c918e25a7c3b51efcbc868bcd497932269af55e4efc9fac66a475e957caf7.png",
        "sha256": "ae1c918e25a7c3b51efcbc868bcd497932269af55e4efc9fac66a475e957caf7"
      },
      {
        "path": "/data2/k6tk/49/499c5030bc6dbfc87936b12bdeb4f477185f9eb0b66a5945a825145fbc495f12.png",
        "sha256": "499c5030bc6dbfc87936b12bdeb4f477185f9eb0b66a5945a825145fbc495f12"
      },
      {
        "path": "/data2/k6tk/f4/f41a429c1b93596ce0a8bf32a428890c0be66462d94539bde493caec63441d32.png",
        "sha256": "f41a429c1b93596ce0a8bf32a428890c0be66462d94539bde493caec63441d32"
      },
      {
        "path": "/data2/k6tk/a8/a8399b2de19f0e186ce3263a21ff27c9d3a19d465b9e6326a3ae8eb6c28aafcb.png",
        "sha256": "a8399b2de19f0e186ce3263a21ff27c9d3a19d465b9e6326a3ae8eb6c28aafcb"
      },
      {
        "path": "/data2/k6tk/44/4418eea29f1a8d7eac42b8ca7946592019986570a838d4411482ff4c35c77493.png",
        "sha256": "4418eea29f1a8d7eac42b8ca7946592019986570a838d4411482ff4c35c77493"
      },
      {
        "path": "/data2/k6tk/67/6770d8d07057e6e15acdcbc94ba787aaafe46fe88965a7bd9869c7dd111253b0.png",
        "sha256": "6770d8d07057e6e15acdcbc94ba787aaafe46fe88965a7bd9869c7dd111253b0"
      },
      {
        "path": "/data2/k6tk/c1/c13a92c735f2a0ebc2691b76198eb5d51efcae6a92d59601f1879ab5362224ec.png",
        "sha256": "c13a92c735f2a0ebc2691b76198eb5d51efcae6a92d59601f1879ab5362224ec"
      },
      {
        "path": "/data2/k6tk/4d/4dc180b3a31de864cf0c8975076bf426a4a7a0da53dd0762944392a48f080ac3.png",
        "sha256": "4dc180b3a31de864cf0c8975076bf426a4a7a0da53dd0762944392a48f080ac3"
      },
      {
        "path": "/data2/k6tk/b8/b85247e2edee5abf1db78ac2c1a7850263dd826db5e82066522a4dadaca1ff5c.png",
        "sha256": "b85247e2edee5abf1db78ac2c1a7850263dd826db5e82066522a4dadaca1ff5c"
      },
      {
        "path": "/data2/k6tk/fa/fa53524edff2122b840f65f1ab092686d9308ac6387755cf16cd1cc993219f2e.png",
        "sha256": "fa53524edff2122b840f65f1ab092686d9308ac6387755cf16cd1cc993219f2e"
      },
      {
        "path": "/data2/k6tk/54/547a7bbea0caf8f3e31fc8022fbaed0083339629150ffe1f3a06ac6e620ac3e9.png",
        "sha256": "547a7bbea0caf8f3e31fc8022fbaed0083339629150ffe1f3a06ac6e620ac3e9"
      },
      {
        "path": "/data2/k6tk/9e/9e5cc8c0cedf874a22dac2863ba2f8206c31f8e838c2a0c6d05b0ead7f9cfe0c.png",
        "sha256": "9e5cc8c0cedf874a22dac2863ba2f8206c31f8e838c2a0c6d05b0ead7f9cfe0c"
      },
      {
        "path": "/data2/k6tk/2b/2b8e345afe6e273732c03c4dec8bd32fb1bb6b56342467c80352647bc20b8e2a.png",
        "sha256": "2b8e345afe6e273732c03c4dec8bd32fb1bb6b56342467c80352647bc20b8e2a"
      },
      {
        "path": "/data2/k6tk/1a/1ad55e8b03ba8339e27b32ef083207260985d5bb4f0891d291db1873ac168241.png",
        "sha256": "1ad55e8b03ba8339e27b32ef083207260985d5bb4f0891d291db1873ac168241"
      },
      {
        "path": "/data2/k6tk/11/1107c7734266f33565ecd43ddd3afac4229485178a67e6a8a239a59127158f48.png",
        "sha256": "1107c7734266f33565ecd43ddd3afac4229485178a67e6a8a239a59127158f48"
      },
      {
        "path": "/data2/k6tk/c6/c64087d72fbfb16526c56e312960973ef0e0445bc833a5cbb2d6803e1d14808d.png",
        "sha256": "c64087d72fbfb16526c56e312960973ef0e0445bc833a5cbb2d6803e1d14808d"
      },
      {
        "path": "/data2/k6tk/d1/d1b36de348fc2f60aa378da4b49a6f28d842d1dafdac4d0b69e4a7dffa968fe0.png",
        "sha256": "d1b36de348fc2f60aa378da4b49a6f28d842d1dafdac4d0b69e4a7dffa968fe0"
      },
      {
        "path": "/data2/k6tk/bc/bc4c46320a05400d784dab2650acf9aecf1d6ff0056e4fb15b844000fa596d41.png",
        "sha256": "bc4c46320a05400d784dab2650acf9aecf1d6ff0056e4fb15b844000fa596d41"
      },
      {
        "path": "/data2/k6tk/fe/feb896eaccf485b30dcab209afe8f806d9db34d505092f0517ddfce2289d1a6e.png",
        "sha256": "feb896eaccf485b30dcab209afe8f806d9db34d505092f0517ddfce2289d1a6e"
      },
      {
        "path": "/data2/k6tk/3f/3f6c8d3f6bce3b33f325e0c60ec2e4119021b8e2df9314cb756b9969204ed2e4.png",
        "sha256": "3f6c8d3f6bce3b33f325e0c60ec2e4119021b8e2df9314cb756b9969204ed2e4"
      },
      {
        "path": "/data2/k6tk/45/45f9a69849b383e44b61574688f697592214d5b01de909f0a8a0cb009f8c0324.png",
        "sha256": "45f9a69849b383e44b61574688f697592214d5b01de909f0a8a0cb009f8c0324"
      }
    ],
    "options": [
      "A. left",
      "B. right",
      "C. back"
    ],
    "question": "If I am standing by the door and facing in the opposite direction of the trash can, is the plant to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      2.5416666666666665,
      5.125,
      7.666666666666667,
      10.25,
      12.791666666666666,
      15.375,
      17.916666666666668,
      20.5,
      23.041666666666668,
      25.625,
      28.208333333333332,
      30.75,
      33.333333333333336,
      35.875,
      38.458333333333336,
      41.0,
      43.583333333333336,
      46.125,
      48.708333333333336,
      51.25,
      53.833333333333336,
      56.416666666666664,
      58.958333333333336,
      61.541666666666664,
      64.08333333333333,
      66.66666666666667,
      69.20833333333333,
      71.79166666666667,
      74.33333333333333,
      76.91666666666667,
      79.5
    ],
    "total_num_frames": 1909
  },
  "target": "<think>\nSeen: door in frame 3; trash can in frame 17; plant in frame 4.\nIf I stood at the door facing the trash can, the plant would be behind me, on my left.\nThe question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the plant to my right.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 24: vsi590k_153780_away_opp

Store index: 202295. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the basket and facing in the opposite direction of the ceiling lamp, is the heater to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: basket in frame 1; ceiling lamp in frame 29; heater in frame 25.
If I stood at the basket facing the ceiling lamp, the heater would be to my left.
The question has me facing in the opposite direction of the ceiling lamp. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my right.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_153780",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 118885,
      "derived_from_v6_qid": "vsi590k_153780_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "1e9913f3dea650e368ce499d780e79ed910212334bda30bc488052fd75773310",
      "source_target_sha256": "e1042a0ff80d60f3eb3b7fc6b0c96e0298f1b0c7b9be7c21e376587fce3e3575",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_153780",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_153780_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vc568a902c996",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_153780",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      223,
      446,
      670,
      893,
      1117,
      1340,
      1564,
      1787,
      2011,
      2234,
      2457,
      2681,
      2904,
      3128,
      3351,
      3575,
      3798,
      4022,
      4245,
      4469,
      4692,
      4915,
      5139,
      5362,
      5586,
      5809,
      6033,
      6256,
      6480,
      6703,
      6927
    ],
    "frames": [
      {
        "path": "/data2/k6tk/37/37e198de77d87c4dcf2cd88d914dbc9bcf79cb6dcb55e0a49eb7e60c5d3392f2.png",
        "sha256": "37e198de77d87c4dcf2cd88d914dbc9bcf79cb6dcb55e0a49eb7e60c5d3392f2"
      },
      {
        "path": "/data2/k6tk/da/da2cd264af9096896e582aa3c5ab250f86f9191f2c8e66610082eb2862d4c30c.png",
        "sha256": "da2cd264af9096896e582aa3c5ab250f86f9191f2c8e66610082eb2862d4c30c"
      },
      {
        "path": "/data2/k6tk/0c/0c6fbabe51bc2d340b0703296cbdf8f016cffd076c7b85d034126fa44db7b5ad.png",
        "sha256": "0c6fbabe51bc2d340b0703296cbdf8f016cffd076c7b85d034126fa44db7b5ad"
      },
      {
        "path": "/data2/k6tk/6f/6fa1d4ac97f216ec68f5cbeead96fbcfc4ee1144ab2539477237468b7b66414e.png",
        "sha256": "6fa1d4ac97f216ec68f5cbeead96fbcfc4ee1144ab2539477237468b7b66414e"
      },
      {
        "path": "/data2/k6tk/55/55d84f261362b360879738f3cd119c76bcf08afcf810e1609e966ed49d7b28ba.png",
        "sha256": "55d84f261362b360879738f3cd119c76bcf08afcf810e1609e966ed49d7b28ba"
      },
      {
        "path": "/data2/k6tk/e1/e12dfa61866bcd8ba539edd018d3951f7887d5c49ea6137711070cd1a8d55262.png",
        "sha256": "e12dfa61866bcd8ba539edd018d3951f7887d5c49ea6137711070cd1a8d55262"
      },
      {
        "path": "/data2/k6tk/42/421c8f9a201f9f9ca1c390fbd1d16a86523a60b1f58dcb01b708da09dcce7a48.png",
        "sha256": "421c8f9a201f9f9ca1c390fbd1d16a86523a60b1f58dcb01b708da09dcce7a48"
      },
      {
        "path": "/data2/k6tk/97/97f20f92faeb49264c934b4cc00f5b4db33b8801f899cfb7e77dbc010b31c7dc.png",
        "sha256": "97f20f92faeb49264c934b4cc00f5b4db33b8801f899cfb7e77dbc010b31c7dc"
      },
      {
        "path": "/data2/k6tk/e7/e7213efdf4e4e0b204a705a02078a08ec9aa104a628d434fcdcb23eda65a93a9.png",
        "sha256": "e7213efdf4e4e0b204a705a02078a08ec9aa104a628d434fcdcb23eda65a93a9"
      },
      {
        "path": "/data2/k6tk/d1/d1c14fb7cdc100fd6bb3e7e7f5b2cd55183dba7c0db119e19d097e740aacfe5e.png",
        "sha256": "d1c14fb7cdc100fd6bb3e7e7f5b2cd55183dba7c0db119e19d097e740aacfe5e"
      },
      {
        "path": "/data2/k6tk/42/42b7ed2b64faa277993fb85064df649c375f756bc75a78f72d1887d2732b5829.png",
        "sha256": "42b7ed2b64faa277993fb85064df649c375f756bc75a78f72d1887d2732b5829"
      },
      {
        "path": "/data2/k6tk/5a/5a93928cf56e618e461b40b9a2c2b0e900dd48f1a2ab10825543e19ceee6a9fd.png",
        "sha256": "5a93928cf56e618e461b40b9a2c2b0e900dd48f1a2ab10825543e19ceee6a9fd"
      },
      {
        "path": "/data2/k6tk/d2/d2240f7749b08ec24f72a9f5e55cfe54a2bf0e8f046e395514933ccb6c588a9c.png",
        "sha256": "d2240f7749b08ec24f72a9f5e55cfe54a2bf0e8f046e395514933ccb6c588a9c"
      },
      {
        "path": "/data2/k6tk/11/11f5a4e9e8aabc9f014dad6dbd900f7f6439c6520908559f60fd829f5d000f0b.png",
        "sha256": "11f5a4e9e8aabc9f014dad6dbd900f7f6439c6520908559f60fd829f5d000f0b"
      },
      {
        "path": "/data2/k6tk/6b/6bf579d467786f781de170d1b1045397c99d2b9118a1584ebeb2a3926544fe1e.png",
        "sha256": "6bf579d467786f781de170d1b1045397c99d2b9118a1584ebeb2a3926544fe1e"
      },
      {
        "path": "/data2/k6tk/4e/4e66d1b182bb53117e2cd18f52ff1a3e96775f0126bf1057be1181917b286b84.png",
        "sha256": "4e66d1b182bb53117e2cd18f52ff1a3e96775f0126bf1057be1181917b286b84"
      },
      {
        "path": "/data2/k6tk/7c/7cc2ec123d73f9c6edd063ae22ed8af68962d0788dde0dc72134ecb075cbacc7.png",
        "sha256": "7cc2ec123d73f9c6edd063ae22ed8af68962d0788dde0dc72134ecb075cbacc7"
      },
      {
        "path": "/data2/k6tk/39/39acb8004ff59f03c21e3c41a8d14d86d862a864d81e3d52dbb8c09be102f3a4.png",
        "sha256": "39acb8004ff59f03c21e3c41a8d14d86d862a864d81e3d52dbb8c09be102f3a4"
      },
      {
        "path": "/data2/k6tk/4c/4c68e099b918a520b3b6b1a96bd51efc19bd6f6df25a06ca03c887b024ef1123.png",
        "sha256": "4c68e099b918a520b3b6b1a96bd51efc19bd6f6df25a06ca03c887b024ef1123"
      },
      {
        "path": "/data2/k6tk/d1/d184e8931911bd1b8fb8be70225d7a0117dcbf36fd333c3ce30730f2a293541b.png",
        "sha256": "d184e8931911bd1b8fb8be70225d7a0117dcbf36fd333c3ce30730f2a293541b"
      },
      {
        "path": "/data2/k6tk/49/499f2c47c2e218d221e9df0c7205a3456211040114c0a20a985198c4b8cf4c33.png",
        "sha256": "499f2c47c2e218d221e9df0c7205a3456211040114c0a20a985198c4b8cf4c33"
      },
      {
        "path": "/data2/k6tk/fb/fb3491554d184ba244e64d64f69af686a45e7eb681469b8953663f9117178b74.png",
        "sha256": "fb3491554d184ba244e64d64f69af686a45e7eb681469b8953663f9117178b74"
      },
      {
        "path": "/data2/k6tk/34/34a80df57d4407f49856fbb7c185eb43f37918be3442749a5de0de8e3498ecba.png",
        "sha256": "34a80df57d4407f49856fbb7c185eb43f37918be3442749a5de0de8e3498ecba"
      },
      {
        "path": "/data2/k6tk/f9/f9021a392e6e698c8dae0314c1c9dbdb43021de0a9e5fdf8e77ace1ac167f65b.png",
        "sha256": "f9021a392e6e698c8dae0314c1c9dbdb43021de0a9e5fdf8e77ace1ac167f65b"
      },
      {
        "path": "/data2/k6tk/7f/7fdd47c57a4dda7088999a2b986860f927876586b20c614e3d0e406ae1266a8b.png",
        "sha256": "7fdd47c57a4dda7088999a2b986860f927876586b20c614e3d0e406ae1266a8b"
      },
      {
        "path": "/data2/k6tk/9a/9ad68100eacc1f1fa18195c801a53146a9cf30fb2fb18e22a90145f87b820927.png",
        "sha256": "9ad68100eacc1f1fa18195c801a53146a9cf30fb2fb18e22a90145f87b820927"
      },
      {
        "path": "/data2/k6tk/4e/4eb0159b01b77a9c7ebded3ed03280d82780d7cbaf0b8f1c51c39c92a5288491.png",
        "sha256": "4eb0159b01b77a9c7ebded3ed03280d82780d7cbaf0b8f1c51c39c92a5288491"
      },
      {
        "path": "/data2/k6tk/62/627237026895a8ac88aa2456fed26ecd69f5a282e79af85bdb102553920194a7.png",
        "sha256": "627237026895a8ac88aa2456fed26ecd69f5a282e79af85bdb102553920194a7"
      },
      {
        "path": "/data2/k6tk/52/524eb0b6e6e5cf939289e61c7f5864e3446bd91ccec47298256caf53bc004dad.png",
        "sha256": "524eb0b6e6e5cf939289e61c7f5864e3446bd91ccec47298256caf53bc004dad"
      },
      {
        "path": "/data2/k6tk/92/92328a4da61133a3f6985ace8b817484495a6453cf0bf297aa4b5cc169510dca.png",
        "sha256": "92328a4da61133a3f6985ace8b817484495a6453cf0bf297aa4b5cc169510dca"
      },
      {
        "path": "/data2/k6tk/54/54d62d7435946a2750aa690a31b6a7cb56827b53f96a76a952da5c277b928f87.png",
        "sha256": "54d62d7435946a2750aa690a31b6a7cb56827b53f96a76a952da5c277b928f87"
      },
      {
        "path": "/data2/k6tk/f9/f91c7275bdb665f43d94765863f4d1a56a47531ae7250bb0003a91b884cce094.png",
        "sha256": "f91c7275bdb665f43d94765863f4d1a56a47531ae7250bb0003a91b884cce094"
      }
    ],
    "options": [
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the basket and facing in the opposite direction of the ceiling lamp, is the heater to my left or to my right?",
    "timestamps": [
      0.0,
      3.716666666666667,
      7.433333333333334,
      11.166666666666666,
      14.883333333333333,
      18.616666666666667,
      22.333333333333332,
      26.066666666666666,
      29.783333333333335,
      33.516666666666666,
      37.233333333333334,
      40.95,
      44.68333333333333,
      48.4,
      52.13333333333333,
      55.85,
      59.583333333333336,
      63.3,
      67.03333333333333,
      70.75,
      74.48333333333333,
      78.2,
      81.91666666666667,
      85.65,
      89.36666666666666,
      93.1,
      96.81666666666666,
      100.55,
      104.26666666666667,
      108.0,
      111.71666666666667,
      115.45
    ],
    "total_num_frames": 6928
  },
  "target": "<think>\nSeen: basket in frame 1; ceiling lamp in frame 29; heater in frame 25.\nIf I stood at the basket facing the ceiling lamp, the heater would be to my left.\nThe question has me facing in the opposite direction of the ceiling lamp. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the heater to my right.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 25: vsi590k_038297_away_opp

Store index: 198263. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the couch and facing in the opposite direction of the mirror, is the door to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: couch in frame 7; mirror in frame 30; door in frame 30.
If I stood at the couch facing the mirror, the door would be to my left.
The question has me facing in the opposite direction of the mirror. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the door to my right.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_038297",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 127149,
      "derived_from_v6_qid": "vsi590k_038297_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "797fd870e5908ffd184cdea70600679dbc86030440f3b147e076585f2dd2749b",
      "source_target_sha256": "5f1d5fa5a72b92deeb726d61fe925c938bd316a2a6d0952c4b05d53373a165a5",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_038297",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_038297_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "v3644016ad99a",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_038297",
  "source_set": "T0_gaps",
  "student_input": {
    "fps": 24.0,
    "frame_indices": [
      0,
      65,
      131,
      197,
      263,
      328,
      394,
      460,
      526,
      591,
      657,
      723,
      789,
      855,
      920,
      986,
      1052,
      1118,
      1183,
      1249,
      1315,
      1381,
      1447,
      1512,
      1578,
      1644,
      1710,
      1775,
      1841,
      1907,
      1973,
      2039
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f9/f9c601078cced16da6e448cb864d4aac0319acb5f51258a24ecb169b9f32ec80.png",
        "sha256": "f9c601078cced16da6e448cb864d4aac0319acb5f51258a24ecb169b9f32ec80"
      },
      {
        "path": "/data2/k6tk/89/890cf8f48eafbf4323f243dbb3441811a5e76839b18f3d36d26e98de7e4bd08b.png",
        "sha256": "890cf8f48eafbf4323f243dbb3441811a5e76839b18f3d36d26e98de7e4bd08b"
      },
      {
        "path": "/data2/k6tk/a1/a1924fe4db757bda1813c745e76625dade35c6d24932a7304c49013de90d878c.png",
        "sha256": "a1924fe4db757bda1813c745e76625dade35c6d24932a7304c49013de90d878c"
      },
      {
        "path": "/data2/k6tk/95/959b8450f8e66362c55fe410c4d981b947c0d8fb88c762c3ba66c0de1e117caa.png",
        "sha256": "959b8450f8e66362c55fe410c4d981b947c0d8fb88c762c3ba66c0de1e117caa"
      },
      {
        "path": "/data2/k6tk/46/46540b7fc9153086b1975802aa27554bf888f02b43d19abcb9aabaac5ecab650.png",
        "sha256": "46540b7fc9153086b1975802aa27554bf888f02b43d19abcb9aabaac5ecab650"
      },
      {
        "path": "/data2/k6tk/05/05ccabe62d7fadbe45e1c51b6ed7eeda90143b8b5924a84d2b04864fe0504611.png",
        "sha256": "05ccabe62d7fadbe45e1c51b6ed7eeda90143b8b5924a84d2b04864fe0504611"
      },
      {
        "path": "/data2/k6tk/66/66ca2eb4555307fe376be46f1d0f7f6991e9a36040df2f539162045c639eb7d9.png",
        "sha256": "66ca2eb4555307fe376be46f1d0f7f6991e9a36040df2f539162045c639eb7d9"
      },
      {
        "path": "/data2/k6tk/9b/9b27a7323f57bfa0ed2ad263ae00d4a206ec34160754634713b4c8979a51b54f.png",
        "sha256": "9b27a7323f57bfa0ed2ad263ae00d4a206ec34160754634713b4c8979a51b54f"
      },
      {
        "path": "/data2/k6tk/af/afa561402e9c2eb3feef518323969d2c6bd0ab9a1e5cd4ffd5eca80ddb15dea5.png",
        "sha256": "afa561402e9c2eb3feef518323969d2c6bd0ab9a1e5cd4ffd5eca80ddb15dea5"
      },
      {
        "path": "/data2/k6tk/aa/aad512a6faf88e4747e6624b8f2d505be9f00926ca4b12ab684a6a5f664ef7a2.png",
        "sha256": "aad512a6faf88e4747e6624b8f2d505be9f00926ca4b12ab684a6a5f664ef7a2"
      },
      {
        "path": "/data2/k6tk/82/828b17b40887ea7c942de2963e866c8bc205389a3f6e01abfa35f3c3714ebae5.png",
        "sha256": "828b17b40887ea7c942de2963e866c8bc205389a3f6e01abfa35f3c3714ebae5"
      },
      {
        "path": "/data2/k6tk/9c/9c28b84d77e158e58bb666bebae86f287cdd664ff208f0167680f2dbba3b80d7.png",
        "sha256": "9c28b84d77e158e58bb666bebae86f287cdd664ff208f0167680f2dbba3b80d7"
      },
      {
        "path": "/data2/k6tk/7e/7e8201dbb792e80c77ed720cb41c310a3f0487922a20d70ab4de8c8614662d71.png",
        "sha256": "7e8201dbb792e80c77ed720cb41c310a3f0487922a20d70ab4de8c8614662d71"
      },
      {
        "path": "/data2/k6tk/f5/f53ce6d7d61364286fae0bce0f168163c6a2144606543ff4340929aad259e8ba.png",
        "sha256": "f53ce6d7d61364286fae0bce0f168163c6a2144606543ff4340929aad259e8ba"
      },
      {
        "path": "/data2/k6tk/8e/8e6588c1306f5f90bae8708bc63a353200ebf2ef423e98f2fcf043a184133605.png",
        "sha256": "8e6588c1306f5f90bae8708bc63a353200ebf2ef423e98f2fcf043a184133605"
      },
      {
        "path": "/data2/k6tk/f9/f99f207d339e89bff3ea4286355ec252083336655febbe9a628928e72ed641cd.png",
        "sha256": "f99f207d339e89bff3ea4286355ec252083336655febbe9a628928e72ed641cd"
      },
      {
        "path": "/data2/k6tk/5c/5cc1af6579bc269b2fa22629fccec921039ef6d24fa6e9333550e0af4447db65.png",
        "sha256": "5cc1af6579bc269b2fa22629fccec921039ef6d24fa6e9333550e0af4447db65"
      },
      {
        "path": "/data2/k6tk/4d/4d6355d043118919fc00d59facd9a80d14e2cb772291621dd7106566f7db6f3f.png",
        "sha256": "4d6355d043118919fc00d59facd9a80d14e2cb772291621dd7106566f7db6f3f"
      },
      {
        "path": "/data2/k6tk/75/75c3426bfd898d0ff31f1bb7be60ea5c79fab52de9531b6710371e19fcfc58b3.png",
        "sha256": "75c3426bfd898d0ff31f1bb7be60ea5c79fab52de9531b6710371e19fcfc58b3"
      },
      {
        "path": "/data2/k6tk/0e/0e044e66e16e59ececd97ef6d9133f04e83a74f2ce6334991c3db5b4d62f5d42.png",
        "sha256": "0e044e66e16e59ececd97ef6d9133f04e83a74f2ce6334991c3db5b4d62f5d42"
      },
      {
        "path": "/data2/k6tk/8c/8c814be741814207806d768cc9f8053529947f3006f07513091a59b81aab5bd5.png",
        "sha256": "8c814be741814207806d768cc9f8053529947f3006f07513091a59b81aab5bd5"
      },
      {
        "path": "/data2/k6tk/bc/bc38ac6a829aba862dce2826211b02eca8b654e8a7b887936abde9131cb1007a.png",
        "sha256": "bc38ac6a829aba862dce2826211b02eca8b654e8a7b887936abde9131cb1007a"
      },
      {
        "path": "/data2/k6tk/c4/c49c0326362e96b3762162a18a687971f304aaf45460efe0fb712060e6641422.png",
        "sha256": "c49c0326362e96b3762162a18a687971f304aaf45460efe0fb712060e6641422"
      },
      {
        "path": "/data2/k6tk/26/26550214038f9985c5ab13c00519cdd4c3defab27674d173edb672db48674145.png",
        "sha256": "26550214038f9985c5ab13c00519cdd4c3defab27674d173edb672db48674145"
      },
      {
        "path": "/data2/k6tk/33/33832201ce799ef178e8e0ea180b743900e38a4e2965c0261345d46a1e45e6f1.png",
        "sha256": "33832201ce799ef178e8e0ea180b743900e38a4e2965c0261345d46a1e45e6f1"
      },
      {
        "path": "/data2/k6tk/20/205cd5b279b49f1ae6dc57d6437eb59c514796c50fd3c3b3ee39552e4c2fe373.png",
        "sha256": "205cd5b279b49f1ae6dc57d6437eb59c514796c50fd3c3b3ee39552e4c2fe373"
      },
      {
        "path": "/data2/k6tk/7e/7e07dbd149a62ed8ae98a66fb0ca8c526df68144f4258d071173fca3a5798fee.png",
        "sha256": "7e07dbd149a62ed8ae98a66fb0ca8c526df68144f4258d071173fca3a5798fee"
      },
      {
        "path": "/data2/k6tk/73/73ca7d051e35fd98a75b0b68747a1e6125353a94df40754c6ab8137d535dd678.png",
        "sha256": "73ca7d051e35fd98a75b0b68747a1e6125353a94df40754c6ab8137d535dd678"
      },
      {
        "path": "/data2/k6tk/ff/ff002a78e64831cc0b23a7ac80e7b5a3aac3840fc88380af6576d2f40b2b0389.png",
        "sha256": "ff002a78e64831cc0b23a7ac80e7b5a3aac3840fc88380af6576d2f40b2b0389"
      },
      {
        "path": "/data2/k6tk/cb/cb6446ef1a7f54707bfde101e23a32cf586c85347ffda057af3f0761e7df2ccb.png",
        "sha256": "cb6446ef1a7f54707bfde101e23a32cf586c85347ffda057af3f0761e7df2ccb"
      },
      {
        "path": "/data2/k6tk/28/28b384b0b0224a9d17be2ea2329fc3cfb938bb271a06b0221fb5b96b34b20a94.png",
        "sha256": "28b384b0b0224a9d17be2ea2329fc3cfb938bb271a06b0221fb5b96b34b20a94"
      },
      {
        "path": "/data2/k6tk/6c/6c9e9f171b041098c7a2ecde50bc84cb3fefe0c7791ead2a85f40c706ffc717d.png",
        "sha256": "6c9e9f171b041098c7a2ecde50bc84cb3fefe0c7791ead2a85f40c706ffc717d"
      }
    ],
    "options": [
      "A. left",
      "B. right"
    ],
    "question": "If I am standing by the couch and facing in the opposite direction of the mirror, is the door to my left or to my right?",
    "timestamps": [
      0.0,
      2.7083333333333335,
      5.458333333333333,
      8.208333333333334,
      10.958333333333334,
      13.666666666666666,
      16.416666666666668,
      19.166666666666668,
      21.916666666666668,
      24.625,
      27.375,
      30.125,
      32.875,
      35.625,
      38.333333333333336,
      41.083333333333336,
      43.833333333333336,
      46.583333333333336,
      49.291666666666664,
      52.041666666666664,
      54.791666666666664,
      57.541666666666664,
      60.291666666666664,
      63.0,
      65.75,
      68.5,
      71.25,
      73.95833333333333,
      76.70833333333333,
      79.45833333333333,
      82.20833333333333,
      84.95833333333333
    ],
    "total_num_frames": 2040
  },
  "target": "<think>\nSeen: couch in frame 7; mirror in frame 30; door in frame 30.\nIf I stood at the couch facing the mirror, the door would be to my left.\nThe question has me facing in the opposite direction of the mirror. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the door to my right.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 26: vsi590k_242463_away_opp

Store index: 199416. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the bathtub and facing in the opposite direction of the stool, is the bed to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: A

```text
<think>
Seen: bathtub in frame 20; stool in frame 28; bed in frame 23.
If I stood at the bathtub facing the stool, the bed would be out to my left.
The question has me facing in the opposite direction of the stool. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bed to my right.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d3",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_242463",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 132735,
      "derived_from_v6_qid": "vsi590k_242463_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "eeafe4178c2ee603539dc92b2c6c990fdd8517a910c6eeb782c1fc0229faf5d3",
      "source_target_sha256": "97ac8f3e600165f569ad7630db6788cc754399c3574eb8eedfdc97cc28af4fbf",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/9eecedf23da3bd91.jsonl.gz",
    "source_qid": "vsi590k_242463",
    "source_set": "ARKIT_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_242463_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v31455c538a29",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_242463",
  "source_set": "ARKIT_gen_r2",
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      15,
      30,
      45,
      59,
      74,
      89,
      104,
      119,
      134,
      148,
      163,
      178,
      193,
      208,
      223,
      237,
      252,
      267,
      282,
      297,
      312,
      326,
      341,
      356,
      371,
      386,
      401,
      415,
      430,
      445,
      460
    ],
    "frames": [
      {
        "path": "/data2/k6tk/87/87f21a78d2296c3e176b1ba1998987811e8cc66624c03ac7d4540db681a0b889.png",
        "sha256": "87f21a78d2296c3e176b1ba1998987811e8cc66624c03ac7d4540db681a0b889"
      },
      {
        "path": "/data2/k6tk/9f/9fe1d5f0fb8b09e9eb98e6a77d8e2630abe086c55d86456b9530fac840009a41.png",
        "sha256": "9fe1d5f0fb8b09e9eb98e6a77d8e2630abe086c55d86456b9530fac840009a41"
      },
      {
        "path": "/data2/k6tk/ab/ab0cdd5832ef8758026ce7a108f57721909b88ceca24642459d1cac2745a0e9a.png",
        "sha256": "ab0cdd5832ef8758026ce7a108f57721909b88ceca24642459d1cac2745a0e9a"
      },
      {
        "path": "/data2/k6tk/1d/1d74e33f9c350fa400829535bbf1f2dfb4d0c853e860865e16dd0e09fa82eacc.png",
        "sha256": "1d74e33f9c350fa400829535bbf1f2dfb4d0c853e860865e16dd0e09fa82eacc"
      },
      {
        "path": "/data2/k6tk/ac/acb3071735a91479eb69f18f72063a0cc3bd407fcfa0b34b51ec1e6b380efb7a.png",
        "sha256": "acb3071735a91479eb69f18f72063a0cc3bd407fcfa0b34b51ec1e6b380efb7a"
      },
      {
        "path": "/data2/k6tk/44/441edc3e622912986829bb57e004533cdeb81b64590ecffbd793518b7ad7df14.png",
        "sha256": "441edc3e622912986829bb57e004533cdeb81b64590ecffbd793518b7ad7df14"
      },
      {
        "path": "/data2/k6tk/26/2630be9e4d4828545063f1bdeca3a1813ca1604b8b07448dca50c27e19d3c202.png",
        "sha256": "2630be9e4d4828545063f1bdeca3a1813ca1604b8b07448dca50c27e19d3c202"
      },
      {
        "path": "/data2/k6tk/b2/b222f59c0b98fef60c7deb4ee3963ff6796d39b917bb6e43c317ee641a2ad01a.png",
        "sha256": "b222f59c0b98fef60c7deb4ee3963ff6796d39b917bb6e43c317ee641a2ad01a"
      },
      {
        "path": "/data2/k6tk/0c/0cf26a04097420df052da5e02f27bffab6be1e0233e663852f851f4c72b9c9a1.png",
        "sha256": "0cf26a04097420df052da5e02f27bffab6be1e0233e663852f851f4c72b9c9a1"
      },
      {
        "path": "/data2/k6tk/3c/3ce46305fb02916f500e68ae69d60d28304ace69b6b12228367fa199fb679455.png",
        "sha256": "3ce46305fb02916f500e68ae69d60d28304ace69b6b12228367fa199fb679455"
      },
      {
        "path": "/data2/k6tk/87/8778ea3f7a9711b02353924fae2c0dfe00efe926681bd69a1b2b739d8e6c091f.png",
        "sha256": "8778ea3f7a9711b02353924fae2c0dfe00efe926681bd69a1b2b739d8e6c091f"
      },
      {
        "path": "/data2/k6tk/71/7149b99451dbc4db79593d796f8d72ca48ae687d2d6eaf667d938e587fcf3514.png",
        "sha256": "7149b99451dbc4db79593d796f8d72ca48ae687d2d6eaf667d938e587fcf3514"
      },
      {
        "path": "/data2/k6tk/80/80186fb76c8bfcbe43d82d5d329e8693f11b0807ecb5815d1a9805416413c269.png",
        "sha256": "80186fb76c8bfcbe43d82d5d329e8693f11b0807ecb5815d1a9805416413c269"
      },
      {
        "path": "/data2/k6tk/6f/6ffdd0db209afd5bd2fc86e702bd504db134960beed6c274007560bf23642b02.png",
        "sha256": "6ffdd0db209afd5bd2fc86e702bd504db134960beed6c274007560bf23642b02"
      },
      {
        "path": "/data2/k6tk/dc/dc55f2ff2ac5002f38be466aed844f453ae7dbbeb052d1c6c7d6ffc2bb15bd9e.png",
        "sha256": "dc55f2ff2ac5002f38be466aed844f453ae7dbbeb052d1c6c7d6ffc2bb15bd9e"
      },
      {
        "path": "/data2/k6tk/7b/7bcb5358f09e4aeee7fb7c92da9520360d3fd883c98befa6c42d0e5739493d2f.png",
        "sha256": "7bcb5358f09e4aeee7fb7c92da9520360d3fd883c98befa6c42d0e5739493d2f"
      },
      {
        "path": "/data2/k6tk/9a/9a33eced85921c91c5ab1c5a41017fba7f103d827955a2a0e97a99e5506c9005.png",
        "sha256": "9a33eced85921c91c5ab1c5a41017fba7f103d827955a2a0e97a99e5506c9005"
      },
      {
        "path": "/data2/k6tk/84/84ccd7557feda11d75b9988c2672dfb80f42d7818c391f3f16e8a15cf2dde5fd.png",
        "sha256": "84ccd7557feda11d75b9988c2672dfb80f42d7818c391f3f16e8a15cf2dde5fd"
      },
      {
        "path": "/data2/k6tk/73/73c01d9f99528927d86434b925880fdb777b81e50c3f5e76bf14ca6feb44321a.png",
        "sha256": "73c01d9f99528927d86434b925880fdb777b81e50c3f5e76bf14ca6feb44321a"
      },
      {
        "path": "/data2/k6tk/af/af2f437bc7ac3b60711e72ae6774a251aeefba6de27526eed2f19cdacac690c4.png",
        "sha256": "af2f437bc7ac3b60711e72ae6774a251aeefba6de27526eed2f19cdacac690c4"
      },
      {
        "path": "/data2/k6tk/1e/1ebec9c57add64ef2300104a01f225daa042b14c2e5d97f5469f543bef4984ff.png",
        "sha256": "1ebec9c57add64ef2300104a01f225daa042b14c2e5d97f5469f543bef4984ff"
      },
      {
        "path": "/data2/k6tk/22/22384752877373d6969b13fea9c96efe84b8c477bb18a53b7f73a3e8876cafc2.png",
        "sha256": "22384752877373d6969b13fea9c96efe84b8c477bb18a53b7f73a3e8876cafc2"
      },
      {
        "path": "/data2/k6tk/64/643d19f7d00a44ed7873ac54c9c8d71b33b6100ba3452b2b7be99b6ffc3c649b.png",
        "sha256": "643d19f7d00a44ed7873ac54c9c8d71b33b6100ba3452b2b7be99b6ffc3c649b"
      },
      {
        "path": "/data2/k6tk/7f/7f1e6db4727812e8879eb802f27a50ea2c930333f1a735ac4842be2769428414.png",
        "sha256": "7f1e6db4727812e8879eb802f27a50ea2c930333f1a735ac4842be2769428414"
      },
      {
        "path": "/data2/k6tk/6b/6b5ec78090eceb078c6e2d7ee3a3a76a8e8ac7e66bbe15d0379047e7945582ac.png",
        "sha256": "6b5ec78090eceb078c6e2d7ee3a3a76a8e8ac7e66bbe15d0379047e7945582ac"
      },
      {
        "path": "/data2/k6tk/82/82a67033efa75b62f74b2d88b1a2cc42f12ad681f4eae41d7d9cc8c98d98fae5.png",
        "sha256": "82a67033efa75b62f74b2d88b1a2cc42f12ad681f4eae41d7d9cc8c98d98fae5"
      },
      {
        "path": "/data2/k6tk/38/384fe0b05e7316ac1ea4263af59f995c7b2b5d36b3b9df1a3b3461f1380ebf92.png",
        "sha256": "384fe0b05e7316ac1ea4263af59f995c7b2b5d36b3b9df1a3b3461f1380ebf92"
      },
      {
        "path": "/data2/k6tk/dd/dd371f7140b42bdbb56d68ad4a45295947240e36e16e945d93687feeb2e13552.png",
        "sha256": "dd371f7140b42bdbb56d68ad4a45295947240e36e16e945d93687feeb2e13552"
      },
      {
        "path": "/data2/k6tk/c5/c5d529c75d4247f15c72399d66725d6e35e263e325452b47cfd921f38c547cce.png",
        "sha256": "c5d529c75d4247f15c72399d66725d6e35e263e325452b47cfd921f38c547cce"
      },
      {
        "path": "/data2/k6tk/f1/f16d3f83075be4fa1989a3036a3d2b4293a89f250bad9ae938e5c54394c5e6ad.png",
        "sha256": "f16d3f83075be4fa1989a3036a3d2b4293a89f250bad9ae938e5c54394c5e6ad"
      },
      {
        "path": "/data2/k6tk/0f/0fa8e51b528cad4dfc49989396477a78dad48714ad4ad4be5ff5f2f430361b18.png",
        "sha256": "0fa8e51b528cad4dfc49989396477a78dad48714ad4ad4be5ff5f2f430361b18"
      },
      {
        "path": "/data2/k6tk/50/506e50be9db8f11481437a33971c573ced0ae4ce7080a19f0b224c2085a2e670.png",
        "sha256": "506e50be9db8f11481437a33971c573ced0ae4ce7080a19f0b224c2085a2e670"
      }
    ],
    "options": [
      "A. right",
      "B. back",
      "C. left"
    ],
    "question": "If I am standing by the bathtub and facing in the opposite direction of the stool, is the bed to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      1.5,
      3.0,
      4.5,
      5.9,
      7.4,
      8.9,
      10.4,
      11.9,
      13.4,
      14.8,
      16.3,
      17.8,
      19.3,
      20.8,
      22.3,
      23.7,
      25.2,
      26.7,
      28.2,
      29.7,
      31.2,
      32.6,
      34.1,
      35.6,
      37.1,
      38.6,
      40.1,
      41.5,
      43.0,
      44.5,
      46.0
    ],
    "total_num_frames": 461
  },
  "target": "<think>\nSeen: bathtub in frame 20; stool in frame 28; bed in frame 23.\nIf I stood at the bathtub facing the stool, the bed would be out to my left.\nThe question has me facing in the opposite direction of the stool. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the bed to my right.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 27: vsi590k_128129_away_opp

Store index: 199700. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the shoes and facing in the opposite direction of the laptop, is the trash can to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: A

```text
<think>
Seen: shoes in frame 4; laptop in frame 14; trash can in frame 13.
If I stood at the shoes facing the laptop, the trash can would be ahead of me, slightly to my right.
The question has me facing in the opposite direction of the laptop. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the trash can at my back.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_128129",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 132529,
      "derived_from_v6_qid": "vsi590k_128129_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "0a8e6a8d5b42b63305ec93f7ca20ab167a975ab3234b4d6c0846546b458c4da5",
      "source_target_sha256": "16299f6e04c3022ffaa225d770891131560d60de1f89215b6e0e7624d7c6cc09",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/c16c5db36e04c1ef.jsonl.gz",
    "source_qid": "vsi590k_128129",
    "source_set": "T1H2_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_128129_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v437d5b50c2bc",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_128129",
  "source_set": "T1H2_gen_r2",
  "student_input": {
    "fps": 60.0,
    "frame_indices": [
      0,
      480,
      960,
      1440,
      1920,
      2400,
      2880,
      3360,
      3840,
      4320,
      4800,
      5280,
      5760,
      6240,
      6720,
      7200,
      7681,
      8161,
      8641,
      9121,
      9601,
      10081,
      10561,
      11041,
      11521,
      12001,
      12481,
      12961,
      13441,
      13921,
      14401,
      14882
    ],
    "frames": [
      {
        "path": "/data2/k6tk/bd/bde5b9157dddd130c921b72925528f5d21df1c91d0eca0b81d8ff5321b7f5376.png",
        "sha256": "bde5b9157dddd130c921b72925528f5d21df1c91d0eca0b81d8ff5321b7f5376"
      },
      {
        "path": "/data2/k6tk/9c/9c387ee8bf2791d1caf1ad694ec188b372668098b716a747beaa2929c72cd29f.png",
        "sha256": "9c387ee8bf2791d1caf1ad694ec188b372668098b716a747beaa2929c72cd29f"
      },
      {
        "path": "/data2/k6tk/d8/d81bc7a54822ec7e2bf8538c5a35707ba3bdbccf38385c733cd0897808bd9789.png",
        "sha256": "d81bc7a54822ec7e2bf8538c5a35707ba3bdbccf38385c733cd0897808bd9789"
      },
      {
        "path": "/data2/k6tk/c6/c675b18565f68334c4bcae0d1d2516cbe33eecbae5b768f30c6d79839b7ae878.png",
        "sha256": "c675b18565f68334c4bcae0d1d2516cbe33eecbae5b768f30c6d79839b7ae878"
      },
      {
        "path": "/data2/k6tk/0d/0dcfb0ee6bed9b64639903a07de4d5f846c701dcfb6ac8070865b2cba12f11e5.png",
        "sha256": "0dcfb0ee6bed9b64639903a07de4d5f846c701dcfb6ac8070865b2cba12f11e5"
      },
      {
        "path": "/data2/k6tk/f5/f50223bb0e950170c7b7671e7916fa96fe8cee2c6278581f9b46c13a83b6325c.png",
        "sha256": "f50223bb0e950170c7b7671e7916fa96fe8cee2c6278581f9b46c13a83b6325c"
      },
      {
        "path": "/data2/k6tk/f4/f40990b1f6a4ee671aad7da120b02ca490c70580c5a153b6e3cbc82b494f70df.png",
        "sha256": "f40990b1f6a4ee671aad7da120b02ca490c70580c5a153b6e3cbc82b494f70df"
      },
      {
        "path": "/data2/k6tk/f1/f1ec57444b09e883808ecdb69a40384e4028f8147a2b96e7c8141b85ed7bc0f8.png",
        "sha256": "f1ec57444b09e883808ecdb69a40384e4028f8147a2b96e7c8141b85ed7bc0f8"
      },
      {
        "path": "/data2/k6tk/5b/5bca7fa9db5211516f7d423a11da022a71545ff0797ea5d79582d4fd71110f5b.png",
        "sha256": "5bca7fa9db5211516f7d423a11da022a71545ff0797ea5d79582d4fd71110f5b"
      },
      {
        "path": "/data2/k6tk/78/782ffa241528f26b8a04c1d2e2ee6b7f2409d08837df4d48c83005487c859197.png",
        "sha256": "782ffa241528f26b8a04c1d2e2ee6b7f2409d08837df4d48c83005487c859197"
      },
      {
        "path": "/data2/k6tk/02/02170f876e730eef2b5a833d4c06afb6052a40dd1b1a1561c54b96b995c61c44.png",
        "sha256": "02170f876e730eef2b5a833d4c06afb6052a40dd1b1a1561c54b96b995c61c44"
      },
      {
        "path": "/data2/k6tk/38/38287925df04b654f7692b3c8b81e833c57087e341b231783f8d5f5d5e2b6beb.png",
        "sha256": "38287925df04b654f7692b3c8b81e833c57087e341b231783f8d5f5d5e2b6beb"
      },
      {
        "path": "/data2/k6tk/14/1426e671ef1d63db3b2cf501866ba3b9520f85c3d56200bc69dfec8244e7c57e.png",
        "sha256": "1426e671ef1d63db3b2cf501866ba3b9520f85c3d56200bc69dfec8244e7c57e"
      },
      {
        "path": "/data2/k6tk/e7/e7522034f9b1d2e9543ee00e91bbcb5ba53e8526d5cc6b75014be054fac6ddb2.png",
        "sha256": "e7522034f9b1d2e9543ee00e91bbcb5ba53e8526d5cc6b75014be054fac6ddb2"
      },
      {
        "path": "/data2/k6tk/13/13203f57a578ef75eb1083491993981490e94166906a0e24f3087ce26f6133be.png",
        "sha256": "13203f57a578ef75eb1083491993981490e94166906a0e24f3087ce26f6133be"
      },
      {
        "path": "/data2/k6tk/db/db0451de8c451f161e806f944f2d0c44f4555973c35ad6552e6b04c054d5dfce.png",
        "sha256": "db0451de8c451f161e806f944f2d0c44f4555973c35ad6552e6b04c054d5dfce"
      },
      {
        "path": "/data2/k6tk/2e/2e1ba61a204e816458a314d79a11809122a774732e43ba71c91dd2ffc8440c62.png",
        "sha256": "2e1ba61a204e816458a314d79a11809122a774732e43ba71c91dd2ffc8440c62"
      },
      {
        "path": "/data2/k6tk/79/7954580b8a281adfb2e38b94214bb5099313bc6b536137ad30f4814b443f09db.png",
        "sha256": "7954580b8a281adfb2e38b94214bb5099313bc6b536137ad30f4814b443f09db"
      },
      {
        "path": "/data2/k6tk/2c/2c4e0f450bba9c55b4d8292a4f4efa367ac9629a7ee51f76ae9624d9e9e72022.png",
        "sha256": "2c4e0f450bba9c55b4d8292a4f4efa367ac9629a7ee51f76ae9624d9e9e72022"
      },
      {
        "path": "/data2/k6tk/ee/ee0a1031c128298f57a3cd0ff466bec4933b9dc3246055f8312497b2871d44e7.png",
        "sha256": "ee0a1031c128298f57a3cd0ff466bec4933b9dc3246055f8312497b2871d44e7"
      },
      {
        "path": "/data2/k6tk/83/8375e4faf7c59372c332fdeb9bd5640207baec260c63ec326a780f821c4fe726.png",
        "sha256": "8375e4faf7c59372c332fdeb9bd5640207baec260c63ec326a780f821c4fe726"
      },
      {
        "path": "/data2/k6tk/31/31456dd43920628b3be8ff0f6c6a1997072cb816bac6f2fc5b56c12b33a5d116.png",
        "sha256": "31456dd43920628b3be8ff0f6c6a1997072cb816bac6f2fc5b56c12b33a5d116"
      },
      {
        "path": "/data2/k6tk/08/0804a136f06ae9c84c98081305caf66e567adb710b3d33b604401aee3e598e77.png",
        "sha256": "0804a136f06ae9c84c98081305caf66e567adb710b3d33b604401aee3e598e77"
      },
      {
        "path": "/data2/k6tk/98/98bc2f85546c014bd09a941e406990d30b84f368904186652f22b97331e41ca4.png",
        "sha256": "98bc2f85546c014bd09a941e406990d30b84f368904186652f22b97331e41ca4"
      },
      {
        "path": "/data2/k6tk/97/97c8f013a25ada07a7d8179f4658920f46d348ce27739f7d0bed374b2517b6cc.png",
        "sha256": "97c8f013a25ada07a7d8179f4658920f46d348ce27739f7d0bed374b2517b6cc"
      },
      {
        "path": "/data2/k6tk/56/56d5f7b016fc7f984200454a770c7be61d92830335563c5bbc289f3d9d045a4c.png",
        "sha256": "56d5f7b016fc7f984200454a770c7be61d92830335563c5bbc289f3d9d045a4c"
      },
      {
        "path": "/data2/k6tk/e1/e1312b6ff35bb8a22b1c88b0c046229ffaa081c6a8a883621df47eda001dc651.png",
        "sha256": "e1312b6ff35bb8a22b1c88b0c046229ffaa081c6a8a883621df47eda001dc651"
      },
      {
        "path": "/data2/k6tk/4d/4dfbd0ac5cfbf0ed470a7271f75f4d04cccbb380ab87bb5f28360c904fc5d320.png",
        "sha256": "4dfbd0ac5cfbf0ed470a7271f75f4d04cccbb380ab87bb5f28360c904fc5d320"
      },
      {
        "path": "/data2/k6tk/3e/3e9d9b9bd07dff6c15484a6f8bad252e134fd39a96dac77398294467e3352a45.png",
        "sha256": "3e9d9b9bd07dff6c15484a6f8bad252e134fd39a96dac77398294467e3352a45"
      },
      {
        "path": "/data2/k6tk/2a/2a22fd59f5842550148e44d57b51ccb7497b89b0444109b7fddcc2c2a4b8769d.png",
        "sha256": "2a22fd59f5842550148e44d57b51ccb7497b89b0444109b7fddcc2c2a4b8769d"
      },
      {
        "path": "/data2/k6tk/1f/1f3a6c5ffbe143e42480569b62552eae624663ddc88e34c74bd0a5a9ff9f7c0c.png",
        "sha256": "1f3a6c5ffbe143e42480569b62552eae624663ddc88e34c74bd0a5a9ff9f7c0c"
      },
      {
        "path": "/data2/k6tk/be/be86dfec6cb9c6360b650ad0b1aed8a87774900c9ae8492eb87b8778331dbd20.png",
        "sha256": "be86dfec6cb9c6360b650ad0b1aed8a87774900c9ae8492eb87b8778331dbd20"
      }
    ],
    "options": [
      "A. back",
      "B. right",
      "C. left"
    ],
    "question": "If I am standing by the shoes and facing in the opposite direction of the laptop, is the trash can to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
    "timestamps": [
      0.0,
      8.0,
      16.0,
      24.0,
      32.0,
      40.0,
      48.0,
      56.0,
      64.0,
      72.0,
      80.0,
      88.0,
      96.0,
      104.0,
      112.0,
      120.0,
      128.01666666666668,
      136.01666666666668,
      144.01666666666668,
      152.01666666666668,
      160.01666666666668,
      168.01666666666668,
      176.01666666666668,
      184.01666666666668,
      192.01666666666668,
      200.01666666666668,
      208.01666666666668,
      216.01666666666668,
      224.01666666666668,
      232.01666666666668,
      240.01666666666668,
      248.03333333333333
    ],
    "total_num_frames": 14883
  },
  "target": "<think>\nSeen: shoes in frame 4; laptop in frame 14; trash can in frame 13.\nIf I stood at the shoes facing the laptop, the trash can would be ahead of me, slightly to my right.\nThe question has me facing in the opposite direction of the laptop. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the trash can at my back.\n</think>\n\nA",
  "validation_commit": ""
}
```

### Sample 28: vsi590k_124317_away_opp

Store index: 197656. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the cutting board and facing in the opposite direction of the refrigerator, is the power strip to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: C

```text
<think>
Seen: cutting board in frame 22; refrigerator in frame 20; power strip in frame 19.
If I stood at the cutting board facing the refrigerator, the power strip would be out to my right.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the power strip to my left.
</think>

C
```

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_medium",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_124317",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 140477,
      "derived_from_v6_qid": "vsi590k_124317_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "ed6aad6160fd0c998fb51e12bca328a7c35482d9621be31835b7155c356c5dbd",
      "source_target_sha256": "23d197f0ab1c827507f11e7c22e1d9c70b194b5b0588b7521fd739af4ec35a4f",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7e4e92918e312afd.jsonl.gz",
    "source_qid": "vsi590k_124317",
    "source_set": "T0_gen_r2",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_124317_away_opp",
  "question_type": "object_rel_direction_medium",
  "result_status": "diagnostic, provisional",
  "scene": "v9e32221af081",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_124317",
  "source_set": "T0_gen_r2",
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
      "A. back",
      "B. right",
      "C. left"
    ],
    "question": "If I am standing by the cutting board and facing in the opposite direction of the refrigerator, is the power strip to my left, right, or back?\nAn object is to my back if I would have to turn at least 135 degrees in order to face it.",
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
  "target": "<think>\nSeen: cutting board in frame 22; refrigerator in frame 20; power strip in frame 19.\nIf I stood at the cutting board facing the refrigerator, the power strip would be out to my right.\nThe question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the power strip to my left.\n</think>\n\nC",
  "validation_commit": ""
}
```

### Sample 29: vsi590k_030986_away_opp

Store index: 203997. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the radiator and facing in the opposite direction of the couch, is the trash can to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: radiator in frame 14; couch in frame 7; trash can in frame 23.
If I stood at the radiator facing the couch, the trash can would be to my right.
The question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the trash can to my left.
</think>

B
```

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d1",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_030986",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 113813,
      "derived_from_v6_qid": "vsi590k_030986_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "2ba83b3ca501990cb1394310ea893cd823b9434dcd88c05c1207fd1e786785ea",
      "source_target_sha256": "3852bf9119fd280140581b841a5b0eda1bfd68e47694bf423505dffa3e390c17",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/7a1c59097139f59d.jsonl.gz",
    "source_qid": "vsi590k_030986",
    "source_set": "T0_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_030986_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "vea85b4637bdd",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_030986",
  "source_set": "T0_gaps",
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
      "A. right",
      "B. left"
    ],
    "question": "If I am standing by the radiator and facing in the opposite direction of the couch, is the trash can to my left or to my right?",
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
  "target": "<think>\nSeen: radiator in frame 14; couch in frame 7; trash can in frame 23.\nIf I stood at the radiator facing the couch, the trash can would be to my right.\nThe question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the trash can to my left.\n</think>\n\nB",
  "validation_commit": ""
}
```

### Sample 30: vsi590k_138039_away_opp

Store index: 202900. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the whiteboard and facing in the opposite direction of the printer, is the heater to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: whiteboard in frame 24; printer in frame 21; heater in frame 11.
If I stood at the whiteboard facing the printer, the heater would be to my right.
The question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my left.
</think>

A
```

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "category": "object_rel_direction_easy",
  "dataset": "d2",
  "facing": "away",
  "generation_commit": "",
  "head_program": null,
  "infrastructure_only": false,
  "license": [],
  "pair_id": "vsi590k_138039",
  "pool": "r1_away_opp",
  "provenance": {
    "rendering": {
      "derived_from_v6_i": 132333,
      "derived_from_v6_qid": "vsi590k_138039_away",
      "kind": "ra",
      "phrase": "facing in the opposite direction of",
      "selection_seed": "rows_r1_opp_v1",
      "source_question_sha256": "6480fadfae4dbb61062205709070235157de9aa52c054fc47ebe8b6b0800dbeb",
      "source_target_sha256": "0589e2ace3bf950662c6432718a81c07c8231d64b35fb68fceb419363faab3a4",
      "version": "b13_v1"
    },
    "source": "/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool/b6ac18d55d697a23.jsonl.gz",
    "source_qid": "vsi590k_138039",
    "source_set": "T1H1_gaps",
    "view_labels": "frame_numbers"
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "vsi590k_138039_away_opp",
  "question_type": "object_rel_direction_easy",
  "result_status": "diagnostic, provisional",
  "scene": "ve629201a8ae1",
  "score_nomination_allowed": false,
  "source_qid": "vsi590k_138039",
  "source_set": "T1H1_gaps",
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
    "question": "If I am standing by the whiteboard and facing in the opposite direction of the printer, is the heater to my left or to my right?",
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
  "target": "<think>\nSeen: whiteboard in frame 24; printer in frame 21; heater in frame 11.\nIf I stood at the whiteboard facing the printer, the heater would be to my right.\nThe question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the heater to my left.\n</think>\n\nA",
  "validation_commit": ""
}
```

