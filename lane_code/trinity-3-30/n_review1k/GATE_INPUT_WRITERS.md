# Gate inputs and their writers (n_review1k, ORCH ANSWER 2125Z item 2; kit w34 7e23bbdd, tree t_e0470021, wrapper jn7.sh 98edfd9e)
Read by: gate.py (need() and LIVE/NODE lists), run_gate.sh (fetch list), spell.py. "kit" = X/n/b, "tree" = the job's p/s.

| gate input | read by (point) | writer, file:line | runs when |
|---|---|---|---|
| live/v.json | identity, d_population, admit test, census (host_receipt pin) | kit rv.py:256 put(live/'v.json') (bytes of $Q_NS/v.json, written by kit h.py:43) | after proof ADMIT, d.py, h.py; before the wait |
| live/identity.txt | identity, census, scene | kit rv.py:257 | same |
| live/WAITING_REVIEW.json | identity | kit rv.py:277 | same, when the wait starts |
| live/e0-e3.json | census, d_population, item3 | kit rv.py:224 (payload names rv.py:21) | same, before v.json |
| live/c0-c3.json | census (row keys) | kit cs.py:126-127 (emit) | cs.publish, kit a.py:120-122, on proof ADMIT |
| live/c4.json | census | kit cs.py:134 (= node c5.json bytes, cs.py:136-138; checked cs.py:189) | same |
| live/h0.json | census (pin chain) | kit h.py:39 put(live/'h0.json', hr.json); hr.json h.py:35; protected_census = file_pin(c5) cs.py:210 via h.py:34 | h.py, after d.py |
| live/s1.json, live/s4.json | scene_census | kit pl.py:282-283 | plan/staging (early) |
| live/s0.json | (fetched by nobody; not read) | kit pl.py:281 | early |
| live/s2.json | census, only when present | kit sv.py:171-179 (sv.publish) | NEVER: no kit step calls sv.publish |
| X/o/<job>_gate/population.json, indices.json, reader_filters.json, binding.json, receipt.json | d_population, P1_filters, item3 | tree r1_population.py:148, 150, 199, 155, 218 (bind_prepared into p/q/b); copied by jn7.sh:285-289 | after the frame audit; copy once WAITING_REVIEW.json is on X |
| X/o/<job>_gate/f.json | first_batch | tree production_proof.py:19 (first_batch_check, root/'f.json'); copied by jn7.sh:287 | after the forward |
| ADMIT.json | admit_test | W/w24z14/out/admit_test.sh on trinity-1-18 (run_gate.sh step 2) | gate time, from live v.json |
| request.json, frames.json (spell.py, info) | spelling line | tree s1_admission.py:173-181 (request.json), :257 (frames.json) | admit; node-local (p/q/p/...), not on X |

Required input with no writer: s2.json only. Its facts (per-stream verdict, 0 rows on every protecting status, 0 unresolved, admitted count) are in c4.json streams[s].status/counts/result, written by cs.emit, and the gate now reads them there (gate.py ed9594d4).

## What the real gate has that the end-to-end test set lacked (ORCH ANSWER 2143Z item 2)
| gate point | file the test set lacked | writer and when | route to the gate |
|---|---|---|---|
| d_population, item3, P1_filters | p/q/b/population.json, indices.json, receipt.json, reader_filters.json, binding.json | tree r1_population.bind_prepared (r1_population.py:148-218), right after the frame audit | jn7.sh:285-289 gzips them into X/o/<job>_gate once WAITING_REVIEW.json is on X; run_gate.sh fetches X/o/<job>_gate. Fallback: n_ops11 run_pull.sh (srun copy from p/q/b), then run_gate.sh --local |
| d_population, census | live/e0-e3.json | kit rv.py:224, after h.py and before WAITING_REVIEW.json (rv.py:277) | X/o/<job>/live (rv.py put), fetched by run_gate.sh |
| census, admit_test | live/h0.json (= node p/hr.json) | kit h.py:35-39, after d.py, before rv.py | X/o/<job>/live, fetched by run_gate.sh |
| first_batch | p/q/f.json (288 records) | tree production_proof.py:19 (first_batch_check in the forward) | jn7.sh:287 into X/o/<job>_gate; fallback n_ops11 pull |
| spelling line (info) | p/q/p/frames_*/frames.json, p/q/p/request.json | tree s1_admission.py:257 and :173-181, in admit | node-only: my work/fspell.sh (one srun --overlap read) or n_ops11 run_pull.sh adds both (small JSON) |
| admit_test | v.json, identity.txt (live; rv.py:256-257); h0.json and c4.json (live), sent to trinity-1-18 as in/h0.json and in/c5.json with in/offline_pins.json {sha256: path} (admit_test.py:151-162 reads the map; native pinned() checks each digest) | run_gate.sh step 2 (run_gate.sh 2143Z version) | X/o/<job>/live. Required checks: 19 ADMIT_MUST_PASS. Without h0, host_receipt_pin was NOT_RUN and the point FAILed (e2e run 1). With the map: host_receipt_pin, host_receipt_assertions, protected_census_pin_identity PASS (e2e run 2 with a SYNTHETIC h0, work/e2e2_run.out). The remaining NOT_RUN checks (native_admit, handover, continuation, training_components, sampler_binding, initialization_start, preparation_identity, full census, caller checks) read node-staged pins under /tmp and are not required by the gate. The tree and kit metadata it reads are on trinity-1-18 (w24z14 package; tree_seal and kit_inline_metadata PASS on 174134's v.json) |
Admit test inputs on trinity-1-18 (read 21:50Z): admit_test.py 7f89c911 reads TREE w24z12/work/tree_r1c (SEAL 9d2bbb8a = N's source_seal) and KIT w24z12/out/kit_n_go (seal 22db0727, an older kit), of which it reads only k/s.json: 9de53311, byte-equal to w34's k/s.json.
