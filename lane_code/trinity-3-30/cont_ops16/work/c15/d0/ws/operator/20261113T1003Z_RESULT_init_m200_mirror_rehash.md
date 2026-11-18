# RESULT (orchard_cp2 s10): the parent CP1 m200 init mirror re-hashed on Orchard; every file matches

To: ORCH (your 1002Z item for the production GO list).
- **Where I ran it:** inside workbench job 168962, as a read-only `srun --overlap` step (1 CPU, 2 GB, nice 19, ionice idle) on orchard-community-2 at 10:03:24Z. The script is `work/adm/init_rehash.sh`.
- **What I checked:** the mirror is `/tmp/jjyeung/okit_8865619b/root/c7d31ddd/init/c1a4258816b3f561/`. It matches the kit pin `init` = ap/f2ad01ad/runs/49becb79/m200/artifact.json, sha c1a42588…, which k/0.json of ee36228a pins.
  - artifact.json re-hashes to c1a4258816b3f561….
  - heads.pt (2,763,214,343 B, nlink 2) matches the artifact.
  - The full_weights manifest matches the artifact.
  - **6 of 6 manifest-pinned files (the index plus the shards, 18,819,788,707 B) match.** No mismatches, no unexpected extra files. The check took 15.7 s.
- **Scope:** Orchard's /tmp is private to each job (job_container/tmpfs), so a `.verified` mirror cannot carry over from one job into another; every job builds it fresh in tk_stage_init. The reuse that c.sh:223 allows is therefore limited to a second `tk_stage` within the same job. The hard links point into the same job's union tree, which tk_stage_tars extracted with per-member sha checks. The production leg will build its own mirror, so this result covers the bytes the workbench uses. A re-hash inside the production job itself would need one line in its wrapper; that is leg_s1_tree's call.
