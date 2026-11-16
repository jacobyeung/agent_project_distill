<!-- recovered by seal_plan: transcript=71f94277 line=14410 utc=2026-11-12T17:52:43.891Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > leg_s1_tree/inbox/${T}_ORCH_ANSWER_probe_location.md <<EOF
# ORCH answer ($T): the probe's root is in project space; one new run is authorized

Use /project/community/jjyeung/okh7/probe37845077/ as the probe's root (I told orchard_cp2 the same at 1743Z). It is disk-backed NFS with more than 1 TB free; nothing more goes into the login node's /tmp or /var/tmp. One new run of the fixed script is authorized: idle priority, CPU only, bytecode writing off, the size inventory before extraction as you propose, the F1 third-party imports included, nothing that creates a persistent marker. Send the fixed script to orchard_cp2 now and continue with the F2 check and final_a; the probe and the assembly run in parallel.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: leg_s1_tree QUESTION 1750Z (probe location): answered project space okh7/probe37845077; one new run authorized." >> ORCH_HANDOFF.md