**NO_GO.** The all-cell production identity proof is MISSING for `pointing`, `pose`, and `routing_base`; their native data and final post-filter offsets are unavailable. No real prepared receipt was synthesized.

`PROOF.json` records every cell, filter-stage count/hash, mismatch and missing path. `TESTS.json` records the tests; `HOST_INPUTS.json` names the training-host fields and files.

The 12 launch removal lists, naming removal, s/u/u_union, aliases, bindings, wordings and room-authority bytes authenticate. The metadata-filter replay retains **189,063 VQA rows** from 204,413 source rows plus 7,971 twins. All 18 VQA cell counts match their explicit card ceilings, including 55,808 direction and 42,507 facing-pair rows.
Frame-host rebuild/admission and final native offsets remain unproved. The launch population has `complete=false`, `after_all_filters=false`, 31 zero counts and 31 empty index lists; its 16 nonzero VQA source-count comparisons are MISMATCH, recorded without substitution.

Launch `0e78d7f8` and kit `2ad4032d` agree in counts and pins after ignoring paths. Pointing `c09bb5ca`, routing `4e8e6c04`, and composite pose `6d591440` receipt identities match; only VQA store bytes `210b2534` are locally verified.
The mirrored VQA receipt hashes to `8091154c`, versus launch pin `e3ee51da` (MISMATCH). The copied admission review hashes to `30cf2da5`, versus `c3cfe01f` (MISMATCH). `INPUT_AUDIT_FINAL.json` gives full hashes and all unresolved pins.

The exact 940-file seal `189df6ac` is reproducible from the authenticated base plus HOST24J.patch. PATCH_PRIOR applies with `--fuzz=0`, without offsets. The supplied live tree itself differs from that seal in `launch_r1/entry.py` and `launch_r1/production_proof.py`; `LIVE_PATCH.json` records both mismatches.

**Fixture results only:** the same gate runs through native `Rows`, pose mix/order tables and reader-filter subset validation. Its 31 cells and 288,000 seed-17 draws pass: field absent equals base byte-for-byte; field present changes only toward-hard slots in direction/facing_pairs; all other positions and counts match. Each row appears at most four times; resume matches.

| Cell / toward-hard | Draws | Base back | Patched back |
|---|---:|---:|---:|
| direction | 13,566 | 2,391 (17.6249%) | 6,783 (50.0000%) |
| facing_pairs | 1,875 | 290 (15.4667%) | 937 (49.9733%) |

Each other clause × difficulty group is unchanged. The fixture uses reconstructed VQA source rows and explicitly synthetic support rows for the three unavailable streams. It grants no production PASS.

All nine added prior tests pass on both the reconstructed seal and the supplied live tree. The broader patched suite has 40 tests: 37 pass, zero fail, and three error; the base has the same three errors. They require missing `fixtures/work/build6/INIT_INPUT.json`. No existing result worsens. All five checker refusal tests pass.

Commands below produce the reported counts, hashes, draw shares and test totals from this workspace. They retain fixtures; use a fresh workspace/output directory when repeating them.
```bash
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
nice -n 10 "$PY" scripts/setup_live.py
nice -n 10 "$PY" scripts/sealed_tree.py
nice -n 10 "$PY" scripts/recover_metadata.py
nice -n 10 "$PY" scripts/inspect_pins.py
nice -n 10 "$PY" scripts/supplement_inputs.py
nice -n 10 "$PY" scripts/source_census.py
nice -n 10 "$PY" scripts/store_audit.py
nice -n 10 "$PY" scripts/build_fixture.py
nice -n 10 "$PY" scripts/native_fixture.py
nice -n 10 "$PY" scripts/mix_fixture.py
nice -n 10 "$PY" out/prove_on_prepared.py --base-tree work/sealed_base --patched-tree work/sealed_new --weights out/TOWARD_HARD_WEIGHTS.json --fixture work/mix_fixture/FIXTURE.json --output-dir work/final_gate
ln -s /scratch/jjyeung/orch_n30/fb_pack/prior2/work/base work/tree_r1_base
nice -n 10 "$PY" scripts/test_live.py sealed_base
nice -n 10 "$PY" scripts/test_live.py sealed_new
nice -n 10 "$PY" scripts/test_live.py live_new tests.test_r1_direction_prior
nice -n 10 "$PY" scripts/test_checker.py
nice -n 10 "$PY" scripts/finalize.py
```

Training-host command (variables must name real files identified by `HOST_INPUTS.json`; no guessed table paths):
```bash
nice -n 10 "$PY" out/prove_on_prepared.py --base-tree work/sealed_base --patched-tree work/sealed_new --weights out/TOWARD_HARD_WEIGHTS.json \
  --config "$N_CONFIG" --prepared-receipt "$N_PREP" --output-dir "$NEW_PROOF_DIR" \
  --receipt pointing="$POINT_RECEIPT" --receipt pose="$POSE_RECEIPT" --receipt routing="$ROUTE_RECEIPT" --receipt vqa="$VQA_RECEIPT" \
  --offset-table pointing="$POINT_INDICES" --offset-table pose="$POSE_ORDER" --offset-table routing="$ROUTE_INDICES" --offset-table vqa="$VQA_INDICES"
```

`N_PREP` is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json` (MISSING). Exact final table paths/hashes must come from its stream pins. The checker prints PASS/FAIL for each cell and refuses incomplete populations, changed hashes, duplicate offsets and fixtures passed as real preparation.

`fbp_prior2b.tar.sha256` authenticates the archive. `PACKAGE.json` records member hashes; native JSON arrays and unchanged input copies inherit provenance through their pinned fixture manifests.
