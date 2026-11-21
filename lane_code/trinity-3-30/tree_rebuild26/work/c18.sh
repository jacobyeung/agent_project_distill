K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go; cd $K/b; date -u +%TZ
sed -n 262,300p rv.py | cut -c1-200; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys;sys.path.insert(0,'$K/b');from z import load;a=load('$K/k/a.json');print('review_wait_seconds',a.get('review_wait_seconds'),'GO',a.get('GO'))"
J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26t5/work/build26; cat $J/DONE 2>&1; tail -1 $J/tests.log | cut -c1-200
