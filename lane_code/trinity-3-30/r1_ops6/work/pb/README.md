Run the survey first. From this directory, set `OSSH` to the existing `ossh.sh` helper; it is not included here:

```bash
OSSH=/absolute/path/to/ossh.sh
bash "$OSSH" 'bash -s' < survey.sh
```

Submit the rehearsal with an unused opaque token. These commands submit the script through stdin, so no installation on Orchard is needed:

```bash
token=81a60d2f
job=$(bash "$OSSH" "sbatch --parsable --job-name=a15_cot_ap${token} --time=04:00:00 /dev/stdin 673bc60f 200 /project/community/jjyeung/okh7/pb_${token} 13800" < pbjob.sh)
job=${job%%;*}
[[ $job =~ ^[0-9]+$ ]] || exit 1
printf '{"token":"%s","job":"%s","run":"673bc60f","step":200,"purpose":"pb200","utc":"%s"}\n' "$token" "$job" "$(date -u +%FT%TZ)" >> /scratch/jjyeung/orch_n30/r1_ops6/work/ORCHARD_LEDGER.jsonl
```

Expected verdict: `PASS`, because run A stopped at 200. This has **not** been run on Orchard.

After job 172660 leaves the queue, if `/project/community/jjyeung/okh7/h_6ed2c7aa/m600/DONE.json` is absent, submit plan B:

```bash
token=9c31e4a7
job=$(bash "$OSSH" "test ! -e /project/community/jjyeung/okh7/h_6ed2c7aa/m600/DONE.json && sbatch --parsable --job-name=a15_cot_ap${token} --time=04:00:00 /dev/stdin 6ed2c7aa 600 /project/community/jjyeung/okh7/pb_${token} 13800" < pbjob.sh)
job=${job%%;*}
[[ $job =~ ^[0-9]+$ ]] || exit 1
printf '{"token":"%s","job":"%s","run":"6ed2c7aa","step":600,"purpose":"pb600","utc":"%s"}\n' "$token" "$job" "$(date -u +%FT%TZ)" >> /scratch/jjyeung/orch_n30/r1_ops6/work/ORCHARD_LEDGER.jsonl
```

Post the order's BLOCKER with the returned job ID and estimated finish; queue delay is additional. Ledger writes above are operator actions, not writes performed by this build or the batch job. Use fresh tokens for subsequent submissions; the output directory must not exist. No automatic retries or cleanup occur.

Interface: `pbjob.sh RUN STEP OUT LIMIT_SECONDS [KH [ZIP [SHA]]]`. `OUT` must be a new `/project/community/jjyeung/okh7/pb_<hex>` directory. Defaults select `x_69d2930d` for A, `x_ee227714` for P, and q2 with SHA `f415c69d7f8adfb6e9483c1bf53deb6f01728689f3c33806c4bda540675c4fdc`. An alternate tree requires both ZIP and SHA. The job reserves 20 seconds of its hard limit for reporting; Slurm's limit should exceed that argument. It requests 16 CPUs, 192 GiB, no GPUs, and no requeue.

The job checks the source job has ended and A's step matches exactly. It verifies the slot and concatenated export before extracting only listed payloads and closure metadata. External metadata resolves from `KH/k`, `KH/in_small`, declared `extra` entries, or exact members of the pinned small archive. The venv comes from `k/0.json:venv`. Absolute pin paths remain intact under read-only mounts; SDK state is copied privately. No frame/store trees are extracted, and no cleanup occurs.

Success produces `h.json`, `RP.json`, `pb_report.json`, and `pb.log`. The report records stage minutes, each phase's timing, receipt SHA minutes separately from archive verification, verdict/error, output hashes, and maximum process RSS. Failures publish available evidence without fabricating a receipt. Preemption/SIGKILL can prevent publication; directory existence alone does not establish success.

Still unknown until survey/rehearsal: live slot/marker availability, exact small-archive members, venv layout/dependencies, Python >=3.9, credentials, and CPU-only admission. `sinfo` reports configured TmpDisk, **not live free `/tmp`**. The job checks free space against three times the archive sizes plus 150 GiB. GCS authentication/object existence is checked during the job because SDK queries can update credentials. Unknown sources fail closed.

Risks: queue delay, preemption and throughput remain unmeasured; an alternate tree may require a different closure. RSS measures the largest process, not aggregate memory. Plan B records its own Slurm ID; downstream acceptance still needs the order's requested confirmation. The exact order was read; q2 replaces its “build-21” wording as instructed.

Validation: both `bash -n` checks passed. Local fixtures tested RP pins, safe extraction, output refusal, failure-report publication, and actual q2 closure hashing/corruption rejection. The q2 fixture stubbed recipe validation and used a compatibility shim for local Python 3.6.8. Orchard execution and the unavailable m400 archive were not tested. Small test fixtures remain under `_check_*`; nothing was deleted.
