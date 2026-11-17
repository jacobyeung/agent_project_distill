#!/bin/bash
# Orchard login node, run under setsid nohup: empty-root CPU restore check of bf94a7976a7e9 on general (CPU only)
P=/project/community/jjyeung/bf94a7976a7e9
echo "start $(date -u +%TZ)" >> $P/a/cpu.log
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" TZ=UTC \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_ap5307e38583 \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" --results "$P/a/c" >> $P/a/cpu.log 2>&1
echo "srun rc=$? $(date -u +%TZ)" >> $P/a/cpu.log
