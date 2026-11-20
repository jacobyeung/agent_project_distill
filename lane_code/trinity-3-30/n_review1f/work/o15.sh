cd /project/community/jjyeung/okh7/x_22c714e1/u && sha256sum e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536 && nice -n 10 python3 -I -s -B - <<'PY'
import tarfile,re
t=tarfile.open('e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536')
names=[m.name for m in t.getmembers() if m.isfile()]
print('files',len(names),'student_pilot py',sum(1 for n in names if '/student_pilot/' in n or n.startswith('student_pilot/')))
print('extent files',[n for n in names if 'extent' in n.lower()])
for n in names:
    if n.endswith('student_pilot/carrier_c1_run.py') or n.endswith('student_pilot/s1_routing.py'):
        s=t.extractfile(n).read().decode().split('\n')
        print('@@',n,len(s),'extent lines',[i+1 for i,l in enumerate(s) if 'extent' in l.lower()])
        if n.endswith('carrier_c1_run.py'):
            for i,l in enumerate(s):
                if re.match(r'\s+def row\(self, stream, index\)',l): print('\n'.join(f'{j+1}: {s[j]}' for j in range(i,i+11)))
PY
