import base64
b = base64.encodebytes(open('build24m4u.md', 'rb').read()).decode().rstrip('\n')
head = """W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls 2>/dev/null | grep tr2
test ! -e $W/w24u || { echo W24U EXISTS; exit 1; }
P=$W/w24t/out/tree_rebuild_b24m4t_744b3636.tar; [ "$(sha256sum $P | cut -c1-16)" = 08a6c303c510257a ] || { echo PKG BAD; exit 1; }
mkdir -p $W/w24u && tar xf $P -C $W/w24u && ls $W/w24u | head -3
base64 -d > $W/prompts/build24m4u.md <<'B64'
"""
tail = """
B64
sha256sum $W/prompts/build24m4u.md | cut -c1-8
tmux new-session -d -s tr21_b24m4u "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24u $W/prompts/build24m4u.md --model gpt-6-astra --effort high --label tree_rebuild24m4u --skip-git-check > $W/work/b24m4u.log 2>&1"; sleep 8; tmux ls | grep tr2
"""
open('p11.sh', 'w').write(head + b + tail)
