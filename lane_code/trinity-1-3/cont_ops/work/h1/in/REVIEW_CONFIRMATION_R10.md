# REVIEW_CONFIRMATION_R10

## Part 1

**A2’s derivation checks pass; its execution bundle needs fixes.**

- The final manifest hashes to `17784778267ecf138b167d6a2bc7ffb25c9fcade5943cefc01e51f54b6e5be34`. Its **90 unchanged lines** match the sealed manifest; all six changed/new members match their hashes.
- Orchard records match the fixture, except launch status and the intended authorization replacement. Orchard `4.json` equals the bundled authorization.
- Identity `e757f64a7f46a4ff40eec3ced85f26fdd5fb3c3cab5052db55c7c6a6a7f01587` recomputes correctly. Authorization allows only `p`; its GO hash matches the supplied event.
- Both job receipts differ from `r_v5_orchard.json` only in `database.path`. Their hash is `c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8`.
- `make_over_b.py` defaults reproduce `over_b.json` byte for byte. Bundle checksums and shell/Python syntax pass.

The cited `v5/orchard_check.json` is absent; matching evidence exists under `v5a2` and `v5b`. I accepted `indep_v5.out` as the supplied independent row comparison and did not open the row store.

**Admission reuse is correct once the script path is fixed.** Stage 2 uses the same namespace functions, mode-`p` Python path, frame-root mapping, config pin, destination and 16 threads. Its 512-GiB limit differs from stage 1’s default, but memory is not part of the request binding.

Each process reuses the completed preparation/frame phases. Rank proofs bind the same configuration, preparation, code, plans, CPU device, Torch version and thread count that final admission checks. Distinct rank files and attempt directories avoid a journal race. Final admission reuses all four valid proofs without loading another model.

The sealed code compares existing `data_receipt.json` and refuses disagreement; it does not overwrite it. Stage 2 adds its own admission receipt. Its ordinary return code does not replace stage 1’s recorded status.

**Required fixes:**

1. **Fix the overwritten bundle path.** [s2.sh:12](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/s2.sh:12) sources `c.sh`, which assigns `IN=$R/in`. Consequently, lines 26 and 39 invoke `/project/community/jjyeung/distill/okit/in/a2/s2.py`, not the supplied bundle script. Use a separate variable that `c.sh` does not assign.

2. **Enforce the stated time limit.** [s2.sh:38](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/s2.sh:38) gives final admission another 900 seconds beyond `CAP`. Persistence and summary work are uncapped. `06:00:00` and `WALL=21600` agree, but stage 2 is not bounded to three hours. Bound finalization and reporting as well.

3. **Require successful stage-1 publication before stage 2.** [ja2.sh:16](/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/ja2.sh:16) converts upload failure into successful logging; stage 2 proceeds after tar/upload failure. Propagate publication success and skip stage 2 if publication fails, while preserving the mode-`p` result.

4. **Remove identifying literals and unrestricted diagnostic text.** [s2sum.py:4](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/s2sum.py:4) introduces the ANON hits below. Its blacklist also lets other pool/rule/source messages through unchanged; I reproduced this with synthetic text. Hash all free-form errors and potentially identifying QIDs instead. Both helpers open SQLite read-only, but that alone does not guarantee anonymous output.

5. **Supply refused counts per family.** [fam.py:21](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/fam.py:21) counts stored rows and parse failures. It does not calculate the admitted/refused family accounting required by the supplied GO; `unparsed` is not a refusal count.

## Part 2

**B’s configuration, review binding and pin closure pass.**

| Check | Recomputed value |
|---|---|
| Configuration identity | `80f4af947f0ca9edfac04041cf65e079edb92752618b2de6dc4078491a88f1ba` |
| Admission contract | `aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19` |

I verified the six substantive configuration changes, plus installation of the new admission-review pin. Gate code remains sealed; the trainer archive matches its sealed hash. All nine export-member pins match the repack receipt, and the full-weights manifest matches its embedded bytes.

Recomputed closure reports four newly traversed documents, eleven additions and nine removals, with only the existing division and provenance waivers. **The drafted `review.json` attestation accurately describes these checks; no rewrite is needed.**

With READY launch bytes supplied in memory, `g.check(..., mode="p")` passes the review, contract and staging checks. I stopped before persistent-state operations. This does not establish native admission or authorize submission.

The wrapper diff affects only the insufficient-project-space branch. Normal copying, restoration and `TK_JOB_START` remain unchanged. The supplied harness contains the exact fallback block. Metadata tests reject missing MD5, mismatched size/digest and malformed size. Failed pipelines cannot produce verified success; an abandoned object may remain unclaimed. Restoration does not automatically consume that object.

**Required fixes:**

1. **Check publication of `SLOT_TO_GCS`.** [jb.sh:134](/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/jb.sh:134) does not check the manifest-hash command or marker write. With marker production replaced by a failing command, the exact branch still prints success and exits **6**. Validate the hash and publish the marker successfully before returning 6. Otherwise return failure. Existing fallback failure returns the trainer’s nonzero status, or 5 when the trainer succeeded.

2. **Correct staging’s config key.** [staging.json](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5b/staging.json) names `f8094169`, the pre-review configuration. `fx_rec` launches `d6827df0`. Update or explicitly relabel that evidence field, then regenerate its pins.

For final manifest comparison, the two locally absent payloads **already have lines in `fx_rec/SHA256SUMS.txt`**. Preserve and compare those hashes; their local absence is not permission to waive them. READY launch changes include both `status="READY"` and `production_authorized=true`.

## ANON scan

**A2: NOT CLEAN.** Across six changed manifest members and nine bundle files, five definite new identifying literals occur in `bundle_tree/a2/s2sum.py:4`:

```text
rows_reb
dose
arkit
scannet
/scratch/jj
```

The same regex also contains `orch`. Remove the blacklist by hashing free-form diagnostics unconditionally.

**B: CLEAN for the current reviewed bytes.** I found no new identifying strings in its eight changed fixture records and six bundle files. With whole paths counted once, the scan counted **360 inherited matches for A2** and **362 for B**. Python calls: A2 **0**; B **3 `split`**, **0 `rsplit`**. No other `split` label appeared. The row store was excluded.

A2 cannot receive a CLEAN certificate. This exact record describes—and blocks—the current bundle:

```json
{
  "status": "NOT_CLEAN",
  "hits": 5,
  "manifest_sha256": "17784778267ecf138b167d6a2bc7ffb25c9fcade5943cefc01e51f54b6e5be34",
  "external": [
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/vb5.json", "sha256": "c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/4.json", "sha256": "578f6d966fa3610a17da569f4b8f029f9bb114ea86e87a6db043d944bd03cc6b"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/fam.py", "sha256": "187c6353e1a7118eb99a353ca88c77e93d8c8abedc1c2ba6408cc9746f1a6630"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/full_weights.json", "sha256": "211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/ja2.sh", "sha256": "e992d30a86dc18d8ca9c276f30585c120ae397013c5aff92c285e3c6fdc66f13"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/over.json", "sha256": "df4a9f6c707f2c646f120f18839dcb98cdac936fe875fd533a6c168b90a2fb63"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/s2.py", "sha256": "1514dabad4e47e5121758d6d39e0dc6ac39f9e7bbcd177f83d8db872b636cbf1"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/s2.sh", "sha256": "34caf8ca936cb2e1cd013b85066f1f09f73d7d870bde46903e53004aa3760525"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/s2sum.py", "sha256": "6422ee9cd7983792fc277b8d44be36baff1c8f4c4cc21d5e3a2942e8613e78ed"}
  ],
  "scope": "Six new or changed final-manifest members and all nine listed bundle files. Five new identifying literals occur in a2/s2sum.py. Inherited identifiers and Python split/rsplit calls counted only. Row-store contents excluded under the supplied exception. This record does not authorize execution."
}
```

B’s template below covers **current bytes only**. The required wrapper/staging fixes will also require updated external hashes, regenerated records and a confirming scan before use.

```json
{
  "status": "CLEAN",
  "hits": 0,
  "manifest_sha256": "<VERIFIED_ORCHARD_READY_MANIFEST_SHA256>",
  "external": [
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/vb5.json", "sha256": "c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/4.json", "sha256": "3f64925ab47ef60416ac574c806aabad5d4f3ecc6bab51503968eb10befdf9d7"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/full_weights.json", "sha256": "211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/jb.sh", "sha256": "6c2a99f1f34bffedbea3429d54ff89eff89abbcdc037b06186c8fb1fc9abc4d5"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/over.json", "sha256": "680f04340035f7a1b0146738962c41ef8b62ead0e5817af9a73ab855f69d1d0d"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/review.json", "sha256": "ddd34ff2dadf204960306d960ca039f417ebed93bd62957955479add9f595927"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/staging.json", "sha256": "ece79bb1ccc4d4f2632d716513ac5e8fceb2600822ab2abfe9cb292e99b2c6ff"}
  ],
  "scope": "Eight new or changed fixture records, six listed b5 bundle files, and the shared job receipt. Final Orchard records must match the reviewed fixture except the verified READY launch transition; both locally absent payload manifest entries must retain their sealed hashes. Inherited identifiers and Python split/rsplit calls counted only. Row-store contents excluded under the supplied exception. Content certification does not grant submission authorization."
}
```

I wrote no files, used no network or SSH, opened no session-capability files, and submitted nothing. Tests used read-only inspection and in-memory substitutions.

**A2 — GO AFTER FIXES:** correct the script path, enforce deadlines and publication ordering, sanitize diagnostics, supply refused-family counts, and rescan/rebind the bundle.

**B — GO AFTER FIXES:** check success-marker publication, correct staging evidence, regenerate and verify the READY manifest, and refresh the content certificate. Separate submission GO and native admission gates remain required.