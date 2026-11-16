set +e
C=/project/community/jjyeung; O=/home/jjyeung/okit
D=$O/tmp/x27c; mkdir -p $D/r2 $D/r0 $D/cam $D/ebe $D/f17
tar xf $C/bd8ae51c/p/d59945c1/371be2e2.00 -C $D/r2 --exclude='sj/orch_cd/legs1_reads/work/bound_cells_final' 2>&1 | tail -2
du -sh $D/r2; (cd $D/r2 && find . -type f -size +5M -printf '%s %p\n' | sort -rn | head -20)
cat $O/p/d59945c1/4fe70504.00 $O/p/d59945c1/4fe70504.01 | tar xf - -C $D/r0 --exclude='sj/envs' --exclude='sj/uv-python' 2>&1 | tail -2
du -sh $D/r0; (cd $D/r0 && find . -type f -size +5M -printf '%s %p\n' | sort -rn | head -10)
tar xf $C/bd8ae51c/p/d59945c1/5e297c41.tar -C $D/cam
tar xzf $O/evalx_results/ebe307cf4/result.tar.gz -C $D/ebe --exclude='native/geometry'
ls -la $C/cp4tk_eval/eval/cells/f17ref_vsi $C/cp4tk_eval/eval/cells/f17tk_vsi
