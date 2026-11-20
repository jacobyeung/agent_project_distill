# Analysis brief grd_funnel1: at which stage the routed reader loses objects (grounding funnel), and what more frames would buy

You are a Codex analyst on trinity-2-28. Work only in W = /scratch/jjyeung/orch_n30/grd_funnel1 (node-local). B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. D = /data2/jjyeung/agent_project_data/distill_design. Read B/tools/LANE_RULES.md first; its rules bind you. Execute everything yourself.

## Why (the decision this feeds)
Project goal: a ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print. The user asked on 2026-11-19: "how can we not get grounding?? that seems to be the easiest". The routed reader places its calls and copies the printed values; the printed values lose the points, and for object questions the first suspect is the ground call. This analysis ranks the grounding levers for vehicle N's second boundary and for the next leg:
- L1 more input frames for the ground call (64 or 96 instead of 32);
- L2 a presence decision before any box or mask;
- L3 proposals from the model's own tokens added to the segmenter's text-prompted proposals;
- L4 cross-frame coverage and association of the chosen instance;
- L5 the lifting geometry (depth shape, pose).

## Known already (do not redo; cite)
- Base Qwen3.5-9B on single frames: point on the target in 90 to 93% of frames where it is visible; yes/no presence AUROC 0.962; but a box on 92% of frames where the target is absent. Best fusion picks the right instance for 83% of 260 objects.
- dev-S1 route table of 2026-11-12: "object never proposed" was the largest loss (+28.3 points on absolute distance and +23.2 on counting with ground-truth masks); dense prompts plus aliases recovered 55 of 224 never-proposed instances.
- R1 trace analysis (D/R1_M200_TRACE_ANALYSIS_20261119.md, lines about 135, 195, 295): when the rarer object of a distance item is grounded in fewer than three frames the gap scores 55.4 (93 items) against 73.9 (49) at step 544, and 60.3 (61) against 77.9 (24) at step 200. That is an association, not a stage attribution.
- E3 (D/E3_BACKEND_GEOMETRY_PRICING_20261116.md): with ground-truth masks, absolute distance scores 62.9 on tower geometry and 77.9 on ground-truth geometry.

## Question
For every object that a routed read on dev-S1 had to locate (absolute distance first; add any other routed type whose outputs exist), at which stage was it lost, and how many task points does each stage cost?
- S0: the object is visible in none of the read's input frames (ground-truth visibility on the sampled frames).
- S1: visible in at least one input frame, but no candidate was proposed for it.
- S2: a candidate on it existed, but the selector chose another instance, or the null slot.
- S3: the right instance was chosen but in fewer than three frames.
- S4: right instance, three or more frames, but the lifted 3D position is more than 0.25 m outside the annotated box.
- S5: none of the above.
An object takes the first stage that applies. Report counts per stage, the item score by the worse of its two objects' stages, and room-bootstrap 95% intervals (10,000 draws). For each stage give the points recoverable if its items scored like S5 items, and label that number an association unless you rescore counterfactually with ground-truth values for that stage alone.

## Phase 1 (tonight, CPU only, existing outputs)
1. Read D/INDEX.md and from it only the records you need: the reader's serving table (READER_R1_20261117.md), the R1 trace analysis and its distance diagnosis, the dev-S1 baseline and route-table records, the K1 records. Find where the routed reads' per-call outputs live (B/events/cont_ops/ and its files_* folders; the trace corpus /data2/jjyeung/agent_project_data/distill_trace_corpus/ holds every read as archives) and where per-frame ground truth for dev-S1 or K1 captures lives (instance masks or boxes with poses). Search named places only.
2. Build the funnel for step 544 and for the newest step that has a routed distance read. If a stage cannot be decided from existing files (for example no per-frame ground-truth visibility on this node), say which file is missing, where a copy exists, its size, and decide the stages you can.
3. State for each lever L1 to L5 which stages it can move, and the most points it could recover.

## Phase 2 (kit only; no GPU run)
Build W/kit that reruns only the ground call of the same items with 64 and 96 input frames (the answering path keeps its frames) and recomputes the funnel. Include one command run_funnel.sh that takes a GPU index, unit tests for the stage logic on a synthetic capture, and a CPU dry run of the first capture as far as the proposal step allows. Give the GPU-minutes estimate. The orchestrator assigns a card and gives the GO.

## Record
Write D/GROUNDING_FUNNEL_20261120.md (question, method, the funnel tables, options considered and rejected with reasons, what might not work and how we would notice, the tests that would settle it, status) and add one line to D/INDEX.md. Small files; write each once.

## Limits (cluster rules; a violation costs the user their cluster access)
- No GPU, no Slurm or Orchard job, no ssh, no git, no deletion commands of any kind (name files to remove in the report instead).
- Never run find, du, ls -R or grep -r on /home or /data*. Read a named file once; never loop over many small files on NFS.
- Any read above 20 MB from /data* or /home, and any download, registers with the IO governor before it moves a byte: read /data3/jjyeung/orch_n13_20261026/io_governor/README.md and follow it (one stream at a time for the whole account, 8 MB/s; this node has a live agent in tmux `iogov_agent`). Another build on this node (q3d_price1) may hold the stream; wait your turn, never run beside it. If you cannot register, post a BLOCKER. Never run sha256sum or cmp on a file under /data* or /home.
- Disk: stay under 20 GB in W; check `df -h /scratch` before and after.
- dev-S1 and K1 are held-out development scenes: ground truth serves this analysis only; no output becomes a training row.

## Deliverables
One event file, named with the real UTC time from `date -u +%Y%m%dT%H%MZ`:
- B/events/grd_funnel/<UTC>_RESULT_grd_funnel1_<short_finding>.md (at most 20 lines): the funnel table for each step, the lever ranking with points, inputs missing, the Phase 2 kit path with its tar sha256 and GPU estimate, the record path.
- or B/events/grd_funnel/<UTC>_BLOCKER_grd_funnel1_<reason>.md with the evidence.
Out of scope: any GPU run, any training, the Qwen-3D pricing kit (q3d_price1), vehicle N's launch.
