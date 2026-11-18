<!-- recovered by seal_plan: transcript=71f94277 line=27842 utc=2026-11-14T02:45:26.898Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/if_p0/inbox/${N}_ORCH_CONTROL_FILES_written_build_the_P0_packet.md <<'EOF'
# ORCH: final seal 8d5bdd73 accepted; the three control files are written; build the P0 packet

I read the provenance diff (sha 4c277a0d): it is exactly the ruled change. The control files are under `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL/`:
- `review.md` (sha256 7632f686...; the independent verdict verbatim plus my two diff readings),
- `confirmation.json` (sha256 41ab1c53...; your schema, bound to the final seal and to the report hash),
- `launch_note.md` (the single line `LAUNCH IF-P0 P0 8d5bdd73...`).
I ran your kit's own `admit()` on them: P0 is accepted, IF8 is refused.

Now:
1. Mint one opaque token of the form your launcher requires and build the P0 packet locally with the command in `out/SUBMIT_P0_FOR_OPERATOR.md` (it does not submit). Verify `BATCH.sh` against its pin.
2. Post one RESULT with: the token, the path, size and sha256 of `BATCH.sh`, the two exact `sbatch` argument lists, and the result path on Orchard. Write the same facts as a hand-off note into `/scratch/jjyeung/orch_cd/evalx/inbox/` (file name starting with a `date -u` stamp and `IF_P0_P0_PACKET_READY`), stating plainly that evalx submits only when the orchestrator's own note says so.
3. Do not build IF8 or AT8 packets. Stay on the inbox; when P0's result archive returns I will send it to you for the read and the IF8 admission arithmetic.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: if_p0 RESULT 0243Z: final seal 8d5bdd73 (out/tree_provenance_v3/kit_ifp0_orchard_job_8d5bdd730bebb9b3; archive 6a15d91d; 67 tests; rehearsal COMPLETE 3/3; diff 4c277a0d = admission binds source_identity sealed_tree, run record says not in git). I READ THE DIFF: accepted. WROTE the control files if_p0/out/P0_CONTROL/{review.md (7632f686), confirmation.json (41ab1c53), launch_note.md (46e51ff1)} and verified with the kit's own admit(): P0 accepted, IF8 refused. Told if_p0 ($N) to build the P0 packet and hand it to evalx's inbox; evalx submits only on my separate word (waiting on the general-queue facts). Memory lesson-tell-main-before-staging-on-shared-node-20261114 saved (index 24.1 KB)." >> $C/ORCH_HANDOFF.md; echo $N