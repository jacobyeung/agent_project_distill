#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
sed -n '/^## Lane tests and remaining work/,/^## /p' /scratch/jjyeung/orch_n30/so_launch/out/REPORT.md | head -40 | cut -c1-400
cat /scratch/jjyeung/orch_n30/so_git/work/realgit3_launch.txt 2>/dev/null | tail -12
uptime
