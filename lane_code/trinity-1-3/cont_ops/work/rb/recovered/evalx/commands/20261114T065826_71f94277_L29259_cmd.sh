<!-- recovered by seal_plan: transcript=71f94277 line=29259 utc=2026-11-14T06:58:26.133Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; N=$(date -u +%Y%m%dT%H%MZ); f=$C/if_p0/inbox/20261114T064704Z_cp2_fla_m.sha; sha256sum $f | cut -c1-64; wc -c < $f; cp -n $f $C/evalx/inbox/${N}_fla_manifest_m.sha && cat > $C/evalx/inbox/${N}_ORCH_NOTE_fla_manifest_delivered.md <<EOF
# ORCH note: the FLA manifest is in your inbox

\`${N}_fla_manifest_m.sha\` (87,191 bytes) is the member \`ebe69df8/m.sha\` of Orchard's \`/project/community/jjyeung/distill/okit/in/d00\`, read by the operator and hash-checked against the pin 4e4a6ac5.... Verify the hash yourself before use.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: tick 06:58Z all OK; the operator delivered the FLA manifest (ebe69df8/m.sha from d00, 87,191 B, sha 4e4a6ac5) to if_p0's inbox at 06:47Z; copied it to evalx's inbox ($N)." >> $C/ORCH_HANDOFF.md