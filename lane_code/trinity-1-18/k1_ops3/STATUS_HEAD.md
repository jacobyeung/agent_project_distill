# k1_ops STATUS — operator k1_ops7 (Devin, trinity-1-18, from 12:24Z). Events folder events/k1_ops3/.
Updated 2026-11-16T12:28Z (k1_ops7).

## Now
- JOB 170235 (a15_cot_apb7e31d84a90c62f5) submitted 12:26:18Z on Orchard general on ORCH GO 1221Z; PENDING (Resources) at submit. Batch d1553118 (pool copy /project/community/jjyeung/okh7/b7e31d84a90c62f5/a7e31d84.d1553118.sh, sha verified). --time 03:00:00, allocation 10800, reserve 3000. Submit script work/partb/submit7.sh, output work/partb/SUBMIT7.out. Ledger line added. RESULT 1226Z/1227Z sent.
- WATCH (ossh): `TZ=UTC squeue -j 170235; sacct -j 170235 -X --format=State,ExitCode,Elapsed,Start; ls -la $P/170235/` every 1 min after start until canary lands, then 5 -> 10 min.
- Deadline risk: if 170235 is still PENDING at 14:44Z its limit would end after 17:45Z (ORCH 1102Z) -> before then ask ORCH / scontrol update TimeLimit is NOT enough (budget is in a.json); default: scancel at 14:44Z and build the deadline variant (step 3 below, build7_d3000 exists).
- Next: steps 5-8 of k1_ops6's list below (canary -> final return -> convert -> downstream -> report).

