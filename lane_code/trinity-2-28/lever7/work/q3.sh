TZ=UTC sacct -j 174264 -X -o JobID,State,Elapsed,Start,NodeList -n
TZ=UTC squeue -u jjyeung -p general -h -o '%i %j %T %M'
