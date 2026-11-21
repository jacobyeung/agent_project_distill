J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26t; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $J/work/build26
nice -n 10 $P -I -s -B test_jn6.py > tests.log 2>&1; echo "main rc $?" >> tests.log
nice -n 10 $P -I -s -B test_extra6.py > extra.log 2>&1; echo "extra rc $?" >> extra.log; date -u +%TZ > DONE
