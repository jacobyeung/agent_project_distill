import base64
p='/scratch/jjyeung/orch_n30/swarm_build/work/prompts/'
b=base64.b64encode(open(p+'sb_ktfix4.md','rb').read()).decode()
s=f'''R=/scratch/jjyeung/orch_n30
echo {b} | base64 -d > $R/sb_ktfix2/prompts/sb_ktfix4.md
printf 'sb_ktfix4:sb_ktfix2\\n' >> $R/sb_queue/queue.txt; cat $R/sb_queue/queue.txt | tr "\\n" " "; echo
'''
open('/scratch/jjyeung/orch_n30/swarm_build/work/sh/w59.sh','w').write(s)
