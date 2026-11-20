from pathlib import Path
import shutil,sys
J=Path.cwd();D=J/'work/build24m4z5';W=J/'work/enospc5_final'
W.mkdir()
for p in (J/'work/enospc5').glob('*.py'):
 s=p.read_text().replace('work/enospc5/','work/enospc5_final/')
 (W/p.name).write_text(s)
helper=(J/'out/jn3.sh').read_text().split("<<'PYJ2'\n",1)[1].split('\nPYJ2',1)[0]
(W/'j2_helper_new.py').write_text(helper+'\n')
for name in ('bin','tmp','logs','mnt','mnt4','mnt5','node'):(W/name).mkdir()
shutil.copytree(J/'out/kit_n',W/'kit')
(W/'bin/python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(W/'runtime.py')+' "$@"\n');(W/'bin/python3').chmod(0o755)
for prefix in ('archive','current','legacy'):
 s=(D/(prefix+'_final_tests.py')).read_text().replace('enospc5/','enospc5_final/').replace('build24m4z5/'+prefix+'_final','build24m4z5/'+prefix+'_validated')
 (D/(prefix+'_validated_tests.py')).write_text(s)
 if prefix=='legacy':(D/'legacy_validated').mkdir()
s=(D/'e3_local.py').read_text().replace('build24m4z5/e3_verified','build24m4z5/e3_final')
(D/'e3_final.py').write_text(s)
s=(J/'work/build24m4z4/readback_final_test.py').read_text().replace('build24m4z4','build24m4z5').replace('e2_verified','e3_final').replace('e2','e3').replace('E2','E3').replace('==33','==41').replace('objects=16','objects=20').replace('serial_requests=32','serial_requests=40').replace('16 objects','20 objects')
(D/'readback_final_test.py').write_text(s)
s=(J/'work/build24m4z4/final_loop_test.py').read_text().replace('build24m4z4','build24m4z5').replace('archive_final_tests.py','archive_validated_tests.py').replace('build24m4z5/archive_final','build24m4z5/archive_validated')
s=s.replace("i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4)","i:i+5]==['stop','exports','logs','o','checkpoints'] for i in range(0,len(phases),5)").replace('len(phases)>=8','len(phases)>=10').replace('len(phases)//4','len(phases)//5')
(D/'final_loop_test.py').write_text(s)
print('Final fixtures ready')
