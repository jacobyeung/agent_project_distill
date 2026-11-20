set -e
D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
test "$(sha256sum 985f082abb9ff856.sh | cut -c1-64)" = d11d0ba8f47391c7cfd44067e7acd4f9c7b17c2d5d6852e61d060bafa0947074
TZ=UTC squeue -u $USER -o '%i %j %P %T %N %R'
J=$(/usr/local/bin/sbatch --parsable --account=mt01 --partition=advanced --qos=adv_4gpu_qos --nodelist=orchard-community-1 --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=02:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap985f082abb9ff856 985f082abb9ff856.sh)
echo "GPU=$J $(date -u +%T)"; sleep 20; TZ=UTC squeue -j $J -o '%i %j %P %T %N %R %S'
