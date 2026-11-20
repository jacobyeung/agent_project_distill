W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls 2>/dev/null | grep -q tr20_b24m4r && { echo STILL_BUILDING; C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4r | tail -1); ls -la $d | tail -3; ls $W/w24r/out | tail -8; exit 0; }; P=$(ls $W/w24r/out/tree_rebuild_b24m4r_*.tar 2>/dev/null); test -n "$P" && test -f $P.sha256 || { echo NO_SHA; ls -la $W/w24r/out | tail; exit 0; }; echo $P; cat $P.sha256; sha256sum $P | cut -c1-16
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4r | tail -1); head -c 1500 $d/final_message.md; echo; cat $W/w24r/out/BUILD24M4R_REPORT.md; echo ===; cat $W/w24r/out/UPLOADS_24M4R.list; head -c 3000 $W/w24r/out/UPLOADS_24M4R.json
base64 -d > $W/prompts/review24m4r.md <<'B64'
IyBEZWx0YSByZXZpZXcgKHJlYWQtb25seSwgb25jZSkgb2YgS0lUIGJ1aWxkIDI0bTRyIG9mIGxh
bmUgdHJlZV9yZWJ1aWxkOiBid3JhcCBtb3VudC1vcmRlciBmaXggZm9yIHRoZSBwb29sIGNlbnN1
cyBzY2VuZSByZWJ1aWxkIChraXQgYi9zYy5weSkgYW5kIGV2ZXJ5IG90aGVyIGtpdC9yY2ogYndy
YXAgY29tbWFuZCwgd2l0aCBhIHJlYWwtYndyYXAgcHJvb2YKCllvdSByZXZpZXc7IHlvdSBkbyBu
b3QgZml4LiBSdW4gb25jZSwgcmVhZC1vbmx5LCBvbiB0cmluaXR5LTEtMTg7IG5vYm9keSBhbnN3
ZXJzIHF1ZXN0aW9ucy4gUmVwb3J0IG9ubHkgdmVyaWZpZWQgcHJvYmxlbXMgd2l0aCBmaWxlOmxp
bmUgYW5kIGV2aWRlbmNlLiBGaW5hbCBtZXNzYWdlIGlzIHRoZSB2ZXJkaWN0LgoKLSBCdWlsZDog
YC9zY3JhdGNoL2pqeWV1bmcvb3JjaF9uMzAvdHJlZV9yZWJ1aWxkMTBfdy93MjRyL2AgKHByb21w
dCBgL3NjcmF0Y2gvamp5ZXVuZy9vcmNoX24zMC90cmVlX3JlYnVpbGQxMF93L3Byb21wdHMvYnVp
bGQyNG00ci5tZGA7IG91dC9CVUlMRDI0TTRSX1JFUE9SVC5tZCwgb3V0L1VQTE9BRFNfMjRNNFIu
anNvbi8ubGlzdCwgb3V0L3Jjai8pLiBCYXNlOiAyNG00cTIgYC9zY3JhdGNoL2pqeWV1bmcvb3Jj
aF9uMzAvdHJlZV9yZWJ1aWxkMTBfdy93MjRxMi9gICh5b3VyIHJldmlldyBjb2RleF9ydW5zLypf
dHJlZV9yZWJ1aWxkX3JldjI0bTRxOiBHTyBBRlRFUiBGSVhFUykuIEZhaWx1cmUgZXZpZGVuY2U6
IGAvc2NyYXRjaC9qanlldW5nL29yY2hfbjMwL3RyZWVfcmVidWlsZDEwX3cvd29yay9kMTczNzEw
LzE3MzcxMC9qb2IubG9nYCAoc2MucHk6NDMgYndyYXAgYC0tdG1wZnMgemAgdGhlbiBgLS1yby1i
aW5kIHovc2AgLT4gc291cmNlIG1pc3NpbmcpLgotIFZlcmlmeTogKDEpIHRoZSBmYXVsdCBpcyBm
aXhlZDogZXZlcnkgYmluZCBzb3VyY2Ugb2YgdGhlIHNjZW5lLXJlYnVpbGQgc2FuZGJveCByZXNv
bHZlcyBvdXRzaWRlIGFueSB0bXBmcyBpdCBpcyBtb3VudGVkIHVuZGVyLCBpbnB1dHMgcmVhZC1v
bmx5LCBvbmx5IHRoZSBvdXRwdXQgd3JpdGFibGU7ICgyKSBldmVyeSBvdGhlciBid3JhcCBjb21t
YW5kIHRoZSBraXQgYW5kIHJjaiBidWlsZCAoc2MucHksIHBsLnB5LCByYi5weSwgeC5weSwgcGMu
cHksIGNoLnB5LCByZGlmZikgd2FzIGNoZWNrZWQgZm9yIHRoZSBzYW1lIG9yZGVyaW5nIGZhdWx0
IGluIG1vZGUgciAodW5kZXIgeC5weSdzIG91dGVyIHNhbmRib3gpIGFuZCBtb2RlIHEgKGpkNS5z
aCwgbm8gb3V0ZXIgc2FuZGJveCksIGFuZCB0aGUgZml4ZXMgYXJlIGNvcnJlY3Q7ICgzKSB0aGUg
cmVhbC1id3JhcCBwcm9vZiBhY3R1YWxseSByYW4gbmVzdGVkIGFuZCB1bm5lc3RlZCBvbiB0aGUg
T3JjaGFyZCBsYXlvdXQgYW5kIHJlYWNoZWQgdGhlIGNlbnN1cyBjb21wYXJlIChyZWFkIGl0cyBs
b2dzOyBpZiBuZXN0ZWQgYndyYXAgd2FzIGltcG9zc2libGUsIHRoZSByZXBvcnQgc2F5cyB3aHkg
aG9uZXN0bHkpOyAoNCkgbm90aGluZyBlbHNlIGNoYW5nZXM6IEMnJyBkZTIwMmY1OCwgY2Vuc3Vz
IGNvbXBhcmUgbG9naWMsIHJlZnVzYWwvYnVpbGQvcHVibGlzaGVyIHN0YXR1c2VzLCBjaGFpbiBz
dGVwLCBtb2RlIGIgYnl0ZS1pZGVudGljYWw7IG9ubHkgaW50ZW5kZWQgZmlsZXMgZGlmZmVyIHZz
IDI0bTRxMjsgR08gZmFsc2UgZXhjZXB0IGtpdF9uX2dvOyAoNSkgVVBMT0FEU18yNE00UiBsaXN0
cyBleGFjdGx5IHRoZSBjaGFuZ2VkIGZpbGVzIHZzIE9yY2hhcmQgKHEgMDk4OTg3ZTIsIG4gYTQ1
NTQxNjEsIHFkIDAyMmMxYzdhOyByY2ogeC5weSBkODUxNzMzMywgY2gucHkgMTZkNzIxMGIsIG5k
LnB5IGViMGJhOTJlLCBmLmpzb24gMzdjYmMwNWQsIHBjLnB5IGJkODcyNTJiLCBwcy5weSA2OTQ1
MjkyZSwgcmNqLnNoIGIyMzM5M2YyLCBQX1NBTVBMRV9JIGZmZjc0MmJiKSB3aXRoIGNvcnJlY3Qg
c2hhMjU2IGFuZCBuZXcgc2VhbHM7ICg2KSB3aGF0IHlvdSBkaWQgbm90IGNoZWNrLgoKUnVsZXM6
IFJlYWQtb25seS4gTm8gc3NoLCBuZXR3b3JrLCBHUFUsIEdpdCwgdG11eCwgc2NoZWR1bGVyIG9y
IGFub3RoZXIgYWdlbnQuIE5ldmVyIGxpc3QsIHNlYXJjaCBvciBncmVwIG9uIC9ob21lIG9yIC9k
YXRhKiAocmVhZCBvbmx5IHRoZSBuYW1lZCBmaWxlcyB0aGVyZSkuIG5pY2UgLW4gMTAsIGF0IG1v
c3QgOCB0aHJlYWRzLCB1bmRlciAyMCBHQiBSQU0uIEZpcnN0IGxpbmUgYEdPYCwgYEdPIEFGVEVS
IEZJWEVTYCBvciBgTk8tR09gOyBhdCBtb3N0IDEyIGxpbmVzLgo=
B64
sha256sum $W/prompts/review24m4r.md | cut -c1-8
tmux new-session -d -s tr21_rev24m4r "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24r $W/prompts/review24m4r.md --model gpt-6-astra --effort high --label tree_rebuild_rev24m4r --skip-git-check > $W/work/rev24m4r.log 2>&1"; sleep 5; tmux ls | grep tr2
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild21 && cat > /scratch/jjyeung/n30_mirror/tree_rebuild21/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild21/$(basename $P) | cut -c1-16'"
