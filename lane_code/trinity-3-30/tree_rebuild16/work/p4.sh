W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr15|tr16'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W 2>/dev/null | cut -f1
for l in tree_rebuild24m2c; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l $d"; grep -c "Selected model is at capacity" $d/transcript.log; test -f $d/final_message.md && head -c 4000 $d/final_message.md || tail -c 800 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-300; echo; done
ls -lt $W/w24/out | head -15
test -e $W/work/dbb.py || base64 -d > $W/work/dbb.py <<EOB
aW1wb3J0IGhhc2hsaWIsIGpzb24sIG9zLCBzeXMKbiwgbyA9IHN5cy5hcmd2WzFdLCBzeXMuYXJn
dlsyXQpvdXQgPSBbXQpmb3IgZCwgZHMsIGZzIGluIG9zLndhbGsobik6CiAgICBpZiBub3QgZC5y
ZXBsYWNlKG9zLnNlcCwgJy8nKS5lbmRzd2l0aCgnL3AvcS9zZWxlY3Rpb24nKToKICAgICAgICBj
b250aW51ZQogICAgZm9yIGYgaW4gc29ydGVkKGZzKToKICAgICAgICBwID0gb3MucGF0aC5qb2lu
KGQsIGYpCiAgICAgICAgaWYgb3MucGF0aC5pc2xpbmsocCkgb3Igbm90IG9zLnBhdGguaXNmaWxl
KHApOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHdpdGggb3BlbihwLCAncmInKSBhcyBo
OgogICAgICAgICAgICBoZWFkID0gaC5yZWFkKDEwMCkKICAgICAgICAgICAgaWYgbm90IChmLmVu
ZHN3aXRoKCcuc3FsaXRlJykgb3IgaGVhZC5zdGFydHN3aXRoKGInU1FMaXRlIGZvcm1hdCAzXHgw
MCcpKToKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIHdob2xlID0gaGFzaGxp
Yi5zaGEyNTYoaGVhZCk7IGJvZHkgPSBoYXNobGliLnNoYTI1NigpCiAgICAgICAgICAgIGZvciBi
IGluIGl0ZXIobGFtYmRhOiBoLnJlYWQoMSA8PCAyMiksIGInJyk6CiAgICAgICAgICAgICAgICB3
aG9sZS51cGRhdGUoYik7IGJvZHkudXBkYXRlKGIpCiAgICAgICAgb3V0LmFwcGVuZChkaWN0KHBh
dGg9b3MucGF0aC5yZWxwYXRoKHAsIG4pLCBzaXplPW9zLnBhdGguZ2V0c2l6ZShwKSwgc2hhMjU2
PXdob2xlLmhleGRpZ2VzdCgpLAogICAgICAgICAgICAgICAgICAgICAgICBoZWFkMTAwX2hleD1o
ZWFkLmhleCgpLCBib2R5X3NoYTI1Nj1ib2R5LmhleGRpZ2VzdCgpKSkKaWYgbm90IG91dDoKICAg
IHN5cy5leGl0KDEpCnQgPSBvcy5wYXRoLmpvaW4obywgJy5kYl9ieXRlcy5qc29uLnRtcCcpCndp
dGggb3Blbih0LCAndycpIGFzIGg6CiAgICBqc29uLmR1bXAoZGljdChmaWxlcz1vdXQpLCBoLCBp
bmRlbnQ9MSkKb3MucmVwbGFjZSh0LCBvcy5wYXRoLmpvaW4obywgJ2RiX2J5dGVzLmpzb24nKSkK
cHJpbnQoJ2RiX2J5dGVzJywganNvbi5kdW1wcyhbKHhbJ3BhdGgnXSwgeFsnc2l6ZSddLCB4Wydz
aGEyNTYnXVs6MTZdLCB4Wydib2R5X3NoYTI1NiddWzoxNl0pIGZvciB4IGluIG91dF0pKQo=
EOB
sha256sum $W/work/dbb.py
