export TZ=UTC
sinfo -N -h -p general -o "%N %G %f %T"
N=$(sinfo -N -h -p general -o %N | head -1); scontrol show node $N | grep -iE "gres|features|cfgtres"
cat /project/community/jjyeung/e09e45fda45db/a/7.txt
