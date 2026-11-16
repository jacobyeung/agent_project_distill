set +e
cat /project/community/jjyeung/okh7/x27tmp/move2.log; ps -u jjyeung -o pid,etime,cmd | grep -E ' mv |sleep 10' | grep -v grep
ls /home/jjyeung/okit/tmp; ls -la /project/community/jjyeung/okh7/x27tmp/
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=100 2>&1 | tail -1
: > /home/jjyeung/okit/tmp/.qprobe_x27
