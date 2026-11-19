set -euo pipefail; umask 077
P=/project/community/jjyeung/okh7/a15_cot_apdc863c3e6b41d; cd $P; JOB=$(cat a/8.txt); [[ "$JOB" =~ ^[0-9]+$ ]]
RET=dc863c3e6b41d$(printf '%08x' $JOB); echo RET $RET
/usr/bin/python3 -I -s -B a/7.py --package $P --return-token $RET --out $P/a/f
head -c 700 a/f/EXIT.json; echo; for f in a/x*; do echo "== $f"; head -3 $f; done
du -sb $P
