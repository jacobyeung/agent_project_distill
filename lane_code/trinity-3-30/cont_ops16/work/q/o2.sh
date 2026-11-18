TZ=UTC sacct -u jjyeung -S 2026-11-18T00:00 -n -X -o JobID,JobName%30,Partition,State,Start,End | tail -25
ls -la /project/community/jjyeung/okh7/ae71c903/ | grep -E "a8102c3207b|a35f73e87f0"; echo "pool check done"
ls -la /project/community/jjyeung/okh7/af83c921/
