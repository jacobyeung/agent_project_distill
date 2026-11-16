cd /scratch/jjyeung/mp3d && ls -la; for d in */; do echo "-- $d"; ls -la $d | head -30; done
ls e0_scenes/* | head -30; du -sh e0_scenes mp3d_dl 2>/dev/null
ls mp3d_dl/* 2>/dev/null | head -40
ls -d /scratch/jjyeung/envs/nav_habitat024 /scratch/jjyeung/orch_cd 2>&1; ls /scratch/jjyeung/orch_cd 2>&1 | head
df -h /scratch | tail -1
