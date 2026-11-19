from common import *
import shutil,math
from fractions import Fraction
track(__file__);source=P.load(track(W/'out/SOURCE_RECONSTRUCTION.json'));cfg=config();cardpath=resolve(cfg['r2_sampling']['card']);card=P.load(cardpath)
root=W/'work/fixture';root.mkdir(exist_ok=True)
shutil.copyfile(cardpath,root/'card.json');cardpin=P.file_pin(root/'card.json');track(root/'card.json')
weight=OLD/'out/TOWARD_HARD_WEIGHTS.json';track(weight);shutil.copyfile(weight,W/'out/TOWARD_HARD_WEIGHTS.json');weightpin=P.file_pin(W/'out/TOWARD_HARD_WEIGHTS.json');track(W/'out/TOWARD_HARD_WEIGHTS.json')
indices=P.load(track(W/'work/source/source_indices.json'));groups=indices['cells'];stream_counts={'vqa':source['eligible_vqa']}
for c in card['cells']:
 s,k=c['stream'],c['type']
 if s=='vqa':continue
 # These fabricated support rows are explicitly confined to the unit fixture.
 n=math.ceil(Fraction(str(c['rows_per_step']))*1000/4)
 start=stream_counts.get(s,0);groups[k]=list(range(start,start+n));stream_counts[s]=start+n
scope='FIXTURE_ONLY_NOT_PRODUCTION'
evidence=write('work/fixture/evidence.json',dict(scope=scope,source_reconstruction=P.file_pin(W/'out/SOURCE_RECONSTRUCTION.json'),synthetic_streams=['pose','pointing','routing'],reason='Native stores and final post-filter tables are absent; support rows exercise checker branches only.'))
evidencepin=P.file_pin(evidence)
member=write('work/fixture/membership.json',dict(schema='r1-source-membership-v1',sources={},scope=scope))
memberpin=P.file_pin(member)
pop=write('work/fixture/population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,scope=scope,card_sha256=cardpin['sha256'],counts={k:len(v) for k,v in groups.items()},evidence=[evidencepin],source_membership=memberpin))
poppin=P.file_pin(pop)
idx=write('work/fixture/indices.json',dict(scope=scope,population_sha256=poppin['sha256'],cells=groups))
binding=dict(schema='r1-sampling-v1',card=cardpin,population=poppin,indices=P.file_pin(idx))
write('work/fixture/FIXTURE.json',dict(scope=scope,binding=binding,config=dict(r1_training=dict(routing_slices='deferred_first_boundary')),source_reconstruction=P.file_pin(W/'out/SOURCE_RECONSTRUCTION.json'),vqa_database=source['database'],stream_counts=stream_counts))
# Compare counts to every explicit card ceiling; never silently promote placeholders.
comparisons=[]
for c in card['cells']:
 k=c['type'];observed=source['cells'].get(k)
 expected=int(Fraction(str(c.get('ceiling_rows_per_step',0)))*250) if 'ceiling_rows_per_step' in c else None
 comparisons.append(dict(cell=k,stream=c['stream'],source_rows=observed,card_ceiling_rows=expected,card_ceiling_rows_per_step=c.get('ceiling_rows_per_step'),status='MISSING' if observed is None else 'PASS' if expected==observed else 'MISMATCH',launch_population_rows=0,launch_population_comparison='MISMATCH_INCOMPLETE_PLACEHOLDER' if observed else 'ZERO_PLACEHOLDER_NOT_PROOF'))
write('out/COUNT_CROSSCHECK.json',dict(scope='SOURCE_COUNTS_VS_CARD_AND_LAUNCH_PLACEHOLDERS',cells=comparisons))
print('Fixture stream counts',stream_counts)
