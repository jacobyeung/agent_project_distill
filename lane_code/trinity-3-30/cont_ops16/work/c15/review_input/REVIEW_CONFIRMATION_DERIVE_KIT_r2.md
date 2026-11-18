# REVIEW_CONFIRMATION_DERIVE_KIT

**GO AFTER FIXES.** Finding 4 is fixed; findings 1, 2, 3 and 5 remain partly fixed. This is a code-based review, not a test-suite pass.

| r1 finding | Status | Confirmation |
|---|---|---|
| **1. Config/staging consistency** | **PARTLY FIXED** | [derive_kit.py:119](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:119) checks overridden receipt pins and init-artifact agreement. It never reads receipts to validate database dependencies, checks complete init-weight dependencies, or closes pool/catalog dependencies. Replacing `deployment.tars`/`extra` without overriding those config fields bypasses their checks. |
| **2. Data-only enforcement** | **PARTLY FIXED** | [derive_kit.py:61](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:61) rejects unknown fields and unsafe `add_k` names. However, line 103 replaces the entire `init_artifact`, allowing training settings such as `lm` and `heads` to change. Line 104 permits unrestricted replacement of staging inventories, including unaffected inputs. |
| **3. Complete run identity** | **PARTLY FIXED** | [derive_kit.py:85](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:85) requires new identifiers for config/deployment/addition overrides. Identity-only overrides do not set `changing`: a lone new `run_key` still retains the old kit key and persistent root. Root distinctness also compares raw strings, so a trailing slash can disguise the same location. |
| **4. Launch provenance** | **FIXED** | [derive_kit.py:150](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:150) regenerates `inherited_streams`, `source_selection`, the config/seal bindings and admission directory from the resulting config. |
| **5. Readiness and evidence** | **PARTLY FIXED** | [derive_kit.py:159](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:159) requires newly supplied review, staging and `4.json`, each bound to the identity—but only when `changing` is true. Changed outputs receive an appropriately unreviewed `ANON_OK` placeholder. Unchanged fixtures and identity-only changes bypass these protections. |

Required fixes, including new defects:

1. **Validate the final dependency graph, regardless of which override keys were supplied.** Receipt hashes in caller-declared inventories do not establish database coverage. The test’s “consistent D0” receipts contain only `schema` and `stream`; its new tar inventory supplies no corresponding row databases. Init heads, manifests, indices and shards need equivalent closure checks.

2. **Enforce nested data-only restrictions.** Preserve `init_artifact.lm`/`heads` and unaffected staging entries. Validate staging paths and destinations rather than accepting arbitrary dictionaries.

3. **Compare actual stream changes.** [Lines 138–141](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:138) reject a valid VQA-only change if the caller explicitly includes the unchanged routing receipt. Omitting that routing field accepts the same resulting configuration. Validation must depend on the resulting pins, not whether an unchanged field was repeated.

4. **Reject conflicting staging entries.** [Lines 44–51](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:44) correctly recognize both `extra` and `tars`, but silently let `extra` hashes override tar hashes. Runtime stages extras **before** tars (`b/c.sh:316–317`). Thus the checker can accept the desired hash while staging subsequently replaces those bytes. Reject conflicting destinations after accounting for path aliases.

5. **Apply identity and readiness checks to every effective change.** Identity-only changes must require complete new identifiers and applicable evidence. Explicit `status="BLOCKED"` must also take effect when `changing` is false. Normalize persistent roots before comparing them.

6. **Make every fixture unconditionally non-READY and unauthorized.** [Line 169](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:169) preserves the source’s `READY` status for `{"fixture": true}`; `production_authorized` remains true. The regenerated manifest omits missing payloads, so a subsequent nonfixture derivation sees no missing manifest entries. Preserve fixture/incompleteness provenance and verify referenced payload completeness independently of manifest membership.

The `ANON_OK` placeholder correctly fails `a.py`’s production scan check; it does **not** certify launch readiness.

I read the suite without running it because it writes outside `/tmp`. Its READY test manually flips launch metadata; it does not exercise the tool’s nonfixture READY branch or its review/staging/authorization rejection cases. The unchanged-fixture byte-equality assertion actually preserves the READY defect. No files were written, and no SSH or submissions occurred.