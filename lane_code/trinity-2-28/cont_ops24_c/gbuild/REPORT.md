The derived package is built and CPU-tested. Its token is `a1abb3a204ff8`; its destination is `/project/community/jjyeung/a1abb3a204ff8`. No SSH, Git, network, GPU inference, submission, deletion, or remote command ran. Runtime files and tests were written here. GT metadata was read only from the permitted sibling `gt` directory. The explicitly requested environment check selected `/scratch/jjyeung/envs/p1cpu/bin/python` (Python 3.12.13, NumPy 2.2.6); this node's default `python3` is 3.6.8.

**Delivery.** [out/delivery.tgz](out/delivery.tgz) contains 14 package files. [out/BUILD.json](out/BUILD.json) lists every outer-file and payload-member SHA256, the changed members, token, sizes, and canonical plan digest. The job requests one H100, eight CPUs, 200 GiB host memory, general partition, and `05:00:00`. Orchard CPU staging retains the parent's 200 GiB allocation; local tests used one numerical-library thread and a 15 GiB address-space limit.

- Delivery bytes: `5314949`; SHA256: `d0dac81b82995c8ed756c99a498cb85cdb73d9f2e7cf280fcca4dcb69def0187`.
- Payload SHA256: `d7e65fb68490352588fb34a11a056b94ead6c16bdba3e84eaf65f1bd23238a33`.
- Plan SHA256: `87449d1f2ed45bcb15dd30c7597665f62b78e1437743e905258d809ee548ca38`.
- Installed package bytes: `5349185`. Placement conservatively budgets `10770765` bytes, including the streamed delivery and BUILD descriptor, below 50,000,000.
- Job name: `a15_cot_apa1abb3a204ff8`.

`gpkg/build.py` derives the token from authenticated parent bytes and changed content. Repeated builds produced identical bytes. `--no-overlay` preserves every selected parent delivery file byte-for-byte, including `0.tgz`, `BATCH.sh`, and the differently formatted public descriptors. The original outer delivery archive was not supplied, so its tar-container byte identity is not claimed. Old CPU receipts, job IDs, and baseline returns are deliberately not placed in the new package.

`a/1.json`, `a/export.json`, and `a/5.py` remain byte-identical to the parent. All original `b/`, `tree/`, `h1eval/`, and `items/` members remain byte-identical. The parent plan predates the named `serving_pins` and `evaluator_code_sha256` fields; the builder preserves every existing plan field except `token` and updated `payload_pins`. Tests compare all serving/evaluator source bytes directly. The parent `8.py` remains unchanged, and its real `load_helpers` and `check_inputs` functions accept the derived package locally. The generic package/plan/payload/export checks follow the applicable `return_tools_h.package_info` pattern without importing its incompatible H-only item rules.

The runtime overlay lives under `g/`, with numeric manifests. The framework changes are `job.py`, numeric action 3 in `entry.py`, and a narrow resource change in `common.py`. `common.py` requests H100 and eight CPUs; its opacity guard exempts only the exact scheduler argument `--gres=gpu:h100:1`, whose `h1` substring otherwise triggers the experiment-name filter. Other forbidden strings remain rejected. New external argv, environment values, launch paths, and GCS object names pass that guard. Existing sealed internal filenames and the explicitly requested `metadata/PARITY.json` and `metadata/CAPTURE.json` remain descriptive.

**Read and capture.** The operator prepares exactly one read. Its selector, tower/none settings, memo verify mode, 30 verify IDs, `['g3t']` module allowlist, and disabled own-depth saving equal baseline read 1. Tests also compare all manifest call texts, responses, served flags, and item order directly with the supplied baseline return.

The worker uses `make_capped_real`, `parity.bind_item`, the original prompt builder and `_prepare_decode`, and the production per-read call cap. It performs one prefill per item, including the non-caller, and no answer decode. The prefill counter observes the shared language decoder because `_prepare_decode` constructs a temporary native wrapper. It runs 150 primary items in manifest order, then the first ten callers again. During repeats, the shared memo allowlist is empty; G3T recomputes, and each new SAM socket encodes fresh features. Weight objects stay loaded. The capture includes pass index, seconds, peak allocated/reserved GPU memory, calls, proposals, tracks, selector/null information, masks, lifts, fitted boxes, cameras, and scale.

The gzip stream lives at logical `/scratch/jjyeung/b01ec87a6f29b/c/0.gz`, physically under the assigned job's private local directory. It is outside `/scratch/jjyeung/b01ec87a6f29b/r`, which the normal return archives. The writer flushes every committed item and reserves gzip-trailer space within the exact 1,900,000,000-byte compressed cap. A full run contains 160 records: 150 primary and ten repeat records. `CAPTURE.json.items` counts these records; the parity receipt separately reports primary and repeat completion.

The operator launches the numeric worker under the same vnice prefix, environment construction, and installed process guard as the parent runner. It starts the worker in its own process group so a deadline cannot leave a vnice child writing while publication starts. STOP prevents new items. The operator starts no new work after `end - max(stop_margin, 5100)` and allows 180 seconds to drain, then 30 seconds after TERM before killing its own worker group. This reserves 85 minutes for two 1800-second transfers, describe, and the parent's normal return margin. The unchanged plan still records the parent's 1800-second stop margin; this operator stops earlier.

**Parity and return.** An item matches only when every call matches the registered discrete fields; numeric box coordinates are outside that rule. At least 143 of 150 must match. The gap tolerance is exactly twice the largest absolute printed-gap difference between primary and repeat calls, calculated with decimal arithmetic. Every baseline gap in a discrete-matching item must fall within that tolerance. Missing repeats cannot certify a tolerance. The receipt contains every item's flags and the complete baseline/repeat gap-difference lists. A failed rule never aborts or suppresses capture.

In `job.py`'s `finally`, publication attempts whatever capture exists, including a partial file. It uses the template's CLOUD_CONFIG and GCS_ROOT, `cp`, `objects describe`, and generation-specific `cat` readback, with byte and SHA256 comparison. The object is `GCS_ROOT/<return_token>c/0.gz`; the readback stays beside the local capture. Errors go to the returned CAPTURE receipt and do not prevent normal pool/GCS publication. `COMPLETE` describes worker completion, not successful capture upload: inspect `CAPTURE.json.verified` and `PARITY.json.trusted` separately.

`gpkg/join_capture.py` skips repeat records and copies the global `trusted` flag and the item's discrete-match flag into every table row. It authenticates the gzip SHA256 and record counts, admits untrusted captures with explicit flags, and uses the kit's unchanged S0–S5 scorer. The original kit CLI rejects untrusted receipts and does not distinguish repeats; use this wrapper for the new package.

**GT: principled refusal.** `gt/adapter.py --inspect-only` inspected all 38 available NPZs using ZIP/array headers and small metadata arrays. It did not decompress their depth/instance pixel arrays or hash the entire NPZs. The sibling SHA list lies outside the permitted read roots and was not read. [gt/INSPECTION.json](gt/INSPECTION.json) contains per-file schemas, instance inventories, boxes, cameras, intrinsics, source indices, missing requirements, and all 300 occurrence bindings.

| Measurement | Count |
|---|---:|
| Required / available / missing captures | 60 / 38 / 22 |
| Items with / without a GT file | 76 / 74 |
| Unique exact-label bindings | 142 / 300 |
| Occurrences without a GT file | 148 |
| Occurrences without an exact label | 10 |
| Ambiguous exact labels among these occurrences | 0 |
| Available items with all 32 exact anchor indices | 76 / 76 |
| Landscape / portrait instance rasters | 29 / 9 |
| Complete converted GT items | 0 |

The NPZs provide `ids`, `labels`, `obb_centroid`, `obb_lengths`, `obb_axes`, `c2w`, `K_frames`, `valid`, and `frame_indices`. All available frame-validity flags are true. Their instance rasters are either `(32,240,320)` or `(32,320,240)`. None provides the required 480×640 raster. Nine ARKit files also lack the selected-mask grid in the reader's orientation. Replicating or transposing pixels would manufacture the missing visibility evidence. The files also lack explicit camera/world axes, pixel-center conventions, metric units, OBB-axis layout, and full-length versus half-length declarations. Field names alone do not certify those conventions.

Binding uses exact labels, with no synonym or fuzzy matching. The sole non-caller's two names come literally from its question. Missing and ambiguous bindings remain U; all joins remain U because complete annotations are unavailable. `convert()` refuses, and the default adapter CLI exits with a refusal after writing evidence. Part B stops here as requested. No metric alignment or residual was computed: no real reader capture is present, and the convention/raster prerequisites are missing. A future adapter must use shared camera poses for one rigid SE(3) transform, never fit scale or object boxes, and report translation and rotation residuals.

**Point mode: refusing stub.** The worker accepts `--points FILE` through `python -m g.w CONFIG --points FILE`; numeric action 3 also accepts a `points` key in its config. `g/q.py` validates the requested nested JSON and finite normalized coordinates, then refuses before weights load. The payload lacks `sam3/model/sam3_image.py`, the implementation of the backend model's `_get_dummy_prompt()`, and the definition/constructor of the geometric-prompt object passed to `forward_grounding`. `tree/student_pilot/sam3_tower.py` only calls the dummy-prompt method; it does not define a geometric point class. Its external source receipt expects SAM source staged separately on Orchard. No unsupported class name or constructor signature is invented.

Once that pinned implementation is available, the mode should bind every point to an exact anchor source index; null means no mask. Each positive point and unchanged text should enter `forward_grounding`; choose the containing mask with greatest score × presence, combine the frames into one track, record that the selector was skipped, and pass those masks through the existing lift/gap code. The capture validator will need an explicit selector-skipped point-mode record. The current package cannot perform this ceiling experiment.

**Validation actually run.** All 33 tests passed: 13 package/runtime/GT tests, nine kit replay/lifting tests, and eleven funnel tests. The package tests cover deterministic/no-overlay bytes, parent helper pin admission, baseline calls/settings, embedded bundle contents, operator rehearsal and dispatch with CPU doubles, vnice argv and STOP handling, real capped-hook semantics, one prefill/no decode, the 160-record main/repeat lifecycle, partial capture, 94% rejection and 143-item acceptance, repeat-derived and zero tolerances, lossless RLE, cap/trailer behavior, fresh-memo bypass, points refusal, and fake-gcloud success/failure/corrupt readback/invalid metadata with normal return preserved.

The final package-test process used a 15 GiB address-space limit and peaked at 146196 KiB RSS. GPU visibility was empty; no actual torch weights were loaded. `bash -n` passed for all five shell scripts, both embedded Orchard Python programs compiled, and the place script's embedded delivery and BUILD bytes matched the final artifacts. Logs: [TESTS_FINAL.txt](out/TESTS_FINAL.txt), [TESTS_KIT.txt](out/TESTS_KIT.txt), [TESTS_FUNNEL.txt](out/TESTS_FUNNEL.txt), [TEST_RESOURCES.json](out/TEST_RESOURCES.json), [SCRIPTS_CHECK.json](out/SCRIPTS_CHECK.json).

The actual Orchard CPU namespace/staging/restore sequence, live Slurm resource admission, vnice script behavior, GPU model loading, full perception audit, real parity, real capture size, GCS credentials and throughput, pool return, and transfer pipeline remain unverified. The scripts gate GPU submission on the real CPU receipt; local doubles do not substitute for that receipt. SIGKILL can leave a truncated gzip: its bytes still upload, but it may need salvage before analysis. The 300-second streamed-command cutoff is handled by `nohup setsid` background work with a printed log path; remote completion must be checked in that log.

**Exact Orchard sequence; authored, not executed.** From the authorized transport session holding these scripts, run each line only after its stated prerequisite. Do not launch these commands from this build session.

```bash
ssh orchard 'bash -s' < orchard/o_place.sh
# Wait for the printed background log to report verified placement.
ssh orchard 'bash -s' < orchard/o_cpu.sh
# Wait for the CPU job to finish and /project/community/jjyeung/a1abb3a204ff8/a/c/CPU.json to pass.
ssh orchard 'bash -s' < orchard/o_check_sub.sh
# Wait for the GPU job recorded in /project/community/jjyeung/a1abb3a204ff8/a/8.txt to end.
ssh orchard 'bash -s' < orchard/o_fetch.sh
```

Placement embeds the exact delivery, refuses an existing destination, checks every outer/payload hash and the plan hash, and enforces the 50 MB placement limit. CPU submission uses preempt, eight CPUs, no GPU request, and the unchanged `a/5.py --package P --sequence P/a/6.py --results P/a/c`. GPU submission validates CPU entry-sequence/memory receipts, runs `3.py check --gpus 1 --time 05:00:00`, refuses any jjyeung job in general, then submits and writes `a/8.txt`. Fetch authenticates the pool receipts before and after `3.py fetch`, validates the inner return identity, and prints/saves CAPTURE and PARITY under `a/f`. One-use lock files prevent accidental repeated submissions; failures require operator review, not an automatic retry.

After placing the delivered pull script and verified CAPTURE receipt on trinity-3-30, run:

```bash
bash trinity/pull_capture.sh CAPTURE.json
```

It prints a stopped process-group ID. Register that group with the IO governor before the governor resumes it. The single pipeline reads `gcloud storage cat URI#GENERATION`, limits Internet ingress to 8 MiB/s, and streams directly through one `ssh trinity-2-28.ib` to `/scratch/jjyeung/orch_n30/cont_ops24_c/cap/0.gz`. It refuses an existing output and checks bytes and SHA256 remotely. It neither runs here nor integrates an invented governor API.

Rebuild and test locally:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
export TMPDIR="$PWD/work/tests"
/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/build.py
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s gpkg -p 'test_*.py' -v
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s kit2/kit/rerun2 -p 'test_*.py' -v
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s kit2/kit -p test_funnel.py -v
/scratch/jjyeung/envs/p1cpu/bin/python -B gt/adapter.py --inspect-only
```

**Retained files.** No files were deleted. `work/payload/` and `work/bundle/` hold inspection extracts; `work/tests/` holds retained fixture/build directories. The exhaustive path list is [out/RETAINED_FILES.txt](out/RETAINED_FILES.txt). These files are not delivery inputs. `out/TESTS_A.txt`, `TESTS_A2.txt`, `TESTS_A3.txt`, `TESTS_A4.txt`, and `GT_TEST.txt` are superseded test evidence; the current results are the FINAL/KIT/FUNNEL/resource/script files linked above. Supplied `parent/`, `hrem_ref/`, and `kit2/` were not edited.

**SHA256 inventory.** The table below covers every authored deliverable and retained top-level test log. [out/DELIVERABLES.json](out/DELIVERABLES.json) also records their sizes. `BUILD.json.files` covers every package file; `BUILD.json.payload_files` covers all 934 payload members, including unchanged inputs. [SHA256SUMS](SHA256SUMS) includes this report and the inventory JSON. No file purports to hash itself.

| File | SHA256 |
|---|---|
| `gpkg/build.py` | `60dbae5b2bbe6e43d69d786824861af2e525a2ba5a9c6a4fa7819acdf77e7720` |
| `gpkg/cpu_receipt.py` | `0d091589d5f19956203388ec7c2c421bd68a8809c56fe25db6cb7b55cfcceafa` |
| `gpkg/dispatch.py` | `fff23eea15abdd6070cfd280280f34235c210e5466c6e4f1552ee69950505c18` |
| `gpkg/fetch_auth.py` | `fcf45c0b1aae272be9e78b8b38b72c51d2259e62a3a64e379e74e67185f03e13` |
| `gpkg/join_capture.py` | `6dbd3c7bdccca49c1e3605d5359c255a424c9eb7b130a439eaceba2fe9a43e20` |
| `gpkg/runtime/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `gpkg/runtime/c.py` | `226f175892e4c77bfd839169845fa5264f7fb57bc297a732ed03f88abed34281` |
| `gpkg/runtime/p.py` | `017f1f259b87c3bc103782ae74ae0464090952486d5cfdbe7ce706295d27dd00` |
| `gpkg/runtime/q.py` | `d06923d8c80ed73380d467eb2eeae8d1e96ca9699f5d63e3683bd5cdf7121a50` |
| `gpkg/runtime/w.py` | `42de351e3950a0825c38621b1e24ebec81515bbec454fe252b96f62e98c9033f` |
| `gpkg/scripts.py` | `db36f12356eae4c5d8df2a9205df856978b91152ea73a1ad358e2c40c1ec9cb1` |
| `gpkg/test_gt.py` | `e4d636a017cf6123c4c7a7ad06fe868b25a08b8011bab8475472726d81129dbc` |
| `gpkg/test_package.py` | `df74d13fc7857e7f26ee4a84bec62eb4dcc462eaec224d1565ed415bfca52818` |
| `gpkg/test_runtime.py` | `68d550f81db4397618ee237a1060b8438a0171639c9acee2c7cb1b2b7255222f` |
| `gpkg/upload.py` | `a7433cb80a79319ea19a8fe404cabfe8c1ba712ed0c73d06e37d31af89498f2a` |
| `gt/INSPECTION.json` | `ee2a30bf54f9eaabae37f524c9c03a806c521e4c3480bff41d7be27d4301ad7c` |
| `gt/adapter.py` | `8af2813d99eb3e217fe7d62c1213291bdfc98a129bbb454ba887757320ca7397` |
| `orchard/o_check_sub.sh` | `4e1e71424afdce42a13b736b88c60cf645e0515783f30f288550b092fe96af38` |
| `orchard/o_cpu.sh` | `16b2cbdfb980d186dc254236f9af9f7c6cc316b7e91a083d05b63838e75f7b4d` |
| `orchard/o_fetch.sh` | `fe32f80892d27e915b6c98dc52f547bebed8a03ccf27ef0d76fb69d27b9f903e` |
| `orchard/o_place.sh` | `305f4cbdea7e50afef343e3e493f2b3d278297d82d95a76a4e6197ef08e8e6ad` |
| `out/BUILD.json` | `61d62413ebd1f2f9a9ae78cf85f35c63214cbcdc25f3056cc30d648918310b5f` |
| `out/BUILD_RUN.txt` | `a06679a16f15da8cca2a18442ec4bd4022225dee41b9e9025b586178dde2f7ed` |
| `out/GT_TEST.txt` | `752f33c1686391ac7b1221f0e78c7ce80dd856faa0af998776989f43df092d0f` |
| `out/GT_TEST_FINAL.txt` | `a5cfc171c6db66e247ecf7b8dff418878cebc97804eb4575aeb60211504b0f7b` |
| `out/RETAINED_FILES.txt` | `a9f7a530ccbd8694ba8840230f56edbc840ec235a88d53fdbeaecac50568308e` |
| `out/SCRIPTS_CHECK.json` | `869515fd5ec66e6f8b2b5d3620862bb7367aca26563a0f8292172cddf0c8d15f` |
| `out/TESTS_A.txt` | `b1b74816ea4ed7e9c64bc5f7fe723d836512f83e06b8e6463781e8f8c10a6812` |
| `out/TESTS_A2.txt` | `fe922064b2aa89f38beeb2091ae219bba71d43dc94632809973bc0dea6993e0c` |
| `out/TESTS_A3.txt` | `864619901cb73c81f06ab6e7a1308e3878f01ea6ed6565bd0b7b649a834fc37e` |
| `out/TESTS_A4.txt` | `147b682c5be3e15aede2b70ee364ed46d31c59ecd363b5c299e2c11ca81ea112` |
| `out/TESTS_FINAL.txt` | `cad718725556f4d8ac21be234630eb2deecbeb522559bae7723cd1767eaa480d` |
| `out/TESTS_FUNNEL.txt` | `27d5987f846d1a9a6472382f388916a068a47f08213d13b9608db547468cf80d` |
| `out/TESTS_KIT.txt` | `310f27a6a286eb8a918af2ecbdd97b2f627dc8625ce5828ae9bf29082da735ed` |
| `out/TEST_RESOURCES.json` | `d010f36d93c2a54f48abc6a1af408500863d41eadcce7b10def1680f1df262e5` |
| `out/delivery.tgz` | `d0dac81b82995c8ed756c99a498cb85cdb73d9f2e7cf280fcca4dcb69def0187` |
| `trinity/pull_capture.sh` | `019f97688125fd7ca3b99d47adc11611b4f753fac3c6fb682e3c3ec255acbeaa` |

The package contains these sealed files:

| Package file | SHA256 |
|---|---|
| `0.json` | `87ebf9a75c68609add0d7847e3525fe02b1b0a602aaa269ea2ee4b1480d2c55c` |
| `0.tgz` | `d7e65fb68490352588fb34a11a056b94ead6c16bdba3e84eaf65f1bd23238a33` |
| `3.py` | `53f53bf2ff2b772eda193b067e5a166a988a343745f89a54cb82731ab120a99d` |
| `BATCH.sh` | `40ef4162fb119bd5274a4fc3ddaa20377d23b01a9a1ab6a939647f94d679a07a` |
| `CONFIG.json` | `87ebf9a75c68609add0d7847e3525fe02b1b0a602aaa269ea2ee4b1480d2c55c` |
| `INPUTS.example.json` | `1f0e23861cc1814705c214a2dc93cc105c63e3c30be0adc22bf774dca9b6066d` |
| `PACKAGE.json` | `387313184359d90a178d144bbf1fc98b5723d6866c4c676dbe88169789900634` |
| `SUBMIT.cmd` | `fc7bd3c2354fcbdf495df37f09b69b83ccd950ca2db1997519192f3ca410b23d` |
| `a/1.json` | `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207` |
| `a/5.py` | `a09deab25695cab459c0b882978746b657c12230c2ce5ee640dd4801304e5674` |
| `a/6.py` | `fff23eea15abdd6070cfd280280f34235c210e5466c6e4f1552ee69950505c18` |
| `a/7.py` | `fcf45c0b1aae272be9e78b8b38b72c51d2259e62a3a64e379e74e67185f03e13` |
| `a/9.py` | `0d091589d5f19956203388ec7c2c421bd68a8809c56fe25db6cb7b55cfcceafa` |
| `a/export.json` | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
