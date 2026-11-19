export P=/project/community/jjyeung/okh7/a15_cot_apdd92e95963089 T=02:20:00
# Run on Orchard login after placement/fill. T must match the sealed build walltime.
set -euo pipefail
umask 077
: "${P:?Set P to /project/community/jjyeung/okh7/a15_cot_ap<token>}"
: "${T:?Set T to the package sealed walltime HH:MM:SS}"
[[ "$P" =~ ^/project/community/jjyeung/okh7/a15_cot_ap[0-9a-f]+$ ]]
[[ "$T" =~ ^[0-9]{2}:[0-5][0-9]:[0-5][0-9]$ ]]
test "$(cat "$P/a/1.txt")" = 0
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time "$T"
test ! -e "$P/a/4.txt"
test ! -e "$P/a/c"
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES=  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1  --job-name="${P##*/}" --cpus-per-task=8 --mem=200G --time="$T"  --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue --chdir=/tmp  --output="$P/a/4.log" --error="$P/a/4.err"  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s
' "$CPU_JOB" > "$P/a/4.txt"
cat "$P/a/4.txt"

echo CPUJOB $(cat $P/a/4.txt)
