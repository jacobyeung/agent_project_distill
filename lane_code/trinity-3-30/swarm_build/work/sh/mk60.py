import base64
p='/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
e=lambda f: base64.b64encode(open(p+f,'rb').read()).decode()
s=f'''R=/scratch/jjyeung/orch_n30
echo {e('sb_fhalias2.md')} | base64 -d > $R/sb_fhalias/prompts/sb_fhalias2.md
echo {e('sb_fullinv2.md')} | base64 -d > $R/sb_fullinv/prompts/sb_fullinv2.md
echo {e('sb_ph2gate3.md')} | base64 -d > $R/sb_ph2fix/prompts/sb_ph2gate3.md
printf 'sb_fhalias2:sb_fhalias\\nsb_fullinv2:sb_fullinv\\nsb_ph2gate3:sb_ph2fix\\n' >> $R/sb_queue/queue.txt; cat $R/sb_queue/queue.txt | tr "\\n" " "; echo; tail -1 $R/sb_queue/codexq.log
'''
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w60.sh','w').write(s)
