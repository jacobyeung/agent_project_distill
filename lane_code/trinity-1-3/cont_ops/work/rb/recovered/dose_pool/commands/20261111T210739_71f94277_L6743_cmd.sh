<!-- recovered by seal_plan: transcript=71f94277 line=6743 utc=2026-11-11T21:07:39.145Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > leg_s1_tree/inbox/${T}_ORCH_dev_S1_withhold.md <<'EOF'
# ORCH: dev-S1 is adopted: withhold its scenes from LEG-S1's training set
/scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/: MANIFEST.json, MANIFEST.md, WITHHOLD_SCENES.json (sha 969cdb56ce50), QIDS.jsonl.gz (18,277 questions on 100 rooms, 224 captures; no overlap with any evaluation set). Lane dose_pool's RESULT 20261111T2105Z_RESULT_dev_S1_manifest.md counts the rows on those rooms in each source (about 4% of each: head-backed pool, route rows, room rows, routing M and L, vqa, pointing, mdg, the pose databases). The builder must drop every row on a withheld room from every source, record the list's sha in the receipt, print the count dropped per source, and fail if a withheld room is present after the build (a hashed scene-exclusion check, as the launch gate requires). The dev reads of the leg (parent and checkpoints) use QIDS.jsonl.gz; put that in the pre-launch card.
EOF
cat > evalx/inbox/${T}_ORCH_dev_S1_tower_exports.md <<'EOF'
# ORCH: a new small GPU item for the queue: geometry-tower exports on the dev-S1 scenes (prepare on CPU now; the HOLD stands)
A held-out development set on training-side scenes now exists: /scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/MANIFEST.json (its `geometry_tower_job` lists 224 captures, 154 with frames in the k6tk store). Rules that may not be chosen on benchmark scenes (the fusion rule and route choices for VSTI, room size, route planning) will be frozen on it, and that needs the tower's exports for those captures: G3T at 64 frames with its frozen scale rule, and the V-C depth head, in the format of /scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64 (lane ttower's STATUS.md and work/ hold the exporter; about 4.6 s per scene, well under one GPU-hour in all).
Prepare: find the exporter and its inputs, say what must be staged on the run node (frames for the 154 captures, checkpoints) and how, write the launch line with a stall guard, and dry-run what can run on CPU. Place it after THINK-0 in your order; it needs one card for under an hour. One RESULT.
EOF
python3 - <<'EOF'
p='/scratch/jjyeung/orch_cd/READY_QUEUE.md'
s=open(p).read()
s+='''
## REVISION 21:08Z
- dev-S1 adopted (dose_pool/out/DEV_S1: 100 rooms, 224 captures, 18,277 questions, withheld from LEG-S1; no overlap with any evaluation set). New GPU item after THINK-0: tower exports (G3T 64-frame + V-C) on its 154 captures with frames, under 1 GPU-h (evalx prepares; ttower's exporter). It makes legal freezes possible for VSTI, room size and route planning.
- Cards: main said (20:39Z) that trinity-1-18 GPUs 1-4 come to us under vnice after its Gemma cell ends (soon after 21:10Z), until it asks for them back; it writes the indices in its notices log first. Plan: f17_s32 -> f17_s64 (1 card); THINK-0 budget CP1 -> T0 (2 cards); ReVSI t32 at 32 duplicate + canary (1 card).
- Orchard: 168042 estimate 2026-11-15T04:54Z; kit authorization expires 2026-11-14T20:50Z; swap design reviewed DO NOT INSTALL (swap_review/REVIEW_VERDICT.md); orchard_cp2 revising; LEG-S1 must be world 8, one node, 24 h to take the slot.
- Final closed-model bars: Argon 76.68 / 86.60 / 83.33, Carbon 75.97 / 89.76 / 82.29 on VSI-500 / ReVSI-999 / VSTI-450.
- Training pool: dose_pool/out/POOL_S1, 102,216 rows in 11 sets (head-backed v3.14 rows of nine types + 10,458 direct route rows); frames resolve in k6tk on Orchard.
'''
open(p,'w').write(s)
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) dose_pool RESULT 2105Z dev-S1: 100 rooms (35 ScanNet train rooms / 84 rescans, 30 ScanNet++ scenes, 35 ARKit training venues / 110 videos), 224 captures, 18,277 questions (route planning 536; camera displacement 804, movement 714, rotation 563; room 73; abs 1,136; counting 301; rel 2,498; directions 1,838/1,811/1,228; size 710; appearance order 0), zero overlap with every evaluation set; withholding costs about 4% of each training source (WITHHOLD_SCENES.json sha 969cdb56ce50). ADOPTED: leg_s1_tree told to withhold; evalx told to prepare tower exports on its 154 captures with frames (<1 GPU-h); READY_QUEUE.md revised." >> ORCH_HANDOFF.md