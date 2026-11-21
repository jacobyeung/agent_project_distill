W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep tr2
tail -c 1500 $W/work/rev24m4z7.log; echo; tail -c 800 $W/work/b24m4z9.log; echo
cat $W/w24z9/out/BUILD24M4Z9_REPORT.md; ls $W/w24z9/out $W/w24z9/out/e3
for P in $W/w24z8/out/tree_rebuild_b24m4z8_1075c5ab.tar $W/w24z9/out/tree_rebuild_b24m4z9_360fab65.tar; do cut -c1-16 $P.sha256; sha256sum $P | cut -c1-16; timeout 200 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null; done
echo =====PIN; cat $W/w24z8/out/PIN_24M4Z8.md
