# REVIEW_CONFIRMATION_DERIVE_KIT_R3

**GO AFTER FIXES.** Fix 3 is fixed. Fixes 1, 2, 4, 5 and 6 remain partly fixed.

I compared `derive_kit_r3.py` with `derive_kit.py`, read the tests and their **53-check, `FAILS 0`** log, and ran targeted read-only Python probes. I did not rerun the suite because it writes under `work/d0/testruns`. No files, SSH connections or submissions were made.

| r2 required fix | Verdict | Evidence |
|---|---|---|
| **1. Close the final dependency graph** | **PARTLY FIXED** | The walker follows new receipts and export manifests, but placement modeling and exemptions remain unsound. [derive_kit.py:93](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:93), [derive_kit.py:144](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:144). |
| **2. Enforce nested data-only restrictions** | **PARTLY FIXED** | `lm`/`heads` are preserved and additions receive checks. Runtime-code destinations, part-path traversal and incomplete ownership checks remain. [derive_kit.py:79](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:79), [derive_kit.py:180](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:180), [derive_kit.py:246](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:246). |
| **3. Compare actual stream changes** | **FIXED** | Closure compares resulting stream pins. Repeating the unchanged routing pin no longer rejects a VQA-only change. [derive_kit.py:167](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:167). |
| **4. Reject conflicting staging entries** | **PARTLY FIXED** | Conflicts between declared `extra`/`tars` entries are rejected. Collisions with `a1rows`, staged imports and other producers are not covered. [derive_kit.py:51](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:51), [derive_kit.py:96](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:96). |
| **5. Apply identity/readiness checks to every effective change** | **PARTLY FIXED** | Identity-only changes now require complete identifiers; roots are normalized. However, explicit `status="BLOCKED"` still has no effect when `changing` is false. [derive_kit.py:228](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:228), [derive_kit.py:318](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:318). |
| **6. Keep fixtures permanently non-READY and unauthorized** | **PARTLY FIXED** | The immediate fixture output is correctly marked. Missing payloads disappear from its manifest, and subsequent derivation neither preserves an incompleteness record nor checks referenced payload completeness independently. [derive_kit.py:213](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:213), [derive_kit.py:327](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:327). |

**(a) Required placement versus `resolvable()`**

`AS` and `AL` denote the two code-aws prefixes; `X=AS/ap/8865619b`.

| Consumer/path | Required physical location |
|---|---|
| Ordinary paths outside `ap/8865619b` | Both prefixes resolve into `U`; tars and extras can populate it. |
| Trainer reading `X/u/...` | `U/ap/8865619b/u/...`, because bwrap explicitly mounts that subtree. An **AS-prefixed extra** instead lands in `NX/u/...` and is hidden. |
| Trainer reading `X/k/...` or `X/b/...` | `NX/k/...` or `NX/b/...`. A tar member placed under the corresponding union path is hidden. The AL spelling still resolves through `U`, not `NX`. |
| Trainer reading `X/runs`, `X/models`, `X/data2root` | Their explicit mounts override the union and NX locations. |
| Init staging | The artifact is read through `hp()`. Heads, manifest, index and shards are read directly from `U` through the separate Python `host()` function. |
| Trainer using the verified init mirror | `$C1_INIT_LOCAL/<artifact-sha16>/`; raw union weights may therefore be valid init inputs even when their original AS paths are hidden during training. |

These distinctions follow from [c.sh:31](/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/b/c.sh:31), `c.sh:128`, `:151`, `:227`, `:238`, `:347`, `:393`, and [carrier_c1_run.py:842](/scratch/jjyeung/orch_n30/cont_ops/work/d0/src/student_pilot/carrier_c1_run.py:842).

**`resolvable()` does not model this exactly.** It collapses AS/AL and all consumers into one map. It also treats single-file declarations—including `init`—as placement evidence, and omits the small-tar member inventory.

Read-only probes confirmed that it reports both a hidden tar member at `X/hidden.json` and a hidden AS extra at `X/u/hidden.json` as resolvable.

**(b) Dependency closure and exemptions**

The new traversal is useful, but it still accepts missing runtime dependencies:

- **`accept_unstaged` is unrestricted.** Removing the real v1 VQA database placement and adding its hash with an arbitrary reason still makes `close()` succeed. It also accepts an entirely unplaced stream receipt. `derive_kit.py:150`.
- **`inherit` does not distinguish provenance from runtime dependencies.** Removing the catalog mapping for `remove_files[0]` (`62113ff3…`) from the real operator configuration still passes closure. Runtime relocation calls `pinned()` on that unresolved Trinity path. `derive_kit.py:148`; `s1_pool_relocate.py:14`, `:42`.
- **The init declaration proves its own placement.** Removing the synthetic artifact JSON from every tar/extra entry still passes closure because `cur.init` inserts it into `R`. `derive_kit.py:97`.
- **`base_R` is not a verified dependency closure.** An unchanged document stops traversal even when its dependencies or catalog mappings need revalidation. Unchanged stream roots are skipped altogether. `derive_kit.py:154`, `:167`.
- **`via_catalog` and `leaf` need typed traversal.** Catalog fallback checks a mapped destination but does not reproduce the relocator’s field-specific behavior. `leaf` itself checks placement, but suppresses traversal; export recognition is structural, and other documents require content only when their names end in `.json`. `derive_kit.py:146`, `:154`, `:158`, `:162`.
- **`pins_in()` misses companion-key pins**, including pool-manifest `withhold`/`withhold_sha256`, `list`/`list_sha256` and `v2`/`v2_sha256`. `derive_kit.py:109`; `s1_pool_relocate.py:32`.

The two operator exceptions have different justifications:

1. **BUILD_MANIFEST `64bdf9c5…`: justified as provenance for this admission path.** VQA rebuilding reads the input receipt’s database, not its `source` document. See `carrier_c1_data.py:543` and `s1_admission.py:189`. This supports a narrowly scoped exception.
2. **Division `0d28fdd4…`: supported as staged, not provenance-only.** `inv8.out:7` records the member hash, and `c.sh:115` verifies e00 before extracting its contents into `U`. Admission actually reads this division. The resolver should represent that evidenced placement rather than waive a runtime dependency.

**(c) Staging restrictions, shapes and part names**

The new checks reject many malformed entries and ordinary sealed-part reuse, but remain incomplete:

- Every catalog entry is a traversal root. A caller can make an arbitrary added file “reached” by adding its hash/path to the catalog.
- A read-only probe accepted an extra targeting **`X/b/g.py`**. The same construction can target **`X/b/i.py`**, which `r.sh:73` executes after staging. Safe relative paths do not enforce data-only destinations.
- Removal ownership uses directory prefixes, not dependency ownership. It does not prove that a removed sibling belongs exclusively to the replaced input. `derive_kit.py:184`.
- `PART` accepts `/project/community/jjyeung/okh7/../e00` and `/project/community/jjyeung/distill/okit/in/..`; both passed `check_entries()`. `derive_kit.py:69`.
- Sealed-part protection indexes only `tars` and `extra`. Reusing sealed **e00** or an **a1rows part** in a new entry passed closure. `derive_kit.py:189`.
- An extra with a conflicting hash at the immutable `a1rows.dest` also passed. Runtime stages `a1rows` after extras, so its bytes replace the purported dependency. `c.sh:136`.
- Tar staging extracts every member but verifies only listed members. Declared reachability alone does not constrain unlisted archive contents. `c.sh:151`.

**(d) Operator claims and dev-list bindings**

**The ROUTE_direct KeyError claim is correct.** The lane selection removes the source while retaining its report entries and manifest membership. `s1_pool_relocate.py:27` indexes the absent source; `s1_routing.py:420`–`:422` has the same assumption. The operator’s selection differs from the sealed selection only in ROUTE_direct’s status and reason, preserving the required entry.

**The dev-list check is necessary but insufficient.**

The strongest missed binding is the **pool manifest**:

- `Pool` derives its scene lists from manifest exclusions: `s1_pool.py:40`.
- Relocation overwrites selection/report list pins from those manifest-derived lists: `s1_pool_relocate.py:39`, `:52`.
- The passing test changes the selection’s list pins but retains the old manifest. Its manifest still binds `969cdb56…`. Relocation therefore restores the old binding, and `totals()` rejects it against the new config.

The derive check also misses nested `upstream` reports, benchmark bindings, census consistency and effective stream receipts’ `source_scene_exclusions`. Runtime validates these through `s1_exclusions.py:232`, `:251`, `:257`.

One qualification to the QUESTION file: in-job admission **rebuilds pointing and VQA and rematerializes routing** before preparation (`s1_admission.py:183`). An old report on an original receipt does not automatically survive into that effective stream.

Admission evidence must also cover the new configuration and policy. Runtime checks those bindings in `b/g.py:98` and `b/d.py:64`, `:103`; successful derivation is not fresh admission evidence.

**(e) Other defects and supplied-output scope**

The explicit-BLOCKED and fixture-ancestry defects remain as recorded above. The passing fixture demonstrably omits both missing payloads from its regenerated manifest while deployment references survive.

`out_v1a_t2` is **FIXTURE, unauthorized**. Its changed configuration fields are output paths, VQA and routing-selection inputs. It retains the sealed init and dev list; it does not establish the proposed m544/full-exclusion configuration.

**GO AFTER FIXES:**

1. Model staging and trainer namespaces separately, including the init mirror and evidenced small-tar members.
2. Close schema-specific runtime dependencies; restrict exemptions to identified provenance fields and revalidate inherited dependencies.
3. Protect runtime-code destinations, cover every staging producer, validate normalized part paths and reserve all sealed parts.
4. Validate manifest-derived dev bindings, recursive reports and effective admission evidence.
5. Honor explicit BLOCKED and preserve fixture/incompleteness provenance across derivations.