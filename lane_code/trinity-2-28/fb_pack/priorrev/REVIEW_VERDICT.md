VERDICT: GO AFTER FIXES — the sampler patch is correct; prove_on_prepared.py needs MUST 1 and MUST 2 before its PASS can serve as the production gate.

## MUST
1. **The checker proves a recomputed schedule, not the one training uses.** `prior2b/out/prove_on_prepared.py:102-103` drops the production
   binding's `direction_prior` and rebinds one from `--weights` (`:172`, `:85`). Nothing compares the result with `cfg['r2_sampling']['direction_prior']`
   or with `cfg['r1_training']['direction_prior']`. The plan path cannot catch the gap either: `schedules` checks only per-side counts and cell
   membership (`student_pilot/r1_direction_prior.py:92-99`), and my probes found it accepts a re-pinned offsets file with facing sides swapped,
   or with a non-target row in a toward-hard slot (`work/s5/new_enabled_r2/REPLAY.json` "tamper").
   Fix: in real mode, require the config field and `binding['direction_prior']`, require the field's sha256 to equal `--weights`, require the
   production offsets file to equal the recomputed one (cells, policy sha, card/population/indices sha), and run the enabled plan on the production binding.
2. **Real mode passes on synthetic rows.** Only the `scope` label separates a fixture from real preparation (`:189-190`); line 81 anchors only the card.
   I deleted `scope` from the mix fixture's config and receipt and re-pinned the receipt (`work/s6_unlabelled.py`). The checker then printed
   `PASS REAL_PREPARED`, `production_gate: PASS`, on the synthetic pose/pointing/routing sqlite stores and the reconstructed VQA store (`work/s6/result/RESULT.json`).
   Fix: anchor real mode to N's launch identities, for example `r1_training.store_hashes.vqa` = 210b2534 (`N_LAUNCH_CONFIG.json:254-256`),
   the source database pins listed in `HOST_INPUTS.json:130-178`, and the sealed patched-tree pin.

## SHOULD
3. `HOST_INPUTS.json:121` and `REPORT.md:55` name `…/8865619b/f/469ddece/receipt.json` as the final preparation. `bind_prepared` writes
   `<proof root>/b/receipt.json` (`launch_r1/production_proof.py:142`, `r1_population.py:225-227`), `bind_handover` writes `<root>/h/receipt.json`
   (`production_proof.py:57-59,151`), and `entry.frame_host` writes `<root>/population/receipt.json` (`entry.py:194`). The checker fails closed
   on the named file (`prove_on_prepared.py:185`), so the cost is a failed run, not a false PASS. Every other field name in HOST_INPUTS matches
   bind_prepared's output (`r1_population.py:191-202,216-227`).

## Verified (own code under work/, CPU, 8 cores)
- **(1) Patch applies.** It applies to base seal 57a1f14d (941 files, `patch --fuzz=0` rc 0). The patch sha and all 6 changed files' before/after
  hashes equal FILES_TOUCHED.json, and the new tree is 31c8f6b8 (`work/S1_APPLY.json`).
- **(2) Field absent.** Base and patched plans are byte-identical on prior2b's fixture (2c0ba89b). They are also identical on a replay of the
  189,063-row population through native `produce()` and `plans()`, with stand-in pose/pointing/routing rows at card ceilings (35c96481).
  Populations and indices are identical (`work/S5_COMPARE.json`).
- **(3) Field present.**
  - The cell sequence is unchanged. Only toward-hard slots change: direction 13,565 of 13,566, facing_pairs 1,875 of 1,875. Zero other positions change.
  - Toward-hard back share, read from the drawn rows: direction 17.62% → 50.00% (6,783/6,783), facing_pairs 15.47% → 49.97% (937/938).
    Every other clause × difficulty group is unchanged.
  - No row is drawn more than 4 times. Resume matches at steps 1, 250, 723, 999 and 1000, and a rerun is deterministic.
  - `plans()` refuses changed bytes, a changed card or population sha, a dropped, duplicated or out-of-cell offset, a flipped weight side, and a wrong policy sha.
- **(4) Weight file.** Its 24,862 rows equal the population's toward-hard set exactly (qid, cell, row digest, side). All 189,063 rows match
  v7 store 210b2534 and twins 7b3d696d. Class counts match WEIGHTS (3,676/16,826; 651/3,709), and my own option parse agrees on every side.
  No row in any cell matches dev-S1 a1869ae2, the M400 dev list, benchmark 3119aa4a, test split dafa4a9c, R0 f7c45817, the division held-out
  scenes and QIDs, or held QIDs 66c427e2. Every scene token resolved. My matcher and the tree's Exclusions/Reserve each caught 200/200
  planted positives per list (`work/S4_LEGAL_own.json`, `S4B_CONTROL.json`, `S4C_POWER.json`).
- **(5) No vacuous pass on target cells.** Empty tables and missing cells cannot pass: target checks need non-empty toward-hard audits and at
  least one changed draw (`:143-146`), `Prior` refuses zero mass (`r1_direction_prior.py:39-41`), `bind` refuses a changed population (`:67-68`),
  and `validate_binding` refuses the placeholder (`r1_mix.py:55-59`). Synthetic rows can pass; see MUST 2.
- **(6) Mismatches are mirror artifacts, not defects.**
  - 30cf2da5 is the donor kit's `p_files['k/review.json']` (`kit_n_go/k/p.json` base64 payload). N's pin c3cfe01f is uploaded (uploads[164], pin_paths).
  - 8091154c (mirror receipt) and e3ee51da (`store_parameter`, `N_LAUNCH_CONFIG.json:257-260`) are both uploaded (uploads[113], [193]),
    and runtime guards bind both to store 210b2534 (`r1_training.py:175-191`, `r1_direction_twins.py:109-112`). The e3ee51da bytes are not mirrored here.
  - The zero counts belong to the launch placeholder, which `bind_prepared` replaces (`r1_population.py:216`).
- **(7) Loader audit.** The new clause parser matches ground truth on all 98,315 direction/facing rows (the facing field, twin clause edits,
  v7 toward). The old parser mislabelled 23,121 clauses. `dimensions` and DirectionAudit feed only the audit's RESULT.json, and the absent-field
  replay shows no stream changes.

## Notes (not defects)
- Away-hard keeps its native back share: 67.6% pooled, 84.4% in facing_pairs, 49.6% in direction. The patch targets toward-hard only.
- DirectionAudit pools both cells (`r1_loader.py:123-133`), so the production audit shows only the pooled toward-hard share. Per-cell
  balance comes only from the checker's per-cell audits.
- Unit tests: 22/23 pass (`tests.test_r1_direction_prior`, `tests.test_r1_build13`). `test_native_composition_envelopes` errors because
  `R2_FIXTURES/work/build6/INIT_INPUT.json` is absent here (`tests/r2_init_fixture.py:4-5`); this predates the patch and does not involve it.
