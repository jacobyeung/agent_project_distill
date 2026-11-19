J=/project/community/jjyeung/okh7
S=$J/h_6ed2c7aa/m400/s.tar
python3 - <<'PY'
import tarfile,hashlib,io,json
def inv(f):
    out={}
    with tarfile.open(fileobj=f,mode='r|') as t:
        for m in t:
            if m.isfile():
                out[m.name.lstrip('./')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
    return out
J='/project/community/jjyeung/okh7'
a=inv(open(J+'/x_07ca49df/k/t_b01ce449beffe35b.tar','rb'))
with tarfile.open(J+'/h_6ed2c7aa/m400/s.tar') as s:
    m=s.getmember('files/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/t_b83a8a35d420815b.tar')
    b=inv(s.extractfile(m))
print('files', len(a), len(b))
only_a=sorted(set(a)-set(b)); only_b=sorted(set(b)-set(a)); diff=sorted(k for k in set(a)&set(b) if a[k]!=b[k])
print('only_168872', len(only_a), only_a[:30]); print('only_b83', len(only_b), only_b[:40]); print('changed', len(diff)); print('\n'.join(diff))
json.dump(dict(a=a,b=b),open('/tmp/k1fwd_treeinv.json','w'))
PY
