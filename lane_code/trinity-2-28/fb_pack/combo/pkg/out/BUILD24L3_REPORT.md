TREE 24l3 is complete; native staging is re-verified, and hook staging records its authenticated plan.
Tree seal: 96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf; 943 files.
The untouched tree_r1_24ln snapshot retains seal e17fc130870963170e6bc5f4f536ca0c36a7afa272725908afdcaa7ad5dc26eb (942 files).
Production delta against 24l2: launch_r1/entry.py only; the verifier checks are unchanged and run only when stage is None.
Both branches record stager and staging_plan_sha256 from the verified request staging pin; capsule plans record the file hash, not the decoded JSON digest.
The 24k-shaped hook passes stage_host and writes host.json without native layout verification; a changed pinned plan still refuses before the hook.
Native direct bytes, archive bytes, member inventories and staged targets still refuse on corruption by name.
All 44 focused tests pass: 15 from 24j, 12 from 24l, 10 from 24n and 7 branch tests; four corruption fixtures test native staging under this ruling.
The scoped suites run 110 tests on each tree: 50 pass and the same 60 require missing archived fixtures; no new failures or skips occur.
Of those 60 errors, 35 require work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L3.json lists every missing fixture and matching base outcome.
admit(), identity(), mode p, donor binding, scene checks, routing, row legality, exclusions, sampling, scoring and DEFERRED evidence remain unchanged from 24l2.
The hook needs no native-layout adapter; the kit still needs the new tree archive/seals and the scene evidence and independent routing approval described in the retained reports.
UNCHANGED24L3.json records every file against 189df6ac and 24l2; both patches replay exactly, and the tar preserves all retained out reports.
Delivery archive: tree_rebuild_b24l3_96ff9a03.tar. CPU fixtures do not establish production PASS or launch GO.
All work stayed under J on trinity-2-28 with nice 10, one-thread libraries and a 19,000,000-KiB memory ceiling; no forbidden service, Git, deletion or other agent was used.
