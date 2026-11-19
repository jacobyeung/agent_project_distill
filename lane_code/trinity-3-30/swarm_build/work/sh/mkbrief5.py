B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'
s = open(B + '/briefs/swarm_build4.md').read()
s = s.replace('# Lane swarm_build4 (Devin Opus high, trinity-3-30)', '# Lane swarm_build5 (Devin Opus high, trinity-3-30)')
a = s.index('## State you build on'); b = s.index('## How to build')
mid = '''## State you build on
- Resume from /scratch/jjyeung/orch_n30/swarm_build/STATUS.md (exact state at 15:35Z: the three GPU kits, what survives of each on trinity-2-28, the resume mechanics, scripts used) and B/events/swarm_build/READY_QUEUE.md. Read every B/events/swarm_build/*ORCH*.md newer than 15:21Z and the lane inbox before acting.
- Orders in force (B/events/swarm_build): 0607Z (K1 train selects; K1 held-out report-only; R0-dev one look per category, bar first, R0DEV_LOOKS.md; dev-S1 diagnostic; official never), 0611Z (CPU manners on trinity-1-18), 0636Z (Devin economy: poll every 10 min; if your queue waits more than 20 minutes only on others, write STATUS.md exact, post a RESULT and end without a successor), 1010Z (exclusion pins R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4, K1 held-out 4d4736cf), 1056Z (1,012-row population binding), 1135Z item 4 (every kit writes its frozen bars first and refuses to score over existing scores), 1234Z (at most two Astra dispatches at once, top three of the queue only, until tree_rebuild12/13 posts build 21h's package), 1259Z item 5 (FULL; done on this lane's side), 1437Z (standing GO: one reviewed kit per empty card on trinity-1-18, order carry, phrase part 2, tower A, then B/C after A's table), 1442Z (GO on trinity-2-28: the three kits each on its own card, cards < 100 MiB with no process in a fresh reading, up to 4 cards, then tower B/C, then the object-route tracker; mask adapter only if phrase part 2 clears its bar; yield to main; one RESULT per kit; outputs back to trinity-1-18 as one tar each over InfiniBand), 1521Z (tower A resume once, 0.5 h, missing captures only; size B/C stops from 3.4 captures/min).
- trinity-2-28 is reachable again since its 14:32Z reboot (ORCH 1442Z overrides the old LANE_RULES line): reach it only by nesting `ssh trinity-2-28.ib` inside the tssh call to trinity-1-18.
- All three kits ran on trinity-2-28 from 14:57-14:59Z and were killed by vnice preemption at 15:30:43Z (user qiwu2 took all 8 cards). BLOCKER ~1533Z asks for resume orders and whether carry may price its complete decision arm S_A0/D64 on CPU. Default: no rerun and no pricing until answered.
- Vehicle N is owned by tree_rebuild12/13 (B/events/tree_rebuild): never touch its folders or tmux sessions.

## Priorities now
1. Act on the orchestrator's answer to BLOCKER ~1533Z: resume each killed kit's missing units on an empty card (2-28 or 1-18), with the kit's own launcher and an operator override only as ordered; record the two readings in the launch event; poll each minute until first output, then every 5 minutes.
2. Price each finished kit on trinity-1-18 (return outputs as one tar over InfiniBand) and post one RESULT per kit: bar, value, interval, verdict, what N should bind; record it under distill_design with an INDEX line.
3. Tower B and C after A's table says more frames can pay (stops sized from 3.4 captures/min, stated in the grant); then the object-route tracker kit (R/sb_kobj4: build a final-kit review first if it has none).
4. Keep READY_QUEUE.md current.

'''
s = s[:a] + mid + s[b:]
s = s.replace("Never ssh to trinity-1-3, trinity-2-18 or trinity-2-28.", "Never ssh to trinity-1-3 or trinity-2-18; trinity-2-28 only nested through trinity-1-18 as above.")
s = s.replace('Rotate 5.5 hours after your start (you start about 11:40Z)', 'Rotate 5.5 hours after your start (you start about 15:40Z)')
s = s.replace('copy this brief to briefs/swarm_build5.md', 'copy this brief to briefs/swarm_build6.md').replace('devin_bg.sh swarm_build5', 'devin_bg.sh swarm_build6')
open(B + '/briefs/swarm_build5.md', 'w').write(s)
print(len(s))
