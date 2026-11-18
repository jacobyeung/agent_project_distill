export TZ=UTC
scancel 171335; echo scancel rc=$?
sleep 20
sacct -X -n -P -j 171335 -o JobIDRaw,State,Elapsed
squeue -u $USER -h -o "%i|%T|%R" | grep -v jjy_
