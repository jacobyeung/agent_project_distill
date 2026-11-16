#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=general
#SBATCH --gres=gpu:h100:1
#SBATCH --time=07:00:00
#SBATCH --job-name=a15_cot_ap123456789abcdef012345678
#SBATCH --output=/dev/null
set -euo pipefail
exec /usr/bin/python3 -s -B /project/community/jjyeung/okh7/d9c35d0a/p/123456789abcdef012345678/o.py run --config /project/community/jjyeung/okh7/d9c35d0a/p/123456789abcdef012345678/a.json
