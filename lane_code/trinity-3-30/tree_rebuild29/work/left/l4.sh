export TZ=UTC; date -u +%TZ; head -1 ~/a15o/l.sh
for N in orchard-community-3 orchard-community-2; do sbatch -p preempt -w $N -N1 -n1 -c2 --mem=2G -t 00:08:00 --job-name a15_cot_apb2a413982c51 -o ~/a15o/$N.out ~/a15o/l.sh; done
