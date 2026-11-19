Done. All five findings are fixed.

- Four configurations each ran 173 tests: 171 passed, two expected skips.
- All 39 native output files matched byte-for-byte.
- The 820-key, four-chunk tests pass; all 13 deliberate variants were caught.
- Patches and manifest verified against `b262e7a7`.

[Report and exact outputs](/scratch/jjyeung/orch_n30/so_modep/out/REPORT.md) · [Rebuild instructions](/scratch/jjyeung/orch_n30/so_modep/out/NOTE_FOR_TREE_REBUILD.md)

Both switches remain OFF on N’s first launch. Enable them on a later launch only after real-store parity is established.