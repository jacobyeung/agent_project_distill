D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
TZ=UTC sacct -j 173340,173343 -X -n --format=JobID,State,Elapsed,Start,NodeList%22,ExitCode
j=f67f0b1118da0677/173340; ls $j/cpu 2>/dev/null; [ -f $j/cpu/failure.json ] && cat $j/cpu/failure.json; cat $j/cpu/a04.json 2>/dev/null
[ -f $j/cpu/CPU_CHECK.json ] && python3 -c "
import json;d=json.load(open('$j/cpu/CPU_CHECK.json'));print(d['passed'],json.dumps(d['prepared'])[:600]);print(d['verified_sources'])"
python3 -c "import json;r=json.load(open('$j/cpu/a01.json'));print(json.dumps(r.get('closure'))[:500])" 2>/dev/null
tail -c 1200 $j/cpu/a.log 2>/dev/null
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %N %R'
