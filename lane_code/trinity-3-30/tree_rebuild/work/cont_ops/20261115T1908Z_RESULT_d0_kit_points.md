# RESULT d0_kit_points (cont_ops). Detail and procedure: events/cont_ops/D0_LAUNCH_PROCEDURE.md; tools: d0_tools/
1. Builder: launch_s1/build.py does not rebuild a four-stream kit. It always injects mdg, and when fed the production values it refuses at recipe_for (CPU run, repro4.log). 07ca49df itself was made by editing a five-stream config (its review.json says so). New tool derive_kit.py derives a kit from 07ca49df's records with no code edit:
   - with no overrides it reproduces b02e4385/launch/0/1/7.json byte for byte;
   - a D0 stand-in derivation passes the kit's own b/g.py check (p) and a.py --build-only;
   - the old review is refused.
   Any new identity needs a new review.json, staging.json and ANON_OK scan.
2. Warm start: m544 export (1d6eeb28) as init_artifact through config fields only; validate_init, validate(cfg) and all artifact gates PASS on CPU (stops only at the unstaged weight read). Caveat: final mode always resets the routing-opener embedding rows after the LM load (carrier_c1_run.py:781-783). Config cannot stop it; keeping them needs a one-hunk source patch (from 3d2e5fa8) plus a review. Default: accept the reset, as LEG-S1 did from m200.
   The m544 export must be repacked: its members are `m544/...`, and the files must sit at `ap/8865619b/runs/469ddece/m544/...`, with the artifact.json copy outside ap/8865619b. About 10-20 min on the Orchard login node.
3. k6: complete. 12 archives, 78.3 GB, 290,880 members = the 290,880 frames of MAP.jsonl.gz. All 151 staging sources in k/0.json are present at pinned sizes (stat only). New rows must cite only frames in k/frame_map.jsonl.gz.
4. Pool without ROUTE_direct: accepted with no code change, as a DEFERRED source; SCENE_room_sppK is the precedent. The new pool_selection.json gives a new pin, identity and review. Routing becomes 47,732 program rows; per step (64): camera displacement 18.8, movement 16.4, rotation 12.3, absolute distance 15.7, room 0.8, route planning 0 (was 10.5). Unverified: whether VQA admission takes route_planning rows. The CPU mode-p job settles it.
GO needed later: the CPU job on general (procedure step 8) once rows exist. Its packet is in the procedure.
Incident: at 18:37Z one Orchard→Trinity tar of kit metadata was 42 MB, over the 20 MB unregistered limit. It finished; it is not repeated; all later pulls were <20 MB.
