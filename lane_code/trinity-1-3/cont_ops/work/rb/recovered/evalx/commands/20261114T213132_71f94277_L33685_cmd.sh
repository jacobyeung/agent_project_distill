<!-- recovered by seal_plan: transcript=71f94277 line=33685 utc=2026-11-14T21:31:32.042Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_submit_IF8_general_now.md <<'EOF'
# ORCH order: submit IF-P0 arm IF8 on `general` at your next natural break (the slot is free)

LAUNCH IF-P0 IF8 eef3ba96a639d634be9ec9e976ce16aadec648f4eeb07e2bc6fee196d94516bb general a1cafcdc02be21b39

- P0 (job 169530) finished at 18.11 degrees, above the 12-degree stop threshold, so the next registered arm runs. Packet: `/scratch/jjyeung/orch_cd/if_p0/out/IF8_SUBMISSION_eef3ba96_general/` (token a1cafcdc02be21b39, BATCH.sh sha256 0c2c5ec479f99bd3f86fa4e200d7d459b41a08a0a5bca7cbf42099c8062c21bf, 12 h; projected 5.1 to 6.1 h). Control files: `/scratch/jjyeung/orch_cd/if_p0/out/IF8_CONTROL_eef3ba96/`. if_p0's validation receipt: `/scratch/jjyeung/orch_cd/if_p0/out/IF8_PACKET_READY_eef3ba96_general.json`.
- How: adapt the controller you inherited for the P0 full run (`M/s23/ifp0_a9fa8d8e44ae3c98e/` and its queue wrapper) to this packet without changing its checks; the packet's own admission, one test-only call, one real submission; our account must have no other job on `general`; no retry on any failure.
- Observe it in your ten-minute batched calls with the same stall rule (URGENT after 30 minutes without a new phase or 20 minutes without a new step); only I order a cancel. Two things to report as soon as they appear, in one event to me and a one-line note to if_p0: (a) whether the in-job prior check passed (it compares P0's result exactly; a refusal reads `Held-out metrics differ from the raw readout` and ends the job before staging); (b) the first ten step times and peak GPU memory. When it ends, fetch the return with the P0 return adapter's method into `if_p0/inbox_results/a1cafcdc02be21b39/` and notify if_p0 once.
- The routed-reader fixes keep priority otherwise; this submission should cost you about ten minutes.

One event with the job id.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) if_p0(3) RESULT 2130Z: IF8 runnable packets pass the kit's admission with my controls: general token a1cafcdc02be21b39 (BATCH sha 0c2c5ec4), advanced a9e882e9722007806 (b04310ad); projection 5.07-6.12 h; prior-check refusal and step-8 time guard documented (no proactive memory guard: OOM would abort). ORDERED evalx(24) to submit IF8 on general (inbox ${N}_ORCH_ORDER_submit_IF8_general_now.md)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md