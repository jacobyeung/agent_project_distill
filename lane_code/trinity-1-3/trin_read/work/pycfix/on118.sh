cd /scratch/jjyeung/orch_n30/trin_read/build || exit 1
/usr/bin/python3 -B trinity_read.py selfcheck --root ../root --bwrap /usr/bin/bwrap > ../work/selfcheck_118_t3b.json 2>/dev/null; echo selfcheck_rc=$?
python3 -c "import json;d=json.load(open('../work/selfcheck_118_t3b.json'));print(d['passed'],{k:v.get('passed') for k,v in d['checks'].items()},len(d['checks']['pieces'].get('errors',[])),sum(1 for f in d['portability']['findings'] if f.get('fails')))"
