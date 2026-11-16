import sys,json,shlex
sys.path[:0]=['/scratch/jjyeung/orch_cd/evalx/work/milestone/orchard_native','/scratch/jjyeung/orch_cd/evalx/work/milestone']
import native_common as C, native_launcher as N
config=C.load(sys.argv[1]+'/CONFIG.json')
cmd=N.submit_command(config)
open(sys.argv[1]+'/SUBMIT_COMMAND.txt','w').write(shlex.join(cmd))
print(cmd[-1])
