set +e
kill 1003279 1050890; sleep 5
ps -u jjyeung -o pid,etime,cmd | grep -E ' mv |sleep 10|x27' | grep -v grep
ls -la /project/community/jjyeung/okh7/x27tmp/
