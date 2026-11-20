#!/bin/bash
bash /scratch/jjyeung/orch_n30/n_ops8/work/wait.sh ${1:-590} | grep -v -E "^2026[0-9T]*Z rc=2 .*PROJECT_DISK<150G$|^03:13:37Z|^NEW ALERTS"
