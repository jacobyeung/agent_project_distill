# REVIEW_CONFIRMATION_DERIVE_KIT_R4

**GO AFTER FIXES.** The named regressions mostly reject correctly, but dependency closure, archive evidence and runtime-code protection still have gaps.

I diffed both versions and ran read-only, in-memory probes. I did not run the write-producing suite. During review, `PREPARATION_ONLY` was added; the latest supplied log reports **69 checks, FAILS 0**. This verdict covers `derive_kit.py` SHA-256 `175b2f3345c0ba875a6b0c1f88aaf12d45dc4dc694d476f624a43d4bea98c332`.

| R3 required fix | Verdict | Evidence |
|---|---|---|
| **1. Model staging and trainer namespaces separately** | **PARTLY FIXED** | Trainer, `hp()` and init-union views now distinguish hidden placements correctly. However, caller-supplied `small_members` becomes trusted placement in both current and sealed maps without binding its contents to e00. [derive_kit.py:193](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:193). |
| **2. Close runtime dependencies and revalidate inherited dependencies** | **PARTLY FIXED** | Runtime waivers now reject, and changed selections require their catalog mappings. Unchanged selections still bypass traversal, while unchanged document hashes terminate it. [derive_kit.py:225](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:225), [264](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:264). |
| **3. Protect code destinations, producers and sealed parts** | **PARTLY FIXED** | The named code paths, traversal paths, sealed parts and a1rows collision now reject. Other executable directories remain writable through additions, and archive membership remains an unchecked declaration. [derive_kit.py:275](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:275), [289](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:289). |
| **4. Preserve sealed dev bindings under the narrowed scope** | **FIXED** | Config overrides for the dev list and scene coverage, and added dev-list records, are refused. [derive_kit.py:300](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:300). |
| **5. Honor BLOCKED and preserve fixture provenance** | **PARTLY FIXED** | Both original defects are fixed: explicit BLOCKED binds, missing payloads stay in the manifest, and fixture ancestry rejects nonfixture derivation. The newly added preparation status has a separate authorization bypass. [derive_kit.py:320](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:320), [408](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:408), [422](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:422). |

**Round-3 probe recheck**

| Probe | R4 result |
|---|---|
| Hidden AS extra under `X/u` | Correctly absent from the trainer’s view. |
| Hidden tar member under `X` | Correctly absent from the trainer’s view. |
| Unrestricted `accept_unstaged` | Restricted; waiving the missing runtime database rejects. |
| Catalog-mapping removal | Rejects for the changed selection; **still accepts for an unchanged selection**. |
| Init declaration as placement | Rejects when the artifact lacks actual placement. |
| `X/b/i.py`, `X/b/g.py` destinations | Both reject. |
| Both reported `..` part paths | Both reject. |
| e00 and a1rows part reuse | Both reject as sealed parts. |
| Conflicting a1rows destination | Rejects. |
| Unlisted tar members | A declared extra rejects; omitted actual members and claimed export extras remain uncovered. |

**Remaining defects**

1. **Inherited catalog closure remains unsound.** Removing mapping `62113ff3…` while retaining the sealed selection passes `close()`. Runtime still needs that mapping for `remove_files`: [s1_pool_relocate.py:42](/scratch/jjyeung/orch_n30/cont_ops/work/d0/src/student_pilot/s1_pool_relocate.py:42). Preserving file placements does not preserve catalog resolution.

2. **Small-tar evidence can fabricate placement.** Removing the real VQA database extra and inserting its path/hash into `small_members` passes closure. The tool checks that the small-tar declaration stayed unchanged, but never establishes that the claimed member belongs to that tar.

3. **The destination restriction misses executable directories outside X.** An extra targeting `ap/7b30c1e4/u/ebe69df8/p/sitecustomize.py`, made reachable through a catalog entry, passes closure. That directory enters `PYTHONPATH` in [c.sh:385](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/b/c.sh:385). Protecting `X/b` alone does not enforce data-only additions.

4. **Archive declarations do not constrain extracted contents.** Adding `evil.py` beneath the export directory to both `export_member_names` and `tar_members` passes closure. The tool treats it as verified through the manifest without establishing that the manifest names it. Also, `tar_members` is not enforced against the actual archive: [c.sh:151](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/b/c.sh:151) extracts everything and checks only listed hashes.

5. **Status-only `PREPARATION_ONLY` skips authorization validation.** Its fresh, identity-bound `4.json` checks run only when `changing` is true. The unchanged branch accepts the status directly at [derive_kit.py:414](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:414). Runtime preparation checks source/expiry/mode, then returns before checking configuration-bound review; it does not repair the missing authorization binding. [g.py:82](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/b/g.py:82).

**D0 v1 and the m544 chain**

`make_over.py` reproduces `over_v1.json` exactly. Its small-member listing matches `E00_MEMBERS.json`; the real overrides pass closure. `out_v1_t2` retains both missing tar entries and remains **FIXTURE, unauthorized**.

The m544 **weight-integrity chain is sound for files actually named by the pinned manifest**: staging verifies the artifact, heads, manifest, index and shards before publishing `.verified`. The trainer then uses that mirror. Pre-job `full_weights.json` bytes are unnecessary for this check.

That chain does **not** prove archive completeness or exclude extra files. The real [m.tar declaration](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/over_v1.json:372) has no enforced binding between the repacked archive and its claimed inventory. This remains a defect in the supplied derivation.

**GO AFTER FIXES:**

1. Revalidate inherited dependencies whenever catalog resolution can change.
2. Bind small-member evidence to a trusted inventory of sealed e00.
3. Protect every runtime executable/import directory.
4. Bind archive inventories to actual contents and validate claimed export members against the pinned manifest.
5. Apply preparation authorization checks to status-only requests too.