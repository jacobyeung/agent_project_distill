W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>/dev/null | grep -q tr20_b24m4q2 && { echo STILL_BUILDING; exit 0; }; P=$(ls $W/w24q2/out/tree_rebuild_b24m4q_*.tar); test -f $P.sha256 || { echo NO_SHA; exit 0; }; echo $P; cat $P.sha256; sha256sum $P | cut -c1-16
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4q2 | tail -1); head -c 1500 $d/final_message.md; echo; cat $W/w24q2/out/BUILD24M4Q_REPORT.md; echo ===; head -c 5000 $W/w24q2/out/CHAIN_24M4Q.md; echo; cat $W/w24q2/out/UPLOADS_24M4Q.list
base64 -d > $W/prompts/review24m4q.md <<'B64'
IyBEZWx0YSByZXZpZXcgKHJlYWQtb25seSwgb25jZSkgb2YgS0lUIGJ1aWxkIDI0bTRxMiBvZiBs
YW5lIHRyZWVfcmVidWlsZDogdGhlIENQVSBqb2IgcnVucyB0aGUgdHJhaW5pbmctdGltZSBwZXIt
cm93IGNoYWluIG92ZXIgYWxsIG9mIE4ncyByb3V0aW5nIHJvd3MsIGV4dGVudC1yZWNlaXB0IGNh
bmRpZGF0ZSwgcG9wdWxhdGlvbiBldmlkZW5jZSwgcHJvY2Vzc29yLWNoZWNrIG1vZGVsIHJvb3Qs
IHB1YmxpY2F0aW9uIGZpeGVzCgpZb3UgcmV2aWV3OyB5b3UgZG8gbm90IGZpeC4gUnVuIG9uY2Us
IHJlYWQtb25seSwgb24gdHJpbml0eS0xLTE4OyBub2JvZHkgYW5zd2VycyBxdWVzdGlvbnMuIFJl
cG9ydCBvbmx5IHZlcmlmaWVkIHByb2JsZW1zIHdpdGggZmlsZTpsaW5lIGFuZCBldmlkZW5jZS4g
RmluYWwgbWVzc2FnZSBpcyB0aGUgdmVyZGljdC4KCi0gQnVpbGQ6IGAvc2NyYXRjaC9qanlldW5n
L29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvdzI0cTIvYCAocHJvbXB0IGAvc2NyYXRjaC9qanll
dW5nL29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvcHJvbXB0cy9idWlsZDI0bTRxMi5tZGA7IG91
dC9CVUlMRDI0TTRRX1JFUE9SVC5tZCwgb3V0L0NIQUlOXzI0TTRRLm1kLCBvdXQvVVBMT0FEU18y
NE00US5qc29uLy5saXN0LCBvdXQvcmNqLykuIEJhc2U6IDI0bTRwIGAvc2NyYXRjaC9qanlldW5n
L29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvdzI0cC9gICh5b3VyIHJldmlldyBjb2RleF9ydW5z
LzIwMjYxMTIwVDEyMjQ1NVpfdHJlZV9yZWJ1aWxkX3JldjI0bTRwOiBHTyBBRlRFUiBGSVhFUywg
dGhyZWUgZmluZGluZ3MsIG5vdyB0byBiZSBmaXhlZCkuCi0gVmVyaWZ5OiAoMSkgeW91ciB0aHJl
ZSAyNG00cCBmaW5kaW5ncyBhcmUgZml4ZWQgKG5hdGl2ZSBmYW1pbHkgZm9yIHJvdXRpbmcgdHlw
ZXM7IGV4YWN0IFVQTE9BRFM7IGRvYyBsaW5lKTsgKDIpIHRoZSBjaGFpbiBzdGVwIGNhbGxzIHRo
ZSBsYXVuY2gga2l0J3Mgb3duIFJvd3Mucm93IGNoYWluIGNvZGUgYW5kIHBpbnMgKHdvcmRpbmcg
ZXhjbHVzaW9uLCB0ZXh0IGF1ZGl0LCBleHRlbnRzIHdpdGggTidzIHBpbm5lZCByZWNlaXB0LCBy
MV90cmFpbmluZy5yb3dfY2hlY2ssIHJlc2VydmUsIHIyIGFkbWlzc2lvbiBpZiBib3VuZCksIG5v
dCBhIHJlaW1wbGVtZW50YXRpb24sIG92ZXIgQUxMIE4gcm91dGluZyByb3dzOyBjaGFpbi5qc29u
IGdpdmVzIGNvdW50cyBieSBjaGVjay9yZXN1bHQsIHJvd3MgY2hlY2tlZCA9IERCIHJvd3MsIGZp
cnN0IHRlbiByZWZ1c2FscyBpbiBmdWxsOyBpdCBjaGFuZ2VzIG5vIGJ1aWxkL3JlZnVzYWwgc3Rh
dHVzOyAoMykgdGhlIGNhbmRpZGF0ZSBleHRlbnQgcmVjZWlwdCBpcyBidWlsdCBieSB0aGUgdHJl
ZSdzIG93biBidWlsZGVyLCBjYXJyaWVzIFAncyBlbnRyaWVzIGV4Y2VwdCBjb250ZW50X3NoYTI1
NiAoYm94IHN0YXR1c2VzLCByZXBhaXIgaGFzaCB1bmNoYW5nZWQpLCBpdHMgcWlkIHNldCA9IE4n
cyBwb29sIHFpZHMsIGNhbmRfY21wLmpzb24gY29tcGFyZXMgYm90aCwgYW5kIG5vdGhpbmcgcGlu
cyBvciB1c2VzIGl0IGluIGFueSBqb2I7ICg0KSBwb3B1bGF0aW9uIGV2aWRlbmNlIChjb3VudCAr
IGtleS1zZXQgc2hhMjU2IG9mIHRoZSBwcmVwYXJlZCBwb3B1bGF0aW9uIHZzIHRoZSBEQikgaXMg
Y29tcHV0ZWQgYnkgdGhlIGtpdCdzIG93biBwcmVwYXJhdGlvbiBjb2RlLCBvciB0aGUgcmVwb3J0
IHNheXMgaG9uZXN0bHkgd2hlcmUgbW9kZSByIHN0b3BzOyAoNSkgcGMucHkgY2hpbGRyZW4gYmlu
ZCBvbmx5IHRoZSBwcm9jZXNzb3IvdG9rZW5pemVyIG1ldGFkYXRhIHJlYWQtb25seSBhdCBlYWNo
IHNpZGUncyBsb2dpY2FsIG1vZGVsIHJvb3QsIGZyb20gc3RhZ2VkIGJ5dGVzIHBpbm5lZCBieSBo
YXNoLCBsb29zZW4gbm8gY29tcGFyaXNvbiwgbG9hZCBubyB3ZWlnaHRzOyB0aGUgdHdvIHJldjI0
bTRvMyBmaXhlcyAoZXhjZXB0aW9uIGxpbmU7IGJ1ZGdldCBjb3VudHMgbWV0YWRhdGEpOyAoNikg
Q0hBSU5fMjRNNFEubWQgYW5zd2VycyBvbiB0aGUgcGlubmVkIGV4dGVudCByZWNlaXB0LCByMV9o
YW5kb3ZlciByZWJpbmRpbmcsIGFuZCB3aGV0aGVyIHByZXBhcmF0aW9uIHJ1bnMgdGhlIGNoYWlu
IG92ZXIgZXZlcnkgcm93IG9mIGV2ZXJ5IHN0cmVhbSAoYW5kIHRoZSAyMCwwMDAtcm93IG90aGVy
LXN0cmVhbSBzYW1wbGVzIGlmIG5vdCkgYXJlIHN1cHBvcnRlZCBieSBmaWxlOmxpbmU7ICg3KSBD
JycgdW5jaGFuZ2VkOyBvbmx5IGludGVuZGVkIGtpdC9oZWxwZXIgZmlsZXMgZGlmZmVyOyBHTyBm
YWxzZSBleGNlcHQga2l0X25fZ287ICg4KSB3aGF0IHlvdSBkaWQgbm90IGNoZWNrLgoKUnVsZXM6
IFJlYWQtb25seS4gTm8gc3NoLCBuZXR3b3JrLCBHUFUsIEdpdCwgdG11eCwgc2NoZWR1bGVyIG9y
IGFub3RoZXIgYWdlbnQuIE5ldmVyIGxpc3QsIHNlYXJjaCBvciBncmVwIG9uIC9ob21lIG9yIC9k
YXRhKiAocmVhZCBvbmx5IHRoZSBuYW1lZCBmaWxlcyB0aGVyZSkuIG5pY2UgLW4gMTAsIGF0IG1v
c3QgOCB0aHJlYWRzLCB1bmRlciAyMCBHQiBSQU0uIEZpcnN0IGxpbmUgYEdPYCwgYEdPIEFGVEVS
IEZJWEVTYCBvciBgTk8tR09gOyBhdCBtb3N0IDE0IGxpbmVzLgo=
B64
tmux new-session -d -s tr20_rev24m4q "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24q2 $W/prompts/review24m4q.md --model gpt-6-astra --effort high --label tree_rebuild_rev24m4q --skip-git-check > $W/work/rev24m4q.log 2>&1"; sleep 5; tmux ls | grep tr20
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild20/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild20/$(basename $P) | cut -c1-16'"
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24m4q; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24m4q'
def entries(j):
    d=json.load(open(j)); out={}
    def walk(x):
        if isinstance(x,dict):
            if 'local_path' in x and ('name' in x or 'opaque_name' in x): out[x.get('name') or x.get('opaque_name')]=x
            else:
                for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(d); return out
final={}
for tag in ('24M4Q',):
    e=entries(W+'/w24q2/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24q2/out/UPLOADS_%s.list'%tag) if l.strip()]
    miss=[n for n in names if n not in e]
    print(tag,'list',len(names),'json',len(e),'missing',miss[:3])
    assert not miss, tag
    for n in names: final[n]=dict(e[n],tag=tag)
tot=0; sums=[]
for n,x in sorted(final.items()):
    assert not n.startswith('/') and '..' not in n.split('/'), n
    p=x['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest(); assert h==x['sha256'],(n,p)
    dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True)
    shutil.copyfile(p,dst); assert hashlib.sha256(open(dst,"rb").read()).hexdigest()==h
    tot+=os.path.getsize(p); sums.append('%s  %s'%(h,n))
open(W+'/work/up24m4q.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24m4q.sha; sha256sum $W/work/up24m4q.sha | cut -c1-16
grep -E "  (n|q|qd)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24m4q.sha
cd $W/work && tar cf $W/work/s24m4q.tar -C $S $(cd $S && ls) && ls -l $W/work/s24m4q.tar && sha256sum $W/work/s24m4q.tar
echo B64TAR; base64 -w0 $W/work/s24m4q.tar; echo
