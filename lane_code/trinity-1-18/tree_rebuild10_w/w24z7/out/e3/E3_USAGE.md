E3 is ready for the lane's held CPU submission. All 16 checks pass against the strict offline sink. No real GCS throughput has been measured, and no remote job was submitted by this build.

Upload these six files below `X=/project/community/jjyeung/okh7/x_22c714e1`. Every upload is below 5,000,000 bytes. The bundle contains the complete sealed N kit with GO=false.

| Destination relative to X | Bytes | SHA256 |
|---|---:|---|
| e3/e3.sh | 1617 | `cf71474f4d7b07b192978612caf558d435275026cf47f833d056dd073ed52887` |
| e3/e3.py | 13250 | `06d703bc316a7c20987638118d58cbb879c77a1d1960c548942855c9cd2c511b` |
| e3/observe.py | 1490 | `a4efef1acbb0999794fd0865711748f3a31ede2318df49577c270bdfbb5f5721` |
| e3/run.sh | 282 | `98a27aae6fc5d467825aaa9a6be62d1732334f4f03bb7fb1ad85ddae30f1cc73` |
| e3/k.tgz | 3870443 | `408766f0758faf572f2e69559d6a159eaba5fbd4807ebef148040eddc2b21e65` |
| e3/pins.json | 325 | `f84b0199ac3b1213d38a24600d0a4f8afd5b1ba4718684ae48a894f201d34eb4` |

Submit and keep the job held:

```bash
X=/project/community/jjyeung/okh7/x_22c714e1
sbatch --hold "$X/e3/e3.sh"
```

The job name is `a15_cot_ap2da56272b86d`. It requests preempt, four CPUs, 16G, one hour, and no GPU. Its node-local log records SLURM_TMPDIR and `df -B1` before staging. JSON records that directory and its free bytes too.

While held, mint 108 fresh sessions for this exact job ID and install `X/n_s/sess_<job>.json`: a complete object-name-to-resumable-URL JSON mapping, directory 0700, file 0600, both owned by the submitting user. Replace `<job>` in SESSION_NAMES.template.list with the returned numeric ID. Never print the values. Copying and validating sessions precedes filling the private tmpfs. Each cache use revalidates the set, ownership, permissions, and JSON. Each allocation needs fresh names and sessions.

After installation, release only this CPU test:

```bash
scontrol release <job>
```

Budget under one minute to submit held, approximately 5–10 minutes to mint and install 108 sessions, and under one minute to release. These are operator planning estimates; queue time is unknown. The allocation limit is 60 minutes. The fixture's explicit final pass is bounded to 240 seconds, and publication recovery can wait 660 seconds. A slow transfer produces FAIL rather than an invented rate.

The job verifies pins, manifest, BUILD and the kit checker. It generates a 3 MiB export and a 2 GiB random stop-checkpoint-like payload on node-local storage. It mounts a private 16 MiB tmpfs over X, installs sessions, fills it, and checks zero free bytes. The real pc.sh/pc.py/gc.py path uploads four parts per label. The stop payload also exercises the ordinary checkpoint route; total checkpoint traffic is about 4 GiB. The archive remains capped at 50,000,000 bytes. No 2 GiB payload was created in the offline build; the dry run substitutes 3 MiB and explicitly records that limitation.

E3.json retains all 14 E2 checks plus rate and upload_logging. It records per-part bytes, seconds and MB/s; total stop-upload duration spans the first part's start to the last part's finish. The total rate includes hashing and protocol work. Final-pass time is a separate field. The report includes receipt hashes and final GCS name, size, generation, md5Hash and crc32c fields. The observer does not replace the remote HTTP transport. The copier uses threads, so the observer remains active in all four upload workers.

The copier queries each resumable offset, sends Content-Range on every chunk, and resumes acknowledged bytes. Chunks are 8 MiB except the last. Only final 200/201 JSON with matching name, size, MD5 and generation creates a receipt. Every request records status and Range, and failures record masked exception text. UPLOAD_NO_RECEIPTS.json names a first attempt that produced no receipt. Live logs retry when X recovers; the frozen archive contains log tails available when it is built. Later archive attempts and resumed work continue in the live/local upload log.

The status-tool/readback names actually consumed by the fixture are listed in STATUS_NAMES.template.list:

- `q9/22c714e1/469ddece_ckstop.tar.j<job>.part00-of-04`
- `q9/22c714e1/469ddece_ckstop.tar.j<job>.part01-of-04`
- `q9/22c714e1/469ddece_ckstop.tar.j<job>.part02-of-04`
- `q9/22c714e1/469ddece_ckstop.tar.j<job>.part03-of-04`
- `q9/22c714e1/469ddece_m100.tar.j<job>.part00-of-04`
- `q9/22c714e1/469ddece_m100.tar.j<job>.part01-of-04`
- `q9/22c714e1/469ddece_m100.tar.j<job>.part02-of-04`
- `q9/22c714e1/469ddece_m100.tar.j<job>.part03-of-04`
- `q9/22c714e1/469ddece_o.tar.j<job>.part00-of-04`
- `q9/22c714e1/469ddece_o.tar.j<job>.part01-of-04`
- `q9/22c714e1/469ddece_o.tar.j<job>.part02-of-04`
- `q9/22c714e1/469ddece_o.tar.j<job>.part03-of-04`
- `q9/22c714e1/469ddece_ck00.tar.j<job>.part00-of-04`
- `q9/22c714e1/469ddece_ck00.tar.j<job>.part01-of-04`
- `q9/22c714e1/469ddece_ck00.tar.j<job>.part02-of-04`
- `q9/22c714e1/469ddece_ck00.tar.j<job>.part03-of-04`

The complete preparation set remains SESSION_NAMES.template.list (108 names). On the credentialed node, use the supplied mint tool's status operation for each consumed name without displaying its session value:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B mint_n.py status sess_<job>.json OBJECT_NAME
```

Copy only the small E3.json report for readback. On trinity-3-30, run the operator-side reader:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B readback.py E3.json --bucket BUCKET
```

The reader serially fetches the exact generations at at most 8 MiB/s, checks sizes, MD5 and SHA256, compares CRC32C metadata, and reconstructs the four archive parts for its complete SHA256. Credentials enter curl through stdin. Budget about nine minutes for roughly 4 GiB of readback at that cap, plus metadata requests. It prints object names and hashes, never a session URL. The operator reader SHA256 is `238ea609ea8124cedd3a12b944e5ebd3cbaa8e4bd086d25a96429da8e31ee0e6`.

The job writes E3.json and logs.tgz only under real X/o/<job>. Logs include the full upload event log plus bounded copier/state diagnostics. A failed report publication retains node-local evidence. No training release is authorized by an E3 dry-run pass; the unresolved real failure and stop-window findings are recorded in ENOSPC_24M4Z7.md.
