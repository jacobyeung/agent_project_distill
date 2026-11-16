# Time and storage

The requested wall limit is `05:00:00` (`SIZING.json`). The estimated need is 12259.5 seconds, with 4290.8 seconds of margin (`SIZING.json`).

The estimate includes shared staging, another export transfer and header check, complete geometry preparation for both exports, measured native item time, the selected proof items and conservative load/parity residuals. Canary rows are reused. The accepted native item total is 6378.3 seconds (`SIZING.json`, sourced from `/scratch/jjyeung/orch_n30/b01_d0guard/work/ret544/native/R1.json`). Scripted records do not measure a second model decode, so halving the paired wall time is unsupported.

The provisional disk estimate is 250290030222 bytes (`SIZING.json`). It includes retained archives, expanded files and reserve. Candidate size and free job-local space must be checked before staging. No large runtime, base or export archive was expanded here.

The local build cap is 6000000000 bytes (`SIZING.json`). Final measured use is recorded in `BUILD_SIZE.json`. Live Orchard free space, transfer throughput and candidate decode duration were not checked.
