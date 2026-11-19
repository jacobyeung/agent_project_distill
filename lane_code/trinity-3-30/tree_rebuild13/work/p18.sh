W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w23
ls work/build23b | tr '\n' ' '; echo; head -c 1500 work/build23b/CAPACITY_PENDING.json; echo
cat work/build23b/run.sh | head -20
grep -l "native23\|capacity" work/build23b/*.py work/build23b/*.sh 2>/dev/null | head
ls -la work/build23b/CAPACITY.json 2>&1 | head -2
