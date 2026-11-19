# Lane sb_roomdesign (Devin Fable xhigh, trinity-3-30): design the room head
First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it (no recursive search on /home or /data*, no Git, no deletion, no GPU, no ssh except as it allows). B = that orch_n30 folder. Lane folder: /scratch/jjyeung/orch_n30/sb_roomdesign on trinity-3-30 (below its disk floor: under 20 MB from you, nothing above 5 MB per file). Events: B/events/sb_roomdesign (results, questions, blockers only, 20 lines max). Coordinator: lane swarm_build (events B/events/swarm_build); it builds the kit you specify.

## Goal of the project
A ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print; ReVSI first. Room size is the weakest ReVSI category: step 544 scores 6.6 on dev and most reads end without an answer. Record E3_BACKEND_GEOMETRY_PRICING_20261116.md shows no scale or floor rule on the present towers (frozen G3T pose/points, own depth head, SAM 3 segmenter) makes room routable.

## Question
Which head inside the checkpoint could serve a room-size call, and how do we price it before any training? Candidates to weigh (add others if the evidence points there):
1. A depth model with metric scale (e.g. Depth Anything 3 metric) as a frozen tower, plus fixed-math floor area (floor plane fit, floor-point footprint, alpha shape / grid occupancy over frames registered by the pose tower).
2. A learned floor-extent head on the model's own vision features.
3. A room-area regression head (direct scalar from pooled features).
For each: what it needs (weights, licence, memory and latency in the 9B checkpoint, inputs per frame, pose dependence), how it is called and what it prints in the chain of thought, the training-free pricing test on K1 training captures and R0-dev rooms (metric: the ReVSI/VSI-Bench room-size MRA, plus relative error), the bar it must clear (direct room answer of the model at step 200 or step 400 of leg R1, read by lane cont_ops18; ask that lane for the numbers in one QUESTION in B/events/cont_ops if they are not in a record), and the rows that would teach the call (sources, counts, room exclusions: never R0-dev, the 80 withheld rooms, benchmark scenes; K1 held-out only for fitting rules).

## Read (open the lines you need; never read the design folder end to end)
/data2/jjyeung/agent_project_data/distill_design/INDEX.md, then E3_BACKEND_GEOMETRY_PRICING_20261116.md, NEXT_LEG_DECISION_20261117.md, R0_RESERVE_SCENES_20261116.md, REFREEZE_PREREGISTRATION_20261115.md (room rule), ROWS_V7_R1_20261117.md (431 traced room rows), E2E_READER_B04_20261116.md, B6_GROUNDING_DESIGN_20261115.md, and any INDEX line on room, floor, area, scale, depth or DA3. Web search is allowed for published methods and released weights (licence, metric-scale accuracy on ScanNet/ARKitScenes).

## Deliver
- /data2/jjyeung/agent_project_data/distill_design/ROOM_HEAD_DESIGN_20261119.md (question, answer, evidence, options rejected and why, what might not work and how we notice, tests that would settle it, status) and one INDEX.md line.
- A kit specification for the top candidate the coordinator can hand to a builder verbatim: B/events/sb_roomdesign/KIT_SPEC_room_pricing.md (inputs by path, the exact fixed math, the CPU dry run on two captures, the GPU pricing run with its expected GPU-hours, outputs, pass/fail bar written before any number exists).
- One RESULT event naming both files. Then stop. Time box 3 hours.
