exec 3>&1 1>&2
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild && sha256sum --check --quiet orchard_tower2x_b/SHA256SUMS_K3c && echo SUMS_OK && cd orchard_tower2x_b && ls -la o_*.sh place.tar && tar cf - o_place_head.sh place.tar o_cpu.sh o_check_sub.sh o_fetch.sh SHA256SUMS_K3c >&3
