export TZ=UTC; date -u +%TZ; squeue -j 170846 -h -o "%i %T %M %N %r" 2>&1; sstat -j 170846.batch -n -o AveCPU,MaxRSS,MaxDiskRead 2>&1 | head -1; squeue -u jjyeung -h -p general -o "%i %j %T %r" | grep -v 170846
ls /project/community/jjyeung/okh7/ae71c903 | grep bf94 ; 
