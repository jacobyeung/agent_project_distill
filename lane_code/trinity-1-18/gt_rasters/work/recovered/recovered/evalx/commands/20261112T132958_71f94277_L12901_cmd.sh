<!-- recovered by seal_plan: transcript=71f94277 line=12901 utc=2026-11-12T13:29:58.338Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > evalx/inbox/${T}_ORCH_f17_devs1_read_on_1-18.md <<EOF
# ORCH ($T): run f17's dev-S1 read on trinity-1-18 (Orchard cannot take it)

**Why.** The m100 rule of the next leg compares the leg with f17 on dev-S1, per task, with paired intervals. f17's dev-S1 read does not exist yet. It was orchard_port's job 1, but Orchard's project space is full and its /home is at quota, so nothing can be staged there until the user removes files. You have read f17 on 1-18 before (f17_s32 on dev 741), and the dev-S1 cells with true frame timing and the reviewed scorer exist for CP1 (devs1_direct/out/r3, r4, r5; item list evalx/out/DEV_S1_ITEMS_v1.jsonl, 2,136 items).

**Do.**
1. On CPU now: bind the dev-S1 cells to f17 in its trained format (32 frames, spread layout, 16 groups; its trained thinking setting; true frame timing as in r3). Reuse the checkpoint-parametric cells of legs1_reads if they fit; get the per-cell layout table before any read (lesson: eval frame layout must match training). Dry-run the first 20 items' prompts on CPU and read them.
2. On a card: after the current mask-recall variant finishes on GPU 2, or at once on another 1-18 card that has stayed idle five minutes (main's ruling 118; under vnice; keep at least 110 GiB free on /scratch), run the main cells (primary stratum first), then the facing-away pairs. 1-minute checks until the first answers land, then every 5 minutes.
3. Score with the r5 adapter and report with report.py; quote the primary stratum only. Deliver the per-item journal in the format the m100 decision report reads (legs1_reads/out/RUNCARD_M100_M200.md), so the paired comparison with a later leg checkpoint needs no conversion.
RESULT: f17 per type beside CP1 m200 (71.64 primary, B2048) with paired differences and intervals over rooms; the layout table; anything in the cells that differs between f17 and CP1 other than the checkpoint and its trained format.
If f17's weights or its serving view are not on 1-18, say so in a QUESTION with sizes and where the nearest copy is; do not start a pull above 10 GB without my answer.
EOF
cat > orchard_port/inbox/${T}_ORCH_job1_moves_to_1-18.md <<EOF
# ORCH ($T): job 1 (f17's dev-S1 read) moves to evalx on trinity-1-18

Orchard's project space is full and /home is at quota, so your staging cannot finish until the user removes files. The f17 read is needed before the leg's m100 is judged, so evalx runs it on 1-18 now. Keep job 2 (the checkpoint reads on Orchard, legs1_reads cells) as your goal: finish everything that needs no write to Orchard (cells, run card, CPU dry-runs, the list of what still has to be pushed with sizes), keep your parts in /tmp/jjyeung/op_parts, and wait for a poll that shows at least 150 GB free in the project space. If evalx asks for your f17 cell bindings, share them through its inbox.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: f17's dev-S1 read (needed for the m100 rule) moved from orchard_port job 1 to evalx on 1-18 (order evalx/inbox/${T}_ORCH_f17_devs1_read_on_1-18.md: bind cells to f17's trained format 32 spread, CPU dry-run, run after the mask variant or on a card idle 5 min under vnice, score with r5, journal in the m100 report's format); orchard_port keeps job 2 (checkpoint reads on Orchard) and waits for space." >> ORCH_HANDOFF.md