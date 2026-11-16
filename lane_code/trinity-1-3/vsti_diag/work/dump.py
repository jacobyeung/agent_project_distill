exec(open('load.py').read())
import random
with open('FAILING_ITEMS.md','w') as f:
  for qt in REL:
    ks=sorted((k for k in nat if nat[k]['question_type']==qt and nat[k]['score']==0), key=lambda k:int(k[1:]))
    f.write(f'\n## {qt}: {len(ks)} failing (all listed)\n')
    for k in ks:
        r=nat[k]; t=T[k]
        f.write(f"\n### {k} {S[k]['scene']} GT={S[k]['ground_truth']}({opt(k,S[k]['ground_truth'])}) native={r['answer']} f17={cmp['f17'][k]['official_fuzzy_pred']} p1={cmp['p1m200'][k]['official_fuzzy_pred']}\nQ: {t['question']} {S[k]['options']}\n```\n{thinktext(r).strip()}\n```\n")
