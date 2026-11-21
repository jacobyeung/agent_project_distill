# 9-min wait while 174198 held; exits on state change, new inbox file, or fix16 report change
W=/scratch/jjyeung/orch_n30/tree_rebuild28/work/watch.log; I=/scratch/jjyeung/orch_n30/tree_rebuild28/inbox; R=/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix16/REPORT.md
n0=$(ls $I | wc -l); s0=$(stat -c %s $R 2>/dev/null || echo 0)
for i in $(seq 1 9); do sleep 60; l=$(grep 'state=' $W | tail -1); echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM $l" | cut -c1-300; exit 1; }
 [ $(ls $I | wc -l) -gt $n0 ] && { echo "NEW INBOX: $(ls -t $I | head -1)"; break; }
 [ $(stat -c %s $R 2>/dev/null || echo 0) -ne $s0 ] && [ $i -ge 3 ] && { echo "FIX16 REPORT CHANGED"; break; }; done
echo "$(echo "$l" | cut -c1-60) $(echo "$l" | grep -o 'hold=[A-Za-z]*')"
