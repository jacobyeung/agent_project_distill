#!/bin/bash
exec > >(/usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/27.py /scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/20 /scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/22) 2>&1
A_PID=$!
ulimit -S -f 512
trap 'r=$?; printf "%s %s\n" "$r" "$LINENO" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/21' ERR
trap 'r=$?; trap - ERR EXIT; printf "%s %s\n" "$r" "$LINENO" >>/scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/21; exec 1>&- 2>&-; wait "$A_PID"; exit "$r"' EXIT
set -Eeuo pipefail
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import os,resource,signal,sys
assert resource.getrlimit(resource.RLIMIT_FSIZE)[0]==524288
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
f=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT,0o600)
try:
 for _ in range(256):os.write(f,b'"'"'x'"'"'*8192)
except OSError:pass
else:raise AssertionError('"'"'limit absent'"'"')
' /scratch/jjyeung/orch_n30/lever1_c/r1/tests/limit_mgtviqxj/26
