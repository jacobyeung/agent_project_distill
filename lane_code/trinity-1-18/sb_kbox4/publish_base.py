"""Publish complete base-arm training prices while selector fitting runs."""
import json
import serving_reference as R
import summarize_train as S

def main():
    arms=S.byarm(S.load('base'))
    tables=set(R.read(R.ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    frozen=json.loads(R.read(R.OUT/'FREEZE.json'))
    summary={a:dict(rows=len(rs),mra=S.mean(rs),refusals=sum(r['prediction'] is None for r in rs),selection='in-sample') for a,rs in arms.items()}
    contrasts=dict(oracle_minus_A0=S.contrast(arms['A1_oracle_select'],[r for r in arms['A0_deployed'] if r['row_id'] in tables]),
        GT_masks_minus_A0=S.contrast(arms['A2_gt_masks'],arms['A0_deployed']),
        S4_today_minus_A0=S.contrast(arms['A9_s4_today'],arms['A0_deployed']),
        object_cf_minus_A0=frozen['object_gain'],fused_cf_minus_A2=frozen['fused_gain'])
    R.code_pins();R.write(R.OUT/'BASE_TABLE.json',dict(command='bash run.sh publish_base.py',arms=summary,contrasts=contrasts,
        selector_status='PENDING',heldout_status='DEFERRED',A6_status='DEFERRED'))
    lines=['K1 TRAINING base arms. Individual arm means are in-sample; rule gains below are cross-fitted.',
        'Command: bash run.sh publish_base.py','Arm | Rows | MRA | Refusals']
    lines += [f'{a} | {s["rows"]} | {s["mra"]:.4f} | {s["refusals"]}' for a,s in sorted(summary.items())]
    lines += ['','Paired contrast | Delta [95% CI]']+[f'{a} | {s["estimate"]:+.4f} [{s["ci95"][0]:+.4f}, {s["ci95"][1]:+.4f}]' for a,s in contrasts.items()]
    lines += ['','Selector pricing remains pending. Held-out and A6 remain deferred.']
    (R.OUT/'LADDER_BASE.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[-9:]))

if __name__=='__main__':main()
