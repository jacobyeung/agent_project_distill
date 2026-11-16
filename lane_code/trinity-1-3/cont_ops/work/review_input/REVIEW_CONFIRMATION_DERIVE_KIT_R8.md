# REVIEW_CONFIRMATION_DERIVE_KIT_R8

| R7 fix | Verdict | Evidence |
|---|---|---|
| 1. Neutral pool-selection reason | **FIXED** | Byte comparison confirms exactly one replacement: `route_planning_moved_to_vqa_store_d0` → `moved_to_vqa_store`. Nothing else differs; DEFERRED behavior remains unchanged. |
| 2. Remove the job label from scanned content | **FIXED** | Both `ja.sh` copies are identical (`61dacd80`), contain no job name, and reference `x_3b862883`. The label remains in the packet’s command-line `-J`, outside the requested scan scope. |
| 3. Rebuild pins, identity, authorization, manifest and packet | **FIXED** | Config key `6224c536`, identity `c07a4d53`, authorization `0123e18c`, launch pins and source seal agree. Both bundle checksum lists pass; the packet’s current bundle hashes match. |

The final manifest hashes to `47297116f57e565b78a1fa9a8f0216c9c331f0e789ef68983e3810c83fa1fcea`.

- **90 manifest lines** match the sealed manifest byte for byte.
- All **six changed/new members** match their manifest hashes. Only the old config entry disappears.
- Config, deployment, selector and pool-selection bytes match `out_v1_t10`. The authorization differs as intended; launch differs only in status.
- No superseded kit or pool-selection references remain in the r8 records.

**New defects: none found.**

## ANON scan

**CLEAN within the requested scope.** I scanned all six changed/new manifest members, all 12 active bundle files, and the supporting derivation records. No new identifying strings were found.

Inherited path/keyword matches: **593**, counting repeated copies separately. Python calls, counted separately: **12 `split`**, **6 `rsplit`**. No non-call `split` word or label was found.

Write this exact content to `x_3b862883/ANON_OK.json`:

```json
{
  "status": "CLEAN",
  "hits": 0,
  "manifest_sha256": "47297116f57e565b78a1fa9a8f0216c9c331f0e789ef68983e3810c83fa1fcea",
  "external": [
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/E00_MEMBERS.json",
      "sha256": "96ae3bf0e45edf887f4a2f2cb645f5e3afe4773e11e47996372c8e2f7b42b607"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/M544_SOURCE.json",
      "sha256": "efa496fdec92fdfeb0142a490f9751c11fc655ae4c9255f05db3ec0f46efd34d"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/artifact.json",
      "sha256": "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/derive_kit.py",
      "sha256": "4ad1a5ace3a8b830acbc9f1523d71ea2fdc74e97bb4596bd435f88af6de49812"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/repack_m544.py",
      "sha256": "e68e9095c8ebd0168495ca57984ee3b3c139f86ba739385eb793e8ca857f2557"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/sealed_vqa_receipt.json",
      "sha256": "524b14f9f180ba7d2c1c860cab294145b7370f3f1282960a55bbcbc6c5657634"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/v.json",
      "sha256": "fc9fea77c763c7202be382e6a31b4f70f77ad4084c0bbfb81de00cf3913bdc0d"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/vt.py",
      "sha256": "672df2c117e4db03aa2bdec9757b76b68faa494947f4654dd08e27c2078e9135"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/pool_selection_aa128e6f.json",
      "sha256": "f232d4160d75b5826d9e24aec324d690920a752a5bfaa33e5009d7550349dfc6"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/r8/4.json",
      "sha256": "0123e18c96522c8c5064524f84c4cc5992283daa596100f3f36389233098a3d1"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/r8/ja.sh",
      "sha256": "61dacd80eb8699e8655153731d8632db90c3954559fdc493c02a48e95fb824f7"
    },
    {
      "path": "/project/community/jjyeung/okh7/i_bb09a77d/r8/over.json",
      "sha256": "d295484209981324e28e11f6eb55051e0356bf07a3bb994ec7dd0235f873b1bf"
    }
  ],
  "scope": "Independent content scan for new identifying strings relative to sealed kit 07ca49df: all six new or changed final-manifest members and all external files listed here; supporting derivation records also reviewed. Inherited identifiers and Python split/rsplit calls counted only. Superseded bundle files and submission-command metadata excluded."
}
```

This verdict covers Job A. Install the certificate and complete the packet’s existing pre-submission checks before submission. I wrote no files, opened no SSH connections, and submitted no jobs.

**GO**