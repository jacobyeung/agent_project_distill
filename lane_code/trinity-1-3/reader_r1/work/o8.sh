set -euo pipefail
P=/project/community/jjyeung/e09e45fda45db
cd "$P"
test ! -e a/c
mv a/cpu_check.log a/cpu_check_srun_refused.log
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape09e45fda45db --cpus-per-task=8 --mem=200G --no-requeue \
  --time=04:00:00 --export=ALL --output="$P/a/cpu_check.log" --chdir=/tmp \
  --wrap="/usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c"
sleep 30
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %R' | grep -v -E "jjy_"
tail -5 "$P/a/cpu_check.log" 2>/dev/null || true
