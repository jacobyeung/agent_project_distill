import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
def read(path):return json.loads(path.read_text()) if path.exists() else {}
stages=read(B/'QUALIFICATION.json');current=stages[-1] if stages else {}
value=dict(stage=current.get('step'),state=current.get('status'))
if (read(B/'FINAL_PASS.json').get('status')=='REQUALIFYING'
        and (B/'REQUALIFICATION.json').stat().st_mtime>(B/'QUALIFICATION.json').stat().st_mtime):
    value=dict(stage='reader_repair_and_kit_staging',state='running')
if value['stage']=='frozen_package':
    value['package']=read(L/'work/merge11/proofs/n1/package/RESULTS.json')
    active=read(L/'work/merge11/proofs/n1/suite_tree/progress.json')
    value['active_group']=active
    for group in [active.get('group')]:
        if not group:continue
        p=L/'work/merge11/proofs/n1/suite_tree'/group/'progress.json'
        if p.exists():value[group]=read(p)
if value['stage']=='packet':
    path=L/'work/tmp/packet_r6/current_test.txt'
    if path.exists():value['test']=path.read_text().strip()
if value['stage']=='final_receipts':
    stage_path=B/'FINAL_STAGE.json'
    value['final_stage']=read(stage_path)
    if value['final_stage'].get('stage')=='packet' and value['final_stage'].get('status')=='running':
        path=L/'work/tmp/packet_r6/current_test.txt'
        if path.exists() and path.stat().st_mtime>=stage_path.stat().st_mtime:
            value['test']=path.read_text().strip()
if not read(B/'FINAL_PASS.json').get('status','').startswith('COMPLETE'):
    (B/'STATUS.md').write_text('# Build n1 status\n\nFinal qualification: '+str(value['stage'])+' is '+str(value['state'])+'. GO=false. Source: work/n1fix2/QUALIFICATION.json.\n\n'
        'The current report is out/BUILD_R1_REPORT.md. Full scene-admitted populations, sampler indices, runtime resolution and scale evidence, component lineage, remote staging and the real frame-host receipt remain missing. CARRIED_BLOCKERS.json names the required inputs.\n')
print(json.dumps(value))
