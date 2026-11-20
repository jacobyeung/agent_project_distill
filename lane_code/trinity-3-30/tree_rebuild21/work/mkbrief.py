B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/'
s = open(B + 'tree_rebuild21_d.md').read()
def rep(old, new):
    global s
    assert old in s, old[:60]
    s = s.replace(old, new)
rep('# Lane tree_rebuild21 (Devin Opus high; session on trinity-3-30, work on trinity-1-18 and trinity-2-28): successor of tree_rebuild20',
    '# Lane tree_rebuild22 (Devin Opus high; session on trinity-3-30, work on trinity-1-18 and trinity-2-28): successor of tree_rebuild21')
rep('"Next (in order; tree_rebuild21)"', '"Next (in order; tree_rebuild22)"')
rep('every `*_ORCH_*` file in events/tree_rebuild newer than 20261120T1040Z and in your inbox, newest first (they bind: 1232Z NOTE rebuilt extent receipt conditions, 1226Z ANSWER criterion (i) = (a)-(d),',
    'every `*_ORCH_*` file in events/tree_rebuild newer than 20261120T1040Z and in your inbox, newest first (they bind: 1556Z RULING extent route E or T by the reader rule (readers24 selected T), 1551Z ANSWER extent exemption scope + card defect counts (NOTE 1232Z withdrawn), 1419Z ORDER fail-before on the real path + candidates in the CPU job + one full kit review, 1226Z ANSWER criterion (i) = (a)-(d),')
rep('plus events/n_review newest n_review1e files, events/n_ops newest n_ops5 files',
    'plus events/n_review newest n_review1f files, events/n_ops newest n_ops6 files')
rep('Your lane folder: trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild21 (create it with work/ and inbox/ if absent; copy tree_rebuild20/work/st.py and ss.sh with the lane name changed). tree_rebuild20/work holds the last session\'s scripts:',
    'Your lane folder: trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild22 (create it with work/ and inbox/ if absent; copy tree_rebuild21/work/st.py and ss.sh with the lane name and times changed, and tree_rebuild21/inbox/* into your inbox). tree_rebuild21/work holds the last session\'s scripts: mkcand.py (candidate upload + CPU job generator, usage in STATUS Next), stage24m4u.sh, p12b.sh (verdict + mirror + stage), o3.sh/o7.sh (poll/fetch), o4.sh/o5.sh (Orchard summaries), revT_prompt.md (Cursor tree review, ready), build24m4s/t/u/v.md, review24m4s/t.md, readers24.md, d173717/d173724 outputs. tree_rebuild20/work holds older scripts:')
rep('Copy tree_rebuild20/REMOVAL_CANDIDATES.md into your lane folder', 'Copy tree_rebuild21/REMOVAL_CANDIDATES.md into your lane folder')
rep('with a reviewed kit (tree C\'\' de202f58 = tree C 0c7614c8 + processor patch a0d9cef4 + Cursor\'s test fix; kit line 24m4p/24m4q/24m4r, armed by arm_routing after n_review1e\'s task-A PASS under RULING 1135Z / ANSWER 1226Z), n_review1e\'s pre-submission PASS',
    'with a reviewed kit (tree C\'\' de202f58 + route-T extent patch of 24m4v after its Cursor review = the new launch tree; kit line 24m4u (helpers) merged with 24m4v as 24m4w, armed by arm_routing after n_review1f\'s task-A PASS under RULING 1135Z / ANSWER 1226Z / ANSWER 1551Z), n_review1f\'s pre-submission PASS')
rep('forecast given to ORCH: launch QUESTION ~17:00Z.', 'forecast given to ORCH: launch QUESTION ~21:00Z.')
rep('The CPU job (rcj mode r, ~8 min on preempt) runs N\'s whole mode r; repeat it, never a discovery, until N\'s routing build passes and nd.json, na.json.gz, chain.json (zero refusals), routing_types.json and proc_check pass; then ONE discovery',
    'The CPU job (rcj mode r, ~30 min on preempt) runs N\'s whole mode r; unreviewed candidates run beside the reviewed overlay (ORDER 1419Z); repeat it, never a discovery, until a candidate shows N\'s routing build PASS and nd.json, na.json.gz, chain.json (zero refusals over 43,101 rows, exempted count), routing_types.json and proc_check pass; then one full kit review, overlay, an evidence CPU run, then ONE discovery')
rep('Launch line (newest last): W/w24m', 'Launch line (newest last; 24m4r..24m4v below): W/w24m')
rep('W/w24r (24m4r building: sc.py bwrap mount order).',
    'W/w24r (24m4r: sc.py fresh root; reviewed overlay q e7ac0727 n a7809da0 qd 221d1782), W/w24s (24m4s: sc.py binds imported trainer source), W/w24t (24m4t: pl.py live dir local; x.py publisher), W/w24u (24m4u: publication budget, helper diagnostics, EXTENT_24M4U.md; package c7fba195), W/w24v (24m4v building: route T tree patch). Candidate job outputs W/work/d173724, d173725 (first mode-r end to end), d173754.')
rep('The reviewer lane is n_review1d (its events in B/events/n_review); the operator lane is n_ops4 (B/events/n_ops)',
    'The reviewer lane is n_review1f (its events in B/events/n_review); the operator lane is n_ops6 (B/events/n_ops)')
rep('(for n_review1d)', '(for n_review1f)')
rep('(for n_ops4)', '(for n_ops6)')
open(B + 'tree_rebuild22_d.md', 'w').write(s)
print('ok', len(s))
