export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb; R=$K/runs/17c4ffa4; J=170710
ls -la --time-style=+%TZ $R $R/inputs | head -30
cat $R/attempt_$J.json; echo; cat $R/binding.json; echo
tail -n 3 $K/o/$J.steps; tail -n 3 $K/o/$J.w.steps; wc -c $K/o/$J.err
sstat -j $J.batch -n -o AveCPU,MaxRSS 2>&1 | head -2
