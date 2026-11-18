# REVIEW_CONFIRMATION_DERIVE_KIT_R7

| R6 fix | Verdict | Evidence |
|---|---|---|
| 1. Archive verification and Job B coverage | **FIXED for Job A.** All 14 verifier assertions passed in memory. Nonregular members, conflicting pins and absent manifest members now reject. [vt.py:66](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/vt.py:66), [84](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/vt.py:84), [88](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/vt.py:88). Job A verifies before staging at [ja.sh:20](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/ja.sh:20). Job B’s wrapper remains for its later review, as [packet:7](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/D0_JOB_A_PACKET_r7.md:7) specifies. |
| 2. Remove identifiers, rebuild and certify | **PARTLY FIXED.** The replacement paths, authorization and preparation derivation check out. The final scan still finds the labels below. |
| 3. Reconcile packet hashes | **FIXED.** All 12 bundle files match both supplied checksum lists and the hashes in [packet:17](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/D0_JOB_A_PACKET_r7.md:17). |

No further verifier change is needed for Job A. Its remaining requirements are a clean content scan, the certificate, and the packet’s existing pre-submission checks.

The final manifest hashes to **d58f338515fb316cc9d191e3a7f55cf85b312437a62686b9aa3dcdb3b99adf36**:

- **90 entries** retain exactly their sealed names and hashes.
- All **six changed records** match their manifest hashes.
- The old config is removed and replaced by `k/8d141f0e.json`; nothing is unexplained.
- Compared with `out_v1_t9`, only the authorization and launch status differ.
- Both locally absent payloads retain their sealed hashes. The Orchard derivation reports no absent source files.

## ANON scan

**NOT CLEAN.** New identifying strings:

| File | String |
|---|---|
| [orch_r7/k/pool_selection_13b52fee.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/orch_r7/k/pool_selection_13b52fee.json:1) | `route_planning_moved_to_vqa_store_d0` — once |
| [bundle_r7/pool_selection_13b52fee.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/pool_selection_13b52fee.json:1) | `route_planning_moved_to_vqa_store_d0` — once |
| [bundle_r7/ja.sh:3](/scratch/jjyeung/orch_n30/cont_ops/work/d0/bundle_r7/ja.sh:3) | `a15_cot_ap543f18fd` — new full work label; its prefix is inherited |

I scanned every changed manifest member and all 12 bundle files, plus the pulled-back supporting records. Inherited matching occurrences: **893**, counting repeated copies separately. Python calls: **12 `split`**, **6 `rsplit`**. No additional new identifying hits were found.

Do not write a CLEAN certificate for this content. No files were written, connections opened, or jobs submitted.

**GO AFTER FIXES:**

1. Replace the pool-selection reason with neutral wording while preserving DEFERRED behavior.
2. Replace the job name with an opaque label.
3. Rebuild all affected pins, configuration identity, authorization and manifest; update bundle/packet hashes, then rescan and certify the resulting manifest.