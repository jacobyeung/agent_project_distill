Forty complete rows follow: one unequal case and one tie for each template. Counts are audit metadata only.

### 1. fbp_relcnt2_398067368e9e448eab79c881

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-12e89756158fd356953546edba5ab09bbb215c833fef288e232c5fa632b1f456",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42899632",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42899632.npz": "96b034989b909ced0a45d9b67c4c62103999efc15b68bfd78ee223ec35068c28",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42899632.npz",
    "raster_sha256": "96b034989b909ced0a45d9b67c4c62103999efc15b68bfd78ee223ec35068c28",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "3",
      "count_a": 1,
      "count_b": 3,
      "ids_a": [
        4
      ],
      "ids_b": [
        0,
        5,
        6
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue435357",
      "scene_use_cap": 24,
      "source_qid": "b12ct_f95899ab9eb6c28d88cf5e43",
      "source_row_sha256": "621e6795bb42b2f461e21dccc36a442dfda6280762453271bc14a8170544fa01",
      "source_use_cap": 8,
      "template_id": 0,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_398067368e9e448eab79c881",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v1f8578c3d354",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      14,
      29,
      43,
      58,
      72,
      87,
      101,
      116,
      130,
      145,
      159,
      173,
      188,
      202,
      217,
      231,
      246,
      260,
      275,
      289,
      303,
      318,
      332,
      347,
      361,
      376,
      390,
      405,
      419,
      434,
      448
    ],
    "frames": [
      {
        "path": "/data2/k6tk/0f/0faf0ab3e864472a4c8f571ab2dbd6eefb3e109fd2ddb6ff1097ecd32d2cda52.png",
        "sha256": "0faf0ab3e864472a4c8f571ab2dbd6eefb3e109fd2ddb6ff1097ecd32d2cda52"
      },
      {
        "path": "/data2/k6tk/cc/cc00684edcb092c19d0addcf51c22679b9ccd414c46cbf0a2f92ec9d9c3d6a3b.png",
        "sha256": "cc00684edcb092c19d0addcf51c22679b9ccd414c46cbf0a2f92ec9d9c3d6a3b"
      },
      {
        "path": "/data2/k6tk/5c/5c6cad251e0c600401d4276712df19e5bdefe7d4b826026cecfd60dacc36c715.png",
        "sha256": "5c6cad251e0c600401d4276712df19e5bdefe7d4b826026cecfd60dacc36c715"
      },
      {
        "path": "/data2/k6tk/43/43e1a85470d06c2b7785d995f2d7b9fce0b3a6fe1ccefe576e00f5d17bc4ab52.png",
        "sha256": "43e1a85470d06c2b7785d995f2d7b9fce0b3a6fe1ccefe576e00f5d17bc4ab52"
      },
      {
        "path": "/data2/k6tk/25/2547cb46bbce9708e9942e2a3a9d2a1ae84f46f42685bd3d62493038a3e189ae.png",
        "sha256": "2547cb46bbce9708e9942e2a3a9d2a1ae84f46f42685bd3d62493038a3e189ae"
      },
      {
        "path": "/data2/k6tk/38/38f07b18ab78b48c714aa5a08e4bce7f863454ed4d0dd97e91db8ebbea25e027.png",
        "sha256": "38f07b18ab78b48c714aa5a08e4bce7f863454ed4d0dd97e91db8ebbea25e027"
      },
      {
        "path": "/data2/k6tk/af/af277a75133b5c25f9c6b0349bd049224a2acfa40208f08e44c4b9bb9f2b347c.png",
        "sha256": "af277a75133b5c25f9c6b0349bd049224a2acfa40208f08e44c4b9bb9f2b347c"
      },
      {
        "path": "/data2/k6tk/e0/e059099e7bdf6042c154ed7831630de88be52f7e743a2884bb09636063227735.png",
        "sha256": "e059099e7bdf6042c154ed7831630de88be52f7e743a2884bb09636063227735"
      },
      {
        "path": "/data2/k6tk/47/47bc3bf34a89ddba64d2891cd6a9ace6ca8787f22fdaa85153d2b0d50f57595e.png",
        "sha256": "47bc3bf34a89ddba64d2891cd6a9ace6ca8787f22fdaa85153d2b0d50f57595e"
      },
      {
        "path": "/data2/k6tk/5d/5da6d91864fe2860706f6d63d3ad6a9099bafed4a2d7969d6620483cee0a2243.png",
        "sha256": "5da6d91864fe2860706f6d63d3ad6a9099bafed4a2d7969d6620483cee0a2243"
      },
      {
        "path": "/data2/k6tk/bc/bc1323ef906544dba6316bb5f1bbcab3b86db7acb8cb57ba5259434ef0923aec.png",
        "sha256": "bc1323ef906544dba6316bb5f1bbcab3b86db7acb8cb57ba5259434ef0923aec"
      },
      {
        "path": "/data2/k6tk/1a/1a750f2b3b97b87829b1b1617014d3abb52898421520f453d68e2562c32211e4.png",
        "sha256": "1a750f2b3b97b87829b1b1617014d3abb52898421520f453d68e2562c32211e4"
      },
      {
        "path": "/data2/k6tk/7d/7d53c2bf7588f9a1c0ec8515cdc4e510ddc2529c5cb97ebedddf64aa46679a80.png",
        "sha256": "7d53c2bf7588f9a1c0ec8515cdc4e510ddc2529c5cb97ebedddf64aa46679a80"
      },
      {
        "path": "/data2/k6tk/cf/cf6ef255d199d67a088aad2cf3228912f4415f9b6a4734d67b3b9a29ce8b0c40.png",
        "sha256": "cf6ef255d199d67a088aad2cf3228912f4415f9b6a4734d67b3b9a29ce8b0c40"
      },
      {
        "path": "/data2/k6tk/37/37dfb1bc3332ac3f6798f9275f2f4dcd5c59a6ad2a7556d48842fd0170fa2284.png",
        "sha256": "37dfb1bc3332ac3f6798f9275f2f4dcd5c59a6ad2a7556d48842fd0170fa2284"
      },
      {
        "path": "/data2/k6tk/55/555428f4f807621de8728d3966f761618f7b7597df3e545ada4620133689ed53.png",
        "sha256": "555428f4f807621de8728d3966f761618f7b7597df3e545ada4620133689ed53"
      },
      {
        "path": "/data2/k6tk/ea/ea93f055c749c5220c0eaef052c6f37be2d69ab9f9067fbda4d41099c14560ae.png",
        "sha256": "ea93f055c749c5220c0eaef052c6f37be2d69ab9f9067fbda4d41099c14560ae"
      },
      {
        "path": "/data2/k6tk/06/06c87d779ae1bacff1b354031f07b16b4b8d84ea657ff2fd35a213dd17340169.png",
        "sha256": "06c87d779ae1bacff1b354031f07b16b4b8d84ea657ff2fd35a213dd17340169"
      },
      {
        "path": "/data2/k6tk/d8/d8ba251ebb1143d111753ecfc2f05c8459f2d24bd078768ea65185bc7283a641.png",
        "sha256": "d8ba251ebb1143d111753ecfc2f05c8459f2d24bd078768ea65185bc7283a641"
      },
      {
        "path": "/data2/k6tk/6c/6c6d1aff12568d3e61bd8a924dd9b491b960751ec8fd53ba60a020557ae2c47d.png",
        "sha256": "6c6d1aff12568d3e61bd8a924dd9b491b960751ec8fd53ba60a020557ae2c47d"
      },
      {
        "path": "/data2/k6tk/45/45469bf398f936b2f398381532c1c774a907efc3f9b693f2590f16963bab0f55.png",
        "sha256": "45469bf398f936b2f398381532c1c774a907efc3f9b693f2590f16963bab0f55"
      },
      {
        "path": "/data2/k6tk/44/445f30dc0218d9ddf92b04ec005c1527cbaf59e00bbcb4edaebda68cab4e2042.png",
        "sha256": "445f30dc0218d9ddf92b04ec005c1527cbaf59e00bbcb4edaebda68cab4e2042"
      },
      {
        "path": "/data2/k6tk/20/20e33c47fc23894b37feb82ac1327c904e6ef43b68dc9774c30afbcd9cee904e.png",
        "sha256": "20e33c47fc23894b37feb82ac1327c904e6ef43b68dc9774c30afbcd9cee904e"
      },
      {
        "path": "/data2/k6tk/97/975d8ef2c9d023383598c759d64717f89a7850ad4871637b6f3c2335c41cf225.png",
        "sha256": "975d8ef2c9d023383598c759d64717f89a7850ad4871637b6f3c2335c41cf225"
      },
      {
        "path": "/data2/k6tk/1b/1b3a28161187e68a25374d66062b374ca7a6b106209760481cfe9d24aed14e61.png",
        "sha256": "1b3a28161187e68a25374d66062b374ca7a6b106209760481cfe9d24aed14e61"
      },
      {
        "path": "/data2/k6tk/c1/c198d5e5c2b9c5a98c49d99c70512c10311c26e0b5754c5e85ac2813431d929f.png",
        "sha256": "c198d5e5c2b9c5a98c49d99c70512c10311c26e0b5754c5e85ac2813431d929f"
      },
      {
        "path": "/data2/k6tk/90/90395eb1dfd9abdc2c89b2a3d0cf3e8576160a4393f26e613174781924bc126c.png",
        "sha256": "90395eb1dfd9abdc2c89b2a3d0cf3e8576160a4393f26e613174781924bc126c"
      },
      {
        "path": "/data2/k6tk/8a/8a34c50785faf34dff969933f1cb04f66a2520f50cbcd2b0dabacacf8a2c6882.png",
        "sha256": "8a34c50785faf34dff969933f1cb04f66a2520f50cbcd2b0dabacacf8a2c6882"
      },
      {
        "path": "/data2/k6tk/f0/f0a625f2de6c6495cad862455b9b004119c10c23ea5692ea9f298e2643d590c4.png",
        "sha256": "f0a625f2de6c6495cad862455b9b004119c10c23ea5692ea9f298e2643d590c4"
      },
      {
        "path": "/data2/k6tk/df/df6f8e08f074b202ea94f809172c51822d7c471ce30ae630623b8500ae1bcf5f.png",
        "sha256": "df6f8e08f074b202ea94f809172c51822d7c471ce30ae630623b8500ae1bcf5f"
      },
      {
        "path": "/data2/k6tk/e8/e88039b297c902c1da7a75cbdcab545a568fad7329a38865111d49441e524ea5.png",
        "sha256": "e88039b297c902c1da7a75cbdcab545a568fad7329a38865111d49441e524ea5"
      },
      {
        "path": "/data2/k6tk/5b/5b9787ea96045ed5db98a3b607d1b7ed032cd890d7be83480bac35884a22ba69.png",
        "sha256": "5b9787ea96045ed5db98a3b607d1b7ed032cd890d7be83480bac35884a22ba69"
      }
    ],
    "options": [
      "A. fewer",
      "B. equal number",
      "C. more"
    ],
    "question": "Count the separate objects in the 'table' and 'sofa' categories. For 'table' relative to 'sofa', which choice describes the result?",
    "timestamps": [
      0.0,
      1.4,
      2.9,
      4.3,
      5.8,
      7.2,
      8.7,
      10.1,
      11.6,
      13.0,
      14.5,
      15.9,
      17.3,
      18.8,
      20.2,
      21.7,
      23.1,
      24.6,
      26.0,
      27.5,
      28.9,
      30.3,
      31.8,
      33.2,
      34.7,
      36.1,
      37.6,
      39.0,
      40.5,
      41.9,
      43.4,
      44.8
    ],
    "total_num_frames": 449
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are fewer table instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 2. fbp_relcnt2_fd8f3e9e19dc3d7f8bb22e83

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-abd9409ff2b4a37483bbe12ab1d97fa35b6cf254aefae8a4e8ce6fe0c490bd8b",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/44796722",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/44796722.npz": "05282f6f06a420856e64c5dda99833441e1d2b59b85dfd4a1a46986530765af3",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "44796722.npz",
    "raster_sha256": "05282f6f06a420856e64c5dda99833441e1d2b59b85dfd4a1a46986530765af3",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "10",
      "count_a": 2,
      "count_b": 11,
      "ids_a": [
        2,
        3
      ],
      "ids_b": [
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        30,
        31,
        32
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue466242",
      "scene_use_cap": 24,
      "source_qid": "b12ct_a49c7cdb31cf8bafbd01073f",
      "source_row_sha256": "4874cc9f05c2dc8277e508f1b3d3697a30fbf73bd39a43123701a11f89d71e3a",
      "source_use_cap": 8,
      "template_id": 1,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_fd8f3e9e19dc3d7f8bb22e83",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "ve56298a3cffb",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      38,
      77,
      115,
      153,
      191,
      230,
      268,
      306,
      344,
      383,
      421,
      459,
      497,
      536,
      574,
      612,
      650,
      689,
      727,
      765,
      803,
      842,
      880,
      918,
      956,
      995,
      1033,
      1071,
      1109,
      1148,
      1186
    ],
    "frames": [
      {
        "path": "/data2/k6tk/7c/7c7b39931cfb7e0c62c2bec1722569c8fb098814c49a6474111f3d820473fb72.png",
        "sha256": "7c7b39931cfb7e0c62c2bec1722569c8fb098814c49a6474111f3d820473fb72"
      },
      {
        "path": "/data2/k6tk/f9/f941838f058fd5c80ecd176bf4f8b78bfe2e86656a5d519f9da71d51983a5aed.png",
        "sha256": "f941838f058fd5c80ecd176bf4f8b78bfe2e86656a5d519f9da71d51983a5aed"
      },
      {
        "path": "/data2/k6tk/44/4496df8a77008f979d6fe54dfb3b0e9e6a0d4be14149bd18d902fe5c3632d2c4.png",
        "sha256": "4496df8a77008f979d6fe54dfb3b0e9e6a0d4be14149bd18d902fe5c3632d2c4"
      },
      {
        "path": "/data2/k6tk/5c/5c7a0ad2aa16dd247d6f4a2c0c8075370ec652edb7d79e0dddc389d9d34cd29e.png",
        "sha256": "5c7a0ad2aa16dd247d6f4a2c0c8075370ec652edb7d79e0dddc389d9d34cd29e"
      },
      {
        "path": "/data2/k6tk/83/83752da983007c136456cc2d8867681e9747bc743dafc90e3f41fce1462b6f30.png",
        "sha256": "83752da983007c136456cc2d8867681e9747bc743dafc90e3f41fce1462b6f30"
      },
      {
        "path": "/data2/k6tk/cf/cfb122a698d13c8c015275b036eb489ccdbd09ad8ee0a90345d9f0e1a49867dd.png",
        "sha256": "cfb122a698d13c8c015275b036eb489ccdbd09ad8ee0a90345d9f0e1a49867dd"
      },
      {
        "path": "/data2/k6tk/37/3707bc80534a993ecdf64f9ecaa567298d10736906ecb566c41a7d9e397e9404.png",
        "sha256": "3707bc80534a993ecdf64f9ecaa567298d10736906ecb566c41a7d9e397e9404"
      },
      {
        "path": "/data2/k6tk/2b/2b987486f8cb8de29a09abf9090c53639fd7d31e099e516eef8329167cb4ff13.png",
        "sha256": "2b987486f8cb8de29a09abf9090c53639fd7d31e099e516eef8329167cb4ff13"
      },
      {
        "path": "/data2/k6tk/a8/a84fa9162926c25350d568ff71eb690b6703ab0b3fa509a450ae66d4e14e56ea.png",
        "sha256": "a84fa9162926c25350d568ff71eb690b6703ab0b3fa509a450ae66d4e14e56ea"
      },
      {
        "path": "/data2/k6tk/d6/d60602a06259da30f1ca134c7cd5bca9a57fac2de8d75cb06852b56141b9669c.png",
        "sha256": "d60602a06259da30f1ca134c7cd5bca9a57fac2de8d75cb06852b56141b9669c"
      },
      {
        "path": "/data2/k6tk/e8/e86cf53097f1fa97f99431fdd560e18851ad12ab7590caf78584364256c46996.png",
        "sha256": "e86cf53097f1fa97f99431fdd560e18851ad12ab7590caf78584364256c46996"
      },
      {
        "path": "/data2/k6tk/66/66cbe5b52f79da3a973e755b100d01fba7dae3a1d96f50bb0b068325b167939d.png",
        "sha256": "66cbe5b52f79da3a973e755b100d01fba7dae3a1d96f50bb0b068325b167939d"
      },
      {
        "path": "/data2/k6tk/68/682bc9788011348382702f14e92100027cf531743827a75e8219fe4ef8295a6d.png",
        "sha256": "682bc9788011348382702f14e92100027cf531743827a75e8219fe4ef8295a6d"
      },
      {
        "path": "/data2/k6tk/c3/c3759627fa713660add9be8c24c17bb5883537342956f5b07c060e41b593bafb.png",
        "sha256": "c3759627fa713660add9be8c24c17bb5883537342956f5b07c060e41b593bafb"
      },
      {
        "path": "/data2/k6tk/87/87a0d41707ae6c0ad748ae6e852ab150691086eb9b3eae8b673a6014de18f100.png",
        "sha256": "87a0d41707ae6c0ad748ae6e852ab150691086eb9b3eae8b673a6014de18f100"
      },
      {
        "path": "/data2/k6tk/f5/f541eec431dae8d02f540f39b0ffee7c0930963493ef463e40ffccece880c25f.png",
        "sha256": "f541eec431dae8d02f540f39b0ffee7c0930963493ef463e40ffccece880c25f"
      },
      {
        "path": "/data2/k6tk/9b/9b842a2ec58317638f3ca06c360b13e8c83ff0a21f62830128471850c09970dc.png",
        "sha256": "9b842a2ec58317638f3ca06c360b13e8c83ff0a21f62830128471850c09970dc"
      },
      {
        "path": "/data2/k6tk/99/99715fb3e6e5ef5ab6415a5dbcc9b694c10aef03752bab6b289588f0003bd753.png",
        "sha256": "99715fb3e6e5ef5ab6415a5dbcc9b694c10aef03752bab6b289588f0003bd753"
      },
      {
        "path": "/data2/k6tk/31/3120d14062049a9813453af3a36c4500589e22c90a157ec9267e5c3cb372c076.png",
        "sha256": "3120d14062049a9813453af3a36c4500589e22c90a157ec9267e5c3cb372c076"
      },
      {
        "path": "/data2/k6tk/10/10a2b72bdef42f026da7ffd0509615aef8c33e1248036548b00a6acd40a20090.png",
        "sha256": "10a2b72bdef42f026da7ffd0509615aef8c33e1248036548b00a6acd40a20090"
      },
      {
        "path": "/data2/k6tk/27/27c701a06ee2840164d455125e18d8bf83ac89a1fe07e9258f448fddfdd8fbb1.png",
        "sha256": "27c701a06ee2840164d455125e18d8bf83ac89a1fe07e9258f448fddfdd8fbb1"
      },
      {
        "path": "/data2/k6tk/67/678bc852a20b2c23eca0a253e97638f42f00edf0acfd1611deaeb3b064ca4ebb.png",
        "sha256": "678bc852a20b2c23eca0a253e97638f42f00edf0acfd1611deaeb3b064ca4ebb"
      },
      {
        "path": "/data2/k6tk/e5/e54d087af88cf9f883550f2575b5b0a62bf100b84f7dd24e1fa3df7d50140861.png",
        "sha256": "e54d087af88cf9f883550f2575b5b0a62bf100b84f7dd24e1fa3df7d50140861"
      },
      {
        "path": "/data2/k6tk/b7/b7c74c056fc8ea6cb72fb59e5615f02df56b06e3b83c26edfbe6a28abe76b7fb.png",
        "sha256": "b7c74c056fc8ea6cb72fb59e5615f02df56b06e3b83c26edfbe6a28abe76b7fb"
      },
      {
        "path": "/data2/k6tk/16/166898dbb281945d072af377635549d64a6c24506eb832d3c1f5fbe61a4ae83a.png",
        "sha256": "166898dbb281945d072af377635549d64a6c24506eb832d3c1f5fbe61a4ae83a"
      },
      {
        "path": "/data2/k6tk/cb/cba4272dde9e863df4da61426628c630419450aca150c1b52479c1c548c5058a.png",
        "sha256": "cba4272dde9e863df4da61426628c630419450aca150c1b52479c1c548c5058a"
      },
      {
        "path": "/data2/k6tk/f3/f316d26ba22fa3e2b2d2343ffd5a5a181ca68c9e94a741b9d278f0086fca8b24.png",
        "sha256": "f316d26ba22fa3e2b2d2343ffd5a5a181ca68c9e94a741b9d278f0086fca8b24"
      },
      {
        "path": "/data2/k6tk/ef/effdcff22e4bb92c38127bc2f9ae63c438eeadb9a80f5221c60c1670970189a4.png",
        "sha256": "effdcff22e4bb92c38127bc2f9ae63c438eeadb9a80f5221c60c1670970189a4"
      },
      {
        "path": "/data2/k6tk/f4/f45de6f6c575a57ecbeac2803b7bd9a30b0126b18ea8b8de925368ad494c0ca6.png",
        "sha256": "f45de6f6c575a57ecbeac2803b7bd9a30b0126b18ea8b8de925368ad494c0ca6"
      },
      {
        "path": "/data2/k6tk/01/013406a7fd72904761bd3e9b78e663e5a78fa402f8674726fe0ea031ae04306c.png",
        "sha256": "013406a7fd72904761bd3e9b78e663e5a78fa402f8674726fe0ea031ae04306c"
      },
      {
        "path": "/data2/k6tk/22/2250e08cce55aad9086a85ea26254c6c7094a9e9d6bad8b929c25350ec52249f.png",
        "sha256": "2250e08cce55aad9086a85ea26254c6c7094a9e9d6bad8b929c25350ec52249f"
      },
      {
        "path": "/data2/k6tk/0b/0bef36580cefaf84414e3686eb9d8c866db4b279d5227de9276c98910fac80a7.png",
        "sha256": "0bef36580cefaf84414e3686eb9d8c866db4b279d5227de9276c98910fac80a7"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Consider the room's 'table' objects as one group and its 'chair' objects as another. Which comparison describes the size of the first group?",
    "timestamps": [
      0.0,
      3.8,
      7.7,
      11.5,
      15.3,
      19.1,
      23.0,
      26.8,
      30.6,
      34.4,
      38.3,
      42.1,
      45.9,
      49.7,
      53.6,
      57.4,
      61.2,
      65.0,
      68.9,
      72.7,
      76.5,
      80.3,
      84.2,
      88.0,
      91.8,
      95.6,
      99.5,
      103.3,
      107.1,
      110.9,
      114.8,
      118.6
    ],
    "total_num_frames": 1187
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are fewer table instances than chair instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 3. fbp_relcnt2_4e5f1b475ab64edd191c2579

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-e1bd47121d346739709daa3f1e948d81f73bea999ab86275b16b35f94d1db664",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42899664",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42899664.npz": "226c87b05ad81304ca598e2f78366bf374fc9dc03390c46637acd3d33009b0d3",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42899664.npz",
    "raster_sha256": "226c87b05ad81304ca598e2f78366bf374fc9dc03390c46637acd3d33009b0d3",
    "relative_count": {
      "a": "chair",
      "b": "stool",
      "bucket": "3",
      "count_a": 2,
      "count_b": 3,
      "ids_a": [
        16,
        17
      ],
      "ids_b": [
        12,
        13,
        15
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue435723",
      "scene_use_cap": 24,
      "source_qid": "b12ct_d6cfd0d807c83b02b1e62955",
      "source_row_sha256": "4f9dfc44257e57f3ae70165d63fbda89ee302bfc247b35283774797af72a5377",
      "source_use_cap": 8,
      "template_id": 2,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_4e5f1b475ab64edd191c2579",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v035505b7ffb1",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      39,
      78,
      117,
      156,
      195,
      234,
      273,
      312,
      351,
      390,
      429,
      468,
      507,
      546,
      585,
      624,
      663,
      702,
      741,
      780,
      819,
      858,
      897,
      936,
      975,
      1014,
      1053,
      1092,
      1131,
      1170,
      1209
    ],
    "frames": [
      {
        "path": "/data2/k6tk/31/310531c6b95aaea68ab85e913bc79898eaa9d4d13c1a26b437014ebb1e6a3302.png",
        "sha256": "310531c6b95aaea68ab85e913bc79898eaa9d4d13c1a26b437014ebb1e6a3302"
      },
      {
        "path": "/data2/k6tk/f9/f99e6331507e33544d5a98c0671735eaa8428435481e1b133450443b045cc460.png",
        "sha256": "f99e6331507e33544d5a98c0671735eaa8428435481e1b133450443b045cc460"
      },
      {
        "path": "/data2/k6tk/c7/c7356cf347dcdd059e199e8893902799eca26dc5ebba87a9dc30a52393b3b7f6.png",
        "sha256": "c7356cf347dcdd059e199e8893902799eca26dc5ebba87a9dc30a52393b3b7f6"
      },
      {
        "path": "/data2/k6tk/8d/8d8aafe2e1c902c2419e08ec4b46b62564641d76db42fa81f10f5118a151ba61.png",
        "sha256": "8d8aafe2e1c902c2419e08ec4b46b62564641d76db42fa81f10f5118a151ba61"
      },
      {
        "path": "/data2/k6tk/db/db46c52c6c8aba033b47f1fd7dd6924ab3b22800022644d9815310076a9ed2cb.png",
        "sha256": "db46c52c6c8aba033b47f1fd7dd6924ab3b22800022644d9815310076a9ed2cb"
      },
      {
        "path": "/data2/k6tk/2c/2cec910862a3c46c7751bb736ba1e01e1c61eaf9aff301d1d6196c4010e3f96c.png",
        "sha256": "2cec910862a3c46c7751bb736ba1e01e1c61eaf9aff301d1d6196c4010e3f96c"
      },
      {
        "path": "/data2/k6tk/38/38c9ea0b4180221ff80f53508eafdd03a1d3463d24469c7d0a5ef8b9ebe4faff.png",
        "sha256": "38c9ea0b4180221ff80f53508eafdd03a1d3463d24469c7d0a5ef8b9ebe4faff"
      },
      {
        "path": "/data2/k6tk/29/29637b963254d4f81bb570aa28f8356cc9a0070e682ec94e488d73ba620e51e7.png",
        "sha256": "29637b963254d4f81bb570aa28f8356cc9a0070e682ec94e488d73ba620e51e7"
      },
      {
        "path": "/data2/k6tk/62/62dd4eb7f44c0dbbd4d0995de4d8c9dbc297cb7b3ee122059dec95b005a6151d.png",
        "sha256": "62dd4eb7f44c0dbbd4d0995de4d8c9dbc297cb7b3ee122059dec95b005a6151d"
      },
      {
        "path": "/data2/k6tk/7e/7ec8b93442617f055019f4e1e46af5110d15b76b10e51766213cb61d64d4a3d1.png",
        "sha256": "7ec8b93442617f055019f4e1e46af5110d15b76b10e51766213cb61d64d4a3d1"
      },
      {
        "path": "/data2/k6tk/28/28b198c475d20766a5eaccbb8c0374201bc9e2dad69ba636f510a0cecfc6d114.png",
        "sha256": "28b198c475d20766a5eaccbb8c0374201bc9e2dad69ba636f510a0cecfc6d114"
      },
      {
        "path": "/data2/k6tk/4c/4c712663f672c6b3c99625521e08e24e329fa734360515ca113cb1cfea06b0e5.png",
        "sha256": "4c712663f672c6b3c99625521e08e24e329fa734360515ca113cb1cfea06b0e5"
      },
      {
        "path": "/data2/k6tk/34/34134ae1bad6639ee45dfaf0a17f86e94a4b3358edab20759d598a5d6820bfce.png",
        "sha256": "34134ae1bad6639ee45dfaf0a17f86e94a4b3358edab20759d598a5d6820bfce"
      },
      {
        "path": "/data2/k6tk/2c/2c5632c5d9121938cd041d23e86b585d83b37668324c762a10fc570683b6761f.png",
        "sha256": "2c5632c5d9121938cd041d23e86b585d83b37668324c762a10fc570683b6761f"
      },
      {
        "path": "/data2/k6tk/7e/7ef1bea66681fd70402aab56fd337cf456be716f3f8e3f73bc80db1201ac6f91.png",
        "sha256": "7ef1bea66681fd70402aab56fd337cf456be716f3f8e3f73bc80db1201ac6f91"
      },
      {
        "path": "/data2/k6tk/e2/e2979f1aa38b6c2eda8c963b177f002872cbb5d7a4c51ff866afe978dda26880.png",
        "sha256": "e2979f1aa38b6c2eda8c963b177f002872cbb5d7a4c51ff866afe978dda26880"
      },
      {
        "path": "/data2/k6tk/67/67755b2cd2a2daf6401dd1ad9a5fdf7e193b391c236f3bf82309a74cd071fe46.png",
        "sha256": "67755b2cd2a2daf6401dd1ad9a5fdf7e193b391c236f3bf82309a74cd071fe46"
      },
      {
        "path": "/data2/k6tk/82/82fac4d458a1d45d0e2bd0480fd7c451db64c14f67f7bb5af933e68961a4541a.png",
        "sha256": "82fac4d458a1d45d0e2bd0480fd7c451db64c14f67f7bb5af933e68961a4541a"
      },
      {
        "path": "/data2/k6tk/0b/0bf1655de20f0f61e3ceaeb90af4be124988d73bd316ef18e5019c216749c27b.png",
        "sha256": "0bf1655de20f0f61e3ceaeb90af4be124988d73bd316ef18e5019c216749c27b"
      },
      {
        "path": "/data2/k6tk/5e/5e784ad06e9a8fe787c6db3da9049124f72d292ef22ce91ad901ea8d7cfdeb6a.png",
        "sha256": "5e784ad06e9a8fe787c6db3da9049124f72d292ef22ce91ad901ea8d7cfdeb6a"
      },
      {
        "path": "/data2/k6tk/be/be1b4eff755a25077554e5bfc28214a61407fec9d66716697cfcca5b0e2d7f1d.png",
        "sha256": "be1b4eff755a25077554e5bfc28214a61407fec9d66716697cfcca5b0e2d7f1d"
      },
      {
        "path": "/data2/k6tk/0f/0fee8adba43ce6148d59b2f452ac21da62bd690bf24bc4b6fa1baf03c5053d37.png",
        "sha256": "0fee8adba43ce6148d59b2f452ac21da62bd690bf24bc4b6fa1baf03c5053d37"
      },
      {
        "path": "/data2/k6tk/4a/4aebdc588ba2aa136317ff32276dc75a0aba995826790849215b67799af811ef.png",
        "sha256": "4aebdc588ba2aa136317ff32276dc75a0aba995826790849215b67799af811ef"
      },
      {
        "path": "/data2/k6tk/ab/ab1a3acc7c3cbdbde6aeaa05664c23dd36d2d72c80a7598309fb58756a5857d7.png",
        "sha256": "ab1a3acc7c3cbdbde6aeaa05664c23dd36d2d72c80a7598309fb58756a5857d7"
      },
      {
        "path": "/data2/k6tk/66/66773be784d3de5d526128edcb1a7ad03d16dae0a0973a89528bcdae80bd2100.png",
        "sha256": "66773be784d3de5d526128edcb1a7ad03d16dae0a0973a89528bcdae80bd2100"
      },
      {
        "path": "/data2/k6tk/57/57b5642708aa93b3848dd35c9cb57daa89a40077f2f38a59523973da8ef93c4b.png",
        "sha256": "57b5642708aa93b3848dd35c9cb57daa89a40077f2f38a59523973da8ef93c4b"
      },
      {
        "path": "/data2/k6tk/86/8613db788115b17b9858a8312419b112ae3c04c2c02ed3f87dcbb56cec52204c.png",
        "sha256": "8613db788115b17b9858a8312419b112ae3c04c2c02ed3f87dcbb56cec52204c"
      },
      {
        "path": "/data2/k6tk/55/55cbfb78c3a0d433f4c9c82a7c5f2d455eacf564d384fcf98ab3741a7b1e966c.png",
        "sha256": "55cbfb78c3a0d433f4c9c82a7c5f2d455eacf564d384fcf98ab3741a7b1e966c"
      },
      {
        "path": "/data2/k6tk/48/48006fe70ed5c85d765cdfaf5d18faf6ac4e002cca1f579c73744e216d7119c9.png",
        "sha256": "48006fe70ed5c85d765cdfaf5d18faf6ac4e002cca1f579c73744e216d7119c9"
      },
      {
        "path": "/data2/k6tk/65/658e372c241a68dc26d3543489111f1eeb1afc3b358ef6dc5c8e5449cf037cff.png",
        "sha256": "658e372c241a68dc26d3543489111f1eeb1afc3b358ef6dc5c8e5449cf037cff"
      },
      {
        "path": "/data2/k6tk/3d/3dfd48de9a5bfa5670313565ae778fce6d03ccbb25125bcca1bf1b51a8fd6fda.png",
        "sha256": "3dfd48de9a5bfa5670313565ae778fce6d03ccbb25125bcca1bf1b51a8fd6fda"
      },
      {
        "path": "/data2/k6tk/77/77571133311a4c0b521a660b10594beb3b14c0ddbdca1c09a1fcd9a463d4bac1.png",
        "sha256": "77571133311a4c0b521a660b10594beb3b14c0ddbdca1c09a1fcd9a463d4bac1"
      }
    ],
    "options": [
      "A. equal number",
      "B. fewer",
      "C. more"
    ],
    "question": "Tally distinct instances of 'chair' and then distinct instances of 'stool' across the video. How does the first tally compare with the second?",
    "timestamps": [
      0.0,
      3.9,
      7.8,
      11.7,
      15.6,
      19.5,
      23.4,
      27.3,
      31.2,
      35.1,
      39.0,
      42.9,
      46.8,
      50.7,
      54.6,
      58.5,
      62.4,
      66.3,
      70.2,
      74.1,
      78.0,
      81.9,
      85.8,
      89.7,
      93.6,
      97.5,
      101.4,
      105.3,
      109.2,
      113.1,
      117.0,
      120.9
    ],
    "total_num_frames": 1210
  },
  "target": "<think>\nlocate the distinct instances of chair; count each once across the frames.\nlocate the distinct instances of stool; count each once across the frames.\nSo there are fewer chair instances than stool instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 4. fbp_relcnt2_02f5a17d3fff69d6cbc78779

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-4a6288e6c2da8684cecd9d4b84d0955c8218eb7b208e6b88a22c7207d427ce11",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47115143",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47115143.npz": "56da0a4a90ab9da796b2f0a51f38b00deb99f09ae46fa27c953ee02ff59e5fc8",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47115143.npz",
    "raster_sha256": "56da0a4a90ab9da796b2f0a51f38b00deb99f09ae46fa27c953ee02ff59e5fc8",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "3",
      "count_a": 3,
      "count_b": 2,
      "ids_a": [
        2,
        3,
        6
      ],
      "ids_b": [
        0,
        1
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue469607",
      "scene_use_cap": 24,
      "source_qid": "b12ct_3286b1c843f7246c13ceb383",
      "source_row_sha256": "a50e26752be19131884fe0ef1cbe874c861bfbf2d1e9dc26231442233a2c52eb",
      "source_use_cap": 8,
      "template_id": 3,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_02f5a17d3fff69d6cbc78779",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v555b182b3440",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      51,
      102,
      153,
      205,
      256,
      307,
      358,
      409,
      460,
      512,
      563,
      614,
      665,
      716,
      767,
      819,
      870,
      921,
      972,
      1023,
      1074,
      1126,
      1177,
      1228,
      1279,
      1330,
      1381,
      1433,
      1484,
      1535,
      1586
    ],
    "frames": [
      {
        "path": "/data2/k6tk/43/43f806a2c3c7d21bf2daedb2dc7ecf58e9140a7bef2fd8c7d45a3443be9a9cbb.png",
        "sha256": "43f806a2c3c7d21bf2daedb2dc7ecf58e9140a7bef2fd8c7d45a3443be9a9cbb"
      },
      {
        "path": "/data2/k6tk/62/626c2234dc5576823e73e3750cb81eaf101d1f5eb73271255dc1cf76750a7913.png",
        "sha256": "626c2234dc5576823e73e3750cb81eaf101d1f5eb73271255dc1cf76750a7913"
      },
      {
        "path": "/data2/k6tk/c8/c808335c4e0cab1d007cf716f32c0d7ea079272ebd3b8543bfb313e899c57fa7.png",
        "sha256": "c808335c4e0cab1d007cf716f32c0d7ea079272ebd3b8543bfb313e899c57fa7"
      },
      {
        "path": "/data2/k6tk/87/870a3d4da50a242a95e9f7458e32482b472b85534aefb6ec26203c1bd261b867.png",
        "sha256": "870a3d4da50a242a95e9f7458e32482b472b85534aefb6ec26203c1bd261b867"
      },
      {
        "path": "/data2/k6tk/ad/ad42933f2f6a956ac71277114cbfbe1d7df5bbdae2bf126a7989bfb9c834e678.png",
        "sha256": "ad42933f2f6a956ac71277114cbfbe1d7df5bbdae2bf126a7989bfb9c834e678"
      },
      {
        "path": "/data2/k6tk/36/36b2b29ea49aef3ee2d78ce2f848154003e05f4975481b91c4be11b5822bd804.png",
        "sha256": "36b2b29ea49aef3ee2d78ce2f848154003e05f4975481b91c4be11b5822bd804"
      },
      {
        "path": "/data2/k6tk/b6/b6152036e9aaa95500ef495d8dd46ece3db5de142d467f90644759c7794d5bf6.png",
        "sha256": "b6152036e9aaa95500ef495d8dd46ece3db5de142d467f90644759c7794d5bf6"
      },
      {
        "path": "/data2/k6tk/da/dafb098ac4fec24b608de7375aad4c0a47285174a45fcbfafed37b70a2028585.png",
        "sha256": "dafb098ac4fec24b608de7375aad4c0a47285174a45fcbfafed37b70a2028585"
      },
      {
        "path": "/data2/k6tk/55/556e8f5e82679700da717f0073d3273bd19a3413f37a0c4f0c51ee5100eee1da.png",
        "sha256": "556e8f5e82679700da717f0073d3273bd19a3413f37a0c4f0c51ee5100eee1da"
      },
      {
        "path": "/data2/k6tk/69/698788ca5cb011adbd9a19f4bc834c23f1501f7e5e1c2505fad0f67776f52115.png",
        "sha256": "698788ca5cb011adbd9a19f4bc834c23f1501f7e5e1c2505fad0f67776f52115"
      },
      {
        "path": "/data2/k6tk/2e/2e0d619a2bf1156229653c3db232459764994762d0c1fc99b306bc5b5ff56fe6.png",
        "sha256": "2e0d619a2bf1156229653c3db232459764994762d0c1fc99b306bc5b5ff56fe6"
      },
      {
        "path": "/data2/k6tk/93/93fe705c8b027e877d9e1b0ebf30b45c1e7dfdf552e010522e8daa8c8ed22d0d.png",
        "sha256": "93fe705c8b027e877d9e1b0ebf30b45c1e7dfdf552e010522e8daa8c8ed22d0d"
      },
      {
        "path": "/data2/k6tk/f8/f8a113b019c411fa3c0004ae88343e39dd7e0520717c9bda1f6eab5877fb726e.png",
        "sha256": "f8a113b019c411fa3c0004ae88343e39dd7e0520717c9bda1f6eab5877fb726e"
      },
      {
        "path": "/data2/k6tk/95/95eeb3b5ecfa76af2eaace88167b4a10ab10cbe658cbd940db9e18a9d96fd604.png",
        "sha256": "95eeb3b5ecfa76af2eaace88167b4a10ab10cbe658cbd940db9e18a9d96fd604"
      },
      {
        "path": "/data2/k6tk/94/94d6be7070614c91a7a47a30ac683a07234f6f2bad036060405967f04adb7c8d.png",
        "sha256": "94d6be7070614c91a7a47a30ac683a07234f6f2bad036060405967f04adb7c8d"
      },
      {
        "path": "/data2/k6tk/9e/9e03c751f36cdc4d60238899f95a3ce2c615b44ade881f30ee2a331a3d5fd6be.png",
        "sha256": "9e03c751f36cdc4d60238899f95a3ce2c615b44ade881f30ee2a331a3d5fd6be"
      },
      {
        "path": "/data2/k6tk/b9/b96fe9f0dc80f2688acc2c2bc5b17e195deb533f5de4952ddd1801dd8690e6ab.png",
        "sha256": "b96fe9f0dc80f2688acc2c2bc5b17e195deb533f5de4952ddd1801dd8690e6ab"
      },
      {
        "path": "/data2/k6tk/f3/f30f4326d8fd35d3b0d4be1feb85d6fff22d2d06e20a29e4487f3f21e1c250bb.png",
        "sha256": "f30f4326d8fd35d3b0d4be1feb85d6fff22d2d06e20a29e4487f3f21e1c250bb"
      },
      {
        "path": "/data2/k6tk/42/42727e43c75065d15ae6ff886fe838d492b808aecb6fadfbacb6808a76378ddd.png",
        "sha256": "42727e43c75065d15ae6ff886fe838d492b808aecb6fadfbacb6808a76378ddd"
      },
      {
        "path": "/data2/k6tk/82/82368894a6a63930a2e3f635cceda6c0a694b9170ff155131edfa5b0c22c60e3.png",
        "sha256": "82368894a6a63930a2e3f635cceda6c0a694b9170ff155131edfa5b0c22c60e3"
      },
      {
        "path": "/data2/k6tk/71/715d3fb20683b071923d67cfb96223818ad2809c6cfb401bf1ed784bdba7ce21.png",
        "sha256": "715d3fb20683b071923d67cfb96223818ad2809c6cfb401bf1ed784bdba7ce21"
      },
      {
        "path": "/data2/k6tk/89/8929048826018aca29c2bbe3697198f26819cca5e5f7772956743275102a09dd.png",
        "sha256": "8929048826018aca29c2bbe3697198f26819cca5e5f7772956743275102a09dd"
      },
      {
        "path": "/data2/k6tk/56/56c9791fb2aeceadd7078b202590a310272bdaa7d11509a494821f968dc229dd.png",
        "sha256": "56c9791fb2aeceadd7078b202590a310272bdaa7d11509a494821f968dc229dd"
      },
      {
        "path": "/data2/k6tk/a1/a140c5f614c3a1d74e42135f4df5b021c69671c16426e23792ee8a7bcdcbe4ce.png",
        "sha256": "a140c5f614c3a1d74e42135f4df5b021c69671c16426e23792ee8a7bcdcbe4ce"
      },
      {
        "path": "/data2/k6tk/f6/f64da99dd1e752bcfa7c5de5439254ca7e4078792ac883dabea19fe86df7a3d5.png",
        "sha256": "f64da99dd1e752bcfa7c5de5439254ca7e4078792ac883dabea19fe86df7a3d5"
      },
      {
        "path": "/data2/k6tk/0f/0f37b9d20ac4c21081cd3e7d3f2d0e6dbd73064f406d8c51b3c22b64c1bfc3a9.png",
        "sha256": "0f37b9d20ac4c21081cd3e7d3f2d0e6dbd73064f406d8c51b3c22b64c1bfc3a9"
      },
      {
        "path": "/data2/k6tk/96/9628a015c6e7e8c1b97e9766a80ebdad35bc74145892f65505c1a7b53c406c3b.png",
        "sha256": "9628a015c6e7e8c1b97e9766a80ebdad35bc74145892f65505c1a7b53c406c3b"
      },
      {
        "path": "/data2/k6tk/ca/ca3526cfd784ec11d920a8bedb44077717d603ab7ef78e86f186372571d9706c.png",
        "sha256": "ca3526cfd784ec11d920a8bedb44077717d603ab7ef78e86f186372571d9706c"
      },
      {
        "path": "/data2/k6tk/15/1525408efd4a6ecc7c70a1b7831925c818be0e003191a038313be6fa7bc87f0c.png",
        "sha256": "1525408efd4a6ecc7c70a1b7831925c818be0e003191a038313be6fa7bc87f0c"
      },
      {
        "path": "/data2/k6tk/28/2869b0ebbe133eeebfaacb4020b73c94be257ee450b637aa7481610184487c3f.png",
        "sha256": "2869b0ebbe133eeebfaacb4020b73c94be257ee450b637aa7481610184487c3f"
      },
      {
        "path": "/data2/k6tk/a7/a77dbacd26bf75d1a2de852f41bfe5790959fc85676089aaa2e1394418472cbf.png",
        "sha256": "a77dbacd26bf75d1a2de852f41bfe5790959fc85676089aaa2e1394418472cbf"
      },
      {
        "path": "/data2/k6tk/52/5202f564187046ac09cfbeda3863ce75cb1aebf97b50c01c18b24720d4dfae8c.png",
        "sha256": "5202f564187046ac09cfbeda3863ce75cb1aebf97b50c01c18b24720d4dfae8c"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "Use a separate tally for each category: 'table' followed by 'sofa'. Which option correctly compares the first category's total to the second category's total?",
    "timestamps": [
      0.0,
      5.1,
      10.2,
      15.3,
      20.5,
      25.6,
      30.7,
      35.8,
      40.9,
      46.0,
      51.2,
      56.3,
      61.4,
      66.5,
      71.6,
      76.7,
      81.9,
      87.0,
      92.1,
      97.2,
      102.3,
      107.4,
      112.6,
      117.7,
      122.8,
      127.9,
      133.0,
      138.1,
      143.3,
      148.4,
      153.5,
      158.6
    ],
    "total_num_frames": 1587
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are more table instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 5. fbp_relcnt2_1051efbb3f9ef7e875013e60

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-edac027e2126b79cc0e877d7eff54da1e0f79c3aa490042978fd551bf95f3dbd",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41159830",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41159830.npz": "76f220cbc53b1af3a73f4e01f603f6c2622ad6040c7e1ec0f2df5d5eedfce512",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41159830.npz",
    "raster_sha256": "76f220cbc53b1af3a73f4e01f603f6c2622ad6040c7e1ec0f2df5d5eedfce512",
    "relative_count": {
      "a": "tv",
      "b": "sofa",
      "bucket": "5",
      "count_a": 1,
      "count_b": 5,
      "ids_a": [
        12
      ],
      "ids_b": [
        0,
        2,
        4,
        6,
        13
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue382967",
      "scene_use_cap": 24,
      "source_qid": "b12ct_1343d0a3b4f0fba3364b219a",
      "source_row_sha256": "4938ac2de583eb9315e3da199bd0afface450107baf276774ec7cb98611eb154",
      "source_use_cap": 8,
      "template_id": 4,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_1051efbb3f9ef7e875013e60",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v923e85ff65f3",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      55,
      110,
      165,
      220,
      275,
      330,
      385,
      440,
      495,
      550,
      605,
      660,
      715,
      770,
      825,
      880,
      935,
      990,
      1045,
      1100,
      1155,
      1210,
      1265,
      1320,
      1375,
      1430,
      1485,
      1540,
      1595,
      1650,
      1705
    ],
    "frames": [
      {
        "path": "/data2/k6tk/46/46fd2c6c2457f8cbc749fb1af7b746fb7a12aeeb6974c7a8f39f430b458527d0.png",
        "sha256": "46fd2c6c2457f8cbc749fb1af7b746fb7a12aeeb6974c7a8f39f430b458527d0"
      },
      {
        "path": "/data2/k6tk/6a/6a124f0d3fefa7b0da10d5b5e6afb0ad7923f8d519c6f8a6963693008afc8369.png",
        "sha256": "6a124f0d3fefa7b0da10d5b5e6afb0ad7923f8d519c6f8a6963693008afc8369"
      },
      {
        "path": "/data2/k6tk/61/61a16adae60fb7eba68a09a6d0c9b70e40d05bf8b059200912a82a1f22251f2e.png",
        "sha256": "61a16adae60fb7eba68a09a6d0c9b70e40d05bf8b059200912a82a1f22251f2e"
      },
      {
        "path": "/data2/k6tk/37/37f380e1ead66e8d90498462491cfb1049093030f72e637f7324c51f92f85187.png",
        "sha256": "37f380e1ead66e8d90498462491cfb1049093030f72e637f7324c51f92f85187"
      },
      {
        "path": "/data2/k6tk/44/4408bc036009ceea4e1406e6c37b79d96f5f872e880b11873dcb67855ee354ed.png",
        "sha256": "4408bc036009ceea4e1406e6c37b79d96f5f872e880b11873dcb67855ee354ed"
      },
      {
        "path": "/data2/k6tk/f7/f791c7b94f3e839c87dc5e7f0530d6a03106cd5590499d76bcc3342b96a02a28.png",
        "sha256": "f791c7b94f3e839c87dc5e7f0530d6a03106cd5590499d76bcc3342b96a02a28"
      },
      {
        "path": "/data2/k6tk/3a/3ad41a7b38d2d8b0e25710cf4471bc9dbf67d9be8b6345958ac91d99f704d3be.png",
        "sha256": "3ad41a7b38d2d8b0e25710cf4471bc9dbf67d9be8b6345958ac91d99f704d3be"
      },
      {
        "path": "/data2/k6tk/a7/a7026717bc05bd68f122fa82373d71ebba7a506744986653196a59fb297566a8.png",
        "sha256": "a7026717bc05bd68f122fa82373d71ebba7a506744986653196a59fb297566a8"
      },
      {
        "path": "/data2/k6tk/df/df206485ad9626cfc8ab9f5d9d9da39efcd66d1ced3e3da37e5ba235fed07b65.png",
        "sha256": "df206485ad9626cfc8ab9f5d9d9da39efcd66d1ced3e3da37e5ba235fed07b65"
      },
      {
        "path": "/data2/k6tk/52/5282c806bcbacd8364913e36bc19b5a734272c4fad63d36857ef8958ba52918c.png",
        "sha256": "5282c806bcbacd8364913e36bc19b5a734272c4fad63d36857ef8958ba52918c"
      },
      {
        "path": "/data2/k6tk/d1/d18bf9a253f924402c20f2d219ee504d73e43993a68d8eb3bd762f2afb82a1d5.png",
        "sha256": "d18bf9a253f924402c20f2d219ee504d73e43993a68d8eb3bd762f2afb82a1d5"
      },
      {
        "path": "/data2/k6tk/46/461e2d8d12444f4213e213127fc23b6f2250ae705b1dbb8cdbaf3a4e02332c10.png",
        "sha256": "461e2d8d12444f4213e213127fc23b6f2250ae705b1dbb8cdbaf3a4e02332c10"
      },
      {
        "path": "/data2/k6tk/dd/dde3cc9f4b1ba318e34368eae6d4e3dc42b97ca8764a44b3892cb09c35c4f0d3.png",
        "sha256": "dde3cc9f4b1ba318e34368eae6d4e3dc42b97ca8764a44b3892cb09c35c4f0d3"
      },
      {
        "path": "/data2/k6tk/e3/e34e50bbe5f7e64e66bf31867d39d67bea1d6ad43378316d40b1443854f392a7.png",
        "sha256": "e34e50bbe5f7e64e66bf31867d39d67bea1d6ad43378316d40b1443854f392a7"
      },
      {
        "path": "/data2/k6tk/59/59d46561e5c9923434b6e71f9d540cb733549b51db1b39bf85c2f431d97328a5.png",
        "sha256": "59d46561e5c9923434b6e71f9d540cb733549b51db1b39bf85c2f431d97328a5"
      },
      {
        "path": "/data2/k6tk/ca/cac00220c9151b358f592ee2bcd9fe09184400184adc858b2f206a1f47eb22c9.png",
        "sha256": "cac00220c9151b358f592ee2bcd9fe09184400184adc858b2f206a1f47eb22c9"
      },
      {
        "path": "/data2/k6tk/01/0109e2fb4fb17669f8bab83e8febbc1ab4730c00ab60f6a7e930c0a482fb0e2b.png",
        "sha256": "0109e2fb4fb17669f8bab83e8febbc1ab4730c00ab60f6a7e930c0a482fb0e2b"
      },
      {
        "path": "/data2/k6tk/3c/3c9d4b5ab7517758c4519bc57e5c4b1c770a06329496d2546b132ac95d86344a.png",
        "sha256": "3c9d4b5ab7517758c4519bc57e5c4b1c770a06329496d2546b132ac95d86344a"
      },
      {
        "path": "/data2/k6tk/f0/f0879507038f9e9cd954e420dc717061eadeeeaea65c3eae3f36e9b1ab4797d2.png",
        "sha256": "f0879507038f9e9cd954e420dc717061eadeeeaea65c3eae3f36e9b1ab4797d2"
      },
      {
        "path": "/data2/k6tk/f2/f2f68faa31e472438f155c956d6936ac1468ab492665514c66fba6814dcba0c9.png",
        "sha256": "f2f68faa31e472438f155c956d6936ac1468ab492665514c66fba6814dcba0c9"
      },
      {
        "path": "/data2/k6tk/94/944ab745585e819807317bea3cd19a875c136788a37420d72e41d0515bf7de88.png",
        "sha256": "944ab745585e819807317bea3cd19a875c136788a37420d72e41d0515bf7de88"
      },
      {
        "path": "/data2/k6tk/2c/2cfa4dabc0050c6c48ba8616a855a5df288c8fde2beb8fed9185fa0d8de329cd.png",
        "sha256": "2cfa4dabc0050c6c48ba8616a855a5df288c8fde2beb8fed9185fa0d8de329cd"
      },
      {
        "path": "/data2/k6tk/f5/f551f11e8796df95ce1c26f3cf4410dcf541e69481a26dff13dd7f60ec7cd20a.png",
        "sha256": "f551f11e8796df95ce1c26f3cf4410dcf541e69481a26dff13dd7f60ec7cd20a"
      },
      {
        "path": "/data2/k6tk/ca/cac893690cd70a65936a229e5d77f6289041c8a4a6f60959db593e40184954a1.png",
        "sha256": "cac893690cd70a65936a229e5d77f6289041c8a4a6f60959db593e40184954a1"
      },
      {
        "path": "/data2/k6tk/fa/faf5bf5c0e25c3524938a1e19dbe9253fae2c5f0618be06d54ec5a9bb554b9f7.png",
        "sha256": "faf5bf5c0e25c3524938a1e19dbe9253fae2c5f0618be06d54ec5a9bb554b9f7"
      },
      {
        "path": "/data2/k6tk/04/048f1bcd5eca0761a1a09e3f58087048451ed86a0254b90247b4b545e292e6f8.png",
        "sha256": "048f1bcd5eca0761a1a09e3f58087048451ed86a0254b90247b4b545e292e6f8"
      },
      {
        "path": "/data2/k6tk/71/7107d05b7cbd02cae05e9b06ff737d4138cb6ecfb3af53f2d5afb895beffd2eb.png",
        "sha256": "7107d05b7cbd02cae05e9b06ff737d4138cb6ecfb3af53f2d5afb895beffd2eb"
      },
      {
        "path": "/data2/k6tk/ce/ce23a8c3160865d88721d80e565a23d1daf68f33b6a64f6616189e6eada5a82f.png",
        "sha256": "ce23a8c3160865d88721d80e565a23d1daf68f33b6a64f6616189e6eada5a82f"
      },
      {
        "path": "/data2/k6tk/4e/4ec3d55c529a760b93364b036065bb8db29abcf9a64a4f68a0c576a53d9af4fa.png",
        "sha256": "4ec3d55c529a760b93364b036065bb8db29abcf9a64a4f68a0c576a53d9af4fa"
      },
      {
        "path": "/data2/k6tk/54/54767941832d6c08dc9974529cf3f2f080d27578d3cd7e1a96b49918781d11e5.png",
        "sha256": "54767941832d6c08dc9974529cf3f2f080d27578d3cd7e1a96b49918781d11e5"
      },
      {
        "path": "/data2/k6tk/df/df8579a95426951baefdb1078bf2280f03b1e0792627fe49ce1460b357eebbd9.png",
        "sha256": "df8579a95426951baefdb1078bf2280f03b1e0792627fe49ce1460b357eebbd9"
      },
      {
        "path": "/data2/k6tk/e0/e0322ae8a2a5aa7946a518e8e948dba63f6a340d415259bac0264325eab3f368.png",
        "sha256": "e0322ae8a2a5aa7946a518e8e948dba63f6a340d415259bac0264325eab3f368"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "Inspect the room for objects belonging to 'tv' and 'sofa'. After counting each object once, choose the relation of the 'tv' count to the 'sofa' count.",
    "timestamps": [
      0.0,
      5.5,
      11.0,
      16.5,
      22.0,
      27.5,
      33.0,
      38.5,
      44.0,
      49.5,
      55.0,
      60.5,
      66.0,
      71.5,
      77.0,
      82.5,
      88.0,
      93.5,
      99.0,
      104.5,
      110.0,
      115.5,
      121.0,
      126.5,
      132.0,
      137.5,
      143.0,
      148.5,
      154.0,
      159.5,
      165.0,
      170.5
    ],
    "total_num_frames": 1706
  },
  "target": "<think>\nlocate the distinct instances of tv; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are fewer tv instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 6. fbp_relcnt2_56c9c76ffb555dbf7fad751f

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-7e07c6d7fff8726b154227346ece6b21420554026357f8f977a1fd47add1a493",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47204783",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47204783.npz": "6336475706c0b2d39228d944a283371f125ee9fbac15e4d37423479f38967ccc",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47204783.npz",
    "raster_sha256": "6336475706c0b2d39228d944a283371f125ee9fbac15e4d37423479f38967ccc",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "3",
      "count_a": 1,
      "count_b": 3,
      "ids_a": [
        12
      ],
      "ids_b": [
        0,
        2,
        3
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue472473",
      "scene_use_cap": 24,
      "source_qid": "b12ct_e2eb441eaef17a3a147f5509",
      "source_row_sha256": "fd7a78f38f72bc429350c263387d7fcca1bb4d6bffb70fe295c35dc3781110d7",
      "source_use_cap": 8,
      "template_id": 5,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_56c9c76ffb555dbf7fad751f",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v4a9d50d82af7",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      10,
      20,
      29,
      39,
      49,
      59,
      68,
      78,
      88,
      98,
      108,
      117,
      127,
      137,
      147,
      156,
      166,
      176,
      186,
      195,
      205,
      215,
      225,
      235,
      244,
      254,
      264,
      274,
      283,
      293,
      303
    ],
    "frames": [
      {
        "path": "/data2/k6tk/94/948baa833e79e8b06c921f6c9b306e194214191e0541ebe889e230bdacf31560.png",
        "sha256": "948baa833e79e8b06c921f6c9b306e194214191e0541ebe889e230bdacf31560"
      },
      {
        "path": "/data2/k6tk/1f/1f9362a7cd80100fb5f32002e1fb50280074ceec4ef49e9ea3cf497a0659a7d4.png",
        "sha256": "1f9362a7cd80100fb5f32002e1fb50280074ceec4ef49e9ea3cf497a0659a7d4"
      },
      {
        "path": "/data2/k6tk/2e/2edf9adfe70a76f34b920d1c758feb844d21ba3a6fd06237ef640753724e4d6c.png",
        "sha256": "2edf9adfe70a76f34b920d1c758feb844d21ba3a6fd06237ef640753724e4d6c"
      },
      {
        "path": "/data2/k6tk/41/4159b43daaa628b8c7d827e6b678fca367e1d8761bfe2b293034bc3d584c8cd7.png",
        "sha256": "4159b43daaa628b8c7d827e6b678fca367e1d8761bfe2b293034bc3d584c8cd7"
      },
      {
        "path": "/data2/k6tk/04/041b41823f533ac5e0ac3d1772c21ff07d1cde4fd3261a099820e526569a8eb9.png",
        "sha256": "041b41823f533ac5e0ac3d1772c21ff07d1cde4fd3261a099820e526569a8eb9"
      },
      {
        "path": "/data2/k6tk/25/254f792253d0ad9b1833ba49beb3c8b0fd52065fd43aadb6b63fd48d99264b6a.png",
        "sha256": "254f792253d0ad9b1833ba49beb3c8b0fd52065fd43aadb6b63fd48d99264b6a"
      },
      {
        "path": "/data2/k6tk/82/82d2099dc50a6f41120da2ff983342714c500ef3400be3001889e24eb7fbeb11.png",
        "sha256": "82d2099dc50a6f41120da2ff983342714c500ef3400be3001889e24eb7fbeb11"
      },
      {
        "path": "/data2/k6tk/c8/c8264cc427e3e5acd77f2eee3c5de65bc051fffa45d0462c20cdc36bb14b0122.png",
        "sha256": "c8264cc427e3e5acd77f2eee3c5de65bc051fffa45d0462c20cdc36bb14b0122"
      },
      {
        "path": "/data2/k6tk/00/00c3719689dd18786620de2c6cd3cc5c7f03815438072e96df237e5092a9bd34.png",
        "sha256": "00c3719689dd18786620de2c6cd3cc5c7f03815438072e96df237e5092a9bd34"
      },
      {
        "path": "/data2/k6tk/96/96c091991a6194bf815206ac0842f451f92dfd6c1473fa66c4ca12faeb334310.png",
        "sha256": "96c091991a6194bf815206ac0842f451f92dfd6c1473fa66c4ca12faeb334310"
      },
      {
        "path": "/data2/k6tk/d1/d1eb197392c4e8eb7cf850fd31558ead8585066fd694377cf75b2f13819ce472.png",
        "sha256": "d1eb197392c4e8eb7cf850fd31558ead8585066fd694377cf75b2f13819ce472"
      },
      {
        "path": "/data2/k6tk/67/67d650092dbfc0533b38724bb1d9fcfec61d7acf318a4b8bcaf7bd672b1767e4.png",
        "sha256": "67d650092dbfc0533b38724bb1d9fcfec61d7acf318a4b8bcaf7bd672b1767e4"
      },
      {
        "path": "/data2/k6tk/4e/4eb1bf2557611eed86cfcc0f8b8e8049c9290aa0367fdb14c25e8d20021eb0b7.png",
        "sha256": "4eb1bf2557611eed86cfcc0f8b8e8049c9290aa0367fdb14c25e8d20021eb0b7"
      },
      {
        "path": "/data2/k6tk/5b/5bef0652d98214eccb6aceaab55baa720208def2b1a557d6ae611d4070dfb662.png",
        "sha256": "5bef0652d98214eccb6aceaab55baa720208def2b1a557d6ae611d4070dfb662"
      },
      {
        "path": "/data2/k6tk/d8/d8eea4e756dc6fe0e7e38ec670b7680a7f1d7e20a64f1cf1eb344c976d28135c.png",
        "sha256": "d8eea4e756dc6fe0e7e38ec670b7680a7f1d7e20a64f1cf1eb344c976d28135c"
      },
      {
        "path": "/data2/k6tk/53/536c503c6a75ba0534af1b497ebeafc2f5040cc8ab7af97eaa2ef09074e9eec4.png",
        "sha256": "536c503c6a75ba0534af1b497ebeafc2f5040cc8ab7af97eaa2ef09074e9eec4"
      },
      {
        "path": "/data2/k6tk/d5/d5990b9c99217f98cad6b590c21b9750979f77e1f8d8748ea37105d4cdd47aa2.png",
        "sha256": "d5990b9c99217f98cad6b590c21b9750979f77e1f8d8748ea37105d4cdd47aa2"
      },
      {
        "path": "/data2/k6tk/8b/8b7d0e8b94747aa9833d667701162c18e78d883d2c754b8568cdff6c40e96021.png",
        "sha256": "8b7d0e8b94747aa9833d667701162c18e78d883d2c754b8568cdff6c40e96021"
      },
      {
        "path": "/data2/k6tk/23/2320d820055893df674e4ee9305468f55c69d84a14a282fbc6292c7e6395b224.png",
        "sha256": "2320d820055893df674e4ee9305468f55c69d84a14a282fbc6292c7e6395b224"
      },
      {
        "path": "/data2/k6tk/10/102d27ed5ed974e0a715541c5cbdde2fd34257fd2fdecf13016ad481e6818357.png",
        "sha256": "102d27ed5ed974e0a715541c5cbdde2fd34257fd2fdecf13016ad481e6818357"
      },
      {
        "path": "/data2/k6tk/cc/ccc06a877ca17e03f7f5d506d1bd6f7f52ebc635b2d7ef189eb4374e5d6f9326.png",
        "sha256": "ccc06a877ca17e03f7f5d506d1bd6f7f52ebc635b2d7ef189eb4374e5d6f9326"
      },
      {
        "path": "/data2/k6tk/30/30428d91545c6dd00f1a58c1b6c1a3b324cb9f244c3b190b82ccd4938cfb81ea.png",
        "sha256": "30428d91545c6dd00f1a58c1b6c1a3b324cb9f244c3b190b82ccd4938cfb81ea"
      },
      {
        "path": "/data2/k6tk/91/91c3d7f4e97782485d4cd6ff5716e224e443d953705602ddbfad2fe75e9c6561.png",
        "sha256": "91c3d7f4e97782485d4cd6ff5716e224e443d953705602ddbfad2fe75e9c6561"
      },
      {
        "path": "/data2/k6tk/b3/b37eecb71001dc406c9fd7c0048c08ed0c79cd2f66aaa143d221f6eef0a3e37a.png",
        "sha256": "b37eecb71001dc406c9fd7c0048c08ed0c79cd2f66aaa143d221f6eef0a3e37a"
      },
      {
        "path": "/data2/k6tk/47/47ba35012ef159e7404e2e7047d75cc90375ec637e675b691b82a699f07acd72.png",
        "sha256": "47ba35012ef159e7404e2e7047d75cc90375ec637e675b691b82a699f07acd72"
      },
      {
        "path": "/data2/k6tk/29/294660c5c06faa3e6c4c8d2df7a4b8a067266a612b7e59b7b373466d3c13304c.png",
        "sha256": "294660c5c06faa3e6c4c8d2df7a4b8a067266a612b7e59b7b373466d3c13304c"
      },
      {
        "path": "/data2/k6tk/79/79f4fa2165330121cd9adb2b9c2354e3b113598026d5d7cebe8cb88e6385b6c2.png",
        "sha256": "79f4fa2165330121cd9adb2b9c2354e3b113598026d5d7cebe8cb88e6385b6c2"
      },
      {
        "path": "/data2/k6tk/ac/ac53a36fa27c46438036536668387b119a36578a1f574cbceb86bac5aea3dab2.png",
        "sha256": "ac53a36fa27c46438036536668387b119a36578a1f574cbceb86bac5aea3dab2"
      },
      {
        "path": "/data2/k6tk/ed/edbd1ac80d9a6f2aaf0d9a3af3c9890844a1ff9a163096f8b05b232f80582400.png",
        "sha256": "edbd1ac80d9a6f2aaf0d9a3af3c9890844a1ff9a163096f8b05b232f80582400"
      },
      {
        "path": "/data2/k6tk/cf/cf5449039c5adf80f37c28ae2ee53db1d6e7ad38e40f3e118a0f8ee7c32b6d7d.png",
        "sha256": "cf5449039c5adf80f37c28ae2ee53db1d6e7ad38e40f3e118a0f8ee7c32b6d7d"
      },
      {
        "path": "/data2/k6tk/19/19820ca27d019826214b4d8c667ab7e82e27dcc693a5422c18a61de8445f2259.png",
        "sha256": "19820ca27d019826214b4d8c667ab7e82e27dcc693a5422c18a61de8445f2259"
      },
      {
        "path": "/data2/k6tk/bc/bc4881e602200ebee7e8de4a895a6136a359dc91f44ee621b76b88d3a0ba7fd2.png",
        "sha256": "bc4881e602200ebee7e8de4a895a6136a359dc91f44ee621b76b88d3a0ba7fd2"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "The categories to compare are 'table' and 'sofa', in that order. Which answer describes the number of distinct objects in the first category relative to the second?",
    "timestamps": [
      0.0,
      1.0,
      2.0,
      2.9,
      3.9,
      4.9,
      5.9,
      6.8,
      7.8,
      8.8,
      9.8,
      10.8,
      11.7,
      12.7,
      13.7,
      14.7,
      15.6,
      16.6,
      17.6,
      18.6,
      19.5,
      20.5,
      21.5,
      22.5,
      23.5,
      24.4,
      25.4,
      26.4,
      27.4,
      28.3,
      29.3,
      30.3
    ],
    "total_num_frames": 304
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are fewer table instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 7. fbp_relcnt2_105ca83a0f7c2b3e75609a5b

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-a88f43a7fdd3aa894fdfc9ed2979a9f2f2e51ffd8f2847291b78b7e078a29d22",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/45261390",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/45261390.npz": "1004ddcfc8fef71cc7583a667b39139bf8f1e3f8722d659c5f5483a891d390f8",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "45261390.npz",
    "raster_sha256": "1004ddcfc8fef71cc7583a667b39139bf8f1e3f8722d659c5f5483a891d390f8",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "3",
      "count_a": 2,
      "count_b": 3,
      "ids_a": [
        1,
        5
      ],
      "ids_b": [
        2,
        3,
        4
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue466857",
      "scene_use_cap": 24,
      "source_qid": "b12ct_8451bba1d4c95051df52ca96",
      "source_row_sha256": "4d64cf676c51bf87d8197a64de1ef6fdc7664d4a0f7878de4f7822eaad25b386",
      "source_use_cap": 8,
      "template_id": 6,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_105ca83a0f7c2b3e75609a5b",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v9d766ea8e611",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      20,
      39,
      59,
      78,
      98,
      117,
      137,
      156,
      176,
      195,
      215,
      234,
      254,
      273,
      293,
      312,
      332,
      351,
      371,
      390,
      410,
      429,
      449,
      468,
      488,
      507,
      527,
      546,
      566,
      585,
      605
    ],
    "frames": [
      {
        "path": "/data2/k6tk/11/113f39641416afd05d799b18c176489fd519970e7e132df54d5b3f7b5f9c76dc.png",
        "sha256": "113f39641416afd05d799b18c176489fd519970e7e132df54d5b3f7b5f9c76dc"
      },
      {
        "path": "/data2/k6tk/42/4257e4b2a1b50852993fc9792ccaf4295b8aa106a9efb9045cbd9206c6e20296.png",
        "sha256": "4257e4b2a1b50852993fc9792ccaf4295b8aa106a9efb9045cbd9206c6e20296"
      },
      {
        "path": "/data2/k6tk/a9/a9cb6a90ab191fbc7f22bf4f8a95415fec6298eaf1ed1e47e590d2e3bb05ab86.png",
        "sha256": "a9cb6a90ab191fbc7f22bf4f8a95415fec6298eaf1ed1e47e590d2e3bb05ab86"
      },
      {
        "path": "/data2/k6tk/e2/e2ed3d82956d65a3befc50a66b5fa97ab24af0c7bacba01c64bb4febcb2d8542.png",
        "sha256": "e2ed3d82956d65a3befc50a66b5fa97ab24af0c7bacba01c64bb4febcb2d8542"
      },
      {
        "path": "/data2/k6tk/55/5590b035fbe782b68424e1e325929f2e8c3a1a53e100331634b7974b9aa97f81.png",
        "sha256": "5590b035fbe782b68424e1e325929f2e8c3a1a53e100331634b7974b9aa97f81"
      },
      {
        "path": "/data2/k6tk/36/366b6da4211718a236401b1dca88bb02781b3ec0c0e1211f23c5383a86b831e5.png",
        "sha256": "366b6da4211718a236401b1dca88bb02781b3ec0c0e1211f23c5383a86b831e5"
      },
      {
        "path": "/data2/k6tk/fc/fc37f328708361dc4c18e9e9b4375641973ca8df9dffa030f0512f09082536fb.png",
        "sha256": "fc37f328708361dc4c18e9e9b4375641973ca8df9dffa030f0512f09082536fb"
      },
      {
        "path": "/data2/k6tk/83/831938f9db7d3bfad1eb70d3c2e1cd7128a218e47e64bd8da03b6f6b1aa64db4.png",
        "sha256": "831938f9db7d3bfad1eb70d3c2e1cd7128a218e47e64bd8da03b6f6b1aa64db4"
      },
      {
        "path": "/data2/k6tk/3b/3bd4b8e5d522b9af46396322b404550bf638f0fa2242e71da32efa174ffc94b7.png",
        "sha256": "3bd4b8e5d522b9af46396322b404550bf638f0fa2242e71da32efa174ffc94b7"
      },
      {
        "path": "/data2/k6tk/e0/e0064bf62ca69706a3c3a75a35c01a7f451f8439e5f23e607ad1c4dfd8ce3e08.png",
        "sha256": "e0064bf62ca69706a3c3a75a35c01a7f451f8439e5f23e607ad1c4dfd8ce3e08"
      },
      {
        "path": "/data2/k6tk/ef/effca0df81f8f3a501c6dee24bbd1d29829aaf7ab87b6c7509228e7e09d3ff6a.png",
        "sha256": "effca0df81f8f3a501c6dee24bbd1d29829aaf7ab87b6c7509228e7e09d3ff6a"
      },
      {
        "path": "/data2/k6tk/dd/ddd37e50892796e85c6a1e3247a60b2325b1a5931f0b23fe0d23e09e846f21b3.png",
        "sha256": "ddd37e50892796e85c6a1e3247a60b2325b1a5931f0b23fe0d23e09e846f21b3"
      },
      {
        "path": "/data2/k6tk/bf/bfa0013fd6c50405ca70c5e8a16790db8db2d3747d4b0415e6fb8cf77edba0d6.png",
        "sha256": "bfa0013fd6c50405ca70c5e8a16790db8db2d3747d4b0415e6fb8cf77edba0d6"
      },
      {
        "path": "/data2/k6tk/5e/5ec4949f224b2757c2c639cf59e3ab64a055e50a902b695d5542ab9af45090a4.png",
        "sha256": "5ec4949f224b2757c2c639cf59e3ab64a055e50a902b695d5542ab9af45090a4"
      },
      {
        "path": "/data2/k6tk/ed/ed740b5747eca80a63fd85b100a50f607900e7ad50f90f94a99e10fe00fcf06a.png",
        "sha256": "ed740b5747eca80a63fd85b100a50f607900e7ad50f90f94a99e10fe00fcf06a"
      },
      {
        "path": "/data2/k6tk/c3/c344586856a2a8a67cb956d5594aea075a8b3f70262c02d3bc644ff1a290db11.png",
        "sha256": "c344586856a2a8a67cb956d5594aea075a8b3f70262c02d3bc644ff1a290db11"
      },
      {
        "path": "/data2/k6tk/01/018abe5efcaf003b83fdbe0dd8f663a96bc9f701c3651cec58500f620a429d7b.png",
        "sha256": "018abe5efcaf003b83fdbe0dd8f663a96bc9f701c3651cec58500f620a429d7b"
      },
      {
        "path": "/data2/k6tk/9d/9d98e9dd23d49a2f6be8bbeae772631e39f24f18c6629595d65ff8bde59fe76f.png",
        "sha256": "9d98e9dd23d49a2f6be8bbeae772631e39f24f18c6629595d65ff8bde59fe76f"
      },
      {
        "path": "/data2/k6tk/c6/c6fd139722d492ab5facd395a4e09509566d642c867ca60631ab07e132a50ffd.png",
        "sha256": "c6fd139722d492ab5facd395a4e09509566d642c867ca60631ab07e132a50ffd"
      },
      {
        "path": "/data2/k6tk/23/2357736058a5f2a4fe9ece9d301e24afdb6c416728552fdefae4cdc5f74227d2.png",
        "sha256": "2357736058a5f2a4fe9ece9d301e24afdb6c416728552fdefae4cdc5f74227d2"
      },
      {
        "path": "/data2/k6tk/43/4304ef179af83201baf53fb32a01fe68879d5a42a26435538851557b7cd31796.png",
        "sha256": "4304ef179af83201baf53fb32a01fe68879d5a42a26435538851557b7cd31796"
      },
      {
        "path": "/data2/k6tk/6b/6b47f900e5de5e69e52e6427f33f95e25e0e4fe4a2904e11c2a03867227db40a.png",
        "sha256": "6b47f900e5de5e69e52e6427f33f95e25e0e4fe4a2904e11c2a03867227db40a"
      },
      {
        "path": "/data2/k6tk/41/41dd1c8e02be7a5522f9a0f12105cccfee185f0f4045b4b22cc3d614f7eb3554.png",
        "sha256": "41dd1c8e02be7a5522f9a0f12105cccfee185f0f4045b4b22cc3d614f7eb3554"
      },
      {
        "path": "/data2/k6tk/09/0923c35ff46cdda31bd65d6baf0cb53d224df4777e5f5d3552fcd635197f766b.png",
        "sha256": "0923c35ff46cdda31bd65d6baf0cb53d224df4777e5f5d3552fcd635197f766b"
      },
      {
        "path": "/data2/k6tk/4c/4c6993e386c2c9a4468b16f399b3bdc096aea6ad21c8b0c3a44d3a8a8eb114ec.png",
        "sha256": "4c6993e386c2c9a4468b16f399b3bdc096aea6ad21c8b0c3a44d3a8a8eb114ec"
      },
      {
        "path": "/data2/k6tk/a3/a398cda3b18df54e54d497499db34e124dadf3ac04dcacd3b8196a9c02f20120.png",
        "sha256": "a398cda3b18df54e54d497499db34e124dadf3ac04dcacd3b8196a9c02f20120"
      },
      {
        "path": "/data2/k6tk/39/3962c0f135a977dbc23bd284be38f7778dda5e8a886b6547754c7f42465e5c0f.png",
        "sha256": "3962c0f135a977dbc23bd284be38f7778dda5e8a886b6547754c7f42465e5c0f"
      },
      {
        "path": "/data2/k6tk/d4/d4a5964fbf4218b5158c6751a87adcb7a35d91505b3aedad5ed5bdfb48aefa4f.png",
        "sha256": "d4a5964fbf4218b5158c6751a87adcb7a35d91505b3aedad5ed5bdfb48aefa4f"
      },
      {
        "path": "/data2/k6tk/5a/5a972914d79a998e394192aefc0b3383419f9c5f8d188973bdfcfcef2f5df1a9.png",
        "sha256": "5a972914d79a998e394192aefc0b3383419f9c5f8d188973bdfcfcef2f5df1a9"
      },
      {
        "path": "/data2/k6tk/4b/4bf5681f18191785686c6314a61d295e73fee134fbf6f20d967d712e87fa03d0.png",
        "sha256": "4bf5681f18191785686c6314a61d295e73fee134fbf6f20d967d712e87fa03d0"
      },
      {
        "path": "/data2/k6tk/3e/3ec62bd299cb37b924407e1d3b535ee35cf090653af90e007f97458fb2c0fa47.png",
        "sha256": "3ec62bd299cb37b924407e1d3b535ee35cf090653af90e007f97458fb2c0fa47"
      },
      {
        "path": "/data2/k6tk/c2/c2a459dcdbf0a5e5a8a0a06aa68266d8feb68a62b5d841b93847dcaa746de7c2.png",
        "sha256": "c2a459dcdbf0a5e5a8a0a06aa68266d8feb68a62b5d841b93847dcaa746de7c2"
      }
    ],
    "options": [
      "A. fewer",
      "B. equal number",
      "C. more"
    ],
    "question": "Keep track of distinct 'table' objects while viewing the room, and do the same for 'sofa'. Select the comparison that places the 'table' tally against the 'sofa' tally.",
    "timestamps": [
      0.0,
      2.0,
      3.9,
      5.9,
      7.8,
      9.8,
      11.7,
      13.7,
      15.6,
      17.6,
      19.5,
      21.5,
      23.4,
      25.4,
      27.3,
      29.3,
      31.2,
      33.2,
      35.1,
      37.1,
      39.0,
      41.0,
      42.9,
      44.9,
      46.8,
      48.8,
      50.7,
      52.7,
      54.6,
      56.6,
      58.5,
      60.5
    ],
    "total_num_frames": 606
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are fewer table instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 8. fbp_relcnt2_2f189e4693ebf2e11d257eaa

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-18b2702ef6df1d9a131781a7ec10d1552fd0f459540d429879f36cc52a66f24a",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42898247",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42898247.npz": "c7160ebb6e3641346ccbe47ebce832a9364c0587f485969da13eaab4df5b501c",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42898247.npz",
    "raster_sha256": "c7160ebb6e3641346ccbe47ebce832a9364c0587f485969da13eaab4df5b501c",
    "relative_count": {
      "a": "stool",
      "b": "table",
      "bucket": "6",
      "count_a": 1,
      "count_b": 6,
      "ids_a": [
        10
      ],
      "ids_b": [
        4,
        5,
        6,
        7,
        9,
        12
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue423974",
      "scene_use_cap": 24,
      "source_qid": "b12ct_612c187a969641a5fa5a1dfc",
      "source_row_sha256": "ec3cf6d3ece650d2f22a8e9b2918a9597077f1e5ed2f890c43c9f29d4b71c1da",
      "source_use_cap": 8,
      "template_id": 7,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_2f189e4693ebf2e11d257eaa",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vf5b3aaa4a4c1",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      13,
      26,
      39,
      52,
      65,
      78,
      91,
      104,
      117,
      130,
      143,
      156,
      169,
      182,
      195,
      208,
      221,
      234,
      247,
      260,
      273,
      286,
      299,
      312,
      325,
      338,
      351,
      364,
      377,
      390,
      403
    ],
    "frames": [
      {
        "path": "/data2/k6tk/21/21ecf615d559e718d0d7f02d269861057ccd0dc7e04b41293933c32d8cd0cf84.png",
        "sha256": "21ecf615d559e718d0d7f02d269861057ccd0dc7e04b41293933c32d8cd0cf84"
      },
      {
        "path": "/data2/k6tk/a0/a0387bbd5ae1266e27f7a08c0337ddb4fa61ebefe0711c12771ae2b307e90370.png",
        "sha256": "a0387bbd5ae1266e27f7a08c0337ddb4fa61ebefe0711c12771ae2b307e90370"
      },
      {
        "path": "/data2/k6tk/13/136b1d54fe3508d2adc2f74e855532fa39f80bc7564bb972d1926fd480188248.png",
        "sha256": "136b1d54fe3508d2adc2f74e855532fa39f80bc7564bb972d1926fd480188248"
      },
      {
        "path": "/data2/k6tk/f8/f8e1e3e6134bcc24eb4956729451aa0b9bc413ddfd7ab95f1561abf5ca89b5bf.png",
        "sha256": "f8e1e3e6134bcc24eb4956729451aa0b9bc413ddfd7ab95f1561abf5ca89b5bf"
      },
      {
        "path": "/data2/k6tk/37/37142fa05c8cf18f9ae58ee02d85f1ec92a4424f512df9db18d1d93fd0446baa.png",
        "sha256": "37142fa05c8cf18f9ae58ee02d85f1ec92a4424f512df9db18d1d93fd0446baa"
      },
      {
        "path": "/data2/k6tk/ba/ba9bdcafc99ff155d34014d34fc09ed6a0de72803d3380bc8f8d62fb3b9763c9.png",
        "sha256": "ba9bdcafc99ff155d34014d34fc09ed6a0de72803d3380bc8f8d62fb3b9763c9"
      },
      {
        "path": "/data2/k6tk/84/8442d1eaf7c6f681d336205dc1e07be2dcfdd607531bf50345352e9b3deb6a4e.png",
        "sha256": "8442d1eaf7c6f681d336205dc1e07be2dcfdd607531bf50345352e9b3deb6a4e"
      },
      {
        "path": "/data2/k6tk/5b/5b1962993b525c6501aed74911917a48f4f05b8c6cab5ece9ea70399a9a5cbb0.png",
        "sha256": "5b1962993b525c6501aed74911917a48f4f05b8c6cab5ece9ea70399a9a5cbb0"
      },
      {
        "path": "/data2/k6tk/4b/4b490376cdbf034d17c3118b4926b42b215f8c7e2b0016a37e6e1d87ef6150d9.png",
        "sha256": "4b490376cdbf034d17c3118b4926b42b215f8c7e2b0016a37e6e1d87ef6150d9"
      },
      {
        "path": "/data2/k6tk/73/73fb26cdad3521c0ec406c9bc67ccb197485e21a70f72805ea23a29b96e219e5.png",
        "sha256": "73fb26cdad3521c0ec406c9bc67ccb197485e21a70f72805ea23a29b96e219e5"
      },
      {
        "path": "/data2/k6tk/7b/7b64d13d2c7b03173ac5890569cbff32bcad3ee8a675bc427aab5837d87f4ffc.png",
        "sha256": "7b64d13d2c7b03173ac5890569cbff32bcad3ee8a675bc427aab5837d87f4ffc"
      },
      {
        "path": "/data2/k6tk/7e/7e82314046fafab597b46bb2525a0976e950c5838349e4ed43538b772a128d46.png",
        "sha256": "7e82314046fafab597b46bb2525a0976e950c5838349e4ed43538b772a128d46"
      },
      {
        "path": "/data2/k6tk/fd/fd08b001fd76e55ebd2b3713810bf067dd8b4fda30a9fdc23972ab44966d4ee9.png",
        "sha256": "fd08b001fd76e55ebd2b3713810bf067dd8b4fda30a9fdc23972ab44966d4ee9"
      },
      {
        "path": "/data2/k6tk/0d/0d09c8645a9dc72bf449a2127c475827c5da5cfec14b425e321da3befe23a7d8.png",
        "sha256": "0d09c8645a9dc72bf449a2127c475827c5da5cfec14b425e321da3befe23a7d8"
      },
      {
        "path": "/data2/k6tk/ef/ef427c98eebbc11a92cdde011adaee521f8f4b98877ec6d5060e4ebeaa7bb1dc.png",
        "sha256": "ef427c98eebbc11a92cdde011adaee521f8f4b98877ec6d5060e4ebeaa7bb1dc"
      },
      {
        "path": "/data2/k6tk/1c/1cfb3b5816fa16a2e153ad2032021d75662673d16484ea60a2a9eca715b90a55.png",
        "sha256": "1cfb3b5816fa16a2e153ad2032021d75662673d16484ea60a2a9eca715b90a55"
      },
      {
        "path": "/data2/k6tk/1c/1ca0a05cab94d60bfb92f22cf61a6c4477cd8f00f1c874690b3f022fbd05dfb8.png",
        "sha256": "1ca0a05cab94d60bfb92f22cf61a6c4477cd8f00f1c874690b3f022fbd05dfb8"
      },
      {
        "path": "/data2/k6tk/34/34d5cb8b19a4aee3883287eb3d297c532e97abd1b61e6887868b3852c7fde413.png",
        "sha256": "34d5cb8b19a4aee3883287eb3d297c532e97abd1b61e6887868b3852c7fde413"
      },
      {
        "path": "/data2/k6tk/e4/e42c68c46a86b88ccd1d998445f8976b18de2d5e5f10bb82f2aa7a332218fd4d.png",
        "sha256": "e42c68c46a86b88ccd1d998445f8976b18de2d5e5f10bb82f2aa7a332218fd4d"
      },
      {
        "path": "/data2/k6tk/45/45f48cbe6e559869c297a6438fb4f005fed74d7316608677e79efe41f23c5e74.png",
        "sha256": "45f48cbe6e559869c297a6438fb4f005fed74d7316608677e79efe41f23c5e74"
      },
      {
        "path": "/data2/k6tk/30/30184d25d4fcb8f657371fc1b7fcdd3a33d541fc45a8af686fad19fcf10f7097.png",
        "sha256": "30184d25d4fcb8f657371fc1b7fcdd3a33d541fc45a8af686fad19fcf10f7097"
      },
      {
        "path": "/data2/k6tk/50/5080cbdf6971acd90751011b383208cc63399aadf8fc1dbe315f90ae7e27a65d.png",
        "sha256": "5080cbdf6971acd90751011b383208cc63399aadf8fc1dbe315f90ae7e27a65d"
      },
      {
        "path": "/data2/k6tk/75/75badbf599b197f9ec66f699586b775d7e5e0b042ea1387a024452c22cf35ee6.png",
        "sha256": "75badbf599b197f9ec66f699586b775d7e5e0b042ea1387a024452c22cf35ee6"
      },
      {
        "path": "/data2/k6tk/cb/cb1500b15b2130ab1442507df975f87723cdf2403514ac201df40da09bd6cad5.png",
        "sha256": "cb1500b15b2130ab1442507df975f87723cdf2403514ac201df40da09bd6cad5"
      },
      {
        "path": "/data2/k6tk/09/09fc7a9fe2874c64ebd7d408d2cff64f3b4d32d866ba2af926d568845c01e94a.png",
        "sha256": "09fc7a9fe2874c64ebd7d408d2cff64f3b4d32d866ba2af926d568845c01e94a"
      },
      {
        "path": "/data2/k6tk/d1/d124d25724909e90700a7cf942a5ebc7f6191a4714f1f740b773deb0b1c945d8.png",
        "sha256": "d124d25724909e90700a7cf942a5ebc7f6191a4714f1f740b773deb0b1c945d8"
      },
      {
        "path": "/data2/k6tk/21/21608deace711cf7066be7ef071161f4b261f523f58a8e22f302e66ef766f408.png",
        "sha256": "21608deace711cf7066be7ef071161f4b261f523f58a8e22f302e66ef766f408"
      },
      {
        "path": "/data2/k6tk/25/2536c4962dc41d0a71d1194c683862f0d7558db8a2bea563660a62f53f2d9975.png",
        "sha256": "2536c4962dc41d0a71d1194c683862f0d7558db8a2bea563660a62f53f2d9975"
      },
      {
        "path": "/data2/k6tk/22/2205774f0becc61e7c4d0ac3a2c9a7b88317483ff57a534cc285376efc496c33.png",
        "sha256": "2205774f0becc61e7c4d0ac3a2c9a7b88317483ff57a534cc285376efc496c33"
      },
      {
        "path": "/data2/k6tk/0c/0cb7b9324df511d2e40fcc65f28443338cbb104520d4df0e430280dc6afcc130.png",
        "sha256": "0cb7b9324df511d2e40fcc65f28443338cbb104520d4df0e430280dc6afcc130"
      },
      {
        "path": "/data2/k6tk/79/79c4d3fded1229a2842ac69260054ff19531649afcab5ac9459d782fd1bf87a2.png",
        "sha256": "79c4d3fded1229a2842ac69260054ff19531649afcab5ac9459d782fd1bf87a2"
      },
      {
        "path": "/data2/k6tk/d0/d08b9a0cbc7e64838141c77a2134e50ec8de4326047ca36b708b808c86caba86.png",
        "sha256": "d08b9a0cbc7e64838141c77a2134e50ec8de4326047ca36b708b808c86caba86"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Make independent counts for 'stool' and 'table' using the video. Which option states how the total for 'stool' compares with the total for 'table'?",
    "timestamps": [
      0.0,
      1.3,
      2.6,
      3.9,
      5.2,
      6.5,
      7.8,
      9.1,
      10.4,
      11.7,
      13.0,
      14.3,
      15.6,
      16.9,
      18.2,
      19.5,
      20.8,
      22.1,
      23.4,
      24.7,
      26.0,
      27.3,
      28.6,
      29.9,
      31.2,
      32.5,
      33.8,
      35.1,
      36.4,
      37.7,
      39.0,
      40.3
    ],
    "total_num_frames": 404
  },
  "target": "<think>\nlocate the distinct instances of stool; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are fewer stool instances than table instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 9. fbp_relcnt2_57eb37a3c25d1168e5a43d55

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-3a4c7c4f3129b8c6f1ba0a03b92b3d890addca520a615880692ec144b6e208ae",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/44796391",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/44796391.npz": "02ea9c130fd2b59e6dcb9daea71c35a12af1929205439ccd0d890b8f073d0c1a",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "44796391.npz",
    "raster_sha256": "02ea9c130fd2b59e6dcb9daea71c35a12af1929205439ccd0d890b8f073d0c1a",
    "relative_count": {
      "a": "sofa",
      "b": "table",
      "bucket": "4",
      "count_a": 4,
      "count_b": 1,
      "ids_a": [
        1,
        3,
        8,
        9
      ],
      "ids_b": [
        0
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue464790",
      "scene_use_cap": 24,
      "source_qid": "b12ct_40e9a9cd002358e89ae10853",
      "source_row_sha256": "059d92a35420ff239855e3e65cb8e4e9bb59064ecd9e7ffa34a8825825b06ae4",
      "source_use_cap": 8,
      "template_id": 8,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_57eb37a3c25d1168e5a43d55",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v0d2e11f50318",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      22,
      44,
      67,
      89,
      111,
      133,
      156,
      178,
      200,
      222,
      244,
      267,
      289,
      311,
      333,
      356,
      378,
      400,
      422,
      445,
      467,
      489,
      511,
      533,
      556,
      578,
      600,
      622,
      645,
      667,
      689
    ],
    "frames": [
      {
        "path": "/data2/k6tk/2f/2f9f997cf0c5e6e7c1e997ba8e7da0e375bb0daccaa96b9efc2abbb367c2358d.png",
        "sha256": "2f9f997cf0c5e6e7c1e997ba8e7da0e375bb0daccaa96b9efc2abbb367c2358d"
      },
      {
        "path": "/data2/k6tk/07/0729d2667ec8a3ff90ddd1091a5400a0226243fd371c27ffc1ee386848e18c61.png",
        "sha256": "0729d2667ec8a3ff90ddd1091a5400a0226243fd371c27ffc1ee386848e18c61"
      },
      {
        "path": "/data2/k6tk/4d/4df11b0ec134497adfea6dbdae9067409ec62348706f074da7f7b749143536f3.png",
        "sha256": "4df11b0ec134497adfea6dbdae9067409ec62348706f074da7f7b749143536f3"
      },
      {
        "path": "/data2/k6tk/cc/cccb62afa3ed4d7e3a9c92b6e99a1f1d8e38517e1cb13156ef1f52e1e9b332c8.png",
        "sha256": "cccb62afa3ed4d7e3a9c92b6e99a1f1d8e38517e1cb13156ef1f52e1e9b332c8"
      },
      {
        "path": "/data2/k6tk/d5/d5ec69f1990482b8976529166a405e1c08ef4c2ce46f3d87e2f23205392a1b0d.png",
        "sha256": "d5ec69f1990482b8976529166a405e1c08ef4c2ce46f3d87e2f23205392a1b0d"
      },
      {
        "path": "/data2/k6tk/56/56eea61864ba4f49fd8e49d49f602ead6b7582fa446de9f43ce852442793b6e3.png",
        "sha256": "56eea61864ba4f49fd8e49d49f602ead6b7582fa446de9f43ce852442793b6e3"
      },
      {
        "path": "/data2/k6tk/c6/c63b55bf98b20461cdba7d44c52b1cd34634caf91aacf8618a36e95a9f666050.png",
        "sha256": "c63b55bf98b20461cdba7d44c52b1cd34634caf91aacf8618a36e95a9f666050"
      },
      {
        "path": "/data2/k6tk/c9/c942b84bf35b3d1d3544b57d777b613d1ef2b3d91a07c3f8f2d27c166ec57744.png",
        "sha256": "c942b84bf35b3d1d3544b57d777b613d1ef2b3d91a07c3f8f2d27c166ec57744"
      },
      {
        "path": "/data2/k6tk/ea/ea682ea514b6b5218bf52f64213a168d6c08191a6d1e344f779bac0395ebbfde.png",
        "sha256": "ea682ea514b6b5218bf52f64213a168d6c08191a6d1e344f779bac0395ebbfde"
      },
      {
        "path": "/data2/k6tk/53/536e69aa6f4dc3426d99581b725da6433c5a37fb4997f99b34960900c1c98e3b.png",
        "sha256": "536e69aa6f4dc3426d99581b725da6433c5a37fb4997f99b34960900c1c98e3b"
      },
      {
        "path": "/data2/k6tk/72/722899e36fa2834e4e4c4a0cb119f46e7fe604796f8e54be9d2933d447978c69.png",
        "sha256": "722899e36fa2834e4e4c4a0cb119f46e7fe604796f8e54be9d2933d447978c69"
      },
      {
        "path": "/data2/k6tk/ec/ecb52f648507883da240b783a77eb6cb9b401f0244c5ed93944cc0d993573c6d.png",
        "sha256": "ecb52f648507883da240b783a77eb6cb9b401f0244c5ed93944cc0d993573c6d"
      },
      {
        "path": "/data2/k6tk/81/813f43403fa8b6ede038fc058aeecc5eb060f9d07210795c99ce32ad8cc1d259.png",
        "sha256": "813f43403fa8b6ede038fc058aeecc5eb060f9d07210795c99ce32ad8cc1d259"
      },
      {
        "path": "/data2/k6tk/fa/fa55e8c5f869475efbf6f5e8f0a5ecbd5a1d32ed8b7b6c0a3d803659e9a3a6b6.png",
        "sha256": "fa55e8c5f869475efbf6f5e8f0a5ecbd5a1d32ed8b7b6c0a3d803659e9a3a6b6"
      },
      {
        "path": "/data2/k6tk/6f/6f432af640592bcbee57d0af675077cd2e0d19f63dd6d539c0d4be278dd32de2.png",
        "sha256": "6f432af640592bcbee57d0af675077cd2e0d19f63dd6d539c0d4be278dd32de2"
      },
      {
        "path": "/data2/k6tk/3b/3b7f84e793d1216e504696151eedec2ab4a024df470df8351db703a502af3aee.png",
        "sha256": "3b7f84e793d1216e504696151eedec2ab4a024df470df8351db703a502af3aee"
      },
      {
        "path": "/data2/k6tk/1c/1c5d48ba6b3241e37b974ed93abbcc9ef962aed1cff9b8054266033df53dd7d3.png",
        "sha256": "1c5d48ba6b3241e37b974ed93abbcc9ef962aed1cff9b8054266033df53dd7d3"
      },
      {
        "path": "/data2/k6tk/5e/5eedaac782df58af1ab72e1f4efac92c223a3c5a86f2b6e2d2f10663881748ef.png",
        "sha256": "5eedaac782df58af1ab72e1f4efac92c223a3c5a86f2b6e2d2f10663881748ef"
      },
      {
        "path": "/data2/k6tk/44/44e958956133dde91d5a623f5d89ac65e1ed7a7b4531d134bdc4a94247915780.png",
        "sha256": "44e958956133dde91d5a623f5d89ac65e1ed7a7b4531d134bdc4a94247915780"
      },
      {
        "path": "/data2/k6tk/d7/d7f1da0ba31aa6e002717061a1d91e1f6d7f90abc2862449f0bc4141cccf42c6.png",
        "sha256": "d7f1da0ba31aa6e002717061a1d91e1f6d7f90abc2862449f0bc4141cccf42c6"
      },
      {
        "path": "/data2/k6tk/ff/ff20c19419516ac5ef7c6b4d138cf764d041d680fe99548a78077d4dfce9205e.png",
        "sha256": "ff20c19419516ac5ef7c6b4d138cf764d041d680fe99548a78077d4dfce9205e"
      },
      {
        "path": "/data2/k6tk/7e/7e610ddaafd6832706406bbe2ae4da084a7f18cc2417a264cb49c1fd5286d020.png",
        "sha256": "7e610ddaafd6832706406bbe2ae4da084a7f18cc2417a264cb49c1fd5286d020"
      },
      {
        "path": "/data2/k6tk/c4/c4a332f8a4d863c758abaa4bf7e5469ad128efaffe1b6e97bf75058c3d491594.png",
        "sha256": "c4a332f8a4d863c758abaa4bf7e5469ad128efaffe1b6e97bf75058c3d491594"
      },
      {
        "path": "/data2/k6tk/f8/f868a0845414fcd4985419e81f3937fd916e0614e0298ffc93010c2cb7fe0453.png",
        "sha256": "f868a0845414fcd4985419e81f3937fd916e0614e0298ffc93010c2cb7fe0453"
      },
      {
        "path": "/data2/k6tk/1b/1ba8aa4af18d0ce902cb2a03465094971d9c003fe438f8107d19ea66fbb58004.png",
        "sha256": "1ba8aa4af18d0ce902cb2a03465094971d9c003fe438f8107d19ea66fbb58004"
      },
      {
        "path": "/data2/k6tk/00/00355999c34018a702d355e8e082452a82cd5a493ed348531b65b5e3a9bcb2dd.png",
        "sha256": "00355999c34018a702d355e8e082452a82cd5a493ed348531b65b5e3a9bcb2dd"
      },
      {
        "path": "/data2/k6tk/d2/d2478931529683c37caf4bcd577199459c7621edc83e1e7c15b4e77e92812275.png",
        "sha256": "d2478931529683c37caf4bcd577199459c7621edc83e1e7c15b4e77e92812275"
      },
      {
        "path": "/data2/k6tk/00/00a65c990e52af9d8b1c3816e1cb395b2c0d1134b3efeb535092b88de3c95670.png",
        "sha256": "00a65c990e52af9d8b1c3816e1cb395b2c0d1134b3efeb535092b88de3c95670"
      },
      {
        "path": "/data2/k6tk/70/705e29cca75e7496569e2b4a0fe0494c858f7dd92d8d209a2fb3259c8949eb5d.png",
        "sha256": "705e29cca75e7496569e2b4a0fe0494c858f7dd92d8d209a2fb3259c8949eb5d"
      },
      {
        "path": "/data2/k6tk/c3/c38fd717ee2d79d81b4aef8b0329ec784be6f02e9454806fbffdf0e0131023b3.png",
        "sha256": "c38fd717ee2d79d81b4aef8b0329ec784be6f02e9454806fbffdf0e0131023b3"
      },
      {
        "path": "/data2/k6tk/fe/fee063ce29d5c9914fdbbf02759a15f4de9c45849ddf9a9ef69ba4ed56d30568.png",
        "sha256": "fee063ce29d5c9914fdbbf02759a15f4de9c45849ddf9a9ef69ba4ed56d30568"
      },
      {
        "path": "/data2/k6tk/92/923774a81ca1836731e61bed50ceac2544e5bc3c12fc4b40fc3766814aa98905.png",
        "sha256": "923774a81ca1836731e61bed50ceac2544e5bc3c12fc4b40fc3766814aa98905"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "For a count comparison, take 'sofa' as the first category and 'table' as the second. What relation between their numbers of instances does the room show?",
    "timestamps": [
      0.0,
      2.2,
      4.4,
      6.7,
      8.9,
      11.1,
      13.3,
      15.6,
      17.8,
      20.0,
      22.2,
      24.4,
      26.7,
      28.9,
      31.1,
      33.3,
      35.6,
      37.8,
      40.0,
      42.2,
      44.5,
      46.7,
      48.9,
      51.1,
      53.3,
      55.6,
      57.8,
      60.0,
      62.2,
      64.5,
      66.7,
      68.9
    ],
    "total_num_frames": 690
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are more sofa instances than table instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 10. fbp_relcnt2_5ff54c9cb314be3c801760bf

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-717bfad83e6e453e058e7485dc69cc609cbea7a660a1b7aedf70c810f29c1cbb",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/40958767",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/40958767.npz": "3bb4e01b5e39e35783d8a29cd103d015c1e48bb320daa7cf1354aa18f4fbfff5",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "40958767.npz",
    "raster_sha256": "3bb4e01b5e39e35783d8a29cd103d015c1e48bb320daa7cf1354aa18f4fbfff5",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "4",
      "count_a": 4,
      "count_b": 1,
      "ids_a": [
        3,
        4,
        5,
        6
      ],
      "ids_b": [
        0
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue379876",
      "scene_use_cap": 24,
      "source_qid": "b12ct_548fe66ac752412ceec262c8",
      "source_row_sha256": "694b847098ed41d6e35f2fc7baf4b20a82c7d2d96e50148bc0aa73d028bc982d",
      "source_use_cap": 8,
      "template_id": 9,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_5ff54c9cb314be3c801760bf",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v380a757276e9",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      42,
      84,
      126,
      167,
      209,
      251,
      293,
      335,
      377,
      419,
      461,
      502,
      544,
      586,
      628,
      670,
      712,
      754,
      796,
      837,
      879,
      921,
      963,
      1005,
      1047,
      1089,
      1131,
      1172,
      1214,
      1256,
      1298
    ],
    "frames": [
      {
        "path": "/data2/k6tk/80/807e7bf9da96bc4b44c7eaa78a9391dbaf381acfce34ca28e0a8827d7d158bee.png",
        "sha256": "807e7bf9da96bc4b44c7eaa78a9391dbaf381acfce34ca28e0a8827d7d158bee"
      },
      {
        "path": "/data2/k6tk/5b/5b29e88764858c367c22edbd159daecf520ffdcb061778ec3aa0e1be033f59c8.png",
        "sha256": "5b29e88764858c367c22edbd159daecf520ffdcb061778ec3aa0e1be033f59c8"
      },
      {
        "path": "/data2/k6tk/e2/e26064edc2dc034511327041fc109dbe6848143ec6436ae49fd196ccd802de66.png",
        "sha256": "e26064edc2dc034511327041fc109dbe6848143ec6436ae49fd196ccd802de66"
      },
      {
        "path": "/data2/k6tk/8a/8a7deb249a5545d13690d66523df864edae1b5d8635523128b44600841f478f7.png",
        "sha256": "8a7deb249a5545d13690d66523df864edae1b5d8635523128b44600841f478f7"
      },
      {
        "path": "/data2/k6tk/7e/7e52bb15acef2bc5bd65e02967e65b645e851321a9d0e6822f1477c9a38c0c4e.png",
        "sha256": "7e52bb15acef2bc5bd65e02967e65b645e851321a9d0e6822f1477c9a38c0c4e"
      },
      {
        "path": "/data2/k6tk/ee/ee1d7d5d698903014263b2e0fb7284ec6b407e3ddd81c56ce1d6c47a827c58b7.png",
        "sha256": "ee1d7d5d698903014263b2e0fb7284ec6b407e3ddd81c56ce1d6c47a827c58b7"
      },
      {
        "path": "/data2/k6tk/da/da197e21207bafe3546dc001e4a2c1a8b401ea96d72b985b8c47ba88b793f2a5.png",
        "sha256": "da197e21207bafe3546dc001e4a2c1a8b401ea96d72b985b8c47ba88b793f2a5"
      },
      {
        "path": "/data2/k6tk/c1/c15b797f42e2b03e6ca0a6ea1bb0d122599a6b3444a6629e25ce7bdcdea86323.png",
        "sha256": "c15b797f42e2b03e6ca0a6ea1bb0d122599a6b3444a6629e25ce7bdcdea86323"
      },
      {
        "path": "/data2/k6tk/a5/a5306fe6c3f7e4a9d215a8593c527d056965a130411445507100617ac5dd7059.png",
        "sha256": "a5306fe6c3f7e4a9d215a8593c527d056965a130411445507100617ac5dd7059"
      },
      {
        "path": "/data2/k6tk/e1/e119afc3c6c6ac89b271b056a3a2d716fa2cea2ba26b78977c5db5e870c50d17.png",
        "sha256": "e119afc3c6c6ac89b271b056a3a2d716fa2cea2ba26b78977c5db5e870c50d17"
      },
      {
        "path": "/data2/k6tk/8a/8a2a45a229d8d9cd981bde8faaf945c5ed0f8cfd70c7f1e0748c66ef6bbbec56.png",
        "sha256": "8a2a45a229d8d9cd981bde8faaf945c5ed0f8cfd70c7f1e0748c66ef6bbbec56"
      },
      {
        "path": "/data2/k6tk/c9/c901a8f0f5172daa0ee8b89f7a94e30d011aef84b4cfc0b7a91cc14f284dbe0e.png",
        "sha256": "c901a8f0f5172daa0ee8b89f7a94e30d011aef84b4cfc0b7a91cc14f284dbe0e"
      },
      {
        "path": "/data2/k6tk/6b/6b877da405b10fd403fbea4f97ca968cdda0b4b66e0db71bb86592ee730a96d0.png",
        "sha256": "6b877da405b10fd403fbea4f97ca968cdda0b4b66e0db71bb86592ee730a96d0"
      },
      {
        "path": "/data2/k6tk/29/294e8743d27c125619209926029cdba624edd67e99b40c3d4068382695d40fb1.png",
        "sha256": "294e8743d27c125619209926029cdba624edd67e99b40c3d4068382695d40fb1"
      },
      {
        "path": "/data2/k6tk/0e/0e7930bdde6102299d87a405653b5fafd0750d9656ea119bf09957eb7af8aa94.png",
        "sha256": "0e7930bdde6102299d87a405653b5fafd0750d9656ea119bf09957eb7af8aa94"
      },
      {
        "path": "/data2/k6tk/cb/cb61928fe75a7f12668b67c5fcc6937b2bbaa74997d405f045576e70b0cddf68.png",
        "sha256": "cb61928fe75a7f12668b67c5fcc6937b2bbaa74997d405f045576e70b0cddf68"
      },
      {
        "path": "/data2/k6tk/50/50e85f3d3c8e718f2b53e995d6982d09c710f79dcecde5f7021c17b00854ec77.png",
        "sha256": "50e85f3d3c8e718f2b53e995d6982d09c710f79dcecde5f7021c17b00854ec77"
      },
      {
        "path": "/data2/k6tk/e4/e47e031147643a0bb34c482e11693e098a55f635a255c466763f050bad7084f8.png",
        "sha256": "e47e031147643a0bb34c482e11693e098a55f635a255c466763f050bad7084f8"
      },
      {
        "path": "/data2/k6tk/59/594558429c46f869bbce1a9b2a7d5e540b254ba97ca3be1f560711df9c7a2362.png",
        "sha256": "594558429c46f869bbce1a9b2a7d5e540b254ba97ca3be1f560711df9c7a2362"
      },
      {
        "path": "/data2/k6tk/28/288ea8cc1366b573843cd7e40e7324f9d0deb42a9377db5e5d3a326440883c4e.png",
        "sha256": "288ea8cc1366b573843cd7e40e7324f9d0deb42a9377db5e5d3a326440883c4e"
      },
      {
        "path": "/data2/k6tk/40/40c5411362b82bd3240dc7487ad6b4a8e201392a648bef0a0c76ca1b9c2f3eeb.png",
        "sha256": "40c5411362b82bd3240dc7487ad6b4a8e201392a648bef0a0c76ca1b9c2f3eeb"
      },
      {
        "path": "/data2/k6tk/fe/fea5d8d7f88a4db33969ba3671f1bb06ce4fc2323ba56a5da3b42c49e429d124.png",
        "sha256": "fea5d8d7f88a4db33969ba3671f1bb06ce4fc2323ba56a5da3b42c49e429d124"
      },
      {
        "path": "/data2/k6tk/05/05a351b7a15674035fd931897f6b6250fdc03fd358d61923cba8d2bf4fd51b41.png",
        "sha256": "05a351b7a15674035fd931897f6b6250fdc03fd358d61923cba8d2bf4fd51b41"
      },
      {
        "path": "/data2/k6tk/bb/bb80c5c5b4dd5afff6c0c68b073aef9806f21de575ddfff6aecf77fc6f3cccb7.png",
        "sha256": "bb80c5c5b4dd5afff6c0c68b073aef9806f21de575ddfff6aecf77fc6f3cccb7"
      },
      {
        "path": "/data2/k6tk/75/7549bbfc476bf657e77de311beafea46800dd8ee6d5686d8932dc53d69d6666f.png",
        "sha256": "7549bbfc476bf657e77de311beafea46800dd8ee6d5686d8932dc53d69d6666f"
      },
      {
        "path": "/data2/k6tk/30/306918565fa5ffec2e15dfbd5779f1a65d95cad2f14664778fb3d8d63b1190e7.png",
        "sha256": "306918565fa5ffec2e15dfbd5779f1a65d95cad2f14664778fb3d8d63b1190e7"
      },
      {
        "path": "/data2/k6tk/72/72c0fb838675b93558e8dc279f9961415fb4c67d3cf0761e4e70636eeb4203a6.png",
        "sha256": "72c0fb838675b93558e8dc279f9961415fb4c67d3cf0761e4e70636eeb4203a6"
      },
      {
        "path": "/data2/k6tk/3d/3d8a6f207f8b41959d61bec19835d869d4b74cea52899aa973b9cefb22bb3d1a.png",
        "sha256": "3d8a6f207f8b41959d61bec19835d869d4b74cea52899aa973b9cefb22bb3d1a"
      },
      {
        "path": "/data2/k6tk/be/be3fb7cbf8b96b48ec24ca34c08c8e97cba89158dc38272f95c656ffe187563d.png",
        "sha256": "be3fb7cbf8b96b48ec24ca34c08c8e97cba89158dc38272f95c656ffe187563d"
      },
      {
        "path": "/data2/k6tk/73/7336a045fd8aac4750b5dff5309a3bc77d6496ec92a213bef63c40dbacfbbc8f.png",
        "sha256": "7336a045fd8aac4750b5dff5309a3bc77d6496ec92a213bef63c40dbacfbbc8f"
      },
      {
        "path": "/data2/k6tk/3c/3cf278f8a51c7c7ee09003eb67ecb90d94eb0b950092f85ef8662202de1c4094.png",
        "sha256": "3cf278f8a51c7c7ee09003eb67ecb90d94eb0b950092f85ef8662202de1c4094"
      },
      {
        "path": "/data2/k6tk/23/23d730a91dca58b677b492de946b61396401bc0e727f4fc057d4cca71666ae88.png",
        "sha256": "23d730a91dca58b677b492de946b61396401bc0e727f4fc057d4cca71666ae88"
      }
    ],
    "options": [
      "A. fewer",
      "B. equal number",
      "C. more"
    ],
    "question": "Look through the room views and count each distinct object in 'table' and in 'sofa'. Compared with the second category, how many instances does the first category have: more, fewer, or an equal number?",
    "timestamps": [
      0.0,
      4.2,
      8.4,
      12.6,
      16.7,
      20.9,
      25.1,
      29.3,
      33.5,
      37.7,
      41.9,
      46.1,
      50.2,
      54.4,
      58.6,
      62.8,
      67.0,
      71.2,
      75.4,
      79.6,
      83.7,
      87.9,
      92.1,
      96.3,
      100.5,
      104.7,
      108.9,
      113.1,
      117.2,
      121.4,
      125.6,
      129.8
    ],
    "total_num_frames": 1299
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are more table instances than sofa instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 11. fbp_relcnt2_c448223fbe2df5ab7523f63a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-810ff7ca90bda09b7e13b1c23cb664ec4fee53ed16722878f7c67d4b08b0d926",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47332139",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47332139.npz": "f3575e430e0c718f650e7ad2d74eb8d204f78533e46810382b6881906fd256ce",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47332139.npz",
    "raster_sha256": "f3575e430e0c718f650e7ad2d74eb8d204f78533e46810382b6881906fd256ce",
    "relative_count": {
      "a": "sofa",
      "b": "chair",
      "bucket": "2",
      "count_a": 1,
      "count_b": 2,
      "ids_a": [
        0
      ],
      "ids_b": [
        7,
        8
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue471187",
      "scene_use_cap": 24,
      "source_qid": "b12ct_a0a68ab342717e341ed0db94",
      "source_row_sha256": "9a357a94720ef1ea7c2bb300a13344464b150e2d1c56c1d3ad9f48e946934660",
      "source_use_cap": 8,
      "template_id": 10,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_c448223fbe2df5ab7523f63a",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vc1d06b7f0af5",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      19,
      38,
      57,
      76,
      95,
      115,
      134,
      153,
      172,
      191,
      210,
      229,
      248,
      267,
      286,
      306,
      325,
      344,
      363,
      382,
      401,
      420,
      439,
      458,
      477,
      497,
      516,
      535,
      554,
      573,
      592
    ],
    "frames": [
      {
        "path": "/data2/k6tk/8b/8b27842ce9b77adb39194c6048758d6b122124e31ac8e1e3c45e91a499dd8184.png",
        "sha256": "8b27842ce9b77adb39194c6048758d6b122124e31ac8e1e3c45e91a499dd8184"
      },
      {
        "path": "/data2/k6tk/62/6241a1d015d7a60066d6ad2413e16f467a93721a85a1953e5a29cbae65762e4d.png",
        "sha256": "6241a1d015d7a60066d6ad2413e16f467a93721a85a1953e5a29cbae65762e4d"
      },
      {
        "path": "/data2/k6tk/86/8632b32c2af3e17edd1c5a92a4fbead5f1bee8c6c2d41f3219f834137c57116e.png",
        "sha256": "8632b32c2af3e17edd1c5a92a4fbead5f1bee8c6c2d41f3219f834137c57116e"
      },
      {
        "path": "/data2/k6tk/f3/f3e531213efb6ddc4ba59ed1a1f79196c199dbc3daf368f8a61f0400a1d71e39.png",
        "sha256": "f3e531213efb6ddc4ba59ed1a1f79196c199dbc3daf368f8a61f0400a1d71e39"
      },
      {
        "path": "/data2/k6tk/1d/1d2f00611d98e27bac1f42f616a0be04c22308507df5a6dbc88326bd4fb59e3b.png",
        "sha256": "1d2f00611d98e27bac1f42f616a0be04c22308507df5a6dbc88326bd4fb59e3b"
      },
      {
        "path": "/data2/k6tk/e4/e49c360952c235c81f4e63ed676dce9e393b3c096d13223b4cb53fcfd0ae4ed2.png",
        "sha256": "e49c360952c235c81f4e63ed676dce9e393b3c096d13223b4cb53fcfd0ae4ed2"
      },
      {
        "path": "/data2/k6tk/d4/d48eea03121dc7abe727742fb96f76dcee30ebd17b6f587f51a8447c4d0c5717.png",
        "sha256": "d48eea03121dc7abe727742fb96f76dcee30ebd17b6f587f51a8447c4d0c5717"
      },
      {
        "path": "/data2/k6tk/43/43bc239e3d783367909cd56503dc86c5f06ee775a70ab147ad9f1c848d228265.png",
        "sha256": "43bc239e3d783367909cd56503dc86c5f06ee775a70ab147ad9f1c848d228265"
      },
      {
        "path": "/data2/k6tk/f7/f755bdc70c6872491ccb392eee1454f94763b5954fa62f6009aa51296fe242e6.png",
        "sha256": "f755bdc70c6872491ccb392eee1454f94763b5954fa62f6009aa51296fe242e6"
      },
      {
        "path": "/data2/k6tk/bd/bd83ec2b85b801cf03658ab019e65e44e5181efe14efeee89b43788b1b322338.png",
        "sha256": "bd83ec2b85b801cf03658ab019e65e44e5181efe14efeee89b43788b1b322338"
      },
      {
        "path": "/data2/k6tk/9c/9ca90cc2ebc312e59a8319c6b665850f6efe9c2454924f99bad1c8f02fec7621.png",
        "sha256": "9ca90cc2ebc312e59a8319c6b665850f6efe9c2454924f99bad1c8f02fec7621"
      },
      {
        "path": "/data2/k6tk/20/20a7de49a8a843a14f3fb7a5b63cb6cf4208c314d27e9d3f971966479d48beda.png",
        "sha256": "20a7de49a8a843a14f3fb7a5b63cb6cf4208c314d27e9d3f971966479d48beda"
      },
      {
        "path": "/data2/k6tk/25/25554d08efcf4ba49dafa2001985a086edf44d9f6d2fe7e534cffe3d7795b50a.png",
        "sha256": "25554d08efcf4ba49dafa2001985a086edf44d9f6d2fe7e534cffe3d7795b50a"
      },
      {
        "path": "/data2/k6tk/5d/5dc7aad2b6ef98d08b3cb983847f5994b89572317c4e3e738764193ac4e6b5f8.png",
        "sha256": "5dc7aad2b6ef98d08b3cb983847f5994b89572317c4e3e738764193ac4e6b5f8"
      },
      {
        "path": "/data2/k6tk/00/00e3dfe52dbd79b2f240c6bf817f5588ea48595afc9c6acc98cc223e7a04fc57.png",
        "sha256": "00e3dfe52dbd79b2f240c6bf817f5588ea48595afc9c6acc98cc223e7a04fc57"
      },
      {
        "path": "/data2/k6tk/95/95b8b248e4fe1ccbcdf4755ea7dd7453da648e78332812523a09fb82b0a508a0.png",
        "sha256": "95b8b248e4fe1ccbcdf4755ea7dd7453da648e78332812523a09fb82b0a508a0"
      },
      {
        "path": "/data2/k6tk/e9/e99d9caca3523dba4490d9c830f0fb22fb1c4e368bef9fb0b77aa1bd3db3d6ea.png",
        "sha256": "e99d9caca3523dba4490d9c830f0fb22fb1c4e368bef9fb0b77aa1bd3db3d6ea"
      },
      {
        "path": "/data2/k6tk/c5/c59d61ec02792ae7151f988a4bf9a78d1451ccec4bc461bbd9c6573d1ea1178b.png",
        "sha256": "c59d61ec02792ae7151f988a4bf9a78d1451ccec4bc461bbd9c6573d1ea1178b"
      },
      {
        "path": "/data2/k6tk/1f/1f813b0f7182ffc8d458c5f4efd33c4ea7a0e46e5600fcdd5ce1309e3ad7352a.png",
        "sha256": "1f813b0f7182ffc8d458c5f4efd33c4ea7a0e46e5600fcdd5ce1309e3ad7352a"
      },
      {
        "path": "/data2/k6tk/64/64748f83678651832742a1c1ae7ee71a60edfb4c4d591601c3716770f44be7b2.png",
        "sha256": "64748f83678651832742a1c1ae7ee71a60edfb4c4d591601c3716770f44be7b2"
      },
      {
        "path": "/data2/k6tk/77/777ccfe78bed6b9d37b8d6db43a8a319f20984b586510a63f9df5df23d4c3390.png",
        "sha256": "777ccfe78bed6b9d37b8d6db43a8a319f20984b586510a63f9df5df23d4c3390"
      },
      {
        "path": "/data2/k6tk/60/6068c5347da7303ccd44fefa5fd65c56ad76685608463d1bfafd1458617d6c1a.png",
        "sha256": "6068c5347da7303ccd44fefa5fd65c56ad76685608463d1bfafd1458617d6c1a"
      },
      {
        "path": "/data2/k6tk/34/349d808ea50cd70fd5dd23857c3b98a535c5fb21f43262cb2dd5ad37cc147cab.png",
        "sha256": "349d808ea50cd70fd5dd23857c3b98a535c5fb21f43262cb2dd5ad37cc147cab"
      },
      {
        "path": "/data2/k6tk/92/9262400292b6e2216b9f47032d048dda959af5a20f06220180e7b6f1237ff67a.png",
        "sha256": "9262400292b6e2216b9f47032d048dda959af5a20f06220180e7b6f1237ff67a"
      },
      {
        "path": "/data2/k6tk/be/be31c41a9f16faceaeedb1b0647bfb02c49be2c1fa87fa350078f16cbf3707f9.png",
        "sha256": "be31c41a9f16faceaeedb1b0647bfb02c49be2c1fa87fa350078f16cbf3707f9"
      },
      {
        "path": "/data2/k6tk/d7/d7f47eb411e73a91da6e569d9102e50180955e0ef1f3e2411c6e71001124b7b9.png",
        "sha256": "d7f47eb411e73a91da6e569d9102e50180955e0ef1f3e2411c6e71001124b7b9"
      },
      {
        "path": "/data2/k6tk/42/42b0a49f0c28d63a0103ba5e7022a953c73c63c343fd024cb98eaa70cc670aef.png",
        "sha256": "42b0a49f0c28d63a0103ba5e7022a953c73c63c343fd024cb98eaa70cc670aef"
      },
      {
        "path": "/data2/k6tk/27/27543a2f9d3e95c0aeb019d0617fb7bff2083be439e3ffc23d96e3c7699cc597.png",
        "sha256": "27543a2f9d3e95c0aeb019d0617fb7bff2083be439e3ffc23d96e3c7699cc597"
      },
      {
        "path": "/data2/k6tk/3a/3a25fd1ddafe209ed78f08d980a331e3da8c5acedd8672fa5a451e8c85a0f3d8.png",
        "sha256": "3a25fd1ddafe209ed78f08d980a331e3da8c5acedd8672fa5a451e8c85a0f3d8"
      },
      {
        "path": "/data2/k6tk/f1/f15041b36f522cc3e72775321e0af2b7a9fd1ee76b9fc1c28bc944f262d4c95b.png",
        "sha256": "f15041b36f522cc3e72775321e0af2b7a9fd1ee76b9fc1c28bc944f262d4c95b"
      },
      {
        "path": "/data2/k6tk/f1/f12e3c7da0ec5655a0709b92224940bae11d3b2fefc9840d7eb2a7209e6f2d29.png",
        "sha256": "f12e3c7da0ec5655a0709b92224940bae11d3b2fefc9840d7eb2a7209e6f2d29"
      },
      {
        "path": "/data2/k6tk/05/05ec64d435ad19bf16aa48a6b83ff5bf51d7e29d171b5fc3230bab58e924cad5.png",
        "sha256": "05ec64d435ad19bf16aa48a6b83ff5bf51d7e29d171b5fc3230bab58e924cad5"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "Assess the numbers of objects belonging to 'sofa' and 'chair' without counting repeat views twice. Which choice gives the comparison for 'sofa' against 'chair'?",
    "timestamps": [
      0.0,
      1.9,
      3.8,
      5.7,
      7.6,
      9.5,
      11.5,
      13.4,
      15.3,
      17.2,
      19.1,
      21.0,
      22.9,
      24.8,
      26.7,
      28.6,
      30.6,
      32.5,
      34.4,
      36.3,
      38.2,
      40.1,
      42.0,
      43.9,
      45.8,
      47.7,
      49.7,
      51.6,
      53.5,
      55.4,
      57.3,
      59.2
    ],
    "total_num_frames": 593
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are fewer sofa instances than chair instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 12. fbp_relcnt2_500aa23ec8c8d31ed5764afa

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-56ff1be51087572d92f00d79a2f620bd724259e5307c44b872965b683f228f4b",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42897982",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42897982.npz": "516da49d71e55eeae43bde0bd4fdf34833a8fcd60cf07d987d6dd41ba6091fd7",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42897982.npz",
    "raster_sha256": "516da49d71e55eeae43bde0bd4fdf34833a8fcd60cf07d987d6dd41ba6091fd7",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "2",
      "count_a": 2,
      "count_b": 1,
      "ids_a": [
        0,
        2
      ],
      "ids_b": [
        1
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue423319",
      "scene_use_cap": 24,
      "source_qid": "b12ct_77ae00290c2aced232fb191b",
      "source_row_sha256": "f929dd432960c75f931537e8dbda678ed125b1065ca39e1bf5625eda15afaf65",
      "source_use_cap": 8,
      "template_id": 11,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_500aa23ec8c8d31ed5764afa",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v7303056739a1",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      18,
      36,
      54,
      72,
      90,
      108,
      126,
      144,
      162,
      180,
      198,
      216,
      234,
      252,
      270,
      287,
      305,
      323,
      341,
      359,
      377,
      395,
      413,
      431,
      449,
      467,
      485,
      503,
      521,
      539,
      557
    ],
    "frames": [
      {
        "path": "/data2/k6tk/df/df42445d916f3e17e1ddd37bf92a5e2f1cdbb232282bdd50c0352419430d794f.png",
        "sha256": "df42445d916f3e17e1ddd37bf92a5e2f1cdbb232282bdd50c0352419430d794f"
      },
      {
        "path": "/data2/k6tk/53/53e384df7d61abe720fa0d2eb0801668b725e9c208316bbf789c196b9bd27619.png",
        "sha256": "53e384df7d61abe720fa0d2eb0801668b725e9c208316bbf789c196b9bd27619"
      },
      {
        "path": "/data2/k6tk/65/656bb85fe37ef5b95f5341a4efd0dcd156323fdb211b2293631eddf4e3fdec51.png",
        "sha256": "656bb85fe37ef5b95f5341a4efd0dcd156323fdb211b2293631eddf4e3fdec51"
      },
      {
        "path": "/data2/k6tk/75/753f79f521d567ddb8d872df24e2a057bcc51bce0d474f98013d224fbc78a470.png",
        "sha256": "753f79f521d567ddb8d872df24e2a057bcc51bce0d474f98013d224fbc78a470"
      },
      {
        "path": "/data2/k6tk/00/0005417ce63dd112dd0eae9b17928eb5e5226fb4e48432bd5f3a65d4f2f8e076.png",
        "sha256": "0005417ce63dd112dd0eae9b17928eb5e5226fb4e48432bd5f3a65d4f2f8e076"
      },
      {
        "path": "/data2/k6tk/97/976846dbe1a78e1ae1b8dfc1252098c2fa40d5f045dee7098bbd407c20b69c4d.png",
        "sha256": "976846dbe1a78e1ae1b8dfc1252098c2fa40d5f045dee7098bbd407c20b69c4d"
      },
      {
        "path": "/data2/k6tk/d6/d641b87f5b4f2aba5048edfa8485f88af1c9b81a496ab05eb885c98cb8e63e65.png",
        "sha256": "d641b87f5b4f2aba5048edfa8485f88af1c9b81a496ab05eb885c98cb8e63e65"
      },
      {
        "path": "/data2/k6tk/1f/1fd19602194c0addfe2651a28883d580e2f6c933415aacc9ebadc6197848ffc7.png",
        "sha256": "1fd19602194c0addfe2651a28883d580e2f6c933415aacc9ebadc6197848ffc7"
      },
      {
        "path": "/data2/k6tk/79/795e37d30e002786e72c0c98e8e5c6a6b4947cfb87694407af2b15c92b75b395.png",
        "sha256": "795e37d30e002786e72c0c98e8e5c6a6b4947cfb87694407af2b15c92b75b395"
      },
      {
        "path": "/data2/k6tk/7a/7aa1a0234b4b19211f247f026d1e16329f73cf21250ea32a1ea02f79ad0b0ab1.png",
        "sha256": "7aa1a0234b4b19211f247f026d1e16329f73cf21250ea32a1ea02f79ad0b0ab1"
      },
      {
        "path": "/data2/k6tk/11/11bb8cafe14a33aa3adcd6f5ad0e5fdbaefdf4fd926046ef778580819ff87a0c.png",
        "sha256": "11bb8cafe14a33aa3adcd6f5ad0e5fdbaefdf4fd926046ef778580819ff87a0c"
      },
      {
        "path": "/data2/k6tk/b4/b404e2368a03f744cd2d10218259971d7ea1006347a66ddd3cc9b447df7ed1f1.png",
        "sha256": "b404e2368a03f744cd2d10218259971d7ea1006347a66ddd3cc9b447df7ed1f1"
      },
      {
        "path": "/data2/k6tk/9f/9fad8088289fc383553d59a850dbbf790e6343fbc851f40d23661b823a4765d9.png",
        "sha256": "9fad8088289fc383553d59a850dbbf790e6343fbc851f40d23661b823a4765d9"
      },
      {
        "path": "/data2/k6tk/af/af4942952dd842d78ec881a4ce5585b7f88093ed16238a35baf8205174b060c0.png",
        "sha256": "af4942952dd842d78ec881a4ce5585b7f88093ed16238a35baf8205174b060c0"
      },
      {
        "path": "/data2/k6tk/42/4295195735ac3b62ef1dee58039dcdf17418cd1b9e7376d28bafcaa1b84dd339.png",
        "sha256": "4295195735ac3b62ef1dee58039dcdf17418cd1b9e7376d28bafcaa1b84dd339"
      },
      {
        "path": "/data2/k6tk/4f/4fa490c9e21311848e553d20196106d34c7c8029ebfec410911d98eb1d34196e.png",
        "sha256": "4fa490c9e21311848e553d20196106d34c7c8029ebfec410911d98eb1d34196e"
      },
      {
        "path": "/data2/k6tk/2d/2d881ce57805fe255494e52225443eb8f00e61996c598faf0fa2ef5ad6f0ac6c.png",
        "sha256": "2d881ce57805fe255494e52225443eb8f00e61996c598faf0fa2ef5ad6f0ac6c"
      },
      {
        "path": "/data2/k6tk/1f/1f3059e5605a2d21a403aaa601bbfcf92ed11a4d902a73d9a7022f8b99351943.png",
        "sha256": "1f3059e5605a2d21a403aaa601bbfcf92ed11a4d902a73d9a7022f8b99351943"
      },
      {
        "path": "/data2/k6tk/12/1250340794f5f93b8418e2402745106d3df38b4760a5e88c52470e3686398c56.png",
        "sha256": "1250340794f5f93b8418e2402745106d3df38b4760a5e88c52470e3686398c56"
      },
      {
        "path": "/data2/k6tk/c7/c744eb20b0d81124ebff262bf56c79d32332ed7edffaffd6c6ead6e1f3964f63.png",
        "sha256": "c744eb20b0d81124ebff262bf56c79d32332ed7edffaffd6c6ead6e1f3964f63"
      },
      {
        "path": "/data2/k6tk/06/0601d0a0de9a8f1d9fd1aaccdf7b576011c30b7b5c5e2d60d2d760832e6f69df.png",
        "sha256": "0601d0a0de9a8f1d9fd1aaccdf7b576011c30b7b5c5e2d60d2d760832e6f69df"
      },
      {
        "path": "/data2/k6tk/70/709b86e3f9a1d4bd9342f16e633f0b3c9c443c4dac378a1d11e9236501ea3e93.png",
        "sha256": "709b86e3f9a1d4bd9342f16e633f0b3c9c443c4dac378a1d11e9236501ea3e93"
      },
      {
        "path": "/data2/k6tk/13/13dc76ed249c379e8e1de90d09a5065f06476de26ca7fd6bf64c578b9da3c058.png",
        "sha256": "13dc76ed249c379e8e1de90d09a5065f06476de26ca7fd6bf64c578b9da3c058"
      },
      {
        "path": "/data2/k6tk/db/db709d336c1d14a5f7cda7f4bf60ec3f626fd27537beaa0cebd6701bc2fda833.png",
        "sha256": "db709d336c1d14a5f7cda7f4bf60ec3f626fd27537beaa0cebd6701bc2fda833"
      },
      {
        "path": "/data2/k6tk/36/3677e9fe8d7abec6a4e701d6a6aacbc3a7034fb9059ebd75089b67e573a2d99f.png",
        "sha256": "3677e9fe8d7abec6a4e701d6a6aacbc3a7034fb9059ebd75089b67e573a2d99f"
      },
      {
        "path": "/data2/k6tk/c9/c910c29f9322d2c893ae3c302ab9bbf5ebcedbc506ac158eb468a798d59a2d91.png",
        "sha256": "c910c29f9322d2c893ae3c302ab9bbf5ebcedbc506ac158eb468a798d59a2d91"
      },
      {
        "path": "/data2/k6tk/c2/c2a9d89893a4096b30098745887621f1eaf5d03b2c6bef80fca0fc9dfb32b20d.png",
        "sha256": "c2a9d89893a4096b30098745887621f1eaf5d03b2c6bef80fca0fc9dfb32b20d"
      },
      {
        "path": "/data2/k6tk/98/98c7d6f61feb73ad248c6dad1502335ce1a978d5660c38393d758e55452adf87.png",
        "sha256": "98c7d6f61feb73ad248c6dad1502335ce1a978d5660c38393d758e55452adf87"
      },
      {
        "path": "/data2/k6tk/ca/caffbdb7383341b18d4c36bb05218087e3f14f4b8910e23ee15338042e1f1547.png",
        "sha256": "caffbdb7383341b18d4c36bb05218087e3f14f4b8910e23ee15338042e1f1547"
      },
      {
        "path": "/data2/k6tk/a7/a793d3d6bf8c8b02600347d877b6b13713b020107f6e5426f0849e8c8abba41c.png",
        "sha256": "a793d3d6bf8c8b02600347d877b6b13713b020107f6e5426f0849e8c8abba41c"
      },
      {
        "path": "/data2/k6tk/8f/8fde3625b73b2c8bd4270a23d79eaf86376f55e7f6ee7fa01085ef2800948559.png",
        "sha256": "8fde3625b73b2c8bd4270a23d79eaf86376f55e7f6ee7fa01085ef2800948559"
      },
      {
        "path": "/data2/k6tk/be/be022888ce065af820d3f9b3be44b73aa543337dd1d9f3bb538903599e71d2fd.png",
        "sha256": "be022888ce065af820d3f9b3be44b73aa543337dd1d9f3bb538903599e71d2fd"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "Start with a count of the room's distinct 'table' objects, then count its distinct 'chair' objects. Select the option that relates the first count to the second.",
    "timestamps": [
      0.0,
      1.8,
      3.6,
      5.4,
      7.2,
      9.0,
      10.8,
      12.6,
      14.4,
      16.2,
      18.0,
      19.8,
      21.6,
      23.4,
      25.2,
      27.0,
      28.7,
      30.5,
      32.3,
      34.1,
      35.9,
      37.7,
      39.5,
      41.3,
      43.1,
      44.9,
      46.7,
      48.5,
      50.3,
      52.1,
      53.9,
      55.7
    ],
    "total_num_frames": 558
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are more table instances than chair instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 13. fbp_relcnt2_753552f041594ac9b7fd8a0e

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-06c81c37b9340e41ed05e1bf2b703b0c0d99200be78a6eef43dee5c7a5b06f0c",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42899248",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42899248.npz": "dbbd489fa499e01a0cfbbc395f02805f71e2d18b32e97a18392b6d333e74a4d9",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42899248.npz",
    "raster_sha256": "dbbd489fa499e01a0cfbbc395f02805f71e2d18b32e97a18392b6d333e74a4d9",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "5",
      "count_a": 5,
      "count_b": 3,
      "ids_a": [
        0,
        1,
        4,
        7,
        9
      ],
      "ids_b": [
        3,
        5,
        8
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue434903",
      "scene_use_cap": 24,
      "source_qid": "b12ct_7b86cb37e3c71767efb9c880",
      "source_row_sha256": "d77ca9cd56e7d8e0a9447df3943016efbb6398a22ae4ae8246ca41fe786f8dfe",
      "source_use_cap": 8,
      "template_id": 12,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_753552f041594ac9b7fd8a0e",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vb3937b2569b8",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      57,
      115,
      172,
      229,
      287,
      344,
      401,
      459,
      516,
      573,
      631,
      688,
      745,
      803,
      860,
      917,
      974,
      1032,
      1089,
      1146,
      1204,
      1261,
      1318,
      1376,
      1433,
      1490,
      1548,
      1605,
      1662,
      1720,
      1777
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e2/e2d215a96bd155bd5e1bd552a9305d250bcfed05681eb55b743da188a931f437.png",
        "sha256": "e2d215a96bd155bd5e1bd552a9305d250bcfed05681eb55b743da188a931f437"
      },
      {
        "path": "/data2/k6tk/b7/b772191eab73bb9dd767d838d9ef89ed18855bfa8d4609ff01e6637c9e952425.png",
        "sha256": "b772191eab73bb9dd767d838d9ef89ed18855bfa8d4609ff01e6637c9e952425"
      },
      {
        "path": "/data2/k6tk/f6/f660f821a83ad2961797490427bd718fd4861b24c25829e6efeeeb6985d4b0d0.png",
        "sha256": "f660f821a83ad2961797490427bd718fd4861b24c25829e6efeeeb6985d4b0d0"
      },
      {
        "path": "/data2/k6tk/f7/f71d47d37a2bb34e8a083f605647c711efaec4e1a7f0d44edc4a2fd581227134.png",
        "sha256": "f71d47d37a2bb34e8a083f605647c711efaec4e1a7f0d44edc4a2fd581227134"
      },
      {
        "path": "/data2/k6tk/40/40bde787ee181714486e3567840e83361e1f209e5ac038137dc7363c36c08fd9.png",
        "sha256": "40bde787ee181714486e3567840e83361e1f209e5ac038137dc7363c36c08fd9"
      },
      {
        "path": "/data2/k6tk/42/429b3bb6ba4f6e47508ae3efd04abd6b7c683d9f9db9922363675bd6fa44befa.png",
        "sha256": "429b3bb6ba4f6e47508ae3efd04abd6b7c683d9f9db9922363675bd6fa44befa"
      },
      {
        "path": "/data2/k6tk/25/254b088f6949bb26c935afa45a8128f6ab1efdf0af0e6de3109c73633ee238ba.png",
        "sha256": "254b088f6949bb26c935afa45a8128f6ab1efdf0af0e6de3109c73633ee238ba"
      },
      {
        "path": "/data2/k6tk/fe/febeb8dd0971df26ee376b3a97b09bfb2059d9696b1a05c15437aadaa453249b.png",
        "sha256": "febeb8dd0971df26ee376b3a97b09bfb2059d9696b1a05c15437aadaa453249b"
      },
      {
        "path": "/data2/k6tk/03/03d3d547b55a7c6d12fb58c33b2607b26e77d764db54fed80324359b8488c39e.png",
        "sha256": "03d3d547b55a7c6d12fb58c33b2607b26e77d764db54fed80324359b8488c39e"
      },
      {
        "path": "/data2/k6tk/1a/1a39e3cb460e3a226c3e8553e82b2953f4e68443e11dcdf93a8cd9f8f67218ad.png",
        "sha256": "1a39e3cb460e3a226c3e8553e82b2953f4e68443e11dcdf93a8cd9f8f67218ad"
      },
      {
        "path": "/data2/k6tk/73/73329a7e1092aa90805830770013862afebfadaf61217e078ce0258bb7041c65.png",
        "sha256": "73329a7e1092aa90805830770013862afebfadaf61217e078ce0258bb7041c65"
      },
      {
        "path": "/data2/k6tk/57/57f8ed549ea065f3574e83ab38c16080caac081bdceec9d0fa2135093fbb7753.png",
        "sha256": "57f8ed549ea065f3574e83ab38c16080caac081bdceec9d0fa2135093fbb7753"
      },
      {
        "path": "/data2/k6tk/97/971b3c35bff0990d034f77cb279c05758f16ef1fb85197c1d05ac309b5d1d807.png",
        "sha256": "971b3c35bff0990d034f77cb279c05758f16ef1fb85197c1d05ac309b5d1d807"
      },
      {
        "path": "/data2/k6tk/34/34b84b707770d20aa18e3c2b7f62c6cd46cfb010e39132c6d2752b30a0f4782f.png",
        "sha256": "34b84b707770d20aa18e3c2b7f62c6cd46cfb010e39132c6d2752b30a0f4782f"
      },
      {
        "path": "/data2/k6tk/e0/e08304a6f5dfeea7fd30007dadecf56a20ccc3313520a77e0f255d1b708b3022.png",
        "sha256": "e08304a6f5dfeea7fd30007dadecf56a20ccc3313520a77e0f255d1b708b3022"
      },
      {
        "path": "/data2/k6tk/5a/5ae355301b98693dfffd797889d4979315477c88f2cb1d6c421cf7027611540c.png",
        "sha256": "5ae355301b98693dfffd797889d4979315477c88f2cb1d6c421cf7027611540c"
      },
      {
        "path": "/data2/k6tk/81/81e181177d1802d05dfc3cd6f3f687431d16692066033d33137a3d5de91176a9.png",
        "sha256": "81e181177d1802d05dfc3cd6f3f687431d16692066033d33137a3d5de91176a9"
      },
      {
        "path": "/data2/k6tk/13/13b0b467609ce2039b06de7163adcf5de7314bf9c2c1c783d5f68832473c7e5c.png",
        "sha256": "13b0b467609ce2039b06de7163adcf5de7314bf9c2c1c783d5f68832473c7e5c"
      },
      {
        "path": "/data2/k6tk/30/301e428edcc381e13f3000b25051e9f3d41c9491df069f59316618420f6e6cd0.png",
        "sha256": "301e428edcc381e13f3000b25051e9f3d41c9491df069f59316618420f6e6cd0"
      },
      {
        "path": "/data2/k6tk/5f/5f7c15412b1d0bc3685b70d04ed37e1988e92b6680ed52b051d3f6d75469d4a2.png",
        "sha256": "5f7c15412b1d0bc3685b70d04ed37e1988e92b6680ed52b051d3f6d75469d4a2"
      },
      {
        "path": "/data2/k6tk/74/740d775a3e6336a4d006f3e6fd5ca1a3caf05ea226e5f00479b699d33f48759d.png",
        "sha256": "740d775a3e6336a4d006f3e6fd5ca1a3caf05ea226e5f00479b699d33f48759d"
      },
      {
        "path": "/data2/k6tk/7d/7d9242be2c6ad43328af15d6a406e8e699b237add6b030f34a3b357db68ed2b6.png",
        "sha256": "7d9242be2c6ad43328af15d6a406e8e699b237add6b030f34a3b357db68ed2b6"
      },
      {
        "path": "/data2/k6tk/4e/4e64ff4847b6f201b292604010b9c768d4712e76979b95e8c87931f4689b358b.png",
        "sha256": "4e64ff4847b6f201b292604010b9c768d4712e76979b95e8c87931f4689b358b"
      },
      {
        "path": "/data2/k6tk/42/42a9ba4f3b961b8181da16a7d6d9ce07bab1dcaaaa8d543065c62c4bf8ff23b7.png",
        "sha256": "42a9ba4f3b961b8181da16a7d6d9ce07bab1dcaaaa8d543065c62c4bf8ff23b7"
      },
      {
        "path": "/data2/k6tk/7f/7f1ffbb3690824d2b422e433bd01b715386840a9ad339bdb6fe21ad8bced5ad8.png",
        "sha256": "7f1ffbb3690824d2b422e433bd01b715386840a9ad339bdb6fe21ad8bced5ad8"
      },
      {
        "path": "/data2/k6tk/f3/f30b6fe4d62d3d634d9b7177d7b77b9bb97c77948a2aa2d3c061d742c7ccbdf3.png",
        "sha256": "f30b6fe4d62d3d634d9b7177d7b77b9bb97c77948a2aa2d3c061d742c7ccbdf3"
      },
      {
        "path": "/data2/k6tk/d7/d7a9d1017208c0ac5482484148c3ed776a3ee89bd0d72298778bf340f90aacc8.png",
        "sha256": "d7a9d1017208c0ac5482484148c3ed776a3ee89bd0d72298778bf340f90aacc8"
      },
      {
        "path": "/data2/k6tk/48/48c2a9efbd3c6e87986444e96ec6447d76dfe2a5202714573915c46ef0b9aeb8.png",
        "sha256": "48c2a9efbd3c6e87986444e96ec6447d76dfe2a5202714573915c46ef0b9aeb8"
      },
      {
        "path": "/data2/k6tk/3e/3e8d532e3d244a28f2f7748d238547969fa4c36c92a9f30502022ecfc32ca705.png",
        "sha256": "3e8d532e3d244a28f2f7748d238547969fa4c36c92a9f30502022ecfc32ca705"
      },
      {
        "path": "/data2/k6tk/fe/fe76a1a71001aabb80065b98eb0b512dc360da251f91692660b90084018b5993.png",
        "sha256": "fe76a1a71001aabb80065b98eb0b512dc360da251f91692660b90084018b5993"
      },
      {
        "path": "/data2/k6tk/b7/b7b7a550c4a1b67efaee4879b793eaf1373c08fa584440606b603d2a2e2a56e4.png",
        "sha256": "b7b7a550c4a1b67efaee4879b793eaf1373c08fa584440606b603d2a2e2a56e4"
      },
      {
        "path": "/data2/k6tk/38/380fa6b7953f86e9f1c26f0dd36a282b1b283917840aee1d7e6a54efd89c6257.png",
        "sha256": "380fa6b7953f86e9f1c26f0dd36a282b1b283917840aee1d7e6a54efd89c6257"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "Treat 'table' and 'sofa' as separate categories when counting objects in the scene. Which answer fits the number in 'table' relative to the number in 'sofa'?",
    "timestamps": [
      0.0,
      5.7,
      11.5,
      17.2,
      22.9,
      28.7,
      34.4,
      40.1,
      45.9,
      51.6,
      57.3,
      63.1,
      68.8,
      74.5,
      80.3,
      86.0,
      91.7,
      97.4,
      103.2,
      108.9,
      114.6,
      120.4,
      126.1,
      131.8,
      137.6,
      143.3,
      149.0,
      154.8,
      160.5,
      166.2,
      172.0,
      177.7
    ],
    "total_num_frames": 1778
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are more table instances than sofa instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 14. fbp_relcnt2_74a9f6a386041a4397bcba73

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-5e45ad106ced66c842d0cf9d85d7342a5c76a00c7fee90e99de93a558be975d4",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42897818",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42897818.npz": "9bd9a0ceecbb954535d8e530e0802fbc608aef81c793867996784614100dd2f3",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42897818.npz",
    "raster_sha256": "9bd9a0ceecbb954535d8e530e0802fbc608aef81c793867996784614100dd2f3",
    "relative_count": {
      "a": "bed",
      "b": "tv",
      "bucket": "2",
      "count_a": 2,
      "count_b": 1,
      "ids_a": [
        2,
        4
      ],
      "ids_b": [
        8
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue423738",
      "scene_use_cap": 24,
      "source_qid": "b12ct_b122014addd19325b32cb6b8",
      "source_row_sha256": "1054f72a1a2eb865b964c0caef11a634d0527cc5d69d79c2e80ce5d6c59b4587",
      "source_use_cap": 8,
      "template_id": 13,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_74a9f6a386041a4397bcba73",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v3ccec3162998",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      22,
      44,
      66,
      88,
      110,
      132,
      154,
      176,
      198,
      220,
      242,
      264,
      286,
      308,
      330,
      351,
      373,
      395,
      417,
      439,
      461,
      483,
      505,
      527,
      549,
      571,
      593,
      615,
      637,
      659,
      681
    ],
    "frames": [
      {
        "path": "/data2/k6tk/4c/4c88db56666367695448b7a36a78813cb0360dbf4bddce3a3c6c1d2e42380667.png",
        "sha256": "4c88db56666367695448b7a36a78813cb0360dbf4bddce3a3c6c1d2e42380667"
      },
      {
        "path": "/data2/k6tk/78/78ad03d5a0c017a1fb2b68128a9309d4c663dce4f97046fb0d85b579331fbb0f.png",
        "sha256": "78ad03d5a0c017a1fb2b68128a9309d4c663dce4f97046fb0d85b579331fbb0f"
      },
      {
        "path": "/data2/k6tk/32/3290a6023506f20c1ffd719481c63a96927d4575d1cb217a634afaf730a34316.png",
        "sha256": "3290a6023506f20c1ffd719481c63a96927d4575d1cb217a634afaf730a34316"
      },
      {
        "path": "/data2/k6tk/7d/7d70cc177c98b1d38744fc1d502057de57631ee215a015a257b1a50b14b1c11e.png",
        "sha256": "7d70cc177c98b1d38744fc1d502057de57631ee215a015a257b1a50b14b1c11e"
      },
      {
        "path": "/data2/k6tk/40/40554585d4744308f2993cedab15537432a2046f6afaef5c71497f203e96c3d4.png",
        "sha256": "40554585d4744308f2993cedab15537432a2046f6afaef5c71497f203e96c3d4"
      },
      {
        "path": "/data2/k6tk/84/848ea5d460dd59450615fd823712691bcf85eb2cfcf183d34452966351912fc9.png",
        "sha256": "848ea5d460dd59450615fd823712691bcf85eb2cfcf183d34452966351912fc9"
      },
      {
        "path": "/data2/k6tk/43/4307d0c6cca14c6511bd77bda517013e2e007fbf377eb0bd88bbda70815673dd.png",
        "sha256": "4307d0c6cca14c6511bd77bda517013e2e007fbf377eb0bd88bbda70815673dd"
      },
      {
        "path": "/data2/k6tk/27/27ec54207ae0e753641aec18af72665a53086541361d3dcb8573ed2868cdcf89.png",
        "sha256": "27ec54207ae0e753641aec18af72665a53086541361d3dcb8573ed2868cdcf89"
      },
      {
        "path": "/data2/k6tk/27/27f887eb607d9d378b3230a4b1f6fc3e242f3e38c84436275ec1ef0cee098c56.png",
        "sha256": "27f887eb607d9d378b3230a4b1f6fc3e242f3e38c84436275ec1ef0cee098c56"
      },
      {
        "path": "/data2/k6tk/ce/ce4f24f109bf14c288b35f46739c186ea9e8842240b99cff66b4aa8683c084c1.png",
        "sha256": "ce4f24f109bf14c288b35f46739c186ea9e8842240b99cff66b4aa8683c084c1"
      },
      {
        "path": "/data2/k6tk/fc/fc2add770f7bf46882efa4b84a4e358881eefccea71d3fa557aa0f68c9018707.png",
        "sha256": "fc2add770f7bf46882efa4b84a4e358881eefccea71d3fa557aa0f68c9018707"
      },
      {
        "path": "/data2/k6tk/f5/f5c46e74816bef7e993c192e5aff7376fa32e7dea986bd9b167c4c502912d29c.png",
        "sha256": "f5c46e74816bef7e993c192e5aff7376fa32e7dea986bd9b167c4c502912d29c"
      },
      {
        "path": "/data2/k6tk/7b/7b72382ac798a5b0842608539f59f44dc21c28024ad0b75d498b84e07079d9b3.png",
        "sha256": "7b72382ac798a5b0842608539f59f44dc21c28024ad0b75d498b84e07079d9b3"
      },
      {
        "path": "/data2/k6tk/98/9869299360da32efc849aabf38150d85cad330b01d54d731e19fde83161d9d99.png",
        "sha256": "9869299360da32efc849aabf38150d85cad330b01d54d731e19fde83161d9d99"
      },
      {
        "path": "/data2/k6tk/73/738fb98162c82c1829f58ff55d156663690d696694a02a47c1d0e46cdb02d068.png",
        "sha256": "738fb98162c82c1829f58ff55d156663690d696694a02a47c1d0e46cdb02d068"
      },
      {
        "path": "/data2/k6tk/ee/ee8634790c4ba0badd93237be79ef0cf9a30e65f4b4b42501a9435341d59ea18.png",
        "sha256": "ee8634790c4ba0badd93237be79ef0cf9a30e65f4b4b42501a9435341d59ea18"
      },
      {
        "path": "/data2/k6tk/4a/4abe881f252e2ea8ac81044edc49f5fc7e2783a7005ecdd59302d96aacc36597.png",
        "sha256": "4abe881f252e2ea8ac81044edc49f5fc7e2783a7005ecdd59302d96aacc36597"
      },
      {
        "path": "/data2/k6tk/26/26d7b0922fa04c8affff9ed700f08925247a50c4a9aadfe97656ae2803bae823.png",
        "sha256": "26d7b0922fa04c8affff9ed700f08925247a50c4a9aadfe97656ae2803bae823"
      },
      {
        "path": "/data2/k6tk/d5/d5c546d7c82e1b83e0281045214fdf025bab78c4188da1a9aef4cd90007445fc.png",
        "sha256": "d5c546d7c82e1b83e0281045214fdf025bab78c4188da1a9aef4cd90007445fc"
      },
      {
        "path": "/data2/k6tk/68/683b12630f01abcccc7039876e8beab77bd7463712a813123b459ee2f991508a.png",
        "sha256": "683b12630f01abcccc7039876e8beab77bd7463712a813123b459ee2f991508a"
      },
      {
        "path": "/data2/k6tk/d2/d23f11a2f216aa706fd04ec6e58a03827a895627e64042e432d3e1fdf1e34993.png",
        "sha256": "d23f11a2f216aa706fd04ec6e58a03827a895627e64042e432d3e1fdf1e34993"
      },
      {
        "path": "/data2/k6tk/8b/8bd31c5faa51630476d769161648e14a1ff8638efc6d140da8a1ccba1cfcc6b5.png",
        "sha256": "8bd31c5faa51630476d769161648e14a1ff8638efc6d140da8a1ccba1cfcc6b5"
      },
      {
        "path": "/data2/k6tk/e6/e686bb78f473964eab730873d1d86bc32909b1b1aafceaa94aa1246f70d260a5.png",
        "sha256": "e686bb78f473964eab730873d1d86bc32909b1b1aafceaa94aa1246f70d260a5"
      },
      {
        "path": "/data2/k6tk/94/94504221503e1954e826fde1caf220d07d2c3fee4d9e2aa1edbf464972b13ad3.png",
        "sha256": "94504221503e1954e826fde1caf220d07d2c3fee4d9e2aa1edbf464972b13ad3"
      },
      {
        "path": "/data2/k6tk/12/125f1c1433def18d93f0695750c29f2747ecc33883c0b416589d554d12cb33e3.png",
        "sha256": "125f1c1433def18d93f0695750c29f2747ecc33883c0b416589d554d12cb33e3"
      },
      {
        "path": "/data2/k6tk/50/5045a38b9a2dc7649dfa477ae26e4ac02a583339e5dd3b3cb46c16a70f980f34.png",
        "sha256": "5045a38b9a2dc7649dfa477ae26e4ac02a583339e5dd3b3cb46c16a70f980f34"
      },
      {
        "path": "/data2/k6tk/bb/bbec5c98d5bdc051676a6a521fc2864b9d3280e0de42bc32c059b2cccb8bfb06.png",
        "sha256": "bbec5c98d5bdc051676a6a521fc2864b9d3280e0de42bc32c059b2cccb8bfb06"
      },
      {
        "path": "/data2/k6tk/06/06c7e7c0d3b35cb216db4302a006f96fb4196002e6f760d8687cb1cf75c1ccb9.png",
        "sha256": "06c7e7c0d3b35cb216db4302a006f96fb4196002e6f760d8687cb1cf75c1ccb9"
      },
      {
        "path": "/data2/k6tk/5f/5fa6d5218527489010b1087630ab77cce44ee1bdb6a0e0d5ea4d3f79a67794e8.png",
        "sha256": "5fa6d5218527489010b1087630ab77cce44ee1bdb6a0e0d5ea4d3f79a67794e8"
      },
      {
        "path": "/data2/k6tk/ad/adc5200debc5714e1da398071658a0d343609dd7af44e2670a878624cd711d39.png",
        "sha256": "adc5200debc5714e1da398071658a0d343609dd7af44e2670a878624cd711d39"
      },
      {
        "path": "/data2/k6tk/a7/a751671c9914516c9834e50188a5a207a2b627f18a5eecb6c69e493096e6fc6f.png",
        "sha256": "a751671c9914516c9834e50188a5a207a2b627f18a5eecb6c69e493096e6fc6f"
      },
      {
        "path": "/data2/k6tk/66/665dda46c8cc6b084ff7a4e86de4bda25bf3d33a7ca28734b90129d18754ad08.png",
        "sha256": "665dda46c8cc6b084ff7a4e86de4bda25bf3d33a7ca28734b90129d18754ad08"
      }
    ],
    "options": [
      "A. fewer",
      "B. equal number",
      "C. more"
    ],
    "question": "Review the video to establish a total for 'bed' and a total for 'tv'. How should the 'bed' total be classified when compared with the 'tv' total?",
    "timestamps": [
      0.0,
      2.2,
      4.4,
      6.6,
      8.8,
      11.0,
      13.2,
      15.4,
      17.6,
      19.8,
      22.0,
      24.2,
      26.4,
      28.6,
      30.8,
      33.0,
      35.1,
      37.3,
      39.5,
      41.7,
      43.9,
      46.1,
      48.3,
      50.5,
      52.7,
      54.9,
      57.1,
      59.3,
      61.5,
      63.7,
      65.9,
      68.1
    ],
    "total_num_frames": 682
  },
  "target": "<think>\nlocate the distinct instances of bed; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are more bed instances than tv instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 15. fbp_relcnt2_d5cfdaee26b0eb15fd91bc2f

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-30e40613270c677c24415c3c8398b2091dbd6e81a30f697bcd02b35a1a90c26c",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41127059",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41127059.npz": "d54df73d80f8bacb84bcebc590c97cc6735b14989a37a3e50e1a494cfc77daae",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41127059.npz",
    "raster_sha256": "d54df73d80f8bacb84bcebc590c97cc6735b14989a37a3e50e1a494cfc77daae",
    "relative_count": {
      "a": "sofa",
      "b": "table",
      "bucket": "3",
      "count_a": 1,
      "count_b": 3,
      "ids_a": [
        12
      ],
      "ids_b": [
        7,
        13,
        14
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue383240",
      "scene_use_cap": 24,
      "source_qid": "b12ct_c46a9d05b87290f3c24bfb74",
      "source_row_sha256": "57ee2e0b6397e3b2b9d5cc6b688e690bceb167ddc0b71c2a241fbe13e7d21c40",
      "source_use_cap": 8,
      "template_id": 14,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_d5cfdaee26b0eb15fd91bc2f",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "ve3790c6ec193",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      19,
      38,
      56,
      75,
      94,
      113,
      131,
      150,
      169,
      188,
      207,
      225,
      244,
      263,
      282,
      300,
      319,
      338,
      357,
      375,
      394,
      413,
      432,
      451,
      469,
      488,
      507,
      526,
      544,
      563,
      582
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9a/9ad284524a04e84acbe2fc20963a02927bd726c1d5548e2c187aab9e0702e63c.png",
        "sha256": "9ad284524a04e84acbe2fc20963a02927bd726c1d5548e2c187aab9e0702e63c"
      },
      {
        "path": "/data2/k6tk/f9/f9fb67a73504539f2cd7b43466a3049253877297b07f20249e9c2be56c195875.png",
        "sha256": "f9fb67a73504539f2cd7b43466a3049253877297b07f20249e9c2be56c195875"
      },
      {
        "path": "/data2/k6tk/d9/d9c518aed51d28ba61980cb81f3789b94c18fe2f11650a97f702fa2066fe7a87.png",
        "sha256": "d9c518aed51d28ba61980cb81f3789b94c18fe2f11650a97f702fa2066fe7a87"
      },
      {
        "path": "/data2/k6tk/8d/8d2fde97511d16a6edf937b9546b97bda22db06412b5d142ef1c4fc20d694e98.png",
        "sha256": "8d2fde97511d16a6edf937b9546b97bda22db06412b5d142ef1c4fc20d694e98"
      },
      {
        "path": "/data2/k6tk/83/8346a28b8ccdc96bc1651a3b55a469f877dffcf92f7068139d4073aee09c77cc.png",
        "sha256": "8346a28b8ccdc96bc1651a3b55a469f877dffcf92f7068139d4073aee09c77cc"
      },
      {
        "path": "/data2/k6tk/02/02fa42c40e5e95f17db3001e232dd3bdd36cb510e41246a7cfc1f036f870e32c.png",
        "sha256": "02fa42c40e5e95f17db3001e232dd3bdd36cb510e41246a7cfc1f036f870e32c"
      },
      {
        "path": "/data2/k6tk/57/57b0864abbc7936c96af3825cb1cf81846696d23357ccbf32aed511714f2cb3c.png",
        "sha256": "57b0864abbc7936c96af3825cb1cf81846696d23357ccbf32aed511714f2cb3c"
      },
      {
        "path": "/data2/k6tk/27/2718a518adfefad816c03e6136578a0cee879f0137fc54860c9832ce5e1cad67.png",
        "sha256": "2718a518adfefad816c03e6136578a0cee879f0137fc54860c9832ce5e1cad67"
      },
      {
        "path": "/data2/k6tk/54/54676f40557974a76a96c122a14a96a219d0ab32081ccbacbb97bbd94ff9597f.png",
        "sha256": "54676f40557974a76a96c122a14a96a219d0ab32081ccbacbb97bbd94ff9597f"
      },
      {
        "path": "/data2/k6tk/ce/ceaba430e8375290a032647858a40f86b912947d75adffcb15667bdc4e1db781.png",
        "sha256": "ceaba430e8375290a032647858a40f86b912947d75adffcb15667bdc4e1db781"
      },
      {
        "path": "/data2/k6tk/02/022484d705abdfadd659adcffea508f96e99e863182a401e3298e6c4997a8d15.png",
        "sha256": "022484d705abdfadd659adcffea508f96e99e863182a401e3298e6c4997a8d15"
      },
      {
        "path": "/data2/k6tk/6f/6fa9d5f8cfdbc1a2340568d33f52078252e0d0c68ecff1a91113ede1f024bd1d.png",
        "sha256": "6fa9d5f8cfdbc1a2340568d33f52078252e0d0c68ecff1a91113ede1f024bd1d"
      },
      {
        "path": "/data2/k6tk/01/01337259899e0b72185f1f5bd503e5ac16e2142cd3b0e6b297dfb88693c4ccc9.png",
        "sha256": "01337259899e0b72185f1f5bd503e5ac16e2142cd3b0e6b297dfb88693c4ccc9"
      },
      {
        "path": "/data2/k6tk/28/289c29b5fe24f30b072ca7fb94d9a7f0de85a907fb929782f3523921bf2354a5.png",
        "sha256": "289c29b5fe24f30b072ca7fb94d9a7f0de85a907fb929782f3523921bf2354a5"
      },
      {
        "path": "/data2/k6tk/d9/d98b49de0bcb9493dcb32a8e66b25e6b280a8c59d11d04bd222a682de99254dc.png",
        "sha256": "d98b49de0bcb9493dcb32a8e66b25e6b280a8c59d11d04bd222a682de99254dc"
      },
      {
        "path": "/data2/k6tk/72/725a4c71827d306f91aee07ae12a013dfeafcfe587a595ad1bc1851f8c1548a2.png",
        "sha256": "725a4c71827d306f91aee07ae12a013dfeafcfe587a595ad1bc1851f8c1548a2"
      },
      {
        "path": "/data2/k6tk/ff/ff35738cb8a6f06d4ea74f3877bfcee357f51097baae9294c218d5613c531e21.png",
        "sha256": "ff35738cb8a6f06d4ea74f3877bfcee357f51097baae9294c218d5613c531e21"
      },
      {
        "path": "/data2/k6tk/ca/ca181933ef8c8ab8aa6c668119c2f08c58bf4b851ab8460d3ed71be633591ce0.png",
        "sha256": "ca181933ef8c8ab8aa6c668119c2f08c58bf4b851ab8460d3ed71be633591ce0"
      },
      {
        "path": "/data2/k6tk/8e/8ed3133da261f1c40c3c471eb03581b070a032388de125bcf28d206fcc1d2571.png",
        "sha256": "8ed3133da261f1c40c3c471eb03581b070a032388de125bcf28d206fcc1d2571"
      },
      {
        "path": "/data2/k6tk/1e/1e79e459e7e0341bde243d78d988526d45a46aedd25cc65f7a26dc623b5d3d35.png",
        "sha256": "1e79e459e7e0341bde243d78d988526d45a46aedd25cc65f7a26dc623b5d3d35"
      },
      {
        "path": "/data2/k6tk/cc/cc41975f38c641c13fc1bd05d7ec4792b46d9d63c93b14714fd027550e162462.png",
        "sha256": "cc41975f38c641c13fc1bd05d7ec4792b46d9d63c93b14714fd027550e162462"
      },
      {
        "path": "/data2/k6tk/c7/c74a72a6fe353df2ab6ab41012dfe0ab30ea8ab4c77c3f3950691243970814f3.png",
        "sha256": "c74a72a6fe353df2ab6ab41012dfe0ab30ea8ab4c77c3f3950691243970814f3"
      },
      {
        "path": "/data2/k6tk/8b/8b968a879a03787e8e06e8ba8243eeb5c7773d584cc14e41cdec06d29363dbe9.png",
        "sha256": "8b968a879a03787e8e06e8ba8243eeb5c7773d584cc14e41cdec06d29363dbe9"
      },
      {
        "path": "/data2/k6tk/84/846e7ac9dca99373693f77f366ec6b08c48f01899f4cc6c03fc7653ba5172481.png",
        "sha256": "846e7ac9dca99373693f77f366ec6b08c48f01899f4cc6c03fc7653ba5172481"
      },
      {
        "path": "/data2/k6tk/a1/a1ac7feddd6e2ea210ef5ac5206b1d56c88473983d22185176f034092a669126.png",
        "sha256": "a1ac7feddd6e2ea210ef5ac5206b1d56c88473983d22185176f034092a669126"
      },
      {
        "path": "/data2/k6tk/f8/f8f11110321713e56a65a59b5c5d391e03a6c7e3737556361f00cb9823d1517d.png",
        "sha256": "f8f11110321713e56a65a59b5c5d391e03a6c7e3737556361f00cb9823d1517d"
      },
      {
        "path": "/data2/k6tk/af/af35232c7dfe283eac293eacb29e7527c9bc17772a0e6e8790f94e0351f56f71.png",
        "sha256": "af35232c7dfe283eac293eacb29e7527c9bc17772a0e6e8790f94e0351f56f71"
      },
      {
        "path": "/data2/k6tk/03/03ec245e67c184c0fc587024deaee96a11f0c92373f6e2c2d409e99f559cf09e.png",
        "sha256": "03ec245e67c184c0fc587024deaee96a11f0c92373f6e2c2d409e99f559cf09e"
      },
      {
        "path": "/data2/k6tk/64/64e1e58e98d17d0a4d9854d3e0e460c6a8d51f42e7f1644e460ba16c349c2225.png",
        "sha256": "64e1e58e98d17d0a4d9854d3e0e460c6a8d51f42e7f1644e460ba16c349c2225"
      },
      {
        "path": "/data2/k6tk/69/692315fc00905696da44007ad5edc6f6a095c24ba657c64697d91ebba43fba2a.png",
        "sha256": "692315fc00905696da44007ad5edc6f6a095c24ba657c64697d91ebba43fba2a"
      },
      {
        "path": "/data2/k6tk/9f/9f64d3709d02aedcfb24bbd972fdde084e22642044298e958fd74bfe28c06ba9.png",
        "sha256": "9f64d3709d02aedcfb24bbd972fdde084e22642044298e958fd74bfe28c06ba9"
      },
      {
        "path": "/data2/k6tk/18/186b8711f1fa16bb512c398360c6866f5a70717bdb4e5e12509f8ff6d945137d.png",
        "sha256": "186b8711f1fa16bb512c398360c6866f5a70717bdb4e5e12509f8ff6d945137d"
      }
    ],
    "options": [
      "A. fewer",
      "B. equal number",
      "C. more"
    ],
    "question": "Compare category totals after identifying the distinct objects in the room: 'sofa' first, 'table' second. Which choice describes the first total in relation to the second?",
    "timestamps": [
      0.0,
      1.9,
      3.8,
      5.6,
      7.5,
      9.4,
      11.3,
      13.1,
      15.0,
      16.9,
      18.8,
      20.7,
      22.5,
      24.4,
      26.3,
      28.2,
      30.0,
      31.9,
      33.8,
      35.7,
      37.5,
      39.4,
      41.3,
      43.2,
      45.1,
      46.9,
      48.8,
      50.7,
      52.6,
      54.4,
      56.3,
      58.2
    ],
    "total_num_frames": 583
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are fewer sofa instances than table instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 16. fbp_relcnt2_a0da015989d7952bae223986

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-5444ff43e4f0eef91b223a21535df6502b8d874984ff43e5f51674cd595bec18",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47204674",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47204674.npz": "30023d7c1a2feb8a31ec70326715f77358278cd6dc1fac36ecfbcdfad25fae94",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47204674.npz",
    "raster_sha256": "30023d7c1a2feb8a31ec70326715f77358278cd6dc1fac36ecfbcdfad25fae94",
    "relative_count": {
      "a": "chair",
      "b": "table",
      "bucket": "6",
      "count_a": 6,
      "count_b": 4,
      "ids_a": [
        11,
        16,
        17,
        18,
        19,
        21
      ],
      "ids_b": [
        10,
        13,
        15,
        20
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue472045",
      "scene_use_cap": 24,
      "source_qid": "b12ct_e1e1bade157c4180e3963de9",
      "source_row_sha256": "36e74eac7e19f944eb6ebdea1946f469507556b484725ffc18dfa60e6540d591",
      "source_use_cap": 8,
      "template_id": 15,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_a0da015989d7952bae223986",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v52bddac82595",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      17,
      35,
      52,
      69,
      86,
      104,
      121,
      138,
      155,
      173,
      190,
      207,
      224,
      242,
      259,
      276,
      293,
      311,
      328,
      345,
      362,
      380,
      397,
      414,
      431,
      449,
      466,
      483,
      500,
      518,
      535
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f1/f12efd975ad362767c0361982ded2e8ed58c8b95a682a7f2db1dc91ca422862d.png",
        "sha256": "f12efd975ad362767c0361982ded2e8ed58c8b95a682a7f2db1dc91ca422862d"
      },
      {
        "path": "/data2/k6tk/66/66c0cad9a93305a6155f2a5075be85d84215018955c51142d60cec28e341adf8.png",
        "sha256": "66c0cad9a93305a6155f2a5075be85d84215018955c51142d60cec28e341adf8"
      },
      {
        "path": "/data2/k6tk/8a/8afe8a74f24d92bb0fcc39558a61c374a508d4d68c4749a609f3b8129a5711ab.png",
        "sha256": "8afe8a74f24d92bb0fcc39558a61c374a508d4d68c4749a609f3b8129a5711ab"
      },
      {
        "path": "/data2/k6tk/2b/2ba85f58f3cdab174a9ad54896546d6665c2dd9b0bcb63823970676bc5ff8c2f.png",
        "sha256": "2ba85f58f3cdab174a9ad54896546d6665c2dd9b0bcb63823970676bc5ff8c2f"
      },
      {
        "path": "/data2/k6tk/aa/aa04e2584edfb3e2de8ec47e01eefb6f3e6898534117735dc1144316646eb0a8.png",
        "sha256": "aa04e2584edfb3e2de8ec47e01eefb6f3e6898534117735dc1144316646eb0a8"
      },
      {
        "path": "/data2/k6tk/eb/eb042f0e6c2e02657f27cbb680ada3f6a5df0198115c3a765a3db7d7915b69a7.png",
        "sha256": "eb042f0e6c2e02657f27cbb680ada3f6a5df0198115c3a765a3db7d7915b69a7"
      },
      {
        "path": "/data2/k6tk/97/977bdba30213d7b45d9e2d9d26a126a06e6c5176fa8429ad8d6e37e57e10671d.png",
        "sha256": "977bdba30213d7b45d9e2d9d26a126a06e6c5176fa8429ad8d6e37e57e10671d"
      },
      {
        "path": "/data2/k6tk/72/724c690f3a6f0b9912f64a7973f14aca8e7eda8e1fb525a62db3233481a53dfc.png",
        "sha256": "724c690f3a6f0b9912f64a7973f14aca8e7eda8e1fb525a62db3233481a53dfc"
      },
      {
        "path": "/data2/k6tk/80/80be24ffc299f8ff3fef871f2f43da1003f2f4f4a75557e4c92f23779097b4ed.png",
        "sha256": "80be24ffc299f8ff3fef871f2f43da1003f2f4f4a75557e4c92f23779097b4ed"
      },
      {
        "path": "/data2/k6tk/ca/ca71860c053a1fdcf3fecbacdf9d81f54719d33bb8f7796869cc5815dd0fefec.png",
        "sha256": "ca71860c053a1fdcf3fecbacdf9d81f54719d33bb8f7796869cc5815dd0fefec"
      },
      {
        "path": "/data2/k6tk/5b/5ba0449755c95e4c4305434d0d521ecd71b553b923355c4f020a50f4a112a153.png",
        "sha256": "5ba0449755c95e4c4305434d0d521ecd71b553b923355c4f020a50f4a112a153"
      },
      {
        "path": "/data2/k6tk/dc/dc745bd458083d4e84a9e0aab63b838172b7747f87943c6bdc3f4b28b5193a4c.png",
        "sha256": "dc745bd458083d4e84a9e0aab63b838172b7747f87943c6bdc3f4b28b5193a4c"
      },
      {
        "path": "/data2/k6tk/c7/c7ba9dadc4011a83197e4d6371716eec2a2b1e9b4bac120a9793c3f90cb11ff1.png",
        "sha256": "c7ba9dadc4011a83197e4d6371716eec2a2b1e9b4bac120a9793c3f90cb11ff1"
      },
      {
        "path": "/data2/k6tk/7b/7b259f8c4c869a582caaaca681b42a2a1bdabacf5c45e5837ddc5cb91e626e55.png",
        "sha256": "7b259f8c4c869a582caaaca681b42a2a1bdabacf5c45e5837ddc5cb91e626e55"
      },
      {
        "path": "/data2/k6tk/cd/cdd4d63c3d5667453d20e81835647d599ef903bdc0532bf4d29f373f8c522081.png",
        "sha256": "cdd4d63c3d5667453d20e81835647d599ef903bdc0532bf4d29f373f8c522081"
      },
      {
        "path": "/data2/k6tk/38/389ee4692d58c3b31dbaa0aacb50988c0c9d446a0a9e8891203cefed853388e8.png",
        "sha256": "389ee4692d58c3b31dbaa0aacb50988c0c9d446a0a9e8891203cefed853388e8"
      },
      {
        "path": "/data2/k6tk/d8/d8650b08fe7c9d29d0e8a9f6e1377ad09e5433bfddbefa5f8c7e2f3e1f0f095e.png",
        "sha256": "d8650b08fe7c9d29d0e8a9f6e1377ad09e5433bfddbefa5f8c7e2f3e1f0f095e"
      },
      {
        "path": "/data2/k6tk/6c/6c61b06a08eecb2b4aebe5fc5c691b15c36a50145eeb3accfb565bfe943e6a20.png",
        "sha256": "6c61b06a08eecb2b4aebe5fc5c691b15c36a50145eeb3accfb565bfe943e6a20"
      },
      {
        "path": "/data2/k6tk/e9/e98b5643ca469e3c25215a8982edc7d4835125c77b5a4e402eef39e28592c7f5.png",
        "sha256": "e98b5643ca469e3c25215a8982edc7d4835125c77b5a4e402eef39e28592c7f5"
      },
      {
        "path": "/data2/k6tk/25/25addd92be46d678e2f94bae58ec11fa82b215b56740d967a9c50c368c40e196.png",
        "sha256": "25addd92be46d678e2f94bae58ec11fa82b215b56740d967a9c50c368c40e196"
      },
      {
        "path": "/data2/k6tk/bb/bb670bb20062a2813345c9d07c71140b3f1ad5f0ab1570a4b0398053e291d38c.png",
        "sha256": "bb670bb20062a2813345c9d07c71140b3f1ad5f0ab1570a4b0398053e291d38c"
      },
      {
        "path": "/data2/k6tk/79/79174b02204935b993de0e162ddaa736070f5640633793df9597176307057998.png",
        "sha256": "79174b02204935b993de0e162ddaa736070f5640633793df9597176307057998"
      },
      {
        "path": "/data2/k6tk/b0/b067a56fe91b6e0fdb786537c9130a8786de7ecba70341318913eee710a62fcf.png",
        "sha256": "b067a56fe91b6e0fdb786537c9130a8786de7ecba70341318913eee710a62fcf"
      },
      {
        "path": "/data2/k6tk/32/32948a8f4682b1f53baea4e549fe9dc92275490af1553f52a6cd71eab816b120.png",
        "sha256": "32948a8f4682b1f53baea4e549fe9dc92275490af1553f52a6cd71eab816b120"
      },
      {
        "path": "/data2/k6tk/9f/9fecd66f59621f089635dc389cee245a4a10b1b961134745e4dfca70ad4a49d2.png",
        "sha256": "9fecd66f59621f089635dc389cee245a4a10b1b961134745e4dfca70ad4a49d2"
      },
      {
        "path": "/data2/k6tk/83/83d285f6b92d57b059c296ac4b2393f133933e9d290f1aed34b773009f3e829c.png",
        "sha256": "83d285f6b92d57b059c296ac4b2393f133933e9d290f1aed34b773009f3e829c"
      },
      {
        "path": "/data2/k6tk/90/903a47444a7228d849a74409bc0e9fbee3da384426bb8fbba4845ae5baac0a85.png",
        "sha256": "903a47444a7228d849a74409bc0e9fbee3da384426bb8fbba4845ae5baac0a85"
      },
      {
        "path": "/data2/k6tk/76/769e17e9da608a3ee8ca38c6e373b1de4210b8753989baabb911f6e3458a51a1.png",
        "sha256": "769e17e9da608a3ee8ca38c6e373b1de4210b8753989baabb911f6e3458a51a1"
      },
      {
        "path": "/data2/k6tk/dd/dd911d0295c55981508b21e7cac5e1a671ffddf294cb8240793e51a29a47a335.png",
        "sha256": "dd911d0295c55981508b21e7cac5e1a671ffddf294cb8240793e51a29a47a335"
      },
      {
        "path": "/data2/k6tk/b2/b20778857a7d0e41c082768f1ee4be7182e14ce75ecb1fb07e58b0913ea385ac.png",
        "sha256": "b20778857a7d0e41c082768f1ee4be7182e14ce75ecb1fb07e58b0913ea385ac"
      },
      {
        "path": "/data2/k6tk/0c/0c8fc0349bdc33f1788f41227305b229ee428b050b7dd44141418ef89314824b.png",
        "sha256": "0c8fc0349bdc33f1788f41227305b229ee428b050b7dd44141418ef89314824b"
      },
      {
        "path": "/data2/k6tk/ad/adf7109a640112686c64d77920a5968a6274c1e0c0456aa3c05dfd50475373ff.png",
        "sha256": "adf7109a640112686c64d77920a5968a6274c1e0c0456aa3c05dfd50475373ff"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "There are separate object categories named 'chair' and 'table' to tally in these views. Choose the count relationship with 'chair' as the category being compared and 'table' as the reference.",
    "timestamps": [
      0.0,
      1.7,
      3.5,
      5.2,
      6.9,
      8.6,
      10.4,
      12.1,
      13.8,
      15.5,
      17.3,
      19.0,
      20.7,
      22.4,
      24.2,
      25.9,
      27.6,
      29.3,
      31.1,
      32.8,
      34.5,
      36.2,
      38.0,
      39.7,
      41.4,
      43.1,
      44.9,
      46.6,
      48.3,
      50.0,
      51.8,
      53.5
    ],
    "total_num_frames": 536
  },
  "target": "<think>\nlocate the distinct instances of chair; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are more chair instances than table instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 17. fbp_relcnt2_da1e3a9d5562f136aa9fdf21

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-e60ab59b84892fcd02be8e4f6b832180fd5a16092fae47334ea95771db8ab421",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/44796340",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/44796340.npz": "b4beca9df0cb252e8cfe1e8f390e9ca4f4e705007fb5329463c47a778f4f4753",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "44796340.npz",
    "raster_sha256": "b4beca9df0cb252e8cfe1e8f390e9ca4f4e705007fb5329463c47a778f4f4753",
    "relative_count": {
      "a": "sofa",
      "b": "table",
      "bucket": "2",
      "count_a": 2,
      "count_b": 1,
      "ids_a": [
        2,
        5
      ],
      "ids_b": [
        3
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue464785",
      "scene_use_cap": 24,
      "source_qid": "b12ct_01af3c72ced716a0764e0c28",
      "source_row_sha256": "c5fe211abf76ad5cbe2310464625760959e064fd5d285439295249eb504eb029",
      "source_use_cap": 8,
      "template_id": 16,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_da1e3a9d5562f136aa9fdf21",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v2a8b7ec4806c",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      22,
      44,
      65,
      87,
      109,
      131,
      153,
      174,
      196,
      218,
      240,
      262,
      283,
      305,
      327,
      349,
      371,
      393,
      414,
      436,
      458,
      480,
      502,
      523,
      545,
      567,
      589,
      611,
      632,
      654,
      676
    ],
    "frames": [
      {
        "path": "/data2/k6tk/16/1671a058698d4573b8f8d9ae785d0318dadbeccc01ca7700567e917d4eff6dd9.png",
        "sha256": "1671a058698d4573b8f8d9ae785d0318dadbeccc01ca7700567e917d4eff6dd9"
      },
      {
        "path": "/data2/k6tk/5c/5c7aa437f3c93f8a4c259102c1247b715b5f69215531ce5dc1ef0801680ff358.png",
        "sha256": "5c7aa437f3c93f8a4c259102c1247b715b5f69215531ce5dc1ef0801680ff358"
      },
      {
        "path": "/data2/k6tk/15/1525d948c9aee9de5e1d22e065a9995bb8071d7b16887eb5cf5a3a5716866126.png",
        "sha256": "1525d948c9aee9de5e1d22e065a9995bb8071d7b16887eb5cf5a3a5716866126"
      },
      {
        "path": "/data2/k6tk/26/26dbc8251b1f608b7c055179b5202720e6acf8b59ea6fc79049442401814a5b1.png",
        "sha256": "26dbc8251b1f608b7c055179b5202720e6acf8b59ea6fc79049442401814a5b1"
      },
      {
        "path": "/data2/k6tk/5a/5a2f10748bce565363b8f08848635e8ef8aa8b7bafd166a8b3e1af55e18b1ffb.png",
        "sha256": "5a2f10748bce565363b8f08848635e8ef8aa8b7bafd166a8b3e1af55e18b1ffb"
      },
      {
        "path": "/data2/k6tk/b7/b73b911bcaf7bfb6b75e0a68b3727b9fdd67c4220f0e53aba62d71d37c8bcf6d.png",
        "sha256": "b73b911bcaf7bfb6b75e0a68b3727b9fdd67c4220f0e53aba62d71d37c8bcf6d"
      },
      {
        "path": "/data2/k6tk/bc/bc34d1ade323b2b5d7415fbb0319994706832db12808c95fce5ef1f7370412aa.png",
        "sha256": "bc34d1ade323b2b5d7415fbb0319994706832db12808c95fce5ef1f7370412aa"
      },
      {
        "path": "/data2/k6tk/bd/bd4a29739b807607be5b527ceefa7d440fac085861c631fc5f47a58506f5b02a.png",
        "sha256": "bd4a29739b807607be5b527ceefa7d440fac085861c631fc5f47a58506f5b02a"
      },
      {
        "path": "/data2/k6tk/d5/d54b479262b0449ac0faf78639d9697974d7b228d2fa96f653cecd2f7af51711.png",
        "sha256": "d54b479262b0449ac0faf78639d9697974d7b228d2fa96f653cecd2f7af51711"
      },
      {
        "path": "/data2/k6tk/94/945d2c2f69ba3d44184b098cce5cc2fb505826c2826006691522c1c40af0dbfd.png",
        "sha256": "945d2c2f69ba3d44184b098cce5cc2fb505826c2826006691522c1c40af0dbfd"
      },
      {
        "path": "/data2/k6tk/b5/b5157df9eaf0ba28e1f48a25d1a3a2948051bbf5798905234e6403c265298133.png",
        "sha256": "b5157df9eaf0ba28e1f48a25d1a3a2948051bbf5798905234e6403c265298133"
      },
      {
        "path": "/data2/k6tk/71/71c320a09ced78d811f86773ebe994eaacfad8dd2369a7343c495f1257d1a435.png",
        "sha256": "71c320a09ced78d811f86773ebe994eaacfad8dd2369a7343c495f1257d1a435"
      },
      {
        "path": "/data2/k6tk/6e/6ed34526901bdc580f55e92e1cd35eb47b54838141460eb0a107e00622b8507b.png",
        "sha256": "6ed34526901bdc580f55e92e1cd35eb47b54838141460eb0a107e00622b8507b"
      },
      {
        "path": "/data2/k6tk/1e/1e99ac0f08fc7952d1e534913bf91caccc4306b6efaf5d0942f8be8e0c34b030.png",
        "sha256": "1e99ac0f08fc7952d1e534913bf91caccc4306b6efaf5d0942f8be8e0c34b030"
      },
      {
        "path": "/data2/k6tk/4b/4b2f6cb9e3c23da3f072f171b2feec700cb854db094e7735072a94079a75401b.png",
        "sha256": "4b2f6cb9e3c23da3f072f171b2feec700cb854db094e7735072a94079a75401b"
      },
      {
        "path": "/data2/k6tk/ab/abfd174cba9c31dba61187a4b2b01a6245098d176ab16d3754873a6b47a734a7.png",
        "sha256": "abfd174cba9c31dba61187a4b2b01a6245098d176ab16d3754873a6b47a734a7"
      },
      {
        "path": "/data2/k6tk/97/9713c1b893fa954bda939646d0c522317a5f3c6b92a4c0bed11fbb934d7a1dd9.png",
        "sha256": "9713c1b893fa954bda939646d0c522317a5f3c6b92a4c0bed11fbb934d7a1dd9"
      },
      {
        "path": "/data2/k6tk/9b/9bb1167ed69152c8cf780570e876ff840ee752902f8629817080a45e2eac6178.png",
        "sha256": "9bb1167ed69152c8cf780570e876ff840ee752902f8629817080a45e2eac6178"
      },
      {
        "path": "/data2/k6tk/f8/f89cf6e734e91df44f4e2c2730d227f046ab0e89addcb6709617140ddcf38d07.png",
        "sha256": "f89cf6e734e91df44f4e2c2730d227f046ab0e89addcb6709617140ddcf38d07"
      },
      {
        "path": "/data2/k6tk/05/05f87f7a0416e2fd50fc5901aafa989bf14638f897d39b89620376e779bc09f3.png",
        "sha256": "05f87f7a0416e2fd50fc5901aafa989bf14638f897d39b89620376e779bc09f3"
      },
      {
        "path": "/data2/k6tk/d9/d902d7e04a03273cec7855636b163a5caeee661d6d462bca6148297aa633b6cf.png",
        "sha256": "d902d7e04a03273cec7855636b163a5caeee661d6d462bca6148297aa633b6cf"
      },
      {
        "path": "/data2/k6tk/52/52b2f453475ae7cba8c68d58ab6baa7588af8f464c7698b50008e91e3e4eb251.png",
        "sha256": "52b2f453475ae7cba8c68d58ab6baa7588af8f464c7698b50008e91e3e4eb251"
      },
      {
        "path": "/data2/k6tk/89/898de231da142b8c65b27fb9687ee319ebe8078cf07e35161185294e1e9fd976.png",
        "sha256": "898de231da142b8c65b27fb9687ee319ebe8078cf07e35161185294e1e9fd976"
      },
      {
        "path": "/data2/k6tk/59/5934386ab1ea634d7929789d62e92cd49a44d87fe2fa3edc50fd009b94bb8567.png",
        "sha256": "5934386ab1ea634d7929789d62e92cd49a44d87fe2fa3edc50fd009b94bb8567"
      },
      {
        "path": "/data2/k6tk/4f/4f3e111d7b55a7d8c8f13e2e63356ffcec92699ccb27295007bee195e2e90018.png",
        "sha256": "4f3e111d7b55a7d8c8f13e2e63356ffcec92699ccb27295007bee195e2e90018"
      },
      {
        "path": "/data2/k6tk/3e/3e2fa93b60c5b6d60af4e08ae1a32972c8d307924f9e6b97b007a15d1ada7b6f.png",
        "sha256": "3e2fa93b60c5b6d60af4e08ae1a32972c8d307924f9e6b97b007a15d1ada7b6f"
      },
      {
        "path": "/data2/k6tk/1a/1a23c4b712785466c77562133cb0844fc9afc551c4f3db880645c31ea70af255.png",
        "sha256": "1a23c4b712785466c77562133cb0844fc9afc551c4f3db880645c31ea70af255"
      },
      {
        "path": "/data2/k6tk/98/98b35102e0e23ff9d0ca15365fac4192cd83742ef5996371621c5359cd6d17cd.png",
        "sha256": "98b35102e0e23ff9d0ca15365fac4192cd83742ef5996371621c5359cd6d17cd"
      },
      {
        "path": "/data2/k6tk/50/509fc97e5e0a7d6b8d5187bdfcd401b34e6dde951a57195ebe572fa0edb1bb8e.png",
        "sha256": "509fc97e5e0a7d6b8d5187bdfcd401b34e6dde951a57195ebe572fa0edb1bb8e"
      },
      {
        "path": "/data2/k6tk/bb/bbe1f30e45d5d223795e0aeb020d48cdf0d379aac8bd876336577557016538cc.png",
        "sha256": "bbe1f30e45d5d223795e0aeb020d48cdf0d379aac8bd876336577557016538cc"
      },
      {
        "path": "/data2/k6tk/69/691002daf6909344c10acdf6c5b992946c3508942fd0b79a12aa0a15e5c7631a.png",
        "sha256": "691002daf6909344c10acdf6c5b992946c3508942fd0b79a12aa0a15e5c7631a"
      },
      {
        "path": "/data2/k6tk/48/48c4030bf0126579e9b9ec3071be7b9ff278e3251ae9b1ee5e97f93d1084695b.png",
        "sha256": "48c4030bf0126579e9b9ec3071be7b9ff278e3251ae9b1ee5e97f93d1084695b"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "Determine how many separate objects belong to 'sofa' and how many belong to 'table'. Using those totals, choose the comparison of 'sofa' with 'table'.",
    "timestamps": [
      0.0,
      2.2,
      4.4,
      6.5,
      8.7,
      10.9,
      13.1,
      15.3,
      17.4,
      19.6,
      21.8,
      24.0,
      26.2,
      28.3,
      30.5,
      32.7,
      34.9,
      37.1,
      39.3,
      41.4,
      43.6,
      45.8,
      48.0,
      50.2,
      52.3,
      54.5,
      56.7,
      58.9,
      61.1,
      63.2,
      65.4,
      67.6
    ],
    "total_num_frames": 677
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are more sofa instances than table instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 18. fbp_relcnt2_6e242cee1f20569f6c2a3f1c

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-d2f2b6f3d9b1e823464ef08388d12bec78a21f7545a4ae2afeab4ce32887b7d0",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/43649742",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/43649742.npz": "c09ef78331f4951a8d550b81697bbf566d87847c65b795463268892a33e4b37a",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "43649742.npz",
    "raster_sha256": "c09ef78331f4951a8d550b81697bbf566d87847c65b795463268892a33e4b37a",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "7",
      "count_a": 7,
      "count_b": 1,
      "ids_a": [
        2,
        3,
        4,
        6,
        11,
        14,
        15
      ],
      "ids_b": [
        5
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue437218",
      "scene_use_cap": 24,
      "source_qid": "b12ct_cb662736cb5033076c397127",
      "source_row_sha256": "9c7c579683ce8d0e06c726b882710b50f27b6e1759fa6454f3a4b06982ad6dce",
      "source_use_cap": 8,
      "template_id": 17,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_6e242cee1f20569f6c2a3f1c",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v896598632578",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      32,
      64,
      97,
      129,
      161,
      193,
      225,
      258,
      290,
      322,
      354,
      386,
      419,
      451,
      483,
      515,
      547,
      579,
      612,
      644,
      676,
      708,
      740,
      773,
      805,
      837,
      869,
      901,
      934,
      966,
      998
    ],
    "frames": [
      {
        "path": "/data2/k6tk/40/409e40159b94f1ea0926a46e633f2720f13e4cadfdb3787e37b0ea8a8ca8e70b.png",
        "sha256": "409e40159b94f1ea0926a46e633f2720f13e4cadfdb3787e37b0ea8a8ca8e70b"
      },
      {
        "path": "/data2/k6tk/3b/3b4b67e68b756d7a67b207f67b6d994b2b57a565be3dede9489aaca67ae2c165.png",
        "sha256": "3b4b67e68b756d7a67b207f67b6d994b2b57a565be3dede9489aaca67ae2c165"
      },
      {
        "path": "/data2/k6tk/ed/ed9b48be3455e11673640c61659613553636aff39c606f4ae22b83cf1cfd5e55.png",
        "sha256": "ed9b48be3455e11673640c61659613553636aff39c606f4ae22b83cf1cfd5e55"
      },
      {
        "path": "/data2/k6tk/db/dba8714cd1a6083ca4695d473d6181365afbddc6c910aa9e7ea16f5e83d27db9.png",
        "sha256": "dba8714cd1a6083ca4695d473d6181365afbddc6c910aa9e7ea16f5e83d27db9"
      },
      {
        "path": "/data2/k6tk/94/94883cfdb4aceb6ad53856ef58d915c516a8fc0c1b3e0cf82d9dd82f23a08cbf.png",
        "sha256": "94883cfdb4aceb6ad53856ef58d915c516a8fc0c1b3e0cf82d9dd82f23a08cbf"
      },
      {
        "path": "/data2/k6tk/58/58bd6383667e8b09c8c6752982de173b5610535339c994e9b832d1db9ef55561.png",
        "sha256": "58bd6383667e8b09c8c6752982de173b5610535339c994e9b832d1db9ef55561"
      },
      {
        "path": "/data2/k6tk/6c/6cadbc2b9b553ade1d2244614496375ceacfa73e39d50540d3211ffbc4551b9e.png",
        "sha256": "6cadbc2b9b553ade1d2244614496375ceacfa73e39d50540d3211ffbc4551b9e"
      },
      {
        "path": "/data2/k6tk/99/99311bfe02bfa88761119a05fdbd77f9e14a1a055ef9fe2072715fed70e7ca4c.png",
        "sha256": "99311bfe02bfa88761119a05fdbd77f9e14a1a055ef9fe2072715fed70e7ca4c"
      },
      {
        "path": "/data2/k6tk/1b/1b82791d9c334a246330f04e423b2c94a805d779024f6222fb6cabfec5d7bee4.png",
        "sha256": "1b82791d9c334a246330f04e423b2c94a805d779024f6222fb6cabfec5d7bee4"
      },
      {
        "path": "/data2/k6tk/77/77e060c48a25cc4fb93529ca2db86b2531bd9ac867f01273567ceba145da5142.png",
        "sha256": "77e060c48a25cc4fb93529ca2db86b2531bd9ac867f01273567ceba145da5142"
      },
      {
        "path": "/data2/k6tk/37/378b6ed73afff759dd7901a9e652acac6483a83109ed46ea98b52b31aa4cff75.png",
        "sha256": "378b6ed73afff759dd7901a9e652acac6483a83109ed46ea98b52b31aa4cff75"
      },
      {
        "path": "/data2/k6tk/2b/2b491de0d072c472b9c9ca689ae30ab932453a6579566453a8cb345a6842628a.png",
        "sha256": "2b491de0d072c472b9c9ca689ae30ab932453a6579566453a8cb345a6842628a"
      },
      {
        "path": "/data2/k6tk/6a/6a276d2b11ab72914d76c8251b0f055a813780545d4ca3d0c4adff64b3e658ef.png",
        "sha256": "6a276d2b11ab72914d76c8251b0f055a813780545d4ca3d0c4adff64b3e658ef"
      },
      {
        "path": "/data2/k6tk/9d/9ddaf3e30523af291cce328e47e2c6578c72cc397a73bea9fd6e6d5bfd07b346.png",
        "sha256": "9ddaf3e30523af291cce328e47e2c6578c72cc397a73bea9fd6e6d5bfd07b346"
      },
      {
        "path": "/data2/k6tk/5d/5d74babba0a3abe4d686d1e7459753b49c142b0eaeffaca864891df9013e5e1e.png",
        "sha256": "5d74babba0a3abe4d686d1e7459753b49c142b0eaeffaca864891df9013e5e1e"
      },
      {
        "path": "/data2/k6tk/4b/4b97becf30825183e31d88124c96048997a84890651f9946394db2a79494b6aa.png",
        "sha256": "4b97becf30825183e31d88124c96048997a84890651f9946394db2a79494b6aa"
      },
      {
        "path": "/data2/k6tk/e1/e1b9923df5e33afa61c3de1edd1c4b21ba1b3ac0066882165434e0e1514728a0.png",
        "sha256": "e1b9923df5e33afa61c3de1edd1c4b21ba1b3ac0066882165434e0e1514728a0"
      },
      {
        "path": "/data2/k6tk/60/60d9991b80e7156212db16198e0c967ed6a23d61930006384fe0892dc9b18e63.png",
        "sha256": "60d9991b80e7156212db16198e0c967ed6a23d61930006384fe0892dc9b18e63"
      },
      {
        "path": "/data2/k6tk/7f/7f5afd97a52820bd11b08bbb13adb5c568f7922e172fe630ca2a23c2a356db11.png",
        "sha256": "7f5afd97a52820bd11b08bbb13adb5c568f7922e172fe630ca2a23c2a356db11"
      },
      {
        "path": "/data2/k6tk/12/1246a609741ae1412fca6e777be68c5ca89a85b2a7cca38b4025bbeaf81b7ed9.png",
        "sha256": "1246a609741ae1412fca6e777be68c5ca89a85b2a7cca38b4025bbeaf81b7ed9"
      },
      {
        "path": "/data2/k6tk/9c/9cabdbd9cc1e90d3254da0156f624fe922377638c17006b70d634ab18b566834.png",
        "sha256": "9cabdbd9cc1e90d3254da0156f624fe922377638c17006b70d634ab18b566834"
      },
      {
        "path": "/data2/k6tk/49/492ff53a3b26e6a6bb6d6e588bcb2bccb0072fd0c4a7012671a92ae62b4a0ee0.png",
        "sha256": "492ff53a3b26e6a6bb6d6e588bcb2bccb0072fd0c4a7012671a92ae62b4a0ee0"
      },
      {
        "path": "/data2/k6tk/27/27104bc0e98b4f5dfe0a61a56dc6dd34b9a67a8411288615f067b11452e68755.png",
        "sha256": "27104bc0e98b4f5dfe0a61a56dc6dd34b9a67a8411288615f067b11452e68755"
      },
      {
        "path": "/data2/k6tk/e5/e502d89d47bf2bb9f6d308abfb845413dca1e9c7c4758debf5f3829ae1af9833.png",
        "sha256": "e502d89d47bf2bb9f6d308abfb845413dca1e9c7c4758debf5f3829ae1af9833"
      },
      {
        "path": "/data2/k6tk/74/740197863c594f24066971f845e106b28f856fcb4951f2215e409d54c2d7290a.png",
        "sha256": "740197863c594f24066971f845e106b28f856fcb4951f2215e409d54c2d7290a"
      },
      {
        "path": "/data2/k6tk/d9/d9f5a506904d5cf7001413e8ea95ae5522fd8a91c626a6e1570eb34f892d7dfe.png",
        "sha256": "d9f5a506904d5cf7001413e8ea95ae5522fd8a91c626a6e1570eb34f892d7dfe"
      },
      {
        "path": "/data2/k6tk/e6/e6a6fef59bedcb891c13e25fc973353ab3f25c9f1c3bc006ebc92763a2239e68.png",
        "sha256": "e6a6fef59bedcb891c13e25fc973353ab3f25c9f1c3bc006ebc92763a2239e68"
      },
      {
        "path": "/data2/k6tk/b7/b73e2f41bc39f883674d7b04e2f17dd9e621f100fa17b69e9493aa4fbbe05327.png",
        "sha256": "b73e2f41bc39f883674d7b04e2f17dd9e621f100fa17b69e9493aa4fbbe05327"
      },
      {
        "path": "/data2/k6tk/1f/1f82676eef89fb96f26c47d9272d5ba75138485e4b52698656d235d280ac0920.png",
        "sha256": "1f82676eef89fb96f26c47d9272d5ba75138485e4b52698656d235d280ac0920"
      },
      {
        "path": "/data2/k6tk/5c/5c1e7bd351e9dd183878b84bce6b29b9e9ef3555a7449249e2044a9a5bac1778.png",
        "sha256": "5c1e7bd351e9dd183878b84bce6b29b9e9ef3555a7449249e2044a9a5bac1778"
      },
      {
        "path": "/data2/k6tk/87/87c1aec9b884242b2843f0fa9bc4f39aa0e03e26a857b28314914940821d856f.png",
        "sha256": "87c1aec9b884242b2843f0fa9bc4f39aa0e03e26a857b28314914940821d856f"
      },
      {
        "path": "/data2/k6tk/a7/a7f96a0022af5f14a49b9d1f2a49d194d5938746e395279d1096d32e0d291bba.png",
        "sha256": "a7f96a0022af5f14a49b9d1f2a49d194d5938746e395279d1096d32e0d291bba"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Use the room video to compare the populations of 'table' objects and 'chair' objects. Which option describes the first population relative to the second after repeated views are counted only once?",
    "timestamps": [
      0.0,
      3.2,
      6.4,
      9.7,
      12.9,
      16.1,
      19.3,
      22.5,
      25.8,
      29.0,
      32.2,
      35.4,
      38.6,
      41.9,
      45.1,
      48.3,
      51.5,
      54.7,
      57.9,
      61.2,
      64.4,
      67.6,
      70.8,
      74.0,
      77.3,
      80.5,
      83.7,
      86.9,
      90.1,
      93.4,
      96.6,
      99.8
    ],
    "total_num_frames": 999
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are more table instances than chair instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 19. fbp_relcnt2_0077fac1f0689194d6d83f70

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-279875c78b1d30340f5b46dbc7864f364c7375b6d0548bb7b3df84404adb23ab",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47204473",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47204473.npz": "a7ec2ce53f30fc3aa2b073a1cdd940852b9e3f4711d0f60f4b68bcc23ffaac9a",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47204473.npz",
    "raster_sha256": "a7ec2ce53f30fc3aa2b073a1cdd940852b9e3f4711d0f60f4b68bcc23ffaac9a",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "6",
      "count_a": 6,
      "count_b": 3,
      "ids_a": [
        2,
        3,
        7,
        10,
        15,
        16
      ],
      "ids_b": [
        0,
        1,
        6
      ],
      "orientation_use_cap": 2,
      "relation": "more",
      "room": "arkitscenes/venue471146",
      "scene_use_cap": 24,
      "source_qid": "b12ct_54e22f02cbade76e902d0374",
      "source_row_sha256": "a146e969aa2e040a884c5ba4cd04354ad1fc5750aa781b2f32869259417280b0",
      "source_use_cap": 8,
      "template_id": 18,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_0077fac1f0689194d6d83f70",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vff604c93f780",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      25,
      49,
      74,
      99,
      123,
      148,
      173,
      197,
      222,
      247,
      271,
      296,
      321,
      345,
      370,
      395,
      420,
      444,
      469,
      494,
      518,
      543,
      568,
      592,
      617,
      642,
      666,
      691,
      716,
      740,
      765
    ],
    "frames": [
      {
        "path": "/data2/k6tk/02/02645d173ba50880d7e9dacd1e023f3f424ceee957fe3248f27ca9774c6e929b.png",
        "sha256": "02645d173ba50880d7e9dacd1e023f3f424ceee957fe3248f27ca9774c6e929b"
      },
      {
        "path": "/data2/k6tk/1c/1c39d963d9d4f4523338b60c4e70d718a0af6146036ea609ba6e35c8a1b4f9a0.png",
        "sha256": "1c39d963d9d4f4523338b60c4e70d718a0af6146036ea609ba6e35c8a1b4f9a0"
      },
      {
        "path": "/data2/k6tk/dd/dde71dd6e9b0e8070296857270221000bccda40ff0c7a586ec2f17c9b6f3fc4d.png",
        "sha256": "dde71dd6e9b0e8070296857270221000bccda40ff0c7a586ec2f17c9b6f3fc4d"
      },
      {
        "path": "/data2/k6tk/fe/fe1d4069a67f018acb4ed9bf1222240af50aa6321ada7b8a753c2475f7c3517d.png",
        "sha256": "fe1d4069a67f018acb4ed9bf1222240af50aa6321ada7b8a753c2475f7c3517d"
      },
      {
        "path": "/data2/k6tk/1f/1fbfb53123381facaf1c05529117ad3e6fc3f74f4cb3ae79d9d00124a91f58ed.png",
        "sha256": "1fbfb53123381facaf1c05529117ad3e6fc3f74f4cb3ae79d9d00124a91f58ed"
      },
      {
        "path": "/data2/k6tk/0c/0cedfdf5bc735aa7c0e9fabf5648e03e9e5685d20c1dc70bc9b18fc59992483e.png",
        "sha256": "0cedfdf5bc735aa7c0e9fabf5648e03e9e5685d20c1dc70bc9b18fc59992483e"
      },
      {
        "path": "/data2/k6tk/66/66770279841afecfbe84eca0a69f2ea0dafd383f15abc89d0e6fe6579549bd71.png",
        "sha256": "66770279841afecfbe84eca0a69f2ea0dafd383f15abc89d0e6fe6579549bd71"
      },
      {
        "path": "/data2/k6tk/d8/d870f54ae6dfd18624eb42e8ce61c250a94d21145831215b17c72409bad222ba.png",
        "sha256": "d870f54ae6dfd18624eb42e8ce61c250a94d21145831215b17c72409bad222ba"
      },
      {
        "path": "/data2/k6tk/25/2577b171441937b86610f2ed39953146f49e6c0a1e5ca8af696bf873b3ef788c.png",
        "sha256": "2577b171441937b86610f2ed39953146f49e6c0a1e5ca8af696bf873b3ef788c"
      },
      {
        "path": "/data2/k6tk/1b/1bac7045da3f5f594a8fcc5a00ac2d342b05adca830f34ced7bb3e0efbbeeeec.png",
        "sha256": "1bac7045da3f5f594a8fcc5a00ac2d342b05adca830f34ced7bb3e0efbbeeeec"
      },
      {
        "path": "/data2/k6tk/8c/8c9c76977177ec21ba23faa57179141a513d68e36f9e5fe44e64392ee70c2e84.png",
        "sha256": "8c9c76977177ec21ba23faa57179141a513d68e36f9e5fe44e64392ee70c2e84"
      },
      {
        "path": "/data2/k6tk/72/720350ade4dc77a7c66208e31bcb9fa1d6df3bbab48aba5efc3838722af2db8d.png",
        "sha256": "720350ade4dc77a7c66208e31bcb9fa1d6df3bbab48aba5efc3838722af2db8d"
      },
      {
        "path": "/data2/k6tk/d4/d46ff94994892a3b623d2fd1106023de714108b296ca104c7852e12f8adbb442.png",
        "sha256": "d46ff94994892a3b623d2fd1106023de714108b296ca104c7852e12f8adbb442"
      },
      {
        "path": "/data2/k6tk/87/8729c8516b867627c86bbc027b1026496e462f5b63815ffdef23e6c241475c22.png",
        "sha256": "8729c8516b867627c86bbc027b1026496e462f5b63815ffdef23e6c241475c22"
      },
      {
        "path": "/data2/k6tk/9e/9ee39d00f5dfa3b829a8859146cbb15ffabde8c6416d2aea394b2d1b69323f21.png",
        "sha256": "9ee39d00f5dfa3b829a8859146cbb15ffabde8c6416d2aea394b2d1b69323f21"
      },
      {
        "path": "/data2/k6tk/fd/fd65f2272435fce7efa9517917803ed043f5bac3b3cd2cf3a7c2e885e7ec47a8.png",
        "sha256": "fd65f2272435fce7efa9517917803ed043f5bac3b3cd2cf3a7c2e885e7ec47a8"
      },
      {
        "path": "/data2/k6tk/9f/9f9d8e80cd90848a905a36d90b0cd0ea6ed447b52de137915071a04663aa8d5e.png",
        "sha256": "9f9d8e80cd90848a905a36d90b0cd0ea6ed447b52de137915071a04663aa8d5e"
      },
      {
        "path": "/data2/k6tk/8b/8b2b08b1f41186c889a19a5ba29e8258b618e38d6896e6d15d2551f8af1a02dd.png",
        "sha256": "8b2b08b1f41186c889a19a5ba29e8258b618e38d6896e6d15d2551f8af1a02dd"
      },
      {
        "path": "/data2/k6tk/fa/fa55c93ec619f0dab36b5d2a8f5c139c71511955e79f45f50dbcbb06f70900ce.png",
        "sha256": "fa55c93ec619f0dab36b5d2a8f5c139c71511955e79f45f50dbcbb06f70900ce"
      },
      {
        "path": "/data2/k6tk/27/272ef3e304329916a2ed641fa71195594273be9cb670673719216364a9525919.png",
        "sha256": "272ef3e304329916a2ed641fa71195594273be9cb670673719216364a9525919"
      },
      {
        "path": "/data2/k6tk/d5/d5ce053cb82b8ef8a4818078668a8583d2e879f78d77a9535c755b302e146e63.png",
        "sha256": "d5ce053cb82b8ef8a4818078668a8583d2e879f78d77a9535c755b302e146e63"
      },
      {
        "path": "/data2/k6tk/b7/b7e8c6235aece92033c96f9c708b8eac03fb9e571bc94ae4604848edd0559d19.png",
        "sha256": "b7e8c6235aece92033c96f9c708b8eac03fb9e571bc94ae4604848edd0559d19"
      },
      {
        "path": "/data2/k6tk/a4/a4f0c636a7fc6437e94f647eb6b8b0e9af7c6d51ab6fbcb990ee363da0fc8ad3.png",
        "sha256": "a4f0c636a7fc6437e94f647eb6b8b0e9af7c6d51ab6fbcb990ee363da0fc8ad3"
      },
      {
        "path": "/data2/k6tk/e5/e57406333b2d985c450efb834899c24af63e3a3c4adc0bbc7016fd9e3ceffef8.png",
        "sha256": "e57406333b2d985c450efb834899c24af63e3a3c4adc0bbc7016fd9e3ceffef8"
      },
      {
        "path": "/data2/k6tk/4a/4a9263ce6c7a3050610673a1d6be3326d56775cd38c65faf3cbe47934b776a47.png",
        "sha256": "4a9263ce6c7a3050610673a1d6be3326d56775cd38c65faf3cbe47934b776a47"
      },
      {
        "path": "/data2/k6tk/7c/7c988a1abaa60c657d54535d493e0eb8a3c6aae722fd10680f7af3738ee929c8.png",
        "sha256": "7c988a1abaa60c657d54535d493e0eb8a3c6aae722fd10680f7af3738ee929c8"
      },
      {
        "path": "/data2/k6tk/26/26a7173530c48ab6795fe381a9a87a7d68188cad0e5fcab967eda080a91a8cdd.png",
        "sha256": "26a7173530c48ab6795fe381a9a87a7d68188cad0e5fcab967eda080a91a8cdd"
      },
      {
        "path": "/data2/k6tk/30/30398626e013cea58a7c94f4b2a15cf30cb985163a6553d1c5e541e47939be95.png",
        "sha256": "30398626e013cea58a7c94f4b2a15cf30cb985163a6553d1c5e541e47939be95"
      },
      {
        "path": "/data2/k6tk/4b/4b38e32690448da22519c2a612852c2ec0a8c9ccd8cda74069b81c8043537dd9.png",
        "sha256": "4b38e32690448da22519c2a612852c2ec0a8c9ccd8cda74069b81c8043537dd9"
      },
      {
        "path": "/data2/k6tk/84/84db83cf4691e26b3ff8d32c2f5951adb6ecde67a7a284ffa6ab1a5e05ac7fc5.png",
        "sha256": "84db83cf4691e26b3ff8d32c2f5951adb6ecde67a7a284ffa6ab1a5e05ac7fc5"
      },
      {
        "path": "/data2/k6tk/a7/a7d13c2c6116e4f08bb1b9922034111b7d11996047e9618274ead594ace205d5.png",
        "sha256": "a7d13c2c6116e4f08bb1b9922034111b7d11996047e9618274ead594ace205d5"
      },
      {
        "path": "/data2/k6tk/1d/1d4e07828a3639f8cf66648ac9bf09b0ef4e62c754cdd9eebdab8db3568ba7ba.png",
        "sha256": "1d4e07828a3639f8cf66648ac9bf09b0ef4e62c754cdd9eebdab8db3568ba7ba"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "For the objects in categories 'table' and 'sofa', compare distinct-instance totals across the room. Read each answer choice as describing 'table' relative to 'sofa' and select the correct one.",
    "timestamps": [
      0.0,
      2.5,
      4.9,
      7.4,
      9.9,
      12.3,
      14.8,
      17.3,
      19.7,
      22.2,
      24.7,
      27.1,
      29.6,
      32.1,
      34.5,
      37.0,
      39.5,
      42.0,
      44.4,
      46.9,
      49.4,
      51.8,
      54.3,
      56.8,
      59.2,
      61.7,
      64.2,
      66.6,
      69.1,
      71.6,
      74.0,
      76.5
    ],
    "total_num_frames": 766
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are more table instances than sofa instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 20. fbp_relcnt2_04df9038518336f10586cec9

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-f59a6d437dc45014dc8b888cdcaa7d5b5621b7f44315ff81c242089fc0ba7e46",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/45662796",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/45662796.npz": "da73410bba99bbd9f3a97326699f47b508b11592b6749c1418388f3aaa943344",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "45662796.npz",
    "raster_sha256": "da73410bba99bbd9f3a97326699f47b508b11592b6749c1418388f3aaa943344",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "2",
      "count_a": 1,
      "count_b": 2,
      "ids_a": [
        6
      ],
      "ids_b": [
        0,
        1
      ],
      "orientation_use_cap": 2,
      "relation": "fewer",
      "room": "arkitscenes/venue468509",
      "scene_use_cap": 24,
      "source_qid": "b12ct_557bf41ac994a0f95233cbce",
      "source_row_sha256": "40edb6448673f531a52e39d78def166cc7b9060ecdfd41f4827e1b829c737f5e",
      "source_use_cap": 8,
      "template_id": 19,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_04df9038518336f10586cec9",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v75bb34e37ced",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      19,
      38,
      57,
      76,
      95,
      114,
      133,
      152,
      171,
      190,
      209,
      228,
      247,
      266,
      285,
      303,
      322,
      341,
      360,
      379,
      398,
      417,
      436,
      455,
      474,
      493,
      512,
      531,
      550,
      569,
      588
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e9/e9c8d4bc1494b2cf0488de1b774e80f1378a70a45724a9174208db042065e0cb.png",
        "sha256": "e9c8d4bc1494b2cf0488de1b774e80f1378a70a45724a9174208db042065e0cb"
      },
      {
        "path": "/data2/k6tk/be/bed4375d505e15330cd72ea76bf60bf1d21eaf0389211113157c82676faa2435.png",
        "sha256": "bed4375d505e15330cd72ea76bf60bf1d21eaf0389211113157c82676faa2435"
      },
      {
        "path": "/data2/k6tk/c7/c7c093293e887737c619541fca4ac2ea6e49348cc0da31abd65ec32f22c6aafd.png",
        "sha256": "c7c093293e887737c619541fca4ac2ea6e49348cc0da31abd65ec32f22c6aafd"
      },
      {
        "path": "/data2/k6tk/c6/c674e0b89c85ca8ca5331f4a3a2bf9e3154536e5248cdbb1d5f11d824bb3f4b4.png",
        "sha256": "c674e0b89c85ca8ca5331f4a3a2bf9e3154536e5248cdbb1d5f11d824bb3f4b4"
      },
      {
        "path": "/data2/k6tk/d2/d226a30466e8d4c90c7f6a895101aa3758241e21d1226d861f7b56817c7b10f6.png",
        "sha256": "d226a30466e8d4c90c7f6a895101aa3758241e21d1226d861f7b56817c7b10f6"
      },
      {
        "path": "/data2/k6tk/4c/4c4b54a6e3300e3c05d911eab19d5dbb9b51fd699370b10dbc742dbd0cf933ed.png",
        "sha256": "4c4b54a6e3300e3c05d911eab19d5dbb9b51fd699370b10dbc742dbd0cf933ed"
      },
      {
        "path": "/data2/k6tk/6b/6ba1a3bc2b8636e9548ba975a8ef0388bf93ecdcff9a02953a204d5bc7cbb39b.png",
        "sha256": "6ba1a3bc2b8636e9548ba975a8ef0388bf93ecdcff9a02953a204d5bc7cbb39b"
      },
      {
        "path": "/data2/k6tk/2f/2f116ded7c218c9d4826772e453d879cafcd41febd2a454d65f4b504f522b452.png",
        "sha256": "2f116ded7c218c9d4826772e453d879cafcd41febd2a454d65f4b504f522b452"
      },
      {
        "path": "/data2/k6tk/75/75d64751305f1516ee81ed47b7b8a9bc4cac19356162c977093dc6f3f3a0b140.png",
        "sha256": "75d64751305f1516ee81ed47b7b8a9bc4cac19356162c977093dc6f3f3a0b140"
      },
      {
        "path": "/data2/k6tk/ca/ca77abcb3de20b775c3789b5760c5bda1848263d275d66c2a659d1094d21dcba.png",
        "sha256": "ca77abcb3de20b775c3789b5760c5bda1848263d275d66c2a659d1094d21dcba"
      },
      {
        "path": "/data2/k6tk/65/657479946fa0f08bbdb2792d2c709382a2162ca0523bf2dea62093f340b06871.png",
        "sha256": "657479946fa0f08bbdb2792d2c709382a2162ca0523bf2dea62093f340b06871"
      },
      {
        "path": "/data2/k6tk/75/7517eacda4c6e1c1c0cee53b2be17155cbd4b245964a2c1f58672cb11a7980d3.png",
        "sha256": "7517eacda4c6e1c1c0cee53b2be17155cbd4b245964a2c1f58672cb11a7980d3"
      },
      {
        "path": "/data2/k6tk/12/126d7ca1a05bdcae578b92ab545369135c86e0b743024a848752776fe026c44b.png",
        "sha256": "126d7ca1a05bdcae578b92ab545369135c86e0b743024a848752776fe026c44b"
      },
      {
        "path": "/data2/k6tk/e6/e6779081b98b67f85cdd4cd8ece9c2147971d92f97fc44cf523c34a6155baf5a.png",
        "sha256": "e6779081b98b67f85cdd4cd8ece9c2147971d92f97fc44cf523c34a6155baf5a"
      },
      {
        "path": "/data2/k6tk/9b/9b0f3450e663c685c4b4c15032a927749379136fd8dff1cad68bc402d29439ce.png",
        "sha256": "9b0f3450e663c685c4b4c15032a927749379136fd8dff1cad68bc402d29439ce"
      },
      {
        "path": "/data2/k6tk/a4/a4dfa3fd908de2021df7810d3507b71a4a29329ae891b3769281b9598a83ab94.png",
        "sha256": "a4dfa3fd908de2021df7810d3507b71a4a29329ae891b3769281b9598a83ab94"
      },
      {
        "path": "/data2/k6tk/b3/b307cfc3f74ca0e16466aabe92cfdee3d20079fb6dc05e95194522515010899d.png",
        "sha256": "b307cfc3f74ca0e16466aabe92cfdee3d20079fb6dc05e95194522515010899d"
      },
      {
        "path": "/data2/k6tk/5c/5cd47b3659f28a984bb1c82e2dbe402d7c7fa1654ac793efcdbe648c6463ecf6.png",
        "sha256": "5cd47b3659f28a984bb1c82e2dbe402d7c7fa1654ac793efcdbe648c6463ecf6"
      },
      {
        "path": "/data2/k6tk/55/555e8f850601de50cb3a59e5b7751e3cb667c8b17f975a707617d405eb9c19ed.png",
        "sha256": "555e8f850601de50cb3a59e5b7751e3cb667c8b17f975a707617d405eb9c19ed"
      },
      {
        "path": "/data2/k6tk/82/824bb765734d3da499d73462a7b78c9a19e393dda717e61cba68ad03080b0a1d.png",
        "sha256": "824bb765734d3da499d73462a7b78c9a19e393dda717e61cba68ad03080b0a1d"
      },
      {
        "path": "/data2/k6tk/01/0168d2e8a755b27ee8c455d5aede7da0ca226d9a01cb87e907a4df5547c65cd0.png",
        "sha256": "0168d2e8a755b27ee8c455d5aede7da0ca226d9a01cb87e907a4df5547c65cd0"
      },
      {
        "path": "/data2/k6tk/1f/1f6e5371af2d2fd0e0040a7261ed12c7dce306caee4586e66634e7a6e69dbcf2.png",
        "sha256": "1f6e5371af2d2fd0e0040a7261ed12c7dce306caee4586e66634e7a6e69dbcf2"
      },
      {
        "path": "/data2/k6tk/2c/2cceb5e7a82d6d7a469ddc27360de9ad0b049aaa00a9e3b9e2ef9791e739d3a0.png",
        "sha256": "2cceb5e7a82d6d7a469ddc27360de9ad0b049aaa00a9e3b9e2ef9791e739d3a0"
      },
      {
        "path": "/data2/k6tk/53/5300c14b07b66ebf1f936410e86d50428130c6c8c6b6a8acca7ab126c67325cd.png",
        "sha256": "5300c14b07b66ebf1f936410e86d50428130c6c8c6b6a8acca7ab126c67325cd"
      },
      {
        "path": "/data2/k6tk/82/8280fdb72b3dc6a4373b5e0afcb524d8f2dde43b84b79f3a852bee16c5cd47b8.png",
        "sha256": "8280fdb72b3dc6a4373b5e0afcb524d8f2dde43b84b79f3a852bee16c5cd47b8"
      },
      {
        "path": "/data2/k6tk/4c/4cb9e6f1bb4e73a0c40ab4ff3c5bc8f0babf2641ce7be40e9f75fe2f18ee6a27.png",
        "sha256": "4cb9e6f1bb4e73a0c40ab4ff3c5bc8f0babf2641ce7be40e9f75fe2f18ee6a27"
      },
      {
        "path": "/data2/k6tk/25/259339642e5df12dd08e2c96dfa4ec6f1af1453f2a4f6632272f70ccd5f8797e.png",
        "sha256": "259339642e5df12dd08e2c96dfa4ec6f1af1453f2a4f6632272f70ccd5f8797e"
      },
      {
        "path": "/data2/k6tk/0b/0bfab6ba0c98db6343b23f748fb02555734e2da6819a033e0e160775d80214a8.png",
        "sha256": "0bfab6ba0c98db6343b23f748fb02555734e2da6819a033e0e160775d80214a8"
      },
      {
        "path": "/data2/k6tk/20/20ff8bc534b64f2df5f979c7a58e7493d79d0950e5b406dc5ddd1475c335e5c2.png",
        "sha256": "20ff8bc534b64f2df5f979c7a58e7493d79d0950e5b406dc5ddd1475c335e5c2"
      },
      {
        "path": "/data2/k6tk/d2/d205aaec127a547ead80767ea948c3dcf5c39e2ca5c09cbb3abd67c70748cdb1.png",
        "sha256": "d205aaec127a547ead80767ea948c3dcf5c39e2ca5c09cbb3abd67c70748cdb1"
      },
      {
        "path": "/data2/k6tk/ae/ae97d5dd051311e5d7c3e310a8e363ac09a5944f052cf28f6cc525587b321a7c.png",
        "sha256": "ae97d5dd051311e5d7c3e310a8e363ac09a5944f052cf28f6cc525587b321a7c"
      },
      {
        "path": "/data2/k6tk/54/54b49edc1db7387b6eca3f8ece01a6c7f12bcb5b583c351cf3daaac07d5d9f56.png",
        "sha256": "54b49edc1db7387b6eca3f8ece01a6c7f12bcb5b583c351cf3daaac07d5d9f56"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Work out separate object totals for 'table' and 'sofa' from the scene. With the 'sofa' total as the reference, which answer describes the 'table' total?",
    "timestamps": [
      0.0,
      1.9,
      3.8,
      5.7,
      7.6,
      9.5,
      11.4,
      13.3,
      15.2,
      17.1,
      19.0,
      20.9,
      22.8,
      24.7,
      26.6,
      28.5,
      30.3,
      32.2,
      34.1,
      36.0,
      37.9,
      39.8,
      41.7,
      43.6,
      45.5,
      47.4,
      49.3,
      51.2,
      53.1,
      55.0,
      56.9,
      58.8
    ],
    "total_num_frames": 589
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are fewer table instances than sofa instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 21. fbp_relcnt2_83af74df559a5f809d926ddb

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-d6dff36f68a2bf7284fe1e0692986365b73f941a7addc070cf3cb11107789a0a",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42898379",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42898379.npz": "d9bb821b8ff67933a7ade9958d2ce1e8a37b0ec36c1aff6db9df1f7d27b3670d",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42898379.npz",
    "raster_sha256": "d9bb821b8ff67933a7ade9958d2ce1e8a37b0ec36c1aff6db9df1f7d27b3670d",
    "relative_count": {
      "a": "sofa",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        0
      ],
      "ids_b": [
        4
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue423979",
      "scene_use_cap": 24,
      "source_qid": "b12ct_246b1a189285867d1236a0dd",
      "source_row_sha256": "059a86064f83cf112937ad2483f4739025d5e3cf0484d5b5759d2a8ad2883f99",
      "source_use_cap": 8,
      "template_id": 0,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_83af74df559a5f809d926ddb",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vd4a76ef18f82",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      21,
      43,
      64,
      85,
      107,
      128,
      149,
      171,
      192,
      213,
      235,
      256,
      277,
      299,
      320,
      341,
      362,
      384,
      405,
      426,
      448,
      469,
      490,
      512,
      533,
      554,
      576,
      597,
      618,
      640,
      661
    ],
    "frames": [
      {
        "path": "/data2/k6tk/0a/0aac2c5c4465ebcdb72099c84caa3c470e18c4651de95b7b5c02161dd6e8f6f3.png",
        "sha256": "0aac2c5c4465ebcdb72099c84caa3c470e18c4651de95b7b5c02161dd6e8f6f3"
      },
      {
        "path": "/data2/k6tk/6e/6e84fc95c20ec1270ab497f29c9eb32a5d765c5dbfa54a54520b940d99ba25a1.png",
        "sha256": "6e84fc95c20ec1270ab497f29c9eb32a5d765c5dbfa54a54520b940d99ba25a1"
      },
      {
        "path": "/data2/k6tk/01/0155d3d3df3333932a1a263af49469b0702eb3d7a50a7553c225dfc44369e55a.png",
        "sha256": "0155d3d3df3333932a1a263af49469b0702eb3d7a50a7553c225dfc44369e55a"
      },
      {
        "path": "/data2/k6tk/6a/6a61bbf8ca2707e7a62faa719bf2e13f9b189cbffb7b6e20ff4be2d1dc625aea.png",
        "sha256": "6a61bbf8ca2707e7a62faa719bf2e13f9b189cbffb7b6e20ff4be2d1dc625aea"
      },
      {
        "path": "/data2/k6tk/a9/a91cec571c8d5c0db0ac3b0c11dea18735d69ada55c8f11efd36617e646e84e8.png",
        "sha256": "a91cec571c8d5c0db0ac3b0c11dea18735d69ada55c8f11efd36617e646e84e8"
      },
      {
        "path": "/data2/k6tk/62/628a7ca698b0c919d98af9dd5a3c5989e0ac0da7ab9e045db807c5e69e7acc30.png",
        "sha256": "628a7ca698b0c919d98af9dd5a3c5989e0ac0da7ab9e045db807c5e69e7acc30"
      },
      {
        "path": "/data2/k6tk/5f/5f3f788cef0f92c3c001baac02b468a94d75327e71b0520d601ae84f968e3b67.png",
        "sha256": "5f3f788cef0f92c3c001baac02b468a94d75327e71b0520d601ae84f968e3b67"
      },
      {
        "path": "/data2/k6tk/42/426350cd38639b6d6b083eec1dea68049c9c922cbf44e86509cf8df7a63ff9a1.png",
        "sha256": "426350cd38639b6d6b083eec1dea68049c9c922cbf44e86509cf8df7a63ff9a1"
      },
      {
        "path": "/data2/k6tk/48/48be1fe0c163ad07a64b54f83fdf41cbe2e3a5c318984261d24fc6a87ee27a46.png",
        "sha256": "48be1fe0c163ad07a64b54f83fdf41cbe2e3a5c318984261d24fc6a87ee27a46"
      },
      {
        "path": "/data2/k6tk/bc/bc925ed5b694d982c51cfb952eda0f609a93a9ee780b52aa861acf20dfac441b.png",
        "sha256": "bc925ed5b694d982c51cfb952eda0f609a93a9ee780b52aa861acf20dfac441b"
      },
      {
        "path": "/data2/k6tk/15/15ea4cbf27e122ce801bfada485899d8d8ef576e09e2bcf03a8fc5abdb473c74.png",
        "sha256": "15ea4cbf27e122ce801bfada485899d8d8ef576e09e2bcf03a8fc5abdb473c74"
      },
      {
        "path": "/data2/k6tk/6b/6b3249b9c8322c47eb998b0d21420832b9c6130f516c9aa4a014bfdef29b0658.png",
        "sha256": "6b3249b9c8322c47eb998b0d21420832b9c6130f516c9aa4a014bfdef29b0658"
      },
      {
        "path": "/data2/k6tk/61/61aca11060ab6126321ccdb4de56101da79e5d4e354c28f51dee120caf7d4e98.png",
        "sha256": "61aca11060ab6126321ccdb4de56101da79e5d4e354c28f51dee120caf7d4e98"
      },
      {
        "path": "/data2/k6tk/05/05b71b044697e50920edb3c7819caf8a31b4e7f7e9ecaf5223a4aaa356a48b17.png",
        "sha256": "05b71b044697e50920edb3c7819caf8a31b4e7f7e9ecaf5223a4aaa356a48b17"
      },
      {
        "path": "/data2/k6tk/36/36c60b5fe31b08309539c5a36069e6105e0fdf7f32e2db88de65bf66f017347f.png",
        "sha256": "36c60b5fe31b08309539c5a36069e6105e0fdf7f32e2db88de65bf66f017347f"
      },
      {
        "path": "/data2/k6tk/42/42b6ef4c7f44754469cc18de1063e82f3141fd4d19fc12d2822bdfb6a80145de.png",
        "sha256": "42b6ef4c7f44754469cc18de1063e82f3141fd4d19fc12d2822bdfb6a80145de"
      },
      {
        "path": "/data2/k6tk/ec/ec49dd7fc96e460b54190a20edcb27e5720f8171b329b72f034aebc2549cd274.png",
        "sha256": "ec49dd7fc96e460b54190a20edcb27e5720f8171b329b72f034aebc2549cd274"
      },
      {
        "path": "/data2/k6tk/47/477056f1ca8756bdf1be1a9abb03c6e1d51c02744de796b6cd4b3ef7c4fc7cb3.png",
        "sha256": "477056f1ca8756bdf1be1a9abb03c6e1d51c02744de796b6cd4b3ef7c4fc7cb3"
      },
      {
        "path": "/data2/k6tk/88/8836ed515b0ea9809193ef8b9757913c175e5ada0d238da336dfbc6d8598d965.png",
        "sha256": "8836ed515b0ea9809193ef8b9757913c175e5ada0d238da336dfbc6d8598d965"
      },
      {
        "path": "/data2/k6tk/47/472df7b76eeffe03970f7b6432a0db1b649c51e22fdd00950c6d186f6ef01139.png",
        "sha256": "472df7b76eeffe03970f7b6432a0db1b649c51e22fdd00950c6d186f6ef01139"
      },
      {
        "path": "/data2/k6tk/82/82846bd1175524e344625abb8e58963301f8759d75fde59ad227ec65dad3ba87.png",
        "sha256": "82846bd1175524e344625abb8e58963301f8759d75fde59ad227ec65dad3ba87"
      },
      {
        "path": "/data2/k6tk/ff/ffa7996d25d2715b8127d93ba950520df6903225bb6478787c47d2ee025614de.png",
        "sha256": "ffa7996d25d2715b8127d93ba950520df6903225bb6478787c47d2ee025614de"
      },
      {
        "path": "/data2/k6tk/22/221933d5767df5f8aaa8ffdbc7d8c1123b75c09f2ae11ed1a9af9a04255de324.png",
        "sha256": "221933d5767df5f8aaa8ffdbc7d8c1123b75c09f2ae11ed1a9af9a04255de324"
      },
      {
        "path": "/data2/k6tk/dd/ddaabc0e46c756b1fe65fd93110e473c2c6b5bfa0ab7cff4af4f3726aaa752fa.png",
        "sha256": "ddaabc0e46c756b1fe65fd93110e473c2c6b5bfa0ab7cff4af4f3726aaa752fa"
      },
      {
        "path": "/data2/k6tk/bd/bdb38649a8189378b334598d246a46bee739bc1363369451c2f6e1ba4f3df762.png",
        "sha256": "bdb38649a8189378b334598d246a46bee739bc1363369451c2f6e1ba4f3df762"
      },
      {
        "path": "/data2/k6tk/1a/1aacb97d7b39667ec6f58090664c7c55ddbaa8af9f460ae6a881059fec1f4e2f.png",
        "sha256": "1aacb97d7b39667ec6f58090664c7c55ddbaa8af9f460ae6a881059fec1f4e2f"
      },
      {
        "path": "/data2/k6tk/03/030411db024e9ea67f5f648c268b1ff8d75e1a7378414ddd0f6d35784d975582.png",
        "sha256": "030411db024e9ea67f5f648c268b1ff8d75e1a7378414ddd0f6d35784d975582"
      },
      {
        "path": "/data2/k6tk/2c/2c515795b40e08bab4de9a4373aeade7a5c4df8fd6b8e3a26e58b13c66615b75.png",
        "sha256": "2c515795b40e08bab4de9a4373aeade7a5c4df8fd6b8e3a26e58b13c66615b75"
      },
      {
        "path": "/data2/k6tk/55/55a39051070cbe4339a2c63613b3ed2e47afa3b962a8493511cc0b0c7458538d.png",
        "sha256": "55a39051070cbe4339a2c63613b3ed2e47afa3b962a8493511cc0b0c7458538d"
      },
      {
        "path": "/data2/k6tk/99/992b0f34a82c726740aca90ba8a788f143a9863b4f3939bcf2de17d62b1a4928.png",
        "sha256": "992b0f34a82c726740aca90ba8a788f143a9863b4f3939bcf2de17d62b1a4928"
      },
      {
        "path": "/data2/k6tk/c6/c614d68d126810f96a0979161657c5151647c49499418af99153959179219da3.png",
        "sha256": "c614d68d126810f96a0979161657c5151647c49499418af99153959179219da3"
      },
      {
        "path": "/data2/k6tk/6c/6caf5df78446503d22418b8a925ba93a002932b8669502d92573bf78557432db.png",
        "sha256": "6caf5df78446503d22418b8a925ba93a002932b8669502d92573bf78557432db"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Count the separate objects in the 'sofa' and 'tv' categories. For 'sofa' relative to 'tv', which choice describes the result?",
    "timestamps": [
      0.0,
      2.1,
      4.3,
      6.4,
      8.5,
      10.7,
      12.8,
      14.9,
      17.1,
      19.2,
      21.3,
      23.5,
      25.6,
      27.7,
      29.9,
      32.0,
      34.1,
      36.2,
      38.4,
      40.5,
      42.6,
      44.8,
      46.9,
      49.0,
      51.2,
      53.3,
      55.4,
      57.6,
      59.7,
      61.8,
      64.0,
      66.1
    ],
    "total_num_frames": 662
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many sofa instances as tv instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 22. fbp_relcnt2_af92d2e2f21c1e46d712efae

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-fb1ec9f2638a708c6907f7cc0f42ac88a1a3cae546fc4a828104664389f218b4",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47115358",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47115358.npz": "46c5550587fe18de40e78c5305902d4346ddbaf36c2168dc34cc209bd5412ced",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47115358.npz",
    "raster_sha256": "46c5550587fe18de40e78c5305902d4346ddbaf36c2168dc34cc209bd5412ced",
    "relative_count": {
      "a": "tv",
      "b": "chair",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        6
      ],
      "ids_b": [
        9
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue470443",
      "scene_use_cap": 24,
      "source_qid": "b12ct_4ad4c8b7b949a86c21ec393d",
      "source_row_sha256": "a0a9a8196488111f64a56e738238a00b2d4b8ee56221e4dd23249ae4316f753d",
      "source_use_cap": 8,
      "template_id": 1,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_af92d2e2f21c1e46d712efae",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v52e9f5f2b91d",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      53,
      105,
      158,
      211,
      264,
      316,
      369,
      422,
      475,
      527,
      580,
      633,
      686,
      738,
      791,
      844,
      897,
      949,
      1002,
      1055,
      1108,
      1160,
      1213,
      1266,
      1319,
      1371,
      1424,
      1477,
      1530,
      1582,
      1635
    ],
    "frames": [
      {
        "path": "/data2/k6tk/ee/ee58d687c4827443693ea3ed667bf4de8db88824c70c4922d8f0feb60622b856.png",
        "sha256": "ee58d687c4827443693ea3ed667bf4de8db88824c70c4922d8f0feb60622b856"
      },
      {
        "path": "/data2/k6tk/cb/cb35bf323038da98c36a63d8fc7a95127f0787a879eca3c6a6229d702318b24e.png",
        "sha256": "cb35bf323038da98c36a63d8fc7a95127f0787a879eca3c6a6229d702318b24e"
      },
      {
        "path": "/data2/k6tk/68/6855ea0145c3ec92d9b55dd82970a3e2b3c662c557180835e8f2695c540aa99b.png",
        "sha256": "6855ea0145c3ec92d9b55dd82970a3e2b3c662c557180835e8f2695c540aa99b"
      },
      {
        "path": "/data2/k6tk/80/8085c9d12395e48a3390aee3d849cf569b3782991d42a2313427803bf2cd7384.png",
        "sha256": "8085c9d12395e48a3390aee3d849cf569b3782991d42a2313427803bf2cd7384"
      },
      {
        "path": "/data2/k6tk/bb/bb35de914a885070180e4b6fa8f1f88168d6950f715a4ff66f7133c273653e75.png",
        "sha256": "bb35de914a885070180e4b6fa8f1f88168d6950f715a4ff66f7133c273653e75"
      },
      {
        "path": "/data2/k6tk/fe/fe8b0131dfe658e095d71a38e241fb9bcff484233e5a30cbcf99d7d0914d0795.png",
        "sha256": "fe8b0131dfe658e095d71a38e241fb9bcff484233e5a30cbcf99d7d0914d0795"
      },
      {
        "path": "/data2/k6tk/93/93de7c4bcdf0cdd5cebac4eb0568644dd5730808e6aebd1c63cda19d661da3a7.png",
        "sha256": "93de7c4bcdf0cdd5cebac4eb0568644dd5730808e6aebd1c63cda19d661da3a7"
      },
      {
        "path": "/data2/k6tk/07/076f935217bc1c6c6ef93ff2b7096829da7f924874e8d588580431e414eb75cc.png",
        "sha256": "076f935217bc1c6c6ef93ff2b7096829da7f924874e8d588580431e414eb75cc"
      },
      {
        "path": "/data2/k6tk/29/2916c6bcd9f5614d5266cd9c976ddd192a1c09c64db29768c56a431f5a7f4b7d.png",
        "sha256": "2916c6bcd9f5614d5266cd9c976ddd192a1c09c64db29768c56a431f5a7f4b7d"
      },
      {
        "path": "/data2/k6tk/36/362ace9b889bafaa71cfde0b19a3bc9da985181c57d3f5e8968fc80639bc70e5.png",
        "sha256": "362ace9b889bafaa71cfde0b19a3bc9da985181c57d3f5e8968fc80639bc70e5"
      },
      {
        "path": "/data2/k6tk/26/2690c55d9238974411f0e0b463d3032f9cdcac03000feacb8c1f264349b5843e.png",
        "sha256": "2690c55d9238974411f0e0b463d3032f9cdcac03000feacb8c1f264349b5843e"
      },
      {
        "path": "/data2/k6tk/85/854e223042da57e24611dc0a29e8dfe74150d863153b82131153aef71c563242.png",
        "sha256": "854e223042da57e24611dc0a29e8dfe74150d863153b82131153aef71c563242"
      },
      {
        "path": "/data2/k6tk/53/530ca5a19ea3f92c2be1c3abcd9d2aba3513480afa00e6234c88cc0a3f4277b1.png",
        "sha256": "530ca5a19ea3f92c2be1c3abcd9d2aba3513480afa00e6234c88cc0a3f4277b1"
      },
      {
        "path": "/data2/k6tk/02/02ad0c451eeaca931f33db31e955e2435345df52de0ed1a63172eb3da7c49db7.png",
        "sha256": "02ad0c451eeaca931f33db31e955e2435345df52de0ed1a63172eb3da7c49db7"
      },
      {
        "path": "/data2/k6tk/34/346b482f540344c8fd807ecc03f6c3319a12a00e4241bd18fa51eccaee7a4d1e.png",
        "sha256": "346b482f540344c8fd807ecc03f6c3319a12a00e4241bd18fa51eccaee7a4d1e"
      },
      {
        "path": "/data2/k6tk/a8/a8b91b165d38bf952268b1e1b5029a0023a6edcfdca2b43e5a04e3e9bef74a28.png",
        "sha256": "a8b91b165d38bf952268b1e1b5029a0023a6edcfdca2b43e5a04e3e9bef74a28"
      },
      {
        "path": "/data2/k6tk/a2/a24a645b697383c3f1be29c29b870068943a3b25d31173f0d40049bab0362b3b.png",
        "sha256": "a24a645b697383c3f1be29c29b870068943a3b25d31173f0d40049bab0362b3b"
      },
      {
        "path": "/data2/k6tk/b6/b685b4831d65b73cf5500e84ee2e5aa0bb1c108c162823c24fb0091e8755c5df.png",
        "sha256": "b685b4831d65b73cf5500e84ee2e5aa0bb1c108c162823c24fb0091e8755c5df"
      },
      {
        "path": "/data2/k6tk/da/da9230004b3bdc44e0310fc5d9112a5daaa934b9bf6183cff1e010e93c1f5acf.png",
        "sha256": "da9230004b3bdc44e0310fc5d9112a5daaa934b9bf6183cff1e010e93c1f5acf"
      },
      {
        "path": "/data2/k6tk/30/30025a8aa7dceab00e44986bfd6f525bad4bbdf415b70db129216581c412e62e.png",
        "sha256": "30025a8aa7dceab00e44986bfd6f525bad4bbdf415b70db129216581c412e62e"
      },
      {
        "path": "/data2/k6tk/3e/3e41827d4f8416b8c2660880d4bd5969450d6e3f9681079fa432b51e59f3ab13.png",
        "sha256": "3e41827d4f8416b8c2660880d4bd5969450d6e3f9681079fa432b51e59f3ab13"
      },
      {
        "path": "/data2/k6tk/bd/bdfdda9d36e99a8ec39b731fbbe7a36de32ccbf2a8eb85b5acbdbe3bf0e23e2e.png",
        "sha256": "bdfdda9d36e99a8ec39b731fbbe7a36de32ccbf2a8eb85b5acbdbe3bf0e23e2e"
      },
      {
        "path": "/data2/k6tk/92/92b843e6e0cd34eb8cbb6fff24a46eaf8bab389b3c83089dd31d4355be7f0c6e.png",
        "sha256": "92b843e6e0cd34eb8cbb6fff24a46eaf8bab389b3c83089dd31d4355be7f0c6e"
      },
      {
        "path": "/data2/k6tk/08/0834a0b29639061b84825603d5e2619f3a6f544a0f826aebedd7006d124c1288.png",
        "sha256": "0834a0b29639061b84825603d5e2619f3a6f544a0f826aebedd7006d124c1288"
      },
      {
        "path": "/data2/k6tk/d7/d742bb8d2b604063592d71a6de9bd59b290d601c6281895b552688cb90249e95.png",
        "sha256": "d742bb8d2b604063592d71a6de9bd59b290d601c6281895b552688cb90249e95"
      },
      {
        "path": "/data2/k6tk/80/80d81c753bc937c8ef7bea268642a48c0bf8e9edd05670a7769bc56a5f80b66f.png",
        "sha256": "80d81c753bc937c8ef7bea268642a48c0bf8e9edd05670a7769bc56a5f80b66f"
      },
      {
        "path": "/data2/k6tk/1d/1dc18f48d8bbd97e79364c0937bc18d10369bda2ef8b40a118990415e78ecc84.png",
        "sha256": "1dc18f48d8bbd97e79364c0937bc18d10369bda2ef8b40a118990415e78ecc84"
      },
      {
        "path": "/data2/k6tk/bf/bf5efbd9d180453a4a977f3039ef50786468a69073303a99a991b220395ea6f8.png",
        "sha256": "bf5efbd9d180453a4a977f3039ef50786468a69073303a99a991b220395ea6f8"
      },
      {
        "path": "/data2/k6tk/f6/f6b383e1d692023ca9de850cf22565786cdf11ae145915f1673f81f972d19b10.png",
        "sha256": "f6b383e1d692023ca9de850cf22565786cdf11ae145915f1673f81f972d19b10"
      },
      {
        "path": "/data2/k6tk/f5/f519644b77b6e9fdbff64b55f9a2c68fbcdc132fef8e5c7faea4dff134503b3d.png",
        "sha256": "f519644b77b6e9fdbff64b55f9a2c68fbcdc132fef8e5c7faea4dff134503b3d"
      },
      {
        "path": "/data2/k6tk/b7/b7d78a98e0ce9daea1b6053ecc8064c1f6636259e05b9233a37fe3d9bd19f23d.png",
        "sha256": "b7d78a98e0ce9daea1b6053ecc8064c1f6636259e05b9233a37fe3d9bd19f23d"
      },
      {
        "path": "/data2/k6tk/fe/feb1f4fb5bfc133481499b7d7936737c5a660f36863982fcdf89a2e32e015a1e.png",
        "sha256": "feb1f4fb5bfc133481499b7d7936737c5a660f36863982fcdf89a2e32e015a1e"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Consider the room's 'tv' objects as one group and its 'chair' objects as another. Which comparison describes the size of the first group?",
    "timestamps": [
      0.0,
      5.3,
      10.5,
      15.8,
      21.1,
      26.4,
      31.6,
      36.9,
      42.2,
      47.5,
      52.7,
      58.0,
      63.3,
      68.6,
      73.8,
      79.1,
      84.4,
      89.7,
      94.9,
      100.2,
      105.5,
      110.8,
      116.0,
      121.3,
      126.6,
      131.9,
      137.1,
      142.4,
      147.7,
      153.0,
      158.2,
      163.5
    ],
    "total_num_frames": 1636
  },
  "target": "<think>\nlocate the distinct instances of tv; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many tv instances as chair instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 23. fbp_relcnt2_9de352139800cc5129caed1d

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-0af2b8c4a99fbbafa2a2f52d35c74f866dde16c52bfd315d2a9ba5ee0617650e",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/43828460",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/43828460.npz": "e328e00cfcd0558acf13266c9382d81ea38d6b20455b87484b627742a0ba6f6b",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "43828460.npz",
    "raster_sha256": "e328e00cfcd0558acf13266c9382d81ea38d6b20455b87484b627742a0ba6f6b",
    "relative_count": {
      "a": "bed",
      "b": "chair",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        0
      ],
      "ids_b": [
        3
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue437711",
      "scene_use_cap": 24,
      "source_qid": "b12ct_37249381d491a1e9e733b8bf",
      "source_row_sha256": "4c8a0d8bf971e2873d7bebab3d31fa8595e47d9632f71923f39b3ca5650eb609",
      "source_use_cap": 8,
      "template_id": 2,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_9de352139800cc5129caed1d",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vde7ff034ca48",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      18,
      35,
      53,
      70,
      88,
      105,
      123,
      140,
      158,
      175,
      193,
      210,
      228,
      245,
      263,
      280,
      298,
      315,
      333,
      350,
      368,
      385,
      403,
      420,
      438,
      455,
      473,
      490,
      508,
      525,
      543
    ],
    "frames": [
      {
        "path": "/data2/k6tk/82/8282666a95c70fd96b678486aa54c4e5dc7a436985a6a709439c3b35bfe20f97.png",
        "sha256": "8282666a95c70fd96b678486aa54c4e5dc7a436985a6a709439c3b35bfe20f97"
      },
      {
        "path": "/data2/k6tk/b6/b6f4068db696eb941cd8547ff4cb1d0f2c1486b791e5767b95f05332f1133262.png",
        "sha256": "b6f4068db696eb941cd8547ff4cb1d0f2c1486b791e5767b95f05332f1133262"
      },
      {
        "path": "/data2/k6tk/9f/9f091a8813455cfed2f39ba9a823d68b2772e2b38a2ac9a66388b7a5276c7ec5.png",
        "sha256": "9f091a8813455cfed2f39ba9a823d68b2772e2b38a2ac9a66388b7a5276c7ec5"
      },
      {
        "path": "/data2/k6tk/85/85048a3fb3d287670179a65bfe18df0e03b186cf7b8bcd0f15838e7d43e3efae.png",
        "sha256": "85048a3fb3d287670179a65bfe18df0e03b186cf7b8bcd0f15838e7d43e3efae"
      },
      {
        "path": "/data2/k6tk/03/03d3ca795883eaaeebe031a2214d9d7320859dd95805b6addf354c53a31efa43.png",
        "sha256": "03d3ca795883eaaeebe031a2214d9d7320859dd95805b6addf354c53a31efa43"
      },
      {
        "path": "/data2/k6tk/10/10f86ec1d518f9f56c19443c22e4a02129b814bd38f5b2071059fcc947730468.png",
        "sha256": "10f86ec1d518f9f56c19443c22e4a02129b814bd38f5b2071059fcc947730468"
      },
      {
        "path": "/data2/k6tk/01/01fed84b6e810f113b5e519df5ccc56a454766aed8da76a3b39ffcdcea14cb3e.png",
        "sha256": "01fed84b6e810f113b5e519df5ccc56a454766aed8da76a3b39ffcdcea14cb3e"
      },
      {
        "path": "/data2/k6tk/3b/3b3d653b4099bf4ed990c090b011b9ad23f1574fb339872dd1c46db71fe6cdf2.png",
        "sha256": "3b3d653b4099bf4ed990c090b011b9ad23f1574fb339872dd1c46db71fe6cdf2"
      },
      {
        "path": "/data2/k6tk/93/932bbeac88f15814ec7b6242da27bbfb9b3e01967cfe1932188ceefe8ca7532a.png",
        "sha256": "932bbeac88f15814ec7b6242da27bbfb9b3e01967cfe1932188ceefe8ca7532a"
      },
      {
        "path": "/data2/k6tk/f1/f1e363457c65b9f6863a05bcad730043884482f79d4ae2573b1f681476ff9253.png",
        "sha256": "f1e363457c65b9f6863a05bcad730043884482f79d4ae2573b1f681476ff9253"
      },
      {
        "path": "/data2/k6tk/e0/e05fc7a39f9a9c5f0753c700beab1a1d7db0c0120d13c24fac9753833016f0f4.png",
        "sha256": "e05fc7a39f9a9c5f0753c700beab1a1d7db0c0120d13c24fac9753833016f0f4"
      },
      {
        "path": "/data2/k6tk/ba/ba4cd8e3729fcb2c61a7ef432625db2820f421629e48ad79c8532934c4634f1e.png",
        "sha256": "ba4cd8e3729fcb2c61a7ef432625db2820f421629e48ad79c8532934c4634f1e"
      },
      {
        "path": "/data2/k6tk/88/88af48417e1e8482e2838ef3ac9ffff4e7561a9bacc8ace45701ff22c71c7a8c.png",
        "sha256": "88af48417e1e8482e2838ef3ac9ffff4e7561a9bacc8ace45701ff22c71c7a8c"
      },
      {
        "path": "/data2/k6tk/7f/7f467ce5022b90573503b332f061d06a48a132bcaebb693be44c3eab3b31d4a3.png",
        "sha256": "7f467ce5022b90573503b332f061d06a48a132bcaebb693be44c3eab3b31d4a3"
      },
      {
        "path": "/data2/k6tk/b2/b28cc23988aef58599140112e5013b94e8f54ce18c04f7d0ea8f54c6e7ec4a50.png",
        "sha256": "b28cc23988aef58599140112e5013b94e8f54ce18c04f7d0ea8f54c6e7ec4a50"
      },
      {
        "path": "/data2/k6tk/56/56a31be8c5028622149ab23c9163271421e2d7ea100abd202406ba76e0b8a21d.png",
        "sha256": "56a31be8c5028622149ab23c9163271421e2d7ea100abd202406ba76e0b8a21d"
      },
      {
        "path": "/data2/k6tk/86/86beed17d4ffb49e88526935f2b96718fddcf3c658c4c068736acb432829060b.png",
        "sha256": "86beed17d4ffb49e88526935f2b96718fddcf3c658c4c068736acb432829060b"
      },
      {
        "path": "/data2/k6tk/d0/d03dddfa45e228309ed7dbc24df5931f6b1e955099bbc94f862a810e0e17daf2.png",
        "sha256": "d03dddfa45e228309ed7dbc24df5931f6b1e955099bbc94f862a810e0e17daf2"
      },
      {
        "path": "/data2/k6tk/90/903024c350068c078bae7a63d47231bb2999cae1ec75cc4c10f00336d112d65d.png",
        "sha256": "903024c350068c078bae7a63d47231bb2999cae1ec75cc4c10f00336d112d65d"
      },
      {
        "path": "/data2/k6tk/6c/6c240b8046c80b15ce16e3161c74be2df0cdf4dc7c8d719db06e0bcc15a95edd.png",
        "sha256": "6c240b8046c80b15ce16e3161c74be2df0cdf4dc7c8d719db06e0bcc15a95edd"
      },
      {
        "path": "/data2/k6tk/be/beb7e2a7053ef7d4a652d7ea02304c7dee869b441fbdbc7f319e92d817cfd205.png",
        "sha256": "beb7e2a7053ef7d4a652d7ea02304c7dee869b441fbdbc7f319e92d817cfd205"
      },
      {
        "path": "/data2/k6tk/c9/c938de805036f034a8ed3828c3abcc13993ef192fef5ed60551eb09882dcb071.png",
        "sha256": "c938de805036f034a8ed3828c3abcc13993ef192fef5ed60551eb09882dcb071"
      },
      {
        "path": "/data2/k6tk/6f/6fe2f8c36f526509765b6eb99e60bc3f903857ea0aff263c23e9d0be5517fc8d.png",
        "sha256": "6fe2f8c36f526509765b6eb99e60bc3f903857ea0aff263c23e9d0be5517fc8d"
      },
      {
        "path": "/data2/k6tk/f4/f4f8460771bc4e678816dd432d23512030c0b2417b0256ed02bdb26dc3814ddb.png",
        "sha256": "f4f8460771bc4e678816dd432d23512030c0b2417b0256ed02bdb26dc3814ddb"
      },
      {
        "path": "/data2/k6tk/ff/ffa6be5505fe20fd54e464e73d6f49efba3d2d4bae25108bae59d48248b9fb8b.png",
        "sha256": "ffa6be5505fe20fd54e464e73d6f49efba3d2d4bae25108bae59d48248b9fb8b"
      },
      {
        "path": "/data2/k6tk/aa/aa42e7f3de17fc55a42bde8c420718f8f7889c9c5286b8ebf579addc5db24555.png",
        "sha256": "aa42e7f3de17fc55a42bde8c420718f8f7889c9c5286b8ebf579addc5db24555"
      },
      {
        "path": "/data2/k6tk/8d/8de876357ac995c629095e14f602d24888a6adef5d5c44bdae76337675bf9ece.png",
        "sha256": "8de876357ac995c629095e14f602d24888a6adef5d5c44bdae76337675bf9ece"
      },
      {
        "path": "/data2/k6tk/36/36039f7658b9472fe2bf7491b03506465b283df957569345e9eb294f2954eb62.png",
        "sha256": "36039f7658b9472fe2bf7491b03506465b283df957569345e9eb294f2954eb62"
      },
      {
        "path": "/data2/k6tk/31/312e33d38f6cfa220d834122b93136acac0f0bb93cc2f72a25c8ba06f9397f7f.png",
        "sha256": "312e33d38f6cfa220d834122b93136acac0f0bb93cc2f72a25c8ba06f9397f7f"
      },
      {
        "path": "/data2/k6tk/9c/9cc55b257ddbaeb7e46e6d849513abad2b6b240fc1f583208585a79dd3957ccd.png",
        "sha256": "9cc55b257ddbaeb7e46e6d849513abad2b6b240fc1f583208585a79dd3957ccd"
      },
      {
        "path": "/data2/k6tk/86/86cdf70bdf6abd2955266dac83011e12320996c458475444346359d9686b4e82.png",
        "sha256": "86cdf70bdf6abd2955266dac83011e12320996c458475444346359d9686b4e82"
      },
      {
        "path": "/data2/k6tk/69/69df8b070c25dd51cce1c182f1f174a5631a782677a36a91ccfe5230ecb2589b.png",
        "sha256": "69df8b070c25dd51cce1c182f1f174a5631a782677a36a91ccfe5230ecb2589b"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "Tally distinct instances of 'bed' and then distinct instances of 'chair' across the video. How does the first tally compare with the second?",
    "timestamps": [
      0.0,
      1.8,
      3.5,
      5.3,
      7.0,
      8.8,
      10.5,
      12.3,
      14.0,
      15.8,
      17.5,
      19.3,
      21.0,
      22.8,
      24.5,
      26.3,
      28.0,
      29.8,
      31.5,
      33.3,
      35.0,
      36.8,
      38.5,
      40.3,
      42.0,
      43.8,
      45.5,
      47.3,
      49.0,
      50.8,
      52.5,
      54.3
    ],
    "total_num_frames": 544
  },
  "target": "<think>\nlocate the distinct instances of bed; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many bed instances as chair instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 24. fbp_relcnt2_05b8167de0dc72060b836339

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-02977a8a8473d2d83e49d6f86312a46f0ccfb80c88fa91fffc30d094c4e711bf",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41254656",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41254656.npz": "f4def2559f89b3d24f832f132cd9fee3a6febcf3f4ad3109a0975e1da6583189",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41254656.npz",
    "raster_sha256": "f4def2559f89b3d24f832f132cd9fee3a6febcf3f4ad3109a0975e1da6583189",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        3
      ],
      "ids_b": [
        6
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue383998",
      "scene_use_cap": 24,
      "source_qid": "b12ct_49c31f3508d480fdee42ab3f",
      "source_row_sha256": "2a572c73de56efdb1aab448bf83e85269f9e31f7f48815febf4709d10d9182ca",
      "source_use_cap": 8,
      "template_id": 3,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_05b8167de0dc72060b836339",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v6037791cc7d6",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      42,
      85,
      127,
      169,
      212,
      254,
      296,
      339,
      381,
      424,
      466,
      508,
      551,
      593,
      635,
      678,
      720,
      762,
      805,
      847,
      889,
      932,
      974,
      1017,
      1059,
      1101,
      1144,
      1186,
      1228,
      1271,
      1313
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f8/f89730fde90226d660cab0151ca385c534b1dc54172433ea4843175207ab650a.png",
        "sha256": "f89730fde90226d660cab0151ca385c534b1dc54172433ea4843175207ab650a"
      },
      {
        "path": "/data2/k6tk/09/098592df968ed29a370fc577b0edb25d5ff155557fa73180a0cd7d766696ef5d.png",
        "sha256": "098592df968ed29a370fc577b0edb25d5ff155557fa73180a0cd7d766696ef5d"
      },
      {
        "path": "/data2/k6tk/38/385f13835af0af3f0da138bb11640d35a88a9cb49d7d15b8730d796d2d8d400d.png",
        "sha256": "385f13835af0af3f0da138bb11640d35a88a9cb49d7d15b8730d796d2d8d400d"
      },
      {
        "path": "/data2/k6tk/c1/c13d233a1fac31c71de4e9032d29b777ba0bc9ebd48d6a30e64ebb8c9877a960.png",
        "sha256": "c13d233a1fac31c71de4e9032d29b777ba0bc9ebd48d6a30e64ebb8c9877a960"
      },
      {
        "path": "/data2/k6tk/58/58bc86fc653f273eb81532d836a9d079730d4ec5fc5001580fdc88914459188b.png",
        "sha256": "58bc86fc653f273eb81532d836a9d079730d4ec5fc5001580fdc88914459188b"
      },
      {
        "path": "/data2/k6tk/54/54feb17714de02466a1b621af08ec14737adc9720d2c021b6f56f6c3ab103ba4.png",
        "sha256": "54feb17714de02466a1b621af08ec14737adc9720d2c021b6f56f6c3ab103ba4"
      },
      {
        "path": "/data2/k6tk/8d/8d5ec044b6199c4d656624a0b420c047480d4280d93494087319bad78a41773b.png",
        "sha256": "8d5ec044b6199c4d656624a0b420c047480d4280d93494087319bad78a41773b"
      },
      {
        "path": "/data2/k6tk/22/222735c809e8b00625687f62dac0f23105018024d0e0f43cea8b8e6e49729e36.png",
        "sha256": "222735c809e8b00625687f62dac0f23105018024d0e0f43cea8b8e6e49729e36"
      },
      {
        "path": "/data2/k6tk/b2/b2535401df0db63283f9284bc9540427ec023057e1b26f7fea896f336430b558.png",
        "sha256": "b2535401df0db63283f9284bc9540427ec023057e1b26f7fea896f336430b558"
      },
      {
        "path": "/data2/k6tk/43/43860e3d75229964d282317d898940dca735f0eb97bbde6b6ebfd7e5d251da62.png",
        "sha256": "43860e3d75229964d282317d898940dca735f0eb97bbde6b6ebfd7e5d251da62"
      },
      {
        "path": "/data2/k6tk/44/4431534e52e8869eb03d16ec76af59c6813bb093b1b5f8e43223a59d2ff9377a.png",
        "sha256": "4431534e52e8869eb03d16ec76af59c6813bb093b1b5f8e43223a59d2ff9377a"
      },
      {
        "path": "/data2/k6tk/36/36d77bed6766a3ca2ffcf8fc04ed402af9f9e88fe55be57a4ad1b5dcfad76762.png",
        "sha256": "36d77bed6766a3ca2ffcf8fc04ed402af9f9e88fe55be57a4ad1b5dcfad76762"
      },
      {
        "path": "/data2/k6tk/0d/0dd20dc54d5418b0837eee58f1e4e127464a1946774d744e011310de81381f1b.png",
        "sha256": "0dd20dc54d5418b0837eee58f1e4e127464a1946774d744e011310de81381f1b"
      },
      {
        "path": "/data2/k6tk/50/509b5566346e396726a0bffe76c77eb3c92a31f9f797ca8c529e08a8615e5902.png",
        "sha256": "509b5566346e396726a0bffe76c77eb3c92a31f9f797ca8c529e08a8615e5902"
      },
      {
        "path": "/data2/k6tk/02/0221796a6325d1fec3041454220b7a8b10dabbbe25b9d02346713d124f96ebea.png",
        "sha256": "0221796a6325d1fec3041454220b7a8b10dabbbe25b9d02346713d124f96ebea"
      },
      {
        "path": "/data2/k6tk/5b/5b6c515b83d58d5c02105eba831f29b9589c242fb983adcd05c8bf6ceb7d2ce9.png",
        "sha256": "5b6c515b83d58d5c02105eba831f29b9589c242fb983adcd05c8bf6ceb7d2ce9"
      },
      {
        "path": "/data2/k6tk/cb/cb0b0a9177f57de97854f514f845c9730131866688ada5b218088eb04d165fc9.png",
        "sha256": "cb0b0a9177f57de97854f514f845c9730131866688ada5b218088eb04d165fc9"
      },
      {
        "path": "/data2/k6tk/fa/faddf9e22ac3fc765b61733fc83b2f7eda0bc3e726208df1d25522dd34b2f4f6.png",
        "sha256": "faddf9e22ac3fc765b61733fc83b2f7eda0bc3e726208df1d25522dd34b2f4f6"
      },
      {
        "path": "/data2/k6tk/11/110c8bc1e2c0bbfeb91f69596071ab98f02f0e0db22b8b61b3644bb26d2d5910.png",
        "sha256": "110c8bc1e2c0bbfeb91f69596071ab98f02f0e0db22b8b61b3644bb26d2d5910"
      },
      {
        "path": "/data2/k6tk/33/3362cba13b3f73175f6eb7744dd0980b7734c2f9e7ca128d802feaaf053946f6.png",
        "sha256": "3362cba13b3f73175f6eb7744dd0980b7734c2f9e7ca128d802feaaf053946f6"
      },
      {
        "path": "/data2/k6tk/d9/d9466ad43683f16b1fa85afba2a2d458159d8bfc9e7370e25107b83a0cbd1bb0.png",
        "sha256": "d9466ad43683f16b1fa85afba2a2d458159d8bfc9e7370e25107b83a0cbd1bb0"
      },
      {
        "path": "/data2/k6tk/0b/0b4ea1d017a3693069fbd37f6a9863c0f6c4e0d34f045184bee403a3c0144ef9.png",
        "sha256": "0b4ea1d017a3693069fbd37f6a9863c0f6c4e0d34f045184bee403a3c0144ef9"
      },
      {
        "path": "/data2/k6tk/56/567aca99a002c0dce94c438f01e8a8672d179a4a79a0d33b042cc6be79122504.png",
        "sha256": "567aca99a002c0dce94c438f01e8a8672d179a4a79a0d33b042cc6be79122504"
      },
      {
        "path": "/data2/k6tk/eb/eb9d8369b19d2b992691ac0bd85dac9abf07c06725eaa4b20193811ae1786eac.png",
        "sha256": "eb9d8369b19d2b992691ac0bd85dac9abf07c06725eaa4b20193811ae1786eac"
      },
      {
        "path": "/data2/k6tk/30/30f177d825cbf57fddb79ab0270183dd2703043bea549e3fdcdfd6068ec2bdfa.png",
        "sha256": "30f177d825cbf57fddb79ab0270183dd2703043bea549e3fdcdfd6068ec2bdfa"
      },
      {
        "path": "/data2/k6tk/65/65db038b911bcdbba0a0e2ad38074b8f01e69a39cb7b8f10e008cc1dec41a181.png",
        "sha256": "65db038b911bcdbba0a0e2ad38074b8f01e69a39cb7b8f10e008cc1dec41a181"
      },
      {
        "path": "/data2/k6tk/fa/fa6a7143f600f7f348dedcc5c077fd65e27d2128c685a60033212235e9c8c851.png",
        "sha256": "fa6a7143f600f7f348dedcc5c077fd65e27d2128c685a60033212235e9c8c851"
      },
      {
        "path": "/data2/k6tk/e5/e584daa5b6fbe9365643f420300de68e2cfb19bf4bf69f759fe19ad18fa49b32.png",
        "sha256": "e584daa5b6fbe9365643f420300de68e2cfb19bf4bf69f759fe19ad18fa49b32"
      },
      {
        "path": "/data2/k6tk/14/14d097ff314d505c8629a57fd1f348b5348076bc98394e8c0f19698ba8b2b7c8.png",
        "sha256": "14d097ff314d505c8629a57fd1f348b5348076bc98394e8c0f19698ba8b2b7c8"
      },
      {
        "path": "/data2/k6tk/0a/0a1a764ac52a4230f17d86dcfff2ec60e8ae7917b174d42490565b270b732e1d.png",
        "sha256": "0a1a764ac52a4230f17d86dcfff2ec60e8ae7917b174d42490565b270b732e1d"
      },
      {
        "path": "/data2/k6tk/28/2834a264bbf5a934f2d7350c59255f2e5be2a6dff2f0071452ce8e1c41dd47b0.png",
        "sha256": "2834a264bbf5a934f2d7350c59255f2e5be2a6dff2f0071452ce8e1c41dd47b0"
      },
      {
        "path": "/data2/k6tk/78/7808a374241852288ed2f14e2a5cbcc90f0996890dbdbbd80eec43c6db6781e2.png",
        "sha256": "7808a374241852288ed2f14e2a5cbcc90f0996890dbdbbd80eec43c6db6781e2"
      }
    ],
    "options": [
      "A. equal number",
      "B. fewer",
      "C. more"
    ],
    "question": "Use a separate tally for each category: 'table' followed by 'chair'. Which option correctly compares the first category's total to the second category's total?",
    "timestamps": [
      0.0,
      4.2,
      8.5,
      12.7,
      16.9,
      21.2,
      25.4,
      29.6,
      33.9,
      38.1,
      42.4,
      46.6,
      50.8,
      55.1,
      59.3,
      63.5,
      67.8,
      72.0,
      76.2,
      80.5,
      84.7,
      88.9,
      93.2,
      97.4,
      101.7,
      105.9,
      110.1,
      114.4,
      118.6,
      122.8,
      127.1,
      131.3
    ],
    "total_num_frames": 1314
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many table instances as chair instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 25. fbp_relcnt2_0c89d68f814ac8af9d96297f

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-191d6b421e7ceef39d62eb2c8d2c0eeb0443c21780df02cccade1b157d1fbe91",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/45261675",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/45261675.npz": "aa745d927f2d2c0a3975bd987e9f6a955f7ca6c02f984af3b4013513f82dee38",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "45261675.npz",
    "raster_sha256": "aa745d927f2d2c0a3975bd987e9f6a955f7ca6c02f984af3b4013513f82dee38",
    "relative_count": {
      "a": "table",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        3
      ],
      "ids_b": [
        5
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue468477",
      "scene_use_cap": 24,
      "source_qid": "b12ct_702c45c2f45a64ac16421e67",
      "source_row_sha256": "0aa6fb60cb8f6af8763cf2f430e0e586f7a2596b0ea5ceb991055a81d62b6348",
      "source_use_cap": 8,
      "template_id": 4,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_0c89d68f814ac8af9d96297f",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v7a3c97463c59",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      29,
      59,
      88,
      117,
      146,
      176,
      205,
      234,
      263,
      293,
      322,
      351,
      380,
      410,
      439,
      468,
      497,
      527,
      556,
      585,
      614,
      644,
      673,
      702,
      731,
      761,
      790,
      819,
      848,
      878,
      907
    ],
    "frames": [
      {
        "path": "/data2/k6tk/10/1013a93cf1950b5584eb8b98bf09bf739c1a6b5429c2c221d0a88fc9b598c04f.png",
        "sha256": "1013a93cf1950b5584eb8b98bf09bf739c1a6b5429c2c221d0a88fc9b598c04f"
      },
      {
        "path": "/data2/k6tk/25/251c192e661a5500064df614c2535ca821bd6ee8ecde470da79c0c6860cc0900.png",
        "sha256": "251c192e661a5500064df614c2535ca821bd6ee8ecde470da79c0c6860cc0900"
      },
      {
        "path": "/data2/k6tk/e4/e4f49a689830cb6fe80f24a5c03e061ca2505a527b7fda6f8eb3a20c3d6181b8.png",
        "sha256": "e4f49a689830cb6fe80f24a5c03e061ca2505a527b7fda6f8eb3a20c3d6181b8"
      },
      {
        "path": "/data2/k6tk/e9/e956698789ef936eacb0cbdb30ce64db77a764a12474b622945f69725cd8e1b3.png",
        "sha256": "e956698789ef936eacb0cbdb30ce64db77a764a12474b622945f69725cd8e1b3"
      },
      {
        "path": "/data2/k6tk/5e/5ef020dcfef06fa7966651e29bc59bb17ac80f0cb0eb93d108e052df1e5d97c1.png",
        "sha256": "5ef020dcfef06fa7966651e29bc59bb17ac80f0cb0eb93d108e052df1e5d97c1"
      },
      {
        "path": "/data2/k6tk/24/2414c124fcff96feddc2a1f02f04dd0ce85e04b2d710f2b176e155236ba93b7e.png",
        "sha256": "2414c124fcff96feddc2a1f02f04dd0ce85e04b2d710f2b176e155236ba93b7e"
      },
      {
        "path": "/data2/k6tk/81/81339f187a3699ae4827b9a3aff8c569d90c30ae6e5ae9702b9eb2db2e6cf3f3.png",
        "sha256": "81339f187a3699ae4827b9a3aff8c569d90c30ae6e5ae9702b9eb2db2e6cf3f3"
      },
      {
        "path": "/data2/k6tk/24/246bde6dba51e8344d6162a231f9cb80df9dbb9fbd9b6fe42fe974c27b3de3ae.png",
        "sha256": "246bde6dba51e8344d6162a231f9cb80df9dbb9fbd9b6fe42fe974c27b3de3ae"
      },
      {
        "path": "/data2/k6tk/9e/9ec3072005c6c2ad6fba3e0f28fb19be4132b93acbc5ae7e65c6020927ffad05.png",
        "sha256": "9ec3072005c6c2ad6fba3e0f28fb19be4132b93acbc5ae7e65c6020927ffad05"
      },
      {
        "path": "/data2/k6tk/47/473669f1a803b84e473493ca5324e46e4233317d6bf93889dab5ea81df3fe593.png",
        "sha256": "473669f1a803b84e473493ca5324e46e4233317d6bf93889dab5ea81df3fe593"
      },
      {
        "path": "/data2/k6tk/30/30f8bb7e7a33b6b70e53cfbfd411b3a5758a8ed8ddd285a80bf42c2153d5c9d0.png",
        "sha256": "30f8bb7e7a33b6b70e53cfbfd411b3a5758a8ed8ddd285a80bf42c2153d5c9d0"
      },
      {
        "path": "/data2/k6tk/40/402f562836e5fbfe21c7b7b5d081366632a4cac70b3751d19b775779854fb6e7.png",
        "sha256": "402f562836e5fbfe21c7b7b5d081366632a4cac70b3751d19b775779854fb6e7"
      },
      {
        "path": "/data2/k6tk/6c/6c83b6e95eb7f93a9ea34bc5105436cf03a0b66bf83688a7c97a31c424412c37.png",
        "sha256": "6c83b6e95eb7f93a9ea34bc5105436cf03a0b66bf83688a7c97a31c424412c37"
      },
      {
        "path": "/data2/k6tk/59/596576fc2d2571ce5b7cd6cadd71970624790ffe9c624dfd5a0999257d97cde8.png",
        "sha256": "596576fc2d2571ce5b7cd6cadd71970624790ffe9c624dfd5a0999257d97cde8"
      },
      {
        "path": "/data2/k6tk/14/1464717ac33ea93f13778e540323ede2c75d85aeea63cc2535a44d6abc86efff.png",
        "sha256": "1464717ac33ea93f13778e540323ede2c75d85aeea63cc2535a44d6abc86efff"
      },
      {
        "path": "/data2/k6tk/03/03e0643f2891b6aef12d2c9f81742fae908712c834dfdf1f709ef9879be64adc.png",
        "sha256": "03e0643f2891b6aef12d2c9f81742fae908712c834dfdf1f709ef9879be64adc"
      },
      {
        "path": "/data2/k6tk/9d/9db5cc7a17abd664042dad9e7ce4c432e0e685c9f0c28758563e8c6dc7f9c128.png",
        "sha256": "9db5cc7a17abd664042dad9e7ce4c432e0e685c9f0c28758563e8c6dc7f9c128"
      },
      {
        "path": "/data2/k6tk/53/5352cf22e6086913ea42e6c551b51f6c6638232878bfa1a5686c07f771e2b932.png",
        "sha256": "5352cf22e6086913ea42e6c551b51f6c6638232878bfa1a5686c07f771e2b932"
      },
      {
        "path": "/data2/k6tk/20/20804cef7ac95dbe8939fcf7587896b57297b9403eb85a139b4e65fece25ed34.png",
        "sha256": "20804cef7ac95dbe8939fcf7587896b57297b9403eb85a139b4e65fece25ed34"
      },
      {
        "path": "/data2/k6tk/e3/e33686b8371b50a33246a185c441ce3923038b9199b8af760103c3299c0c792a.png",
        "sha256": "e33686b8371b50a33246a185c441ce3923038b9199b8af760103c3299c0c792a"
      },
      {
        "path": "/data2/k6tk/34/345e1ef24136d3fa3fba362544e510927afaf6623268f2f61242d8279e7044e0.png",
        "sha256": "345e1ef24136d3fa3fba362544e510927afaf6623268f2f61242d8279e7044e0"
      },
      {
        "path": "/data2/k6tk/c7/c7a1e54b4db4b022c42c21c629b4f9ddf05d40a84f9093a1e346be7cab116009.png",
        "sha256": "c7a1e54b4db4b022c42c21c629b4f9ddf05d40a84f9093a1e346be7cab116009"
      },
      {
        "path": "/data2/k6tk/bc/bcf0388415d57a907c81e652aca304489a5a899823b815a50e56d0c45c0e1d37.png",
        "sha256": "bcf0388415d57a907c81e652aca304489a5a899823b815a50e56d0c45c0e1d37"
      },
      {
        "path": "/data2/k6tk/91/91599e360cdddcb553073b3444e021eccd6aaef3825ebf24799a0eed15a72791.png",
        "sha256": "91599e360cdddcb553073b3444e021eccd6aaef3825ebf24799a0eed15a72791"
      },
      {
        "path": "/data2/k6tk/20/20ba7c44c430c47716629339646a89576aeadb803e08f17d4b3067c4a39437a2.png",
        "sha256": "20ba7c44c430c47716629339646a89576aeadb803e08f17d4b3067c4a39437a2"
      },
      {
        "path": "/data2/k6tk/24/24dfbd94433489b7f29cc59b8f23c3ba86caedc290c415b986537c901cc1fa02.png",
        "sha256": "24dfbd94433489b7f29cc59b8f23c3ba86caedc290c415b986537c901cc1fa02"
      },
      {
        "path": "/data2/k6tk/ec/ecfb20a718acc46d9d2e9f6b5ebe5f56efb50090d64a5abf262550836f731240.png",
        "sha256": "ecfb20a718acc46d9d2e9f6b5ebe5f56efb50090d64a5abf262550836f731240"
      },
      {
        "path": "/data2/k6tk/00/00b8354b67d918f86866e67f68906db9533651d7466924fd8ec68e18190f623c.png",
        "sha256": "00b8354b67d918f86866e67f68906db9533651d7466924fd8ec68e18190f623c"
      },
      {
        "path": "/data2/k6tk/b1/b129b7f916979d59531b64ec734aa21bd3ef63f089d2e8f0f6f443f5ca992865.png",
        "sha256": "b129b7f916979d59531b64ec734aa21bd3ef63f089d2e8f0f6f443f5ca992865"
      },
      {
        "path": "/data2/k6tk/86/86c5dfe74589c145aa1565f0662cda07c7652ef4339f27b02887a56c9016b895.png",
        "sha256": "86c5dfe74589c145aa1565f0662cda07c7652ef4339f27b02887a56c9016b895"
      },
      {
        "path": "/data2/k6tk/e9/e9d1bb000445b3c5d4aa41e652b0fdbfa7e2f0a5d94411a321e00bd05607c07f.png",
        "sha256": "e9d1bb000445b3c5d4aa41e652b0fdbfa7e2f0a5d94411a321e00bd05607c07f"
      },
      {
        "path": "/data2/k6tk/94/94924baa2e022243a6ab5587c00106ac4c5a56a889935d9b57da18ee364b7091.png",
        "sha256": "94924baa2e022243a6ab5587c00106ac4c5a56a889935d9b57da18ee364b7091"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Inspect the room for objects belonging to 'table' and 'tv'. After counting each object once, choose the relation of the 'table' count to the 'tv' count.",
    "timestamps": [
      0.0,
      2.9,
      5.9,
      8.8,
      11.7,
      14.6,
      17.6,
      20.5,
      23.4,
      26.3,
      29.3,
      32.2,
      35.1,
      38.0,
      41.0,
      43.9,
      46.8,
      49.7,
      52.7,
      55.6,
      58.5,
      61.4,
      64.4,
      67.3,
      70.2,
      73.1,
      76.1,
      79.0,
      81.9,
      84.8,
      87.8,
      90.7
    ],
    "total_num_frames": 908
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many table instances as tv instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 26. fbp_relcnt2_8ae33053bfc75286cac8c788

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-ad41015e4ae3ef0d916eb67760ca58fa5b7dfe990f07f3c7052854db4e27839c",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42447203",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42447203.npz": "f5947a9f1330bdae767635ba77fa5ea3dfa9136f0652b9488fa547380037e470",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42447203.npz",
    "raster_sha256": "f5947a9f1330bdae767635ba77fa5ea3dfa9136f0652b9488fa547380037e470",
    "relative_count": {
      "a": "tv",
      "b": "chair",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        8
      ],
      "ids_b": [
        6
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue422384",
      "scene_use_cap": 24,
      "source_qid": "b12ct_2ab515223cac6979782ee76f",
      "source_row_sha256": "e3a701fcdfb0ee96be53e6964936c2f4215d5119402c8492fc119245498d71f6",
      "source_use_cap": 8,
      "template_id": 5,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_8ae33053bfc75286cac8c788",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v9cbee26737de",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      25,
      49,
      74,
      99,
      123,
      148,
      173,
      197,
      222,
      246,
      271,
      296,
      320,
      345,
      370,
      394,
      419,
      444,
      468,
      493,
      518,
      542,
      567,
      591,
      616,
      641,
      665,
      690,
      715,
      739,
      764
    ],
    "frames": [
      {
        "path": "/data2/k6tk/f1/f1f46cf5de68580e97544ae1621a6cb7d9eac24b16ad7d4d7cd0c165d41cabe1.png",
        "sha256": "f1f46cf5de68580e97544ae1621a6cb7d9eac24b16ad7d4d7cd0c165d41cabe1"
      },
      {
        "path": "/data2/k6tk/6f/6ff7690f5add242e1faef1e6c1b2427b63a2700ec83a0691171f8e3d12a78dbc.png",
        "sha256": "6ff7690f5add242e1faef1e6c1b2427b63a2700ec83a0691171f8e3d12a78dbc"
      },
      {
        "path": "/data2/k6tk/39/39535d9ba98f4ba9bae182ca4b74aa3f807dd9adb869ce2c2b78ec99f02b3911.png",
        "sha256": "39535d9ba98f4ba9bae182ca4b74aa3f807dd9adb869ce2c2b78ec99f02b3911"
      },
      {
        "path": "/data2/k6tk/c3/c34b46514b14af90e816758326c6df6185a279703b03fb5e3411cce1471bb233.png",
        "sha256": "c34b46514b14af90e816758326c6df6185a279703b03fb5e3411cce1471bb233"
      },
      {
        "path": "/data2/k6tk/d9/d931f40979c2a352fd43642713cd1b854666cc9add33d5c77db261014689fce4.png",
        "sha256": "d931f40979c2a352fd43642713cd1b854666cc9add33d5c77db261014689fce4"
      },
      {
        "path": "/data2/k6tk/ea/ea8a2628363a1d72e3a6c4b47ca1dfaafa3939b24feb7a5df189e89f46ead201.png",
        "sha256": "ea8a2628363a1d72e3a6c4b47ca1dfaafa3939b24feb7a5df189e89f46ead201"
      },
      {
        "path": "/data2/k6tk/4e/4e8ca473d00100bcafecaf80994125fe1727e69995667c9571538279e8b5aff1.png",
        "sha256": "4e8ca473d00100bcafecaf80994125fe1727e69995667c9571538279e8b5aff1"
      },
      {
        "path": "/data2/k6tk/34/34d58b7594ab4d9448419162344f2ed676749bcb6abc1d506fb09a38229ceefc.png",
        "sha256": "34d58b7594ab4d9448419162344f2ed676749bcb6abc1d506fb09a38229ceefc"
      },
      {
        "path": "/data2/k6tk/a5/a5851d5fe5699a5df37c6d45ec8c6a18b2b168045e060f58a131ef25b380d410.png",
        "sha256": "a5851d5fe5699a5df37c6d45ec8c6a18b2b168045e060f58a131ef25b380d410"
      },
      {
        "path": "/data2/k6tk/cb/cb05aa445ab79c834a43531d9fb9051f0adc8e8ea5d1b51bf4b430cf1d76096b.png",
        "sha256": "cb05aa445ab79c834a43531d9fb9051f0adc8e8ea5d1b51bf4b430cf1d76096b"
      },
      {
        "path": "/data2/k6tk/8d/8d3596b5b46bf2d6722aee19d70980f894eb8851acbc0ed773bfdc5f850ea5b4.png",
        "sha256": "8d3596b5b46bf2d6722aee19d70980f894eb8851acbc0ed773bfdc5f850ea5b4"
      },
      {
        "path": "/data2/k6tk/a0/a059496529f0ab143b51de5c6290329a2cdf7b011f69db68069b0416dda0ae14.png",
        "sha256": "a059496529f0ab143b51de5c6290329a2cdf7b011f69db68069b0416dda0ae14"
      },
      {
        "path": "/data2/k6tk/90/9022cca230a06cc9ea99889dfaaad51c59a3ca24d5aac8e019798750f3bd151e.png",
        "sha256": "9022cca230a06cc9ea99889dfaaad51c59a3ca24d5aac8e019798750f3bd151e"
      },
      {
        "path": "/data2/k6tk/8d/8d9643040420ec201dba7dd72c6ef63450e9bbfe8e66d3cabf40f82cbd243963.png",
        "sha256": "8d9643040420ec201dba7dd72c6ef63450e9bbfe8e66d3cabf40f82cbd243963"
      },
      {
        "path": "/data2/k6tk/6a/6a0b9cb2d2ef160c1f5c09656fa595fb429a984715877754479d1b3def5c6d05.png",
        "sha256": "6a0b9cb2d2ef160c1f5c09656fa595fb429a984715877754479d1b3def5c6d05"
      },
      {
        "path": "/data2/k6tk/b9/b9e3a83752997a4ac9cabdeef522fd659616e4dea7b2317a5c0e1e2d944a4c2a.png",
        "sha256": "b9e3a83752997a4ac9cabdeef522fd659616e4dea7b2317a5c0e1e2d944a4c2a"
      },
      {
        "path": "/data2/k6tk/e1/e112ed387eb73406d2e995d662e5038df317cc655a4670061274f57244c6f9e1.png",
        "sha256": "e112ed387eb73406d2e995d662e5038df317cc655a4670061274f57244c6f9e1"
      },
      {
        "path": "/data2/k6tk/bd/bd0d141593b77d8453cd5cdb5a037064bd0bc41c3ac14ee2dabaac1f42bef7d7.png",
        "sha256": "bd0d141593b77d8453cd5cdb5a037064bd0bc41c3ac14ee2dabaac1f42bef7d7"
      },
      {
        "path": "/data2/k6tk/12/120ea3050a330c78027a923bd7eb7253ff710683a045147c1dced49f24d7cd45.png",
        "sha256": "120ea3050a330c78027a923bd7eb7253ff710683a045147c1dced49f24d7cd45"
      },
      {
        "path": "/data2/k6tk/4d/4d8b53f623cfffb1d3fdc5b4b948f253aa1fb53ec2849a4c4ae56f914b03f861.png",
        "sha256": "4d8b53f623cfffb1d3fdc5b4b948f253aa1fb53ec2849a4c4ae56f914b03f861"
      },
      {
        "path": "/data2/k6tk/ac/ac641914ed00dff9e5f25eb526c20c1ac83960ea1790aa6999d50ac2f7d74805.png",
        "sha256": "ac641914ed00dff9e5f25eb526c20c1ac83960ea1790aa6999d50ac2f7d74805"
      },
      {
        "path": "/data2/k6tk/9f/9f7f0f9f6bfa34ddda19013cfa7b87a0a55d5e5bd11efc3c936a90f8f89bdbc6.png",
        "sha256": "9f7f0f9f6bfa34ddda19013cfa7b87a0a55d5e5bd11efc3c936a90f8f89bdbc6"
      },
      {
        "path": "/data2/k6tk/26/26b11f671f65bc57f7ce21f72d8b5252f67303bec3b695dfb1b110fc6bb38d03.png",
        "sha256": "26b11f671f65bc57f7ce21f72d8b5252f67303bec3b695dfb1b110fc6bb38d03"
      },
      {
        "path": "/data2/k6tk/94/949870d4bc05a002572cb2684ae98ac23dee2c8b17d946654691e8ae213c220c.png",
        "sha256": "949870d4bc05a002572cb2684ae98ac23dee2c8b17d946654691e8ae213c220c"
      },
      {
        "path": "/data2/k6tk/1e/1e29bffe96c7949dc96844eaa5a7c9ff97eddc0728e49a0789752882d1283236.png",
        "sha256": "1e29bffe96c7949dc96844eaa5a7c9ff97eddc0728e49a0789752882d1283236"
      },
      {
        "path": "/data2/k6tk/46/468e1c03677681361bc09e3eba4f06f26053ad3ec42810183f5806a1fb9cff7b.png",
        "sha256": "468e1c03677681361bc09e3eba4f06f26053ad3ec42810183f5806a1fb9cff7b"
      },
      {
        "path": "/data2/k6tk/c9/c9aad4c11cc7276392e4a2046842e99663f94f4a564d70152706cf96939b5bb9.png",
        "sha256": "c9aad4c11cc7276392e4a2046842e99663f94f4a564d70152706cf96939b5bb9"
      },
      {
        "path": "/data2/k6tk/82/828208f3909ba7738cbb29739797d3fc44b0bf13b8a66fac5cbe473050a31642.png",
        "sha256": "828208f3909ba7738cbb29739797d3fc44b0bf13b8a66fac5cbe473050a31642"
      },
      {
        "path": "/data2/k6tk/0c/0c2054f5e62dca5c6f08df11f519822f43af2c5abfc7cc2cc5884fa8382e0964.png",
        "sha256": "0c2054f5e62dca5c6f08df11f519822f43af2c5abfc7cc2cc5884fa8382e0964"
      },
      {
        "path": "/data2/k6tk/e7/e717b9a03a0755f762521df086cce4be204346d498756377b0d321f11af9444e.png",
        "sha256": "e717b9a03a0755f762521df086cce4be204346d498756377b0d321f11af9444e"
      },
      {
        "path": "/data2/k6tk/e8/e8a7347876c83f4cdd5ddf327b4bd64ec3c60cef042821e30150bc70a4a95877.png",
        "sha256": "e8a7347876c83f4cdd5ddf327b4bd64ec3c60cef042821e30150bc70a4a95877"
      },
      {
        "path": "/data2/k6tk/d1/d15efc769c592b4bb9e2c30ec1a5a7905feb22164b82fe870bc293c1cea87763.png",
        "sha256": "d15efc769c592b4bb9e2c30ec1a5a7905feb22164b82fe870bc293c1cea87763"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "The categories to compare are 'tv' and 'chair', in that order. Which answer describes the number of distinct objects in the first category relative to the second?",
    "timestamps": [
      0.0,
      2.5,
      4.9,
      7.4,
      9.9,
      12.3,
      14.8,
      17.3,
      19.7,
      22.2,
      24.6,
      27.1,
      29.6,
      32.0,
      34.5,
      37.0,
      39.4,
      41.9,
      44.4,
      46.8,
      49.3,
      51.8,
      54.2,
      56.7,
      59.1,
      61.6,
      64.1,
      66.5,
      69.0,
      71.5,
      73.9,
      76.4
    ],
    "total_num_frames": 765
  },
  "target": "<think>\nlocate the distinct instances of tv; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many tv instances as chair instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 27. fbp_relcnt2_4833972ae98a857242cecb4c

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-ef39c01af48e963cc306ea251011135c509fe4cba8eb2104d690c75d498e98f2",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41159369",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41159369.npz": "cdd6a484759aea0bef88e1e106fdf096b2b8d245740d9b01d2e01d72045af2c8",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41159369.npz",
    "raster_sha256": "cdd6a484759aea0bef88e1e106fdf096b2b8d245740d9b01d2e01d72045af2c8",
    "relative_count": {
      "a": "chair",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        9
      ],
      "ids_b": [
        13
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue381626",
      "scene_use_cap": 24,
      "source_qid": "b12ct_61253f7d79d877ccd7e7a32f",
      "source_row_sha256": "1cff30d1f907f6ec7f43c56247f1a2a91b7297893d893f4dab9c8e030263327f",
      "source_use_cap": 8,
      "template_id": 6,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_4833972ae98a857242cecb4c",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v9d58292bb527",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      36,
      73,
      109,
      145,
      181,
      218,
      254,
      290,
      327,
      363,
      399,
      435,
      472,
      508,
      544,
      581,
      617,
      653,
      690,
      726,
      762,
      798,
      835,
      871,
      907,
      944,
      980,
      1016,
      1052,
      1089,
      1125
    ],
    "frames": [
      {
        "path": "/data2/k6tk/41/41af1546069652dc0c6b17e7aaacf728fd8857ab896c96114671a72ff7da28f3.png",
        "sha256": "41af1546069652dc0c6b17e7aaacf728fd8857ab896c96114671a72ff7da28f3"
      },
      {
        "path": "/data2/k6tk/03/0328223bd91a9a2802b105c792477ad2d7bf455fa6b92ae33444e21ab8eaed22.png",
        "sha256": "0328223bd91a9a2802b105c792477ad2d7bf455fa6b92ae33444e21ab8eaed22"
      },
      {
        "path": "/data2/k6tk/c1/c1911354d0befa193d8ed8d82e8c331b912469ffe9e16a86d5520e91644b09ce.png",
        "sha256": "c1911354d0befa193d8ed8d82e8c331b912469ffe9e16a86d5520e91644b09ce"
      },
      {
        "path": "/data2/k6tk/ff/ff7b5f9aabadffa32b3daba4eb37da7b26b434ade4a5dbd827ba87571ff03f2c.png",
        "sha256": "ff7b5f9aabadffa32b3daba4eb37da7b26b434ade4a5dbd827ba87571ff03f2c"
      },
      {
        "path": "/data2/k6tk/3d/3d600a9b6d5d03e930c1648b91ceb7baae50cdd50a6c1ef41ffbe2fa57a696f3.png",
        "sha256": "3d600a9b6d5d03e930c1648b91ceb7baae50cdd50a6c1ef41ffbe2fa57a696f3"
      },
      {
        "path": "/data2/k6tk/7e/7eb4d6c56f553b6508d04acd6ff3f64f5d5adb0b0682709b819102a73ee48bee.png",
        "sha256": "7eb4d6c56f553b6508d04acd6ff3f64f5d5adb0b0682709b819102a73ee48bee"
      },
      {
        "path": "/data2/k6tk/25/25c94ee4814538d879cd94ee141220befc52152b08b4fc791ef67d72cf6b3f6e.png",
        "sha256": "25c94ee4814538d879cd94ee141220befc52152b08b4fc791ef67d72cf6b3f6e"
      },
      {
        "path": "/data2/k6tk/51/51ed503f1e28e2dbfb65512d31bfe8cb0645403b875a0ce0f9d6fe8857a9b2cb.png",
        "sha256": "51ed503f1e28e2dbfb65512d31bfe8cb0645403b875a0ce0f9d6fe8857a9b2cb"
      },
      {
        "path": "/data2/k6tk/19/1992aa6d6e8aa94fe88fa7b66384f461494757bf12c241fe75b69fe873d338de.png",
        "sha256": "1992aa6d6e8aa94fe88fa7b66384f461494757bf12c241fe75b69fe873d338de"
      },
      {
        "path": "/data2/k6tk/16/1686b9043b9122d9793afb99ab262ccc67675c53883eb0a4cf05297301635762.png",
        "sha256": "1686b9043b9122d9793afb99ab262ccc67675c53883eb0a4cf05297301635762"
      },
      {
        "path": "/data2/k6tk/58/5802ea43e249100951ec6401538a046db9b7efe9f75c2a06b3a3b225e460ffa5.png",
        "sha256": "5802ea43e249100951ec6401538a046db9b7efe9f75c2a06b3a3b225e460ffa5"
      },
      {
        "path": "/data2/k6tk/6d/6db26510acfbb0dc92fa4081ddeb2948eda9f8545e2776d5be53498474c9f34a.png",
        "sha256": "6db26510acfbb0dc92fa4081ddeb2948eda9f8545e2776d5be53498474c9f34a"
      },
      {
        "path": "/data2/k6tk/93/935518f3e3cb6ca6c8fac8c1e82438456c00daacbdf4083a1e71f9b35e2fa350.png",
        "sha256": "935518f3e3cb6ca6c8fac8c1e82438456c00daacbdf4083a1e71f9b35e2fa350"
      },
      {
        "path": "/data2/k6tk/35/35d0d82ffd8cf3aa8d2bc842bac59f4de534dcfa10f8786b99702b1b4fa7f095.png",
        "sha256": "35d0d82ffd8cf3aa8d2bc842bac59f4de534dcfa10f8786b99702b1b4fa7f095"
      },
      {
        "path": "/data2/k6tk/5c/5cde62e7e4e80f5655c902ad733288e31bf3c00aea906f7630c457abdaec1fb0.png",
        "sha256": "5cde62e7e4e80f5655c902ad733288e31bf3c00aea906f7630c457abdaec1fb0"
      },
      {
        "path": "/data2/k6tk/f6/f6c04ea1cc1a8d95ac8d49beadc6edbcd483d317865c8c66d4ad7a4cf86799cc.png",
        "sha256": "f6c04ea1cc1a8d95ac8d49beadc6edbcd483d317865c8c66d4ad7a4cf86799cc"
      },
      {
        "path": "/data2/k6tk/71/7109994642f7bf59ff59b458c91eeee05d562bab9790f7942ee4b1149303d5df.png",
        "sha256": "7109994642f7bf59ff59b458c91eeee05d562bab9790f7942ee4b1149303d5df"
      },
      {
        "path": "/data2/k6tk/43/43745b72a6e2274b753bbd75ed2b4e808758715920bb984483e84b4661711d4b.png",
        "sha256": "43745b72a6e2274b753bbd75ed2b4e808758715920bb984483e84b4661711d4b"
      },
      {
        "path": "/data2/k6tk/d3/d3b0d19a96ec8386dfb81dd17f725f0404f31dfb73c34f2b8dc8922ba6ef9ef0.png",
        "sha256": "d3b0d19a96ec8386dfb81dd17f725f0404f31dfb73c34f2b8dc8922ba6ef9ef0"
      },
      {
        "path": "/data2/k6tk/c0/c00fa921b8713b0365afb696ea72cf3df58b14adb8a90bc4ee87ca0f21c7e0ce.png",
        "sha256": "c00fa921b8713b0365afb696ea72cf3df58b14adb8a90bc4ee87ca0f21c7e0ce"
      },
      {
        "path": "/data2/k6tk/cb/cb2f0ffd2de84a1ddb9bf97a358087127095a597144a297b1205050e573deb21.png",
        "sha256": "cb2f0ffd2de84a1ddb9bf97a358087127095a597144a297b1205050e573deb21"
      },
      {
        "path": "/data2/k6tk/ba/ba3f7086ab5bd7d4d8ef8717af5b0815657826ca74359945f0394c2bf08e3be5.png",
        "sha256": "ba3f7086ab5bd7d4d8ef8717af5b0815657826ca74359945f0394c2bf08e3be5"
      },
      {
        "path": "/data2/k6tk/c6/c61f9eff9dde44aa160e8c8f13d3be91a3cd7d5a761bcc50818e7fcf46b175aa.png",
        "sha256": "c61f9eff9dde44aa160e8c8f13d3be91a3cd7d5a761bcc50818e7fcf46b175aa"
      },
      {
        "path": "/data2/k6tk/fd/fd8c13ad4133ac8a22c23f8c97db3e02d5f424f1c9bcfbda62bfebbb6a3c0a4f.png",
        "sha256": "fd8c13ad4133ac8a22c23f8c97db3e02d5f424f1c9bcfbda62bfebbb6a3c0a4f"
      },
      {
        "path": "/data2/k6tk/99/99f41b62ddfe0227fc2f24c9fa1f9910829f259c2fa0ec6a3c13e0614b80d8f0.png",
        "sha256": "99f41b62ddfe0227fc2f24c9fa1f9910829f259c2fa0ec6a3c13e0614b80d8f0"
      },
      {
        "path": "/data2/k6tk/20/20ea718961ecef7962df23e141a9fca5b55cee3c06bd7003ded2126e31978e90.png",
        "sha256": "20ea718961ecef7962df23e141a9fca5b55cee3c06bd7003ded2126e31978e90"
      },
      {
        "path": "/data2/k6tk/31/3157e3df1eb0b0c148aa1041b661133751aa3977a0ceb183ef2c2261e149b3c0.png",
        "sha256": "3157e3df1eb0b0c148aa1041b661133751aa3977a0ceb183ef2c2261e149b3c0"
      },
      {
        "path": "/data2/k6tk/52/5257c6e2f253343371ac2a555fc691959179f8208ae5e3c5bf2a14d6e9c8105a.png",
        "sha256": "5257c6e2f253343371ac2a555fc691959179f8208ae5e3c5bf2a14d6e9c8105a"
      },
      {
        "path": "/data2/k6tk/75/751705583977144ccd87af39941be8aa1ab3872e3ca73cfd06d0bcdf430935e9.png",
        "sha256": "751705583977144ccd87af39941be8aa1ab3872e3ca73cfd06d0bcdf430935e9"
      },
      {
        "path": "/data2/k6tk/c7/c7507eebc562ae6fe5104bb4f8958c70a404845532efd785c07cc4abc4144b2c.png",
        "sha256": "c7507eebc562ae6fe5104bb4f8958c70a404845532efd785c07cc4abc4144b2c"
      },
      {
        "path": "/data2/k6tk/f6/f6ce372b602393c67986ff4686f5188d8750a55dde65ea71539a16fead0153bd.png",
        "sha256": "f6ce372b602393c67986ff4686f5188d8750a55dde65ea71539a16fead0153bd"
      },
      {
        "path": "/data2/k6tk/b2/b26def573cf7ef49b0432eed0e041df62197066246f3cb2ab7e970087539cda1.png",
        "sha256": "b26def573cf7ef49b0432eed0e041df62197066246f3cb2ab7e970087539cda1"
      }
    ],
    "options": [
      "A. equal number",
      "B. fewer",
      "C. more"
    ],
    "question": "Keep track of distinct 'chair' objects while viewing the room, and do the same for 'tv'. Select the comparison that places the 'chair' tally against the 'tv' tally.",
    "timestamps": [
      0.0,
      3.6,
      7.3,
      10.9,
      14.5,
      18.1,
      21.8,
      25.4,
      29.0,
      32.7,
      36.3,
      39.9,
      43.5,
      47.2,
      50.8,
      54.4,
      58.1,
      61.7,
      65.3,
      69.0,
      72.6,
      76.2,
      79.8,
      83.5,
      87.1,
      90.7,
      94.4,
      98.0,
      101.6,
      105.2,
      108.9,
      112.5
    ],
    "total_num_frames": 1126
  },
  "target": "<think>\nlocate the distinct instances of chair; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many chair instances as tv instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 28. fbp_relcnt2_b0bf451b691a5f1b9c508ab6

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-c081e37181f38924b3d5f987a440f858deaa82a5cd453a101c179181f1809fe2",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42444735",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42444735.npz": "30b5660a8e657796ebcf4f9586e3e89dcbac96e104cd7b3e04bc9d78d26a66ad",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42444735.npz",
    "raster_sha256": "30b5660a8e657796ebcf4f9586e3e89dcbac96e104cd7b3e04bc9d78d26a66ad",
    "relative_count": {
      "a": "tv",
      "b": "table",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        7
      ],
      "ids_b": [
        3
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue421267",
      "scene_use_cap": 24,
      "source_qid": "b12ct_cdf72f724f28402c11ffa32b",
      "source_row_sha256": "2a890345b4fc712c32e4573478607022187f8986d1c0320c4209a58fc8b06989",
      "source_use_cap": 8,
      "template_id": 7,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_b0bf451b691a5f1b9c508ab6",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v822cd92ae774",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      20,
      40,
      60,
      80,
      100,
      120,
      140,
      161,
      181,
      201,
      221,
      241,
      261,
      281,
      301,
      321,
      341,
      361,
      381,
      401,
      421,
      441,
      461,
      482,
      502,
      522,
      542,
      562,
      582,
      602,
      622
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9b/9bc4530152aca563a277f3aab3f96e16cedac5ef69d5da8463670177983454e0.png",
        "sha256": "9bc4530152aca563a277f3aab3f96e16cedac5ef69d5da8463670177983454e0"
      },
      {
        "path": "/data2/k6tk/60/60445fb7fd02eda8ae490483cc118fb1fdfa1a4bf1cac796e3e6ced2eec590f6.png",
        "sha256": "60445fb7fd02eda8ae490483cc118fb1fdfa1a4bf1cac796e3e6ced2eec590f6"
      },
      {
        "path": "/data2/k6tk/5c/5c0eb8974fb1b26d9a879ca9be5af8e49de5e9c5378334ac0743f0af8beb260c.png",
        "sha256": "5c0eb8974fb1b26d9a879ca9be5af8e49de5e9c5378334ac0743f0af8beb260c"
      },
      {
        "path": "/data2/k6tk/e7/e707c733b8c21dfe8c47411cc4b4c029c96ecfc0681a9080c6e0a2a9cb4c507b.png",
        "sha256": "e707c733b8c21dfe8c47411cc4b4c029c96ecfc0681a9080c6e0a2a9cb4c507b"
      },
      {
        "path": "/data2/k6tk/32/32023e3d9bce131502f5628d03aeeb5ca33363eea25554bb02dcc7adf5353af9.png",
        "sha256": "32023e3d9bce131502f5628d03aeeb5ca33363eea25554bb02dcc7adf5353af9"
      },
      {
        "path": "/data2/k6tk/c8/c87142cb16466d4a790aa3b2ea35c00aea6b25785629668f9080baecd7cebb81.png",
        "sha256": "c87142cb16466d4a790aa3b2ea35c00aea6b25785629668f9080baecd7cebb81"
      },
      {
        "path": "/data2/k6tk/39/39e7ccd636eb0722e227afcea7b80f8c185370f350abe711863c4d130e097dbf.png",
        "sha256": "39e7ccd636eb0722e227afcea7b80f8c185370f350abe711863c4d130e097dbf"
      },
      {
        "path": "/data2/k6tk/84/8416d7c2d05c1f8e0028f481fdb07e1746d10cb4cae12dd72e50eba962ba1175.png",
        "sha256": "8416d7c2d05c1f8e0028f481fdb07e1746d10cb4cae12dd72e50eba962ba1175"
      },
      {
        "path": "/data2/k6tk/dd/dd56ee693928e2754e517a275606b068db56a00823fa9ad528960d0fdd999a59.png",
        "sha256": "dd56ee693928e2754e517a275606b068db56a00823fa9ad528960d0fdd999a59"
      },
      {
        "path": "/data2/k6tk/13/13f8cc9dcf37e137d132607d2b0c1e9f7f080cf4e9a21c3d53648805742da50d.png",
        "sha256": "13f8cc9dcf37e137d132607d2b0c1e9f7f080cf4e9a21c3d53648805742da50d"
      },
      {
        "path": "/data2/k6tk/d6/d634e0544ac0d8e187610005b47f68de501cfd1070f026061b838955c999470d.png",
        "sha256": "d634e0544ac0d8e187610005b47f68de501cfd1070f026061b838955c999470d"
      },
      {
        "path": "/data2/k6tk/e9/e9b5f95e73ec2dfac0e5747325e99c58a6901e14ee7e823999e77381e01311a1.png",
        "sha256": "e9b5f95e73ec2dfac0e5747325e99c58a6901e14ee7e823999e77381e01311a1"
      },
      {
        "path": "/data2/k6tk/d6/d6221cc18ed996e57a25485d8ca2bb128f5bf51204537e60704a50b50fab5a07.png",
        "sha256": "d6221cc18ed996e57a25485d8ca2bb128f5bf51204537e60704a50b50fab5a07"
      },
      {
        "path": "/data2/k6tk/76/7649bbb51ddd4cde908284108e4aea8167da4d91fd380c524351757bf36408b4.png",
        "sha256": "7649bbb51ddd4cde908284108e4aea8167da4d91fd380c524351757bf36408b4"
      },
      {
        "path": "/data2/k6tk/58/58c95daa182e4cb9075473a36cac8ecb4137d56d9fd377ddc27ab294f2a5b621.png",
        "sha256": "58c95daa182e4cb9075473a36cac8ecb4137d56d9fd377ddc27ab294f2a5b621"
      },
      {
        "path": "/data2/k6tk/de/de1939630daf82c2807db13735aa65cf90c0b5f1b318b6191c7a01e4dd50df60.png",
        "sha256": "de1939630daf82c2807db13735aa65cf90c0b5f1b318b6191c7a01e4dd50df60"
      },
      {
        "path": "/data2/k6tk/a3/a3e752ea1a57f06c4909e79d818b799e40bf97b9bbb3b3777cb75f14dd879786.png",
        "sha256": "a3e752ea1a57f06c4909e79d818b799e40bf97b9bbb3b3777cb75f14dd879786"
      },
      {
        "path": "/data2/k6tk/51/51a7effa68695b4832c04c65dabf5a9a9e303a96a967c38ce02d747ea6e8cc7c.png",
        "sha256": "51a7effa68695b4832c04c65dabf5a9a9e303a96a967c38ce02d747ea6e8cc7c"
      },
      {
        "path": "/data2/k6tk/49/499d020d7dc7134f3e6cd4d8ed6416db6f0f44975a34c85b5fe6da0e9ed4fdfa.png",
        "sha256": "499d020d7dc7134f3e6cd4d8ed6416db6f0f44975a34c85b5fe6da0e9ed4fdfa"
      },
      {
        "path": "/data2/k6tk/36/369e52f26e9fb752b4b12c2e356403ebd19cd407ae82d134b448820c9632375e.png",
        "sha256": "369e52f26e9fb752b4b12c2e356403ebd19cd407ae82d134b448820c9632375e"
      },
      {
        "path": "/data2/k6tk/9c/9cdf68879f6dd72be71cf3ccf6f69e4eb6a597260127ae529805870413f28375.png",
        "sha256": "9cdf68879f6dd72be71cf3ccf6f69e4eb6a597260127ae529805870413f28375"
      },
      {
        "path": "/data2/k6tk/2d/2d523c9d8ffb8167ab62448281b82ac77e8c0d66df749ee4ce2cb6e40a110cd6.png",
        "sha256": "2d523c9d8ffb8167ab62448281b82ac77e8c0d66df749ee4ce2cb6e40a110cd6"
      },
      {
        "path": "/data2/k6tk/2d/2d2536af5b40580ce6c7ad74977d1f2a22646c04a2bd6de5c3b7927e538d02ec.png",
        "sha256": "2d2536af5b40580ce6c7ad74977d1f2a22646c04a2bd6de5c3b7927e538d02ec"
      },
      {
        "path": "/data2/k6tk/0d/0d1e24ac107a8adafe4fbaf81ab03b607e29a239cef15f79d6335192d5a0117b.png",
        "sha256": "0d1e24ac107a8adafe4fbaf81ab03b607e29a239cef15f79d6335192d5a0117b"
      },
      {
        "path": "/data2/k6tk/b5/b53685276f59cf7bc3561a0fd5afd0fd8af9251dd37c0ea8b39954c0a401fdc8.png",
        "sha256": "b53685276f59cf7bc3561a0fd5afd0fd8af9251dd37c0ea8b39954c0a401fdc8"
      },
      {
        "path": "/data2/k6tk/da/da370c3a602676a39e022706b5edd4f104973feb6896899962bfebdf86e61136.png",
        "sha256": "da370c3a602676a39e022706b5edd4f104973feb6896899962bfebdf86e61136"
      },
      {
        "path": "/data2/k6tk/be/be579f2a507001b3bbf2c82410acd51bd24a2b4c3f8948f0d75bf213ce37bc8f.png",
        "sha256": "be579f2a507001b3bbf2c82410acd51bd24a2b4c3f8948f0d75bf213ce37bc8f"
      },
      {
        "path": "/data2/k6tk/b6/b61ce07425532fdd0d97d67e7e69e7b9ddc62d7c2427c1413e4f633c0b9e8d07.png",
        "sha256": "b61ce07425532fdd0d97d67e7e69e7b9ddc62d7c2427c1413e4f633c0b9e8d07"
      },
      {
        "path": "/data2/k6tk/9e/9e9c8631edfa2670127ffd561a7d41acb200f70e20899c3c70d071235bc4eddd.png",
        "sha256": "9e9c8631edfa2670127ffd561a7d41acb200f70e20899c3c70d071235bc4eddd"
      },
      {
        "path": "/data2/k6tk/8b/8b07a459ec7444fbc0cd058a70f22fd5f9500ffe8d1010fcc9f423bcd4c225e4.png",
        "sha256": "8b07a459ec7444fbc0cd058a70f22fd5f9500ffe8d1010fcc9f423bcd4c225e4"
      },
      {
        "path": "/data2/k6tk/66/661108c2d7d880bcee584a92f15ce87c8a27d404ea3f11cdbe20e4857cad318d.png",
        "sha256": "661108c2d7d880bcee584a92f15ce87c8a27d404ea3f11cdbe20e4857cad318d"
      },
      {
        "path": "/data2/k6tk/03/0373f456c80ab7397ccf771791fee56a6976a73713a546d38aa79a82a9e82d4d.png",
        "sha256": "0373f456c80ab7397ccf771791fee56a6976a73713a546d38aa79a82a9e82d4d"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Make independent counts for 'tv' and 'table' using the video. Which option states how the total for 'tv' compares with the total for 'table'?",
    "timestamps": [
      0.0,
      2.0,
      4.0,
      6.0,
      8.0,
      10.0,
      12.0,
      14.0,
      16.1,
      18.1,
      20.1,
      22.1,
      24.1,
      26.1,
      28.1,
      30.1,
      32.1,
      34.1,
      36.1,
      38.1,
      40.1,
      42.1,
      44.1,
      46.1,
      48.2,
      50.2,
      52.2,
      54.2,
      56.2,
      58.2,
      60.2,
      62.2
    ],
    "total_num_frames": 623
  },
  "target": "<think>\nlocate the distinct instances of tv; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are as many tv instances as table instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 29. fbp_relcnt2_17d57fe08bb390eec2b36daa

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-7912ccc5ca730a8b158cc2b8e2e5cde6a0e1d50d35dfae82c6aa2c01e619fc34",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41048129",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41048129.npz": "b2a424813031c0a1350f9e07e0c7032951ba57d3bf7e95235cf38325bb2bf56f",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41048129.npz",
    "raster_sha256": "b2a424813031c0a1350f9e07e0c7032951ba57d3bf7e95235cf38325bb2bf56f",
    "relative_count": {
      "a": "sofa",
      "b": "table",
      "bucket": "tie",
      "count_a": 2,
      "count_b": 2,
      "ids_a": [
        0,
        5
      ],
      "ids_b": [
        1,
        4
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue381584",
      "scene_use_cap": 24,
      "source_qid": "b12ct_0603567270237246a10ccefb",
      "source_row_sha256": "7f86457568364d19fa85470e99997615e950967571abf702ec153923468704f4",
      "source_use_cap": 8,
      "template_id": 8,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_17d57fe08bb390eec2b36daa",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v102a5089dd2f",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      17,
      34,
      50,
      67,
      84,
      101,
      117,
      134,
      151,
      168,
      185,
      201,
      218,
      235,
      252,
      268,
      285,
      302,
      319,
      335,
      352,
      369,
      386,
      403,
      419,
      436,
      453,
      470,
      486,
      503,
      520
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c7/c707cd98b291e5173bb15358e47ebf0ffad61c78555dfc19644255e7cfbdaf01.png",
        "sha256": "c707cd98b291e5173bb15358e47ebf0ffad61c78555dfc19644255e7cfbdaf01"
      },
      {
        "path": "/data2/k6tk/b1/b1f3c1bd78271d1c274c71a30e934a256868240e762512a8c8ef73d196484dcb.png",
        "sha256": "b1f3c1bd78271d1c274c71a30e934a256868240e762512a8c8ef73d196484dcb"
      },
      {
        "path": "/data2/k6tk/56/5609c2da4fea0b694efc5258d2d9e123d5fa0cc14c2575a7724de1e75e66e3d5.png",
        "sha256": "5609c2da4fea0b694efc5258d2d9e123d5fa0cc14c2575a7724de1e75e66e3d5"
      },
      {
        "path": "/data2/k6tk/46/463e1a3e14d4a22701b2d8557afe3dccf21795d2bf4111c1a0d3b4f27725c40f.png",
        "sha256": "463e1a3e14d4a22701b2d8557afe3dccf21795d2bf4111c1a0d3b4f27725c40f"
      },
      {
        "path": "/data2/k6tk/f8/f8db9193495b1dfad0f3434b82cbc64614ce675f7e1dd5ea9ee0b6717c475224.png",
        "sha256": "f8db9193495b1dfad0f3434b82cbc64614ce675f7e1dd5ea9ee0b6717c475224"
      },
      {
        "path": "/data2/k6tk/43/4374dc229d1be7e9e081b705a67939b390c2d3be5760cc28bf710d2c4c713299.png",
        "sha256": "4374dc229d1be7e9e081b705a67939b390c2d3be5760cc28bf710d2c4c713299"
      },
      {
        "path": "/data2/k6tk/06/063b50ecc4d7aae6e874a7a740d37d40b665fede218f16df89e4057c7fb17bae.png",
        "sha256": "063b50ecc4d7aae6e874a7a740d37d40b665fede218f16df89e4057c7fb17bae"
      },
      {
        "path": "/data2/k6tk/ee/ee041bd039c22a9eab39503c431bd0c82e996aa8bdf92451cc7bf4621fc42ff8.png",
        "sha256": "ee041bd039c22a9eab39503c431bd0c82e996aa8bdf92451cc7bf4621fc42ff8"
      },
      {
        "path": "/data2/k6tk/cf/cfe904446eeac954b3c47ad3b86787b5ec848f0cb6b022c8b51f1278a25edee4.png",
        "sha256": "cfe904446eeac954b3c47ad3b86787b5ec848f0cb6b022c8b51f1278a25edee4"
      },
      {
        "path": "/data2/k6tk/3b/3b40cbdc9477f2fc1f04ae3e0151c51045710047e3d5a031f2ef49dbe2bb67d2.png",
        "sha256": "3b40cbdc9477f2fc1f04ae3e0151c51045710047e3d5a031f2ef49dbe2bb67d2"
      },
      {
        "path": "/data2/k6tk/88/8828992c8ceb747b0008c6846abbf4de8e150c5b0bbbf9127d6c0b9cfe227bc1.png",
        "sha256": "8828992c8ceb747b0008c6846abbf4de8e150c5b0bbbf9127d6c0b9cfe227bc1"
      },
      {
        "path": "/data2/k6tk/cb/cbd1840047c7214bddd430e2bbd5928915f462b10f9769b3bad1b65108bb91c3.png",
        "sha256": "cbd1840047c7214bddd430e2bbd5928915f462b10f9769b3bad1b65108bb91c3"
      },
      {
        "path": "/data2/k6tk/0a/0a5c08753a6e94e1f3a443e5f74631412edbc665f4dd2c114cc948cb7872c1f2.png",
        "sha256": "0a5c08753a6e94e1f3a443e5f74631412edbc665f4dd2c114cc948cb7872c1f2"
      },
      {
        "path": "/data2/k6tk/1d/1d3960a94a33566a149dcd53eb068393b98082dd949bbfeb3b6e85ff49ee9c15.png",
        "sha256": "1d3960a94a33566a149dcd53eb068393b98082dd949bbfeb3b6e85ff49ee9c15"
      },
      {
        "path": "/data2/k6tk/e6/e681c8710cf4162dd81e59e96b169c14bb6a737bd03387ab4c87db0469b3bd38.png",
        "sha256": "e681c8710cf4162dd81e59e96b169c14bb6a737bd03387ab4c87db0469b3bd38"
      },
      {
        "path": "/data2/k6tk/45/45dac5b78ee82768eba1e508e669174a6c1a16f186b90fb5fbd58751c9b177c4.png",
        "sha256": "45dac5b78ee82768eba1e508e669174a6c1a16f186b90fb5fbd58751c9b177c4"
      },
      {
        "path": "/data2/k6tk/fe/fe4e1f0d0cc39b55bb5e821d2e0423c16d3e05a2070147f120dffa69d868d4f9.png",
        "sha256": "fe4e1f0d0cc39b55bb5e821d2e0423c16d3e05a2070147f120dffa69d868d4f9"
      },
      {
        "path": "/data2/k6tk/a7/a7f12780a2855d2256a44ab133ec805808b4e219ca2d223d38437040b30e1dfc.png",
        "sha256": "a7f12780a2855d2256a44ab133ec805808b4e219ca2d223d38437040b30e1dfc"
      },
      {
        "path": "/data2/k6tk/dd/dd2f7030856d6197d24beb87369dd749479c791f8b1d926919df1cee99edaee8.png",
        "sha256": "dd2f7030856d6197d24beb87369dd749479c791f8b1d926919df1cee99edaee8"
      },
      {
        "path": "/data2/k6tk/77/77679303aab825721eb41a7f4d2479bba72578fa9b3e13ba3b8781de84f113aa.png",
        "sha256": "77679303aab825721eb41a7f4d2479bba72578fa9b3e13ba3b8781de84f113aa"
      },
      {
        "path": "/data2/k6tk/14/14a7e70e4eb59c14c9a8256767e911783ec283fa19a4abe953bd621f15b0b381.png",
        "sha256": "14a7e70e4eb59c14c9a8256767e911783ec283fa19a4abe953bd621f15b0b381"
      },
      {
        "path": "/data2/k6tk/52/5220a89c57f194be7d22197624e093589f9138f76e0b1e8c087fddf64c6b4cf3.png",
        "sha256": "5220a89c57f194be7d22197624e093589f9138f76e0b1e8c087fddf64c6b4cf3"
      },
      {
        "path": "/data2/k6tk/22/2247d18574f0fd4e3a0fcf1243827a79ddf3ad6f25607d8f6180e49c69196cc3.png",
        "sha256": "2247d18574f0fd4e3a0fcf1243827a79ddf3ad6f25607d8f6180e49c69196cc3"
      },
      {
        "path": "/data2/k6tk/b7/b7b1d1c522c77801061b7beae29feed18f6a24af9509fd27e9c3e765f28168e7.png",
        "sha256": "b7b1d1c522c77801061b7beae29feed18f6a24af9509fd27e9c3e765f28168e7"
      },
      {
        "path": "/data2/k6tk/b2/b29ee56b5d432420a331e5947daadea11730b6fefc256820b4745e9edbfa30fa.png",
        "sha256": "b29ee56b5d432420a331e5947daadea11730b6fefc256820b4745e9edbfa30fa"
      },
      {
        "path": "/data2/k6tk/d0/d0921e5140cabf0d6df7b2bd0db0f46c53145c1cb11c540c1d32cbb0bcc48d10.png",
        "sha256": "d0921e5140cabf0d6df7b2bd0db0f46c53145c1cb11c540c1d32cbb0bcc48d10"
      },
      {
        "path": "/data2/k6tk/db/db57358de8b10ec32676c713e5cd6ecf873715bb25fbddb044b9f615a9acd63f.png",
        "sha256": "db57358de8b10ec32676c713e5cd6ecf873715bb25fbddb044b9f615a9acd63f"
      },
      {
        "path": "/data2/k6tk/1e/1e96bcfab4111eac11f70500373754d94b262385ae6e3627554fb10838e0352a.png",
        "sha256": "1e96bcfab4111eac11f70500373754d94b262385ae6e3627554fb10838e0352a"
      },
      {
        "path": "/data2/k6tk/1b/1b275265b70c0debf769915822788448e1e189b344930a4d42030d31a8d99857.png",
        "sha256": "1b275265b70c0debf769915822788448e1e189b344930a4d42030d31a8d99857"
      },
      {
        "path": "/data2/k6tk/c2/c258af36f1a70b5b9ce1bf737f31dab6c1631c10ba18c2541dc1acfd355eea90.png",
        "sha256": "c258af36f1a70b5b9ce1bf737f31dab6c1631c10ba18c2541dc1acfd355eea90"
      },
      {
        "path": "/data2/k6tk/03/03efd42076359241e39284d3d7ac9c37ee84c6174d96aa33f70d9cb904d86958.png",
        "sha256": "03efd42076359241e39284d3d7ac9c37ee84c6174d96aa33f70d9cb904d86958"
      },
      {
        "path": "/data2/k6tk/18/1866b020ed9c6360aff751dd3beac4cbb4ac973d9796509fff00c996a37c5268.png",
        "sha256": "1866b020ed9c6360aff751dd3beac4cbb4ac973d9796509fff00c996a37c5268"
      }
    ],
    "options": [
      "A. fewer",
      "B. more",
      "C. equal number"
    ],
    "question": "For a count comparison, take 'sofa' as the first category and 'table' as the second. What relation between their numbers of instances does the room show?",
    "timestamps": [
      0.0,
      1.7,
      3.4,
      5.0,
      6.7,
      8.4,
      10.1,
      11.7,
      13.4,
      15.1,
      16.8,
      18.5,
      20.1,
      21.8,
      23.5,
      25.2,
      26.8,
      28.5,
      30.2,
      31.9,
      33.5,
      35.2,
      36.9,
      38.6,
      40.3,
      41.9,
      43.6,
      45.3,
      47.0,
      48.6,
      50.3,
      52.0
    ],
    "total_num_frames": 521
  },
  "target": "<think>\nlocate the distinct instances of sofa; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are as many sofa instances as table instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 30. fbp_relcnt2_eb2b8f5286ce268584c24b3b

```json
{
  "answer": "B",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-de41324ff151c6110bdfa527bfcd850d20acde894b347a7a447c4bbdd5e4ab2a",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42445902",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42445902.npz": "ef0613fc0a4c1a867c49b9d4afb68db59bb1d22614e3023ab038cc0d63329728",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42445902.npz",
    "raster_sha256": "ef0613fc0a4c1a867c49b9d4afb68db59bb1d22614e3023ab038cc0d63329728",
    "relative_count": {
      "a": "table",
      "b": "stool",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        20
      ],
      "ids_b": [
        21
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue422149",
      "scene_use_cap": 24,
      "source_qid": "b12ct_53a1a3495da9a2947e8ef221",
      "source_row_sha256": "696238a6a2422fd5cf424d01056a2c2370d17389e13c5ae3280a59ee378919b5",
      "source_use_cap": 8,
      "template_id": 9,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_eb2b8f5286ce268584c24b3b",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vd59ef6543605",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      23,
      47,
      70,
      94,
      117,
      140,
      164,
      187,
      210,
      234,
      257,
      281,
      304,
      327,
      351,
      374,
      398,
      421,
      444,
      468,
      491,
      515,
      538,
      561,
      585,
      608,
      631,
      655,
      678,
      702,
      725
    ],
    "frames": [
      {
        "path": "/data2/k6tk/a0/a081fd539032da8e6ce6792525bb76e7cf08c94ca3333bc5e28d4f72a462fa95.png",
        "sha256": "a081fd539032da8e6ce6792525bb76e7cf08c94ca3333bc5e28d4f72a462fa95"
      },
      {
        "path": "/data2/k6tk/e8/e84de3c3aa4e5aa47671ef0bf8ec683201e6e362be322f081d0ae88e67719bf9.png",
        "sha256": "e84de3c3aa4e5aa47671ef0bf8ec683201e6e362be322f081d0ae88e67719bf9"
      },
      {
        "path": "/data2/k6tk/d4/d4e608867b30d1e58ddd889ddf7bbbeb3350b73b73c54e29c587e774055f2cbe.png",
        "sha256": "d4e608867b30d1e58ddd889ddf7bbbeb3350b73b73c54e29c587e774055f2cbe"
      },
      {
        "path": "/data2/k6tk/bd/bd9dc9803df8558c1fd70f717a994f0a43ba458130ee2a9bc2f80cc1c50b46bd.png",
        "sha256": "bd9dc9803df8558c1fd70f717a994f0a43ba458130ee2a9bc2f80cc1c50b46bd"
      },
      {
        "path": "/data2/k6tk/ec/ec1fd2dde579fd62fdb0677050f0da29c93a2a297f38d084e96eaf484a94282e.png",
        "sha256": "ec1fd2dde579fd62fdb0677050f0da29c93a2a297f38d084e96eaf484a94282e"
      },
      {
        "path": "/data2/k6tk/7e/7e5eb5318ffdd2f747e7e0980c8df37a6366772200b68093a75f6834a433ec79.png",
        "sha256": "7e5eb5318ffdd2f747e7e0980c8df37a6366772200b68093a75f6834a433ec79"
      },
      {
        "path": "/data2/k6tk/73/73db458f648b7c12b21a0608ad1c92ef19aa83694d53a642f66f3d9acbe651b0.png",
        "sha256": "73db458f648b7c12b21a0608ad1c92ef19aa83694d53a642f66f3d9acbe651b0"
      },
      {
        "path": "/data2/k6tk/00/000bf014cb82e3ef683e2f9be35c4102798721e601a3d70d898d53d40694b70e.png",
        "sha256": "000bf014cb82e3ef683e2f9be35c4102798721e601a3d70d898d53d40694b70e"
      },
      {
        "path": "/data2/k6tk/5a/5ad60ea3617ddbaa31f22faf8c0cdf2db153f1cfda6f18fa18678bdf7ba0f869.png",
        "sha256": "5ad60ea3617ddbaa31f22faf8c0cdf2db153f1cfda6f18fa18678bdf7ba0f869"
      },
      {
        "path": "/data2/k6tk/b3/b3f325532c1e8b303a5861720916b780fc781cd5debb0df535c409fe6e71aba8.png",
        "sha256": "b3f325532c1e8b303a5861720916b780fc781cd5debb0df535c409fe6e71aba8"
      },
      {
        "path": "/data2/k6tk/d2/d27784661d66b95c5c0eb15b5cd804d9714251cb53ff7ccd33385eda96c899d5.png",
        "sha256": "d27784661d66b95c5c0eb15b5cd804d9714251cb53ff7ccd33385eda96c899d5"
      },
      {
        "path": "/data2/k6tk/0b/0b0495699a1a411cf78ffb9760c8948b85b3c386aef0715f18e3b209848832d4.png",
        "sha256": "0b0495699a1a411cf78ffb9760c8948b85b3c386aef0715f18e3b209848832d4"
      },
      {
        "path": "/data2/k6tk/21/21fc5450db619f9b96a1cee1d375e6deebcb238e967d7d2f09d875078635cdc8.png",
        "sha256": "21fc5450db619f9b96a1cee1d375e6deebcb238e967d7d2f09d875078635cdc8"
      },
      {
        "path": "/data2/k6tk/df/df4ac86defb2cc0c2fe8e4eeff90c44b2b18f1a2d71a3726eff6be51bced0754.png",
        "sha256": "df4ac86defb2cc0c2fe8e4eeff90c44b2b18f1a2d71a3726eff6be51bced0754"
      },
      {
        "path": "/data2/k6tk/26/268840cc866f49926d35297a58434d285ef716b4fae056b02fd06aaac87ae4fb.png",
        "sha256": "268840cc866f49926d35297a58434d285ef716b4fae056b02fd06aaac87ae4fb"
      },
      {
        "path": "/data2/k6tk/07/07e86777ff80d638b8c61096dc9ef0e3d545503c342b3b1bd903ef5e8b392032.png",
        "sha256": "07e86777ff80d638b8c61096dc9ef0e3d545503c342b3b1bd903ef5e8b392032"
      },
      {
        "path": "/data2/k6tk/89/899bf5526f5fefbf764f734ea86ab1f84e70a54c15715846f06ba082c77925ac.png",
        "sha256": "899bf5526f5fefbf764f734ea86ab1f84e70a54c15715846f06ba082c77925ac"
      },
      {
        "path": "/data2/k6tk/81/8145d83492e692f2f5d53b17f2efd168804bb8ad777e202370744d438026b70a.png",
        "sha256": "8145d83492e692f2f5d53b17f2efd168804bb8ad777e202370744d438026b70a"
      },
      {
        "path": "/data2/k6tk/9a/9a0b24e9acdea926e29539dec980784a4d0b30e0610284672a93e2fa5d2e8397.png",
        "sha256": "9a0b24e9acdea926e29539dec980784a4d0b30e0610284672a93e2fa5d2e8397"
      },
      {
        "path": "/data2/k6tk/37/37d1b56128ffc320182be693f8171605d48e6a21a7f90c689e70f1b087bc1a5f.png",
        "sha256": "37d1b56128ffc320182be693f8171605d48e6a21a7f90c689e70f1b087bc1a5f"
      },
      {
        "path": "/data2/k6tk/45/4536ced7b4e5d779c0f4f503690d957494dc997e2996c1e953917cf01b557abd.png",
        "sha256": "4536ced7b4e5d779c0f4f503690d957494dc997e2996c1e953917cf01b557abd"
      },
      {
        "path": "/data2/k6tk/23/23163b6930ce4d62c795657b39201622b85860411a69dab69dd564f7f08b70cb.png",
        "sha256": "23163b6930ce4d62c795657b39201622b85860411a69dab69dd564f7f08b70cb"
      },
      {
        "path": "/data2/k6tk/09/091bde8c119f8191a066cb7c6fa7e9b599a7c6a14fe37fdc2bc043c07b6c90c6.png",
        "sha256": "091bde8c119f8191a066cb7c6fa7e9b599a7c6a14fe37fdc2bc043c07b6c90c6"
      },
      {
        "path": "/data2/k6tk/76/760771b835ec3498951b693016bfd9a4f6fa020d432f005d4af6e08844f93483.png",
        "sha256": "760771b835ec3498951b693016bfd9a4f6fa020d432f005d4af6e08844f93483"
      },
      {
        "path": "/data2/k6tk/3f/3f05e4ffda69c5abe2c56a741f9d78806d9b56f82262a9ff8f44ebb4e7646696.png",
        "sha256": "3f05e4ffda69c5abe2c56a741f9d78806d9b56f82262a9ff8f44ebb4e7646696"
      },
      {
        "path": "/data2/k6tk/19/19306d372e41f3bab3bd785ad63f73631c3555925eade940d8c176a78dfd83f7.png",
        "sha256": "19306d372e41f3bab3bd785ad63f73631c3555925eade940d8c176a78dfd83f7"
      },
      {
        "path": "/data2/k6tk/1f/1f7aae10f412420b0d8da3800ceb8bb893a1c88e2ded2635990014f29ce6fdcd.png",
        "sha256": "1f7aae10f412420b0d8da3800ceb8bb893a1c88e2ded2635990014f29ce6fdcd"
      },
      {
        "path": "/data2/k6tk/47/475a6e3998034cde1a10abbef4fa660f12449cbcb495f5a7c70ac957745f9dd1.png",
        "sha256": "475a6e3998034cde1a10abbef4fa660f12449cbcb495f5a7c70ac957745f9dd1"
      },
      {
        "path": "/data2/k6tk/0f/0f55cce5ae926dadeaaabafbc128a79709b8b97ec547df6badc1116700264530.png",
        "sha256": "0f55cce5ae926dadeaaabafbc128a79709b8b97ec547df6badc1116700264530"
      },
      {
        "path": "/data2/k6tk/46/4671e0e9221b75dc4f80f08b7907150f33eab0fd0d09055d91ea0dbe05fece49.png",
        "sha256": "4671e0e9221b75dc4f80f08b7907150f33eab0fd0d09055d91ea0dbe05fece49"
      },
      {
        "path": "/data2/k6tk/90/90f2ee8736b0f0467c8b9e38486c98343fb6027d096e62a37c1d2ae626fd01be.png",
        "sha256": "90f2ee8736b0f0467c8b9e38486c98343fb6027d096e62a37c1d2ae626fd01be"
      },
      {
        "path": "/data2/k6tk/ac/ac0a2fce8a333355e0c9ecaaa1b917ae4e6348a2018bd9f088aa4c0e58c10efe.png",
        "sha256": "ac0a2fce8a333355e0c9ecaaa1b917ae4e6348a2018bd9f088aa4c0e58c10efe"
      }
    ],
    "options": [
      "A. more",
      "B. equal number",
      "C. fewer"
    ],
    "question": "Look through the room views and count each distinct object in 'table' and in 'stool'. Compared with the second category, how many instances does the first category have: more, fewer, or an equal number?",
    "timestamps": [
      0.0,
      2.3,
      4.7,
      7.0,
      9.4,
      11.7,
      14.0,
      16.4,
      18.7,
      21.0,
      23.4,
      25.7,
      28.1,
      30.4,
      32.7,
      35.1,
      37.4,
      39.8,
      42.1,
      44.4,
      46.8,
      49.1,
      51.5,
      53.8,
      56.1,
      58.5,
      60.8,
      63.1,
      65.5,
      67.8,
      70.2,
      72.5
    ],
    "total_num_frames": 726
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of stool; count each once across the frames.\nSo there are as many table instances as stool instances.\n</think>\n\nB",
  "validation_commit": ""
}
```

### 31. fbp_relcnt2_3424b73dc487fd1d448a521b

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-fcdcc4064101944af343a2951f955ffc88f49d117be13e018301409f7e821d8b",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42447250",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42447250.npz": "fa92e2c571c2b73f4ef408a86774d0c984e35126aa1c9293a8e065d687452c75",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42447250.npz",
    "raster_sha256": "fa92e2c571c2b73f4ef408a86774d0c984e35126aa1c9293a8e065d687452c75",
    "relative_count": {
      "a": "stool",
      "b": "table",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        5
      ],
      "ids_b": [
        1
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue422389",
      "scene_use_cap": 24,
      "source_qid": "b12ct_9cc6467536ab0f56e08a5a49",
      "source_row_sha256": "221838f740d1eb3d167c49113e359840f77820de40c16239fdb0ab3d6c08fde1",
      "source_use_cap": 8,
      "template_id": 10,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_3424b73dc487fd1d448a521b",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vc5e8921531ef",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      98,
      196,
      295,
      393,
      491,
      589,
      687,
      786,
      884,
      982,
      1080,
      1178,
      1277,
      1375,
      1473,
      1571,
      1669,
      1767,
      1866,
      1964,
      2062,
      2160,
      2258,
      2357,
      2455,
      2553,
      2651,
      2749,
      2848,
      2946,
      3044
    ],
    "frames": [
      {
        "path": "/data2/k6tk/e6/e6f9df65bb2af8476d4f7ee4906ced9442ac41dfaab6cff996e59a28f61b2c35.png",
        "sha256": "e6f9df65bb2af8476d4f7ee4906ced9442ac41dfaab6cff996e59a28f61b2c35"
      },
      {
        "path": "/data2/k6tk/77/77d9bdac855897515ea65b8349f2c9327d1b38a3013d8b89f0e2f35a6ef1f872.png",
        "sha256": "77d9bdac855897515ea65b8349f2c9327d1b38a3013d8b89f0e2f35a6ef1f872"
      },
      {
        "path": "/data2/k6tk/fc/fc601c4a1a28af5b1c7ac6b2d60052ceb9e56726e0bd7d9b05499938529b8e7f.png",
        "sha256": "fc601c4a1a28af5b1c7ac6b2d60052ceb9e56726e0bd7d9b05499938529b8e7f"
      },
      {
        "path": "/data2/k6tk/a7/a71034343e8d81c396e42b0c59178f0ab955e3c09b7bc4ddd29aafb59be7a951.png",
        "sha256": "a71034343e8d81c396e42b0c59178f0ab955e3c09b7bc4ddd29aafb59be7a951"
      },
      {
        "path": "/data2/k6tk/99/990a91f57fbe7e0958014fa3c85a3132137aaa8f1fd1c9320236886b6b526b98.png",
        "sha256": "990a91f57fbe7e0958014fa3c85a3132137aaa8f1fd1c9320236886b6b526b98"
      },
      {
        "path": "/data2/k6tk/9c/9c8710416b7a16c309697417feb8325eab141a979f9f909eb46cf70922c1483f.png",
        "sha256": "9c8710416b7a16c309697417feb8325eab141a979f9f909eb46cf70922c1483f"
      },
      {
        "path": "/data2/k6tk/fe/fec08b3ece432bb5c89a35cdde67b324f992addfeadc31bd00ed635d3a60d31a.png",
        "sha256": "fec08b3ece432bb5c89a35cdde67b324f992addfeadc31bd00ed635d3a60d31a"
      },
      {
        "path": "/data2/k6tk/4f/4fb5180bd67aec2644d768aa8cda6d47cb9c375348b90e49e2e345b9dd37046e.png",
        "sha256": "4fb5180bd67aec2644d768aa8cda6d47cb9c375348b90e49e2e345b9dd37046e"
      },
      {
        "path": "/data2/k6tk/8b/8bad59d6fc6d8dc6f00315f6a7bfbf12fc643fe5bca2ec01156956c70b97936e.png",
        "sha256": "8bad59d6fc6d8dc6f00315f6a7bfbf12fc643fe5bca2ec01156956c70b97936e"
      },
      {
        "path": "/data2/k6tk/9b/9b62276af273d49bb7add7404ecdf3d46a0cc686c57494c1b6fb39c7af6977c4.png",
        "sha256": "9b62276af273d49bb7add7404ecdf3d46a0cc686c57494c1b6fb39c7af6977c4"
      },
      {
        "path": "/data2/k6tk/83/836ce63aeebd52fd8c7fbf3faae8e66d29c4a0c288394f20a24cc513d9ce1f62.png",
        "sha256": "836ce63aeebd52fd8c7fbf3faae8e66d29c4a0c288394f20a24cc513d9ce1f62"
      },
      {
        "path": "/data2/k6tk/d9/d95a8f40fdfc112283f5975f54a9f2a8316110315d19696ffe1646f15871b1a7.png",
        "sha256": "d95a8f40fdfc112283f5975f54a9f2a8316110315d19696ffe1646f15871b1a7"
      },
      {
        "path": "/data2/k6tk/9a/9a0c0d2437642e7ddb0ad00d83fbed2e5fb53bc72f3bbadced4c8e07d178da63.png",
        "sha256": "9a0c0d2437642e7ddb0ad00d83fbed2e5fb53bc72f3bbadced4c8e07d178da63"
      },
      {
        "path": "/data2/k6tk/92/923483d4874930bd7fe23f52c8852d4c6e04009ef872e07f7020f3a431703e96.png",
        "sha256": "923483d4874930bd7fe23f52c8852d4c6e04009ef872e07f7020f3a431703e96"
      },
      {
        "path": "/data2/k6tk/2a/2afac53f2a02b6f721dd3a74f9a543f54eaa6343d8a378eac311a245fcb1dd74.png",
        "sha256": "2afac53f2a02b6f721dd3a74f9a543f54eaa6343d8a378eac311a245fcb1dd74"
      },
      {
        "path": "/data2/k6tk/22/225613998fe398e2d4298ef8bab1441988e1aeb59c4a6e3196950cacaff34490.png",
        "sha256": "225613998fe398e2d4298ef8bab1441988e1aeb59c4a6e3196950cacaff34490"
      },
      {
        "path": "/data2/k6tk/a2/a2195cccbef8cdbef4a9f327185640f04c75f7914d3e1b046627fc91b9fec7ca.png",
        "sha256": "a2195cccbef8cdbef4a9f327185640f04c75f7914d3e1b046627fc91b9fec7ca"
      },
      {
        "path": "/data2/k6tk/ba/ba399c85eb70c1cd68c625d184e99ee720e5f07651df10cc6c25e1314e8f8136.png",
        "sha256": "ba399c85eb70c1cd68c625d184e99ee720e5f07651df10cc6c25e1314e8f8136"
      },
      {
        "path": "/data2/k6tk/2d/2d8f646f70e1dd3323c4a2097eac507728584260f1ad17f2032db23074617c0c.png",
        "sha256": "2d8f646f70e1dd3323c4a2097eac507728584260f1ad17f2032db23074617c0c"
      },
      {
        "path": "/data2/k6tk/54/54ce416c4f579c746036b05be14bec589733f5daac0db349798a2fea86348ba9.png",
        "sha256": "54ce416c4f579c746036b05be14bec589733f5daac0db349798a2fea86348ba9"
      },
      {
        "path": "/data2/k6tk/e7/e71893c801455db65543032789572d4d804bd9f648bb672bb157b1944e3ba210.png",
        "sha256": "e71893c801455db65543032789572d4d804bd9f648bb672bb157b1944e3ba210"
      },
      {
        "path": "/data2/k6tk/b2/b2ee02df45b9789fbcc45080453cc0292ea3d39431592101fb6f1d2a779a05bd.png",
        "sha256": "b2ee02df45b9789fbcc45080453cc0292ea3d39431592101fb6f1d2a779a05bd"
      },
      {
        "path": "/data2/k6tk/d1/d18564c9b15b445206e2029840cd311f39009a2bf1657882dba5967ccd0e99cd.png",
        "sha256": "d18564c9b15b445206e2029840cd311f39009a2bf1657882dba5967ccd0e99cd"
      },
      {
        "path": "/data2/k6tk/49/4995a0b49cd8e70c8795a8a1bb44b0ee0113057e0537cb81abe47dbb6f42c3e6.png",
        "sha256": "4995a0b49cd8e70c8795a8a1bb44b0ee0113057e0537cb81abe47dbb6f42c3e6"
      },
      {
        "path": "/data2/k6tk/11/110c9f4a1864ec0d77d1bad8e1f67675782aca171e64f0b92209e90271d7fe36.png",
        "sha256": "110c9f4a1864ec0d77d1bad8e1f67675782aca171e64f0b92209e90271d7fe36"
      },
      {
        "path": "/data2/k6tk/1a/1a9c26000a86cba6b3ca5c7aee48118e1bde8d118416ec90c6b2e4b262071e6d.png",
        "sha256": "1a9c26000a86cba6b3ca5c7aee48118e1bde8d118416ec90c6b2e4b262071e6d"
      },
      {
        "path": "/data2/k6tk/a6/a607986a52f46685557fc75e5d6c2bb2310776c33a2c1045d9791b9c224f15fe.png",
        "sha256": "a607986a52f46685557fc75e5d6c2bb2310776c33a2c1045d9791b9c224f15fe"
      },
      {
        "path": "/data2/k6tk/39/39fcd0c7f2c530e6a91f127f8ef8fc88153633ee36be661f45babc14d8c9e374.png",
        "sha256": "39fcd0c7f2c530e6a91f127f8ef8fc88153633ee36be661f45babc14d8c9e374"
      },
      {
        "path": "/data2/k6tk/a3/a377a81522f761d0d57c14749f24a7f610ea7d1f1893291b338991d58a3ea73a.png",
        "sha256": "a377a81522f761d0d57c14749f24a7f610ea7d1f1893291b338991d58a3ea73a"
      },
      {
        "path": "/data2/k6tk/df/dfc21f8fdc7b1e68056e6447a5d62b51fcd3ec9aa7ecb63d55aef16b54d9effb.png",
        "sha256": "dfc21f8fdc7b1e68056e6447a5d62b51fcd3ec9aa7ecb63d55aef16b54d9effb"
      },
      {
        "path": "/data2/k6tk/d3/d3326713046c7a6ad29cfff33efe2279706f5af5459c78309b8cecea58110641.png",
        "sha256": "d3326713046c7a6ad29cfff33efe2279706f5af5459c78309b8cecea58110641"
      },
      {
        "path": "/data2/k6tk/7e/7ef21b4f39dddf15078190d4fc0722ffd4314dc9aec0b4975fc21b24f70e3c60.png",
        "sha256": "7ef21b4f39dddf15078190d4fc0722ffd4314dc9aec0b4975fc21b24f70e3c60"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Assess the numbers of objects belonging to 'stool' and 'table' without counting repeat views twice. Which choice gives the comparison for 'stool' against 'table'?",
    "timestamps": [
      0.0,
      9.8,
      19.6,
      29.5,
      39.3,
      49.1,
      58.9,
      68.7,
      78.6,
      88.4,
      98.2,
      108.0,
      117.8,
      127.7,
      137.5,
      147.3,
      157.1,
      166.9,
      176.7,
      186.6,
      196.4,
      206.2,
      216.0,
      225.8,
      235.7,
      245.5,
      255.3,
      265.1,
      274.9,
      284.8,
      294.6,
      304.4
    ],
    "total_num_frames": 3045
  },
  "target": "<think>\nlocate the distinct instances of stool; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are as many stool instances as table instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 32. fbp_relcnt2_aaa9852ce6d9fe391bb8e8f9

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-8ce3f626141f5010c6bc09594f0acd98167e04a3658e2172ecb2dfe6734d4f89",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/47331920",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/47331920.npz": "f82ffb591a5dbfd729c03f5d72692237c61bb5182eed0c2a1fcf3e39dcb2fb61",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "47331920.npz",
    "raster_sha256": "f82ffb591a5dbfd729c03f5d72692237c61bb5182eed0c2a1fcf3e39dcb2fb61",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "tie",
      "count_a": 2,
      "count_b": 2,
      "ids_a": [
        3,
        6
      ],
      "ids_b": [
        2,
        10
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue470826",
      "scene_use_cap": 24,
      "source_qid": "b12ct_29c935992620d2933641ab18",
      "source_row_sha256": "13bd822e61db64a706d94a94851ac6d916164028e3622503cbdbe3b408bfbad2",
      "source_use_cap": 8,
      "template_id": 11,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_aaa9852ce6d9fe391bb8e8f9",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vd635e4665e50",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      19,
      39,
      58,
      77,
      97,
      116,
      135,
      155,
      174,
      194,
      213,
      232,
      252,
      271,
      290,
      310,
      329,
      348,
      368,
      387,
      406,
      426,
      445,
      465,
      484,
      503,
      523,
      542,
      561,
      581,
      600
    ],
    "frames": [
      {
        "path": "/data2/k6tk/84/8424d29d3062d8d8192b8735c50c5236935dab9d6c6a3eff1681fd7b2479a7bf.png",
        "sha256": "8424d29d3062d8d8192b8735c50c5236935dab9d6c6a3eff1681fd7b2479a7bf"
      },
      {
        "path": "/data2/k6tk/f0/f087f81a37d979c833f28d10ad32f14f5ae4502f8f002b14939a01617c94d1b0.png",
        "sha256": "f087f81a37d979c833f28d10ad32f14f5ae4502f8f002b14939a01617c94d1b0"
      },
      {
        "path": "/data2/k6tk/db/db53562f5482b170e9fd6ae4d007430743aaa56a409a37201429d93c46a0bdc8.png",
        "sha256": "db53562f5482b170e9fd6ae4d007430743aaa56a409a37201429d93c46a0bdc8"
      },
      {
        "path": "/data2/k6tk/b7/b71bdee686f03c6cd29ccea4cc3140f424b6980c38d1b2620af6dfbf78d4f05d.png",
        "sha256": "b71bdee686f03c6cd29ccea4cc3140f424b6980c38d1b2620af6dfbf78d4f05d"
      },
      {
        "path": "/data2/k6tk/19/191d16ae2eded4524d339aa49b8fcdef2c4008b44035525d47e2535781714cec.png",
        "sha256": "191d16ae2eded4524d339aa49b8fcdef2c4008b44035525d47e2535781714cec"
      },
      {
        "path": "/data2/k6tk/1a/1a6c4a3c57cb1b1ce6701df93b3aa038fae4db9b160d5a8395ba2163834e3d34.png",
        "sha256": "1a6c4a3c57cb1b1ce6701df93b3aa038fae4db9b160d5a8395ba2163834e3d34"
      },
      {
        "path": "/data2/k6tk/e8/e85e71cecfeded8835ef36bbad8b1c92e3b455a255c45b2a40c8b3d909560ff0.png",
        "sha256": "e85e71cecfeded8835ef36bbad8b1c92e3b455a255c45b2a40c8b3d909560ff0"
      },
      {
        "path": "/data2/k6tk/1b/1b11d4294fae5a510596ca9e8869d00fa8baa64d29545f3f3e9723a9596cde0c.png",
        "sha256": "1b11d4294fae5a510596ca9e8869d00fa8baa64d29545f3f3e9723a9596cde0c"
      },
      {
        "path": "/data2/k6tk/41/416595f058762a8845553329006ec9d97e74d68da0bc2931325bc029df92413f.png",
        "sha256": "416595f058762a8845553329006ec9d97e74d68da0bc2931325bc029df92413f"
      },
      {
        "path": "/data2/k6tk/72/72b887cca53a7cf6331e47aa49553dea9802bd071ab3eb1d76fa6c0fe1878434.png",
        "sha256": "72b887cca53a7cf6331e47aa49553dea9802bd071ab3eb1d76fa6c0fe1878434"
      },
      {
        "path": "/data2/k6tk/ad/adeb566080cc2de81a037f45846787c075ad57d3b634a429db453b42d8a15baa.png",
        "sha256": "adeb566080cc2de81a037f45846787c075ad57d3b634a429db453b42d8a15baa"
      },
      {
        "path": "/data2/k6tk/29/29bed005cba0cdd88f4896f86fcc6f0367bd5db1f677fd88a7a8ff2d11cfb55e.png",
        "sha256": "29bed005cba0cdd88f4896f86fcc6f0367bd5db1f677fd88a7a8ff2d11cfb55e"
      },
      {
        "path": "/data2/k6tk/99/9989b2f8f63487b9a19865c1a7533d3bb2c49aa0e6c6ac9ccb0d60a4e1fc2c8d.png",
        "sha256": "9989b2f8f63487b9a19865c1a7533d3bb2c49aa0e6c6ac9ccb0d60a4e1fc2c8d"
      },
      {
        "path": "/data2/k6tk/5c/5c41a989ccd6e4b4904cee1b016703c9c3de55ef05259c71591657ff07e15a82.png",
        "sha256": "5c41a989ccd6e4b4904cee1b016703c9c3de55ef05259c71591657ff07e15a82"
      },
      {
        "path": "/data2/k6tk/98/980344bb76e253a60338ed8f09a30842c998007bc76f3086679407a7094a7a74.png",
        "sha256": "980344bb76e253a60338ed8f09a30842c998007bc76f3086679407a7094a7a74"
      },
      {
        "path": "/data2/k6tk/2d/2d9afcdf6d6084d56fb5900db7233ec3690460a3c78755c93aeecb6a79d48f7b.png",
        "sha256": "2d9afcdf6d6084d56fb5900db7233ec3690460a3c78755c93aeecb6a79d48f7b"
      },
      {
        "path": "/data2/k6tk/20/20c92a7d18c981a4543e795f2d69abb14e30084e06e782fad621c38cd9f9f630.png",
        "sha256": "20c92a7d18c981a4543e795f2d69abb14e30084e06e782fad621c38cd9f9f630"
      },
      {
        "path": "/data2/k6tk/ff/ffb37efafb1d9a91ec374b284742f9c13b21bb9ac7886b9c64d5693f1eccb32b.png",
        "sha256": "ffb37efafb1d9a91ec374b284742f9c13b21bb9ac7886b9c64d5693f1eccb32b"
      },
      {
        "path": "/data2/k6tk/22/223031fabb6acbed512da2bcfc86c883b7d50b720a603389881877f682bf122c.png",
        "sha256": "223031fabb6acbed512da2bcfc86c883b7d50b720a603389881877f682bf122c"
      },
      {
        "path": "/data2/k6tk/32/321fa3f14d20c70a716a6c405759d1f5f8725d506d20febb19be01eedb6a6ef0.png",
        "sha256": "321fa3f14d20c70a716a6c405759d1f5f8725d506d20febb19be01eedb6a6ef0"
      },
      {
        "path": "/data2/k6tk/e5/e58191b00a82d45454a83a8fbf5d361098dd48a54706faad213138835f67a1af.png",
        "sha256": "e58191b00a82d45454a83a8fbf5d361098dd48a54706faad213138835f67a1af"
      },
      {
        "path": "/data2/k6tk/f4/f4fdc3f1b54f0e3d8f2092f29a7d4104a32e1dfa17c2153df32fdc7add4a1d77.png",
        "sha256": "f4fdc3f1b54f0e3d8f2092f29a7d4104a32e1dfa17c2153df32fdc7add4a1d77"
      },
      {
        "path": "/data2/k6tk/f9/f90a168e102bb9da52e34fc7d6e25eea744e96742ec0dd02985a4306e4069a79.png",
        "sha256": "f90a168e102bb9da52e34fc7d6e25eea744e96742ec0dd02985a4306e4069a79"
      },
      {
        "path": "/data2/k6tk/bf/bf2f9d25ef1ac395311a7c64e8d8470581bccae03dd12feea8fbe3e7ca78853f.png",
        "sha256": "bf2f9d25ef1ac395311a7c64e8d8470581bccae03dd12feea8fbe3e7ca78853f"
      },
      {
        "path": "/data2/k6tk/f0/f0c3b9f908df04d09acc05003db0fa581b03e5230ab274b1e83b570c178e949e.png",
        "sha256": "f0c3b9f908df04d09acc05003db0fa581b03e5230ab274b1e83b570c178e949e"
      },
      {
        "path": "/data2/k6tk/32/3224420a1e04dd6d64524dc7d443f690f0e15903aca70012d8941eeaa6e4488e.png",
        "sha256": "3224420a1e04dd6d64524dc7d443f690f0e15903aca70012d8941eeaa6e4488e"
      },
      {
        "path": "/data2/k6tk/b0/b099f897f3ac3e37b68e26521a2eff7262408f0e370da52603e29d415876cfa7.png",
        "sha256": "b099f897f3ac3e37b68e26521a2eff7262408f0e370da52603e29d415876cfa7"
      },
      {
        "path": "/data2/k6tk/42/42c04d3a74c0e1ba63125bf972e611e150ca080e92f67167a87e16b5218ca597.png",
        "sha256": "42c04d3a74c0e1ba63125bf972e611e150ca080e92f67167a87e16b5218ca597"
      },
      {
        "path": "/data2/k6tk/a4/a4e6ecae56025f1d8475dff3a262f27ef3678df077d2fc339e32705996d574a3.png",
        "sha256": "a4e6ecae56025f1d8475dff3a262f27ef3678df077d2fc339e32705996d574a3"
      },
      {
        "path": "/data2/k6tk/5a/5a6d4c1fac9764522072520ba6e348b142654cd15b1a9e272d268e4f25f21ba4.png",
        "sha256": "5a6d4c1fac9764522072520ba6e348b142654cd15b1a9e272d268e4f25f21ba4"
      },
      {
        "path": "/data2/k6tk/4b/4bb70b1603a0f4749e9682b84b81889457b2497ed18ad13081cfd02da252495a.png",
        "sha256": "4bb70b1603a0f4749e9682b84b81889457b2497ed18ad13081cfd02da252495a"
      },
      {
        "path": "/data2/k6tk/79/794e5f972eca70473c70ad71d4879ebaf05a13fbe52cbbb13b54f2e115730c9d.png",
        "sha256": "794e5f972eca70473c70ad71d4879ebaf05a13fbe52cbbb13b54f2e115730c9d"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Start with a count of the room's distinct 'table' objects, then count its distinct 'chair' objects. Select the option that relates the first count to the second.",
    "timestamps": [
      0.0,
      1.9,
      3.9,
      5.8,
      7.7,
      9.7,
      11.6,
      13.5,
      15.5,
      17.4,
      19.4,
      21.3,
      23.2,
      25.2,
      27.1,
      29.0,
      31.0,
      32.9,
      34.8,
      36.8,
      38.7,
      40.6,
      42.6,
      44.5,
      46.5,
      48.4,
      50.3,
      52.3,
      54.2,
      56.1,
      58.1,
      60.0
    ],
    "total_num_frames": 601
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many table instances as chair instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 33. fbp_relcnt2_4a4a434ee0e374b20ab84f28

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-5664fd67a4aa497df8998efa57f549c998ef5bc98c455b09ec7fea29163c2e95",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/45261406",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/45261406.npz": "f1776da8fb72e92a52c119c1502621f6516453e484b8f9e81d942145e13be39a",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "45261406.npz",
    "raster_sha256": "f1776da8fb72e92a52c119c1502621f6516453e484b8f9e81d942145e13be39a",
    "relative_count": {
      "a": "table",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        0
      ],
      "ids_b": [
        2
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue467252",
      "scene_use_cap": 24,
      "source_qid": "b12ct_67fb1e40241715eacaec55bd",
      "source_row_sha256": "d20f2e417986aa1d495936dc42610cb1c5cf949f6618793a709bc4cde18db46b",
      "source_use_cap": 8,
      "template_id": 12,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_4a4a434ee0e374b20ab84f28",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v6aa7c3dc8600",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      44,
      88,
      133,
      177,
      221,
      265,
      309,
      354,
      398,
      442,
      486,
      530,
      575,
      619,
      663,
      707,
      751,
      795,
      840,
      884,
      928,
      972,
      1016,
      1061,
      1105,
      1149,
      1193,
      1237,
      1282,
      1326,
      1370
    ],
    "frames": [
      {
        "path": "/data2/k6tk/c8/c833faf4cb5e99aa8f3e10a4ad970e551f893de243591aef82bdbb9e95eb7515.png",
        "sha256": "c833faf4cb5e99aa8f3e10a4ad970e551f893de243591aef82bdbb9e95eb7515"
      },
      {
        "path": "/data2/k6tk/d5/d5a797f7cbad92abb6608f934854cde2e41784859451ccb74aadc18373e10127.png",
        "sha256": "d5a797f7cbad92abb6608f934854cde2e41784859451ccb74aadc18373e10127"
      },
      {
        "path": "/data2/k6tk/e6/e6c430aae20744273b562ac7ab883a652e6d5d7532ffeb37c1213fc4bda1f87d.png",
        "sha256": "e6c430aae20744273b562ac7ab883a652e6d5d7532ffeb37c1213fc4bda1f87d"
      },
      {
        "path": "/data2/k6tk/73/733d66018b18244b1559ac6891f7c71ea76719fdb1bdfc744e2a686a09fb9937.png",
        "sha256": "733d66018b18244b1559ac6891f7c71ea76719fdb1bdfc744e2a686a09fb9937"
      },
      {
        "path": "/data2/k6tk/99/99c07690f4b3484d0d7a2cf61ec7f7fdf46d29786675f0159e1a84d230a6dd12.png",
        "sha256": "99c07690f4b3484d0d7a2cf61ec7f7fdf46d29786675f0159e1a84d230a6dd12"
      },
      {
        "path": "/data2/k6tk/81/81f52f2120c2b0bdf630b4582e35dfac7d002f71aa64a8adb1383526b9c08292.png",
        "sha256": "81f52f2120c2b0bdf630b4582e35dfac7d002f71aa64a8adb1383526b9c08292"
      },
      {
        "path": "/data2/k6tk/93/93efd0154639fc35045aee6accbb3814d024b82574a590c6d0859f6f21d9e118.png",
        "sha256": "93efd0154639fc35045aee6accbb3814d024b82574a590c6d0859f6f21d9e118"
      },
      {
        "path": "/data2/k6tk/e4/e448fa2a5c017ae81d1eae3523c99abf431761cf5505171d6603bc5e814a0b50.png",
        "sha256": "e448fa2a5c017ae81d1eae3523c99abf431761cf5505171d6603bc5e814a0b50"
      },
      {
        "path": "/data2/k6tk/a1/a1657164bd482899566436ffa70b53c8adcfca8995b23d5fd40c7cda9c0656a0.png",
        "sha256": "a1657164bd482899566436ffa70b53c8adcfca8995b23d5fd40c7cda9c0656a0"
      },
      {
        "path": "/data2/k6tk/99/99e6d2aadbcb46750807946819182df4bc3caa5038ead6111675cf86ff63562f.png",
        "sha256": "99e6d2aadbcb46750807946819182df4bc3caa5038ead6111675cf86ff63562f"
      },
      {
        "path": "/data2/k6tk/36/36aee44001b1e774181c7443af4f87fdbaedba785284a75eecb4ad0d1a15429c.png",
        "sha256": "36aee44001b1e774181c7443af4f87fdbaedba785284a75eecb4ad0d1a15429c"
      },
      {
        "path": "/data2/k6tk/da/dae6cc63aac29ad0fa6f86a6a202a5a538f0a14e4adf28c28216c9f28a7a3a47.png",
        "sha256": "dae6cc63aac29ad0fa6f86a6a202a5a538f0a14e4adf28c28216c9f28a7a3a47"
      },
      {
        "path": "/data2/k6tk/e1/e1c4abdf4dffd973d23177ba6fd5728525b04fc8a4b4cd6f60854c447a437a51.png",
        "sha256": "e1c4abdf4dffd973d23177ba6fd5728525b04fc8a4b4cd6f60854c447a437a51"
      },
      {
        "path": "/data2/k6tk/74/749a9f61dfd21d31d3394ab28e70415c8b9cda073f51fca8d63ba7e5afb07b6f.png",
        "sha256": "749a9f61dfd21d31d3394ab28e70415c8b9cda073f51fca8d63ba7e5afb07b6f"
      },
      {
        "path": "/data2/k6tk/b3/b33b75ecc94626f4f9503568fe3a668bb965aa2a7f3bdbce815b299da15b40d3.png",
        "sha256": "b33b75ecc94626f4f9503568fe3a668bb965aa2a7f3bdbce815b299da15b40d3"
      },
      {
        "path": "/data2/k6tk/c8/c81ef6f251540cd60a413cb9fa9060ea45f882bbccca7c87707632db57f75b40.png",
        "sha256": "c81ef6f251540cd60a413cb9fa9060ea45f882bbccca7c87707632db57f75b40"
      },
      {
        "path": "/data2/k6tk/aa/aaab410c28d542b477e4a0b4ccd60767276d51d3a405488bfa115a2621562e8d.png",
        "sha256": "aaab410c28d542b477e4a0b4ccd60767276d51d3a405488bfa115a2621562e8d"
      },
      {
        "path": "/data2/k6tk/62/62c9b94d80e1b15d8e242fa6a3972d6aded5accf4018680445b3096ef8b0282a.png",
        "sha256": "62c9b94d80e1b15d8e242fa6a3972d6aded5accf4018680445b3096ef8b0282a"
      },
      {
        "path": "/data2/k6tk/86/86292a389f6572f2563fc8b207141568e24cef841c45d78dcbb53528f5c18eb4.png",
        "sha256": "86292a389f6572f2563fc8b207141568e24cef841c45d78dcbb53528f5c18eb4"
      },
      {
        "path": "/data2/k6tk/de/dea3c5cbb2acc4b7069074a525da1d3bf432874ff6743c21a9d870ed86751dab.png",
        "sha256": "dea3c5cbb2acc4b7069074a525da1d3bf432874ff6743c21a9d870ed86751dab"
      },
      {
        "path": "/data2/k6tk/95/95baa987bf109bafac7faf53e7b90dc39bb57c76b2f4c338b4aa5d3a1ecd4f16.png",
        "sha256": "95baa987bf109bafac7faf53e7b90dc39bb57c76b2f4c338b4aa5d3a1ecd4f16"
      },
      {
        "path": "/data2/k6tk/29/29b3143db3264378a824aaeb327c6215d4a3febb87c2bf17d20ff6027eaa6d85.png",
        "sha256": "29b3143db3264378a824aaeb327c6215d4a3febb87c2bf17d20ff6027eaa6d85"
      },
      {
        "path": "/data2/k6tk/3d/3de2ed9bbc1b02185270505196847262867b1e394590e12358ed5ce866551742.png",
        "sha256": "3de2ed9bbc1b02185270505196847262867b1e394590e12358ed5ce866551742"
      },
      {
        "path": "/data2/k6tk/4f/4f7ce3b41644345ae4c6e6b630fdde63ff3af9c5124c01f9bf42b8037c8bb4f3.png",
        "sha256": "4f7ce3b41644345ae4c6e6b630fdde63ff3af9c5124c01f9bf42b8037c8bb4f3"
      },
      {
        "path": "/data2/k6tk/b7/b7b5d21b9e3568c0ee41cfc322fe2712cdb7fe8eb1e0110e23eff4dc9d65a070.png",
        "sha256": "b7b5d21b9e3568c0ee41cfc322fe2712cdb7fe8eb1e0110e23eff4dc9d65a070"
      },
      {
        "path": "/data2/k6tk/26/2612ac08c19b23ea947dd00ae78221f1f584e8351c7e0063cb40e6534db5b90a.png",
        "sha256": "2612ac08c19b23ea947dd00ae78221f1f584e8351c7e0063cb40e6534db5b90a"
      },
      {
        "path": "/data2/k6tk/29/29309f7296da0aaa67dd3e2afacbe37d4daa40db6be98fef25615fdfedadbd32.png",
        "sha256": "29309f7296da0aaa67dd3e2afacbe37d4daa40db6be98fef25615fdfedadbd32"
      },
      {
        "path": "/data2/k6tk/f4/f4cfaf39a24a0f1f2c9f83aed7e65accca5f7edef756f0bf57d864ea755777a2.png",
        "sha256": "f4cfaf39a24a0f1f2c9f83aed7e65accca5f7edef756f0bf57d864ea755777a2"
      },
      {
        "path": "/data2/k6tk/a8/a863382f391ee64852793cc7d12f25131972f818a726bf3162ae68fb66b4afe1.png",
        "sha256": "a863382f391ee64852793cc7d12f25131972f818a726bf3162ae68fb66b4afe1"
      },
      {
        "path": "/data2/k6tk/7c/7c720d6c9e58d693be901db53f66f7d8f620f3a1167757ae3a58920a46a26a4d.png",
        "sha256": "7c720d6c9e58d693be901db53f66f7d8f620f3a1167757ae3a58920a46a26a4d"
      },
      {
        "path": "/data2/k6tk/fb/fb73cf332e1086e9605af5344a445691241dbbd3b179e8b04832c81e5f2cc70a.png",
        "sha256": "fb73cf332e1086e9605af5344a445691241dbbd3b179e8b04832c81e5f2cc70a"
      },
      {
        "path": "/data2/k6tk/29/2914890ef33cd6a0ff3b3fbad4ba392e540f156351596d17bdbb87cb5048850b.png",
        "sha256": "2914890ef33cd6a0ff3b3fbad4ba392e540f156351596d17bdbb87cb5048850b"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Treat 'table' and 'tv' as separate categories when counting objects in the scene. Which answer fits the number in 'table' relative to the number in 'tv'?",
    "timestamps": [
      0.0,
      4.4,
      8.8,
      13.3,
      17.7,
      22.1,
      26.5,
      30.9,
      35.4,
      39.8,
      44.2,
      48.6,
      53.0,
      57.5,
      61.9,
      66.3,
      70.7,
      75.1,
      79.5,
      84.0,
      88.4,
      92.8,
      97.2,
      101.6,
      106.1,
      110.5,
      114.9,
      119.3,
      123.7,
      128.2,
      132.6,
      137.0
    ],
    "total_num_frames": 1371
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many table instances as tv instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 34. fbp_relcnt2_b2f963b39f68cf56ab993f21

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-d0828190895f7a29315fa89c652214556c46648cf1a7965fc1ec785a4b5d17ef",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41159454",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41159454.npz": "434b3a589ee4e1f32a4ae4c9e8150eb5f783fc56fbf0d828df895c81b2d2e54c",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41159454.npz",
    "raster_sha256": "434b3a589ee4e1f32a4ae4c9e8150eb5f783fc56fbf0d828df895c81b2d2e54c",
    "relative_count": {
      "a": "table",
      "b": "chair",
      "bucket": "tie",
      "count_a": 3,
      "count_b": 3,
      "ids_a": [
        1,
        5,
        6
      ],
      "ids_b": [
        0,
        2,
        3
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue381628",
      "scene_use_cap": 24,
      "source_qid": "b12ct_159a30d22ecf72043b97f04d",
      "source_row_sha256": "9333787db9a726d4cb81748909363bc203442c8d04fe3f62e7f17956317d562a",
      "source_use_cap": 8,
      "template_id": 13,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_b2f963b39f68cf56ab993f21",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v363b9ad6874b",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      62,
      125,
      187,
      250,
      312,
      374,
      437,
      499,
      561,
      624,
      686,
      749,
      811,
      873,
      936,
      998,
      1061,
      1123,
      1185,
      1248,
      1310,
      1373,
      1435,
      1497,
      1560,
      1622,
      1684,
      1747,
      1809,
      1872,
      1934
    ],
    "frames": [
      {
        "path": "/data2/k6tk/69/69521fe6206b7319d00b63954eb38965ee10a78dce51fd2461d2ebc60612c3d9.png",
        "sha256": "69521fe6206b7319d00b63954eb38965ee10a78dce51fd2461d2ebc60612c3d9"
      },
      {
        "path": "/data2/k6tk/a4/a4cb041282a8b72ad57c62f8e2a2604eb0e7d79dfc235a4378e5f07ead53c8bc.png",
        "sha256": "a4cb041282a8b72ad57c62f8e2a2604eb0e7d79dfc235a4378e5f07ead53c8bc"
      },
      {
        "path": "/data2/k6tk/4c/4c8de8038517c4dbc62ae2acff3ca72147b0756ae40b40f56e395f37b6e7cbdd.png",
        "sha256": "4c8de8038517c4dbc62ae2acff3ca72147b0756ae40b40f56e395f37b6e7cbdd"
      },
      {
        "path": "/data2/k6tk/56/566715b3743ad6b7fd52941335c6f342553d242759d287f22e60faabb2571a83.png",
        "sha256": "566715b3743ad6b7fd52941335c6f342553d242759d287f22e60faabb2571a83"
      },
      {
        "path": "/data2/k6tk/b5/b57924d41756d21de8a42c9c98ba4b2f1134af4203d22fae31a027d51665c0f1.png",
        "sha256": "b57924d41756d21de8a42c9c98ba4b2f1134af4203d22fae31a027d51665c0f1"
      },
      {
        "path": "/data2/k6tk/29/294d311e2f3f19c4f87c02ab786299474ba859d906ce092176423cf8f693c067.png",
        "sha256": "294d311e2f3f19c4f87c02ab786299474ba859d906ce092176423cf8f693c067"
      },
      {
        "path": "/data2/k6tk/d3/d35c204b69012352be41aa93ac3cd24cf4658fc7be6e67ebe88dbc96f2f9b4b8.png",
        "sha256": "d35c204b69012352be41aa93ac3cd24cf4658fc7be6e67ebe88dbc96f2f9b4b8"
      },
      {
        "path": "/data2/k6tk/b4/b4a7fb9f18c700be3225993416d986051fb24789c5ae669180af4945c2836e0c.png",
        "sha256": "b4a7fb9f18c700be3225993416d986051fb24789c5ae669180af4945c2836e0c"
      },
      {
        "path": "/data2/k6tk/71/717bf319a67e9e129e212fca12a667aa50c3c93fcdcd4ddaa4982e5189fdf8b2.png",
        "sha256": "717bf319a67e9e129e212fca12a667aa50c3c93fcdcd4ddaa4982e5189fdf8b2"
      },
      {
        "path": "/data2/k6tk/14/14fb177471cd1d7e6d53060e56e3e56d47571329e3353d251875ed0627d17e4b.png",
        "sha256": "14fb177471cd1d7e6d53060e56e3e56d47571329e3353d251875ed0627d17e4b"
      },
      {
        "path": "/data2/k6tk/e0/e0f6824556ea88eb13c9ddd6f65c64eb9a6795c906544c19b3474b04d703a929.png",
        "sha256": "e0f6824556ea88eb13c9ddd6f65c64eb9a6795c906544c19b3474b04d703a929"
      },
      {
        "path": "/data2/k6tk/86/867b55737cd8ed6fb4af944bd0199e3383d34cc54c0183de86c5de394ed954b7.png",
        "sha256": "867b55737cd8ed6fb4af944bd0199e3383d34cc54c0183de86c5de394ed954b7"
      },
      {
        "path": "/data2/k6tk/89/89523a4778bb430f9b9aefe654373701079810ec731e539c7543377ac7fdb08e.png",
        "sha256": "89523a4778bb430f9b9aefe654373701079810ec731e539c7543377ac7fdb08e"
      },
      {
        "path": "/data2/k6tk/9b/9bc1b860fc1f0e8ccdee0c17c6f85498f7384e28fc52861a044556e92469ac20.png",
        "sha256": "9bc1b860fc1f0e8ccdee0c17c6f85498f7384e28fc52861a044556e92469ac20"
      },
      {
        "path": "/data2/k6tk/80/80cc31cd383e8ab8175d98fa323ad29ea7451852780fda1e8a5390afe4702671.png",
        "sha256": "80cc31cd383e8ab8175d98fa323ad29ea7451852780fda1e8a5390afe4702671"
      },
      {
        "path": "/data2/k6tk/73/73618b14458dbbb04e295c5e240b5e9d55865cd9a5becbcaa9d5c3c8af401bdf.png",
        "sha256": "73618b14458dbbb04e295c5e240b5e9d55865cd9a5becbcaa9d5c3c8af401bdf"
      },
      {
        "path": "/data2/k6tk/ea/ea1ca8ae27d6719b3bd23be3442fa91b3705aaaa9c090e6b7089db0377988631.png",
        "sha256": "ea1ca8ae27d6719b3bd23be3442fa91b3705aaaa9c090e6b7089db0377988631"
      },
      {
        "path": "/data2/k6tk/70/70f2c93ce12d0e36ddacca36d1508c6a9016624aaa2c01d57b8f41a3991d7882.png",
        "sha256": "70f2c93ce12d0e36ddacca36d1508c6a9016624aaa2c01d57b8f41a3991d7882"
      },
      {
        "path": "/data2/k6tk/31/3142f16f710186488dea7892bbf5dc40bff3aeb8315453624e5d0cf2f6ff105a.png",
        "sha256": "3142f16f710186488dea7892bbf5dc40bff3aeb8315453624e5d0cf2f6ff105a"
      },
      {
        "path": "/data2/k6tk/03/0394df04ed435ad29746c194e52b00a3f10d2cf22d002ea27ffa962922a23b9d.png",
        "sha256": "0394df04ed435ad29746c194e52b00a3f10d2cf22d002ea27ffa962922a23b9d"
      },
      {
        "path": "/data2/k6tk/0a/0a0f4cfacc4fc254812d90b66edbdb01031e1b4b3cd6eaf71a74dee4a9a58f27.png",
        "sha256": "0a0f4cfacc4fc254812d90b66edbdb01031e1b4b3cd6eaf71a74dee4a9a58f27"
      },
      {
        "path": "/data2/k6tk/62/62589bdaa38fe87fcc1328dd9088f0e990773fcf9c7beea1f0d2a29abfbec722.png",
        "sha256": "62589bdaa38fe87fcc1328dd9088f0e990773fcf9c7beea1f0d2a29abfbec722"
      },
      {
        "path": "/data2/k6tk/fb/fbf30e263eefd6a9d1cfc7cccd5d4887b5b7563cb65d2b49b05084c433246797.png",
        "sha256": "fbf30e263eefd6a9d1cfc7cccd5d4887b5b7563cb65d2b49b05084c433246797"
      },
      {
        "path": "/data2/k6tk/9a/9a01d387c2d0e3e51d8240d281904e3f197b64d9b9757869bed72647c0ab4750.png",
        "sha256": "9a01d387c2d0e3e51d8240d281904e3f197b64d9b9757869bed72647c0ab4750"
      },
      {
        "path": "/data2/k6tk/2a/2ab77d457f614e86f9222265921170ffb26dba88e5b1851226743ed49cbe8c48.png",
        "sha256": "2ab77d457f614e86f9222265921170ffb26dba88e5b1851226743ed49cbe8c48"
      },
      {
        "path": "/data2/k6tk/46/468c6c87dedfee2eec84f5e066de2d5cada44031af22de9f9c03a8af4945ad8f.png",
        "sha256": "468c6c87dedfee2eec84f5e066de2d5cada44031af22de9f9c03a8af4945ad8f"
      },
      {
        "path": "/data2/k6tk/d1/d1de6c3e7b6a9baaa75e2627fc46c5a42664d42cfbcade4b53c6323320f2231c.png",
        "sha256": "d1de6c3e7b6a9baaa75e2627fc46c5a42664d42cfbcade4b53c6323320f2231c"
      },
      {
        "path": "/data2/k6tk/fb/fbc831e58098ddad985c21bf69f3af09a534101d1bd9effe9de23225f2c5ae08.png",
        "sha256": "fbc831e58098ddad985c21bf69f3af09a534101d1bd9effe9de23225f2c5ae08"
      },
      {
        "path": "/data2/k6tk/09/099bfa84e104a18b1713133c08a4be5d92ab059087fdee35399e32c1815fdc25.png",
        "sha256": "099bfa84e104a18b1713133c08a4be5d92ab059087fdee35399e32c1815fdc25"
      },
      {
        "path": "/data2/k6tk/52/52ef4ec66192885f69784b5171de4de1dbb10e622d1764aa3016d47df461b0bd.png",
        "sha256": "52ef4ec66192885f69784b5171de4de1dbb10e622d1764aa3016d47df461b0bd"
      },
      {
        "path": "/data2/k6tk/6d/6d95d7ad4e772336bd795a42fa230e63d993b1d29b60e0caea0d70f13b0c92f0.png",
        "sha256": "6d95d7ad4e772336bd795a42fa230e63d993b1d29b60e0caea0d70f13b0c92f0"
      },
      {
        "path": "/data2/k6tk/dc/dcded28866e45926aef0a6c2d7a3bf50c93d5e4cbe0e5a1658c5bef9246c5287.png",
        "sha256": "dcded28866e45926aef0a6c2d7a3bf50c93d5e4cbe0e5a1658c5bef9246c5287"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Review the video to establish a total for 'table' and a total for 'chair'. How should the 'table' total be classified when compared with the 'chair' total?",
    "timestamps": [
      0.0,
      6.2,
      12.5,
      18.7,
      25.0,
      31.2,
      37.4,
      43.7,
      49.9,
      56.1,
      62.4,
      68.6,
      74.9,
      81.1,
      87.3,
      93.6,
      99.8,
      106.1,
      112.3,
      118.5,
      124.8,
      131.0,
      137.3,
      143.5,
      149.7,
      156.0,
      162.2,
      168.4,
      174.7,
      180.9,
      187.2,
      193.4
    ],
    "total_num_frames": 1935
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of chair; count each once across the frames.\nSo there are as many table instances as chair instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 35. fbp_relcnt2_5a86b867060e90916fec2760

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-ae83cac8a89ea819af66139d8e76f8b460484a0a17484e30193ffac63af00b8e",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41125536",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41125536.npz": "3a6c9843063767e1842e10019d9ad850bf5233be3cd4260b94ee2eac98fd12cf",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41125536.npz",
    "raster_sha256": "3a6c9843063767e1842e10019d9ad850bf5233be3cd4260b94ee2eac98fd12cf",
    "relative_count": {
      "a": "stool",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        10
      ],
      "ids_b": [
        3
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue382435",
      "scene_use_cap": 24,
      "source_qid": "b12ct_6e887bc6d677c6b80a74a818",
      "source_row_sha256": "83abf189bbf44af5c4f0f244dd8f3c6b141e0411d36a71b74fd2096f8af96785",
      "source_use_cap": 8,
      "template_id": 14,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_5a86b867060e90916fec2760",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vc10ae382258a",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      41,
      82,
      123,
      164,
      205,
      245,
      286,
      327,
      368,
      409,
      450,
      491,
      532,
      573,
      614,
      654,
      695,
      736,
      777,
      818,
      859,
      900,
      941,
      982,
      1023,
      1063,
      1104,
      1145,
      1186,
      1227,
      1268
    ],
    "frames": [
      {
        "path": "/data2/k6tk/97/97f3fcd7f5a3adcf7efec9be2923996236075465a83c2a18c36685e1b4779321.png",
        "sha256": "97f3fcd7f5a3adcf7efec9be2923996236075465a83c2a18c36685e1b4779321"
      },
      {
        "path": "/data2/k6tk/a6/a6508ce2e13832797453b0ad62ecbae41e454aff16e60a040d80c7ad65b0d585.png",
        "sha256": "a6508ce2e13832797453b0ad62ecbae41e454aff16e60a040d80c7ad65b0d585"
      },
      {
        "path": "/data2/k6tk/1f/1f34fe6ac25823b795cefac648a5e838d29a87dc18333b20782e533e839aa78c.png",
        "sha256": "1f34fe6ac25823b795cefac648a5e838d29a87dc18333b20782e533e839aa78c"
      },
      {
        "path": "/data2/k6tk/c2/c29378024072cf1830e825599e3a8a9fcc8c87423dc7c93eada0cdf8a16d363c.png",
        "sha256": "c29378024072cf1830e825599e3a8a9fcc8c87423dc7c93eada0cdf8a16d363c"
      },
      {
        "path": "/data2/k6tk/64/6445bb7bae1d6967b2b8f455750e56b0b5a41f13d8b7f80b6244d513534a7342.png",
        "sha256": "6445bb7bae1d6967b2b8f455750e56b0b5a41f13d8b7f80b6244d513534a7342"
      },
      {
        "path": "/data2/k6tk/43/43d244f7b1d91a43ff12e320c838332517205ab9c6e946a9210b3c08c7d73499.png",
        "sha256": "43d244f7b1d91a43ff12e320c838332517205ab9c6e946a9210b3c08c7d73499"
      },
      {
        "path": "/data2/k6tk/d3/d33b50819822588ae144df1e6cc578391eaabebb3b21e939036292b41444ebcf.png",
        "sha256": "d33b50819822588ae144df1e6cc578391eaabebb3b21e939036292b41444ebcf"
      },
      {
        "path": "/data2/k6tk/5c/5c8f44e34907c27a3b28ba0f59a460f3357a0dd22416d73370df0a135bbc0c90.png",
        "sha256": "5c8f44e34907c27a3b28ba0f59a460f3357a0dd22416d73370df0a135bbc0c90"
      },
      {
        "path": "/data2/k6tk/f3/f32f94237656864a6b220f71e818272b4220ae51e59d646d39e82cd7c79378eb.png",
        "sha256": "f32f94237656864a6b220f71e818272b4220ae51e59d646d39e82cd7c79378eb"
      },
      {
        "path": "/data2/k6tk/8e/8e235eb7ab3fd96a7dceb636081c5a555d2857552ce85210f92df419ac39eb6b.png",
        "sha256": "8e235eb7ab3fd96a7dceb636081c5a555d2857552ce85210f92df419ac39eb6b"
      },
      {
        "path": "/data2/k6tk/6f/6f351e7b4b2838afb48e7febef8bde253675a37ef9fbf16c039f64d1ed177c4d.png",
        "sha256": "6f351e7b4b2838afb48e7febef8bde253675a37ef9fbf16c039f64d1ed177c4d"
      },
      {
        "path": "/data2/k6tk/08/085c398697f5dd2f79478799bff5c6dde95c7f014b312be9371ca0a93654dcce.png",
        "sha256": "085c398697f5dd2f79478799bff5c6dde95c7f014b312be9371ca0a93654dcce"
      },
      {
        "path": "/data2/k6tk/aa/aad222b22ed6580553b83c888b615b2e80dd20d1c8766a4677b09d18bad2cd13.png",
        "sha256": "aad222b22ed6580553b83c888b615b2e80dd20d1c8766a4677b09d18bad2cd13"
      },
      {
        "path": "/data2/k6tk/3c/3c1d7ff560662f07d636618f042781292dc054050dbd141e9eae82d8e0861f72.png",
        "sha256": "3c1d7ff560662f07d636618f042781292dc054050dbd141e9eae82d8e0861f72"
      },
      {
        "path": "/data2/k6tk/de/dede28d631f86fe46248896696a6dc89a65751770db330c8f8c3aa9ed51c6089.png",
        "sha256": "dede28d631f86fe46248896696a6dc89a65751770db330c8f8c3aa9ed51c6089"
      },
      {
        "path": "/data2/k6tk/ae/aebd7a92e6ebac60589dce78d17dcc359f5e5d27697f4f8a442d6ea927883fae.png",
        "sha256": "aebd7a92e6ebac60589dce78d17dcc359f5e5d27697f4f8a442d6ea927883fae"
      },
      {
        "path": "/data2/k6tk/c6/c6b06c17d017e602a1417fea2af5c615e9dba887e6c0515554b89595bc682433.png",
        "sha256": "c6b06c17d017e602a1417fea2af5c615e9dba887e6c0515554b89595bc682433"
      },
      {
        "path": "/data2/k6tk/1e/1e3a2fa07932aa4e56495fc5a29f1405748e3b8f4c3044b3040b119f7a89b67f.png",
        "sha256": "1e3a2fa07932aa4e56495fc5a29f1405748e3b8f4c3044b3040b119f7a89b67f"
      },
      {
        "path": "/data2/k6tk/0b/0b50b75f37ba3ad8e3ebb4ba5211274ba242b5b515d1c884360575ee4d76a690.png",
        "sha256": "0b50b75f37ba3ad8e3ebb4ba5211274ba242b5b515d1c884360575ee4d76a690"
      },
      {
        "path": "/data2/k6tk/9b/9be02c127b4863657ebc7e6ff99b9ea700e9011f2954223ce2502e8f5a3c9a4f.png",
        "sha256": "9be02c127b4863657ebc7e6ff99b9ea700e9011f2954223ce2502e8f5a3c9a4f"
      },
      {
        "path": "/data2/k6tk/a5/a5c0a7d0fe875d1d0b26853cf83ad202703ef136cd4587a5bf4078ee4560e43e.png",
        "sha256": "a5c0a7d0fe875d1d0b26853cf83ad202703ef136cd4587a5bf4078ee4560e43e"
      },
      {
        "path": "/data2/k6tk/e8/e82b93168c55f2d2a70827f649e64b8a1406199c8d8a2b6e7e0d03486bb77680.png",
        "sha256": "e82b93168c55f2d2a70827f649e64b8a1406199c8d8a2b6e7e0d03486bb77680"
      },
      {
        "path": "/data2/k6tk/45/4591183f261149f1bde5faf3d5ba71c5f8124b187aa906523f7dbfb97174d4ad.png",
        "sha256": "4591183f261149f1bde5faf3d5ba71c5f8124b187aa906523f7dbfb97174d4ad"
      },
      {
        "path": "/data2/k6tk/87/873eaec5cff1654fa6da4dacf3f3b94afdfcae3dc9df03bfbe907d58c9abfba2.png",
        "sha256": "873eaec5cff1654fa6da4dacf3f3b94afdfcae3dc9df03bfbe907d58c9abfba2"
      },
      {
        "path": "/data2/k6tk/47/47e0dcec7cb911e8eec0bbbbeb2bfbecde7d0ef3551de8005e6370e0f49f1499.png",
        "sha256": "47e0dcec7cb911e8eec0bbbbeb2bfbecde7d0ef3551de8005e6370e0f49f1499"
      },
      {
        "path": "/data2/k6tk/e7/e7002300446a9e05e63735e30698e073dd9be79fb8ad10209152712668a1f962.png",
        "sha256": "e7002300446a9e05e63735e30698e073dd9be79fb8ad10209152712668a1f962"
      },
      {
        "path": "/data2/k6tk/cb/cb955b7155d79e581fd556abc495e52a0331af98ad4db95bf0ae4a49db647ae9.png",
        "sha256": "cb955b7155d79e581fd556abc495e52a0331af98ad4db95bf0ae4a49db647ae9"
      },
      {
        "path": "/data2/k6tk/06/066c5b7e31cf590042ac673e40319ad37d0d50d53e44b26761e9fb5debaa9d79.png",
        "sha256": "066c5b7e31cf590042ac673e40319ad37d0d50d53e44b26761e9fb5debaa9d79"
      },
      {
        "path": "/data2/k6tk/f6/f6009cc3fcb3f3bab6ab8ca33801c60491d55fea531d7d6932b0bc09be01548e.png",
        "sha256": "f6009cc3fcb3f3bab6ab8ca33801c60491d55fea531d7d6932b0bc09be01548e"
      },
      {
        "path": "/data2/k6tk/f2/f2363b06b0228ba10ea5f109211dce64b5be330f0b4ae37e125445ab0c495838.png",
        "sha256": "f2363b06b0228ba10ea5f109211dce64b5be330f0b4ae37e125445ab0c495838"
      },
      {
        "path": "/data2/k6tk/b6/b655a1f0491685a035b72d13598e83fc2511b108f0b4fedf3dc0a93da1836670.png",
        "sha256": "b655a1f0491685a035b72d13598e83fc2511b108f0b4fedf3dc0a93da1836670"
      },
      {
        "path": "/data2/k6tk/fa/fa35fa49f9a5642e8b1669cf4a741d07c00531d028f80577ff382aded0c060fc.png",
        "sha256": "fa35fa49f9a5642e8b1669cf4a741d07c00531d028f80577ff382aded0c060fc"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Compare category totals after identifying the distinct objects in the room: 'stool' first, 'tv' second. Which choice describes the first total in relation to the second?",
    "timestamps": [
      0.0,
      4.1,
      8.2,
      12.3,
      16.4,
      20.5,
      24.5,
      28.6,
      32.7,
      36.8,
      40.9,
      45.0,
      49.1,
      53.2,
      57.3,
      61.4,
      65.4,
      69.5,
      73.6,
      77.7,
      81.8,
      85.9,
      90.0,
      94.1,
      98.2,
      102.3,
      106.3,
      110.4,
      114.5,
      118.6,
      122.7,
      126.8
    ],
    "total_num_frames": 1269
  },
  "target": "<think>\nlocate the distinct instances of stool; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many stool instances as tv instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 36. fbp_relcnt2_f34701f83c3b4cee5159c414

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-bda964cc8c9dfd06e0eacdd798cc94158ebcb72f0d62a0bb444231fde92fa76d",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42899632",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42899632.npz": "96b034989b909ced0a45d9b67c4c62103999efc15b68bfd78ee223ec35068c28",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42899632.npz",
    "raster_sha256": "96b034989b909ced0a45d9b67c4c62103999efc15b68bfd78ee223ec35068c28",
    "relative_count": {
      "a": "tv",
      "b": "table",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        3
      ],
      "ids_b": [
        4
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue435357",
      "scene_use_cap": 24,
      "source_qid": "b12ct_f95899ab9eb6c28d88cf5e43",
      "source_row_sha256": "621e6795bb42b2f461e21dccc36a442dfda6280762453271bc14a8170544fa01",
      "source_use_cap": 8,
      "template_id": 15,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_f34701f83c3b4cee5159c414",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v1f8578c3d354",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      14,
      29,
      43,
      58,
      72,
      87,
      101,
      116,
      130,
      145,
      159,
      173,
      188,
      202,
      217,
      231,
      246,
      260,
      275,
      289,
      303,
      318,
      332,
      347,
      361,
      376,
      390,
      405,
      419,
      434,
      448
    ],
    "frames": [
      {
        "path": "/data2/k6tk/0f/0faf0ab3e864472a4c8f571ab2dbd6eefb3e109fd2ddb6ff1097ecd32d2cda52.png",
        "sha256": "0faf0ab3e864472a4c8f571ab2dbd6eefb3e109fd2ddb6ff1097ecd32d2cda52"
      },
      {
        "path": "/data2/k6tk/cc/cc00684edcb092c19d0addcf51c22679b9ccd414c46cbf0a2f92ec9d9c3d6a3b.png",
        "sha256": "cc00684edcb092c19d0addcf51c22679b9ccd414c46cbf0a2f92ec9d9c3d6a3b"
      },
      {
        "path": "/data2/k6tk/5c/5c6cad251e0c600401d4276712df19e5bdefe7d4b826026cecfd60dacc36c715.png",
        "sha256": "5c6cad251e0c600401d4276712df19e5bdefe7d4b826026cecfd60dacc36c715"
      },
      {
        "path": "/data2/k6tk/43/43e1a85470d06c2b7785d995f2d7b9fce0b3a6fe1ccefe576e00f5d17bc4ab52.png",
        "sha256": "43e1a85470d06c2b7785d995f2d7b9fce0b3a6fe1ccefe576e00f5d17bc4ab52"
      },
      {
        "path": "/data2/k6tk/25/2547cb46bbce9708e9942e2a3a9d2a1ae84f46f42685bd3d62493038a3e189ae.png",
        "sha256": "2547cb46bbce9708e9942e2a3a9d2a1ae84f46f42685bd3d62493038a3e189ae"
      },
      {
        "path": "/data2/k6tk/38/38f07b18ab78b48c714aa5a08e4bce7f863454ed4d0dd97e91db8ebbea25e027.png",
        "sha256": "38f07b18ab78b48c714aa5a08e4bce7f863454ed4d0dd97e91db8ebbea25e027"
      },
      {
        "path": "/data2/k6tk/af/af277a75133b5c25f9c6b0349bd049224a2acfa40208f08e44c4b9bb9f2b347c.png",
        "sha256": "af277a75133b5c25f9c6b0349bd049224a2acfa40208f08e44c4b9bb9f2b347c"
      },
      {
        "path": "/data2/k6tk/e0/e059099e7bdf6042c154ed7831630de88be52f7e743a2884bb09636063227735.png",
        "sha256": "e059099e7bdf6042c154ed7831630de88be52f7e743a2884bb09636063227735"
      },
      {
        "path": "/data2/k6tk/47/47bc3bf34a89ddba64d2891cd6a9ace6ca8787f22fdaa85153d2b0d50f57595e.png",
        "sha256": "47bc3bf34a89ddba64d2891cd6a9ace6ca8787f22fdaa85153d2b0d50f57595e"
      },
      {
        "path": "/data2/k6tk/5d/5da6d91864fe2860706f6d63d3ad6a9099bafed4a2d7969d6620483cee0a2243.png",
        "sha256": "5da6d91864fe2860706f6d63d3ad6a9099bafed4a2d7969d6620483cee0a2243"
      },
      {
        "path": "/data2/k6tk/bc/bc1323ef906544dba6316bb5f1bbcab3b86db7acb8cb57ba5259434ef0923aec.png",
        "sha256": "bc1323ef906544dba6316bb5f1bbcab3b86db7acb8cb57ba5259434ef0923aec"
      },
      {
        "path": "/data2/k6tk/1a/1a750f2b3b97b87829b1b1617014d3abb52898421520f453d68e2562c32211e4.png",
        "sha256": "1a750f2b3b97b87829b1b1617014d3abb52898421520f453d68e2562c32211e4"
      },
      {
        "path": "/data2/k6tk/7d/7d53c2bf7588f9a1c0ec8515cdc4e510ddc2529c5cb97ebedddf64aa46679a80.png",
        "sha256": "7d53c2bf7588f9a1c0ec8515cdc4e510ddc2529c5cb97ebedddf64aa46679a80"
      },
      {
        "path": "/data2/k6tk/cf/cf6ef255d199d67a088aad2cf3228912f4415f9b6a4734d67b3b9a29ce8b0c40.png",
        "sha256": "cf6ef255d199d67a088aad2cf3228912f4415f9b6a4734d67b3b9a29ce8b0c40"
      },
      {
        "path": "/data2/k6tk/37/37dfb1bc3332ac3f6798f9275f2f4dcd5c59a6ad2a7556d48842fd0170fa2284.png",
        "sha256": "37dfb1bc3332ac3f6798f9275f2f4dcd5c59a6ad2a7556d48842fd0170fa2284"
      },
      {
        "path": "/data2/k6tk/55/555428f4f807621de8728d3966f761618f7b7597df3e545ada4620133689ed53.png",
        "sha256": "555428f4f807621de8728d3966f761618f7b7597df3e545ada4620133689ed53"
      },
      {
        "path": "/data2/k6tk/ea/ea93f055c749c5220c0eaef052c6f37be2d69ab9f9067fbda4d41099c14560ae.png",
        "sha256": "ea93f055c749c5220c0eaef052c6f37be2d69ab9f9067fbda4d41099c14560ae"
      },
      {
        "path": "/data2/k6tk/06/06c87d779ae1bacff1b354031f07b16b4b8d84ea657ff2fd35a213dd17340169.png",
        "sha256": "06c87d779ae1bacff1b354031f07b16b4b8d84ea657ff2fd35a213dd17340169"
      },
      {
        "path": "/data2/k6tk/d8/d8ba251ebb1143d111753ecfc2f05c8459f2d24bd078768ea65185bc7283a641.png",
        "sha256": "d8ba251ebb1143d111753ecfc2f05c8459f2d24bd078768ea65185bc7283a641"
      },
      {
        "path": "/data2/k6tk/6c/6c6d1aff12568d3e61bd8a924dd9b491b960751ec8fd53ba60a020557ae2c47d.png",
        "sha256": "6c6d1aff12568d3e61bd8a924dd9b491b960751ec8fd53ba60a020557ae2c47d"
      },
      {
        "path": "/data2/k6tk/45/45469bf398f936b2f398381532c1c774a907efc3f9b693f2590f16963bab0f55.png",
        "sha256": "45469bf398f936b2f398381532c1c774a907efc3f9b693f2590f16963bab0f55"
      },
      {
        "path": "/data2/k6tk/44/445f30dc0218d9ddf92b04ec005c1527cbaf59e00bbcb4edaebda68cab4e2042.png",
        "sha256": "445f30dc0218d9ddf92b04ec005c1527cbaf59e00bbcb4edaebda68cab4e2042"
      },
      {
        "path": "/data2/k6tk/20/20e33c47fc23894b37feb82ac1327c904e6ef43b68dc9774c30afbcd9cee904e.png",
        "sha256": "20e33c47fc23894b37feb82ac1327c904e6ef43b68dc9774c30afbcd9cee904e"
      },
      {
        "path": "/data2/k6tk/97/975d8ef2c9d023383598c759d64717f89a7850ad4871637b6f3c2335c41cf225.png",
        "sha256": "975d8ef2c9d023383598c759d64717f89a7850ad4871637b6f3c2335c41cf225"
      },
      {
        "path": "/data2/k6tk/1b/1b3a28161187e68a25374d66062b374ca7a6b106209760481cfe9d24aed14e61.png",
        "sha256": "1b3a28161187e68a25374d66062b374ca7a6b106209760481cfe9d24aed14e61"
      },
      {
        "path": "/data2/k6tk/c1/c198d5e5c2b9c5a98c49d99c70512c10311c26e0b5754c5e85ac2813431d929f.png",
        "sha256": "c198d5e5c2b9c5a98c49d99c70512c10311c26e0b5754c5e85ac2813431d929f"
      },
      {
        "path": "/data2/k6tk/90/90395eb1dfd9abdc2c89b2a3d0cf3e8576160a4393f26e613174781924bc126c.png",
        "sha256": "90395eb1dfd9abdc2c89b2a3d0cf3e8576160a4393f26e613174781924bc126c"
      },
      {
        "path": "/data2/k6tk/8a/8a34c50785faf34dff969933f1cb04f66a2520f50cbcd2b0dabacacf8a2c6882.png",
        "sha256": "8a34c50785faf34dff969933f1cb04f66a2520f50cbcd2b0dabacacf8a2c6882"
      },
      {
        "path": "/data2/k6tk/f0/f0a625f2de6c6495cad862455b9b004119c10c23ea5692ea9f298e2643d590c4.png",
        "sha256": "f0a625f2de6c6495cad862455b9b004119c10c23ea5692ea9f298e2643d590c4"
      },
      {
        "path": "/data2/k6tk/df/df6f8e08f074b202ea94f809172c51822d7c471ce30ae630623b8500ae1bcf5f.png",
        "sha256": "df6f8e08f074b202ea94f809172c51822d7c471ce30ae630623b8500ae1bcf5f"
      },
      {
        "path": "/data2/k6tk/e8/e88039b297c902c1da7a75cbdcab545a568fad7329a38865111d49441e524ea5.png",
        "sha256": "e88039b297c902c1da7a75cbdcab545a568fad7329a38865111d49441e524ea5"
      },
      {
        "path": "/data2/k6tk/5b/5b9787ea96045ed5db98a3b607d1b7ed032cd890d7be83480bac35884a22ba69.png",
        "sha256": "5b9787ea96045ed5db98a3b607d1b7ed032cd890d7be83480bac35884a22ba69"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "There are separate object categories named 'tv' and 'table' to tally in these views. Choose the count relationship with 'tv' as the category being compared and 'table' as the reference.",
    "timestamps": [
      0.0,
      1.4,
      2.9,
      4.3,
      5.8,
      7.2,
      8.7,
      10.1,
      11.6,
      13.0,
      14.5,
      15.9,
      17.3,
      18.8,
      20.2,
      21.7,
      23.1,
      24.6,
      26.0,
      27.5,
      28.9,
      30.3,
      31.8,
      33.2,
      34.7,
      36.1,
      37.6,
      39.0,
      40.5,
      41.9,
      43.4,
      44.8
    ],
    "total_num_frames": 449
  },
  "target": "<think>\nlocate the distinct instances of tv; count each once across the frames.\nlocate the distinct instances of table; count each once across the frames.\nSo there are as many tv instances as table instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 37. fbp_relcnt2_abf187824f99204b238dc8a4

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-77f0409021987a9ab2a80d9d7449b1dd1b99c04c41099df065c232cb4fd0227f",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/42899072",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/42899072.npz": "b67248d2c94afc75c49a8b333cb7340e33d86b754c3efe7ec5b9c7514038ed9e",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "42899072.npz",
    "raster_sha256": "b67248d2c94afc75c49a8b333cb7340e33d86b754c3efe7ec5b9c7514038ed9e",
    "relative_count": {
      "a": "bed",
      "b": "tv",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        0
      ],
      "ids_b": [
        6
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue434975",
      "scene_use_cap": 24,
      "source_qid": "b12ct_f9bce9b76f39a00388eafa3e",
      "source_row_sha256": "bb06effbff992ee5d6108b91edba0a108a8227160d35043f4f003cd65c718800",
      "source_use_cap": 8,
      "template_id": 16,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_abf187824f99204b238dc8a4",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vaf052c662739",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      23,
      47,
      70,
      94,
      117,
      141,
      164,
      188,
      211,
      235,
      258,
      281,
      305,
      328,
      352,
      375,
      399,
      422,
      446,
      469,
      492,
      516,
      539,
      563,
      586,
      610,
      633,
      657,
      680,
      704,
      727
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9a/9a5ea83145bdb2e2c5c2ecc1af6758a26707afa690a214ec58a9b861b6f507e1.png",
        "sha256": "9a5ea83145bdb2e2c5c2ecc1af6758a26707afa690a214ec58a9b861b6f507e1"
      },
      {
        "path": "/data2/k6tk/12/12a89ffc01c5814003075141f0e9c00192cb2a045410fc4f1cf5c2d23578c27e.png",
        "sha256": "12a89ffc01c5814003075141f0e9c00192cb2a045410fc4f1cf5c2d23578c27e"
      },
      {
        "path": "/data2/k6tk/c7/c718b7b68ddecf918d3c958a44a2de2cc4d03be3ef580a15e4050dc30df58660.png",
        "sha256": "c718b7b68ddecf918d3c958a44a2de2cc4d03be3ef580a15e4050dc30df58660"
      },
      {
        "path": "/data2/k6tk/6b/6b8a139ccbb2a476573dbb0e4d1c35ad83f840092576c8ff79c88e292d34c518.png",
        "sha256": "6b8a139ccbb2a476573dbb0e4d1c35ad83f840092576c8ff79c88e292d34c518"
      },
      {
        "path": "/data2/k6tk/eb/ebad584b78f10b066b3fc81355f6bb0b95898fa22f4f2d40052a8b9f02bf8367.png",
        "sha256": "ebad584b78f10b066b3fc81355f6bb0b95898fa22f4f2d40052a8b9f02bf8367"
      },
      {
        "path": "/data2/k6tk/cd/cdf131689ad16f38fdfc456b01c95ad82b62a3988c4f02f2554e84e6206d450e.png",
        "sha256": "cdf131689ad16f38fdfc456b01c95ad82b62a3988c4f02f2554e84e6206d450e"
      },
      {
        "path": "/data2/k6tk/70/7062f933cd666837f66c596dca985ed47c2699915bb4ece05b62998b13856465.png",
        "sha256": "7062f933cd666837f66c596dca985ed47c2699915bb4ece05b62998b13856465"
      },
      {
        "path": "/data2/k6tk/d5/d5cf1f90cf2d24fb867c570548f9247fc862d5bc889b4683ca690289c8b7e20e.png",
        "sha256": "d5cf1f90cf2d24fb867c570548f9247fc862d5bc889b4683ca690289c8b7e20e"
      },
      {
        "path": "/data2/k6tk/c7/c788250154204d480f50df7a6e0398dd23393530ed64bdb616bdb524351a311f.png",
        "sha256": "c788250154204d480f50df7a6e0398dd23393530ed64bdb616bdb524351a311f"
      },
      {
        "path": "/data2/k6tk/72/722fd3f9e5e023c32591fcb54892e113dcee4e6fd457ba9c05ef587ad67f3479.png",
        "sha256": "722fd3f9e5e023c32591fcb54892e113dcee4e6fd457ba9c05ef587ad67f3479"
      },
      {
        "path": "/data2/k6tk/c1/c1530d5d18fcf06c9a9dcc20dc4abf119fee289d4938947a3eb754d97287516d.png",
        "sha256": "c1530d5d18fcf06c9a9dcc20dc4abf119fee289d4938947a3eb754d97287516d"
      },
      {
        "path": "/data2/k6tk/d1/d1ba2e69170e95717f3262835298b78e49e0b5f21e630ad307b31ba8951687de.png",
        "sha256": "d1ba2e69170e95717f3262835298b78e49e0b5f21e630ad307b31ba8951687de"
      },
      {
        "path": "/data2/k6tk/f9/f9325928afad60b9c86bb6918676dfd3cc14ab30275aa618b5fe2d5bbcb1211e.png",
        "sha256": "f9325928afad60b9c86bb6918676dfd3cc14ab30275aa618b5fe2d5bbcb1211e"
      },
      {
        "path": "/data2/k6tk/24/242b293815d86597501162cc0ce7f11bc0c73cda6db2bd6ece07836ee12341b6.png",
        "sha256": "242b293815d86597501162cc0ce7f11bc0c73cda6db2bd6ece07836ee12341b6"
      },
      {
        "path": "/data2/k6tk/b9/b9003d9c99e7e0dd61ee8d3fb77c3e533e185e61d426fdd8cd8a51e86a06c951.png",
        "sha256": "b9003d9c99e7e0dd61ee8d3fb77c3e533e185e61d426fdd8cd8a51e86a06c951"
      },
      {
        "path": "/data2/k6tk/ad/adaef9215d83d79d9e2b6ecbc970759c64b612a6aded3b7d6601cf62ad6e4598.png",
        "sha256": "adaef9215d83d79d9e2b6ecbc970759c64b612a6aded3b7d6601cf62ad6e4598"
      },
      {
        "path": "/data2/k6tk/4d/4d0305310f0368c8f56b27427dac32e25bf47e775729d1e9db7721fb61f2c273.png",
        "sha256": "4d0305310f0368c8f56b27427dac32e25bf47e775729d1e9db7721fb61f2c273"
      },
      {
        "path": "/data2/k6tk/ba/bae3bbb3ec897d01bc3cbf9c2a4677b4b8dff3a3ec75bd8768ce1c4999489eef.png",
        "sha256": "bae3bbb3ec897d01bc3cbf9c2a4677b4b8dff3a3ec75bd8768ce1c4999489eef"
      },
      {
        "path": "/data2/k6tk/a6/a60044cd399d8fd910b3f91be02f7dcf5ab180f2d0deb97840981d6b1749b72c.png",
        "sha256": "a60044cd399d8fd910b3f91be02f7dcf5ab180f2d0deb97840981d6b1749b72c"
      },
      {
        "path": "/data2/k6tk/c4/c4f457deb221174727dbe6e4423709ec5b6e1e0b93e43b51d4da9dbe97990da9.png",
        "sha256": "c4f457deb221174727dbe6e4423709ec5b6e1e0b93e43b51d4da9dbe97990da9"
      },
      {
        "path": "/data2/k6tk/0a/0ab6d674b34ff507c1a1103f070f23de06d88090604f554af3b9646b5a425ddb.png",
        "sha256": "0ab6d674b34ff507c1a1103f070f23de06d88090604f554af3b9646b5a425ddb"
      },
      {
        "path": "/data2/k6tk/a1/a18cfda26fbb64c81b14053bfed5b7e6593757684742029c4ef1445710009312.png",
        "sha256": "a18cfda26fbb64c81b14053bfed5b7e6593757684742029c4ef1445710009312"
      },
      {
        "path": "/data2/k6tk/5f/5f2f06673f6078819a297ffefb849335f46eb28cf46eca2df1f52848cc28b33b.png",
        "sha256": "5f2f06673f6078819a297ffefb849335f46eb28cf46eca2df1f52848cc28b33b"
      },
      {
        "path": "/data2/k6tk/73/7394386fa5002480af22e3e3ee1d41ac3d0cc96adea2d5904f54e508e803caf7.png",
        "sha256": "7394386fa5002480af22e3e3ee1d41ac3d0cc96adea2d5904f54e508e803caf7"
      },
      {
        "path": "/data2/k6tk/85/856fc47acda0007f889f77e5a333a68e1689dd6a0beba882d42615e20f3b51b9.png",
        "sha256": "856fc47acda0007f889f77e5a333a68e1689dd6a0beba882d42615e20f3b51b9"
      },
      {
        "path": "/data2/k6tk/38/38f315adc77b573655389840481bb2e19a56598edc621ce56d1fde0b3c775cdc.png",
        "sha256": "38f315adc77b573655389840481bb2e19a56598edc621ce56d1fde0b3c775cdc"
      },
      {
        "path": "/data2/k6tk/cc/cc0f5d2e1e52f0a5a2656d1ade99a8123a1d8fea3196511d64d91207874fa685.png",
        "sha256": "cc0f5d2e1e52f0a5a2656d1ade99a8123a1d8fea3196511d64d91207874fa685"
      },
      {
        "path": "/data2/k6tk/e4/e4bbf327661975d39094304d017194d625a9b47539c2d0b1baaf4ef64122ab08.png",
        "sha256": "e4bbf327661975d39094304d017194d625a9b47539c2d0b1baaf4ef64122ab08"
      },
      {
        "path": "/data2/k6tk/ec/ec46f9538465e8177927994c457ce78830ba10c92f56fe337d7db0cf1912c641.png",
        "sha256": "ec46f9538465e8177927994c457ce78830ba10c92f56fe337d7db0cf1912c641"
      },
      {
        "path": "/data2/k6tk/ea/ea751bb2e923ac98db247d8cdbd65a4be003601bc4a6e6118e9134c8a509652d.png",
        "sha256": "ea751bb2e923ac98db247d8cdbd65a4be003601bc4a6e6118e9134c8a509652d"
      },
      {
        "path": "/data2/k6tk/bd/bd14603e8b7083ad2d757803ea9ed9fd82900d0d46fcc34624b53e0a8dde3845.png",
        "sha256": "bd14603e8b7083ad2d757803ea9ed9fd82900d0d46fcc34624b53e0a8dde3845"
      },
      {
        "path": "/data2/k6tk/55/55718b62fe8b548f2c5521ecc52642a956b7acfb7d89693835923a845cd4aeee.png",
        "sha256": "55718b62fe8b548f2c5521ecc52642a956b7acfb7d89693835923a845cd4aeee"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Determine how many separate objects belong to 'bed' and how many belong to 'tv'. Using those totals, choose the comparison of 'bed' with 'tv'.",
    "timestamps": [
      0.0,
      2.3,
      4.7,
      7.0,
      9.4,
      11.7,
      14.1,
      16.4,
      18.8,
      21.1,
      23.5,
      25.8,
      28.1,
      30.5,
      32.8,
      35.2,
      37.5,
      39.9,
      42.2,
      44.6,
      46.9,
      49.2,
      51.6,
      53.9,
      56.3,
      58.6,
      61.0,
      63.3,
      65.7,
      68.0,
      70.4,
      72.7
    ],
    "total_num_frames": 728
  },
  "target": "<think>\nlocate the distinct instances of bed; count each once across the frames.\nlocate the distinct instances of tv; count each once across the frames.\nSo there are as many bed instances as tv instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 38. fbp_relcnt2_806495e356f4cec4664ba1cf

```json
{
  "answer": "A",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-bb43bad2d77fe5b43d36d2a146e67061a8af69bdb96fcb6ffa68e8052b16c907",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/43896339",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/43896339.npz": "e1acd04965b140a0ba44723b2ca206d8105b91793b698150a233661118453617",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "43896339.npz",
    "raster_sha256": "e1acd04965b140a0ba44723b2ca206d8105b91793b698150a233661118453617",
    "relative_count": {
      "a": "table",
      "b": "stool",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        4
      ],
      "ids_b": [
        9
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue438376",
      "scene_use_cap": 24,
      "source_qid": "b12ct_147617d5e4558ab525a8e743",
      "source_row_sha256": "0126e7e73f10100a2aff3965452e91c26383be6f8d4242a454813480e558945a",
      "source_use_cap": 8,
      "template_id": 17,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_806495e356f4cec4664ba1cf",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "vb118aae887fd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      31,
      62,
      92,
      123,
      154,
      185,
      216,
      246,
      277,
      308,
      339,
      370,
      400,
      431,
      462,
      493,
      524,
      555,
      585,
      616,
      647,
      678,
      709,
      739,
      770,
      801,
      832,
      863,
      893,
      924,
      955
    ],
    "frames": [
      {
        "path": "/data2/k6tk/8c/8c89e315c82e4b20c619829286d26d0a710ddb2458159f7a5c6438800b04b064.png",
        "sha256": "8c89e315c82e4b20c619829286d26d0a710ddb2458159f7a5c6438800b04b064"
      },
      {
        "path": "/data2/k6tk/e8/e8c5ac153d092cb978ec7847525b9e34096976c118c59e5e5890c6a37124cc1e.png",
        "sha256": "e8c5ac153d092cb978ec7847525b9e34096976c118c59e5e5890c6a37124cc1e"
      },
      {
        "path": "/data2/k6tk/b9/b91b5e75f062ebb4564109ea82e1f893aa685a9f674d473e9e3215d0f84bb6f4.png",
        "sha256": "b91b5e75f062ebb4564109ea82e1f893aa685a9f674d473e9e3215d0f84bb6f4"
      },
      {
        "path": "/data2/k6tk/6e/6e62f9724615598031b1eb03670ec40eaba9cd73bf6364a715544419f011e4b1.png",
        "sha256": "6e62f9724615598031b1eb03670ec40eaba9cd73bf6364a715544419f011e4b1"
      },
      {
        "path": "/data2/k6tk/e0/e01d37b68e9d17ca68632d7e6cc13ea0794c77f1d60a9f1a1ffe6f4bfb964800.png",
        "sha256": "e01d37b68e9d17ca68632d7e6cc13ea0794c77f1d60a9f1a1ffe6f4bfb964800"
      },
      {
        "path": "/data2/k6tk/4a/4a4dc297a3a7cb236cfe054de71dfcb33b6db45af0846f4416b089d1da4c77ed.png",
        "sha256": "4a4dc297a3a7cb236cfe054de71dfcb33b6db45af0846f4416b089d1da4c77ed"
      },
      {
        "path": "/data2/k6tk/63/63ca747fa3b3ea308aa1a9a5b2cf09884643f36ecff815cacaade6e56314b238.png",
        "sha256": "63ca747fa3b3ea308aa1a9a5b2cf09884643f36ecff815cacaade6e56314b238"
      },
      {
        "path": "/data2/k6tk/c7/c7b3274257c855a88045861e1e42d61d9c46f130d9fca8175266969fa81f7fe4.png",
        "sha256": "c7b3274257c855a88045861e1e42d61d9c46f130d9fca8175266969fa81f7fe4"
      },
      {
        "path": "/data2/k6tk/53/53d8e470ad8764e875c692d441f927eff1ab92693bc4bb56371cf5ffffd52871.png",
        "sha256": "53d8e470ad8764e875c692d441f927eff1ab92693bc4bb56371cf5ffffd52871"
      },
      {
        "path": "/data2/k6tk/a4/a400ee8df3b5930453f4aaf86d4d3ac1ca43ab4f57b67b0a183e44a4432425bf.png",
        "sha256": "a400ee8df3b5930453f4aaf86d4d3ac1ca43ab4f57b67b0a183e44a4432425bf"
      },
      {
        "path": "/data2/k6tk/5a/5a9a6318ea6e7329ce82117cdcfe78c707851b13959c11867b9c0ae994e8774d.png",
        "sha256": "5a9a6318ea6e7329ce82117cdcfe78c707851b13959c11867b9c0ae994e8774d"
      },
      {
        "path": "/data2/k6tk/55/5588ebeea1640fad87c986bf4f19bcf44f57feb89cf50fcb7629897503b56099.png",
        "sha256": "5588ebeea1640fad87c986bf4f19bcf44f57feb89cf50fcb7629897503b56099"
      },
      {
        "path": "/data2/k6tk/0e/0e92ded86029b76120c1c4fc616bd7a6b72b49a2d79d138f0c0e56aae8f28de4.png",
        "sha256": "0e92ded86029b76120c1c4fc616bd7a6b72b49a2d79d138f0c0e56aae8f28de4"
      },
      {
        "path": "/data2/k6tk/7e/7e25134f28c6c2fde889e368264357daa8f01bb2d5dd199bc6d80cd41431334f.png",
        "sha256": "7e25134f28c6c2fde889e368264357daa8f01bb2d5dd199bc6d80cd41431334f"
      },
      {
        "path": "/data2/k6tk/cf/cf87947b337c94881bc6e4fe51a0d5ca50e99ea8a65610a27d5e5230285c8a8c.png",
        "sha256": "cf87947b337c94881bc6e4fe51a0d5ca50e99ea8a65610a27d5e5230285c8a8c"
      },
      {
        "path": "/data2/k6tk/42/424794df41a0f4931cc302afec2c41d390d1c589c849c2e6359abff8279580f3.png",
        "sha256": "424794df41a0f4931cc302afec2c41d390d1c589c849c2e6359abff8279580f3"
      },
      {
        "path": "/data2/k6tk/bb/bbd70c0593a8e8e5b54c86cdc76a8da0a1a1bbd2df24a19c024ba0080d4aaf05.png",
        "sha256": "bbd70c0593a8e8e5b54c86cdc76a8da0a1a1bbd2df24a19c024ba0080d4aaf05"
      },
      {
        "path": "/data2/k6tk/c5/c536fc091bc0ad7803810df62f9658fbc7862ce5f53ece06eb7672aa660c5945.png",
        "sha256": "c536fc091bc0ad7803810df62f9658fbc7862ce5f53ece06eb7672aa660c5945"
      },
      {
        "path": "/data2/k6tk/0b/0b9daec25d782a195e370714d13adc7419c433bf755f558fcc0b451e5518738d.png",
        "sha256": "0b9daec25d782a195e370714d13adc7419c433bf755f558fcc0b451e5518738d"
      },
      {
        "path": "/data2/k6tk/02/02db99aa1b83722d1b31182a3dba11e4b84639250ae16477838922d15b2e9956.png",
        "sha256": "02db99aa1b83722d1b31182a3dba11e4b84639250ae16477838922d15b2e9956"
      },
      {
        "path": "/data2/k6tk/7b/7bc57d14e42da285740e301b63414630e856d7cbcfd5cc38ca630b9c9cfca3ac.png",
        "sha256": "7bc57d14e42da285740e301b63414630e856d7cbcfd5cc38ca630b9c9cfca3ac"
      },
      {
        "path": "/data2/k6tk/46/468414cad4b643db70875c420d7c257c077c5bac83e69a179b62666cb6c66d31.png",
        "sha256": "468414cad4b643db70875c420d7c257c077c5bac83e69a179b62666cb6c66d31"
      },
      {
        "path": "/data2/k6tk/d5/d5da76ca26cbb203f5e4b34538992797c592170eec274a8bd62636d6ba171591.png",
        "sha256": "d5da76ca26cbb203f5e4b34538992797c592170eec274a8bd62636d6ba171591"
      },
      {
        "path": "/data2/k6tk/66/66cccc5549af8b2f01a7e31e72ad0e958805f38838268f506c25bd45540133ea.png",
        "sha256": "66cccc5549af8b2f01a7e31e72ad0e958805f38838268f506c25bd45540133ea"
      },
      {
        "path": "/data2/k6tk/f4/f42cfe7b83d3f41e55150429eb756641914226560b6955ede2623f9c740f7579.png",
        "sha256": "f42cfe7b83d3f41e55150429eb756641914226560b6955ede2623f9c740f7579"
      },
      {
        "path": "/data2/k6tk/21/216e03998f814f76cdbf7b25f150127ff8476fdf6ffd895eb7501e87f5925687.png",
        "sha256": "216e03998f814f76cdbf7b25f150127ff8476fdf6ffd895eb7501e87f5925687"
      },
      {
        "path": "/data2/k6tk/29/299363b917fc4f8870321065c01f6372717430ae39c405405ad2ae5825da27a3.png",
        "sha256": "299363b917fc4f8870321065c01f6372717430ae39c405405ad2ae5825da27a3"
      },
      {
        "path": "/data2/k6tk/55/55bec3ee28c5f38a93b0ab9baded3d203cffdfecbb22ffdca326da63048e28a5.png",
        "sha256": "55bec3ee28c5f38a93b0ab9baded3d203cffdfecbb22ffdca326da63048e28a5"
      },
      {
        "path": "/data2/k6tk/3f/3f0e6b8a8fed655e844f002afafc9c388d23410ac7ffbb7289cc169898a2111c.png",
        "sha256": "3f0e6b8a8fed655e844f002afafc9c388d23410ac7ffbb7289cc169898a2111c"
      },
      {
        "path": "/data2/k6tk/8a/8a27ebc78c7875a7f43ef54e3f4dc069d18c48ae51bcec9bcf857977d821c460.png",
        "sha256": "8a27ebc78c7875a7f43ef54e3f4dc069d18c48ae51bcec9bcf857977d821c460"
      },
      {
        "path": "/data2/k6tk/26/269a33884eabfc1bf1f1c33d9ab473fcb2345f68789a7c6d2d29281ab5542184.png",
        "sha256": "269a33884eabfc1bf1f1c33d9ab473fcb2345f68789a7c6d2d29281ab5542184"
      },
      {
        "path": "/data2/k6tk/33/330f5f881f6fb7711db08ac489226b1e8d6e01c5467bb208edbda6c69cffb028.png",
        "sha256": "330f5f881f6fb7711db08ac489226b1e8d6e01c5467bb208edbda6c69cffb028"
      }
    ],
    "options": [
      "A. equal number",
      "B. more",
      "C. fewer"
    ],
    "question": "Use the room video to compare the populations of 'table' objects and 'stool' objects. Which option describes the first population relative to the second after repeated views are counted only once?",
    "timestamps": [
      0.0,
      3.1,
      6.2,
      9.2,
      12.3,
      15.4,
      18.5,
      21.6,
      24.6,
      27.7,
      30.8,
      33.9,
      37.0,
      40.0,
      43.1,
      46.2,
      49.3,
      52.4,
      55.5,
      58.5,
      61.6,
      64.7,
      67.8,
      70.9,
      73.9,
      77.0,
      80.1,
      83.2,
      86.3,
      89.3,
      92.4,
      95.5
    ],
    "total_num_frames": 956
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of stool; count each once across the frames.\nSo there are as many table instances as stool instances.\n</think>\n\nA",
  "validation_commit": ""
}
```

### 39. fbp_relcnt2_526ff39d20844fd0e28d5a59

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-d7386cbda11be490d9fd0cce326e141666516f33fff719ca4182b75766c830c0",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/44796227",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/44796227.npz": "b43eb5a770cb157c4c0ed6da7e1dae9e7e19887a52126bfb73567228f2fb6cc5",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "44796227.npz",
    "raster_sha256": "b43eb5a770cb157c4c0ed6da7e1dae9e7e19887a52126bfb73567228f2fb6cc5",
    "relative_count": {
      "a": "bed",
      "b": "stool",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        0
      ],
      "ids_b": [
        4
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue464750",
      "scene_use_cap": 24,
      "source_qid": "b12ct_bd9fa039ed86199652911fe8",
      "source_row_sha256": "dc1d82f185a5b6843d08f49eddc1d0cc0be0aeaa8e5adce7edd689606021f65d",
      "source_use_cap": 8,
      "template_id": 18,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_526ff39d20844fd0e28d5a59",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v19d395a78cdd",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      19,
      38,
      57,
      76,
      95,
      114,
      133,
      152,
      171,
      190,
      209,
      228,
      247,
      266,
      285,
      305,
      324,
      343,
      362,
      381,
      400,
      419,
      438,
      457,
      476,
      495,
      514,
      533,
      552,
      571,
      590
    ],
    "frames": [
      {
        "path": "/data2/k6tk/23/23aceef5327a744f3caa6b2b9c8ad2020061ba467440cb3753904cd6bfdd660a.png",
        "sha256": "23aceef5327a744f3caa6b2b9c8ad2020061ba467440cb3753904cd6bfdd660a"
      },
      {
        "path": "/data2/k6tk/b4/b45b4b51c24853d07c72c0e6cacf45bb3f193631bbe0786a2d6510fbd90fd8c9.png",
        "sha256": "b45b4b51c24853d07c72c0e6cacf45bb3f193631bbe0786a2d6510fbd90fd8c9"
      },
      {
        "path": "/data2/k6tk/dc/dca595b0dcf36a96028097378ed824d0792b978840f226b178aba30fb26ce1a6.png",
        "sha256": "dca595b0dcf36a96028097378ed824d0792b978840f226b178aba30fb26ce1a6"
      },
      {
        "path": "/data2/k6tk/35/3568a9329716dd62fa9368ad6f95d95d56ad426766fe3739de2efbe015ca074b.png",
        "sha256": "3568a9329716dd62fa9368ad6f95d95d56ad426766fe3739de2efbe015ca074b"
      },
      {
        "path": "/data2/k6tk/82/829192e63e0bedaa0eb2fb3882961977e259ccd74c571da072d3dbf690c16460.png",
        "sha256": "829192e63e0bedaa0eb2fb3882961977e259ccd74c571da072d3dbf690c16460"
      },
      {
        "path": "/data2/k6tk/c5/c50068f6a145e88b1277f15952311dbf90cbedb034c397e886675b1ce3ba7d48.png",
        "sha256": "c50068f6a145e88b1277f15952311dbf90cbedb034c397e886675b1ce3ba7d48"
      },
      {
        "path": "/data2/k6tk/3b/3b0ab3d56ce929c74fafc13f3df72670c6f305897914ddbecb84df63bee3c734.png",
        "sha256": "3b0ab3d56ce929c74fafc13f3df72670c6f305897914ddbecb84df63bee3c734"
      },
      {
        "path": "/data2/k6tk/c7/c7f694532a3755f50713a1f9e1e7d3cd5e554aea5577a309ffe371981829fa20.png",
        "sha256": "c7f694532a3755f50713a1f9e1e7d3cd5e554aea5577a309ffe371981829fa20"
      },
      {
        "path": "/data2/k6tk/86/86cee9620e0033c23bcb2cced2b546e1c62628ec4aa46354f51b770532d4f3c8.png",
        "sha256": "86cee9620e0033c23bcb2cced2b546e1c62628ec4aa46354f51b770532d4f3c8"
      },
      {
        "path": "/data2/k6tk/57/571610adaa5b06eb660ccff7a059df38bc413321cd940947a2c8fd48abd311a2.png",
        "sha256": "571610adaa5b06eb660ccff7a059df38bc413321cd940947a2c8fd48abd311a2"
      },
      {
        "path": "/data2/k6tk/aa/aae028dff2aac7b33d08ffb4c95879c5556f96b29641ac6325540dd705d76e2c.png",
        "sha256": "aae028dff2aac7b33d08ffb4c95879c5556f96b29641ac6325540dd705d76e2c"
      },
      {
        "path": "/data2/k6tk/0c/0c95554234f344e703d741938939038ceac84dedf17f815811ea28f1c95850a5.png",
        "sha256": "0c95554234f344e703d741938939038ceac84dedf17f815811ea28f1c95850a5"
      },
      {
        "path": "/data2/k6tk/c9/c9f3ae0b60e0a55cd792f4d2805788fc0b520f1d20d94fb8150b2e02bcd0d2b9.png",
        "sha256": "c9f3ae0b60e0a55cd792f4d2805788fc0b520f1d20d94fb8150b2e02bcd0d2b9"
      },
      {
        "path": "/data2/k6tk/0c/0ceb0c67ee8c6b92215d51aab2c6d067ae220e4b3852f5a419a72872aeb1dc43.png",
        "sha256": "0ceb0c67ee8c6b92215d51aab2c6d067ae220e4b3852f5a419a72872aeb1dc43"
      },
      {
        "path": "/data2/k6tk/de/de9290abd00ca60df4a05cf1b97ca78f65b181800aa397d8fb8fd4ba9537a05d.png",
        "sha256": "de9290abd00ca60df4a05cf1b97ca78f65b181800aa397d8fb8fd4ba9537a05d"
      },
      {
        "path": "/data2/k6tk/8d/8d7c124155d4b419f22332c5fb00c1ceab955a46b0f0e2dbd51b0bc40a557113.png",
        "sha256": "8d7c124155d4b419f22332c5fb00c1ceab955a46b0f0e2dbd51b0bc40a557113"
      },
      {
        "path": "/data2/k6tk/0b/0be2513c6220441f1bef24e9bf4555e6d0b850fc504ba5ecf03058cd609c0451.png",
        "sha256": "0be2513c6220441f1bef24e9bf4555e6d0b850fc504ba5ecf03058cd609c0451"
      },
      {
        "path": "/data2/k6tk/60/6076a7ffba16d6f4c7a03f166a4e9cece6ae2e44090d598b54bbcdbccf77ce95.png",
        "sha256": "6076a7ffba16d6f4c7a03f166a4e9cece6ae2e44090d598b54bbcdbccf77ce95"
      },
      {
        "path": "/data2/k6tk/3f/3f1080a2cdf35974bcaba89f16460fefff8636f1cd88c250028609c7f52bd1bf.png",
        "sha256": "3f1080a2cdf35974bcaba89f16460fefff8636f1cd88c250028609c7f52bd1bf"
      },
      {
        "path": "/data2/k6tk/3b/3bdc4e3249aab9a19fdb1404f3a5eb8e1b915e3b2537f1a8f5fdb547cbd3f477.png",
        "sha256": "3bdc4e3249aab9a19fdb1404f3a5eb8e1b915e3b2537f1a8f5fdb547cbd3f477"
      },
      {
        "path": "/data2/k6tk/82/8272ab467e8a6d93dda3b832798a405f142fe755b9ed85124f927e2f792860a6.png",
        "sha256": "8272ab467e8a6d93dda3b832798a405f142fe755b9ed85124f927e2f792860a6"
      },
      {
        "path": "/data2/k6tk/a4/a4789a79bd451aea41a63129e3197799f6dd86ba08a89c33d260c2ce0e8494d2.png",
        "sha256": "a4789a79bd451aea41a63129e3197799f6dd86ba08a89c33d260c2ce0e8494d2"
      },
      {
        "path": "/data2/k6tk/82/8292b4bfcf7e8d8424607d2beb17a12045829ba7110160a6b0c410e8ddce2a35.png",
        "sha256": "8292b4bfcf7e8d8424607d2beb17a12045829ba7110160a6b0c410e8ddce2a35"
      },
      {
        "path": "/data2/k6tk/c3/c362c3a6ad8ed343cf11bde66746dd49341c0a9732d387c60b659cdbba8d968d.png",
        "sha256": "c362c3a6ad8ed343cf11bde66746dd49341c0a9732d387c60b659cdbba8d968d"
      },
      {
        "path": "/data2/k6tk/dd/dda5b4735dde6b86b9040301f7ae63f06854dce3fd89d88d6423e9bf2dd24656.png",
        "sha256": "dda5b4735dde6b86b9040301f7ae63f06854dce3fd89d88d6423e9bf2dd24656"
      },
      {
        "path": "/data2/k6tk/b1/b1022a959587136d92ebc81cbc05fd4ba41fdf0052c57edb708e74d07248b2a6.png",
        "sha256": "b1022a959587136d92ebc81cbc05fd4ba41fdf0052c57edb708e74d07248b2a6"
      },
      {
        "path": "/data2/k6tk/b9/b9450738016bdb6be7306b343dcf72501ee8cb5f81b64fbb470a71940cd08945.png",
        "sha256": "b9450738016bdb6be7306b343dcf72501ee8cb5f81b64fbb470a71940cd08945"
      },
      {
        "path": "/data2/k6tk/39/39a9d671cca23897d90b09cee0ccd8c4f663790ee43a2038168baa3c9168780e.png",
        "sha256": "39a9d671cca23897d90b09cee0ccd8c4f663790ee43a2038168baa3c9168780e"
      },
      {
        "path": "/data2/k6tk/c4/c4846b64c9ce18514b6e4432fb3466483350f61c4dc892da6f1e0aa90ebadecf.png",
        "sha256": "c4846b64c9ce18514b6e4432fb3466483350f61c4dc892da6f1e0aa90ebadecf"
      },
      {
        "path": "/data2/k6tk/bb/bb77924d93ac528607f1b9fefc1311688b124ddc2ca8531f20291d694a769d7e.png",
        "sha256": "bb77924d93ac528607f1b9fefc1311688b124ddc2ca8531f20291d694a769d7e"
      },
      {
        "path": "/data2/k6tk/5e/5e69754bf09596fe81c09a64dfa4ec40b8e253915277af1c89898140f5d7977a.png",
        "sha256": "5e69754bf09596fe81c09a64dfa4ec40b8e253915277af1c89898140f5d7977a"
      },
      {
        "path": "/data2/k6tk/74/74bf58bf87a22f7d7cdb7ad7fc6d44fb66c834e53f8068e981c43332de75599c.png",
        "sha256": "74bf58bf87a22f7d7cdb7ad7fc6d44fb66c834e53f8068e981c43332de75599c"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "For the objects in categories 'bed' and 'stool', compare distinct-instance totals across the room. Read each answer choice as describing 'bed' relative to 'stool' and select the correct one.",
    "timestamps": [
      0.0,
      1.9,
      3.8,
      5.7,
      7.6,
      9.5,
      11.4,
      13.3,
      15.2,
      17.1,
      19.0,
      20.9,
      22.8,
      24.7,
      26.6,
      28.5,
      30.5,
      32.4,
      34.3,
      36.2,
      38.1,
      40.0,
      41.9,
      43.8,
      45.7,
      47.6,
      49.5,
      51.4,
      53.3,
      55.2,
      57.1,
      59.0
    ],
    "total_num_frames": 591
  },
  "target": "<think>\nlocate the distinct instances of bed; count each once across the frames.\nlocate the distinct instances of stool; count each once across the frames.\nSo there are as many bed instances as stool instances.\n</think>\n\nC",
  "validation_commit": ""
}
```

### 40. fbp_relcnt2_3770c690d6ed584ae510df0a

```json
{
  "answer": "C",
  "benchmark_improvement_claim": false,
  "benchmark_trained_diagnostic": true,
  "candidate_id": "ground-8bb9f425d9f86b1cb4cb4f0634b47bd26a5d2aaa0b59a7cc0f5937770ec9959e",
  "category": "relative_count",
  "dataset": "d3",
  "generation_commit": "",
  "infrastructure_only": false,
  "license": [
    "ARKitScenes CC BY-NC-SA 4.0"
  ],
  "pool": "b12_cntapp_gt_v1",
  "provenance": {
    "canonical": "arkitscenes/41254780",
    "frame_map_sha256": "17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3",
    "frame_store": "k6tk",
    "generator_sha256": "e3f3838f622d68d0761ca8b4d4df434158217d9eb6b074325c2ae3bd4b86f884",
    "gtvis_sha256": "e43e96764917ebbd3cc3be0a92d297d33d0fffd5d4a1a19baba795e0a58a2a2e",
    "input_sha256": {
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt/out/BUILD.json": "99a541db261e9f284383bd2594ad14583c252a84a2aff27f0add4dc11295f450",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/build.py": "f5b2245ab4335d72e0423530424d1360323cc1317eaf411aad234098a213cb47",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/code/wordings.py": "5b56669d7173ffad8dde44a04968bac7f7916ff150b3bb066283715e951a7281",
      "/scratch/jjyeung/orch_n30/fb_pack/relcnt2/out/SELECTION_60.json": "a61fba7d55c3ea496c17e4ad6f60e631b0c07eada6e926e19af9d27d0cd22583",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/CENSUS.json": "2e937bace57b8552c8de6ea49ed9a0b5faa83e75fb3bda1bafd309c5c99e5212",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12/out/PACKET_b12_v4/count_total.jsonl": "0ec47aa286991fcc36b254d30258c1044bd434b707c6a20a542f0a4e13d911a1",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/b12gt/work/rasters/arkit/41254780.npz": "b0acdef6f924ee9fd23f89874cd59543c222f72da641c75109795a5e56612b15",
      "/scratch/jjyeung/orch_n30/sb_rowC/in/procedure_source.json": "3c8529fe9686b3c574f84e6a41326e7b14d407e5b9c6fa3d3da899f87ecee2f2"
    },
    "onset_eps": 0.0005,
    "raster": "41254780.npz",
    "raster_sha256": "b0acdef6f924ee9fd23f89874cd59543c222f72da641c75109795a5e56612b15",
    "relative_count": {
      "a": "table",
      "b": "sofa",
      "bucket": "tie",
      "count_a": 1,
      "count_b": 1,
      "ids_a": [
        4
      ],
      "ids_b": [
        3
      ],
      "orientation_use_cap": 2,
      "relation": "tie",
      "room": "arkitscenes/venue383993",
      "scene_use_cap": 24,
      "source_qid": "b12ct_a9e83efb3bf2b2f839032ecf",
      "source_row_sha256": "83ec9e83d98deb34c27b9cdd128232020a1d611f168a73be1d0c40486ca56f51",
      "source_use_cap": 8,
      "template_id": 19,
      "unordered_pair_use_cap": 4
    },
    "source": "b12_cntapp gt raster",
    "view_labels": "frame_numbers",
    "visibility_floor": 0.002
  },
  "provisional_diagnostic": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW",
  "qid": "fbp_relcnt2_3770c690d6ed584ae510df0a",
  "question_type": "relative_count",
  "result_status": "diagnostic, provisional",
  "scene": "v4d72c5ac7662",
  "score_nomination_allowed": false,
  "student_input": {
    "fps": 10.0,
    "frame_indices": [
      0,
      74,
      148,
      222,
      296,
      370,
      443,
      517,
      591,
      665,
      739,
      813,
      887,
      961,
      1035,
      1109,
      1182,
      1256,
      1330,
      1404,
      1478,
      1552,
      1626,
      1700,
      1774,
      1848,
      1921,
      1995,
      2069,
      2143,
      2217,
      2291
    ],
    "frames": [
      {
        "path": "/data2/k6tk/9d/9d56c8e209a84a4f25be983e7ad35ce39734e9224264cf86ba1a642cc1f10b55.png",
        "sha256": "9d56c8e209a84a4f25be983e7ad35ce39734e9224264cf86ba1a642cc1f10b55"
      },
      {
        "path": "/data2/k6tk/17/1723812eb105300637c274f67847b492701acae0cc7796749fad2910a1163ef2.png",
        "sha256": "1723812eb105300637c274f67847b492701acae0cc7796749fad2910a1163ef2"
      },
      {
        "path": "/data2/k6tk/e1/e1da54d97d0ae818cece963f25aa44cb9e19eb460ee7379e201c826d2d244ab8.png",
        "sha256": "e1da54d97d0ae818cece963f25aa44cb9e19eb460ee7379e201c826d2d244ab8"
      },
      {
        "path": "/data2/k6tk/2a/2a77c7a2bc827b60dafd8994994b636d4b21a5cd95407cfa037d76da16f5c157.png",
        "sha256": "2a77c7a2bc827b60dafd8994994b636d4b21a5cd95407cfa037d76da16f5c157"
      },
      {
        "path": "/data2/k6tk/6e/6e615d51f054ed73c39adb7802d35edb07bdf09004f8f5490ad5ba36c65151bd.png",
        "sha256": "6e615d51f054ed73c39adb7802d35edb07bdf09004f8f5490ad5ba36c65151bd"
      },
      {
        "path": "/data2/k6tk/49/494324a67fa3fac9bd5891e035f8136551f65964d96a01470847c9434222e001.png",
        "sha256": "494324a67fa3fac9bd5891e035f8136551f65964d96a01470847c9434222e001"
      },
      {
        "path": "/data2/k6tk/0b/0b57f09d7b7735ba3b2dd5e8c63023c25abcd7d4d081a0c8faeb36f64a4ed65e.png",
        "sha256": "0b57f09d7b7735ba3b2dd5e8c63023c25abcd7d4d081a0c8faeb36f64a4ed65e"
      },
      {
        "path": "/data2/k6tk/e5/e5c21e478bb6e356aff4b10a03bcda30d47f024dcbcf2af07eb4a489f731113b.png",
        "sha256": "e5c21e478bb6e356aff4b10a03bcda30d47f024dcbcf2af07eb4a489f731113b"
      },
      {
        "path": "/data2/k6tk/5c/5cfb48d9d714c1b1782a489f4280ff1712564fd2b87b857149facecab26f40fa.png",
        "sha256": "5cfb48d9d714c1b1782a489f4280ff1712564fd2b87b857149facecab26f40fa"
      },
      {
        "path": "/data2/k6tk/8c/8c71612025f98429c90522e718fedf56a1e4941198172c87ecee5d488c4542d7.png",
        "sha256": "8c71612025f98429c90522e718fedf56a1e4941198172c87ecee5d488c4542d7"
      },
      {
        "path": "/data2/k6tk/81/81fc57d07decaccaf0c8845021869e8382d4257c4cde3b14863d47d2e3809b37.png",
        "sha256": "81fc57d07decaccaf0c8845021869e8382d4257c4cde3b14863d47d2e3809b37"
      },
      {
        "path": "/data2/k6tk/65/65a73b82d34e5b23e696b07a7b0e2abe942af17fda14257964ef7a5068cf27b0.png",
        "sha256": "65a73b82d34e5b23e696b07a7b0e2abe942af17fda14257964ef7a5068cf27b0"
      },
      {
        "path": "/data2/k6tk/bf/bf9fb2a721ff4dd8e5b181974d76f9ea0d65901457e7daa36da5120c4a62847b.png",
        "sha256": "bf9fb2a721ff4dd8e5b181974d76f9ea0d65901457e7daa36da5120c4a62847b"
      },
      {
        "path": "/data2/k6tk/ee/ee030e82afc372790f607ab848c6fe65e43b76ec8c2492867cddcb18084cad31.png",
        "sha256": "ee030e82afc372790f607ab848c6fe65e43b76ec8c2492867cddcb18084cad31"
      },
      {
        "path": "/data2/k6tk/c7/c7ae12e1e0a660c4b929933e9055e9d88fdb868eebc27e4f2bfb07be9be532f8.png",
        "sha256": "c7ae12e1e0a660c4b929933e9055e9d88fdb868eebc27e4f2bfb07be9be532f8"
      },
      {
        "path": "/data2/k6tk/ad/adc3529d2775abe66614e1a0a8da7377c2321ea27ed5ab013e7cb7e1a78f4b6e.png",
        "sha256": "adc3529d2775abe66614e1a0a8da7377c2321ea27ed5ab013e7cb7e1a78f4b6e"
      },
      {
        "path": "/data2/k6tk/05/059b1bbe9279a71a45926ddc5febe53d3715ea9ad18bdebd0368c7bc01cdebe9.png",
        "sha256": "059b1bbe9279a71a45926ddc5febe53d3715ea9ad18bdebd0368c7bc01cdebe9"
      },
      {
        "path": "/data2/k6tk/3a/3a5769265ab29c0ff098ebe4753f735304c514ff2edb85a97d68c509020a26d4.png",
        "sha256": "3a5769265ab29c0ff098ebe4753f735304c514ff2edb85a97d68c509020a26d4"
      },
      {
        "path": "/data2/k6tk/65/65c3d4c97efc1a0500e1c7b2578a5b4e23e272a5058b8eb7875f4d478d4e9310.png",
        "sha256": "65c3d4c97efc1a0500e1c7b2578a5b4e23e272a5058b8eb7875f4d478d4e9310"
      },
      {
        "path": "/data2/k6tk/b7/b76ef8a2b04676bcc26b88144cea524eed494c2a2cc85d600a7eeee4e6f3392a.png",
        "sha256": "b76ef8a2b04676bcc26b88144cea524eed494c2a2cc85d600a7eeee4e6f3392a"
      },
      {
        "path": "/data2/k6tk/af/afc20da025fe1bd159cd2048c255eef65bb61f81f88979423aa60cf8d82bc693.png",
        "sha256": "afc20da025fe1bd159cd2048c255eef65bb61f81f88979423aa60cf8d82bc693"
      },
      {
        "path": "/data2/k6tk/2e/2e0120316e7a0ca10d54de88016f4a767c2b48195d349d7ba8cb7dae91bcc513.png",
        "sha256": "2e0120316e7a0ca10d54de88016f4a767c2b48195d349d7ba8cb7dae91bcc513"
      },
      {
        "path": "/data2/k6tk/1d/1dfdb988be91a09d57008b0a13bb5bcfc937d7913857f4b24e299e79d61f7cb7.png",
        "sha256": "1dfdb988be91a09d57008b0a13bb5bcfc937d7913857f4b24e299e79d61f7cb7"
      },
      {
        "path": "/data2/k6tk/99/995ac83933072f0af5de5407044ba3694bf054c9c1e44e26e3f1662d05b79935.png",
        "sha256": "995ac83933072f0af5de5407044ba3694bf054c9c1e44e26e3f1662d05b79935"
      },
      {
        "path": "/data2/k6tk/cf/cf2105f93ea2965778082fdb3ea608a25080ba8a082d00595fbd162d178dd839.png",
        "sha256": "cf2105f93ea2965778082fdb3ea608a25080ba8a082d00595fbd162d178dd839"
      },
      {
        "path": "/data2/k6tk/14/14bd97d09dc4148aa847011be4e4d089c2d64283209e3068a1742d6fcb9dee18.png",
        "sha256": "14bd97d09dc4148aa847011be4e4d089c2d64283209e3068a1742d6fcb9dee18"
      },
      {
        "path": "/data2/k6tk/e3/e31152dd9bac65fbc9d2dba562276e7a0ec2bd9a37292723091bf5fd386cf080.png",
        "sha256": "e31152dd9bac65fbc9d2dba562276e7a0ec2bd9a37292723091bf5fd386cf080"
      },
      {
        "path": "/data2/k6tk/13/1351e145913f7f691d82499fd6119856db7768bcbb59b74d18c3ac27d68d1c7a.png",
        "sha256": "1351e145913f7f691d82499fd6119856db7768bcbb59b74d18c3ac27d68d1c7a"
      },
      {
        "path": "/data2/k6tk/aa/aa13649c35ebd67cce2831cfc707b9ae6c0e42b2657060d3141ff18110f2a104.png",
        "sha256": "aa13649c35ebd67cce2831cfc707b9ae6c0e42b2657060d3141ff18110f2a104"
      },
      {
        "path": "/data2/k6tk/fc/fc857217c604d2ec7c17cfdd9dacec4d0fcbc9f4e2d560ecdebab5508e11f8d9.png",
        "sha256": "fc857217c604d2ec7c17cfdd9dacec4d0fcbc9f4e2d560ecdebab5508e11f8d9"
      },
      {
        "path": "/data2/k6tk/3d/3d3530f4b98f149822c4a95bab2180f32f930a7b6a9c57083ddea21e1c7018a2.png",
        "sha256": "3d3530f4b98f149822c4a95bab2180f32f930a7b6a9c57083ddea21e1c7018a2"
      },
      {
        "path": "/data2/k6tk/b8/b81c3b5553340b673314ad98ef0d1ea9b3742f3cd00968edd47988c53b5fd018.png",
        "sha256": "b81c3b5553340b673314ad98ef0d1ea9b3742f3cd00968edd47988c53b5fd018"
      }
    ],
    "options": [
      "A. more",
      "B. fewer",
      "C. equal number"
    ],
    "question": "Work out separate object totals for 'table' and 'sofa' from the scene. With the 'sofa' total as the reference, which answer describes the 'table' total?",
    "timestamps": [
      0.0,
      7.4,
      14.8,
      22.2,
      29.6,
      37.0,
      44.3,
      51.7,
      59.1,
      66.5,
      73.9,
      81.3,
      88.7,
      96.1,
      103.5,
      110.9,
      118.2,
      125.6,
      133.0,
      140.4,
      147.8,
      155.2,
      162.6,
      170.0,
      177.4,
      184.8,
      192.1,
      199.5,
      206.9,
      214.3,
      221.7,
      229.1
    ],
    "total_num_frames": 2292
  },
  "target": "<think>\nlocate the distinct instances of table; count each once across the frames.\nlocate the distinct instances of sofa; count each once across the frames.\nSo there are as many table instances as sofa instances.\n</think>\n\nC",
  "validation_commit": ""
}
```
