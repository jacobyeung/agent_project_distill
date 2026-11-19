**NO_GO for N’s first boundary.** The required all-cell production identity proof is MISSING. The patch must wait.

The base seal is `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7` (939 verified files).
The six-file patch applies cleanly; all 941 resulting files match `31c8f6b8c28c8213ff78a65df6f0fce23a99c24f56945359dade50d394a6236c`.
`FILES_TOUCHED.json` lists the changes. No file overlaps the other lanes’ declared scopes; their actual patch manifests were not supplied.

Set the optional `r1_training.direction_prior` pin to `TOWARD_HARD_WEIGHTS.json`. Preparation authenticates QIDs, row hashes, clauses, answers and forward relations, then binds native offsets to the card, population and indices.
The sampler alternates front/back within existing toward-hard slots and shuffles each side independently from the card seed. It preserves other positions and refuses insufficient four-draw capacity. Non-VQA streams are outside the prior’s scope.

Weights are `direction`: back `10251/3676`, front `10251/16826`; `facing_pairs`: back `2180/651`, front `2180/3709`.
All 98,315 rows in the prior lane’s pinned filtered extract match original v7 and twin bytes. The weight file records inherited source pins; missing inputs prevent independent filtering.
The loader audit includes facing_pairs and corrects 23,121 clause-parser disagreements. Its production-entrypoint fixture counts both drawn rows; the base counts one.

**Diagnostic scope:** N’s exact seed-17 card and authenticated direction/facing-pair rows, with synthetic support offsets for unavailable cells. This is not a production population or launch configuration.

| Clause / difficulty | Draws | Base back share | Patched back share |
|---|---:|---:|---:|
| away / easy | 7,304 | 0.0000% | 0.0000% |
| away / hard | 5,371 | 67.6224% | 67.6224% |
| away / medium | 3,331 | 42.8100% | 42.8100% |
| toward / easy | 11,412 | 0.0000% | 0.0000% |
| toward / hard | 15,441 | 17.3629% | 49.9968% |
| toward / medium | 12,177 | 4.4182% | 4.4182% |

The first 1,000 steps are the full schedule. Direction retains 36,866 draws, facing_pairs 18,170, and the card 288,000.
These are realized shares. The prior report’s 67.873% away-hard figure was an expectation; realized away-hard and every other non-target group remain exactly unchanged.
With the field absent, every diagnostic cell matches base byte-for-byte. With it present, only toward-hard rows change; their count and all other positions stay fixed. The maximum repeat is four, resume matches, and tampered weights refuse.
The base ignores both the field and tampered weights. `CENSUS_LOADER.json` records loader counts, sequence hashes, negative controls and input pins.

The guarded CPU runner attempts every existing module and records prohibited operations as errors. Base: 1913 tests, 16 failures, 475 errors, 145 skips. New: 1922 tests, 16 failures, 475 errors, 145 skips.
Comparison: `NO_NEW_FAILURE`; 0 worsened existing outcomes. `TESTS.json` includes subtest comparisons and new tests. Existing missing fixtures and restricted operations prevent an all-pass claim.

Missing filter inputs, at their original 1-18 paths (apply the prompt’s mirror map):

- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/build17/inputs/s.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/inputs/u.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/build21/inputs/u_union.json`
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json`
- `/scratch/jjyeung/orch_n30/sb_d7bind/BINDING.jsonl`
- `/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json`
- `/scratch/jjyeung/orch_n30/sb_rowA/out/WORDINGS.json`

`MISSING_INPUTS.json` gives all expected paths and pins, including the room-authority input, population/indices and other-stream populations. The production receipt is also MISSING at `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json`.
No production mapping, manifest, scene list or proof was synthesized. The exact card bytes were recovered from the kit capsule and hash-verified.

Commands producing the numbers above, from this workspace:
```bash
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
PY=/scratch/jjyeung/envs/p1cpu/bin/python
nice -n 10 "$PY" scripts/setup.py                 # seal and 939 files
patch --batch -p1 -d work/new -i "$PWD/out/PATCH_PRIOR.patch"
mkdir -p work/recovered
nice -n 10 "$PY" scripts/locate.py                # input availability
nice -n 10 "$PY" scripts/recover_capsules.py      # exact card bytes
nice -n 10 "$PY" scripts/missing_inputs.py        # missing pins and kit comparison
nice -n 10 "$PY" scripts/build_weights.py         # source counts, weights, parser count
nice -n 10 "$PY" scripts/replay.py                # all draw counts, shares and invariants
nice -n 10 "$PY" scripts/cpu_run.py base          # full CPU baseline
nice -n 10 "$PY" scripts/cpu_run.py new           # full CPU patched tree
nice -n 10 "$PY" scripts/make_patch.py             # six-file patch and 941-file verification
nice -n 10 "$PY" scripts/compare_tests.py          # CPU comparison
nice -n 10 "$PY" scripts/verify_evidence.py        # direct input hashes
nice -n 10 "$PY" scripts/finalize.py               # report, archive and SHA256
```
Use fresh output directories for immutable fixtures. After the production checks pass, preparation must bind the weight pin and the orchestrator must reseal the tree and kit before activation. No launch configuration changed here.
`fbp_prior2.tar.sha256` authenticates the archive; `PACKAGE.json` records every member hash.
