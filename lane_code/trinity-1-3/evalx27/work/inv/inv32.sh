set +e
cd /home/jjyeung/okit/tmp
timeout 100 mv x27c.tar.gz x27_pull.tar x27c_list.txt /project/community/jjyeung/okh7/x27tmp/ && echo moved_small
ls -la /project/community/jjyeung/okh7/x27tmp/
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=8 2>&1 | tail -1
: > /home/jjyeung/okit/tmp/.qprobe_x27
cat /proc/981703/status 2>/dev/null | grep State; ls -la /proc/981703/fd 2>/dev/null | tail -3
