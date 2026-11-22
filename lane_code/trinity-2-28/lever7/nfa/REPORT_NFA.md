# NF-A kit: the served step-544 tower read in two item orders, 150 dev-S1 items (token c8b836b4ae536; built and tested locally, nothing placed or submitted)
Kit: /scratch/jjyeung/orch_n30/lever7/nfa/kit (SHA256SUMS_NFA, 36 files). Parent: package b9ef552934627 (job 171253), byte-exact copy at trinity-2-28:/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/parent with return c82cb20f; 11/11 files match Orchard sha256.
## Reused byte for byte
- Payload 0.tgz: all 927 files except 9.json (the plan, which carries the token); the builder reproduces the parent byte for byte given the old token, operator and CPU runner. Bootstrap 0.py, 3.py, SUBMIT.cmd, a/1.json (inputs 025b4688, 27 GB already on Orchard), a/export.json. Served read: runner, launch loop, reader, tower arm, G3T memo on.
## Changed
- a/6.py (bundled 7.py), operator: two reads in one job, each its own worker process (fresh model and memo). Read 0 = 171253 read 0's order (distance, displacement, rotation, direction; ids in order). Read 1 = exact reverse (type sequence reversed; metadata/a/5.py reverses each type list when flag=1). Manifest built at run time from embedded canonical positions; fwd/rev id hashes checked against ITEMS_NFA.json. Pins: candidates_argmax, memo on for g3t, verify ids [] (RULING 0527Z).
- a/5.py, CPU check: parent check + the job's own run configuration with device cpu; each read through the job's own launcher line; read 1 stops once its worker bound the reversed order; read 0 runs its first real item (vsi590k_042608) and stops. Causes leave gzip+base64 (decode_nfa.py).
## Items (select_nfa.py, rule nfa-v1, ITEMS_NFA.json 3e495afc)
| type | scannet | scannetppv2 | arkitscenes | total |
| camera_displacement | 18 | 19 | 0 | 37 |
| camera_rotation | 19 | 18 | 0 | 37 |
| camera_movement_direction | 19 | 19 | 0 | 38 |
| object_abs_distance | 8 | 18 | 12 | 38 |
58 captures; fwd ids 35cb48e2..., rev 953fa8a9...
## Forecast: 1.34 H100-h expected, <= 2.5 allocated (budget 3). Each order 1,975 s of reads + 226 s load/warmup per process + 378 s staging = 4,810 s; one general job, 1 H100, 02:30:00. CPU check: general, 16 CPU, 200G, 03:00:00, no GPU.
## Bytes: 5,354,793 B new on /project; o_place.sh 7,091,076 B (sha 8317559e...). Returns ~2 MB.
## Tests: TESTS_NFA.log 25/25; LAUNCH_TEST_NFA.log (job's own launcher line locally, worker death cause returned encoded E70/E72); scorer reproduces 171253 baselines (82.33, 75.60, 94.67, 26.93).
## Scorer score_nfa.py (fixed): per type score per order, paired diff (rev - prod), room bootstrap 10,000 seed 0 (20261115 printed beside), share of changed answers, order check. FAIL if 95% CI lies at/beyond 0.5 from 0 or > 5% items change.
## Defaults: selector candidates_argmax (production pin); seed 0.
## Lane commands (kit/, T=.../orch_n30/tools; one Orchard call at a time)
1. sha256sum --check --quiet SHA256SUMS_NFA; fresh review; mirror over IB; append LEDGER_LINE.jsonl to lever7/work/ORCHARD_LEDGER.jsonl.
2. ossh < o_place.sh (prints 5354793). 3. ossh < o_check.sh (True 1 02:30:00; writes 2.json). 4. ossh < o_cpu.sh (CPU job id).
5. after it ends: ossh < o_cfetch.sh > ../ret_cpu.tgz (needs cpu_reads_passed; else decode_nfa.py a/c/1.log).
6. ossh < o_sub.sh (refuses unless CPU.json and 2.json bind, general empty, pool <= 75 MB). 7. o_mon.sh at most 1/min; ossh < o_fetch.sh > ../ret_g.tgz.
8. extract result.tar.gz to ../ret/g; /scratch/jjyeung/envs/p1cpu/bin/python -I -B score_nfa.py --returned ../ret/g --items ITEMS_NFA.json --out ../ret/scored
