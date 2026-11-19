# Using so_pack for step 600

`pack.py` is an opt-in local release gate with `build`, `check`, `place`, `fill`, `submit`, and `all`. Its sibling `pack_probes.py` must stay beside it. The supplied packages **do not pass the requested strict all-files privacy policy**. Original r10 source deliveries and authenticated local fill/dependency mirrors are also absent. Nothing is placed or submitted until these prerequisites pass; there is no privacy bypass.

Prepare one JSON config using `config_step600.example.json`. Pin the existing `build_r10.py`, its complete step-600 binding, source deliveries under its `KROOT`, and the ordered export/preparation/dependency mirrors. Each mirror records its original logical path, local `/scratch` path, byte count and SHA256. Keep builder stage/report/output paths inside the config's workspace. The wrapper calls the builder unchanged; it does not reconstruct missing authenticated source archives. `build_r8.py` and `build_d.py` also have adapters. Older hardcoded-root builders are refused.

Set `CUDA_VISIBLE_DEVICES=""`, `OMP_NUM_THREADS=8`, `MKL_NUM_THREADS=8`, `OPENBLAS_NUM_THREADS=8`, `TOKENIZERS_PARALLELISM=false`, and `PYTHONDONTWRITEBYTECODE=1`. Use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, prefixed with `nice -n 10`.

Build once, then read the explicit token from `BUILD_STATE.json`:

```sh
nice -n 10 "$PY" -I -s -B "$L/pack.py" build --enable --config "$L/work/600.json"
```

With that token, one command validates the build, runs all local gates, and prints the exact place/fill/CPU-then-GPU-submit ossh commands:

```sh
nice -n 10 "$PY" -I -s -B "$L/pack.py" all --enable --reuse-build \
  --config "$L/work/600.json" --yes --token TOKEN
```

The default prints commands. Production execution additionally requires `--execute-remote`; it uses the configured ossh once per phase and stops at the first failure. Submit always requires `--yes` and an exact explicit token. The existing-build option preserves that confirmed token instead of minting another. A fresh `all` calls the builder first; its randomly minted token cannot be confirmed in advance. Inspect any failed attempt before taking further action; the tool never retries it.

Local checks cover shipped-byte hashes, bundle equality, isolated imports and real fill through authenticated path mirrors, preserved env/policy archives, header/member/policy resolution, native planning/stub rehearsal/memory bounds, duplicate-layout row metadata, process guard/write/dispatch, early-error capture, and native read-runner stop/end behavior. Missing mirrors fail locally. `check --audit` gathers failures but cannot grant release. Extend `forbidden_extra` for additional project/model/method terms; the built-in policy cannot be reduced. Default mirror-read budget is 256 MiB; large local reads need separate authorization and a suitable workspace.

The tool does not certify the Orchard namespace, job venv, real export restore/RGB rehearsal, live queue/pool, CUDA/H100 execution, training-rank shutdown/export, model quality, or scores. Native Orchard CPU checks still run before GPU submission. Direct/facing/VSTI kit builders were not supplied. See `ORCHARD_ONLY_CHECKS.md`, `CHECK_INVENTORY.md`, and `DEFECT_MATRIX.md` for exact scope. No remote operation was tested in this dispatch.
