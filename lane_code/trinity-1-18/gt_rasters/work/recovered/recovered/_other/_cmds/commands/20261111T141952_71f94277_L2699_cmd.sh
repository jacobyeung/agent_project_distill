<!-- recovered by seal_plan: transcript=71f94277 line=2699 utc=2026-11-11T14:19:52.525Z kind=commands original_path=(bash command)  -->
python3 - <<'EOF'
p='/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/gemini-argon-subagents.md'
s=open(p).read()
i=s.find('**Harness findings (2026-11-11')
assert i>0
new='''**Harness findings (2026-11-11, record /data2/jjyeung/agent_project_data/distill_design/GEMINI_AGENT_HARNESS_20261111.md):** use `argon-agent` for everything on the Gemini key. `argon-agent --model <id>` runs any model id on the key (`--list-models` prints them), and every subagent and workflow agent in the run follows `--model`. Its context window is set by `--window` (100k to 1m, default 290k): use `--window 200k` when many long sessions share the key's token rate, and a larger value for one very long task. A 100-agent workflow completes inside ONE argon-agent session: start that one session through Bash with `-C` on a /scratch directory (never 100 separate runs); keep Argon at the default 16 agents at once; Carbon takes `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=100`. With the default window argon-agent ties the Antigravity CLI on coding tasks (median 30.7 against 30.1 min), so Antigravity (a test install on trinity-2-18 with no usage meter, rm_guard or Carbon) is not needed.
'''
open(p,'w').write(s[:i]+new)
print('memory updated')
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: USER relayed an update on Gemini-key agents: use argon-agent for everything (new --window flag, default 290k; --window 200k when many long sessions share the key); memory gemini-argon-subagents rewritten in place." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md