R1-P uses the ruled vehicle-P family set. Recovery, room and size have zero launch dose; units stay at zero until a faithful file is bound. Full production evidence remains pending. Read `REPORT.md` and `proof/GATES.json` before deployment.

| Binding | Value |
|---|---|
| Config identity | `841f06376f20f7a446592f9af2daea2458e8b61ebf6967d37822f615be446948` |
| Tree | `1ed29ed34cc6c31bd3d66f8fc059e11969ee36a3d3a312fe6683f8a1d1618272` |
| Run / job name | `29c71287` / `a15_cot_ap29c71287` |
| Producer receipt SHA | `9fddc04354b75e88579e3a2a4e91e7a4468cc2ab0fa958051e151c898d1af173` |
| Database SHA | `0608dd985243e5e68dfd8206cbd474350b97b3af8d238cab5b562bd4354b3092` |
| Selection SHA | `88bd3399d40b857b3d8f3d3844fa108a8f3c9c7a8ca30861f50de1a7a23a2354` |
| Operator archive | `p_0a4d6fc3.tar` |
| Archive SHA | `db2a80b7832647aef89276a794fa585c9733c6180027eaa63e128938abe942c0` |

Relative to H1-1, this config disables S1 and S2, restores D0 scheduled sampling, uses milestones [100, 200] and stop 200, binds v6, removes room programs and adds capped family quotas. The 1,000-step schedule, stream totals (pose 64, VQA 128, routing 64, pointing 32), optimizer and initial weights stay in the inherited recipe. Field-level changes are in `../configs/diff_against_h1_1.json` and `../configs/diff_against_deployed.json`. `SAMPLER_REVIEW.patch` contains the trainer changes; no admission predicate changes. `DEPLOYMENT_REVIEW.patch` covers the staging, wrapper and submitter changes.

Rebind a store, size selector and mix with one command from the lane. This regenerates the admission table, config identity, code archive, loader audit, proof inputs and operator archive:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \
  --receipt /scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/receipt.json \
  --receipt-sha256 9fddc04354b75e88579e3a2a4e91e7a4468cc2ab0fa958051e151c898d1af173 \
  --orchard-store /project/community/jjyeung/okh7/s_8805de22/d.db \
  --mix configs/mix.json --reuse-census --proof-partition advanced
```

For v7, pass its exact receipt SHA, its local database via `--database` if needed, and its Orchard database path. `--size-selector FILE` accepts `{"field":"metadata.path","equals":"value"}`; omission keeps all admitted size rows eligible, while the mix controls whether any are drawn. The mix file controls requested doses and refill rules. Traced rooms enter through the bound VQA store and remain subject to the qualitative-trace predicate and cap. `--room-receipt FILE` binds optional provenance for traced rows already integrated into that store; it does not merge a second database. A separate room store must be integrated by its producer. Rebinding invalidates earlier first-batch and deployment proof results; rerun them against the new identity. Use `--reuse-census` only for unchanged store bytes and receipt. After rebinding, run `/scratch/jjyeung/envs/p1cpu/bin/python -B tools/run_local_checks.py` to refresh the local evidence and this packet.

To bind units, add `--unit-rows FILE --unit-rows-sha256 SHA` and optionally `--unit-cents N` (default 287 hundredths of a row per step, capped by eligibility). The file must contain faithful, already packed JSONL rows with full events and all 32 frame pins. No answer, event, or row payload is regenerated. A mismatched SHA, incomplete frame pins, sealed semantic refusal, or row removed by native source selection rejects the binding. The source must already be a clean slice; this command does not repair it.

Unit binding is an **admission-input change**: `u.gz` transports the exact JSONL bytes; `m.json` adds `U_Faithful` to the pool manifest; `i.json` binds its native ordered indices; `u.json` records hashes and per-unit/per-dataset counts. These artifacts enter the operator bundle. Derivation stages `u.gz`, `m.json` and `i.json` into private, read-only namespace paths and adds their pins to the routing catalog. RGB bytes are not bundled: the complete staged RGB map/plan and frame store must resolve every supplied frame pin unchanged. Missing or conflicting RGB fails production admission. Full native materialization calls the sealed `selected_rows`, frame resolution, division/scene/QID filters and RGB audit before the sampler or proof counts units.

The prepared operator archive contains no database bytes. Its sole v6 input is the existing mode-0400 Orchard file `/project/community/jjyeung/okh7/s_8805de22/d.db`. The inherited staging code copies it into `/tmp/jjyeung/a_29c71287/root/aws/u/ap/0a4d6fc3/d.db`, verifies the database SHA and removes file write bits. Inside the namespace, both `/scratch/fsw` and `/lustre/fsw` aliases resolve to that private union. The deployment receipt is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/0a4d6fc3/d.json` with SHA `9dd178c3af53d210512d154ccddb777fcb8d192c10456532ac16c6397dbf851a`; its database path is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/0a4d6fc3/d.db`. The original producer receipt remains a separately pinned provenance record. No Trinity database path is a runtime input.

Operator steps below describe the future Orchard execution; this lane made no Orchard call. Keep all destinations private (directories 0700, files 0600 unless the sealed input requires 0400). Do not copy the descriptive reports to the public job surface.

1. Verify `SHA256SUMS` locally and transfer only `p_0a4d6fc3.tar` through the operator's approved route. Extract it into fresh bundle `/project/community/jjyeung/okh7/i_0a4d6fc3`. Verify its `sums.txt`. Resolve the complete H1-1 deployment as `H`, whose source manifest must hash to `f13eccc20b7d2ee8b9622ce66db36e3cf561d0d41e69a367e9c435d5bf4261d6`. The local incomplete fixture cannot be used for production.
2. Run H1's authenticated native selection regeneration on its complete staged inputs, as in its `build/q.sh`. Retain the fresh raw `s1_pool.prepare` receipt as `NATIVE_RECEIPT`. Project it with the supplied helper; it verifies all regenerated ordered-index hashes and all non-room entries. It also binds the selector import-closure fingerprint to the archived trainer code; admission predicates must retain their parent hashes:

```bash
BUN=/project/community/jjyeung/okh7/i_0a4d6fc3
python3 -B "$BUN/q.py" \
  --parent "$H/k/pool_selection_eac5f9f0.json" --indices "$H/k" \
  --native-receipt "$NATIVE_RECEIPT" --implementation "$BUN/j.json" \
  --code-record "$BUN/c.json" --out "$BUN/q"
```

For a unit-bound packet, run the projection command with `--unit-binding "$BUN/u.json" --config "$BUN/config.json"` as well, using the authenticated CPU environment for the bound code tree. It executes sealed `s1_pool.prepare` on the unit source again, compares every ordered index, combines that source with the freshly checked parent selection, and refuses any final selection hash mismatch. The complete H1 inputs remain necessary. The source-selection counts are preliminary; the production proof reports post-filter counts, 1,000-step shares by family and question type, five bound traces per populated family, and missing units below 100 rows.

3. Obtain one independent review of the changed admission inputs and sampler. Supply identity-bound `review.json`, `staging.json`, `archive.json` and `4.json` in `EVIDENCE`, using the inherited production schemas. The durable source-archive attestation must cover the new tree. These are required inputs, not output claims of this build. Derive a fresh kit; the command invokes the inherited verifier and refuses incompatible evidence:

```bash
KH=/project/community/jjyeung/okh7/x_0a4d6fc3
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
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap29c71287 -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" \
  "$BUN/p_29c71287.sh" "$BUN/a.json"
```

6. Inspect the named checks in `KH/o/JOB.proof.json`, its bound loader audit and the five printed traces per family. The required-family check permits the named absences recovery, room and size; it must pass for every nonzero VQA cell and the four native routing cells. Once bound, units must also pass, with cm/ft/in counts at least 100 each. Confirm the proof receipt records the requested partition and actual node. The separate `go.json` must bind the final config, contract, wrapper and manifest; only then may the operator set `PROOF_JOB` and run `BUN/s.sh`. The submitter refuses any missing proof check or missing GO.

Local validation: 21 tests passed; OFF identity is exact on four tiny-model ranks; 288 final-config microsteps pass finite full-forward checks; two fixture derivations are byte-identical; the real-v6 loader audit covers 1,000 steps. These are bounded local results. Full native selection regeneration, production RGB/admission, complete routing counts, complete privacy scan and production CPU proof are NOT_RUN. `proof/GATES.json` is the authoritative gate list.
