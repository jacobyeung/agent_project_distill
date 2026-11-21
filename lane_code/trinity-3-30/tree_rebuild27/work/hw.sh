# held-job wait: 9 min; exits early if job leaves RUNNING or new inbox file
W=/scratch/jjyeung/orch_n30/tree_rebuild27/work/watch.log; I=/scratch/jjyeung/orch_n30/tree_rebuild27/inbox; n0=$(ls $I | wc -l)
for i in $(seq 1 9); do sleep 60; l=$(grep 'state=' $W | tail -1); echo "$l" | grep -q 'state=RUNNING' || { echo "ANOM $l" | cut -c1-300; exit 1; }; [ $(ls $I | wc -l) -gt $n0 ] && { echo "NEW INBOX: $(ls -t $I | head -1)"; break; }; done
echo "$(echo "$l" | cut -c1-60) $(echo "$l" | grep -o 'hold=[A-Za-z]*')"; R=work/fix6/REPORT.md; grep -n "^## \|^VERDICT\|^ITEM\|^STATUS" /scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/REPORT.md | tail -6 | cut -c1-200
