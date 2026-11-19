#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
set -eu
umask 077
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
ulimit -v 188743680
exec python3 -I -s -B b/a.py q "$1" "$2"
