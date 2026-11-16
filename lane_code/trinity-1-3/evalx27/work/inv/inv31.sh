set +e
cat /project/community/jjyeung/okh7/x27tmp/move2.log
ps -u jjyeung -o pid,etime,cmd | grep -E ' mv ' | grep -v grep | head
ls /home/jjyeung/okit/tmp
du -sh /project/community/jjyeung/okh7/x27tmp/x27env 2>/dev/null
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=8 2>&1 | tail -1
: > /home/jjyeung/okit/tmp/.qprobe_x27
