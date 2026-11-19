O=/scratch/jjyeung/orch_n30; cd $O/sb_cachk; ls; ls kit_v2 | head -40; wc -l kit_v2/post_gpu.sh; cat kit_v2/post_gpu.sh | head -80; df -h /scratch | tail -1; ls out/v2 2>/dev/null | head
timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
cd /scratch/jjyeung/orch_n30/sb_cachk/out/v2 && du -sh track && ls track | head -20 && ls track | wc -l && ls
Y
