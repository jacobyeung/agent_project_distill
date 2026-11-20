# Codex build 24m4y of lane tree_rebuild: rcj helpers only. (1) The CPU job's exit status and nd's task_i must follow ORCH ANSWER 1226Z, not the literal row diff. (2) The third extent control should come from a real Orchard row if one exists.

You run once, on trinity-1-18; nobody answers questions. Writable: `J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y/` only (step 0, already done by the lane: untar of `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24x2/out/tree_rebuild_b24m4x2_e3d14e7b.tar`, sha256 70c757dc...). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 50 minutes. The tree (9d2bbb8a) and the kits' admission behaviour do not change. Change only rcj helpers (x.py, nd.py, ch.py, f.json if needed) and reseal what you change.

## Why (full kit review rev24m4x2c NO-GO, codex_runs/*_tree_rebuild_rev24m4x2c/final_message.md; read it)
- Finding 1. Candidate 173817 (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817/`) runs mode r to the end with every step passing: chain refused_rows 0, extent_exempted_rows 10,945; routing_types PASS; proc_check PASS; nd/na published. But timings.json has post_returncode 1 and rdiff_returncode 1, and nd.json says task_i FAIL. The reason is that nd's task_i compares the whole /row value literally, so it flags the ordinal /i on 39,892 rows and the copied top-level fields on the 11,663 pool rows. ORCH ANSWER 1226Z (binding) defines criterion (i) instead:
  - (a) every encode-relevant field of the published reader list, and the raw SQL target, are identical over all rows;
  - (b) the four metadata classes are counted over all rows, and nothing else differs;
  - (c) the full per-row chain refuses zero rows over all routing rows with N's real pins;
  - (d) the sampler's population is exactly N's routing database (row count and key set), which only the discovery's preparation reaches.
  Also, "a difference counts as content only if it changes a training example or a refusal". rd0 is informational by design (nd.json "rd0": "informational; includes ordinal").
- Finding 2. ch.py:371 takes the third control ("a row of neither kind refuses") from an embedded sealed reference row, vsi590k_169139 (origin sealed_reference), because N's routing DB has no such row. ANSWER 1551Z item 2 asks for real rows.

## Do
1. Fail-before (real path): cite 173817's timings.json post_returncode 1 / rdiff_returncode 1 and nd.json task_i FAIL with its cause, and chain.json's sealed_reference origin. Pass-after: show the same rcj steps passing on 173817's real published files (offline replay of nd's decision on those files where possible), and say what only the next CPU job can show.
2. nd/x.py decision per ANSWER 1226Z:
  - Derive from C'' / tree 9d2bbb8a code, with file:line, which reader-list fields reach the encoded training example (prompt ids, target ids, frames, masks, spans; e.g. carrier_c1_routing encode, carrier_c1_data, batches). Compute (a) as identity of exactly those fields plus the raw SQL target over all 43,101 rows.
  - Keep (b) as is.
  - Take (c) from the chain.
  - Report (d) as DEFERRED_TO_DISCOVERY, not FAIL.
  - Publish each of (a)-(d) separately, with counts and the field list. Keep the literal whole-row diff published, under a new name, as information.
  - x.py's exit status is 0 iff every step mode r runs passes and (a), (b) and (c) pass. rd0 stays informational and published, and does not decide the exit status.
  - No check is weakened in the other direction: any difference in an encode-relevant field or in the SQL target fails (a) with examples.
3. Third control: search the real databases the CPU job already stages on Orchard (N's routing DB, P's rebuilt base DB 4e8e6c04, the first-boundary slice and recovery stores the kit pins, if staged; read the kit configs and x.py to see what is staged). You need a row the gate requires that is neither from a listed source nor an a0_ slice, for example a row with an r1_source key or an unlisted-source distance row. If one exists, the control uses it (origin database, with path and sha256). If none exists in any staged store, keep the sealed reference row, and publish why no real row of that kind exists, with the count per store, so the reviewer can verify it.
4. Reseal the changed rcj files (and kits only if their sealed files change; GO false except kit_n_go). Rerun the rcj suites, the chain controls, the 80-row chain and 24m4x2's targeted tests.
5. Outputs: out/UPLOADS_24M4Y.json/.list exact against the reviewed Orchard overlay (q e7ac0727, n a7809da0, qd 221d1782; rcj x.py d8517333, ch.py 16d7210b, nd.py eb0ba92e, f.json 37cbc05d, pc.py bd87252b, ps.py 6945292e, rcj.sh b23393f2, P_SAMPLE_I fff742bb), plus every 24m4x2 upload, so the list is the full delta; package out/tree_rebuild_b24m4y_<seal8>.tar + .sha256 (written last); out/BUILD24M4Y_REPORT.md under 12 lines.

## Rules for the build (restating build 15's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J (and a private tmp under J). No deletion (superseded files into J/attic/). Every CPU process under `nice -n 10`, at most 8 threads, under 16 GB RAM. The tree does not change. No project, benchmark, dataset, model or method word in any new Orchard-visible name, path, argument or log. Report failures with their output; never claim a check you did not run.
