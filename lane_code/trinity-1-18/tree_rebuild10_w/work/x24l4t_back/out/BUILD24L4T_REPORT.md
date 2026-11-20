New seal: c558ad33286680e17c45ec54c825a9f236e80fd789f4ce6b0189273cd63fc16c; 946 files; untouched 24l4s snapshot retains dd522bb92a7005e63130d40e9947258fda0c0196f533fb9d9677a1a0a7981781.
Production changes only check_protected_rooms in student_pilot/r1_rooms.py; its signature, call contract and native admission wiring are unchanged.
Pointing refuses R1_PROTECTED_ROOM_UNRESOLVED:pointing when canonical_scene fails Rooms.room and Withheld finds no hit, even when an ordinary room resolves clean or protected; listed keys obey the same rule.
Protection through either resolvable pointing field and native withheld aliases remains active; the withheld-hit fallback retains opaque alias protection.
Pose/routing retain Rooms.canonical/Rooms.room; VQA retains native Binding.room with direction_twins and strict Rooms otherwise; pointing adds canonical_scene. These match the existing census authorities documented in PROTECTED_ROOMS_API_24L4T.md.
All 105 focused tests pass: 97 retained and 8 new. One 24l4s test expectation now requires UNRESOLVED for both admitted and listed rows, as this ruling requires; every other retained test is byte-identical.
Failing-before evidence: all four reviewer scenes are admitted by untouched 24l4s and refuse UNRESOLVED on 24l4t; six new tests fail on 24l4s, with two unchanged-behavior tests passing.
Seeded fuzz compares 2,500 rows on each of four streams against actual 24l4r/24l4s code: zero 24l4t admissions of baseline refusals. VQA fuzz disables twins; retained tests cover native tiered Binding.
Both 110-test scoped runs match: 50 pass and 60 error on missing archived fixtures, including 35 missing work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L4T.json records all causes.
HOST24L4T.patch, HOST24L4TR.patch and HOST24L4TB.patch replay to this seal from 24l4s, 24l4r and 96ff9a03 respectively; UNCHANGED24L4T.json records every file hash against 96ff9a03 and both comparison trees.
Delivery: tree_rebuild_b24l4t_c558ad33.tar; it contains sealed work/tree_r1, versioned 24l4r/24l4s/24l4t reports, test evidence and validation scripts. The API document specifies the unchanged kit call and inputs.
Validation uses synthetic pinned fixtures; no production-store census or launch was performed. Only the requested baseline comparisons describe build differences because they establish scope and failing-before behavior.
Work used trinity-2-28, nice 10, one-thread CPU libraries and a memory cap below 20 GB; no deletion, Git, SSH, network, GPU or other agent was used.
