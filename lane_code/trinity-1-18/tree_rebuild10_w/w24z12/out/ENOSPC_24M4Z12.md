Both review findings pass offline on the sealed kits. The build used the real shell EXIT finalizer and the strict resumable sink for the old/new controls.

| Finding | Fail-before: 24m4z10 | Pass-after: 24m4z12 | Logs |
|---|---|---|---|
| 1. Ordinary checkpoint drain | No pending ordinary checkpoint obtains a receipt after either an explicit or nominal stop. | Steps 10 and 2 upload in that order after step 30's stop checkpoint, the stop export, other exports, logs, archive and the durable u-log prefix settle. A failed stop also releases the queue. Interrupted ordinary parts resume from their acknowledged Range; the reserve blocks further ordinary work. A fresh live pass drains the same settled queue. | work/build24m4z12/new_verified/RESULT.json and each case's shell.log, sink/events.jsonl; PRIORITY_CONTROLS.json |
| 2. Live log screening | The probe token survives unchanged in live/j2.log, live/j2.err and the other four log tails. | Every live log tail passes through the kit's sealed screen with k/g.json and b/wh.json; the transformed token replaces the probe before publication. | work/build24m4z12/new_verified/RESULT.json; after_success/x/o/41/live/ |

Ordinary checkpoints remain held until the final priority pass has attempted each publication. A snapshot binds settlement to the stop request, nominal-stop state and checkpoint/export/report markers. Both the copier and each writer request reject stale settlement; a new export interrupts an in-flight ordinary part before the next request. The ordinary budget ends at the earlier of archive_due and data_deadline. The 150-second reserve and allocation deadline remain unchanged.

The u publication retains its sealed four-part design: its durable prefix settles before ordinary checkpoints, and its reserved final tail records the subsequent retries after the final pass. The new ordering does not freeze that final tail early or alter completed parts. A final checkpoint failure is never relabeled as an ordinary checkpoint. Empty or completed ordinary queues do not add a checkpoint phase.

All required suites pass: current (8), archive (4), legacy (5), ENOSPC/refusal/recovery, signals, wrapper forwarding/race/exception, core (7), advanced (9), real EXIT, final-loop, strict-sink malformed-range negatives, both tgcs controls, E3 offline (17 checks), Trinity fake-session, set_stop and stop-policy. Evidence: work/build24m4z12/ALL_SEALED.json, SUITES_SEALED.json, e3_sealed/RESULT.json, trinity_sealed/RESULT.json and findings_sealed/RESULT.json. FAILURES.json preserves the setup/assertion failures and their output; no unresolved gate remains.

The full comparison hashes all 192,840 members of baseline archive 15cdc1273ff7a1c794c79c895505d08a5a1e325b21029d3606eac999f5efa181. Only b/o.py, b/pc.py, b/pc.sh, k/y.json and seals differ in each N kit. Against 24m4z10, only b/pc.py and seals differ. Q, QD, rcj and both trees are unchanged; the tree seal is 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b. See DELTA.json and SCOPE.json.

E3's k.tgz and pins match the final GO=false kit. e3.py, observe.py, run.sh, e3.sh, trinity.py, trinity.sh and readback.py are byte-identical to 24m4z10. The supplied tgcs_900004 evidence has 16 receipts whose hashes match their local part bytes, including u; ckstop reused ck00. The unchanged transport/session files preserve the stated carry for job 173966; this build made no remote request and claims no new real-service rate or resume result.

The stop setting remains 3,600 seconds. The planning rule remains 2 x (W + B/R) + 150 <= stop_before_seconds - 15, using measured write time W, bytes B and real rate R; the 1.5x variant requires qualifying real resume evidence. No training or numerical stop-window approval is inferred from offline fixtures.

| Kit | Old seal | New seal |
|---|---|---|
| out/kit_n | fb5c7f62c91b55cf0b432e65fd79d582c581b1fa27aa5b23ef36bb8001fab867 | 402a2fe23831c449e46cdb0b80fa9cde41e0bd5abf6d9edb57a106c0d5b202f2 |
| out/kit_n_go | 5c8ba4b4dc52c08388b4e911dd77ea3a380a79a53eb6389010ff9fb666fe2b4d | 22db0727c2eb58c14cd14d371799b9e508264ab201155ec68243597bb9598444 |

y.json, gc.py, o.py, pc.sh, the session-cache format and session handling are unchanged. SHA256 values follow; session rows hash the exact unchanged function source.

| Unchanged file/source | SHA256 |
|---|---|
| k/y.json | 9ce253964ef8d060ae99be248dab4d743035ef61fd49ee3a5b9642f543a434c2 |
| b/gc.py | 8d9fcaa12efd038debd78853ab6eae0fbccb0f15c843fe4b7241d28c1cc60949 |
| b/o.py | 977268cd8e59f956ac3383acd7d55f68ef19a276b042cdfcb75169ab6a3254ec |
| b/pc.sh | 3fb410443e0e4ad3082290045b619d9107f06822d0e891c001b6e2bb3eb8ebab |
| k/n.json | 2786173ecd83ad5eb5e21d17b1be255c54484cd9e544b33ebaf5e06c1a6fe2a2 |
| e3/e3.py | c8ad02a3eb1ff223cb51441e6313d1360620ffb686604f0bf5552d9a810760ab |
| e3/observe.py | d52a715764c26f1a666b85f6002bfd32318f72b4e71b96f31e24634aff0f52f2 |
| e3/run.sh | 98a27aae6fc5d467825aaa9a6be62d1732334f4f03bb7fb1ad85ddae30f1cc73 |
| e3/e3.sh | 7bc226ac254ff641893e8b28cce3d6b96340bb84240a96181f3406cb16296497 |
| e3/trinity.py | 845e64d5b81db45803892920fc49e4e4a3a72414054cd922fb7904daf048c5e5 |
| e3/trinity.sh | 4335d3d21de10fa316da01bd547b5393a5b9a0585c2ea66ee40b40b2382e6edc |
| e3/readback.py | 238ea609ea8124cedd3a12b944e5ebd3cbaa8e4bd086d25a96429da8e31ee0e6 |
| jn3.sh | 90ba554022dd1765785073e80e133f2a2036a8c032743ba746a2958546a930af |
| pc.py:__init__ | 82ea112d9840dcc5e2431bce07c9fbcf4b770405f73b2da5e42cf1614cc7cef3 |
| pc.py:validate_sessions | 0c0f299d9c8bd98d6146581db79a7840c7ad1fcd6856fc2dd167354131c0ede7 |
| pc.py:cached_sessions | e2e6b7375ef2909a111d3f4cff88b75a218ea75d702b65c02e4f6b83bc14d54b |
| pc.py:session_bytes | 224a262d3f58f21e7c334d18985fa69100ae99ff184b9ef3a18ba5273b080d7d |
| pc.py:atomic | 9d33e3cbfe1f125683360fcb0d545d1d8aca5dee94b98e42347b4270a31a9286 |
| pc.py:writer_main | 63425db5d3c88c2c62b60e2de59b5431907aad8f6e186bc1982a1df1080c6bf4 |

The old/new descriptions above are required controls, retained as evidence rather than revision history.

The paired exit controls also produce byte-identical private fake-session caches: SHA256 ab354790d24735878b93c6dcd50b1b05044e48c6bea5f49ec2fcc4963841670e. The fixture mapping contains no real session capabilities.
