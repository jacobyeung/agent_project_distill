<!-- recovered by seal_plan: transcript=a97ad692 line=587 utc=2026-11-15T05:01:48.145Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; P=$R/evalx/work/milestone/native_package_s24_05; ls -la --time-style=+%H:%M:%S $P/uploads/code/ | cut -c20-140; echo "== limiter state"; cat /tmp/ratelimit-25409/614157.181747488.state 2>/dev/null | cut -c1-200; echo; ps -o pid,stat,etime -p 614156,614157 2>/dev/null; echo "== governor turn"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,time
s=json.load(open('/scratch/jjyeung/io_governor/slot_state.json'))
print('now',int(time.time()),'bounded_turn',s.get('bounded_turn'),'credit_owner',s.get('credit_owner'),'last_started',s.get('last_started'),'last_ended',s.get('last_ended'))
ws=s.get('wait_since',{}); k=[x for x in ws if ':614156:' in x or ':614157:' in x or ':614154:' in x]; print('our keys',k,[ws[x] for x in k])
"; echo "== master"; timeout 100 bash $R/orchard_kit/work/ossh.sh orchard 'true'; echo "ossh rc=$?"