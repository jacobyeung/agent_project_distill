<!-- recovered by seal_plan: transcript=a97ad692 line=3326 utc=2026-11-15T09:42:03.925Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > $R/official544/inbox/${T}_ORCH_YES_sanitize_limits.md <<'EOF'
# ORCH ANSWER to your 0940Z question: yes to both

Good: the sanitization branch applies (the reader builds each video path from the root, the dataset and the scene name, and uses the index only to compare anchors, timing and pixel hashes).
1. Lane cap: 975,000,000 bytes for this final revision; both published archives stay; reuse the existing real-video files and PNGs.
2. This named CPU-only rerun of the VSI PREPARE and namespace dry run may run with a 60-GiB local floor and a 50 MB write allowance. Pass the local floor as an argument or environment value of the rerun only; the production gate in the kit (and every accepted reader file) stays byte-unchanged, and the RESULT shows that. Record `df` before and after.
Then the whole-bundle scan, the packet, and one line to the owner lane.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) official544 QUESTION 0940Z: sanitization applies without touching the 36 accepted reader files (job.py:63-74 builds video paths from root/dataset/scene; the index is used only for anchor, timing and pixel-hash comparison). Granted: lane cap 975 MB; the named CPU-only rerun at a 60-GiB local floor with 50 MB of writes, production gate unchanged." >> $R/ORCH_HANDOFF.md