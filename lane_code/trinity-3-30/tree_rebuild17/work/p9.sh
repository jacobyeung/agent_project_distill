W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr17
cat $W/w24/out/BUILD24M4_REPORT.md; echo =====; cat $W/w24c/out/BUILD24M4C_REPORT.md; echo =====
for p in w24/out/tree_rebuild_b24m4_d134c375.tar:conf24m4 w24c/out/tree_rebuild_b24m4c_20f61e78.tar:conf24m4c; do f=${p%%:*}; d=${p##*:}; sha256sum $W/$f; test ! -e $W/work/$d && mkdir -p $W/work/$d/pkg && cd $W/work/$d/pkg && tar xf $W/$f && for k in kit_q kit_n kit_n_go kit_qd; do echo "$d $k $(sha256sum out/$k/SHA256SUMS.txt | cut -c1-16) bad $(cd out/$k && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')"; done; done
ls $W/w24/out/ | grep -i "blocker\|UPLOADS_24M4"; ls $W/w24c/out | grep -i "blocker\|UPLOADS_24M4C"
