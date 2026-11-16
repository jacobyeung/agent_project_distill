The read serves move, turn and pose through C8r's original response dispatcher and camera conversion. Every other recognized call, including unknown names, receives the fixed recoverable error response. The real decoder injects that response and continues.

- Dispatch policy: `code/policy.py:16`; call records: `code/policy.py:32`.
- The inherited camera conversion is `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py:173`. It uses the prepared tower geometry, with no own-pose fallback for scored items.
- The tower reads the read's verified RGB frames: `code/engine.py:96` and `code/adapter.py:69`. The adapter verifies selection and PNG hashes, preserves frame ordinals and timing, and uses the same anchors as dense frames.
- The public frozen tower weight, configuration and revision identities are the constants in `from113/work/tree/student_pilot/tower_read.py:18`; their file paths and receipt are recorded by the tower phase. No tower weights are fitted by this build.
- The checkpoint loader authenticates the prepared configuration and checkpoint heads: `code/engine.py:28` and the unchanged `read_runtime.py`. Scale is estimated from tower depth and the checkpoint's own predicted depth on this read's images. Gravity comes from the checkpoint's own head. No answer labels enter either computation.
- The original scale conversion and reviewed gravity guard remain active: `code/engine.py:109`, `geometry.py:24`, and `gravity_guard.py:16`. A gravity refusal yields an explicit zero-score item with no decoded answer; it cannot silently disappear from the denominator.
- Prompt records contain no ground truth: `code/adapter.py:69`. Labels live only in `SCORES.json`. The runtime builds prompts through the inherited trainer adapter.
- The production namespace binds only the new read inputs, the trainer tree, code, numerical libraries, frozen tower, base model and checkpoint preparation assets: `code/venue.py:117`. It binds no old evaluation mask or geometry asset. Historical inputs are confined to the separate proof-stage runner.
- The proof runner deliberately restores the original inputs and serving policy for historical equality: `code/proof.py:35`. Its CPU comparator rehearsal is not evidence of GPU equality.

The headline includes the refusal-policy disclosure on its own line with the primary. The report also states: "only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused".

Unchecked: real GPU prompt/cache/head parity, greedy decoding, the historical GPU repeat, full-corpus staging, and both remote return transports. The detailed line census is `out/UNEXECUTED.md`.
