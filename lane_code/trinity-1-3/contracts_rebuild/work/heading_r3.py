from pathlib import Path
import difflib,re
L=Path(__file__).resolve().parents[1];S=L/'work/src_r3';O=L/'out'
s=(O/'HEADING_DEPENDENCE_R2.md').read_text()
maps={}
def location(m):
    label,path,line=m.groups();line=int(line)
    rel=path.split('/r2_proof/base/')[-1]
    old=L/'work/src_r2'/rel;new=S/rel
    if old.exists() and new.exists():
        if rel not in maps:
            a=old.read_text().splitlines();b=new.read_text().splitlines();mapping={}
            for op,i,j,k,n in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
                for p in range(i,j):mapping[p+1]=min(k+p-i+1,max(k+1,n))
            maps[rel]=mapping
        updated=maps[rel].get(line,line)
    else:updated=line
    label=re.sub(r':\d+$',':'+str(updated),label)
    return f'[{label}]({path.replace("r2_proof", "r3_proof")}:{updated})'
s=re.sub(r'\[([^\]]+)\]\(([^)]+/r2_proof/base/[^):]+):(\d+)\)',location,s)
s=s.replace('tests_r2','tests_r3').replace('_R2','_R3')
lines=[]
for line in s.splitlines():
    if line.startswith('| angle ') or line.startswith('| calculator waypoint turn '):
        fields=line.split(' | ')
        if 'horizontal components' in line:
            fields[2]='no'
            fields[3]='Calculator arithmetic uses its registered rounded operands; capture heading is not a dispatch condition.'
            fields[5]='Serve the ordinary calculator response, including vectors; preserve arithmetic and syntax refusals.'
            line=' | '.join(fields)
    if line.startswith('- [trace_format/calculator.py:') and 'Calculator horizontal' in line:continue
    if line.startswith('| pose |') and ('horizontal' in line or '| yaw |' in line):
        line=line.replace('yes |','frames 1 and k |')
        line=line.replace('Replace each component with heading unavailable.', 'Withhold when either the reference or queried heading is unavailable.')
    lines.append(line)
s='\n'.join(lines)+'\n'
s+='''
## Frame-specific rules

| Call | Required headings | Fields retained without those headings |
|---|---|---|
| move(i,j) | i for dx/dz | dy and Euclidean distance |
| turn(i,j) | i and j | Named unavailable status |
| pose(k) | reference and k for horizontal centre and yaw | Vertical centre |
| depth_at(k) | reference for f1 horizontal coordinates | Camera coordinates, height, spread and labels |
| angle and point-waypoint turn | None at dispatch | Ordinary calculator arithmetic and error text |

The default heading threshold is 0.3 and remains separate from the fixed convention guard. Source: [contracts.py](SOURCE/trace_format/contracts.py).

Gravity-noise evidence compares each served field with the same perturbed geometry under disabled availability checks. Relative horizontal move, turn, and distance are stable in attack A; dy changes because the gravity vector itself changes. Attack B and the later-frame fixture withhold the unstable horizontal fields. The complete noisy strings and calls are in [DECODE_ATTACK_R3.json](OUT/DECODE_ATTACK_R3.json). Exact vertical endpoints can also make the disabled legacy basis refuse; the partial path still serves the direct Euclidean distance and gravity projection.

Genuine all-frame rolls of 30, 45, and 80 degrees pass for both storage orientations. A 90-degree roll lies on the convention sign boundary and is not evidence for robust rolled operation. Source: [test_review_r3.py](TESTS/test_review_r3.py).
'''.replace('SOURCE',str(S)).replace('OUT',str(O)).replace('TESTS',str(L/'work/tests_r3'))
s=s.replace('Needs frame-1 heading','Required heading').replace('Undefined-reference behavior','Unavailable-heading behavior')
s=s.replace('Each no entry describes the quantity’s coordinate meaning.', 'A no entry means no heading gate; the math column distinguishes geometric independence from calculator operand arithmetic.')
s=s.replace('Pose yaw of a degenerate queried frame, named explicitly.', 'Pose horizontal centre and yaw of a degenerate queried frame, named explicitly.')
s=s.replace('| yes |','| reference |')
for field in ('dx','dz'):
    s=s.replace(f'| move i to j | {field} | no |',f'| move i to j | {field} | source i |')
s=s.replace('| turn i to j | signed turn | no |','| turn i to j | signed turn | endpoints i and j |')
(O/'HEADING_DEPENDENCE_R3.md').write_text(s)
