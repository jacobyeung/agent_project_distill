The discovery kit is pinned to run 173912's selection and remains unable to start training. Install it as `X/qp_ee8c749b`; leave `X/qd` untouched. The second discovery still owes the production population, P1, and first-batch evidence.

1. The authenticated identities match task A's evidence run.

| Object | SHA256 / value | Evidence |
|---|---|---|
| Selection, both 173912 and 173881 | `a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73` | `work/build24m4z8/HASH_CHECK.json:2`; both actual files were hashed |
| Native receipt, both runs | `38c52f008d131a8554d3d18974f4d2de1e77bdf092c747132df477db8ff08398` | `work/build24m4z8/HASH_CHECK.json:4` |
| Canonical native receipt digest | `522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39` | Recomputed from the native receipt with sorted compact JSON; `HASH_CHECK.json:6` |
| Selection database | `5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df`, 849,543,168 bytes | `work/build24m4z8/evidence/db_bytes.json:7`; native receipt's database pin agrees |
| Base database | `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`, 837,255,168 bytes | `work/build24m4z8/evidence/db_bytes.json:23`; selection's input pin agrees |
| Selection receipt | `74640a29f939ce2aac8ce13683574078a09f3d02e89bbbe07653dda70ef49576` | Actual `d173912/173912/k_dr_p_q_sc_p_p_receipt.json` was hashed in `audit.py:21` |
| Authorization | `f9bdaf0ba8b84606d007cbfb5113cf470718fe2ce89a554af42c5ed8b8a50f6f` | Actual `inputs/ORCH_2258Z.md:2`; path and hash recorded in `PIN.json` |

`inputs/ORCH_2256Z.md:4`, `inputs/ORCH_2258Z.md:2`, and `inputs/NREVIEW_2258Z.md:4` authorize this discovery-only binding. `HASH_CHECK.json` records both runs and all full hashes. Evidence copies live under `work/build24m4z8/evidence/`; native receipts that contain inherited positive status text are stored losslessly as gzip.

2. The pin changes four control capsules and the seal.

`out/pin_discovery.py:32` authenticates the reviewed source seal, exact selection, exact authorization, native receipt, and database sizes before creating the kit. `out/pin_discovery.py:64` writes matching `routing_selection` objects in `k/h.json` and `k/r.json`, adds the selection to `staged_pins`, and adds its size/hash to `k/p.json` uploads and `pin_paths`. `out/pin_discovery.py:79` records the three selection identities, base, selection receipt, and authorization hash inside sealed `k/a.json`. The helper records the original file paths and hashes in `PIN.json`; it does not copy the authorization into the kit.

`out/arm_routing.py:14` exposes only `apply`, whose independent verdict gate runs at lines 23–27 before the pin-writing block at lines 91–107. There is no separately callable pin writer. The discovery helper therefore implements that small block independently. It leaves the arming helper byte-identical at `1a4b900b7153e540e3674d1ccb98c2c8bd75be3b2ac61ccd1edb17a0ad1a6a13`. Unlike launch arming, it does not add the base database to pool uploads: the discovery shell runs r first, and `out/kit_qdp/b/pl.py:135` authenticates `dr/p/q/base/rows.sqlite` before q reads it. The actual unchanged arming helper rejects the authorization message with `R1_REVIEW_VERDICT_HASH_MISSING` (`AUDIT.json`).

The source kit contains the reserved review token in eight Python files. Those literal spellings use escapes in qdp; their ASTs and runtime strings remain identical (`PIN.json.literal_escapes`, `AUDIT.json`). No such literal byte sequence occurs anywhere in qdp. The embedded source archive, configs, admission logic, and training guard retain their bytes or exact AST semantics. `PIN_TESTS.json` proves a reproducible kit and rejects altered selection, authorization, and receipt inputs.

Seal: `8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784` → `ee8c749b72ed21d3f1e20b8592cb14d9a171b3280b907b2220b0aea96407a608`. `GO=false` in both `k/a.json` and `BUILD.json`. All 2,099 checked original tree/kit/helper files retain their reviewed hashes and modes (`AUDIT.json`).

The read path and source of each required class of input are explicit below. `READ_CLOSURE.json` lists every one of the 224 pool upload entries, its size, state, and reader; it also lists all 92 selected handover members and eight external metadata records. `READ_SITES.json` lists static file-reading call sites in the wrapper, planner, resolver, native admission, population, and loader chain; it is a source audit, not a claim that every branch ran offline.

| Reader / call site | Files read | Satisfaction |
|---|---|---|
| `b/q.sh:5`, `job.sh:27`, `b/x.py:5`, `b/z.py:576` | Kit control, sealed bootstrap files, `k/j.json`, resolved record | New kit upload; bootstrap inputs remain in the existing pool |
| `b/z.py:188`, `b/z.py:198` | m400 DONE, receipt, run, small archive; existing export parts and metadata | Existing handover pool; unchanged resolver |
| `b/a.py:8`, `b/a.py:28`, `b/a.py:53` | Control, embedded source archive, incoming resolved record | New kit upload and node-local resolver output |
| `b/pl.py:17`, `b/pl.py:24`, `b/pl.py:43` | `k/h.json`, `k/p.json`, `X/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73` | Selection is the sole new u upload |
| `b/pl.py:51`, `b/pl.py:66`, `b/pl.py:67`, `b/pl.py:69` | Handover archive members, receipt, 224 uploads, external metadata | 223 u files already match supplied listing sizes; one selection upload; other files remain in the existing pool |
| `b/pl.py:79`, `b/pl.py:129`, `b/px.py:46` | Selection's chosen base receipt and database closure | Base receipt already in u; base DB generated by preceding r, then hash-checked at `pl.py:138`; other closure inputs use sealed `k/l.json` staging |
| `b/pl.py:190`, `b/i.py:41`, `b/pl.py:244` | Refreshed and scene-bound receipts | Generated node-locally from the existing authenticated recipe; 74640a29 is provenance, not an additional u dependency |
| `b/pl.py:269`, `b/pl.py:315` | Selection is copied into staged request and payload | Same new u object; content hash remains a49f117f |
| `launch_r1/entry.py:281`, `launch_r1/entry.py:282` | Native build inputs, then staged selection | Rebuilds N and compares its compact receipt digest against 522a3be3; it does not open historical paths embedded in the selection |
| `launch_r1/production_proof.py:151`, `student_pilot/r1_population.py:161` | Prepared native receipts/stores and all final reader offsets | Generated node-locally; selection DB 5e35c3ce already also exists in Orchard u (listing line 96) |
| `launch_r1/production_proof.py:168`, `launch_r1/production_proof.py:174`, `b/f0.py:60` | Bound population/indices, native loader, model/frame inputs, first batch | Existing authenticated staging plus generated preparation; no additional upload introduced by the pin |

3. The kit cannot start training.

`out/kit_qdp/b/a.py:11` rejects mode t when GO is false, before creating any work directory or importing the trainer. The real interpreter invocation returned `E03` (`work/build24m4z8/training_refused.log`). Mode q exits at `b/a.py:86`; the trainer call below that branch is unreachable from q. The unchanged decoded shell invokes only r and q at `work/build24m4z8/j_decoded.sh:414` and `:422`, then exits at `:435`. The discovery review publisher returns without training (`b/rv.py:279`). The config's `proof_mode=train` remains required by native initialization; it does not select the executable training branch. No claim about an unavailable jn2/jn3 wrapper is needed for this guard.

4. The real planner refuses before the pin and authenticates it afterward.

Run 173912 refused with `R1_ROUTING_SELECTION_PIN_MISSING` at `d173912/173912/q.log:10`. The local unarmed invocation reproduces that refusal (`work/build24m4z8/qd_plan.log`). The final qdp invocation passes the unchanged `selection_pin` and stops at `b/pl.py:51` with `E10:/project/community/jjyeung/okh7/h_6ed2c7aa/m400/s.tar` (`work/build24m4z8/qdp_plan.log`). That authenticated 194,334,720-byte archive is unavailable locally. The harness uses 173912's actual resolved record and maps only the Orchard selection location to a private local copy; it does not stub the planner, seal, or hash checks (`real_path.py:10`, `REAL_PATH_TESTS.json`).

`out/pp/pp.sh:1` is the separate preempt CPU probe: eight threads, 14 GiB address-space cap, empty CUDA visibility, nice 10, and node-local Slurm logs/caches. `out/j7.py:77` resolves the real pool and calls mode-q `plan_payload` at line 91; it never calls the returned staging hook, production proof, or trainer. Its mount keeps any planner publication node-local; the shell copies only the small `p0.json` outcome to `X/o/<job>/`. Missing staged runtime inputs remain an explicit possible stop on Orchard; this CPU probe does not perform full production staging. It was not submitted. `PP_SHELL.json` verifies failure publication through the actual shell with an explicit helper fixture.

5. The wrapper uses the new kit and repairs the path bug.

`out/jd7.sh:21` selects `X/qp_ee8c749b`. It retains the original j2 code verbatim (`:26`), node-local logs (`:25`), resource request, and polling interval. Its new job name has 12 random hex characters. `jd6.sh` contains no executable free-space floor check, so no threshold was lowered: the lane must still observe the answer's 30 GiB floor, or its accepted 25 GiB exception when its own shared writes stay below 1 GB.

`out/jd7.sh:75` calls `out/j7.py:21` to map only removal-file paths from the logical namespace into `$N/dr`, preserving and verifying every hash and defect restriction. It passes the normalized node-local manifest to the unchanged rdiff script. The real rdiff removal reader fails before mapping at `/tmp/q_22c714e1` and succeeds afterward on all 13 real removal files (`WRAPPER_TESTS.json`). The script remains `bc2db7747322d4c3eda8372ce4c9a3e74d457baa609f2798c465bf4054e75d92`; no rdiff2 is required.

`db_bytes.json:13` searches whether changing only SQLite header bytes could make N equal the target base DB; `dbb.log:2` reports no match. N is 12,288,000 bytes larger and its body digest differs from the base. A header-only substitution cannot make these databases equal. This diagnostic neither establishes nor blocks population equality, reader filtering, or the first batch. dbb3 remains unchanged; the second run must retain the actual N and base hashes, not force them equal.

`JD_SHELL.json` executes the delivered discovery shell with a relocated shared root and real bwrap mount. Explicit fixtures replace unavailable resolver/bootstrap assets and periodic publication; the x call executes the real mode-q planner and publishes its missing-archive refusal. The j2 body runs for one iteration. `MOUNT_PROBE.json` separately proves that the actual mount redirects result writes to local storage. These tests exercise no GPU or production data.

6. The second discovery publishes the evidence needed for (d), P1, and step 1.

`out/jd7.sh:60` binds `X/o/<job>/` to `$N/ev` for the discovery process; only unchanged j2 writes live screened log tails to the real shared directory. `out/jd7.sh:61` runs the final copier. `out/j7.py:42` adds the missing native population, filter, preparation, and forward files; it retains every inherited evidence file under the same result directory, optionally with `.gz`. `X/o/<job>/j7.json` maps each published filename to its original node path, exact uncompressed SHA256, stored SHA256, and byte sizes.

| Published name (possibly `.gz`) | Native source | Check |
|---|---|---|
| `j7/e0.json`, `j7/e1.json`, `j7/e3.json` | `p/q/b/population.json`, `indices.json`, `binding.json` | Complete post-filter sampler population and bound offsets |
| `j7/e2.json`, additional `j7/b*.json` | `reader_filters.json`, native per-stream order/indices, population config | P1 refusal counts and exact offsets retained by each reader |
| `j7/e4.json`, `j7/e5.json`, `j7/e6.json`, `j7/e10.json`, inherited `db_bytes.json` and `live/e2.json` | Final prepared/handover config and receipts; N routing receipt; native routing census | Trace the sampler's routing store back to DB 5e35c3ce and compare its population with the DB; the pin alone is not proof of (d) |
| `j7/e7.json`, `j7/e9.json`, inherited `live/f1.json` | Native `f.json`, `RESULT.json`, same-processor forward observations | Step-1 rows for all four ranks, losses/finite flags, and actual processor settings; expected absolute start is 0 with initialization milestone 400 |
| `j7/e8.json`, additional `j7/a*.json` | Native host receipt and loader audit | Selection digest, host assertions, and final sampler audit |

`production_proof.py:153` produces the population, `r1_population.py:199` writes reader filters, and `production_proof.py:18` calls the one-step native batch check. Missing files remain explicit in `j7.json`; the copier does not fabricate them. It prepares at most 3,500,000 payload bytes plus at most 100,000 manifest bytes, reserving 1,200,000 bytes for j2 and concurrent temporary copies: less than 4,800,000 bytes total (`out/j7.py:41`, `:62`, `:67`). Oversized publication fails before copying payloads (`WRAPPER_TESTS.json`).

For n_review1g: verify the new kit's SHA256SUMS seal is `ee8c749b72ed21d3f1e20b8592cb14d9a171b3280b907b2220b0aea96407a608` and verify every listed kit member. Decode and authenticate `k/a.json`; its `discovery_pin` must contain exactly a49f117f/522a3be3/5e35c3ce with the full values above, plus base 4e8e6c04, receipt 74640a29, and the authorization hash. Decode `k/h.json` and `k/r.json`; both must point to `u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73`. Hash that file and recompute the compact digest of the published native receipt authenticated by its `regenerated_receipt` pin; confirm its database is 5e35c3ce. Check the second job's `j7.json.kit_sha256`, host digest, prepared receipts, population, filters, and first-batch files before judging (d) or P1. Keep launch arming separate and use the unchanged independent verdict gate.

All 14 requested suite groups succeed; `work/build24m4z8/VALIDATION.json` names the exact final logs. Arming tests keep synthetic review text only in memory and serialize its backing state as base64; no plaintext synthetic verdict file exists (`AUDIT.json`). `FAILURES.json` retains setup failures and their output. `UPLOADS_24M4Z8.json/.list` contains exactly 51 files totaling 5,851,738 bytes; every file is below 5 MB. Only the selection is a new u object; the 223 existing u entries match the supplied size listing. The local pin builder and authorization are not Orchard uploads. No Orchard command, upload, scheduler, training run, or full production first batch was executed.
