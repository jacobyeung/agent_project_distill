TZ=UTC sacct -j 173346 -X -n --format=State,Elapsed,ExitCode
timeout 120 srun --overlap --jobid=173346 --ntasks=1 --cpus-per-task=1 bash -c "grep -c capture_commit /tmp/a_173346_f67f0b1118da0677/sj/a7e31d84/r/a/native/probe/PROGRESS.jsonl"
ls /project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5/f67f0b1118da0677/173346/
