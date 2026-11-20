The CPU job is ready to upload. No remote job has been submitted. Its aggregate result must remain FAIL while the adopted kit lacks an exit-archive GCS route (E102); all other checks have passed against a local sink.

Upload these six files beneath `/project/community/jjyeung/okh7/x_22c714e1/`. Every listed SHA256 authenticates the complete file. `k.tgz` contains the full newly sealed N kit with GO=false; its copier and archive bytes match N_GO.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e2/e2.sh | 1414 | `2b45d52c99a025607c9b961a41074abf93246251c23b287cb9e3fa250d2e0c6a` |
| e2/e2.py | 10583 | `4a806c64097921accca3eff658cb990f70c2b03bc6a0f7a08da4f51790d5ed52` |
| e2/observe.py | 1762 | `50de6431ac2f1564ee63e687d90b95e8a779bbbb9e0685eabdff533090813182` |
| e2/run.sh | 282 | `df2d5cf38797f606be97d031a47c8a580d4c58cd8dd86206c18c819347e2550f` |
| e2/k.tgz | 3865574 | `9dca770964ddffb216fa9d0c26e4dbdf76c8da67d9a82767683f7a60e304db26` |
| e2/pins.json | 404 | `b9cb6e1f82228d3097aef52cea1fec2443b6d3f5dbdffd19e14a5606f8bf1111` |

On Orchard, submit exactly:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e2/e2.sh"
```

Record the returned numeric job ID. The file requests partition `preempt`, one CPU-only task, four CPUs, 16G and one hour. Its fixed name is `a15_cot_apf482d730ca91`. Slurm stdout and stderr go to `/tmp/q_e2_%j.log` and `/tmp/q_e2_%j.err`; the body redirects both streams to node-local files. The job writes only `X/o/<job>/E2.json` and `logs.tgz` on the real filesystem, using `.part` names during replacement.

While held, n_ops8 must mint 104 fresh sessions in its chosen bucket, then install `X/n_s/sess_<job>.json` with directory mode 0700 and file mode 0600, both owned by the submitting user. The JSON maps each exact object name to its fresh resumable session URL. Never print the file or its values. The required names are all 26 values from the new `k/y.json`, each followed by `.j<job>.part00-of-04` through `.j<job>.part03-of-04`. `SESSION_NAMES.template.list` spells out all 104 names; replace `<job>` with the actual job ID. No exit-archive label exists. Only the m100, ck00 and ckstop groups are consumed by this fixture, but prepare requires the full set.

After n_ops8 confirms installation, the lane can run `scontrol release <job>`. A failed allocation must use a new job ID and fresh sessions; do not reuse completed resumable sessions.

The job first probes `unshare -Urm` and a 1 MiB tmpfs; E01 means either is unavailable. It verifies the staged bundle pins, every sealed member, BUILD's manifest hash and the kit's own checker. It then creates two 3 MiB local payloads and an exit archive. A private 16 MiB tmpfs covers X; the sessions are copied there before dd fills it and df records zero available bytes. The same real pc.sh/pc.py/gc.py/o.py sources execute from the verified local kit. A separate observer forwards the unmodified HTTP response bytes and saves only size, crc32c, md5Hash, name and generation. The observer wraps the gc.py invocation so the sealed writer still performs the request, hashing and receipt checks. It supplies no replacement network implementation on Orchard.

The fixture invokes the launch's final-copy command while its files are static and X is full. The original small publisher remains alive. After tmpfs grows to 64 MiB, the job waits up to 660 seconds for that same publisher to resume; the actual 600-second interval is unchanged. This proves the copier with synthetic payloads and real sessions, not admission or training. The unchanged 50 GiB local spool reserve still applies; insufficient local free space produces a failed check.

`E2.json` lists PASS/FAIL per check and one row per part: exact name, bytes, locally computed SHA256 and the final response fields returned by GCS. It also retains the copier's local receipt fields. `logs.tgz` contains screened bounded logs and receipts, never sessions or tokens. E102 records the missing exit-archive route; the separate recovery check verifies that o.tar reaches X after space returns. An allocation that cannot publish its final report retains it under its node-local q_e2_<job> directory.

On trinity-3-30, n_ops8 can validate the exact GCS generations using the separately supplied local `readback.py`. Copy the small E2.json report to node-local scratch using the lane's authorized channel. In the credentialed shell on that node, run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E2.json --bucket BUCKET
```

Use the bucket n_ops8 selected when minting the sessions. The reader obtains an access token through gcloud without displaying it and passes it to curl through stdin. It reads serially at at most 8 MiB/s, pins the returned generation, and compares name, size, SHA256, md5Hash and crc32c. It prints only names, sizes, hashes and PASS/FAIL. Readback uses the full object names in E2.json; it does not use or expose session URLs. For a restored archive, concatenate part00 through part03 in that order. `readback.py`, this usage file and the name template are operator-side helpers, not part of the six-file Orchard upload list.

The operator-side readback helper SHA256 is `4430043bc8bc7cbfd193336bba3754e94607e1e3889293aef8de4b602769293b`.
