set -euo pipefail; export TZ=UTC
(
D=/project/community/jjyeung/okh7/7b422049
set -euo pipefail
umask 077
P=/project/community/jjyeung/b9ef552934627
printf '%s  %s\n' 57d2a513b6770447680fc088a39fd02c00945491bdde46309e9ade0c84540f3e "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
python3 -c "import json;c=json.load(open(\"2.json\"));print(\"META1\",c[\"passed\"],c[\"plan\"][:12],c[\"time\"])"
test ! -e a/c
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apb9ef552934627 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue \
  --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" \
  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$CPU_JOB" > "$P/a/4.txt"
echo CPU1 $CPU_JOB
)
(
D=/project/community/jjyeung/okh7/cbb7b4dd
set -euo pipefail
umask 077
P=/project/community/jjyeung/f40065df28aa3
printf '%s  %s\n' 89cb14a499609741233996e4023e235901849232a3aa92a7637d252108878990 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
python3 -c "import json;c=json.load(open(\"2.json\"));print(\"META2\",c[\"passed\"],c[\"plan\"][:12],c[\"time\"])"
test ! -e a/c
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apf40065df28aa3 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue \
  --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" \
  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$CPU_JOB" > "$P/a/4.txt"
echo CPU2 $CPU_JOB
)
sleep 20; squeue -u $USER -o "%i %j %P %T %M %R" | grep -v jjy_
