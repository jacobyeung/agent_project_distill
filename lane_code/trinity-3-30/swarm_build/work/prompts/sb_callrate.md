# Task sb_callrate: call-rate and usage reader for routed-read returns
Workspace: /scratch/jjyeung/orch_n30/sb_callrate (write here only). Inputs copied for you under in/ (paths mirror /scratch/jjyeung/orch_n30/...; the original absolute paths are /scratch/jjyeung/orch_n30/<same relative path> on another node, so rewrite path constants to arguments; in/cont_ops16/work/c15/r1route/out3s/bases is a symlink to the absolute out3/bases path: point it at in/cont_ops/work/r1route/out3/bases).

## Background
The model (a 9B VLM) writes a chain of thought that may place routed calls (camera pose, object distance, room size, ...) to heads; the head's response is printed into the trace and the model should answer from it. A "routed-read return" is the output tree of one evaluation read (metadata/IDENTITY.json, metadata/reads/<n>/metadata/journals/*/*/items.jsonl, ...). Existing code that loads and pairs them: in/cont_ops16/work/c15/r1route/out3s/score_r5.py (pairs step-200 returns, A4/ret, against the registered step-544 reads in bases/b1 and bases/b2, room134 items in b2) and in/dist_diag/work/q1/{load.py,classify.py,phrase_traces.py} (classifies the 150 dev-S1 distance items by unit and wording, call/no-call). Scorers come from the package (h1eval.scorers under out3s/A/src). The room134 summary for step 200 reads: calls200 0, calls544 134, capped544 115.

## Build
A CLI `callrate.py --a <return root> --a-step N [--b <return root> --b-step M] --out DIR` (default pairing: B = the step-544 registered reads, exactly as score_r5.py loads them, verifying the same identity checks) that prints and writes JSON, for every routed type present in the returns (camera_displacement, camera_rotation, camera_movement_direction, object_abs_distance, room_size_estimation, and any other routed type found in the items):
- n items; call rate (share of items whose trace places at least one call of that type); capped rate (share whose call hits the call/length cap or ends truncated, using the same definition the existing code uses for "capped"; find it); usage (among items with a call and a parsed response, share whose final answer follows the response: equal after the type's unit normalisation and the tolerance the scorer uses, or derived by the fixed math the prompt asks for); answer rate (a final answer exists); score (the type's scorer);
- the same broken down by unit (m, cm, ft, in, mm; via scorers.unit_factor as load.py does) and by wording cluster (reuse classify.py's wording classes where they exist; otherwise the question template with numbers and object names masked);
- paired deltas A minus B per type with room-clustered bootstrap CIs exactly as score_r5.py's bootstrap() (seed 17, 10,000 draws).
Write a plain-text table (one line per type, then per unit and wording) and a JSON. Keep it read-only on the returns.

## Tests
- Reproduce the step-200 vs step-544 room134 numbers above (calls 0/134, capped 115) and score_r5.py's scoresAB/scores.json values for the camera types and distance from the shipped returns; fail loudly if they differ.
- Unit tests on synthetic items for call detection, capped detection and usage (answer follows response, does not follow, no response).
- A README.md (at most 40 lines) with the exact commands to run it on a new return root at step 400 and 600.
Deliver out/CALLRATE_REPORT.md (tests run, reproduction table, the step-200 vs 544 output) and out/sb_callrate.tar (code + README + tests, no data) with its sha256.
