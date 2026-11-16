set +e
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=8 2>&1 | tail -1
ls -la /home/jjyeung/okit/tmp/.qprobe_x27
: > /home/jjyeung/okit/tmp/.qprobe_x27
ls -la /home/jjyeung/okit/tmp/nr2 /home/jjyeung/okit/tmp/nr2/* 2>&1 | head
repquota 2>&1 | head -2; quota -v 2>&1 | head; cat /etc/quota* 2>/dev/null | head -3
df -h /project/community | tail -1
