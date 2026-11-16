Build N is NOT READY for an official native read. ReVSI has a tested CPU orchestration fixture; its production runtime and Orchard bootstrap are unfinished. VSI-Bench is not done. No official benchmark score, submission, or upload was produced.

The seven phases are stage, frames, towers, identity proof, canary, read, and score. Every attempted phase writes a PASS or FAIL receipt. A proof failure prevents official decoding. The harness read creates primary, secondary_fallback, and secondary_room_unserved records. The e2e read creates one primary arm. Exact ID-union checks reject missing or duplicate worker records.

All 24 tests pass in `tests_final.log`. The final fixture runs are `../work/rehearsal_revsi_harness_04/` and `../work/rehearsal_revsi_e2e_03/`. Each run covers two generated videos and 26 synthetic items, which gives two items for each of ReVSI's 13 subtypes. Both runs pass all seven phases and produce labelled offkit reports. The harness fixture uses a synthetic serving adapter over b04's tiny-model decode path; it does not execute C8r's real decoder.

The tests cover the 999-item and 302-scene cohort, missing IDs and types, exact journal unions, raw UTF-8 answer delivery to the official scorer, unserved-call accounting, a refused distance fallback, frame-layout guards, binding refusals, unsafe archives, the inherited item-start cutoff, and fixture-to-production rejection. The mutation test writes a failed proof receipt with zero official decodes and no canary receipt.

`PROOF_KEYS.json` records five camera and five distance items chosen by ascending SHA256 of their keys. `PROOF_CPU.json` records equality for all ten through b04's actual decode loop using forced reference token IDs. Five camera responses are independently recomputed from the recorded geometry. Five distance responses use the recorded response strings because the journal's ground queries are digests. A changed response fails the forced-token comparison. `proof_cpu_final.log` records the final-source run. This test does not prove real-model logits, independent distance serving, or GPU equality.

`EXECUTED_LINES.json`, `COVERAGE_revsi_harness.json`, and `COVERAGE_revsi_e2e.json` record the executed-line census. `ORCHARD_ONLY.md` identifies unexecuted paths. The requested production-CONFIG rehearsal with only transport changed has NOT run. The inspected first batch of the real export has NOT run. `DIAGNOSTICS.json` records the voluntarily cancelled broad-tracing diagnostic; no cluster-killed job was retried.

`NEED_302.json` lists every ReVSI media file. `REVSI_ADDITIONAL_41.md` names the additional 41. The push manifest covers 24 of those without hashes; 17 have no manifest entry. `NAME_INVENTORY.json` counts 501 distinct question-operand/video pairs without consulting answers. It is not proof that every arbitrary model-emitted alias has a proposal.

`OPEN_INPUTS.md` lists the P8 freeze record, K1-refit selector, 41 media uploads and pins, SAM 3 Orchard checkpoint location, b04 artifact and EAT-1 record, and the missing dense-video mapping for tier-32 ReVSI. It also identifies unfinished implementation: the production stager, C8r context and cache bridge, original-export in-job proof, portable opaque bootstrap, remote return authentication, and outer deadline watchdog. The launcher refuses submission even if an input-only binding succeeds.

The imported offkit modules own binding, frame guards, native-record adaptation, aggregation, labels, and report rendering. The accepted evaluator owns item scoring. No scorer, geometry rule, selector, unit conversion, or reader core was forked. `../DIFF.md` records exact inherited call sites and adapter differences. C8r's scripted answer and unit-conversion path are excluded from the adapter call graph.

`MODULE_MAP.md` maps every module to `tools/orchkit/reader/read.py` and companion modules. `read_config.frames` already has the shared orchkit-read-v1 form. The complete production read config and shared pin-manifest integration remain unfinished. The code tar uses absolute read-only Trinity dependencies and is a review artifact, not a deployable Orchard packet.

`../RUN.md` gives operator commands and transfer constraints. `../SIZING.md` reports the measured-rate limits. ReVSI's routed primary decode plus the supplied G3T scene term already projects to 2.264 H100-hours, before the other phases. The named K1 measurements contain no SAM elapsed-time rate, so no total or 64-frame speed claim is fabricated.

The code archive is `code.tar`, with SHA256 `044f81136d60a1136b3151d51e3616df87f6d943e7a24ff8078a9accf8d84fe8`. `CODE_PINS.json` lists every archived file. `DEPENDENCY_PINS.json` pins the named read-only integrations. `SHIP_SHA256SUMS` also covers this readiness report, the other delivery evidence, and the two authoritative fixture runs; the checksum list cannot hash itself. `BUILD_INVENTORY.json` records the build's total size.

The following hashes identify every file in the code archive.

| File | SHA256 |
|---|---|
| `native_read.py` | `c1e2bbe70f09a73a82be7461ae76c820367a8ef0d972836cccb25e39381a063b` |
| `offnative/__init__.py` | `64c81ea7466554f99550b8bafcea7f2e3f71890974980d43ac04f912180f3639` |
| `offnative/census.py` | `ae1cfec52861bda5e931746a683ca505c89988ad0a49e2940fad7729ce5ef656` |
| `offnative/cli.py` | `62122f35704b5c87f419e071053fc08b0fb5d76a40dca7652e770da2af738e67` |
| `offnative/cohort.py` | `2d7287d190dd3b1801726ff29780caa7ae1199a4721d8644d5344749329cf107` |
| `offnative/fixture.py` | `946b15d676708a45e77c39c9e9c9261e9070ef36dc99ea39898c8da05d64a81c` |
| `offnative/frames.py` | `415b14338877167a9c0c9254839b37fb3126598a2096190bd811a0070332d348` |
| `offnative/io.py` | `f448c2425f616760b416f51a13d7158ff2a10f760e48f713b0f92f523379771b` |
| `offnative/package.py` | `d84b6c02a6af698f041bc96a96770f2830dcf200d36c5962cf7dc6f282dac1d0` |
| `offnative/paths.py` | `25b95c8efa533ad09ea39f5483bb0820772f9487f8908c3e70b0b101b7c4f4e4` |
| `offnative/proof.py` | `9116d226070c0a73f0e24a4a5d599da02fa84c874b47d390067111b526284b04` |
| `offnative/readers.py` | `433b77412916c564b7483d6de72d33e6270ba8be8e33d2ad9a9b967f1abf889c` |
| `offnative/rehearse.py` | `b96ad29facaf00472cb13363d53ac9f8a513e765e606ca753670bb09c187537b` |
| `offnative/replay.py` | `0582214b2b9296d9be381247e55b71f25a4264875fd825a29c1ecdf413cd3883` |
| `offnative/reporting.py` | `c0f053653bbebebae2bc9851501826407d89b2dd8d48d770a5fb2e4a826ada45` |
| `offnative/scoring.py` | `ca28b7ffdb2e4560dd26d6b7d2826d7ea0e038cae6382c0b176c68b4738e5143` |
| `offnative/staging.py` | `26e3a8c7b5f0d815e1a177e6b76db83248d30b654a0e4033b47cdf0672271e7e` |
| `offnative/worker.py` | `838400339eec34c57941feb53211cbb466512a9900d2d7e55ad6426b31c10a97` |
| `kit/tests/conftest.py` | `059729f5faa9d76f97c9b99520b1dc8ef31698b9adef4d674a8cc84cd248e12b` |
| `kit/tests/test_admission.py` | `1193ef89a92a51e0f486f92b116fb8858e2def4ffdf6a16e50144c54058f0e19` |
| `kit/tests/test_contracts.py` | `9c88069d2bd8727e85e4f5ca148f42b5f618fe3a14ba366d2dccb64410d92303` |
| `kit/tests/test_frames.py` | `879dfe60d69ff10740f8e8576d2b0d01aa51ca1470cd847b01bd75d779febdcb` |
| `kit/tests/test_staging.py` | `d7f6e6c21cf24e0faa1497c9fa376313fbc266f3911001ede4b33d411327a67c` |
| `kit/tests/test_worker.py` | `9655ce7674d2469ebddae8bbb0d6cf2cc19657fd88076d850b06332abc901e5b` |
| `RUN.md` | `16a2e6c6ea95413610ce2a83dfd6bf521b24a60e24c5c51f74ee2d6ece80c147` |
| `SIZING.md` | `41ba7e29bf5cc3b215307b230bacf4fb7cc48b92acba4dedb6c6983135166da9` |
| `DIFF.md` | `1f040599ff16111af12dc6b5f320e28c2eed1cbe1daf539e7fe71376c8307707` |
