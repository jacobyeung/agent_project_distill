echo "== $(hostname -s) $(date -u +%T)"
cd /scratch/jjyeung
timeout 60 find orch_n30 n30_mirror orch_cd -maxdepth 7 \( -name '*metadata*.csv' -o -name '*visits*.csv' -o -name 'VISITS*' \) 2>/dev/null | head -20
mkdir -p /tmp/nvk2_excl && cd /tmp/nvk2_excl && cp /scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json /scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json /scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json /scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt /scratch/jjyeung/orch_n30/sb_alias2/work/TEACHER_K1.raw . && sha256sum * 
