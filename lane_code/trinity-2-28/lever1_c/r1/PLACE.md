The delivery is ready for re-review. Placement and submission wait for that review.

The lane can place the depth package at `/project/community/jjyeung/a99a83187be42`. This builder has not placed, submitted, or fetched anything.

| Artifact | Bytes |
| --- | ---: |
| `out/delivery.tgz` | 3,490,726 |
| Expanded inner payload (32 MiB limit) | 29,515,891 |
| Installed package files | 3,685,443 |
| Installed `BUILD.json` | 52,685 |
| Streamed `orchard/o_place.sh` | 4,729,697 |
| Conservative delivery + installed files + descriptor | 7,228,854 |

Delivery SHA256: `672076c0edda7703c22500f4c9b3ce1b7f6e6421f23b3cc5d2174eef5b8115dd`.

The job uses `a15_cot_apa99a83187be42`, general, `--gres=gpu:1`, `--cpus-per-task=16`, `--mem=200G`, and `--exclude=orchard-community-4`. The worker checks for an H100 before model loading. The inherited submission checker requires a minimum 40-minute allocation. The worker has a 30-minute cap and a deadline 270 seconds before allocation end; termination and reaping allow at most another 25 seconds. Staging and work share a deadline 240 seconds before allocation end. Capture publication stops 90 seconds before allocation end, normal publication stops 10 seconds before it, and the failure-receipt fallback stops two seconds before it. Every transfer uses the remaining time in its window. The forecast is 16.75 worker minutes and 30.75 minutes including unmeasured staging/publication allowances.

After re-review, run these commands from the authorized lane holding this directory. Wait for each background script's printed log to report completion before starting its dependent step. Check job status at most once per minute. The scripts refuse an existing destination and use one-use submission locks; do not retry a killed or failed command automatically.

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
sha256sum --check --quiet SHA256SUMS
ssh orchard 'bash -s' < orchard/o_place.sh
# Wait for verified placement.
ssh orchard 'bash -s' < orchard/o_cpu.sh
# Wait for the CPU job and its authenticated CPU.json receipt to pass.
ssh orchard 'bash -s' < orchard/o_sub_hand.sh
# Wait for the GPU job to finish.
ssh orchard 'bash -s' < orchard/o_fetch.sh
# Wait for the authenticated fetch into the package's a/f directory.
mkdir -p returned
ssh orchard 'bash -s' < orchard/o_get.sh | pv -q -L 8000000 > returned/receipts.tgz
tar -xzf returned/receipts.tgz -C returned
```

`returned/4.json` is the depth upload receipt: URI, immutable generation, SHA256, size, and verification status. `returned/5.json` contains camera/scale parity. The small `returned/0.tgz` contains normal job receipts. Failed camera/scale parity does not suppress the depth return.

Retrieve the depth gzip through the lane's governed stream, using `returned/4.json`. Expected compressed size is 40 MB; the conservative budget is 80 MB and the enforced cap is 1,000,000,000 bytes. The supplied transport uses one GCS stream, an 8 MiB/s throttle, and the direct InfiniBand destination on trinity-2-28. It creates only `r1/returned/0.gz`, refuses overwrite, and verifies bytes and SHA256.

From the authorized transport session on trinity-3-30, with the script and receipt available locally:

```bash
bash orchard/pull_depth.sh returned/4.json
```

This prints a stopped process-group ID. The governor must register and resume that group before any bytes move. No governor API is assumed. The builder did not run this script. Internet ingress shares the user's cluster allowance; coordinate it with other streams.

After the authenticated return lands on this node:

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B relift.py \
  --depth returned/0.gz --receipt returned/4.json --out out/RELIFT.json
```

The CLI first checks all 150 items at the registered 0.00 m printed-gap tolerance. Each of the two operands inherits its item's gap-match flag; at least 95% must match. Failed parity writes a STOP result and evaluates no intervention cells. Missing depth writes `depth return missing` and exits successfully. `--half-only` explicitly tests float16-only sensitivity under the same gate; the default reconstructs the exact served depth from float16 plus its lossless residual.

Rebuild and CPU-test locally:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build_depth.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_all.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/check_imports.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
```

`build_depth.py` authenticates the exact T1 delivery and capture, preserves the 270 retained serving/evaluator source files byte for byte under opaque paths, and reseals the worker, plan, operator, batch bundle, descriptors, and scripts. It reads the named sibling inputs and writes under `r1/`. The package authenticates the existing Orchard archives once and extracts only the required roots. Segmentation weights, receipt, source, and selector inputs have no pins, preparation settings, or extracted files. Required archive paths and file paths are already opaque; no external alias is needed.

The CPU rehearsal runs twice and scans all eight output files by name, raw content, and JSON-decoded string against the deny-list. The item copy retains exact `a0` source bytes; the copied dispatcher uses opaque source storage and passes the numeric entry test. `out/CPU_ENTRY_STUB.json` records every scanned output file and hash.

The built delivery passes 28 CPU tests and both fresh-process import/admission checks. `out/FIX_CHECKS.json` records the actual staging test, all-asset label scan, 150 exact prompt/RGB bindings, source hashes, naming scan, and simulated transfer/worker deadlines. Staging uses the production function and extractor with tiny local substitutes for external archives. No live Orchard job ran.

JSON transport uses an `a0` envelope containing the exact original bytes in hexadecimal. The numeric launchers, import loader, placement/fetch scripts, and local relift CLI decode it. Package pins authenticate stored bytes; preparation and resource checks authenticate the original decoded bytes. Job-owned metadata and capture records use this transport. The runtime environment archive retains its installed third-party library layout.
