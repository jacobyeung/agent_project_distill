W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
du -sh /scratch/jjyeung/envs/p1cpu $W/w24/work/tree_r1 2>/dev/null; ls -la --time-style=+%H:%M $W/w24/out/TREE_SEAL.json $W/w24/out/TREE_FILES.sha256; head -c 400 $W/w24/out/TREE_SEAL.json; echo
tmux ls | grep -i "tr14\|b24f"; tail -c 300 $W/w24/out/BUILD24F_REPORT.md 2>/dev/null; echo
grep -n "ALIASES\|STUDENT_R2_FRAME_HOST\|Q_E7" $W/w24/work/tree_r1/student_pilot/job_env.py | head -5; grep -n "env_key\|STUDENT_R2_FRAME_HOST" $W/w24/work/tree_r1/student_pilot/r2_intake.py | head
ls /scratch/jjyeung/orch_n30/sb_own400 /scratch/jjyeung/orch_n30/sb_own400/kit | head -30
