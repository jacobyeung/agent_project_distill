W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w23; date -u +%TZ
mv work/build23b/selected attic/tr13/selected_1526Z && mv work/build23b/proofs attic/tr13/proofs_1526Z && mv work/build23b/source.tar attic/tr13/source.tar_try2 2>/dev/null; mv work/build23b/capacity_final_tr13.log attic/tr13/capacity_final_tr13_try2.log
tmux new -d -s tr13_cap23b "cd $W/w23 && nice -n 10 bash work/build23b/run.sh work/build23b/capacity_final.py > work/build23b/capacity_final_tr13.log 2>&1; echo EXIT \$? >> work/build23b/capacity_final_tr13.log"
sleep 45; tmux ls | grep tr13; tail -c 600 work/build23b/capacity_final_tr13.log
