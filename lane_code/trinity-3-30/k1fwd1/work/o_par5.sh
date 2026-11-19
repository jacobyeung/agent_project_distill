D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
TZ=UTC sacct -j 173343 -X -n --format=State,Elapsed,End,ExitCode
ls -la 944b6b6a8f8d8c7f/173343/*/ 2>/dev/null | grep -v total; cat 944b6b6a8f8d8c7f/a.json 2>/dev/null; echo
N=$(ls -t 944b6b6a8f8d8c7f/173343/a*/result.tar.gz 2>/dev/null | head -1)
if [ -n "$N" ]; then O=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170235/ad2472b1be07d4193/result.tar.gz
 timeout 900 /usr/bin/python3 -I -s -B parity.py $O $N $D/PARITY_544.json; cat $(dirname $N)/EXIT.json; echo
 tar xzOf $N metadata/budget.json; tar xzOf $N COMPLETE.json 2>/dev/null; tar tzf $N | grep -c own.npz; tar xzOf $N native/probe/STOP 2>/dev/null
 python3 -c "
import json;p=json.load(open('$D/PARITY_544.json'));print([(r['capture'],r['depth']['max_rel'],r['gravity']['max_rel']) for r in p['rows'][:8]])"
fi
TZ=UTC squeue -u $USER -o "%i %j %P %T %M %N %R"
