The CPU job is ready to upload. All 14 checks and the aggregate result pass in the local dry run, including archive_while_full. No remote job has been submitted; real-session GCS validation remains for the held job.

Upload these six files beneath `/project/community/jjyeung/okh7/x_22c714e1/`. Every listed SHA256 authenticates the complete file. `k.tgz` contains the full newly sealed N kit with GO=false; its copier and archive bytes match N_GO.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e2/e2.sh | 1474 | `7df901f392c6efc84f5208b86c72ff262e34d484391c509791763810cc32ac26` |
| e2/e2.py | 11483 | `bf01d22f6aa091153cdbf809ec467d7f6e1c4c99dcb25ef2e704ee87e2a94746` |
| e2/observe.py | 1844 | `c6def00dd6bb8b5757774eac43c5683b31eb3a6ebe1ecef7cefd1d2b2a982eb5` |
| e2/run.sh | 282 | `df2d5cf38797f606be97d031a47c8a580d4c58cd8dd86206c18c819347e2550f` |
| e2/k.tgz | 3866567 | `130d0ea2ba9337c01a5c9c7a7bfd5dc9ca997c65e8c88898d32af3f4ec490df7` |
| e2/pins.json | 325 | `0de1c49d2f502b9c633c12d8386d239fe271813d18fadf1620a238bd717778fe` |

On Orchard, submit exactly:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e2/e2.sh"
```

Record the returned numeric job ID. The file requests partition `preempt`, one CPU-only task, four CPUs, 16G and one hour. Its fixed name is `a15_cot_apf482d730ca91`. Slurm stdout and stderr go to `/tmp/q_e2_%j.log` and `/tmp/q_e2_%j.err`; the body redirects both streams to node-local files. The job writes only `X/o/<job>/E2.json` and `logs.tgz` on the real filesystem, using `.part` names during replacement.

While held, n_ops8 must mint 108 fresh sessions in its chosen bucket, then install `X/n_s/sess_<job>.json` with directory mode 0700 and file mode 0600, both owned by the submitting user. The JSON maps each exact object name to its fresh resumable session URL. Never print the file or its values. The required names are all 27 values from the new `k/y.json`, each followed by `.j<job>.part00-of-04` through `.j<job>.part03-of-04`. `SESSION_NAMES.template.list` spells out all 108 names; replace `<job>` with the actual job ID. The exit-archive label is `o`, with base name `q9/22c714e1/469ddece_o.tar`; its four names are `q9/22c714e1/469ddece_o.tar.j<job>.part00-of-04` through `.part03-of-04`. The fixture consumes m100, ck00, ckstop and o (16 parts), but prepare requires all 108 names, including the four archive names.

After n_ops8 confirms installation, the lane can run `scontrol release <job>`. A failed allocation must use a new job ID and fresh sessions; do not reuse completed resumable sessions.

The job first probes `unshare -Urm` and a 1 MiB tmpfs; E01 means either is unavailable. It verifies the staged bundle pins, every sealed member, BUILD's manifest hash and the kit's own checker. It then creates two 3 MiB local payloads and an exit archive. A private 16 MiB tmpfs covers X; the sessions are copied there before dd fills it and df records zero available bytes. The same real pc.sh/pc.py/gc.py/o.py sources execute from the verified local kit. A separate observer forwards the unmodified HTTP response bytes and saves only size, crc32c, md5Hash, name and generation. The observer wraps the gc.py invocation so the sealed writer still performs the request, hashing and receipt checks. It supplies no replacement network implementation on Orchard.

The fixture invokes the launch's final-copy command while its files are static and X is full. Each final pass handles the stop checkpoint first, then exports (including ordinary checkpoint exports), then logs, then creates and uploads the exit archive last. A pending stop blocks the archive. The final loop retries unfinished destinations for up to 140 seconds inside pc.sh's 150-second timeout; production intervals remain unchanged. The original small publisher remains alive. After tmpfs grows to 64 MiB, the job waits up to 660 seconds for that same publisher to resume; the actual 600-second interval is unchanged. This proves the copier with synthetic payloads and real sessions, not admission or training. The unchanged 50 GiB local spool reserve still applies; insufficient local free space produces a failed check.

`E2.json` lists PASS/FAIL per check and one row per part: exact name, bytes, locally computed SHA256 and the final response fields returned by GCS. It also retains the copier's local receipt fields. `logs.tgz` contains screened bounded logs and receipts, never sessions or tokens. The required archive_while_full check verifies all four archive parts, their receipts, the full archive SHA256, embedded RESULT.json and zero available bytes in X. The final_order check requires stop, exports, logs, o. The separate recovery check verifies exact o.tar bytes at X after space returns. An allocation that cannot publish its final report retains it under its node-local q_e2_<job> directory.

On trinity-3-30, n_ops8 can validate the exact GCS generations using the separately supplied local `readback.py`. Copy the small E2.json report to node-local scratch using the lane's authorized channel. In the credentialed shell on that node, run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E2.json --bucket BUCKET
```

Use the bucket n_ops8 selected when minting the sessions. The reader obtains an access token through gcloud without displaying it and passes it to curl through stdin. It reads serially at at most 8 MiB/s, pins the returned generation, and compares name, size, SHA256, md5Hash and crc32c. It prints only names, sizes, hashes and PASS/FAIL. Readback uses the full object names in E2.json; it does not use or expose session URLs. The reader requires 16 parts and also concatenates the four o parts to verify the complete archive byte count and SHA256. For restoration, concatenate part00 through part03 in that order; RESULT.json is inside this gzip-compressed tar. `readback.py`, this usage file and the name template are operator-side helpers, not part of the six-file Orchard upload list.

The operator-side readback helper SHA256 is `c4f9fcd9728d912c947e994552d22190d4db5e28104f5de4ae68a715e36923c3`.

Budget at most 50,000,000 bytes for the exit archive. Its input caps retain 40,000,000 log-tail bytes and at most 9,000,000 metadata bytes, including RESULT.json; tar/gzip overhead fits the remaining allowance and the encoded output is checked against the cap. The local full-X fixture produces 220 bytes. No real-job o.tar exists in the inspected d173* scratch directories, so no real-job size is asserted.
