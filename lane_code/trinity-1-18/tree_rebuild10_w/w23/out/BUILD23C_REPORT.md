PASS: kit-only GPU guard repair validated. Production GO=false.
The in-view guard prints one flushed JSON diagnostic, accepts at least 75 GiB, and refuses missing CUDA, zero devices or failed property queries with E42.
The diagnostic records torch version, CUDA availability/count, CUDA_VISIBLE_DEVICES, device name/memory bytes, and /dev/nvidia0 plus /dev/nvidiactl existence.
Opaque key meanings and the exact build-24 generator patch are in out/GUARD_PATCH.md; out/GUARD_PATCH.diff contains the two generator hunks.
Source: work/build21/kit.py; emitted guard: work/build21/kits/q/b/g.py. Resource metadata also declares 75 GiB.

The guard runs inside bwrap, after tk_bwrap constructs BW; q/job.sh reaches it through bootstrap and decoded k/j.json.
The view matches P: --dev-bind /dev /dev exposes host NVIDIA nodes; top-level read-only binds/symlinks preserve host driver-library paths.
No bind change was needed. Source audit: work/build23c/VIEW_AUDIT.json; P reference: ext/pwrap/b/c.sh:339-366.
Job 173076 did not record its cause; this CPU check cannot establish its CUDA visibility or device-memory value.

Before/after: 85,520,809,984 bytes refuses/passes; no CUDA refuses/refuses; 70 GiB refuses/refuses.
Guard tests: 9 passed, including exact/below threshold, zero count, property failure and missing-node diagnostics; all 12 guard statement lines covered (work/build23c/GUARD_TESTS.json).
Regression tests: 67 passed across kit, naming and resolver suites; 76 tests total (work/build23c/TEST_COUNTS.json, SUITES.json).
Decoded scan: PASS, 76663 strings (work/build23c/SCAN.json).
Look-ahead: view PASS; CPU guard E42 with diagnostic; stubbed 80 GB-class guard PASS; native entry reaches R1_PROOF_FRAME_HOST_REQUIRED.
The look-ahead uses the kit own decoded config unchanged. Only the guard uses stubbed torch; the native entry uses real CPU torch and the inherited empty/prefixed mounts.
That refusal remains the frame-host boundary; no production proof or capacity rerun is claimed (work/build23c/LOOKAHEAD.json).

Tree seal unchanged: 5b349b1819bc7dca1010feb81da2e7b1326f9992aff913416981b932cdd58c6c (out/TREE_SEAL.json; work/build23c/INTEGRITY.json).
Kit q seal: a258d7e7383411eb010055a172d2fef799bb43ec16eb1da0e2b9a9142709e3d6 (work/build21/kits/q/SHA256SUMS.txt).
Upload diff versus 67ce92f6: 3 files, 3391 bytes: q/b/g.py, q/SHA256SUMS.txt and q/BUILD.json (out/UPLOADS_NEW_23C.json).
All sealed-tree bytes, config, resolver identities, admission, legality, removals, P opener rows, step-544 lineage and DEFERRED behavior remain unchanged.
Existing packages are byte-identical; superseded generator, guard and metadata are retained in attic/build23c (work/build23c/START.json).
Package seal, byte count, SHA-256 and stream verification: work/build23c/DELIVERY.json, external to avoid circular hashing.
The requested before/after comparison is retained as regression evidence. No upload, submission, network or GPU execution occurred.
