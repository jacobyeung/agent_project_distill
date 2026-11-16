export TZ=UTC
date -u
for p in advanced general; do echo "== $p"; printf '#!/bin/bash\ntrue\n' | sbatch --test-only --account=mt01 --partition=$p --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=02:00:00 --job-name=a15_cot_aptest 2>&1; done
squeue -j 169991 -o "%.10i %.8T %.20S %R"
squeue -p advanced -o "%.10i %.10u %.10T %.10M %b %R" | head -20
