TZ=UTC sacct -j 174328,174439 -X -o JobID,State,Elapsed,Start,NodeList -n
TZ=UTC squeue -u jjyeung -p general -h -o '%i %j %T %M'
TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %M %R'
