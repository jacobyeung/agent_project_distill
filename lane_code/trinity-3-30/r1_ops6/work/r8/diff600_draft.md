# step-400 rehearsal vs step-600 plan (RULING 0209Z item 4) - draft, numbers filled after m400
1. Namespace: 400 nsenter into a live rank (proven 02:06Z); 600 the trainer has exited, so hr2 runs in the rebuilt bwrap view (probe7 binds), rehearsed read-only only (probe8, 04:20Z): its rw bind of runs/ and the receipt write are first exercised at 600.
2. Receipt: 400 requires export-only (q3 346c4cba, p-export-only-v1) and expects handover rc 1 at the step check (no step-400 checkpoint), before any hashing; 600 requires the handover receipt (q2 f415c69d, p-handover-v1), which hashes every export shard and every checkpoint_000600 file (~113 GB): untimed until 600.
3. Window: 400 has no deadline (trainer keeps running; rc-5 retries every 300 s for up to 2 h); 600 runs between the m600 upload marker and the job end (A: 13:07:38Z -> 13:22:56Z, ~15 min), minus marker poll latency; a job end mid-run kills the srun step and leaves no DONE.json.
4. Guards: 400 save clock (age <= 5,700 s) and BUSY; 600 no clock (no writer), BUSY only if a checkpoint dir lacks complete.json; post-hash overlap check is trivially "no" at 600.
5. Concurrent IO: 600 the wrapper's slot copy reads the same checkpoint (node /tmp -> okh7/r/6ed2c7aa) while hr2 hashes it; 400 competes only with training.
6. Environment: 400 inherits the rank's environment minus distributed variables; 600 env -i with PATH and HOME=/tmp only.
7. Writes: both write only m<step>/{RP,h,r,e}.json beside the artifact; the slot copy takes checkpoint dir, inputs/ and binding.json, so it never sees them.
8. Watcher: 400 = exw.sh (poll 120 s, retry 300 s); 600 = exw6.sh (same code, POLL/RETRY env) planned with POLL=30 RETRY=60, armed from ETA-45 min.
