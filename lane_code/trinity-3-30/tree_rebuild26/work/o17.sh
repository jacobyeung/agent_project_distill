export TZ=UTC; date -u +%TZ; sinfo -h -o "%P %a %l %D %G" | sort -u | head -12
for p in general preempt; do for m in 32G 8G; do echo "$p $m: $(sbatch --test-only -p $p --gres=gpu:1 --cpus-per-task=2 --mem=$m -t 00:10:00 --wrap 'true' 2>&1 | tail -1)"; done; done
squeue -p general -h -o "%i %u %T %b %R" | head -8
