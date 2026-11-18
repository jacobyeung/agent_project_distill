#!/bin/bash
# Usage: gen_submit_a2.sh ANON_OK.json TOKEN > submit_a2.sh  (upload a3, install ANON_OK in x_8417c021, a.py gate, test-only, submit)
set -euo pipefail
A=$(readlink -f "$1"); TOK=$2; B=/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5a3
cat <<'HDR'
set -uo pipefail
export TZ=UTC; O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_8417c021
date -u +%FT%TZ
[ ! -e $IN/a3 ] && [ ! -e $O/r/4d3cd40e ] && [ -f $IN/m.tar ] || { echo "precondition failed: a3 or root exists, or m.tar absent"; exit 3; }
mkdir -p $IN/a3
base64 -d > $IN/a3/.bundle.tar <<'B64'
HDR
(cd $B && tar cf - a3) | base64
echo B64
echo 'tar xf $IN/a3/.bundle.tar -C $IN && chmod 755 $IN/a3/ja2.sh $IN/a3/s2.sh'
echo "(cd \$IN && sha256sum -c) <<'SUMS' || { echo 'a3 sums differ'; exit 3; }"
cat $B/bundle.SHA256SUMS
echo SUMS
echo '[ -e $KH/ANON_OK.json ] && mv $KH/ANON_OK.json $KH/o/ANON_OK.placeholder.json'
echo "cat > \$KH/ANON_OK.json <<'J'"; cat "$A"; echo J
cat <<TAIL
chmod 600 \$KH/ANON_OK.json; sha256sum \$KH/ANON_OK.json \$KH/SHA256SUMS.txt
cd \$IN && /usr/bin/python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1] + "/b"); import a; c = a.main(sys.argv[1]); print("a.py PASS", c["status"])' \$KH 2>&1 | tail -2 | tee /dev/stderr | grep -q "a.py PASS CLEAN" || { echo "a.py gate failed"; exit 3; }
squeue -u \$USER -p general -o '%i %j %T %S' 2>&1
cd \$IN && sbatch --test-only -J $TOK -o /dev/null -e \$KH/o/%j.err a3/ja2.sh 2>&1 | tail -2
cd \$IN && sbatch -J $TOK -o /dev/null -e \$KH/o/%j.err a3/ja2.sh 2>&1
sleep 20; squeue -u \$USER -p general -o '%i %j %T %S %l %C %m' 2>&1
TAIL
