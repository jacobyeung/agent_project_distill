**Verdict:** I walked 46 checks: 41 up to the first GPU call (`model.to(device)` in read_runtime.py:92) and 5 after it. Two would fail today for family 62a94599. #35, before any GPU work, is pilot 5's stale worker pin. #42, after load, parity and the five geometry captures, is a stale reader pin inside MASK_CACHE.json. The checks involve 21 duplicate-pin groups, and the copies disagree in 2 of them. native_local_check.py enforces the stale value of #35. No newer seal (native_package_s23_03) existed when I audited.

Key: "local" means I recomputed the value against the exact objects (stage_advanced_v2; all 5 archives match the sealed sha, bytes and members). "P5" means it passed in job 169589 with these inputs. "P3" means it passed in job 169521, whose inputs are identical except the reader (nomdg's diff touches only the parity gate). "N/E" means I could not evaluate it locally.

| # | Location | Expected from | Actual from | Duplicate pin? | Passes today? |
|---|---|---|---|---|---|
| 1-3 | BATCH.sh:7-20 | job id digits; literal payload sha 5f29511c; token literal e54df2d6a; exclusive mkdir; tar ≤32 MiB | environment; decoded payload | token ×4 (BATCH, CONFIG, authorization, ORDER); PACKET pins the script | yes (local), P5 |
| 4-5 | native_job.py:257, 69-74 | CONFIG schema, mode, partition, step, token, gpus; partition, root, user | CONFIG; environment | – | yes; P5 |
| 6 | native_job.py:83-86 | CONFIG.family / review / orch_order sha | bootstrap FAMILY, REVIEW, ORDER | family sha ×4 (CONFIG, REVIEW, authorization, ORDER) | yes (local) |
| 7-8 | native_common.py:68-102 | FAMILY assets, limits, worker_contract; REVIEW; authorization; plan; one ORDER line | CONFIG | CONFIG.assets≡FAMILY.assets; CONFIG.worker≡worker_contract; artifact sha ×4 | yes (local) |
| 9 | native_job.py:89-91 | FAMILY.bootstrap_pins (16) | payload bootstrap/* | = code_pins = code members | yes (local) |
| 10-11 | native_job.py:176-194; orchard_stage.py:120 | job-private /tmp mount; empty H100; exclusive control and archive files | /proc, nvidia-smi | – | P5 |
| 12-13 | native_stage.py:400-402, 36-41, 144 | 5 objects under 1 GB; name, generation, sha, bytes, prefix | small_objects | – | yes (local) |
| 14 | orchard_stage.py:142-149 | per-part bytes, sha, md5; whole sha | GCS stream | object sha also in its name | yes (local, sha and bytes); md5 P5 |
| 15 | native_stage.py:409-410 | members 39/47/614/1/464; expanded_bytes | extracted inventory | members duplicate every code, adapter and input pin | yes (local) |
| 16-17 | native_stage.py:415, 95-106, 427-431 | runtime, numpy, closure, trainer (bytes and sha); interpreter links | /project tars | runtime sha = native_bootstrap.ARCHIVE | P5; N/E |
| 18 | native_stage.py:436-438 | assets.tree_sources (792) | trainer tar | b01ce449 ×4 (digest, RUNTIME_TREE.json, runtime_tree.EXPECTED, bootstrap.SOURCE) | P5; copies agree |
| 19-20 | native_stage.py:444-455 | bwrap; fla.manifest 4e4a6ac5; fla bytes and members | metadata member m.sha; /project | manifest pin = member | yes (local), P5 |
| 21 | native_stage.py:168-175 | builds the runtime spec: entrypoints ← assets.worker_entrypoint, sitecustomize ← assets.sitecustomize | – | copies | feeds #33, #35 |
| 22-24 | native_stage.py:460-473 | model_manifest cc724d5e; base and model.json files; depth ×3 | model member; /project | manifest = member | yes (local), P5 |
| 25 | native_stage.py:480-499 | transport parts; archive sha and bytes; m200 headers; artifact sha | GCS export | artifact sha ×4 | P5 |
| 26-27 | native_stage.py:197-212 | frame_puller 46000e96; frames_inventory (4864) | code member; puller stream | puller = member | yes (local), P5 |
| 28-29 | native_job.py:182-183 → native_common.py:123-133 | family, review, order; code_pins (34); step 200; run dir absent | staged sj/fsw | code_pins = bootstrap_pins = members | yes (local), P5; token must be fresh |
| 30 | native_job.py:195 | assets.vnice 3ab2b542 | code member vnice.sh | = member = ORCHARD_ASSETS | yes (local) |
| 31-32 | native_bootstrap.py:32-45 | flags; SCHEMA; ARCHIVE ffc81db4; SOURCE; python; overlays | spec, runtime | ARCHIVE is a hand copy of assets.runtime.sha256 | yes, P5 |
| 33-34 | native_bootstrap.py:47-66 | sitecustomize b3eeec3c; 7 import pins; fla/triton versions | code member; runtime | sitecustomize = member | yes (local), P5 |
| **35** | **native_bootstrap.py:87** | **assets.worker_entrypoint 65f5cc0a (FAMILY + CONFIG → spec)** | **code member native_worker.py 8611b515** | **code_pins, bootstrap_pins and member say 8611b515** | **NO, stale** |
| 36-37 | native_worker.py:249, 17-18 | validate_config(launch) in the namespace; adapter_pins (18) | ro-bound sj, fsw | = code_pins = members | yes (local) |
| 38 | native_worker.py:26-41; nomdg.py:52-60; camera_cohort.py:42-71 | inputs pins; FROZEN_COHORT_SHA; 152/636/84; keys; counts; select_pilot = pilot_selection | metadata members | cohort sha ×3 | yes (CPU replica) |
| 39 | native_worker.py:127 → kernels.py:117-129 | kernel_source_pins nomdg 6b61d819, geometry 4bee6fc6 | staged out2 | = adapter_pins = code_pins = members | yes (local); partition succeeds |
