# Fix for REVIEW_R8 (Codex gpt-6-astra, NO-GO, 1 finding) — assign.py 91d1d660..., tests 29 OK
1. replay_receipt reads the Session's version as getattr(session, 'spec_version', '3.12.2'), the sealed renderer's own default (ground_v312.py:252), so legacy v3.12 Sessions earn receipts for 3.12.2 records and still refuse other versions. Test test_replay_receipt_uses_sealed_replay (Legacy stub).
