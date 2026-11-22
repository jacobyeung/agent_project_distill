export TZ=UTC; date -u +%TZ
sbatch -p preempt -w orchard-community-3 -N1 -n1 -c 8 --mem=32G -t 01:10:00 --no-requeue --job-name a15_cot_apc6b14e700ea2 -o ~/a15o/f23/main_%j.out ~/a15o/f23/job.sh
sleep 30; squeue -u jjyeung -h -o '%i|%j|%T|%N|%r|%M' | grep c6b14e; sprio -u jjyeung 2>/dev/null | head -8
for n in 2 3 4; do [[ -f ~/a15o/f23/p$n.out ]] && grep -v "error:" ~/a15o/f23/p$n.out; done
