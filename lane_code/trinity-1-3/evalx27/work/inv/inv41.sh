export TZ=UTC
sinfo -p general -N -o "%N %T %C %G %m %e" 2>&1
squeue -p general -o "%.10i %.10u %.10T %.10M %.6D %b %R" | head -30
echo '#!/bin/bash
true' | sbatch --test-only --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=128G --time=02:00:00 --job-name=a15_cot_aptest 2>&1
echo '#!/bin/bash
true' | sbatch --test-only --account=mt01 --partition=general --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=02:00:00 --job-name=a15_cot_aptest 2>&1
