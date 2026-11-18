# STATUS lane pooled_rule3 (Devin Opus high, trinity-1-3), started 2026-11-18T03:42Z, finished 03:54Z; lane exits after the RESULT event
Task: close fix 2 (export provenance) of COMPLIANCE_POOLED_V2.md. Done; v3 is ready to register.

## Deliverables (events/pooled_rule/; lane copies in work/)
- pooled_harm_rule_v3.py 3c7661fe28589f8ef12003d4c0ade78f9ae12fbc0fe0514cfa2a508ecb84d880 (statistics byte-identical to v2)
- POOLED_RULE_REGISTRATION_v3.md c4c66d7bbc7d465006ed42c1a2c6e9c2320012e63b072b17e1153c76539a29bf (rule text unchanged, provenance section exact)
- PROVENANCE_SCHEMA.md 79d0f697 (updated in place; the v2 text is in pooled_rule2_evidence.tgz), pooled_rule3_COMPLIANCE.md, test_pooled_rule_v3.py, TEST_OUTPUT_v3.txt (36 of 36 OK)
- pooled_rule3_evidence.tgz 28ec0f6273e9acdc63987a2cc1a7b4dc6b044a2544938c1e55430925ee59d586 (lane copy out/)
- Record distill_design/POOLED_HARM_RULE_R1_20261118.md Status line and INDEX.md line 233 rewritten.
- Unchanged pins: ROOM_CROSSWALK.json 994902af..., BASE_MANIFEST_dev-S1_544.json e08a1d34..., BASE_MANIFEST_R0-dev_544.json 86c8f993...

## Open
- No independent review of v3. Decision reads now need `--export-receipt <dir>/runs/673bc60f/m<step>/artifact.json` (the run's own artifact.json, fetched unchanged) and `--ledger`.
- rm_guard queued two of my commands in agent_project/agent/PENDING_USER_COMMANDS.md: a copy of pooled_rule2/work that also cleared this lane's pycache folder, and a STATUS/RESULT heredoc whose text matched the guard. Neither needs running; the second would write a duplicate RESULT event.
- No IB mirror: all deliverables are on /data2 in events/pooled_rule/.
