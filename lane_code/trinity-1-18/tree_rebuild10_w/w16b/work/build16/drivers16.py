from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
for name in ('test','kits','packet','packet_inputs','suite','real','delta_coverage','delivery','storage'):
    s=(L/f'work/build15/{name}15.py').read_text()
    s=s.replace('work/build15','work/build16').replace('B15_PROOF','B16_PROOF')
    if name=='delta_coverage':
        s=s.replace('BASE14_SEAL','BASE15_SEAL').replace("L.parent/'w14", "L.parent/'w15").replace('build-14','build-15').replace('build-15 observations','build-16 observations')
    if name=='suite':
        s=s.replace("'work/build_n1/inputs'", "'work/build15/inputs','work/build_n1/inputs'")
    (B/f'{name}16.py').write_text(s)
