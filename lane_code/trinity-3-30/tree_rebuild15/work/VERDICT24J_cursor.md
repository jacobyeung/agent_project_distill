GO AFTER FIXES
Independent review of build 24j: tree 189df6ac against base 57a1f14d, read-only on trinity-1-18.
1. Scope and bytes PASS, with one exception. I recomputed the sha256 of all 940 and 939 files. Every UNCHANGED24J.json entry matches, only entry.py, production_proof.py and tests/test_host24j.py differ, and source_seal.inventory plus digest reproduces both seals.
   Mode p is unchanged: test_mode_p_bytes_match_base (7 fixtures) and both test_r2_n1fix frame_host tests pass. test_r2_build_n1, test_r1_build16 and test_r1_build17 hit the same missing-fixture errors in both trees.
   Exception: q now trains the config that stage_host returns. That config takes streams.routing from request['routing_base'] and routing_inputs from request['routing_inputs'] (entry.py:194-196, production_proof.py:94). Base q trained the config's own values, and no check makes the two equal.
2. Assertions PASS, except scene_division in q. begin_host sets empty_root and job_tmp before staging (production_proof.py:91, before :94). disk_plan, runtime_binaries, routing_selection and directory_modes are computed from evidence (entry.py:157-168, 211-215, 223-224).
   scene_division turns true only after check_bound returns, and check_bound raises on any violation (scene_division_gate.py:25-26). Every mutation test refuses by name, and foreign, input and pre-bind identities refuse.
   host.json is written only after bind_handover and the final-config loader audit (production_proof.py:157, 168-178). All 15 new tests pass in my run.
3. Routing-selection pin: neither option holds. ROUTING_SELECTION_PIN.json has status BLOCKED_MISSING_SOURCE, regenerated_sha256 null and recipe_executed false.
   Option (a) cannot work as built. digest(build(...)) hashes a receipt that embeds absolute output paths (s1_routing.py:481, 484), so no digest from P's run can equal the digest of q's root/selection build.
   The recipe emits the digest of a P-config build at the reviewer's --output path (ROUTING_REGENERATE_24J.py:41-44, 62), not the N staged-config build that q compares against.
   The assertion can pass on a different selection. It compares against whatever pin the request supplies (entry.py:212-213), and host.json records neither that pin nor the regenerated digest. N is deferred (routing_slices=deferred_first_boundary), so admit() also skips the routing-count check (entry.py:102-103).
4. Kit wiring (24k): NOT CHECKED. w24/out/BUILD24K_REPORT.md does not exist.
Fixes:
- MUST: in q, run check_host_scene after the direction_twins block. N_PRODUCTION_CONFIG.json enables r1_training.direction_twins, and production_proof.py:95 checks scenes before the augment step (:97-106).
  augment replaces streams.vqa with a store that appends 7,971 twin rows (r1_direction_twins.py:11, 122-131), so N's receipt would certify a VQA store that does not train. Twins inherit their source scene (r1_direction_twins.py:70-72), so leak risk is low, but condition 2 fails. Add a q fixture with direction_twins; the current fixture has none.
- MUST: count no host PASS until an independent reviewer approves regenerated_sha256 for N's exact runtime inputs and q paths, backed by an executed P-row equality run.
- SHOULD: record request['routing_selection'] and digest(regenerated) in host.json, so that admit and review can bind the approved selection.
- SHOULD: in q, refuse when the localized request['routing_base'] differs from cfg['streams']['routing'] (likewise routing_inputs), or record the substitution in host.json.
- SHOULD: after a caller-supplied stage hook (entry.py:180), re-verify the staged entries or record the stager in host.json. A custom hook skips the archive-inventory and hash checks that stage_inputs runs (launch_r2/staging.py:118-121, 130); only pinned reads are still re-hashed (p3_provenance.py:49).
Not checked: real preparation, P-row regeneration and the GPU forward pass. I did not check whether native admit and forward work under host_environment's cwd, umask 077 and redirected HF_HOME/TORCH_HOME/TRITON_CACHE_DIR (production_proof.py:92).
   I did not check whether native prepare's second routing build equals the checked build, beyond confirming its inputs are unchanged, nor kit 24k. N cannot reach PASS as configured today: N_PRODUCTION_CONFIG.json holds 52 absolute paths outside /tmp/q_22c714e1, and begin_host's temporary_paths refuses them (a known kit item).
