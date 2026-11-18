<!-- recovered by seal_plan: transcript=71f94277 line=902 utc=2026-11-11T12:09:14.811Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && T=$(date -u +%Y%m%dT%H%MZ) && cat > vla_libero/inbox/${T}_ORCH_ANSWER_b1_weights.md <<EOF
# ORCH ANSWER ($(date -u +%Y-%m-%dT%H:%M:%SZ)) to your 1208Z QUESTION: keep your default; do not move T0 m800
- Use CP1 m200 from orchard_cp2's parts (read-only, staged in-job to node-local /tmp) for every kit test and for the B1 launch config. Keep B1_SRC as the one variable.
- Do not copy T0 m800 from Trinity. The real B1 will be the best student at launch time (the Orchard runs 168042/168043 produce the next ones on Orchard itself); anything that must come from elsewhere goes Mind -> GCS -> Orchard, never through the Trinity head node.
- In the pre-launch card, state which export B1 used in the tests and that the final run swaps it by B1_SRC; the kit must fail loudly if the export's key layout differs from CP1 m200's (760 tensors, HF Qwen3.5 key names).
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: vla_libero Q 1208Z (which student export is B1; T0 m800 only on 2-18): ANSWER keep default = CP1 m200 from orchard_cp2's Orchard parts, B1_SRC variable, no Trinity->Orchard copy." >> ORCH_HANDOFF.md