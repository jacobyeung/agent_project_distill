export TZ=UTC
scontrol show job 172481 2>&1 | grep -E "JobState|Reason|SubmitTime|EligibleTime|StartTime|Priority|Hold" | head
scancel 172481; echo scancel_rc=$?
sleep 5; squeue -u $USER -o '%i %j %P %T %M' ; sacct -j 172481 -X -o JobID,State,End 2>&1 | tail -2
K=/project/community/jjyeung/okh7
cat $K/r/673bc60f/A.json; echo; cat $K/r/673bc60f/A.verify.part; echo; cat $K/r/673bc60f/A.sha256; cat $K/r/673bc60f/binding.json; echo
ls -la $K/x_7f1589c1/o 2>&1 | tail -20
