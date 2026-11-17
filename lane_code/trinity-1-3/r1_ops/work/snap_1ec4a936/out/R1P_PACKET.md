R1-P is built for review and blocked for production: recovery is refused, units are only partly admitted, and full production evidence is pending. Read `REPORT.md` and `proof/GATES.json` before deployment.

| Binding | Value |
|---|---|
| Config identity | `1ec4a936d86d0f93237a704e276a8b1b54dd6a7e465990d9ba6f4089ae559feb` |
| Tree | `a0a454331ff04e280670fc19b465b75f97b38ffad8920f67ec643d7a13d768f4` |
| Run / job name | `31e9f783` / `a15_cot_ap31e9f783` |
| Producer receipt SHA | `9fddc04354b75e88579e3a2a4e91e7a4468cc2ab0fa958051e151c898d1af173` |
| Database SHA | `0608dd985243e5e68dfd8206cbd474350b97b3af8d238cab5b562bd4354b3092` |
| Selection SHA | `d07c3bd55161332ffc03112caa6065ea776f748122c20d462385f2b81df47171` |
| Operator archive | `p_17eb48c6.tar` |
| Archive SHA | `d6e18979907f5a25c6eb3e6a9dca47cc277705bbb3bfb65d24d691c33fb879e1` |

Relative to H1-1, this config disables S1 and S2, restores D0 scheduled sampling, uses milestones [100, 200] and stop 200, binds v6, removes room programs and adds capped family quotas. The 1,000-step schedule, stream totals (pose 64, VQA 128, routing 64, pointing 32), optimizer and initial weights stay in the inherited recipe. Field-level changes are in `../configs/diff_against_h1_1.json` and `../configs/diff_against_deployed.json`. `SAMPLER_REVIEW.patch` contains the four trainer-file changes; no admission predicate changes. `DEPLOYMENT_REVIEW.patch` covers the staging, wrapper and submitter changes.

Rebind a store, size selector and mix with one command from the lane. This regenerates the admission table, config identity, code archive, loader audit, proof inputs and operator archive:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \
  --receipt /scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/receipt.json \
  --receipt-sha256 9fddc04354b75e88579e3a2a4e91e7a4468cc2ab0fa958051e151c898d1af173 \
  --orchard-store /project/community/jjyeung/okh7/s_8805de22/d.db \
  --mix configs/mix.json
```

For v7, pass its exact receipt SHA, its local database via `--database` if needed, and its Orchard database path. `--size-selector FILE` accepts `{"field":"metadata.path","equals":"value"}`; omission keeps all admitted size rows. The mix file controls requested doses and refill rules. Traced rooms enter through the bound VQA store and remain subject to the qualitative-trace predicate and cap. `--room-receipt FILE` binds optional provenance for traced rows already integrated into that store; it does not merge a second database. A separate room store must be integrated by its producer. Rebinding invalidates earlier first-batch and deployment proof results; rerun them against the new identity. Use `--reuse-census` only for unchanged store bytes and receipt. After rebinding, run `/scratch/jjyeung/envs/p1cpu/bin/python -B tools/run_local_checks.py` to refresh the local evidence and this packet.

The prepared operator archive contains no database bytes. Its sole v6 input is the existing mode-0400 Orchard file `/project/community/jjyeung/okh7/s_8805de22/d.db`. The inherited staging code copies it into `/tmp/jjyeung/a_31e9f783/root/aws/u/ap/17eb48c6/d.db`, verifies the database SHA and removes file write bits. Inside the namespace, both `/scratch/fsw` and `/lustre/fsw` aliases resolve to that private union. The deployment receipt is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/17eb48c6/d.json` with SHA `b4c148e03f7201b117e7e81e5a53e758ce2f2d0f9fc91d74e30937aa505f819f`; its database path is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/17eb48c6/d.db`. The original producer receipt remains a separately pinned provenance record. No Trinity database path is a runtime input.

Operator steps below describe the future Orchard execution; this lane made no Orchard call. Keep all destinations private (directories 0700, files 0600 unless the sealed input requires 0400). Do not copy the descriptive reports to the public job surface.

1. Verify `SHA256SUMS` locally and transfer only `p_17eb48c6.tar` through the operator's approved route. Extract it into fresh bundle `/project/community/jjyeung/okh7/i_17eb48c6`. Verify its `sums.txt`. Resolve the complete H1-1 deployment as `H`, whose source manifest must hash to `f13eccc20b7d2ee8b9622ce66db36e3cf561d0d41e69a367e9c435d5bf4261d6`. The local incomplete fixture cannot be used for production.
2. Run H1's authenticated native selection regeneration on its complete staged inputs, as in its `build/q.sh`. Retain the fresh raw `s1_pool.prepare` receipt as `NATIVE_RECEIPT`. Project it with the supplied helper; it verifies all regenerated ordered-index hashes and all non-room entries:

```bash
BUN=/project/community/jjyeung/okh7/i_17eb48c6
python3 -B "$BUN/q.py" \
  --parent "$H/k/pool_selection_eac5f9f0.json" --indices "$H/k" \
  --native-receipt "$NATIVE_RECEIPT" --out "$BUN/q"
```

3. Obtain one independent review of the changed admission inputs and sampler. Supply identity-bound `review.json`, `staging.json`, `archive.json` and `4.json` in `EVIDENCE`, using the inherited production schemas. The durable source-archive attestation must cover the new tree. These are required inputs, not output claims of this build. Derive a fresh kit; the command invokes the inherited verifier and refuses incompatible evidence:

```bash
KH=/project/community/jjyeung/okh7/x_17eb48c6
python3 -B "$BUN/d.py" --source "$H" \
  --source-manifest-sha256 f13eccc20b7d2ee8b9622ce66db36e3cf561d0d41e69a367e9c435d5bf4261d6 \
  --packet "$BUN" --bundle "$BUN" --out "$KH" \
  --selection-evidence "$BUN/q/q.json" --evidence "$EVIDENCE" > "$BUN/compare.json"
```

4. Run the independent complete content scan on the final kit and supply its `ANON_OK.json`, bound to the final manifest. Create new export sessions for the 20 part destinations in `e.txt` and install the private `sess.json` in the kit. The plan has three exports (100, 200, stop); stopB and stopC are alternate stop-slot names. Never reuse H1 sessions or approval evidence.
5. Bind and submit the production CPU proof, starting from an empty root. `p.py` requires a READY kit and native selection evidence. The proof resolves and hashes binaries at run time; it obtains bwrap from the kit's verified executable pin.

```bash
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" \
  --binding "$BUN/BINDING.json" --out "$BUN/a.json"
sbatch -J a15_cot_ap31e9f783 -o /dev/null -e "$KH/o/%j.err" \
  "$BUN/p_31e9f783.sh" "$BUN/a.json"
```

6. Inspect the named checks in `KH/o/JOB.proof.json`, its bound loader audit and the five printed traces per family. This packet's required-family check cannot pass with absent recovery rows. Resolve the repair-family blocker before requesting production approval. The separate `go.json` must bind the final config, contract, wrapper and manifest; only then may the operator set `PROOF_JOB` and run `BUN/s.sh`. The submitter refuses any missing proof check or missing GO.

Local validation: 17 tests passed; OFF identity is exact on four tiny-model ranks; 288 final-config microsteps pass finite full-forward checks; two fixture derivations are byte-identical; the real-v6 loader audit covers 1,000 steps. These are bounded local results. Full native selection regeneration, production RGB/admission, complete routing counts, complete privacy scan and production CPU proof are NOT_RUN. `proof/GATES.json` is the authoritative gate list.
