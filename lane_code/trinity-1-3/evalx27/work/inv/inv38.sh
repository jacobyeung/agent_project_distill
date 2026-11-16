set +e
pkill -u jjyeung -f '^mv x27' ; sleep 3
ps -u jjyeung -o pid,ppid,etime,cmd | grep -E 'mv x27|bash -s' | grep -v grep
