from pathlib import Path
L=Path.cwd();D=L/'work/build24m4q'
s=(L/'work/build24m4n/rcj_tests.py').read_text().replace("D/'p_tree/launch_s1/b/s.py'","L/'work/build24m4m/rcj_l/p_tree/launch_s1/b/s.py'")
s=s.replace("assert str(e)=='fixture' and seen", "assert str(e)=='fixture' and not seen and J.load(root/'build.json')['status']=='REFUSE'")
s=s.replace('published_before_raise=True','build_receipt_before_raise=True').replace('independent publication before raise','independent publication and build receipt before raise')
(D/'core_tests.py').write_text(s)
for name,source in [('mount_tests.py','work/build24m4m/mount_tests.py'),('recorder_tests.py','work/build24m4o/recorder_tests.py')]:
 (D/name).write_bytes((L/source).read_bytes())
