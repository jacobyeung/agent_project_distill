<!-- recovered by seal_plan: transcript=71f94277 line=3723 utc=2026-11-11T15:15:13.985Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; cat > READY_QUEUE.md <<'EOF'
# READY QUEUE (orchestrator's ranking, 2026-11-11T15:20Z). Detail per row: READY_QUEUE_DRAFT.md (inventory). Update in place.
Rule: spatial understanding first (USER 11-11); highest signal per GPU-hour; a freed card is filled within minutes. All Trinity GPU starts wait for main's release (about 20:00Z). Orchard: nothing submitted without the orchestrator's written go.

## Trinity, in launch order at release
| # | experiment | owner | cards, GPU-h | decides | gap to close before release (owner) |
|---|---|---|---|---|---|
| 0 | r15 acceptance of the integrated decoder | evalx | 1, short | lets routed reads run | move the 17:00Z deadline (evalx) |
| 1 | READ-0a: T0 m800 on official VSI-Bench 5,130 at 64 frames | evalx | shard over >=4 cards, 11-15 | the baseline every later stage is read against (only official read today: f17 63.79 at 32 f) | shard plan, measured items/h, kit present on the run node (evalx dry run, note 1508Z) |
| 2 | READ-0b: ReVSI 999 at tiers 32 and 64 | evalx | 2, 4-6 | baseline against 57.5-58.2 | none (reviewed, fixes landed) |
| 3 | GEO-1: geometry-backend bake-off, priced under the v3.14 programs | geo_bakeoff | 1-2, not yet estimated | keep the tower + scale head, swap depth, or swap pose too (tower geometry costs 60 points on abs distance and 49 on size with GT masks) | kit, weights, CPU smoke, run card (geo_bakeoff, running); tolerance curves (gt_ceiling task 5, running) |
| 4 | READ-0b: VSTI 5,736 at 32 frames (64 frames is part of FRAMES-1) | evalx | 2-4, 8-12 | camera-type baseline | KIT GAP: kit accepts only VSTI-450 (eval_gaps, Codex) |
| 5 | THINK-0: thinking on against off, direct path | diag_kits | 1-2, 4-10 | trace format for the direct types | inputs not staged: 64-frame PNG cache (reuse READ-0's), videos, vLLM env (evalx stages) |
| 6 | FRAMES-1: 96 and 128 frames on dev cells | evalx | 4, 20-40 | frame count for every later read | exact command lines, dev cells, G3T at 128, CPU long-context decode check (eval_gaps) |
| 7 | GRD-1: denser SAM 3 re-cache, then PRES32 + V3 features | grd_selector | 1, 3-4 + re-cache | proposal ceiling (63-70% today) is the largest mask lever | NO KIT for the denser re-cache; step C copy to the run node (grd_selector) |
| 8 | ARK-1a: ARKit metric scale with fixed weights | diag_kits | 1, 2-4 | route metric types on ARKit or build ARK-1b | inputs not staged; GEO-1 may supersede it (decide after GEO-1's ARKit arm) |
| 9 | READ-0c: CP1 m200 routed, dev-frozen route table | evalx | 2-4, 10-20 | deployed routed baseline | no official-set routed kit; route table not frozen (eval_gaps); low priority while routing loses to direct on abs, counting, size |
| 10 | RFT-1: reward-filtered program sampling | rft1_kit | 6-8, 38 | whether RL rows enter the leg | needs the merged v3.14 tree, CP1 runtime, admitted 5K pool; stage after LEG-S1's tree exists |
| 11 | VLA-side GPU checks (dyn_probe Stage 0; nav oracle-click ceiling with occlusion; T-10, T-11, provider precheck) | dyn_probe, vla_nav, vla_where | 1 each | VLA wiring on the real student | after the spatial reads; assets not staged |

## Orchard
- Pending: 168042 / 168043 (CP1-Rv, v3.13 traces; Slurm estimate 2026-11-12T17:45Z). DECISION OWED before 168042 starts: let it run, or replace it with LEG-S1 on v3.14 traces if the merged tree and rows are ready by then.
- LEG-S1 (stacked leg: v3.14 traces, selector defaults, fusion connector as infrastructure, head-backed traced pool, label REMOVE lists): needs integ_v314 pass 2 (running), the merged tree (owed), the tiny-model rehearsal (leg_s1_rehearsal, running), T0/T1 head-backed rows read by the orchestrator (dose_pool), a pre-launch card shown to the user.
- GF-1 Stage 1 and 2 run inside LEG-S1; missing: dense 64-frame benchmark builders for evaluation, real-checkpoint parity, memory calibration.
- DOSE first batch on real frames: after v3.14 rows exist in the tree's reader.
- LIBERO arms B0 / B1 / U1: after the spatial student (USER: base arms authorised once per benchmark; spatial first).

## Launch-ready with nothing missing: 0 of 21. Ready except the hold: r15, READ-0a (one card), ReVSI t32, ReVSI t64, vnice reruns.
EOF
mkdir -p eval_gaps/events eval_gaps/work eval_gaps/out
cat > eval_gaps/BRIEF.md <<'EOF'
# eval_gaps (Codex): close three gaps in the evaluation kits before the GPUs free, on CPU, with tests
Host trinity-2-18. Your folder: /scratch/jjyeung/orch_cd/eval_gaps (write only here). The evaluation operator's folder /scratch/jjyeung/orch_cd/evalx is read-only for you: copy the kit files you change into work/ and deliver sealed copies plus patches; the operator adopts them.

## Why
The user (2026-11-11): "we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" Cards free at about 20:00Z today. An inventory (/scratch/jjyeung/orch_cd/READY_QUEUE_DRAFT.md; ranked in READY_QUEUE.md) found that three planned reads of our student checkpoint T0 m800 cannot start because their kits are incomplete.

## Read first
- /scratch/jjyeung/orch_cd/evalx/STATUS.md (the newest CURRENT STATE block: how reads are launched with work/trin_vl/go_f1.sh, the kits work/aws_vl64o, work/aws_vl64r, work/aws_vl128, the DRY seal checks, cells JSON files, the stall guard) and its newest RESULT events. List evalx/work one level at a time.
- /scratch/jjyeung/orch_cd/aws_vl128_build (how the 96/128-frame kit was built) and /scratch/jjyeung/orch_cd/revsi999_review/REVIEW_VERDICT.md (the defects a reviewer found in a sibling kit; avoid the same ones).
- /data2/jjyeung/agent_project_data/DATA_MAP.md (one named file; you may open it) for where benchmark item lists live. Prefer copies already on /scratch. If an item list exists only on /data*, read that single file with `rsync --bwlimit=8000 --partial` into work/inputs (under 200 MB in total).

## Do
1. VSTI-Bench full corrected set (5,736 items) at 32 frames. Today the kit's item loader (evalpath/items.py) accepts only the 450-item v3 subset. Extend it to the full corrected set with the same prompt, frame rule (standard 32 frames, no patch) and scorer; pin the item list by sha256 and count; add a cells file for T0 m800; tests: count is exactly 5,736, the 450 subset is contained and scores identically item by item through both loaders, per-type counts match the list. Write the exact go_f1.sh line and a shard plan for 2 to 4 cards.
2. FRAMES-1 (96 and 128 frames). Write the exact launch lines for the dev cells (the dev sets are named in evalx/STATUS.md and the plan /scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md, section on the frames experiment); build the cells files; run the long-context decode check on CPU with the tiny model the kit tests use (96 and 128 frames through encode, generate and answer parse, with the token counts 30,912 and 35,072 asserted against the kit's own count); state the memory estimate per card and what fails first.
3. Routed read of checkpoint CP1 m200 on the official sets with a route table frozen on dev: say exactly what exists (scripts go_rv.sh and the tp scripts for routed dev reads), what is missing for the official sets, and build the missing kit pieces with a CPU replay test on recorded generations. The route table file must be an input pinned by sha256, never chosen on the test set; if no frozen table exists, write the command that freezes it from the dev results and leave the table path as the one required argument.
For each of the three: a DRY seal the same way the existing kits are sealed, a stall guard on the launch line, and a first-item CPU dry run (inputs resolve, frames decode for the first and last item, the prompt builds).

## Limits
- CPU only; no GPU, no ssh, no git commands, no network, no deletion commands of any kind (a hook blocks them). Run tests under `ulimit -f 204800`; keep this folder under 2 GB; temporary files under work/tmp, not /tmp. Never load real 9B weights.
- /home and /data* are overloaded network storage: open named files only; no recursive search or listing there; write nothing there.
- You cannot ask questions: choose the option closest to the existing kits' conventions and write the choice down.

## Deliver
out/EVAL_GAPS.md (per read: what was missing, what you built, the exact launch line, tests and counts, what the operator must still do on the run node), the sealed kit copies under out/kits/, patches under out/, events/<UTC stamp from date -u +%Y%m%dT%H%MZ>_RESULT_eval_gaps.md and a final message, each at most 15 lines.
EOF
tmux new -d -s cx_eval_gaps "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/eval_gaps /scratch/jjyeung/orch_cd/eval_gaps/BRIEF.md --model gpt-6-astra --effort high --skip-git-check --label eval_gaps > /scratch/jjyeung/orch_cd/eval_gaps/dispatch.out 2>&1"
T=$(date -u +%Y%m%dT%H%MZ)
cat > evalx/inbox/${T}_ORCH_ready_queue_gaps.md <<'EOF'
# ORCH: ranked queue and your gaps (adds to my 1508Z dry-run note)
Read /scratch/jjyeung/orch_cd/READY_QUEUE.md (my ranking) and the rows for your lane in READY_QUEUE_DRAFT.md. Before the release at about 20:00Z, on CPU and within your ssh limits:
1. READ-0a on one card takes 11-15 hours: write the shard plan over at least 4 cards (which nodes and cards you expect free, items per shard, the merge and the count check to 5,130) and the measured items per hour from any earlier 64-frame run.
2. The kits and cells live on trinity-2-18 while the runs are on trinity-1-18 with NOSYNC=1: make sure each kit the first four queue rows need is on its run node, verified by sha256, before the release.
3. Stage THINK-0's inputs next to READ-0's (it reuses the 64-frame PNG cache; its card is /scratch/jjyeung/orch_cd/diag_kits/out/RUN_CARD.md) and say on which node it will run.
4. Codex lane eval_gaps is building the VSTI 5,736 kit change, the FRAMES-1 launch lines and the routed official-set read; its RESULT lands in /scratch/jjyeung/orch_cd/eval_gaps/events. Adopt its sealed kits when it does; do not build those yourself.
5. VSTI's first read is at 32 frames (my 1330Z ruling stands; 64 frames belongs to FRAMES-1).
One RESULT with the table when done. Start nothing on a GPU.
EOF
cat > grd_selector/inbox/${T}_ORCH_dense_recache_kit.md <<'EOF'
# ORCH: the denser SAM 3 re-cache needs a KIT, not only a run card
Your 1445Z RESULT names the denser re-cache (more prompts or a lower floor) as the largest mask lever, with proposals binding at 63-70%. After your CPU steps, build it so that it starts within minutes of the GPU release (about 20:00Z): the script with its exact prompt and threshold grid, a stub or tiny-input CPU test of the whole path including resume, the staging step to the run node written as commands (the existing re-cache is on trinity-2-18; frames and checkpoints are in /dev/shm on trinity-1-8), a stall guard, GPU-hours, the disk it writes (cap it and check free space first), and the pre-registered reading: which proposal recall would change the routing decision for absolute distance, size and counting. Also correct STATUS.md: it says no GPU step is pending while your RUN_CARD lists one. No GPU process until I write GO.
EOF
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; printf 'eval_gaps|tmux:cx_eval_gaps||\n' >> $S/LANES
echo "$(date -u +%Y-%m-%dT%H:%MZ) READY_QUEUE.md written (ranked; inventory READY_QUEUE_DRAFT.md by Sonnet: 21 GPU experiments, 0 launch-ready with nothing missing, 5 ready except the hold). Gap closers: eval_gaps (Codex Astra, tmux cx_eval_gaps: VSTI 5,736 kit change, FRAMES-1 lines + CPU long-context check, routed official-set read kit), evalx note (shard READ-0a over >=4 cards, kits onto run node, stage THINK-0 inputs), grd_selector note (dense SAM 3 re-cache kit). DECISION OWED: Orchard 168042/168043 (CP1-Rv on v3.13 traces, Slurm estimate 11-12T17:45Z) run as is or replaced by LEG-S1 on v3.14." >> ORCH_HANDOFF.md; sleep 2; tmux ls | grep -c cx_