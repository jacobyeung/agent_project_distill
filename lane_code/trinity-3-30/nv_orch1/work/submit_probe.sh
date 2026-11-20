set +x
export TZ=UTC
chmod 700 /project/community/jjyeung/4f5e45fe5d74c
JID=$(sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=00:45:00 --requeue --export=PATH,HOME,USER,NVK_A,NVK_B,NVK_C,NVK_D --output=/project/community/jjyeung/4f5e45fe5d74c/log/%j.out --chdir=/tmp --job-name=a15_cot_apda683b7817 /project/community/jjyeung/4f5e45fe5d74c/kit/job.sh 240 probe)
unset NVK_A NVK_B NVK_C NVK_D
echo "submitted $JID"
sleep 5; squeue -j $JID -o '%i %j %P %T %M %R'
