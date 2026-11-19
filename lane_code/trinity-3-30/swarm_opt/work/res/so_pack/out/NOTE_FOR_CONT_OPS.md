# Using so_pack for step 600

`pack.py` is an opt-in local release gate with `build`, `check`, `place`, `fill`, `submit`, and `all`. Keep `pack_probes.py` beside it. The supplied packages **do not pass the strict all-files privacy policy**. Original r10 source deliveries and authenticated local fill/dependency mirrors are also absent. Nothing is placed or submitted until these prerequisites pass; there is no privacy bypass.

Set `L=/scratch/jjyeung/orch_n30/so_pack` and `PY=/scratch/jjyeung/envs/p1cpu/bin/python` for the commands below.

Prepare one JSON config using `config_step600.example.json`. Pin the existing `build_r10.py`, its complete step-600 binding, source deliveries under its `KROOT`, and ordered export/preparation/dependency mirrors. Each mirror records its logical path, local `/scratch` path, byte count and SHA256. Keep builder stage/report/output paths inside the workspace. The wrapper calls the builder unchanged; it does not reconstruct missing source archives. `build_r8.py` and `build_d.py` also have adapters. Older hardcoded-root builders are refused. For fixed-token A/B operational scripts, `parameterize: true` explicitly adapts package/job-name and public walltime arguments while retaining native guards. That adapter defaults off; D scripts already accept P/T.

Set `CUDA_VISIBLE_DEVICES=""`, `OMP_NUM_THREADS=8`, `MKL_NUM_THREADS=8`, `OPENBLAS_NUM_THREADS=8`, `TOKENIZERS_PARALLELISM=false`, and `PYTHONDONTWRITEBYTECODE=1`. Use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, prefixed with `nice -n 10`.

For a fresh one-command build, select the optional token-patched builder copy and set `builder.explicit_token_switch: true`. Choose an unused token with 11–16 lowercase hex characters starting a–f. The wrapper enables the builder's token switch only when `--token` is supplied:

```sh
nice -n 10 "$PY" -I -s -B "$L/pack.py" all --enable \
  --config "$L/work/600.json" --yes --token TOKEN
```

The default prints exact ossh commands. Production execution also requires `--execute-remote`; it uses ossh once per phase and stops at the first failure. Submit requires `--yes` and the exact token. Both token and operational-script adapters default off, and original input trees remain untouched. Without the optional token patch, run `build` first, read its minted token, then run `all --reuse-build --yes --token TOKEN`. Inspect any failed attempt before proceeding; the tool never retries it.

Local checks cover shipped-byte hashes, bundle equality, isolated imports and real fill through authenticated path mirrors, preserved env/policy archives, header/member/policy resolution, native planning/stub rehearsal/memory bounds, duplicate-layout row metadata, process guard/write/dispatch, early-error capture, and native read-runner stop/end behavior. Missing mirrors fail locally. `check --audit` gathers failures but cannot grant release. Extend `forbidden_extra` for additional project/model/method terms; the built-in policy cannot be reduced. Default mirror-read budget is 256 MiB; large local reads need separate authorization and a suitable workspace.

The tool does not certify the Orchard namespace, job venv, real export restore/RGB rehearsal, live queue/pool, CUDA/H100 execution, training-rank shutdown/export, model quality, or scores. Native Orchard CPU checks still run before GPU submission. Direct/facing/VSTI kit builders were not supplied. See `ORCHARD_ONLY_CHECKS.md`, `CHECK_INVENTORY.md`, and `DEFECT_MATRIX.md` for exact scope. No remote operation was tested in this dispatch.
