For labels matching `trinity-<n>-<n>`, the filter preserves each top-level lane directory and the explicit source/delivery containers before applying name, path and MAXDIR exclusions. `.git` is repository metadata, so it remains excluded. Every direct child directory of `codex_runs/` is also protected as a run record (except `.git`). Protected containers do not rescue files below a separately excluded child or ancestor. File extension, size and content deduplication rules still apply.

Both scanners call the same `protected_dir()` and `excluded_dir()` functions. `dry_count.py` reads the regex constants by AST and applies the same predicates to the requested folder and all its ancestors, in both review modes. Its main function and all code outside the constants reader/root gate remain byte-identical.

The table records measured matches in all eight inventories, summed over changed-file observations. Rules overlap, so the bytes must not be added. These are matches before other rules, not incremental savings. Full example paths are in [rule-evidence.json](measurements/rule-evidence.json).

| Accepted rule | Files matched | Bytes matched | Decision and reason |
|---|---:|---:|---|
| test_runs / test-artifacts | 24,921 | 122,251,978 | These directories contain test-generated JSON rows and synthetic kits. Match these exact basenames without regard to case. |
| LANE_TEST_OUTPUT / B2_TEST_OUTPUT / TMPDIR / R2_PROOFS | 4,855 | 71,848,310 | These named test-output roots contain generated records. Uppercase variants bypass the existing lowercase rules; the new names match without regard to case. |
| 32 hexadecimal characters in a directory | 18,749 | 165,876,728 | UUID/content-addressed run directories hold repeated test outputs. Match a run anywhere in a basename, including uppercase hex and longer runs. |
| Mixed letter/digit eight-character suffix | 24,295 | 221,065,411 | Python temporary directory suffixes recur across unrelated test families. Require exactly eight trailing [a-z0-9_] characters after an underscore, including a digit and a letter. Exempt word-plus-number suffixes ending in one to three digits from this generic rule; explicit tempfile families and hex rules still apply. |
| Known tempfile families | 11,140 | 117,657,476 | sam_r10_ljgx_vjf has no digit in its suffix, so the generic rule intentionally does not catch it. The observed sam_r10_, finetune_gate_test_, provisional_ and driver_ families also get an explicit eight-character suffix rule. |
| Nested orch_n30 tree | 6,262 | 51,571,506 | These paths hold copied trees from other lanes, including fb_pack/ro/orch_n30. The label is stripped before applying relative-path rules. |
| Nested scratch/jjyeung tree | 648 | 9,470,368 | These paths hold staged payload/file copies, including payload/files/scratch/jjyeung and so_in/scratch/jjyeung. |
| Vendored Python library | 2,349 | 37,160,274 | The directory-only PATHRE `/lib/python[0-9][^/]*/` identifies bundled interpreters, including Python 3.12 standard-library sources. Keep the existing site-packages rule. Source filenames such as `src/lib/python_compat.py` stay eligible. |
| Conda metadata | 66 | 1,640,904 | conda-meta records belong to the bundled interpreter rather than the lane source. |
| Staged interpreter environment | 2,433 | 38,865,933 | /payload/environment also contains Tcl, package metadata and other runtime support files outside /lib/python. Restrict this exclusion to the payload path; do not ban environment globally. |
| Extracted work archives | 1,435 | 21,714,098 | /work/extract contains unpacked copies. Preserve a source package named src/extract. |
| Rehearsals | 579 | 8,860,536 | rehearsal and rehearsal<N> contain synthetic build runs and repeated kit trees. Match the named family without regard to case. |
| Attics | 1,153 | 17,423,662 | attic contains retained build attempts and repeated packages, including w24/attic. Match the exact basename without regard to case. |
| Nested build work | 0 | 0 | The task explicitly identifies work/build*/work as a generated-tree pattern. None of the supplied changed-file inventories contains this exact direct-child pattern; the fixture verifies it. No savings are attributed to it here. |
| Generated build review tests | 671 | 5,551,813 | Under work/build*, review_tests holds repeated before/go/no kit trees and their outputs. Scope the rule to that build path so independent review_tests source folders remain eligible. |
| Generated build integration tests | 27 | 516,622 | Under work/build*, integration, integration2 and integration3 hold synthetic BUILD.json/kit/q test trees. The supplied inventories contain 27 files in these trees. Scope the rule to that build path. |
| patch_validation_* | 0 | 0 | The task identifies this generated validation prefix. It does not appear in the eight changed-file inventories; the fixture checks both cases. No measured savings are attributed to it. |
| fixtry | 293 | 19,172,710 | sb_ktchk2/work/fixtry contains trial code/runtime copies. Match only the explicit basename, without regard to case. |
| sandbox / sandboxes | 829 | 7,823,553 | sandbox appears in generated job trees. Exclude these exact singular/plural names without regard to case; do not ban every name containing sand. |
| Named pytest output trees | 290 | 1,296,748 | Only `pytest_kit`, `pytest_dry`, `pytest_dry_verified`, and `pytest_patched` beneath `work/` or `out/` are excluded. Their inventory descendants are generated pytest case directories containing synthetic packages, JSON outputs, and shell stubs. Other pytest-prefixed names stay eligible. |
| Nested lane copies | 193 | 589,295 | `/work/{fcopy,scopy,lcopy,pcopy}/` contains nested `sb_mask_phrase` lane copies and generated gate-test runs. Scope these exact names to work. |
| Existing cache rules | 0 | 0 | Keep the existing cache, __pycache__, .cache and node_modules exclusions. No matching changed-file directories are present in these inventories; this is not claimed as new savings. |

The following candidate exclusions were rejected. These decisions preserve sources and reviewable deliverables rather than inferring a file’s purpose from a broad parent name.

| Rejected name or pattern | Reason |
|---|---|
| Any top-level lane basename under a node label | The task requires every lane to remain traversable, including a lane whose name resembles a temporary directory. |
| `out`, `out_round<N>`, `in`, `kit`, `kits`, `src`, `tests`, `code`, `inputs` | These are explicit preservation requirements. Their own directory entries bypass name/path and MAXDIR pruning; known by-product children are still excluded. |
| `work/prompts`, `work/tree` | These hold authored prompts and source trees. They bypass their own directory gates. |
| `work`, `build*`, `w24`, `runtime` | Each can mix scripts, configuration and generated results. Exclude only identified descendants. |
| `base`, `replay*`, `new`, `tree`, `student_pilot`, `vendor` | The inventories include substantial Python source under these names. Generic vendored project sources are not the same as a bundled interpreter. |
| `payload`, `files`, `environment`, `lib` | These names alone are ambiguous. Use the copied-tree and interpreter path rules instead. |
| Global `extract` | A source module may use this name. Restrict the rule to `/work/extract/`. |
| Global `review_tests` or `integration<N>` | These may be source test folders. Only their generated occurrences immediately under `work/build*` are excluded. |
| `sequence_native`, `sequence_final`, `resolver` | The inventories contain Python and shell files alongside kit material; the names do not establish that the entire directory is disposable. |
| `run`, `run3`, `run4`, `plant`, `plant3`, `plant4`, `suite`, `checks`, `validation`, `output`, `round<N>` | These broad names can hold useful scripts or receipts. Their identified temporary, interpreter and copied-tree descendants are filtered independently. |
| `reports`, `receipts`, `reviews`, `prompts`, `config` | These describe the deliverables the task requires retaining. |
| Every eight-character suffix | Pure letters, pure digits, and underscores alone do not meet the required generic tempfile rule. Known generated families get explicit exceptions. |
| Seven- or nine-character mixed suffixes; uppercase suffix characters | These do not match the requested eight-character lowercase tempfile alphabet. |
| Short hex IDs or hex strings in filenames | The generic hex rule applies to directories containing at least 32 hex characters. It does not ban hashed source/config filenames. |
| Global case-insensitive matching for all existing rules | Only the new named by-product families need case folding. Preserve the existing predicates, including their `$` anchor behavior for trailing newlines, and the strict lowercase tempfile alphabet. New alternatives use `\Z`. |

Case-insensitive explicit names are `test_runs`, `test-artifacts`, `LANE_TEST_OUTPUT`, `B2_TEST_OUTPUT`, `TMPDIR`, `R2_PROOFS`, `patch_validation_*`, `fixtry`, `rehearsal<N>`, `attic`, `sandbox` and `sandboxes`. Existing cache rules remain in force. The generic regexes and path rules are visible in the complete [filter](tools/lane_code_filter.py).


The regex evidence counts raw directory-path matches, including overlaps and protected run-record names. The simulation applies protection first and provides the actual path-only retained counts. Ancestor gates apply even when `LCS_REVIEW2_FIXES` is unset.
