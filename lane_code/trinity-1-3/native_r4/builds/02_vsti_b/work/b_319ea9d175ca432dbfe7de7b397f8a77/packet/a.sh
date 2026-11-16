#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=general
#SBATCH --gres=gpu:h100:1
#SBATCH --time=07:00:00
#SBATCH --job-name=a15_cot_ap123456789abcdef012345678
#SBATCH --output=/scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/b_319ea9d175ca432dbfe7de7b397f8a77/packet/a.log
set -euo pipefail
exec /usr/bin/python3 -s -B /scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/b_319ea9d175ca432dbfe7de7b397f8a77/packet/o.py run --config /scratch/jjyeung/orch_n30/native_r4/builds/02_vsti_b/work/b_319ea9d175ca432dbfe7de7b397f8a77/packet/a.json
