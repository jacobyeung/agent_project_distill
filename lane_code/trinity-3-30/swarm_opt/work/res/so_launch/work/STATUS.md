2026-11-19T07:05:43Z — Continuation; deadline 08:45Z. Host trinity-1-18. UTC checked at each task boundary.

Verification: all four delivered patches applied independently to fresh copies with `patch --batch --fuzz=0 -p1`; their tests passed. The combined application and all 24 selected native regressions passed. Exact commands and outputs: out/tests/20261119T070308Z/. That snapshot contains 19 cache, five wrapper, seven frame, nine checkpoint and three timing tests.

Task 1: the measured S1 mode-p envelope is 140.57 minutes in 172660 and 145.27 minutes in 171377. Building the report's complete phase table and preparation-input audit. R2 has a different host receipt and no supplied timing measurement.

Decision: retain the conservative full config identity, including logical output paths. Byte-identical receipts retain their source/configuration seals; changing a logical run path must miss. Only physical pool relocation is supported.
Decision: retain prepared phase closures and frame receipts. Every reused payload requires SHA256; size/mtime alone never authorizes a prepared-input hit.
Decision: retain S1-only integration. R2 needs a distinct adapter for its checklist, absolute output paths, frame-host admission and metadata index; this delivery does not claim R2 cache coverage.

Task 2: a real-tk_env regression showed that R1_MOUNT and R1_STUDENT_HEX changed the restore key before tk_env into a different publication key after tk_env. Evidence: out/tests/07_environment_key_before_fix.txt (one failing test). Key construction now excludes these ambient values because tk_env overwrites them and its implementation is hashed. All 20 cache tests pass: out/tests/07_environment_key_after_fix.txt. This changes the environment-key implementation based on a failing test; the saved full-config and provenance decisions remain intact. Repackaging and fresh-tree validation remain required.

Task 3: opt-in parallel frame hashing, same-allocation checkpoint verification memo and launch/lock timing are implemented. Their seven, nine and three tests passed. No GPU or production-sized timing was run. Auditing the smaller-win claims before writing expected savings.

Task 4: final REPORT.md and NOTE_FOR_TREE_REBUILD.md remain unfinished. All production switches default OFF. Inputs remain read-only. No Git, SSH, GPU, network download or heavy I/O ran.
