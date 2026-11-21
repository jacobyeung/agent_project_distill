set -u; mkdir -p /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/in
base64 -d > /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/in/v.json <<'B64'
eyJmcmFtZV9jb3VudCI6MzIsImZyYW1lX2xheW91dCI6ImR1cGxpY2F0ZSIsImZyYW1lX21hcmtl
cnMiOnRydWUsInIyX3NhbXBsaW5nIjp7ImluZGljZXMiOnsicGF0aCI6ImIvaW5kaWNlcy5qc29u
Iiwic2hhMjU2IjoiYzQ1MDdlMzg0MmQyMmNlZmQyZDJmNjBjODdiODUyMTBhNmM2MWVjMmRmZmIx
ZWQyNDMzNWIxZjEwOWNlZjI1ZCJ9LCJwb3B1bGF0aW9uIjp7InBhdGgiOiJiL3BvcHVsYXRpb24u
anNvbiIsInNoYTI1NiI6ImM3NDg5ZWU3YTNmODNhNzRmODQ1ZmVhYTEwNjQ1NmM0YTc2NThkMWI5
OGNlZDMxMDUzMjBkM2UyM2I5YjFkOTMifX19Cg==
B64
base64 -d > /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/in/identity.txt <<'B64'
NDc5NGIyN2Y0ODM3OThkM2EzM2U4MDA0Yzk4Y2Q1Zjk5NzJiOTVkMmFiZjc1MjVkOTk1MWNkZjZl
ZjJjNWU0Mwo=
B64
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z && sha256sum in/v.json in/identity.txt 1>&2 < /dev/null
timeout 900 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out/admit_test.sh /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/in/v.json /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/admit > /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/admit.stdout 2>&1 < /dev/null; echo admit_rc=$? 1>&2
tail -3 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/admit.stdout 1>&2; base64 -w0 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_990777_20261121T105705Z/admit/ADMIT.json < /dev/null
