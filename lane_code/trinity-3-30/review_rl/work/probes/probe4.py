from rltests.test_reward import rec, program, FT, FT_BODY, CFG
from rlkit import select as SEL, sampler as S, grpo as GR
r = rec(program(FT_BODY.format(conv='Converting to feet: 3.22 x 3.28084 = 10.56.\n'), '10.56'), 120, 0)
r.update(seed=1, tokens=[5]*120, kinds='s'*120, prompt_ids_sha256='x', response_sources=S.response_sources(dict(heads={}, calls=[]), {}))
out, rep = SEL.select([dict(FT, row={})], {'p': [r]}, reward_cfg=CFG)
print('A-select counts', rep['counts'], 'stream', out['own_rows'][0]['stream'] if out['own_rows'] else None)
gq = dict(heads=dict(ground_queries=[dict(name='cup', backend='ground_v3', source_provenance='gt_instance_masks', presence_source='external_presence')]), calls=[dict(kind='ground')])
print('I gt-provenance ground_v3 query ->', SEL.artifact_policy(dict(gq, response_sources=S.response_sources(gq, {}))))
donor = dict(r, response_sources=dict(r['response_sources'], donor=True), logp_tempered=[-1.0]*120, kinds='s'*120)
row = GR.to_row(dict(FT, row={}), donor, 1.0, [-1.0]*120, [1, 2, 3])
print('GRPO row from donor responses built; keys', sorted(row)[:6], 'has policy field', 'response_policy' in row)
