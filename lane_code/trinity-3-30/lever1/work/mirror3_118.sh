M=/scratch/jjyeung/orch_n30/lever1_m; cat $M/run.log; tmux ls 2>/dev/null | grep l1_
if grep -q DONE $M/run.log; then
 cd /scratch/jjyeung
 nice -n 19 tar cf - orch_n30/sb_harev orch_n30/sb_k1012 | tee >(sha256sum > $M/src_tar2.sha) | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/lever1/k1x_inputs2.tar && sha256sum /scratch/jjyeung/n30_mirror/lever1/k1x_inputs2.tar'
 sleep 1; cat $M/src_tar2.sha
 # 10 sampled files: sha on the source
 tar tf /dev/null 2>/dev/null
 for p in $(cat $M/PATHS.txt); do find $p -type f 2>/dev/null; done | awk 'NR%997==1' | head -10 > $M/SAMPLE.txt
 xargs -a $M/SAMPLE.txt -d '\n' sha256sum > $M/SAMPLE_src.sha; cat $M/SAMPLE_src.sha
fi
