D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
TZ=UTC sacct -j 173484 -X -n --format=State,Elapsed,End,ExitCode
ls -la 985f082abb9ff856/173484/cpu 2>/dev/null
for f in 985f082abb9ff856/173484/cpu/a04.json 985f082abb9ff856/173484/cpu/failure.json; do [ -f $f ] && cat $f; done
[ -f 985f082abb9ff856/173484/cpu/CPU_CHECK.json ] && /usr/bin/python3 -c "
import json;d=json.load(open('985f082abb9ff856/173484/cpu/CPU_CHECK.json'));print(d.get('passed'),d.get('plan'),json.dumps(d.get('prepared'))[:300]);print(list(d))"
[ -f 985f082abb9ff856/173484/cpu/a.log ] && tail -5 985f082abb9ff856/173484/cpu/a.log | cut -c1-300
TZ=UTC squeue -w orchard-community-1 -o '%i %j %u %T %M %l %b %P'; scontrol show node orchard-community-1 | grep AllocTRES
