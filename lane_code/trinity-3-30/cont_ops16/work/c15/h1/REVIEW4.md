The review covers the supplied Orchard SRC, E, P and SRC-size listings, plus every login entrypoint. SRC has 193 entries; E has 103. Their 90-entry difference is runtime state, and all shared modes agree. The P listing contains no source runtime files.

| Check | Verdict | Finding and required behavior |
|---|---|---|
| `orch_h1.sh` extraction and `o.sh` freshness | OK | Both require private directories and refuse existing targets. The operator must rename `i_1be16f28` to `i_1be16f28.f2` before uploading. IDs stay fixed. |
| `r.py prepare` bytes and identity | OK | Derive verifies the sealed manifest and member hashes; prepare checks identity, contract and empty-reproduction bytes. |
| `r.py prepare` modes | FIXED | Whole-tree inventory includes 90 runtime entries. Inventory must use manifest members, their ancestor directories and the root only. |
| Source validation and copying | FIXED | The supplied P is clean, but recursive source validation, whole-`b/` copying and whole-`k/` copying could touch unlisted state. Only manifest members and their ancestor directories may be inspected or copied. |
| Source JSON dependency closure | FIXED | The source `k/*.json` scan could parse an unlisted runtime record. Read only JSON members in the manifest. |
| Runtime directories and certificate | FIXED | Create fresh empty 0700 `o/` and `runs/` for changed kits. Do not copy source runtime state or its unmanifested certificate; generate an UNREVIEWED certificate for independent certification. Empty reproduction compares sealed members only. |
| Sealed writes | OK | The output-scoped writer temporarily adds owner write permission and restores modes. This covers 0400 runtime files, 0500 `b/` and `b/sa/`, 0600 `k/` files and 0700 `job.sh`. Source modes are never changed. |
| `r.py stage` and `v.py` | OK | They read candidate and sealed `k/0.json`, verify changed archive/file bytes and check inherited part availability. They neither scan runtime state nor write sealed members. Missing or corrupt external staging inputs still refuse. |
| `g.sh` and `r.py copy` | OK | Copy reads the sealed deployment record and its explicitly pinned routing archive. Gate extraction and caches use mutable BUN directories. Dependencies, routing receipt/rows and a passing identity gate remain required. |
| `z.sh derive` and `r.py final` | FIXED | The shell checks immutable sums and dispatches. Final comparison and recorded mode digests must use the same manifest scope as prepare, including newly added kit members. Temporary launch updates preserve sealed modes. |
| `z.sh certify` and native `b/a.py` | OK | Certificate replacement uses the output writer. Native validation checks the manifest and exact executable inventory under `b/`, `k/` and the two job scripts. Runtime state is absent from those directories; a fresh valid CLEAN certificate is required. |
| `s.sh` | OK | It checks private roots, immutable sums, GO bindings and native kit integrity before submission. The source runtime directories and their modes are not inputs. No submission is run locally. |
| `jb.sh` preflight | OK | It checks `/tmp/jjyeung/a_17c4ffa4/runs`, not source `runs/469ddece`. Fresh output `o/` accepts logs; foreign runs in H1's own root still refuse. Sessions, disk capacity and native staging checks remain required. |
| Reproduction helpers | FIXED | Sealed-tree mode comparisons must use the manifest scope. Separate whole-fixture snapshots may check that synthetic source data remained untouched. |

Every FIXED item is implemented and tested. `tools/sealed_output.py:7–34` defines membership and scoped modes; generated `payload/d.py:417,567–577,627–633,702` restricts source reads/copies and creates fresh runtime state. `payload/r.py:55,83,88` uses this scope in prepare, final and comparison evidence; `z.sh` dispatches those paths without a separate inventory.

`evidence/fix4_listing.json` proves that the fixture has exactly the 193 SRC names/types/modes, including all 90 runtime entries. Fix-3 fails after producing p/e; current prepare, empty reproduction, final comparison and native certification pass. Source-access guards reject unlisted opens, stats and traversal. Additional unlisted b/k files and a dangling link are ignored; sealed-file, ancestor-directory and root mode mismatches still fail. Certification uses an explicitly synthetic certificate, not a deployment approval.

`evidence/fix4_sealed_modes.json` covers six derivations, write restoration, confinement, final comparison and certificate permissions. All eleven original/reviewer CPU checks pass in `evidence/fix4/tests.json`; all review harnesses pass syntax checks. The four-rank runner is unchanged and was not executed. `evidence/fix4/package.json` records matching repeated upload/fixture builds and an independently rebuilt trainer archive.

The listings establish names, types, modes and sizes; they do not establish external archive availability, installed gate dependencies, independent approvals or GPU execution. Those prerequisites and their existing refusals remain intact.
