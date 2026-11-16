# Source changes

All original C8r source files remain byte-identical (`SOURCE_IDENTITY.json`). Added modules are a partial review implementation. Production packet integration is incomplete.

| File | Lines | Change | Reason | Brief item |
|---|---|---|---|---|
| `guard_kit/guard_backend.py` | 1–109 | Authenticate candidate metadata and prepare/serve using C8r | Preserve restoration checks; candidate closure required | 1, 2, 3 |
| `guard_kit/guard_core.py` | 1–154 | Strict completion receipt, identity comparison and proof/canary sequencing | Fail closed on foreign exports and proof mismatch | 1, 3, 4, 5 |
| `guard_kit/guard_export.py` | 1–31 | Wrap unchanged reviewed stager with plan-bound plain-text receipt | Check candidate identity, bytes and digest before extraction | 1 |
| `guard_kit/names.py` | 1–36 | Reversible name substitutions and occurrence scanner | Audit name-only edits without modifying other JSON values | 6 |
| `guard_kit/native_arm.py` | 1–38 | Select native AST prefix and one refusal row | Preserve sealed kernels and omit scripted serving | 3 |
| `guard_kit/packet.py` | 1–85 | Draft-plan preparation, regular-tar checks, resource arguments and explicit release refusal | Prevent incomplete kit from launching | 1, 6, 7 |
| `guard_kit/reviewed/chain_save.py` | 1–137 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/checker/common.py` | 1–43 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/checker/export_check.py` | 1–84 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/export_stage.py` | 1–224 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/orchard_job.py` | 1–279 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/orchard_results.py` | 1–194 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/orchard_stage.py` | 1–302 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
| `guard_kit/reviewed/return_io.py` | 1–68 | Copy reviewed dependency unchanged | Keep reviewed export-admission semantics and full checker | 1 |
