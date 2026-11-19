D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D
TZ=UTC sacct -j 173339,173340 -X -n --format=JobID,State,Elapsed,NodeList%22,ExitCode
for j in 944b6b6a8f8d8c7f/173339 f67f0b1118da0677/173340; do echo "== $j"; ls $j $j/cpu 2>/dev/null; for f in $j/cpu/failure.json $j/cpu/a04.json; do [ -f $f ] && cat $f; done; [ -f $j/cpu/a.log ] && tail -c 1500 $j/cpu/a.log; [ -f $j/cpu/CPU_CHECK.json ] && python3 -c "import json;d=json.load(open('$j/cpu/CPU_CHECK.json'));print(d['passed'],d['prepared'],d['binding'].get('manifest_sha256'),d['verified_sources'])"; done
ls 944b6b6a8f8d8c7f/173339/*/ 2>/dev/null | head
