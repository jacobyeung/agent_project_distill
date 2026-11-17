export TZ=UTC
echo "== host $(hostname) $(date -u +%FT%TZ)"
squeue -u jjyeung -o '%i %j %P %T %M %l %D %b' 2>&1 | head -30
echo "== df"; df -h /project/community 2>&1 | tail -2; lfs quota -u jjyeung /project/community 2>&1 | tail -3
echo "== top"; ls -la /project/community/jjyeung | head -80
echo "== okh7"; ls -la /project/community/jjyeung/okh7 | head -60
echo "== okit"; ls -la /home/jjyeung/okit /home/jjyeung/okit/p 2>&1 | head -40
echo "== lustre ap"; ls /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap 2>&1 | head
echo "== tools"; which gsutil gcloud python3 2>&1; ls -la /project/community/jjyeung/gcloud 2>&1 | head
echo "== big files"
nice -n 19 find /project/community/jjyeung /home/jjyeung -maxdepth 5 -type f -size +1000M -printf '%s %TY-%Tm-%Td %p\n' 2>/dev/null | sort -k3 | head -150
