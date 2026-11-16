set +e
kill 981701 2>/dev/null; sleep 2; ps -u jjyeung -o pid,etime,cmd | grep -E "mv x27|981701" | grep -v grep; echo ok
