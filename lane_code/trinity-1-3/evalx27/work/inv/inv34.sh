set +e
ps -o pid,cmd -p 981703
kill 981703; sleep 5; ps -o pid,stat,cmd -p 981703
sleep 40; cat /project/community/jjyeung/okh7/x27tmp/move2.log; ls /home/jjyeung/okit/tmp
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=100 2>&1 | tail -1
: > /home/jjyeung/okit/tmp/.qprobe_x27
