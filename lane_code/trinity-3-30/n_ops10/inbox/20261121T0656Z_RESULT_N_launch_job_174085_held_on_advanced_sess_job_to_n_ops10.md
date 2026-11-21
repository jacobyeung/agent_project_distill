# RESULT tree_rebuild26 -> ORCH, n_ops10, n_review1i: N's launch job 174085 is HELD on advanced
1. 06:56:33Z `sbatch --hold X/jn6.sh` -> 174085 (a15_cot_apb2edfac4, advanced, gres/gpu:4, PENDING JobHeldUser). Pre-checks in the same call: /project free 23 GiB by `df -BG --output=avail /project/community` (floor 20), no other job of ours on advanced, X/jn6.sh 0c0e5d3b, X/n seal 3f55530cc3874ed3 with `sha256sum -c` 0 bad, X/q seal ece78fea6daa3acb (lane work/o9.out).
2. SESS_JOB = 174085 written to /scratch/jjyeung/orch_n30/n_ops10/inbox/SESS_JOB. n_ops10: mint and install X/n_s/sess_174085.json and post the sha256.
3. Release: as soon as n_ops10's sessions and n_review1i's ARMED BYTES OK are both posted (ORCH GO item 4); if either is missing at 07:11Z I tell ORCH.
4. Full armed n_go seal: 3f55530cc3874ed3734f08c1e31589389ab8631ce9d0205b881e682b3e519b0c (arm log W/work/arm_0216Z.log "kits.n_go"); "3f555300" in older STATUS lines was a truncation slip.
