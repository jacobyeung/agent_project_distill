The kit is built and locally validated. No Orchard job was submitted; real-engine agreement remains pending.

- Return CONFIG accepts prepare --pool; default: /project/community/jjyeung/okh7/x27ret.
- Before staging, a subprocess writes/fsyncs/reads/hashes 4 MiB in <pool>/<token>/.wtest, then removes that file only. Any error or >60 s refuses the job.
- Pool operations lock and enforce total use below 100 MB. Proof returns stay below 20 MB; production compressed packets stay below 90 MB.
- The job builds locally and independently verifies pool and GCS returns. Either verified channel satisfies transport; computational failure still fails the job.
- GCS destination: gs://cmu-gpucloud-jjyeung/q8/x27r/<token>/, using CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud.
- Uploads have deadlines and generation-pinned SHA256 readback. RETURN_RECEIPT.json/JOB.log record generations, hashes, partial failures and verified channels.
- Fetch tries pool then GCS, streams stdout directly to the Trinity lane at 8 MB/s, and stops before packets >=20 MB for governor registration.
- Proof requests one H100, general, 16 CPUs, 200G, 02:00:00; production requests the same resources for 06:00:00. Both keep real card checks.
- Phase A runs real staging/processor/288-video planning on Orchard, first-20 prompt parity, and 14 official items through the fake engine only.
- The 14-item allocation covers all eight subtypes: two per non-direction task, two easy direction, one medium and one hard. Two per subtype would require 16.
- Phase B starts only after Phase A passes, in a fresh interpreter. It uses unchanged direct/r3/r5 and runtime_2 evaluator code with the step-544 export.
- Only smoke_items=20 changes reader settings; the worker sort order must reproduce accepted job 169526's first 20 main IDs.
- All 20 reconstructed frame receipts match accepted frames/0.json hashes. The unchanged accepted puller needs 576 PNGs from the k6tk store.
- Phase B requires 16 ID and two pixel checks. It compares prompt bytes, 16 accepted prompt-ID hashes, ON16k token IDs/raw text, and budget answers/scores.
- PHASE_B.json reports item-level equality, exact counts and paired per-arm means. Real generation differences are reported; prompt/parity differences fail.
- Tests: 78 passed in 61.47 s. The separate local two-phase proof passed: 14 official + 20 dev items; archive 222,537 bytes.
- Local engines/processors/models/media/staging/namespace use fixtures. The accepted puller runs against a miniature store. GCS commands are mocked in tests.
- Observed coverage.py: 2631/4109 statements (64.03%) across 42 imported job/parity modules; the line audit also includes the Phase B/puller subprocess trace.
- LINES.md leaves 2,986 missing lines, including 2,971 gaps; no Orchard lines or every-line guarantee are assumed.
- Stdlib tracing covers pool helpers, frame puller, chain, adapters and worker. A bounded final trace sidecar falls back to the packet snapshot if unavailable.
- DIFF.md lists this pass's source changes and all package hashes. direct.py/vendor/puller bytes remain accepted; one evaluator file carries the shared official filter.
- package.tar: 116 files, 12,503,040 bytes. Two builds matched; all member hashes/metadata and 75 Python compilations passed.
- KIT_SHA256: f42aa1a4aec049e03a321e88ccd8a5004a3e95963b08f18242db625bdec95684
- Pending: real Slurm/H100/bwrap, credentials/returns, four export parts, 288 videos, processor/k6tk/vLLM parity, final Orchard trace union and two-hour feasibility.

Operator preparation from work/:
```bash
TOKEN=$(python3 -c 'import secrets;print("p"+secrets.token_hex(5))')
kit/.venv/bin/python kit/launcher/orchard_launcher.py prepare --mode proof --pool /project/community/jjyeung/okh7/x27ret --token "$TOKEN" --destination "kit/build/$TOKEN"
```
PROOF_JOB.md supplies exact GPU stdin submission, UTC polling, pool/GCS fetch, governor registration, lines_report and production commands.
No SSH, submission, Git or network calls ran during this build. Only local authorized .wtest files were removed.
