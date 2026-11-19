p = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/READY_QUEUE.md'
L = open(p).read().split('\n')
L[0] = L[0].replace('13:00Z', '13:35Z')
for k, l in enumerate(L):
    if l.startswith('| 1 | mask phrase kit'):
        L[k] = ('| 1 | mask phrase kit: part 1 SELECTED (registered); part 2 READY for GPU (sb_ph2fix2) | does the stored-pool price hold for a standalone SAM 3 call; do new phrases or conditional retention add? '
                '| R/sb_ph2fix/out/sb_ph2fix2.tar 3440a9ff (13.45 GB incl. payload); gate fix before pricing sb_ph2gate3 | Cursor sb_ph2chk: GPU pass GO as shipped '
                '| suites 26/26/25, guard attacks refuse, strace 0 /home,/data opens | one idle >= 48 GB bf16 card off 0-13; ~0.92 GPU-h (projection drops new phrases), stop 1.2; staging 13.22 GB '
                '| Codex+Cursor | exact_holds fails -> serving score below stored-pool price; QUESTION ~1333Z |')
    if l.startswith('| 3 | tower frames'):
        L[k] = l.replace('sb_ktchk GO AFTER FIXES (4 edits) -> applied; Cursor re-check sb_ktchk2 running',
                         'sb_ktchk2 GO AFTER FIXES (3 holes + padded reading) -> Codex sb_ktfix4 running').replace(
                         'R/sb_ktfix2/out/sb_ktfix3.tar 1a222dd5, code 47ecaeec', 'R/sb_ktfix2 (sb_ktfix4 pending; never bind 47ecaeec)')
L.insert(3, "| 0 | FULL native routing for N first boundary (RULING 1259Z item 5) | can N train on all five routing slices + camera wording at its first boundary? "
            "| R/sb_fullinv (inventory dd5038b9, draft envelopes); R/sb_fhalias (ALIAS.patch; 4th file in sb_fhalias2) | inventory: dry-validated with the real intake; patch: Cursor review after fhalias2 "
            "| drafts fail at r2_intake.py:58 (upstream MISSING) | none (CPU); frame staging on the frame host is main's | Codex "
            "| upstream receipts and map 17aa3e9e + plan 7cc01f36 decide when envelopes complete |")
open(p, 'w').write('\n'.join(L))
