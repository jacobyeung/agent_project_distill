W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; df -BG --output=avail /scratch | tail -1
du -s --block-size=1M $W/* 2>/dev/null | sort -n | tail -8; du -s --block-size=1M $W/w24/* $W/w24/work/* 2>/dev/null | sort -n | tail -10
ls $W/REMOVAL_CANDIDATES.md 2>/dev/null && tail -5 $W/REMOVAL_CANDIDATES.md | cut -c1-200
