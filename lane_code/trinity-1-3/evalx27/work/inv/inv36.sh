set +e
ls -la /proc/1050890/fd 2>/dev/null | tail -2; grep State /proc/1050890/status 2>/dev/null
ps -o pid,ppid,etime,cmd -p $(pgrep -u jjyeung -x sleep | head -3 | tr '\n' ',' | sed 's/,$//') 2>/dev/null
du -sh /project/community/jjyeung/okh7/x27tmp/x27c 2>/dev/null
