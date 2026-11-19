set -e
D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
test "$(sha256sum f67f0b1118da0677.sh | cut -c1-64)" = 3a9e6fa71e4fc146aa11d87bfcd9be937196ba2c57aeea5493895aa1012c0f3e
J=$(/usr/local/bin/sbatch --parsable --dependency=afterok:173343 --account=mt01 --partition=advanced --qos=adv_4gpu_qos --nodelist=orchard-community-1 --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=03:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apf67f0b1118da0677 f67f0b1118da0677.sh)
echo "P400=$J $(date -u +%T)"; sleep 2; TZ=UTC squeue -u $USER -o '%i %j %P %T %M %N %R'
