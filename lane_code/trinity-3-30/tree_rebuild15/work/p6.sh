W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B=$W/w24/work/build24f; date -u +%TZ; wc -l $B/rehearsal_run4.log; grep -n -iE "export|copier|receipt|error|refus|Traceback|MISMATCH" $B/rehearsal_run4.log | head -30 | cut -c1-400
ls $B/rehearsal4 | tr '\n' ' '; echo
for f in $(ls -t $B/rehearsal4/*.log 2>/dev/null | head -4); do echo "== $f"; grep -n -iE "export|copier|error|refus|Traceback|Mismatch" $f | tail -8 | cut -c1-400; done
sed -n 1,200p $B/check_rehearsal.py | grep -n -iE "export|copier" | head -20 | cut -c1-300
du -sh $B/rehearsal4 | cut -f1
