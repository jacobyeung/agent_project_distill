# F1 package comparison against 6e025a89

KIT_SHA256: `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b`

The baseline was reconstructed from the requested read-only archive and its full SHA256 was verified.
The package contains 125 files: 112 retain both their names and bytes; five retain their bytes under opaque names; eight contain only the path replacements or package-list exclusions shown below. Two unused cell files are omitted.
All 76 Python files compile. Every evaluator file is byte-identical. Reader, adapter and scorer changes are limited to the shown path strings; input hashes and pin constants are unchanged.
The archive uses sorted entries, fixed modes, mtime/uid/gid zero and empty owner/group names. F1 evidence and reports are external sidecars.
Packaged coverage and LOCAL_PROOF records retain baseline bytes; current-run evidence is linked from F1_EVIDENCE.md.

| Baseline file | Current file | Status | Baseline SHA256 | Current SHA256 |
|---|---|---|---|---|
| PROOF_JOB.md | PROOF_JOB.md | IDENTICAL | 826bc7a9b92bdc50d1beda0f268507da90af700cf9ba5434071efb251c9878c8 | 826bc7a9b92bdc50d1beda0f268507da90af700cf9ba5434071efb251c9878c8 |
| build/BASE_FILES.json | build/BASE_FILES.json | IDENTICAL | 90d0f20b5c766ecb7c6755dfde60f0d98a1d5f1ca9165f1f02d16004ae6e521e | 90d0f20b5c766ecb7c6755dfde60f0d98a1d5f1ca9165f1f02d16004ae6e521e |
| build/evidence.py | build/evidence.py | IDENTICAL | 25e9cbd568da22a698228079985a931e86986358ef9afea2f64efcf556bc1d3b | 25e9cbd568da22a698228079985a931e86986358ef9afea2f64efcf556bc1d3b |
| build/package.py | build/package.py | PACKAGE_FILE_LIST | 5459cce52cf6d0ca1adbdce877861c22de4ce16c396c51f37a2de6b82c647fe3 | 6da458f0cec2637c8f463c4eac189b597481651ebddfe41fd8cfac4a07b3deab |
| cohort/COHORT_OFFICIAL6.jsonl | cohort/COHORT_OFFICIAL6.jsonl | IDENTICAL | ccb51d5cbb552cb942518ed47badd36d4d5778a7dacaf6615e88cd1118361db8 | ccb51d5cbb552cb942518ed47badd36d4d5778a7dacaf6615e88cd1118361db8 |
| cohort/COHORT_REVSI5.jsonl | cohort/c5.jsonl | RENAMED_IDENTICAL | 62bb4df707ef6733ba708343be194e1dce083e25262057f86985eca2606be455 | 62bb4df707ef6733ba708343be194e1dce083e25262057f86985eca2606be455 |
| cohort/MEDIA_MANIFEST.json | cohort/MEDIA_MANIFEST.json | IDENTICAL | 632fd68c10dcb22ae995b2b3ba76cdbf01e5c36fc9791e757768ce27d3538d98 | 632fd68c10dcb22ae995b2b3ba76cdbf01e5c36fc9791e757768ce27d3538d98 |
| cohort/frame_plan.py | cohort/frame_plan.py | PATH_STRINGS | fd2f7c223fdfe47925f13d08a9efc1014f1b688ce03cdf78b90c8d58a5e86761 | 3672ea278f26fba3f4f5ad0e25feade77d0e9dccbf86919f3dced58642163846 |
| cohort/meta_5130.jsonl | cohort/meta_5130.jsonl | IDENTICAL | d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc | d69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc |
| inputs/REVSI999_PROVENANCE.json | inputs/REVSI999_PROVENANCE.json | IDENTICAL | d2335071a150dff05e09bee11a0f22036b43022243dbed7da77c1ea915ded032 | d2335071a150dff05e09bee11a0f22036b43022243dbed7da77c1ea915ded032 |
| inputs/REVSI_PUSH_FILES.json | inputs/REVSI_PUSH_FILES.json | IDENTICAL | bd1463c728874dcd98a7890343645d746cb489b35b2d52672f770f14af61dace | bd1463c728874dcd98a7890343645d746cb489b35b2d52672f770f14af61dace |
| inputs/cells_rv999_d32_cp1m200_on.json | — | OMITTED | a14efe5d150b8a125a8bf81587ed258c81b5178e21e2eeeec9686ebe137f312b | — |
| inputs/cells_tr_rv999_cp1on.json | — | OMITTED | a14efe5d150b8a125a8bf81587ed258c81b5178e21e2eeeec9686ebe137f312b | — |
| inputs/revsi999_membership.json | inputs/i2.json | RENAMED_IDENTICAL | 03456abc2fcd8199ed4fb4a3af54651ed07df2e5a1efa752aa165006ad4b6850 | 03456abc2fcd8199ed4fb4a3af54651ed07df2e5a1efa752aa165006ad4b6850 |
| inputs/revsi999_rows_t32.json | inputs/i1.json | RENAMED_IDENTICAL | 511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9 | 511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9 |
| inputs/revsi999_videos_t32.json | inputs/i3.json | RENAMED_IDENTICAL | badb56dc5cd95118c686262ed9af4055d92727ae9e282b5a3b41198a96411c82 | badb56dc5cd95118c686262ed9af4055d92727ae9e282b5a3b41198a96411c82 |
| inputs/revsi_indices.json | inputs/i4.json | RENAMED_IDENTICAL | 290111cf9c2bfa8fec66e70395922b830c2738633abf736600489cdff4b429b2 | 290111cf9c2bfa8fec66e70395922b830c2738633abf736600489cdff4b429b2 |
| launcher/MODELS.json | launcher/MODELS.json | IDENTICAL | 72cdfbff0e93a881099096f06e22b5c7e98046d443ae3430d498d06b49cfb37a | 72cdfbff0e93a881099096f06e22b5c7e98046d443ae3430d498d06b49cfb37a |
| launcher/ORCHARD_ASSETS.json | launcher/ORCHARD_ASSETS.json | IDENTICAL | 7e1da1668b4bac1d101692486e45f45912ccdde13d9f8ba8ca72cdd2287bf809 | 7e1da1668b4bac1d101692486e45f45912ccdde13d9f8ba8ca72cdd2287bf809 |
| launcher/TRANSPORT.json | launcher/TRANSPORT.json | IDENTICAL | 23339074f3eb41507c3e3c657159415582573cd8332c3b4777b4ac577a7b3b50 | 23339074f3eb41507c3e3c657159415582573cd8332c3b4777b4ac577a7b3b50 |
| launcher/chain_save.py | launcher/chain_save.py | IDENTICAL | c03862ffe60619f45a70514b0402db0411b5c6c79d2af8cbac48945575c15bdc | c03862ffe60619f45a70514b0402db0411b5c6c79d2af8cbac48945575c15bdc |
| launcher/orchard_job.py | launcher/orchard_job.py | IDENTICAL | b464a88866be571bdce7ddfdb1df70485c88c46102779e9c442369f1c4cbfe3c | b464a88866be571bdce7ddfdb1df70485c88c46102779e9c442369f1c4cbfe3c |
| launcher/orchard_launcher.py | launcher/orchard_launcher.py | PATH_STRINGS | 0114bd54cabac6d526a1cc2a8125a66a338f4f576c3ef147c2e2686138c79c7f | dae5a9665b5b4659fa5d21e57383369bc2d639a88ebdb920caa6853f0f5e94d9 |
| launcher/orchard_results.py | launcher/orchard_results.py | IDENTICAL | 6cf748b3539571935f3266e88510b222dfdbb8992a4024a0da44166f830a466e | 6cf748b3539571935f3266e88510b222dfdbb8992a4024a0da44166f830a466e |
| launcher/orchard_stage.py | launcher/orchard_stage.py | IDENTICAL | 371b8f850f2caa2002740d832c7e71623933f195408c0bd48fbc56605b1c4d08 | 371b8f850f2caa2002740d832c7e71623933f195408c0bd48fbc56605b1c4d08 |
| launcher/proof_card.py | launcher/proof_card.py | IDENTICAL | 332fd8c0cd26cc303463da8055261a17d77081f59df69a31d945bd9352ecc606 | 332fd8c0cd26cc303463da8055261a17d77081f59df69a31d945bd9352ecc606 |
| launcher/return_io.py | launcher/return_io.py | IDENTICAL | 774f5c0c134c44fd2ca5261e2ceb0b34f4cbd0edee5cffffa4c4f091ca4c6d90 | 774f5c0c134c44fd2ca5261e2ceb0b34f4cbd0edee5cffffa4c4f091ca4c6d90 |
| launcher/stdout_transfer.py | launcher/stdout_transfer.py | IDENTICAL | 85ad256cfa7836948ddba934ca82537486fc3c42cab06fa5442de86caef2e0f6 | 85ad256cfa7836948ddba934ca82537486fc3c42cab06fa5442de86caef2e0f6 |
| launcher/trace_runtime.py | launcher/trace_runtime.py | IDENTICAL | faec481ff5b445fdeb885a0ee70e1f83beaff05afb115dd3073fa6ce1934237d | faec481ff5b445fdeb885a0ee70e1f83beaff05afb115dd3073fa6ce1934237d |
| media/NEED_261.json | media/NEED_261.json | IDENTICAL | 50928f6f9a05da010dfcefe8f9975d32b3b33d97217630371232aece1f0caefe | 50928f6f9a05da010dfcefe8f9975d32b3b33d97217630371232aece1f0caefe |
| media/check_on_orchard.py | media/check_on_orchard.py | IDENTICAL | 82001b2d036455bb1764048964d4d4d286cc9a391aa21d1c2325c93e667df604 | 82001b2d036455bb1764048964d4d4d286cc9a391aa21d1c2325c93e667df604 |
| media/make_archive.py | media/make_archive.py | IDENTICAL | 1893053938c4ea3ebdab57aab098061bd017a467fb7138f1c3ca9eab484aa7a8 | 1893053938c4ea3ebdab57aab098061bd017a467fb7138f1c3ca9eab484aa7a8 |
| parity/ACCEPTED20.json | parity/ACCEPTED20.json | IDENTICAL | cf30bbe06af9c5a7d9d9bbf40ff9344b439bc0a8a3932dc422edb658be09a5b6 | cf30bbe06af9c5a7d9d9bbf40ff9344b439bc0a8a3932dc422edb658be09a5b6 |
| parity/DEV20.json | parity/DEV20.json | IDENTICAL | 6220488ff2488ce2084d38de4513bf35535f23a3e65b19cf216e8bcf23400b99 | 6220488ff2488ce2084d38de4513bf35535f23a3e65b19cf216e8bcf23400b99 |
| parity/PROMPT_PINS.json | parity/PROMPT_PINS.json | IDENTICAL | 7a43deb2ee2756d13044640c394deb4e8a5a7b6e59045f17bd7b1beb9f588637 | 7a43deb2ee2756d13044640c394deb4e8a5a7b6e59045f17bd7b1beb9f588637 |
| parity/prove_prompts.py | parity/prove_prompts.py | IDENTICAL | e46ef2c4d566ebd2b8c5cc970877184d028e801c8cd2a4d3b3e52055e87451b2 | e46ef2c4d566ebd2b8c5cc970877184d028e801c8cd2a4d3b3e52055e87451b2 |
| proof/COVERAGE.json | proof/COVERAGE.json | IDENTICAL | 612ad66f8c0f95a5364a1c3072954a05c6975e703acc0287e3eeceb64a458367 | 612ad66f8c0f95a5364a1c3072954a05c6975e703acc0287e3eeceb64a458367 |
| proof/COVERAGE_SUMMARY.json | proof/COVERAGE_SUMMARY.json | IDENTICAL | 50f6ced5f0ee334b2de68575390960dbc09a87de3226bdaf5209464911dba690 | 50f6ced5f0ee334b2de68575390960dbc09a87de3226bdaf5209464911dba690 |
| proof/LINES.md | proof/LINES.md | IDENTICAL | 0856310df654a0390a97297325996d410ea843baf5835148bc554d4453f18981 | 0856310df654a0390a97297325996d410ea843baf5835148bc554d4453f18981 |
| proof/LINES_CHECK.json | proof/LINES_CHECK.json | IDENTICAL | cc6c6d6e616e2ca159b0179e70f2dc318e01920bf13cc2c330f1f7683b133eb9 | cc6c6d6e616e2ca159b0179e70f2dc318e01920bf13cc2c330f1f7683b133eb9 |
| proof/LINES_LOCAL.json | proof/LINES_LOCAL.json | IDENTICAL | c5e06dbc7e87a2f1a48199b41a2177add515a4720d4406526f9139b349b1053f | c5e06dbc7e87a2f1a48199b41a2177add515a4720d4406526f9139b349b1053f |
| proof/LOCAL_LINES.json.gz | proof/LOCAL_LINES.json.gz | IDENTICAL | 6447d1f09c419b6a1b6e53aaafe5ff50db9aa66945246359c7a6fc7a3c102b50 | 6447d1f09c419b6a1b6e53aaafe5ff50db9aa66945246359c7a6fc7a3c102b50 |
| proof/LOCAL_PROOF.json | proof/LOCAL_PROOF.json | IDENTICAL | 7e24c4713f48d6220acef200d33d9b8090543cf036e94cf71909afdbaf3a494b | 7e24c4713f48d6220acef200d33d9b8090543cf036e94cf71909afdbaf3a494b |
| proof/PROOF.md | proof/PROOF.md | IDENTICAL | fa37a5c5f025431d66f518827a1c9b71ac241ebac9620a8a4c1097e4e75e00dc | fa37a5c5f025431d66f518827a1c9b71ac241ebac9620a8a4c1097e4e75e00dc |
| proof/SCORER_CHECK.json | proof/SCORER_CHECK.json | IDENTICAL | eb83f317d6b34132acaa1c04ad849922c8bb83dad98579862f2a87d8a01a206f | eb83f317d6b34132acaa1c04ad849922c8bb83dad98579862f2a87d8a01a206f |
| proof/coverage.ini | proof/coverage.ini | IDENTICAL | f483b6327862aec9285a563a0317bcdfccafa874ff28f404a46d72998878a4f9 | f483b6327862aec9285a563a0317bcdfccafa874ff28f404a46d72998878a4f9 |
| proof/fakes.py | proof/fakes.py | IDENTICAL | 97a378b0cf706e07e30bcd7bff21af8ccab07f49e22449da6538aff15e6c6f3a | 97a378b0cf706e07e30bcd7bff21af8ccab07f49e22449da6538aff15e6c6f3a |
| proof/fixtures.py | proof/fixtures.py | IDENTICAL | 224e65e476e323f1ff5bb5e85b13e21195e62513ba2f0b5132f729fa5a505f20 | 224e65e476e323f1ff5bb5e85b13e21195e62513ba2f0b5132f729fa5a505f20 |
| proof/lines_report.py | proof/lines_report.py | IDENTICAL | 55d6eb477fe3582e5442372ac404d43d0dc91a72cf95ff8ab93b45371f45b340 | 55d6eb477fe3582e5442372ac404d43d0dc91a72cf95ff8ab93b45371f45b340 |
| proof/measure.py | proof/measure.py | IDENTICAL | 108de721d328e0cb0951fe9563764ba46bd01a1e0fbf72884362a8ae0b79a2a9 | 108de721d328e0cb0951fe9563764ba46bd01a1e0fbf72884362a8ae0b79a2a9 |
| proof/orchard_env.py | proof/orchard_env.py | IDENTICAL | acba5c863658c0f81bfef9ca3c7c9abb5e76ec86926181bb188727c27dac45f3 | acba5c863658c0f81bfef9ca3c7c9abb5e76ec86926181bb188727c27dac45f3 |
| proof/phase_b.py | proof/phase_b.py | IDENTICAL | 3d7171dc348f4d7cd9b5a6fda26f4e9146eaf56633d366fb5dbf2ac4458f3f79 | 3d7171dc348f4d7cd9b5a6fda26f4e9146eaf56633d366fb5dbf2ac4458f3f79 |
| proof/plan_on_orchard.py | proof/plan_on_orchard.py | IDENTICAL | ef05c9f77dc06306ca11fba98da06f06b9ac716d96357547967be98f068083e2 | ef05c9f77dc06306ca11fba98da06f06b9ac716d96357547967be98f068083e2 |
| proof/pull.py | proof/pull.py | IDENTICAL | 46000e96334535933239800d1437afc49cc74ca4017c337a43798c9906b8b694 | 46000e96334535933239800d1437afc49cc74ca4017c337a43798c9906b8b694 |
| proof/run.py | proof/run.py | PATH_STRINGS | 2b67672adacda82b4fa86d8c696852700db3991d91893e2206428200dd016e94 | 892342c722fc0f721db8a2f5c1140d16c6a452b9a01e73b9e67d64a22af86fbb |
| proof/run_on_orchard.sh | proof/run_on_orchard.sh | IDENTICAL | faa4af48f9a684b35daadb22a21dc7d54539ebae8793660968e21d3a892e3eaf | faa4af48f9a684b35daadb22a21dc7d54539ebae8793660968e21d3a892e3eaf |
| proof/runtime_checks.py | proof/runtime_checks.py | IDENTICAL | 45bf7ad05d2dbfa57c7c17c7b0ac7e1cbfed0a092b60ebd0f0e84d7f6f131dd2 | 45bf7ad05d2dbfa57c7c17c7b0ac7e1cbfed0a092b60ebd0f0e84d7f6f131dd2 |
| proof/selection.py | proof/selection.py | IDENTICAL | d21f61c890c7b865cd543a6884281483951425929f10b6ab9123eab6c8589527 | d21f61c890c7b865cd543a6884281483951425929f10b6ab9123eab6c8589527 |
| reader/chain.py | reader/chain.py | PATH_STRINGS | 6eb8d7220726b74bc210c6befafa6312c1880742c5fb28ea2b7201464e89d435 | 96cf9ad22618899ddafe4b5ee8c337598f5612e9d4e5bc5cb8ded7061d833084 |
| reader/evaluator/budget.py | reader/evaluator/budget.py | IDENTICAL | 8365bd3b1db5bedc0a86e2ef9624faf01ad43d0e3d3fffda53169cd9ad003175 | 8365bd3b1db5bedc0a86e2ef9624faf01ad43d0e3d3fffda53169cd9ad003175 |
| reader/evaluator/budget_admission.py | reader/evaluator/budget_admission.py | IDENTICAL | be32a571fbb9c4024d739b51302d3881aa1ce628bb45e2e8cc9924060f653341 | be32a571fbb9c4024d739b51302d3881aa1ce628bb45e2e8cc9924060f653341 |
| reader/evaluator/budget_annotation.py | reader/evaluator/budget_annotation.py | IDENTICAL | c63f058069e8302fcd3bd69505690ab0e784b6f368d3492429335d30cebbc4d1 | c63f058069e8302fcd3bd69505690ab0e784b6f368d3492429335d30cebbc4d1 |
| reader/evaluator/budget_merge.py | reader/evaluator/budget_merge.py | IDENTICAL | fc7c2872dc5daeb1eb1de61ee95b7b7a0e160fc697995ac2caf1615a4bd7ff2a | fc7c2872dc5daeb1eb1de61ee95b7b7a0e160fc697995ac2caf1615a4bd7ff2a |
| reader/evaluator/c1_export.py | reader/evaluator/c1_export.py | IDENTICAL | 7716fd6750376830519ef39295992bfab6876e644c92745d6a0ec82aceec7177 | 7716fd6750376830519ef39295992bfab6876e644c92745d6a0ec82aceec7177 |
| reader/evaluator/cells.py | reader/evaluator/cells.py | IDENTICAL | 8336d2d64ffd2b7f492dc6b52fb4182523eced3610483932d91e086d2b9b50ff | 8336d2d64ffd2b7f492dc6b52fb4182523eced3610483932d91e086d2b9b50ff |
| reader/evaluator/data.py | reader/evaluator/data.py | IDENTICAL | 5c667bc55150adc13a50131b624962ea9a9f510f5b803f258ad9a31a710ef045 | 5c667bc55150adc13a50131b624962ea9a9f510f5b803f258ad9a31a710ef045 |
| reader/evaluator/evalpath/SOURCE_PINS.json | reader/evaluator/evalpath/SOURCE_PINS.json | IDENTICAL | 7f1d449de1498e5a6f34dbdc09309dcbeaceef76e3f20bec92f603771a345781 | 7f1d449de1498e5a6f34dbdc09309dcbeaceef76e3f20bec92f603771a345781 |
| reader/evaluator/evalpath/__init__.py | reader/evaluator/evalpath/__init__.py | IDENTICAL | 320ff8e49d53c5528f439ae83544dcd0e4063933eb2168774b70ca6d9d1cdd38 | 320ff8e49d53c5528f439ae83544dcd0e4063933eb2168774b70ca6d9d1cdd38 |
| reader/evaluator/evalpath/items.py | reader/evaluator/evalpath/items.py | IDENTICAL | bc9211c07c803111a8c9f6af8ecb6e7bc057b0034da09ad94b02862f41526590 | bc9211c07c803111a8c9f6af8ecb6e7bc057b0034da09ad94b02862f41526590 |
| reader/evaluator/evalpath/kit_inputs.py | reader/evaluator/evalpath/kit_inputs.py | IDENTICAL | e4a6bdae702ab3fb003d7c11388fc22b051f92e5f9ca3d1cf0e95c250a0cd977 | e4a6bdae702ab3fb003d7c11388fc22b051f92e5f9ca3d1cf0e95c250a0cd977 |
| reader/evaluator/evalpath/official.py | reader/evaluator/evalpath/official.py | IDENTICAL | a5d6d79fd29fce43791401cd01438f16f3ff6ad7a6c2651cb70d0d42088cf589 | a5d6d79fd29fce43791401cd01438f16f3ff6ad7a6c2651cb70d0d42088cf589 |
| reader/evaluator/evalpath/sampling.py | reader/evaluator/evalpath/sampling.py | IDENTICAL | 9235a822a813648ee0da7cf9cc79531a4cbb7b6344e8fee369e5b34e615d82e1 | 9235a822a813648ee0da7cf9cc79531a4cbb7b6344e8fee369e5b34e615d82e1 |
| reader/evaluator/frame_env.py | reader/evaluator/frame_env.py | IDENTICAL | 8b6ddcb0caa15e68f304d50cd41952b7e7d9eba4542c1beb1b49ecdf9b6be7ed | 8b6ddcb0caa15e68f304d50cd41952b7e7d9eba4542c1beb1b49ecdf9b6be7ed |
| reader/evaluator/frame_stage.py | reader/evaluator/frame_stage.py | IDENTICAL | 991f297fd783a37342ab65f4fed5580b47fb25550375efdee5fce14564b3ea5c | 991f297fd783a37342ab65f4fed5580b47fb25550375efdee5fce14564b3ea5c |
| reader/evaluator/journal.py | reader/evaluator/journal.py | IDENTICAL | 508eca8d6877fe6898d9309f0f5c23b4580c321d27dc258ddd6fe4718cc9b1a5 | 508eca8d6877fe6898d9309f0f5c23b4580c321d27dc258ddd6fe4718cc9b1a5 |
| reader/evaluator/launch.py | reader/evaluator/launch.py | IDENTICAL | 80af57d28cffe87e85d76a898ab6c4cbe898d53772ce1e90ecbcee4d333009f2 | 80af57d28cffe87e85d76a898ab6c4cbe898d53772ce1e90ecbcee4d333009f2 |
| reader/evaluator/media.py | reader/evaluator/media.py | IDENTICAL | 537fb597909e41699511d2e85c16029836cc4ba5aa0fcf25dc76f3abe5f0fc8d | 537fb597909e41699511d2e85c16029836cc4ba5aa0fcf25dc76f3abe5f0fc8d |
| reader/evaluator/merge.py | reader/evaluator/merge.py | IDENTICAL | 5da344c8ff214bcd106b0b78635eda330aed2a85169ac03e1ef9977341d65912 | 5da344c8ff214bcd106b0b78635eda330aed2a85169ac03e1ef9977341d65912 |
| reader/evaluator/metric.py | reader/evaluator/metric.py | IDENTICAL | aa0c7968a9a8c812222b8d3468864b54e13eb21cff25155e4a6393508beb05fc | aa0c7968a9a8c812222b8d3468864b54e13eb21cff25155e4a6393508beb05fc |
| reader/evaluator/nested_sampling.py | reader/evaluator/nested_sampling.py | IDENTICAL | 231bad31b385b01d3fdd46d8b8341e6ebfcc67e6d06cfb8f1fc277ec5bf017f2 | 231bad31b385b01d3fdd46d8b8341e6ebfcc67e6d06cfb8f1fc277ec5bf017f2 |
| reader/evaluator/parity.py | reader/evaluator/parity.py | IDENTICAL | 6e259bd1dd23ec67bb8feef5a3a06bbc2e67ecfd60cc98a876febd510f44c14c | 6e259bd1dd23ec67bb8feef5a3a06bbc2e67ecfd60cc98a876febd510f44c14c |
| reader/evaluator/pointing.py | reader/evaluator/pointing.py | IDENTICAL | 1ee243eb896b518c74f06f18a3d98a213a7d5f09617296b3a5d9cf26d2a2ff5c | 1ee243eb896b518c74f06f18a3d98a213a7d5f09617296b3a5d9cf26d2a2ff5c |
| reader/evaluator/pointing_video.py | reader/evaluator/pointing_video.py | IDENTICAL | 4712457ebf1e932219966a5b4eae6bddbc43a077251f717e636085c88dba1ee7 | 4712457ebf1e932219966a5b4eae6bddbc43a077251f717e636085c88dba1ee7 |
| reader/evaluator/provenance.py | reader/evaluator/provenance.py | IDENTICAL | 35e544877add1d9d4b6e2167aa071ffda13da390db4a410bd4b51339655b5c7c | 35e544877add1d9d4b6e2167aa071ffda13da390db4a410bd4b51339655b5c7c |
| reader/evaluator/scoring.py | reader/evaluator/scoring.py | IDENTICAL | 0e3bcf0a578f18846f671b85582bb030137bb3169346dd5f99a10c6a8b099cce | 0e3bcf0a578f18846f671b85582bb030137bb3169346dd5f99a10c6a8b099cce |
| reader/evaluator/stage.py | reader/evaluator/stage.py | IDENTICAL | 890ea8641c08c2de4e12169c77202c8cc7b19f1bc360c0a36509c5c451474d2b | 890ea8641c08c2de4e12169c77202c8cc7b19f1bc360c0a36509c5c451474d2b |
| reader/evaluator/think_settings.py | reader/evaluator/think_settings.py | IDENTICAL | 23af8945c30247bc80ebd0b2b7b7e6d22c0e6e70a190594d84161af49fb533df | 23af8945c30247bc80ebd0b2b7b7e6d22c0e6e70a190594d84161af49fb533df |
| reader/evaluator/token_audit.py | reader/evaluator/token_audit.py | IDENTICAL | 20dd4f31b70350b80ddb0cab1b35294349b9ff8f76058648da5537e265cff0b0 | 20dd4f31b70350b80ddb0cab1b35294349b9ff8f76058648da5537e265cff0b0 |
| reader/evaluator/trainer/__init__.py | reader/evaluator/trainer/__init__.py | IDENTICAL | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| reader/evaluator/trainer/batches.py | reader/evaluator/trainer/batches.py | IDENTICAL | d9f5a79b63baf1144dc5d0377450491dcb04c28335dbce51093e4edde7614638 | d9f5a79b63baf1144dc5d0377450491dcb04c28335dbce51093e4edde7614638 |
| reader/evaluator/trainer/layout_reference.py | reader/evaluator/trainer/layout_reference.py | IDENTICAL | 596760db5b3ccf6cceb5ab2938402ba9e6c559a069ef5fd84b041ce90b71700e | 596760db5b3ccf6cceb5ab2938402ba9e6c559a069ef5fd84b041ce90b71700e |
| reader/evaluator/trainer/pose_samples.py | reader/evaluator/trainer/pose_samples.py | IDENTICAL | 0484ecce014fa97f6f2b44f250ddfdee142b42662d765638f130c59ddd53a736 | 0484ecce014fa97f6f2b44f250ddfdee142b42662d765638f130c59ddd53a736 |
| reader/evaluator/trainer/students.py | reader/evaluator/trainer/students.py | IDENTICAL | cfe01c144680c8126328e7ad9afc7b1a002de7ba143dcea9c156e0473fe619c3 | cfe01c144680c8126328e7ad9afc7b1a002de7ba143dcea9c156e0473fe619c3 |
| reader/evaluator/trainer/trace_contract.py | reader/evaluator/trainer/trace_contract.py | IDENTICAL | aed482c7ca7d15cd22b524ba0c9bdd1595d6e0c518c0d9d1e54c3c9377cebae8 | aed482c7ca7d15cd22b524ba0c9bdd1595d6e0c518c0d9d1e54c3c9377cebae8 |
| reader/evaluator/worker.py | reader/evaluator/worker.py | IDENTICAL | b2ac21c1549b87baff730e50279d3c4c0844966bc5e29363aef372c76574e20e | b2ac21c1549b87baff730e50279d3c4c0844966bc5e29363aef372c76574e20e |
| reader/official_adapter.py | reader/official_adapter.py | PATH_STRINGS | 243e03b584650edfb7d4c20967c772afb906654c8cba7c7c25957e98a781c522 | a10f34f4b6d240e0e366e56c9928f1c7d9cd080a91886d6a3a1d6c1381b35109 |
| reader/official_score.py | reader/official_score.py | PATH_STRINGS | 54a55bb6cf202c16d45a5479bd6242bfb4abb07a72fbe009cbade1b7edaad0a4 | b279ddc18acd3e019b8343214d963a60d3bafcd929f2a3e4d965a0aa1b88d409 |
| reader/out/common.py | reader/out/common.py | IDENTICAL | 1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4 | 1954de01cc935fb744ebc92a3ede19a94658d2ce4fefb3c1e1ba40b03d2508c4 |
| reader/out/direct.py | reader/out/direct.py | IDENTICAL | d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a | d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a |
| reader/out/export_check.py | reader/out/export_check.py | IDENTICAL | 0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2 | 0400842c559565b66db50d6c8fde7c323e8600a82d70685d469a4b316d7ec8d2 |
| reader/work/vendor/r3/CELL_ITEMS.json | reader/work/vendor/r3/CELL_ITEMS.json | IDENTICAL | ed6d686aad9e21ceeeebe3ef7b9b0a8ff4bb2f9334b0f546ca972003fdcce860 | ed6d686aad9e21ceeeebe3ef7b9b0a8ff4bb2f9334b0f546ca972003fdcce860 |
| reader/work/vendor/r3/EXCLUDED.jsonl | reader/work/vendor/r3/EXCLUDED.jsonl | IDENTICAL | f7a212048c2cfe95538b4c35d5f9147ff107743d1811ca0c57880ca93ae38941 | f7a212048c2cfe95538b4c35d5f9147ff107743d1811ca0c57880ca93ae38941 |
| reader/work/vendor/r3/EXCLUDED_MISSING_ROOM.jsonl | reader/work/vendor/r3/EXCLUDED_MISSING_ROOM.jsonl | IDENTICAL | 279889626320714771abbd38185d3b07b8abb7daf3b965301d1842bbc8dcfdfd | 279889626320714771abbd38185d3b07b8abb7daf3b965301d1842bbc8dcfdfd |
| reader/work/vendor/r3/FPS_AUTHORITY.source.json | reader/work/vendor/r3/FPS_AUTHORITY.source.json | IDENTICAL | 36ae882f936ebc7a7d1a7651b5c53056c07d39ff552b2368a5c1e8068568d422 | 36ae882f936ebc7a7d1a7651b5c53056c07d39ff552b2368a5c1e8068568d422 |
| reader/work/vendor/r3/FPS_RULE.json | reader/work/vendor/r3/FPS_RULE.json | IDENTICAL | d9af606320e78823fb2e0fa3c80358c77d7e3cdc2326684a501893c04af3094f | d9af606320e78823fb2e0fa3c80358c77d7e3cdc2326684a501893c04af3094f |
| reader/work/vendor/r3/FRAMES.json | reader/work/vendor/r3/FRAMES.json | IDENTICAL | c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439 | c5e0dad804a59bb6f4932137d129e3a7dc1cf675e6342ff94e36979b7ca29439 |
| reader/work/vendor/r3/ITEMS.jsonl | reader/work/vendor/r3/ITEMS.jsonl | IDENTICAL | 00144cd0f736b4bd7908030b7feb749a926d7ef37b54c555c09bdd8c82ef9111 | 00144cd0f736b4bd7908030b7feb749a926d7ef37b54c555c09bdd8c82ef9111 |
| reader/work/vendor/r3/LABEL_BLOCKERS.jsonl | reader/work/vendor/r3/LABEL_BLOCKERS.jsonl | IDENTICAL | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| reader/work/vendor/r3/LABEL_SOURCE_PINS.json | reader/work/vendor/r3/LABEL_SOURCE_PINS.json | IDENTICAL | 8b69c0a012cca31376f2b46c7da58744cdfb94af4ec94f9bb646f2c92d981efb | 8b69c0a012cca31376f2b46c7da58744cdfb94af4ec94f9bb646f2c92d981efb |
| reader/work/vendor/r3/MISSING_LABELS.jsonl | reader/work/vendor/r3/MISSING_LABELS.jsonl | IDENTICAL | b8aff3d740f37d95b3e4a85a3f3faac5580b2e19c02cb2360e541611a2dacd4b | b8aff3d740f37d95b3e4a85a3f3faac5580b2e19c02cb2360e541611a2dacd4b |
| reader/work/vendor/r3/PINS.json | reader/work/vendor/r3/PINS.json | IDENTICAL | 698d623e9f49bdcbf101719bb2b09fd7239452d1d610d827110a1423dcce9db2 | 698d623e9f49bdcbf101719bb2b09fd7239452d1d610d827110a1423dcce9db2 |
| reader/work/vendor/r3/RELEASED_DEV.jsonl | reader/work/vendor/r3/RELEASED_DEV.jsonl | IDENTICAL | edafe3e5b436f16fd22a49facd25c62216f3478c6952ccbd9e5e1eef7cae7760 | edafe3e5b436f16fd22a49facd25c62216f3478c6952ccbd9e5e1eef7cae7760 |
| reader/work/vendor/r3/STRATA.jsonl | reader/work/vendor/r3/STRATA.jsonl | IDENTICAL | 9ee9c29820a85cf4da89a4499d8bc644b5c88c0ad22f151a09a770b025563af0 | 9ee9c29820a85cf4da89a4499d8bc644b5c88c0ad22f151a09a770b025563af0 |
| reader/work/vendor/r3/TASKS.jsonl | reader/work/vendor/r3/TASKS.jsonl | IDENTICAL | a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e | a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e |
| reader/work/vendor/r3/TIMING_AUTHORITY.json | reader/work/vendor/r3/TIMING_AUTHORITY.json | IDENTICAL | 7827fb117e158809c59bda741976a872761790bbd2298047ba8c6f33ba72ea43 | 7827fb117e158809c59bda741976a872761790bbd2298047ba8c6f33ba72ea43 |
| reader/work/vendor/r3/WITHHOLD_SCENES.json | reader/work/vendor/r3/WITHHOLD_SCENES.json | IDENTICAL | 88e1a708e240920fb39e34ede6f47c189be830538388db7a214b60ca258df05e | 88e1a708e240920fb39e34ede6f47c189be830538388db7a214b60ca258df05e |
| reader/work/vendor/r3/adapter.py | reader/work/vendor/r3/adapter.py | IDENTICAL | eb53eb601f7ef5ed732f0d7a9ef2275349de9553eb9c7ac39dd464bcfa03789a | eb53eb601f7ef5ed732f0d7a9ef2275349de9553eb9c7ac39dd464bcfa03789a |
| reader/work/vendor/r3/cells_cp1m200.json | reader/work/vendor/r3/cells_cp1m200.json | IDENTICAL | 472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135 | 472c0c9793735a044ee2f11bf2ee6f155c452ce5cbcb2b4fc262974c9c4b1135 |
| reader/work/vendor/r3/cells_f17.json | reader/work/vendor/r3/cells_f17.json | IDENTICAL | cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878 | cbb5521184c1410861b5339dcf40100196fc661d9b4ec6bafa3d548ad8d86878 |
| reader/work/vendor/r4/adapter.py | reader/work/vendor/r4/adapter.py | IDENTICAL | 9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099 | 9ccf84f1a2b9e7b99abf1975a98f67d1ea610cb1acc72728a60c2b2234a6c099 |
| reader/work/vendor/r5/adapter.py | reader/work/vendor/r5/adapter.py | IDENTICAL | 431b5d367ccde126f02297489da5a328ecd2484bd787f8acfae73eecec3fd9d1 | 431b5d367ccde126f02297489da5a328ecd2484bd787f8acfae73eecec3fd9d1 |
| reader/work/vendor/r5/dev_scoring.py | reader/work/vendor/r5/dev_scoring.py | IDENTICAL | d7594f9dad6045a6c6fdb55e7136401a6368d1c2fabc801bc1cb7c7eaedda220 | d7594f9dad6045a6c6fdb55e7136401a6368d1c2fabc801bc1cb7c7eaedda220 |
| reader/work/vendor/r5/report.py | reader/work/vendor/r5/report.py | IDENTICAL | c0d60afe47a5459150d40841e923fffe90d7ea749c12fcd3ef44b21950b24fd6 | c0d60afe47a5459150d40841e923fffe90d7ea749c12fcd3ef44b21950b24fd6 |
| tests/conftest.py | tests/conftest.py | IDENTICAL | 2f68c7c03f6c9d73cc3dacdf6e227bce4f7b5ceb270b7656f2c56774d2e41b71 | 2f68c7c03f6c9d73cc3dacdf6e227bce4f7b5ceb270b7656f2c56774d2e41b71 |
| tests/test_kit.py | tests/test_kit.py | PATH_STRINGS | a9a54b4d51ad402cfdfa2f01019173612a7beefb56612026e162747d9065cc53 | a00c72872280b4321fa0d2ef4d3163b34efb2d1a75729496c91bad9bd4c96548 |
| tests/test_pass2.py | tests/test_pass2.py | IDENTICAL | 0a550c006d7fc9a855cbe2e127690201b29df851b72d959de65ae07fcbb51efb | 0a550c006d7fc9a855cbe2e127690201b29df851b72d959de65ae07fcbb51efb |
| tests/test_pass3.py | tests/test_pass3.py | IDENTICAL | c8e378dde95ee969d29ab44d5f2eca6a4f26a752346fe4c82c6e2d00e8dfbd66 | c8e378dde95ee969d29ab44d5f2eca6a4f26a752346fe4c82c6e2d00e8dfbd66 |

## Complete unified diffs (zero context)

```diff
--- 6e025a89/build/package.py
+++ F1/build/package.py
@@ -10,2 +10,2 @@
-names.update(('cohort/COHORT_REVSI5.jsonl','proof/LOCAL_PROOF.json','build/package.py','build/evidence.py','build/BASE_FILES.json'))
-names=sorted(names)
+names.update(('cohort/c5.jsonl','proof/LOCAL_PROOF.json','build/package.py','build/evidence.py','build/BASE_FILES.json'))
+names=sorted(names - {'inputs/cells_rv999_d32_cp1m200_on.json','inputs/cells_tr_rv999_cp1on.json'})

--- 6e025a89/cohort/frame_plan.py
+++ F1/cohort/frame_plan.py
@@ -46 +46 @@
-    indices=json.loads((Path(__file__).resolve().parents[1]/'inputs/revsi_indices.json').read_text())
+    indices=json.loads((Path(__file__).resolve().parents[1]/'inputs/i4.json').read_text())

--- 6e025a89/launcher/orchard_launcher.py
+++ F1/launcher/orchard_launcher.py
@@ -199 +199 @@
-        inputs=dict(rows=str(payload_root/'inputs/revsi999_rows_t32.json'),video_root=str(logical/'v0'),
+        inputs=dict(rows=str(payload_root/'inputs/i1.json'),video_root=str(logical/'v0'),
@@ -208 +208 @@
-            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name not in ('meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json'):
+            if p.is_file() and p.suffix in ('.py','.json','.jsonl') and p.name not in ('meta_5130.jsonl','COHORT_OFFICIAL6.jsonl','FRAME_PLAN.json','REVSI_PUSH_FILES.json','REVSI999_PROVENANCE.json','cells_rv999_d32_cp1m200_on.json','cells_tr_rv999_cp1on.json'):

--- 6e025a89/proof/run.py
+++ F1/proof/run.py
@@ -31 +31 @@
-    all_rows=O.read_rows(ROOT/'cohort/COHORT_REVSI5.jsonl');chosen=F.select(all_rows);chosen_ids={str(r['id']) for r in chosen}
+    all_rows=O.read_rows(ROOT/'cohort/c5.jsonl');chosen=F.select(all_rows);chosen_ids={str(r['id']) for r in chosen}
@@ -38 +38 @@
-        indices=json.loads((ROOT/'inputs/revsi_indices.json').read_text())[Path(rel).stem]['32-frame']
+        indices=json.loads((ROOT/'inputs/i4.json').read_text())[Path(rel).stem]['32-frame']
@@ -58 +58 @@
-    payload[pfx+'cohort/COHORT_REVSI5.jsonl']=''.join(json.dumps(r)+'\n' for r in chosen).encode()
+    payload[pfx+'cohort/c5.jsonl']=''.join(json.dumps(r)+'\n' for r in chosen).encode()
@@ -63 +63 @@
-    fixture_videos=json.loads((ROOT/'inputs/revsi999_videos_t32.json').read_text())
+    fixture_videos=json.loads((ROOT/'inputs/i3.json').read_text())
@@ -67 +67 @@
-    payload[pfx+'inputs/revsi999_videos_t32.json']=video_bytes
+    payload[pfx+'inputs/i3.json']=video_bytes
@@ -110 +110 @@
-    def score(dest,cohort,output,**kwargs):return original_score(dest,package/'cohort/COHORT_REVSI5.jsonl',output,allow_partial=True)
+    def score(dest,cohort,output,**kwargs):return original_score(dest,package/'cohort/c5.jsonl',output,allow_partial=True)

--- 6e025a89/reader/chain.py
+++ F1/reader/chain.py
@@ -82 +82 @@
-        cohort=HERE.parent/'cohort/COHORT_REVSI5.jsonl'
+        cohort=HERE.parent/'cohort/c5.jsonl'
@@ -86 +86 @@
-            cohort.write_text(''.join(json.dumps(r)+'\n' for r in A.load_rows(HERE.parent/'cohort/COHORT_REVSI5.jsonl') if str(r['id']) in selected))
+            cohort.write_text(''.join(json.dumps(r)+'\n' for r in A.load_rows(HERE.parent/'cohort/c5.jsonl') if str(r['id']) in selected))

--- 6e025a89/reader/official_adapter.py
+++ F1/reader/official_adapter.py
@@ -29,2 +29,2 @@
-    names={'rows':'revsi999_rows_t32.json','membership':'revsi999_membership.json',
-           'videos':'revsi999_videos_t32.json','indices':'revsi_indices.json'}
+    names={'rows':'i1.json','membership':'i2.json',
+           'videos':'i3.json','indices':'i4.json'}
@@ -75 +75 @@
-        expected = sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/COHORT_REVSI5.jsonl')))
+        expected = sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/c5.jsonl')))
@@ -97 +97 @@
-        cfg['datasets'][0]['example_ids']=sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/COHORT_REVSI5.jsonl')))
+        cfg['datasets'][0]['example_ids']=sorted(str(r['id']) for r in select(load_rows(HERE.parent/'cohort/c5.jsonl')))

--- 6e025a89/reader/official_score.py
+++ F1/reader/official_score.py
@@ -193 +193 @@
-    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);p.add_argument('--cohort',default=str(Path(__file__).resolve().parents[1]/'cohort/COHORT_REVSI5.jsonl'));p.add_argument('--output',required=True);p.add_argument('--parent-answers')
+    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);p.add_argument('--cohort',default=str(Path(__file__).resolve().parents[1]/'cohort/c5.jsonl'));p.add_argument('--output',required=True);p.add_argument('--parent-answers')

--- 6e025a89/tests/test_kit.py
+++ F1/tests/test_kit.py
@@ -24,2 +24,2 @@
-def spec():return A.dataset(ROOT/'inputs/revsi999_rows_t32.json')
-def cohort():return O.read_rows(ROOT/'cohort/COHORT_REVSI5.jsonl')
+def spec():return A.dataset(ROOT/'inputs/i1.json')
+def cohort():return O.read_rows(ROOT/'cohort/c5.jsonl')
@@ -38 +38 @@
-    native=json.loads((ROOT/'inputs/revsi999_rows_t32.json').read_text());gt={r['example_id']:r['ground_truth'] for r in native}
+    native=json.loads((ROOT/'inputs/i1.json').read_text());gt={r['example_id']:r['ground_truth'] for r in native}
@@ -66 +66 @@
-    p=fresh('tamper');p.mkdir();rows=json.loads((ROOT/'inputs/revsi999_rows_t32.json').read_text())[:-1];file=F.js(p/'rows.json',rows)
+    p=fresh('tamper');p.mkdir();rows=json.loads((ROOT/'inputs/i1.json').read_text())[:-1];file=F.js(p/'rows.json',rows)
@@ -214 +214 @@
-    videos=json.loads((ROOT/'inputs/revsi999_videos_t32.json').read_text())
+    videos=json.loads((ROOT/'inputs/i3.json').read_text())
```
