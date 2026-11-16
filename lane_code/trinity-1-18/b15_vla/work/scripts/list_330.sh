echo "HOST $(hostname -s) $(date -u)"
cd /scratch/jjyeung 2>/dev/null && ls -la
for d in orch_cd orch_cd/nav_build orch_cd/vla_pilot vla_pilot nav_build envs; do [ -e "$d" ] && { echo "== $d"; ls -la "$d" | head -50; }; done
for d in orch_cd/nav_build nav_build; do [ -d "$d" ] && { echo "== tree $d"; find "$d" -maxdepth 4 -not -path '*/__pycache__*' -not -path '*/scenes*' | head -200; echo "== du $d"; du -sh "$d"/* 2>/dev/null | head -30; }; done
for d in orch_cd/vla_pilot vla_pilot; do [ -d "$d" ] && { echo "== tree $d"; find "$d" -maxdepth 3 | head -120; du -sh "$d" 2>/dev/null; }; done
ls -d /scratch/jjyeung/mp3d* /scratch/jjyeung/orch_cd/mp3d* 2>/dev/null
df -h /scratch
