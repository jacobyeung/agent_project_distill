set +e
T=/project/community/jjyeung/okh7/x27tmp
mkdir -p $T
cd /home/jjyeung/okit/tmp
for f in x27env x27c x27b x27c.tar.gz x27_pull.tar x27c_list.txt; do mv $f $T/ && echo "moved $f"; done
du -sh $T/* 2>/dev/null
du -sh /home/jjyeung 2>/dev/null
dd if=/dev/zero of=/home/jjyeung/okit/tmp/.qprobe_x27 bs=1M count=8 2>&1 | tail -1
: > /home/jjyeung/okit/tmp/.qprobe_x27
ls -la /home/jjyeung/okit/tmp
