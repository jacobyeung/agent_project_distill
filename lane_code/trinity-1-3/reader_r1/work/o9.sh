set -euo pipefail
umask 077
export TZ=UTC
D=/project/community/jjyeung/okh7/2ff0cebc
P=/project/community/jjyeung/c3cc59fb4aae0
printf '%s  %s\n' 741a362d5abd06124f3cff004123396ba43e8446e51883f0af955455f4b40d97 "$D/1.tgz" | sha256sum -c -
test ! -e "$P"
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00 > /dev/null
python3 -c "import json;c=json.load(open('2.json'));print('META',c['passed'],c['plan'][:12],c['package'][:12],c['inputs'][:12],c['time'])"
test ! -e a/c
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apc3cc59fb4aae0 --cpus-per-task=8 --mem=200G --no-requeue \
  --time=04:00:00 --export=ALL --output="$P/a/cpu_check.log" --chdir=/tmp \
  --wrap="/usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c"
sleep 30
squeue -u $USER -o '%i %j %P %T %M %l %R' | grep -v -E "jjy_"
tail -5 "$P/a/cpu_check.log" 2>/dev/null || true
