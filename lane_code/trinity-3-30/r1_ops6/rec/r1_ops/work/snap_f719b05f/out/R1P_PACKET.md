R1-P uses the ruled vehicle-P family set. Room requests 1.72 rows per step and receives 1.72 after filtering. Size, recovery and unbound units have zero dose. Full production evidence remains pending. Read `REPORT.md` and `proof/GATES.json` before deployment.

| Binding | Value |
|---|---|
| Config identity | `782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da` |
| Tree | `b7d19ec090bcab112ed0ce72758e4491e02aff14d4645ac3945bb56ebd7d379e` |
| Run / job name | `125c4c87` / `a15_cot_ap125c4c87` |
| Producer receipt SHA | `8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd` |
| Database SHA | `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443` |
| Selection SHA | `78d01f893720baf0e31b3ce06bc4a157a99510d42f5bcfeccb0000ad84705c70` |
| Operator archive | `p_1130b378.tar` |
| Archive SHA | `f719b05fcbe934654499d786d1a56d413c0db71f6a1fd9a60b5097e788ebfad9` |

Relative to H1-1, this config disables S1 and S2, restores D0 scheduled sampling, uses milestones [100, 200] and stop 200, binds v7, removes room programs and adds capped family quotas. The 1,000-step schedule, stream totals (pose 64, VQA 128, routing 64, pointing 32), optimizer and initial weights stay in the inherited recipe. Field-level changes are in `../configs/diff_against_h1_1.json` and `../configs/diff_against_deployed.json`. `SAMPLER_REVIEW.patch` contains the trainer changes; no admission predicate changes. `DEPLOYMENT_REVIEW.patch` covers the staging, wrapper and submitter changes.

Rebind a store, size selector and mix with one command from the lane. This regenerates the admission table, config identity, code archive, loader audit, proof inputs and operator archive:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \
  --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json \
  --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd \
  --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db \
  --mix configs/mix.json --proof-partition advanced
```

The bound store is v7; its producer receipt and database SHA are fixed above. `--size-selector FILE` accepts `{"field":"metadata.path","equals":"value"}`; omission keeps all admitted size rows eligible, while the mix controls whether any are drawn. The mix file controls requested doses and refill rules. Traced rooms enter through the bound VQA store and remain subject to the qualitative-trace predicate and cap. `--room-receipt FILE` binds optional provenance for traced rows already integrated into that store; it does not merge a second database. A separate room store must be integrated by its producer. Rebinding invalidates earlier first-batch and deployment proof results; rerun them against the new identity. Use `--reuse-census` only for unchanged store bytes, receipt and sampler-predicate hash. After rebinding, run `/scratch/jjyeung/envs/p1cpu/bin/python -B tools/run_local_checks.py` to refresh the local evidence and this packet.

The default `--units-allowlist ft` samples feet only; freed routing slots go pro rata to camera displacement, movement direction, rotation and absolute distance. To bind units, add `--unit-rows FILE --unit-rows-sha256 SHA` and optionally `--unit-cents N` (default 100 hundredths of a row per step, capped at 4 × allowlisted eligible / 1,000). The file must contain faithful, already packed JSONL rows with full events and all 32 frame pins. Direct packed-file binding preserves every JSONL byte. The optional slice path described in `UNIT_PACKING.md` adds only missing events and resolved frame inputs; it refuses changes to the supplied target, answer, responses or spans. A mismatched SHA, incomplete frame pins, sealed semantic refusal, or row removed by native source selection rejects the binding. The source must already be a clean slice; this command does not repair it.

Each fallback is one rebind command and retains v7 as the sole store:

```bash
# Refused room traces: zero the room cell and send its slots to direction.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --room-cents 0 --proof-partition advanced
# Refused reworded away rows: exclude the exact QID suffix.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --exclude-qid-suffix _away_opp --proof-partition advanced
# Bind audited, fully packed rows; slice input requires the explicit option below.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --unit-rows "$UNIT_FILE" --unit-rows-sha256 "$UNIT_SHA256" --units-allowlist ft --unit-cents 100 --proof-partition advanced
```

Set `UNIT_FILE` and `UNIT_SHA256` to the audited packed file and its SHA. The named candidate is `/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl`; its unchanged read-only fixture is refused by direct binding. `UNIT_PACKING.md` gives the optional packing command and required Orchard frame authorities. After any rebind, run `tools/run_local_checks.py` with the CPU Python above. Neither fallback merges loose files into v6.

Unit binding is an **admission-input change**: `u.gz` transports the exact JSONL bytes; `m.json` adds `U_Faithful` to the pool manifest; `i.json` binds its native ordered indices; `u.json` records hashes and per-unit/per-dataset counts. These artifacts enter the operator bundle. Derivation stages `u.gz`, `m.json` and `i.json` into private, read-only namespace paths and adds their pins to the routing catalog. RGB bytes are not bundled: the complete staged RGB map/plan and frame store must resolve every supplied frame pin unchanged. Missing or conflicting RGB fails production admission. Full native materialization calls the sealed `selected_rows`, frame resolution, division/scene/QID filters and RGB audit before the sampler or proof counts units.

The prepared operator archive contains no database bytes. Its sole v7 input is the existing mode-0400 Orchard file `/project/community/jjyeung/okh7/s_22b44165/d.db`. The inherited staging code copies it into `/tmp/jjyeung/a_125c4c87/root/aws/u/ap/1130b378/d.db`, verifies the database SHA and removes file write bits. Inside the namespace, both `/scratch/fsw` and `/lustre/fsw` aliases resolve to that private union. The deployment receipt is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/1130b378/d.json` with SHA `4e53936594280c3434ddd9ad07b6e068d1f2758d670008e8c89b5bfa1bedd8b1`; its database path is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/1130b378/d.db`. The original producer receipt remains a separately pinned provenance record. No Trinity database path is a runtime input.

Operator steps below describe the future Orchard execution; this lane made no Orchard call. Keep all destinations private (directories 0700, files 0600 unless the sealed input requires 0400). Do not copy the descriptive reports to the public job surface.

1. Verify `SHA256SUMS` locally and transfer only `p_1130b378.tar` through the operator's approved route. Extract it into fresh bundle `/project/community/jjyeung/okh7/i_1130b378`. Verify its `sums.txt`. Set `H=/project/community/jjyeung/okh7/x_3fdda0fb`; its `SHA256SUMS.txt` must hash to `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3`. The local incomplete fixture cannot be used for production.
2. Run H1's authenticated native selection regeneration on its complete staged inputs, as in its `build/q.sh`. Retain the fresh raw `s1_pool.prepare` receipt as `NATIVE_RECEIPT`. Project it with the supplied helper; it verifies all regenerated ordered-index hashes and all non-room entries. It also binds the selector import-closure fingerprint to the archived trainer code; admission predicates must retain their parent hashes:

```bash
BUN=/project/community/jjyeung/okh7/i_1130b378
python3 -B "$BUN/q.py" \
  --parent "$H/k/pool_selection_eac5f9f0.json" --indices "$H/k" \
  --native-receipt "$NATIVE_RECEIPT" --implementation "$BUN/j.json" \
  --code-record "$BUN/c.json" --out "$BUN/q"
```

For a unit-bound packet, run the projection command with `--unit-binding "$BUN/u.json" --config "$BUN/config.json"` as well, using the authenticated CPU environment for the bound code tree. It executes sealed `s1_pool.prepare` on the unit source again, compares every ordered index, combines that source with the freshly checked parent selection, and refuses any final selection hash mismatch. The complete H1 inputs remain necessary. The source-selection counts are preliminary; the production proof reports post-filter counts, 1,000-step shares by family and question type, five bound traces per populated family, and missing units below 100 rows.

3. Obtain one independent review of the changed admission inputs and sampler. Supply identity-bound `review.json`, `staging.json`, `archive.json` and `4.json` in `EVIDENCE`, using the inherited production schemas. The durable source-archive attestation must cover the new tree. These are required inputs, not output claims of this build. Derive a fresh kit; the command validates the four records and their bindings with inherited read-only helpers. It needs no Slurm identity and writes no persistent run state. The full inherited `g.check` remains in the allocation-time job path:

```bash
KH=/project/community/jjyeung/okh7/x_1130b378
H=/project/community/jjyeung/okh7/x_3fdda0fb
python3 -B "$BUN/d.py" --source "$H" \
  --source-manifest-sha256 661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3 \
  --packet "$BUN" --bundle "$BUN" --out "$KH" \
  --selection-evidence "$BUN/q/q.json" --evidence "$EVIDENCE" > "$BUN/compare.json"
```

4. Run the independent complete content scan on the final kit and supply its `ANON_OK.json`, bound to the final manifest. Create new export sessions for the 20 part destinations in `e.txt` and install the private `sess.json` in the kit. The plan has three exports (100, 200, stop); stopB and stopC are alternate stop-slot names. Never reuse H1 sessions or approval evidence.
5. Bind and submit the production CPU proof, starting from an empty root. `p.py` requires a READY kit and native selection evidence. The proof resolves and hashes binaries at run time; it obtains bwrap from the kit's verified executable pin.

```bash
PARTITION=advanced  # advanced (one approved CPU job) or general
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" \
  --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap125c4c87 -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" \
  "$BUN/p_125c4c87.sh" "$BUN/a.json"
```

6. Inspect the named checks in `KH/o/JOB.proof.json`, its bound loader audit and the five printed traces per family. The required-family check permits recovery, size, unbound units, any zero-dose room cell, and bound units below 100 eligible rows; it must pass for every nonzero VQA cell and the four native routing cells. For a bound source, each unit below 100 is listed under absent_on_P with its count. Only allowlisted units with at least 100 rows enter the capped sampler. Confirm the proof receipt records the requested partition and actual node. The separate `go.json` must bind the final config, contract, wrapper and manifest; only then may the operator set `PROOF_JOB` and run `BUN/s.sh`. The submitter refuses any missing proof check or missing GO.

Local validation: 31 tests passed; production-form fixture records reach READY without Slurm identity or persistent initialization, and wrong evidence fails; OFF identity is exact on four tiny-model ranks; 288 final-config microsteps pass finite full-forward checks; two fixture derivations are byte-identical; the real-v7 loader audit covers 1,000 steps. These are bounded local results. Full native selection regeneration, production RGB/admission, complete routing counts, complete privacy scan and production CPU proof are NOT_RUN. `proof/GATES.json` is the authoritative gate list.
