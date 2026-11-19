set -e
D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
sha256sum 944b6b6a8f8d8c7f.sh f67f0b1118da0677.sh
A=$(/usr/local/bin/sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap944b6b6a8f8d8c7f 944b6b6a8f8d8c7f.sh)
B=$(/usr/local/bin/sbatch --parsable --dependency=afterany:$A --account=mt01 --partition=preempt --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apf67f0b1118da0677 f67f0b1118da0677.sh)
echo "cpu544=$A cpu400=$B"; TZ=UTC squeue -j $A,$B -o '%i %j %P %T %R'
