timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
K=/scratch/jjyeung/orch_n30/sb_ktfix2; sed -n 66,116p $K/code/runner.py | cut -c1-260; grep -n -E "grant|reservation" $K/code/*.py | grep -v test | head -12 | cut -c1-220; cat $K/scripts/run_A.sh
Y
