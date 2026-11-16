# CPU rehearsal commands

The harness has not passed a whole-worker run. Both recorded attempts stopped at preflight because the required interpreter and streamed inputs are absent. Production branch coverage remains unavailable.

All commands run from the build folder. They use the required interpreter with isolated mode and explicit coverage-path insertion inside the harness. Environment variables bound caches to this build before a real run; no installation or network access is needed or permitted.

```bash
export PYTHONPATH=/scratch/jjyeung/orch_n30/native_r2/work/pyextra
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/hf"
export TRITON_CACHE_DIR="$PWD/work/triton" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/tests/test_core.py
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/tests/test_guard.py
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode pilot --dest "$PWD/work/pilot_production_runtime"
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode full --dest "$PWD/work/full_production_runtime"
```

The run script verifies object hashes before extraction, checks the initial disk floor, binds logical paths through bwrap, uses the production NumPy overlay, and starts branch coverage inside the namespace. The model fixture calls real preparation, trainer-source authentication, init-spec checks, and processor construction. The fixtures supply prefill gravity from the real geometry manifest, deterministic depth scaled from the real caches, forward logits/heads, and token generation. They preserve actual parity, prompts, masks, geometry, scoring, projection, terminal receipts, and return-chain validators.

The source kernels are compiled with their real source filenames for coverage. This changes coverage attribution only; kernel ASTs and executable source bytes are preserved. The result pool is mapped to a build-local fixture directory; no external result is published.

The numerical test file must also run under the production NumPy overlay to establish the exact environment. Running it with the environment's default NumPy provides only an additional diagnostic. The harness itself refuses versions outside the required tuple.

The code archive and family are **drafts**. Filling `assets.small_objects[role=code].generation` and `.md5` after upload is necessary but insufficient for admission. Actual cache-bind reproduction, whole-worker execution, full-mode coverage, historical local-check authority, and operator review remain required.

The harness stages the inputs once under `work/rehearsal_assets/`, keyed by the code hash. Both modes reuse that staging tree and bind separate output directories. It refuses archive expansion beyond the build allowance and monitors aggregate run and build bytes while the worker runs. This path remains unvalidated because the required inputs are absent.
