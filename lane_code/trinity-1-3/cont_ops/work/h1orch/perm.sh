export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb
N=$(sinfo -p advanced -h -N -o '%N' | sort -u | tr '\n' ' '); echo "nodes: $N"
cd /tmp
for n in $N; do
  sbatch --parsable -J a15_cot_ap7e24afacbc -A mt01 -p advanced -w $n -N1 --ntasks=1 -c 1 --mem=1G -t 00:05:00 --no-requeue -o "$K/o/perm_${n##*-}_%j.out" -e "$K/o/perm_${n##*-}_%j.out" --wrap "stat -c '%a %U %n' /tmp/jjyeung 2>&1; if [ -d /tmp/jjyeung ] && [ -O /tmp/jjyeung ] && [ ! -L /tmp/jjyeung ]; then chmod 700 /tmp/jjyeung; fi; stat -c '%a %U %n' /tmp/jjyeung 2>&1"
done
squeue -u jjyeung -n a15_cot_ap7e24afacbc -o '%i %T %N %R'
