exec(open('load.py').read())
from collections import Counter,defaultdict
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.append(s)
def cnf(th):
    if 'box distance' in th or 'box gap' in th: return 'N_absdist_program_prose(one gap, threshold)'
    if 'to each:' in th: return 'N_reldist_template(camera as object)'
    if re.search(r'closer than|farther than|further than',th): return 'N_two_distances_compared'
    if 'in front of' in th or 'behind' in th or 'foreground' in th: return 'N_order_claim(no number or one number)'
    return 'N_other'
def cud(th):
    if re.search(r'\b(up|down|above|below|rise|higher|lower)\b',th.split('So')[0]) and not 'straight ahead' in th: return 'U_vertical_offset_stated'
    if 'straight ahead' in th: return 'U_horizontal_bearing(direction template)'
    return 'U_other'
def clr(th):
    if 'straight ahead' in th: return 'L_bearing'
    return 'L_other'
def crd(r,k):
    th=thinktext(r); d=dict((a.strip(),float(b)) for a,b in re.findall(r'([A-Za-z][A-Za-z \-]*?) (\d+\.\d+) m',th.split('to each:')[-1]))
    return 'R_template_zero_distance_picked' if any(v==0 for v in d.values()) else 'R_template_fabricated_nonzero'
for qt in REL:
    ks=[k for k in nat if nat[k]['question_type']==qt]
    g=defaultdict(lambda:[0,0])
    for k in ks:
        r=nat[k]; th=thinktext(r)
        c=crd(r,k) if 'rel_dist' in qt else cnf(th) if qt.endswith('nf') else cud(th) if qt.endswith('ud') else clr(th)
        g[c][0]+=1; g[c][1]+=r['score']
        # does conclusion follow? answer word vs CoT "So" line
    P(qt,{c:f"{v[0]} items, {100*v[1]/v[0]:.0f}% right, {v[0]-int(v[1])} wrong" for c,v in g.items()})
# ud: does the 'So' line name up/down?
ks=[k for k in nat if nat[k]['question_type'].endswith('ud')]
c=Counter()
for k in ks:
    th=thinktext(nat[k]); so=th.strip().split('\n')[-1].lower()
    c[('names_up_down' if re.search(r'\b(up|down|above|below|higher|lower)\b',so) else 'names_left_right_or_none', nat[k]['score'])]+=1
P('ud conclusion line',dict(c))
ks=[k for k in nat if nat[k]['question_type'].endswith('nf')]
c=Counter()
for k in ks:
    th=thinktext(nat[k]); so=th.strip().split('\n')[-1].lower()
    c['mentions_camera_in_conclusion' if 'camera' in so else 'no_camera']+=1
    c['ref_object_named_with_number' ]+=0
P('nf conclusion',dict(c))
open('a5.txt','w').write('\n'.join(out))
