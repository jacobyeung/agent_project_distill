W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls 2>/dev/null | grep -q tr21_b24m4t && { echo STILL_BUILDING; C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4t | tail -1); ls -la $d | tail -3; ls $W/w24t/out | tail -8; exit 0; }; P=$(ls $W/w24t/out/tree_rebuild_b24m4t_*.tar 2>/dev/null); test -n "$P" && test -f $P.sha256 || { echo NO_SHA; ls -la $W/w24t/out | tail; exit 0; }; echo $P; cat $P.sha256; sha256sum $P | cut -c1-16
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4t | tail -1); head -c 1500 $d/final_message.md; echo; cat $W/w24t/out/BUILD24M4T_REPORT.md; echo ===; cat $W/w24t/out/UPLOADS_24M4T.list; head -c 3000 $W/w24t/out/UPLOADS_24M4T.json
base64 -d > $W/prompts/review24m4t.md <<'B64'
IyBEZWx0YSByZXZpZXcgKHJlYWQtb25seSwgb25jZSkgb2YgS0lUIGJ1aWxkIDI0bTR0IG9mIGxh
bmUgdHJlZV9yZWJ1aWxkOiBraXQgYi9wbC5weToyNDggcnYubG9jYXRpb24oKSB3cm90ZSBgPHBv
b2w+L28vPGpvYj4vbGl2ZWAgb24gcmVhZC1vbmx5IC9wcm9qZWN0IGluc2lkZSByY2ogeC5weSdz
IG1vZGUtciBzYW5kYm94ICh5b3VyIHJldjI0bTRzIE5PLUdPIGZpbmRpbmcpLCBwbHVzIGxvb2st
YWhlYWQgZml4ZXMgb2YgbGF0ZXIgbW9kZS1yIHdyaXRlcwoKWW91IHJldmlldzsgeW91IGRvIG5v
dCBmaXguIFJ1biBvbmNlLCByZWFkLW9ubHksIG9uIHRyaW5pdHktMS0xODsgbm9ib2R5IGFuc3dl
cnMgcXVlc3Rpb25zLiBSZXBvcnQgb25seSB2ZXJpZmllZCBwcm9ibGVtcyB3aXRoIGZpbGU6bGlu
ZSBhbmQgZXZpZGVuY2UuIEZpbmFsIG1lc3NhZ2UgaXMgdGhlIHZlcmRpY3QuCgotIEJ1aWxkOiBg
L3NjcmF0Y2gvamp5ZXVuZy9vcmNoX24zMC90cmVlX3JlYnVpbGQxMF93L3cyNHQvYCAocHJvbXB0
IGAvc2NyYXRjaC9qanlldW5nL29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvcHJvbXB0cy9idWls
ZDI0bTR0Lm1kYDsgb3V0L0JVSUxEMjRNNFRfUkVQT1JULm1kLCBvdXQvVVBMT0FEU18yNE00VC5q
c29uLy5saXN0LCBvdXQvcmNqLykuIEJhc2U6IDI0bTRzIGAvc2NyYXRjaC9qanlldW5nL29yY2hf
bjMwL3RyZWVfcmVidWlsZDEwX3cvdzI0cy9gICh5b3VyIHJldmlldyBjb2RleF9ydW5zLypfdHJl
ZV9yZWJ1aWxkX3JldjI0bTRzOiBOTy1HTywgcGwucHk6MjQ4IGxpdmUgZGlyKS4gRmFpbHVyZSBl
dmlkZW5jZTogYC9zY3JhdGNoL2pqeWV1bmcvb3JjaF9uMzAvdHJlZV9yZWJ1aWxkMTBfdy93b3Jr
L2QxNzM3MjQvMTczNzI0L2pvYi5sb2dgIGxpbmVzIDM5NS00NDQgKGNhbmRpZGF0ZSBDUFUgam9i
IG9uIDI0bTRzOiBzY2VuZSByZWJ1aWxkIHBhc3NlZCwgdGhlbiB0aGUgbGl2ZSBta2RpciByZWZ1
c2VkKS4KLSBWZXJpZnkgRklSU1QgKE9SQ0ggT1JERVIgMTQxOVogaXRlbSAxKTogdGhlIHJlcG9y
dCBzaG93cyB0aGUgZmFpbHVyZSByZXByb2R1Y2VkIG9uIHRoZSB1bmZpeGVkIGtpdCB0aHJvdWdo
IHRoZSBqb2IncyByZWFsIGVudHJ5IHBhdGggKHgucHkncyBvd24gbW9kZSByIG9yIG1vZGUgcSBv
biB0aGUgT3JjaGFyZCBsYXlvdXQpIHdpdGggdGhlIHNhbWUgcmVmdXNhbCBzdHJpbmcsIGFuZCB0
aGUgc2FtZSBjb21tYW5kIHBhc3NpbmcgYWZ0ZXIgdGhlIGZpeDsgYSBmaXh0dXJlIHRoYXQgYnVp
bGRzIGJ5IGhhbmQgd2hhdCB0aGUgcmVhbCBwYXRoIGZhaWxzIHRvIGJ1aWxkIGRvZXMgbm90IGNv
dW50OyB3aXRob3V0IHRoaXMgZXZpZGVuY2UgcmV0dXJuIE5PLUdPIGFuZCBzdG9wLgotIFRoZW4g
dmVyaWZ5OiAoMSkgdGhlIGZhaWwtYmVmb3JlIGV2aWRlbmNlIGlzIHJlYWwgKHVuZml4ZWQga2l0
LCB4LnB5J3MgcmVhbCBsYXVuY2goKS9wbGFuX3IgcGF0aCwgcmVhZC1vbmx5IHBvb2wgcm9vdCwg
bm8gaGFuZC1tYWRlIG8vPGpvYj4pIGFuZCB0aGUgc2FtZSBjb21tYW5kIHBhc3NlcyBhZnRlciB0
aGUgZml4OyAoMikgbW9kZSByIGdldHMgYSB3cml0YWJsZSBsaXZlIGxvY2F0aW9uIHdpdGhvdXQg
YW55IHdyaXRlIHRvIHJlYWQtb25seSAvcHJvamVjdCwgcHVibGljYXRpb24gc3RheXMgYm91bmRl
ZCBhbmQgb3BhcXVlLCBhbmQgbW9kZSBxIChqZDUuc2ggZGlzY292ZXJ5KSBhbmQgbGF1bmNoIGJl
aGF2aW91ciBhcmUgdW5jaGFuZ2VkIChmaWxlOmxpbmUpOyAoMykgMjRtNHMncyBzYy5weSBmaXgg
aXMgaW50YWN0ICh0cmFpbmVyIHNvdXJjZSBhY3R1YWxseSBpbXBvcnRlZCwgaW5wdXRzIHJvLCBu
YW1lZCByZWZ1c2FsKSBhbmQgaXRzIGZpeHR1cmVzIHN0aWxsIHBhc3M7ICg0KSB0aGUgbG9vay1h
aGVhZCBsaXN0OiBldmVyeSBsYXRlciBtb2RlLXIgd3JpdGUgb3IgbWlzc2luZyBwYXRoIHRoZSBy
ZXBvcnQgbmFtZXMgaXMgcmVhbCwgZWFjaCBjbGFpbWVkIGZpeCBoYXMgZmFpbC1iZWZvcmUgZXZp
ZGVuY2UsIGFuZCBub3RoaW5nIGl0IGxpc3RzIGFzIHVuZml4ZWQgd2lsbCByZWZ1c2UgdGhlIG5l
eHQgQ1BVIGpvYiAoaWYgb25lIHdpbGwsIHNheSBzbyB3aXRoIGZpbGU6bGluZSk7ICg1KSBub3Ro
aW5nIGVsc2UgY2hhbmdlczogQycnIGRlMjAyZjU4LCBjZW5zdXMgY29tcGFyZSwgcmVmdXNhbC9i
dWlsZC9wdWJsaXNoZXIgc3RhdHVzZXMsIGNoYWluIHN0ZXAsIG1vZGUgYiBieXRlLWlkZW50aWNh
bDsgR08gZmFsc2UgZXhjZXB0IGtpdF9uX2dvOyAoNikgVVBMT0FEU18yNE00VCBleGFjdCB2cyBP
cmNoYXJkIHJldmlld2VkIG92ZXJsYXkgKHEgZTdhYzA3MjcsIG4gYTc4MDlkYTAsIHFkIDIyMWQx
NzgyOyByY2ogeC5weSBkODUxNzMzMywgY2gucHkgMTZkNzIxMGIsIG5kLnB5IGViMGJhOTJlLCBm
Lmpzb24gMzdjYmMwNWQsIHBjLnB5IGJkODcyNTJiLCBwcy5weSA2OTQ1MjkyZSwgcmNqLnNoIGIy
MzM5M2YyLCBQX1NBTVBMRV9JIGZmZjc0MmJiKSwgc2hhMjU2IGFuZCBzZWFscyBjb3JyZWN0OyAo
Nykgd2hhdCB5b3UgZGlkIG5vdCBjaGVjay4KClJ1bGVzOiBSZWFkLW9ubHkuIE5vIHNzaCwgbmV0
d29yaywgR1BVLCBHaXQsIHRtdXgsIHNjaGVkdWxlciBvciBhbm90aGVyIGFnZW50LiBOZXZlciBs
aXN0LCBzZWFyY2ggb3IgZ3JlcCBvbiAvaG9tZSBvciAvZGF0YSogKHJlYWQgb25seSB0aGUgbmFt
ZWQgZmlsZXMgdGhlcmUpLiBuaWNlIC1uIDEwLCBhdCBtb3N0IDggdGhyZWFkcywgdW5kZXIgMjAg
R0IgUkFNLiBGaXJzdCBsaW5lIGBHT2AsIGBHTyBBRlRFUiBGSVhFU2Agb3IgYE5PLUdPYDsgYXQg
bW9zdCAxNCBsaW5lcy4K
B64
sha256sum $W/prompts/review24m4t.md | cut -c1-8
tmux new-session -d -s tr21_rev24m4t "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24t $W/prompts/review24m4t.md --model gpt-6-astra --effort high --label tree_rebuild_rev24m4t --skip-git-check > $W/work/rev24m4t.log 2>&1"; sleep 5; tmux ls | grep tr2
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild21 && cat > /scratch/jjyeung/n30_mirror/tree_rebuild21/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild21/$(basename $P) | cut -c1-16'"
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24m4t; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24m4t'
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
for tag in ('24M4T',):
    e=entries(W+'/w24t/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24t/out/UPLOADS_%s.list'%tag) if l.strip()]
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
open(W+'/work/up24m4t.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24m4t.sha; sha256sum $W/work/up24m4t.sha | cut -c1-16
grep -E "  (n|q|qd)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24m4t.sha
cd $W/work && tar cf $W/work/s24m4t.tar -C $S $(cd $S && ls) && ls -l $W/work/s24m4t.tar && sha256sum $W/work/s24m4t.tar
echo B64TAR; base64 -w0 $W/work/s24m4t.tar; echo
