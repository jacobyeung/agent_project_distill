# Time and storage

The requested limit is `05:00:00` (`SIZING.json`, `FAMILY.json`). The inherited measured estimate needs 12259.5 seconds with 4290.8 seconds of margin (`SIZING.json`; original measurements are listed in its `sources`). The coordinator reserves 300 seconds for publication (`guard_kit/worker.py`). Candidate duration and live transfer rates remain unmeasured.

The estimate covers shared staging, both exports, both geometry preparations, historical proof and the candidate arm. Canary rows are reused. It uses measured native item times rather than assuming that removing the scripted arm halves model time (`SIZING.json`).

The provisional job disk estimate is 250290030222 bytes (`SIZING.json`). The unchanged stager also requires its free-space reserve before copying (`guard_kit/sj/orch_cd/evalx/work/milestone/orchard_stage.py`). Actual candidate `.done` bytes must replace the reference-size assumption before launch; a larger export can invalidate the estimate.

Cloud publication has bounded subprocess deadlines, and a failed cloud attempt retains the verified result-pool copy (`guard_kit/transport.py`). The receipt acknowledgement cannot wait indefinitely for cloud publication. The reserve is provisional; live pool latency and archive compression time remain unmeasured.

Local archive sizes are recorded in `CODE_MANIFEST.json`, `INPUT_MANIFEST.json`, and `candidate_m50/CLOSURE.json`. The local build cap is 6000000000 bytes, and measured use is recorded in `BUILD_SIZE.json`. No large runtime, base-model or real export archive was expanded in this build.
