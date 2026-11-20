# Kit review (read-only, once) of vehicle N's ENOSPC kit change 24m4z4 of lane tree_rebuild

You review; you do not fix. Run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, with file:line and evidence. Your final message is the verdict.

- Build: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z4/` (prompts `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m4z2.md` and `build24m4z4.md`; reports out/BUILD24M4Z2_REPORT.md, out/BUILD24M4Z4_REPORT.md, out/ENOSPC_24M4Z2.md, out/ENOSPC_24M4Z4.md; work/build24m4z2/, work/build24m4z4/, work/enospc2/). Base: the reviewed kit line 24m4y2, package `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2/out/tree_rebuild_b24m4y2_42b4d736.tar` (sha256 15cdc127...), untarred at `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2/`.
- Why: on a full Orchard project filesystem X the 24m4y2 kit trains and then loses its exports, stop checkpoint and exit archive (24m4z test: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z/out/ENOSPC_24M4Z.md`). ORCH RULING 2055Z adopts the change: claims and receipts on node-local disk, uploads to fresh per-allocation GCS objects, retried publication. The launch wrapper is `J/inputs/jn2.sh` (outside the seal).
- Verify, each with evidence:
  1. Scope: in kits n and n_go only b/o.py, b/pc.py, b/pc.sh, k/y.json, SHA256SUMS.txt and BUILD.json differ from 24m4y2 (compare the files yourself); kits q, qd, the rcj helpers and the tree (9d2bbb8a) are byte-identical; n and n_go differ only in their GO files; GO is false except in n_go; seals verify.
  2. Nothing in admission, census, preparation, the review wait (rv.py) or the training loop changes behaviour: trace every caller of the changed functions.
  3. With X full: exports, ordinary and stop checkpoints and the exit archive reach GCS through gc.py with no byte required on X; publication failures are retried and logged on node-local disk and never end the job after training starts; the evidence in work/enospc2 and work/build24m4z4 shows this on the sealed bytes.
  4. Object safety: object names are unique per allocation (<label>.j<job>.partNN-of-04), a rerun never overwrites or duplicates a finished object, a missing or incomplete session file refuses before training, no session URL or token is printed, logged or published, and the local claim store cannot let two uploads of different bytes claim one object.
  5. jn2.sh: job name a15_cot_apb2edfac4; Slurm output on node-local /tmp; the publisher never holds a pipe of the job; ENOSPC on X is not fatal; the screen filter is applied before publication.
  6. out/e2/: e2.sh/e2.py write only under X/o/<job>/ on the real filesystem, fill only their private tmpfs, run the sealed kit bytes after verifying them, never print sessions, and their checks prove item 3 with real sessions (archive_while_full included).
  7. Upload lists (UPLOADS_24M4Z4*.json/.list) are exact and every file is under 5 MB.
- Also list what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 16 lines.
