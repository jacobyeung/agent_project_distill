#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=256G
#SBATCH --time=48:00:00
set -eu
umask 077
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""
ulimit -v 251658240
exec python3 -I -s -B b/a.py q "$1" "$2"
