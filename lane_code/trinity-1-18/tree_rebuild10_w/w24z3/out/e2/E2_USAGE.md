The CPU job is ready to upload. No remote job has been submitted. Its local dry run passes every required check, including archive_while_full. Real GCS validation still requires the held CPU job and generation-pinned readback.

Upload these six files beneath `/project/community/jjyeung/okh7/x_22c714e1/`. Every listed SHA256 authenticates the complete file. `k.tgz` contains the full newly sealed N kit with GO=false; its copier and archive bytes match N_GO.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e2/e2.sh | 1414 | `b0fae92daadb38bc96449e7a68e09654f0918d26f99bf2e458ddee2e79ae4e61` |
| e2/e2.py | 11029 | `1959f4523f78c8a3d6c73b3320dc961fc2975f14f25b6c2ccc2918c054b7a6a4` |
| e2/observe.py | 1762 | `50de6431ac2f1564ee63e687d90b95e8a779bbbb9e0685eabdff533090813182` |
| e2/run.sh | 282 | `df2d5cf38797f606be97d031a47c8a580d4c58cd8dd86206c18c819347e2550f` |
| e2/k.tgz | 3865957 | `01883fc25ad7c4215f74cd9eeea31cad5423b640bb7d2cdce04f80201c4ad7bb` |
| e2/pins.json | 404 | `04d401fc672a2dd327c541d1cf69a8dc0184d55b13229ef4238a8fbefe52b050` |

On Orchard, submit exactly:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e2/e2.sh"
```

Record the returned numeric job ID. The file requests partition `preempt`, one CPU-only task, four CPUs, 16G and one hour. Its fixed name is `a15_cot_ap8d3ce49b27f1`. Slurm stdout and stderr go to `/tmp/q_e2_%j.log` and `/tmp/q_e2_%j.err`; the body redirects both streams to node-local files. The job writes only `X/o/<job>/E2.json` and `logs.tgz` on the real filesystem, using `.part` names during replacement.

While held, n_ops8 must mint 108 fresh sessions in its chosen bucket, then install `X/n_s/sess_<job>.json` with directory mode 0700 and file mode 0600, both owned by the submitting user. The JSON maps each exact object name to its fresh resumable session URL. Never print the file or its values. The required names are all 27 values from the new `k/y.json`, each followed by `.j<job>.part00-of-04` through `.j<job>.part03-of-04`. `SESSION_NAMES.template.list` spells out all 108 names; replace `<job>` with the actual job ID. The exit archive uses label `o`, whose base name is `q9/22c714e1/469ddece_o.tar`. The fixture consumes m100, ck00, ckstop and o (16 parts); prepare requires all 108 names and refuses a set missing the four o parts.

After n_ops8 confirms installation, the lane can run `scontrol release <job>`. A failed allocation must use a new job ID and fresh sessions; do not reuse completed resumable sessions.

The job first probes `unshare -Urm` and a 1 MiB tmpfs; E01 means either is unavailable. It verifies the staged bundle pins, every sealed member, BUILD's manifest hash and the kit's own checker. It then creates two 3 MiB local payloads and an exit archive. A private 16 MiB tmpfs covers X; the sessions are copied there before dd fills it and df records zero available bytes. The same real pc.sh/pc.py/gc.py/o.py sources execute from the verified local kit. A separate observer forwards the unmodified HTTP response bytes and saves only size, crc32c, md5Hash, name and generation. The observer wraps the gc.py invocation so the sealed writer still performs the request, hashing and receipt checks. It supplies no replacement network implementation on Orchard.

The fixture invokes the launch's final-copy command while its files are static and X is full. The original small publisher remains alive. After tmpfs grows to 64 MiB, the job waits up to 660 seconds for that same publisher to resume; the actual 600-second interval is unchanged. This proves the copier with synthetic payloads and real sessions, not admission or training. The unchanged 50 GiB local spool reserve still applies; insufficient local free space produces a failed check.

`E2.json` lists PASS/FAIL per check and one row per part: exact name, bytes, locally computed SHA256 and the final response fields returned by GCS. It also retains the copier's local receipt fields. `logs.tgz` contains screened bounded logs and receipts, never sessions or tokens. archive_while_full is a required PASS: all four archive parts must have verified receipts while X has zero free bytes, and RESULT.json must be inside the exact o.tar bytes. The separate recovery check verifies that o.tar reaches X after space returns. An allocation that cannot publish its final report retains it under its node-local q_e2_<job> directory.

On trinity-3-30, n_ops8 can validate the exact GCS generations using the separately supplied local `readback.py`. Copy the small E2.json report to node-local scratch using the lane's authorized channel. In the credentialed shell on that node, run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E2.json --bucket BUCKET
```

Use the bucket n_ops8 selected when minting the sessions. The reader obtains an access token through gcloud without displaying it and passes it to curl through stdin. It reads serially at at most 8 MiB/s, pins the returned generation, and compares name, size, SHA256, md5Hash and crc32c. It prints only names, sizes, hashes and PASS/FAIL. Readback uses the full object names in E2.json; it does not use or expose session URLs. The reader requires all 16 parts and archive_while_full=PASS. It also concatenates the four archive parts in order and verifies the complete o.tar size and SHA256 from E2.json. RESULT.json is inside that archive; its node-local copy also publishes to X/o/<job>/RESULT.json. `readback.py`, this usage file and the name template are operator-side helpers, not part of the six-file Orchard upload list.

The operator-side readback helper SHA256 is `ac718897b11db750f3c1bec6c57ccfe6202c1d90dfd752ecde2e0cd42eda5577`.
