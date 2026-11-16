# End-to-end reader (brief 04): ready for review, not yet for the parity read

Lane b04_e2ehook, trinity-3-30, 2026-11-16. Code `/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/`, heads `heads/scale`, `heads/selector`, tests `tests/`, proofs `out/proofs/`. CPU only; no GPU, no Orchard, no AWS used.

## Outcome
The reader serves every camera call from the in-call G3T tower, the own gravity head and the scale head, and serves ground/gap through a stage-1 socket (in-call SAM 3 on the raw name, the runtime's candidate producers, the learned selector head with a null slot, plain unprojection, a min-area box). Room calls are unserved and counted (room is a direct type). One `generate` entry, one prefill, the KV cache continues through forced response tokens (emitted by the call hook's forward), and the loader refuses any data file outside the manifest. A failed ground/gap call answers `error: <code>` with no fallback sentence.
- The selector head passes B6's kill bar on raw-name candidates (top-1 60.5% vs the logistic's 59.9%; AUC 0.940 vs 0.942).
- The scale head misses its bar: K1 distance 61.3 vs S4+G1's 62.9 (-1.6 [-4.1, +1.1]); on dev-S1 it costs displacement 9.3 points and distance 3.1 points against the deployed own-depth rule.
- K1's SAM 3 cache contains an alias table: 26% of its instances came from alias prompts. Removing aliases costs the logistic 2.8 top-1 points on K1 held-out.

## Proofs and tests (all run, 17 CPU tests pass: `cd L && /scratch/jjyeung/envs/p1cpu/bin/python -B -m pytest -q -p no:cacheprovider tests/`)
| Check | Result | Evidence |
|---|---|---|
| Hook vs job 170056, token for token | 927/927 calls detected with equal text and position; forced ids equal on 462/462 comparable calls (465 ground/gap/room calls kept only query digests) | out/proofs/REPLAY_170056_{suffix,nosuffix}.json |
| Tiny-model e2e, every call type | 1 prefill; cache length = prompt + ids - 1; cached logits = fresh forward; loader refuses outside and changed files; perturbing a head changes only its responses | tests/test_tiny_e2e.py, out/proofs/TINY_E2E.json |
| In-call stage 1 vs training tables | head inputs equal to < 1e-9 on a real K1 capture, alias and raw tables; ground and gap answer through the trained head | tests/test_stage1_k1.py |
| Heads | forward on real tensors; retrain bit-identical; sha256 mismatch refused; zero sockets leave the selector unchanged | tests/test_heads.py |
| Guard removed | the reader's geometry is the tree's ProfileGeometry over `ReaderContract` (the sealed validate compiled without its terminal up-axis statement); no read-path code evaluates or records the old checks. Lane diagnostics (tests/guard_diag.py) say the sealed check refuses 11 of 84 dev-S1 clips and the reviewed check 1 (d3/41254810); the reader refuses none and serves camera, ground and gap on a refused clip (tests/test_no_guard.py). The 10 sealed-only clips carry 19 distance items, answered at 55.3 in the job; the reviewed clip's 2 items need the GPU read | out/proofs/GUARD_VERDICTS_DEVS1_v2.json |
| EAT-1 dynamic run (lane b03's `eat1.run`, proposed unreviewed allowlist; tiny LM + trained scale and selector heads + K1 tower/SAM 3 stand-ins; 7 items, every call type) | A1 PASS (no data file outside the artifact); A2: one model entry per item and 0 injected tokens, FAIL only on 3 static findings in sealed tree formatters; A3 FAIL: 230 findings, 21 in this lane's code (frame-count and canvas shape constants 32/33/9/1000, eps clips, the call-length cap, the producers' lift floor 0.3, selector_inputs' 0.3 threshold), the rest in tree producers and formatters; A4 FAIL: 15 findings, none in this lane's code; A5: sandbox (i) PASS, cache proof (iii) PASS, perturbation (ii) FAIL only for the SAM 3 stand-in, a byte buffer that noise cannot perturb | out/proofs/EAT1_DYNAMIC_v2/EAT1_REPORT.{json,md}; adapter eat1_adapter/b04_tiny.py |

## Heads on K1 (held-out rooms, paired room bootstrap 10,000 draws, seed 20261116)
| Head | Metric | Head | Bar arm | Diff | Verdict |
|---|---|---|---|---|---|
| Selector run_raw (1931446b) | top-1 / AUC, raw names | 60.5% / 0.940 | logistic 59.9% / 0.942 | +0.6 [-2.7, +4.0] / -0.002 [-0.012, +0.009] | PASS |
| Selector run1 (09c1e6ba) | top-1, alias tables | 58.9% | logistic 62.7% | -3.8 [-7.5, 0.0] | FAIL |
| Scale (a90b5216) | distance MRA | 61.3 | S4+G1 62.9 (oracle 65.6) | -1.6 [-4.1, +1.1] | FAIL |
| Scale | scale within 20% | 91.2% | S4 87.7% | | better |
Reports: heads/selector/SELECTOR_HEAD_REPORT.md, heads/scale/SCALE_HEAD_REPORT.md.

## Price on dev-S1 (CPU, job 170056's 636 items; calls held at the scripted arm, headline labels; the recomputation reproduces all 634 decoded scores)
| Replacement | camera displacement | direction | rotation | abs distance | room |
|---|---|---|---|---|---|
| old runtime (recorded) | 82.3 | 94.7 | 75.7 | 54.7 | 65.0 |
| hook only | identical (token parity) | identical | identical | identical | identical |
| + scale head | 73.1 (-9.3 [-14.1, -5.0]) | 94.7 | 75.7 | 51.5 (-3.1 [-6.4, -0.6]) | unserved (0) |
| + selector head, raw names | needs dev-S1 SAM 3 on the read's frames: GPU read | | | | |
| + no depth cut | GPU read | | | | |
Files: out/proofs/PRICE_DEVS1_{old,identity,scale}.json, PRICE_DEVS1_scale_scale_paired.json, SCALE_HEAD_DEVS1.json.

## Decisions for ORCH
1. Scale: the head loses to the deployed rule, median(own depth / G3T depth), which reads the checkpoint's own depth head and so already lives in the weights. Default: keep that rule as the scale (fixed math on an in-checkpoint head) and train the scale head's own-depth gate in the leg; the head alone is not used in a claimed read.
2. Grounding: ship run_raw. The candidate producers keep their fixed constants (lift floor 0.3, linking radii); only the selector is learned.
3. Parity read: the step-544 export lives on AWS only, so its CPU first batch and the GPU read run there. The read needs arms hook-only, + scale, + selector (raw), + no depth cut on the 636 items; this lane builds that kit after the review and an ORCH GO naming the host.

## One reader (ORCH 1149Z)
`e2e_reader/core.py` `E2EGenerator(item) -> {text, tokens, finish, calls, audit, seconds, heads, scale, frames}` is the generator behind reader-harness's `read.py` interface: an `orchkit-read-v1` config supplies the artifact manifest sha256 (`e2e_reader/assemble.py` builds it on the export host), the frame layout and count (32 or 64; `check_layout` refuses a layout that differs from the export's training layout unless the config gives a reason), and the item list; `read.py` keeps scoring. The generator writes no answer: the scored answer is the model's own text.

## Hashes (sha256 prefixes)
e2e_reader: artifact.py 40735dfd, assemble.py 04f42cd1, callhook.py 09577596, core.py dbbda5b8, generate.py 088613c1, geometry.py 51c4aca2, grounding.py 36eb32b5, real.py 08419a2c, servers.py 3cd2e6db, stage1.py 54dabbda. tests: guard_diag.py 35b14741, guard_verdicts_devs1.py 16e74eec, price_agg.py ac0e6896, price_devs1.py 711136ab, replay_170056.py 22e73273, scale_devs1.py e0d19c24, test_heads.py b5d2c996, test_no_guard.py 00af83a4, test_stage1_k1.py 5c7e50e7, test_tiny_e2e.py c48f6216. eat1_adapter/b04_tiny.py d071b22a; EAT-1 report b2bf5fbb. Weights: selector run_raw 1931446b20f4ecd4ec41916bd2ca61238f23d43039c07a7ac64b5cb323d929cb, scale a90b521628fc52b41c676955f485e6771971acf30e4ec19cdf172474c6cbcbfa.

## Not done
- No GPU work: SAM 3 seconds per name inside the call are unmeasured (brief estimate 2 to 7 s); the real export's CPU first batch has not run.
- EAT-1 verdict: the remaining A2/A3/A4 findings sit in sealed tree code (producers, v3.14 formatters) and in shape constants; they need the reviewed allowlist (lane b03) or a ruling, not a reader change.
- Independent review (another model family) of the hook, the loader and both heads' training code: requested in the RESULT event.
