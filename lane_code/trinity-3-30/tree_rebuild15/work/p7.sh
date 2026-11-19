W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B=$W/w24/work/build24f; R=$B/rehearsal4; date -u +%TZ
sed -n 1,41p $B/check_rehearsal.py
ls $R | tr '\n' ' '; echo; cat $R/CHECK.json | head -c 2500; echo
grep -n -iE "export|milestone" $R/train_fresh.log | grep -v disk_guard | tail -15 | cut -c1-600
tail -5 $R/train_fresh.log | cut -c1-800
