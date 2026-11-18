M=/scratch/jjyeung/n30_mirror
ls -la $M/cont_ops/ ; ls $M | head -40
for f in $M/cont_ops/h1vsti*.tar; do echo "== $f"; tar tf $f | awk -F/ '{print $1"/"$2"/"$3}' | sort | uniq -c | sort -rn | head -40; done
