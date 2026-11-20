"""Call incidence only: paired room bootstrap; no item-answer scoring."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tarfile

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',ROOT/'src/probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def percentile(x,p):
    x=sorted(x);v=(len(x)-1)*p;i=int(v);j=min(i+1,len(x)-1)
    return x[i]+(x[j]-x[i])*(v-i)


def score(rows, receipt, draws=10000, seed=20261120):
    frozen=hashlib.sha256((ROOT/'FROZEN.json').read_bytes()).hexdigest()
    binding=json.loads((ROOT/'FROZEN.json').read_text())
    expected={(r['i'],a):r for r in json.loads((ROOT/'PAIR_MAP.json').read_text()) for a in (0,1)}
    assert receipt.get('frozen')==frozen
    assert receipt.get('artifact')==binding['checkpoint']['artifact']['sha256']
    assert receipt.get('mode')=='g' and receipt.get('tools_served')==0
    assert receipt.get('max_new_tokens')==64 and receipt.get('external_components_loaded') is False
    grouped={}; seen=set()
    for r in rows:
        key=(r['i'],r['a']);assert key in expected and key not in seen
        seen.add(key);assert r['r']==expected[key]['r']
        assert type(r['n']) is int and 1<=r['n']<=64 and r['n']==len(r['tokens'])
        assert all(type(t) is int for t in r['tokens'])
        opened=probe.detect(r['text'])
        assert type(r['g']) is bool and r['g']==(0 in opened)
        assert r['o']==[i for i in opened if i]
        assert r['finish'] in ('call','cap','eos')
        assert (r['finish']=='call')==bool(opened)
        if r['finish']=='cap':assert r['n']==64
        grouped.setdefault(r['r'],[[],[]])[r['a']].append(int(r['g']))
    assert receipt['records']==len(rows)
    if seen!=set(expected) or not receipt.get('passed'):
        return dict(complete=False,observed=len(rows),expected=580,gate='incomplete; no verdict',
                    arm_D='closed',frozen=frozen)
    rooms=sorted(grouped)
    assert len(rooms)==98 and all(len(grouped[r][0])==len(grouped[r][1]) for r in rooms)
    counts=[[sum(grouped[r][a]) for a in (0,1)] for r in rooms]
    sizes=[len(grouped[r][0]) for r in rooms]
    rates=[sum(x[a] for x in counts)/sum(sizes) for a in (0,1)]
    rng=random.Random(seed);samples=[[],[],[]]
    for _ in range(draws):
        indices=[rng.randrange(len(rooms)) for _ in rooms]
        n=sum(sizes[i] for i in indices)
        a,b=[sum(counts[i][arm] for i in indices)/n for arm in (0,1)]
        for dest,value in zip(samples,(a,b,b-a)):dest.append(value)
    result=dict(complete=True,pairs=290,rooms=98,draws=draws,seed=seed,frozen=frozen,
        bootstrap='paired rooms with replacement; item-weighted; percentile 95%',
        gate='no change' if rates[1]>=.95 else 'report to orchestrator via lane',arm_D='closed')
    for name,rate,sample in zip(('ORIG','REVSI','REVSI_minus_ORIG'),(*rates,rates[1]-rates[0]),samples):
        result[name]=dict(rate=rate,ci95=[percentile(sample,.025),percentile(sample,.975)])
    result['other_calls']={name:{probe.OPENINGS[i]:sum(i in r['o'] for r in rows if r['a']==a)
                                for i in range(1,len(probe.OPENINGS))}
                           for a,name in enumerate(('ORIG','REVSI'))}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('return_archive');p.add_argument('--out',required=True)
    a=p.parse_args();path=Path(a.return_archive)
    assert path.stat().st_size<=50000000
    with tarfile.open(path) as t:
        members=t.getmembers();assert all(m.isfile() for m in members)
        assert sum(m.size for m in members)<=50000000
        assert len({m.name for m in members})==len(members)
        assert {m.name for m in members}<={'0.jsonl','1.json','2.json'}
        if '1.json' not in {m.name for m in members}:
            result=dict(complete=False,gate='incomplete; no verdict',arm_D='closed')
        else:
            receipt=json.load(t.extractfile('1.json'))
            rows=[json.loads(x) for x in t.extractfile('0.jsonl')] if '0.jsonl' in {m.name for m in members} else []
            result=score(rows,receipt)
    Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
