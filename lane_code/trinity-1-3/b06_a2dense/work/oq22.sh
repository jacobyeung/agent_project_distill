export TZ=UTC; date -u +%FT%TZ
[ -n "$(squeue -u jjyeung -p general -h -o %i)" ] && { echo "REFUSE: job of ours on general"; exit 9; }
J=$(sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=64G --time=04:00:00 --array=0-5%1 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap7128842a8567 --wrap 'K=$([ $SLURM_ARRAY_TASK_ID -lt 3 ] && echo a || echo v); /project/community/jjyeung/okh7/db3954b2/bin/djob.sh $K $((SLURM_ARRAY_TASK_ID % 3)) 3 16'); echo "JOB $J rc $?"
sleep 20; squeue -j $J -h -o '%i %j %T %S %r %N'
