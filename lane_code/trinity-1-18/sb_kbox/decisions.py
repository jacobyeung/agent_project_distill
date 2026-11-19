"""Predeclared decision bars. Missing evidence never becomes a negative finding."""

BAR_NAMES=('replace_box','fused_path','gather_safe','selector_worth',
           'selector_adopt','size_screen','first_seen_screen','tower_challenger')


def judge(evidence):
    result={}
    def add(name,required,test):
        missing=[k for k in required if evidence.get(k) is None]
        result[name]=dict(verdict='MISSING' if missing else ('PASS' if test() else 'FAIL'),
                          missing=missing,evidence={k:evidence.get(k) for k in required})
    e=evidence
    add('replace_box',['rule_train_gain','rule_train_lo','rule_heldout_gain'],
        lambda:e['rule_train_gain']>=3 and e['rule_train_lo']>0 and e['rule_heldout_gain']>0)
    add('fused_path',['fusion_train_gain','fusion_train_lo'],
        lambda:e['fusion_train_gain']>=3 and e['fusion_train_lo']>0)
    if e.get('fusion_train_gain') is not None and e['fusion_train_gain']<1:
        result['fused_path']['action']='the single view is not the limit under this tower; stop fused path'
    add('gather_safe',['member_precision_train'],lambda:e['member_precision_train']>=.90)
    add('selector_worth',['oracle_train_gain'],lambda:e['oracle_train_gain']>=4)
    add('selector_adopt',['nonull_oof_train_lo','nonull_heldout_gain'],
        lambda:e['nonull_oof_train_lo']>0 and e['nonull_heldout_gain']>0)
    add('size_screen',['heldout_scannetpp_size_mra'],lambda:e['heldout_scannetpp_size_mra']>=63.3)
    add('first_seen_screen',['train_exact','train_within_one'],
        lambda:e['train_exact']>=.75 and e['train_within_one']>=.90)
    add('tower_challenger',['tower_train_shared_answered_lo'],lambda:e['tower_train_shared_answered_lo']>0)
    return result
