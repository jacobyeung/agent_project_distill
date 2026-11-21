Fixed and validated.

- **Cause:** [boot_order.py:30](/scratch/jjyeung/orch_n30/lever1_c/r1/boot_order.py:30) selected `a2.tar`, which contains no `v/`. Input 3, `a4.tar`, supplies `v/py`—a regular executable shell wrapper, not a symlink.
- **Fix:** Stage complete CPython, base environment, overlay and policy before boot; defer all bulk assets.
- **Tests:** All **73 tests** and two import checks passed. Real pinned archives reproduced the failure; corrected bwrap execution imported **411 modules** and verified **2,104 symlinks** plus ELF libraries. Validation and handoff checksums agree.
- **Token:** `a7e29d4c8f103`, superseding `a6f198d3c7b20`.
- **Delivery:** **3,700,123 bytes**.
- **Pre-bulk authenticated bytes:** **10,237,337,443**; zero bulk bytes staged.

SHA256: `86836622ee2b2b002510448d5777cfd3023817893b6f3d2649c21a716f055285`