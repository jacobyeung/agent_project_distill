New seal: dd522bb92a7005e63130d40e9947258fda0c0196f533fb9d9677a1a0a7981781; 945 files; preserved 24l4r seal 92fe11f83f9e79234f00ed56521e8ad0b1dd48c80ffc593e9c0f6814610186b9.
Only student_pilot/r1_rooms.py:check_protected_rooms and new tests/test_host24l4s.py differ from 24l4r; the API, call contract and native admission wiring are unchanged.
Pointing rejects protection found through either provenance.canonical_scene or Rooms.canonical/Rooms.room, or Withheld.touches; listed source rows use the same predicate.
VQA uses r1_direction_twins.Binding.room with authenticated tiered aliases when direction_twins is enabled, exactly as the native VQA census does; both use strict Rooms without that binding.
Pose and routing use Rooms.canonical/Rooms.room, the tree census authority behind Rooms.status; pointing uses that authority plus canonical_scene. All streams check the native withheld-80 authority.
The tree census enumerates routing slices and VQA; the kit supplies complete pose/pointing stores. Unknown native rooms still refuse; authority authentication remains intact.
All 97 focused tests pass: 12 new and all 85 retained 24l4r/24l3/24n/24l/24j and removal tests. Nine new tests fail against untouched 24l4r; three confirm unchanged behavior.
Both scoped suites run 110 tests: 50 pass and the same 60 error on missing archived fixtures; 35 need work/base/tree_b01ce449/student_pilot/carrier_c1_run.py. TESTS24L4S.json records causes and matching outcomes.
Native Binding construction, strict/tiered resolution, census agreement, conflicting pointing fields and withheld aliases run on pinned synthetic fixtures; no production-store census or launch was performed.
HOST24L4S.patch and HOST24L4SB.patch replay to the seal from 92fe11f8 and 96ff9a03 respectively; UNCHANGED24L4S.json records every file hash against 96ff9a03 and 24l4r.
PROTECTED_ROOMS_API.md and PROTECTED_ROOMS_API_24L4S.md specify stream authorities and the unchanged kit contract; the historical API is retained as PROTECTED_ROOMS_API_24L4R.md.
Delivery: tree_rebuild_b24l4s_dd522bb9.tar; it contains the sealed work/tree_r1, retained reports, 24l4r/24l4s evidence and validation scripts. The kit must bind post-condition results to its launched config and store pins.
Work used trinity-2-28, nice 10, single-threaded CPU libraries and a memory cap below 20 GB. No deletion, Git, SSH, network, GPU or other agent was used. Required base comparisons document validation; no revision-history prose was added.
