# Fixes for REVIEW_R6 (Codex gpt-6-astra, NO-GO, 2 findings) — assign.py 8cfcc90f..., tests 26 OK
1. Unrecorded calls: after removing each recorded call+'\n'+response block from the suffix, the remaining text may hold no tag other than <think>, </think>, <answer>, </answer> ('record_unrecorded_tag'), so every call in a head or recovery target is a recorded, replayed event. Test test_review6.
2. GT ids and selected ids per operand must be lists (no dict keys, no strings as character lists). Test test_review6.
