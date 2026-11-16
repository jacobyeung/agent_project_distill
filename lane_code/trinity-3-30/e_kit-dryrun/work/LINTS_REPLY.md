Implemented the linters, AST cap checks, streaming row checks, fixtures, and tests. All 33 tests pass; the exact lint unittest command remains blocked by a missing package marker.

Files written (relative to `clone/tools/orchkit/`):
- `lint_config.py`, `rowschema.py`.
- `tests/test_lint_config.py`, `tests/test_rowschema.py`.
- `tests/fixtures/dryrun/lint/toy.schema.json`, `tests/fixtures/dryrun/rows/d0_rows.profile.json`.
- Reply: `/scratch/jjyeung/orch_n30/e_kit-dryrun/work/LINTS_REPLY.md`.

Required lint discovery with `-t .` fails before loading tests:
```text
ImportError: Start directory is not importable: '/scratch/jjyeung/orch_n30/e_kit-dryrun/clone/tools/orchkit/tests'
```
The brief excludes `tests/__init__.py` and forbids editing `__init__.py`; permission to create the missing marker is pending.

Python 3.6 unittest tails (lint without `-t .`; rows uses the required command):
```text
Ran 17 tests in 0.522s
OK
Ran 16 tests in 0.564s
OK
```
Required sandboxed pytest tail:
```text
.................................                                        [100%]
33 passed in 1.04s
```

Rules from the two D0 records that this checker cannot establish mechanically:
- Frame counts must come from permitted sources, never recordings or an unapproved routing lower bound; positive integers cannot prove provenance or source approval.
- Admitted store identities, populations, sealed companion stores and pool selection must match; phrase-only edits and v5's exact 81 exclusions must preserve retained rows and targets. Full stores, pins, and comparison artifacts are absent.
- Facing pairs must remain whole, including the 21 removed pairs; the checker supports groups, but the records supply no concrete pair-key field or exclusion list.
- Facing labels, totals, routes, trace grammar, and frame citations must satisfy the cited validators and ground truth. Their implementations, permitted fallback semantics, concrete vocabulary, and source evidence are absent; generic checks cannot verify semantic correctness or residual error rates.
- Withheld, dev, and benchmark scenes must be excluded; their actual identifiers are absent. The prohibition on routed decisions using a D0 checkpoint on withheld rooms concerns downstream use, outside these rows.
- Every row must pass the sealed preparation under its actual layout, followed by the complete mode-p run; the required preparation code and runtime inputs are outside this build.
- Independent layout/diff agreement, fixed-seed family and changed-row reviews, and orchestrator admission require independent evidence and human decisions.
- Procedure-only rows remain by default pending the user's decision; counting and size supervision must not be dropped, and unverified citations must not be restored. These require admission policy and source comparisons.
- Step-100/200 reads must compare counting/size against the step-544 journal and report toward/away separately on the named evaluations; training outputs and reference measurements are unavailable.
- The planned A0 repair requires verified first-seen frames, byte-identical rebuilt rasters, and four additional validator rules; those artifacts and rule definitions are absent.
