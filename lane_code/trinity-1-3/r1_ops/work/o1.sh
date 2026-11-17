export TZ=UTC
date -u
squeue -u $USER -o '%i %j %P %T %M %R' 2>&1 | head -20
echo ---
squeue -p advanced -o '%i %u %j %T %R' 2>&1 | head -15
O=/project/community/jjyeung/okh7
ls -d $O/i_17eb48c6 $O/x_17eb48c6 2>&1
ls $O/x_3fdda0fb | head -30
df -h /project/community 2>&1 | tail -1
sinfo -p advanced,general -o '%P %a %l %D %c %m %G' 2>&1 | head
