#!/usr/bin/env bash
mount --bind /scratch/jjyeung/orch_n30/sb_ktchk/work/plant /scratch/jjyeung/orch_n30/sb_ktfix2 && cd /scratch/jjyeung/orch_n30/sb_ktfix2 && bash scripts/cpu.sh /scratch/jjyeung/orch_n30/sb_ktchk/work/rows_probe.py
ls /scratch/jjyeung/orch_n30/sb_ktfix2/out/looks 2>&1 | head -2
