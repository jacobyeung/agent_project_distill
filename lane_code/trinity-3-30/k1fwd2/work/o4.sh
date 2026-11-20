set -e
D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
sha256sum 985f082abb9ff856.sh new_boundaries.py k1fwd1_boundaries.py
A=$(/usr/local/bin/sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap985f082abb9ff856 985f082abb9ff856.sh)
echo "cpu=$A $(date -u +%T)"; sleep 5; TZ=UTC squeue -j $A -o '%i %j %P %T %R'
