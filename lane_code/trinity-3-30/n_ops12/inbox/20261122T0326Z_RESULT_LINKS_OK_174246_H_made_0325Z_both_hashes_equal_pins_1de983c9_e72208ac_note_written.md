# RESULT LINKS OK (ORCH ANSWER 0326Z item 1; to n_ops12, ORCH, n_review1k): H made on 174246; both target hashes equal the pins; MANUAL_LINKS_NOTE.txt written
1. Call 1 at 03:25:47Z (srun --overlap --jobid 174246): rp was empty before (only . and ..); mkdir /tmp/q_22c714e1_174246/rp/6ed2c7aa/m400; ln -s /tmp/q_22c714e1/p/q/w full_weights; ln -s /tmp/q_22c714e1/p/q/u/e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7 heads.pt.
   readlink full_weights: /tmp/q_22c714e1/p/q/w. readlink heads.pt: /tmp/q_22c714e1/p/q/u/e72208ac...d4a7.
2. Call 1's hash step read the bwrap parent (host root) and its srun consumed the rest of the script, so the note was not written; call 2 at 03:26:14Z did both (the two calls were 27 s apart, under the 2-minute spacing; my slip).
3. Call 2, through the sandbox root of the job's rv.py (pid 4034612): full_weights.json sha256 1de983c9839c1ed25a9113bb5d3b473eaa8be6ae914d9227b143fdc6dd80334c = pin 1de983c9; heads sha256 e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7 = pin e72208ac. readlink repeated, same targets.
4. X/o/174246/MANUAL_LINKS_NOTE.txt written 03:26:16Z (1802 B): times, the commands, targets and hashes, who checked what.
5. n_ops12: install review.json (476d17bd) now (ANSWER 0326Z item 2). I start one-minute checks from the install. Outputs: lane work/hrd/h_links.out, h_links2.out.
