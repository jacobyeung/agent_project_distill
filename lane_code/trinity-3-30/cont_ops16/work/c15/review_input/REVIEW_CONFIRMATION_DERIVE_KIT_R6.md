# REVIEW_CONFIRMATION_DERIVE_KIT_R6

Reviewed `derive_kit.py` **4ad1a5ac** against **ef166e88**. No files written, SSH connections opened, or jobs submitted.

The supplied derivation log reports **84 checks, FAILS 0**. I rechecked the probes in memory and reran all **11 verifier assertions** with an in-memory filesystem: **PASS**.

| R5 fix | Verdict | Evidence |
|---|---|---|
| **1. Conflicting placements and sealed destinations** | **FIXED** | Explicit conflicts no longer receive sealed fallback. Fresh-directory checks include sealed records, receipts and the supplied e00 listing. [derive_kit.py:255](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:255), [326](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:326). |
| **2. Actual archive enforcement and promotion** | **PARTLY FIXED** | Job A invokes verification before staging; derived-source promotion rejects. READY requires full-weights content for this changed init. However, training entrypoints lack verification, and the verifier has gaps below. [ja.sh:20](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/ja.sh:20), [derive_kit.py:299](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:299), [375](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:375). |
| **3. Preparation-to-training lifecycle** | **FIXED under the stated lifecycle** | Retiring Job A’s run/root and assigning Job B fresh run, kit and root tokens suffices. No `r8.py`/`g.py` change is necessary. Job B’s internal preparation and training share its job ID. Existing-root derivation rejects. [derive_kit.py:394](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:394), [r8.py:96](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/b/r8.py:96). |
| **4. Existing archive reuse and upload integrity** | **FIXED** | `ja.sh` refuses existing final or partial archives. Repacking forces non-composite upload and compares size and MD5. [ja.sh:15](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/ja.sh:15), [repack_m544.py:118](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/repack_m544.py:118). |
| **5. Preparation authorization, scan and write disclosure** | **PARTLY FIXED** | `4p.json` matches identity **3d00fbd3**; `i.authorize`, `x.ready` and `g.check` before persistence pass with preparation status/auth substituted in memory. It specifies `general`, mode `p`, zero GPUs. The packet now lists the previously omitted write trees. The scan finds new identifiers; the fixture remains unlaunchable. |

## Probe recheck and remaining defects

The R5 probes reject: conflicting sealed division; hidden AS/X placements; kit-code and FLA additions; catalog removal; runtime database waiver; unstaged init; traversal; sealed-part reuse; a1rows collision; fabricated `small_members`; foreign export names; names-only READY; and status-only preparation.

`make_over.py` reproduces `over_v1.json`. Real v1 closure passes: **4 documents walked, 11 additions, 9 removals, 7 chained export members**.

Remaining defects:

1. **Verification covers Job A only.** The inherited training scripts still reach extraction without `vt.py`. Deriving READY from the sealed kit prevents promotion bypass but does not enforce actual archive contents on Job B. Add verification to the reviewed Job B wrapper before staging. [job.sh:19](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/job.sh:19).

2. **`vt.py` accepts incomplete or contradictory manifest evidence.** Both probes returned PASS:
   - A manifest-named shard was absent because absence checks cover only `files`.
   - An explicit `files` hash contradicted the manifest because `setdefault` retained it.

   Require every manifest member and reject conflicting pins. Later init staging catches these errors, but verification should reject before extraction. [vt.py:83](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/vt.py:83), [86](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/vt.py:86).

3. **Directory entries bypass collision checks.** An unlisted directory over a sealed directory passes because directories skip duplicate/protection checks. Extraction can alter directory metadata. Validate permitted directories before skipping them. [vt.py:65](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/vt.py:65).

The packet also retains obsolete hashes in its upload/submission instructions alongside the correct r6 bundle hashes. Reconcile those instructions.

## ANON scan

**NOT CLEAN.**

New identifying strings:

| File | New string |
|---|---|
| [v1/4p.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/4p.json:1) | `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/20261115T2109Z_ORCH_GO_d0_job_a.md` — **two occurrences**. |
| Same file | `Preparation only: mode p on general, CPU (D0 job A); no training mode is authorized by this record` |
| [k/3e9eb72e.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t8/k/3e9eb72e.json:1) | New work labels in `ap/d0i04e67f96/m544/artifact.json` and `k/pool_selection_d0c.json` (**two references** to the latter). |
| [k/0.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t8/k/0.json:1) | `ap/d0i04e67f96/m544/artifact.json` — absolute and relative forms. |
| [k/launch.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t8/k/launch.json:1) | New reference to `k/pool_selection_d0c.json`. |
| [job/ja.sh:10](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/ja.sh:10) | `/tmp/jjyeung/d0r_${SLURM_JOB_ID}` |
| [job/repack_m544.py:1](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/repack_m544.py:1) | `D0`; line 4: `ap/d0i<run>/m544/artifact.json`; line 72: `ap/d0i`; line 122: `d0-m544-repack-v1`. |

The literal scan also finds new code contexts containing `split`: `vt.py:29` and `repack_m544.py:37,78`. Substring matching additionally finds `rsplit` at `vt.py:80` and `repack_m544.py:99`. These are Python operations, not project identifiers.

Inherited matching occurrences, counted without repeating their strings: **355** — config **2**, deployment **101**, pool selection **238**, authorization **14**; other requested files **0**. No additional new named benchmark, dataset, model or personal-name hits were found.

I verified **89 unchanged supplied members byte-for-byte**. Two sealed payloads remain absent. `out_v1_t8` remains **FIXTURE**, with the inherited authorization and **UNREVIEWED** certificate.

**GO AFTER FIXES:**
1. Complete verifier coverage for Job B and close the manifest/directory gaps.
2. Remove new identifying labels, rebuild with `4p.json` and both sealed payloads, then scan and certify the final manifest.
3. Replace stale packet hashes with the reviewed r6 hashes.