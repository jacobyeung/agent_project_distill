# 9-min held wait; exits on state change, new inbox, change of fix16's EARLY STEPS/QUESTION/BLOCKER lines
W=/scratch/jjyeung/orch_n30/tree_rebuild28/work/watch.log; I=/scratch/jjyeung/orch_n30/tree_rebuild28/inbox; R=/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix16/REPORT.md
k(){ grep -E "^(EARLY STEPS|QUESTION|BLOCKER|REFUS)" $R 2>/dev/null | md5sum; }
n0=$(ls $I | wc -l); s0=$(k)
for i in $(seq 1 9); do sleep 60; l=$(grep 'state=' $W | tail -1); echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM $l" | cut -c1-300; exit 1; }
 [ $(ls $I | wc -l) -gt $n0 ] && { echo "NEW INBOX: $(ls -t $I | head -1)"; break; }
 [ "$(k)" != "$s0" ] && { echo "FIX16 KEY LINES CHANGED"; break; }; done
echo "$(echo "$l" | cut -c1-60) $(echo "$l" | grep -o 'hold=[A-Za-z]*')"; grep -E "^(EARLY STEPS|QUESTION|BLOCKER)" $R | cut -c1-300
