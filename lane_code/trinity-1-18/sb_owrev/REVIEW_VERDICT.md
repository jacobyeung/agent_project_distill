GO AFTER FIXES

Review host: trinity-1-18; CPU only. Fix findings 1–2 before treating this kit's scorer as a strict decision gate.
Paths below are relative to `/scratch/jjyeung/orch_n30/sb_owrev`: K=`review/kit`, P=`review/out/pkg/b200`.
K and P were extracted from the delivered tar; the audit confirms K matches the builder's loose kit and every P/package and P/src member matches its seal.
Commands use `PY=/scratch/jjyeung/envs/p1cpu/bin/python`, `PYTHONDONTWRITEBYTECODE=1`, and OMP/MKL/OPENBLAS threads=4.

1. **MEDIUM — Partial returns do not fail the default scorer.** Removing all 150 displacement own rows leaves 300 own / 450 tower rows, but the CLI exits 0 and writes its normal outputs.
   Evidence: K/ownread.py:113, :124, :134, :184; `$PY -B probe_refusals.py` → `partial: accepted=true, cli_exit=0, all_complete=false, decision=null` (logs/refusals.txt; full CLI command/output in logs/partial_cli.txt).
   The null decision prevents a false positive, but does not satisfy the requested refusal. Make incomplete paired sets fail by default; allow diagnostic partial scoring only through an explicit option.

2. **MEDIUM — Some mismatched return metadata passes the scorer.** The same probe accepts an EXPORT_PIN archive SHA of 64 zeros and a journal declaring `binding.ids=[]` while supplying 300 rows.
   Evidence: K/ownread.py:59 checks selected export fields but omits the archive SHA; :78 and :88 never reconcile journal-declared IDs with journal rows. logs/refusals.txt reports `archive_pin` and `journal_ids: accepted=true`.
   Compare the archive SHA with READ_PLAN.export_binding.archive_sha256, and require each journal's rows to respect its declared IDs. These are direct-scorer gaps: the documented unpack step checks the archive SHA against INPUTS (P/src/orchard_h10/export_pins.py:77), so the first mutation alone is caught upstream.
   Other mismatches are rejected: the probe returns `Pair metadata differs` for a wrong room and `Mixed journals` for a differing export hash; the kit tests also reject duplicates, wrong arms, tails, settings, and arm bindings.

3. **PASS — Seals regenerate reproducibly; the A4 tower settings survive.** `$PY -B $K/build_ownread.py --out work/rebuilt --token ade90fc02479b` reproduces A4 in its null-fork check, then reproduces the delivered fork; `cmp work/rebuilt/1.tgz $P/1.tgz` exits 0.
   Evidence: K/build_ownread.py:74 imports the payload's own builder; :84 regenerates bundle/public/manifest hashes; :120 checks the null fork. Its tar/manifest recipe agrees with out3/rebuild.py:12 and out3/seal_delivery.py:11.
   `$PY -B review_audit.py` verifies all 926 payload pins, 927 payload members, and 15 delivery members. Only payload `9.json` differs; its only configuration change is the token at step 200. Delivery changes are 0.json, 0.tgz, BATCH.sh, CONFIG.json, PACKAGE.json, and a/6.py.
   Fork SHA256: `af37ab141f6d0304264ffdeb47ec840037fce6366b5825f5c7142508b16147bf`; kit tar SHA256: `ac9373eef3e0a55886fc182f31529f57771da1357ca2d89d8668ecdfb11de306`, matching its sidecar.
   `$PY -B $K/tests/check_build.py $P` → passed=true, 14 Python-3.6 helpers; `$PY -B $K/tests/cpu_proof.py $P work/proof` → passed=true, 900/900 reads, identical A4 tower settings SHA `2c3cc6b4f97ed64157f9addf73447763c781d2ba2294c7a3ff1b95ef75a0ebca` (logs/check_build.txt; logs/cpu_proof.txt).
   `BUILD=$PWD/$P PROOF=$PWD/work/proof $PY -B -m pytest -q -p no:cacheprovider $K/tests/test_kit.py --basetemp=$PWD/work/pytest` → 23 passed in 21.22 s (substitute P/K above; logs/pytest.txt).
   The changes also select camera types and per-type workers; both are disclosed (K/OPERATOR_DIFF_VS_A4.patch:12; K/OPERATOR.md:71).

4. **PASS WITH DISCLOSED LIMIT — Own scale and baseline mode match H1-0.** P/src/h1eval/perception.py:99 uses OwnGeometry and scale 1, as does `/scratch/jjyeung/orch_n30/h10_stage/work/k330/kit/h1eval/perception.py:99`.
   `$PY -B review_audit.py` confirms H1-0 includes mode none plus six interventions; this kit uses none only. K/OPERATOR.md:72 discloses that choice and :73 discloses the older H1-0 reader/evaluator/maker/parity code.
   A4 uses candidates_argmax; the registered step-544 tower uses null_argmax (K/ref/REFS.json:69 and :139). The builder report explicitly discloses this at `/scratch/jjyeung/orch_n30/sb_ownread/out/OWNREAD_REPORT.md:88`. Step-544 comparisons share items but are not controlled checkpoint-only comparisons; current own−tower is the relevant decision comparison.

5. **PASS — Independent synthetic recomputation agrees.** `$PY -B review_audit.py` recalculates all 900 answer scores from text and labels, then independently implements the seed-17, 10,000-draw paired room ratio bootstrap. It finds zero answer-score mismatches and matches both interval levels (logs/audit.txt; AUDIT.json).
   Displacement: own 47.20, tower 81.87, difference −34.67, 95% [−42.59, −26.60]; movement direction: 75.33, 94.67, −19.33 [−27.59, −11.81]; rotation: 42.73, 76.27, −33.53 [−40.13, −27.06]. Each comparison has 150 paired items; room counts are 36/36/34.
   K/ownread.py:87 indexes by arm/item ID; :101 joins by item and clusters on room; :124 implements point ≥−5 and :125 implements lower-95%-bound >−5. All three synthetic types fail both bars, as expected. These are replay results, not milestone measurements.

6. **PASS — Submission, export pins, and runtime estimate are grounded.** K/OPERATOR.md:9 specifies one H100, 16 CPUs, five hours; :19–40 gives receipt-driven step-400/600 pins and build/check commands; :65 requires orchestrator GO and :67 forbids launching b200.
   `$PY -B review_audit.py` independently sums the measured journals: staging 256.97 s, tower decoding 3552.90/3447.89 s (steps 200/544), own decoding 3138.56 s, tower load 75.45 s, maximum own overhead 112.81 s.
   The stated formula yields 7633.20 s = 2.1203 h; multiplying decoding by 1.5 yields 3.0497 h (K/time_estimate.py:12–29; logs/audit.txt). The latter is a slowdown scenario, not a guaranteed upper bound. CPU checks cannot establish CUDA memory use or actual milestone speed.

7. **PASS — The scheduled population is the fixed dev-S1 camera set.** K/ownread_sequence.py:7 and :14 select types 0/1/2; P/src/orchard_h10/runner.py:42 uses the sealed devs1_routed manifest.
   `$PY -B review_audit.py` finds exactly 450 unique `devs1cam-*` IDs, 150 per camera type, all with native_camera_gt labels and A4's camera order. No operator step selects an official benchmark item set. The `official_vsi_mra` label names the scoring rule, not an official benchmark population.

Evidence JSONs AUDIT.json and REFUSALS.json include input SHA256 maps; scripts and command outputs are retained here. Reviewed source files were not edited.
Review-process caveat: the kit's builder tests created temporary helper copies under `/tmp` through K/build_ownread.py:77 before `review/work` existed. This exceeded the requested workspace-only scratch scope; I did not delete those copies.
