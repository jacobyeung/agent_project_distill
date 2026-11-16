# Routed pilot 169605: distance refusals, runaway decode, room unit

Debug agent, 2026-11-14, trinity-2-18. Evidence: the fetched return (unpacked in `work_debug_distance/ret/`), the reader files (hashes equal BUILD_RECEIPT), and the trainer tree (all 792 files equal RUNTIME_TREE b01ce449). Replay: `work_debug_distance/replay_universe.py` writes `REPLAY_UNIVERSE.json`.

## A. Why the grounding calls are refused: (b), a defect in the reader
- The error comes from the sealed runtime `student_pilot/routed_features.py:290-294` ("requires a fixed named candidate universe": the first ground call of a session finds the name outside the universe or the universe empty) and `:312-313` ("outside the fixed candidate universe": a later call after the cache was built from the universe). Both messages are one check, `name in owner.config["candidate_universe"]`, made before any mask or mode is touched. live_instances314.py:120-127 calls it; trace_format313.py:29 wraps it as `error: …; answer directly from the video`.
- The universe is `sorted(source.names)` (ground_v3.py:71). The reader sets `source.names = normalize_name(candidate_names(question, options))` (perception.py:104,123,129). `candidate_names` (s1_grounding.py:23-27) returns only those **keys of the 8-key VSI-ScanNet vocabulary** (`trace_format/vsi_scannet_vocab.json`: bed, chair, counter, door, lamp, refrigerator, table, trash bin) that occur in the question text. Their aliases (desk, trash can, mini fridge, …) are ignored.
- Admission checks a different list: the capture's normalized cache phrases (nomdg.py:84-95 → perception.py:55-59,92-93; the same check runs again at runtime, perception.py:189-192). The bound request computed `mask_operand_refusals={}` this way (native_worker.py:181). The earlier audit's harness modelled only this check (work_pin_graph/harness.py:105).
- Pilot records: vsi590k_161825 asks for "the refrigerator and the bucket", so the universe is [refrigerator]. The refrigerator is served and the bucket is refused. vsi590k_161841 asks for "the microwave and the printer", so the universe is empty and both are refused. The replay reproduces both codes exactly.
- This is not a perception limit. The frozen cache for d2/ca3b651c23 holds every phrase with proposals: bucket 11 instances in 7 frames (presence 0.07-0.16), microwave 45 in 6, printer 122 in 7.
- Verdict: the reader is defective. It reuses the MDG-era 8-category `candidate_names` as the routed candidate universe, while admission, the spec (lines 41-43), the scripted programs and the leg's training rows all use open-vocabulary names. In a 165-row PK sample of routing DB r16, 268 of 330 grounded operands lie outside the 8 keys. The spec's own "table lamp" example is refused at runtime (vsi590k_163082). The runtime's refusal of names outside a supplied universe is designed; the universe the reader supplies is the defect. The model's later behaviour (C) is a consequence.

## B. Items affected (CPU replay of the scripted grounding requests against cache + runtime universe, in runtime order)
| Distance (150) | both served | one refused | both refused |
|---|---:|---:|---:|
| all | 14 | 66 | 70 |
| d1 ScanNet (30) | 5 | 16 | 9 |
| d2 ScanNet++ (73) | 3 | 26 | 44 |
| d3 ARKitScenes (47) | 6 | 24 | 17 |
- The cache-phrase check refuses 0 of 300 operand checks. The universe check refuses 206: 187 "requires", 19 "outside". Most often refused: tv 19, heater 15, stove 13, toilet 9; alias refusals: desk 3, trash can 3.
- Room (36, all d1): `<ground mode="room">` carries no named operand and no mask source (nomdg.py:35-38), so none is affected.
- Not replayable on CPU: what happens after a name passes, namely lifting, policy selection and "not seen". That needs per-capture G3T geometry, and the return holds it for only 5 of 84 captures.

## C. The runaway
- Trace (161841, unflagged): after two refused grounds the model emits `<gap a="microwave" b="printer" rule="box_grid_5cm">` and receives `not seen`. The gap code returns not seen for unresolved operands (box_v313.py:226-228). The model then writes "The box gap is not seen, so I will give their box distance." and repeats the same gap call. That makes 198 identical gap calls, `finish=call_limit` at 200 calls and 14,754 tokens, with no `</think>`.
- Training never showed this state. In 165 sampled r16 distance rows, 0 contain an error, not-seen or unresolved response, and the row generator stops before the gap when a ground fails (box_v313.py:388-393).
- Limits in the loop: `max_calls=200` (carrier_c1_decode.py:432, checked at carrier_c1_batch_decode.py:136-137); a token cap of `min(16384, context−prompt)` (perception.py:227 and request max_new_tokens in native_worker.py:71 pass 16384, and the sealed decode refuses any explicit cap below 16,384, carrier_c1_decode.py:291-293); `MAX_CALL_TOKENS=96`, the call-parse window (carrier_c1_decode.py:39); and the job's `stall_seconds` 1200 and `gpu_seconds` 2400 (CONFIG `limits`). There is no repetition stop, so 14,754 tokens were allowed: the call limit (200) fired before the 16,384-token cap.
- `capped` is false because evalpath/run.py:83 counts only `max_new_tokens` and `context_exhaustion`, not `call_limit`.
- A per-item limit matching the direct read cannot use `max_new_tokens`, which has a floor of 16,384. Set it in `perception.generate` (perception.py:221-229) as a logits processor through the existing `logits_processor` slot (carrier_c1_batch_decode.py:104-105; items pass no tap, nomdg.py:409). After 2,048 generated ids without `</think>`, it forces `\n</think>\n\n`, then allows at most 64 tokens, then forces EOS. Bind it in the request. A cheaper pure bound is `max_calls≈8`, which the sealed `generate` accepts.
- The scripted arm needs no limit. It does not decode; it runs at most 3 fixed calls (perception.py:337-344).
