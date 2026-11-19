set -u
hostname -s
ls /scratch/jjyeung/ 2>&1 | tr '\n' ' ' | cut -c1-1500; echo
ls /scratch/jjyeung/orch_n30/ 2>&1 | tr '\n' ' ' | cut -c1-2500; echo
ls -d /scratch/jjyeung/*/b08_headrows /scratch/jjyeung/orch_n30/*/b08_headrows /scratch/jjyeung/n30_mirror/* 2>&1 | head -40
ls -d /scratch/jjyeung/*/devs1_masks* /scratch/jjyeung/orch_n30/*/devs1* /scratch/jjyeung/*devs1* 2>&1 | head
df -h /scratch | tail -1
