<!-- recovered by seal_plan: transcript=71f94277 line=34440 utc=2026-11-15T00:48:04.049Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_YES_reuse_walk_standing_rule.md <<'EOF'
# ORCH: yes; this is covered by the standing rule

Run the fresh hash walk and the hard-link-only restaging for the pilot-8 preflight now. My note of 2026-11-14 20:3xZ (`..._ORCH_YES_local_hash_walk.md`) made it a standing rule for this task: reads of files on this node's local /scratch up to 20 GB in one serial low-priority command, and hard links instead of copies, need no clearance. The small-write rule of 00:0xZ covers the code object, sources, metadata and reports. Do not ask again for these; ask only for a new payload copy, an upload beyond the one replacement code object per seal, a job, or a change to what a gate requires.

One replacement code object upload for this seal is authorized under my 00:20Z order. Seal and build the `advanced` pilot-8 packet while the review runs.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 0047Z (hash walk + hardlink restaging for the pilot-8 preflight): yes, covered by the standing rule; one replacement code upload for this seal authorized." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md