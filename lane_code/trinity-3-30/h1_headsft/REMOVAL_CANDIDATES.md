# h1_headsft removal candidates (for the user; this lane deletes nothing)
All paths under /scratch/jjyeung/orch_n30/h1_headsft on trinity-3-30. Re-creatable; nothing below is the only copy of a deliverable.
- kit/tmp/* : Codex test temporaries and pytest basetemp dirs of builds 1-4 (~1.5 GB). Keep kit/tmp itself (tests need the directory).
- work/verify1/ : my rerun copy of build 1 (~0.5 GB).
- work/verify2/ : my rerun copy of build 2 (~0.2 GB).
- trinity-3-30 /dev/shm/jjyeung/h1tmp/ : session-2 temporaries (packet staging, test basetemps, probes; ~30 MB RAM).
- trinity-3-30 kit/tmp/b5/ and kit/tmp/b6/ : test basetemps of builds 5-6.
- /dev/shm/jjyeung/h1tmp/kit8 (121 MB RAM copy for the b8 suite rerun), /dev/shm/jjyeung/h1tmp/b8t, suite8.* (session 3)
- K/tmp/b9 (~18 MB, Build 9 test outputs, session 3); /dev/shm/jjyeung/h1tmp/{b9t,r0in,prompts,dispatch_kit9.log}
- K/tmp/b10 (~6.4 MB, F4 package/reviewer test outputs incl. 344 KB from an aborted full-suite start, session 4); /dev/shm/jjyeung/h1tmp/{f4src,f4b,f4t,pkg_b9_pre,f4suite.*,f4pkg.*,kit_b10.sha} (session 4)
