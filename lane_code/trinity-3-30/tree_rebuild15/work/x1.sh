J0=/scratch/jjyeung/orch_n30/tree_rebuild14_w24j; J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; uptime; tmux ls 2>/dev/null
test -e $J && { echo J EXISTS; exit 1; }; mkdir -p $J/work $J/out $J/out24j $J/prompts
cp -a $J0/work/tree_r1 $J/work/tree_r1 && cp -a $J0/work/tree_r1 $J/work/tree_r1_base
for f in BUILD24J_REPORT.md KIT_WIRING_24J.md UNCHANGED24J.json ROUTING_SELECTION_PIN.json ROUTING_REGENERATE_24J.py HOST24J.patch TREE24J_SEAL.json; do cp -p $J0/out/$f $J/out24j/ || echo MISSING $f; done; cp -p $J0/prompts/build24j.md $J/prompts/
cat > $J/REVIEW24J_CURSOR.md <<'EOV'
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
EOV
cat > $J/prompts/build24l.md <<'EOPX'
# Codex build 24l of lane tree_rebuild: TREE fix of build 24j after its independent review (Cursor Opus, GO AFTER FIXES): host scene check after direction twins, and three receipt-recording fixes

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. It holds build 24j's changed tree at `J/work/tree_r1` (seal 189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710, 940 files), an untouched copy `J/work/tree_r1_base` (same seal; never edit it), 24j's outputs in `J/out24j/` (BUILD24J_REPORT.md, KIT_WIRING_24J.md, UNCHANGED24J.json, ROUTING_SELECTION_PIN.json, ROUTING_REGENERATE_24J.py, HOST24J.patch, TREE24J_SEAL.json; read the report first), the 24j build prompt `J/prompts/build24j.md` (its ruling conditions stay binding) and the review verdict `J/REVIEW24J_CURSOR.md` (read it whole). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 50 minutes.

## Fix (only these, in launch_r1/production_proof.py and launch_r1/entry.py, plus tests)
1. MUST: in production_proof._run, the host scene assertion (check_host_scene) must certify the config that trains. N's config enables r1_training.direction_twins, and the augment block (production_proof.py:97-106) replaces streams.vqa with the twin-augmented store after check_host_scene ran on the pre-twin config. Run check_host_scene on the cfg after the augment block (keep the pre-twin check too if removing it loses a refusal). Add a q-path fixture with direction_twins enabled, and tests: the receipt's scene_division refers to the augmented VQA store; a twin store that crosses the scene division refuses by name.
2. SHOULD: host.json records the request's routing_selection pin and digest(regenerated) beside the assertion, so admit's caller and the reviewer can bind the approved selection. Do not change how the digest is computed or compared.
3. SHOULD: stage_host replaces streams.routing with the localized request['routing_base'] (and routing_inputs when not minimal). Record in host.json the sha256 of cfg's own streams.routing (and routing_inputs) and of the substituted values, and a boolean `routing_substituted`. Do not refuse on a difference (N's kit supplies routing_base from its k/r.json by design); the reviewer reads it.
4. SHOULD: after a caller-supplied stage hook (entry.py:180), re-verify the staged entries with the tree's own checks that stage_inputs runs (archive inventory and hashes, launch_r2/staging.py:118-130) and refuse by name on a difference; record `stager: native|hook` in host.json. Test: a hook that stages a wrong byte refuses.
5. Report (do not fix) whether digest(build(cfg, root/'selection', ...)) depends on anything besides the job root path and the staged inputs (e.g. time, pid, host name, absolute paths outside root): run build twice on a fixture at the same root path in two fresh roots of the same path, and once at another path, and say whether the digests are equal. This decides whether a separate CPU job at the same root path can produce the pin.

## Conditions
Everything else byte-identical: admit(), identity(), row legality, exclusions, routing policy, sampling, scoring, the seven assertions' definitions, mode p (frame_host) behaviour and its tests. List every tree file's sha256 before and after; only production_proof.py, entry.py and test files may differ. All 24j tests (tests/test_host24j.py) still pass; run the launch_r1, r1_population, r1_handover, r1_loader and entry tests and report pre-existing failures with their cause.

## Outputs
`J/out/HOST24L.patch` (diff against tree_r1_base), `J/out/TREE24L_SEAL.json` (seal by `student_pilot.source_seal.inventory` + `p3_provenance.digest`, file count), `J/out/UNCHANGED24L.json`, `J/out/ROUTING_DIGEST_STABILITY.json` (item 5), `J/out/KIT_WIRING_24L.md` (kit edits needed beyond 24k's wiring; expected: none except the new t_ tar and seals), `J/out/BUILD24L_REPORT.md` under 30 lines, and `J/out/tree_rebuild_b24l_<seal8>.tar` of work/tree_r1 plus those outputs.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Change nothing in admission semantics, identity, legality, exclusions, routing policy, sampling, scoring, removals, opener rows, the step-544 lineage or the DEFERRED boundary.
EOPX
sha256sum $J/prompts/build24l.md | cut -c1-16; du -sh $J | cut -f1
cd $J/work/tree_r1 && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,\".\"); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory(\".\"); print(len(f), digest(f))"
tmux new -d -s tr15_b24l "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $J $J/prompts/build24l.md --model gpt-6-astra --effort high --label tree_rebuild24l --skip-git-check > $J/build24l_dispatch.log 2>&1"
sleep 20; tmux ls | grep tr15; tail -5 $J/build24l_dispatch.log
