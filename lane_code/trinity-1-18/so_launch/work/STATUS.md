Task 1: startup trace complete; evidence and phase table are being packaged in out/REPORT.md.
Decision: use a conservative full config identity, including logical output paths. Byte-identical receipts retain their source/configuration seals; changing a run path must miss, rather than rewrite provenance.
Decision: cache prepared phase closures and frame receipts. All reuse requires SHA256; size/mtime alone never authorizes a hit.
Task 2: implementing an opt-in wrapper cache and CPU-only tests.
