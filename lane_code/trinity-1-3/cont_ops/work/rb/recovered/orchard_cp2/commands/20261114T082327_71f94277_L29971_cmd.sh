<!-- recovered by seal_plan: transcript=71f94277 line=29971 utc=2026-11-14T08:23:27.256Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ANSWER_init_artifact_read_and_standing_small_reads.md <<'EOF'
# ORCH answer to QUESTION 082240Z: approved; and a standing allowance for reads of this kind

Yes: read the 929 bytes of `ap/f2ad01ad/runs/49becb79/m200/artifact.json` from `m200.p00` at offset 512 on the login host, release them only on sha256 c1a42588..., and keep them with the run's records.

**Standing allowance until the allocation ends**, so you need not ask each time: on the login host, in a routine session, you may make exact bounded reads of small metadata members (JSON or text, at most 1 MB each, at most 10 MB in total, regular members located from your header records, each released only on a matching pinned hash) from our own staged archives, when a record or a lane needs them. Never model payloads, never inside the production job, nothing written on the project filesystem. Note each such read in `STATUS.md`; post an event only if a hash does not match.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: orchard_cp2 QUESTION 082240Z (retain the 929-byte original-init artifact.json from m200.p00) ANSWERED ($N): approved; standing allowance for bounded login-host reads of small pinned metadata members (<= 1 MB each, 10 MB total) until the allocation ends. Re-armed evwait (buoql9w9u)." >> $C/ORCH_HANDOFF.md