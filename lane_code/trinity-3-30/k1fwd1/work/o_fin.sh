D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5/f67f0b1118da0677; cd $D
TZ=UTC sacct -j 173346 -X -n --format=State,Elapsed,Start,End,ExitCode; cat a.json; echo
R=173346/afb7cac2552774e1b; ls -la $R; cat $R/EXIT.json; echo
N=$R/result.tar.gz; tar tzf $N | awk -F/ '{print $1"/"$2}' | sort | uniq -c | head; tar tzf $N | grep -c own.npz; tar tzf $N | grep -c PHASE_COMPLETE
tar xzOf $N COMPLETE.json; tar xzOf $N metadata/budget.json; tar xzOf $N native/probe/STOP 2>/dev/null; echo
d=$(tar tzf $N | grep PHASE_COMPLETE | head -1); tar xzOf $N $d | python3 -c "import json,sys;p=json.load(sys.stdin);print({k:v for k,v in p.items() if k!='sources'}); print([k for k in p['sources'] if 'student_pilot' in k][:3])"
tar xzOf $N native/probe/TOKENS.json | python3 -c "import json,sys;t=json.load(sys.stdin);v=[x['seconds'] for x in t.values()];print(len(v),min(v),sum(v)/len(v),max(v))"
tar tzvf $N | awk '{s+=$3} END {print "uncompressed", s}'
