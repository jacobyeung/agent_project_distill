import base64
p='/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
b=base64.b64encode(open(p+'sb_ph2fix2.md','rb').read()).decode()
s=f'''R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p
mkdir -p $R/sb_ph2fix/prompts
echo {b} | base64 -d > $R/sb_ph2fix/prompts/sb_ph2fix2.md
printf 'sb_ph2fix2:sb_ph2fix\\n' >> $R/sb_queue/queue.txt; cat $R/sb_queue/queue.txt | tr "\\n" " "; echo
'''
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w57.sh','w').write(s)
