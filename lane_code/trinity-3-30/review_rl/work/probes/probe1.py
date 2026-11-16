import json
from rltests.test_reward import rec, direct, program, REL, FT, FT_BODY, REL_SHORT, CFG, EOS
from rlkit.reward import score_group
from rlkit.gate import gate
from rlkit.score import score
def show(tag, rows):
    for r in rows: print(tag, dict(c=r['c'], g=r['g'], path=r['path'], r=round(r['r'],4), n_min=r['n_min'], lt=round(r['length_term'],4), reasons=r['reasons']))
# A fabricated response: calls=[] kinds all model
good = rec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56'), 120, 0)
print('A calls', good['calls'])
show('A', score_group(FT, [good], CFG))
# B direct numeric detached
SZ = dict(prompt_id='p', type='object_size_estimation', question='What is the length of the longest dimension (length, width, or height) of the table, measured in centimeters?', options=None, gt_answer='120')
for body in ['Step 1: the table is about 80 cm long.\n', 'Step 1: find the table, first seen in frame 3.\n', 'Step 1: I look at the room.\n']:
    show('B '+body.strip(), score_group(SZ, [rec(direct(body, '120'), 20)], CFG))
# C recovery vs direct, same n
FAILCALL = '<ground obj="zebra">\n<tool_response>\nzebra: not seen\n</tool_response>\n'
tab = dict(CFG, n_min={'object_rel_distance': {'direct': 20, 'head': 60}})
rows = score_group(REL, [rec(direct(REL_SHORT, 'D'), 50, 0), rec(program(FAILCALL + REL_SHORT, 'D'), 50, 1), rec(direct(FAILCALL + REL_SHORT, 'D'), 50, 2)], tab)
show('C', rows)
# E partial MRA short vs exact long
rows = score_group(dict(FT, gt_answer='10.56'), [rec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56'), 5000, 0),
    rec(program(FT_BODY.format(conv=''), '3.22'), 100, 1)], dict(CFG, n_min={'object_abs_distance': {'head': 100}}))
show('E', rows)
