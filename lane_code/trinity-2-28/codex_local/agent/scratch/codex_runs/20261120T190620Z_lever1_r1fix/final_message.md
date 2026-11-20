All four fixes are complete. Stopped for re-review; nothing submitted.

- **Staging:** actual staging passes at **16,501,670 / 33,554,432 bytes**.
- **Labels:** recursive scan passes; all **150 prompt/RGB bindings** remain unchanged.
- **Naming:** opaque paths and deny-list checks pass; **270 source hashes** match.
- **Deadlines:** worker and transfers are bounded; simulated slow-upload failure receipt finishes at **238/240 seconds**.

**22 tests pass**, plus both import/admission checks, shell checks, checksum verification, and the missing-depth dry run.

Updated [PLACE.md](/scratch/jjyeung/orch_n30/lever1_c/r1/PLACE.md) and [REPORT.md](/scratch/jjyeung/orch_n30/lever1_c/r1/REPORT.md).

Delivery: **2,668,881 bytes**  
SHA256: `8dee5268e3fe2583a60464c57223d031a3153b3ab32e907095ffaeef8365b8ee`