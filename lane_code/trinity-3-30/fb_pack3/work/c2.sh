set -u; F=/scratch/jjyeung/orch_n30/fb_pack; C=$F/combo; T=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out/tree_rebuild_b24l4t_c558ad33.tar
mkdir -p $C/pkg && cd $C/pkg && { [ -n "$(ls -A)" ] || tar xf $T; } && ls | head; sha256sum $T | cut -c1-16
