cd /scratch/jjyeung/orch_n30 && tar cf - so_launch/out/REPORT.md so_launch/out/NOTE_FOR_TREE_REBUILD.md so_launch/out/CROSS_RUN_STORE_DESIGN.md so_launch/out/patches/manifest.json so_git/out/REPORT.md so_git/out/GIT_OWNER.md so_git/out/MANIFEST.json 2>/dev/null | base64 -w0; echo
bash /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/qrun.sh
