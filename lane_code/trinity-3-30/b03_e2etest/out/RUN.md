# Running EAT-1 on a GPU against a real artifact (operator)

EAT-1 wraps any reader that exposes one `generate(frames, question)` entry (protocol: `eat1/run.py` docstring). The checks need about 2.5 h on one H100 for 200 items at 32 frames, and about 4 h at 64 frames (estimate, §4). The run needs an ORCH GO naming the card or job; this lane launches nothing.

## 1. Kit
- Code: the lane folder's `eat1/` package (`artifact.py`, `hook.py`, `scan.py`, `closure.py`, `run.py`, `allowlist.json`, `adapters/`). It needs no change to the reader under test.
- Python: the reader's own environment, plus `bwrap` on the host for A5 (i). Check `bwrap --version` before the run; without it, skip `--sandbox` and report A5 (i) NOT RUN.
- Optional: `strace` for A1's second witness (`--strace-log`, §3).

## 2. Inputs
1. **Artifact manifest** (`eat1-artifact-v1`, `eat1/artifact.py`). List every file of the claimed checkpoint by sha256 and role: full_weights shards, `heads.pt`, `artifact.json`, tokenizer and config files. Also list each frozen tower weight file the read loads (G3T `model.safetensors`, SAM 3 weights) with role `tower`. Then declare the modules under `reader.model`: `lm`, `vit`, each head (`auxiliary_heads.pose` → `pose_head`, `auxiliary_heads.depth` → `depth_head`), each tower and each connector, plus any `call_handler`. A file that is not in this manifest fails A1 when the read opens it.
2. **Items** (`items.jsonl`): 200 items covering every type that emits a call, as `{"id", "type", "frames", "question"}`. Rank by ReVSI first (USER 2026-11-16): 50 camera displacement, 50 movement direction, 50 rotation and 50 object absolute distance, from ReVSI (official999) where the type exists and from dev-S1 otherwise. Room size is a direct type (ORCH 1227Z, TRACE_RULING_20261115.md): add 20 room items only to count unserved room calls, which A6 prints as that type's call rate. Keep the training frame layout and state the frame count (32 or 64) in the item file name.
3. **Reader adapter.** For C8r: `eat1/adapters/c8r_native.py` (it mirrors the unflagged arm of `nomdg.run`; UNTESTED on GPU, so run one item first, §3). For the next leg, the b5 tree refuses the legacy reader entries (`evalpath/runtime.py:55`). Its routed reader does not exist yet, so a next-leg EAT-1 run needs its reader plus an adapter in the same shape.

## 3. Commands (on the assigned node, from the lane kit copied to node-local /scratch)
```
cd <kit>   # contains eat1/
export PYTHONPATH=$PWD
# one item first: CPU-side load, then a single-item GPU read, to check the adapter
python -m eat1.run --reader eat1.adapters.c8r_native:make_reader \
  --reader-kwargs '{"out2": "<out2>", "request_dir": "<dest>", "artifact_manifest": "<ARTIFACT.json>", "device": "cuda:0"}' \
  --items items.jsonl --limit 1 --out out/eat1_first --code-root <tree> --code-root <out2>
# full run: observation + static scope + A5 (i) unmounted rerun + A5 (ii) perturbation
python -m eat1.run --reader ... --items items.jsonl --out out/eat1 \
  --code-root <tree> --code-root <out2> --input-root <frames_root> --sandbox --perturb --perturb-limit 50
# optional A1 second witness: run the same command under
#   strace -f -e trace=openat,open -o out/strace.log python -m eat1.run ... --strace-log out/strace.log
```
- Outputs: `out/eat1/EAT1_REPORT.md` (PASS or FAIL per clause, with offender file and line), `EAT1_REPORT.json`, `ITEMS.jsonl` (per item: seconds, model entries, violations, module runs), and `a5_sandbox/`.
- A5 (iii) cache proof: a reader that reads a cache sets `reader.eat1_cache_proof` to an `eat1-cache-proof-v1` file of at least 50 live/cached items. A claimed number still comes from the live run.
- Read data from node-local /scratch only, and write outputs there. Copy the report off as one archive.

## 4. Time estimate (one H100, batch size 1, greedy)
Source: Orchard job 170056 read 2 arms × 636 dev-S1 keys in 2:35:07, about 7.3 s per item including load (`distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md:47`).
| Pass | Items | Estimate |
|---|---|---|
| Observation (line tracing on reader code: ×1.5–2 on the Python share) | 200 | 35–50 min |
| A5 (i) sandboxed rerun | 200 | 25–30 min |
| A5 (ii) perturbation: 3 seeds × each head and tower (pose, depth, G3T, SAM 3 = 4) | 200 | 12 × 25 min = 5 h; with `--perturb-limit 50` (order items so the first 50 cover every call type), 1.2 h |
| Total with the 50-item perturbation subset | | about 2.5 h |
At 64 frames the prefill visual tokens double. Assume 1.5–2× per item, so the total is about 4 h. A run on a tiny model takes seconds (CPU baselines: `work/c8r_tiny/run5`, `work/b5_gf1_tiny/run2`).

## 5. What a PASS requires
All five clauses report PASS. Per type, A6 reports call rate, the heads behind each response field, and seconds per item. A run where any clause is NOT RUN reports INCOMPLETE, never PASS. A dispute over a clause is decided by the user's wording (brief `qs/03_e2e_acceptance_test.md`, ORCH 1155Z ruling 5).
