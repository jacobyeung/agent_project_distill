from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build17';P=L/'work/build16'
for name in ('real','suite','packet','packet_inputs','storage','integrity'):
    text=(P/(name+'16.py')).read_text().replace('work/build16','work/build17')
    if name=='suite':
        text=text.replace("'work/build17/inputs',", "'work/build17/inputs','work/build16/inputs',")
        text=text.replace('Build 15 status','Build 17 status').replace('build15_pass','build17_pass').replace('to build 15','to build 17')
        text=text.replace('A/C/Cprime admission and native opener proof pass.', 'A/C/Cprime configuration comparisons pass; complete native proof remains blocked.')
    if name=='integrity':text=text.replace('BUILD16_REPORT','BUILD17_REPORT')
    (B/(name+'17.py')).write_text(text)
text=(P/'kits16.py').read_text().replace('work/build16','work/build17')
text=text.replace("(B/'STATUS.md').write_text('# Build 13 status", "(B/'STATUS.md').write_text('# Build 17 status")
(B/'kits17.py').write_text(text)
text=(P/'delta_coverage16.py').read_text().replace('work/build16','work/build17').replace("(B/'BASE15_SEAL.json')", "(L.parent/'w16b/out/TREE_SEAL.json')").replace("'w15/work/tree_r1'", "'w16b/work/tree_r1'").replace('build-15 source','build-16 source').replace('build-16 observations','build-17 observations')
(B/'delta_coverage17.py').write_text(text)
text=(P/'preserve16.py').read_text().replace('work/build16','work/build17').replace("'w15/work/tree_r1'", "'w16b/work/tree_r1'")
text=text.replace("'student_pilot/s1_admission.py',", "'student_pilot/r1_counting.py',").replace("'student_pilot/r1_routing.py',", "'student_pilot/carrier_c1_run.py',")
(B/'preserve17.py').write_text(text)
text=(P/'delivery16.py').read_text().replace('tree_rebuild_b16_', 'tree_rebuild_b17_').replace("'work/build16/kits'", "'work/build17/kits'").replace("'work/build16/PACKET_INPUTS.json'", "'work/build17/PACKET_INPUTS.json'").replace("'work/build16/DELIVERY.json'", "'work/build17/DELIVERY.json'")
marker="members.extend(p for p in (L/'out').glob('*.md'))"
extra="""extra=L/'work/build17'
for p in extra.rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(extra)
    if str(rel) in ('DELIVERY.json','proofs/integrity/RESULT.json','delivery.log','integrity.log'):continue
    if set(rel.parts)&{'mutant','frozen','base','kits'}:continue
    if p.suffix in ('.py','.sh','.json','.jsonl','.md','.log') and p.stat().st_size<30_000_000:members.append(p)

"""
text=text.replace(marker,extra+marker)
(B/'delivery17.py').write_text(text)
print('Prepared final scripts')
