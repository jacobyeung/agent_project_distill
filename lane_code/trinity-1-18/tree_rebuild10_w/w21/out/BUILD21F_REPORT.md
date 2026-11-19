NO-GO: ENV_UNRESOLVED:b/z.py:353:environment:environment capability escapes supported literal operations: os.environ

The final kit scan refused an unresolved environment operation. GO remains false.
Kit q and the sealed tree are unchanged. The required stop condition applies; no package was produced.

The scanner checks names first, then refuses unresolved environment writes and passed maps.
It follows environment aliases, blocks capability escapes, and rejects unsupported reflection and shell indirection.
The explicit runtime-value allowlist is empty. Computed keys and inherited maps have no exemption.
Scanner files: `work/build21/naming21.py`, `work/build21/environment21f.py`.
The job-side checker has no duplicate environment-scanning logic and was not edited.

Final scanner suite: 6 methods passed, with no failures or errors (`work/build21f/TESTS.json`).
Selected naming21c/21d controls: 21 methods passed (`work/build21f/REGRESSION_TESTS.json`).
Every naming21d negative Python case also runs verbatim in naming21f. Literal positive fixtures pass.
The forbidden-name controls execute before the strict gate; their naming21.py hash matches the final file.
All 6 requested full-kit mutations passed the frozen scanner and refused the new scanner
at the injected `b/o.py` location (`work/build21f/MUTATIONS.json`).
The reviewer's tuple mutation returned old PASS with 76,251 checked strings;
the new result is `ENV_UNRESOLVED:b/o.py:13:environment:environment key is not a literal string: os.environ[key] = value` (same source).
Changed-statement coverage: naming21.py: 12/13; environment21f.py: 322/342 (`work/build21f/COVERAGE.json`).
Uncovered statements remain listed there; this report does not claim complete coverage.

Kit q seal before and after: `5d300f192c97134c441696df0ab09435e2ad15be879603b230e6cd0c5d615522`.
Every kit file matched its starting bytes and SHA-256 (`work/build21f/INTEGRITY.json`).
The sealed-tree files matched the delivery manifest (same source).
Build21e's package and report matched their starting hashes (same source; originals preserved).

Not run after refusal: full naming21c/21d baseline suites, `focused.py`, or packaging.
No kit, tree, upload inventory, or build21e artifact was changed. No upload was attempted.
The report follows the explicit instruction to put the real-kit finding first and stop.
The old/new mutation comparison is retained as requested regression evidence.
