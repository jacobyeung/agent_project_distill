cd /scratch/jjyeung/orch_cd && for d in mp3d_dl nav_build nav_survey; do echo "== $d"; ls -la $d; for s in $d/*/; do echo "-- $s"; ls -la $s | head -25; done; done
du -sh mp3d_dl/* nav_build/* 2>/dev/null
ls /scratch/jjyeung/mp3d/v1/tasks; ls -la /scratch/jjyeung/mp3d/e0_scenes/mp3d/8194nk5LbLH
