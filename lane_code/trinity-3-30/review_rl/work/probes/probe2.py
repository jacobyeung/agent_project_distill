import torch
from rltests.test_reward import rec, direct, program, FT_BODY, CFG
from rlkit.reward import score_group
from rlkit import gate as G
SZ = dict(prompt_id='p', type='object_size_estimation', question='What is the length of the longest dimension (length, width, or height) of the table, measured in centimeters?', options=None, gt_answer='120')
B = 'Step 1: find the table, first seen in frame 3.\n'
rows = score_group(SZ, [rec(direct(B, '120'), 5000, 0), rec(direct(B, '100'), 20, 1)], CFG)
print('E2', [(r['c'], r['g'], round(r['r'], 3)) for r in rows])
# D numeric options: replay check vacuous
Q = 'What is the distance between the cup and the trash can (in meters)?'
NOPT = dict(prompt_id='p', type='object_abs_distance', question=Q, options=['A. 1.0 m', 'B. 2.6 m', 'C. 5.0 m', 'D. 8.0 m'], gt_answer='B')
body = FT_BODY.format(conv='Converting: 3.22 x 0.001 = 0.00322.\nAdding: 0.00322 + 2.54 = 2.54322.\n')
print('D direct call', G.program_option(body, NOPT, 'B'))
print('D answer far from final witness', G.program_option(FT_BODY.format(conv=''), dict(NOPT, options=['A. 0.1 m','B. 3.0 m','C. 9.0 m','D. 20.0 m']), 'A'))
# F temperature mismatch
import sys; sys.path.insert(0, 'grpo_tree')
from student_pilot import grpo_loss as L
torch.manual_seed(0)
logits = torch.randn(6, 50); labels = torch.randint(0, 50, (1, 6)); valid = torch.ones(1, 6, dtype=torch.bool)
reserved = torch.tensor([48, 49])
lg = logits.clone(); lg[:, reserved] = -float('inf')
old07 = torch.log_softmax(lg / 0.7, -1).gather(-1, labels[0][:, None])[:, 0]
batch = dict(aux_pg_mask=torch.ones(1, 7, dtype=torch.bool), aux_old_logp=torch.cat([torch.zeros(1), old07])[None],
             aux_ref_logp=torch.cat([torch.zeros(1), old07])[None], aux_pg_advantage=torch.tensor([1.0]), aux_pg_reserved=reserved)
loss, m = L.loss_from_logits(logits, labels, valid, batch, {})
print('F default recipe vs sampler T=0.7: ratio', m['ratio'], 'clip_fraction', m['clip_fraction'], 'kl', m['kl'])
loss, m = L.loss_from_logits(logits, labels, valid, batch, {'grpo': {'temperature': 0.7}})
print('F matched T: ratio', m['ratio'])
