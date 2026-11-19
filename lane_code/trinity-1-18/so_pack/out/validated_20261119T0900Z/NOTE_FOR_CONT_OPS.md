# Step-600 use

Use the adjacent pack.py and pack_probes.py as one source set. They match the source that passed 21 local tests. Other root and out/tool commands changed concurrently and do not share that validation.

Create a configuration from the workspace example, supply the complete reviewed step-600 binding and authenticated archive mirrors, and SHA-pin the chosen builder and inputs. Use a fresh workspace. The supplied example is incomplete and cannot authorize release.

```sh
L=/scratch/jjyeung/orch_n30/so_pack
PY=/scratch/jjyeung/envs/p1cpu/bin/python
TOOL="$L/out/validated_20261119T0900Z/pack.py"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
nice -n 10 "$PY" -I -s -B "$TOOL" --help
```

The tool defaults OFF. Pass --enable, --config CONFIG and the chosen subcommand. Use --help for exact placement of options. build invokes the existing pinned builder. check validates the built bytes, runs the isolated fill and available native checks, and binds its local receipt to source/config/package hashes. place, fill and submit print exact ossh commands. all preflights all phases and stops at the first failure. submit requires --yes and a matching explicit --token. Transport requires --execute-remote as well. This task executed no remote transport.

Apply the two add-only unified patches with patch -p1 at a copy of the mirrored orch_n30 root. Native builders remain unchanged. Optional builder copies preserve default randomness; SO_PACK_EXPLICIT_TOKEN=1 plus SO_PACK_TOKEN selects an explicit token. Configure builder.explicit_token_switch only when choosing such a copy. D default deliveries were byte-identical under deterministic fixture entropy. r10 full-build equivalence remains untested because source archives are missing.

Strict privacy includes names, paths, job names, comments, env literals and nested archive/bundle contents. Existing payloads fail this rule. Do not relax it to release them. Missing authenticated mirrors and step-600 bindings also block release. Small fixtures prove packaging logic only. The tool does not certify Orchard's real venv, full restore/RGB data, GPU behavior, scheduler delivery or the production trainer's four-rank stop/export. See CHECK_INVENTORY.md and ORCHARD_ONLY_CHECKS.md.
