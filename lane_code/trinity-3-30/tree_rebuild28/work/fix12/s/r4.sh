W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w33n; cd $F
cat test1.t1.log | cut -c1-300
tar cf - test1.build.log test1.tchk.log test1.fu.log test1/BUILD33.json test1/TEST_T1_33.json test1/TEST_FRAMES_33.json test1/j_merged.sh </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix12/rd && tar xf - && echo GOT'
