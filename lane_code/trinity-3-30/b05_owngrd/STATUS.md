# b05_owngrd STATUS (Claude Opus lane on trinity-3-30; brief qs/05_own_grounding_head.md)
Updated: see `date` stamp at bottom.
## Facts established
- F1 Shared Qwen ViT is FROZEN in D0 (sealed b01ce449) and in the A2 tree (kit a2 t_0fc11a63209cc6e7.tar): carrier_c1.py:133-136 passes full_ft {'learning_rates':{'llm':..}} with no 'train' key, so full_ft.DEFAULT_TRAIN = {llm True, vision_blocks False, merger False}. Only the private depth ViT copy trains. So the head trains on ViT taps that are identical across step 544, D0 exports and A2 (verify by tensor hash when an export is read).
- F2 Pool: kit_k1a CAPTURES.json (local copy trinity-3-30:/scratch/jjyeung/orch_n30/k1_ops6/src118/kc/k1_build/work/kit_k1a/out/CAPTURES.json): 2,343 captures, 2,090 eligible (arkit 1130, scannetpp 605, scannet 355); refusal reasons evaluation_rooms 162, ReSTI 99, dev_s1 95, qualification 52, MindCube 14. K1 pilot = 300 of them.
- F3 K1 SAM 3 pass (mirror trinity-3-30:/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2, 300 capture dirs, 3.0 GB): dense_aliases, joint floor 0.05, cap 100, 1008 px, bf16, 32 anchor frames, phrases = K1 question operands only (not GT names+confusers+absent as the design asks).
- F4 trinity-1-18: k1_frames (5.6 GB, K1 frames, content-addressed), envs/sam3_capretry_native_v1, orch_cd/mdg_next/work/data/sam3src, k1/g3t, k1/m544_parts (21 GB step-544 export tar parts), own_ground_gpu/kit_{A,B} (105 MB).
## Next
see bottom
