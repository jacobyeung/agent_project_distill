cd /scratch/jjyeung/orch_n30 && tar cf - so_step/work/full_suite_by_swarm_opt.txt so_launch/out/REPORT.md so_launch/out/NOTE_FOR_TREE_REBUILD.md so_launch/out/patches/manifest.json 2>/dev/null | base64 -w0; echo
tail -c 400 /scratch/jjyeung/orch_n30/so_cr_probe/cursor.log
