export TZ=UTC
I=/project/community/jjyeung/okh7/i_bb09a77d
ls -la $I $I/jb $I/r8 $I/g 2>&1 | head -60
ls -la /project/community/jjyeung/okh7/x_3b862883/g /project/community/jjyeung/okh7/x_3b862883/k/4.json 2>&1 | head
ls -lt /project/community/jjyeung/okh7/ | head -15
df -h /project/community 2>&1 | tail -1
squeue -u $USER -o '%i %j %P %T %S %M %b' 2>&1 | head
