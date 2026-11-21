X=/project/community/jjyeung/okh7/x_22c714e1
cat $X/o/n10_du_0915Z.txt
df -B1 /project/community | tail -1
TZ=UTC squeue -u jjyeung -h -o "%i|%j|%P|%T|%M|%N"
