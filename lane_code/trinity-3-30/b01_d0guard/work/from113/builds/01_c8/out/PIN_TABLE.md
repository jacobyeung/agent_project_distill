# C8 pin audit

This table recomputes local evidence. N/E includes partial checks; it is not a pass or permission to launch.

| Check | Expected | Actual | Result |
|---|---|---|---|
| 1 | assigned job and private root | No C8 allocation or launch packet exists. | N/E |
| 2 | literal payload digest | No C8 BATCH payload exists. | N/E |
| 3 | 32 MiB, unique relative regular members | No C8 BATCH payload exists. | N/E |
| 4 | config schema, mode, partition, step, token, GPU count | No C8 runtime configuration or allocation exists. | N/E |
| 5 | partition, root, user and allocation | Orchard environment cannot be tested on this host. | N/E |
| 6 | family, review and order pins | C8 REVIEW and ORDER are not supplied. | N/E |
| 7 | family assets, limits, contract and ACCEPT | C8 authority and upload are pending. | N/E |
| 8 | authorization, plan and one order line | No C8 launch token or ORDER exists. | N/E |
| 9 | Bootstrap copies equal shipped code | 18 bootstrap hashes recomputed | PASS |
| 10 | job-private local storage | No Orchard private job mount exists. | N/E |
| 11 | empty exclusive H100 | GPU use is forbidden for this build. | N/E |
| 12 | five objects under one billion bytes | Declared five-object size fits the cap; masks and geometry bytes are unavailable. | N/E |
| 13 | prefix, name, generation, size and digest | Code generation and md5 are PENDING_UPLOAD; missing archives are unverified. | N/E |
| 14 | per-part size, SHA256, optional MD5; whole SHA256 | Available code, metadata and model hashes pass; masks/geometry and cloud generation are unavailable. | N/E |
| 15 | Exact member hashes and expanded sizes of available objects | {"code": 46, "metadata": 47, "model": 1}; absent: masks,geometry; Available archive inventories pass; masks and geometry inventories cannot be checked from absent bytes. | N/E |
| 16 | runtime, numpy, closure and trainer identities | Runtime/overlay/closure archives are unavailable; retained identities alone are insufficient. | N/E |
| 17 | safe interpreter links and unique interpreter | Required Python environment is absent. | N/E |
| 18 | Every sealed tree source and duplicated tree digest | 792 files; b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 | PASS |
| 19 | bwrap size and digest | Local bwrap smoke succeeded, but the pinned production binary is unavailable. | N/E |
| 20 | FLA manifest, bytes and members | FLA manifest pin passes; FLA runtime bytes are unavailable. | N/E |
| 21 | Worker and sitecustomize spec inputs equal exact members | {"worker_entrypoint": "cedb7bea5b94e345adcbf95f779c9be3d36e0064460055eca0bddefbcee7ebc7", "sitecustomize": "b3eeec3c45e00249b9d60db057b55fbd3ed1e7f2a53e6d88eba2bdaf36b94c58"} | PASS |
| 22 | Model manifest equals exact model-object member | cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7 | PASS |
| 23 | base archive and model-file inventory | Tokenizer/config subset is present; base weights are intentionally absent. | N/E |
| 24 | three depth-file identities | Depth weights are unavailable. | N/E |
| 25 | export parts, size, hash, headers and artifact | Artifact metadata hash and step pass; export tensor transport is unavailable. | N/E |
| 26 | Frame puller equals exact code member | 46000e96334535933239800d1437afc49cc74ca4017c337a43798c9906b8b694 | PASS |
| 27 | frame inventory | Frame inventory is retained, but frames.tar has not arrived. | N/E |
| 28 | real controls, code pins and checkpoint step | No C8 authority packet or worker namespace run exists. | N/E |
| 29 | fresh output directory | No worker run was started. | N/E |
| 30 | Both guard shell scripts have executable archive modes | 0o755 for both; source hashes unchanged | PASS |
| 31 | isolated flags, schema, ARCHIVE and SOURCE | Runtime/source constants agree; production bootstrap flags/import path not executed. | N/E |
| 32 | interpreter and overlay identities | Required interpreter and overlays are unavailable. | N/E |
| 33 | Sitecustomize equals code member | b3eeec3c45e00249b9d60db057b55fbd3ed1e7f2a53e6d88eba2bdaf36b94c58 | PASS |
| 34 | seven import pins, origins and required versions | Required runtime imports cannot be checked. | N/E |
| 35 | Worker entrypoint equals worker source, code pin and bootstrap pin | cedb7bea5b94e345adcbf95f779c9be3d36e0064460055eca0bddefbcee7ebc7 | PASS |
| 36 | complete config admission and allocation | Whole-worker config admission has not executed. | N/E |
| 37 | All adapter pins equal exact code members | 21 recomputed | PASS |
| 38 | input pins, cohort, 152/636/84, counts, keys and selection | Input pins pass; complete real cohort path requires the missing runtime. | N/E |
| 39 | nomdg and geometry kernel-source pins | Kernel source pins agree; AST partition requires a supported Python runtime. | N/E |
| 40 | runtime tree and restore source identities | Tree bytes pass; authenticated model restoration has not executed. | N/E |
| 41 | config, artifact, receipt, preparation, source seals and init-spec | Preparation/source-seal/model authentication has not executed. | N/E |
| 42 | Mask producer equals nomdg; all other receipt fields unchanged | c4a505fc88b61028a57f0a4cb4074a2ee0adb6f17eeed10aa93c9bf30764024e; scalar binding verified, cache-bind not executed; Producer-only draft pin passes static checks; actual cache-bind is blocked by the missing masks and runtime. | N/E |
| 43 | mask headers, frozen kit, SAM, provenance, operands and cache pins | Masks object is incomplete. | N/E |
| 44 | raw G3T constants and pins, capture rows and frame hashes | Raw G3T and real-frame objects are absent. | N/E |
| 45 | all 84 capture dispositions, ten-pair refusal coverage or explicit insufficient coverage | Core test drives real pilot terminal/project; no whole-worker pilot/full evidence exists. | N/E |
| 46 | fresh pool/token directory; pool at most one GiB | No rehearsal or production return has been published or verified. | N/E |

Evidence: `out/PIN_AUDIT.json`, `out/NATIVE_PIN_GRAPH.json`, and `out/NATIVE_LOCAL_CHECK.json`.
