"""Count-first and tally renderers with a strict semantic gate; no kit patches."""
import collections
import re

def render(categories, evidence, answer, form='B'):
    lines=['<think>'];totals=[]
    for step,(cat,instances) in enumerate(zip(categories,evidence),1):
        n=len(instances);totals.append(n)
        frames=sorted(f for _,f in instances);noun='object' if n==1 else 'objects';verb='is' if n==1 else 'are'
        if form=='B':
            entries='; '.join(f'{i} of {n}, frame {f}' for i,f in enumerate(frames,1))
            lines.append(f'Step {step}: I count {n} distinct {noun} labelled "{cat}", each by the frame where it first appears: {entries}.')
            lines.append(f'So there {verb} {n} {noun} labelled "{cat}".')
        else:
            counts=collections.Counter(frames)
            entries='; '.join(f'frame {f}: {counts[f]}' for f in sorted(counts))
            lines.append(f'Step {step}: "{cat}": {entries}, total {n}.')
    a,b=totals;na='object' if a==1 else 'objects';nb='object' if b==1 else 'objects';relation='equals' if a==b else 'is more than' if a>b else 'is less than'
    lines.append(f'Step 3: Compare the counts: {a} {na} labelled "{categories[0]}" against {b} {nb} labelled "{categories[1]}"; {a} {relation} {b}.')
    return '\n'.join(lines)+f'\n</think>\n\n{answer}'

def validate(row,form=None):
    cats=re.findall(r'"([a-z][a-z -]*)"',row['student_input']['question'])
    assert len(cats)==len(set(cats))==2
    lines=row['target'].splitlines();form=form or row['provenance']['relative_count_counts']['form']
    assert lines[0]=='<think>' and lines[-3:]==['</think>','',row['answer']]
    assert len(lines)==(9 if form=='B' else 7)
    totals=[];hist=[]
    for j,cat in enumerate(cats):
        if form=='B':
            m=re.fullmatch(r'Step '+str(j+1)+r': I count ([1-9][0-9]*) distinct objects? labelled "'+re.escape(cat)+r'", each by the frame where it first appears: (.+)\.',lines[1+2*j]);assert m
            n=int(m[1]);noun='object' if n==1 else 'objects';verb='is' if n==1 else 'are'
            assert f'{n} distinct {noun} labelled' in lines[1+2*j]
            entries=m[2].split('; ');assert len(entries)==n
            frames=[]
            for i,e in enumerate(entries,1):
                v=re.fullmatch(r'([1-9][0-9]*) of ([1-9][0-9]*), frame ([1-9][0-9]*)',e);assert v
                k,total,f=map(int,v.groups());assert k==i and total==n and 1<=f<=32
                frames.append(f)
            assert frames==sorted(frames)
            assert lines[2+2*j]==f'So there {verb} {n} {noun} labelled "{cat}".'
            h=dict(collections.Counter(frames))
        else:
            m=re.fullmatch(r'Step '+str(j+1)+r': "'+re.escape(cat)+r'": (.+), total ([1-9][0-9]*)\.',lines[1+j]);assert m
            n=int(m[2]);h={};previous=0
            for e in m[1].split('; '):
                v=re.fullmatch(r'frame ([1-9][0-9]*): ([1-9][0-9]*)',e);assert v
                f,c=map(int,v.groups());assert previous<f<=32;h[f]=c;previous=f
            assert sum(h.values())==n
        totals.append(n);hist.append(h)
    a,b=totals;na='object' if a==1 else 'objects';nb='object' if b==1 else 'objects';word='equals' if a==b else 'is more than' if a>b else 'is less than'
    assert lines[-4]==f'Step 3: Compare the counts: {a} {na} labelled "{cats[0]}" against {b} {nb} labelled "{cats[1]}"; {a} {word} {b}.'
    relation='equal number' if a==b else 'more' if a>b else 'fewer'
    options=row['student_input']['options'];assert len(options)==3
    choice={o.split('. ',1)[0]:o.split('. ',1)[1] for o in options}
    assert set(choice)==set('ABC') and set(choice.values())=={'more','fewer','equal number'}
    assert choice[row['answer']]==relation and row['question_type']=='relative_count'
    return cats,totals,hist,'=' if a==b else '>' if a>b else '<'
