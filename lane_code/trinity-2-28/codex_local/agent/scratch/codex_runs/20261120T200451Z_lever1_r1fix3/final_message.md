Fixed the item copy to preserve exact `a0` bytes and made the copied dispatcher opaque.

All 28 tests and both fresh-process checks pass. The actual CPU rehearsal scans all eight output files: names, raw contents, and JSON-decoded strings. Evidence: [REPORT.md](/scratch/jjyeung/orch_n30/lever1_c/r1/REPORT.md).

`PLACE.md`, `REPORT.md`, and `BUILD.json` agree:

- Token: `a99a83187be42`
- Delivery: **3,490,726 bytes**
- SHA256: `672076c0edda7703c22500f4c9b3ce1b7f6e6421f23b3cc5d2174eef5b8115dd`