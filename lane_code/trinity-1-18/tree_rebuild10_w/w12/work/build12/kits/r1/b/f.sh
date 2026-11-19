#!/bin/bash
set -eu
umask 077
export CUDA_VISIBLE_DEVICES=""
exec python3 -I -s -B b/a.py p "$1"
