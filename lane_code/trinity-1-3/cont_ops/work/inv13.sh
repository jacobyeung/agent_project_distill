cd /tmp
TZ=UTC sbatch --test-only -p general -c 32 --mem=800G -t 06:00:00 --no-requeue -J a15_cot_ap5d0c1e7f -o /dev/null --wrap 'true' 2>&1 | tail -2
TZ=UTC sbatch --test-only -p general --gres=gpu:1 -c 32 --mem=800G -t 06:00:00 --no-requeue -J a15_cot_ap5d0c1e7f -o /dev/null --wrap 'true' 2>&1 | tail -2
TZ=UTC sbatch --test-only -p advanced --nodes=1 --gpus-per-node=4 -c 48 --mem=800G -t 24:00:00 --no-requeue -J a15_cot_ap5d0c1e7f -o /dev/null --wrap 'true' 2>&1 | tail -2
TZ=UTC squeue -p general,advanced -o '%i %u %P %T %M %l %b' | head -30
/usr/bin/python3 --version
df -h /project/community | tail -1
