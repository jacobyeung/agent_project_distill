cd /lab_data/tarrlab/jacoby/agent_project/aws_evac || exit 1
P='97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad'
python3 - <<'PY'
import json,glob,re,os
T=['97a6a3eb/runs/b19c1200/train/step_400/heads.json','f2ad01ad/runs/49becb79/m200/artifact.json','8865619b/u/7c9f2d84/receipt.json','5e1d07a4/f/h/r16/receipt.json','1742c666/s/q127808/vxm_m4/receipt.json','f02f16ad/s/a2v3/receipt.json','f02f16ad/s/a3v2/receipt.json','8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/pointing/rows.sqlite','f02f16ad/s/a2v3/rows.sqlite','f02f16ad/s/a3v2/rows.sqlite','8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/rows.sqlite','8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/vqa/rows.sqlite','5e1d07a4/f/h/r16/rows.sqlite']
P=re.compile(r'(97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad)')
for f in sorted(glob.glob('_direct/map/*.json')):
    s=open(f).read()
    if not P.search(s): continue
    d=json.loads(s); tok=os.path.basename(f)[:-5]
    dest='d/'+d['dest']; ex=os.path.exists(dest); part=os.path.exists(dest+'.part')
    sz=os.path.getsize(dest) if ex else None
    m=json.dumps(d.get('manifest',''))
    hits=[t for t in T if t in m or t in d.get('label','')]
    okf='_direct/ok/'+tok+'.json'
    print(tok,'exists' if ex else ('PART' if part else 'ABSENT'),sz,'ok' if os.path.exists(okf) else '-',d['dest'],'hits=',hits)
    if hits and os.path.exists(okf): print('   OK:',open(okf).read()[:700])
    if hits and 'manifest' in d:
        man=d['manifest']
        for t in hits:
            print('   MAN:',[str(x)[:300] for x in (man if isinstance(man,list) else [man]) if t in json.dumps(x)][:2] if isinstance(man,list) else str(man)[:300])
PY
echo "== other index greps"
for f in _ret_ctl/queue.tsv _gcs3/queue.tsv ../aws_evac/_stg_ctl/* ; do [ -f "$f" ] && n=$(grep -c -E "$P" "$f") && [ "$n" != 0 ] && echo "$f $n"; done
ls _ret_ctl/ok 2>/dev/null | wc -l; grep -l -E "$P" _ret_ctl/ok/* _gcs3/ok/* 2>/dev/null | head
G=/lab_data/tarrlab/jacoby/gcs_evac_20261111; ls $G/_receipts $G/aws_return 2>/dev/null | head -20; grep -l -E "$P" $G/_receipts/* $G/_receipts/*/* 2>/dev/null | head
ls d/unsent d/aws_return | head -30
