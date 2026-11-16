<!-- recovered by seal_plan: transcript=71f94277 line=28207 utc=2026-11-14T03:46:18.500Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; cat > $C/leg_s1_canary/inbox/${N}_ORCH_RULING_packed_job_not_built_write_the_record.md <<'EOF'
# ORCH ruling on RESULT 0345Z: the packed four-worker job will not be built; write the design record

Your feasibility report is exactly what I needed, and it decides against the packed job: both owners would need a new sealed step mode with step-UUID evidence, namespace and shared-configuration fixes, new seals and confirmations, a controller and a step shim, a joint independent review, and a first run in which only Orchard can prove the step isolation. That is a day of new machinery to gain one to four hours on three evaluation reads and one probe arm. Declined.

What I am doing instead: the IF-P0 baseline arm moves to the `advanced` partition as an ordinary single one-GPU job once the production leg releases our cap there (a partition allowlist in that kit, nothing step-shaped), which frees the one-GPU partition for the three evaluation reads in sequence.

**Your task: the design record**, so the next agent who thinks of packing does not pay for this again. Write `/data2/jjyeung/agent_project_data/distill_design/ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md` (at most 50 lines, current state only) and append one line to `INDEX.md` there with `>>` (touch nothing else under `/data2`): the question; the answer (not built, and why); the facts with file and line (what each accepted job script checks about its allocation; why `SLURM_JOB_GPUS` indices are not CUDA ordinals in a step; that both namespaces expose all of `/tmp`; the shared cloud configuration; signals reach only the batch step); the Orchard limits that shape the choice (`advanced`: four GPUs on one node per user, so one job at a time; `general`: one running GPU and one node per user, queued jobs allowed; forecasts of 13 hours on 2026-11-14); the outer request and step lines you would use; the disk bound; what only a real job can prove; and when packing would be worth building (many short one-GPU jobs over days, designed into the kits from the start). Post one RESULT with the hash. Then stay on the inbox.
EOF
cat > $C/if_p0/inbox/${N}_ORCH_TASK_admit_advanced_partition_single_job.md <<'EOF'
# ORCH task: admit the `advanced` partition for the same single one-GPU job, and prepare a second P0 packet for it

## Why

P0 is queued on `general` as job 169413 (token a35f2d78fe7c5ee8d) with a Slurm forecast of 17:59Z, behind the step-200 evaluation read (16:33Z), and it would then hold the one-GPU partition for four hours ahead of the step-400 and final reads. The production leg releases our cap on the `advanced` partition (four GPUs on one node per user, 24-hour limit) when its job ends, at about 15:00Z. P0 can run there as an ordinary single job with one GPU; nothing packed, no job steps.

## Change (smallest possible)

Admit partition `advanced` beside `general` wherever the kit binds the partition: the `sbatch` argument list, `allocation()`, `card()` if it checks the partition, the child environment and the job context, and `validate_context`. The context records the partition the job actually ran in; the launcher takes the partition as an explicit argument limited to those two names, and the packet is bound to it (a packet built for one partition refuses in the other). Everything else is unchanged: one node, one task, eight CPUs, at least 200 GiB, one H100, twelve hours, no requeue, the same preflight order, the same result return.

Check one thing on paper and tell me: on `advanced` the job may land on a node where our own production job ran or another user's jobs run; your mount proof, card check ("one empty 80-GB H100") and free-space floor must hold there exactly as on `general`. If the card check requires the card to be empty, say what it does when a neighbour job uses the other cards of the node (it must only look at its own assigned card).

## Deliver

1. New seal with the diff against 8d5bdd73 (runtime and tests separately), the test count and the rehearsal result.
2. The exact control files I must rewrite for the new seal (same three as before; I will reuse the review text with one more paragraph for this diff).
3. After my confirmation and new control files: a second packet for `advanced` with a fresh token, and an updated hand-off for evalx with both argument lists. Never reuse token a35f2d78fe7c5ee8d.
4. State how duplicates are prevented: the `general` job 169413 stays queued until the `advanced` job has been accepted and has passed its preflight; then I order 169413 cancelled. If 169413 starts first, the `advanced` packet is not submitted. Your kit cannot enforce this; say so and leave it to my orders.
EOF
cat > $D/INBOX_TO_NONTRAINING_ORCHESTRATOR_${N}_orchard_advanced_after_leg.md <<EOF
# From the distillation orchestrator, $(date -u +"%Y-%m-%d %H:%M UTC"): intended Orchard use after our leg ends (tell me if you need the capacity)

- Our LEG-S1 job 169097 holds the four-GPU \`advanced\` cap until about 15:00Z (wall end 15:25Z).
- After it ends I intend to run ONE single-GPU job there for about five hours (a probe arm, IF-P0 P0), not a new four-GPU leg; a continuation of the leg needs the user's decision and will not start before about 20:00Z.
- On \`general\` we have two one-GPU jobs queued (169367, an evaluation read, forecast 16:33Z; 169413, the same probe arm, forecast 17:59Z, to be cancelled once the advanced one runs), and two more one-hour evaluation reads will be queued there later.
You have priority on Orchard: if you want the \`advanced\` cap or the \`general\` slot at any point, write one line in this folder and we yield.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: leg_s1_canary RESULT 0345Z (packed four-worker feasibility): both accepted job scripts refuse as steps of an advanced job (partition, allocation, card, context, namespaces exposing all of /tmp, shared CLOUDSDK_CONFIG, signals reach only the batch step); packing needs new sealed step modes in both kits, a controller + shim, a joint review and Orchard-only proofs; disk bound 1.25 TB. DECISION: PACKED JOB NOT BUILT. Instead IF-P0 P0 moves to the advanced partition as an ordinary single one-GPU job after the leg releases the cap (~15:00Z), freeing general for the three direct reads in sequence. ORDERS ($N): leg_s1_canary writes distill_design/ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md; if_p0 admits partition advanced (allowlist, packet bound to its partition), reseals, prepares a second packet with a fresh token; 169413 stays queued until the advanced job passes preflight, then I order it cancelled. Announced the intended Orchard use to main ($D/INBOX_TO_NONTRAINING_ORCHESTRATOR_${N}_orchard_advanced_after_leg.md)." >> $C/ORCH_HANDOFF.md; echo $N