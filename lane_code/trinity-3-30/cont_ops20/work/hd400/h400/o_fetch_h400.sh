set -euo pipefail; umask 077
P=/project/community/jjyeung/okh7/a15_cot_apd7a6db629db02; cd $P; JOB=$(cat a/8.txt); [[ "$JOB" =~ ^[0-9]+$ ]]
RET=d7a6db629db02$(printf '%08x' $JOB); echo RET $RET
/usr/bin/python3 -I -s -B a/7.py --package $P --return-token $RET --out $P/a/f
head -c 700 a/f/EXIT.json; echo; for f in a/x*; do echo "== $f"; head -3 $f; done
SP=/project/community/jjyeung/okh7/ae71c903; test -d $SP/$RET && ! test -e ${SP}_fetched/$RET && mv $SP/$RET ${SP}_fetched/$RET && echo "moved $RET"
du -sb $P
