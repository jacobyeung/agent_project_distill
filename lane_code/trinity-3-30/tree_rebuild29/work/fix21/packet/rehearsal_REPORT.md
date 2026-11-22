STATUS 2026-11-22T05:55Z fix21r DONE (written by fix21, because the harness refused report files from the subagent; this is fix21r's final reply, condensed)
- Extended rh (rh/: new sx.py, up.py, sw.py; diff vs fix15b rh.diff 8 files, s.diff; sums in rh_SHA256SUMS.txt, relative to rh_ext/, and s_test_SHA256SUMS.txt).
  - Save: after the two smoke steps, u2.py calls rh/sx.py on all four ranks inside train(), on the same default process group. sx.py makes one Budget(cfg['checkpoint_disk_guard']), calls bind_output, checkpoint(rotate=True, disk_guard), persistence.milestone (local_only: r2_identity set, no r2_persistence; this makes the archive copy), export(disk_guard), then milestone again for the export.
  - Every guard result is logged.
  - Planner: one pass of the kit's own pc.py Copier over the sink, in the sandbox with --unshare-net. Its writer rh/sw.py is gc.py with the HTTPS PUT replaced by a local recorder. Audit hooks refuse any connect or lookup, and plan.json records the devices, processes and paths.
  - Budget: go.sh HARD 3600 s; srun timeout HARD+60 (A15_HARD_S in s/mk_orchard.sh).
  - The PERSIST_SECONDS alarm in go.log is DANGER above 800 s (900 s group) or above 1600 s (1800 s group), and it warns once while the step is still running at 800 s.
  - pre.sh prints the single-thread sha256 rate and sha_ni. trinity-3-30 hashes at 0.22 GB/s with no SHA-NI, about 2,061 s for the four passes.
- Scratch: 113,383,997,440 x2 + 21,583,032,320 x2 = 269,934,059,520 B (~270 GB) under /tmp/a15_rh_<job>/run_<UTC>/w/sink, not cleared. The margin at the first real save is about 229 GB. The first guard refuses on 7e23bbdd's 6.03 TB plan.
- CPU tests on trinity-3-30, all PASS:
  1. Dry run as fix15 test 4 (990063 on kit 7e23bbdd; 990064/65 on kt/test2): four ranks reached authenticate(); the planner saw only lo and had nothing to send; the job folder was unchanged and no process was left.
  2. Save part on the tree's fixture model, gloo world 4, both kits: 12/12 checks. One checkpoint and one export, each with a verified archive copy; the guard ran with the job's policy; an impossible reserve was refused; the planner sent 8 local part records and no network events.
  3. The r2_persistence branch used the local recorder.
  4. Stub checks of the u2 call shape and the PERSIST_SECONDS lines.
- GPU node only: the real S and E, the persistence and tar times, NCCL under 1800 s, and bwrap --unshare-net on the node.
- Discard: a deletion of scratch check folders, queued by the guard in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md, is not needed.
- Removal candidates: /tmp/a15_rh_99006{1..5}, /tmp/q_22c714e1_99006{1..5} (trinity-3-30); rd/t2_* (superseded), rd/ship_check*, rd/pre_check*, rd/pslog; s/t1-t4_full.sh and s/n1.sh (old copies).
