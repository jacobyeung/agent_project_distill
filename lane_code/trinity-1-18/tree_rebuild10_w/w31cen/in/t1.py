"""fix10 Trinity: build W/w31cen/n_go (test seal only) and unit-test b/cn.py with the kit tree's own functions."""
import sys, json, shutil, subprocess, hashlib
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); OLD = W/'w30f1/n_go'; F = W/'w31cen'; NEW = F/'n_go'; IN = F/'in'
sys.path[:0] = [str(W/'w24z11b/work/build24m4x2')]
from support import J, reseal
out = {}
OLDSEAL = '489f7f0fbfb9913066d0840bde40d01fc30927d2d127709e41bb479e554e2e90'
assert J.seal(OLD) == OLDSEAL; out['old_seal'] = OLDSEAL
for name, h in json.loads((IN/'base.json').read_text()).items():
    assert J.sha(OLD/name) == h, name
assert not NEW.exists(), 'w31cen/n_go exists already'
shutil.copytree(OLD, NEW, copy_function=shutil.copy2)
for name in ('sc.py', 'pl.py', 'cn.py'):
    shutil.copy2(IN/name, NEW/'b'/name)
(NEW/'b/cn.py').chmod((NEW/'b/sc.py').stat().st_mode & 0o777)
T = F/'tree'
if not T.exists():
    T.mkdir(); subprocess.run(['tar', 'xf', str(OLD/'k/t_e047002134f979bd.tar'), '-C', str(T)], check=True)
sys.path.insert(0, str(T))
seal = reseal(NEW); out['test_seal'] = seal
from launch_r1.build import verify
out['verify_kit_tree'] = verify(NEW) == seal
out['changed'] = sorted(str(p.relative_to(NEW)) for p in NEW.rglob('*') if p.is_file() and (not (OLD/p.relative_to(NEW)).exists() or J.sha(OLD/p.relative_to(NEW)) != J.sha(p)))
out['sha256'] = {n: J.sha(NEW/n) for n in out['changed']}
r = subprocess.run(['diff', '-ruN', str(OLD), str(NEW)], capture_output=True, text=True)
(F/'DIFF.patch').write_text(r.stdout); out['diff_sha256'] = hashlib.sha256(r.stdout.encode()).hexdigest()
# ---- unit tests with the kit tree's functions
sys.path.insert(0, str(NEW/'b'))
import cn
from student_pilot.s1_exclusions import Exclusions, coverage_report
from student_pilot.p3_provenance import file_pin, write
DEV = dict(path='/scratch/jjyeung/orch_n30/sb_framepool/work/blobs/a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5.json', sha256='a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5')
BEN = dict(path='/scratch/jjyeung/orch_n30/sb_afrev/tar_x/inputs/lists/3119aa4a.raw', sha256='3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970')
assert J.sha(Path(DEV['path'])) == DEV['sha256'] and J.sha(Path(BEN['path'])) == BEN['sha256']
files = dict(dev=DEV, benchmark=BEN)
rule0 = Exclusions(DEV, BEN)
dev_names = sorted(rule0.names['dev'])[:400]; ben_names = sorted(rule0.names['benchmark'] - rule0.names['dev'])[:200]
rows = []
for i in range(3000):
    kind = i % 5
    if kind == 0:
        d, s = dev_names[i % len(dev_names)].split('/', 1); row = dict(dataset=d, scene=s)
    elif kind == 1:
        d, s = ben_names[i % len(ben_names)].split('/', 1); row = dict(dataset=d, scene=s, provenance=dict(note='x'))
    elif kind == 2:
        row = dict(dataset='d2', scene='zz_fix10_unlisted_%d' % i, routing=dict(room=dev_names[(i*7) % len(dev_names)], question_type='q'))
    else:
        row = dict(dataset='d2', scene='zz_fix10_unlisted_%d' % i, other=list(range(3)), routing=dict(answer='a'))
    row['big'] = 'y' * 50; rows.append(row)
# T1: view() keeps exactly what both counters read
r = Exclusions(DEV, BEN)
out['T1_view_equivalent'] = all(r.identifiers(cn.view(x)) == r.identifiers(x) and r.census.identities(cn.view(x)) == r.census.identities(x) for x in rows)
admit = lambda i: i % 3 != 0  # the stream reads two thirds of the store
items = [(i, cn.view(x)) for i, x in enumerate(rows)]
inside = [it for it in items if admit(it[0])]; outside = [it for it in items if not admit(it[0])]
dev_a, test_a, listed_a = cn._count('pose_a2v3', inside, files)
dev_o, test_o, listed_o = cn._count('pose_a2v3', outside, files)
dev_w, test_w, _ = cn._count('pose_a2v3', items, files)
out['T2_whole_eq_admitted_plus_outside'] = dict(whole=[dev_w, test_w], admitted=[dev_a, test_a], outside=[dev_o, test_o], ok=(dev_w == dev_a+dev_o and test_w == test_a+test_o))
# the stream's filter sees only the admitted rows (as the pose mix does), named as apply() names them
flt = Exclusions(DEV, BEN)
flt.expect('pose/0', (x for i, x in enumerate(rows) if admit(i)), dict(t='fix10'))
for i, x in enumerate(rows):
    if admit(i):
        flt.keep(x, 'pose/0')
D = F/'t'; D.mkdir(exist_ok=True)


def policy(dev, test, tag):
    write(D/(tag+'.json'), dict(schema='dev_s1_manifest_v1', withhold_file=DEV, benchmark_file=BEN, exact_rebuilt_population=True,
          withheld_training_rows=dict(pose_a2v3=dict(path='synthetic', rows_withheld=dev, benchmark_rows_withheld=test))))
    return dict(schema='s1-scene-coverage-v1', reference=file_pin(D/(tag+'.json')), source_map=dict(pose=[dict(source='pose_a2v3')]))


def run(p):
    try:
        rep = coverage_report(flt, {}, p)
        return 'PASS ' + json.dumps({k: [v['observed_dev_matches'], v['observed_benchmark_matches'], v['reference_dev_rows'], v['reference_benchmark_rows']] for k, v in rep['coverage']['sources'].items()})
    except Exception as e:
        return 'REFUSE ' + type(e).__name__ + ': ' + str(e)


out['T3_admitted_census'] = run(policy(dev_a, test_a, 'admitted'))
out['T4_whole_store_census_control'] = run(policy(dev_w, test_w, 'whole'))
key = next(k[0] for k in listed_o if k[1])  # one dev-listed row of the outside population, planted into the admitted one
planted = [it for it in outside if it[0] == key]
dev_p, test_p, _ = cn._count('pose_a2v3', inside+planted, files)
out['T5_leak_control'] = dict(planted_row=key, census=[dev_p, test_p], result=run(policy(dev_p, test_p, 'leak')))
# pool path of _count: per-source expect/keep with the source tag stripped
pool_items = [(('S%d' % (i % 3), 'q%d' % i), dict(cn.view(x), _pool_source='S%d' % (i % 3))) for i, x in enumerate(rows[:900])]
pdev, ptest, plisted = cn._count('pool', pool_items, files, pool=True)
pd, pt, _ = cn._count('x', [(k, {a: b for a, b in v.items() if a != '_pool_source'}) for k, v in pool_items], files)
out['T6_pool_count_equals_plain_count'] = dict(pool=[pdev, ptest], plain=[pd, pt], ok=(pdev, ptest) == (pd, pt))
(F/'TEST_T1.json').write_text(json.dumps(out, indent=1, default=str)+'\n')
print(json.dumps(out, indent=1, default=str))
