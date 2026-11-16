"""Reproduce the tuning-only SAM 3 selection and top-five reference."""
import argparse
from pathlib import Path
from probe_common import *


def run(path):
    rules()  # Refuse before reading metrics if the rules are not frozen.
    groups,labels,fits,pins=candidate_inputs()
    top=[];ceiling=[];consistent=[]
    for g in groups:
        good,fit,_=candidate_truth(g,labels[g['object_id']],fits[g['object_id']])
        top.append(float(good[0]));ceiling.append(float(good.any()));consistent.append(float(fit[0]))
    counts=dict(objects=len(groups),on_target=int(sum(top)),top5_ceiling=int(sum(ceiling)),name_consistent=int(sum(consistent)))
    expected=dict(objects=221,on_target=168,top5_ceiling=202,name_consistent=206)
    rooms=[gate.room(*g['scene'].split('/')) for g in groups]
    value=dict(counts=counts,expected=expected,pass_=counts==expected,
               on_target=mean_ci(top,rooms=rooms),top5_ceiling=mean_ci(ceiling,rooms=rooms),name_consistent=mean_ci(consistent,rooms=rooms),input_pins=pins)
    output_metrics(path,value,[RULES_PATH,Path(__file__)],dict(split='tuning',fitting=False))
    if counts!=expected:raise ValueError(f'SAM reference differs: {counts} != {expected}')
    print(counts)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(ROOT/'out/SAM_REFERENCE.json'));run(p.parse_args().out)
