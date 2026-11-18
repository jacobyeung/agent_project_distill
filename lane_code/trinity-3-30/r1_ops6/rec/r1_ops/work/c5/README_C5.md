`rh2.sh` submits one CPU rehearsal that stages its inputs and invokes the sealed proof entry in the same allocation. `pr4.sh` submits one HELD CPU proof after verifying an explicit operator waiver. Both are standalone drivers. Copy only those two drivers to the operator directory; the helper files and fixtures stay local.

Packet C remains `08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd`. No driver edits the archive, kit code, kit metadata, or existing drv_c1 files.

Run these commands from the directory containing the copied drivers and the existing `ossh.sh`, or set `OSSH` to that script's absolute path. These commands are operator instructions; the local build made no connection or submission.

```bash
OSSH=./ossh.sh
timeout 300 bash "$OSSH" 'bash -s' < rh2.sh
```

Expected output includes `PASS retained valid general a4.json` (or `PASS installed fresh general a4.json`), `PASS retained rehearsal 172467 markers`, and `SUBMITTED rehearsal_job=<ID>; never a PASS proof`. The timeout covers the login-side submission, not the batch runtime.

`rh2.sh` verifies the packet, bundle member pins, private directories, queue snapshot, kit top-level inventory, failed receipt, and 172467 markers. It refuses an existing proof attempt. It creates a fresh general authority with the sealed sealer at `KH/o/rh2.a4.check.json`. If that authority equals `BUN/a4.json`, it retains a4 byte-for-byte. Otherwise it moves a4 to `a4.json.r172467` and installs the new authority. It moves the four rehearsal markers to names ending `.r172467` with atomic same-filesystem RENAME_NOREPLACE. Every collision refuses; there is no rename fallback or automatic retry. The per-job 172467 receipt and logs remain in `KH/o`.

The job requests account mt01, general, orchard-community-0, one node, one task, four CPUs, 32G, zero GPUs, and 45 minutes. Its wrapper is `KH/o/rh2_08f3a7b2.sh`. The wrapper creates `/tmp/jjyeung/rh2_08f3a7b2_<ID>/root`, then runs:

```bash
/bin/bash "$BUN/p_05b8ac69.sh" "$BUN/a4.json" --rehearsal "/tmp/jjyeung/rh2_08f3a7b2_${SLURM_JOB_ID}/root"
```

The wrapper preserves the child return code. A staging error creates a separate `REHEARSAL_FAIL` receipt with `steps.self_stage=FAIL`; it cannot produce REHEARSAL_OK. The sealed child writes the normal receipt and log after startup. Staging records source paths, sizes, and verified SHA256 values in `KH/o/<ID>.rh2.stage.json`. The bundle ledger retains the wrapper path and SHA256.

Inspect the result using the existing read-only driver, no more than once per minute:

```bash
timeout 300 bash "$OSSH" 'bash -s' < rhf.sh
```

Require `REHEARSAL_OK`, rc 0, the new job ID, `rehearsal=true`, and `admission_output_boundary=EXPECTED_MISSING`. Once the job has left the queue, the existing `pr1.sh general --hold` can consume that receipt. The rehearsal never writes `BUN/job.id` and never counts as a proof. Follow the existing general-slot ordering; submission does not establish that another allocation has finished its required read.

The staging sources are exactly the runtime pins and the two selected `extra` entries in the deployed `KH/k/0.json`. Logical paths under the kit's existing `ap/8865619b` prefix map to `KH/k`. The following sizes come from the retained, pinned 172180 admission log and packet descriptor; the job measures current sizes before staging.

| Input | Login-visible source | Bytes | Destination below the new root |
|---|---|---:|---|
| Runtime environment | `/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar` | 8,105,379,840 | `c7d31ddd/venvs` |
| Runtime closure | `/project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar` | 368,640 | `c7d31ddd/_jobs/cp4tk_fa8681cba4c0` |
| Code tree | `KH/k/t_b83a8a35d420815b.tar` | 9,963,520 | `epochs/<commit>` |
| Array overlay | `KH/k/np226_5204b3a0.tar` | 202,598,400 | `np226` |
| Runtime record | `KH/k/s1_record.json` | 80,263 | `c7d31ddd/anyhost/<record SHA>.json` |
| Store descriptor | `BUN/d.json`, selected through the config and `extra` pin | 685 | `aws/u/ap/69d2930d/d.json` |
| SQLite file | `/project/community/jjyeung/okh7/s_22b44165/d.db` | 1,718,255,616 | `aws/u/ap/69d2930d/d.db` |

These inputs total **10,036,646,964 bytes (10.04 GB)**, plus two small pinned files from `KH/b/sa`. The wrapper uses the sealed streaming extractor for the four complete runtime archives; the code-tree check requires the complete tree. It copies and verifies the descriptor, SQLite file, record, and two startup files. It retains the archive's existing site_alias directory before installing the same startup files that admission installs. Direct invocation of the Python binary needs no console-script shebang rewrite.

The wrapper creates empty directories for the mount sources at `aws/u/ap/8865619b/u`, `c7d31ddd/data2root`, and `c7d31ddd/runs/aws128p_20261025/models`. The sealed `tk_nx` copies b/ and k/ into its separate writable per-job kit; the loader's `root/k/launch.json` refers to that kit, not to a missing k/ below the staged input root. The sealed code supplies the normal run and job directories. The admission output remains absent.

Budget **2–5 minutes after allocation**, excluding queue wait. This is an estimate, not a live measurement: the retained admission log reports 15 seconds for the environment extraction, with the other three archive times rounded to zero. Pool contention and hashing the SQLite copy can increase runtime. The wrapper refuses more than 24 GB of source inputs or less than three times measured input size plus 2 GB of free temporary space. It submits no admission, restore, or training job.

Use the fallback only with an explicit operator waiver event. The file must already exist on the login-visible filesystem, contain the approved event bytes, and use an absolute path without symlinks. `KH/o/waiver_event.txt` is a permitted location. Set `WAIVER_SHA` to the SHA256 of those exact bytes. The driver records the path and SHA, plus the raw SHA256 of `KH/o/172467.rehearsal.json`.

```bash
WAIVER_FILE=/project/community/jjyeung/okh7/x_7f1589c1/o/waiver_event.txt
WAIVER_SHA='REPLACE_WITH_APPROVED_EVENT_SHA256'
printf -v remote 'bash -s -- general --hold --waive-rehearsal %q %q' "$WAIVER_SHA" "$WAIVER_FILE"
timeout 300 bash "$OSSH" "$remote" < pr4.sh
```

Expected output includes `PASS history: FAILED 172180 and rejected bootstrap only`, `PASS explicit rehearsal waiver; HELD proof only`, and `SUBMITTED job_id=<ID>; HELD requested; production GO remains false`. The proof requests general, 48 CPUs, 800G, four hours, and the original CPU entry. `--hold` is required by both argument validation and the sbatch argv. No release command runs. The ledger says HELD_REQUESTED because sbatch acceptance alone does not verify live scheduler state.

`pr4.sh` retains pr1's packet, private-directory, lock, fresh-attempt, queue, accounting, authority, certificate, external pin, sessions, runtime, and sealer checks. Only the successful-rehearsal requirement becomes the waiver check. Parser calls use neutral `rsplit` spelling; their delimiters and guard predicates remain unchanged for the sealed formats. The waiver is retained in `KH/o/pr4.waiver.json` before submission and in `KH/o/<ID>.waiver.json` after a numeric submission receipt. Existing submission.started, sbatch.out, a.json, and job.id accounting remains unchanged.

The existing `go_submit_canary_08f3a7b2.sh` accepts this proof's markers. It checks the recorded proof ID, submission marker, sbatch receipt, and active general PENDING/RUNNING state. It does not require a rehearsal-success marker or inspect waiver files. The sealed canary gate rejects a rehearsal receipt for the proof ID, which pr4 never creates. A held PENDING proof is accepted. The existing separate ruling, donor checks, admission pins, queue checks, and training guards still apply; any queued rehearsal causes the canary wrapper to refuse.

No sealed refusal blocks child invocation. In `snap_08f3a7b2/out/proof/p.py`, `proof_allocation` checks partition and GPU visibility; `main` checks numeric Slurm ID and the distinct rehearsal name. The stage check at lines 375–381 requires an existing absolute, nonlinked directory resolving below `/tmp/jjyeung`. It does not inspect the Slurm batch-script filename or require provenance from job 172180. The source embedded in the unchanged entry matches SHA256 `90f968228b4130f5d65f33e3fce7604a582f8c80fd7b5bd56fd070625c647e47`.

All new persistent runtime files reside under KH/o or the existing bundle marker locations. The real sealed kit validator accepts the KH/o additions; the top-level allowlist remains intact. A failed or uncertain submission leaves evidence and blocks another attempt. Inspect retained state manually; do not rerun a driver automatically. Runtime namespace, source availability, and actual scheduler behavior still need the operator's Orchard run.

Local validation uses only `/scratch/jjyeung/envs/p1cpu/bin/python`. Run `"$PY" -B test_c5.py` and `"$PY" -B test_stage_c5.py` from c5 after setting PY to that path. The 44 fixture checks cover submission guards, waiver failures, marker collisions, uncertain replies, complete streaming extraction, pin failures, GPU refusal, and child return codes. The canary test executes the existing outer wrapper with scheduler and sealed-gate stubs; it does not claim a real canary approval. Separate checks execute the real sealed authority sealer and real kit inventory validator. The packet SHA, Bash syntax, and shipped-driver vocabulary scan also pass. Tests create fresh local fixture directories and retain them.
