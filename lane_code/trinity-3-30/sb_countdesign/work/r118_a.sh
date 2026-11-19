set -u
hostname -s
echo ---MIRROR
ls -la /scratch/jjyeung/n30_mirror/ | head -60
ls -la /scratch/jjyeung/n30_mirror/b08_headrows/ 2>&1 | head
T=/scratch/jjyeung/n30_mirror/b08_headrows/b08_partA.tar
echo ---TARLIST
tar tvf $T 2>&1 | head -60
echo ---LANES
ls /scratch/jjyeung/orch_n30/ 2>&1 | tr '\n' ' '
echo
echo ---B10
ls -la /scratch/jjyeung/orch_n30/b10_reserve/ /scratch/jjyeung/orch_n30/b10_reserve/out /scratch/jjyeung/orch_n30/b10_reserve/code 2>&1 | head -120
