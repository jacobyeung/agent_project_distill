"""Publish the fixed merge-eligibility screen from the completed base pass."""
import json
import summarize_train as S
import serving_reference as R
import math_v2 as M

def main():
    arms=S.byarm(S.load('base'));rows=[]
    for tau in M.TAUS:
        base=arms[f'A4_obj_{tau:.2f}_best1']
        alltrain=S.precision(base)
        folds={str(k):S.precision([r for r in base if r['fold']!=k]) for k in range(5)}
        variants={rule:S.mean(arms[f'A4_obj_{tau:.2f}_{rule}']) for rule in M.RULES}
        rows.append(dict(tau=tau,all_train=alltrain,other_four_folds=folds,in_sample_variant_mra=variants))
    R.code_pins();R.write(R.OUT/'MERGE_ELIGIBILITY.json',dict(threshold=.90,rows=rows,
        use='Eligibility only; safety evidence comes from OOF selected merges'))
    lines=['All-train merge eligibility (not OOF safety evidence). Threshold: 90%.',
        'Tau | Correct additions | All additions | Precision']
    lines += [f'{r["tau"]:.2f} | {r["all_train"]["correct"]} | {r["all_train"]["added"]} | {r["all_train"]["precision"]:.6f}' for r in rows]
    (R.OUT/'MERGE_ELIGIBILITY.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':main()
