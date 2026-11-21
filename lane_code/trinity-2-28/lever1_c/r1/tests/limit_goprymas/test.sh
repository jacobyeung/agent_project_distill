#!/bin/bash
ulimit -S -f 512
trap 'r=$?; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_goprymas/21' ERR
trap 'r=$?; trap - ERR EXIT; printf "%s %s %s\n" "$r" "$LINENO" "${SLURM_JOB_ID:-0}" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_goprymas/21; exit "$r"' EXIT
exec >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_goprymas/19 2>>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_goprymas/24
set -Eeuo pipefail
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import os,resource,signal,sys
assert resource.getrlimit(resource.RLIMIT_FSIZE)[0]==524288
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
f=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT,0o600)
try:
 for _ in range(256):os.write(f,b'"'"'x'"'"'*8192)
except OSError:pass
else:raise AssertionError('"'"'limit absent'"'"')
' /scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_goprymas/26
