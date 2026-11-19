set -e
D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
test "$(sha256sum 944b6b6a8f8d8c7f.sh | cut -c1-64)" = 3f848683956aebd53857e827d4a3bd51e7759c500224465195029ba3ccd2ba2a
TZ=UTC squeue -u $USER -o '%i %j %P %T %N %R'
J=$(/usr/local/bin/sbatch --parsable --account=mt01 --partition=advanced --qos=adv_4gpu_qos --nodelist=orchard-community-1 --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=01:30:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap944b6b6a8f8d8c7f 944b6b6a8f8d8c7f.sh)
echo "P544=$J $(date -u +%T)"; sleep 3; TZ=UTC squeue -j $J -o '%i %j %P %T %N %R'
