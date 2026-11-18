set -uo pipefail
export TZ=UTC
P=/project/community/jjyeung/f40065df28aa3
cd "$P"
JOB=$(<a/8.txt); echo JOB $JOB
sacct -j $JOB -X -n -o JobID,State,Elapsed,ExitCode
RET=f40065df28aa3$(printf '%08x' $JOB); echo RET $RET
test -e a/f && echo "a/f EXISTS" || /usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f" 2>&1 | tail -5
ls -la a/f; sha256sum a/f/0.tgz a/f/EXIT.json; cat a/f/EXIT.json
