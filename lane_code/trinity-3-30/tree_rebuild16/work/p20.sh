W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr16
cat > $W/work/d173496.log <<'EOPY'
4659b14c73e4881fcadeacbe5c5824ec5af5c5d722548611cca0aaf25c6ce7f0
2026-11-19T23:53:37Z | stage full on orchard-community-2: /tmp free 5725 GiB; mem 1842 GiB
KITX_OK venv_rwtrain_torch211_cu129.tar 13s
venv console scripts repointed: 26
KITX_OK c_fa8681cba4c0.tar 0s
KITX_OK t_b83a8a35d420815b.tar 0s
KITX_OK t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar 0s
2026-11-19T23:54:43Z | model staged: 18876308 KiB
KITX_OK art_8e85699ccf79.tar 0s
2026-11-19T23:54:43Z | small inputs staged
2026-11-19T23:54:43Z | joined receipt.json 724 B
2026-11-19T23:54:45Z | joined rows.sqlite 1931452416 B
2026-11-19T23:54:45Z | joined sources.json 585 B
2026-11-19T23:54:45Z | joined receipt.json 8547 B
2026-11-19T23:54:51Z | joined rows.sqlite 4891635712 B
2026-11-19T23:54:51Z | joined division.json 143998 B
2026-11-19T23:54:51Z | joined k.json 12169729 B
2026-11-19T23:54:51Z | joined k3_109026.json 651169 B
2026-11-19T23:54:51Z | joined k4_111337.json 1121761 B
2026-11-19T23:54:51Z | joined k7_115066.json 229825 B
2026-11-19T23:54:51Z | joined k.json 19469377 B
2026-11-19T23:54:51Z | joined k.json 51519052 B
2026-11-19T23:54:51Z | joined receipt.json 715 B
2026-11-19T23:54:53Z | joined rows.sqlite 1297735680 B
2026-11-19T23:54:53Z | joined sources.json 591 B
2026-11-19T23:54:53Z | joined receipt.json 2211 B
2026-11-19T23:55:15Z | joined rows.sqlite 21010542592 B
2026-11-19T23:55:15Z | joined receipt.json 713 B
2026-11-19T23:55:15Z | joined rows.sqlite 97079296 B
2026-11-19T23:55:15Z | joined receipt.json 714 B
2026-11-19T23:55:16Z | joined rows.sqlite 240427008 B
2026-11-19T23:55:16Z | joined heads.json 3410 B
2026-11-19T23:55:17Z | joined heads.safetensors 924151276 B
2026-11-19T23:55:19Z | joined encoder.safetensors 1824074576 B
2026-11-19T23:55:19Z | joined receipt.json 713 B
2026-11-19T23:55:20Z | joined rows.sqlite 1298710528 B
2026-11-19T23:55:20Z | joined patch.json 4231876 B
2026-11-19T23:55:20Z | joined 30c516bf.json 229 B
2026-11-19T23:55:20Z | joined 19c85a70.jsonl.gz 68141 B
2026-11-19T23:55:20Z | joined 99e6eed6.json 52806 B
2026-11-19T23:55:21Z | joined rows.sqlite 1251414016 B
2026-11-19T23:55:21Z | joined receipt.json 731 B
2026-11-19T23:55:23Z | joined d.db 1718255616 B
2026-11-19T23:55:23Z | joined i.json 2880 B
2026-11-19T23:55:23Z | joined m.json 47603 B
2026-11-19T23:55:23Z | joined u.gz 1688862 B
2026-11-19T23:55:23Z | joined c.json 120969 B
2026-11-19T23:55:23Z | joined d.json 685 B
2026-11-19T23:55:23Z | joined d_8091154cd499c474.json 712 B
2026-11-19T23:55:23Z | joined j.json 20313 B
2026-11-19T23:55:23Z | joined n.json 107499 B
2026-11-19T23:55:23Z | joined r.json 1025 B
2026-11-19T23:55:23Z | joined v.json 231 B
2026-11-19T23:55:23Z | joined z.json 2982924 B
2026-11-19T23:55:23Z | joined s.json 78196 B
2026-11-19T23:55:46Z | joined rows.sqlite 21377871872 B
archive members verified: 3
2026-11-19T23:55:48Z | archive d687a3f8a327b8cd staged
archive members verified: 2
2026-11-19T23:55:49Z | archive 7e0caa14a50f0379 staged
archive members verified: 2
2026-11-19T23:55:50Z | archive feec2fa581af5928 staged
archive members verified: 2
2026-11-19T23:55:52Z | archive ab7bc2ee0029d035 staged
x_3f0c6f46bed773a432d88ab2dbf23dd0d11e1fa8556ca8d26c31aa74643863b9 (most recent call last):
  File "<stdin>", line 3, in <module>
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/q_22c714e1_173496/h/k/0.json'
2026-11-19T23:55:54Z work exit 1
dbb none
EOPY
base64 -d > $W/work/jd2.sh <<EOB
IyEvYmluL2Jhc2gKI1NCQVRDSCAtcCBwcmVlbXB0CiNTQkFUQ0ggLS1qb2ItbmFtZT1hMTVfY290
X2FwMjRkOWI4ZTIKI1NCQVRDSCAtLW5vZGVzPTEKI1NCQVRDSCAtLW50YXNrcz0xCiNTQkFUQ0gg
LS1ncmVzPWdwdToxCiNTQkFUQ0ggLS1jcHVzLXBlci10YXNrPTQ4CiNTQkFUQ0ggLS1tZW09ODAw
RwojU0JBVENIIC0tdGltZT0wNDowMDowMAojU0JBVENIIC0tbm8tcmVxdWV1ZQojU0JBVENIIC0t
c2lnbmFsPUI6VEVSTUA2MDAKI1NCQVRDSCAtLW91dHB1dD0vcHJvamVjdC9jb21tdW5pdHkvamp5
ZXVuZy9va2g3L3hfMjJjNzE0ZTEvai9hMTVfY290X2FwMjRkOWI4ZTJfJWoubG9nCiNTQkFUQ0gg
LS1lcnJvcj0vcHJvamVjdC9jb21tdW5pdHkvamp5ZXVuZy9va2g3L3hfMjJjNzE0ZTEvai9hMTVf
Y290X2FwMjRkOWI4ZTJfJWouZXJyCnNldCAtZXVvIHBpcGVmYWlsCnVtYXNrIDA3NwpleHBvcnQg
UFlUSE9ORE9OVFdSSVRFQllURUNPREU9MQpleHBvcnQgT01QX05VTV9USFJFQURTPTggTUtMX05V
TV9USFJFQURTPTggT1BFTkJMQVNfTlVNX1RIUkVBRFM9OApleHBvcnQgVEtfSk9CX1NUQVJUPSIk
KGRhdGUgKyVzKSIKWD0iL3Byb2plY3QvY29tbXVuaXR5L2pqeWV1bmcvb2toNy94XzIyYzcxNGUx
IgpST09UPSIkWC9xZCIKTj0iJHtTTFVSTV9UTVBESVI6LS90bXB9L3FfMjJjNzE0ZTFfJHtTTFVS
TV9KT0JfSUQ6P30iCk89IiRYL28vJHtTTFVSTV9KT0JfSUR9IgpleHBvcnQgVE1QRElSPSIkTi90
bXAiIFhER19DQUNIRV9IT01FPSIkTi9jYWNoZSIKbWtkaXIgLXAgIiRUTVBESVIiICIkWERHX0NB
Q0hFX0hPTUUiICIkTyIKcHl0aG9uMyAtQiAtSSAtcyAiJFJPT1QvYi92LnB5IiAiJFJPT1QiCnNv
dXJjZSAiJFJPT1QvYi9lcC5zaCIKcHl0aG9uMyAtQiAtSSAtcyAiJFJPT1QvYi9yZXNvbHZlLnB5
IiAtLXBvb2wgIi9wcm9qZWN0L2NvbW11bml0eS9qanlldW5nL29raDciIC0tb3V0cHV0ICIkTi9y
MC5qc29uIiAyPiYxIHwgcHl0aG9uMyAtQiAtSSAtcyAiJFJPT1QvYi9sLnB5IiAiJFJPT1QiID4g
IiROL3EubG9nIgpzZXRzaWQgYmFzaCAtYyAnc2V0IC1vIHBpcGVmYWlsOyBweXRob24zIC1CIC1J
IC1zICIkMS9iL3gucHkiICIkMSIgIiQyIiAiJDMiIDI+JjEgfCBweXRob24zIC1CIC1JIC1zICIk
MS9iL2wucHkiICIkMSInIGJhc2ggIiRST09UIiAiJE4vcjAuanNvbiIgIiROIiAmClRLX1dPUktf
UElEPSQhCiggZm9yIGkgaW4gJChzZXEgMSAyNDApOyBkbyBzbGVlcCA2MDsgdGVzdCAtZSAiJE8v
ZGJfYnl0ZXMuanNvbiIgJiYgYnJlYWs7IGlmIHRlc3QgLXMgIiRPL3JvdXRpbmdfc2VsZWN0aW9u
Lmpzb24iOyB0aGVuIG5pY2UgLW4gMTAgcHl0aG9uMyAtQiAtSSAtcyAiJFgvZGJiMi5weSIgIiRO
IiAiJE8iICIkWC91IiA+PiAiJE8vZGJiLmxvZyIgMj4mMSAmJiBicmVhazsgZmk7IGRvbmUgKSAm
CnJjPTA7IHdhaXQgIiRUS19XT1JLX1BJRCIgfHwgcmM9JD8KZWNobyAiJChkYXRlIC11ICslRlQl
VFopIHdvcmsgZXhpdCAkcmMiCnRlc3QgLWUgIiRPL2RiX2J5dGVzLmpzb24iIHx8IG5pY2UgLW4g
MTAgcHl0aG9uMyAtQiAtSSAtcyAiJFgvZGJiMi5weSIgIiROIiAiJE8iICIkWC91IiA+PiAiJE8v
ZGJiLmxvZyIgMj4mMSB8fCBlY2hvICJkYmIgbm9uZSIKZXhpdCAiJHJjIgo=
EOB
cat > $W/prompts/diag173496.md <<'EOPY'
# Read-only diagnosis (once) of Orchard discovery job 173496 of lane tree_rebuild: why `/tmp/q_22c714e1_173496/h/k/0.json` disappeared during staging

You diagnose; you do not edit anything. You run once, read-only, on trinity-1-18; nobody answers questions. Your final message is the answer.

## Facts
- Job 173496 ran kit qd (seal 4659b14c, `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd`, build 24m2d; its BUILD24M2D_REPORT.md and BUILD24M2_REPORT.md in `w24/out/`) with the wrapper `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/jd2.sh` (copy of `w24/out/jd.sh` plus a db_bytes loop; note it does NOT `cd "$N"`, does not set Q_MODE, and runs resolve.py without `--listing`, unlike `w24/out/jr.sh`/`x_22c714e1/jrw.sh` which worked for routing jobs 173349/173368 through staging). Full job log: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173496.log` (69 lines; the .err was empty; `x_3f0c...` replaces the word Traceback).
- Flow: x.py -> z.bootstrap (b/z.py ~line 576-600: copies p_files into $N/h, writes $N/h/k/0.json from k/l.json because p.json local_map = k/l.json, then runs the decoded k/j.json shell with TK_KIT_HOME=$N/h). In that shell (decode k/j.json payload base64), CUR=$HX/k/0.json is read many times; the job died after the last `joined rows.sqlite 21377871872 B` with FileNotFoundError on $N/h/k/0.json from a `python3 - ... <<` heredoc whose line 3 reads sys.argv[1] (the PYTARS block ~line 155, after `cat $parts | tar -x -C "$U"`), so h/k/0.json existed earlier in the same shell and vanished during the extra/a1rows joins or the tars loop.

## Answer
1. The root cause, with file:line (decoded j.sh line numbers, kit file lines) and the evidence (e.g. a tar member, symlink, rsync, mv, cleanup, path collision between $N/h and a staged destination, a relative path under the wrong cwd, or the wrapper differences above). Reproduce on a tiny fixture under /tmp if that settles it (nice -n 10, 8 threads, no network).
2. The smallest fix and whether it is wrapper-only (jd.sh, outside the kit seal) or needs a kit change; whether kits q/n (launch) have the same defect.
3. Anything else in the same staging path that would fail next for kit qd.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Any process under nice -n 10, at most 8 threads, under 20 GB RAM. At most 25 lines.
EOPY
tmux new -d -s tr16_d173496 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W $W/prompts/diag173496.md --model gpt-6-astra --effort high --label tree_rebuild_d173496 --skip-git-check > $W/work/d173496_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr16; tail -3 $W/work/d173496_dispatch.log
