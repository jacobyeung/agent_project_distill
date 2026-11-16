export TZ=UTC; date -u +%FT%TZ
[ -n "$(squeue -u jjyeung -p general -h -o %i)" ] && { echo "REFUSE: job of ours on general"; exit 9; }
J=$(sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:10:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apc9f6b9ac93a6 /project/community/jjyeung/okh7/db3954b2/bin/egress.sh); echo "JOB $J rc $?"
sleep 5; squeue -j $J -h -o '%i %j %T %S %r'
