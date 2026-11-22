C″ de202f58; kits q de53310b, n 3cf38b0b, n_go 1bb191b9 and qd aaa03e58 verify unchanged.
The outer rcj publisher writes pc_n.log.tail, pc_p.log.tail and rd.log.tail when present, capped at 64 KiB each, with full sizes and SHA256 in timings.json.
N child failures retain FAIL and E95, adding the exit code and final exception line (up to 4,096 characters); raw tail bytes are unchanged.
Eight new tests, twelve publication tests, four recorder tests, rcj contract/sample checks, name scanning and exact delta replay pass; tested statuses and mode b bytes match.
nd.py remains byte-identical; tails share the remaining sub-5 MB artifact budget, with budget_limited=true if space forces a shorter tail; JSON metadata is separate.
UPLOADS_24M4O3.json/.list declare seven files against Orchard qd 7d358ff5 and the stated rcj pins; superseded bytes remain in attic.
No production job or upload ran; the actual E95 cause remains unknown. VALIDATION.json records limits; FAILURES.json records the rejected shell command.
