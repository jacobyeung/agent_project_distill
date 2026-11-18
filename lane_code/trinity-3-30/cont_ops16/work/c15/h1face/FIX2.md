# Fix round 2 — local gate complete
H1 `17c4ffa4` binds to `x_3fdda0fb`; old deployment bindings refuse before receipt reads. D0 `359fcc3c -> x_f5c353f7` is byte-for-byte unchanged.
| Audit | Summary; source lines in REPORT.md |
|---|---|
| CHANGED | H1 deployment root and config provenance; only `kit/launcher/binding.py:6` changes in the kit. |
| SAME | Run, namespace, q8 names, part suffixes, relative .done naming/format, stop claims, three stop generations, duplicate layout. |
No local `1dd078da.json` found (one fixture directory unreadable). Retained `d12ae795.json` computes to the supplied production identity and confirms 32 anchors duplicated to 64 frames; the kit has no training-config pin.
Tests PASS: 94 candidate, 53 ported readk, 53 original readk, 4 refute; runtime fixture 4 items; final-pin test 1; all 167 checksum entries verify.
Binding SHA256: `c8e3666cb6502df7dc8936e9a632924cd1880303d6e065607e774e5745da9ffc`.
FINAL_PINS SHA256: `ff2b4b1a0dc75e1ce9b8c1014713a7d2e542bf7deb93b3a358eb617d5fc7c925`.
SHA256SUMS.txt SHA256: `03a3d08a2a677786e6182672c7b9fb0d749799b9ca7e5417349d4000eaf37368`.
Unchanged tar SHA256: `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21`.
Unchanged item SHA256: `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b`.
Evidence: `evidence/FIX2_AUDIT.json`, `EXPORT_SOURCES.json`, `FIX2_{TESTS,READK_PORTED,READK_REFERENCE,REFUTE,RUNTIME}.log`, `FIX2_FINAL_PIN_TEST.log`, `FIX2_SHA256_CHECK.log`.
All writes stayed in h1read; no SSH/network/Orchard/GCS/GPU/Git/deletion. FIX2.md and post-seal verification logs are excluded from FINAL_PINS to avoid circular hashes.
