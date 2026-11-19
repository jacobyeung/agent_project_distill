p = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/READY_QUEUE.md'
L = open(p).read().split('\n')
L[0] = L[0].replace('13:35Z', '14:40Z')
for k, l in enumerate(L):
    if l.startswith('| 0 | FULL'):
        L[k] = ("| 0 | FULL native routing for N first boundary (RULING 1259Z item 5) DONE on this lane's side | can N take all five routing slices + camera wording through full native intake? "
                "| R/sb_fullinv (sb_fullinv2.tar a1d6db13; draft envelopes); R/sb_fhalias/out/ALIAS.patch 474192f3 (sb_fhalias2.tar 6c5e4294) | patch: Cursor sb_fhrev GO; handed to tree_rebuild13 14:10Z "
                "| drafts dry-validated: all six fail first at r2_intake.py:58 (upstream receipts MISSING) | none (CPU); frame staging on the frame host is main's | Codex+Cursor "
                "| upstream receipts, map 17aa3e9e + plan 7cc01f36, camera 21-row evidence and a sixth family decide when envelopes complete |")
    if l.startswith('| 1b | mask carry'):
        L[k] = l.replace('card QUESTION ~1258Z', 'GO 1259Z on 3-3 card 3 not met (node /scratch 90 GB): BLOCKER ~1307Z; default hold')
    if l.startswith('| 3 | tower frames'):
        L[k] = ('| 3 | tower frames 64 (sb_ktfix4) READY | do G3T/SAM 3 at 64 input frames pay? | R/sb_ktfix2/out/sb_ktfix4.tar a4ad9df4, code 076c5d87 '
                '| Cursor sb_ktchk3 GO (after sb_ktchk, sb_ktchk2 fixes) | 68 tests, 30/30 plants refuse, dry run PASS, A0 1,037 and 1,012 '
                '| one Ampere >= 24e9 B card, parts one at a time: A 0.5 (0.75), B 2.5 (3.0), C 0.6 (0.75) GPU-h; staging A 22.24 GB then +3.86 +7.59 (> 20 GB) | Codex+Cursor '
                '| fails -> towers stay at 32; QUESTION ~1437Z |')
open(p, 'w').write('\n'.join(L))
