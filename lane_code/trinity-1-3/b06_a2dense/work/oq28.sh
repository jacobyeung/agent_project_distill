export TZ=UTC; date -u +%FT%TZ
cat /project/community/jjyeung/okh7/db3954b2/logs/dserial.170379.log; ls /project/community/jjyeung/okh7/db3954b2/parts
scancel 170379; echo "scancel rc $? at $(date -u +%FT%TZ)"; sleep 15
squeue -j 170379 -h -o '%i %T' 2>&1; squeue -u jjyeung -p general -h -o '%i %j %T'; echo "-- general empty check done $(date -u +%FT%TZ)"
sacct -j 170379 -X -n -o JobID,State,Start,End 2>&1
