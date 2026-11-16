"""Authenticate deliverables and record the CPU-only build outcome."""
from pathlib import Path
from collections import Counter
import datetime,json,re,sys,tarfile,hashlib
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine

package=load(B/'out/PACKAGE.json');family=load(checked(package['family']))
assert family['code_sources']==engine.source_pins()
for key in ('code','reference'):checked(package[key])
with tarfile.open(checked(package['code'])) as archive:
    for member in archive:
        assert member.isfile()
        assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==sha(B/'code'/member.name)
# Compare V1 with its own sealed source table; this build never edits its tree.
v1=B.parent/'01_vsti';parent=load(v1/'out/FAMILY.json')
unchanged=all(sha(v1/'code'/name)==value for name,value in parent['code_sources'].items())
assert unchanged
assert sha(v1/'out/c.tar')=='f04cac666cce32b5ff97c063cb721872b80299324e8ebbf651835ab35dd6d27c'
assert sha(v1/'out/FAMILY.json')=='a0218d5e8a04755c72a6db3f3c7664960b3d833d77ec92b68157b1ab8ff3bcda'
dump(B/'out/REFRESH.json',dict(source=pin(v1/'out/c.tar'),family=pin(v1/'out/FAMILY.json'),v1_sources_unchanged=unchanged,
    stopped_attempt_evidence_accepted=False,method='Fresh V1 code, tests, rehearsal and helper copies; all new evidence recomputed.'))

def test_log(name):
    path=B/'out'/name;text=path.read_text();match=re.search(r'Ran (\d+) tests? in ([0-9.]+)s',text)
    assert match and text.rstrip().endswith('OK'),name
    return dict(run=int(match[1]),seconds=float(match[2]),passed=True,log=pin(path))
tests=dict(v1_and_new=test_log('tests_v1b.log'),inherited=test_log('legacy_tests.log'),inherited_extra=test_log('legacy_extra.log'))
legacy=load(B/'out/LEGACY_TESTS.json');extra=load(B/'out/LEGACY_EXTRA.json')
not_run=[r for r in legacy['inventory'] if not r['executed'] and r['test'] not in extra['tests']]
tests['inherited_unexecuted']=len(not_run);tests['inherited_unexecuted_reason']='Listed individually in LEGACY_TESTS.json; require unavailable allocation fixtures or forbidden filesystem cleanup.'
dump(B/'out/TESTS.json',tests)
census=load(B/'out/UNEXECUTED.json');assert census['passed'] and census['v1_v1b_counts'].get('UNEXPLAINED',0)==0
for row in census['files']:assert sha(B/row['file'])==row['sha256']
logic=load(B/'work/rehearsal_delivery/RESULT.json');cli=load(B/'work/cli_delivery/RESULT.json')
assert logic['passed'] and cli['passed'] and logic['items']==cli['items']==9
for run,path in [(logic,B/'work/rehearsal_delivery'),(cli,B/'work/cli_delivery/cell')]:
    request=load(path/'j/REQUEST.json');assert request['sources']==family['code_sources']
assert load(B/'out/GEOMETRY_CPU.json')['passed']
assert load(B/'out/RETURN_CPU.json')['passed']
assert load(B/'out/RELEASE_CHECK_SYNTHETIC.json')['passed']
for p in [B/'out/SCORER_PINS.json']:
    p.write_text(p.read_text().replace('builds/01_vsti','builds/02_vsti_b'))
# The prior real tower result is provenance, not a claim of a V1b tower run.
dump(B/'out/rehearsal/REAL_RESULT.json',dict(status='not_run_in_v1b',prior=pin(v1/'out/rehearsal/REAL_RESULT.json'),synthetic_rehearsal=pin(B/'work/rehearsal_delivery/RESULT.json')))
paths=[p for folder in ('code','tests','out','work','events') for p in (B/folder).rglob('*') if p.is_file()]
size=sum(p.stat().st_size for p in paths)+sum(p.stat().st_size for p in B.iterdir() if p.is_file())
assert size<6_000_000_000
dump(B/'out/STORAGE.json',dict(bytes=size,limit_bytes=6_000_000_000,scope=str(B),measured_before_final_receipts=True))
release=load(B/'out/RELEASE_CHECK.json')
assets=dict(full_frames_present=(R/'in/vsti/frames').is_dir(),release_videos_present=[s for s in ('scene0011_00','scene0077_01','scene0139_00','scene0334_02','scene0690_01') if (R/'in/vsti/release5'/(s+'.mp4')).is_file()],
    upload_receipt_present=(R/'work/streams/native_r4_upw.RECEIPT.json').is_file())
dump(B/'out/ASSET_STATUS.json',assets)
value=dict(status='BUILT_CPU_VERIFIED_PENDING_OPERATOR',launch_ready=False,package=package,tests=tests,
    rehearsal=dict(logic=pin(B/'work/rehearsal_delivery/RESULT.json'),cli=pin(B/'work/cli_delivery/RESULT.json'),namespace=pin(B/'out/rehearsal/NAMESPACE.json')),
    geometry_cpu=pin(B/'out/GEOMETRY_CPU.json'),release=pin(B/'out/RELEASE_CHECK.json'),return_cpu=pin(B/'out/RETURN_CPU.json'),
    coverage=dict(source=pin(B/'out/UNEXECUTED.json'),counts=census['counts'],v1_v1b_unexplained=0,
        inherited_unexplained=census['counts'].get('UNEXPLAINED',0),unreachable_lines=sum(r['count'] for r in census['unreachable'])),
    v1_unchanged=pin(B/'out/REFRESH.json'),assets=pin(B/'out/ASSET_STATUS.json'),storage=pin(B/'out/STORAGE.json'),
    decisions=pin(B/'out/DECISIONS.md'),run_orchard=pin(B/'out/RUN_ORCHARD.md'),run_trinity=pin(B/'out/RUN_TRINITY.md'),
    not_checked=['GPU tower, checkpoint prefill, parity and decoding','Historical GPU trace and geometry equality','Full-frame and release-video checks','V1b namespace outside the sandbox','Orchard staging, submission and remote return channels'],
    unresolved_inputs=['Tower archive SHA and verified cloud generations','Full frames archive and verified copies'],
    canary_order='Preserve fixed V1 keys: four camera and six other items, then 96 camera and 344 other items.')
dump(B/'out/FINAL_RESULT.json',value)
now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%MZ')
diffs=load(B/'out/DIFF_STATS.json')
text=[
 'RESULT: V1b built and CPU-verified; upload pins and operator execution remain pending. Source: out/FINAL_RESULT.json.',
 'V1 code and family remain unchanged. Source: out/REFRESH.json.',
 'Code SHA256 '+package['code']['sha256']+': out/c.tar; receipt out/PACKAGE.json.',
 'Family SHA256 '+package['family']['sha256']+': out/FAMILY.json; receipt out/PACKAGE.json.',
 'Reference payload SHA256 '+package['reference']['sha256']+': out/d.tar; receipt out/PACKAGE.json.',
 f"Code diff versus V1 +{diffs['V1']['added']}/-{diffs['V1']['removed']}; versus C8r +{diffs['C8R']['added']}/-{diffs['C8R']['removed']}. Source: out/DIFF_STATS.json.",
 'Byte-identical scorer copies are listed separately: out/SCORER_COPIES.json.',
 f"Tests passed: {tests['v1_and_new']['run']} V1/new and {tests['inherited']['run']+tests['inherited_extra']['run']} inherited; {len(not_run)} inherited tests remain unexecuted with reasons. Source: out/TESTS.json; out/LEGACY_TESTS.json.",
 'Both sample rehearsals passed on 9 items and 2 captures. Sources: work/rehearsal_delivery/RESULT.json; work/cli_delivery/RESULT.json.',
 'Actual-cache CPU preparation is bit-identical for scale, camera_to_world, K and guard decisions with synthetic heads. Source: out/GEOMETRY_CPU.json.',
 'The proof selection has 3 displacement, 3 direction and 4 rotation items. Source: out/PROOF_KEYS.json.',
 'The synthetic MP4 comparison and complete-return archive test pass; remote channels were mocked. Sources: out/RELEASE_CHECK_SYNTHETIC.json; out/RETURN_CPU.json.',
 'Release videos and full frames are absent; runnable checks are provided. Sources: out/ASSET_STATUS.json; out/RUN_TRINITY.md.',
 'V1/V1b unexplained reachable lines: 0. Inherited unexplained lines: '+str(census['counts'].get('UNEXPLAINED',0))+'. Source: out/UNEXECUTED.json.',
 'Unexecuted counts: '+json.dumps(census['counts'],sort_keys=True)+'. Source: out/UNEXECUTED.json.',
 'Primary packet, upload verification, H100 submission and resume commands: out/RUN_ORCHARD.md.',
 'Fallback and namespace rehearsal command with --fixture-tower: out/RUN_TRINITY.md.',
 'Fixed canary membership leaves 96 camera and 344 other items. Sources: out/CANARY_KEYS.json; out/DECISIONS.md; out/SIZING.md.',
 'No network, GPU, SSH, Git or agent delegation was used. No job was submitted.',
 'Unchecked GPU, namespace, full-frame, release-video and remote paths are listed in out/FINAL_RESULT.json.'
]
assert len(text)<=40
(B/'events'/f'{now}_RESULT_final.md').write_text('\n'.join(text)+'\n')
(B/'STATUS.md').write_text('V1b is built and CPU-verified. The code and family are sealed in out/PACKAGE.json. Upload pins, full frames, release videos and operator GPU/namespace execution remain pending. See out/FINAL_RESULT.json and out/RUN_ORCHARD.md.\n')
print(json.dumps(dict(status=value['status'],tests=tests['v1_and_new']['run'],inherited=tests['inherited']['run']+tests['inherited_extra']['run'],unexplained_authored=0,bytes=size,code=package['code']['sha256'],family=package['family']['sha256'],event=str(B/'events'/f'{now}_RESULT_final.md')),indent=2))
