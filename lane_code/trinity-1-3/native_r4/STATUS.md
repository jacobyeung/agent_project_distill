# native_r4 lane STATUS (trinity-1-3) — operator native_r5, updated 2026-11-16T13:57Z
Lane folder /scratch/jjyeung/orch_n30/native_r4; events /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r4/. Record /data2/jjyeung/agent_project_data/distill_design/VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md (+ INDEX line). Rules: .../orch_n30/tools/LANE_RULES.md. native_r5 session ends by ~16:20Z (6 h from 10:20Z) or 60% context: RESULT rotate.

## NOW (13:57Z): third job 170254 (a15_cot_apd12e2a0337651f2637e988f9, V1f) submitted ~13:55Z (RESULT submitted3)
- Poll: `timeout 300 bash .../tools/ossh.sh 'bash -s' < work/orchard/poll3.sh` every 5 min until proof+canary seen, then 10 min; poll3 lowers TimeLimit while PENDING (end <= 17:40Z). Proof >20 min = BLOCKER. Return: okh7/n2r/d12e2a0337651f2637e988f9 + GCS q8/n2r/ same; fetch through governor; merge journals; report with builds/04_vsti_d code.
- V1f builds/07_vsti_f (c.tar 063e09f8, family c6ad8e73) on Orchard as c.tar/FAMILY.json/c/ (V1c kept as *.v1c_*, c_v1c/). GCS c gen 1794832620770863; r3.json, g3.json.
- Packet p/d12e2a0337651f2637e988f9 (TOKEN3; letter-leading), --deadline-utc 17:35Z. Watcher tmux nr5_watch3 (work/orchard/watch3.sh, log watch3.log) runs q11_sbatch3.sh every ~5 min: refuses if own job on general or past 15:40Z; on submit copies to q11.out. Then: RESULT with job id; poll with a poll3.sh (copy of poll2.sh with job id/token); lower TimeLimit while pending so end <= 17:40Z.
- 170228 cause of no return: digit-leading token rejected by publisher (V1f DIAGNOSIS.md); first failure unknown.
- Second job's packet/state below.
- Inputs: b.tar re-packed without _staging hard links (0eadd83e, 10,296 '-' + 313 'd'; GCS gen 1794829424090479); a/c/d unchanged; r2.json, g2.json in okh7/d9c35d0a/. Old b kept as b.tar.hardlinks_06e28d71. Packet p/8f7817fb16bc218af285dc61 (a.sh 2358921d, a.json ec6ef7f1). Return okh7/n2r/8f7817fb16bc218af285dc61 + GCS q8/n2r/ same.
- sbatch --nice=200 gpu:1 16 CPU 200G --time=04:45:00. While PENDING: at each poll `scontrol update JobId=170228 TimeLimit=<16:30Z - now>`.
- Poll: work/orchard/poll.sh (edit job id to 170228 / TOKEN2). Checklist: work/orchard/PRESUBMIT_CHECKLIST.md.
- First job 170209 failed in staging on b.tar hard links (BLOCKER 11:17Z); return okh7/n2r/ece5eea1c1ec94e169abf835.

## First job 170209 (submitted 11:04Z, FAILED 11:10Z in staging; return okh7/n2r/ece5eea1c1ec94e169abf835)
- Orchard job 170209, name a15_cot_apece5eea1c1ec94e169abf835, general, 1 GPU, cpu 16, mem 200G (= job 170056), time 07:00:00, nice 200, internal deadline 16:15Z (kill 16:05Z, return reserve 600 s). Code V1c c.tar dc40cf60 (CONFIRMED_dc40cf60.md). sbatch line: `sbatch --nice=200 --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G a.sh` (a.sh's own gpu:h100:1 is rejected on Orchard).
- Packet okh7/d9c35d0a/p/ece5eea1c1ec94e169abf835/ (a.sh 82f0d491, a.json 874da946); r.json, g.json in okh7/d9c35d0a/. Return: okh7/n2r/ece5eea1c1ec94e169abf835 and gs://cmu-gpucloud-jjyeung/q8/n2r/ece5eea1c1ec94e169abf835/. Ledger work/ORCHARD_LEDGER.jsonl.
- Inputs on Orchard okh7/d9c35d0a/ (sha256 verified 10:58Z, GCS generation): a.tar 795f7255... (1794825294704737), b.tar 06e28d71... (1794826763678301), c.tar dc40cf60... (1794825299420188), d.tar 9a1de860... (1794826765833906), FAMILY.json 3cf68794.
- Phases: stage -> tower+scale/gravity prepare -> dev-S1 proof (10 items vs 170056; failure = receipt; no own cap: >20 min in proof = BLOCKER) -> canary -> 100 camera items -> 350 others. The return is published only at job end (finally block); mid-job state only via work/orchard/poll.sh (srun --overlap read of /tmp/a15_170209_*).
- Watch: `timeout 300 bash .../tools/ossh.sh 'bash -s' < work/orchard/poll.sh` every 5 min until proof+canary seen, then 10 min. Fetch the return through the IO governor (register first; priority from ORCH). Report with V1d code: merge journals first, then builds/04_vsti_d/work/report_return.py (V1d out/RUN_ORCHARD.md). Reports owed: proof outcome; camera types (100 items) beside f17 / P1 m200; full read per-type table, refused-call cost, proof, frames line. Deadline stop with items left: say what is missing, prepare resume packet (RUN_ORCHARD resume section), needs ORCH word.

## Facts
- Frame-index check vs VSTI's own selected-frame list (local; in/vsti/selected_frames_vstibench.json sha 6f1813dd, converted work/index_check/selected_indices_only.json): 309/311 equal; scene0609_02 slots 10,18,19 and scene0690_00 slot 18 off by one ordinal (work/index_check/INDEX_CHECK.json). Release check: same frames, re-encode noise (events/native_r4/RELEASE_CHECK.json).
- Kits: V1c builds/03_vsti_c (submitted code; mirror trinity-3-30:/scratch/jjyeung/n30_mirror/native_r4/kit_v1c.tar 255abab2); V1d builds/04_vsti_d (report code only). V1e not built (ORCH 1021Z/1031Z).
- Kit fix for a future epoch: o.py packet a.sh requests gpu:h100:1 and no cpu/mem.
- Removal candidates: REMOVAL_CANDIDATES.md.
