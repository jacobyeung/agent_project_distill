#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=general
#SBATCH --gres=gpu:1
#SBATCH --time=07:00:00
set -euo pipefail
: "${READ_CODE:?set the staged code directory}"
: "${READ_ASSETS:?set the local asset manifest}"
: "${READ_ROOT:?set the private local root}"
: "${READ_CONFIG:?set the packet configuration path}"
exec nice -n 10 /usr/bin/python3 -s -B "$READ_CODE/orchard.py" --config "$READ_CONFIG" --assets "$READ_ASSETS" --root "$READ_ROOT"
