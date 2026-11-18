"""A/B review isolation and fail-closed regression cases."""
from packet_config import PINS
from review_policy import build_chain, REVIEW_FILES
base={name:'# GO — LOCAL ANTECEDENT' for name in REVIEW_FILES[:-1]}
a=PINS['identity'];b='0647a0df37862199ea4a766875969d28e7fbfc66821ea5f5a0d00f0607452f92'
def check(text, okay):
    try:
        result=build_chain(dict(base,**{'r8.txt':text}),a,PINS['tree'],PINS['outer'])
    except ValueError:
        assert not okay,text
    else:
        assert okay,text
        assert result['packet']=='A' and result['final_reviewer']=='review_r1p8'
        assert len(result['reviews'])==8 and not result['production_go_granted']
positive=[
 '## Packet A: GO\n'+a+'\n## Packet B: NO-GO\n'+b,
 '# Dual review\n## Packet B\nVerdict: NO-GO\n'+b+'\n## Packet A\nVerdict: GO\n'+a,
 '## Packet A\n**GO AFTER FIXES**\n'+a+'\n- LOW: Add an optional note.\n## Packet B: NO-GO\n- HIGH: B is blocked.',
 '| Packet | Verdict | Config |\n| A | GO | '+a+' |\n| B | NO-GO | '+b+' |',
 '# Packet A: GO\n'+PINS['outer'],
]
negative=[
 '## Packet A: GO AFTER FIXES — LOW: required before proof\n'+a+'\n- LOW: Optional.',
 '## Packet A: GO AFTER FIXES — HIGH: fix this\n'+a+'\n- LOW: Optional.',
 '## Packet A: GO AFTER FIXES — fix this\n'+a+'\n- LOW: Optional.',
 '## Packet A: GO\n'+b+'\n| B | PENDING | '+a+' |',
 '## Packet A: NO-GO\n'+a+'\n## Packet B: GO\n'+b,
 '## Packet A: PENDING\n'+a+'\n## Packet B: GO\n'+a,
 '## Packet A: GO\n'+b+'\n## Packet B: GO\n'+a,
 '# GO\n'+a+'\n## Packet B: GO\n'+b,
 '## Packet A: GO\n'+a+'0',
 '## Packet A: GO / NO-GO\n'+a,
 '## Packet A: GO?\n'+a,
 '## Packet A: GO IF ready\n'+a,
 '## Packet A: GO whatever\n'+a,
 '## Packet A: GO\n'+a+'\n## Packet A: GO\n'+a,
 '## Packet A: GO AFTER FIXES\n'+a+'\n- MEDIUM: Must fix.\n## Packet B: GO\n- LOW: Optional.',
 '## Packet A: GO AFTER FIXES\n'+a+'\n- LOW: Optional.\n- Fix this too.',
 '## Packet A: GO AFTER FIXES\n'+a+'\nMEDIUM: unresolved problem.\n- LOW: Optional.',
 '## Packet A: GO AFTER FIXES\n'+a+'\n- LOW: blocking fix.',
 '## Packet A: GO AFTER FIXES\n'+a+'\n## Packet B: GO AFTER FIXES\n- LOW: Optional.',
 '| A | NO-GO | '+a+' |\n| B | GO | '+b+' |',
 '| A | GO | '+b+' |\n| B | GO | '+a+' |',
]
positive += ['Packet A: p_9dd2fbb7.tar '+PINS['outer']+' config '+a+': GO.', 'Packet A: GO AFTER FIXES\n'+a+'\n- LOW: Optional note.']
negative += positive[1:4]
positive = [positive[0], positive[4], positive[5], positive[6]]
for text in positive:check(text,True)
for text in negative:check(text,False)
print(f'PASS A/B isolation: {len(positive)} acceptances and {len(negative)} fail-closed refusals')
