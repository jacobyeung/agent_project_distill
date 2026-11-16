"""Produce deterministic code and review artifacts from the frozen build sources."""
import ast
from collections import Counter
import difflib
from pathlib import Path
import sys
import tarfile
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *

original=R/'work/c8r/code';current=B/'code'
patch=[];changed=[];added=removed=0
reasons={
 'adapter.py':'Change 1 adapts opaque prompt records and SHA-verified local frames, and changes 5–6 fix the canary and shard order.',
 'policy.py':'Change 3 intercepts non-camera calls at the existing response dispatcher and records recoverable refusals.',
 'paths.py':'Change 7 resolves local code and the supplied authenticated trainer tree.',
 'boundary.py':'Changes 3 and 5 receive a deterministic CPU model boundary that exercises the real token and response loop.',
 'engine.py':'Changes 2–6 run fresh geometry, preserve the gravity guard and replay checks, and commit shard journals.',
 'scorer.py':'Change 9 wraps the unchanged scoring authority and verifies the recorded comparator answers.',
 'report.py':'Change 8 reports official groups, clustered intervals, refusal costs and paired comparisons.',
 'proof.py':'Change 10 runs original-policy repeats and compares token, call, response-byte and answer equality.',
 'proof_stage.py':'Change 10 isolates the original read inputs and returned geometry for the historical proof.',
 'entry.py':'Changes 1–10 expose the same neutral commands to both venues and the CPU harness.',
 'venue.py':'Change 7 constructs the private namespace, validates local archive staging and builds a sealed packet.',
 'orchard.py':'Change 7 uses the common job path and inherited return transport inside an allocation.',
 's0.py':'Change 9 includes a byte-identical copy of score_and_aggregate.py.',
 's1.py':'Change 9 includes a byte-identical copy of scoring.py.',
 's2.py':'Change 9 includes a byte-identical copy of the mechanical score-index authority.',
 's3.py':'Change 9 includes a byte-identical copy of score_record_core.py containing the five-subtask formula.',
}
for p in sorted(current.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(current);old=original/rel
 if old.is_file() and old.read_bytes()==p.read_bytes():continue
 a=old.read_text().splitlines(True) if old.is_file() else []
 b=p.read_text().splitlines(True)
 lines=list(difflib.unified_diff(a,b,fromfile='a/'+str(rel),tofile='b/'+str(rel)))
 patch.extend(lines);plus=sum(x.startswith('+') and not x.startswith('+++') for x in lines);minus=sum(x.startswith('-') and not x.startswith('---') for x in lines)
 added+=plus;removed+=minus
 reason=reasons.get(p.name,'Change 2 adds explicit new-frame inputs, CPU tower execution and gravity telemetry to the inherited tower phase.')
 changed.append(dict(file=str(rel),added=plus,removed=minus,reason=reason,sha256=sha(p)))
(B/'out/DIFF_vs_C8R.patch').write_text(''.join(patch))
(B/'out/DIFF_FILES.md').write_text('\n'.join(f"- `{r['file']}`: {r['reason']}" for r in changed)+'\n')
dump(B/'out/DIFF_STATS.json',dict(added=added,removed=removed,files=changed,parent_code=pin(R/'work/c8r/code_c8r.tar')))
target=B/'out/c.tar'
with tarfile.open(target,'w') as archive:
 for p in sorted(current.rglob('*')):
  if not p.is_file():continue
  name=str(p.relative_to(current));info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mode=0o644;info.mtime=0
  with p.open('rb') as stream:archive.addfile(info,stream)
family=dict(schema='camera-read-family-v1',parent=pin(R/'work/c8r/FAMILY.json'),code=pin(target),
    active_driver='/c/entry.py',synthetic=False,launch_ready=False,
    code_sources=__import__('engine').source_pins(),
    protocol=dict(step=544,arms=['native','scripted_camera'],served=['move','turn','pose'],refusal='error: call_unavailable; answer directly from the video',
                  thinking_tokens=2048,answer_tokens=64,frame_count=32,canary=load(B/'out/CANARY_KEYS.json')),
    inputs=dict(item_sha256=sha(R/'in/vsti/vstibench_repr_450_v3.json'),media_sha256=sha(R/'in/vsti/media.json'),
                expected_items=450,expected_types=9,scorer=load(B/'out/SCORER_PINS.json')),
    assets=load(B/'out/ASSETS.json'),limits=dict(full=dict(gpu_seconds=21600,pool_bytes=1073741824,return_bytes=300000000,stall_seconds=1200)),
    return_pool='/project/community/jjyeung/okh7/n2r/<token>',return_gcs='gs://cmu-gpucloud-jjyeung/q8/n2r/<token>/',
    blockers=['The full local frame set and runtime assets have not been staged or verified.',
              'The authenticated GPU dependency closure and namespace have not been exercised.',
              'The candidate Orchard packet has no generation-pinned cloud upload manifest and has not passed the original launcher validator.',
              'Historical GPU equality and both remote return transports remain unexecuted.',
              'See UNEXECUTED.json for uncovered source lines; this is not a production admission.'])
dump(B/'out/FAMILY.json',family)
from venue import packet
packet_dir=B/'out/packet'
if not packet_dir.exists():packet(B/'out/FAMILY.json',B/'out/ASSETS.json',packet_dir,'3917ab0dd64f429ac1e708fb')
else:
 (packet_dir/'FAMILY.json').write_bytes((B/'out/FAMILY.json').read_bytes())
 (packet_dir/'ASSETS.json').write_bytes((B/'out/ASSETS.json').read_bytes())
 config=load(packet_dir/'CONFIG.json');config['family']['sha256']=sha(B/'out/FAMILY.json');config['assets']['sha256']=sha(B/'out/ASSETS.json');dump(packet_dir/'CONFIG.json',config)
 value=load(packet_dir/'PACKET.json');value['config']=config;dump(packet_dir/'PACKET.json',value)
dump(B/'out/PACKAGE.json',dict(code=pin(target),family=pin(B/'out/FAMILY.json'),diff=pin(B/'out/DIFF_vs_C8R.patch'),added=added,removed=removed,launch_ready=False))
