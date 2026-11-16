import sys,json
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_vsti/work/c')
import scorer
for text,item in [('<think>x</think>\n<answer>1.31</answer><|im_end|>',dict(options=None,ground_truth='1.31')),
                  ('<think>x</think>\n<answer>B</answer><|im_end|>',dict(options=['A. left','B. right'],ground_truth='B')),
                  ('</think>\n1.31',dict(options=None,ground_truth='1.31'))]:
    print(repr(scorer.final_text(dict(text=text))),scorer.score(scorer.final_text(dict(text=text)),item))
