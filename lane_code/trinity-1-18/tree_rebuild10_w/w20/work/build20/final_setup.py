from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build20'
for name in ('suite19.py','packet19.py','packet_inputs19.py','storage19.py','configuration19.py'):
    s=(L/'work/build19'/name).read_text().replace('work/build19','work/build20').replace('Build 19','Build 20')
    if name=='suite19.py':s=s.replace("'work/build20/inputs',", "'work/build20/inputs','work/build19/inputs',")
    (B/name.replace('19','20')).write_text(s)
s=(L/'work/build19/final_checks19.py').read_text().replace('work/build19','work/build20').replace('test19.py','test20.py').replace('B19_PROOF','B20_PROOF')
s=s.replace("['tests.test_r1_build19'", "['tests.test_r1_build20','tests.test_r1_build19'")
start=s.index(" ('preservation'");end=s.index('records=[]')
s=s[:start]+']\n'+s[end:]
(B/'focused.py').write_text(s)
