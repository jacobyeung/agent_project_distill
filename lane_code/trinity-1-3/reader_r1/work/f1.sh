set -uo pipefail
export TZ=UTC
P=/project/community/jjyeung/e09e45fda45db
cd "$P"
JOB=$(<a/8.txt); echo JOB $JOB
sacct -j $JOB -n -o JobID,State,Elapsed,ExitCode,NodeList | head
RET=e09e45fda45db$(printf '%08x' $JOB); echo RET $RET
ls -la /project/community/jjyeung/okh7/ae71c903/$RET 2>&1 | head
test -e a/f && echo "a/f EXISTS" || /usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f" 2>&1 | tail -15
ls -la a/f 2>&1
cat a/f/EXIT.json 2>/dev/null | head -c 3000; echo
tar tzf a/f/0.tgz 2>/dev/null | head -40
