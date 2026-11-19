python3 - <<'PY'
import tarfile,difflib
J='/project/community/jjyeung/okh7'
names=['student_pilot/carrier_c1.py','student_pilot/carrier_c1_data.py','student_pilot/carrier_c1_routing.py','student_pilot/carrier_c1_run.py']
def get(f,mode):
    out={}
    with tarfile.open(fileobj=f,mode=mode) as t:
        for m in t:
            n=m.name.lstrip('./')
            if n in names: out[n]=t.extractfile(m).read().decode()
    return out
a=get(open(J+'/x_07ca49df/k/t_b01ce449beffe35b.tar','rb'),'r|')
with tarfile.open(J+'/h_6ed2c7aa/m400/s.tar') as s:
    b=get(s.extractfile('files/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/t_b83a8a35d420815b.tar'),'r|')
for n in names:
    d=list(difflib.unified_diff(a[n].splitlines(),b[n].splitlines(),'168872/'+n,'b83a8a35/'+n,n=1,lineterm=''))
    print('#####',n,len(d))
    print('\n'.join(d[:400]))
PY
