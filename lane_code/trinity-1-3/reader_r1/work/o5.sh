set -euo pipefail
P=/project/community/jjyeung/e09e45fda45db
cd "$P"
test ! -e a/c
nohup env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape09e45fda45db --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c" > "$P/a/cpu_check.log" 2>&1 < /dev/null &
echo started $!
sleep 20
TZ=UTC squeue -u $USER -p general -o '%i %j %T %M %l %R'
tail -5 "$P/a/cpu_check.log"
