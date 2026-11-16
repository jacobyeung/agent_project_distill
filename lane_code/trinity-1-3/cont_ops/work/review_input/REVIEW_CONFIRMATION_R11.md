# REVIEW_CONFIRMATION_R11

## A2 fixes

| Fix | Verdict | Finding |
|---|---|---|
| 1. Bundle path | **FIXED** | `BUN` survives sourcing `c.sh`; both invocations use `a3/s2.py`. Its existence is checked before ranks start. |
| 2. Deadlines | **PARTLY FIXED** | Rank/final-call budgets are corrected, but persistence and reporting still lack reliable hard deadlines. |
| 3. Publication ordering | **PARTLY FIXED** | Status/tar/upload failures block stage 2. A logging failure can still replace mode `p`’s exit code. |
| 4. Anonymous output | **PARTLY FIXED** | Category and row-key hashing work, and the blacklist is gone. Arbitrary receipt strings still reach the summary. |
| 5. Family accounting | **FIXED** | The input path matches `c.sh`’s `hp()` mapping. The census computes admitted families, absent input keys per family, and `not_in_input`. |

Remaining A2 fixes:

1. **Terminate persistence descendants.** [s2.sh:46](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5a3/a3/s2.sh:46) kills only the subshell PID. A bounded reproduction returned from `wait` with **143**, then its child continued and finished. Apply a deadline to the whole copy process group. The plain `timeout` calls in [ja2.sh:19](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5a3/a3/ja2.sh:19) also send TERM without forced termination; a TERM-ignoring test exceeded its deadline. Add forced termination and reserve time for finalization overhead.

2. **Make failure logging nonfatal.** [ja2.sh:40](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5a3/a3/ja2.sh:40) can abort under `set -e` when the failure-reporting `step` also fails. With mode `p` returning **7**, simulated publication and logging failures produced **1**. Preserve the recorded mode-`p` code even when project logging fails.

3. **Validate every summary output field.** [s2sum.py:13](/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5a3/a3/s2sum.py:13) treats any identifier before `:` as an exception class. `PrivateLabel: private message` becomes `PrivateLabel 950ff6f802495e64`. The summary also copies stream names, component names, and the entire resources object. Synthetic receipt strings survived through all four channels. Use approved labels and numeric resource fields; hash other strings. Sanitize top-level failures too, because `ja2.sh` merges stderr into the summary file.

The synthetic census test correctly produced two refused input keys and one foreign rebuilt key. I did not open the real row store.

## B fixes

| Fix | Verdict | Finding |
|---|---|---|
| 1. `SLOT_TO_GCS` publication | **FIXED** | Exit 6 requires a valid manifest digest, successful marker generation, nonempty `.part`, and successful rename. |
| 2. Staging config key | **FIXED** | The obsolete evidence key is removed. Staging pins are regenerated; `review.json` remains `ddd34ff2…`. |

In-memory tests of the publication branch returned:

- **6:** success.
- **5:** marker failure, empty marker, rename failure, hash-command failure, malformed hash, or failed object verification.
- **7:** failed fallback with trainer code 7.

Both supplied harnesses contain the exact fallback branch. I did not execute their file-writing commands.

The B fixture manifest recomputes to `a40b3d8c1be8ef3b83b8a7182b187ed3fc40525e1d4cae0aee108be48e442da8`. Only `k/staging.json` and its launch pin changed from round 10. Identity and contract recompute correctly; the review/staging/contract checks pass before persistence.

Both bundle checksum files and shell/Python syntax checks pass.

## New defects and deployment caveat

The A2 logging failure above is newly reproduced.

`fx_rec_ready` contains the intended READY/authorization changes, but its manifest still contains the FIXTURE launch hash. Treat it as a gate-test copy. Generate and verify the actual Orchard READY manifest before filling B’s certificate.

Both absent payload entries remain equal to their sealed manifest lines.

## ANON scan

**Static content: CLEAN for both reviewed bundles.** A2’s runtime-output requirement remains open as described above.

I scanned the five `a3/` files, the three changed B external files, and all eight B records changed from the sealed kit. The five round-10 identifying literals are absent. Python call counts are A2 **0 split / 0 rsplit** and B **3 split / 0 rsplit**; there are no other `split` labels. B’s eleven flagged word occurrences outside paths are inherited: ten `arkit`, one `revsi`.

The certificates cover current static bytes. Any further script edit requires refreshed hashes and a confirming scan.

A2 — exact `ANON_OK.json`:

```json
{
  "status": "CLEAN",
  "hits": 0,
  "manifest_sha256": "17784778267ecf138b167d6a2bc7ffb25c9fcade5943cefc01e51f54b6e5be34",
  "external": [
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/vb5.json", "sha256": "c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/4.json", "sha256": "578f6d966fa3610a17da569f4b8f029f9bb114ea86e87a6db043d944bd03cc6b"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/full_weights.json", "sha256": "211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a2/over.json", "sha256": "df4a9f6c707f2c646f120f18839dcb98cdac936fe875fd533a6c168b90a2fb63"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a3/fam.py", "sha256": "a451ec5d92be44ea003036908b79532386ad942089504b55c80b810eaa9c580f"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a3/ja2.sh", "sha256": "a4a0a94ef984ebc4ad5680bf1c33cf133864cfe1ea4c7a30418b4b551c29d313"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a3/s2.py", "sha256": "1514dabad4e47e5121758d6d39e0dc6ac39f9e7bbcd177f83d8db872b636cbf1"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a3/s2.sh", "sha256": "47fba87f2b2abcf9a2e2edcde6295bf13e61c3af9ea33743faa08968c688388b"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/a3/s2sum.py", "sha256": "89cffbc7604169f6a919513634020962e4f780f355ceaf8456a6e75022efdb6e"}
  ],
  "scope": "Static-content confirmation of the unchanged round-10 manifest and derivation inputs, plus the five listed a3 execution files. Superseded a2 execution files are excluded and must remain unused. No new identifying literals were found. Inherited identifiers and Python split/rsplit calls are count-only. Row-store contents are excluded under the supplied exception. This certificate does not certify runtime-output sanitization or authorize execution; round-11 A2 fixes remain outstanding."
}
```

B — current template:

```json
{
  "status": "CLEAN",
  "hits": 0,
  "manifest_sha256": "<VERIFIED_ORCHARD_READY_MANIFEST_SHA256>",
  "external": [
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/vb5.json", "sha256": "c95023e46d9171071c7cb738367dae115bebaf4a6519931ec514d20e68ffa5d8"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/4.json", "sha256": "3f64925ab47ef60416ac574c806aabad5d4f3ecc6bab51503968eb10befdf9d7"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/full_weights.json", "sha256": "211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/jb.sh", "sha256": "3b8f0162cba302e06aea764d1b876689938dc26595e8bbda16d95739d09964e8"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/over.json", "sha256": "70bbb61e876bd3883c6eb6fb83ae245f88911b3bd2a3751245bacfb9a9a8669c"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/review.json", "sha256": "ddd34ff2dadf204960306d960ca039f417ebed93bd62957955479add9f595927"},
    {"path": "/project/community/jjyeung/okh7/i_bb09a77d/b5/staging.json", "sha256": "133bffea4c9320fa747f7d6275f43b64ed57cf31fc6c95314fc811721b9100cf"}
  ],
  "scope": "Eight new or changed fixture records, six listed b5 bundle files, and the shared job receipt. Round-11 changed content was scanned; unchanged content retains the round-10 review. Final Orchard records must match fixture manifest a40b3d8c1be8ef3b83b8a7182b187ed3fc40525e1d4cae0aee108be48e442da8 except launch.json status=READY and production_authorized=true, with its manifest hash updated accordingly. Both locally absent payload entries must retain their sealed hashes. Inherited identifiers and Python split/rsplit calls are count-only. Row-store contents are excluded under the supplied exception. Content certification does not grant submission authorization."
}
```

## Verdicts

**A2 — GO AFTER FIXES:** enforce descendant deadlines, preserve mode-`p` status when logging fails, close summary text leaks, then refresh the bundle hashes and certificate.

**B — GO AFTER FIXES:** both requested code fixes pass. Only the stated Orchard READY manifest comparison and final certificate binding remain.

No files were written. I used no SSH or network, opened no session JSON or row store, and submitted nothing.