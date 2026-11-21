# Review gate check for vehicle N's launch job (ORCH RULING 0211Z items 4-5)
Files (trinity-3-30 /scratch/jjyeung/orch_n30/n_review1i/work/gate; copy on trinity-1-18 /scratch/jjyeung/orch_n30/n_review/r1i/gate): gate.py, run_gate.sh, test_gate.py, USAGE.md; sha256 in SHA256SUMS.
## Run (any lane on trinity-3-30, minutes)
`bash run_gate.sh <job id> /scratch/jjyeung/orch_n30/<lane>/gate_<job>` (new empty dir). It makes one Orchard call (tar of X/o/<job>/live and X/o/<job>_gate; stops on a host-key line), one trinity-1-18 call (admit_test.sh on the job's v.json + identity.txt, output in W/w24z14/work/gate_<job>_<stamp>), then runs gate.py. Last line: `GATE ALL PASS` or `GATE ALL FAIL`; exit 0 only on PASS.
By hand: `python3 -I gate.py <dir with live/ copy> <dir with _gate copy> --admit ADMIT.json`.
## Points (one GATE line each, with the registered values)
1. identity: WAITING_REVIEW.json identity = identity.txt, v_sha256 = sha256(v.json).
2. d_population: population.json r1-population-v1 complete after_all_filters; v.json r2_sampling pins = population/indices bytes (binding.json too); routing kinds sum 43,101 = prepared receipt routing count = e2 admitted_rows; routing offsets exactly range(43101); 5e35c3ce named in the prepared routing stream or e2.databases. Key set c2ba56c5 follows from the same database bytes (evidence run 173881) with P1 empty.
3. P1_filters: reader_filters.json refusals.routing == {} and its sha256 pinned in population.evidence.
4. census: c4 r1-protected-census-v1 final PASS with identity; per stream protected_rows 0, keys file [] and pinned; s2 PASS with 0 in benchmark/dev/R0/withheld/K1_heldout/official; e0-e3 protected_rooms 0; admitted equal in c4, s2, e*.
5. item3_counts: per-type rows/step 64 x n/43,101 within 10% of P 18.25/15.88/12.53/16.34/1.00 and units >= 0.90 (ANSWER 0553Z); vqa <= 189,069, pointing <= 18,116.
6. first_batch: f.json c1-first-batch-check-v1, 288 records, ranks 0-3, unique (step, microstep, rank), all four streams, tokens > 0, finite loss, no error.
7. admit_test: ADMIT.json on this v.json bytes, tree 9d2bbb8a, branch legacy_C_prime, 19 required checks PASS, only review_verdict_identity/native_admit may FAIL and only with INDEPENDENT_REVIEW_PENDING; NOT_RUN (bytes not offline) listed.
A missing file fails its point. Tests: `python3 -I test_gate.py <standin_verified/ADMIT.json> <negative_verified/ADMIT.json> <new dir>` -> TEST ALL_OK (pass case + 9 single-point negatives), run with Python 3.6 (3-30) and 3.12 (p1cpu, 1-18).

## Point 8 scene_census (n_review1j, 2026-11-21)
Reads live/s1.json (kit a.json, the admitted census prepare compares with) and live/s4.json (kit o.json). Passes when per source whole = admitted + outside, whole and outside equal the row-key-proven values (SCENE_WHOLE, SCENE_OUTSIDE in gate.py), the outside keys' flags sum to the outside counts, s1 holds the admitted numbers with exact_rebuilt_population true and population 'admitted', and s1's outside pin is the sha256 of s4. run_gate.sh fetches s1.json and s4.json. GATE ALL needs 8 of 8 points. Tests: TEST ALL_OK with the pass case + 11 negatives (scene_outside_differs, scene_s4_absent added); on the real held-node a.json/o.json of fix10 the point PASSes.
Point 4 census (n_review1j, 17:50Z): also requires per stream c4 result.resolved.unresolved == 0, empty result.protected_by_resolution, and K1 exposure (result.exposure.K1_heldout, status 'exposure recorded, not protected') equal to K1_EXPOSURE (pose 2,663, routing 841; none for vqa and pointing, which K1 protects). Tests: pass + 13 negatives TEST ALL_OK (3.12, 3.6).

## n_review1k copy (/scratch/jjyeung/orch_n30/n_review1k/work/gate)
Same gate.py, make_review.py and test_gate.py as n_review1j's kit. run_gate.sh adds step 4: spell.py prints which name of the job folder (/tmp/q_22c714e1 or /tmp/jjyeung/q_22c714e1) frames.json and request.json carry (ORCH ANSWER 1928Z item 4). It is informational and does not change the exit code. If neither file was fetched, read them on the node with srun --overlap.
