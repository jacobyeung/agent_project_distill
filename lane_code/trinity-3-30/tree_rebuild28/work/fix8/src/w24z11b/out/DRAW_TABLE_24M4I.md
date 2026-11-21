P and N each draw **340 direct room rows in the first 200 steps: 1.70 rows/step**. These are global counts across four ranks.

The table reports **plan allocation cells**. N’s `routing_base` contains native routing types; its underlying family split requires production preparation. Zero in a separate N routing cell does not mean that type is absent from `routing_base`.

| Stream / family | P rows/step | N rows/step | N − P | Named ruling or list |
|---|---:|---:|---:|---|
| vqa / direction | 34.990 | 35.165 | +0.175 | K1 union `1c7c930d` / `43853165`; four-repeat counting cap, direction refill; ORCH 0511Z. See calculation below. |
| vqa / facing_pairs | 18.170 | 18.170 | +0.000 | Same configured draw rate; no difference. |
| vqa / relative_distance | 22.740 | 22.740 | +0.000 | Same configured draw rate; no difference. |
| vqa / object_size | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / counting | 10.460 | 10.285 | -0.175 | K1 union `1c7c930d` / `43853165`; four-repeat counting cap, direction refill; ORCH 0511Z. See calculation below. |
| vqa / totals | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / appearance_order | 14.420 | 14.420 | +0.000 | Same configured draw rate; no difference. |
| vqa / first_seen_frame | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / box_3d | 1.820 | 1.820 | +0.000 | Same configured draw rate; no difference. |
| vqa / route_planning | 9.700 | 9.700 | +0.000 | Same configured draw rate; no difference. |
| vqa / camera_object_rel_distance_v1 | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / camera_object_rel_distance_v2 | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / camera_object_rel_distance_v3 | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / object_object_left_right | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / object_object_near_far | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / object_object_up_down | 2.000 | 2.000 | +0.000 | Same configured draw rate; no difference. |
| vqa / room_size | 1.700 | 1.700 | +0.000 | ORCH 0511Z restores P 1.70; ORCH 0418Z item 4 retains SCENE_room 294 + T0_room 65 + T1H1_room 66 = 425 VQA rows. |
| vqa / camera_object_abs_distance | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / camera_displacement | 18.250 | 0.000 | -18.250 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| routing / camera_movement_direction | 15.880 | 0.000 | -15.880 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| routing / camera_rotation | 12.530 | 0.000 | -12.530 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| routing / absolute_distance | 16.340 | 0.000 | -16.340 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| routing / recovery | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / units | 1.000 | 0.000 | -1.000 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| pose / pose | 64.000 | 64.000 | +0.000 | Same configured draw rate; no difference. |
| pointing / pointing | 32.000 | 32.000 | +0.000 | Same configured draw rate; no difference. |
| routing / coverage | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / camera_wording | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / coverage_distance | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / coverage_units | 0.000 | 0.000 | +0.000 | Same configured draw rate; no difference. |
| routing / routing_base | 0.000 | 64.000 | +64.000 | **UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only. |
| **Total** | **288.000** | **288.000** | **0.000** | Same stream quotas |

N’s counting request is 4 × 2,571 / 1,000 = 10.284, compared with P’s 10.460. The 0.176 released rows/step go to direction: 34.990 + 0.176 = 35.166. Over 200 steps the native sampler draws 2,057 counting rows and 7,033 direction rows, giving 10.285 and 35.165.

**steps:** Optimizer steps 1–200, sampler start_step=0, seed=17, world=4; 57,600 global rows per vehicle.
**P:** Authenticated config b08fe50c and preparation a5bbef1b/type_mix_population 736344f3; unmodified P type_mix.bound and carrier_c1_data.mixed_indices/type_mix.plans from the packaged P tree.
**N:** Final card; unmodified C r1_mix.allocate and r1_mix.plans over card-configured ceiling counts and synthetic disjoint indices. Only validate_binding is replaced with that dry input tuple. No production population or admission receipt is asserted.
**N_counts:** Card ceiling_rows_per_step times 1000 / 4. routing_base uses P native count 47898 as an explicit proxy; its 64-row rate is unchanged for every count >=16000. N production counts require native preparation.
**routing:** Rows are plan allocation families. N routing_base=64 contains native routing types whose post-preparation membership and 200-step split are unknown; separate N routing type cells are zero, not proven zero underlying draws. P units is an admitted 683-row population at 1.00/step; N auxiliary units remains deferred.
**room:** room_size is the VQA family name for 425 room_size_estimation rows; SCENE_room/T0_room/T1H1_room partition those same 425 rows and are not an additional population.
**limit:** A dry configured-plan count is not a production loader audit. Missing native production rows can change capped allocation or refuse the job; the unchanged row_check still enforces room trace grammar.
**six_row_gap:** N relative_distance ceiling implies 19,827 rows versus list census 19,833: UNATTRIBUTED population gap. It does not affect the configured 22.74 rows/step because either capacity exceeds the request.
**tool:** No tools/dry_count.py exists in the supplied trees/kits. The scripts execute each plan’s own sampler once through 200 steps.

The JSON contains integer totals, attribution, input identities and paths to all 200 per-step counts. The native code paths are `work/build24m4h/p_tree/student_pilot/type_mix.py:229` (P) and `work/tree_r1/student_pilot/r1_mix.py:68` (N).
