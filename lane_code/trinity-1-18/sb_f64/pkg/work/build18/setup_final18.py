from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build18';P=L/'work/build17'
for name in ('real','suite','packet','packet_inputs','storage','integrity','kits','operator','preserve','delta_coverage','delivery'):
    text=(P/(name+'17.py')).read_text().replace('work/build17','work/build18').replace('BUILD17_REPORT','BUILD18_REPORT').replace('tree_rebuild_b17_','tree_rebuild_b18_').replace('Build 17','Build 18').replace('build17_pass','build18_pass')
    if name=='suite':text=text.replace("'work/build18/inputs',", "'work/build18/inputs','work/build17/inputs',")
    if name in ('preserve','delta_coverage'):text=text.replace('w16b','w17b').replace('build-16 source','build-17 source').replace('build-17 observations','build-18 observations')
    (B/(name+'18.py')).write_text(text)
print('Final drivers prepared')
