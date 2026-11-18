R1-P uses the ruled vehicle-P family set. Room requests 1.72 rows per step and receives 0.00 after filtering. Size, recovery and unbound units have zero dose. Full production evidence remains pending. Read `REPORT.md` and `proof/GATES.json` before deployment.

| Binding | Value |
|---|---|
| Config identity | `a6b70ef26dff31e8c212f94eb6193ced75929ea8b035769f1fe87eb4657766c9` |
| Tree | `32145eae1d96653847d520020842f5719f3adf7e3a890a2d44a3576b4f6ccf15` |
| Run / job name | `6e77070a` / `a15_cot_ap6e77070a` |
| Producer receipt SHA | `8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd` |
| Database SHA | `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443` |
| Selection SHA | `1dc5e6b7bd37c0704d852c800e75cef17fa313db7b4d35301fe6b6ce36403e46` |
| Operator archive | `p_084ba70f.tar` |
| Archive SHA | `88a55761b7acb59c6213b846681c6dceee0e69332d7c4b913bf3084ec45bfa91` |

Relative to H1-1, this config disables S1 and S2, restores D0 scheduled sampling, uses milestones [100, 200] and stop 200, binds v7, removes room programs and adds capped family quotas. The 1,000-step schedule, stream totals (pose 64, VQA 128, routing 64, pointing 32), optimizer and initial weights stay in the inherited recipe. Field-level changes are in `../configs/diff_against_h1_1.json` and `../configs/diff_against_deployed.json`. `SAMPLER_REVIEW.patch` contains the trainer changes; no admission predicate changes. `DEPLOYMENT_REVIEW.patch` covers the staging, wrapper and submitter changes.

Rebind a store, size selector and mix with one command from the lane. This regenerates the admission table, config identity, code archive, loader audit, proof inputs and operator archive:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \
  --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json \
  --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd \
  --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db \
  --mix configs/mix.json --proof-partition advanced
```

The bound store is v7; its producer receipt and database SHA are fixed above. `--size-selector FILE` accepts `{"field":"metadata.path","equals":"value"}`; omission keeps all admitted size rows eligible, while the mix controls whether any are drawn. The mix file controls requested doses and refill rules. Traced rooms enter through the bound VQA store and remain subject to the qualitative-trace predicate and cap. `--room-receipt FILE` binds optional provenance for traced rows already integrated into that store; it does not merge a second database. A separate room store must be integrated by its producer. Rebinding invalidates earlier first-batch and deployment proof results; rerun them against the new identity. Use `--reuse-census` only for unchanged store bytes and receipt. After rebinding, run `/scratch/jjyeung/envs/p1cpu/bin/python -B tools/run_local_checks.py` to refresh the local evidence and this packet.

The default `--units-allowlist ft` samples feet only; freed routing slots go pro rata to camera displacement, movement direction, rotation and absolute distance. To bind units, add `--unit-rows FILE --unit-rows-sha256 SHA` and optionally `--unit-cents N` (default 100 hundredths of a row per step, capped at 4 × allowlisted eligible / 1,000). The file must contain faithful, already packed JSONL rows with full events and all 32 frame pins. No answer, event, or row payload is regenerated. A mismatched SHA, incomplete frame pins, sealed semantic refusal, or row removed by native source selection rejects the binding. The source must already be a clean slice; this command does not repair it.

Each fallback is one rebind command and retains v7 as the sole store:

```bash
# Refused room traces: zero the room cell and send its slots to direction.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --room-cents 0 --proof-partition advanced
# Refused reworded away rows: exclude the exact QID suffix.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --exclude-qid-suffix _away_opp --proof-partition advanced
# Bind a packed, audited successor. The current v2 candidate is refused unchanged.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --unit-rows "$UNIT_FILE" --unit-rows-sha256 "$UNIT_SHA256" --units-allowlist ft --unit-cents 100 --proof-partition advanced
```

Set `UNIT_FILE` and `UNIT_SHA256` to the audited packed file and its SHA. The named candidate is `/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v2/rows.jsonl`; its unchanged read-only fixture is refused for missing events and frame pins. After any rebind, run `tools/run_local_checks.py` with the CPU Python above. Neither fallback merges loose files into v6.

Unit binding is an **admission-input change**: `u.gz` transports the exact JSONL bytes; `m.json` adds `U_Faithful` to the pool manifest; `i.json` binds its native ordered indices; `u.json` records hashes and per-unit/per-dataset counts. These artifacts enter the operator bundle. Derivation stages `u.gz`, `m.json` and `i.json` into private, read-only namespace paths and adds their pins to the routing catalog. RGB bytes are not bundled: the complete staged RGB map/plan and frame store must resolve every supplied frame pin unchanged. Missing or conflicting RGB fails production admission. Full native materialization calls the sealed `selected_rows`, frame resolution, division/scene/QID filters and RGB audit before the sampler or proof counts units.

The prepared operator archive contains no database bytes. Its sole v7 input is the existing mode-0400 Orchard file `/project/community/jjyeung/okh7/s_22b44165/d.db`. The inherited staging code copies it into `/tmp/jjyeung/a_6e77070a/root/aws/u/ap/084ba70f/d.db`, verifies the database SHA and removes file write bits. Inside the namespace, both `/scratch/fsw` and `/lustre/fsw` aliases resolve to that private union. The deployment receipt is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/084ba70f/d.json` with SHA `8c534691ccbdca646d7b93f87ebec5ee2ff1b513d8255ff271622065b6e4ddb6`; its database path is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/084ba70f/d.db`. The original producer receipt remains a separately pinned provenance record. No Trinity database path is a runtime input.

Operator steps below describe the future Orchard execution; this lane made no Orchard call. Keep all destinations private (directories 0700, files 0600 unless the sealed input requires 0400). Do not copy the descriptive reports to the public job surface.

1. Verify `SHA256SUMS` locally and transfer only `p_084ba70f.tar` through the operator's approved route. Extract it into fresh bundle `/project/community/jjyeung/okh7/i_084ba70f`. Verify its `sums.txt`. Resolve the complete H1-1 deployment as `H`, whose source manifest must hash to `f13eccc20b7d2ee8b9622ce66db36e3cf561d0d41e69a367e9c435d5bf4261d6`. The local incomplete fixture cannot be used for production.
2. Run H1's authenticated native selection regeneration on its complete staged inputs, as in its `build/q.sh`. Retain the fresh raw `s1_pool.prepare` receipt as `NATIVE_RECEIPT`. Project it with the supplied helper; it verifies all regenerated ordered-index hashes and all non-room entries. It also binds the selector import-closure fingerprint to the archived trainer code; admission predicates must retain their parent hashes:

```bash
BUN=/project/community/jjyeung/okh7/i_084ba70f
python3 -B "$BUN/q.py" \
  --parent "$H/k/pool_selection_eac5f9f0.json" --indices "$H/k" \
  --native-receipt "$NATIVE_RECEIPT" --implementation "$BUN/j.json" \
  --code-record "$BUN/c.json" --out "$BUN/q"
```

For a unit-bound packet, run the projection command with `--unit-binding "$BUN/u.json" --config "$BUN/config.json"` as well, using the authenticated CPU environment for the bound code tree. It executes sealed `s1_pool.prepare` on the unit source again, compares every ordered index, combines that source with the freshly checked parent selection, and refuses any final selection hash mismatch. The complete H1 inputs remain necessary. The source-selection counts are preliminary; the production proof reports post-filter counts, 1,000-step shares by family and question type, five bound traces per populated family, and missing units below 100 rows.

3. Obtain one independent review of the changed admission inputs and sampler. Supply identity-bound `review.json`, `staging.json`, `archive.json` and `4.json` in `EVIDENCE`, using the inherited production schemas. The durable source-archive attestation must cover the new tree. These are required inputs, not output claims of this build. Derive a fresh kit; the command invokes the inherited verifier and refuses incompatible evidence:

```bash
KH=/project/community/jjyeung/okh7/x_084ba70f
python3 -B "$BUN/d.py" --source "$H" \
  --source-manifest-sha256 f13eccc20b7d2ee8b9622ce66db36e3cf561d0d41e69a367e9c435d5bf4261d6 \
  --packet "$BUN" --bundle "$BUN" --out "$KH" \
  --selection-evidence "$BUN/q/q.json" --evidence "$EVIDENCE" > "$BUN/compare.json"
```

4. Run the independent complete content scan on the final kit and supply its `ANON_OK.json`, bound to the final manifest. Create new export sessions for the 20 part destinations in `e.txt` and install the private `sess.json` in the kit. The plan has three exports (100, 200, stop); stopB and stopC are alternate stop-slot names. Never reuse H1 sessions or approval evidence.
5. Bind and submit the production CPU proof, starting from an empty root. `p.py` requires a READY kit and native selection evidence. The proof resolves and hashes binaries at run time; it obtains bwrap from the kit's verified executable pin.

```bash
PARTITION=advanced  # advanced (one approved CPU job) or general
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" \
  --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap6e77070a -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" \
  "$BUN/p_6e77070a.sh" "$BUN/a.json"
```

6. Inspect the named checks in `KH/o/JOB.proof.json`, its bound loader audit and the five printed traces per family. The required-family check permits recovery, size, unbound units, any zero-dose room cell, and bound units below 100 eligible rows; it must pass for every nonzero VQA cell and the four native routing cells. For a bound source, each unit below 100 is listed under absent_on_P with its count. Only allowlisted units with at least 100 rows enter the capped sampler. Confirm the proof receipt records the requested partition and actual node. The separate `go.json` must bind the final config, contract, wrapper and manifest; only then may the operator set `PROOF_JOB` and run `BUN/s.sh`. The submitter refuses any missing proof check or missing GO.

Local validation: 25 tests passed; OFF identity is exact on four tiny-model ranks; 288 final-config microsteps pass finite full-forward checks; two fixture derivations are byte-identical; the real-v7 loader audit covers 1,000 steps. These are bounded local results. Full native selection regeneration, production RGB/admission, complete routing counts, complete privacy scan and production CPU proof are NOT_RUN. `proof/GATES.json` is the authoritative gate list.
