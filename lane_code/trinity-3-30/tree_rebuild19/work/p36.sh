W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -q tr19_b24m4m && { echo STILL_BUILDING; exit 0; }; P=$W/w24m/out/tree_rebuild_b24m4m_598cadf7.tar; test -f $P.sha256 || { echo NO_SHA; exit 0; }; cat $P.sha256; sha256sum $P
base64 -d > $W/prompts/build24m4n.md <<'B64'
IyBDb2RleCBidWlsZCAyNG00biBvZiBsYW5lIHRyZWVfcmVidWlsZDogZGlzY292ZXJ5IGtpdCBx
ZCByZXBvcnRzIGZyYW1lIGNvdW50IGFuZCBwcm9jZXNzb3IgcGl4ZWwgYm91bmRzIHdpdGggaXRz
IHN0ZXAtMSBmb3J3YXJkIGNoZWNrIChraXQtb25seSkKCllvdSBydW4gb25jZSwgb24gdHJpbml0
eS0xLTE4OyBub2JvZHkgYW5zd2VycyBxdWVzdGlvbnMuIFdyaXRhYmxlOiBgSj0vc2NyYXRjaC9q
anlldW5nL29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvdzI0bjIvYCBvbmx5IChzdGVwIDAsIGFs
cmVhZHkgZG9uZSBieSB0aGUgbGFuZTogdW50YXIgb2YgYC9zY3JhdGNoL2pqeWV1bmcvb3JjaF9u
MzAvdHJlZV9yZWJ1aWxkMTBfdy93MjRtL291dC90cmVlX3JlYnVpbGRfYjI0bTRtXzU5OGNhZGY3
LnRhcmAgKGNoZWNrIGl0cyAuc2hhMjU2KTsgdW5kZXIgMjUgR0IpLiBQeXRob246IGAvc2NyYXRj
aC9qanlldW5nL2VudnMvcDFjcHUvYmluL3B5dGhvbiAtSSAtcyAtQmAuIFRpbWUgbGltaXQ6IDUw
IG1pbnV0ZXMuIENvbmZpcm0gZmlyc3Q6IEMnJyBkZTIwMmY1OC4uLjsga2l0cyBxIGRlNTMzMTBi
LCBuIDNjZjM4YjBiLCBuX2dvIDFiYjE5MWI5LCBxZCA3ZDM1OGZmNS4gUmVhZCBvdXQvQlVJTEQy
NE00TV9SRVBPUlQubWQsIG91dC9RRF9TVEVQMS5tZCBhbmQgdGhlIHJldmlldyBmaW5kaW5nIGJl
bG93LgoKIyMgRmluZGluZyB0byBmaXggKEFzdHJhIHJldmlldyBvZiAyNG00bCwgY2FycmllZCBp
bnRvIDI0bTRtKQpgd29yay90cmVlX3IxYy9zdHVkZW50X3BpbG90L2NhcnJpZXJfYzFfcnVuLnB5
OjMwNTJgOiBxZCdzIGZpcnN0X2JhdGNoX2NoZWNrIHJlY29yZHMgcGVyLXN0cmVhbSByb3cgaWRz
LCB0b2tlbiBjb3VudHMsIGxvc3MgYW5kIGZpbml0ZW5lc3MgYnV0IG5vdCB0aGUgZnJhbWUgY291
bnQgYW5kIHByb2Nlc3NvciBwaXhlbCBib3VuZHMgYWN0dWFsbHkgdXNlZCwgd2hpY2ggT1JDSCBy
ZXF1aXJlcyBwZXIgc3RyZWFtIChyb3dzLCBmcmFtZSBjb3VudCwgcHJvY2Vzc29yIHBpeGVsIGJv
dW5kcywgdG9rZW4gY291bnRzLCBmaW5pdGUgbG9zcykuCgojIyBEbwoxLiBXaXRob3V0IGNoYW5n
aW5nIHRoZSB0cmVlIChDJycgc3RheXMgZGUyMDJmNTgpIGFuZCB3aXRob3V0IGNoYW5naW5nIGtp
dHMgcSwgbiwgbl9nbzogbWFrZSBraXQgcWQgcHVibGlzaCwgd2l0aCB0aGUgc3RlcC0xIGZvcndh
cmQgY2hlY2ssIGZvciBlYWNoIHN0cmVhbTogcm93cywgdGhlIGZyYW1lIGNvdW50IGFuZCBwaXhl
bCBib3VuZHMgdGhlIHByb2Nlc3NvciB1c2VkICh0aGUgcHJvY2Vzc29yIG9iamVjdCdzIHRva2Vu
aXplci5fYzFfZnJhbWVfY291bnQsIF9jMV9mcmFtZV9tYXJrZXJzLCB3aGV0aGVyIF9iN19sYXlv
dXQgaXMgc2V0LCBhbmQgdGhlIChtaW5fcGl4ZWxzLCBtYXhfcGl4ZWxzKSBwYWlyIGNhcnJpZXJf
YzFfZGF0YS5lbmNvZGVfbGF5b3V0X3JvdyBwYXNzZXMgZm9yIHRoYXQgcHJvY2Vzc29yOiBERUZB
VUxUX1BJWEVMUyB3aGVuIF9iN19sYXlvdXQgaXMgYWJzZW50KSwgdG9rZW4gY291bnRzIGFuZCB0
aGUgbG9zcy9maW5pdGVuZXNzIHRoZSBjaGVjayBhbHJlYWR5IHJlY29yZHMuIFByZWZlciByZWFk
aW5nIHRoZXNlIGZyb20gdGhlIHZlcnkgcHJvY2Vzc29yIG9iamVjdCBmaXJzdF9iYXRjaF9jaGVj
ayB1c2VzIChlLmcuIGEga2l0LWxldmVsIHdyYXBwZXIgYXJvdW5kIHByb2Nlc3Nvcl9mb3JfcmVj
ZWlwdCAvIGVuY29kZSB0aGF0IHJlY29yZHMgYXR0cmlidXRlcyBhbmQgdGhlIHBpeGVsIHR1cGxl
IHBlciBjYWxsIHdpdGhvdXQgY2hhbmdpbmcgcmVzdWx0cyk7IGlmIG9ubHkgYSBzYW1lLWFyZ3Vt
ZW50cyByZWNvbnN0cnVjdGlvbiBpcyBwb3NzaWJsZSwgc2F5IHNvIGFuZCByZWNvcmQgYm90aC4g
UHVibGlzaCBhcyBsaXZlIGV2aWRlbmNlIG9mIHRoZSBkaXNjb3ZlcnkgKG8vPGpvYj4vIHBhdGgg
dGhlIGtpdCBhbHJlYWR5IHVzZXMsIHNtYWxsIEpTT04pIGFuZCByZWZ1c2Ugbm90aGluZyBuZXcu
CjIuIFRlc3RzOiBhIGZpeHR1cmUgc2hvd2luZyB0aGUgcmVjb3JkIGNvbnRhaW5zIGFsbCBmaXZl
IGZpZWxkcyBwZXIgc3RyZWFtIGFuZCB0aGF0IGVuY29kZSBvdXRwdXRzIGFyZSBieXRlLWlkZW50
aWNhbCB3aXRoIGFuZCB3aXRob3V0IHRoZSByZWNvcmRlcjsga2l0LCBzY2FuLCBuYW1pbmcsIHJl
c29sdmVyLCBndWFyZCBhbmQgYXJtaW5nIHN1aXRlczsgcWQgc3RpbGwgc3RvcHMgYmVmb3JlIHRy
YWluaW5nLgozLiBPdXRwdXRzOiByZXNlYWwgcWQgb25seTsgb3V0L1VQTE9BRFNfMjRNNE4uanNv
bi8ubGlzdCAocWQgZGVsdGEgdnMgMjRtNG0ncyBxZCA3ZDM1OGZmNSksIHBhY2thZ2Ugb3V0L3Ry
ZWVfcmVidWlsZF9iMjRtNG5fPHNlYWw4Pi50YXIsIG91dC9CVUlMRDI0TTROX1JFUE9SVC5tZCB1
bmRlciAxMCBsaW5lcyAobGluZSAxOiBxZCBzZWFsIGFuZCB0aGUgcSwgbiwgbl9nbyBzZWFscyB1
bmNoYW5nZWQsIG9yIFNUT1Agd2l0aCB0aGUgcmVhc29uKS4KCiMjIFJ1bGVzIGZvciB0aGUgYnVp
bGQgKHJlc3RhdGluZyBidWlsZCAxNSdzKQpObyBzc2gsIG5ldHdvcmssIE9yY2hhcmQsIEdQVSwg
R2l0LCB0bXV4LCBzY2hlZHVsZXIgb3Igb3RoZXIgYWdlbnRzLiBOZXZlciBsaXN0LCBzZWFyY2gg
b3IgZ3JlcCBvbiAvaG9tZSBvciAvZGF0YSo6IHJlYWQgb25seSBuYW1lZCBmaWxlcyB0aGVyZS4g
V3JpdGUgb25seSB1bmRlciBKLiBObyBkZWxldGlvbiAoc3VwZXJzZWRlZCBmaWxlcyBpbnRvIEov
YXR0aWMvKS4gRXZlcnkgQ1BVIHByb2Nlc3MgdW5kZXIgYG5pY2UgLW4gMTBgLCBhdCBtb3N0IDgg
dGhyZWFkcywgdW5kZXIgMTYgR0IgUkFNLiBEbyBub3QgY2hhbmdlIHRoZSB0cmVlIG9yIGtpdHMg
cSwgbiwgbl9nby4gTm8gcHJvamVjdCwgYmVuY2htYXJrLCBkYXRhc2V0LCBtb2RlbCBvciBtZXRo
b2Qgd29yZCBpbiBhbnkgbmV3IE9yY2hhcmQtdmlzaWJsZSBuYW1lLCBwYXRoLCBhcmd1bWVudCBv
ciBsb2cuIFJlcG9ydCBmYWlsdXJlcyB3aXRoIHRoZWlyIG91dHB1dDsgbmV2ZXIgY2xhaW0gYSBj
aGVjayB5b3UgZGlkIG5vdCBydW4uCg==
B64
sha256sum $W/prompts/build24m4n.md | cut -c1-8; mkdir $W/w24n2 && nice -n 10 tar xf $P -C $W/w24n2 && ls $W/w24n2 || exit 1
tmux new-session -d -s tr19_b24m4n "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24n2 $W/prompts/build24m4n.md --model gpt-6-astra --effort high --label tree_rebuild24m4n --skip-git-check > $W/work/b24m4n.log 2>&1"
tmux new-session -d -s tr19_rev24m4m "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24m $W/prompts/review24m4m.md --model gpt-6-astra --effort high --label tree_rebuild_rev24m4m --skip-git-check > $W/work/rev24m4m.log 2>&1"; sleep 8; tmux ls | grep tr19
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild19/tree_rebuild_b24m4m_598cadf7.tar.ok && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild19/tree_rebuild_b24m4m_598cadf7.tar.ok'"
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24m4m2; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24m4m2'
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
for tag in ('24M4M',):
    e=entries(W+'/w24m/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24m/out/UPLOADS_%s.list'%tag) if l.strip()]
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
open(W+'/work/up24m4m2.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24m4m2.sha; sha256sum $W/work/up24m4m2.sha | cut -c1-16
grep -E "  (n|q|qd)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24m4m2.sha
cd $W/work && tar cf $W/work/s24m4m.tar -C $S $(cd $S && ls) && ls -l $W/work/s24m4m.tar && sha256sum $W/work/s24m4m.tar
