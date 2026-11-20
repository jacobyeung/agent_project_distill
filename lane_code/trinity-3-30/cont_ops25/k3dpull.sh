exec 3>&1 1>&2
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild && sha256sum --check --quiet orchard_tower2x_c/SHA256SUMS_K3D && echo SUMS_OK && cd orchard_tower2x_c && ls -la o_*.sh && tar cf - o_place.sh o_cpu.sh o_check_sub.sh o_fetch.sh SHA256SUMS_K3D >&3
