<!-- recovered by seal_plan: transcript=71f94277 line=32363 utc=2026-11-14T16:00:16.841Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_pilot4_input_pin_fix_and_local_as_in_job_check.md <<'EOF'
# ORCH order after pilot 169537: fix the stale code object, and prove the job's own input validation locally before pilot 5

## Probable cause (confirm from local files in five minutes; no Orchard call)

`Native input pin differs: .../orchard_native/native_job.py`. Seal e58e5a1e changed `native_job.py`, `native_metrics.py` and `native_worker.py`, and their code pins and bootstrap pins moved; but in both that seal and e2374d64 the code object's member list changed only for `nomdg.py` ("the archive changes only nomdg.py"). If the code object carries those three files as members, it still holds their old bytes while the pins name the new ones. Check the member hashes inside your local copy of `code_0521775d7ee21337.tar` against the family's code pins and tell me in the event whether this is the cause.

## Fix

1. Rebuild the code object from the current pinned files so every member equals its pin; upload it as before; reseal; build pilot-5 packets (`general` first).
2. New admission check, permanent: before any native submission, run the job's **own** input-pin validation and bootstrap path on CPU against local copies of the exact objects that were uploaded (all five, identified by sha256 and generation), staged into a scratch folder the way the job stages them, up to the point where the worker would restore on a GPU. Every pin the job checks must pass there. A packet whose local as-in-job check has not passed refuses submission. This is the fourth pilot lost to something a local run of the job's first minute would have caught; the whole-job rehearsals used stand-ins.
3. This change is packaging only (no gate, reader or worker logic changes), so it needs no new independent review. Send me one event with: the cause confirmed or not, the new family sha, the new object's name and generation, the token, and the as-in-job check's record (path, sha256, what it staged and validated). I compare the seals and the object's members myself and answer with control files.

## Slot

Keep 169530 held. Pilot 5 goes first on `general` when ready. If pilot 5 fails for any reason, release 169530 at once with exactly `scontrol release 169530` without waiting for me, and report.

Finish the final stop read's packet in parallel as far as your attention allows; the pilot fix comes first.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1559Z: native pilot 4 (169537, general) FAILED before the GPU worker: 'Native input pin differs: .../orchard_native/native_job.py' (probable cause: the code object still carries old native_job/metrics/worker members; only nomdg.py was replaced in the last two seals; I had seen that the member list changed only for nomdg.py and did not question it). Final stop read 169526 returned (39.7 MB, 541 MB expanded; packet in progress). Ordered: rebuild the code object; permanent local as-in-job input validation against the exact uploaded objects before any native submission; pilot 5 on general first; P0 169530 stays held, auto-release if pilot 5 fails." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md