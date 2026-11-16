# Package inventory and diffs

KIT_SHA256: `f42aa1a4aec049e03a321e88ccd8a5004a3e95963b08f18242db625bdec95684`

package.tar uses sorted names, mtime 0, uid/gid 0 and empty owner/group names. DIFF.md, REPORT.md, KIT_SHA256 and this build inventory are external sidecars to avoid a circular self-hash. Local environments, caches, test runs, generated media, archives and large accepted result journals are excluded.

## Scope

- Exactly one evaluator file changes: evalpath/kit_inputs.py adds optional sorted question_types and example_ids filters after the full 5,130-row check; proof selection reaches every caller through the same loader. All 35 other evaluator files equal the accepted bound kit inventory. Every caller enters through data.tasks_for; budgets inherit the worker source IDs and merge against the same loader.
- evalpath/SOURCE_PINS.json does not pin kit_inputs.py. It records upstream official/trainer provenance and remains identical. New per-bind code inventories authenticate the changed kit; the old CODE_PINS/source archive digest is not falsely reused.
- common.py, export_check.py, direct.py and vendor imports are byte-identical. The official adapter does not use the dev label override or PNG store. The unchanged dev wrapper/r3 path remains available for prompt parity.
- Launcher preparation replaces lost release/review files with an explicitly new build-integrity record, fixed step/artifact/model pins and the rebuilt transport. It does not invent an ACCEPT review, training receipt or recovered attestation.
- orchard_stage retains runtime, camera compatibility package, base, payload, bwrap and generation-pinned GCS export staging. It replaces the PNG pull with 288 sequential, SHA-verified video copies using only the two aliases, plus the pinned questions. Physical video cache filenames are SHA256 values. Dataset paths exist in the private bwrap view under the supplied alias; legacy absolute namespace paths remain necessary for the immutable export and runtime links.
- orchard_job retains the H100 checks and local-storage policy, calls reader/chain.py through the accepted vLLM interpreter; proof mode keeps real H100 checks, uses runtime_0 for decoded planning/frame staging, runs 14 official items with AsyncLLM fake, then launches real vLLM on 20 accepted dev-main items in a fresh interpreter. Proof returns stay below 20 MB and production below 90 MB. chain_save saves one copy of each arm and receipt and enforces the existing 512 MiB expanded verifier limit. orchard_results builds locally and verifies independent pool/GCS copies; stdout_transfer remains identical but fetch streams raw bytes directly.
- submit/fetch use the requested ossh.sh operator wrapper. The /data3 notice write is removed. No remote command or job submission ran during this build.
- The deterministic package contains CPU proof code and parity data; both embedded payloads include the same reader, vendor parity data, selection, engine fake and runtime helpers; they exclude official metadata and test artifacts and remain below the original 3 MiB base64 limit.

- Stdlib tracing records hash-keyed line sets in every job Python process and its threads; final publication lines return as a separate bounded TRACE sidecar. lines_report.py combines only matching source hashes.
- Proof and production preparations carry byte-identical code; deterministic gzip removes timestamp differences. CONFIG mode and phase_b select execution; both modes request one GPU; tokens also bind paths and derived hashes.

## File hashes

| File | Status | SHA256 | Accepted SHA256 |
|---|---|---|---|
| PROOF_JOB.md | NEW | `dd48a6feb26692d98bb337c0ce7a8b39d6bedb900dd58d61c781e763fa2b9f7d` | `—` |
| build/ORIGINS.json | NEW | `d49937a798dce62154631ba9ccec55f5aa3b1b2ea81d53929c20addc9b0d322f` | `—` |
| build/PASS2_FILES.json | NEW | `e3fd14091ca2e5d6fab779007541a1031171f32aa4947026d36cea47ec0818de` | `—` |
| build/coverage_report.py | NEW | `27e1d226490c6806bbd1853ead36906d0ffc6114c79d88a71dbc05751e38cb94` | `—` |
| build/package.py | NEW | `22b96994582faa9a52c0dc4a1594946ed6b0a949dce1d9c56ed3b520dfd3a8a0` | `—` |
| build/phase_b_reference.py | NEW | `a86f3e64ce7a012505e3a72479c296389d33f44e4af417928a60b66b3802e1d1` | `—` |
| cohort/COHORT_OFFICIAL6.jsonl | NEW | `ccb51d5cbb552cb942518ed47badd36d4d5778a7dacaf6615e88cd1118361db8` | `—` |
| cohort/MEDIA_MANIFEST.json | NEW | `3f2aba2c25c04e06f0f0badb854e3e7b836d2a60bec8fa28453c6dd41060d5c4` | `—` |
| cohort/frame_plan.py | NEW | `402bdb1d5fb0559f241e951a4c303ef5495e38c347e0a970c2f412e2587e1eec` | `—` |
| cohort/meta_5130.jsonl | IDENTICAL | `d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc` | `d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc` |
| launcher/MODELS.json | NEW | `72cdfbff0e93a881099096f06e22b5c7e98046d443ae3430d498d06b49cfb37a` | `—` |
| launcher/ORCHARD_ASSETS.json | CHANGED | `7e1da1668b4bac1d101692486e45f45912ccdde13d9f8ba8ca72cdd2287bf809` | `3e2139522741cb301aed445d37c6f4180f00e2950c04045dca0c9658321b37c2` |
| launcher/TRANSPORT.json | NEW | `23339074f3eb41507c3e3c657159415582573cd8332c3b4777b4ac577a7b3b50` | `—` |
| launcher/chain_save.py | CHANGED | `c03862ffe60619f45a70514b0402db0411b5c6c79d2af8cbac48945575c15bdc` | `5f870cb53a99933a4a580c8e052895827528931e0c77c141d240c695fadecffc` |
| launcher/orchard_job.py | CHANGED | `b464a88866be571bdce7ddfdb1df70485c88c46102779e9c442369f1c4cbfe3c` | `4c24c386ea0679e6f812c0cf6fbad2d593c427327cd7c69b80bf9a558c35314b` |
| launcher/orchard_launcher.py | CHANGED | `0905ed2a8150ff81156d44437c1648fc516d18a245f9ad59b22a12ad58d8f484` | `33d535b00bd879860a058f630d01ee153c6228123f3697db8d30b8a4233dd49e` |
| launcher/orchard_results.py | CHANGED | `6cf748b3539571935f3266e88510b222dfdbb8992a4024a0da44166f830a466e` | `0c0a2213842515bd2421ac9b60dc738edf14729fa29d819563ca713f6cbc76de` |
| launcher/orchard_stage.py | CHANGED | `4401b329597f8c4491d949b2804df7d011909837dd35a84e23e1f07279217461` | `eb26cea5b056f9fa88c1675109cd18db693f94436a9ccb92aaf3beb092a8d424` |
| launcher/proof_card.py | NEW | `332fd8c0cd26cc303463da8055261a17d77081f59df69a31d945bd9352ecc606` | `—` |
| launcher/return_io.py | NEW | `774f5c0c134c44fd2ca5261e2ceb0b34f4cbd0edee5cffffa4c4f091ca4c6d90` | `—` |
| launcher/stdout_transfer.py | IDENTICAL | `85ad256cfa7836948ddba934ca82537486fc3c42cab06fa5442de86caef2e0f6` | `85ad256cfa7836948ddba934ca82537486fc3c42cab06fa5442de86caef2e0f6` |
| launcher/trace_runtime.py | NEW | `faec481ff5b445fdeb885a0ee70e1f83beaff05afb115dd3073fa6ce1934237d` | `—` |
| parity/ACCEPTED20.json | NEW | `cf30bbe06af9c5a7d9d9bbf40ff9344b439bc0a8a3932dc422edb658be09a5b6` | `—` |
| parity/DEV20.json | NEW | `6220488ff2488ce2084d38de4513bf35535f23a3e65b19cf216e8bcf23400b99` | `—` |
| parity/PROMPT_PINS.json | IDENTICAL | `7a43deb2ee2756d13044640c394deb4e8a5a7b6e59045f17bd7b1beb9f588637` | `7a43deb2ee2756d13044640c394deb4e8a5a7b6e59045f17bd7b1beb9f588637` |
| parity/prove_prompts.py | NEW | `e46ef2c4d566ebd2b8c5cc970877184d028e801c8cd2a4d3b3e52055e87451b2` | `—` |
| proof/COVERAGE.json | NEW | `b6f26d7f9a34dcb1e573549083b3e9dc7cdcf8b91afaa1e8fb2cf79300e33965` | `—` |
| proof/COVERAGE_SUMMARY.json | NEW | `5f48fe83b799bbce4da54bb2f785d1ed2a58f07004f4fe73739d5d9fcb6ca30a` | `—` |
| proof/LINES.md | NEW | `9a8695ce9b34f6cca7582e894d6ce96939886e6b8272ea729328fc5dba54a26f` | `—` |
| proof/LINES_CHECK.json | NEW | `ae504777e854f6aaa77a66d8f8a13998af4752048a91bf10f000677a30e979cc` | `—` |
| proof/LINES_LOCAL.json | NEW | `ae504777e854f6aaa77a66d8f8a13998af4752048a91bf10f000677a30e979cc` | `—` |
| proof/LOCAL_LINES.json.gz | NEW | `e5878839ad2972b5e05667e72bf189bacd554f33f3cbc0fe1b4c96c814ec3373` | `—` |
| proof/PROOF.md | NEW | `73a9bff3d22e48c51363b7965be32d2aec0e7d4aaa62d0e7a15a0ec1a9878c87` | `—` |
| proof/SCORER_CHECK.json | NEW | `47aa108257f1d1c88b1661ec21f795744fad0627cd78ad6fdac7a46086b69871` | `—` |
| proof/coverage.ini | NEW | `1de06729cb8823fa8f4edccc04c6a98c2d80818d22a83d28251a34678d064109` | `—` |
| proof/fakes.py | NEW | `e8d8d0c1321f168341e1aa62357b710c6888f07c1302c4a54f442c58af490788` | `—` |
| proof/fixtures.py | NEW | `bd0568ba819a4f713c8c42b8833317044879eef2af0d2137e62f87ed288569fb` | `—` |
| proof/lines_report.py | NEW | `0e47e9c12cf2818ca460789db68aeb4f44bbd88a6e643ca3ddf74074f6fd45a1` | `—` |
| proof/measure.py | NEW | `108de721d328e0cb0951fe9563764ba46bd01a1e0fbf72884362a8ae0b79a2a9` | `—` |
| proof/orchard_env.py | NEW | `acba5c863658c0f81bfef9ca3c7c9abb5e76ec86926181bb188727c27dac45f3` | `—` |
| proof/phase_b.py | NEW | `3d7171dc348f4d7cd9b5a6fda26f4e9146eaf56633d366fb5dbf2ac4458f3f79` | `—` |
| proof/plan_on_orchard.py | NEW | `7b8071d7697802da68b1c95aaabbc6b2c98a48a57472e523b897ba53dcd40115` | `—` |
| proof/pull.py | IDENTICAL | `46000e96334535933239800d1437afc49cc74ca4017c337a43798c9906b8b694` | `46000e96334535933239800d1437afc49cc74ca4017c337a43798c9906b8b694` |
| proof/run.py | NEW | `7fa69ad83f6635d491d4ce4b3e4a118c08a4f4af60df65369d1814e16f5cc84e` | `—` |
| proof/run_on_orchard.sh | NEW | `faa4af48f9a684b35daadb22a21dc7d54539ebae8793660968e21d3a892e3eaf` | `—` |
| proof/runtime_checks.py | NEW | `45bf7ad05d2dbfa57c7c17c7b0ac7e1cbfed0a092b60ebd0f0e84d7f6f131dd2` | `—` |
| proof/selection.py | NEW | `76d77f2807efbaec70c6c879219aceb2a7159e54cbcba1c45507e93bbd7f356e` | `—` |
| reader/chain.py | NEW | `9084b66515fb01b1269d0b6e0ebbe3402c2b11468abcd77c9a14df4facdcc0ec` | `—` |
| reader/evaluator/budget.py | IDENTICAL | `8365bd3b1db5bedc0a86e2ef9624faf01ad43d0e3d3fffda53169cd9ad003175` | `8365bd3b1db5bedc0a86e2ef9624faf01ad43d0e3d3fffda53169cd9ad003175` |
| reader/evaluator/budget_admission.py | IDENTICAL | `be32a571fbb9c4024d739b51302d3881aa1ce628bb45e2e8cc9924060f653341` | `be32a571fbb9c4024d739b51302d3881aa1ce628bb45e2e8cc9924060f653341` |
| reader/evaluator/budget_annotation.py | IDENTICAL | `c63f058069e8302fcd3bd69505690ab0e784b6f368d3492429335d30cebbc4d1` | `c63f058069e8302fcd3bd69505690ab0e784b6f368d3492429335d30cebbc4d1` |
| reader/evaluator/budget_merge.py | IDENTICAL | `fc7c2872dc5daeb1eb1de61ee95b7b7a0e160fc697995ac2caf1615a4bd7ff2a` | `fc7c2872dc5daeb1eb1de61ee95b7b7a0e160fc697995ac2caf1615a4bd7ff2a` |
| reader/evaluator/c1_export.py | IDENTICAL | `7716fd6750376830519ef39295992bfab6876e644c92745d6a0ec82aceec7177` | `7716fd6750376830519ef39295992bfab6876e644c92745d6a0ec82aceec7177` |
| reader/evaluator/cells.py | IDENTICAL | `8336d2d64ffd2b7f492dc6b52fb4182523eced3610483932d91e086d2b9b50ff` | `8336d2d64ffd2b7f492dc6b52fb4182523eced3610483932d91e086d2b9b50ff` |
| reader/evaluator/data.py | IDENTICAL | `279991a8303e75f8cf553d3b94acb3c62fea82b27a65ac736dad6ab043914e41` | `279991a8303e75f8cf553d3b94acb3c62fea82b27a65ac736dad6ab043914e41` |
| reader/evaluator/evalpath/SOURCE_PINS.json | IDENTICAL | `7f1d449de1498e5a6f34dbdc09309dcbeaceef76e3f20bec92f603771a345781` | `7f1d449de1498e5a6f34dbdc09309dcbeaceef76e3f20bec92f603771a345781` |
| reader/evaluator/evalpath/__init__.py | IDENTICAL | `320ff8e49d53c5528f439ae83544dcd0e4063933eb2168774b70ca6d9d1cdd38` | `320ff8e49d53c5528f439ae83544dcd0e4063933eb2168774b70ca6d9d1cdd38` |
| reader/evaluator/evalpath/items.py | IDENTICAL | `bc9211c07c803111a8c9f6af8ecb6e7bc057b0034da09ad94b02862f41526590` | `bc9211c07c803111a8c9f6af8ecb6e7bc057b0034da09ad94b02862f41526590` |
| reader/evaluator/evalpath/kit_inputs.py | CHANGED | `e4a6bdae702ab3fb003d7c11388fc22b051f92e5f9ca3d1cf0e95c250a0cd977` | `4c06fbdf916e081334c6599942a89f37b4240389fcb401b9dac5fb5814798faa` |
| reader/evaluator/evalpath/official.py | IDENTICAL | `a5d6d79fd29fce43791401cd01438f16f3ff6ad7a6c2651cb70d0d42088cf589` | `a5d6d79fd29fce43791401cd01438f16f3ff6ad7a6c2651cb70d0d42088cf589` |
| reader/evaluator/evalpath/sampling.py | IDENTICAL | `9235a822a813648ee0da7cf9cc79531a4cbb7b6344e8fee369e5b34e615d82e1` | `9235a822a813648ee0da7cf9cc79531a4cbb7b6344e8fee369e5b34e615d82e1` |
| reader/evaluator/frame_env.py | IDENTICAL | `8b6ddcb0caa15e68f304d50cd41952b7e7d9eba4542c1beb1b49ecdf9b6be7ed` | `8b6ddcb0caa15e68f304d50cd41952b7e7d9eba4542c1beb1b49ecdf9b6be7ed` |
| reader/evaluator/frame_stage.py | IDENTICAL | `991f297fd783a37342ab65f4fed5580b47fb25550375efdee5fce14564b3ea5c` | `991f297fd783a37342ab65f4fed5580b47fb25550375efdee5fce14564b3ea5c` |
| reader/evaluator/journal.py | IDENTICAL | `508eca8d6877fe6898d9309f0f5c23b4580c321d27dc258ddd6fe4718cc9b1a5` | `508eca8d6877fe6898d9309f0f5c23b4580c321d27dc258ddd6fe4718cc9b1a5` |
| reader/evaluator/launch.py | IDENTICAL | `80af57d28cffe87e85d76a898ab6c4cbe898d53772ce1e90ecbcee4d333009f2` | `80af57d28cffe87e85d76a898ab6c4cbe898d53772ce1e90ecbcee4d333009f2` |
| reader/evaluator/media.py | IDENTICAL | `537fb597909e41699511d2e85c16029836cc4ba5aa0fcf25dc76f3abe5f0fc8d` | `537fb597909e41699511d2e85c16029836cc4ba5aa0fcf25dc76f3abe5f0fc8d` |
| reader/evaluator/merge.py | IDENTICAL | `5da344c8ff214bcd106b0b78635eda330aed2a85169ac03e1ef9977341d65912` | `5da344c8ff214bcd106b0b78635eda330aed2a85169ac03e1ef9977341d65912` |
| reader/evaluator/metric.py | IDENTICAL | `aa0c7968a9a8c812222b8d3468864b54e13eb21cff25155e4a6393508beb05fc` | `aa0c7968a9a8c812222b8d3468864b54e13eb21cff25155e4a6393508beb05fc` |
| reader/evaluator/nested_sampling.py | IDENTICAL | `231bad31b385b01d3fdd46d8b8341e6ebfcc67e6d06cfb8f1fc277ec5bf017f2` | `231bad31b385b01d3fdd46d8b8341e6ebfcc67e6d06cfb8f1fc277ec5bf017f2` |
| reader/evaluator/parity.py | IDENTICAL | `6e259bd1dd23ec67bb8feef5a3a06bbc2e67ecfd60cc98a876febd510f44c14c` | `6e259bd1dd23ec67bb8feef5a3a06bbc2e67ecfd60cc98a876febd510f44c14c` |
| reader/evaluator/pointing.py | IDENTICAL | `1ee243eb896b518c74f06f18a3d98a213a7d5f09617296b3a5d9cf26d2a2ff5c` | `1ee243eb896b518c74f06f18a3d98a213a7d5f09617296b3a5d9cf26d2a2ff5c` |
| reader/evaluator/pointing_video.py | IDENTICAL | `4712457ebf1e932219966a5b4eae6bddbc43a077251f717e636085c88dba1ee7` | `4712457ebf1e932219966a5b4eae6bddbc43a077251f717e636085c88dba1ee7` |
| reader/evaluator/provenance.py | IDENTICAL | `35e544877add1d9d4b6e2167aa071ffda13da390db4a410bd4b51339655b5c7c` | `35e544877add1d9d4b6e2167aa071ffda13da390db4a410bd4b51339655b5c7c` |
| reader/evaluator/scoring.py | IDENTICAL | `0e3bcf0a578f18846f671b85582bb030137bb3169346dd5f99a10c6a8b099cce` | `0e3bcf0a578f18846f671b85582bb030137bb3169346dd5f99a10c6a8b099cce` |
| reader/evaluator/stage.py | IDENTICAL | `890ea8641c08c2de4e12169c77202c8cc7b19f1bc360c0a36509c5c451474d2b` | `890ea8641c08c2de4e12169c77202c8cc7b19f1bc360c0a36509c5c451474d2b` |
| reader/evaluator/think_settings.py | IDENTICAL | `23af8945c30247bc80ebd0b2b7b7e6d22c0e6e70a190594d84161af49fb533df` | `23af8945c30247bc80ebd0b2b7b7e6d22c0e6e70a190594d84161af49fb533df` |
| reader/evaluator/token_audit.py | IDENTICAL | `20dd4f31b70350b80ddb0cab1b35294349b9ff8f76058648da5537e265cff0b0` | `20dd4f31b70350b80ddb0cab1b35294349b9ff8f76058648da5537e265cff0b0` |
| reader/evaluator/trainer/__init__.py | IDENTICAL | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| reader/evaluator/trainer/batches.py | IDENTICAL | `d9f5a79b63baf1144dc5d0377450491dcb04c28335dbce51093e4edde7614638` | `d9f5a79b63baf1144dc5d0377450491dcb04c28335dbce51093e4edde7614638` |
| reader/evaluator/trainer/layout_reference.py | IDENTICAL | `596760db5b3ccf6cceb5ab2938402ba9e6c559a069ef5fd84b041ce90b71700e` | `596760db5b3ccf6cceb5ab2938402ba9e6c559a069ef5fd84b041ce90b71700e` |
| reader/evaluator/trainer/pose_samples.py | IDENTICAL | `0484ecce014fa97f6f2b44f250ddfdee142b42662d765638f130c59ddd53a736` | `0484ecce014fa97f6f2b44f250ddfdee142b42662d765638f130c59ddd53a736` |
| reader/evaluator/trainer/students.py | IDENTICAL | `cfe01c144680c8126328e7ad9afc7b1a002de7ba143dcea9c156e0473fe619c3` | `cfe01c144680c8126328e7ad9afc7b1a002de7ba143dcea9c156e0473fe619c3` |
| reader/evaluator/trainer/trace_contract.py | IDENTICAL | `aed482c7ca7d15cd22b524ba0c9bdd1595d6e0c518c0d9d1e54c3c9377cebae8` | `aed482c7ca7d15cd22b524ba0c9bdd1595d6e0c518c0d9d1e54c3c9377cebae8` |
| reader/evaluator/worker.py | IDENTICAL | `b2ac21c1549b87baff730e50279d3c4c0844966bc5e29363aef372c76574e20e` | `b2ac21c1549b87baff730e50279d3c4c0844966bc5e29363aef372c76574e20e` |
| reader/official_adapter.py | NEW | `02b2e8df44b0c392861f4d5cdff749bc7b3cc0547229f88cb6ac6585592bfca8` | `—` |
| reader/official_score.py | NEW | `b8399cb01390774726adba21565efc49cbeaf299ea737c918e8d42b0a99604e0` | `—` |
| reader/out/common.py | IDENTICAL | `1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4` | `1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4` |
| reader/out/direct.py | IDENTICAL | `d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a` | `d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a` |
| reader/out/export_check.py | IDENTICAL | `0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2` | `0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2` |
| reader/work/vendor/r3/CELL_ITEMS.json | IDENTICAL | `ed6d686aad9e21ceeeebe3ef7b9b0a8ff4bb2f9334b0f546ca972003fdcce860` | `ed6d686aad9e21ceeeebe3ef7b9b0a8ff4bb2f9334b0f546ca972003fdcce860` |
| reader/work/vendor/r3/EXCLUDED.jsonl | IDENTICAL | `f7a212048c2cfe95538b4c35d5f9147ff107743d1811ca0c57880ca93ae38941` | `f7a212048c2cfe95538b4c35d5f9147ff107743d1811ca0c57880ca93ae38941` |
| reader/work/vendor/r3/EXCLUDED_MISSING_ROOM.jsonl | IDENTICAL | `279889626320714771abbd38185d3b07b8abb7daf3b965301d1842bbc8dcfdfd` | `279889626320714771abbd38185d3b07b8abb7daf3b965301d1842bbc8dcfdfd` |
| reader/work/vendor/r3/FPS_AUTHORITY.source.json | IDENTICAL | `36ae882f936ebc7a7d1a7651b5c53056c07d39ff552b2368a5c1e8068568d422` | `36ae882f936ebc7a7d1a7651b5c53056c07d39ff552b2368a5c1e8068568d422` |
| reader/work/vendor/r3/FPS_RULE.json | IDENTICAL | `d9af606320e78823fb2e0fa3c80358c77d7e3cdc2326684a501893c04af3094f` | `d9af606320e78823fb2e0fa3c80358c77d7e3cdc2326684a501893c04af3094f` |
| reader/work/vendor/r3/FRAMES.json | IDENTICAL | `c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439` | `c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439` |
| reader/work/vendor/r3/ITEMS.jsonl | IDENTICAL | `00144cd0f736b4bd7908030b7feb749a926d7ef37b54c555c09bdd8c82ef9111` | `00144cd0f736b4bd7908030b7feb749a926d7ef37b54c555c09bdd8c82ef9111` |
| reader/work/vendor/r3/LABEL_BLOCKERS.jsonl | IDENTICAL | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| reader/work/vendor/r3/LABEL_SOURCE_PINS.json | IDENTICAL | `8b69c0a012cca31376f2b46c7da58744cdfb94af4ec94f9bb646f2c92d981efb` | `8b69c0a012cca31376f2b46c7da58744cdfb94af4ec94f9bb646f2c92d981efb` |
| reader/work/vendor/r3/MISSING_LABELS.jsonl | IDENTICAL | `b8aff3d740f37d95b3e4a85a3f3faac5580b2e19c02cb2360e541611a2dacd4b` | `b8aff3d740f37d95b3e4a85a3f3faac5580b2e19c02cb2360e541611a2dacd4b` |
| reader/work/vendor/r3/PINS.json | IDENTICAL | `698d623e9f49bdcbf101719bb2b09fd7239452d1d610d827110a1423dcce9db2` | `698d623e9f49bdcbf101719bb2b09fd7239452d1d610d827110a1423dcce9db2` |
| reader/work/vendor/r3/RELEASED_DEV.jsonl | IDENTICAL | `edafe3e5b436f16fd22a49facd25c62216f3478c6952ccbd9e5e1eef7cae7760` | `edafe3e5b436f16fd22a49facd25c62216f3478c6952ccbd9e5e1eef7cae7760` |
| reader/work/vendor/r3/STRATA.jsonl | IDENTICAL | `9ee9c29820a85cf4da89a4499d8bc644b5c88c0ad22f151a09a770b025563af0` | `9ee9c29820a85cf4da89a4499d8bc644b5c88c0ad22f151a09a770b025563af0` |
| reader/work/vendor/r3/TASKS.jsonl | IDENTICAL | `a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e` | `a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e` |
| reader/work/vendor/r3/TIMING_AUTHORITY.json | IDENTICAL | `7827fb117e158809c59bda741976a872761790bbd2298047ba8c6f33ba72ea43` | `7827fb117e158809c59bda741976a872761790bbd2298047ba8c6f33ba72ea43` |
| reader/work/vendor/r3/WITHHOLD_SCENES.json | IDENTICAL | `88e1a708e240920fb39e34ede6f47c189be830538388db7a214b60ca258df05e` | `88e1a708e240920fb39e34ede6f47c189be830538388db7a214b60ca258df05e` |
| reader/work/vendor/r3/adapter.py | IDENTICAL | `eb53eb601f7ef5ed732f0d7a9ef2275349de9553eb9c7ac39dd464bcfa03789a` | `eb53eb601f7ef5ed732f0d7a9ef2275349de9553eb9c7ac39dd464bcfa03789a` |
| reader/work/vendor/r3/cells_cp1m200.json | IDENTICAL | `472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135` | `472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135` |
| reader/work/vendor/r3/cells_f17.json | IDENTICAL | `cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878` | `cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878` |
| reader/work/vendor/r4/adapter.py | IDENTICAL | `9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099` | `9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099` |
| reader/work/vendor/r5/adapter.py | IDENTICAL | `431b5d367ccde126f02297489da5a328ecd2484bd787f8acfae73eecec3fd9d1` | `431b5d367ccde126f02297489da5a328ecd2484bd787f8acfae73eecec3fd9d1` |
| reader/work/vendor/r5/dev_scoring.py | IDENTICAL | `d7594f9dad6045a6c6fdb55e7136401a6368d1c2fabc801bc1cb7c7eaedda220` | `d7594f9dad6045a6c6fdb55e7136401a6368d1c2fabc801bc1cb7c7eaedda220` |
| reader/work/vendor/r5/report.py | IDENTICAL | `c0d60afe47a5459150d40841e923fffe90d7ea749c12fcd3ef44b21950b24fd6` | `c0d60afe47a5459150d40841e923fffe90d7ea749c12fcd3ef44b21950b24fd6` |
| tests/conftest.py | NEW | `2f68c7c03f6c9d73cc3dacdf6e227bce4f7b5ceb270b7656f2c56774d2e41b71` | `—` |
| tests/test_kit.py | NEW | `74a8811ceb10b9666094a044c9dc18304499673b3bcb9af53a8418e0031cc4a6` | `—` |
| tests/test_pass2.py | NEW | `c068c1ce472fb29766ec27d3fe498afa56e1c6722f9473557b102a8a0a967a03` | `—` |
| tests/test_pass3.py | NEW | `c8e378dde95ee969d29ab44d5f2eca6a4f26a752346fe4c82c6e2d00e8dfbd66` | `—` |

## Changes in this pass

Pool configuration defaults to /project/community/jjyeung/okh7/x27ret. A subprocess performs a 4 MiB fsync/SHA256 write test with a 60-second deadline before staging. Pool locks enforce <100 MB; proof returns stay <20 MB and production packets <90 MB. Only the authorized .wtest is removed.
Both return channels verify independently. GCS uploads use the export credentials, deadlines, object generations and SHA256 readback. Receipts/logs identify verified channels. Fetch streams pool/GCS stdout into the lane; >=20 MB stops for governor registration.
Proof requests an H100/16 CPUs/200G/2h, keeps real card checks, runs 14 official fake-engine items and then 20 dev-main real-engine items. An isolated interpreter prevents fake-engine leakage. Accepted request/cell settings and sort order are checked; smoke_items alone limits the dev prefix.
Twenty reconstructed frame receipts match accepted frames/0.json hashes and identify 576 PNGs. The unchanged accepted puller reads k6tk. Phase B requires 16 ID and two pixel checks and reports accepted prompt hashes, item-level generation/answer/score agreement and paired arm means.
Local proof uses fake engines for both phases and miniature media/model/storage fixtures. New tests cover return channels, deadlines, corruption, caps, fetch registration, Phase A gating, accepted receipt reconstruction and comparison counts. No Orchard action was performed.
Final trace sidecars use bounded pool/GCS publication; the archive snapshot remains available if sidecar publication fails. The job runner keeps mode separate from storage evidence.

### Changed/new files relative to the supplied kit

- CHANGED: `PROOF_JOB.md`
- CHANGED: `build/ORIGINS.json`
- NEW: `build/PASS2_FILES.json`
- CHANGED: `build/coverage_report.py`
- CHANGED: `build/package.py`
- NEW: `build/phase_b_reference.py`
- CHANGED: `launcher/chain_save.py`
- CHANGED: `launcher/orchard_job.py`
- CHANGED: `launcher/orchard_launcher.py`
- CHANGED: `launcher/orchard_results.py`
- NEW: `launcher/return_io.py`
- CHANGED: `launcher/trace_runtime.py`
- NEW: `parity/DEV20.json`
- CHANGED: `proof/COVERAGE.json`
- CHANGED: `proof/COVERAGE_SUMMARY.json`
- CHANGED: `proof/LINES.md`
- CHANGED: `proof/LINES_CHECK.json`
- CHANGED: `proof/LINES_LOCAL.json`
- CHANGED: `proof/LOCAL_LINES.json.gz`
- CHANGED: `proof/PROOF.md`
- CHANGED: `proof/coverage.ini`
- CHANGED: `proof/lines_report.py`
- NEW: `proof/phase_b.py`
- NEW: `proof/pull.py`
- CHANGED: `proof/run.py`
- CHANGED: `proof/selection.py`
- CHANGED: `reader/chain.py`
- CHANGED: `tests/test_kit.py`
- CHANGED: `tests/test_pass2.py`
- NEW: `tests/test_pass3.py`
- CHANGED: `REPORT.md`, `DIFF.md`, `KIT_SHA256`, `package.tar` and external build inventories.

## Unified diffs

### launcher/ORCHARD_ASSETS.json

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/ORCHARD_ASSETS.json`.

```diff
--- accepted/launcher/ORCHARD_ASSETS.json
+++ package/launcher/ORCHARD_ASSETS.json
@@ -2,7 +2,7 @@
   "schema": "evalx-orchard-existing-assets-v1",
   "observed_utc": "2026-11-13T19:56Z",
   "observed_host": "orchard-login-001",
-  "base_archive": "/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar",
+  "base_archive": "/project/community/jjyeung/f3069074.tar",
   "base_archive_bytes": 19329320960,
   "base_manifest": {
     "path": "/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/90da7ac2/m/base_manifest.json",
@@ -19,29 +19,80 @@
     "bytes": 3686400,
     "sha256": "9eb53a96642d8bc0c731bd49861a6ce1935c9013e9eb9147da4d94df6f760ff5"
   },
-  "frames_root": "/project/community/jjyeung/cp4tk_fr/k6tk",
   "gcloud_config": "/project/community/jjyeung/gcloud",
   "vnice_sha256": "3ab2b542726f32dbecdbe30104f903aa2bef3526a9257013fd5f8bcc99461c6b",
   "terminator_sha256": "cbb91ba7455d15007bd3affeb358dc5693f3845949ee0abacf892a4402748b94",
   "groups": [
     [
-      ["/home/jjyeung/okit/p/d59945c1/4fe70504.00", 900000000, "273174ae1d1bc812a8843b3e2eec77e77b66b4a10d60c8871ea47529c395e2d7"],
-      ["/home/jjyeung/okit/p/d59945c1/4fe70504.01", 721422080, "c733222251bfa18ca823a719e025e3924fda21cffffc6f50cd19bb8ece4860a3"]
+      [
+        "/home/jjyeung/okit/p/d59945c1/4fe70504.00",
+        900000000,
+        "273174ae1d1bc812a8843b3e2eec77e77b66b4a10d60c8871ea47529c395e2d7"
+      ],
+      [
+        "/home/jjyeung/okit/p/d59945c1/4fe70504.01",
+        721422080,
+        "c733222251bfa18ca823a719e025e3924fda21cffffc6f50cd19bb8ece4860a3"
+      ]
     ],
     [
-      ["/home/jjyeung/okit/p/d59945c1/50011a59.00", 900000000, "a4ca7e645d1c4384bdb9506ef3e823e3964e18948f48cc627709f843744ea976"],
-      ["/home/jjyeung/okit/p/d59945c1/50011a59.01", 900000000, "beca0e524255eb310d978ec092bfab080f45e36e05ae99bfc2c3e6aeb0882e9a"],
-      ["/home/jjyeung/okit/p/d59945c1/50011a59.02", 900000000, "508e09bcce4652471a5f3115344c2ab2e2fde61cc3db17d872d45c37861087c1"],
-      ["/home/jjyeung/okit/p/d59945c1/50011a59.03", 900000000, "6f25823a68896cbf0dc87ae26a9e4d2fa25d57b1d52739c22ccad5c5d49214ef"],
-      ["/home/jjyeung/okit/p/d59945c1/50011a59.04", 900000000, "139fcc93fb1b36552564fceacf201127586c237d03f43b8e3c8e45d116f1be97"],
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05", 900000000, "1cd72e6e222dbe15efab47d01adeca45aaecf3f62fcd52a6e72dd7786b307489"],
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06", 900000000, "010b1302ce0ec32d1db758a4bf503e9cca4583e898ec868be4dc613694f50ed6"],
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07", 900000000, "32687478f272e14632411099b316fdbb6b2d1587708ccd1893c4819a2511ba19"],
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08", 900000000, "d571f17a5ed9e03514ec4553919cdebacb33fe037cad39d8f0aadb1cfafcb4fc"],
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09", 366728960, "128dfaca7b744e0cf884b7caf1bc15080fab549b8e26107adb5a9b8d2b5a51a5"]
+      [
+        "/home/jjyeung/okit/p/d59945c1/50011a59.00",
+        900000000,
+        "a4ca7e645d1c4384bdb9506ef3e823e3964e18948f48cc627709f843744ea976"
+      ],
+      [
+        "/home/jjyeung/okit/p/d59945c1/50011a59.01",
+        900000000,
+        "beca0e524255eb310d978ec092bfab080f45e36e05ae99bfc2c3e6aeb0882e9a"
+      ],
+      [
+        "/home/jjyeung/okit/p/d59945c1/50011a59.02",
+        900000000,
+        "508e09bcce4652471a5f3115344c2ab2e2fde61cc3db17d872d45c37861087c1"
+      ],
+      [
+        "/home/jjyeung/okit/p/d59945c1/50011a59.03",
+        900000000,
+        "6f25823a68896cbf0dc87ae26a9e4d2fa25d57b1d52739c22ccad5c5d49214ef"
+      ],
+      [
+        "/home/jjyeung/okit/p/d59945c1/50011a59.04",
+        900000000,
+        "139fcc93fb1b36552564fceacf201127586c237d03f43b8e3c8e45d116f1be97"
+      ],
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05",
+        900000000,
+        "1cd72e6e222dbe15efab47d01adeca45aaecf3f62fcd52a6e72dd7786b307489"
+      ],
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06",
+        900000000,
+        "010b1302ce0ec32d1db758a4bf503e9cca4583e898ec868be4dc613694f50ed6"
+      ],
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07",
+        900000000,
+        "32687478f272e14632411099b316fdbb6b2d1587708ccd1893c4819a2511ba19"
+      ],
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08",
+        900000000,
+        "d571f17a5ed9e03514ec4553919cdebacb33fe037cad39d8f0aadb1cfafcb4fc"
+      ],
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09",
+        366728960,
+        "128dfaca7b744e0cf884b7caf1bc15080fab549b8e26107adb5a9b8d2b5a51a5"
+      ]
     ],
     [
-      ["/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00", 409282560, "4b11b4df5ebf8a20e5c73e5ae09f4f4695f79b44e0223254a8bbaad84127b6b3"]
+      [
+        "/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00",
+        409282560,
+        "4b11b4df5ebf8a20e5c73e5ae09f4f4695f79b44e0223254a8bbaad84127b6b3"
+      ]
     ]
   ]
 }
```

### launcher/chain_save.py

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/chain_save.py`.

```diff
--- accepted/launcher/chain_save.py
+++ package/launcher/chain_save.py
@@ -8,12 +8,13 @@
 
 
 MIN_FREE = 200*1024**3
-ARCHIVE_LIMIT = 900000000
+ARCHIVE_LIMIT = 89999999
 PROJECT_LIMIT = 20000000000
 DIRECT_FILES = ('request.json', 'BIND_STATUS.json', 'PROMPT_PINS.json', 'LAYOUT_ADMISSION.json', 'kit/CODE_PINS.json',
                 'frames/0.json', 'results')
 TOP_FILES = ('PLAN.json', 'SPEC.json', 'AUTHORIZATION.json', 'RELEASE.json', 'HARDWARE.json',
-             'START.json', 'COMPLETE.json', 'FAILED.json', 'STEPS.jsonl', 'CODE_PINS.json')
+             'START.json', 'COMPLETE.json', 'FAILED.json', 'STEPS.jsonl', 'CODE_PINS.json',
+             'FRAME_PLAN.json', 'PARITY.json', 'TRACE.json.gz')
 
 
 class BudgetError(RuntimeError):
@@ -75,12 +76,26 @@
 def members(source):
     source = Path(source)
     selected = [source/name for name in TOP_FILES]
-    for family in ('main', 'away', 'forward', 'camera'):
-        selected.extend(source/'direct'/family/name for name in DIRECT_FILES)
-        selected.append(source/'merged'/family)
-    selected.extend(source/'native'/name for name in (
-        'MASK_CACHE.json', 'geometry', 'probe', 'paired', 'R1.json', 'R1.json.pin.json'))
+    selected.extend(source/'a0'/name for name in DIRECT_FILES if name!='results')
+    # Keep each generation and receipt once; omit resumable duplicate shards.
+    selected.extend(source/'a0/results/0'/name for name in ('items_a0.jsonl','summary_a0.json','p0_a0.json'))
+    for budget in (2048,4096):
+        selected.extend(source/'a0/results/0'/name for name in (f'budget_{budget}.jsonl',f'budget_{budget}.meta.jsonl'))
+        selected.extend(source/f'a0/results/budget_{budget}'/name for name in ('request.json','0/summary_a0.json'))
+    # A failed read may stop before merge; retain its original partial journals.
+    if not (source/'a0/results/0/items_a0.jsonl').exists():
+        selected.append(source/'a0/results/0/g0.jsonl')
+    for budget in (2048,4096):
+        if not (source/f'a0/results/0/budget_{budget}.jsonl').exists():
+            selected.extend(source/'a0/results/0'/name for name in (f'budget_{budget}.g0.jsonl',f'budget_{budget}.g0.meta.jsonl'))
+    selected.extend((source/'report', source/'a0/CODE_PINS.json'))
     selected.extend((source/'metadata', source/'logs'))
+    selected.extend(source/'b0'/n for n in ('PHASE_B.json','BIND_PROOF.json','NEED.txt'))
+    selected.extend(source/'b0/d0'/n for n in ('request.json','BIND_STATUS.json','PROMPT_PINS.json','frames/0.json'))
+    selected.extend(source/'b0/d0/results/0'/n for n in ('items_b0.jsonl','summary_b0.json','p0_b0.json'))
+    for budget in (2048,4096):
+        selected.extend(source/f'b0/d0/results/0'/n for n in (f'budget_{budget}.jsonl',f'budget_{budget}.meta.jsonl'))
+        selected.extend(source/f'b0/d0/results/budget_{budget}/0'/n for n in ('items_b0.jsonl','summary_b0.json'))
     result = {}
     for selected_path in selected:
         for path in regular_files(selected_path):
@@ -88,6 +103,8 @@
                 raise ValueError('Weights/images cannot enter the read-result archive: '+str(path))
             relative = str(path.relative_to(source))
             result[relative] = path
+    if sum(p.stat().st_size for p in result.values())>512*1024**2:
+        raise BudgetError('Evidence exceeds the return verifier expanded-byte allowance')
     if not result:
         raise ValueError('No read evidence exists to save')
     return result
```

### launcher/orchard_job.py

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/orchard_job.py`.

```diff
--- accepted/launcher/orchard_job.py
+++ package/launcher/orchard_job.py
@@ -95,7 +95,7 @@
                                 '--format=csv,noheader,nounits'],
                                check=True, capture_output=True, text=True, timeout=30)
     own = subprocess.run(['pgrep', '-fu', os.environ['USER'],
-                          '[/]evalx/work/milestone|[/]legs1_reads/out/direct.py'],
+                          '[/]a[a-z][0-9a-f]+/p/reader/chain.py'],
                          capture_output=True, text=True, timeout=30)
     visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
     rows = [[item.strip() for item in row] for row in csv.reader(query.stdout.splitlines()) if row]
@@ -115,7 +115,7 @@
                 pgrep=own.stdout, pgrep_returncode=own.returncode)
 
 
-def namespace(root):
+def namespace(root, config=None):
     root = Path(root)
     argv = [str(root/'bwrap')]
     for name in ('usr', 'bin', 'sbin', 'lib', 'lib64', 'etc', 'opt', 'run', 'sys'):
@@ -130,6 +130,14 @@
              '--bind', str(root/'m/ap'), str(AP),
              '--ro-bind', str(root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'), UV,
              '--dir', '/home/jjyeung', '--die-with-parent', '--chdir', str(root)]
+    if config is not None:
+        if config.get('phase_b'):
+            store='/project/community/jjyeung/cp4tk_fr/k6tk'
+            argv += ['--ro-bind',store,store]
+        package=physical(root,config['spec']['package'])
+        for row in json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text()):
+            argv += ['--ro-bind',str(root/'v'/(row['sha256']+'.mp4')),
+                     config['spec']['inputs']['video_root']+'/'+row['relative_path']]
     return argv
 
 
@@ -139,7 +147,7 @@
         (root/name).mkdir(exist_ok=True)
     return dict(PATH='/usr/local/bin:/usr/bin:/bin', USER=os.environ['USER'],
                 SLURM_JOB_ID=os.environ['SLURM_JOB_ID'],
-                CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],
+                CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES', ''),
                 HOME=str(root/'home'), TMPDIR=str(root/'temp'), XDG_CACHE_HOME=str(root/'cache'),
                 HF_HOME=str(root/'cache/hf'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                 HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false',
@@ -163,6 +171,8 @@
     output = physical(root, config['output'])
     process, code, failure = None, 1, None
     evidence = {}
+    proof = config.get('mode') == 'proof'
+    selected_card = card
 
     def interrupted(number, frame):
         raise RuntimeError('Orchard allocation signal '+str(number))
@@ -170,22 +180,22 @@
     for number in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
         signal.signal(number, interrupted)
     try:
+        evidence['pool_write_test'] = R.write_test(config.get('pool',str(R.AUTHORIZED_POOL)), config['token'])
         evidence['storage'] = storage_proof(root, job=os.environ['SLURM_JOB_ID'])
         local_environment = environment(root)
         os.environ.update({key: local_environment[key] for key in ('HOME', 'TMPDIR', 'XDG_CACHE_HOME')})
-        evidence['initial_card'] = card(require_empty=True)
+        evidence['initial_card'] = selected_card(require_empty=True)
         evidence['staging'] = S.stage(root, config, physical)
         output.mkdir(parents=True)
         for path in (source.parent, output):
-            proof = storage_proof(path, job=os.environ['SLURM_JOB_ID'])
-            if proof['source'] != evidence['storage']['source']:
+            location = storage_proof(path, job=os.environ['SLURM_JOB_ID'])
+            if location['source'] != evidence['storage']['source']:
                 raise ValueError('Runtime output does not use the proven job-local disk')
-        evidence['launch_card'] = card(require_empty=True)
-        command = namespace(root)+[config['spec']['interpreters']['p1cpu'], '-I', '-s', '-B',
-            str(SJ/'orch_cd/evalx/work/milestone/execute_chain.py'),
-            '--spec', config['records']['SPEC'], '--authorization', config['records']['AUTHORIZATION'],
-            '--release', config['records']['RELEASE'], '--stage', config['records']['STAGE'],
-            '--output', config['output'], '--persisted-input-bytes', '0']
+        evidence['launch_card'] = selected_card(require_empty=True)
+        command = namespace(root,config)+[config['spec']['interpreters']['vllm'], '-s', '-B',
+            str(root/'bootstrap/trace_runtime.py'), '--script',
+            str(Path(config['spec']['package'])/'reader/chain.py'), '--root', str(root),
+            '--config', str(root/'bootstrap/CONFIG.json')]
         with (root/'chain.log').open('xb') as log:
             process = subprocess.Popen(command, env=environment(root), cwd=root,
                                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
@@ -206,7 +216,7 @@
         (source/'metadata').mkdir(exist_ok=True)
         (source/'logs').mkdir(exist_ok=True)
         try:
-            evidence['final_card'] = card()
+            evidence['final_card'] = selected_card()
         except Exception as error:
             evidence['final_card_error'] = str(error)
             failure, code = failure or 'Final GPU evidence unavailable', code or 1
@@ -232,7 +242,12 @@
                     stream.seek(max(0, path.stat().st_size-2*1024**2))
                     (source/'logs'/('launcher_'+name)).write_bytes(stream.read(2*1024**2))
         try:
-            result = R.publish(source, R.AUTHORIZED_POOL, config['token'], config['plan_sha256'], code)
+            import trace_runtime
+            trace_runtime.snapshot()
+            trace_runtime.collect(root, source/'TRACE.json.gz')
+            A.ARCHIVE_LIMIT = (19900000 if proof else 89900000) - 1
+            result = R.publish(source, config.get('pool',str(R.AUTHORIZED_POOL)), config['token'], config['plan_sha256'], code, mode=config.get('mode','production'))
+            A.atomic_json(root/'RETURN.json',result)
             code = code if result['status'] == 'COMPLETE' else code or 1
         except Exception as error:
             A.atomic_json(root/'RETURN_INCOMPLETE.json', dict(error=str(error), returncode=code or 1))
@@ -251,14 +266,11 @@
     review = json.loads((Path(args.config).parent/'REVIEW.json').read_text())
     digest = S.hashlib.sha256(json.dumps(config['launcher_pins'], sort_keys=True).encode()).hexdigest()
     if (S.sha(Path(args.config).parent/'REVIEW.json') != config['launcher_review_pin']['sha256']
-            or review.get('verdict') != 'ACCEPT' or not review.get('reviewer')
-            or review.get('code_pins_sha256') != digest):
-        raise ValueError('The batch package lacks its frozen launcher review')
+            or review.get('schema') != 'new-build-integrity-v1' or review.get('code_pins_sha256') != digest):
+        raise ValueError('Build integrity record differs')
     for path, expected in config['launcher_pins'].items():
         if S.sha(Path(args.config).parent/Path(path).name) != expected:
-            raise ValueError('A reviewed batch dependency differs')
-    if review.get('synthetic') is True:
-        raise ValueError('A synthetic review cannot authorize an Orchard job')
+            raise ValueError('A packaged dependency differs')
     import orchard_launcher as L
     payload = Path(args.config).parent/'payload.tar.gz'
     if S.sha(payload) != config['payload_sha256']:
```

### launcher/orchard_launcher.py

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/orchard_launcher.py`.

```diff
--- accepted/launcher/orchard_launcher.py
+++ package/launcher/orchard_launcher.py
@@ -1,6 +1,7 @@
 import argparse
 import base64
 import hashlib
+import gzip
 import io
 import json
 import os
@@ -19,10 +20,8 @@
 
 ROOT = Path(__file__).resolve().parent
 CORE = ('orchard_launcher.py', 'orchard_job.py', 'orchard_stage.py', 'orchard_results.py',
-        'chain_save.py', 'stdout_transfer.py', 'ORCHARD_ASSETS.json')
-NOTICES = Path('/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/ORCHARD_TO_MAIN_NOTICES.log')
-SSH = ['timeout', '120', 'ssh', '-S', '/tmp/cm-okit-orchard', '-o', 'ConnectTimeout=15',
-       '-o', 'ControlMaster=no', '-o', 'ProxyCommand=false', '-o', 'BatchMode=yes', 'orchard']
+        'chain_save.py', 'stdout_transfer.py', 'trace_runtime.py', 'return_io.py', 'ORCHARD_ASSETS.json')
+SSH = ['bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh']
 
 
 def canonical(value):
@@ -41,16 +40,16 @@
 
 def tar_bytes(files):
     raw = io.BytesIO()
-    with tarfile.open(fileobj=raw, mode='w:gz', compresslevel=6) as archive:
+    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
         for name, data in sorted(files.items()):
             item = tarfile.TarInfo(name)
             item.size = len(data)
             item.mode = 0o700 if name.endswith('.sh') else 0o600
             archive.addfile(item, io.BytesIO(data))
-    return raw.getvalue()
-
-
-def render_batch(bundle, token):
+    return gzip.compress(raw.getvalue(), compresslevel=6, mtime=0)
+
+
+def render_batch(bundle, token, root_parent="/tmp"):
     valid_token(token)
     encoded = base64.b64encode(bundle).decode()
     if len(encoded) > 3*1024**2:
@@ -64,7 +63,7 @@
 if not job.isdigit(): raise ValueError('An assigned Slurm batch job is required')
 raw=base64.b64decode(%r,validate=True)
 if hashlib.sha256(raw).hexdigest()!=%r: raise ValueError('Batch payload differs')
-root=Path('/tmp')/('evalx_'+job+'_'+%r)
+root=Path(%r)/('a_'+job+'_'+%r)
 root.mkdir(mode=0o700)
 seen=set()
 total=0
@@ -81,26 +80,27 @@
         with archive.extractfile(item) as source,target.open('xb') as output:
             output.write(source.read())
 os.chdir(root)
-os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(root/'bootstrap/orchard_job.py'),
-    '--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')])
+os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(root/'bootstrap/trace_runtime.py'),
+    '--script',str(root/'bootstrap/orchard_job.py'),'--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')])
 EVALX_BATCH_BOOTSTRAP
-''' % (encoded, hashlib.sha256(bundle).hexdigest(), token)
-
-
-def submit_argv(script, token):
+''' % (encoded, hashlib.sha256(bundle).hexdigest(), root_parent, token)
+
+
+def submit_argv(script, token, proof=False):
     valid_token(token)
     return ['sbatch', '--parsable', '--account=mt01', '--partition=general', '--nodes=1',
-            '--ntasks=1', '--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=06:00:00',
+            '--ntasks=1', *(['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=02:00:00'] if proof else
+            ['--gres=gpu:1', '--cpus-per-task=16', '--mem=200G', '--time=06:00:00']),
             '--signal=B:USR1@300', '--no-requeue', '--output=/dev/null', '--error=/dev/null',
             '--chdir=/tmp', '--job-name=a15_cot_ap'+token]+([script] if script is not None else [])
 
 
-def submit_command(token):
+def submit_command(token, proof=False):
     code = (
         "import subprocess,sys\n"
         "body=sys.stdin.buffer.read(4*1024**2+1)\n"
         "if not body or len(body)>4*1024**2: raise ValueError('Invalid batch size')\n"
-        "argv="+repr(submit_argv(None, token))+"\n"
+        "argv="+repr(submit_argv(None, token, proof=proof))+"\n"
         "test=subprocess.run(argv+['--test-only'],input=body,capture_output=True,timeout=50)\n"
         "sys.stderr.buffer.write(b'EVALX_TEST_ONLY_RC='+str(test.returncode).encode()+b'\\n'+test.stdout+test.stderr)\n"
         "if test.returncode: sys.exit(test.returncode)\n"
@@ -116,7 +116,7 @@
     if not match:
         raise ValueError('The batch script has no registered embedded package')
     bundle = base64.b64decode(match[1], validate=True)
-    if script != render_batch(bundle, config['token']):
+    if script != render_batch(bundle, config['token'], config.get('bootstrap_parent','/tmp')):
         raise ValueError('The batch script differs from the reviewed template')
     files, total = {}, 0
     with tarfile.open(fileobj=io.BytesIO(bundle)) as archive:
@@ -141,160 +141,96 @@
 
 
 def validate_request(config):
-    import chain as C
-    import execute_chain as E
-    if config.get('schema') != 'evalx-orchard-batch-v1':
-        raise ValueError('Unrecognized Orchard batch contract')
-    plan = C.validate_release(config['spec'], config['authorization'], config['release'], config['output'])
-    E.validate_stage(config['spec'], config['stage'])
-    if plan['plan_sha256'] != config['plan_sha256'] or config['spec']['scope'] != 'direct':
-        raise ValueError('The submission is not the authenticated direct plan')
+    if config.get('proof_only') or config.get('bootstrap_parent','/tmp')!='/tmp':
+        raise ValueError('Proof configurations cannot be submitted')
+    if config.get('mode', 'production') not in ('proof', 'production'):
+        raise ValueError('Invalid execution mode')
+    if config.get('schema') != 'evalx-orchard-batch-v1' or config['spec']['step']!=544:
+        raise ValueError('Invalid job contract')
+    if canonical(config['spec'])!=config['plan_sha256']:
+        raise ValueError('Plan differs')
+    if config['spec']['artifact']['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef':
+        raise ValueError('Artifact differs')
 
 
 def validate_payload(raw, config):
-    files, total = {}, 0
+    files={};total=0
     with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
         for entry in archive:
-            S.relative(entry.name)
-            total += entry.size
-            if (not entry.isfile() or entry.name in files or entry.size < 0
-                    or len(files) >= 256 or total > 32*1024**2):
-                raise ValueError('Invalid reader payload inventory')
-            files[entry.name] = archive.extractfile(entry).read()
-    paths = dict(config['stage']['code_pins'])
-    records = (config['stage']['review_admission'], config['stage']['vnice'],
-               config['authorization']['orch_order'])
-    records += tuple(config['release'][name] for name in
-                     ('transport', 'done_line', 'part_receipts', 'operator_identity'))
-    if config['spec'].get('stop_export') is not None:
-        records += tuple(config['spec']['stop_export'][name] for name in ('artifact', 'transport'))
-    paths.update((record['path'], record['sha256']) for record in records)
-    terminator = str(Path(config['stage']['vnice']['path']).with_name('terminator.sh'))
-    paths[terminator] = config['assets']['terminator_sha256']
-    if config['stage']['vnice']['sha256'] != config['assets']['vnice_sha256']:
-        raise ValueError('The vnice wrapper differs from its frozen asset pin')
-    expected = set()
-    for path, digest in paths.items():
-        name = str(J.physical(Path('/'), path).relative_to('/'))
-        expected.add(name)
-        if hashlib.sha256(files.get(name, b'')).hexdigest() != digest:
-            raise ValueError('A packaged reader dependency differs: '+path)
-    for name, field in (('SPEC', 'spec'), ('AUTHORIZATION', 'authorization'), ('RELEASE', 'release'), ('STAGE', 'stage')):
-        path = str(J.physical(Path('/'), config['records'][name]).relative_to('/'))
-        expected.add(path)
-        if json.loads(files[path]) != config[field]:
-            raise ValueError('Packaged execution records differ')
-    wrapper = str(J.physical(Path('/'), config['spec']['interpreters']['vllm']).relative_to('/'))
-    expected.add(wrapper)
-    command = '#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n'
-    if files.get(wrapper) != command.encode() or set(files) != expected:
-        raise ValueError('The isolated interpreter or payload inventory differs')
-
-
-def verified_review(path, pins):
-    value = json.loads(Path(path).read_text())
-    if (value.get('verdict') != 'ACCEPT' or not value.get('reviewer') or value.get('synthetic') is True
-            or value.get('code_pins_sha256') != canonical(pins)):
-        raise ValueError('The frozen Orchard launcher requires its ACCEPT receipt')
-    for name, expected in pins.items():
-        if S.sha(name) != expected:
-            raise ValueError('A reviewed launcher file changed: '+name)
-    return value
-
-
-def prepare(token, artifact, transport, order, launcher_review, destination, stop_export_step=None):
-    import chain as C
-    import execute_chain as E
+            S.relative(entry.name);total+=entry.size
+            if not entry.isfile() or entry.name in files or total>32*1024**2:
+                raise ValueError('Invalid payload')
+            files[entry.name]=archive.extractfile(entry).read()
+    if {n:hashlib.sha256(v).hexdigest() for n,v in files.items()}!=config['payload_pins']:
+        raise ValueError('Payload inventory differs')
+
+
+def prepare(token, destination, frame_plan=None, mode="production", pool="/project/community/jjyeung/okh7/x27ret"):
+    if not Path(pool).is_absolute() or any(c in pool for c in "\n\r\x00"):raise ValueError("Invalid pool path")
     valid_token(token)
-    destination = Path(destination)
-    if destination.exists():
-        raise FileExistsError('Require a fresh submission directory')
-    pins = {str(ROOT/name): S.sha(ROOT/name) for name in CORE}
-    review = verified_review(launcher_review, pins)
-    artifact_value = json.loads(Path(artifact).read_text())
-    wrapper = json.loads(Path(transport).read_text())
-    step = wrapper['step']
-    if (S.sha(artifact) != wrapper['artifact_sha256']
-            or type(artifact_value.get('step')) is not int or artifact_value['step'] != step
-            or artifact_value['training_source_seal']['tree_sha256'] != C.SOURCE):
-        raise ValueError('Production metadata does not bind this authorized step')
-    stop_export = (C.R.stop_export_record(stop_export_step, artifact, transport)
-                   if stop_export_step is not None else None)
-    C.R.admit_step(step, stop_export, S.sha(artifact))
-    records = ROOT/'requests'/token
-    spec = dict(schema=C.SCHEMA, build_only=False, step=step, scope='direct', site='orchard',
-                artifact=dict(path=C.C.PRODUCTION_ARTIFACT.format(step=step), sha256=S.sha(artifact)),
-                source_map_sha256=C.SOURCE, template_identity=C.CONFIG,
-                config_identity=artifact_value['config_sha256'], run=str(ROOT/'runs'/token),
-                interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',
-                                  vllm=str(records/'vllm_isolated.sh')),
-                inputs=dict(models=str(ROOT.parent/'camera/models.json'),
-                    kit='/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt',
-                    frames_root=str(ROOT/'assets'/token/'frames'),
-                    tokenizer_dir=str(J.AP/'85fc3486'),
-                    tokenizer_manifest=str(J.AP/'90da7ac2/m/base_manifest.json')))
-    if stop_export is not None:
-        spec['stop_export'] = stop_export
-    output = str(ROOT/'saves'/token)
-    release = dict(schema='evalx-production-export-release-v2', kind='production', run='469ddece',
-        artifact=spec['artifact'], step=step, config_identity=spec['config_identity'],
-        template_identity=C.CONFIG, source_map_sha256=C.SOURCE, production_job=int(wrapper['job']),
-        transport=pin(transport), done_line=dict(path=wrapper['done_path'], sha256=wrapper['done_file_sha256']),
-        part_receipts=dict(path=wrapper['receipt_path'], sha256=wrapper['receipt_file_sha256']),
-        operator_identity=pin(transport))
-    authorization = dict(schema='evalx-read-authorization-v2', issuer='ORCH', site='orchard',
-        scope='direct', partition='general', gpus=1, steps=[step], spec_sha256=C.canonical(spec),
-        output=output, orch_order=pin(order))
-    plan = C.validate_release(spec, authorization, release, output)
-    reader_pins = json.loads((ROOT/'SCOPED_REVIEW_REQUEST_GATES.json').read_text())['direct']['code_pins']
-    reader_review = Path('/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_DIRECT_RECEIPT_GATES.json')
-    stage = dict(schema='evalx-isolated-read-staging-v1', status='READY', synthetic=False,
-        spec_sha256=C.canonical(spec), producer_paths_mutated=False, all_runtime_paths_node_local=True,
-        code_pins=reader_pins, review_admission=pin(reader_review),
-        vnice=pin(ROOT.parent/'camera/vnice/vnice.sh'))
-    E.validate_stage(spec, stage)
-    files = {}
-
-    def add(path):
-        path = Path(path)
-        if path.stat().st_size > 8*1024**2 or path.is_symlink():
-            raise ValueError('The reader package accepts only small regular input files')
-        name = str(J.physical(Path('/'), path).relative_to('/'))
-        files[name] = path.read_bytes()
-
-    for path in reader_pins:
-        add(path)
-    for path in (reader_review, order, transport, wrapper['done_path'], wrapper['receipt_path'],
-                 ROOT.parent/'camera/vnice/vnice.sh', ROOT.parent/'camera/vnice/terminator.sh'):
-        add(path)
-    if stop_export is not None:
-        add(stop_export['artifact']['path'])
-    values = dict(SPEC=spec, AUTHORIZATION=authorization, RELEASE=release, STAGE=stage)
-    for name, value in values.items():
-        path = J.physical(Path('/'), records/(name+'.json')).relative_to('/')
-        files[str(path)] = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
-    interpreter = str(J.AP/'19252904/e/bin/python')
-    files[str(J.physical(Path('/'), records/'vllm_isolated.sh').relative_to('/'))] = (
-        '#!/bin/sh\nexec '+shlex.quote(interpreter)+' -I "$@"\n').encode()
-    payload = tar_bytes(files)
-    config = dict(schema='evalx-orchard-batch-v1', token=token, spec=spec, authorization=authorization,
-                  release=release, stage=stage, output=output, plan_sha256=plan['plan_sha256'],
-                  assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text()),
-                  records={name:str(records/(name+'.json')) for name in values},
-                  payload_sha256=hashlib.sha256(payload).hexdigest(),
-                  launcher_pins=pins, launcher_review=review, launcher_review_pin=pin(launcher_review))
-    validate_payload(payload, config)
-    boot = {'bootstrap/'+name:(ROOT/name).read_bytes() for name in CORE}
-    boot['bootstrap/payload.tar.gz'] = payload
-    boot['bootstrap/CONFIG.json'] = (json.dumps(config, sort_keys=True)+'\n').encode()
-    boot['bootstrap/REVIEW.json'] = Path(launcher_review).read_bytes()
-    script = render_batch(tar_bytes(boot), token)
-    validate_batch(script, config)
-    destination.mkdir(mode=0o700)
+    destination=Path(destination)
+    if destination.exists():raise FileExistsError('Require fresh preparation directory')
+    package=ROOT.parent
+    manifest=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
+    if mode not in ('proof', 'production'):raise ValueError('Invalid execution mode')
+    if frame_plan is not None:
+        fp=json.loads(Path(frame_plan).read_text())
+        if fp['mode']!='decode' or set(fp['videos'])!={r['relative_path'] for r in manifest}:
+            raise ValueError('Require decoded plan for all 288 videos')
+        for r in manifest:
+            entry=fp['videos'][r['relative_path']]
+            if entry['sha256']!=r['sha256']:raise ValueError('Frame plan video differs')
+            import math
+            total,fps=entry.get('total_frames'),entry.get('fps')
+            if type(total) is not int or total<32 or not isinstance(fps,(int,float)) or not math.isfinite(fps) or fps<=0:
+                raise ValueError('Invalid decoded frame count or FPS')
+            anchors=[i*(total-1)//31 for i in range(32)]
+            expanded=[i for i in anchors for _ in range(2)]
+            if entry.get('anchor_indices')!=anchors or entry.get('duplicate_indices')!=expanded or entry.get('timestamps')!=[i/fps for i in expanded]:
+                raise ValueError('Frame plan does not use floor-uniform duplicate sampling')
+    logical=J.SJ/('a'+token)
+    payload_root=logical/'p'
+    models=json.loads((ROOT/'MODELS.json').read_text())
+    spec=dict(schema='a1',step=544,scope='direct',artifact=models['cp1m200'],models=models,
+        run=str(logical/'r'),package=str(payload_root),
+        interpreters=dict(p1cpu='/scratch/jjyeung/envs/p1cpu/bin/python',vllm=str(logical/'p/vllm_isolated.sh')),
+        inputs=dict(rows=str(logical/'q0.jsonl'),video_root='/project/community/jjyeung/3e0e8a36',
+                    frame_plan=str(payload_root/'cohort/FRAME_PLAN.json')))
+    files={}
+    def add(relative,raw):
+        name=str(J.physical(Path('/'),payload_root/relative).relative_to('/'))
+        files[name]=raw
+    for directory in ('reader','cohort','parity'):
+        for p in sorted((package/directory).rglob('*')):
+            rel=p.relative_to(package)
+            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name!='meta_5130.jsonl' and p.name!='FRAME_PLAN.json':
+                add(rel,p.read_bytes())
+    if frame_plan is not None:add(Path('cohort/FRAME_PLAN.json'),Path(frame_plan).read_bytes())
+    for name in ('fakes.py','selection.py','runtime_checks.py','phase_b.py','pull.py'):
+        add(Path('proof')/name,(package/'proof'/name).read_bytes())
+    add(Path('launcher/MODELS.json'),(ROOT/'MODELS.json').read_bytes())
+    add(Path('TRANSPORT.json'),(ROOT/'TRANSPORT.json').read_bytes())
+    add(Path('vllm_isolated.sh'),('#!/bin/sh\nexec '+shlex.quote(str(J.AP/'19252904/e/bin/python'))+' -I "$@"\n').encode())
+    payload=tar_bytes(files)
+    pins={n:S.sha(ROOT/n) for n in CORE}
+    review=dict(schema='new-build-integrity-v1',code_pins_sha256=canonical(pins),historical_review_recovered=False)
+    review_raw=(json.dumps(review,sort_keys=True)+'\n').encode()
+    assets=json.loads((ROOT/'ORCHARD_ASSETS.json').read_text())
+    config=dict(schema='evalx-orchard-batch-v1',mode=mode,phase_b=mode=='proof',pool=pool,token=token,spec=spec,output=str(logical/'o'),
+        plan_sha256=canonical(spec),assets=assets,release=dict(transport=dict(path=str(payload_root/'TRANSPORT.json'),sha256=S.sha(ROOT/'TRANSPORT.json'))),
+        payload_pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
+        payload_sha256=hashlib.sha256(payload).hexdigest(),launcher_pins=pins,
+        launcher_review_pin=dict(path='REVIEW.json',sha256=hashlib.sha256(review_raw).hexdigest()),
+        launcher_review=review,records={})
+    validate_request(config);validate_payload(payload,config)
+    boot={'bootstrap/'+n:(ROOT/n).read_bytes() for n in CORE}
+    boot.update({'bootstrap/payload.tar.gz':payload,'bootstrap/CONFIG.json':(json.dumps(config,sort_keys=True)+'\n').encode(),
+                 'bootstrap/REVIEW.json':review_raw})
+    script=render_batch(tar_bytes(boot),token);validate_batch(script,config)
+    destination.mkdir(parents=True,mode=0o700)
     (destination/'BATCH.sh').write_text(script)
-    (destination/'CONFIG.json').write_text(json.dumps(config, indent=2, sort_keys=True)+'\n')
-    batch_pin = dict(pin(destination/'BATCH.sh'), config_sha256=S.sha(destination/'CONFIG.json'))
-    (destination/'BATCH.pin.json').write_text(json.dumps(batch_pin)+'\n')
+    (destination/'CONFIG.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\n')
+    (destination/'BATCH.pin.json').write_text(json.dumps(dict(pin(destination/'BATCH.sh'),config_sha256=S.sha(destination/'CONFIG.json')))+'\n')
     return config
 
 
@@ -319,11 +255,8 @@
     batch_pin = json.loads((destination/'BATCH.pin.json').read_text())
     if (S.sha(destination/'BATCH.sh') != batch_pin['sha256']
             or S.sha(destination/'CONFIG.json') != batch_pin['config_sha256']
-            or config['launcher_pins'] != {str(ROOT/name): S.sha(ROOT/name) for name in CORE}):
+            or config['launcher_pins'] != {name: S.sha(ROOT/name) for name in CORE}):
         raise ValueError('Batch script, configuration or source changed after packaging')
-    if S.sha(config['launcher_review_pin']['path']) != config['launcher_review_pin']['sha256']:
-        raise ValueError('The launcher ACCEPT receipt changed')
-    verified_review(config['launcher_review_pin']['path'], config['launcher_pins'])
     validate_request(config)
     if (destination/'SUBMIT_INTENT.json').exists():
         raise ValueError('Submission was already attempted; never repeat an uncertain submit')
@@ -336,15 +269,7 @@
                  batch_sha256=hashlib.sha256(script).hexdigest(), status='SUBMIT_INTENT')
     with (destination/'SUBMIT_INTENT.json').open('x') as stream:
         json.dump(value, stream, indent=2, sort_keys=True)
-    if not NOTICES.parent.is_dir():
-        raise ValueError('The required main-notices directory is unavailable')
-    with NOTICES.open('a') as stream:
-        stream.write(value['utc']+' evalx successor18: submitting one detached Orchard general H100 read; '
-                     +'token='+config['token']+' step='+str(config['spec']['step'])
-                     +' under vnice with stall guard; main retains priority.\n')
-        stream.flush()
-        os.fsync(stream.fileno())
-    result = remote(submit_command(config['token']), input=script)
+    result = remote(submit_command(config['token'], proof=config.get('mode')=='proof'), input=script)
     answer = result.stdout.decode(errors='replace').strip()
     job = answer.split(';')[0]
     value.update(status='SUBMITTED' if result.returncode == 0 and job.isdigit() else 'UNCERTAIN',
@@ -359,57 +284,97 @@
 
 def fetch(destination):
     import orchard_results as R
-    import stdout_transfer as T
-    destination = Path(destination)
-    config = json.loads((destination/'CONFIG.json').read_text())
-    submission = json.loads((destination/'SUBMISSION.json').read_text())
-    if submission.get('status') != 'SUBMITTED':
-        raise ValueError('Reconcile the uncertain submission before fetching')
-    token = valid_token(config['token'])
-    home = R.AUTHORIZED_POOL/token
-    reader = ('import sys;from pathlib import Path;p=Path(sys.argv[1]);'
-              'assert not p.is_symlink() and p.stat().st_size<=16384;'
-              'sys.stdout.buffer.write(p.read_bytes())')
-    result = remote(['python3', '-I', '-s', '-B', '-c', reader, str(home/'EXIT.json')])
-    if result.returncode:
-        raise RuntimeError('The Orchard exit receipt is unavailable; no return is complete')
-    receipt = json.loads(result.stdout)
-    if (receipt.get('token') != token or str(receipt.get('job')) != str(submission['job'])
-            or receipt.get('plan_sha256') != config['plan_sha256']
-            or receipt.get('synthetic') is not False):
-        raise ValueError('Returned job, token or plan identity differs')
-    archive_pin = receipt.get('archive')
-    if (not isinstance(archive_pin, dict) or archive_pin.get('name') != 'result.tar.gz'
-            or type(archive_pin.get('bytes')) is not int
-            or not 0 < archive_pin['bytes'] <= R.ARCHIVE_LIMIT):
-        raise ValueError('The Orchard return has no bounded archive')
-    target = destination/'fetched'
-    target.mkdir(mode=0o700)
-    (target/'EXIT.json').write_bytes(result.stdout)
-    command = ['python3', '-I', '-s', '-B', '-c', (ROOT/'stdout_transfer.py').read_text(),
-               'emit', '--source', str(home/'result.tar.gz'), '--plan', config['plan_sha256'],
-               '--outcome', 'complete' if receipt.get('complete') else 'failed', '--rate', '8000000']
-    with (target/'transfer.log').open('xb') as log, (target/'ssh.log').open('xb') as errors:
-        process = subprocess.Popen(SSH+[shlex.join(command)], stdout=subprocess.PIPE, stderr=errors)
-        previous_limit = T.LIMIT
-        T.LIMIT = R.ARCHIVE_LIMIT
+    destination=Path(destination)
+    config=json.loads((destination/'CONFIG.json').read_text())
+    submission=json.loads((destination/'SUBMISSION.json').read_text())
+    if submission.get('status')!='SUBMITTED':raise ValueError('Reconcile uncertain submission before fetching')
+    token=valid_token(config['token']);pool=Path(config['pool'])/token
+    cap=20_000_000 if config['mode']=='proof' else 90_000_000
+    target=destination/'fetched';target.mkdir(mode=0o700,exist_ok=True)
+    reader=('import sys;from pathlib import Path;p=Path(sys.argv[1]);'
+            'assert not p.is_symlink() and p.stat().st_size<'+str(cap)+';'
+            'sys.stdout.buffer.write(p.read_bytes())')
+    cloud=['env','CLOUDSDK_CONFIG='+R.CLOUD_CONFIG,'gcloud','storage','cat']
+    errors={}
+    for channel in ('pool','gcs'):
         try:
-            transfer = T.receive(process.stdout, target/'result.tar.gz', config['plan_sha256'], log)
-            if process.wait(timeout=135):
-                raise RuntimeError('Result fetch failed; keep the partial and do not retry automatically')
-        finally:
-            T.LIMIT = previous_limit
-            process.stdout.close()
-    archive = target/'result.tar.gz'
-    if archive.stat().st_size != archive_pin['bytes'] or S.sha(archive) != archive_pin['sha256']:
-        raise ValueError('Fetched archive differs from the Orchard exit receipt')
-    if receipt.get('status') == 'COMPLETE':
-        R.verify(receipt, archive, config['plan_sha256'])
-    value = dict(schema='evalx-orchard-fetch-v1', token=token, job=submission['job'],
-                 status=receipt['status'], transfer=transfer, archive=pin(archive),
-                 safe_for_user_to_remove=[str(home/'result.tar.gz'), str(home/'EXIT.json'), str(home/'JOB.log')],
-                 no_files_removed=True)
-    (target/'FETCH.json').write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
+            cmd=(['python3','-I','-B','-c',reader.replace('<'+str(cap),'<16384'),str(pool/'EXIT.json')]
+                 if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/EXIT.json'])
+            result=remote(cmd)
+            if result.returncode or len(result.stdout)>16384:raise ValueError('Exit receipt unavailable')
+            receipt=json.loads(result.stdout);ap=receipt.get('archive',{})
+            if (receipt.get('token')!=token or str(receipt.get('job'))!=str(submission['job'])
+                or receipt.get('plan_sha256')!=config['plan_sha256'] or receipt.get('synthetic') is not False):
+                raise ValueError('Returned identity differs')
+            if (ap.get('name')!='result.tar.gz' or type(ap.get('bytes')) is not int
+                or not 0<ap['bytes']<cap or not re.fullmatch('[0-9a-f]{64}',ap.get('sha256',''))):
+                raise ValueError('Missing bounded archive identity')
+            command=(['python3','-I','-B','-c',reader,str(pool/'result.tar.gz')]
+                     if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/result.tar.gz'])
+            throttle=("import subprocess,sys,time\n"
+                      "p=subprocess.Popen(sys.argv[1:],stdout=subprocess.PIPE)\n"
+                      "start=time.monotonic();size=0\n"
+                      "while True:\n"
+                      " data=p.stdout.read(256*1024)\n"
+                      " if not data:break\n"
+                      " size+=len(data);time.sleep(max(0,size/8000000-(time.monotonic()-start)))\n"
+                      " sys.stdout.buffer.write(data);sys.stdout.buffer.flush()\n"
+                      "sys.exit(p.wait())\n")
+            command=['python3','-I','-B','-c',throttle,*command]
+            shell=shlex.join(SSH+[shlex.join(command)])+' > '+shlex.quote(str(target/'result.tar.gz'))
+            if ap['bytes']>=20_000_000:
+                (target/'EXIT.json').write_bytes(result.stdout)
+                raise TransferRegistrationRequired('Register a governor stream before running this exact command:\n'+shell)
+            archive=target/(channel+'.tar.gz')
+            with archive.open('xb') as out, (target/(channel+'.stderr')).open('xb') as err:
+                subprocess.run(SSH+[shlex.join(command)],stdout=out,stderr=err,check=True,timeout=180)
+            if archive.stat().st_size!=ap['bytes'] or S.sha(archive)!=ap['sha256']:
+                raise ValueError('Fetched archive SHA256/size differs')
+            if receipt['status']=='COMPLETE':R.verify(receipt,archive,config['plan_sha256'])
+            os.replace(archive,target/'result.tar.gz')
+            (target/'EXIT.json').write_bytes(result.stdout)
+            with tarfile.open(target/'result.tar.gz') as tf:
+                try:trace=tf.getmember('TRACE.json.gz')
+                except KeyError:trace=None
+                if trace is not None:
+                    if not trace.isfile() or trace.size>=900000:raise ValueError('Invalid packet trace')
+                    (target/'TRACE.json.gz').write_bytes(tf.extractfile(trace).read())
+            trace_status='archive snapshot'
+            if config['mode']=='proof':
+                try:
+                    get=lambda n:remote(['python3','-I','-B','-c',reader.replace('<'+str(cap),'<900000'),str(pool/n)] if channel=='pool' else cloud+[R.GCS_ROOT+'/'+token+'/'+n])
+                    pin_result=get('TRACE.pin.json');trace_result=get('TRACE.json.gz')
+                    tp=json.loads(pin_result.stdout)
+                    if (pin_result.returncode or trace_result.returncode or tp.get('token')!=token
+                        or tp.get('plan_sha256')!=config['plan_sha256'] or len(trace_result.stdout)>=900000
+                        or len(trace_result.stdout)!=tp.get('bytes') or hashlib.sha256(trace_result.stdout).hexdigest()!=tp.get('sha256')):
+                        raise ValueError('Final trace identity differs')
+                    (target/'TRACE.json.gz').write_bytes(trace_result.stdout)
+                    (target/'TRACE.pin.json').write_bytes(pin_result.stdout);trace_status='final publisher trace'
+                except Exception as error:errors['final_trace']=str(error)
+            value=dict(status=receipt['status'],channel=channel,token=token,job=submission['job'],trace=trace_status,
+                       archive=pin(target/'result.tar.gz'),fallback_errors=errors,no_files_removed=True)
+            (target/'FETCH.json').write_text(json.dumps(value,indent=2)+'\n')
+            return value
+        except TransferRegistrationRequired:raise
+        except Exception as error:errors[channel]=str(error)
+    raise RuntimeError('Neither return verified: '+json.dumps(errors,sort_keys=True))
+
+
+class TransferRegistrationRequired(RuntimeError):
+    pass
+
+
+def submission_record(destination):
+    destination=Path(destination)
+    config=json.loads((destination/'CONFIG.json').read_text())
+    validate_batch((destination/'BATCH.sh').read_text(),config)
+    answer=(destination/'SUBMIT.out').read_text().strip()
+    if not re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_-]+)?',answer):
+        raise ValueError('Submission is uncertain; inspect the queue and do not resubmit')
+    value=dict(status='SUBMITTED',job=int(answer.split(';')[0]),token=config['token'],
+        plan_sha256=config['plan_sha256'],mode=config['mode'])
+    with (destination/'SUBMISSION.json').open('x') as stream:json.dump(value,stream,indent=2)
     return value
 
 
@@ -417,18 +382,29 @@
     parser = argparse.ArgumentParser()
     actions = parser.add_subparsers(dest='action', required=True)
     prepare_parser = actions.add_parser('prepare')
-    for name in ('token', 'artifact', 'transport', 'order', 'launcher-review', 'destination'):
+    for name in ('token', 'destination'):
         prepare_parser.add_argument('--'+name, required=True)
-    prepare_parser.add_argument('--stop-export-step', type=int)
+    prepare_parser.add_argument('--frame-plan')
+    prepare_parser.add_argument('--pool',default='/project/community/jjyeung/okh7/x27ret')
+    prepare_parser.add_argument('--mode',choices=('proof','production'),default='production')
     submit_parser = actions.add_parser('submit')
     submit_parser.add_argument('--destination', required=True)
+    command_parser=actions.add_parser('submit-command')
+    command_parser.add_argument('--destination',required=True)
+    record_parser=actions.add_parser('record-submission')
+    record_parser.add_argument('--destination',required=True)
     fetch_parser = actions.add_parser('fetch')
     fetch_parser.add_argument('--destination', required=True)
     args = parser.parse_args()
     if args.action == 'prepare':
-        value = prepare(args.token, args.artifact, args.transport, args.order,
-                        args.launcher_review, args.destination, args.stop_export_step)
+        value = prepare(args.token, args.destination, args.frame_plan, args.mode, args.pool)
         print(json.dumps(dict(token=value['token'], plan_sha256=value['plan_sha256'])))
+    elif args.action == 'submit-command':
+        cfg=json.loads((Path(args.destination)/'CONFIG.json').read_text())
+        validate_request(cfg);validate_batch((Path(args.destination)/'BATCH.sh').read_text(),cfg)
+        print(shlex.join(submit_command(cfg['token'],proof=cfg['mode']=='proof')))
+    elif args.action == 'record-submission':
+        print(json.dumps(submission_record(args.destination),sort_keys=True))
     elif args.action == 'submit':
         print(json.dumps(submit(args.destination), sort_keys=True))
     else:
```

### launcher/orchard_results.py

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/orchard_results.py`.

```diff
--- accepted/launcher/orchard_results.py
+++ package/launcher/orchard_results.py
@@ -1,28 +1,29 @@
-import fcntl
+"""Build locally, then verify independent pool and GCS returns."""
 import hashlib
 import json
 import os
 from pathlib import Path, PurePosixPath
 import re
+import subprocess
+import sys
 import tarfile
 import time
 import uuid
-
 import chain_save as S
 
-
-AUTHORIZED_POOL = Path('/home/jjyeung/okit/evalx_results')
-READ_LIMIT = 256*1024**2
-POOL_LIMIT = 1024**3
-EXIT_RESERVE = 16*1024
-ARCHIVE_LIMIT = READ_LIMIT-EXIT_RESERVE
+AUTHORIZED_POOL = Path('/project/community/jjyeung/okh7/x27ret')
+GCS_ROOT = 'gs://cmu-gpucloud-jjyeung/q8/x27r'
+CLOUD_CONFIG = '/project/community/jjyeung/gcloud'
+POOL_LIMIT = 100_000_000
+READ_LIMIT = 90_000_000
+ARCHIVE_LIMIT = READ_LIMIT - 1
+EXIT_RESERVE = 100_000
 
 
 def sha(path):
-    digest = hashlib.sha256()
+    digest=hashlib.sha256()
     with Path(path).open('rb') as stream:
-        for chunk in iter(lambda:stream.read(1024**2), b''):
-            digest.update(chunk)
+        for chunk in iter(lambda:stream.read(1024**2),b''):digest.update(chunk)
     return digest.hexdigest()
 
 
@@ -30,91 +31,134 @@
     return sum(p.stat().st_size for p in S.regular_files(path))
 
 
-def publish(source, pool, token, plan_sha256, returncode, synthetic=False, rate=4*1024**2):
-    source, pool = Path(source), Path(pool)
-    if not synthetic and (pool.resolve() != AUTHORIZED_POOL.resolve() or rate > 4*1024**2):
-        raise ValueError('Results require the authorized Orchard home destination and rate')
-    if synthetic and not pool.resolve().is_relative_to(Path(__file__).resolve().parent/'test_runs'):
-        raise ValueError('Synthetic results require the private test directory')
-    if (not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or rate <= 0
-            or not re.fullmatch('[0-9a-f]{64}', plan_sha256)):
-        raise ValueError('Invalid return identity or rate')
-    if pool.is_symlink():
-        raise ValueError('Result pool must not be a symlink')
-    pool.mkdir(mode=0o700, exist_ok=True)
-    directory_fd = os.open(pool, os.O_RDONLY | os.O_DIRECTORY)
+def pool_operation(action,pool,token,local=None,timeout=60):
+    argv=[sys.executable,'-I','-B']
+    if os.environ.get('A_TRACE_RUNNER'):
+        argv += [os.environ['A_TRACE_RUNNER'],'--root',os.environ['A_JOB_ROOT'],
+                 '--config',os.environ['A_JOB_CONFIG'],'--script']
+    argv += [str(Path(__file__).with_name('return_io.py')),action,str(pool),token]
+    if local is not None:argv+=['--local',str(local)]
+    process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
     try:
-        fcntl.flock(directory_fd, fcntl.LOCK_EX)
-        if usage(pool)+EXIT_RESERVE > POOL_LIMIT:
-            raise S.BudgetError('No room for an exit receipt within the 1 GiB result pool')
-        dest = pool/token
-        dest.mkdir(mode=0o700)
-        complete, failed = (source/'COMPLETE.json').is_file(), (source/'FAILED.json').is_file()
-        value = dict(schema='evalx-orchard-result-return-v1', token=token,
-                     plan_sha256=plan_sha256, job=os.environ.get('SLURM_JOB_ID'),
-                     returncode=returncode, synthetic=synthetic, archive=None,
-                     archive_bytes=None, archive_complete=False,
-                     conflicting_terminal_markers=complete and failed,
-                     complete=complete and not failed and returncode == 0,
-                     status='FAILED' if failed or returncode else 'INCOMPLETE')
-        if value['complete']:
-            marker = json.loads((source/'COMPLETE.json').read_text())
-            value['complete'] = marker.get('plan_sha256') == plan_sha256 and marker.get('synthetic') is synthetic
-            if value['complete']:
-                value['status'] = 'COMPLETE'
-        initial = dict(value, status='INCOMPLETE', complete=False)
-        S.atomic_json(dest/'EXIT.json', initial)
-        log = json.dumps(dict(job=value['job'], token=token, returncode=returncode,
-                              status=value['status'], plan_sha256=plan_sha256), sort_keys=True)+'\n'
-        with (dest/'JOB.log').open('x') as stream:
-            stream.write(log[:4096])
-            stream.flush()
-            os.fsync(stream.fileno())
-        local = source.parent/('.return_'+token+'_'+uuid.uuid4().hex+'.tar.gz.partial')
-        try:
-            paths = S.members(source)
-            with local.open('xb') as raw:
-                with tarfile.open(fileobj=S.LimitedWriter(raw, S.ARCHIVE_LIMIT),
-                                  mode='w:gz', compresslevel=6) as archive:
-                    for name, path in sorted(paths.items()):
-                        archive.add(path, arcname=name, recursive=False)
-                raw.flush()
-                os.fsync(raw.fileno())
-            size, digest = local.stat().st_size, sha(local)
-            value.update(archive_bytes=size, archive_complete=True, archive_sha256=digest)
-            if size > ARCHIVE_LIMIT:
-                raise S.BudgetError('The compressed archive exceeds the 256 MiB per-read allowance')
-            if usage(pool)+size+EXIT_RESERVE > POOL_LIMIT:
-                raise S.BudgetError('The archive would exceed the 1 GiB result pool')
-            partial = dest/'result.tar.gz.partial'
-            started, copied = time.monotonic(), 0
-            with local.open('rb') as stream, partial.open('xb') as output:
-                for chunk in iter(lambda:stream.read(256*1024), b''):
-                    written = output.write(chunk)
-                    if written != len(chunk):
-                        raise OSError('Short result write')
-                    copied += written
-                    time.sleep(max(0, copied/rate-(time.monotonic()-started)))
-                output.flush()
-                os.fsync(output.fileno())
-            if copied != size or sha(partial) != digest:
-                raise ValueError('Persisted result differs from the node-local archive')
-            target = dest/'result.tar.gz'
-            os.replace(partial, target)
-            value['archive'] = dict(name=target.name, bytes=size, sha256=digest)
-        except Exception as error:
-            value.update(status='INCOMPLETE', complete=False, error=str(error)[:2048])
-            if value['archive_bytes'] is None and local.exists():
-                value.update(archive_bytes=local.stat().st_size, archive_complete=False,
-                             archive_size_is_lower_bound=True)
-        if (len(json.dumps(value).encode())+1024 > EXIT_RESERVE
-                or usage(dest)+EXIT_RESERVE > READ_LIMIT
-                or usage(pool)+EXIT_RESERVE > POOL_LIMIT):
-            raise S.BudgetError('No room for the bounded exit receipt')
-        S.atomic_json(dest/'EXIT.json', value)
-        return value
-    finally:
-        os.close(directory_fd)
+        stdout,stderr=process.communicate(timeout=timeout)
+    except subprocess.TimeoutExpired:
+        # An NFS process in uninterruptible sleep may not reap after SIGKILL.
+        # Do not wait for it: the parent must retain its deadline.
+        process.kill()
+        process.stdout.close();process.stderr.close()
+        raise TimeoutError('Pool operation exceeded '+str(timeout)+' seconds')
+    if process.returncode:raise subprocess.CalledProcessError(process.returncode,argv,stdout,stderr)
+    return json.loads(stdout)
+
+
+def write_test(pool,token):
+    started=time.monotonic()
+    result=pool_operation('test',pool,token,timeout=60)
+    if time.monotonic()-started>60:raise TimeoutError('Pool write test exceeded 60 seconds')
+    return result
+
+
+class UploadError(ValueError):
+    def __init__(self,error,objects):
+        super().__init__(str(error));self.objects=objects
+
+
+def upload(local,token,names=('result.tar.gz','EXIT.json')):
+    env=dict(os.environ,CLOUDSDK_CONFIG=CLOUD_CONFIG);objects={}
+    try:
+        for name in names:
+            path=Path(local)/name;uri=GCS_ROOT+'/'+token+'/'+name
+            objects[name]=dict(uri=uri,generation=None,sha256=sha(path),bytes=path.stat().st_size,verified=False)
+            subprocess.run(['gcloud','storage','cp',str(path),uri],env=env,check=True,
+                           capture_output=True,timeout=180)
+            described=subprocess.run(['gcloud','storage','objects','describe',uri,'--format=json'],
+                           env=env,check=True,capture_output=True,text=True,timeout=60)
+            meta=json.loads(described.stdout);generation=str(meta.get('generation',''))
+            if not generation.isdigit() or int(meta.get('size',-1))!=path.stat().st_size:
+                raise ValueError('GCS object metadata differs')
+            objects[name]['generation']=generation
+            check=Path(local)/(name+'.gcs-check')
+            with check.open('xb') as out:
+                subprocess.run(['gcloud','storage','cat',uri+'#'+generation],env=env,check=True,
+                               stdout=out,stderr=subprocess.PIPE,timeout=180)
+            digest=sha(check)
+            if check.stat().st_size!=path.stat().st_size or digest!=sha(path):
+                raise ValueError('GCS object SHA256 differs')
+            objects[name]['verified']=True
+            with (Path(local)/'JOB.log').open('a') as log:
+                log.write(json.dumps(dict(upload=objects[name]),sort_keys=True)+'\n')
+    except Exception as error:
+        with (Path(local)/'JOB.log').open('a') as log:
+            log.write(json.dumps(dict(upload_error=str(error),objects=objects),sort_keys=True)+'\n')
+        raise UploadError(error,objects) from error
+    return dict(verified=True,objects=objects)
+
+
+def publish(source,pool,token,plan_sha256,returncode,synthetic=False,rate=4*1024**2,mode='production'):
+    source,pool=Path(source),Path(pool)
+    if (not re.fullmatch('[a-z][0-9a-f]{8,32}',token) or rate<=0
+        or not re.fullmatch('[0-9a-f]{64}',plan_sha256) or not pool.is_absolute()):
+        raise ValueError('Invalid return identity or pool')
+    cap=20_000_000 if mode=='proof' else 90_000_000
+    local=source.parent/('r_'+token+'_'+uuid.uuid4().hex);local.mkdir()
+    complete,failed=(source/'COMPLETE.json').is_file(),(source/'FAILED.json').is_file()
+    marker=json.loads((source/'COMPLETE.json').read_text()) if complete else {}
+    ok=complete and not failed and returncode==0 and marker.get('plan_sha256')==plan_sha256 and marker.get('synthetic') is synthetic
+    value=dict(schema='evalx-orchard-result-return-v1',token=token,plan_sha256=plan_sha256,
+        job=os.environ.get('SLURM_JOB_ID'),returncode=returncode,synthetic=synthetic,
+        conflicting_terminal_markers=complete and failed,complete=ok,status='COMPLETE' if ok else 'FAILED',
+        archive_complete=True,mode=mode)
+    archive=local/'result.tar.gz'
+    with archive.open('xb') as raw:
+        with tarfile.open(fileobj=S.LimitedWriter(raw,min(S.ARCHIVE_LIMIT,cap-(1_000_000 if mode=='proof' else EXIT_RESERVE)-1)),mode='w:gz',compresslevel=6) as tf:
+            for name,path in sorted(S.members(source).items()):tf.add(path,arcname=name,recursive=False)
+        raw.flush();os.fsync(raw.fileno())
+    value.update(archive=dict(name=archive.name,bytes=archive.stat().st_size,sha256=sha(archive)),
+                 archive_bytes=archive.stat().st_size,archive_sha256=sha(archive))
+    S.atomic_json(local/'EXIT.json',value)
+    (local/'JOB.log').write_text(json.dumps(value,sort_keys=True)+'\n')
+    receipt=dict(schema=1,token=token,plan_sha256=plan_sha256,job=value['job'],channels={},returned=False)
+    try:receipt['channels']['pool']=pool_operation('publish',pool,token,local,timeout=120)
+    except Exception as error:receipt['channels']['pool']=dict(verified=False,error=str(error))
+    try:receipt['channels']['gcs']=upload(local,token)
+    except Exception as error:receipt['channels']['gcs']=dict(verified=False,error=str(error),objects=getattr(error,'objects',{}))
+    receipt['returned']=any(c.get('verified') for c in receipt['channels'].values())
+    receipt['verified_channels']=[k for k,v in receipt['channels'].items() if v.get('verified')]
+    S.atomic_json(local/'RETURN_RECEIPT.json',receipt)
+    S.atomic_json(source/'RETURN_RECEIPT.json',receipt)
+    with (local/'JOB.log').open('a') as log:log.write(json.dumps(receipt,sort_keys=True)+'\n')
+    if usage(local)-sum(p.stat().st_size for p in local.glob('*.gcs-check'))>=cap:
+        raise S.BudgetError('Return files exceed mode cap')
+    try:pool_operation('receipt',pool,token,local,timeout=60)
+    except Exception as error:
+        receipt['pool_receipt_error']=str(error)
+        S.atomic_json(source/'RETURN_RECEIPT.json',receipt)
+    value.update(returned=receipt['returned'],verified_channels=receipt['verified_channels'],local_return=str(local))
+    if not receipt['returned']:value.update(status='INCOMPLETE',complete=False)
+    return value
+
+
+def final_trace(root,config):
+    import trace_runtime
+    root=Path(root);returned=json.loads((root/'RETURN.json').read_text())
+    local=Path(returned['local_return'])
+    trace_runtime.collect(root,local/'TRACE.json.gz')
+    pin=dict(token=config['token'],plan_sha256=config['plan_sha256'],bytes=(local/'TRACE.json.gz').stat().st_size,
+             sha256=sha(local/'TRACE.json.gz'))
+    S.atomic_json(local/'TRACE.pin.json',pin)
+    names=('result.tar.gz','EXIT.json','JOB.log','RETURN_RECEIPT.json','TRACE.json.gz','TRACE.pin.json')
+    if sum((local/n).stat().st_size for n in names if (local/n).exists())+100_000>=20_000_000:
+        raise S.BudgetError('Proof return and final trace exceed 20 MB')
+    channels={}
+    try:channels['pool']=pool_operation('trace',config['pool'],config['token'],local,timeout=60)
+    except Exception as error:channels['pool']=dict(verified=False,error=str(error))
+    try:channels['gcs']=upload(local,config['token'],('TRACE.json.gz','TRACE.pin.json'))
+    except Exception as error:channels['gcs']=dict(verified=False,error=str(error),objects=getattr(error,'objects',{}))
+    receipt=json.loads((local/'RETURN_RECEIPT.json').read_text());receipt['final_trace']=channels
+    S.atomic_json(local/'RETURN_RECEIPT.json',receipt)
+    try:pool_operation('receipt',config['pool'],config['token'],local,timeout=60)
+    except Exception as error:S.atomic_json(root/'TRACE_RETURN_INCOMPLETE.json',dict(error=str(error)))
+    return channels
 
 
 def verify(receipt, archive, expected_plan):
```

### launcher/orchard_stage.py

Accepted source: `x27/gs/f665/sj/orch_cd/evalx/work/milestone/orchard_stage.py`.

```diff
--- accepted/launcher/orchard_stage.py
+++ package/launcher/orchard_stage.py
@@ -232,10 +232,10 @@
         unpack(archive, root, links=True)
         phase('runtime_'+str(index))
     camera = assets['camera_archive']
-    archive = archives/'camera.tar'
+    archive = archives/'a0.tar'
     receipts['camera'] = copy_parts([camera], archive, lambda part: Path(part['path']).open('rb'))
     unpack(archive, root)
-    phase('camera_package')
+    phase('a0')
     payload = root/'bootstrap/payload.tar.gz'
     if sha(payload) != config['payload_sha256']:
         raise ValueError('Reader payload differs from the submitted package')
@@ -263,6 +263,7 @@
     receipts['base'] = dict(manifest_sha256=sha(manifest), files=len(inventory))
     phase('base_snapshot')
     transport = json.loads(physical(root, config['release']['transport']['path']).read_text())
+    receipts['export_transport'] = transport
     environment = cloud_environment(assets['gcloud_config'])
 
     def cloud(part):
@@ -290,19 +291,38 @@
     if sha(physical(root, config['spec']['artifact']['path'])) != config['spec']['artifact']['sha256']:
         raise ValueError('Downloaded production artifact differs')
     phase('export_extract')
-    frames = physical(root, config['spec']['inputs']['frames_root'])
-    frames.mkdir(parents=True)
-    python = root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3'
-    command = [str(python), '-I', '-s', '-B', str(root/'x/pull.py'),
-               str(root/'x/need_frames.txt'), assets['frames_root']]
-    with process_stream(command, dict(os.environ), root/'staging.log') as stream:
-        inventory = extract_stream(stream, frames, None, 20*1024**3)
-        while stream.read(CHUNK):
-            pass
-    for name, record in inventory.items():
-        if Path(name).suffix != '.png' or Path(name).stem != record['sha256']:
-            raise ValueError('Frame stream differs from its content address')
-    receipts['frames'] = dict(files=len(inventory), bytes=sum(v['bytes'] for v in inventory.values()))
-    phase('frames')
+    receipts['videos'] = stage_videos(root, config, physical)
+    phase('videos')
     room(root)
     return receipts
+
+
+def stage_videos(root, config, physical):
+    root=Path(root)
+    package=physical(root,config['spec']['package'])
+    rows=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
+    destination=root/'v'
+    destination.mkdir()
+    verified=[]
+    for row in rows:
+        source=Path(row['alias_path'])
+        if not any(source.is_relative_to(Path('/project/community/jjyeung')/a) for a in ('3e0e8a36','8b677689')):
+            raise ValueError('Unregistered video alias')
+        source=video_source(row)
+        target=destination/(row['sha256']+'.mp4')
+        copied=copy_parts([dict(path=str(source),bytes=source.stat().st_size,sha256=row['sha256'])],target,
+                   lambda part:Path(part['path']).open('rb'))
+        verified.append(dict(relative_path=row['relative_path'],alias_path=str(source),**copied))
+    question=question_source()
+    target=physical(root,config['spec']['inputs']['rows']);target.parent.mkdir(parents=True,exist_ok=True)
+    copy_parts([dict(bytes=question.stat().st_size,sha256='d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc')],
+               target,lambda part:question.open('rb'))
+    return dict(videos=len(rows),verified=True,files=verified)
+
+
+def video_source(row):
+    return Path(row["alias_path"])
+
+
+def question_source():
+    return Path("/project/community/jjyeung/cp4tk_eval/official/meta_5130.jsonl")
```

### reader/evaluator/evalpath/kit_inputs.py

Accepted source: `x27c/r2/sj/orch_cd/rv_merge_fix/work/r3/aws_vl64rt/evaluator/evalpath/kit_inputs.py`.

```diff
--- accepted/reader/evaluator/evalpath/kit_inputs.py
+++ package/reader/evaluator/evalpath/kit_inputs.py
@@ -99,6 +99,23 @@
     rows = read_rows(spec['rows'])
     if len(rows) != 5130 or len(index_rows(rows)) != 5130:
         raise ValueError('Official metadata must contain exactly 5130 distinct items')
+    if 'question_types' in spec:
+        types = spec['question_types']
+        known = {r['question_type'] for r in rows}
+        if (not isinstance(types, list) or not types or
+                any(not isinstance(t, str) for t in types) or
+                types != sorted(set(types)) or not set(types) <= known):
+            raise ValueError('question_types must be a nonempty sorted unique known list')
+        if spec.get('slice') is not None:
+            raise ValueError('question_types cannot be combined with a stratified slice')
+        rows = [r for r in rows if r['question_type'] in types]
+    if 'example_ids' in spec:
+        ids = spec['example_ids']
+        if (not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids)
+                or ids != sorted(set(ids)) or spec.get('slice') is not None
+                or not set(ids) <= {str(r['id']) for r in rows}):
+            raise ValueError('example_ids must be sorted unique IDs within the selected cohort')
+        rows = [r for r in rows if str(r['id']) in ids]
     result = []
     for row in stratified(rows, spec.get('slice'), spec.get('seed', 17)):
         task = {**row, 'example_id': str(row['id']), 'benchmark': 'official5130',
```

