echo "== $(hostname -s) $(date -u +%T)"
W=/scratch/jjyeung/orch_n30
grep -n -E "sha256|SHA|\.json|path|Path\(|open\(" $W/sb_alias2/work/audit.py | cut -c1-260 | head -60
cat $W/sb_alias2/work/VALIDATION.json | head -c 1000
