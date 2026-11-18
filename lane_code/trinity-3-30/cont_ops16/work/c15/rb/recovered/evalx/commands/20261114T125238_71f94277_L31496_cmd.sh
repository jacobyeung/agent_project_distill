<!-- recovered by seal_plan: transcript=71f94277 line=31496 utc=2026-11-14T12:52:38.702Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_CLEARED_cpu_rerun_with_production_adaptation.md <<'EOF'
# ORCH: cleared. Rerun the CPU move replay with exactly the production adaptation

Your reading is right: the replay must hand P2 what `nomdg.run` hands it (the deep copy with `trace313_live` removed when there are no ground queries). Rerun now.

Standing rule for the rest of this session: CPU-only reruns and corrections of your own test harness need no clearance from me. Ask only before a job, an upload, a change to a pinned runtime file, or a change of what a gate requires.

If the rerun passes, seal and continue as ordered at 12:18Z (family sha, token, replaced object, replay result, P0 state in one event). If it fails with the production adaptation, that is a real finding: stop and send me the assertion and the P2 inputs.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx BLOCKER 1251Z: CPU move replay detected and served '<move from=18 to=23>' (0 errors) but its own driver passed the raw decode to P2 instead of production's legacy-adapted copy (unsupported_acceptance_call). Cleared an immediate CPU rerun with the production adaptation; standing rule: CPU-only harness reruns need no clearance." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md