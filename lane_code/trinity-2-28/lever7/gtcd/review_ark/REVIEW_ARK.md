# REVIEW_ARK: GTC-D ARKit unit (fresh review, trinity-2-28, 2026-11-22T01:50Z; read-only, no d value read)
## Verdict: NO-GO for the ARKit launch. The code is sound, but ARKit is not reproduced, so there is nothing to launch.
The decode finished at 01:41:08Z. All 18 captures are SHA_MISMATCH, 385 of 576 anchors reproduce, and frames/ is empty
(arkit/DECODE_ARKIT.json status). Every one of the 191 mismatches has max_abs 1 and touches 1-2 pixels: the right member was
decoded, but its bytes are not the served ones. The probe's 2/2 match (probe/PROBE_RESULT.txt) was luck at a ~67% per-anchor rate.
k6 made the served anchors on Orchard with its own venv (k6bin/bin/k6job.sh:5,13). The cv2 4.10.0 here, in both local envs,
gives 21/32 on 43828324, and disabling OpenCV SIMD did not change that. ORCH ANSWER 2341Z item 2 therefore applies: report ARKit
as not reproduced, substitute nothing, and read the ScanNet and ScanNet++ unit alone, labelled that way.
1. Decode and stride: PASS (code); FAIL (outcome: 0 of 18 captures reproduce).
   - warule.py:8-23 equals wa.py:95-103,159-168 (inflate, IMREAD_COLOR, rotate, 2.5x INTER_CUBIC, PNG 3). Picks use wa.py's
     nearest member within 2 ms (zipcd.py:56-64, fetch_arkit.py:119-124, decode_arkit.py:40-46).
   - Stride is 2 in traj rows (gtc_common.py:54, plan_arkit.py:45). Misses are 0 in all 18 captures (fetch_cause.jsonl).
   - A capture with a mismatched anchor goes to frames_rejected/ and nothing is substituted (decode_arkit.py:76-86).
2. Kit diff: PASS.
   - frames.py, seeds.py and the 4 old tests are byte-identical. SHA256SUMS_GTCD and SHA256SUMS_GTCD_ARK both check.
   - track.py changes only its env defaults and adds pairing_check (track.py:242-257,280). Frames resolve from the manifest's
     own folder (track.py:346), so arm d is identical across units. dense.py adds only the ARKit-alone guard (dense.py:197-204,235-239).
3. Relift: PASS.
   - reading_d checks the bars in order and applies the clarification (relift_t.py:95-110). Each population has d-a beside d-b,
     its own reading and a label (relift_t.py:324-353,392-410,511-520).
   - Pooled is read only when both units are complete (relift_t.py:501-504). a..b are asserted equal to RELIFT_GTCB.json
     (relift_t.py:448-458,508), and --out cannot overwrite an earlier relift (relift_t.py:488).
   - Tests not rerun (they write under work/; relift tests take 759 s and 779 s); logged runs pass (work/kit_ark_tests/*.out).
4. Launch: PASS.
   - The reviewed safeguards are all kept: host refusals, /scratch only, the seal check, two nvidia-smi reads, vnice off 0-13,
     timeout 5400, KILLED blocking a rerun, and every child's rc and stderr logged (launch_gpu.sh:44-64,67-107).
   - The outputs cannot collide (launch_gpu.sh:56-62, track.py:242-250). The forecast (~28 min, ~21.7 GiB peak on one 49 GB card)
     is plausible but moot, and it was never rehearsed on real ARKit frames.
5. Governor: PASS.
   - Root starts stopped, never execs (stage_arkit_apple.sh:23; stage.log root_state=T); ratelimit in path (:25); register rc 0 (:37-39).
   - The record was renamed .done only on PIPE_RC 0 0 0 (:47, rc_fetch.txt, streams/lever7_gtcd_arkit.done.1795311297).
   - There was no retry: no REQUEST_FAILED event, and 12,587 requests = 18x2 + 12,551. The retry is bounded at one (fetch_arkit.py:82-94).
6. Run or readability: no crash path found. With ARKit absent or no_ok_capture, the relift reads the ScanNet unit and marks arkit
   and pooled not_read (relift_t.py:363-370). Its label would not name the cause, though. Running dense.py on the empty frames/
   would also mark ARKit SOURCE_MISSING (dense.py:103-104), which hides the SHA_MISMATCH.
## Required fixes and actions
- F1: Do not run dense.py or the GPU pass for ARKit. Report ARKit as not reproduced and cite DECODE_ARKIT.json (18/18
  SHA_MISMATCH; 191/576 anchors off by 1 grey level on 1-2 pixels). Read d on ScanNet and ScanNet++ only, labelled that way.
- F2 (orchestrator ruling, needed before any d value): the next step can only be either (a) to rebuild k6's Orchard cv2/numpy build
  and re-decode the fetched raw/ with no new stream, or (b) a registered pixel tolerance. Either one amends the registration.
