<!-- recovered by seal_plan: transcript=71f94277 line=32254 utc=2026-11-14T15:25:11.982Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_AMEND_keep_P0_held_until_my_order.md <<'EOF'
# ORCH amendment: keep 169530 held; do not release it when the pilot runs

Since `advanced` carries main's pending jobs (167859 to 167861), the full routed read will also need our `general` slot, and it outranks the IF-P0 run. So:

- Do not release 169530 when pilot 169537 starts or finishes. It stays held until I order its release.
- If the pilot passes, build the full-read packet for `general` first and report its token with the pilot's RESULT; I then order the full read, and P0 is released behind it.
- If the pilot fails, I will most likely release P0 at once so the card is not idle while the failure is fixed; wait for that order.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1524Z: account listing shows main's jobs 167859-167861 PENDING (Dependency) on advanced -> fallback applied: pilot 4 submitted once on general = job 169537 (token ee49236ff, family e2374d64), PENDING behind final read 169526; P0 169530 held. Amended: P0 stays held until my order (full routed read goes before it on general)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md