# Dense-frame fetch/decode packet (Orchard root /project/community/jjyeung/okh7/db3954b2; staged, self-tested on the login node)
Nothing here is submitted without an ORCH GO naming the job. CPU only. Ledger: L/work/ORCHARD_LEDGER.jsonl.

## Self-test on the login node (done 2026-11-16 ~12:50Z; L/work/oq9.out, oq13.out)
- v path: synthetic 30-frame mp4, need [0,5,29,31]: 3 frames 640x480, ordinal 31 reported as a miss (as wd.py does).
- a path: one real capture (v00475f483e27, Apple range reads): 64/64 frames, 5.7 MB fetched, 5 s; decoder versions equal the k6 pins.
- Parity: 3 of 32 student frames byte-equal the k6 pins; all 32 pass the pixel rule (max |d| = 1, fraction <= 1.3e-5). Cause: CPU SIMD dispatch in cv2 resize (same versions). Byte pins are therefore not a parity test; dparity.py applies the pixel rule (max |d| <= 1, fraction <= 1e-3), fixed before the full run.

## Jobs (one ossh call each; TZ=UTC squeue afterwards)
1. Egress test (compute-node egress unproven), job a15_cot_apc9f6b9ac93a6:
   sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:10:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apc9f6b9ac93a6 /project/community/jjyeung/okh7/db3954b2/bin/egress.sh
   Pass: logs/egress.<jobid>.json has status 206, bytes 65536, zip_magic true. If it fails, run step 2a on the login node at nice 19 with 8 threads (5 s per capture, about 1 h with no compute job) or inside the frame-host job.
2. Fetch and decode, job a15_cot_ap7128842a8567: ONE allocation running the six parts a0..a2, v0..v2 serially through bin/dserial.sh (general_qos allows 5 submitted and 1 running job per user, so a 6-task array is refused):
   sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=64G --time=05:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap7128842a8567 --wrap '/project/community/jjyeung/okh7/db3954b2/bin/dserial.sh'
   A rerun skips parts that have DONE. egress.sh takes its root from EGRESS_ROOT (default the staged root), because sbatch runs a spooled copy of a script file.
   Expect: a = 1,500 captures, 46,424 frames (+ parity ordinals), about 4.3 GB from Apple, 13.5 GB PNG; v = 1,225 videos, 11,410 frames (+ 4,310 parity), 2.9 GB PNG; each v task streams both media tars (49 GB gzip) through pigz once. Parts land in parts/<kind><shard>n3/ with DONE.
3. Pixel parity after all six parts are DONE, job a15_cot_ap116cafc201ec (or the login node at nice 19):
   sbatch ... --cpus-per-task=4 --mem=16G --time=02:00:00 --job-name=a15_cot_ap116cafc201ec --wrap '/project/community/jjyeung/cp4tk_fr/venv/bin/python -I /project/community/jjyeung/okh7/db3954b2/bin/dparity.py /project/community/jjyeung/okh7/db3954b2 /project/community/jjyeung/okh7/db3954b2/parity.jsonl'
4. Pull to Trinity (small files, one at a time): cat parts/*/out.jsonl into wa_out.jsonl (a*) and wd_out.jsonl (v*), and parity.jsonl; then locally:
   B06_TREE=<tree> python -I dense/dense_manifest.py seal out/plan_v4 wd_out.jsonl wa_out.jsonl SEALED.json parity.jsonl
   Pass: 0 problems unexplained, held scenes listed, 2,741 clips minus refusals with reasons.

## Timing (ORCH 1300Z)
Submit only after the D0 step-200 stop-rule read leaves general (~19:30Z; cont_ops events). Jobs 1, 2, 3 one after another; all must leave general before the D0 m400 read (~01:40Z 11-17). Expected wall: egress minutes; array about 2-3 h serial (each v task streams 49 GB of gzip once); parity under 1 h. If job 2 is not done by 00:40Z, cancel the pending tasks and report.
Job 1 also writes logs/disk.<jobid>.txt (df of /tmp, /dev/shm, lsblk, free) for the cache-location decision.
