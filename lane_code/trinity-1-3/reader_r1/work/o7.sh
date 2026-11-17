set -euo pipefail
P=/project/community/jjyeung/e09e45fda45db
cd "$P"
test ! -e a/c || { echo "a/c exists"; ls -la a/c; }
mv a/cpu_check.log a/cpu_check_cancelled_170853.log
nohup env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape09e45fda45db --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c" > "$P/a/cpu_check.log" 2>&1 < /dev/null &
sleep 30
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %R' | grep -v -E "jjy_"
tail -5 "$P/a/cpu_check.log"
